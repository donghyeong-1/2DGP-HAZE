"""효과음 v2 (2026-11-24, 사용자: 효과음 전반을 손봐야 한다). CC0 녹음 원본 + 합성을 겹쳐 assets/sfx/*.wav 를 다시 만든다.

- 원본: Kenney(kenney.nl) Impact Sounds·Interface Sounds·Sci-fi Sounds·RPG Audio·Digital Audio, 모두 CC0.
  쓰는 파일만 assets/sfx_src/kenney/<묶음>/ 에 둔다 (라이선스 문서 포함).
- 합성: 휘두르기 바람(띠 잡음 쓸기), 낮은 쿵(떨어지는 사인), 종소리(배음) — 녹음 원본에 없는 것.
- 결과: 44.1kHz 16비트 모노. tools/make_sfx.py(옛 8비트 합성)를 먼저 돌린 뒤 이것을 돌리면 여기 있는 소리만 덮어쓴다.
  여기 없는 소리(적 예고음·경고음·심장·환경음)는 make_sfx.py 그대로.

사용:
  python tools/make_sfx_v2.py --import <Kenney 압축을 푼 폴더>   (처음 한 번: 쓰는 원본만 assets/sfx_src/kenney로 복사)
  python tools/make_sfx_v2.py                                   (assets/sfx 다시 만들기)
필요: numpy, pysdl2(SDL_mixer, ogg 읽기)
"""
import glob
import os
import shutil
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx_kit as K  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'sfx_src', 'kenney')
OUT = os.path.join(ROOT, 'assets', 'sfx')
R = K.RATE
_used = set()
_cache = {}
RNG = np.random.default_rng(1)


# ----- 원본 -----
def S(pack, name, length=None, k=1.0, gain=1.0):
    """Kenney 원본 하나: 앞뒤 무음을 자르고, k배 음 높이, length초로 자른다."""
    _used.add((pack, name))
    key = (pack, name)
    if key not in _cache:
        _cache[key] = K.trim(K.load(os.path.join(SRC, pack, name + '.ogg')))
    x = K.pitch(_cache[key], k)
    if length:
        x = K.cut(x, length)
    return x * gain


# ----- 합성 -----
def t_axis(sec):
    return np.arange(int(R * sec)) / R


def whoosh(sec, f0, f1, bright=1.0, peak=0.35):
    """휘두르는 바람: 잡음을 띠 필터로 걸러 중심 주파수를 f0 -> f1로 쓸고, 소리는 빨리 솟았다가 사라진다."""
    n = int(R * sec)
    noise = RNG.uniform(-1, 1, n)
    t = np.linspace(0, 1, n)
    fc = f0 + (f1 - f0) * np.sin(np.pi * np.minimum(1, t / 0.9) / 2)
    out = np.zeros(n)
    lp1 = lp2 = 0.0
    for i in range(n):                                   # 두 단 한 극 필터: 저역 통과 두 개의 차 = 띠
        a = 1 - np.exp(-2 * np.pi * fc[i] * 1.6 / R)
        b = 1 - np.exp(-2 * np.pi * fc[i] * 0.45 / R)
        lp1 += a * (noise[i] - lp1)
        lp2 += b * (noise[i] - lp2)
        out[i] = lp1 - lp2 * (1 - 0.3 * bright)
    env = np.where(t < peak, (t / peak) ** 1.5, ((1 - t) / (1 - peak)) ** 2.2)
    return out * env


def sub(sec, f0, f1, decay):
    """떨어지는 낮은 사인 (몸으로 느끼는 '쿵')."""
    t = t_axis(sec)
    phase = np.cumsum(f1 + (f0 - f1) * np.exp(-t * 18)) / R
    return np.sin(2 * np.pi * phase) * np.exp(-t * decay)


def bell(f0, sec, decay, partials=((1.0, 1.0), (2.0, 0.45), (3.0, 0.22), (4.16, 0.12))):
    t = t_axis(sec)
    return sum(a * np.sin(2 * np.pi * f0 * k * t) * np.exp(-t * decay * k ** 0.6) for k, a in partials)


def rise(sec, f0, f1):
    """올라가는 맑은 음 (모으기·강화)."""
    t = t_axis(sec)
    f = f0 * (f1 / f0) ** (t / sec)
    return np.sin(2 * np.pi * np.cumsum(f) / R) * np.minimum(1, t / sec * 3) * np.exp(-((t - sec) / (sec * 0.5)) ** 2)


# ----- 소리 만들기 (이름 -> 함수). v는 변형 번호(1·2·3): 다른 원본 파일·음 높이 -----
PV = {1: 1.0, 2: 0.94, 3: 1.07}


def swing(v=1):
    return K.mix(0.26, [(0, whoosh(0.24, 700, 2600), 1.0), (0.01, S('rpg-audio', f'cloth{v}', 0.15, PV[v] * 1.2), 0.25)])


def swing_fade(v=1):
    return K.mix(0.22, [(0, K.lowpass(whoosh(0.2, 500, 1400), 4), 0.8), (0, S('rpg-audio', f'cloth{v + 1}', 0.14), 0.2)])


def swing_awake(v=1):
    return K.mix(0.3, [(0, whoosh(0.26, 900, 3400), 1.0), (0.02, S('digital-audio', f'phaserUp{v}', 0.18, 1.3), 0.18),
                       (0.01, S('rpg-audio', f'cloth{v}', 0.15, 1.2), 0.2)])


def swing_critical(v=1):
    return K.mix(0.34, [(0, whoosh(0.3, 600, 3000), 1.1), (0.04, K.highpass(S('sci-fi-sounds', f'explosionCrunch_00{v}', 0.2)), 0.35),
                        (0.03, sub(0.2, 140, 60, 14), 0.4)])


def swing_enhanced():
    return K.mix(0.42, [(0, whoosh(0.32, 600, 3200), 1.0), (0.0, S('sci-fi-sounds', 'forceField_001', 0.4, 1.2), 0.4),
                        (0.02, sub(0.25, 160, 55, 10), 0.35)])


def dash(v=1):
    return K.mix(0.22, [(0, whoosh(0.18, 1200, 3800, peak=0.2), 1.0), (0, S('rpg-audio', f'cloth{v + 1}', 0.14, 1.1), 0.3)])


def jump(v=1):
    return K.mix(0.16, [(0, S('rpg-audio', f'clothBelt{"" if v == 1 else "2"}', 0.14, PV[v] * 1.15), 0.7),
                        (0, whoosh(0.12, 800, 2000, peak=0.15), 0.35)])


def double_jump():
    return K.mix(0.2, [(0, whoosh(0.18, 1200, 4000, peak=0.2), 0.9), (0, S('rpg-audio', 'cloth3', 0.14, 1.3), 0.3)])


def land(v=1):
    return K.mix(0.2, [(0, S('impact-sounds', f'footstep_concrete_00{v + 1}', 0.18, 0.85 * PV[v]), 1.0), (0, sub(0.12, 110, 55, 25), 0.35)])


def hit(v=1):
    """주인공이 맞았다: 묵직한 주먹 + 낮은 쿵 + 짧은 유리 금."""
    return K.mix(0.35, [(0, S('impact-sounds', f'impactPunch_heavy_00{v}', 0.3, 0.9), 1.0), (0, sub(0.22, 150, 50, 12), 0.5),
                        (0.005, S('interface-sounds', 'glass_002', 0.12, 0.8), 0.15)])


def enemy_hit(v=1):
    return K.mix(0.22, [(0, S('impact-sounds', f'impactPunch_medium_00{v}', 0.2, PV[v]), 1.0),
                        (0, S('impact-sounds', f'impactSoft_medium_00{v}', 0.15, PV[v]), 0.35)])


def impact_pipe(v=1):
    """철파이프가 박힌다: 쇠 울림 + 주먹 + 낮은 쿵."""
    return K.mix(0.32, [(0, S('impact-sounds', f'impactMetal_medium_00{v}', 0.28, PV[v] * 0.9), 0.7),
                        (0, S('impact-sounds', f'impactPunch_heavy_00{v + 1}', 0.25, PV[v]), 0.9), (0, sub(0.16, 170, 60, 16), 0.4)])


def impact_knife(v=1):
    return K.mix(0.2, [(0, S('rpg-audio', 'knifeSlice' + ('' if v == 1 else '2'), 0.18, PV[v]), 1.0),
                       (0, S('impact-sounds', f'impactGeneric_light_00{v}', 0.12, PV[v] * 1.2), 0.4)])


def impact_gauntlet(v=1):
    return K.mix(0.32, [(0, S('impact-sounds', f'impactPunch_heavy_00{(v + 2) % 5}', 0.28, PV[v] * 0.85), 1.0),
                        (0, S('impact-sounds', f'impactPlate_heavy_00{v}', 0.22, PV[v]), 0.45), (0, sub(0.2, 140, 45, 12), 0.55)])


def enemy_die():
    return K.mix(0.4, [(0, S('impact-sounds', 'impactPlate_heavy_003', 0.3), 0.6), (0, S('impact-sounds', 'impactPunch_heavy_004', 0.3), 0.9),
                       (0, sub(0.3, 150, 40, 9), 0.5)])


STREAK_STEPS = (0, 2, 4, 7, 9, 12)     # 연속 처치 단계마다 오르는 음 (반음)


def kill_streak(level):
    """연속 처치 1~6: 녹음한 묵직한 일격(단계마다 조금씩 무겁게) 위에 단계마다 높아지고 두꺼워지는 종소리."""
    s = 0.55 + 0.06 * level
    base = 523.25 * 2 ** (STREAK_STEPS[level - 1] / 12)
    parts = [(0, S('impact-sounds', f'impactPunch_heavy_00{level % 5}', 0.3, 0.95 - 0.02 * level), 1.0),
             (0, sub(0.26, 150 + 12 * level, 42, 9), 0.6),
             (0.005, K.highpass(S('sci-fi-sounds', f'explosionCrunch_00{level % 5}', 0.12)), 0.18 + 0.03 * level),
             (0.012, bell(base, s, 6.5 - 0.5 * level), 0.3)]
    if level >= 3:
        parts.append((0.012, bell(base * 1.5, s, 7.0 - 0.5 * level), 0.2))
    if level >= 5:
        parts.append((0.012, bell(base * 2.0, s, 7.5 - 0.5 * level), 0.16))
    if level >= 4:
        for i, r in enumerate((1.0, 1.26, 1.5, 2.0)[:level - 2]):
            parts.append((0.05 + 0.035 * i, bell(base * 2 * r, 0.18, 14), 0.12))
    return K.mix(s, parts)


def kill_last():
    return K.mix(1.0, [(0, S('impact-sounds', 'impactBell_heavy_001', 0.9), 0.6), (0, S('impact-sounds', 'impactPunch_heavy_000', 0.3), 1.0),
                       (0, S('sci-fi-sounds', 'lowFrequency_explosion_000', 0.8), 0.6)])


def absorb(i):
    """흡수 입자가 닿는다 (absorb_1~5, 차례대로 높게): 유리 '팅' + 맑은 종."""
    k = 2 ** ((0, 2, 4, 7, 9)[i - 1] / 12)
    return K.mix(0.16, [(0, S('interface-sounds', 'glass_001', 0.14, 1.25 * k), 0.6), (0, bell(1047 * k, 0.14, 20), 0.35)])


def absorb_done():
    return K.mix(0.5, [(0, S('interface-sounds', 'maximize_006', 0.4, 1.1), 0.6), (0.03, bell(1318.5, 0.35, 8), 0.3),
                       (0.08, bell(1760, 0.35, 9), 0.25), (0.13, bell(2637, 0.3, 10), 0.18)])


def pickup():
    return K.mix(0.35, [(0, S('interface-sounds', 'confirmation_002', 0.32), 0.8), (0, bell(1568, 0.25, 12), 0.2)])


def enhance():
    return K.mix(0.6, [(0, S('digital-audio', 'powerUp7', 0.5), 0.6), (0, S('sci-fi-sounds', 'forceField_000', 0.55, 1.1), 0.5),
                       (0, rise(0.4, 300, 1200), 0.2)])


def overload():
    return K.mix(1.1, [(0, S('sci-fi-sounds', 'lowFrequency_explosion_001', 1.0), 1.0), (0, S('sci-fi-sounds', 'explosionCrunch_002', 0.6), 0.6),
                       (0, sub(0.6, 120, 30, 4), 0.6)])


def overload_zap():
    return S('digital-audio', 'zap1', 0.4)


def stun_end():
    return S('digital-audio', 'phaserDown2', 0.35)


def death():
    return K.mix(1.3, [(0, S('impact-sounds', 'impactSoft_heavy_002', 0.4), 1.0), (0.05, S('sci-fi-sounds', 'lowFrequency_explosion_000', 1.2, 0.8), 0.8),
                       (0, sub(0.8, 120, 30, 3), 0.5)])


def throw(v=1):
    return K.mix(0.18, [(0, whoosh(0.14, 1600, 4200, peak=0.15), 0.9), (0, S('rpg-audio', f'drawKnife{v}', 0.12, 1.3 * PV[v]), 0.3)])


def throw_zone(zone):
    base = throw()
    if zone == 'fade':
        return K.lowpass(base, 4) * 0.8
    extra = {'awake': S('digital-audio', 'phaserUp2', 0.15, 1.4), 'critical': K.highpass(S('sci-fi-sounds', 'explosionCrunch_003', 0.12)),
             'enhanced': S('sci-fi-sounds', 'forceField_002', 0.25, 1.3)}[zone]
    return K.mix(0.3, [(0, base, 1.0), (0.01, extra, 0.3)])


def chain_throw():
    return K.mix(0.3, [(0, S('rpg-audio', 'beltHandle1', 0.25, 1.2), 0.8), (0, S('rpg-audio', 'metalLatch', 0.2, 1.3), 0.4),
                       (0, whoosh(0.22, 700, 2400), 0.6)])


def chain_zone(zone):
    base = chain_throw()
    if zone == 'fade':
        return K.lowpass(base, 4) * 0.8
    extra = {'awake': S('digital-audio', 'phaserUp3', 0.18, 1.3), 'critical': K.highpass(S('sci-fi-sounds', 'explosionCrunch_004', 0.14)),
             'enhanced': S('sci-fi-sounds', 'forceField_003', 0.3, 1.2)}[zone]
    return K.mix(0.36, [(0, base, 1.0), (0.02, extra, 0.3)])


def chain_latch():
    return K.mix(0.25, [(0, S('impact-sounds', 'impactMetal_light_002', 0.22, 1.1), 1.0), (0, S('rpg-audio', 'metalClick', 0.1), 0.4)])


def chain_latch_heavy():
    return K.mix(0.35, [(0, S('impact-sounds', 'impactMetal_heavy_001', 0.3), 1.0), (0, sub(0.2, 160, 50, 12), 0.4)])


def chain_clash():
    return K.mix(0.4, [(0, S('impact-sounds', 'impactMetal_heavy_002', 0.3), 1.0), (0.06, S('impact-sounds', 'impactMetal_heavy_003', 0.3), 0.8),
                       (0, sub(0.25, 130, 45, 10), 0.5)])


def ult_cast():
    return K.mix(0.9, [(0, S('sci-fi-sounds', 'forceField_004', 0.8), 0.7), (0, S('digital-audio', 'powerUp11', 0.6), 0.5),
                       (0, rise(0.7, 200, 1600), 0.25), (0, sub(0.8, 60, 90, 2), 0.4)])


def ult_hit():
    return K.mix(0.45, [(0, S('sci-fi-sounds', 'explosionCrunch_001', 0.4), 0.8), (0, S('impact-sounds', 'impactPunch_heavy_002', 0.3), 0.8),
                        (0, sub(0.3, 160, 45, 9), 0.5)])


def ult_final(kind):
    parts = [(0, S('sci-fi-sounds', 'lowFrequency_explosion_001', 1.2), 0.9), (0, S('sci-fi-sounds', 'explosionCrunch_000', 0.6), 0.6),
             (0, sub(0.8, 140, 30, 4), 0.6)]
    parts.append({'pipe': (0, S('impact-sounds', 'impactBell_heavy_002', 1.0, 0.8), 0.5),
                  'knife': (0, S('rpg-audio', 'knifeSlice2', 0.2, 0.8), 0.8),
                  'gauntlet': (0, S('impact-sounds', 'impactPunch_heavy_004', 0.3, 0.7), 1.0),
                  'chain': (0, S('impact-sounds', 'impactMetal_heavy_004', 0.4, 0.8), 0.8)}[kind])
    return K.mix(1.3, parts)


def ui_move():
    return S('interface-sounds', 'tick_002', 0.08)


def ui_select():
    return S('interface-sounds', 'select_002', 0.2)


def ui_back():
    return S('interface-sounds', 'back_002', 0.2)


def ark_bullet():
    return S('sci-fi-sounds', 'laserSmall_001', 0.3)


def ark_teleport():
    return K.mix(0.5, [(0, S('digital-audio', 'phaseJump3', 0.4), 0.8), (0, S('sci-fi-sounds', 'forceField_002', 0.4, 1.4), 0.3)])


def ark_absorb():
    return K.mix(0.8, [(0, S('sci-fi-sounds', 'forceField_000', 0.7, 0.8), 0.8), (0, rise(0.6, 150, 600), 0.3)])


def ark_burst():
    return K.mix(0.7, [(0, S('sci-fi-sounds', 'explosionCrunch_003', 0.6), 0.9), (0, sub(0.4, 140, 40, 7), 0.5)])


def ark_field():
    return S('sci-fi-sounds', 'forceField_003', 0.9, 0.85)


def drone_torch():
    return S('sci-fi-sounds', 'thrusterFire_001', 0.6)


# ===== v3 (2026-11-24, 사용자: 휘두르기가 가볍고 타격이 작다, 공격 종류·적마다 달라야 한다) =====
# 참고한 방식 (소리를 가져오지 않음): 하데스·스컬·할로우 나이트처럼 타격 = 날카로운 시작(탁) + 몸통(퍽·쾅) + 꼬리(울림),
# 휘두르기 = 낮은 '훙'(무게) + 높은 '쉭'(속도). 강한 공격일수록 낮은 쿵과 길이가 늘고, 강화는 마법 같은 울림이 붙는다.
def heavy_whoosh(sec, low=(220, 800), high=(1200, 3400), weight=1.0, peak=0.4):
    """무게 있는 휘두르기: 낮은 띠(훙) + 높은 띠(쉭)."""
    return whoosh(sec, *low, bright=0.4, peak=peak) * (0.9 * weight) + whoosh(sec, *high, peak=peak) * 0.55


def swing_n(step, v=1):
    """땅 1·2·3타: 뒤로 갈수록 낮고 길고 무겁다. 3타는 끝에 낮은 쿵."""
    k = PV[v]
    if step == 1:
        return K.mix(0.24, [(0, heavy_whoosh(0.22, (260 * k, 900 * k), (1400 * k, 3600 * k)), 1.0),
                            (0.0, S('rpg-audio', f'cloth{v}', 0.12, 1.2 * k), 0.25)])
    if step == 2:
        return K.mix(0.28, [(0, heavy_whoosh(0.26, (200 * k, 760 * k), (1100 * k, 3000 * k), 1.2), 1.0),
                            (0.0, S('rpg-audio', f'cloth{v + 1}', 0.14, 1.0 * k), 0.3)])
    return K.mix(0.38, [(0, heavy_whoosh(0.34, (150 * k, 620 * k), (900 * k, 2800 * k), 1.5, peak=0.5), 1.0),
                        (0.22, sub(0.14, 120, 55, 18), 0.45), (0.0, S('rpg-audio', 'clothBelt', 0.14, 0.9 * k), 0.3)])


def swing_air(v=1):
    """공중 베기: 가볍게 도는 바람 (두 번 출렁)."""
    w = heavy_whoosh(0.26, (320 * PV[v], 1000 * PV[v]), (1600 * PV[v], 4200 * PV[v]), 0.8)
    t = np.linspace(0, 1, len(w))
    return K.mix(0.28, [(0, w * (0.75 + 0.25 * np.cos(2 * np.pi * 2 * t)), 1.0), (0, S('rpg-audio', 'cloth3', 0.12, 1.3), 0.25)])


def swing_dash(v=1):
    """이동 베기: 빠르게 지나가는 바람 (높은 쪽에서 낮은 쪽으로, 도플러)."""
    return K.mix(0.22, [(0, heavy_whoosh(0.2, (900 * PV[v], 300 * PV[v]), (4200 * PV[v], 1200 * PV[v]), 1.0, peak=0.18), 1.1),
                        (0, sub(0.1, 140, 70, 25), 0.35)])


def swing_plunge():
    """찍기: 위에서 떨어지는 바람 (점점 낮아진다)."""
    return K.mix(0.34, [(0, heavy_whoosh(0.32, (700, 220), (3200, 900), 1.3, peak=0.7), 1.0),
                        (0, S('rpg-audio', 'clothBelt2', 0.14, 0.9), 0.3)])


def accent(zone):
    """구간 색 소리 (휘두르기 위에 겹친다): 각성 = 반짝이는 종 둘, 위험 = 지글거리는 불꽃."""
    if zone == 'awake':
        return K.mix(0.3, [(0.02, bell(1568, 0.25, 12), 0.35), (0.06, bell(2093, 0.22, 14), 0.25),
                           (0, S('digital-audio', 'phaserUp4', 0.2, 1.4), 0.2)])
    return K.mix(0.3, [(0, K.highpass(S('sci-fi-sounds', 'explosionCrunch_002', 0.25, 1.2)), 0.6), (0, sub(0.2, 90, 45, 10), 0.4)])


ENH_NOTES = {1: (659.3,), 2: (659.3, 987.8), 3: (659.3, 987.8, 1318.5)}


def swing_enh(level):
    """강화 휘두르기: 단계마다 무겁고 화음이 두꺼워진다 (1 보라·2 금·3 진홍)."""
    s = 0.36 + 0.08 * level
    parts = [(0, heavy_whoosh(s - 0.04, (180, 700), (1000, 3200), 1.2 + 0.3 * level, peak=0.45), 1.0),
             (0, S('sci-fi-sounds', f'forceField_00{level}', s, 1.3 - 0.1 * level), 0.35 + 0.1 * level)]
    parts += [(0.02 + 0.03 * i, bell(f, s, 7), 0.22) for i, f in enumerate(ENH_NOTES[level])]
    if level >= 2:
        parts.append((0.1, sub(0.3, 110, 40, 6), 0.5))
    if level >= 3:
        parts.append((0.08, K.highpass(S('sci-fi-sounds', 'explosionCrunch_000', 0.3)), 0.4))
    return K.mix(s, parts)


def impact_pipe_heavy():
    """3타 마무리: 쇠 + 판 + 주먹 + 깊은 쿵 + 부서지는 소리."""
    return K.mix(0.5, [(0, S('impact-sounds', 'impactPunch_heavy_000', 0.3, 0.85), 1.0), (0, S('impact-sounds', 'impactMetal_heavy_000', 0.4, 0.85), 0.6),
                       (0, S('impact-sounds', 'impactPlate_heavy_000', 0.3), 0.45), (0, sub(0.4, 170, 38, 7), 0.8),
                       (0.005, K.highpass(S('sci-fi-sounds', 'explosionCrunch_001', 0.2)), 0.35)])


def impact_pipe_dash(v=1):
    """이동 베기 적중: 날카롭게 가르는 소리 + 주먹."""
    return K.mix(0.3, [(0, S('rpg-audio', 'knifeSlice' + ('' if v == 1 else '2'), 0.2, 0.8 * PV[v]), 0.8),
                       (0, S('impact-sounds', f'impactPunch_medium_00{v + 1}', 0.25, PV[v]), 0.9), (0, sub(0.14, 160, 60, 18), 0.4)])


def impact_pipe_air(v=1):
    """공중 베기 적중: 가볍고 맑게 (쇠 울림이 위로)."""
    return K.mix(0.28, [(0, S('impact-sounds', f'impactPunch_medium_00{(v + 2) % 5}', 0.22, 1.05 * PV[v]), 0.9),
                        (0, S('impact-sounds', f'impactMetal_light_00{v}', 0.22, 1.1 * PV[v]), 0.55)])


def impact_pipe_plunge():
    """찍기 적중: 땅까지 울리는 쿵 + 돌 부서짐."""
    return K.mix(0.55, [(0, S('impact-sounds', 'impactPunch_heavy_003', 0.3, 0.8), 1.0), (0, S('impact-sounds', 'impactMining_002', 0.35, 0.8), 0.7),
                        (0, sub(0.45, 150, 32, 6), 0.9), (0.01, K.highpass(S('sci-fi-sounds', 'explosionCrunch_004', 0.25)), 0.35)])


def impact_enh(level):
    """강화 적중 1~3단계: 묵직한 일격 + 마법 울림, 단계마다 폭발이 커진다."""
    s = 0.45 + 0.15 * level
    parts = [(0, S('impact-sounds', 'impactPunch_heavy_001', 0.3, 0.85), 1.0), (0, sub(0.3 + 0.1 * level, 160, 38, 8 - level), 0.6 + 0.1 * level),
             (0, S('sci-fi-sounds', f'forceField_00{level + 1}', 0.3, 1.4), 0.3)]
    parts += [(0.01, bell(f * 0.5, s, 6), 0.25) for f in ENH_NOTES[level]]
    if level >= 2:
        parts.append((0, S('impact-sounds', 'impactPlate_heavy_004', 0.3), 0.45))
    if level >= 3:
        parts.append((0, S('sci-fi-sounds', 'lowFrequency_explosion_000', 0.6), 0.7))
    return K.mix(s, parts)


def enhance_level(level):
    """E 강화 1~3단계: 1 = 모이는 소리, 2 = 두 음 + 쿵, 3 = 세 음 화음 + 우렁찬 낮은 소리 + 큰 쿵."""
    s = 0.6 + 0.2 * level
    parts = [(0, S('digital-audio', ('powerUp7', 'powerUp3', 'powerUp11')[level - 1], 0.5), 0.6),
             (0, S('sci-fi-sounds', f'forceField_00{level - 1}', s * 0.8, 1.1), 0.45), (0, rise(0.35, 220 * level, 1100), 0.25)]
    parts += [(0.12 + 0.07 * i, bell(f, s - 0.15, 4.5), 0.3) for i, f in enumerate(ENH_NOTES[level])]
    if level >= 2:
        parts.append((0.1, sub(0.5, 120, 36, 4), 0.7))
    if level >= 3:
        parts += [(0.08, S('sci-fi-sounds', 'lowFrequency_explosion_001', 0.7), 0.7),
                  (0.05, S('sci-fi-sounds', 'spaceEngineLow_002', 0.6, 0.7), 0.35)]
    return K.mix(s, parts)


def hit_material(mat, v=1):
    """적이 맞는 소리 (재질). 무기 타격음과 겹쳐 난다."""
    k = PV[v]
    m = {
        'flesh': [(S('impact-sounds', f'impactPunch_medium_00{v}', 0.2, 0.95 * k), 0.8), (S('impact-sounds', f'impactSoft_heavy_00{v}', 0.22, k), 0.6)],
        'beast': [(S('impact-sounds', f'impactSoft_medium_00{v}', 0.18, 1.15 * k), 0.8), (S('impact-sounds', f'impactGeneric_light_00{v}', 0.12, 0.9 * k), 0.5)],
        'small': [(S('impact-sounds', f'impactSoft_medium_00{v + 1}', 0.12, 1.45 * k), 0.8), (S('impact-sounds', f'impactGeneric_light_00{v + 1}', 0.1, 1.3 * k), 0.4)],
        'armor': [(S('impact-sounds', f'impactPlate_medium_00{v}', 0.25, k), 0.8), (S('impact-sounds', f'impactMetal_light_00{v + 1}', 0.22, k), 0.45)],
        'armor_crystal': [(S('impact-sounds', f'impactPlate_medium_00{v + 1}', 0.22, k), 0.7), (S('impact-sounds', f'impactGlass_light_00{v}', 0.25, k), 0.55)],
        'mech': [(S('impact-sounds', f'impactTin_medium_00{v}', 0.22, k), 0.8), (S('impact-sounds', f'impactMetal_medium_00{v + 1}', 0.2, 1.1 * k), 0.4),
                 (K.highpass(S('sci-fi-sounds', 'explosionCrunch_003', 0.1, 1.3)), 0.25)],
        'crystal': [(S('impact-sounds', f'impactGlass_medium_00{v}', 0.3, k), 0.8), (bell(1760 * k, 0.3, 10), 0.2)],
        'ethereal': [(K.lowpass(S('impact-sounds', f'impactGlass_light_00{v + 1}', 0.3, 0.7 * k), 3), 0.7),
                     (S('sci-fi-sounds', 'forceField_004', 0.25, 1.6 * k), 0.35)],
        'boss_metal': [(S('impact-sounds', f'impactMetal_heavy_00{v}', 0.35, 0.9 * k), 0.8), (S('impact-sounds', f'impactPlate_heavy_00{v}', 0.3, k), 0.5),
                       (sub(0.25, 120, 45, 9), 0.5)],
        'boss_crystal': [(S('impact-sounds', f'impactGlass_heavy_00{v}', 0.35, k), 0.8), (S('impact-sounds', 'impactBell_heavy_003', 0.4, 1.2 * k), 0.3),
                         (sub(0.25, 130, 50, 9), 0.4)],
        'organic': [(S('impact-sounds', f'impactSoft_heavy_00{v + 1}', 0.3, 0.75 * k), 0.9), (S('sci-fi-sounds', 'slime_000', 0.3, 0.9 * k), 0.5)],
    }[mat]
    return K.mix(0.4, [(0, x, g) for x, g in m])


def jump_v3(v=1):
    """점프: 발로 밀어내는 짧은 소리 + 옷 + 짧은 바람."""
    return K.mix(0.2, [(0, S('impact-sounds', f'footstep_concrete_00{v - 1}', 0.1, 1.25 * PV[v]), 0.45),
                       (0, S('rpg-audio', f'cloth{v}', 0.14, 1.1 * PV[v]), 0.45), (0.01, whoosh(0.15, 600, 1600, peak=0.25), 0.4)])


def double_jump_v3():
    """2단 점프: 위로 솟는 바람 + 헤이즈 반짝임."""
    return K.mix(0.3, [(0, heavy_whoosh(0.24, (400, 1200), (1500, 4200), 0.7, peak=0.3), 0.9),
                       (0.03, bell(2093, 0.2, 14), 0.18), (0.06, bell(2637, 0.18, 16), 0.12), (0, S('rpg-audio', 'cloth4', 0.12, 1.3), 0.3)])


def dash_v3(v=1):
    """대시: 앞이 묵직한 '훅' + 빠르게 지나가는 바람 + 헤이즈 반짝임 꼬리."""
    return K.mix(0.28, [(0, sub(0.1, 150, 70, 22), 0.5), (0, heavy_whoosh(0.24, (900 * PV[v], 260 * PV[v]), (4400 * PV[v], 1400 * PV[v]), 1.1, peak=0.15), 1.0),
                        (0.04, S('rpg-audio', f'cloth{v + 1}', 0.12, 1.2), 0.3), (0.08, bell(2349 * PV[v], 0.16, 18), 0.1)])


SOUNDS = {
    'swing': swing, 'swing_fade': swing_fade, 'swing_awake': swing_awake, 'swing_critical': swing_critical,
    'swing_enhanced': swing_enhanced, 'dash': dash, 'jump': jump, 'double_jump': double_jump, 'land': land, 'hit': hit,
    'enemy_hit': enemy_hit, 'impact_pipe': impact_pipe, 'impact_knife': impact_knife, 'impact_gauntlet': impact_gauntlet,
    'enemy_die': enemy_die, 'kill_last': kill_last, 'absorb_done': absorb_done, 'pickup': pickup, 'enhance': enhance,
    'overload': overload, 'overload_zap': overload_zap, 'stun_end': stun_end, 'death': death, 'throw': throw,
    'chain_throw': chain_throw, 'chain_latch': chain_latch, 'chain_latch_heavy': chain_latch_heavy, 'chain_clash': chain_clash,
    'ult_cast': ult_cast, 'ult_hit': ult_hit, 'ui_move': ui_move, 'ui_select': ui_select, 'ui_back': ui_back,
    'ark_bullet': ark_bullet, 'ark_teleport': ark_teleport, 'ark_absorb': ark_absorb, 'ark_burst': ark_burst,
    'ark_field': ark_field, 'drone_torch': drone_torch,
    **{f'kill_streak_{k}': (lambda k=k: kill_streak(k)) for k in range(1, 7)},
    **{f'absorb_{i}': (lambda i=i: absorb(i)) for i in range(1, 6)},
    **{f'throw_{z}': (lambda z=z: throw_zone(z)) for z in ('fade', 'awake', 'critical', 'enhanced')},
    **{f'chain_throw_{z}': (lambda z=z: chain_zone(z)) for z in ('fade', 'awake', 'critical', 'enhanced')},
    **{f'ult_final_{w}': (lambda w=w: ult_final(w)) for w in ('pipe', 'knife', 'gauntlet', 'chain')},
    # v3
    'swing_1': lambda: swing_n(1), 'swing_2': lambda: swing_n(2), 'swing_3': lambda: swing_n(3),
    'swing_air': swing_air, 'swing_dash': swing_dash, 'swing_plunge': swing_plunge,
    'accent_awake': lambda: accent('awake'), 'accent_critical': lambda: accent('critical'),
    **{f'swing_enh{k}': (lambda k=k: swing_enh(k)) for k in (1, 2, 3)},
    'impact_pipe_heavy': impact_pipe_heavy, 'impact_pipe_dash': impact_pipe_dash, 'impact_pipe_air': impact_pipe_air,
    'impact_pipe_plunge': impact_pipe_plunge,
    **{f'impact_enh{k}': (lambda k=k: impact_enh(k)) for k in (1, 2, 3)},
    **{f'enhance_{k}': (lambda k=k: enhance_level(k)) for k in (1, 2, 3)},
    **{f'hit_{m}': (lambda m=m: hit_material(m)) for m in ('flesh', 'beast', 'small', 'armor', 'armor_crystal', 'mech', 'crystal',
                                                           'ethereal', 'boss_metal', 'boss_crystal', 'organic')},
    'jump': jump_v3, 'double_jump': double_jump_v3, 'dash': dash_v3,
}
# 자주 나는 소리의 2·3버전 (src/config.SFX_VARIANTS): 다른 원본 파일과 음 높이로
VARIANT_FNS = {'swing': swing, 'swing_fade': swing_fade, 'swing_awake': swing_awake, 'swing_critical': swing_critical,
               'enemy_hit': enemy_hit, 'impact_pipe': impact_pipe, 'impact_knife': impact_knife, 'impact_gauntlet': impact_gauntlet,
               'hit': hit, 'dash': dash_v3, 'jump': jump_v3, 'land': land, 'throw': throw,
               # v3
               'swing_1': lambda v: swing_n(1, v), 'swing_2': lambda v: swing_n(2, v), 'swing_3': lambda v: swing_n(3, v),
               'swing_air': swing_air, 'swing_dash': swing_dash, 'impact_pipe_dash': impact_pipe_dash, 'impact_pipe_air': impact_pipe_air,
               **{f'hit_{m}': (lambda v, m=m: hit_material(m, v)) for m in ('flesh', 'beast', 'small', 'armor', 'mech')}}


# 원본이 꽉 찬(평균 크기가 큰) 소리는 줄인다: 다른 소리와 체감 크기를 맞춘다 (나머지는 최고점 0.85)
LEVEL = {'overload_zap': 0.55, 'ark_field': 0.6, 'ark_absorb': 0.6, 'throw_enhanced': 0.7, 'chain_throw_enhanced': 0.7,
         'ult_hit': 0.8, 'drone_torch': 0.75}


MIN_SEC, MAX_SEC = 0.06, 0.98     # 효과음 길이 규칙 (tests/test_sfx.py): 짧은 딸깍은 뒤에 무음을 붙이고, 긴 폭발은 줄여 끝낸다


def fit(x):
    if len(x) > MAX_SEC * R:
        x = K.cut(x, MAX_SEC)
    if len(x) < MIN_SEC * R:
        x = np.concatenate([x, np.zeros(int(MIN_SEC * R) - len(x) + 1, dtype=np.float32)])
    return x


def build():
    global RNG
    for name, fn in SOUNDS.items():
        RNG = np.random.default_rng(zlib.crc32(name.encode()))
        K.save(os.path.join(OUT, name + '.wav'), fit(fn()), peak=0.85 * LEVEL.get(name, 1.0))
    for name, fn in VARIANT_FNS.items():
        for v in (2, 3):
            RNG = np.random.default_rng(zlib.crc32(f'{name}_v{v}'.encode()))
            K.save(os.path.join(OUT, f'{name}_v{v}.wav'), fit(fn(v)))
    print(f'{len(SOUNDS)}개 + 변형 {len(VARIANT_FNS) * 2}개 저장 (assets/sfx), 원본 {len(_used)}개 사용')


def import_from(folder):
    """Kenney 압축을 푼 폴더에서 이 도구가 쓰는 원본만 assets/sfx_src/kenney/<묶음>/ 으로 복사한다 (라이선스 문서 포함)."""
    import sfx_kit
    calls = []
    orig = sfx_kit.load
    sfx_kit.load = lambda path: (calls.append(path), np.zeros(4410, dtype=np.float32))[1]
    try:
        for name, fn in SOUNDS.items():
            fn()
        for fn in VARIANT_FNS.values():
            fn(2), fn(3)
    finally:
        sfx_kit.load = orig
    for pack, name in sorted(_used):
        found = glob.glob(os.path.join(folder, pack, '**', name + '.ogg'), recursive=True)
        if not found:
            raise FileNotFoundError(f'{pack}/{name}.ogg')
        os.makedirs(os.path.join(SRC, pack), exist_ok=True)
        shutil.copy(found[0], os.path.join(SRC, pack, name + '.ogg'))
    for pack in {p for p, _ in _used}:
        lic = glob.glob(os.path.join(folder, pack, '**', 'License.txt'), recursive=True)
        if lic:
            shutil.copy(lic[0], os.path.join(SRC, pack, 'License.txt'))
    _used.clear()
    _cache.clear()
    print(f'원본 {len(set(calls))}개 복사 -> assets/sfx_src/kenney')


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--import':
        import_from(sys.argv[2])
    else:
        build()
