#!/usr/bin/env python3
"""3주차 강의 예제 — 1초마다 인사하는 publisher."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Talker(Node):
    def __init__(self):
        super().__init__('talker')
        self.pub = self.create_publisher(String, 'chatter', 10)
        self.count = 0
        self.create_timer(1.0, self.on_timer)

    def on_timer(self):
        msg = String()
        msg.data = f'hello ros2 {self.count}'
        self.pub.publish(msg)
        self.get_logger().info(f'pub: {msg.data}')
        self.count += 1


def main():
    rclpy.init()
    node = Talker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
