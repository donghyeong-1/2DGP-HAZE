"""움직이는 배경 소품 (2026-11-21 퀄리티 계획 2-1, Codex T28 그림). 방 모양을 보고 자리를 골라 자동으로 놓는다.

그림: assets/props/<테마>_<소품>_1~4.png (4장 반복, 장마다 FRAME_TIME초). 충돌 없이 그림만 놓는다.
놓는 규칙(KIND):
- ceiling: 바로 위가 벽인 빈 칸 (천장에 매단다). 기준점 = 매다는 점.
- floor:   바로 아래가 벽인 빈 칸 (바닥에 놓는다). 기준점 = 바닥에 닿는 점.
- wall:    왼쪽이 벽인 빈 칸 (벽에서 오른쪽으로 뿜는다). 기준점 = 벽에 붙는 점.
- back:    뒷벽에 거는 것 (톱니·환풍기). 기준점 = 가운데.
그림 사각형이 덮는 칸은 모두 빈 칸이어야 하고, 문·스폰 근처(room.near_marker), 다른 장식, 먼저 놓은 소품과 겹치지 않는다.
같은 방 이름이면 늘 같은 자리다(방 이름으로 정한 난수).
"""
import random
from collections import namedtuple

import config

FRAME_TIME = 0.12
FRAMES = 4
# 테마 -> 소품 3종. 황금방·정비방·보스방(gold, shop, boss)은 자기 소품만 쓴다.
PROPS = {
    'cell': ('drip', 'rag', 'bulb'),
    'foundry': ('steam', 'gear', 'piston'),
    'haze': ('crystal', 'searchlight', 'chain'),
    'hideout': ('brazier', 'anvil', 'fan'),
}
# 소품 -> 그림 왼쪽 위 기준 기준점 (Codex T28 보고서의 설치점). drip은 웅덩이를 바닥에 맞춘다(관은 뒷벽 배관으로 보인다).
ANCHOR = {
    'drip': (56, 156), 'rag': (64, 7), 'bulb': (26, 7),
    'steam': (7, 40), 'gear': (57, 57), 'piston': (41, 8),
    'crystal': (39, 140), 'searchlight': (65, 7), 'chain': (35, 7),
    'brazier': (49, 112), 'anvil': (55, 110), 'fan': (54, 55),
}
KIND = {
    'drip': 'floor', 'rag': 'ceiling', 'bulb': 'ceiling',
    'steam': 'wall', 'gear': 'back', 'piston': 'ceiling',
    'crystal': 'floor', 'searchlight': 'ceiling', 'chain': 'ceiling',
    'brazier': 'floor', 'anvil': 'floor', 'fan': 'back',
}
SIZE = {
    'drip': (112, 158), 'rag': (129, 121), 'bulb': (52, 103),
    'steam': (146, 80), 'gear': (114, 114), 'piston': (82, 143),
    'crystal': (78, 147), 'searchlight': (130, 139), 'chain': (71, 142),
    'brazier': (99, 120), 'anvil': (132, 117), 'fan': (108, 110),
}
# 방 이름 -> 손으로 정한 자리 [(소품, 열)]. 자동 배치 대신 쓴다. 은신처는 원경 그림이 이미 붐벼서(환풍기도 그려져 있다)
# 정비사(9열) 옆 모루와 NPC 사이 화로만 놓는다.
FIXED = {'hideout_room': [('anvil', 7), ('brazier', 21), ('brazier', 29)]}
TARGET = 4            # 방마다 놓으려는 수 (자리가 모자라면 그보다 적다)
MARGIN = 8            # 그림 가장자리 이만큼은 벽에 걸쳐도 된다 (매다는 고리·받침)
GAP = 1               # 소품 사이에 비워 둘 칸

Placed = namedtuple('Placed', 'name left bottom w h phase')


def frame_at(t):
    return int(t / FRAME_TIME + 1e-9) % FRAMES + 1


def _cells(room, left, bottom, w, h, pad=0):
    t = config.TILE
    c0, c1 = int((left + MARGIN) // t) - pad, int((left + w - MARGIN) // t) + pad
    r0, r1 = room.row_of(bottom + h - MARGIN) - pad, room.row_of(bottom + MARGIN) + pad
    return {(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)}


def _spots(room, prop):
    """이 소품을 기준점에 맞춰 놓을 수 있는 (left, bottom) 후보들."""
    t = config.TILE
    kind = KIND[prop]
    ax, ay = ANCHOR[prop]
    w, h = SIZE[prop]
    out = []
    for row in range(1, room.nrows - 1):
        for col in range(1, room.cols - 1):
            if room.rows[row][col] != '.':
                continue
            if kind == 'ceiling' and room.rows[row - 1][col] == '#':
                x, y = col * t + t // 2, room.height - row * t
            elif kind == 'floor' and room.rows[row + 1][col] == '#':
                x, y = col * t + t // 2, room.height - (row + 1) * t
            elif kind == 'wall' and room.rows[row][col - 1] == '#':
                x, y = col * t, room.height - row * t - t // 2
            elif kind == 'back':
                x, y = col * t + t // 2, room.height - row * t - t // 2
            else:
                continue
            out.append((x - ax, y - (h - ay)))
    return out


def place(room, theme):
    """방에 놓을 소품 목록 [Placed]. room에는 rows·cols·nrows·height·near_marker·decor가 있어야 한다."""
    names = PROPS.get(theme)
    if not names:
        return []
    rng = random.Random(f'{room.name}:{room.cols}x{room.nrows}:{theme}:props')
    if room.name in FIXED:
        out = []
        for prop, col in FIXED[room.name]:
            t = config.TILE
            ax = ANCHOR[prop][0]
            spots = [s for s in _spots(room, prop) if s[0] + ax == col * t + t // 2]
            if spots:
                left, bottom = min(spots, key=lambda s: s[1])          # 그 열의 맨 아래 바닥
                out.append(Placed(f'{theme}_{prop}', left, bottom, *SIZE[prop], rng.random() * FRAME_TIME * FRAMES))
        return out
    blocked = set(room.near_marker) | {(col, row) for _k, col, row in room.decor}
    placed = []
    order = list(names)
    rng.shuffle(order)
    tries = 0
    while len(placed) < TARGET and tries < 3:
        tries += 1
        for prop in order:
            if len(placed) >= TARGET:
                break
            w, h = SIZE[prop]
            spots = _spots(room, prop)
            rng.shuffle(spots)
            for left, bottom in spots:
                cells = _cells(room, left, bottom, w, h)
                if cells & blocked or not all(room.tile_at(c, r) == '.' for c, r in cells):
                    continue
                placed.append(Placed(f'{theme}_{prop}', left, bottom, w, h, rng.random() * FRAME_TIME * FRAMES))
                blocked |= _cells(room, left, bottom, w, h, pad=GAP)
                break
    return placed
