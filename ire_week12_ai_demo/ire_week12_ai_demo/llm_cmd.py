#!/usr/bin/env python3
"""12주차 — LLM 파싱 노드: 자연어 명령 → 검증된 미션 JSON.

/voice_cmd(String) 를 받아 로컬 Ollama에 보내고, JSON 스키마 검증을
통과한 경우에만 /mission_goal(String) 로 발행한다.

  ros2 run ire_week12_ai_demo llm_cmd
  ros2 topic pub --once /voice_cmd std_msgs/msg/String "{data: '빨간 블록 가져와'}"

원칙: LLM은 조타수가 아니라 통역사 — 출력은 반드시 검증 후 사용.
"""
import json
import requests
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

OLLAMA_URL = 'http://localhost:11434/api/generate'
SYSTEM = ('너는 로봇 명령 파서다. 반드시 JSON 한 개로만 답하라: '
          '{"action": "navigate|pick|place|stop", "target": "<이름 또는 null>"} '
          '모르면 {"action": "stop", "target": null}')
ALLOWED = {'navigate', 'pick', 'place', 'stop'}


class LlmCmd(Node):
    def __init__(self):
        super().__init__('llm_cmd')
        self.declare_parameter('model', 'llama3.2:3b')
        self.create_subscription(String, '/voice_cmd', self.on_cmd, 10)
        self.pub = self.create_publisher(String, '/mission_goal', 10)
        self.get_logger().info('llm_cmd ready — Ollama가 떠 있어야 한다')

    def on_cmd(self, msg):
        payload = {'model': self.get_parameter('model').value,
                   'prompt': SYSTEM + '\n명령: ' + msg.data,
                   'format': 'json', 'stream': False}
        try:
            res = requests.post(OLLAMA_URL, json=payload, timeout=30)
            plan = json.loads(res.json()['response'])
        except Exception as e:
            self.get_logger().warn(f'LLM 실패: {e}')
            return
        if plan.get('action') not in ALLOWED:            # 검증 = 실행 허가
            self.get_logger().warn(f'검증 탈락: {plan}')
            return
        self.pub.publish(String(data=json.dumps(plan, ensure_ascii=False)))
        self.get_logger().info(f'mission: {plan}')


def main():
    rclpy.init()
    node = LlmCmd()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
