# ire_week08_vision

카메라 영상에서 물체를 찾는 두 가지 방법을 다룹니다.

- `color_detect` — HSV 색 검출로 빨간 기둥을 찾아 `/red_pillar/exists`(Bool) 발행 **(완성 예제)**
- `aruco_detect` — ArUco 마커 검출 + pose 추정, `/aruco/pose`·`/aruco/image` 발행 **(완성 예제)**
- `generate_aruco` — ArUco 마커 이미지 생성 (화면 표시·인쇄용)
- `aruco_world.launch.py` — ArUco 박스가 놓인 월드 (검출 노드는 따로 실행)
- `config/pi_camera_320x240.yaml` — 실물 Pi 카메라 캘리브레이션 파일 (조교 제공)

수업에서는 Gazebo로 원리를 확인하고, 실물 키트로 같은 코드를 검증하는 순서를 권장합니다.

---

## A. Gazebo (수업)

### A-1. 빨간 기둥 검출 — 완성 예제

```bash
ros2 launch ire_week08_vision red_pillar_world.launch.py
```

월드 + 빨간 기둥 + `color_detect`가 한 번에 뜹니다. 창 두 개가 함께 열립니다.

| 창 | 내용 |
|---|---|
| `camera` | 카메라 원본 + 검출 영역 초록 윤곽선 |
| `red_mask` | HSV 판정 결과 (흰색 = 빨강으로 판정된 픽셀) |

터미널에는 상태가 바뀔 때만 로그가 찍힙니다.

```
[color_detect]: RED PILLAR: PRESENT
```

파라미터를 바꾸면 `red_mask`가 즉시 달라집니다. 재빌드가 필요 없습니다.

```bash
ros2 topic echo /red_pillar/exists                        # 검출 결과 구독
ros2 param set /color_detect min_area 5000                # 판정을 까다롭게
ros2 param set /color_detect hsv1_low "[0, 200, 150]"     # 마스크 자체를 줄임
ros2 param set /color_detect show_windows false           # 창 닫기
```

### A-2. ArUco 마커

```bash
# 터미널1
ros2 launch ire_week08_vision aruco_world.launch.py
# 터미널2
ros2 run ire_week08_vision aruco_detect
```

박스(id 0)는 로봇 정면 약 1.0 m에 놓이므로 이동 없이 바로 보입니다.
`aruco_detect`의 기본값이 Gazebo 기준(`/pi_camera/...`, `marker_size` 0.117)이므로 인자 없이 실행합니다.

- `0.117`은 검은 마커의 실제 한 변 길이입니다. 박스는 0.15 m지만 텍스처의 흰 여백을 빼면 0.117 m입니다.
- 카메라 행렬 K와 왜곡계수 D는 `/pi_camera/camera_info`에서 받습니다.

로그에 `ArUco ids: [0]`이 찍히면 검출된 것입니다. pose는 토픽으로 확인합니다.

```bash
ros2 topic echo /aruco/pose          # position.z ≈ 마커까지 거리 [m]
```

**RViz2로 보기**

```bash
# 터미널3
rviz2
```

1. Fixed Frame = `base_footprint`
2. Add → RobotModel → Description Topic을 `/robot_description`으로
3. Add → By topic → `/aruco/image` (Image)
4. Add → By topic → `/aruco/pose` (Pose) → Shape를 `Axes`로

`/aruco/pose`는 카메라 광학 프레임 `camera_rgb_optical_frame`(z 앞·x 오른쪽·y 아래) 기준입니다.
이 프레임은 URDF에 있어 TF로 로봇에 붙어 있으므로, 마커 축이 로봇 앞 실제 위치에 그려집니다.

노드 구조는 구독(영상·camera_info) → `cv_bridge` → `detectMarkers` → `estimatePoseSingleMarkers` → 발행입니다.
`color_detect`와 뼈대가 같습니다.

### A-3. 마커 이미지 생성

```bash
ros2 run ire_week08_vision generate_aruco     # aruco_0.png ~ aruco_9.png
```

실습 때 조원 노트북이나 스마트폰 화면에 띄워 사용합니다 (인쇄도 가능).
마커 크기는 화면 위 검은 사각형을 자로 재서 `marker_size`에 넣습니다. 잰 뒤에는 화면을 확대·축소하지 마십시오.

마커 둘레의 흰 여백은 검출에 반드시 필요합니다. 화면에 띄울 때도 여백이 보이게 하고,
인쇄한 경우 검은 테두리까지 바짝 자르지 마십시오.

---

## B. 실물 키트 (실습)

Gazebo에서 확인한 코드를 실제 로봇에서 그대로 돌려봅니다.
하드웨어 준비(OpenCR 펌웨어, SBC 설정)는 ROBOTIS 문서를 따르십시오.
<https://docs.robotis.com/docs/systems/turtlebot3/manipulation/>

> `[TurtleBot3 SBC]` 명령은 로봇에 SSH로 접속해서 실행합니다.
> `[Remote PC]` 명령은 각각 별도 터미널에서 실행합니다.
>
> ```bash
> ssh ubuntu@<로봇 IP>
> ```

실습은 세 단계로 진행합니다.

| 단계 | 내용 |
|---|---|
| 1단계 | 로봇 SBC에 카메라 설치 → 캘리브레이션 파일 복사 → 카메라 노드 → 영상 확인 |
| 2단계 | 예제 노드 `aruco_detect` 실행 → ID(로그)·pose(토픽) 확인 → RViz2 표시 |
| 3단계 | 카메라 토픽(image_raw + camera_info)을 rosbag으로 기록 → 카메라 끄고 재생 → 같은 결과 |

### B-1. [1단계] 로봇 SBC에 카메라 설치 — 처음 한 번 (실습 시간에 진행)

ROBOTIS e-Manual › TurtleBot3 › SBC Setup › Raspberry Pi Camera › 방법 1(camera-ros)을 따르되,
마지막 `camera.launch.py` 줄은 하지 않습니다(`turtlebot3` 패키지를 쓰지 않음). libcamera 빌드가 오래 걸립니다.

```bash
# [TurtleBot3 SBC]
# ① 빌드 도구 + camera_ros
sudo apt update
sudo apt install -y python3-pip git python3-jinja2 libboost-dev libgnutls28-dev openssl libtiff-dev \
    pybind11-dev qtbase5-dev libqt5core5a libqt5widgets5 meson cmake python3-yaml python3-ply \
    libglib2.0-dev libgstreamer-plugins-base1.0-dev
sudo apt install ros-humble-camera-ros
# ② 라즈베리파이용 libcamera 빌드·설치 — 오래 걸린다
git clone -b v0.5.2 https://github.com/raspberrypi/libcamera.git && cd libcamera
meson setup build --buildtype=release -Dpipelines=rpi/vc4,rpi/pisp -Dipas=rpi/vc4,rpi/pisp \
    -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled \
    -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled
ninja -C build -j 1 && sudo ninja -C build install -j 1 && sudo ldconfig
# ③ 라이브러리 경로 — .bashrc 맨 끝(ROS source 줄보다 아래)에 추가
echo 'export LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH' >> ~/.bashrc
```

설치 확인

```bash
# [TurtleBot3 SBC] (새 터미널)
ros2 run camera_ros camera_node --ros-args -p format:='RGB888' -p width:=320 -p height:=240
# [Remote PC]
ros2 topic hz /camera/image_raw        # 영상이 들어오면 준비 끝
```

> `"no cameras available"`이면 `LD_LIBRARY_PATH` 줄과 카메라 케이블을 확인합니다.
> `/boot/firmware/config.txt`에 `start_x=1`·`camera_auto_detect=0`(레거시 설정)이 있으면 주석 처리합니다.

### B-2. [1단계] 캘리브레이션 파일 복사 → 브링업 → 카메라 노드 → 확인

```bash
# [Remote PC] 처음 한 번 — repo의 캘리브레이션 파일을 로봇으로 복사 (git pull 후)
ssh ubuntu@<로봇 IP> "mkdir -p ~/.ros/camera_info"
scp ~/ire_ws/src/icir_ire_lecture/ire_week08_vision/config/pi_camera_320x240.yaml \
      ubuntu@<로봇 IP>:~/.ros/camera_info/
```

```bash
# [TurtleBot3 SBC] 터미널1 — 브링업 (카메라는 여기에 포함되지 않는다)
ros2 launch turtlebot3_manipulation_bringup hardware.launch.py
```

```bash
# [TurtleBot3 SBC] 터미널2 — Pi 카메라 노드 (캘리브레이션 파일 경로를 함께 지정)
ros2 run camera_ros camera_node --ros-args \
    -p format:='RGB888' -p width:=320 -p height:=240 \
    -p camera_info_url:=file:///home/ubuntu/.ros/camera_info/pi_camera_320x240.yaml
```

```bash
# [Remote PC] 토픽을 확인하고 눈으로 본다
ros2 topic list | grep camera              # /camera/image_raw, /camera/camera_info
ros2 run rqt_image_view rqt_image_view
ros2 topic echo /camera/camera_info --once  # k가 0이 아니면 캘리브레이션 적용 OK
```

기본 해상도는 640이지만 320×240 으로 낮췄습니다. 라즈베리파이 부담과 무선 전송량이
줄고, ArUco 검출에도 충분하며, 캘리브레이션 파일도 이 해상도 전용입니다.

> 시뮬레이션과 토픽 이름이 다릅니다. Gazebo 로봇은 `/pi_camera/image_raw`·`/pi_camera/camera_info`,
> 실물은 위와 같이 실행하면 `/camera/image_raw`·`/camera/camera_info` 입니다.
> `ros2 topic list | grep camera` 로 확인하십시오.

### B-3. [2단계] ArUco 검출 — `aruco_detect`

```bash
# [Remote PC]
ros2 run ire_week08_vision aruco_detect --ros-args \
    -p image_topic:=/camera/image_raw -p camera_info_topic:=/camera/camera_info \
    -p marker_size:=0.05     # 화면 위 검은 사각형을 자로 잰 값 [m]
```

마커 PNG는 조원 노트북이나 스마트폰 화면에 띄우고, 내 노트북에서 `aruco_detect`·RViz2로 확인합니다.
로그의 `ArUco ids`와 `ros2 topic echo /aruco/pose`로 확인합니다. RViz2는 A-2와 같은 설정입니다.
마커는 카메라에서 0.3~0.5 m 거리에 둡니다. 더 멀면 영상 속 마커가 작아져 자세(각도) 오차가 커집니다.

### B-4. [3단계] rosbag으로 재현

```bash
# [Remote PC] 카메라 노드가 도는 상태에서 10초 정도 기록 (Ctrl+C로 종료)
ros2 bag record /camera/image_raw /camera/camera_info -o aruco_bag
# 카메라 노드만 끈 뒤 재생 — 브링업·aruco_detect·RViz2는 그대로 둔다
ros2 bag play aruco_bag
```

- `camera_info`도 반드시 같이 기록합니다. 빠지면 재생 때 K가 없어 pose가 나오지 않습니다.
- 브링업은 켜 둡니다. 카메라 → 로봇 TF가 브링업에서 나오므로, 끄면 RViz2에 Pose가 표시되지 않습니다.
- 영상 토픽은 용량이 큽니다 (320×240·30 fps ≈ 1분 400 MB). 필요한 구간만 짧게 기록합니다.

재생만으로 같은 ID·pose가 나오고 RViz2에 표시되면 완성입니다.

### B-5. (참고) 실물에서 색 검출 — 실습 필수 아님

```bash
# [Remote PC]
ros2 run ire_week08_vision color_detect --ros-args \
  -p image_topic:=/camera/image_raw -p show_windows:=true
```

> **카메라 토픽 이름을 반드시 확인하십시오.** 노드 기본값은 Gazebo 실습 키트 기준인
> `/pi_camera/image_raw`입니다. 실물 로봇은 카메라 구동 방식에 따라 이름이 다를 수
> 있으므로 `ros2 topic list | grep image`로 확인한 뒤 `image_topic` 파라미터로 지정합니다.

실제 조명에서는 색이 달라지므로 HSV 범위를 다시 맞춰야 합니다. (실습은 ArUco만 다룹니다)
`red_mask` 창을 보면서 `hsv1_low`/`hsv1_high`를 조정합니다.

```bash
ros2 param set /color_detect hsv1_low "[0, 120, 80]"
ros2 param set /color_detect hsv1_high "[10, 255, 255]"
ros2 param set /color_detect min_area 300
```

## 문제 해결

| 증상 | 원인 |
|---|---|
| `listening:` 만 찍히고 검출 로그가 없음 | 카메라 토픽 불일치 — `ros2 topic list \| grep image`로 확인 |
| 창이 뜨지 않음 | `show_windows` 파라미터가 `false` |
| ArUco가 검출되지 않음 | 마커 흰 여백 부족, 조명·화면 반사, 화면 밝기, 거리가 너무 멂 |
| `aruco_detect`가 `camera_info 대기 중`만 출력 | `camera_info_topic` 이름 불일치 — `ros2 topic list \| grep camera_info` |
| `camera_info의 K가 전부 0` 경고 | 캘리브레이션 파일 미적용 — B-2의 scp와 `camera_info_url` 경로 확인 |
| `no cameras available` | B-1 주의 참조 (`LD_LIBRARY_PATH`, 케이블, `config.txt`) |
| RViz2에 Pose가 안 보임 | TF 없음 — Fixed Frame이 `base_footprint`인지, 브링업(실물)·Gazebo가 떠 있는지 확인 |
| 거리(z)가 실제와 다름 | `marker_size`가 실측값이 아니거나, 잰 뒤 화면을 확대·축소함 |
| bag 재생 때 pose가 안 나옴 | `/camera/camera_info`를 기록하지 않음 (B-4) |
| Gazebo가 뜨지 않음 | 최상위 README 5절(문제 해결) 참조 |
