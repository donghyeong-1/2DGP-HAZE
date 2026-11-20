"""효과음을 코드로 직접 합성해 assets/sfx/*.wav 로 저장한다. (외부 음원 없음, 저작권 문제 없음)

사각파·삼각파·잡음에 짧은 엔벨로프를 걸어 8비트 느낌으로 만든다. 소리를 바꾸려면 SOUNDS의 값을 고쳐 다시 실행한다.
사용: python tools/make_sfx.py
"""
import wave
import zlib
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
RATE = 22050
RNG = np.random.default_rng(7)  # 잡음이 매번 같도록 고정 (main에서 소리마다 이름으로 다시 고정한다)


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


def swing():
    s = 0.11
    return (lowpass(noise(s), 5) * 0.7 + triangle(sweep(260, 520, s)) * 0.25) * envelope(s, 0.01, 0.8)


def overload_zap():
    s = 0.55
    buzz = square(sweep(900, 140, s, 1.4), 0.5) * 0.45 * (1 + 0.6 * np.sin(2 * np.pi * 38 * t_axis(s)))   # 치직거리는 하강음
    return (buzz + lowpass(noise(s), 2) * 0.7 + triangle(sweep(70, 40, s)) * 0.5) * envelope(s, 0.004, 0.9)


def stun_end():
    s = 0.22
    return (triangle(sweep(300, 620, s)) * 0.45 + square(sweep(600, 1200, s), 0.25) * 0.12) * envelope(s, 0.006, 0.8)


def swing_fade():
    s = 0.13
    return (lowpass(noise(s), 14) * 0.5 + triangle(sweep(150, 230, s)) * 0.2) * envelope(s, 0.012, 0.85) * 0.7   # 약하고 낮다


def swing_awake():
    s = 0.12
    return (lowpass(noise(s), 4) * 0.6 + triangle(sweep(320, 760, s)) * 0.35) * envelope(s, 0.008, 0.8)         # 밝고 높다


def swing_critical():
    s = 0.15
    return (lowpass(noise(s), 3) * 0.8 + square(sweep(200, 620, s), 0.3) * 0.3 + triangle(sweep(90, 60, s)) * 0.4) * envelope(s, 0.008, 0.85)   # 묵직하고 거칠다


def swing_enhanced():
    s = 0.2
    return (triangle(sweep(260, 1000, s)) * 0.4 + square(sweep(520, 1560, s), 0.25) * 0.22 + lowpass(noise(s), 5) * 0.4) * envelope(s, 0.01, 0.85)   # 위로 쓸어 올리는 반짝임


def enemy_hit():
    s = 0.09
    return (square(sweep(520, 240, s), 0.5) * 0.5 + noise(s) * 0.35) * envelope(s, release=0.7)


def enemy_die():
    s = 0.32
    return (square(sweep(380, 90, s, 1.2), 0.5) * 0.5 + lowpass(noise(s), 10) * 0.4) * envelope(s, 0.005, 0.75)


def throw():
    s = 0.12
    return (lowpass(noise(s), 8) * 0.5 + square(sweep(180, 420, s), 0.4) * 0.3) * envelope(s, 0.01, 0.7)


def warn_low():
    """페이드 진입 경고: 낮게 가라앉는 두 번의 맥박."""
    s = 0.5
    t = t_axis(s)
    beat = np.exp(-((t % 0.25) * 22))
    return (triangle(sweep(150, 90, s)) * 0.8 + np.sin(2 * np.pi * 60 * t) * 0.6) * beat * envelope(s, 0.004, 0.5)


def warn_high():
    """위험 구간 진입 경고: 높아지는 세 번의 삑."""
    s = 0.36
    t = t_axis(s)
    gate = ((t % 0.12) < 0.07).astype(float)
    return square(sweep(880, 1320, s), 0.3) * gate * envelope(s, 0.004, 0.4)


# ----- 2026-11-19 전용 효과음: 사슬, 궁극기, 최종 보스 아크 -----
def metal(freqs, sec, decay):
    """서로 배음이 맞지 않는 사인을 겹쳐 쇠붙이 울림을 만든다."""
    t = t_axis(sec)
    return sum(np.sin(2 * np.pi * f * t) * (0.8 ** i) for i, f in enumerate(freqs)) * np.exp(-t * decay)


def place(total, parts):
    """(시작 초, 소리) 조각들을 total초 길이에 겹쳐 놓는다."""
    out = np.zeros(int(RATE * total))
    for start, x in parts:
        i = int(RATE * start)
        n = min(len(x), len(out) - i)
        out[i:i + n] += x[:n]
    return out


def chain_throw():
    """사슬이 풀려 나가는 소리: 짧은 쇠 고리 딸깍임 여러 번 + 바람."""
    s = 0.22
    clicks = place(s, [(0.018 * i, metal((2400 + 160 * (i % 3), 3700), 0.03, 140) * (1 - i / 14)) for i in range(11)])
    return clicks * 0.7 + lowpass(noise(s), 6) * 0.45 * envelope(s, 0.01, 0.9)


def chain_latch():
    """갈고리가 박히는 소리: 짧고 단단한 쇠 울림."""
    s = 0.18
    return metal((1180, 1870, 2650, 3420), s, 30) * 0.8 + noise(s) * 0.5 * envelope(s, 0.002, 0.15)


def chain_clash():
    """끌려온 적끼리 부딪치는 소리: 묵직한 두 번 쿵 + 쇠 울림."""
    s = 0.34
    thud = (triangle(sweep(130, 55, 0.12)) + lowpass(noise(0.12), 10) * 0.6) * envelope(0.12, 0.002, 0.8)
    return place(s, [(0.0, thud), (0.06, thud * 0.8), (0.0, metal((620, 980, 1530), s, 9) * 0.35)])


def sub_drop(sec, f0, f1, decay):
    """떨어지는 낮은 사인 (몸으로 느끼는 '쿵')."""
    t = t_axis(sec)
    phase = np.cumsum(f1 + (f0 - f1) * np.exp(-t * 18)) / RATE
    return np.sin(2 * np.pi * phase) * np.exp(-t * decay)


def drive(x, k):
    """부드럽게 찌그러뜨려 두껍고 거칠게 (tanh 포화)."""
    return np.tanh(x * k) / np.tanh(k)


def ult_cast():
    """궁극기 시전 (2026-11-20 강하게): 0.3초 동안 빨려 들며 차오르다가, 바닥을 때리는 큰 일격.
    차오름 = 점점 커지는 바람 + 올라가는 음 + 낮게 떨리는 울림, 일격 = 짧은 깨짐 + 떨어지는 저음 + 쇳소리 울림 + 긴 꼬리."""
    gather = 0.3
    ramp = np.linspace(0, 1, int(RATE * gather)) ** 2.2
    rise = (lowpass(noise(gather), 3) * 0.7 + triangle(sweep(90, 720, gather, 1.6)) * 0.45
            + np.sin(2 * np.pi * 45 * t_axis(gather)) * 0.5) * ramp
    s = 0.62
    crack = noise(0.03) * envelope(0.03, 0.0005, 0.9) * 1.3
    boom = drive(sub_drop(s, 110, 30, 4.5) * 1.4 + lowpass(noise(s), 6) * 0.6 * np.exp(-t_axis(s) * 7), 2.2)
    ring = metal((220, 347, 512, 771), s, 6) * 0.3
    return place(gather + s, [(0.0, rise), (gather, crack), (gather, boom), (gather + 0.01, ring)])


def ult_hit():
    """궁극기 연타 한 번 (강하게): 짧은 저음 펀치 + 날카로운 타격."""
    s = 0.13
    punch = drive(sub_drop(s, 170, 55, 22) * 1.2, 1.8)
    return punch * 0.8 + noise(s) * 0.5 * envelope(s, 0.001, 0.35) + square(sweep(700, 260, s), 0.3) * 0.2 * envelope(s, 0.001, 0.6)


def ult_final():
    """궁극기 마지막 일격 (강하게): 두 번 겹친 큰 폭발 + 땅울림 꼬리 + 위로 흩어지는 반짝임."""
    s = 0.95
    t2 = t_axis(s)
    boom = drive(sub_drop(s, 130, 26, 3.2) * 1.6 + lowpass(noise(s), 5) * 0.8 * np.exp(-t2 * 5), 2.6)
    second = drive(sub_drop(0.5, 90, 30, 6) * 1.2, 2.0)
    crack = noise(0.04) * envelope(0.04, 0.0005, 0.9) * 1.4
    rumble = lowpass(noise(s), 40) * 1.6 * np.exp(-t2 * 2.5)
    glint = (square(sweep(1200, 2600, 0.5), 0.2) * 0.1 + triangle(sweep(600, 1300, 0.5)) * 0.12) * envelope(0.5, 0.05, 0.9)
    return place(s, [(0.0, crack), (0.0, boom), (0.07, second), (0.0, rumble), (0.1, glint)])


def _pew(f):
    return (square(sweep(f, f * 0.35, 0.14), 0.35) * 0.5 + triangle(sweep(f * 0.5, f * 0.2, 0.14)) * 0.4) * envelope(0.14, 0.003, 0.8)


def ark_bullet():
    """아크 탄막: 부채꼴로 퍼지는 헤이즈 탄 세 발 (조금씩 어긋나게)."""
    s = 0.3
    return place(s, [(0.0, _pew(1250)), (0.05, _pew(1100)), (0.1, _pew(950))]) + lowpass(noise(s), 12) * 0.15 * envelope(s)


def ark_teleport():
    """아크가 흩어졌다 나타나는 소리: 빨려 들어가는 바람(점점 커짐) 뒤 낮은 '훅'."""
    a = 0.2
    ramp = np.linspace(0, 1, int(RATE * a))
    suck = lowpass(noise(a), 5) * ramp ** 2 + triangle(sweep(300, 900, a)) * 0.2 * ramp
    b = 0.14
    pop = (np.sin(2 * np.pi * np.cumsum(sweep(260, 80, b)) / RATE) * 0.9 + lowpass(noise(b), 9) * 0.4) * envelope(b, 0.002, 0.8)
    return place(a + b, [(0.0, suck * 0.8), (a, pop)])


def ark_roar():
    """페이즈가 바뀔 때 아크의 포효: 흔들리는 낮은 쇳소리 + 거친 숨."""
    s = 0.9
    t = t_axis(s)
    f = sweep(95, 60, s) * (1 + 0.04 * np.sin(2 * np.pi * 7 * t))
    growl = square(f, 0.5) * 0.4 + square(f * 1.5, 0.3) * 0.2 + triangle(f * 0.5) * 0.5
    growl *= 1 + 0.35 * np.sin(2 * np.pi * 31 * t)
    return (growl + lowpass(noise(s), 7) * 0.5) * envelope(s, 0.06, 0.6)


def ark_absorb():
    """흡수 파동: 양끝에서 조여 드는 소리 (점점 커지며 내려간다)."""
    s = 0.6
    grow = np.linspace(0.15, 1.0, int(RATE * s)) ** 1.5
    tone = triangle(sweep(700, 160, s)) * 0.6 + square(sweep(350, 80, s), 0.3) * 0.15
    return (tone + lowpass(noise(s), 10) * 0.35) * grow * envelope(s, 0.01, 0.12)


def ark_burst():
    """과충전 파동: 아크에서 퍼져 나가는 소리 (쿵 하고 높아지며 멀어진다)."""
    s = 0.6
    boom = (triangle(sweep(90, 40, 0.25)) + lowpass(noise(0.25), 8) * 0.7) * envelope(0.25, 0.002, 0.9)
    ring = (triangle(sweep(260, 1100, s, 0.8)) * 0.4 + square(sweep(520, 2200, s, 0.8), 0.25) * 0.1) * envelope(s, 0.01, 0.9)
    return place(s, [(0.0, boom), (0.02, ring)])


def ark_field():
    """오염 장판이 깔리는 소리: 부글거리는 쉿 소리."""
    s = 0.45
    t = t_axis(s)
    bubble = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * (14 + 10 * t) * t))
    return (lowpass(noise(s), 3) * 0.6 * bubble + triangle(sweep(180, 120, s)) * 0.3) * envelope(s, 0.03, 0.7)


SOUNDS = {"warn_low": warn_low, "warn_high": warn_high, "overload_zap": overload_zap, "stun_end": stun_end, "jump": jump, "double_jump": double_jump, "dash": dash, "land": land, "hit": hit,
          "pickup": pickup, "enhance": enhance, "overload": overload, "death": death,
          "swing": swing, "swing_fade": swing_fade, "swing_awake": swing_awake, "swing_critical": swing_critical,
          "swing_enhanced": swing_enhanced, "enemy_hit": enemy_hit, "enemy_die": enemy_die, "throw": throw,
          # 2026-11-19 추가
          "chain_throw": chain_throw, "chain_latch": chain_latch, "chain_clash": chain_clash,
          "ult_cast": ult_cast, "ult_hit": ult_hit, "ult_final": ult_final,
          "ark_bullet": ark_bullet, "ark_teleport": ark_teleport, "ark_roar": ark_roar,
          "ark_absorb": ark_absorb, "ark_burst": ark_burst, "ark_field": ark_field}
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
    global RNG
    for name, fn in SOUNDS.items():
        RNG = np.random.default_rng(zlib.crc32(name.encode()))   # 소리마다 따로: 하나를 고쳐도 다른 소리가 바뀌지 않는다
        save(name, fn())
        print("saved", name)


if __name__ == "__main__":
    main()
