#!/usr/bin/env python3
"""4주차 강의 예제 — 서비스로 켜고 끄는 원 그리기 노드.

  ros2 run ire_week04_service_launch circle_driver
  ros2 service call /start_stop std_srvs/srv/SetBool "{data: true}"
  ros2 param set /circle_driver speed 1.5
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool


class CircleDriver(Node):
    def __init__(self):
        super().__init__('circle_driver')
        self.declare_parameter('speed', 1.0)      # 선속도 [m/s]
        self.declare_parameter('turn', 1.0)       # 각속도 [rad/s]
        self.running = False
        self.pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.srv = self.create_service(SetBool, 'start_stop', self.on_call)
        self.create_timer(0.1, self.on_timer)

    def on_call(self, req, res):
        self.running = req.data
        res.success = True
        res.message = 'running' if req.data else 'stopped'
        self.get_logger().info(res.message)
        return res                                 # 짧고 즉시 return!

    def on_timer(self):
        if not self.running:
            return
        msg = Twist()
        msg.linear.x = self.get_parameter('speed').value
        msg.angular.z = self.get_parameter('turn').value
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = CircleDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
