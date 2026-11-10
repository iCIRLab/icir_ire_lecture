"""moveit_py_demo를 RViz로 보기 — move_group(moveit_core) 없이 RViz만 띄운다.

  ros2 launch ire_week11_moveit moveit_py_rviz.launch.py          # Gazebo (기본 use_sim_time:=true)
  ros2 launch ire_week11_moveit moveit_py_rviz.launch.py use_sim_time:=false   # 실물

moveit_py가 발행하는 planning scene(/moveit_cpp/monitored_planning_scene)을 그려서
로봇 + 6단계 충돌 상자가 보인다. MoveIt RViz 플러그인은 로봇 모델(URDF·SRDF)을 RViz 노드의
파라미터에서 읽으므로, kit_moveit_config와 같은 키트 파일을 파라미터로 넘겨 준다.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ire_week11_moveit import kit_moveit_config


def _rviz(context):
    sim = LaunchConfiguration('use_sim_time').perform(context).lower() == 'true'
    cfg = kit_moveit_config.build(use_sim_time=sim)
    rviz_file = os.path.join(get_package_share_directory('ire_assets'), 'rviz', 'week11_moveit_py.rviz')
    return [Node(
        package='rviz2', executable='rviz2', name='rviz2_moveit_py', output='log',
        arguments=['-d', rviz_file],
        parameters=[{
            'robot_description': cfg['robot_description'],
            'robot_description_semantic': cfg['robot_description_semantic'],
            'use_sim_time': sim,
        }],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Gazebo면 true, 실물이면 false'),
        OpaqueFunction(function=_rviz),
    ])
