from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='turtlesim', executable='turtlesim_node'),
        Node(package='ire_week04_service_launch',
             executable='circle_driver',
             parameters=[{'speed': 1.0, 'turn': 1.0}]),
    ])
