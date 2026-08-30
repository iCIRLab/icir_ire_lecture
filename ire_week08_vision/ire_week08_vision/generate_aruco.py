#!/usr/bin/env python3
"""ArUco 마커 이미지 생성 — 출력해서 실물 실습에 사용.

  ros2 run ire_week08_vision generate_aruco        # aruco_0.png ~ aruco_9.png 생성

OpenCV 4.7+(신 API)와 Ubuntu 22.04 apt 기본 4.5.4(구 API) 모두에서 동작한다.

★ 마커 둘레의 흰 여백(quiet zone)은 검출에 반드시 필요하다. 출력물을 검은 테두리까지
  바짝 잘라내면 인식되지 않으므로, 자를 때도 흰 여백을 남겨야 한다.
"""
import cv2
import numpy as np

SIZE = 400          # 마커 한 변 픽셀
PAD = 50            # 사방 흰 여백


def main():
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    for i in range(10):
        if hasattr(cv2.aruco, 'generateImageMarker'):      # OpenCV >= 4.7
            m = cv2.aruco.generateImageMarker(d, i, SIZE)
        else:                                              # OpenCV 4.5.x (apt)
            m = cv2.aruco.drawMarker(d, i, SIZE)

        img = np.full((SIZE + 2 * PAD, SIZE + 2 * PAD), 255, np.uint8)   # 흰 바탕
        img[PAD:PAD + SIZE, PAD:PAD + SIZE] = m
        cv2.imwrite(f'aruco_{i}.png', img)
        print(f'aruco_{i}.png (DICT_4X4_50, id={i}, 여백 {PAD}px)')


if __name__ == '__main__':
    main()
