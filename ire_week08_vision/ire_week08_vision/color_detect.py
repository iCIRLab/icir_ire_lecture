#!/usr/bin/env python3
"""8주차 강의 예제 — 빨간 기둥 색 검출 노드.

카메라 영상에서 빨간 영역을 HSV로 찾아 존재 여부를 /red_pillar/exists 로 발행한다.
빨강은 H가 0과 180 양 끝에 걸쳐 있으므로 inRange를 두 번 하고 OR로 합친다.

  ros2 run ire_week08_vision color_detect
  ros2 param set /color_detect min_area 500      # 튜닝은 파라미터로
"""
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from cv_bridge import CvBridge


class ColorDetect(Node):
    def __init__(self):
        super().__init__('color_detect')
        # 팔이 장착된 실습 키트(turtlebot3_manipulation)의 카메라 토픽.
        # 팔 없는 turtlebot3_gazebo를 쓸 때는 /camera/image_raw 로 바꾼다.
        self.declare_parameter('image_topic', '/pi_camera/image_raw')
        self.declare_parameter('min_area', 300)          # 이보다 작은 빨강은 노이즈
        self.declare_parameter('hsv1_low',  [0, 120, 80])
        self.declare_parameter('hsv1_high', [10, 255, 255])
        self.declare_parameter('hsv2_low',  [170, 120, 80])
        self.declare_parameter('hsv2_high', [180, 255, 255])
        self.declare_parameter('show_windows', False)    # True면 마스크 창 표시

        self.bridge = CvBridge()
        topic = self.get_parameter('image_topic').value
        self.create_subscription(Image, topic, self.on_image, 10)
        self.pub = self.create_publisher(Bool, 'red_pillar/exists', 10)
        self.last = None
        self.windows_open = False        # show_windows를 끄면 창도 닫기 위해 기억해 둔다
        self.get_logger().info(f'listening: {topic}')

    def on_image(self, msg):
        bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        p = lambda n: np.array(self.get_parameter(n).value, dtype=np.uint8)
        mask = cv2.bitwise_or(cv2.inRange(hsv, p('hsv1_low'), p('hsv1_high')),
                              cv2.inRange(hsv, p('hsv2_low'), p('hsv2_high')))

        # 모폴로지로 소금·후추 노이즈 정리
        k = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(cv2.erode(mask, k, iterations=1), k, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = float(self.get_parameter('min_area').value)
        exists = any(cv2.contourArea(c) >= min_area for c in contours)

        if exists != self.last:                          # 상태가 바뀔 때만 로그
            self.get_logger().info('RED PILLAR: ' + ('PRESENT' if exists else 'ABSENT'))
            self.last = exists
        self.pub.publish(Bool(data=exists))

        show = self.get_parameter('show_windows').value
        if show:
            dbg = bgr.copy()
            cv2.drawContours(dbg, contours, -1, (0, 255, 0), 2)
            cv2.imshow('camera', dbg)       # 원본 + 검출 영역
            cv2.imshow('red_mask', mask)    # 빨강으로 판정된 픽셀
            cv2.waitKey(1)
        elif self.windows_open:             # 방금 껐다면 남은 창을 닫는다
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        self.windows_open = show


def main():
    rclpy.init()
    node = ColorDetect()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()


if __name__ == '__main__':
    main()
