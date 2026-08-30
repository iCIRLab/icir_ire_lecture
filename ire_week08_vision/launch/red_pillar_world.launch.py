"""실습 키트(팔 장착) 시뮬레이션를 띄우고 빨간 기둥을 추가한 뒤 색 검출 노드를 실행.

  export TURTLEBOT3_MODEL=waffle_pi
  ros2 launch ire_week08_vision red_pillar_world.launch.py
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    tb3_gazebo = get_package_share_directory('turtlebot3_manipulation_gazebo')
    pillar_sdf = os.path.join(get_package_share_directory('ire_assets'),
                              'models', 'red_pillar', 'model.sdf')

    world = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(tb3_gazebo, 'launch', 'gazebo.launch.py')))

    spawn_pillar = TimerAction(period=5.0, actions=[
        Node(package='gazebo_ros', executable='spawn_entity.py',
             arguments=['-entity', 'red_pillar', '-file', pillar_sdf,
                        '-x', '1.0', '-y', '0.0', '-z', '0.0'])])

    detect = Node(package='ire_week08_vision', executable='color_detect',
                  parameters=[{'show_windows': True}])

    return LaunchDescription([world, spawn_pillar, detect])
