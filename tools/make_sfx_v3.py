"""효과음 v3 (S2-2, 2026-11-27). 사용자: "효과음은 다 별로인데 아까 준 사이트에서도 효과음 좀 가지고 와서 다시 해줘".

v2(tools/make_sfx.py 합성 + make_sfx_v2.py)는 numpy 합성음이 바탕이었다. v3는 **녹음 원본이 바탕**이고 합성은 겹쳐 넣는
보조(낮은 '쿵', 바람 한 줄)로만 쓴다. 결과는 새 묶음 assets/sfx_v3/ (예전 assets/sfx는 그대로, config.SFX_SET으로 고른다).

- 원본: 사이트 Free Game Dev Assets(tmhsdigital.github.io/Free-Game-Dev-Assets)의 오디오 목록에 있는 Kenney 묶음 다섯
  (Impact Sounds, Interface Sounds, Sci-fi Sounds, RPG Audio, Digital Audio), 모두 CC0 1.0. 출처 표는 SOURCES.
  쓰는 파일만 assets/sfx_src/kenney/<묶음>/ (License.txt 포함). 목록의 다른 CC0 효과음(BigSoundBank, OpenGameArt 발소리)은
  사이트가 자동 내려받기를 막아 쓰지 못했다(docs/opus/TASKS.md S2-2 '사용자가 직접 받아 줘야 하는 것').
- 소리마다 레시피(RECIPES): 어느 원본의 어느 구간을, 얼마나 높게(k), 어떤 필터로, 몇 dB로, 언제 겹치는지.
- 공통 처리(한 벌로 들리게): 같은 방 잔향(작은 콘크리트 방, 0.38초) 한 가지, 35Hz 아래 덜기, 종류별 목표 크기(GROUP_TARGET,
  가장 큰 50ms RMS), 최대값 -1.2dBFS 아래(부드러운 리미터), 앞 무음 1ms 안쪽.
- 자주 나는 소리(config.SFX_VARIANTS)는 변주 셋: 다른 원본 녹음(Kenney는 같은 소리를 5번 녹음해 두었다) + 음 높이 차이.

사용:
  python tools/make_sfx_v3.py --import <Kenney 압축을 푼 폴더>   (쓰는 원본을 assets/sfx_src/kenney로 복사)
  python tools/make_sfx_v3.py                                   (assets/sfx_v3 다시 굽기 + MANIFEST.json)
  python tools/make_sfx_v3.py --review shots/review             (S2_sfx_table.md, S2_sfx_wave.png)
필요: numpy, scipy, pysdl2(SDL_mixer, ogg 읽기), Pillow(--review)
"""
import argparse
import json
import os
import shutil
import sys
import wave

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx_kit as K  # noqa: E402
import sfx_metrics as M  # noqa: E402

ROOT = os.path.dirname(HERE)
SRC_ROOT = os.path.join(ROOT, 'assets', 'sfx_src')
OUT = os.path.join(ROOT, 'assets', 'sfx_v3')
OLD = os.path.join(ROOT, 'assets', 'sfx')
R = K.RATE

# ----- 출처 표 (원본이 어디서 왔는지. tests/test_sfx_s2.py가 레시피의 원본이 모두 여기 있는지 본다) -----
SOURCES = {
    'kenney': dict(
        title='Kenney Impact Sounds · Interface Sounds · Sci-fi Sounds · RPG Audio · Digital Audio',
        author='Kenney Vleugels (Kenney.nl)',
        url='https://kenney.nl/assets/impact-sounds , /interface-sounds , /sci-fi-sounds , /rpg-audio , /digital-audio',
        license='CC0 1.0',
        license_text='License (Creative Commons Zero, CC0) http://creativecommons.org/publicdomain/zero/1.0/ '
                     'You may use these assets in personal and commercial projects. '
                     'Credit (Kenney or www.kenney.nl) would be nice but is not mandatory.',
        got='2026-11-24 (사용자가 kenney.nl에서 받은 압축 파일 다섯. 11-27에 같은 압축에서 더 꺼냄)',
        site_entry='Free Game Dev Assets catalog/audio: kenney-impact-sounds, kenney-interface-sounds, kenney-sci-fi-sounds, '
                   'kenney-rpg-audio (모두 license CC0, status active). Digital Audio는 같은 작가·같은 라이선스',
    ),
}

PACK = {'IM': 'impact-sounds', 'UI': 'interface-sounds', 'SF': 'sci-fi-sounds', 'RP': 'rpg-audio', 'DG': 'digital-audio'}


def src_path(ref):
    """'IM:impactMetal_heavy_002' -> 'kenney/impact-sounds/impactMetal_heavy_002.ogg' (assets/sfx_src 아래)."""
    pack, name = ref.split(':')
    return f'kenney/{PACK[pack]}/{name}.ogg'


# ----- 레시피 표 -----
def L(src, at=0.0, db=0.0, k=1.0, start=0.0, length=None, hp=None, lp=None, rev=False, decay=None, sweep=None, fade_in=0.0,
      swell=None):
    """녹음 원본 한 겹. src·k는 변주(1·2·3)마다 다른 값을 줄 수 있다(목록).
    start·length: 원본(앞 무음을 자른 뒤)의 구간(초). k: 음 높이 배율(길이는 1/k). hp·lp: 필터(Hz). rev: 뒤집기.
    decay: 꼬리를 이 시간 상수(초)로 줄인다. sweep: (k0, k1) 음 높이를 k0 -> k1로 쓸기. db: 크기. at: 겹치는 시각(초).
    swell: 바람 모양 크기(0~1, 꼭대기 자리). 녹음의 첫 순간이 '딱' 하고 시작해도 휘두르는 바람처럼 솟았다 사라지게."""
    return dict(kind='rec', src=src, at=at, db=db, k=k, start=start, length=length, hp=hp, lp=lp, rev=rev, decay=decay,
                sweep=sweep, fade_in=fade_in, swell=swell)


def Y(kind, at=0.0, db=0.0, **kw):
    """합성 보조 한 겹 (녹음에 없는 것만): 'sub' 떨어지는 낮은 사인(몸으로 느끼는 쿵), 'air' 띠 잡음 바람."""
    return dict(kind=kind, at=at, db=db, **kw)


def S(group, length, layers, room=0.12, hp=None, lp=None, variants=False, target=None):
    return dict(group=group, length=length, layers=layers, room=room, hp=hp, lp=lp, variants=variants, target=target)


# 종류별 목표 크기 (가장 큰 50ms RMS, dBFS). 타격 > 피격·큰 사건 > 휘두르기·움직임 > 메뉴 > 환경.
# 한 번 칠 때 무기 타격음 + 적 재질음 + 휘두르기가 함께 난다 (재질음은 한 층 아래).
GROUP_TARGET = {'impact': -10.0, 'material': -13.0, 'shot': -14.0, 'swing': -16.0, 'chain': -14.0, 'accent': -21.0,
                'move': -19.0, 'hurt': -9.5, 'big': -8.0, 'enemy': -12.0, 'windup': -14.0, 'gauge': -14.0,
                'reward': -15.0, 'ui': -20.0, 'boss': -10.5, 'amb': -24.0}

# 원본 이름 줄임: 변주(1·2·3)에 다른 녹음을 쓴다
MH = ['IM:impactMetal_heavy_000', 'IM:impactMetal_heavy_002', 'IM:impactMetal_heavy_004']
MM = ['IM:impactMetal_medium_001', 'IM:impactMetal_medium_003', 'IM:impactMetal_medium_000']
ML = ['IM:impactMetal_light_000', 'IM:impactMetal_light_003', 'IM:impactMetal_light_001']
PH = ['IM:impactPunch_heavy_000', 'IM:impactPunch_heavy_001', 'IM:impactPunch_heavy_003']
PM = ['IM:impactPunch_medium_000', 'IM:impactPunch_medium_001', 'IM:impactPunch_medium_003']
SH = ['IM:impactSoft_heavy_000', 'IM:impactSoft_heavy_002', 'IM:impactSoft_heavy_004']
SM = ['IM:impactSoft_medium_001', 'IM:impactSoft_medium_002', 'IM:impactSoft_medium_004']
PLH = ['IM:impactPlate_heavy_001', 'IM:impactPlate_heavy_003', 'IM:impactPlate_heavy_000']
PLM = ['IM:impactPlate_medium_001', 'IM:impactPlate_medium_003', 'IM:impactPlate_medium_004']
PLL = ['IM:impactPlate_light_000', 'IM:impactPlate_light_002', 'IM:impactPlate_light_003']
TIN = ['IM:impactTin_medium_000', 'IM:impactTin_medium_002', 'IM:impactTin_medium_004']
GEN = ['IM:impactGeneric_light_001', 'IM:impactGeneric_light_003', 'IM:impactGeneric_light_004']
FC = ['IM:footstep_concrete_001', 'IM:footstep_concrete_002', 'IM:footstep_concrete_004']
FR = ['RP:footstep01', 'RP:footstep03', 'RP:footstep08']
SL = ['RP:knifeSlice', 'RP:knifeSlice2', 'RP:knifeSlice']          # 칼이 공기를 가르는 녹음: 낮게 하면 휘두르는 바람
SLK = [1.0, 0.97, 1.09]                                               # 세 번째 변주는 같은 녹음을 더 높게
CL = ['RP:cloth1', 'RP:cloth2', 'RP:cloth3']
CR = ['SF:explosionCrunch_000', 'SF:explosionCrunch_001', 'SF:explosionCrunch_003']
FF = ['SF:forceField_000', 'SF:forceField_001', 'SF:forceField_003']
THR = ['SF:thrusterFire_000', 'SF:thrusterFire_002', 'SF:thrusterFire_004']


def kv(base, ks=SLK):
    return [base * k for k in ks]


def swing(base_k, length, extra=(), lp=7000, room=0.1, db_cloth=-9.0, air_db=-14.0, target=None, variants=True):
    """휘두르기 공통: 칼 바람 녹음을 낮춰 몸통 바람 + 천 스침 + 아주 작은 띠 잡음 바람(보조)."""
    layers = [L(SL, k=kv(base_k), hp=140, lp=lp, length=length, swell=0.28),
              L(CL, at=0.005, db=db_cloth, k=[1.45, 1.6, 1.35], length=length * 0.8, hp=300),
              Y('air', db=air_db, sec=length * 0.9, f0=500, f1=2200)] + list(extra)
    return S('swing', length, layers, room=room, variants=variants, target=target)


def material(main, second, db2=-4.0, k=1.0, k2=1.0, third=None, length=0.26, variants=True, room=0.1, hp=None, lp=None):
    layers = [L(main, k=k, decay=0.12), L(second, db=db2, k=k2, decay=0.1)]
    if third:
        layers.append(third)
    return S('material', length, layers, room=room, variants=variants, hp=hp, lp=lp)


def shot(extra=(), lp=None, k=1.55, target=None, variants=True, length=0.2):
    """총성: 폭발 녹음의 첫 순간(짧은 '탕') + 쇠 '찰칵'(기계) + 짧은 낮은 쿵(보조) + 방 울림."""
    layers = [L(CR, k=kv(k, (1.0, 0.94, 1.06)), length=0.1, hp=170, decay=0.05),
              L(ML, at=0.002, db=-9.0, k=1.3, length=0.07, hp=1500),
              Y('sub', db=-9.0, f0=130, f1=55, decay=30, sec=0.12)] + list(extra)
    return S('shot', length, layers, room=0.2, lp=lp, variants=variants, target=target)


def chain_throw(extra=(), lp=None, target=None):
    """사슬 던지기: 채찍 같은 바람(칼 바람 녹음) + 쇠사슬 짤랑임(동전 녹음을 낮춰 굵은 고리로) + 가죽 손잡이."""
    return S('chain', 0.34, [L('RP:knifeSlice2', k=0.82, hp=200, length=0.3, swell=0.25),
                             L('RP:handleCoins', at=0.03, db=-5.0, k=0.72, length=0.28, decay=0.1),
                             L('RP:beltHandle1', db=-10.0, k=0.9)] + list(extra), room=0.1, lp=lp, target=target)


def enemy_throw(extra=(), lp=None, target=None, variants=False):
    return S('enemy', 0.2, [L(CL, k=[1.55, 1.7, 1.45], length=0.16, hp=250),
                            L(SL, db=-5.0, k=kv(1.05), length=0.16, hp=400, swell=0.3)] + list(extra),
             room=0.08, lp=lp, variants=variants, target=target if target is not None else -16.0)


def kill_streak(level):
    bell_k = 0.78 + 0.07 * level
    layers = [L(PH, db=-3.0, k=0.92, decay=0.08),
              L('IM:impactBell_heavy_004', at=0.01, db=-2.0, k=bell_k, decay=0.18),
              L('UI:glass_001', at=0.02, db=-9.0 + level, k=0.8 + 0.08 * level, decay=0.15)]
    if level >= 4:
        layers.append(L('SF:forceField_002', at=0.0, db=-16.0 + level, k=1.6, length=0.3, decay=0.12))
    return S('reward', 0.32 + 0.04 * level, [dict(lay, src=lay['src'][0] if isinstance(lay['src'], list) else lay['src'])
                                             for lay in layers], room=0.15, target=-15.0 + 0.5 * level)


def absorb(i):
    k = 0.8 * 1.12 ** (i - 1)                 # 조각을 하나씩 빨아들일수록 한 단씩 높게
    return S('reward', 0.16, [L('UI:glass_005', k=k, decay=0.07), L('UI:drop_001', db=-8.0, k=k * 1.2, decay=0.05)],
             room=0.1, target=-18.0)


def enhance_level(level):
    layers = [L('SF:forceField_001', k=1.35 - 0.15 * level, length=0.6, decay=0.35),
              L('DG:powerUp3', at=0.02, db=-9.0, k=0.85 - 0.08 * level, decay=0.3),
              L('IM:impactPlate_light_001', db=-10.0, k=0.9)]
    if level >= 2:
        layers.append(L('SF:laserLarge_001', at=0.05, db=-10.0, k=0.7, decay=0.3))
    if level >= 3:
        layers.append(L('SF:lowFrequency_explosion_000', db=-5.0, length=0.8, decay=0.35))
        layers.append(L('IM:impactBell_heavy_001', at=0.08, db=-14.0, k=0.6, decay=0.4))
    return S('gauge', [0.7, 0.85, 0.95][level - 1], layers, room=0.2, target=[-12.0, -11.0, -10.0][level - 1])


def ult_final(kind):
    """궁극기 마무리: 무기의 재질 + 깊은 폭발 + 넓은 울림."""
    sig = {
        'pipe': [L('IM:impactMetal_heavy_000', k=0.65), L('IM:impactBell_heavy_000', at=0.01, db=-9.0, k=0.55, decay=0.45)],
        'knife': [L('RP:knifeSlice', k=0.8, hp=300), L('IM:impactMetal_light_003', at=0.06, db=-3.0, k=0.8)],
        'pistol': [L('SF:explosionCrunch_000', k=1.25, length=0.18, hp=160, decay=0.06),
                   L('SF:explosionCrunch_001', at=0.07, k=1.3, length=0.18, hp=160, decay=0.06, db=-1.0),
                   L('SF:explosionCrunch_003', at=0.14, k=1.2, length=0.25, hp=150, decay=0.08)],
        'gauntlet': [L('IM:impactPunch_heavy_002', k=0.7), L('IM:impactPlate_heavy_004', at=0.01, db=-4.0, k=0.7)],
        'chain': [L('RP:handleCoins', k=0.6, length=0.5, decay=0.25), L('IM:impactPlate_heavy_002', at=0.02, db=-2.0, k=0.8),
                  L('IM:impactMetal_heavy_003', at=0.04, db=-4.0, k=0.75)],
    }[kind]
    base = 0.14 if kind == 'pistol' else 0.0
    return S('big', 0.95, sig + [L('SF:lowFrequency_explosion_001', at=base, db=-2.0, length=0.8, decay=0.35),
                                 L('SF:explosionCrunch_004', at=base, db=-8.0, length=0.7, decay=0.3),
                                 Y('sub', at=base, db=-8.0, f0=90, f1=38, decay=5, sec=0.7)], room=0.35)


RECIPES = {
    # ① 타격: 휘두르기 (칼 바람 녹음을 낮춰 무기의 무게로)
    'swing': swing(0.68, 0.24),
    'swing_1': swing(0.66, 0.24),
    'swing_2': swing(0.61, 0.27),
    'swing_3': swing(0.5, 0.34, extra=[Y('sub', at=0.06, db=-15.0, f0=110, f1=50, decay=12, sec=0.25)], target=-14.5),
    'swing_air': swing(0.76, 0.26, lp=8000),
    'swing_dash': swing(0.85, 0.22, extra=[L(THR, db=-12.0, k=1.5, start=0.3, length=0.18, hp=500, decay=0.06)]),
    'swing_plunge': swing(0.47, 0.34, extra=[Y('sub', at=0.1, db=-15.0, f0=100, f1=45, decay=10, sec=0.25)],
                          target=-14.5, variants=False),
    'swing_fade': swing(0.6, 0.22, lp=1800, target=-18.0, air_db=-18.0),
    'swing_awake': swing(0.72, 0.28, extra=[L('UI:glass_004', at=0.02, db=-15.0, k=0.8, length=0.25, decay=0.1)]),
    'swing_critical': swing(0.6, 0.3, extra=[L('SF:explosionCrunch_002', at=0.03, db=-11.0, k=1.2, length=0.2, hp=900,
                                               decay=0.08)], target=-15.0),
    'swing_enhanced': swing(0.55, 0.42, extra=[L('SF:forceField_001', db=-4.0, k=1.3, length=0.4, decay=0.15)],
                            target=-13.0, variants=False, room=0.15),
    'swing_enh1': swing(0.56, 0.42, extra=[L('SF:forceField_000', db=-4.0, k=1.35, length=0.4, decay=0.15)],
                        target=-13.0, variants=False, room=0.15),
    'swing_enh2': swing(0.53, 0.5, extra=[L('SF:forceField_003', db=-4.0, k=1.2, length=0.45, decay=0.18),
                                          L('SF:laserLarge_002', at=0.02, db=-12.0, k=0.8, decay=0.2)],
                        target=-12.5, variants=False, room=0.18),
    'swing_enh3': swing(0.5, 0.58, extra=[L('SF:forceField_004', db=-3.0, k=1.05, length=0.5, decay=0.2),
                                          L('SF:laserLarge_004', at=0.02, db=-10.0, k=0.7, decay=0.25),
                                          Y('sub', at=0.04, db=-14.0, f0=100, f1=40, decay=7, sec=0.4)],
                        target=-12.0, variants=False, room=0.2),
    'accent_awake': S('accent', 0.28, [L('UI:glass_004', k=0.72, decay=0.12), L('DG:phaserUp1', db=-8.0, k=0.85, decay=0.1)],
                      room=0.15, hp=600),
    'accent_critical': S('accent', 0.28, [L('SF:explosionCrunch_002', k=1.3, length=0.25, hp=1200, decay=0.08),
                                          L('DG:zap1', db=-10.0, k=1.4, length=0.2, decay=0.06)], room=0.12),
    # ① 타격: 무기 타격음 (몸통 + 타격 순간 + 꼬리)
    'impact_pipe': S('impact', 0.3, [L(MH, k=0.85), L(PH, db=-3.0, k=0.9, decay=0.1),
                                     L(PLH, db=-9.0, k=0.95, decay=0.12)], variants=True),
    'impact_pipe_heavy': S('impact', 0.5, [L('IM:impactMetal_heavy_000', k=0.75), L('IM:impactPunch_heavy_002', db=-1.0, k=0.8),
                                           L('IM:impactMining_004', at=0.005, db=-4.0, k=0.9, decay=0.2),
                                           L('IM:impactPlate_heavy_004', db=-7.0, k=0.8, decay=0.25),
                                           Y('sub', db=-8.0, f0=80, f1=40, decay=9, sec=0.35)], room=0.2, target=-8.5),
    'impact_pipe_dash': S('impact', 0.3, [L(MH, k=0.9), L(ML, db=-6.0, k=0.95, decay=0.1),
                                          L(PM, db=-4.0, k=0.95, decay=0.1)], variants=True),
    'impact_pipe_air': S('impact', 0.28, [L(MM, k=0.8, decay=0.12), L(PM, db=-3.0, k=0.9, decay=0.1),
                                          L(PLL, db=-9.0, k=0.95, decay=0.1)], variants=True, target=-10.5),
    'impact_pipe_plunge': S('impact', 0.55, [L('IM:impactMining_000', k=0.85), L('IM:impactMetal_heavy_003', db=-1.0, k=0.7),
                                             L('SF:explosionCrunch_000', db=-7.0, length=0.35, decay=0.15),
                                             L('IM:impactPunch_heavy_004', db=-3.0, k=0.8)], room=0.22, target=-8.5),
    'impact_enh1': S('impact', 0.6, [L('IM:impactMetal_heavy_002', k=0.82), L('IM:impactPunch_heavy_001', db=-2.0, k=0.85),
                                     L('SF:forceField_000', db=-7.0, k=1.5, length=0.4, decay=0.15)], room=0.18, target=-9.0),
    'impact_enh2': S('impact', 0.72, [L('IM:impactMetal_heavy_004', k=0.78), L('IM:impactPunch_heavy_003', db=-2.0, k=0.8),
                                      L('SF:forceField_003', db=-6.0, k=1.3, length=0.5, decay=0.2),
                                      L('SF:laserLarge_001', at=0.01, db=-11.0, k=0.75, decay=0.2)], room=0.22, target=-8.5),
    'impact_enh3': S('impact', 0.88, [L('IM:impactMetal_heavy_000', k=0.7), L('IM:impactPunch_heavy_002', db=-2.0, k=0.75),
                                      L('SF:forceField_004', db=-6.0, k=1.1, length=0.6, decay=0.25),
                                      L('SF:lowFrequency_explosion_001', db=-4.0, length=0.7, decay=0.3),
                                      L('IM:impactBell_heavy_001', at=0.01, db=-13.0, k=0.7, decay=0.4)], room=0.25, target=-8.0),
    'impact_gauntlet': S('impact', 0.32, [L(PH, k=0.85), L(PLM, db=-5.0, k=0.9, decay=0.12), L(SH, db=-6.0, k=0.9, decay=0.1),
                                          Y('sub', db=-11.0, f0=110, f1=50, decay=16, sec=0.2)], variants=True),
    'impact_knife': S('impact', 0.2, [L(SL, k=kv(1.2), start=0.04, length=0.12, hp=500, decay=0.05),
                                      L(ML, db=-4.0, k=1.0, decay=0.08), L(PM, db=-6.0, k=1.0, decay=0.08)],
                      variants=True, target=-11.0),
    'impact_pistol': S('impact', 0.16, [L(MM, k=1.1, length=0.12, decay=0.05), L(PM, db=-4.0, k=1.05, length=0.12, decay=0.05)],
                       variants=True, target=-14.0),
    # ① 타격: 쌍권총
    'shot': shot(),
    'shot_fade': shot(lp=2500, k=1.3, target=-16.0, variants=False),
    'shot_awake': shot(extra=[L('SF:laserRetro_002', db=-15.0, k=1.2, length=0.12, hp=1500, decay=0.05)], variants=False),
    'shot_critical': shot(extra=[L('SF:explosionCrunch_002', db=-7.0, k=1.4, length=0.15, hp=700, decay=0.06)],
                          target=-13.5, variants=False),
    'shot_big': S('shot', 0.6, [L('SF:explosionCrunch_004', k=1.1, length=0.5, hp=120, decay=0.18),
                                L('SF:lowFrequency_explosion_001', db=-4.0, length=0.5, decay=0.2),
                                L('IM:impactMetal_heavy_001', db=-7.0, k=0.9)], room=0.25, target=-10.0),
    # ① 타격: 사슬
    'chain_throw': chain_throw(),
    'chain_throw_fade': chain_throw(lp=2200, target=-16.0),
    'chain_throw_awake': chain_throw(extra=[L('UI:glass_004', at=0.03, db=-15.0, k=0.85, length=0.25, decay=0.1)]),
    'chain_throw_critical': chain_throw(extra=[L('SF:explosionCrunch_002', at=0.04, db=-11.0, k=1.3, length=0.18, hp=900,
                                                 decay=0.07)], target=-13.5),
    'chain_throw_enhanced': chain_throw(extra=[L('SF:forceField_001', db=-7.0, k=1.3, length=0.33, decay=0.15)],
                                        target=-13.0),
    'chain_latch': S('chain', 0.25, [L('RP:metalLatch', k=0.8), L('IM:impactMetal_light_002', db=-4.0, k=0.9, decay=0.08),
                                     L('RP:handleCoins2', db=-8.0, k=0.9, length=0.15, decay=0.06)], target=-12.0),
    'chain_latch_heavy': S('chain', 0.35, [L('RP:metalLatch', k=0.7), L('IM:impactMetal_heavy_001', db=-2.0, k=0.85),
                                           L('IM:impactPunch_heavy_004', db=-6.0, k=0.85),
                                           L('RP:handleCoins', db=-9.0, k=0.75, length=0.25, decay=0.08)], room=0.15, target=-10.5),
    'chain_clash': S('chain', 0.4, [L('IM:impactPlate_heavy_000'), L('IM:impactMetal_heavy_002', at=0.03, db=-1.0, k=0.9),
                                    L('RP:handleCoins', db=-6.0, k=0.8, length=0.3, decay=0.1)], room=0.15, target=-10.0),
    # ① 타격: 적의 재질 (무기 타격음 아래 한 층)
    'enemy_hit': material(PM, SM, k=0.95),
    'hit_flesh': material(PM, SM, k=0.9),
    'hit_beast': material(SH, PM, k=0.95, third=L('RP:dropLeather', db=-8.0, k=1.1, decay=0.08)),
    'hit_small': material(SM, GEN, k=1.35, k2=1.1, db2=-5.0, length=0.2),
    'hit_armor': material(PLM, MM, db2=-3.0, third=L(PM, db=-6.0, decay=0.08)),
    'hit_mech': material(TIN, MM, db2=-3.0, third=L('RP:metalClick', db=-10.0, k=0.9)),
    'hit_armor_crystal': material('IM:impactPlate_medium_002', 'IM:impactGlass_medium_001', db2=-3.0, variants=False),
    'hit_crystal': material('IM:impactGlass_light_001', 'IM:impactGlass_medium_002', db2=-4.0, variants=False),
    'hit_ethereal': material('IM:impactGlass_light_003', 'SF:forceField_002', db2=-10.0, k=0.6, k2=2.0, variants=False,
                             room=0.3, hp=300, length=0.32),
    'hit_boss_metal': material('IM:impactPlate_heavy_002', 'IM:impactMetal_heavy_004', db2=-2.0, k=0.85, k2=0.8,
                               third=L('IM:impactMining_002', db=-6.0, decay=0.12), variants=False, length=0.34),
    'hit_boss_crystal': material('IM:impactGlass_heavy_000', 'IM:impactPlate_heavy_001', db2=-3.0, k=0.85, k2=0.8,
                                 variants=False, length=0.34),
    'hit_organic': material('IM:impactSoft_heavy_003', 'SF:slime_000', db2=-8.0, variants=False, length=0.3),
    # ② 주인공 움직임
    'dash': S('move', 0.24, [L(THR, k=1.4, start=0.3, length=0.2, hp=400, decay=0.07), L(SL, db=-6.0, k=kv(0.9), hp=300, length=0.2, swell=0.25),
                             L(CL, db=-9.0, k=1.5, length=0.18)], variants=True, target=-16.0),
    'jump': S('move', 0.18, [L(FR, k=1.05, decay=0.06), L(CL, db=-6.0, k=1.4, length=0.12, hp=300)], variants=True, target=-21.0),
    'double_jump': S('move', 0.28, [L('RP:cloth1', k=1.6, length=0.2, hp=300), L('RP:knifeSlice2', db=-8.0, k=1.1, hp=500, decay=0.08),
                                    L('UI:glass_002', at=0.01, db=-16.0, k=0.9, decay=0.08)], target=-19.0),
    'land': S('move', 0.2, [L(FC, k=0.9), L(FR, db=-4.0, k=0.95, decay=0.06), L(SM, db=-10.0, k=1.0, decay=0.06)],
              variants=True, target=-21.0),
    'hit': S('hurt', 0.3, [L(PH, k=0.9), L(SH, db=-4.0, k=0.9, decay=0.1),
                           L('SF:explosionCrunch_002', db=-10.0, k=1.3, length=0.1, hp=1500, decay=0.04),
                           L(CL, db=-10.0, k=1.2, length=0.15)], variants=True),
    'death': S('big', 0.98, [L('IM:impactPunch_heavy_002', k=0.7), L('IM:impactSoft_heavy_001', k=0.8, db=-1.0),
                             L('SF:lowFrequency_explosion_000', db=-4.0, length=0.9, decay=0.35),
                             L('RP:dropLeather', at=0.28, db=-4.0, k=0.85), L('IM:footstep_wood_002', at=0.3, db=-8.0, k=0.8)],
               room=0.3, target=-8.5),
    'potion': S('move', 0.45, [L('UI:glass_001', k=0.95, decay=0.15), L('SF:slime_000', at=0.04, db=-8.0, k=1.3, length=0.25, decay=0.1),
                               L('SF:forceField_003', at=0.06, db=-14.0, k=2.0, length=0.3, decay=0.12)], room=0.15, target=-14.0),
    # ③ 적
    'enemy_die': S('enemy', 0.42, [L('IM:impactSoft_heavy_002', k=0.85), L('RP:dropLeather', at=0.08, db=-2.0, k=0.9),
                                   L('SF:explosionCrunch_003', db=-10.0, k=1.2, length=0.3, hp=600, decay=0.12)],
                   room=0.15, target=-11.0),
    'windup_slum': S('windup', 0.32, [L('RP:knifeSlice', k=0.7, rev=True, hp=200), L('RP:beltHandle1', at=0.18, db=-8.0)],
                     room=0.1),
    'windup_thrower': S('windup', 0.26, [L('RP:cloth2', k=1.1, rev=True, length=0.22, hp=250),
                                         L('RP:metalClick', at=0.16, db=-4.0)], target=-15.0),
    'windup_hound': S('windup', 0.36, [L('RP:creak3', k=0.6, lp=2500), L('RP:cloth3', db=-6.0, k=1.2, rev=True, length=0.3)]),
    'windup_guard': S('windup', 0.4, [L('RP:knifeSlice2', k=0.6, rev=True, hp=200), L('RP:metalLatch', at=0.24, db=-2.0, k=0.7),
                                      L('RP:beltHandle2', db=-6.0), L('IM:impactPlate_light_004', at=0.25, db=-8.0)], target=-13.0),
    'windup_drone': S('windup', 0.5, [L('SF:computerNoise_000', start=1.0, length=0.45, sweep=(0.8, 1.7), hp=500, lp=4000),
                                      L('RP:metalClick', db=-6.0, k=1.2)], target=-15.0),
    'windup_cart': S('windup', 0.8, [L('RP:creak2', k=0.8), L('RP:creak1', at=0.25, db=-4.0, k=0.85),
                                     L('RP:metalPot2', db=-14.0, k=0.8, length=0.2, decay=0.1)]),
    'drone_torch': S('enemy', 0.6, [L('SF:thrusterFire_002', start=0.5, length=0.6, hp=300, fade_in=0.03),
                                    L('SF:forceField_002', db=-12.0, k=1.2, length=0.5)], target=-14.0),
    'throw': enemy_throw(variants=True),
    'throw_fade': enemy_throw(lp=2000, target=-17.0),
    'throw_awake': enemy_throw(extra=[L('UI:glass_004', db=-15.0, k=0.9, length=0.18, decay=0.08)], target=-15.0),
    'throw_critical': enemy_throw(extra=[L('SF:explosionCrunch_002', db=-11.0, k=1.4, length=0.15, hp=900, decay=0.06)],
                                  target=-15.0),
    'throw_enhanced': enemy_throw(extra=[L('SF:forceField_001', db=-8.0, k=1.5, length=0.2, decay=0.08)], target=-14.0),
    # ④ 게이지
    'warn_low': S('gauge', 0.5, [L('UI:bong_001', k=0.5, lp=1500), L('UI:bong_001', at=0.22, db=-2.0, k=0.5, lp=1500)],
                  room=0.25, target=-15.0),
    'warn_high': S('gauge', 0.36, [L('UI:error_003', k=0.95), L('UI:error_007', db=-6.0, k=0.9),
                                   L('UI:error_003', at=0.17, db=-3.0, k=0.95)], room=0.1),
    'zone_awake': S('gauge', 0.55, [L('SF:forceField_002', k=1.4, length=0.5, decay=0.2),
                                    L('UI:glass_004', at=0.03, db=-10.0, k=0.8, decay=0.2),
                                    L('DG:phaserUp3', at=0.02, db=-14.0, k=0.9)], room=0.2, target=-15.0),
    'heartbeat': S('gauge', 0.42, [L('IM:impactSoft_medium_001', k=0.6, lp=400), L('IM:impactSoft_medium_002', at=0.16, db=-3.0,
                                                                                     k=0.65, lp=400)], room=0.05, target=-15.0),
    'overload': S('big', 0.98, [L('SF:explosionCrunch_001', k=0.9, length=0.9, decay=0.35),
                                L('SF:lowFrequency_explosion_001', db=-2.0, length=0.8, decay=0.35),
                                L('DG:zap1', db=-10.0, length=0.5, decay=0.2)], room=0.25, target=-7.5),
    'overload_zap': S('gauge', 0.4, [L('DG:zap2', k=1.2, length=0.35, decay=0.15),
                                     L('SF:explosionCrunch_002', db=-6.0, k=1.2, length=0.2, hp=900, decay=0.08)],
                      room=0.15, target=-10.0),
    'stun_end': S('gauge', 0.25, [L('RP:cloth1', k=1.3, length=0.22), L('DG:phaserUp1', db=-6.0, k=1.1, decay=0.1)], target=-14.0),
    'enhance': S('gauge', 0.6, [L('SF:forceField_001', k=1.2, length=0.55, decay=0.3), L('DG:powerUp3', db=-10.0, k=0.7, decay=0.25),
                                L('IM:impactPlate_light_001', db=-12.0)], room=0.2, target=-12.0),
    'enhance_1': enhance_level(1),
    'enhance_2': enhance_level(2),
    'enhance_3': enhance_level(3),
    # ⑤ 줍기·보상
    'pickup': S('reward', 0.35, [L('RP:handleCoins2', k=1.1), L('UI:glass_002', db=-6.0, decay=0.12)], room=0.12),
    'absorb_1': absorb(1), 'absorb_2': absorb(2), 'absorb_3': absorb(3), 'absorb_4': absorb(4), 'absorb_5': absorb(5),
    'absorb_done': S('reward', 0.5, [L('UI:confirmation_001', k=0.85), L('SF:forceField_003', db=-12.0, k=2.0, length=0.3, decay=0.12),
                                     L('UI:glass_004', db=-10.0, k=0.9, decay=0.2)], room=0.18, target=-14.0),
    'kill_streak_1': kill_streak(1), 'kill_streak_2': kill_streak(2), 'kill_streak_3': kill_streak(3),
    'kill_streak_4': kill_streak(4), 'kill_streak_5': kill_streak(5), 'kill_streak_6': kill_streak(6),
    'kill_last': S('big', 0.95, [L('IM:impactPunch_heavy_002', k=0.75), L('IM:impactBell_heavy_001', db=-6.0, k=0.7, decay=0.4),
                                 L('SF:lowFrequency_explosion_001', db=-3.0, length=0.85, decay=0.35)], room=0.35, target=-9.0),
    # ⑥ 메뉴
    'ui_move': S('ui', 0.07, [L('UI:tick_002', k=1.0)], room=0.0, target=-21.0),
    'ui_select': S('ui', 0.16, [L('UI:select_006', k=1.0, decay=0.08)], room=0.05, target=-18.0),
    'ui_back': S('ui', 0.09, [L('UI:back_002', k=0.95)], room=0.03, target=-19.0),
    # ⑦ 보스·궁극기
    'ark_bullet': S('boss', 0.25, [L('SF:laserSmall_001', k=1.0, decay=0.1), L('SF:laserRetro_002', db=-10.0, k=1.1, decay=0.06)],
                    room=0.15, target=-14.0),
    'ark_teleport': S('boss', 0.5, [L('DG:phaseJump1', k=0.8), L('SF:forceField_002', db=-6.0, k=1.5, rev=True, length=0.4)],
                      room=0.25, target=-11.0),
    'ark_roar': S('boss', 0.9, [L('SF:spaceEngineLarge_000', start=1.0, length=0.9, k=0.7, fade_in=0.15, decay=0.5),
                                L('SF:lowFrequency_explosion_000', db=-4.0, length=0.85, decay=0.4),
                                L('RP:creak1', db=-10.0, k=0.4, lp=1500)], room=0.3, target=-9.0),
    'ark_absorb': S('boss', 0.8, [L('SF:forceField_000', rev=True, length=0.69), L('SF:computerNoise_001', start=1.0, length=0.7,
                                                                                    k=0.6, lp=2500, db=-10.0)], room=0.25),
    'ark_burst': S('boss', 0.7, [L('SF:explosionCrunch_003', length=0.7, decay=0.3), L('SF:lowFrequency_explosion_001', db=-3.0,
                                                                                         length=0.6, decay=0.3),
                                 L('DG:zap1', db=-12.0, length=0.3, decay=0.12)], room=0.25, target=-10.0),
    'ark_field': S('boss', 0.8, [L('SF:slime_001', start=0.5, length=0.8, k=0.7, fade_in=0.05), L('SF:forceField_003', db=-6.0, k=0.8)],
                   room=0.25, target=-12.0),
    'ult_cast': S('boss', 0.9, [L('SF:forceField_001', k=0.9, rev=True, length=0.6), L('SF:forceField_001', at=0.55, db=-3.0, k=1.0,
                                                                                         length=0.35),
                                L('DG:powerUp1', db=-10.0, k=0.6, decay=0.4), L('IM:impactBell_heavy_001', at=0.5, db=-12.0, k=0.5,
                                                                                 decay=0.3)],
                    room=0.3, target=-10.0),
    'ult_hit': S('boss', 0.45, [L('IM:impactPunch_heavy_001', k=0.85), L('IM:impactMetal_heavy_002', db=-2.0, k=0.85),
                                L('SF:forceField_000', db=-8.0, k=1.6, length=0.3, decay=0.12)], room=0.18, target=-10.5),
    'ult_final_pipe': ult_final('pipe'), 'ult_final_knife': ult_final('knife'), 'ult_final_pistol': ult_final('pistol'),
    'ult_final_gauntlet': ult_final('gauntlet'), 'ult_final_chain': ult_final('chain'),
    # ⑧ 환경
    'amb_drip': S('amb', 0.5, [L('UI:drop_002', k=0.6), L('UI:drop_003', at=0.0, db=-8.0, k=0.62)], room=0.5),
    'amb_steam': S('amb', 0.8, [L('SF:thrusterFire_000', start=1.0, length=0.8, hp=1500, fade_in=0.08, decay=0.35)], room=0.2),
    'amb_wind': S('amb', 0.95, [L('SF:spaceEngineSmall_001', start=1.0, length=0.95, hp=200, lp=1500, fade_in=0.25, decay=0.45)],
                  room=0.2),
    'amb_forge': S('amb', 0.6, [L('RP:metalPot1', k=0.5, length=0.5, lp=1500, decay=0.25),
                                L('SF:explosionCrunch_002', start=0.3, length=0.4, hp=2000, db=-12.0)], room=0.25, target=-25.0),
}

# 묶음: 통째로 바꾸거나 통째로 둔다 (tests/test_sfx_s2.py). 위에서부터 우선순위
GROUPS = {
    '① 타격': [n for n in RECIPES if n.startswith(('swing', 'accent', 'impact', 'shot', 'chain', 'hit_')) or n == 'enemy_hit'],
    '② 주인공 움직임': ['dash', 'jump', 'double_jump', 'land', 'hit', 'death', 'potion'],
    '③ 적': ['enemy_die', 'windup_slum', 'windup_thrower', 'windup_hound', 'windup_guard', 'windup_drone', 'windup_cart',
            'drone_torch', 'throw', 'throw_fade', 'throw_awake', 'throw_critical', 'throw_enhanced'],
    '④ 게이지': ['warn_low', 'warn_high', 'zone_awake', 'heartbeat', 'overload', 'overload_zap', 'stun_end',
              'enhance', 'enhance_1', 'enhance_2', 'enhance_3'],
    '⑤ 줍기·보상': ['pickup', 'absorb_1', 'absorb_2', 'absorb_3', 'absorb_4', 'absorb_5', 'absorb_done',
                'kill_streak_1', 'kill_streak_2', 'kill_streak_3', 'kill_streak_4', 'kill_streak_5', 'kill_streak_6', 'kill_last'],
    '⑥ 메뉴': ['ui_move', 'ui_select', 'ui_back'],
    '⑦ 보스·궁극기': ['ark_bullet', 'ark_teleport', 'ark_roar', 'ark_absorb', 'ark_burst', 'ark_field', 'ult_cast', 'ult_hit',
                 'ult_final_pipe', 'ult_final_knife', 'ult_final_pistol', 'ult_final_gauntlet', 'ult_final_chain'],
    '⑧ 환경': ['amb_drip', 'amb_steam', 'amb_wind', 'amb_forge'],
}


# ----- 처리 -----
_cache = {}


def load_src(ref):
    if ref not in _cache:
        _cache[ref] = K.trim(K.load(os.path.join(SRC_ROOT, src_path(ref))), threshold=0.02, pad=0.0005).astype(np.float64)
    return _cache[ref]


def pick(v, value):
    return value[(v - 1) % len(value)] if isinstance(value, list) else value


def filt(x, hp=None, lp=None):
    if hp:
        x = signal.sosfilt(signal.butter(2, hp, 'highpass', fs=R, output='sos'), x)
    if lp:
        x = signal.sosfilt(signal.butter(2, min(lp, R / 2 - 100), 'lowpass', fs=R, output='sos'), x)
    return x


def resample(x, k):
    if abs(k - 1.0) < 1e-6:
        return x
    n = max(2, int(len(x) / k))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def sweep(x, k0, k1):
    """음 높이를 k0 -> k1로 쓸며 읽는다 (서보 모터가 돌아가는 소리처럼)."""
    pos, i, out = 0.0, 0, []
    n = len(x)
    while pos < n - 1:
        out.append(x[int(pos)])
        t = pos / n
        pos += k0 + (k1 - k0) * t
        i += 1
    return np.array(out)


def ramp_out(x, sec):
    n = min(len(x), int(sec * R))
    if n > 0:
        x = x.copy()
        x[-n:] *= np.linspace(1, 0, n) ** 1.5
    return x


def rec_layer(lay, v, pv):
    x = load_src(pick(v, lay['src']))
    start = int(lay['start'] * R)
    x = x[start:]
    k = pick(v, lay['k'])
    if not isinstance(lay['k'], list):
        k *= pv
    if lay['sweep']:
        x = sweep(x, lay['sweep'][0] * k, lay['sweep'][1] * k)
    else:
        x = resample(x, k)
    if lay['length']:
        x = ramp_out(x[:int(lay['length'] * R)], min(0.04, lay['length'] * 0.3))
    if lay['rev']:
        x = x[::-1]
    x = filt(x, lay['hp'], lay['lp'])
    if lay['decay']:
        x = x * np.exp(-np.arange(len(x)) / (lay['decay'] * R))
    if lay.get('swell'):
        p = np.linspace(0, 1, len(x))
        pk = lay['swell']
        x = x * np.where(p < pk, (p / pk) ** 1.2, ((1 - p) / (1 - pk)) ** 1.8)
    if lay['fade_in']:
        n = min(len(x), int(lay['fade_in'] * R))
        x = x.copy()
        x[:n] *= np.linspace(0, 1, n)
    return x


_rng = np.random.default_rng(11)


def synth_layer(lay, v, pv):
    sec = lay['sec']
    t = np.arange(int(sec * R)) / R
    if lay['kind'] == 'sub':                       # 떨어지는 낮은 사인 + 아주 짧은 클릭 없이
        f = lay['f1'] + (lay['f0'] - lay['f1']) * np.exp(-t * 25)
        x = np.sin(2 * np.pi * np.cumsum(f * pv) / R) * np.exp(-t * lay['decay'])
        x[:int(0.002 * R)] *= np.linspace(0, 1, int(0.002 * R))
        return x
    if lay['kind'] == 'air':                       # 띠 잡음: 중심 주파수를 f0 -> f1로 (바람의 '쉭')
        rng = np.random.default_rng(100 + v)
        noise = rng.uniform(-1, 1, len(t))
        out = np.zeros(len(t))
        seg = 512
        for i in range(0, len(t), seg):
            fc = (lay['f0'] + (lay['f1'] - lay['f0']) * min(1.0, i / len(t) / 0.8)) * pv
            sos = signal.butter(2, [fc * 0.6, min(fc * 1.6, R / 2 - 100)], 'bandpass', fs=R, output='sos')
            out[i:i + seg] = signal.sosfilt(sos, noise[max(0, i - 2048):i + seg])[-len(noise[i:i + seg]):]
        p = np.linspace(0, 1, len(t))
        env = np.where(p < 0.35, (p / 0.35) ** 1.3, ((1 - p) / 0.65) ** 2)
        return out * env
    raise ValueError(lay['kind'])


def room_ir():
    """같은 방 잔향 한 가지 (작은 콘크리트 방, 잔향 0.38초, 어둡게). 모든 소리가 같은 방에서 나게."""
    rng = np.random.default_rng(7)
    n = int(0.45 * R)
    t = np.arange(n) / R
    ir = rng.standard_normal(n) * np.exp(-t * 6.9 / 0.38)
    ir = filt(ir, hp=200, lp=4500)
    ir[:int(0.008 * R)] = 0                        # 8ms 뒤부터
    for d, a in ((0.007, 0.5), (0.013, 0.35), (0.021, 0.25)):
        ir[int(d * R)] += a
    return ir / np.sqrt(np.sum(ir ** 2))


_IR = room_ir()
PEAK = 10 ** (-1.2 / 20)                           # 최대값 상한 -1.2dBFS (시험 기준 -1dBFS보다 조금 아래)


def limit(x, ceiling=PEAK, knee=0.55):
    """부드러운 리미터: knee 위는 tanh로 눌러 ceiling을 넘지 않게."""
    a = np.abs(x)
    over = a > knee * ceiling
    y = x.copy()
    lo = knee * ceiling
    y[over] = np.sign(x[over]) * (lo + (ceiling - lo) * np.tanh((a[over] - lo) / (ceiling - lo)))
    return y


def loud_of(x):
    return M.measure(x)['loud_db']


def finish(x, target, length):
    x = filt(x, hp=35)
    # 앞 무음: 최대값의 2%를 처음 넘는 곳에서 0.5ms 앞부터
    a = np.abs(x)
    first = int(np.argmax(a > a.max() * 0.02))
    x = x[max(0, first - int(0.0005 * R)):]
    x = ramp_out(x[:int(length * R)], min(0.06, length * 0.3))
    x[:int(0.0005 * R)] *= np.linspace(0, 1, int(0.0005 * R))
    for _ in range(6):                              # 목표 크기로, 넘치면 리미터. 리미터가 크기를 깎으면 다시
        g = 10 ** ((target - loud_of(x)) / 20)
        y = limit(x * g)
        if abs(loud_of(y) - target) < 0.3:
            break
        x = y if loud_of(y) < target else x * g
    y = limit(y)
    m = np.max(np.abs(y))
    if m > PEAK:
        y *= PEAK / m
    a = np.abs(y)                                   # 리미터가 최대값을 눌렀으니 앞 무음을 한 번 더: 최대값의 2.5%부터
    first = int(np.argmax(a > a.max() * 0.03))
    y = y[max(0, first - int(0.0005 * R)):].copy()
    y[:int(0.0005 * R)] *= np.linspace(0, 1, int(0.0005 * R))
    return y


def build_one(name, recipe, v=1):
    pv = {1: 1.0, 2: 0.95, 3: 1.05}[v] if recipe['variants'] else 1.0
    parts, used, synth = [], set(), []
    for lay in recipe['layers']:
        if lay['kind'] == 'rec':
            x = rec_layer(lay, v, pv)
            used.add(src_path(pick(v, lay['src'])).rsplit('.', 1)[0] + '.ogg')
        else:
            x = synth_layer(lay, v, pv)
            synth.append(lay['kind'])
        parts.append((lay['at'], x * 10 ** (lay['db'] / 20)))
    total = max(int(at * R) + len(x) for at, x in parts)
    out = np.zeros(total + int(0.45 * R))
    for at, x in parts:
        i = int(at * R)
        out[i:i + len(x)] += x
    out = filt(out, recipe['hp'], recipe['lp'])
    if recipe['room']:
        wet = signal.fftconvolve(out, _IR)[:len(out)]
        out = out + wet * recipe['room']
    target = recipe['target'] if recipe['target'] is not None else GROUP_TARGET[recipe['group']]
    return finish(out, target, recipe['length']), sorted(used), synth


def write_wav(path, x):
    data = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(R)
        f.writeframes(data.tobytes())


def variant_names():
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import config
    return set(config.SFX_VARIANTS)


def build(only=None):
    os.makedirs(OUT, exist_ok=True)
    frequent = variant_names()
    manifest = {'note': 'tools/make_sfx_v3.py가 굽는다. sounds: 이름 -> 묶음·쓴 원본(assets/sfx_src 아래)·합성 보조·수치',
                'sources': SOURCES, 'sounds': {}}
    for group, names in GROUPS.items():
        for name in names:
            recipe = RECIPES[name]
            if only and name not in only:
                continue
            if name in frequent and not recipe['variants']:
                raise ValueError(f'{name}: 자주 나는 소리인데 변주가 없다')
            files = [(name, 1)] + ([(name + '_v2', 2), (name + '_v3', 3)] if recipe['variants'] else [])
            info = {'group': group, 'sources': [], 'synth': [], 'files': {}}
            for fname, v in files:
                x, used, synth = build_one(name, recipe, v)
                write_wav(os.path.join(OUT, fname + '.wav'), x)
                info['sources'] = sorted(set(info['sources']) | set(used))
                info['synth'] = sorted(set(info['synth']) | set(synth))
                m = M.measure(x)
                info['files'][fname] = {k: (round(val, 2) if isinstance(val, float) else val) for k, val in m.items()}
            manifest['sounds'][name] = info
    with open(os.path.join(OUT, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    return manifest


def all_refs():
    refs = set()
    for recipe in RECIPES.values():
        for lay in recipe['layers']:
            if lay['kind'] == 'rec':
                refs |= set(lay['src'] if isinstance(lay['src'], list) else [lay['src']])
    return refs


def import_from(folder):
    """Kenney 압축을 푼 폴더(묶음마다 하위 폴더, 또는 파일이 한 폴더에)에서 쓰는 원본만 assets/sfx_src/kenney로 복사."""
    index = {}
    for dirpath, _d, files in os.walk(folder):
        for f in files:
            index.setdefault(f, os.path.join(dirpath, f))
    missing = []
    for ref in sorted(all_refs()):
        rel = src_path(ref)
        dst = os.path.join(SRC_ROOT, rel)
        if os.path.exists(dst):
            continue
        name = os.path.basename(rel)
        if name not in index:
            missing.append(ref)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(index[name], dst)
    for pack in PACK.values():
        lic = os.path.join(SRC_ROOT, 'kenney', pack, 'License.txt')
        if not os.path.exists(lic):
            raise SystemExit(f'라이선스 문서가 없다: {lic}')
    if missing:
        raise SystemExit('원본을 찾지 못했다: ' + ', '.join(missing))


# ----- 확인 자료 (아무도 들을 수 없어 수치·그림으로) -----
REVIEW_20 = ['impact_pipe', 'impact_pipe_heavy', 'impact_gauntlet', 'impact_pistol', 'shot', 'chain_throw', 'chain_latch',
             'swing_1', 'swing_3', 'hit_flesh', 'hit_armor', 'dash', 'jump', 'land', 'hit', 'enemy_die', 'windup_guard',
             'overload', 'kill_streak_3', 'ui_select']


def band_ratio(x, lo, hi):
    s = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / R)
    return float(s[(f >= lo) & (f < hi)].sum() / (s.sum() or 1))


def review(folder):
    manifest = json.load(open(os.path.join(OUT, 'MANIFEST.json'), encoding='utf-8'))
    os.makedirs(folder, exist_ok=True)
    rows = []
    for group, names in GROUPS.items():
        for name in names:
            info = manifest['sounds'].get(name)
            new = M.read_wav(os.path.join(OUT, name + '.wav'))[0]
            oldp = os.path.join(OLD, name + '.wav')
            old = M.read_wav(oldp)[0] if os.path.exists(oldp) else None
            rows.append((group, name, info, M.measure(new), M.measure(old) if old is not None else None,
                         (band_ratio(new, 60, 400), band_ratio(old, 60, 400) if old is not None else None)))
    lines = ['# S2-2 효과음 v3 이벤트 표 (2026-11-27, tools/make_sfx_v3.py --review)', '',
             '아무도 들어 보지 않았다. 수치만 잰 것이다(tools/sfx_metrics.py). 크기는 가장 큰 50ms RMS(dBFS), 밝기는 스펙트럼 중심(Hz),',
             '저음은 200Hz 아래 에너지 비율, 몸통은 60~400Hz 비율, 앞은 앞 무음(ms). 크기는 실제 재생 크기: 예전은 파일 값 + config.SFX_GAIN,',
             '새 것은 파일 값 + config.SFX_V3_LEVEL(+2.9dB). 최대는 파일 값(dBFS).',
             '빈도는 밸런스 봇(구역 시나리오, 시드 3) 동안 재생된 횟수의 비율(봇은 메뉴·줍기·환경음을 거의 내지 않는다).', '',
             '| 묶음 | 소리 | 변주 | 원본 (모두 Kenney CC0) | 합성 보조 | 길이 예전→새 | 크기 예전→새 | 최대 새 | 앞 새 | 밝기 예전→새 | 저음 예전→새 | 몸통 예전→새 | 빈도 |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    freq = {}
    fp = os.path.join(os.path.dirname(folder), '..', 'shots', 'review', 'S2_counts.json')
    for cand in (os.path.join(folder, 'S2_counts.json'), fp):
        if os.path.exists(cand):
            freq = json.load(open(cand, encoding='utf-8'))
            break
    total = sum(freq.values()) or 1
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import config
    V3DB = 20 * np.log10(config.SFX_V3_LEVEL)
    for group, name, info, mn, mo, (bn, bo) in rows:
        srcs = ', '.join(s.split('/')[-1][:-4] for s in info['sources'])
        old_loud = (mo['loud_db'] + 20 * np.log10(config.SFX_GAIN.get(name, 1.0))) if mo else None
        mn = dict(mn, loud_db=mn['loud_db'] + V3DB)
        f = lambda v, fmt: (fmt % v) if v is not None else '-'      # noqa: E731
        lines.append(f"| {group} | `{name}` | {len(info['files'])} | {srcs} | {', '.join(info['synth']) or '-'} | "
                     f"{f(mo and mo['length'], '%.2f')}→{mn['length']:.2f} | {f(old_loud, '%.1f')}→{mn['loud_db']:.1f} | "
                     f"{mn['peak_db']:.1f} | {mn['lead_ms']:.1f} | {f(mo and mo['centroid'], '%.0f')}→{mn['centroid']:.0f} | "
                     f"{f(mo and mo['low'], '%.2f')}→{mn['low']:.2f} | {f(bo, '%.2f')}→{bn:.2f} | "
                     f"{freq.get(name, 0) / total * 100:.1f}% |")
    # 묶음별 요약
    lines += ['', '## 묶음별 요약 (중앙값)', '', '| 묶음 | 소리 수 | 크기 예전→새 | 크기 퍼짐(최대-최소) 예전→새 | 밝기 예전→새 | 몸통 예전→새 |', '|---|---|---|---|---|---|']
    for group in GROUPS:
        g = [r for r in rows if r[0] == group and r[4] is not None]
        if not g:
            continue
        ol = [r[4]['loud_db'] + 20 * np.log10(config.SFX_GAIN.get(r[1], 1.0)) for r in g]
        nl = [r[3]['loud_db'] + V3DB for r in g]
        lines.append(f"| {group} | {len(g)} | {np.median(ol):.1f}→{np.median(nl):.1f} | {max(ol) - min(ol):.1f}→{max(nl) - min(nl):.1f} | "
                     f"{np.median([r[4]['centroid'] for r in g]):.0f}→{np.median([r[3]['centroid'] for r in g]):.0f} | "
                     f"{np.median([r[5][1] for r in g]):.2f}→{np.median([r[5][0] for r in g]):.2f} |")
    # 변주끼리 차이
    lines += ['', '## 변주끼리 차이 (스펙트럼 모양 차이, 0이면 같은 소리. 예전 v2 변주와 비교)', '', '| 소리 | 예전 | 새 |', '|---|---|---|']
    for name in sorted(config.SFX_VARIANTS):
        if not os.path.exists(os.path.join(OUT, name + '_v2.wav')):
            continue

        def dist(folder_):
            xs = [M.read_wav(os.path.join(folder_, name + s + '.wav'))[0] for s in ('', '_v2', '_v3')]
            return np.mean([M.spectrum_distance(xs[i], xs[j]) for i, j in ((0, 1), (0, 2), (1, 2))])
        lines.append(f'| `{name}` | {dist(OLD):.2f} | {dist(OUT):.2f} |')
    with open(os.path.join(folder, 'S2_sfx_table.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    wave_sheet(os.path.join(folder, 'S2_sfx_wave.png'))


def wave_sheet(path):
    """주요 소리 20개: 줄마다 예전 | 새, 각각 파형(위)과 스펙트로그램(아래, 0~11kHz, 밝을수록 큼). 같은 시간 축(0.6초)."""
    from PIL import Image, ImageDraw, ImageFont
    cw, wh, sh, span = 560, 70, 90, 0.6
    rowh = wh + sh + 30
    img = Image.new('RGB', (200 + 2 * cw + 30, 40 + rowh * len(REVIEW_20)), (16, 18, 22))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('malgun.ttf', 14)
    except OSError:
        font = ImageFont.load_default()
    d.text((200, 10), '예전 (assets/sfx)', fill=(200, 200, 200), font=font)
    d.text((200 + cw + 20, 10), '새 (assets/sfx_v3)', fill=(200, 200, 200), font=font)
    for i, name in enumerate(REVIEW_20):
        y0 = 40 + i * rowh
        d.text((10, y0 + 60), name, fill=(230, 230, 230), font=font)
        for j, folder in enumerate((OLD, OUT)):
            x0 = 200 + j * (cw + 20)
            p = os.path.join(folder, name + '.wav')
            if not os.path.exists(p):
                continue
            x = M.read_wav(p)[0]
            m = M.measure(x)
            n = int(span * R)
            xs = np.zeros(n)
            xs[:min(n, len(x))] = x[:n]
            cols = xs[:cw * (n // cw)].reshape(cw, -1)
            mid = y0 + wh // 2
            for c in range(cw):
                lo, hi = cols[c].min(), cols[c].max()
                d.line([(x0 + c, mid - int(hi * wh / 2)), (x0 + c, mid - int(lo * wh / 2))], fill=(120, 200, 230))
            d.line([(x0, mid), (x0 + cw, mid)], fill=(50, 60, 70))
            f_, t_, Z = signal.spectrogram(xs, fs=R, nperseg=512, noverlap=384)
            Z = 10 * np.log10(Z[f_ <= 11000] + 1e-12)
            Z = np.clip((Z - (Z.max() - 70)) / 70, 0, 1)
            spec = Image.fromarray((np.flipud(Z) * 255).astype(np.uint8), 'L').resize((cw, sh), Image.BILINEAR)
            img.paste(Image.merge('RGB', (spec, spec.point(lambda v: int(v * 0.8)), spec.point(lambda v: int(v * 0.5)))),
                      (x0, y0 + wh + 2))
            d.text((x0 + 4, y0 + wh + sh + 6), f"{m['length']:.2f}s  크기 {m['loud_db']:.1f}  최대 {m['peak_db']:.1f}  "
                                                f"밝기 {m['centroid']:.0f}Hz  저음 {m['low']:.2f}", fill=(170, 170, 170), font=font)
    img.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--import', dest='imp', help='Kenney 압축을 푼 폴더')
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--review', help='확인 자료를 쓸 폴더 (예: shots/review)')
    a = ap.parse_args()
    if a.imp:
        import_from(a.imp)
    if a.review:
        review(a.review)
        return
    m = build(a.only)
    print(f"{len(m['sounds'])}종, 파일 {sum(len(i['files']) for i in m['sounds'].values())}개 -> {OUT}")


if __name__ == '__main__':
    main()
