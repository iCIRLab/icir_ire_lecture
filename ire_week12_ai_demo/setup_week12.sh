#!/usr/bin/env bash
# IRE 12주차 사전 설치 — 수업 전 주에 실행하세요 (다운로드 수 GB, 시간 걸림)
#
# 강의 환경(시스템 파이썬)을 건드리지 않도록 conda 환경을 따로 만들어 설치한다.
# ROS 2 Humble의 rclpy는 파이썬 3.10 전용이므로 환경도 3.10으로 맞춘다.
set -e

ENV_NAME=ire_ai
PY_VER=3.10

command -v conda >/dev/null || {
  echo "conda 가 없습니다. Miniconda 를 먼저 설치하세요:"
  echo "  https://docs.conda.io/projects/miniconda/en/latest/"
  exit 1
}
source "$(conda info --base)/etc/profile.d/conda.sh"

echo "[1/5] conda 환경 생성 ($ENV_NAME, python $PY_VER)"
conda env list | grep -q "^$ENV_NAME " || conda create -y -n $ENV_NAME python=$PY_VER
conda activate $ENV_NAME

echo "[2/5] YOLO (ultralytics) + SAM"
# GPU 를 쓰려면 torch 를 먼저, CUDA 빌드를 지정해서 설치한다.
# ultralytics 를 먼저 깔면 기본 저장소에서 CPU 판 torch 가 들어올 수 있다.
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install ultralytics      # YOLO 와 SAM 2 가 함께 들어 있다

# NumPy 와 OpenCV 를 apt cv_bridge 에 맞춰 고정한다. 둘을 한 번에 지정해야 한다
# (따로 설치하면 뒤엣것이 앞엣것을 다시 올려버린다).
#   NumPy 2.x  → cv_bridge 가 1.x 로 빌드되어 있어 세그폴트
#                AttributeError: _ARRAY_API not found
#   OpenCV 5.x → cv_bridge 가 4.x 기준이라 타입 매핑 실패
#                cv2_to_imgmsg → KeyError: 16
pip install "numpy<2" "opencv-python<5"

echo "[3/5] Whisper (음성 인식)"
#   ffmpeg          : whisper 가 음성 파일을 디코딩할 때 사용
#   portaudio19-dev : pyaudio 빌드에 필요 (마이크 입력)
#   SpeechRecognition + pyaudio : 마이크 캡처와 발화 구간 검출
sudo apt install -y ffmpeg portaudio19-dev
pip install openai-whisper SpeechRecognition pyaudio

echo "[4/5] Ollama + LLM 모델"
command -v ollama >/dev/null || curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b

echo "[5/5] 스모크 테스트"
mkdir -p ~/ai_weights && cd ~/ai_weights     # 가중치를 한 곳에 모은다
python - <<'PY'
from ultralytics import YOLO
YOLO('yolov8n.pt')            # 가중치 자동 다운로드 + 로드 확인
print('YOLO OK')
from ultralytics import SAM
SAM('sam2.1_b.pt')            # 154MB 자동 다운로드 + 로드 확인
print('SAM 2 OK')
import whisper, torch
whisper.load_model('base')    # 139MB 다운로드 + 로드 확인
print('Whisper OK / torch', torch.__version__, '| CUDA', torch.cuda.is_available())
import speech_recognition, pyaudio
print('마이크 입력 준비 OK')
import numpy, cv2
assert numpy.__version__.startswith('1.'), f'NumPy 가 {numpy.__version__} 입니다 — 1.x 여야 합니다'
assert cv2.__version__.startswith('4.'), f'OpenCV 가 {cv2.__version__} 입니다 — 4.x 여야 합니다'
print('NumPy', numpy.__version__, '/ OpenCV', cv2.__version__, 'OK')
PY

# ROS 연동 확인은 ROS 를 source 한 뒤에 한다 (스크립트 안에서는 source 되어 있지 않다)
if [ -f /opt/ros/humble/setup.bash ]; then
  ( source /opt/ros/humble/setup.bash
    python -c "import rclpy; print('rclpy OK — ROS 2 연동 가능')" ) \
    || echo "  ※ rclpy import 실패 — 환경의 파이썬이 3.10 인지 확인하십시오"
else
  echo "  ※ ROS 2 Humble 이 없어 rclpy 확인을 건너뜁니다"
fi
# llm_cmd.py 와 같은 방식(JSON 모드)으로 확인한다.
# 자유 대화로 물으면 3B 모델이 엉뚱한 답을 내놓아 설치 실패로 오해하기 쉽다.
curl -sS http://localhost:11434/api/generate \
  -d '{"model":"llama3.2:3b","prompt":"JSON 한 개로만 답하라: {\"ok\": true}","format":"json","stream":false}' \
  | python -c "import sys,json; json.loads(json.load(sys.stdin)['response']); print('Ollama OK')"

echo
echo "ALL OK"
