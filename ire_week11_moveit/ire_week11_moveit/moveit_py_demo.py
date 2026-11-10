#!/usr/bin/env python3
"""11주차 — MoveIt API(moveit_py)로 팔 움직이기.

pick_demo(관절 궤적을 arm_controller에 직접 전송)와 같은 팔을 MoveIt 계획으로 움직인다.

  ros2 run ire_week11_moveit moveit_py_demo --sim --step all   # Gazebo
  ros2 run ire_week11_moveit moveit_py_demo --step 1           # 실물 (한 단계씩)

단계
  1  named target ('home', SRDF)
  2  관절 목표 (pick_demo의 'approach'와 같은 값)
  3  pose 목표(위치 + 방향) — 3a 도달 가능한 방향은 성공, 3b yaw 45°는 실패(4자유도 한계, 정상)
  4  위치만 목표 — 성공하지만 손목 각은 IK가 정한다
  5  그리퍼 open / close
  6  충돌 물체(가상 상자) 회피 — 관절 직선 경로는 부딪히고, MoveIt 경로는 돌아간다

move_group 없이도 동작한다 (moveit_py가 자체 planning scene과 실행기를 가진다).
"""
import argparse
import copy
import math
import os
import sys
import time

import rclpy
from rclpy.logging import get_logger
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState
from geometry_msgs.msg import PoseStamped, Pose
from moveit_msgs.msg import Constraints, PositionConstraint, CollisionObject
from shape_msgs.msg import SolidPrimitive

from ire_week11_moveit import kit_moveit_config

LOG = get_logger('moveit_py_demo')

HOME = [0.0, -1.0, 0.7, 0.3]               # pick_demo POSES['home'] = SRDF home
APPROACH = [0.0, 0.4, 0.2, -0.6]           # pick_demo POSES['approach']
FRAME = 'base_footprint'                   # pose 목표 기준 좌표계 (모델 기준 좌표계)
EE = 'end_effector_link'

BOX_POS = (0.14, 0.0, 0.30)                # 6단계 상자 위치 [m] (base_footprint 기준, 헤드리스 검증값)
BOX_SIZE = [0.06, 0.30, 0.06]              # 6단계 상자 크기 [m]


# ---------------------------------------------------------------- 공통 함수
def current(robot, group='arm'):
    with robot.get_planning_scene_monitor().read_only() as scene:
        return list(scene.current_state.get_joint_group_positions(group))


def fmt(q):
    return '[' + ', '.join(f'{v:+.3f}' for v in q) + ']'


def log_joints(robot, label):
    LOG.info(f'  [{label}] 현재 arm = {fmt(current(robot))}, gripper = {fmt(current(robot, "gripper"))}')


def plan_exec(robot, comp, label, execute=True, attempts=1):
    """계획 → (선택) 실행. 성공하면 계획 결과, 실패하면 None."""
    t0 = time.time()
    res = None
    for k in range(attempts):                      # 샘플링 기반 계획은 확률적 — 필요하면 재시도
        res = comp.plan()
        if res:
            break
    ok = bool(res)
    t_plan = time.time() - t0
    n = len(res.trajectory.get_robot_trajectory_msg().joint_trajectory.points) if ok else 0
    ex = robot.execute(comp.planning_group_name, res.trajectory, blocking=True).status if (ok and execute) else None
    LOG.info(f'[{label}] plan={"OK" if ok else "FAIL"} (try {k + 1}/{attempts}, plan {t_plan:.2f}s, {n} pts) '
             f'exec={ex if execute else "(계획만)"}')
    return res if ok else None


def joint_state(model, q):
    """팔 관절값 q의 RobotState. 생성 직후 set_to_default_values() 필수 (안 하면 그리퍼·바퀴에 쓰레기 값)."""
    s = RobotState(model)
    s.set_to_default_values()
    s.set_joint_group_positions('arm', q)
    s.update()
    return s


def go_named(robot, arm, name, label):
    arm.set_start_state_to_current_state()
    arm.set_goal_state(configuration_name=name)
    return plan_exec(robot, arm, label)


# ---------------------------------------------------------------- 단계
def step1(ctx):
    """1 named target: SRDF의 'home'."""
    go_named(ctx['robot'], ctx['arm'], 'home', '1 named home')
    log_joints(ctx['robot'], '1')


def step2(ctx):
    """2 관절 목표: pick_demo의 approach와 같은 관절값."""
    robot, arm = ctx['robot'], ctx['arm']
    ee = ctx['approach_ee']
    LOG.info(f'  approach FK: {EE} = ({ee.position.x:.3f}, {ee.position.y:.3f}, {ee.position.z:.3f}) m, '
             f'q = ({ee.orientation.x:.3f}, {ee.orientation.y:.3f}, {ee.orientation.z:.3f}, {ee.orientation.w:.3f})')
    arm.set_start_state_to_current_state()
    arm.set_goal_state(robot_state=ctx['approach_state'])
    plan_exec(robot, arm, '2 joint approach')
    log_joints(robot, '2')
    go_named(robot, arm, 'home', '2 back home')


def step3(ctx):
    """3 pose 목표(위치 + 방향). 4자유도라 방향을 마음대로 고를 수 없다."""
    robot, arm, ee = ctx['robot'], ctx['arm'], ctx['approach_ee']

    # 3a: FK와 같은 위치 + 같은 방향 → 도달 가능 → 계획 성공
    ps = PoseStamped()
    ps.header.frame_id = FRAME
    ps.pose = ee
    arm.set_start_state_to_current_state()
    arm.set_goal_state(pose_stamped_msg=ps, pose_link=EE)
    plan_exec(robot, arm, '3a pose (reachable orientation)', execute=False)

    # 3b: 같은 위치 + yaw 45° → 계획 실패가 정상
    ps2 = PoseStamped()
    ps2.header.frame_id = FRAME
    ps2.pose.position = ee.position
    ps2.pose.orientation.z = math.sin(math.pi / 8)
    ps2.pose.orientation.w = math.cos(math.pi / 8)
    arm.set_start_state_to_current_state()
    arm.set_goal_state(pose_stamped_msg=ps2, pose_link=EE)
    LOG.info('  3b: 계획 실패가 예상 결과입니다 (몇 초 걸림).')
    r = plan_exec(robot, arm, '3b pose (yaw 45°)', execute=False)
    if r is None:
        LOG.info('  → 정상 결과: OM-X는 4자유도 — 말단 yaw는 위치에 따라 joint1이 정함 '
                 '(y = 0이면 yaw = 0) → 이 방향은 도달 불가.')
    else:
        LOG.warn('  → 예상과 달리 계획 성공. kinematics.yaml의 position_only_ik 설정을 확인하세요.')
    log_joints(robot, '3')


def step4(ctx):
    """4 위치만 목표 (반지름 5 mm 구). 손목 각은 IK가 정한다."""
    robot, arm, ee = ctx['robot'], ctx['arm'], ctx['approach_ee']
    c = Constraints()
    pc = PositionConstraint()
    pc.header.frame_id = FRAME
    pc.link_name = EE
    pc.constraint_region.primitives.append(SolidPrimitive(type=SolidPrimitive.SPHERE, dimensions=[0.005]))
    pp = Pose()
    pp.position = ee.position
    pp.orientation.w = 1.0
    pc.constraint_region.primitive_poses.append(pp)
    pc.weight = 1.0
    c.position_constraints.append(pc)
    arm.set_start_state_to_current_state()
    arm.set_goal_state(motion_plan_constraints=[c])
    plan_exec(robot, arm, '4 position-only')
    q = current(robot)
    LOG.info(f'  손목 각 j2+j3+j4 = {q[1] + q[2] + q[3]:+.3f} rad '
             f'(2단계 approach: {sum(APPROACH[1:]):+.3f}) — 같은 위치여도 실행마다 달라진다')
    log_joints(robot, '4')


def step5(ctx):
    """5 그리퍼 open / close (SRDF named state, GripperCommand 액션)."""
    robot, grip = ctx['robot'], ctx['grip']
    for name in ('open', 'close'):
        grip.set_start_state_to_current_state()
        grip.set_goal_state(configuration_name=name)
        plan_exec(robot, grip, f'5 gripper {name}')
    log_joints(robot, '5')


def step6(ctx):
    """6 충돌 물체 회피: 가상 상자를 planning scene에 넣고 home → approach."""
    robot, arm, model = ctx['robot'], ctx['arm'], ctx['model']
    go_named(robot, arm, 'home', '6 start from home')

    # (1) 상자를 moveit_py planning scene에 추가 (RViz/move_group에는 보이지 않음)
    psm = robot.get_planning_scene_monitor()
    co = CollisionObject()
    co.header.frame_id = FRAME
    co.id = 'box'
    co.primitives.append(SolidPrimitive(type=SolidPrimitive.BOX, dimensions=BOX_SIZE))
    bp = Pose()
    bp.position.x, bp.position.y, bp.position.z = BOX_POS
    bp.orientation.w = 1.0
    co.primitive_poses.append(bp)
    co.operation = CollisionObject.ADD
    with psm.read_write() as scene:
        scene.apply_collision_object(co)
        scene.current_state.update()
    LOG.info(f'  상자 추가: 위치 {BOX_POS} m, 크기 {BOX_SIZE} m ({FRAME} 기준)')

    def colliding(qs):                             # 그리퍼 등 나머지 관절은 현재 값 그대로 두고 팔만 바꿔 검사
        with psm.read_only() as scene:
            s = copy.deepcopy(scene.current_state)
            s.set_joint_group_positions('arm', qs)
            s.update()
            return scene.is_state_colliding(robot_state=s, joint_model_group_name='arm')

    # (2) pick_demo 방식(관절 직선 보간)이면 몇 지점이 부딪히나
    hits = sum(colliding([h + (a - h) * k / 20 for h, a in zip(HOME, APPROACH)]) for k in range(21))
    LOG.info(f'  관절 직선 경로 home→approach: 21개 중 {hits}개 지점 충돌 (pick_demo처럼 보내면 상자를 친다)')

    # (3) MoveIt 계획·실행 (최대 3회 재시도)
    arm.set_start_state_to_current_state()
    arm.set_goal_state(robot_state=ctx['approach_state'])
    r6 = plan_exec(robot, arm, '6 approach with box', attempts=3)

    # (4) MoveIt 경로 분석
    if r6:
        pts = r6.trajectory.get_robot_trajectory_msg().joint_trajectory.points
        zs = [joint_state(model, list(p.positions)[:4]).get_pose(EE).position.z for p in pts]
        bad = sum(colliding(list(p.positions)[:4]) for p in pts)
        LOG.info(f'  MoveIt 경로: 말단 z 최저 {min(zs):.3f} m (approach: {ctx["approach_ee"].position.z:.3f}), '
                 f'충돌 지점 {bad}/{len(pts)} (0이어야 정상)')
    log_joints(robot, '6')


STEPS = {'1': step1, '2': step2, '3': step3, '4': step4, '5': step5, '6': step6}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description='moveit_py 6단계 예제')
    ap.add_argument('--step', default='all', choices=list(STEPS) + ['all'], help='1~6 또는 all (기본 all)')
    ap.add_argument('--sim', action='store_true', help='Gazebo: use_sim_time=True')
    args, _ = ap.parse_known_args(rclpy.utilities.remove_ros_args(sys.argv)[1:])

    rclpy.init()
    robot = MoveItPy(node_name='moveit_py_demo', config_dict=kit_moveit_config.build(use_sim_time=args.sim))
    model = robot.get_robot_model()
    ctx = {
        'robot': robot,
        'model': model,
        'arm': robot.get_planning_component('arm'),
        'grip': robot.get_planning_component('gripper'),
    }
    # 2·3·4·6단계가 함께 쓰는 approach 상태와 그 말단 pose(FK)
    ctx['approach_state'] = joint_state(model, APPROACH)
    ctx['approach_ee'] = ctx['approach_state'].get_pose(EE)
    LOG.info(f'model frame = {model.model_frame}, pose 목표 frame = {FRAME}, sim = {args.sim}, '
             f'속도·가속도 스케일 = 0.1')
    time.sleep(1.0)                                # /joint_states 수신 대기

    code = 0
    try:
        for key in (STEPS if args.step == 'all' else [args.step]):
            LOG.info(f'===== {key}단계: {STEPS[key].__doc__.splitlines()[0]} =====')
            STEPS[key](ctx)
        LOG.info('done')
    except Exception:
        import traceback
        traceback.print_exc()
        code = 1
    finally:
        robot.shutdown()
        rclpy.try_shutdown()
        # Humble apt moveit_py(2.5.10)는 MoveItPy 객체를 파괴할 때(파이썬 종료 시) segfault가 난다
        # (TrajectoryExecutionManager 내부 노드 소멸 중). 동작과는 무관 → 소멸자를 건너뛰고 바로 종료한다.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)


if __name__ == '__main__':
    main()
