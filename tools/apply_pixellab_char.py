"""v6 적·보스(PixelLab)를 게임 그림으로 적용한다 (2026-11-23, docs/plan_v6.md). 주인공은 tools/apply_pixellab_hero.py.

캐릭터마다 assets/sprites/pixellab/<캐릭터>_v6/raw/ 에 base.png(첫 프레임·색 기준)와 동작 폴더(frame_N.png)가 있다.
1. 알파 0/255, 몸과 떨어진 흰 궤적 제거, 색을 base의 색으로만 다시 칠한다.
2. 'loop' 동작은 몸 가로 중심을 구간 평균에 맞춰 흔들림을 없앤다. 나머지는 원본 위치 그대로(base와 같은 좌표).
3. 최근접 2배로 키워 assets/sprites/unified/<접두>_<동작>_<번호>.png 로 쓴다.
4. assets/sprites/unified/skin_<캐릭터>.json 에 {"frames": {세트: [장수, 기준점 x, y]}, "skin": {기존 이름: 세트}}.
   src/sprites.py가 읽어 기존 이름(enemy_guard_walk 등)을 새 그림으로 바꿔 그린다. 게임 코드는 그대로.
공격처럼 적 코드가 장수로 타이밍을 잡는 동작은 기존과 같은 장수를 고른다 (src/sprites.py FRAMES의 기존 장수).

실행: python tools/apply_pixellab_char.py [캐릭터 ...]   (없으면 원본이 있는 캐릭터 전부)
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_pixellab_hero import foot_row, lock_palette, palette_of, remove_white_arcs, shift_x  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIX = os.path.join(ROOT, 'assets', 'sprites', 'pixellab')
DST = os.path.join(ROOT, 'assets', 'sprites', 'unified')
SCALE = 2


def _f(src, numbers):
    return [(src, n) for n in numbers]


# 캐릭터: {'prefix': 새 세트 접두, 'sets': {세트 꼬리: (프레임 목록, 맞추기)}, 'skin': {기존 이름: 세트 꼬리}}
# 프레임 번호는 PixelLab 결과를 본 뒤 정한다 (shots/pixellab_test/<캐릭터>_v6_<동작>.png).
CHARS = {
    # 간수 (2026-11-23, shots/pixellab_test/guard_all.png). 적 공격 그림은 1 예고·2 타격·3 회수 (src/enemy.py _attack_frame)
    'guard': {
        'prefix': 'v6_guard',
        'sets': {
            'idle': ([('base.png', None)], 'none'),                 # 서 있기 = 확정 그림
            'walk': (_f('walk', range(0, 8)), 'loop'),
            'swing': (_f('swing', [1, 3, 5]), 'none'),             # 곤봉 젖힘 -> 앞으로 내지름 -> 회수 (4번은 궤적이 그려져 뺌)
            'heavy': (_f('heavy', [1, 3, 4]), 'none'),             # 머리 위로 듦 -> 내려찍음 -> 회수
            'bash': (_f('bash', [1, 3]), 'none'),                  # 방패 웅크림 -> 밀치기
            'hurt': (_f('hurt', [0, 1]), 'none'),
            'death': (_f('death', [2, 5, 7]), 'none'),             # 무릎 -> 쓰러짐 -> 누움
        },
        'skin': {'enemy_guard': 'idle', 'enemy_guard_walk': 'walk', 'enemy_guard_swing': 'swing',
                 'enemy_guard_heavy': 'heavy', 'enemy_guard_bash': 'bash', 'enemy_guard_hurt': 'hurt',
                 'enemy_guard_death': 'death'},
    },
    # 적 5종 (2026-11-23, shots/pixellab_test/<이름>_all.png). 장수는 src/enemy.py·enemy_kinds.py가 쓰는 그대로.
    'slum': {
        'prefix': 'v6_slum',
        'sets': {'idle': ([('base.png', None)], 'none'), 'walk': (_f('walk', range(0, 8)), 'loop'),
                 'attack': (_f('attack', [1, 3, 5]), 'none'), 'hurt': (_f('hurt', [0, 1]), 'none'),
                 'death': (_f('death', [2, 4, 7]), 'none')},
        'skin': {'enemy_slum_idle': 'idle', 'enemy_slum_walk': 'walk', 'enemy_slum_attack': 'attack',
                 'enemy_slum_hurt': 'hurt', 'enemy_slum_death': 'death'},
    },
    'thrower': {
        'prefix': 'v6_thrower',
        'sets': {'idle': ([('base.png', None)], 'none'), 'walk': (_f('walk', range(0, 8)), 'loop'),
                 'back': (_f('walk', [0, 4]), 'loop'), 'throw': (_f('throw', [1, 3, 5]), 'none'),
                 'hurt': (_f('hurt', [1, 2]), 'none'), 'death': (_f('death', [2, 4, 7]), 'none')},
        'skin': {'enemy_thrower_idle': 'idle', 'enemy_thrower_walk': 'walk', 'enemy_thrower_back': 'back',
                 'enemy_thrower_throw': 'throw', 'enemy_thrower_hurt': 'hurt', 'enemy_thrower_death': 'death'},
    },
    'hound': {
        'prefix': 'v6_hound',
        'sets': {'idle': ([('base.png', None)], 'none'), 'run': (_f('run', range(1, 9)), 'loop'),
                 'bite': (_f('bite', [3, 4, 6]), 'none'), 'pounce': (_f('pounce', [4, 6]), 'none'),
                 'hurt': (_f('hurt', [1, 3]), 'none'), 'death': (_f('death', [5, 6, 8]), 'none')},
        'skin': {'enemy_hound_idle': 'idle', 'enemy_hound_run': 'run', 'enemy_hound_bite': 'bite',
                 'enemy_hound_pounce': 'pounce', 'enemy_hound_hurt': 'hurt', 'enemy_hound_death': 'death'},
    },
    'drone': {
        'prefix': 'v6_drone',
        'float_hb': 32, 'foot_sets': ('wreck',),          # 몸통 중심을 히트박스 가운데에 (기존 드론 규칙), 잔해는 바닥
        'sets': {'fly': (_f('fly', [1, 2, 3, 4]), 'loop'), 'aim': (_f('aim', [2, 4]), 'none'),
                 'fire': (_f('fire', [3, 4, 5]), 'none'), 'hurt': (_f('hurt', [3, 4]), 'none'),
                 'wreck': (_f('wreck', [6, 8]), 'none')},
        'skin': {'enemy_drone_idle': 'fly', 'enemy_drone_fly': 'fly', 'enemy_drone_aim': 'aim',
                 'enemy_drone_fire': 'fire', 'enemy_drone_hurt': 'hurt', 'enemy_drone_wreck': 'wreck'},
    },
    'knight': {
        'prefix': 'v6_knight',
        'sets': {'idle': (_f('idle', [1, 3]), 'loop'), 'walk': (_f('walk', range(0, 8)), 'loop'),
                 'slash': (_f('slash', [1, 3, 5]), 'none'), 'vanish': (_f('vanish', [2, 3]), 'none'),
                 'appear': (_f('appear', [2, 3]), 'none'), 'hurt': (_f('hurt', [2]), 'none'),
                 'death': (_f('death', [2, 4, 7]), 'none')},
        'skin': {'enemy_knight_idle': 'idle', 'enemy_knight_walk': 'walk', 'enemy_knight_slash': 'slash',
                 'enemy_knight_vanish': 'vanish', 'enemy_knight_appear': 'appear', 'enemy_knight_hurt': 'hurt',
                 'enemy_knight_death': 'death'},
    },
    # 크래셔 (3/4 시점 v2, shots/pixellab_test/crasher_all_b.png). 장수는 보스 코드(src/boss.py _body_frame)가 정한다:
    # 숨쉬기 2, 걷기 4, 내려찍기 3(들기·머리 위·타격), 돌진 2, 도약 3(웅크림·공중·착지), 피격 1, 사망 2
    'crasher': {
        'prefix': 'v6_crasher',
        'sets': {
            'idle': (_f('idle', [1, 3]), 'loop'),
            'walk': (_f('walk', [0, 2, 4, 6]), 'loop'),
            'smash': (_f('smash', [2, 4, 5]), 'none'),
            'charge': (_f('charge', [2, 4]), 'none'),
            'leap': (_f('leap', [0, 4, 5]), 'none'),
            'hurt': (_f('hurt', [0]), 'none'),
            'death': (_f('death', [2, 4]), 'none'),
        },
        'skin': {'boss_crasher': 'idle', 'boss_crasher_idle': 'idle', 'boss_crasher_walk': 'walk',
                 'boss_crasher_smash': 'smash', 'boss_crasher_charge': 'charge', 'boss_crasher_leap': 'leap',
                 'boss_crasher_hurt': 'hurt', 'boss_crasher_death': 'death'},
    },
    # 문지기 (2026-11-25, shots/pixellab_test/gatekeeper_v6_<동작>.png). 구역 1 중간 보스. 게임이 쓰는 세트 이름 그대로 굽는다
    # (접두 boss_gatekeeper, skin 없음). 장수는 src/gatekeeper.py·enemy.py가 쓰는 대로: 공격 그림은 1 예고·2 타격·3 회수.
    'gatekeeper': {
        'prefix': 'boss_gatekeeper',
        'still': 'idle',                                           # 정지 그림 boss_gatekeeper_idle.png = idle 1번
        'sets': {
            'idle': (_f('idle', [0, 2]), 'none'),                  # 숨쉬기 2장
            'walk': (_f('walk', range(0, 8)), 'loop'),
            'heavy': (_f('heavy', [1, 4, 5]), 'none'),             # 철퇴를 머리 위로 -> 앞으로 내려찍음 -> 회수 (try1은 방패가 사라져 다시 뽑음)
            'bash': (_f('bash', [1, 4, 5]), 'none'),               # 방패 뒤로 웅크림 -> 낮게 내지름 -> 멈춰 섬
            'call': (_f('call', [0, 2]), 'none'),                  # 철퇴를 치켜들고 외친다 (증원 호출)
            'hurt': ([('hurt', 2), ('death', 1)], 'none'),         # 움찔 / 벽에 부딪혀 비틀(무릎이 꺾인다)
            'death': (_f('death', [1, 3, 5]), 'none'),             # 무릎 -> 쓰러짐 -> 누움
        },
        'skin': {},
    },
}


def load(char, rel, n=None):
    base = os.path.join(PIX, f'{char}_v6', 'raw')
    p = os.path.join(base, rel) if n is None else os.path.join(base, rel, f'frame_{n}.png')
    a = np.array(Image.open(p).convert('RGBA'))
    a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
    a[a[:, :, 3] == 0] = 0
    return a


def body_x(a):
    """몸 가로 중심: 아래쪽 절반(다리·몸통) 불투명 픽셀의 평균 x. 무기·머리 장식에 덜 흔들린다."""
    ys, xs = np.nonzero(a[:, :, 3])
    if not len(xs):
        return None
    mid = (ys.min() + ys.max()) / 2
    low = ys >= mid
    return float(xs[low].mean())


def apply(char):
    cfg = CHARS[char]
    if not cfg['sets']:
        print(f'{char}: 세트가 아직 없다 (원본을 보고 CHARS에 번호를 적는다)')
        return
    base = load(char, 'base.png')
    pal = palette_of(base)
    base_x = body_x(base)
    foot = foot_row([base])
    frames_meta, skin = {}, {}
    for tail, (frames_src, align) in cfg['sets'].items():
        name = f"{cfg['prefix']}_{tail}"
        frames = [lock_palette(remove_white_arcs(load(char, src, n)), pal) for src, n in frames_src]
        anchor_x = base_x
        if align == 'loop':
            bx = [body_x(f) for f in frames]
            anchor_x = float(np.mean([b for b in bx if b is not None]))
            frames = [shift_x(f, int(round(anchor_x - b))) if b is not None else f for f, b in zip(frames, bx)]
        for i, f in enumerate(frames, 1):
            im = Image.fromarray(f, 'RGBA')
            im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(os.path.join(DST, f'{name}_{i}.png'))
        anchor_y = foot * SCALE
        if cfg.get('float_hb') and tail not in cfg.get('foot_sets', ()):
            # 떠 있는 적: 몸통 중심(기준 그림 불투명 줄의 평균)을 히트박스 가운데(발 위 float_hb px)에 맞춘다
            anchor_y = int(round(np.nonzero(base[:, :, 3])[0].mean() * SCALE)) + cfg['float_hb']
        frames_meta[name] = [len(frames), int(round(anchor_x * SCALE)) + 1, anchor_y]
        print(f'{name}: {len(frames)}장, 기준점 {frames_meta[name][1:]}')
        if cfg.get('still') == tail:                               # 정지 그림(<세트 이름>.png)도 같은 그림으로
            im = Image.fromarray(frames[0], 'RGBA')
            im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(os.path.join(DST, f'{name}.png'))
    for old, tail in cfg['skin'].items():
        skin[old] = f"{cfg['prefix']}_{tail}"
    path = os.path.join(DST, f'skin_{char}.json')
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump({'frames': frames_meta, 'skin': skin}, fp, ensure_ascii=False, indent=1)
    print('저장', os.path.relpath(path, ROOT))


def main(names):
    for char in names or [c for c in CHARS if os.path.exists(os.path.join(PIX, f'{c}_v6', 'raw', 'base.png'))]:
        apply(char)


if __name__ == '__main__':
    main(sys.argv[1:])
