#!/usr/bin/env python3
"""12주차 — Whisper: 음성 파일을 텍스트로.

  python3 whisper_file.py sample.wav
  python3 whisper_file.py sample.wav --model small     # 모델 크기 비교
  python3 whisper_file.py sample.wav --lang en

모델은 첫 실행 시 자동으로 내려받아 ~/.cache/whisper 에 저장된다.

  tiny    72 MB   빠름, 정확도 낮음
  base   139 MB   수업 시연에 적당
  small  461 MB   정확도/속도 균형
  medium 1.4 GB
  turbo  1.5 GB   large 수준 정확도, 추론은 빠름 (용량은 큼)
"""
import argparse
import time

import whisper


def main():
    ap = argparse.ArgumentParser(description='음성 파일 → 텍스트')
    ap.add_argument('audio', help='음성 파일 (wav, mp3 등)')
    ap.add_argument('--model', default='base', help='tiny/base/small/medium/turbo')
    ap.add_argument('--lang', default='ko', help='언어 코드 (ko, en, ...)')
    args = ap.parse_args()

    t0 = time.time()
    model = whisper.load_model(args.model)
    print(f'[{args.model}] 모델 로드 {time.time() - t0:.1f}초')

    t0 = time.time()
    result = model.transcribe(args.audio, language=args.lang)
    print(f'인식 {time.time() - t0:.1f}초\n')
    print(result['text'].strip())


if __name__ == '__main__':
    main()
