#!/usr/bin/env python3
"""4주차 강의 예제 — start_stop 서비스의 파이썬 클라이언트.

circle_driver(서버)를 켜둔 상태에서 실행하면 3초마다 켜기/끄기를 반복합니다.
  터미널1: ros2 run ire_week04_service_launch circle_driver
  터미널2: ros2 run ire_week04_service_launch start_stop_client
CLI 클라이언트와 같은 일을 코드로 하는 것:
  ros2 service call /start_stop std_srvs/srv/SetBool "{data: true}"
"""
import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool


class StartStopClient(Node):
    def __init__(self):
        super().__init__('start_stop_client')
        self.cli = self.create_client(SetBool, 'start_stop')
        # 실전형 대기 — 서버가 없으면 1초마다 알리며 기다린다
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('start_stop 서버 대기 중...')
        self.next_cmd = True                       # 다음에 보낼 값 (True=켜기)
        self.create_timer(3.0, self.on_timer)      # 3초마다 요청

    def on_timer(self):
        req = SetBool.Request()
        req.data = self.next_cmd
        self.next_cmd = not self.next_cmd          # 켜기/끄기 토글
        future = self.cli.call_async(req)          # 부치고 기다리지 않음
        future.add_done_callback(self.on_resp)     # 응답 도착 시 호출 예약

    def on_resp(self, future):
        res = future.result()                      # 서버 on_call의 return이 여기로
        self.get_logger().info(f'응답: success={res.success}, "{res.message}"')


def main():
    rclpy.init()
    node = StartStopClient()
    try:
        rclpy.spin(node)                           # 타이머·응답 콜백 상주 처리
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
