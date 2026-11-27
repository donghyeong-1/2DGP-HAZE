"""효과음 수치 재기 (S2-2, 2026-11-27). 아무도 소리를 들을 수 없어서 파일을 수치로만 본다.

재는 것 (모노 float -1~1 배열, 44.1kHz):
- length: 길이(초)
- peak_db: 최대값(dBFS). 0이면 잘림 직전
- loud_db: 가장 큰 50ms 구간의 RMS(dBFS). 귀에 들리는 '크기'에 가장 가까운 단순한 값
- rms_db: 소리가 나는 구간(최대 -40dB 안쪽)의 평균 RMS
- lead_ms: 앞 무음(최대값의 -30dB(3%)를 처음 넘는 데까지, ms). 누른 즉시 나는지
- clip: 최대값의 99.9% 이상인 표본 수가 연달아 셋 이상이면 True
- centroid: 스펙트럼 중심(Hz). 밝기
- low: 200Hz 아래 에너지 비율(0~1). 몸통(무게)
사용: python tools/sfx_metrics.py <wav 또는 폴더>...   (표를 찍는다)
"""
import os
import sys
import wave

import numpy as np

RATE = 44100


def read_wav(path):
    with wave.open(path, 'rb') as f:
        ch, sw, rate, n = f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()
        raw = f.readframes(n)
    assert sw == 2, path
    x = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, rate


def db(v):
    return float(20 * np.log10(max(float(v), 1e-9)))


def measure(x, rate=RATE):
    x = np.asarray(x, dtype=np.float64)
    if not len(x):
        return dict(length=0, peak_db=-180, loud_db=-180, rms_db=-180, lead_ms=0, clip=False, centroid=0, low=0)
    a = np.abs(x)
    peak = float(a.max())
    win = max(1, int(0.05 * rate))
    sq = np.concatenate([[0.0], np.cumsum(x * x)])
    if len(x) > win:
        w = (sq[win:] - sq[:-win]) / win
        loud = float(np.sqrt(w.max()))
    else:
        loud = float(np.sqrt(sq[-1] / len(x)))
    act = a > peak * 0.01
    rms = float(np.sqrt(np.mean(x[act] ** 2))) if act.any() else 0.0
    first = int(np.argmax(a > peak * 0.03)) if peak > 0 else 0
    hot = a >= 0.999 * 32767 / 32768
    clip = bool(np.any(hot[:-2] & hot[1:-1] & hot[2:])) if len(x) > 3 else False
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    freqs = np.fft.rfftfreq(len(x), 1 / rate)
    tot = float(spec.sum()) or 1.0
    return dict(length=len(x) / rate, peak_db=db(peak), loud_db=db(loud), rms_db=db(rms), lead_ms=first / rate * 1000,
                clip=clip, centroid=float((spec * freqs).sum() / tot), low=float(spec[freqs < 200].sum() / tot))


def measure_file(path):
    x, rate = read_wav(path)
    return measure(x, rate)


def spectrum_distance(x, y, rate=RATE, bands=24):
    """두 소리의 스펙트럼 모양 차이(0이면 같음). 로그 간격 띠의 에너지 분포(dB)를 비교한 평균 절대 차."""
    def prof(z):
        s = np.abs(np.fft.rfft(z * np.hanning(len(z)), n=8192)) ** 2
        f = np.fft.rfftfreq(8192, 1 / rate)
        edges = np.geomspace(40, 16000, bands + 1)
        e = np.array([s[(f >= lo) & (f < hi)].sum() for lo, hi in zip(edges[:-1], edges[1:])]) + 1e-12
        return 10 * np.log10(e / e.sum())
    return float(np.mean(np.abs(prof(np.asarray(x, float)) - prof(np.asarray(y, float)))))


def main(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(os.path.join(p, f) for f in os.listdir(p) if f.endswith('.wav'))
        else:
            files.append(p)
    print(f'{"name":28} {"len":>5} {"peak":>6} {"loud":>6} {"rms":>6} {"lead":>5} {"cent":>6} {"low":>5}')
    for f in files:
        m = measure_file(f)
        print(f'{os.path.basename(f)[:-4]:28} {m["length"]:5.2f} {m["peak_db"]:6.1f} {m["loud_db"]:6.1f} {m["rms_db"]:6.1f} '
              f'{m["lead_ms"]:5.1f} {m["centroid"]:6.0f} {m["low"]:5.2f}{" CLIP" if m["clip"] else ""}')


if __name__ == '__main__':
    main(sys.argv[1:] or [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'sfx')])
