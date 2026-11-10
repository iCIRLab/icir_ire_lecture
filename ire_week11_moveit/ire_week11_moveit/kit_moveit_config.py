"""키트(turtlebot3_manipulation_moveit_config) 설정 파일을 그대로 읽어 moveit_py용 파라미터 dict를 만든다.
키트 move_group.launch.py와 같은 파일을 같은 방식으로 읽고, moveit_py 전용 항목만 덧붙인다."""
import os

import xacro
import yaml
from ament_index_python.packages import get_package_share_directory


def _yaml(pkg, *path):
    with open(os.path.join(get_package_share_directory(pkg), *path)) as f:
        return yaml.safe_load(f)


def build(use_sim_time=False, position_only_ik=None, vel_scale=0.1, acc_scale=0.1, segment_fraction=0.002):
    cfg_pkg = 'turtlebot3_manipulation_moveit_config'
    urdf = xacro.process_file(os.path.join(
        get_package_share_directory('turtlebot3_manipulation_description'),
        'urdf', 'turtlebot3_manipulation.urdf.xacro')).toxml()
    with open(os.path.join(get_package_share_directory(cfg_pkg), 'config', 'turtlebot3_manipulation.srdf')) as f:
        srdf = f.read()
    kin = _yaml(cfg_pkg, 'config', 'kinematics.yaml')            # {'arm': {...}} — 키트와 같은 구조
    if position_only_ik is not None:
        kin['arm']['position_only_ik'] = position_only_ik
    ompl = {
        'planning_plugin': 'ompl_interface/OMPLPlanner',
        'request_adapters': (
            'default_planner_request_adapters/AddTimeOptimalParameterization '
            'default_planner_request_adapters/FixWorkspaceBounds '
            'default_planner_request_adapters/FixStartStateBounds '
            'default_planner_request_adapters/FixStartStateCollision '
            'default_planner_request_adapters/FixStartStatePathConstraints'),
        'start_state_max_bounds_error': 0.1,
    }
    ompl.update(_yaml(cfg_pkg, 'config', 'ompl_planning.yaml'))
    # 충돌 검사 간격(경로 길이 대비): 기본 0.01은 얇은 물체를 건너뛸 수 있다 → 0.002 (6단계 성공률 14/20 → 19/20)
    ompl['arm'] = {'longest_valid_segment_fraction': segment_fraction}
    params = {
        'robot_description': urdf,
        'robot_description_semantic': srdf,
        **kin,
        # ---- moveit_py(MoveItCpp) 전용 ----
        'planning_scene_monitor_options': {
            'name': 'planning_scene_monitor',
            'robot_description': 'robot_description',
            'joint_state_topic': '/joint_states',
            'attached_collision_object_topic': '/moveit_cpp/planning_scene_monitor',
            'publish_planning_scene_topic': '/moveit_cpp/publish_planning_scene',
            'monitored_planning_scene_topic': '/moveit_cpp/monitored_planning_scene',
            'wait_for_initial_state_timeout': 10.0,
        },
        'planning_pipelines': {'pipeline_names': ['ompl']},
        'plan_request_params': {
            'planning_attempts': 1,
            'planning_pipeline': 'ompl',
            'planning_time': 5.0,
            'max_velocity_scaling_factor': vel_scale,
            'max_acceleration_scaling_factor': acc_scale,
        },
        'ompl': ompl,
        # ---- 실행: 키트 move_group.launch.py와 동일 ----
        'moveit_manage_controllers': True,
        'trajectory_execution': {
            'allowed_execution_duration_scaling': 1.2,
            'allowed_goal_duration_margin': 0.5,
            'allowed_start_tolerance': 0.05,
        },
        'moveit_simple_controller_manager': _yaml(cfg_pkg, 'config', 'moveit_controllers.yaml'),
        'moveit_controller_manager': 'moveit_simple_controller_manager/MoveItSimpleControllerManager',
        'use_sim_time': use_sim_time,
    }
    if use_sim_time:
        # Humble moveit_py 노드(allow_undeclared_parameters)에 use_sim_time만 주면 시작 시
        # "qos_overrides./clock.subscription.durability could not be set"로 죽는다 → /clock 구독 QoS를 미리 지정
        # (값은 rclcpp ClockQoS 기본값과 같다: best_effort, volatile, keep_last 1)
        params['qos_overrides'] = {'/clock': {'subscription': {
            'durability': 'volatile', 'history': 'keep_last', 'depth': 1, 'reliability': 'best_effort'}}}
    return params
