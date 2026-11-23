"""효과음 가공 공용 함수 (2026-11-24 v7 효과음 개편). CC0 원본(ogg)을 읽어 자르고, 겹치고, 음 높이를 바꾸고, wav로 쓴다.

원본 읽기는 게임이 이미 쓰는 SDL_mixer로 한다 (ogg 해독용 별도 라이브러리 없이). 결과는 44.1kHz 16비트 모노.
tools/make_sfx_v2.py가 쓴다.
"""
import ctypes
import os
import wave

import numpy as np

RATE = 44100
_mixer_open = False


def _open_mixer():
    global _mixer_open
    if _mixer_open:
        return
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')       # 소리를 내지 않고 해독만 한다
    import sdl2
    import sdl2.sdlmixer as mix
    sdl2.SDL_Init(sdl2.SDL_INIT_AUDIO)
    mix.Mix_Init(mix.MIX_INIT_OGG)
    if mix.Mix_OpenAudio(RATE, sdl2.AUDIO_S16LSB, 2, 1024) != 0:
        raise RuntimeError('SDL_mixer를 열 수 없다: ' + mix.Mix_GetError().decode())
    _mixer_open = True


def load(path):
    """ogg/wav -> float 모노 배열(-1~1), RATE Hz."""
    _open_mixer()
    import sdl2.sdlmixer as mix
    chunk = mix.Mix_LoadWAV(path.encode('utf-8'))
    if not chunk:
        raise FileNotFoundError(path)
    c = chunk.contents
    raw = ctypes.string_at(c.abuf, c.alen)
    data = np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768.0
    mix.Mix_FreeChunk(chunk)
    return data.reshape(-1, 2).mean(axis=1)


def trim(x, threshold=0.01, pad=0.004):
    """앞뒤의 거의 무음 부분을 잘라 낸다 (앞은 pad초 남긴다)."""
    idx = np.nonzero(np.abs(x) > threshold * (np.max(np.abs(x)) or 1.0))[0]
    if not len(idx):
        return x
    start = max(0, idx[0] - int(pad * RATE))
    return x[start:idx[-1] + 1]


def fade(x, fade_in=0.002, fade_out=0.03):
    x = x.copy()
    a, b = int(fade_in * RATE), int(fade_out * RATE)
    if a:
        x[:a] *= np.linspace(0, 1, min(a, len(x)))[:len(x[:a])]
    if b:
        n = min(b, len(x))
        x[-n:] *= np.linspace(1, 0, n)
    return x


def pitch(x, k):
    """k배 높게 (길이는 1/k)."""
    if abs(k - 1.0) < 1e-6:
        return x
    n = max(2, int(len(x) / k))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def cut(x, length):
    """length초로 자르고 끝을 부드럽게 줄인다."""
    return fade(x[:int(length * RATE)], 0.0, min(0.05, length * 0.3))


def mix(total, parts):
    """(시작 초, 소리, 크기) 조각을 total초 안에 겹친다."""
    out = np.zeros(int(RATE * total), dtype=np.float32)
    for start, x, gain in parts:
        i = int(RATE * start)
        n = min(len(x), len(out) - i)
        if n > 0:
            out[i:i + n] += x[:n] * gain
    return out


def highpass(x, k=6):
    """이동 평균을 빼서 낮은 소리를 덜어낸다 (k가 클수록 많이 남긴다)."""
    return x - np.convolve(x, np.ones(k) / k, mode='same')


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')


def save(path, x, peak=0.85):
    x = np.asarray(x, dtype=np.float32)
    m = float(np.max(np.abs(x))) or 1.0
    data = (np.tanh(x / m * 1.15) / np.tanh(1.15) * peak * 32767).astype('<i2')   # 살짝 포화시켜 단단하게
    with wave.open(path, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(data.tobytes())
