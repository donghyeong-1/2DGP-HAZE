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
        if n > 0:                                    # 총 길이 밖에서 시작하는 조각은 버린다
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



# ----- 2026-11-21 퀄리티 계획 1-7: 무기별 명중 (적 피격음 위에 겹친다), 적별 공격 예고 -----
def impact_pipe():
    """철파이프 명중: 둔탁한 쇠막대 '퍽' + 짧은 쇳소리."""
    s = 0.16
    thud = drive(sub_drop(s, 150, 60, 20) * 1.2, 1.6)
    return thud * 0.8 + metal((640, 1010, 1490), s, 26) * 0.3 + lowpass(noise(s), 4) * 0.4 * envelope(s, 0.001, 0.3)


def impact_knife():
    """식칼 명중: 날카롭게 베는 '슥' (높은 잡음이 빠르게 지나간다)."""
    s = 0.12
    hiss = (noise(s) - lowpass(noise(s), 6)) * envelope(s, 0.002, 0.7)
    return hiss * 0.9 + metal((2900, 4100), s, 40) * 0.25


def impact_gauntlet():
    """건틀릿 명중: 에너지가 터지는 '쿵' + 지직거림."""
    s = 0.24
    t = t_axis(s)
    zap = square(sweep(520, 140, s), 0.5) * (1 + 0.6 * np.sin(2 * np.pi * 45 * t)) * 0.3
    return drive(sub_drop(s, 120, 40, 12) * 1.3, 2.0) * 0.8 + zap * envelope(s, 0.002, 0.8) + lowpass(noise(s), 3) * 0.35 * envelope(s, 0.002, 0.5)


def windup_slum():
    """슬럼 폐인의 예고: 낮게 끄는 신음."""
    s = 0.32
    t = t_axis(s)
    f = sweep(150, 115, s) * (1 + 0.03 * np.sin(2 * np.pi * 9 * t))
    return (square(f, 0.4) * 0.3 + triangle(f) * 0.5 + lowpass(noise(s), 8) * 0.25) * envelope(s, 0.05, 0.5)


def windup_thrower():
    """고철 투척병의 예고: 고철을 쥐는 짤그락."""
    s = 0.24
    return place(s, [(0.0, metal((1900, 2700), 0.05, 70)), (0.07, metal((1650, 2450), 0.05, 70) * 0.8),
                     (0.12, metal((2100, 3000), 0.06, 60) * 0.6)]) + lowpass(noise(s), 6) * 0.15 * envelope(s)


def windup_hound():
    """안개 사냥개의 예고: 으르렁 (빠르게 떨리는 낮은 소리)."""
    s = 0.36
    t = t_axis(s)
    growl = (triangle(sweep(95, 120, s)) * 0.6 + lowpass(noise(s), 5) * 0.5) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 26 * t)))
    return growl * envelope(s, 0.03, 0.4)


def windup_guard():
    """중장갑 간수의 예고: 갑옷이 삐걱이며 무겁게 드는 소리."""
    s = 0.4
    creak = square(sweep(210, 160, s), 0.15) * 0.25 * (1 + 0.5 * np.sin(2 * np.pi * 17 * t_axis(s)))
    return (metal((310, 470, 690), s, 7) * 0.5 + creak + triangle(sweep(70, 55, s)) * 0.4) * envelope(s, 0.06, 0.5)



# ----- 2026-11-21 계획 2-3 환경음 (가끔 흩뿌리는 짧은 소리, 작게) -----
def amb_drip():
    """슬럼: 천장에서 떨어진 물방울이 웅덩이에 '똑' (올라가는 짧은 사인 + 메아리)."""
    s = 0.5
    t = t_axis(0.09)
    plip = np.sin(2 * np.pi * np.cumsum(sweep(900, 1700, 0.09)) / RATE) * np.exp(-t * 40)
    return place(s, [(0.0, plip), (0.17, plip * 0.35), (0.33, plip * 0.12)])


def amb_steam():
    """공장: 배관에서 새는 증기 '쉬익' (높은 잡음이 부풀었다 줄어듦) + 낮은 쇳소리."""
    s = 0.8
    hiss = (noise(s) - lowpass(noise(s), 4)) * np.sin(np.pi * np.clip(t_axis(s) / s, 0, 1)) ** 1.5
    return hiss * 0.8 + metal((180, 290), s, 5) * 0.25


def amb_wind():
    """탑: 높은 곳을 지나는 낮은 바람 (먹먹한 잡음이 천천히 부풀었다 줄어듦)."""
    s = 0.95
    t = t_axis(s)
    gust = lowpass(noise(s), 30) * np.sin(np.pi * t / s) ** 2 * (1 + 0.3 * np.sin(2 * np.pi * 3 * t))
    return gust + triangle(sweep(110, 95, s)) * 0.12 * np.sin(np.pi * t / s)


def amb_forge():
    """은신처: 화로에서 장작·불똥이 '탁, 타닥' (짧은 딸깍 몇 번 + 낮은 불 울림)."""
    s = 0.6
    crack = lambda k: (noise(0.02) * envelope(0.02, 0.0005, 0.9)) * k
    roar = lowpass(noise(s), 25) * 0.35 * np.sin(np.pi * t_axis(s) / s)
    return roar + place(s, [(0.02, crack(1.0)), (0.19, crack(0.6)), (0.24, crack(0.8)), (0.41, crack(0.45))])


# ----- 2026-11-21 빠진 소리 채우기: 식칼·사슬 구간별, 무기별 궁극기 마무리, 구간 진입, 심장, 마지막 처치 -----
def throw_fade():
    """페이드 식칼: 힘 빠진 낮은 휙."""
    s = 0.13
    return (lowpass(noise(s), 14) * 0.45 + square(sweep(140, 260, s), 0.4) * 0.2) * envelope(s, 0.012, 0.8) * 0.75


def throw_awake():
    """각성 식칼: 날카롭게 높아지는 두 겹 휙."""
    s = 0.12
    one = (lowpass(noise(s), 4) * 0.5 + square(sweep(300, 760, s), 0.35) * 0.35) * envelope(s, 0.008, 0.7)
    return place(0.16, [(0.0, one), (0.035, one * 0.6)])


def throw_critical():
    """위험 식칼: 거칠게 찢는 휙 + 쇳소리."""
    s = 0.15
    return ((lowpass(noise(s), 3) * 0.7 + square(sweep(260, 900, s), 0.25) * 0.3) * envelope(s, 0.006, 0.8)
            + metal((2900, 4100), s, 35) * 0.25)


def throw_enhanced():
    """강화 식칼: 여러 자루가 한꺼번에 풀리는 반짝임."""
    s = 0.24
    one = (square(sweep(500, 1400, 0.1), 0.25) * 0.3 + lowpass(noise(0.1), 5) * 0.4) * envelope(0.1, 0.004, 0.7)
    return place(s, [(0.0, one), (0.04, one * 0.8), (0.08, one * 0.6), (0.0, triangle(sweep(400, 1200, s)) * 0.25 * envelope(s, 0.01, 0.9))])


def _chain(pitch, wind, count=11):
    s = 0.22
    clicks = place(s, [(0.018 * i, metal((2400 * pitch + 160 * (i % 3), 3700 * pitch), 0.03, 140) * (1 - i / 14)) for i in range(count)])
    return clicks * 0.7 + lowpass(noise(s), 6) * wind * envelope(s, 0.01, 0.9)


def chain_throw_fade():
    return _chain(0.7, 0.25, 7) * 0.8          # 느리고 가볍게 몇 고리만


def chain_throw_awake():
    return _chain(1.2, 0.5)


def chain_throw_critical():
    s = 0.24
    return place(s, [(0.0, _chain(1.0, 0.7, 13)), (0.0, drive(sub_drop(s, 120, 60, 12), 1.5) * 0.4)])   # 묵직한 휘두름이 깔린다


def chain_throw_enhanced():
    s = 0.3
    return place(s, [(0.0, _chain(1.35, 0.5, 14)), (0.0, triangle(sweep(500, 1500, s)) * 0.25 * envelope(s, 0.01, 0.9))])


def chain_latch_heavy():
    """위험·강화 갈고리: 깊게 박히는 쇠 울림 + 저음."""
    s = 0.3
    return metal((780, 1240, 1870, 2650), s, 14) * 0.7 + drive(sub_drop(s, 140, 45, 10), 1.8) * 0.6 + noise(s) * 0.4 * envelope(s, 0.002, 0.1)


def _ult_final_base():
    return ult_final()


def ult_final_pipe():
    """철파이프 궁극기 마무리: 큰 폭발 + 낮은 쇠 울림 (내리친 쇳덩이)."""
    s = 0.98
    return place(s, [(0.0, _ult_final_base()), (0.0, metal((180, 284, 415), 0.9, 4) * 0.45)])


def ult_final_knife():
    """식칼 궁극기 마무리: 폭발 + 수많은 칼날이 흩어지는 높은 쇳소리."""
    s = 0.98
    blades = place(0.6, [(0.03 * i, metal((3100 + 220 * (i % 4), 4500), 0.05, 90) * (1 - i / 22)) for i in range(18)])
    return place(s, [(0.0, _ult_final_base() * 0.85), (0.05, blades * 0.5)])


def ult_final_gauntlet():
    """건틀릿 궁극기 마무리: 폭발 + 두 번 치는 압력파(낮고 두껍다)."""
    s = 0.98
    wave_ = drive(sub_drop(0.5, 95, 24, 4.5) * 1.5, 2.4)
    return place(s, [(0.0, _ult_final_base() * 0.8), (0.0, wave_), (0.18, wave_ * 0.7)])


def ult_final_chain():
    """사슬 궁극기 마무리: 폭발 + 사슬이 한꺼번에 조여드는 철컥임."""
    s = 0.98
    rattle = place(0.5, [(0.022 * i, metal((1900 + 140 * (i % 3), 2900), 0.03, 120)) for i in range(16)])
    return place(s, [(0.0, _ult_final_base() * 0.85), (0.02, rattle * 0.45), (0.35, chain_latch_heavy() * 0.6)])


def zone_awake():
    """각성 구간에 들어섬: 올라가는 세 음(장조) + 바람."""
    s = 0.55
    notes = [(0.0, 392), (0.09, 494), (0.18, 587)]
    parts = [(st, (triangle(np.full(int(RATE * 0.3), f)) * 0.4 + square(np.full(int(RATE * 0.3), f * 2), 0.25) * 0.1)
              * envelope(0.3, 0.004, 0.8)) for st, f in notes]
    return place(s, parts + [(0.0, lowpass(noise(s), 6) * 0.25 * envelope(s, 0.1, 0.9))])


def heartbeat():
    """심장 소리: 낮은 '쿵-쿵' 두 번."""
    s = 0.42
    thump = lambda k: drive(sub_drop(0.16, 85, 45, 22) * k, 1.4)   # noqa: E731
    return place(s, [(0.0, thump(1.0)), (0.17, thump(0.7))])


def kill_last():
    """방의 마지막 적: 깊은 일격 + 맑게 울리는 종소리."""
    s = 0.9
    hit_ = drive(sub_drop(0.35, 150, 40, 9) * 1.3, 2.0) + noise(0.35) * 0.4 * envelope(0.35, 0.001, 0.2)
    bell = metal((880, 1318, 1760, 2637), s, 3.5) * 0.35
    return place(s, [(0.0, hit_), (0.05, bell)])


SOUNDS = {"warn_low": warn_low, "warn_high": warn_high, "overload_zap": overload_zap, "stun_end": stun_end, "jump": jump, "double_jump": double_jump, "dash": dash, "land": land, "hit": hit,
          "pickup": pickup, "enhance": enhance, "overload": overload, "death": death,
          "swing": swing, "swing_fade": swing_fade, "swing_awake": swing_awake, "swing_critical": swing_critical,
          "swing_enhanced": swing_enhanced, "enemy_hit": enemy_hit, "enemy_die": enemy_die, "throw": throw,
          # 2026-11-19 추가
          "chain_throw": chain_throw, "chain_latch": chain_latch, "chain_clash": chain_clash,
          "ult_cast": ult_cast, "ult_hit": ult_hit,
          "ark_bullet": ark_bullet, "ark_teleport": ark_teleport, "ark_roar": ark_roar,
          "ark_absorb": ark_absorb, "ark_burst": ark_burst, "ark_field": ark_field,
          # 2026-11-21 추가
          "impact_pipe": impact_pipe, "impact_knife": impact_knife, "impact_gauntlet": impact_gauntlet,
          "windup_slum": windup_slum, "windup_thrower": windup_thrower, "windup_hound": windup_hound,
          "windup_guard": windup_guard,
          "amb_drip": amb_drip, "amb_steam": amb_steam, "amb_wind": amb_wind, "amb_forge": amb_forge,
          # 2026-11-21 빠진 소리 채우기 (무기·구간·강화·궁극기·체력)
          "throw_fade": throw_fade, "throw_awake": throw_awake, "throw_critical": throw_critical, "throw_enhanced": throw_enhanced,
          "chain_throw_fade": chain_throw_fade, "chain_throw_awake": chain_throw_awake,
          "chain_throw_critical": chain_throw_critical, "chain_throw_enhanced": chain_throw_enhanced,
          "chain_latch_heavy": chain_latch_heavy,
          "ult_final_pipe": ult_final_pipe, "ult_final_knife": ult_final_knife, "ult_final_gauntlet": ult_final_gauntlet,
          "ult_final_chain": ult_final_chain,
          "zone_awake": zone_awake, "heartbeat": heartbeat, "kill_last": kill_last}
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
