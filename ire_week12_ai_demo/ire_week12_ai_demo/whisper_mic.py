#!/usr/bin/env python3
"""12주차 — Whisper: 마이크 입력을 실시간으로 텍스트 출력.

  python3 whisper_mic.py                    # 말하면 터미널에 텍스트가 찍힌다
  python3 whisper_mic.py --model small
  python3 whisper_mic.py --energy 1000      # 임계값 수동 지정 (기본: 자동 계산)

Ctrl+C 로 종료.

동작 방식: SpeechRecognition 이 마이크를 감시하다가 소리 크기가 임계값을 넘으면
녹음을 시작하고, 말이 끊기면 한 덩어리로 큐에 넣는다. 그 덩어리를 Whisper 에 넘긴다.
즉 "말할 때만" 인식하므로 계속 추론을 돌리지 않아도 된다.

임계값은 시작할 때 주변 소음을 2초간 재서 자동으로 정한다. 조용한 방에서는 낮게,
시끄러운 곳에서는 높게 잡힌다. 말해도 반응이 없으면 --energy 로 낮춰 볼 것.

참고: kimm_whisper (jspark861102) 의 구조를 수업용으로 간추림.
"""
import argparse
from queue import Queue

import numpy as np
import speech_recognition as sr
import torch
import whisper


def main():
    ap = argparse.ArgumentParser(description='마이크 → 텍스트 (실시간)')
    ap.add_argument('--model', default='base', help='tiny/base/small/medium/turbo')
    ap.add_argument('--lang', default='ko')
    ap.add_argument('--energy', type=int, default=None,
                    help='발화로 판단할 소리 크기 임계값 (기본: 주변 소음에서 자동 계산)')
    ap.add_argument('--phrase', type=float, default=3.0,
                    help='한 덩어리로 자를 최대 길이(초)')
    args = ap.parse_args()

    model = whisper.load_model(args.model)
    use_fp16 = torch.cuda.is_available()
    print(f'[{args.model}] 준비 완료 (GPU: {use_fp16}). 말해 보세요. Ctrl+C 로 종료.\n')

    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.dynamic_energy_threshold = False        # 임계값 고정 — 예측 가능하게

    source = sr.Microphone(sample_rate=16000)        # Whisper 가 16kHz 를 쓴다
    with source:
        recorder.adjust_for_ambient_noise(source)    # 주변 소음에서 임계값 자동 계산
    if args.energy is not None:                      # 인자를 준 경우에만 덮어쓴다
        recorder.energy_threshold = args.energy
    print(f'소리 임계값: {recorder.energy_threshold:.0f} '
          f'(조용한데 반응이 없으면 --energy 로 낮추십시오)')

    def on_audio(_, audio: sr.AudioData):
        # 앞의 음성을 아직 처리 중이면 새 입력을 버린다.
        # 그러지 않으면 말이 쌓여 인식 결과가 점점 밀린다.
        if data_queue.empty():
            data_queue.put(audio.get_raw_data())

    stop = recorder.listen_in_background(source, on_audio,
                                         phrase_time_limit=args.phrase)
    try:
        while True:
            if data_queue.empty():
                continue
            raw = b''.join(data_queue.queue)
            data_queue.queue.clear()

            # int16 PCM → whisper 가 받는 float32 (-1.0 ~ 1.0)
            audio_np = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            text = model.transcribe(audio_np, language=args.lang,
                                    fp16=use_fp16)['text'].strip()
            if text:
                print(text, flush=True)
    except KeyboardInterrupt:
        print('\n종료')
    finally:
        stop(wait_for_stop=False)


if __name__ == '__main__':
    main()
