# ire_week10_nav_demo

RViz에서 **Nav2 Goal**을 클릭하는 것과 같은 일을 코드로 하는 예제입니다.
이 패키지는 목표를 보내는 노드 하나만 제공하며, Nav2 자체는 공식 패키지로 띄웁니다.

- `go_to_pose` — Nav2에 목표 좌표를 보내고 남은 거리를 출력한 뒤 결과를 확인

## A. Gazebo (수업)

터미널 3개를 사용합니다. 각 터미널에서 워크스페이스를 source한 상태여야 합니다.

### 1. 시뮬레이션

```bash
ros2 launch turtlebot3_manipulation_gazebo gazebo.launch.py
```

ROBOTIS 문서(`docs.robotis.com` → TurtleBot3 → Manipulation)와 동일한 명령이며,
팔이 장착된 실습 키트와 같은 로봇이 `turtlebot3_world`에 생성됩니다.
시작 위치는 `(-2.0, -0.5)`, 방향은 +x 입니다.

### 2. Nav2

```bash
ros2 launch turtlebot3_manipulation_navigation2 navigation2.launch.py use_sim_time:=true
```

RViz도 함께 실행됩니다.

**맵**은 이 패키지에 동봉된 `turtlebot3_world.yaml`이 기본값이라 따로 지정하지 않아도 됩니다.
9주차 SLAM에서 직접 만든 맵을 쓰려면 ROBOTIS 문서와 같이 인자로 넘깁니다.

```bash
ros2 launch turtlebot3_manipulation_navigation2 navigation2.launch.py \
  use_sim_time:=true map_yaml_file:=$HOME/map.yaml
```

> `use_sim_time:=true`는 시뮬레이션에서만 필요합니다. ROBOTIS 문서의 Navigation 절은
> 실물 하드웨어(`turtlebot3_manipulation_bringup hardware.launch.py`) 기준이라 이 인자가
> 없습니다. 패키지와 launch 파일 이름은 문서와 동일합니다.

### 3. 초기 위치 지정 (필수)

> ROBOTIS 문서의 Navigation 절에는 이 단계가 명시되어 있지 않지만, 생략하면
> 다음 단계가 진행되지 않습니다. 반드시 수행하십시오.

RViz 상단의 **2D Pose Estimate**를 누르고, 맵에서 로봇의 실제 위치를 클릭한 뒤
로봇이 바라보는 방향으로 드래그합니다. 시뮬레이션 시작 위치는 `(-2.0, -0.5)`이며
로봇은 +x 방향을 봅니다.

이 단계를 건너뛰면 AMCL이 측위하지 못해 `map → base_link` 변환이 만들어지지 않고,
`bt_navigator`가 `inactive`에 머뭅니다. 그 상태에서 4단계를 실행하면
`waitUntilNav2Active()`에서 멈춘 채 진행되지 않습니다.

지정이 잘 되었는지는 이렇게 확인합니다.

```bash
ros2 lifecycle get /bt_navigator      # active 여야 정상
ros2 topic echo /amcl_pose --once     # 지정한 위치 근처 좌표가 나와야 정상
```

### 4. 코드로 목표 전송

```bash
ros2 run ire_week10_nav_demo go_to_pose
```

```
[basic_navigator]: Nav2 is ready for use!
[basic_navigator]: Navigating to goal: 1.5 0.5...
남은 거리: 2.31 m
남은 거리: 1.88 m
...
```

RViz에서 전역 경로(초록 선)와 로봇의 이동을 함께 보면 이해가 빠릅니다.
RViz의 **Nav2 Goal**로 목표를 찍는 것과 같은 동작이며, 차이는 좌표를 코드에 적었다는 점뿐입니다.

---

## B. 실물 키트 (실습)

ROBOTIS 문서의 SLAM·Navigation 절차와 동일합니다.
<https://docs.robotis.com/docs/systems/turtlebot3/manipulation/>

> `[TurtleBot3 SBC]` 명령은 로봇에 SSH로 접속해서 실행합니다.
> `[Remote PC]` 명령은 각각 별도 터미널에서 실행합니다.
>
> ```bash
> ssh ubuntu@<로봇 IP>
> ```

### B-1. 맵 만들기 (SLAM)

**[TurtleBot3 SBC]** — 로봇 구동

```bash
ros2 launch turtlebot3_manipulation_bringup hardware.launch.py
```

**[Remote PC] 터미널1** — SLAM

```bash
ros2 launch turtlebot3_manipulation_cartographer cartographer.launch.py
```

**[Remote PC] 터미널2·3** — 로봇을 움직여 맵을 채웁니다

```bash
ros2 launch turtlebot3_manipulation_moveit_config servo.launch.py
```

```bash
ros2 run turtlebot3_manipulation_teleop turtlebot3_manipulation_teleop
```

**[Remote PC] 터미널4** — 맵 저장 (`~/map.yaml`, `~/map.pgm` 생성)

```bash
ros2 run nav2_map_server map_saver_cli -f ~/map
```

### B-2. 내비게이션

**[TurtleBot3 SBC]** — 로봇 구동

```bash
ros2 launch turtlebot3_manipulation_bringup hardware.launch.py
```

**[Remote PC] 터미널1** — Nav2 (B-1에서 만든 맵 사용)

```bash
ros2 launch turtlebot3_manipulation_navigation2 navigation2.launch.py \
  map_yaml_file:=$HOME/map.yaml
```

**[Remote PC] 터미널2** — A-3처럼 RViz에서 **2D Pose Estimate**로 초기 위치를 지정한 뒤
아래를 실행합니다.
목표 좌표는 자기가 만든 맵 기준이므로, RViz의 **Nav2 Goal**로 먼저 찍어 좌표를 확인한 뒤
코드에 옮기십시오.

```bash
ros2 run ire_week10_nav_demo go_to_pose
```

> 실물에서는 `use_sim_time` 인자를 넣지 않습니다. 시뮬레이션에서만 필요합니다.

## 알려진 문제

### 목표 근처에서 `TaskResult.FAILED`

로봇이 목표까지 이동한 뒤 **0.2~0.3 m를 남기고 정지**하며, 결과가 `TaskResult.FAILED`로
끝납니다. Nav2 로그에는 `[controller_server]: Failed to make progress`가 반복됩니다.

경로 계획과 주행 자체는 정상입니다(계획 실패 0회). 시작점에서 목표 부근까지
장애물을 피해 이동하는 과정은 RViz에서 그대로 관찰할 수 있으며, **마지막 정밀 정렬
구간만 완료되지 않습니다.**

아래 항목은 원인이 아닌 것으로 확인되었습니다. 같은 증상을 만나면 참고하십시오.

| 확인한 항목 | 결과 |
|---|---|
| 목표가 장애물에 가까움 (팽창 영역) | 여유 0.70 m 지점으로 옮겨도 동일 |
| 목표 방향(yaw) 정렬 실패 | 방향을 명시해도 동일 |
| 판정 기준이 빡빡함 | 위치 0.5 m·방향 무제한으로 완화해도 동일 |
| 팔 없는 로봇과의 조합 문제 | 두 로봇 모두 동일 증상 |

수업 목적인 "코드로 Nav2에 목표를 보내고 주행을 관찰한다"는 현재 상태로 달성됩니다.
결과값만 `FAILED`로 출력되므로, 실습 시 이 점을 미리 안내하십시오.

## 목표 좌표를 바꿀 때

`go_to_pose.py`의 `make_pose(nav, x, y)` 값을 고칩니다. `turtlebot3_world`는 기둥이
촘촘하므로 장애물에서 충분히 떨어진 지점을 고르십시오. 맵을 분석해 확인한 값입니다.

| 좌표 | 장애물까지 여유 |
|---|---|
| `(1.5, 0.5)` | 0.50 m (예제 기본값) |
| `(1.75, -0.55)` | 0.70 m |
| `(0.55, -1.80)` | 0.74 m |
| `(0.60, 1.75)` | 0.71 m |

RViz의 **Nav2 Goal**로 먼저 찍어 도달 여부를 확인한 뒤 코드에 옮기는 방법을 권합니다.

## 문제 해결

| 증상 | 원인 |
|---|---|
| `waitUntilNav2Active()`에서 멈춤 | 3단계 초기 위치 미지정 |
| 목표 근처에서 정지 후 `FAILED` | 위 "알려진 문제" 참조 |
| Gazebo가 뜨지 않음 | 최상위 README 5절(문제 해결) 참조 |
