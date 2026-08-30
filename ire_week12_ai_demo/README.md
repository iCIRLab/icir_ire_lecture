# ire_week12_ai_demo

로봇에 붙여 쓸 수 있는 AI 도구를 하나씩 실행해 보는 주차입니다.
각 도구는 독립적으로 동작하며, 프로젝트에서 필요한 것을 골라 쓰면 됩니다.
프로젝트 설계 시 **출력 형태와 속도**를 먼저 보십시오.

| 도구 | 하는 일 | 출력 | 속도 | 만든 곳 · 공식 문서 |
|---|---|---|---|---|
| **YOLO** | 물체 탐지 | 박스 + 클래스 | 실시간 | Ultralytics — <https://docs.ultralytics.com/> |
| **SAM 2** | 클릭한 물체를 분할 | 마스크(픽셀) | 클릭당 1초 내외 | Meta AI — <https://docs.ultralytics.com/models/sam-2/> |
| **Llama 3.2** | 자연어 → 구조화된 명령 | 텍스트/JSON | 초 단위 | Meta AI — <https://ollama.com/library/llama3.2> |
| **Whisper** | 음성 → 텍스트 | 텍스트 | 초 단위 | OpenAI — <https://github.com/openai/whisper> |

만든 곳이 각각 다릅니다. YOLO는 Ultralytics 제품이고, SAM은 Meta가 만든 것을
Ultralytics가 같은 API로 감싸 제공합니다. Llama는 Meta의 모델이며, 그것을 로컬에서
실행해 주는 도구가 **Ollama**(<https://ollama.com/>)로 서로 다른 층위입니다.

설치 방법과 전체 API는 위 공식 문서를 참고하십시오. 본 README의 명령은 수업용으로
간추린 것입니다.

---

## 0. 사전 설치

### 미리 준비할 것

GPU를 쓰려면 시스템 쪽 준비가 먼저 필요합니다.
아래 중 없는 것이 있으면 **설치 스크립트를 돌리기 전에** 설치하십시오.

| 항목 | 확인 명령 | 설치 |
|---|---|---|
| **NVIDIA 드라이버** | `nvidia-smi` | `sudo ubuntu-drivers autoinstall` 후 재부팅 |
| **CUDA Toolkit** | `nvcc --version` | <https://developer.nvidia.com/cuda-toolkit-archive> |
| **cuDNN** | — | <https://developer.nvidia.com/cudnn-archive> |
| **Miniconda** | `conda --version` | <https://docs.conda.io/projects/miniconda/en/latest/> |

CUDA와 cuDNN은 배포판·GPU에 맞는 버전을 위 아카이브에서 골라 설치합니다
(linux → x86_64 → ubuntu → 버전 → deb(local) 순).

### 설치

AI 라이브러리는 강의 환경과 버전이 충돌하기 쉽습니다. 특히 `ultralytics`는
NumPy와 OpenCV를 자기 요구대로 바꾸는데, 그러면 **8주차 비전 예제가 깨집니다.**

그래서 12주차는 **별도 conda 환경**에 설치합니다. 문제가 생기면 환경만 지우고
다시 만들면 되고, 지금까지 만든 ROS 환경은 그대로 남습니다.

```bash
cd ~/ire_ws/src/icir_ire_lecture/ire_week12_ai_demo
./setup_week12.sh
```

마지막에 `ALL OK`가 출력됩니다.

> **⚠ 다운로드가 큽니다.** 새 conda 환경에 torch 계열 약 5 GB(torch 1.6 + CUDA
> 라이브러리 2.7 + triton 0.5)와 LLM 모델 약 2 GB를 받습니다.

### 환경에 대해 알아야 할 것

스크립트는 `ire_ai`라는 이름의 **파이썬 3.10** 환경을 만듭니다. 3.10인 이유가 있습니다.

```
ROS 2 Humble 의 rclpy = 파이썬 3.10 전용으로 컴파일된 바이너리
→ 3.8 이나 3.13 환경에서는 import rclpy 자체가 실패
```

그리고 환경 안의 패키지를 쓰려면 **`ros2 run`이 아니라 `python3`로 직접 실행**해야 합니다.

```bash
ros2 run 패키지 노드      # 시스템 파이썬으로 실행됨 → 환경의 torch 안 보임
python3 노드.py           # 현재 환경의 파이썬 → 정상
```

`ros2 run`은 빌드할 때 스크립트에 `#!/usr/bin/python3`가 박히기 때문입니다.

### venv 와 conda 중 무엇을 쓸까

12주차는 venv로도 됩니다. **conda를 쓰는 것은 수업 차원의 선택**으로,
파이썬 버전까지 고를 수 있어 프로젝트에서 더 쓸모가 있습니다.

| | venv | conda |
|---|---|---|
| 파이썬 버전 | 기존 인터프리터 그대로 (**바꿀 수 없음**) | **원하는 버전 설치 가능** |
| 격리 대상 | pip 패키지만 | pip 패키지 + 인터프리터 + 네이티브 라이브러리 |
| 시스템 패키지 재사용 | `--system-site-packages`로 가능 | 불가 (항상 새로 받음) |
| 준비 | `sudo apt install python3.10-venv` | Miniconda 설치 |

**conda를 쓰는 경우**

- 다른 파이썬 버전이 필요할 때 ← 가장 결정적인 기준
- 논문 코드가 특정 CUDA 런타임이나 컴파일러까지 고정할 때
- 시스템과 완전히 분리하고 싶을 때

```bash
conda create -n 이름 python=3.10
conda activate 이름
```

**venv를 쓰는 경우**

- 파이썬 3.10으로 충분할 때
- 이미 설치된 torch 등을 재사용하고 싶을 때 (약 5 GB 절약)

```bash
python3 -m venv --system-site-packages ~/venv/이름
source ~/venv/이름/bin/activate
```

`--system-site-packages`가 없으면 시스템에 설치된 패키지가 보이지 않습니다.

### 실행 방법

각 도구는 **conda 환경을 활성화한 뒤 `python3`로 직접 실행**합니다.

```bash
conda activate ire_ai
python3 <스크립트 경로>
```

---

## 1. YOLO — 물체 탐지

> 공식 문서: <https://docs.ultralytics.com/>

카메라에 보이는 물체를 실시간으로 찾아 박스와 클래스명을 그립니다.

```bash
conda activate ire_ai

# 카메라 장치 번호와 이름 확인하여 device 번호 수정 (D435 를 연결하면 여러 개가 잡힌다)
for d in /sys/class/video4linux/*; do echo "/dev/$(basename $d)  $(cat $d/name)"; done
cd ~/ire_ws/src/icir_ire_lecture/ire_week12_ai_demo/ire_week12_ai_demo
python3 yolo_cam.py --device 8
```

터미널에는 검출된 클래스명이 찍히고, 창에는 박스가 그려집니다. `q`로 종료합니다.

```bash
python3 yolo_cam.py --conf 0.3        # 임계값을 낮추면 더 많이 잡힌다 (오탐도 늘어남)
python3 yolo_cam.py --model yolov8s.pt  # 더 큰 모델 (n < s < m < l < x)
```

**한계를 함께 확인하십시오.** YOLO는 COCO 데이터셋의 **80종**(person, chair, bottle,
laptop, tv 등)만 압니다. 실험실 부품이나 "빨간 블록"처럼 학습에 없는 물체는 사람이
봐도 뚜렷한데 아무것도 잡히지 않습니다.

### ROS 노드로 쓰기 (RealSense + RViz)

카메라가 ROS 토픽으로 영상을 내보내는 경우입니다. `yolo_cam.py`가 카메라를 직접 여는
것과 달리, 이 노드는 **토픽을 구독**하므로 카메라 노드가 먼저 떠 있어야 합니다.

**터미널1 — RealSense 카메라 노드**

드라이버가 없으면 먼저 설치합니다 (SDK 포함, 약 9 MB).

```bash
sudo apt install ros-humble-realsense2-camera
```

```bash
ros2 launch realsense2_camera rs_launch.py
```

> 일반 웹캠이면 `sudo apt install ros-humble-v4l2-camera` 후
> `ros2 run v4l2_camera v4l2_camera_node --ros-args -p video_device:=/dev/video0`

```bash
ros2 topic list | grep color        # 토픽 이름 확인
# → /camera/camera/color/image_raw
```

**터미널2 — YOLO 노드**

```bash
conda activate ire_ai
cd ~/ire_ws/src/icir_ire_lecture/ire_week12_ai_demo/ire_week12_ai_demo
python3 yolo_detect.py --ros-args -p image_topic:=/camera/camera/color/image_raw
```

두 가지를 발행합니다.

| 토픽 | 형식 | 용도 |
|---|---|---|
| `/yolo/detections` | `String` | `person 0.87 (312,241)` — 다른 노드가 받아 쓰기 |
| `/yolo/image` | `Image` | **박스가 그려진 영상 — RViz 로 확인** |

**터미널3 — RViz 로 결과 보기**

```bash
rviz2
```

RViz에서 **Add → By topic → `/yolo/image` → Image**를 선택하면 탐지 결과가 그려진
영상이 보입니다. `Fixed Frame`은 아무 값이어도 Image 디스플레이에는 영향이 없습니다.

문자열 결과는 아래와 같이 실행합니다.

```bash
ros2 topic echo /yolo/detections
```

---

## 2. SAM 2 — 클릭한 물체 분할

> 공식 문서: <https://docs.ultralytics.com/models/sam-2/>

YOLO가 "학습된 80종"만 아는 것과 달리, SAM은 **클릭한 것이면 무엇이든** 분할합니다.
대신 그것이 무엇인지(클래스명)는 알려주지 않습니다.

```bash
conda activate ire_ai
cd ~/ire_ws/src/icir_ire_lecture/ire_week12_ai_demo/ire_week12_ai_demo
python3 sam_cam.py --device 8
```

가중치는 첫 실행 시 자동으로 받습니다. 별도 준비가 필요 없습니다.

| 조작 | 동작 |
|---|---|
| 마우스 왼쪽 클릭 | 그 물체를 분할 |
| `c` | 마스크 지우고 라이브로 복귀 |
| `q` | 종료 |

### 모델 크기

| 가중치 | 크기 |
|---|---|
| `sam2.1_t.pt` | 74 MB |
| `sam2.1_b.pt` | 154 MB (**기본값**) |
| `sam2.1_l.pt` | 더 큼 |

```bash
python3 sam_cam.py --model sam2.1_t.pt    # 더 가볍고 빠름
```

### SAM 1 · SAM 3 는 무엇이 다른가

본 수업은 **SAM 2**를 씁니다. 앞뒤 버전은 목적이 다르니 프로젝트에서 필요하면
아래를 참고하십시오.

| | 프롬프트 | 특징 | 가중치 |
|---|---|---|---|
| **SAM 1** | 클릭 · 박스 | 이미지 한 장. `segment-anything` 패키지를 따로 설치 | 직접 다운로드 (358 MB~) |
| **SAM 2** | 클릭 · 박스 | **영상 추적** 가능. ultralytics에 포함 | **자동 다운로드** (74 MB~) |
| **SAM 3** | **텍스트** | "red block" 처럼 말로 지정, 같은 개념을 모두 찾음 | **Hugging Face 승인 필요**, 3.45 GB |

- SAM 1: `pip install segment-anything` + 가중치 `wget` — 기존 연구 코드가 이 API를 쓰는 경우가 많습니다
- SAM 3: <https://huggingface.co/facebook/sam3> 에서 접근 권한을 신청한 뒤
  `SAM3SemanticPredictor` 사용 — <https://docs.ultralytics.com/models/sam-3/>

말로 대상을 지정하고 싶으면 SAM 3, 영상에서 계속 추적해야 하면 SAM 2입니다.

## 3. Llama — 자연어를 명령으로

> 공식 문서: <https://ollama.com/library/llama3.2>

로컬 LLM(Ollama)이 자연어를 파싱해 **검증을 통과한 JSON만** 발행합니다.
모델을 한 번 받아 두면 **인터넷 없이 동작합니다.** Ollama는 `localhost:11434`에서만
돌고 외부로 나가지 않으므로, 강의실 네트워크와 무관하며 API 키도 필요 없습니다.

```bash
# 터미널1 — LLM 노드 (ROS 노드이므로 워크스페이스도 source)
conda activate ire_ai
cd ~/ire_ws/src/icir_ire_lecture/ire_week12_ai_demo/ire_week12_ai_demo
python3 llm_cmd.py

# 터미널2 — 결과 구독
ros2 topic echo /mission_goal

# 터미널3 — 명령 전송
ros2 topic pub --once /voice_cmd std_msgs/msg/String "{data: '빨간 블록 가져와'}"
```

```json
{"action": "pick", "target": "빨간 블록"}
```

### 검증이 하는 일

`action`이 `navigate`, `pick`, `place`, `stop` 중 하나가 아니면 발행하지 않고
`검증 탈락` 경고만 남깁니다. 직접 확인해 보십시오.

| 명령 | LLM 출력 | 결과 |
|---|---|---|
| `빨간 블록 가져와` | `{"action": "pick", "target": "빨간 블록"}` | 발행됨 |
| `부엌으로 가` | `{"action": "navigate", "target": "부엌"}` | 발행됨 |
| **`노래 불러줘`** | `{"action": "play", ...}` | **검증 탈락** — 정의에 없는 동작 |

```bash
ros2 topic pub --once /voice_cmd std_msgs/msg/String "{data: '노래 불러줘'}"
```

**LLM은 조타수가 아니라 통역사입니다.** 출력을 그대로 실행하지 않고 반드시 검증을
거친다는 것이 이 노드의 핵심입니다. LLM은 확률적으로 답을 만들기 때문에, 로봇이
할 수 없는 동작을 그럴듯하게 지어낼 수 있습니다.

### 모델 크기 비교

```bash
python3 llm_cmd.py --ros-args -p model:=llama3.2:1b     # 더 작고 빠름
```

작은 모델일수록 응답이 빠르지만 엉뚱한 파싱이 늘어납니다.

---

## 4. Whisper — 음성을 텍스트로

> 공식 문서: <https://github.com/openai/whisper>

### 음성 파일 → 텍스트

```bash
conda activate ire_ai
cd ~/ire_ws/src/icir_ire_lecture/ire_week12_ai_demo/ire_week12_ai_demo
python3 whisper_file.py sample.wav
python3 whisper_file.py sample.wav --model small     # 모델 크기 비교
```

파일이 없으면 직접 녹음하면 됩니다. 별도 프로그램 없이 `arecord`로 됩니다.

```bash
arecord -f S16_LE -r 16000 -c 1 -d 5 sample.wav      # 5초 녹음
```

### 마이크 → 실시간 텍스트

```bash
conda activate ire_ai
cd ~/ire_ws/src/icir_ire_lecture/ire_week12_ai_demo/ire_week12_ai_demo
python3 whisper_mic.py
```

말할 때만 인식합니다. `SpeechRecognition`이 소리 크기를 감시하다가 임계값을 넘으면
녹음을 시작하고, 말이 끊기면 그 덩어리를 Whisper에 넘기는 구조입니다.
계속 추론을 돌리지 않아 부담이 적습니다.

시작할 때 주변 소음을 2초간 재서 **임계값을 자동으로 정하고 출력**합니다.

```
소리 임계값: 12832 (조용한데 반응이 없으면 --energy 로 낮추십시오)
```

말해도 반응이 없거나 반대로 계속 잡히면 수동으로 지정합니다.

```bash
python3 whisper_mic.py --energy 1000
```

> 마이크마다 감도가 크게 다릅니다. 노트북 내장 마이크는 주변 소음만으로도 임계값이
> 만 단위로 잡히는 경우가 있어, 고정값을 쓰면 발화 구간을 제대로 자르지 못합니다.
> 그래서 자동 계산을 기본으로 두었습니다.

### 모델 선택

| 모델 | 용량 | 특징 |
|---|---|---|
| `tiny` | 72 MB | 빠름, 정확도 낮음 |
| `base` | 139 MB | **수업 시연에 적당** (기본값) |
| `small` | 461 MB | 정확도/속도 균형 |
| `medium` | 1.4 GB | |
| `turbo` | 1.5 GB | large 수준 정확도에 추론이 빠름 — **용량은 작지 않음** |

이름과 달리 `turbo`는 가벼운 모델이 아닙니다. 추론 속도가 빠른 것이지 다운로드는
`large`급입니다.

---

## 참고 — 이 밖의 로봇용 AI 도구

수업에서는 다루지 않지만 로봇 응용에 사용할만한 도구들을 소개합니다.

| 도구 | 용도 | 비고 |
|---|---|---|
| **VLM** (llava 등) | 사진을 보고 질문에 답함 | `ollama pull llava` — 3절과 같은 Ollama에서 모델만 바꾸면 됩니다. 단 답이 문장이라 좌표가 필요한 제어에는 쓸 수 없습니다 — <https://ollama.com/library/llava> |
| **YOLO-World** | 텍스트로 지정한 물체 탐지 | ultralytics 포함, 자동 다운로드 — <https://docs.ultralytics.com/models/yolo-world/> |
| **MediaPipe** | 손·몸 포즈 추정 | `pip install mediapipe` — <https://ai.google.dev/edge/mediapipe/solutions/guide> |
| **Depth Anything V2** | 단안 카메라로 깊이 추정 | <https://github.com/DepthAnything/Depth-Anything-V2> |
| **Grounding DINO** | 텍스트 기반 물체 탐지 | SAM과 조합해 "말로 지정 → 분할"에 자주 쓰임 |
| GraspNet · AnyGrasp | 파지점(grasp pose) 생성 | 설치·환경 구성이 까다로움 |
| ACT · Diffusion Policy · LeRobot | 모방학습 정책 | 데이터 수집이 선행되어야 함 |
| OpenVLA · π0 | VLA (시각-언어-행동) | 모델이 크고 GPU 요구가 높음 |

위쪽 다섯은 설치가 가볍고 노트북에서 바로 돌려볼 수 있습니다. 아래쪽 셋은 환경 분리가
필요한 규모이므로 0절의 환경 관리 내용을 참고하십시오.

## 문제 해결

| 증상 | 원인 |
|---|---|
| `ModuleNotFoundError: ultralytics` | `conda activate ire_ai` 누락, 또는 `ros2 run`으로 실행 |
| `ModuleNotFoundError: rclpy` | 환경의 파이썬이 3.10이 아님 — `python3 -V`로 확인 |
| `LLM 실패: ConnectionError` | Ollama 미실행 — `ollama list`로 확인 |
| `검증 탈락`만 반복 | LLM이 스키마를 벗어난 응답 — 명령을 명확히 하거나 모델 변경 |
| YOLO가 아무것도 발행 안 함 | 카메라 토픽 이름 불일치 — `ros2 topic list \| grep image` |
| 8주차 예제가 갑자기 깨짐 | 시스템 파이썬에 AI 패키지를 설치한 경우 — 12주차는 conda 환경에서만 |
| **카메라가 안 열림** (`--device 8` 실패) | RealSense ROS 노드가 스트림을 점유 중 — `pkill -f realsense2_camera_node` 후 재시도 |
| `yolo_detect.py`가 세그폴트 (`_ARRAY_API not found`) | 환경의 NumPy가 2.x — `pip install "numpy<2"` (apt `cv_bridge`가 1.x로 빌드되어 있음) |
