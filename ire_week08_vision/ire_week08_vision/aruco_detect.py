#!/usr/bin/env python3
"""8주차 강의 예제 — ArUco 마커 검출 + pose 추정 노드.

카메라 영상에서 ArUco 마커(DICT_4X4_50)를 찾고, 카메라 기준 마커의 위치·자세를
/aruco/pose(PoseStamped)로 발행한다. 마커 테두리·ID·좌표축을 그린 영상은
/aruco/image 로 발행하므로 RViz2(또는 rqt_image_view)에서 바로 확인할 수 있다.
마커가 여러 개 보이면 /aruco/pose 를 마커마다 한 번씩 발행한다.

  # 수업(Gazebo) — aruco_world를 띄운 뒤
  ros2 run ire_week08_vision aruco_detect

  # 실습(실물) — 토픽 두 개와 마커 크기만 바꾼다
  ros2 run ire_week08_vision aruco_detect --ros-args \
    -p image_topic:=/camera/image_raw -p camera_info_topic:=/camera/camera_info \
    -p marker_size:=0.05        # 화면 위 검은 사각형을 자로 잰 값 [m]
"""
import math

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image

DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# ---- OpenCV 버전 호환 (Ubuntu 22.04 apt = 4.5.4 기준) -------------------------
# 코너를 서브픽셀로 다듬으면 거리 오차가 줄어든다.
if hasattr(cv2.aruco, 'ArucoDetector'):                       # OpenCV 4.7 이상
    _params = cv2.aruco.DetectorParameters()
    _params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    _detector = cv2.aruco.ArucoDetector(DICT, _params)

    def detect(gray):
        return _detector.detectMarkers(gray)
else:                                                          # OpenCV 4.5.x
    _params = cv2.aruco.DetectorParameters_create()
    _params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    def detect(gray):
        return cv2.aruco.detectMarkers(gray, DICT, parameters=_params)


def estimate(corners, size, K, D):
    """코너 4점 → 마커마다 (rvec, tvec). 15p의 estimatePoseSingleMarkers와 같은 계산."""
    if hasattr(cv2.aruco, 'estimatePoseSingleMarkers'):        # OpenCV 4.5.x
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, size, K, D)
        return [(r.ravel(), t.ravel()) for r, t in zip(rvecs, tvecs)]
    h = size / 2.0                                              # 4.7 이상: 같은 계산을 solvePnP로
    obj = np.array([[-h, h, 0], [h, h, 0], [h, -h, 0], [-h, -h, 0]], dtype=np.float32)
    out = []
    for c in corners:
        _, r, t = cv2.solvePnP(obj, c.reshape(4, 2), K, D, flags=cv2.SOLVEPNP_IPPE_SQUARE)
        out.append((r.ravel(), t.ravel()))
    return out


def rvec_to_quaternion(rvec):
    """회전벡터(회전축 × 각도) → 쿼터니언 (x, y, z, w). PoseStamped의 orientation 용."""
    angle = float(np.linalg.norm(rvec))
    if angle < 1e-12:
        return 0.0, 0.0, 0.0, 1.0
    s = math.sin(angle / 2.0) / angle
    return float(rvec[0] * s), float(rvec[1] * s), float(rvec[2] * s), math.cos(angle / 2.0)


class ArucoDetect(Node):
    def __init__(self):
        super().__init__('aruco_detect')
        # 기본값은 수업(Gazebo) 토픽. 실물은 /camera/image_raw, /camera/camera_info
        self.declare_parameter('image_topic', '/pi_camera/image_raw')
        self.declare_parameter('camera_info_topic', '/pi_camera/camera_info')
        self.declare_parameter('marker_size', 0.117)    # 검은 사각형 한 변 [m] (시뮬 0.117)
        self.declare_parameter('show_windows', False)   # True면 OpenCV 창도 띄운다
        # pose가 기준으로 삼는 프레임 — 카메라 광학 프레임(z 앞·x 오른쪽·y 아래).
        # 시뮬·실물 모두 URDF에 있어 TF로 로봇에 붙는다 (영상의 frame_id는 쓰지 않는다)
        self.declare_parameter('frame_id', 'camera_rgb_optical_frame')

        self.bridge = CvBridge()
        self.K = self.D = None
        self.last_ids = None
        self.frame_logged = False
        self.windows_open = False
        image_topic = self.get_parameter('image_topic').value
        info_topic = self.get_parameter('camera_info_topic').value
        # 센서용 QoS로 구독 — 시뮬·실물·bag 재생 어느 쪽 발행자와도 연결된다
        self.create_subscription(CameraInfo, info_topic, self.on_info, qos_profile_sensor_data)
        self.create_subscription(Image, image_topic, self.on_image, qos_profile_sensor_data)
        self.pose_pub = self.create_publisher(PoseStamped, 'aruco/pose', 10)
        self.image_pub = self.create_publisher(Image, 'aruco/image', 10)
        self.get_logger().info(f'listening: {image_topic} + {info_topic}')

    def on_info(self, msg):
        # 카메라 행렬 K(3×3)와 왜곡계수 D — pose 계산에 필요하다
        self.K = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self.D = np.array(msg.d, dtype=np.float64)

    def on_image(self, msg):
        if self.K is None:
            self.get_logger().warn(f'camera_info 대기 중 — '
                                   f'{self.get_parameter("camera_info_topic").value}',
                                   throttle_duration_sec=3.0)
            return
        if not self.K.any():
            self.get_logger().warn('camera_info의 K가 전부 0 — 캘리브레이션 파일이 적용되지 않았다',
                                   throttle_duration_sec=3.0)
            return
        if not self.frame_logged:
            self.get_logger().info(f'pose frame_id = {self.get_parameter("frame_id").value}'
                                   f'  → RViz2 Fixed Frame은 base_footprint')
            self.frame_logged = True

        bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        corners, ids, _ = detect(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))      # ① 검출
        found = [] if ids is None else ids.ravel().tolist()
        if found != self.last_ids:                       # 보이는 ID가 바뀔 때만 로그
            self.get_logger().info(f'ArUco ids: {found}' if found else 'ArUco: none')
            self.last_ids = found

        dbg = bgr.copy()
        if found:
            size = float(self.get_parameter('marker_size').value)
            cv2.aruco.drawDetectedMarkers(dbg, corners, ids)
            for c, (rvec, tvec) in zip(corners, estimate(corners, size, self.K, self.D)):  # ② pose
                cv2.drawFrameAxes(dbg, self.K, self.D, rvec, tvec, size * 0.5)
                x, y = c.reshape(4, 2)[2].astype(int)
                for color, thick in (((0, 0, 0), 3), ((0, 255, 255), 1)):   # 검은 테두리 + 노란 글자
                    cv2.putText(dbg, f'{tvec[2]:.2f} m', (int(x), int(y) + 14),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, thick)

                p = PoseStamped()
                p.header.stamp = msg.header.stamp        # 영상과 같은 시각
                p.header.frame_id = self.get_parameter('frame_id').value   # 카메라 광학 프레임 기준
                p.pose.position.x, p.pose.position.y, p.pose.position.z = map(float, tvec)
                o = p.pose.orientation
                o.x, o.y, o.z, o.w = rvec_to_quaternion(rvec)
                self.pose_pub.publish(p)                 # ③ 발행

        out = self.bridge.cv2_to_imgmsg(dbg, encoding='bgr8')
        out.header = msg.header
        self.image_pub.publish(out)

        show = self.get_parameter('show_windows').value
        if show:
            cv2.imshow('aruco', dbg)
            cv2.waitKey(1)
        elif self.windows_open:                          # 방금 껐다면 남은 창을 닫는다
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        self.windows_open = show


def main():
    rclpy.init()
    node = ArucoDetect()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()


if __name__ == '__main__':
    main()
