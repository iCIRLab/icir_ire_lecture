#!/usr/bin/env python3
"""12주차 — YOLO: 카메라 영상에서 물체를 실시간 탐지.

  python3 yolo_cam.py                    # 기본 카메라
  python3 yolo_cam.py --device 4         # RealSense D435 등 다른 장치
  python3 yolo_cam.py --conf 0.3         # 임계값을 낮추면 더 많이 잡힘
  python3 yolo_cam.py --model yolov8s.pt # 더 큰 모델

카메라 장치 번호 확인:
  for d in /sys/class/video4linux/*; do echo "/dev/$(basename $d)  $(cat $d/name)"; done

q 키로 종료.

YOLO는 COCO 데이터셋의 80종(person, chair, bottle, laptop, tv, ...)만 인식한다.
학습에 없는 물체는 찾지 못한다는 점을 함께 확인할 것.
"""
import argparse
import os

import cv2
from ultralytics import YOLO

WEIGHT_DIR = os.path.expanduser('~/ai_weights')   # 가중치를 한 곳에 모은다


def main():
    ap = argparse.ArgumentParser(description='카메라 → YOLO 실시간 탐지')
    ap.add_argument('--device', type=int, default=0, help='/dev/videoN 의 N')
    ap.add_argument('--model', default='yolov8n.pt', help='yolov8n/s/m/l/x.pt')
    ap.add_argument('--conf', type=float, default=0.5, help='신뢰도 임계값')
    ap.add_argument('--width', type=int, default=1280, help='카메라 가로 해상도')
    ap.add_argument('--height', type=int, default=720, help='카메라 세로 해상도')
    args = ap.parse_args()

    os.makedirs(WEIGHT_DIR, exist_ok=True)
    os.chdir(WEIGHT_DIR)                     # 가중치가 여기에 받아진다
    model = YOLO(args.model)                 # 첫 실행 시 자동 다운로드 (n=6MB, s=22MB)

    cap = cv2.VideoCapture(args.device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not cap.isOpened():
        raise SystemExit(f'/dev/video{args.device} 를 열 수 없습니다. '
                         '장치 목록: for d in /sys/class/video4linux/*; do '
                         'echo "/dev/$(basename $d) $(cat $d/name)"; done')

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # 창 이름은 ASCII 로 둔다 (한글 창 이름은 OpenCV Qt 백엔드에서 문제를 일으킨다)
    win = 'YOLO'
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)  # 창 크기를 마우스로 조절할 수 있다
    cv2.resizeWindow(win, w, h)
    print(f'[{args.model}] {w}x{h} 시작 — q 키로 종료')
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            results = model(frame, conf=args.conf, verbose=False)
            annotated = results[0].plot()    # 박스와 클래스명을 그려 준다
            cv2.imshow(win, annotated)

            names = [model.names[int(b.cls)] for b in results[0].boxes]
            if names:
                print(', '.join(names), flush=True)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
