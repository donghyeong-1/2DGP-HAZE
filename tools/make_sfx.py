"""효과음을 코드로 직접 합성해 assets/sfx/*.wav 로 저장한다. (외부 음원 없음, 저작권 문제 없음)

사각파·삼각파·잡음에 짧은 엔벨로프를 걸어 8비트 느낌으로 만든다. 소리를 바꾸려면 SOUNDS의 값을 고쳐 다시 실행한다.
사용: python tools/make_sfx.py
"""
import wave
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
RATE = 22050
RNG = np.random.default_rng(7)  # 잡음이 매번 같도록 고정


def t_axis(sec):
    return np.linspace(0, sec, int(RATE * sec), endpoint=False)


def square(freq, duty=0.5):
    phase = np.cumsum(freq) / RATE
    return np.where((phase % 1.0) < duty, 1.0, -1.0)


def triangle(freq):
    phase = np.cumsum(freq) / RATE
    return 2 * np.abs(2 * (phase % 1.0) - 1) - 1


def sweep(start, end, sec, curve=1.0):
    t = t_axis(sec) / sec
    return start + (end - start) * t ** curve


def envelope(sec, attack=0.005, release=0.6):
    t = t_axis(sec)
    env = np.minimum(1.0, t / max(attack, 1e-4))
    tail = np.clip((sec - t) / (sec * release), 0, 1)
    return env * tail


def noise(sec):
    return RNG.uniform(-1, 1, int(RATE * sec))


def lowpass(x, k):
    """이동 평균으로 높은 소리를 깎는다 (k가 클수록 먹먹)."""
    return np.convolve(x, np.ones(k) / k, mode="same")


def jump():
    s = 0.14
    return square(sweep(320, 640, s), 0.4) * envelope(s)


def double_jump():
    s = 0.16
    return square(sweep(480, 960, s), 0.3) * envelope(s)


def dash():
    s = 0.16
    return (lowpass(noise(s), 6) * 0.9 + square(sweep(700, 180, s), 0.5) * 0.25) * envelope(s, release=0.8)


def land():
    s = 0.09
    return (triangle(sweep(140, 60, s)) * 0.9 + lowpass(noise(s), 14) * 0.4) * envelope(s, release=0.8)


def hit():
    s = 0.13
    return (noise(s) * 0.6 + square(sweep(220, 90, s), 0.5) * 0.5) * envelope(s, release=0.7)


def pickup():
    s = 0.18
    first = square(np.full(int(RATE * s / 2), 880.0), 0.25)
    second = square(np.full(int(RATE * s / 2), 1320.0), 0.25)
    return np.concatenate([first * envelope(s / 2, release=0.5), second * envelope(s / 2, release=0.9)])


def enhance():
    s = 0.32
    return (triangle(sweep(260, 1040, s, 1.6)) * 0.8 + square(sweep(520, 2080, s, 1.6), 0.25) * 0.2) * envelope(s, 0.02, 0.5)


def overload():
    s = 0.55
    boom = lowpass(noise(s), 10) * 0.8 + triangle(sweep(180, 40, s)) * 0.7
    return boom * envelope(s, 0.003, 0.85)


def death():
    s = 0.7
    return (square(sweep(420, 70, s, 1.3), 0.5) * 0.6 + lowpass(noise(s), 18) * 0.35) * envelope(s, 0.01, 0.7)


SOUNDS = {"jump": jump, "double_jump": double_jump, "dash": dash, "land": land, "hit": hit,
          "pickup": pickup, "enhance": enhance, "overload": overload, "death": death}
GAIN = 0.55  # 전체 음량 (클리핑 방지)


def save(name, samples):
    peak = np.max(np.abs(samples)) or 1.0
    data = (samples / peak * GAIN * 32767).astype("<i2")
    with wave.open(str(OUT / f"{name}.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data.tobytes())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SOUNDS.items():
        save(name, fn())
        print("saved", name)


if __name__ == "__main__":
    main()
