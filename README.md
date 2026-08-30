# icir_ire_lecture

충남대학교 메카트로닉스공학과 **지능로봇실습**(Intelligent Robot Experiment, IRE) 강의 코드 저장소입니다. (iCIR Lab)

본 저장소는 공식 저장소(ROBOTIS TurtleBot3) 외에, 수업에 필요한 추가 자원(예제 노드, Gazebo 모델, 월드)을 제공합니다.

- 대상 장비: TurtleBot3 Waffle Pi + OpenMANIPULATOR-X
- 개발 환경: Ubuntu 22.04, ROS 2 Humble

---

## 1. 최초 설치

> 본 절은 ROS 2 Humble 설치가 2주차 강의자료에 따라 완료된 상태를 전제로 합니다.

### 1-1. apt 패키지 설치

아래 두 블록은 ROBOTIS e-Manual의 명령을 그대로 사용합니다.

**TurtleBot3 Quick Start (Remote PC)**

```bash
sudo apt install ros-humble-gazebo-*
sudo apt install ros-humble-cartographer
sudo apt install ros-humble-cartographer-ros
sudo apt install ros-humble-navigation2
sudo apt install ros-humble-nav2-bringup
sudo apt install python3-colcon-common-extensions
```

**OpenMANIPULATOR-X (Remote PC)**

```bash
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-gripper-controllers ros-humble-moveit*
```

> 매뉴얼 원문에는 `ros-humble-dynamixel-sdk`도 포함되어 있으나, 본 강의는 1-2에서
> DynamixelSDK를 소스로 clone하여 빌드하므로 제외합니다. apt 설치본과 중복되면
> 충돌이 발생할 수 있습니다.

**본 강의 추가 (매뉴얼에 없는 항목)**

```bash
sudo apt install -y \
  ros-humble-cv-bridge python3-opencv \
  ros-humble-image-transport-plugins \
  ros-humble-urdf-tutorial \
  ros-humble-joint-state-publisher-gui
```

| 패키지 | 사용 주차 | 출처 |
|---|---|---|
| gazebo-* | 8주차 이후 (시뮬레이션) | Quick Start |
| colcon-common-extensions | 빌드 도구 (전 주차) | Quick Start |
| cartographer, cartographer-ros | 9주차 (SLAM) | Quick Start |
| navigation2, nav2-bringup | 10주차 (Nav2) | Quick Start |
| ros2-control, ros2-controllers, gripper-controllers, moveit* | 11주차 (MoveIt2) | OpenMANIPULATOR-X |
| urdf-tutorial, joint-state-publisher-gui | 7주차 (URDF) | 본 강의 추가 |
| cv-bridge, python3-opencv, image-transport | 8주차 (비전. ArUco는 OpenCV에 포함되어 있으므로 별도 패키지 필요X) | 본 강의 추가 |

`cv-bridge`, `python3-opencv`는 각 패키지의 `package.xml`에 의존성으로 선언되어 있어
1-3의 `rosdep install` 단계에서도 설치됩니다.

### 1-2. 소스 저장소 clone

```bash
mkdir -p ~/ire_ws/src && cd ~/ire_ws/src

# 공식 저장소
git clone -b humble https://github.com/ROBOTIS-GIT/DynamixelSDK.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_msgs.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_manipulation.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_simulations.git
git clone -b humble https://github.com/ROBOTIS-GIT/turtlebot3_home_service_challenge.git

# 강의 저장소 (예제, 모델, 월드)
git clone https://github.com/iCIRLab/icir_ire_lecture.git
```

본 과목에서 SLAM, Nav2, teleop 설정은 매니퓰레이터가
장착된 본 실습 키트에 맞추어 조정된 `turtlebot3_manipulation_*` 패키지를 사용합니다. `turtlebot3` 저장소는 필수는 아니지만 참고용으로 활용할 수 있습니다.

### 1-2-1. 검증된 버전 (수업 기준 커밋)

본 수업의 모든 예제는 아래 커밋에서 동작이 검증되었습니다 (2026-08-18 기준, humble 브랜치).
평소에는 최신 humble 브랜치를 그대로 사용하고, **upstream 변경으로 실습이 동작하지 않는 경우에 한하여**
아래 명령으로 해당 버전으로 되돌립니다.

| 저장소 | 검증 커밋 |
|---|---|
| DynamixelSDK | `0d3403df2` |
| turtlebot3_msgs | `cdee60f76` |
| turtlebot3_manipulation | `814f140e8` |
| turtlebot3_simulations | `a35a56c8b` |
| turtlebot3_home_service_challenge | `9766cceb1` |

```bash
# 예시: turtlebot3_simulations를 검증 버전으로 고정
cd ~/ire_ws/src/turtlebot3_simulations
git checkout a35a56c8b        # 복귀: git checkout humble
```

### 1-3. 의존성 설치 및 빌드

```bash
cd ~/ire_ws
sudo rosdep init 2>/dev/null; rosdep update
rosdep install --from-paths src --ignore-src -y     # 누락된 의존성 자동 설치
colcon build --symlink-install
```

### 1-4. .bashrc 설정

```bash
echo 'source /usr/share/gazebo/setup.sh' >> ~/.bashrc
echo 'source ~/ire_ws/install/setup.bash' >> ~/.bashrc
echo 'export TURTLEBOT3_MODEL=waffle_pi' >> ~/.bashrc
echo 'export ROS_DOMAIN_ID=<본인 번호>' >> ~/.bashrc
source ~/.bashrc
```

### 1-5. 설치 확인

```bash
ros2 pkg list | grep ire_          # ire_ 패키지 목록이 출력되면 정상
ros2 launch ire_week04_service_launch circle.launch.py   # turtlesim 창이 실행되면 정상
```

---

## 2. 주차별 수행 절차

```bash
cd ~/ire_ws/src/icir_ire_lecture && git pull        # 최신 코드 반영
cd ~/ire_ws && colcon build --symlink-install --packages-select <해당 주차 패키지>
```

## 3. 주차별 패키지 구성

| 주차 | 패키지 | 내용 | 실행 |
|---|---|---|---|
| 3 | `ire_week03_pubsub` | 기본 pub/sub 예제 | `ros2 run ire_week03_pubsub talker` → `ros2 run ire_week03_pubsub listener` |
| 4 | `ire_week04_service_launch` | 서비스 기반 원 그리기 제어, launch, 파이썬 클라이언트 | `ros2 launch ire_week04_service_launch circle.launch.py` → `ros2 run ire_week04_service_launch start_stop_client` |
| 7 | `ire_week07_urdf` | URDF 표시 launch 및 예제 URDF | `ros2 launch ire_week07_urdf display.launch.py` |
| 8 | `ire_week08_vision` | 적색 기둥 색 검출(예제) · ArUco 월드(미션) · 마커 생성 | (8주차 [README](ire_week08_vision/README.md) 참고) |
| 10 | `ire_week10_nav_demo` | 코드로 Nav2 목표 전송 | (10주차 [README](ire_week10_nav_demo/README.md) 참고) |
| 11 | `ire_week11_moveit_skeleton` | MoveIt2 플래닝 · Pick & Place 골격 (미션 #4 시작점) | (11주차 [README](ire_week11_moveit_skeleton/README.md) 참고) |
| 12 | `ire_week12_ai_demo` | YOLO · SAM 2 · Llama · Whisper — **⚠ 수업 전 주에 설치 필요** | (12주차 [README](ire_week12_ai_demo/README.md) 참고) |
| 공용 | `ire_assets` | Gazebo 모델·미로 월드·RViz 설정 | (공용 자산 [README](ire_assets/README.md) 참고) |
| 참고 | `ire_appendix_cpp` | 3주차 Appendix B1~B3의 C++(ament_cmake) 버전 | `ros2 run ire_appendix_cpp practice` |

8주차 이후는 시뮬레이션과 실물 키트를 함께 사용하며, 여러 터미널을 띄워야 하므로
실행 절차를 각 패키지 README에 두었습니다. 시뮬레이션 로봇은
`turtlebot3_manipulation_gazebo`가 띄우는 **팔이 장착된 실습 키트와 같은 구성**이고,
실물 키트 절차는 ROBOTIS 문서를 따릅니다.

> `ire_appendix_cpp`는 강의에서 다루지 않는 참고 자료입니다. C++ 패키지는 `--symlink-install`의
> 즉시 반영 대상이 아니므로, 코드를 수정한 경우 **매번 `colcon build`를 다시 수행**해야 합니다.

## 4. 홈서비스 챌린지 (시뮬레이션)

ROBOTIS가 제공하는 완성 예시입니다. **ArUco 검출 + Nav2 주행 + 팔 제어**를 하나로
묶은 것으로, 8·10·11주차 내용이 합쳐진 형태입니다. 기말 프로젝트 참고용으로
돌려 보십시오.

```bash
# 터미널1 — 챌린지 월드
ros2 launch turtlebot3_manipulation_gazebo turtlebot3_home_service_challenge.launch.py

# 터미널2 — Nav2
ros2 launch turtlebot3_home_service_challenge_tools navigation2.launch.py use_sim:=true

# RViz 에서 2D Pose Estimate 로 초기 위치 지정

# 터미널3 — 미션 제어 (ArUco 주차 · 팔)
ros2 launch turtlebot3_home_service_challenge_core core_node.launch.py
```

```bash
# 시나리오 실행 (room1 ~ room4, config/scenario.yaml 에 정의)
ros2 topic pub -1 /scenario_selection std_msgs/msg/String "{data: 'room1'}"

# 단계별로 직접
ros2 topic pub -1 /target_marker_id std_msgs/msg/Int32 "{data: 1}"
ros2 topic pub -1 /manipulator_control std_msgs/msg/String "{data: 'pick_target'}"
```

> **`use_sim:=true`를 빠뜨리면 로봇이 목표 근처만 맴돕니다.** Nav2가 시뮬레이션
> 시계(`/clock`) 대신 시스템 시계를 써서 TF 시각이 어긋나기 때문입니다.
> ROBOTIS 문서에는 이 인자가 빠져 있습니다.

구조는 코어 노드가 지휘하는 형태입니다. 시나리오를 받으면 ArUco 주차 → 팔 제어 →
다음 목표 순으로 각 노드에 명령을 내리고, 완료 신호를 받아 진행합니다.

- 문서: <https://docs.robotis.com/docs/systems/turtlebot3/manipulation/home_service_challenge>

## 5. 문제 해결

### Gazebo가 뜨지 않고 `gzserver ... exit code 255`

이전 실행의 gzserver가 종료되지 않고 남아 통신 포트(11345)를 점유한 경우입니다.
Gazebo는 Ctrl+C로 launch를 종료해도 gzserver가 남는 경우가 있습니다.

```bash
pgrep -a gzserver || echo "깨끗함"      # 남아 있는지 확인
pkill -f gzserver; pkill -f gzclient    # 정리
```

`깨끗함`이 출력되면 남은 프로세스가 없는 상태입니다. 프로세스 정보가 출력되면
아직 살아 있는 것이므로 `pkill`로 정리한 뒤 다시 실행합니다.

### Gazebo 창(gzclient)만 죽음 — `exit code -6`

로그에 다음 메시지가 함께 출력되는 경우입니다.

```
gzclient: shared_ptr.hpp:728: [T = gazebo::rendering::Camera] Assertion `px != 0' failed.
```

1-4의 `source /usr/share/gazebo/setup.sh`가 `.bashrc`에 없는 경우입니다.
이 줄이 없으면 `gzclient.launch.py`가 `GAZEBO_RESOURCE_PATH`를 ROS 패키지 경로로만
설정하여 Gazebo 기본 리소스 경로가 누락되고, 렌더링 초기화가 실패하여 카메라 객체가
생성되지 않습니다. gzserver(시뮬레이션 본체)는 정상 동작하므로 화면만 뜨지 않는 것이
특징입니다.

```bash
grep gazebo/setup.sh ~/.bashrc || echo 'source /usr/share/gazebo/setup.sh' >> ~/.bashrc
source ~/.bashrc
```

### `PackageNotFoundError: turtlebot3_gazebo`

1-2의 공식 저장소 clone 또는 빌드가 완료되지 않은 경우입니다.
`turtlebot3_simulations`를 clone한 뒤 다시 빌드합니다.

### 로봇이 생성되지 않거나 모델을 찾지 못함

`TURTLEBOT3_MODEL` 환경변수가 설정되지 않은 경우입니다 (1-4 참조).

```bash
echo $TURTLEBOT3_MODEL          # waffle_pi 가 출력되어야 정상
export TURTLEBOT3_MODEL=waffle_pi
```

### `import cv2` 실패 — `numpy.core.multiarray failed to import`

apt로 설치된 `python3-opencv`는 NumPy 1.x에 맞추어 빌드되어 있어 NumPy 2.x에서는
동작하지 않습니다. 12주차 사전 설치(`pip install ultralytics`)가 NumPy 2.x를 함께
설치하면 8주차 비전 예제가 이 오류로 실행되지 않습니다.

```bash
python3 -c "import numpy; print(numpy.__version__)"   # 2.x 이면 아래 실행
pip install --user "numpy<2"
```

### 패키지가 `ros2 pkg list`에 보이지 않음

빌드 후 워크스페이스를 source하지 않은 경우입니다.

```bash
source ~/ire_ws/install/setup.bash
```

## 6. 라이선스

본 저장소의 패키지는 Apache-2.0 라이선스를 따릅니다.
