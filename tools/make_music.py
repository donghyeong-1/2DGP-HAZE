"""배경음악을 코드로 합성한다 (외부 음원 없음, numpy). 직접 작곡·합성한 자체 제작 음악이라 저작권 문제가 없다.

16분음표 격자의 간단한 시퀀서다. 악기: 삼각파 베이스, 사인 겹침 패드, 사각파 아르페지오, 종소리(감쇠 사인),
킥(내려가는 사인), 스네어·하이햇(잡음). 음의 꼬리는 곡 끝에서 처음으로 넘겨 더하므로 반복 재생해도 이음매가 없다.

곡 (assets/music/<이름>.wav, 22050Hz 모노 16비트):
  title    느린 패드와 종소리. 타이틀·엔딩 (70 BPM, 8마디)
  explore  어두운 탐험·전투 (100 BPM, 16마디, D단조: Dm Dm Bb C / Dm Dm Gm A)
  boss     몰아치는 보스전 (140 BPM, 16마디)
사용: python tools/make_music.py [곡 이름 ...]
"""
import os
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'music')
RATE = 22050
RNG = np.random.default_rng(11)

NOTE = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'Bb': 10, 'B': 11}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] - 9) / 12 + (octave - 4))


# 화음: (베이스 음, 화음 구성음)
CHORDS = {
    'Dm': ('D', ['D', 'F', 'A']), 'Bb': ('Bb', ['Bb', 'D', 'F']), 'C': ('C', ['C', 'E', 'G']),
    'Gm': ('G', ['G', 'Bb', 'D']), 'A': ('A', ['A', 'C#', 'E']), 'F': ('F', ['F', 'A', 'C']),
}


class Song:
    def __init__(self, bpm, bars):
        self.step = 60.0 / bpm / 4                       # 16분음표 길이(초)
        self.bars = bars
        self.n = int(round(bars * 16 * self.step * RATE))
        self.buf = np.zeros(self.n)

    def at(self, bar, step):
        return int(round((bar * 16 + step) * self.step * RATE))

    def add(self, start, samples, gain):
        """start 위치에 소리를 더한다. 곡 끝을 넘는 꼬리는 처음으로 돌려 더한다 (이음매 없는 반복)."""
        idx = (start + np.arange(len(samples))) % self.n
        np.add.at(self.buf, idx, samples * gain)

    def save(self, name, gain=0.8):
        peak = np.max(np.abs(self.buf)) or 1.0
        data = (np.tanh(self.buf / peak * 1.4) / np.tanh(1.4) * gain * 32767).astype('<i2')   # 부드러운 눌림
        os.makedirs(OUT, exist_ok=True)
        with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(RATE)
            f.writeframes(data.tobytes())
        print(f'saved {name}.wav  {self.n / RATE:.1f}초')


def t_axis(sec):
    return np.arange(int(RATE * sec)) / RATE


def env(sec, attack=0.01, release=0.3):
    t = t_axis(sec)
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.clip((sec - t) / max(sec * release, 1e-4), 0, 1)


def tri(freq, sec):
    ph = freq * t_axis(sec)
    return 2 * np.abs(2 * (ph % 1.0) - 1) - 1


def square(freq, sec, duty=0.25):
    return np.where((freq * t_axis(sec)) % 1.0 < duty, 1.0, -1.0)


def bass(freq, sec):
    return (tri(freq, sec) * 0.8 + np.sin(2 * np.pi * freq / 2 * t_axis(sec)) * 0.5) * env(sec, 0.005, 0.35)


def pad(freqs, sec):
    t = t_axis(sec)
    out = np.zeros(len(t))
    for f in freqs:
        for det in (0.996, 1.0, 1.004):                 # 살짝 어긋난 사인 세 개로 두껍게
            out += np.sin(2 * np.pi * f * det * t) + 0.3 * np.sin(2 * np.pi * f * 2 * det * t)
    trem = 1 + 0.08 * np.sin(2 * np.pi * 0.35 * t)
    return out / (len(freqs) * 3) * trem * env(sec, sec * 0.25, 0.5)


def pluck(freq, sec):
    return square(freq, sec, 0.25) * env(sec, 0.003, 0.9) * np.exp(-t_axis(sec) * 9)


def bell(freq, sec):
    t = t_axis(sec)
    return (np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)) * np.exp(-t * 2.6)


def kick():
    sec = 0.22
    t = t_axis(sec)
    return np.sin(2 * np.pi * (48 * t + 90 * (1 - np.exp(-t * 28)) / 28)) * np.exp(-t * 16)


def snare():
    sec = 0.16
    t = t_axis(sec)
    return (RNG.uniform(-1, 1, len(t)) * 0.8 + np.sin(2 * np.pi * 190 * t) * 0.4) * np.exp(-t * 26)


def hat(open_=False):
    sec = 0.12 if open_ else 0.04
    t = t_axis(sec)
    n = RNG.uniform(-1, 1, len(t))
    return (n - np.concatenate([[0], n[:-1]])) * np.exp(-t * (18 if open_ else 70))    # 차분으로 높은 소리만


def chord_freqs(chord, octave):
    root, tones = CHORDS[chord]
    base = NOTE[tones[0]]
    return [hz(n, octave + (1 if NOTE[n] < base else 0)) for n in tones]


def title():
    s = Song(70, 8)
    prog = ['Dm', 'Bb', 'F', 'C', 'Dm', 'Bb', 'Gm', 'A']
    bar_sec = 16 * s.step
    melody = [('A', 5), ('F', 5), ('D', 5), ('E', 5), ('F', 5), ('D', 5), ('Bb', 4), ('C#', 5)]
    for b, ch in enumerate(prog):
        s.add(s.at(b, 0), pad(chord_freqs(ch, 3), bar_sec * 1.15), 0.50)
        s.add(s.at(b, 0), bass(hz(CHORDS[ch][0], 2), bar_sec * 0.9), 0.38)
        s.add(s.at(b, 4), bell(hz(*melody[b]), 2.2), 0.30)
        tones = chord_freqs(ch, 5)
        s.add(s.at(b, 10), bell(tones[(b + 1) % 3], 1.8), 0.16)
        s.add(s.at(b, 14), bell(tones[(b + 2) % 3] * 2, 1.4), 0.09)
    s.save('title', 0.7)


def explore():
    s = Song(100, 16)
    prog = ['Dm', 'Dm', 'Bb', 'C', 'Dm', 'Dm', 'Gm', 'A'] * 2
    bar_sec = 16 * s.step
    lead = {8: [('D', 5, 0, 6), ('F', 5, 6, 4), ('A', 5, 10, 6)], 9: [('G', 5, 0, 8), ('F', 5, 8, 8)],
            10: [('F', 5, 0, 6), ('D', 5, 6, 4), ('Bb', 4, 10, 6)], 11: [('C', 5, 0, 8), ('E', 5, 8, 8)],
            12: [('D', 5, 0, 6), ('A', 5, 6, 4), ('F', 5, 10, 6)], 13: [('E', 5, 0, 8), ('D', 5, 8, 8)],
            14: [('Bb', 4, 0, 6), ('D', 5, 6, 4), ('G', 5, 10, 6)], 15: [('E', 5, 0, 8), ('C#', 5, 8, 8)]}
    for b, ch in enumerate(prog):
        root = hz(CHORDS[ch][0], 2)
        s.add(s.at(b, 0), pad(chord_freqs(ch, 3), bar_sec * 1.1), 0.34)
        for st in (0, 3, 6, 8, 11, 14):                      # 싱코페이션 베이스
            s.add(s.at(b, st), bass(root * (2 if st in (6, 14) else 1), s.step * 2.6), 0.50)
        tones = chord_freqs(ch, 4)
        for st in range(0, 16, 2):                           # 8분음표 아르페지오 (둘째 바퀴는 한 옥타브 위를 섞는다)
            f = tones[(st // 2) % 3] * (2 if (b >= 8 and st % 8 == 6) else 1)
            s.add(s.at(b, st), pluck(f, s.step * 3), 0.16)
        for st in (0, 10):
            s.add(s.at(b, st), kick(), 0.75)
        s.add(s.at(b, 4), snare(), 0.30)
        s.add(s.at(b, 12), snare(), 0.34)
        for st in range(2, 16, 4):
            s.add(s.at(b, st), hat(st == 14), 0.14)
        for name, octave, st, length in lead.get(b, []):     # 둘째 바퀴에만 종소리 선율
            s.add(s.at(b, st), bell(hz(name, octave), s.step * length * 1.6), 0.20)
    s.save('explore', 0.72)


def boss():
    s = Song(140, 16)
    prog = ['Dm', 'Dm', 'Bb', 'A', 'Dm', 'F', 'Gm', 'A'] * 2
    bar_sec = 16 * s.step
    riff = [0, 0, 12, 0, 0, 10, 0, 12, 0, 0, 12, 0, 7, 0, 10, 12]            # 베이스 리프 (반음 간격)
    for b, ch in enumerate(prog):
        root = hz(CHORDS[ch][0], 2)
        s.add(s.at(b, 0), pad(chord_freqs(ch, 3), bar_sec * 1.05), 0.26)
        for st in range(16):                                 # 16분음표로 달리는 베이스
            s.add(s.at(b, st), bass(root * 2 ** (riff[st] / 12), s.step * 1.3), 0.44)
        tones = chord_freqs(ch, 5)
        for st in range(0, 16, 3):                           # 엇박 아르페지오
            s.add(s.at(b, st), pluck(tones[(st // 3 + b) % 3], s.step * 2.5), 0.15)
        for st in (0, 4, 8, 12):                             # 네 박 킥
            s.add(s.at(b, st), kick(), 0.85)
        for st in (4, 12):
            s.add(s.at(b, st), snare(), 0.42)
        if b % 4 == 3:                                       # 4마디마다 채워 넣기
            for st in (13, 14, 15):
                s.add(s.at(b, st), snare(), 0.30)
        for st in range(2, 16, 2):
            s.add(s.at(b, st), hat(st % 8 == 6), 0.13)
        if b >= 8:                                           # 뒤 절반은 높은 선율이 붙는다
            top = chord_freqs(ch, 5)
            for st, i in ((0, 2), (6, 1), (10, 0), (12, 2)):
                s.add(s.at(b, st), bell(top[i] * (2 if st == 12 else 1), s.step * 5), 0.17)
    s.save('boss', 0.74)


SONGS = {'title': title, 'explore': explore, 'boss': boss}


def main():
    for name in (sys.argv[1:] or list(SONGS)):
        SONGS[name]()


if __name__ == '__main__':
    main()
