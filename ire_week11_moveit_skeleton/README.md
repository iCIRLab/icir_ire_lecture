# ire_week11_moveit_skeleton

미션 #4 (Pick & Place)의 출발점입니다.

- `pick_demo` — 팔 관절 궤적 + 그리퍼 액션 + 예시 시퀀스 (MoveIt 없이 팔이 움직이는 최소 코드)
- MoveIt2 플래닝은 수업에서 RViz(MotionPlanning 패널)로 체험 — 코드 통합은 심화
- POSES의 관절값은 예시: teleop으로 팔을 움직이며 `/joint_states`를 보고 자기 값으로 교체
- 학생 몫: 8주차 ArUco pose → 목표 연결, pick–place 시퀀스 설계

## A. Gazebo (수업)

### 1. 시뮬레이션 (필수)

```bash
ros2 launch turtlebot3_manipulation_gazebo gazebo.launch.py
```

이 launch가 팔 컨트롤러까지 함께 띄웁니다. 아래 4개가 모두 `active`여야 정상입니다.

```bash
ros2 control list_controllers
```

```
joint_state_broadcaster   active
arm_controller            active
gripper_controller        active
imu_broadcaster           active
```

`pick_demo`는 이 컨트롤러들이 제공하는 인터페이스를 직접 사용합니다.

| pick_demo가 사용하는 것 | 제공 주체 |
|---|---|
| `/arm_controller/joint_trajectory` (토픽) | `arm_controller` |
| `/gripper_controller/gripper_cmd` (액션) | `gripper_controller` |

### 2. MoveIt2

```bash
ros2 launch turtlebot3_manipulation_moveit_config moveit_core.launch.py
```

`move_group`(플래닝 서버)과 RViz를 함께 띄웁니다. RViz의 **MotionPlanning** 패널에서
목표 자세를 끌어다 놓고 *Plan* → *Execute* 하면 MoveIt이 충돌을 피하는 궤적을 계산해
실행합니다. 11주차의 핵심은 이 과정입니다.

정상 실행 시 아래가 보여야 합니다.

```bash
ros2 node list   | grep move_group        # /move_group
ros2 action list | grep move_action       # /move_action, /execute_trajectory
```

> ROBOTIS 문서에는 `moveit_gazebo.launch.py`도 나오지만, 현재 설치된
> `turtlebot3_manipulation` 버전에서는 동작하지 않습니다. 이 launch가 include하는
> `turtlebot3_manipulation_bringup/launch/gazebo.launch.py`가 존재하지 않아
> (그 패키지에는 `base.launch.py`, `hardware.launch.py`뿐) 아래 오류로 중단되며
> `move_group`이 뜨지 않습니다. 위의 `moveit_core.launch.py`를 사용하십시오.
>
> ```
> [ERROR] [launch]: [Errno 2] No such file or directory:
>   '.../turtlebot3_manipulation_bringup/share/.../launch/gazebo.launch.py'
> ```
>
> 참고로 실행 중 `occupancy_map_monitor: No 3D sensor plugin(s) defined`와
> `motion_planning_frame: Action server /recognize_objects not available` 오류가
> 출력되지만, 각각 octomap과 물체 인식용 선택 기능이라 플래닝에는 영향이 없습니다.

#### 팔을 손으로 조작해 보려면 (MoveIt Servo)

키보드로 팔을 직접 조그(jog)하는 기능입니다. `POSES` 값을 찾을 때 유용합니다.
플래닝 대신 사용하는 것이므로, 2단계의 `moveit_core`를 종료한 뒤 실행합니다.

```bash
# 터미널2
ros2 launch turtlebot3_manipulation_moveit_config servo.launch.py
# 터미널3
ros2 run turtlebot3_manipulation_teleop turtlebot3_manipulation_teleop
```

### 3. `pick_demo` — 궤적을 코드로 보내기

```bash
ros2 run ire_week11_moveit_skeleton pick_demo
```

```
[pick_demo]: arm → home
[pick_demo]: gripper open
[pick_demo]: arm → approach
[pick_demo]: gripper close
[pick_demo]: arm → lift
[pick_demo]: arm → home
[pick_demo]: sequence done
```

팔이 실제로 움직였는지는 관절값으로 확인합니다.

```bash
ros2 topic echo /joint_states --once
```

`joint1~4`가 `POSES['home']`인 `[0.0, -1.0, 0.7, 0.3]` 부근이면 정상입니다.

> **이 코드는 MoveIt을 사용하지 않습니다.** 관절 목표값을 컨트롤러에 그대로 보내므로
> 경로 계획도 충돌 검사도 없습니다. 2단계의 MoveIt과 대비해서 보십시오 —
> MoveIt은 "어디로 갈지"만 주면 경로를 만들어 주고, 이 코드는 관절값을 전부 직접 정해야
> 합니다. 그래서 `POSES`를 사람이 찾아 넣어야 하고, 팔이 물체를 치는지도 스스로 확인해야
> 합니다. MoveIt을 코드에서 호출하는 통합은 심화 과제입니다.
>
> 이 때문에 2단계 없이 3단계만 실행해도 팔은 움직입니다(컨트롤러만 있으면 됨).
> 다만 그건 MoveIt 실습을 건너뛴 것입니다.

---

## B. 실물 키트 (실습)

ROBOTIS 문서의 Bringup·MoveIt 절차와 동일합니다.
<https://docs.robotis.com/docs/systems/turtlebot3/manipulation/>

> `[TurtleBot3 SBC]` 명령은 로봇에 SSH로 접속해서 실행합니다.
> `[Remote PC]` 명령은 각각 별도 터미널에서 실행합니다.
>
> ```bash
> ssh ubuntu@<로봇 IP>
> ```

**[TurtleBot3 SBC]** — 로봇 구동

```bash
ros2 launch turtlebot3_manipulation_bringup hardware.launch.py
```

**[Remote PC] 터미널1** — MoveIt (플래닝 + RViz)

```bash
ros2 launch turtlebot3_manipulation_moveit_config moveit_core.launch.py
```

**[Remote PC] 터미널2** — 예제 실행

```bash
ros2 run ire_week11_moveit_skeleton pick_demo
```

팔을 손으로 조작해 관절값을 찾을 때는 위 터미널1의 `moveit_core`를 끄고 아래를 실행합니다.

**[Remote PC] 터미널1·2**

```bash
ros2 launch turtlebot3_manipulation_moveit_config servo.launch.py
```

```bash
ros2 run turtlebot3_manipulation_teleop turtlebot3_manipulation_teleop
```

> **실물에서는 `POSES` 값을 반드시 다시 잡아야 합니다.** 시뮬레이션 값 그대로 실행하면
> 팔이 책상이나 물체를 칠 수 있습니다. teleop으로 안전한 자세를 만든 뒤
> `ros2 topic echo /joint_states`로 관절값을 읽어 옮기십시오.
> 처음에는 그리퍼 아래에 아무것도 두지 말고 동작만 확인하는 것이 안전합니다.

## 선택 — 관절값 직접 찾기

`POSES`의 값은 예시이므로 자기 물체·자세에 맞게 바꿔야 합니다. 위 MoveIt Servo나
RViz로 팔을 원하는 자세로 옮긴 뒤, 그때의 관절값을 읽어 기록하십시오.

```bash
ros2 topic echo /joint_states
```

## 문제 해결

| 증상 | 원인 |
|---|---|
| 로그는 찍히는데 팔이 안 움직임 | `ros2 control list_controllers`에서 `arm_controller`가 `active`인지 확인 |
| `gripper` 단계에서 멈춤 | `gripper_controller` 미실행 — `wait_for_server()`에서 대기 중 |
| `moveit_gazebo.launch.py` 실행 시 `No such file or directory` | 해당 launch는 동작하지 않음 — 2단계 방식 사용 |
| Gazebo가 뜨지 않음 | 최상위 README 5절 참조 |
| 이전 실행이 남아 launch 실패 | `pkill -x gzserver; pkill -x gzclient` 후 재실행 |
