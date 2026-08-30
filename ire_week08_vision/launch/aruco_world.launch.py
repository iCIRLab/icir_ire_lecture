"""실습 키트(팔 장착) 시뮬레이션에 ArUco 박스를 세운다 (검출 노드는 각자 작성!).

  export TURTLEBOT3_MODEL=waffle_pi
  ros2 launch ire_week08_vision aruco_world.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    tb3_gazebo = get_package_share_directory('turtlebot3_manipulation_gazebo')
    box_sdf = os.path.join(get_package_share_directory('ire_assets'),
                           'models', 'aruco_box', 'model.sdf')

    world = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(tb3_gazebo, 'launch', 'gazebo.launch.py')))

    spawn_box = TimerAction(period=5.0, actions=[
        Node(package='gazebo_ros', executable='spawn_entity.py',
             # 로봇 시작 위치(-2.0, -0.5) 정면 약 0.7m — teleop으로 이동하지 않아도
             # 처음부터 카메라에 마커가 보이도록 배치한다.
             arguments=['-entity', 'aruco_box', '-file', box_sdf,
                        '-x', '-0.3', '-y', '-0.5', '-z', '0.0'])])

    return LaunchDescription([world, spawn_box])
