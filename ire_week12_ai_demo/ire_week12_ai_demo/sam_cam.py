#!/usr/bin/env python3
"""12주차 — SAM 2: 카메라 화면에서 클릭한 물체를 분할.

  python3 sam_cam.py                     # 기본 카메라
  python3 sam_cam.py --device 4          # RealSense D435 등
  python3 sam_cam.py --model sam2.1_t.pt # 더 작은 모델 (74MB)

조작
  마우스 왼쪽 클릭 : 그 물체를 분할 (클릭한 프레임으로 예측)
  c                : 마스크 지우고 라이브로 복귀
  q                : 종료

가중치는 첫 실행 시 자동으로 내려받는다 (sam2.1_b.pt 154MB). 별도 준비가 필요 없다.

YOLO 와 비교해서 볼 것.
  YOLO  : 학습된 80종만 인식. 대신 "그게 무엇인지" 클래스명을 알려준다
  SAM 2 : 클릭한 것은 무엇이든 분할. 대신 "그게 무엇인지" 는 모른다
"""
import argparse
import os
import time

import cv2
import numpy as np
from ultralytics import SAM

WEIGHT_DIR = os.path.expanduser('~/ai_weights')   # 가중치를 한 곳에 모은다

state = {'click': None, 'mask': None}


def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        state['click'] = (x, y)


def overlay(frame, mask, color=(0, 255, 0), alpha=0.5):
    """마스크 영역을 반투명하게 칠한다."""
    out = frame.copy()
    out[mask] = (np.array(color) * alpha + frame[mask] * (1 - alpha)).astype(np.uint8)
    return out


def main():
    ap = argparse.ArgumentParser(description='카메라 → 클릭한 물체 분할 (SAM 2)')
    ap.add_argument('--device', type=int, default=0, help='/dev/videoN 의 N')
    ap.add_argument('--model', default='sam2.1_b.pt',
                    help='sam2.1_t.pt(74MB) / sam2.1_b.pt(154MB) / sam2.1_l.pt')
    ap.add_argument('--width', type=int, default=1280, help='카메라 가로 해상도')
    ap.add_argument('--height', type=int, default=720, help='카메라 세로 해상도')
    args = ap.parse_args()

    os.makedirs(WEIGHT_DIR, exist_ok=True)
    os.chdir(WEIGHT_DIR)                     # 가중치가 여기에 받아진다
    print(f'{args.model} 로딩 중... (첫 실행이면 자동 다운로드)')
    model = SAM(args.model)

    cap = cv2.VideoCapture(args.device)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if not cap.isOpened():
        raise SystemExit(f'/dev/video{args.device} 를 열 수 없습니다. '
                         '장치 목록: for d in /sys/class/video4linux/*; do '
                         'echo "/dev/$(basename $d) $(cat $d/name)"; done')

    # 창 이름은 ASCII 로 둔다 — OpenCV Qt 백엔드가 한글 창 이름을 식별하지 못해
    # setMouseCallback 에서 NULL window handler 오류가 난다.
    win = 'SAM2'
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)  # 창 크기를 마우스로 조절할 수 있다
    cv2.resizeWindow(win, int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                          int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    cv2.setMouseCallback(win, on_mouse)
    print('준비 완료 — 물체를 클릭하십시오.  (c: 마스크 지우기 / q: 종료)')

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if state['click'] is not None:
                x, y = state['click']
                t0 = time.time()
                # labels=[1] → "이 점은 찾는 물체" (0 이면 배경으로 취급)
                results = model(frame, points=[x, y], labels=[1], verbose=False)
                dt = time.time() - t0

                masks = results[0].masks
                if masks is not None and len(masks.data):
                    state['mask'] = masks.data[0].cpu().numpy().astype(bool)
                    print(f'분할 완료 {dt:.2f}s', flush=True)
                else:
                    print(f'분할 실패 (마스크 없음) {dt:.2f}s', flush=True)
                state['click'] = None

            shown = frame if state['mask'] is None else overlay(frame, state['mask'])
            cv2.imshow(win, shown)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord('c'):
                state['mask'] = None
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
