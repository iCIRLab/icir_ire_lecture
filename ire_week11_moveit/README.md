# ire_week11_moveit

미션 #4 (Pick & Place)의 출발점입니다. 같은 팔을 세 가지로 움직여 봅니다.

| | 무엇으로 | MoveIt |
|---|---|---|
| RViz MotionPlanning 패널 | 마우스 (GUI) | 사용 |
| 코드로 팔 움직이기 (`pick_demo`) | 코드 — 관절값을 컨트롤러에 직접 전송 | **사용 안 함** |
| 코드로 MoveIt 돌리기 (`moveit_py_demo`) | 코드 — MoveIt API(moveit_py) 호출, 6단계 예제 | 사용 (**RViz에서 하던 일을 코드로**) |

- POSES의 관절값은 예시: teleop으로 팔을 움직이며 `/joint_states`를 보고 자기 값으로 교체
- 학생 몫: 지정 pick–place 시퀀스 설계

시뮬레이션(A)과 실물(B) 모두 **RViz로 MoveIt 체험 → 코드로 팔 움직이기 → 코드로 MoveIt 돌리기** 순서로 진행합니다.

## 0. 준비 — moveit_py 설치 확인 (코드로 MoveIt 돌리기용, 처음 한 번)

moveit_py(MoveIt의 파이썬 API)는 MoveIt 2.5.10(**2026년 9월 릴리스, apt 배포는 10월**)에서 Humble용으로 처음 나온
라이브러리입니다. 학기 초 최초 설치(`ros-humble-moveit*`) 때는 없었으므로, 먼저 설치되어 있는지 확인합니다.

```bash
python3 -c "from moveit.planning import MoveItPy; print('moveit_py OK')"
```

`moveit_py OK`가 나오면 이 절은 건너뜁니다. `No module named 'moveit'` 또는
`libmoveit_...so.2.5.10: cannot open shared object file`이 나오면 아래를 실행합니다.

```bash
sudo apt update
sudo apt install ros-humble-moveit-py
sudo apt install --only-upgrade 'ros-humble-moveit*'   # 기존 MoveIt도 2.5.10으로 (moveit 패키지만 바뀜)
python3 -c "from moveit.planning import MoveItPy; print('moveit_py OK')"
```

> **두 번째 줄만 하면 안 됩니다.** moveit_py 2.5.10은 MoveIt 2.5.10 라이브러리가 필요한데,
> apt가 기존 MoveIt(2.5.9)을 자동으로 올려 주지 않아 `...so.2.5.10` 오류가 납니다.
>
> **`sudo apt upgrade`(전체 업그레이드)는 하지 마십시오.** MoveIt과 관계없는 시스템 패키지
> 수백 개(커널, ROS 전체 등)가 함께 바뀝니다. 위 세 번째 줄은 `ros-humble-moveit*`만 올립니다.

> 12주차 conda 환경(`ire_ai`)이 켜진 상태에서는 실행하지 마십시오(`conda deactivate`).
> 11주차는 시스템 파이썬 + ROS 환경에서 실행합니다.

## A. Gazebo (수업)

1절의 Gazebo는 A절 내내 켜 둡니다. 2~4절의 명령은 그 상태에서 각각 새 터미널에서 실행합니다.

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

### 2. RViz로 MoveIt 돌리기 (MoveIt2)

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
ros2 launch turtlebot3_manipulation_moveit_config servo.launch.py
```

```bash
ros2 run turtlebot3_manipulation_teleop turtlebot3_manipulation_teleop
```

### 3. 코드로 팔 움직이기 — `pick_demo` (MoveIt 없이 관절값 직접)

```bash
ros2 run ire_week11_moveit pick_demo
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
> 합니다. MoveIt을 코드에서 돌리는 방법은 다음 4절(코드로 MoveIt 돌리기)입니다.
>
> 이 때문에 2단계 없이 3단계만 실행해도 팔은 움직입니다(컨트롤러만 있으면 됨).
> 다만 그건 MoveIt 실습을 건너뛴 것입니다.

### 4. 코드로 MoveIt 돌리기 — `moveit_py_demo`

2절에서 RViz 패널로 하던 일(목표 지정 → *Plan* → *Execute*)을 **코드로** 합니다.
3절(`pick_demo`)과 달리 경로 계획·충돌 검사를 MoveIt이 해 줍니다. 먼저 0절(moveit_py 설치 확인)을 마쳐야 합니다.

| RViz 패널에서 | `moveit_py_demo` 코드에서 |
|---|---|
| Goal State에서 `home` 선택 | `arm.set_goal_state(configuration_name='home')` |
| 인터랙티브 마커로 목표 자세 지정 | `arm.set_goal_state(robot_state=...)` 또는 `pose_stamped_msg=...` |
| *Plan* | `arm.plan()` |
| *Execute* | `robot.execute('arm', result.trajectory, blocking=True)` |
| Scene Objects에 상자 추가 | `scene.apply_collision_object(...)` |

| 파일 | 내용 |
|---|---|
| `kit_moveit_config.py` | 키트(`turtlebot3_manipulation_moveit_config`) 설정 파일을 읽어 `MoveItPy(config_dict=...)`에 넘길 dict를 만든다. 새 MoveIt config·launch·yaml이 필요 없다 |
| `moveit_py_demo.py` | 6단계 예제 |

**2절의 `moveit_core`(move_group + RViz)는 띄우지 않습니다.**
RViz 패널은 `move_group`이라는 플래닝 서버에 요청하는 클라이언트이고, moveit_py는 그 플래닝 기능을
**자기 프로세스 안에서 직접** 돌리기 때문입니다(설정은 `kit_moveit_config.py`가 넘겨 줌).

#### ① RViz 띄우기 (선택)

로봇과 6단계 충돌 상자를 보려면 데모보다 먼저 띄웁니다.

```bash
ros2 launch ire_week11_moveit moveit_py_rviz.launch.py
```

`moveit_core`가 아니라 **RViz만** 띄웁니다. moveit_py가 내보내는 planning scene
(`/moveit_cpp/monitored_planning_scene`)을 그대로 그리므로, 6단계에서 넣은 상자(초록)와
팔이 상자를 피해 가는 모습을 볼 수 있습니다.

- `moveit_py_demo`를 실행하기 전에는 로봇이 **관절 0 자세**로 보이고 PlanningScene 항목이 주황색입니다.
  아직 받은 scene이 없어서이며 정상입니다. 데모가 시작되면 실제 자세로 바뀌고, 실행 중일 때만 갱신됩니다.
- `rviz2 -d ...week11_moveit_py.rviz`로 직접 열면 로봇이 안 보입니다. MoveIt RViz 플러그인은 로봇 모델(URDF·SRDF)을
  RViz 노드 파라미터에서 읽는데, 이를 넘겨 주는 것이 이 launch 파일입니다.

#### ② 데모 실행

```bash
ros2 run ire_week11_moveit moveit_py_demo --sim --step all
```

- `--step 1` ~ `--step 6` 으로 한 단계만 실행할 수 있습니다 (기본 `all`).
- `--sim` 은 `use_sim_time=True` 입니다. Gazebo에서는 반드시 붙입니다.

#### 단계별 기대 결과

| 단계 | 내용 | 기대 결과 |
|---|---|---|
| 1 | named target `home` | 계획·실행 성공. SRDF `home` = `pick_demo` `home` = `[0, -1.0, 0.7, 0.3]` |
| 2 | 관절 목표 `approach` `[0, 0.4, 0.2, -0.6]` | 성공. 말단(FK) ≈ (0.220, 0.000, 0.216) m, 방향 q = (0, 0, 0, 1) (회전 없음) |
| 3a | pose 목표 (FK와 같은 방향) | 계획 성공 (실행은 안 함) |
| 3b | pose 목표 (같은 위치, yaw 45°) | **계획 실패 — 정상.** 약 4초 뒤 `Unable to sample any valid states for goal tree` |
| 4 | 위치만 목표 (반지름 5 mm) | 성공. 손목 각 j2+j3+j4가 실행마다 다름 (2단계는 0) |
| 5 | 그리퍼 open / close | 성공 (`gripper_controller/gripper_cmd` 액션) |
| 6 | 상자 회피 (home → approach) | 관절 직선 경로는 21개 지점 중 다수가 충돌. MoveIt 경로는 상자를 돌아가며 경로상 충돌 0. 경로 모양·점 수·말단 z 최저값은 실행마다 다름 |

**왜 3b는 실패하나?** OpenMANIPULATOR-X는 4자유도입니다. 말단의 yaw(위에서 본 방향)는
joint1 하나가 정하고, 위치가 y = 0이면 yaw도 0이어야 합니다. 그래서 "이 위치에서 45° 돌린 방향"은
어떤 관절값으로도 만들 수 없습니다. 위치 + 방향(6개 값)을 4개 관절로 모두 맞출 수는 없으므로,
4단계처럼 **위치만** 주는 것이 이 팔의 일반적인 사용법입니다.

**왜 4단계 손목 각이 매번 다른가?** 위치(3개 값)만 정하면 관절 4개 중 1개가 남습니다.
남은 자유도(손목 pitch)는 IK가 정하므로, 집는 방향이 중요하면 관절 목표나 도달 가능한 pose를 써야 합니다.

#### 알아 둘 것

- **속도:** 키트 launch는 `joint_limits.yaml`을 읽지 않습니다. 스케일을 주지 않으면 최대 속도(1.0)로
  움직이므로 `kit_moveit_config.build()`에서 0.1로 지정했습니다.
  `Joint acceleration limits are not defined. Using the default 1 rad/s^2` 경고는 이 때문이며 무시해도 됩니다.
- **6단계 상자는 `moveit_core`(RViz MotionPlanning)에는 보이지 않습니다.** 상자는 moveit_py의 planning scene에만
  들어가고, `moveit_core`의 RViz는 `move_group`의 scene을 보기 때문입니다. 위 ①(RViz 띄우기)의 `moveit_py_rviz.launch.py`로 보십시오.
- **온라인 튜토리얼(Rolling)과 API가 다릅니다.** Humble은 `robot.execute(group_name, trajectory, blocking=True)`,
  `plan(parameters=...)` 입니다.
- **`RobotState(model)`은 관절값을 초기화하지 않습니다.** 만든 직후 `set_to_default_values()`를 부르거나
  `copy.deepcopy(scene.current_state)`로 복사해서 씁니다. 빠뜨리면 충돌 검사에서 간헐적으로 segfault가 납니다.
- 무시해도 되는 로그: `Using position only ik`(정상), `No 3D sensor plugin(s) defined for octomap updates`,
  `end_effector_link has visual geometry but no collision geometry`.
- `moveit_core.launch.py`를 함께 띄워도 충돌하지는 않습니다(moveit_py는 `/moveit_cpp/...` 토픽 사용). 하지만 필요 없습니다.

### 5. 비교 — `pick_demo` vs `moveit_py_demo`

| | `pick_demo` (관절 직접) | `moveit_py_demo` (MoveIt 계획) |
|---|---|---|
| 목표 | 관절값 4개 | 이름(`home`), 관절값, pose, 위치만 |
| 경로 | 시작→목표 관절 직선 | OMPL이 계획 (실행마다 다를 수 있음) |
| 충돌 검사 | 없음 | 자기 충돌 + planning scene의 물체 |
| 속도 | `time_from_start`로 직접 | 속도·가속도 스케일 (0.1) |

---

## B. 실물 키트 (실습)

ROBOTIS 문서의 Bringup·MoveIt 절차와 동일합니다.
<https://docs.robotis.com/docs/systems/turtlebot3/manipulation/>

> `[TurtleBot3 SBC]` 명령은 로봇에 SSH로 접속해서 실행합니다.
> `[Remote PC]` 명령은 각각 새 터미널에서 실행합니다.
>
> ```bash
> ssh ubuntu@<로봇 IP>
> ```

**[TurtleBot3 SBC]** — 로봇 구동

```bash
ros2 launch turtlebot3_manipulation_bringup hardware.launch.py
```

SBC bringup은 B절 내내 켜 둡니다(컨트롤러가 여기서 뜸). 1~3절의 명령은 그 상태에서 각각 새 터미널에서 실행합니다.

### 1. RViz로 MoveIt 돌리기

**[Remote PC]** — MoveIt (플래닝 서버 `move_group` + RViz)

```bash
ros2 launch turtlebot3_manipulation_moveit_config moveit_core.launch.py
```

A-2절과 같이 MotionPlanning 패널에서 *Plan* → *Execute* 합니다.

### 2. 코드로 팔 움직이기 — `pick_demo` (MoveIt 없이 관절값 직접)

`moveit_core`는 필요 없습니다(켜져 있어도 상관없음).

**[Remote PC]**

```bash
ros2 run ire_week11_moveit pick_demo
```

팔을 손으로 조작해 관절값을 찾을 때는 `moveit_core`를 끄고 아래를 실행합니다.

**[Remote PC]**

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

### 3. 코드로 MoveIt 돌리기 — `moveit_py_demo`

먼저 0절(moveit_py 설치 확인)을 마쳐야 합니다. `moveit_core`는 띄우지 않습니다(A-4절 설명과 같음).

**[Remote PC]** — ① RViz 띄우기 (선택)

```bash
ros2 launch ire_week11_moveit moveit_py_rviz.launch.py use_sim_time:=false
```

**[Remote PC]** — ② 데모 실행: 한 단계씩 (`--sim` 없이)

```bash
ros2 run ire_week11_moveit moveit_py_demo --step 1
```

- 단계별로 하나씩 실행하고(`--step 1` → `--step 2` …), 그리퍼 아래와 팔 주변을 비웁니다.
- 6단계 상자는 **가상 물체**입니다(실물에는 없음). 팔은 이 상자를 피해 돌아가고, 우회 경로는 실행마다 다릅니다.
  실물에서는 6단계를 생략하거나, 팔 주변 작업 공간 전체를 비우고 실행합니다.
- 기대 결과는 A-4절 표와 같습니다.

---

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
| Gazebo가 뜨지 않음 | 최상위 README 5절(문제 해결) 참조 |
| 이전 실행이 남아 launch 실패 | `pkill -x gzserver; pkill -x gzclient` 후 재실행 |
| `ModuleNotFoundError: No module named 'moveit'` | moveit_py 미설치(0절) 또는 conda 환경이 켜져 있음 |
| `libmoveit_planning_scene.so.2.5.10: cannot open shared object file` | 기존 MoveIt이 2.5.9 — 0절의 `--only-upgrade` 줄 실행 |
| `moveit_py_demo`가 안 움직이고 시간 관련 오류 | Gazebo에서 `--sim`을 빠뜨림 |
