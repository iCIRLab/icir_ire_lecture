# ire_week08_vision

카메라 영상에서 물체를 찾는 두 가지 방법을 다룹니다.

- `color_detect` — HSV 색 검출로 적색 기둥을 찾아 `/red_pillar/exists`(Bool) 발행 **(완성 예제)**
- `generate_aruco` — ArUco 마커 이미지 생성 (인쇄용)
- `aruco_world.launch.py` — ArUco 박스가 놓인 월드 **(미션: 검출 노드는 직접 작성)**

수업에서는 Gazebo로 원리를 확인하고, 실물 키트로 같은 코드를 검증하는 순서를 권장합니다.

---

## A. Gazebo (수업)

### A-1. 적색 기둥 검출 — 완성 예제

```bash
ros2 launch ire_week08_vision red_pillar_world.launch.py
```

월드 + 적색 기둥 + `color_detect`가 한 번에 뜹니다. 창 두 개가 함께 열립니다.

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

### A-2. ArUco 마커 — 미션

```bash
ros2 launch ire_week08_vision aruco_world.launch.py
```

월드와 ArUco 박스만 뜨고 **검출 노드는 실행되지 않습니다.** 로봇 정면 약 0.7 m에
박스가 놓이므로 이동 없이 바로 보입니다.

`color_detect`가 그대로 뼈대가 됩니다. 구독 → `cv_bridge` 변환까지는 같고,
HSV 대신 `cv2.aruco.detectMarkers`를 쓰면 됩니다.

```bash
ros2 topic list | grep image_raw     # 구독할 토픽 확인
```

여기서 만든 검출 노드는 11주차 미션 #4(ArUco 위치 → 팔 동작)의 입력이 됩니다.

### A-3. 마커 이미지 생성

```bash
ros2 run ire_week08_vision generate_aruco     # aruco_0.png ~ aruco_9.png
```

인쇄해서 실물 실습에 사용합니다. 마커 둘레의 흰 여백은 검출에 반드시 필요하므로,
자를 때 검은 테두리까지 바짝 자르지 마십시오.

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

**[TurtleBot3 SBC] 터미널1** — 로봇 구동

```bash
ros2 launch turtlebot3_manipulation_bringup hardware.launch.py
```

**[TurtleBot3 SBC] 터미널2** — 카메라 구동

`hardware.launch.py`는 **카메라를 띄우지 않습니다.** 영상을 받으려면 카메라 노드를
따로 실행해야 합니다. 처음 한 번은 설치가 필요합니다.

```bash
sudo apt install ros-humble-camera-ros
```

```bash
ros2 run camera_ros camera_node --ros-args \
  -p format:='RGB888' -p width:=320 -p height:=240
```

→ `/camera/image_raw` 로 발행됩니다.

기본 해상도는 640이지만 320×240 으로 낮췄습니다. 라즈베리파이 부담과 무선 전송량이
줄고, 색 검출에는 이 정도면 충분합니다.

> 시뮬레이션과 토픽 이름이 다릅니다. Gazebo 로봇은 `/pi_camera/image_raw`,
> 실물은 위와 같이 실행하면 `/camera/image_raw` 입니다.
> `ros2 topic list | grep image` 로 확인하십시오.

**[Remote PC]** — 검출 노드 실행

```bash
ros2 run ire_week08_vision color_detect --ros-args \
  -p image_topic:=/camera/image_raw -p show_windows:=true
```

> **카메라 토픽 이름을 반드시 확인하십시오.** 노드 기본값은 Gazebo 실습 키트 기준인
> `/pi_camera/image_raw`입니다. 실물 로봇은 카메라 구동 방식에 따라 이름이 다를 수
> 있으므로 `ros2 topic list | grep image`로 확인한 뒤 `image_topic` 파라미터로 지정합니다.

실물에서는 조명이 시뮬레이션과 달라 **HSV 범위를 다시 잡아야 합니다.** `red_mask` 창을
보면서 `hsv1_low`/`hsv1_high`를 조정하는 것이 이 실습의 핵심입니다.

```bash
ros2 param set /color_detect hsv1_low "[0, 120, 80]"
ros2 param set /color_detect hsv1_high "[10, 255, 255]"
ros2 param set /color_detect min_area 300
```

ArUco 미션은 `generate_aruco`로 만든 마커를 인쇄해 붙이고 같은 방식으로 확인합니다.

## 문제 해결

| 증상 | 원인 |
|---|---|
| `listening:` 만 찍히고 검출 로그가 없음 | 카메라 토픽 불일치 — `ros2 topic list | grep image`로 확인 |
| 창이 뜨지 않음 | `show_windows` 파라미터가 `false` |
| ArUco가 검출되지 않음 | 마커 흰 여백 부족, 조명 반사, 거리가 너무 멂 |
| Gazebo가 뜨지 않음 | 최상위 README 5절(문제 해결) 참조 |
