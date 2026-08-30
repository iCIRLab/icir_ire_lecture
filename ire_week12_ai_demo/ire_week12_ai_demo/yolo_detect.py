#!/usr/bin/env python3
"""12주차 — YOLO 실시간 탐지 (ROS 노드).

카메라 토픽을 구독해 YOLO 로 탐지하고 두 가지를 발행한다.

  /yolo/detections  (String)  "클래스 신뢰도 (중심x,중심y)" 형식
  /yolo/image       (Image)   박스가 그려진 영상 — RViz 로 볼 수 있다

  conda activate ire_ai
  source /opt/ros/humble/setup.bash && source ~/ire_ws/install/setup.bash
  python3 yolo_detect.py --ros-args -p image_topic:=/camera/camera/color/image_raw

주의: 카메라를 직접 여는 yolo_cam.py 와 달리 이 노드는 ROS 토픽을 구독한다.
      realsense2_camera 같은 카메라 노드가 먼저 떠 있어야 한다.
"""
import os

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO

WEIGHT_DIR = os.path.expanduser('~/ai_weights')   # 가중치를 한 곳에 모은다


class YoloDetect(Node):
    def __init__(self):
        super().__init__('yolo_detect')
        self.declare_parameter('image_topic', '/camera/camera/color/image_raw')
        self.declare_parameter('conf', 0.5)
        os.makedirs(WEIGHT_DIR, exist_ok=True)
        os.chdir(WEIGHT_DIR)                     # 가중치가 여기에 받아진다
        self.model = YOLO('yolov8n.pt')          # 첫 실행 시 자동 다운로드(~6MB)
        self.bridge = CvBridge()
        topic = self.get_parameter('image_topic').value
        self.create_subscription(Image, topic, self.on_image, 10)
        self.pub = self.create_publisher(String, '/yolo/detections', 10)
        self.img_pub = self.create_publisher(Image, '/yolo/image', 10)   # RViz 용
        self.get_logger().info(f'YOLO ready on {topic}')
        self.get_logger().info('결과: /yolo/detections (문자열), /yolo/image (RViz)')

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        results = self.model(frame, conf=self.get_parameter('conf').value, verbose=False)
        out = []
        for b in results[0].boxes:
            cls = self.model.names[int(b.cls)]
            cx = float((b.xyxy[0][0] + b.xyxy[0][2]) / 2)
            cy = float((b.xyxy[0][1] + b.xyxy[0][3]) / 2)
            out.append(f'{cls} {float(b.conf):.2f} ({cx:.0f},{cy:.0f})')
        if out:
            self.pub.publish(String(data='; '.join(out)))

        # 박스가 그려진 영상을 발행한다 — RViz 의 Image 디스플레이로 확인
        annotated = results[0].plot()
        img_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        img_msg.header = msg.header          # 타임스탬프·frame_id 를 원본과 맞춘다
        self.img_pub.publish(img_msg)


def main():
    rclpy.init()
    node = YoloDetect()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
