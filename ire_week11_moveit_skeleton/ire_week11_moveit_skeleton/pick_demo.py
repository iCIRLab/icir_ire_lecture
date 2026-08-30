#!/usr/bin/env python3
"""11주차 — Pick & Place.

bringup(또는 gazebo) 상태에서:
  ros2 run ire_week11_moveit_skeleton pick_demo

제공하는 것: 팔 관절 궤적 전송 + 그리퍼 열기/닫기 + 예시 시퀀스.
학생 몫: ArUco pose → 목표 관절각/좌표 연결, 시퀀스 설계, 예외 처리.

주의: POSES의 관절값은 예시다 — 실물에서 teleop으로 팔을 움직여
      /joint_states 를 echo 하면서 자기 값을 찾아 바꿔 넣을 것.
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import GripperCommand
from builtin_interfaces.msg import Duration

ARM_JOINTS = ['joint1', 'joint2', 'joint3', 'joint4']

POSES = {                       # [joint1, joint2, joint3, joint4] (rad) — 예시!
    'home':     [0.0, -1.0, 0.7, 0.3],
    'ready':    [0.0, -0.6, 0.3, 0.3],
    'approach': [0.0,  0.4, 0.2, -0.6],
    'lift':     [0.0, -0.4, 0.0, 0.0],
}


class PickDemo(Node):
    def __init__(self):
        super().__init__('pick_demo')
        self.arm_pub = self.create_publisher(
            JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.grip = ActionClient(self, GripperCommand,
                                 '/gripper_controller/gripper_cmd')

    def arm_to(self, name, sec=2.0):
        traj = JointTrajectory()
        traj.joint_names = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = POSES[name]
        pt.time_from_start = Duration(sec=int(sec), nanosec=int((sec % 1) * 1e9))
        traj.points = [pt]
        self.arm_pub.publish(traj)
        self.get_logger().info(f'arm → {name}')

    def gripper(self, open_):
        goal = GripperCommand.Goal()
        goal.command.position = 0.015 if open_ else -0.005   # 예시값 — 물체 크기에 맞게
        goal.command.max_effort = 5.0
        self.grip.wait_for_server()
        self.grip.send_goal_async(goal)
        self.get_logger().info('gripper ' + ('open' if open_ else 'close'))


def main():
    rclpy.init()
    node = PickDemo()
    import time
    seq = [('home', None), (None, True), ('approach', None), (None, False),
           ('lift', None), ('home', None)]
    for pose, grip in seq:                      # 예시 시퀀스 — 미션에선 직접 설계
        if pose: node.arm_to(pose)
        if grip is not None: node.gripper(grip)
        time.sleep(2.5)
    node.get_logger().info('sequence done')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
