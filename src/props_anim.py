"""움직이는 배경 소품 (2026-11-21 퀄리티 계획 2-1, Codex T28 그림). 방 모양을 보고 자리를 골라 자동으로 놓는다.

그림: assets/props/<테마>_<소품>_1~4.png (4장 반복, 장마다 FRAME_TIME초). 충돌 없이 그림만 놓는다.
놓는 규칙(KIND):
- ceiling: 바로 위가 벽인 빈 칸 (천장에 매단다). 기준점 = 매다는 점.
- floor:   바로 아래가 벽인 빈 칸 (바닥에 놓는다). 기준점 = 바닥에 닿는 점.
- wall:    왼쪽이 벽인 빈 칸 (벽에서 오른쪽으로 뿜는다). 기준점 = 벽에 붙는 점.
- back:    벽에 거는 것 (톱니·환풍기·창·표지판). 천장 바로 아래에 붙이거나 왼쪽·오른쪽 벽에 붙인다.
받침 규칙(2026-11-21 재검토): 바닥 것은 그림 밑 전체가 벽 위에, 천장 것은 그림 위 전체가 벽 아래에,
벽 것은 위가 천장에 붙거나 옆이 그림 높이만큼 벽에 붙어야 한다(허공에 뜬 소품이 없게, _supported).
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
    'cell': ('rag', 'bulb'),       # drip은 관(천장)과 웅덩이(바닥)가 한 그림이라 방 높이에 맞출 수 없어 자동 배치에서 뺐다
    'foundry': ('steam', 'gear', 'piston'),
    'haze': ('crystal', 'searchlight', 'chain'),
    'hideout': ('brazier', 'anvil', 'fan'),
}
# 소품 -> 그림 왼쪽 위 기준 기준점 (Codex T28 보고서의 설치점). drip은 웅덩이를 바닥에 맞춘다(관은 뒷벽 배관으로 보인다).
ANCHOR = {
    'drip': (56, 156), 'rag': (64, 7), 'bulb': (26, 7),
    'steam': (7, 40), 'gear': (57, 57), 'piston': (41, 8),
    'crystal': (39, 140), 'searchlight': (65, 7), 'chain': (35, 7),
    'brazier': (49, 126), 'anvil': (55, 110), 'fan': (54, 55),     # 화로: Q1(11/27) PixelLab 그림이 불꽃까지 높아 캔버스를 10px 키움 (발 닿는 자리 그대로)
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
    'brazier': (99, 130), 'anvil': (132, 117), 'fan': (108, 110),
}
# 방 이름 -> 손으로 정한 자리 [(소품, 열)]. 자동 배치 대신 쓴다. 은신처는 원경 그림이 이미 붐벼서(환풍기도 그려져 있다)
# 정비사(9열) 옆 모루와 NPC 사이 화로만 놓는다.
FIXED = {'hideout_room': [('anvil', 7), ('brazier', 21), ('brazier', 29)]}
# 멈춘 장식 (Codex T31, 2026-11-21 계획 2-4): 테마마다 바닥 3종 + 벽·천장 3종. 기준점은 바닥 것은 밑줄 가운데(그림 밑이 바닥에 닿게),
# 벽 것은 윗변 가운데(back: 빈 칸 가운데에 건다), 천장 것은 매다는 점.
DECOR = {
    'cell': ('broken_crates', 'rusty_drum', 'rag_heap', 'barred_window', 'wanted_poster', 'sagging_wires'),
    'foundry': ('scrap_cart', 'stacked_moulds', 'tool_chest', 'warning_sign', 'wall_gauge', 'hanging_hook'),
    'haze': ('broken_crystals', 'watcher_wreck', 'sealed_chest', 'teal_panel', 'broken_monitor', 'watch_camera'),
}
SIZE.update({
    'broken_crates': (128, 75), 'rusty_drum': (66, 85), 'rag_heap': (129, 50), 'barred_window': (123, 111),
    'wanted_poster': (64, 86), 'sagging_wires': (128, 89), 'scrap_cart': (132, 85), 'stacked_moulds': (116, 77),
    'tool_chest': (86, 59), 'warning_sign': (84, 64), 'wall_gauge': (107, 73), 'hanging_hook': (52, 100),
    'broken_crystals': (100, 57), 'watcher_wreck': (133, 64), 'sealed_chest': (123, 65), 'teal_panel': (80, 107),
    'broken_monitor': (70, 75), 'watch_camera': (75, 64),
})
for _name in ('broken_crates', 'rusty_drum', 'rag_heap', 'scrap_cart', 'stacked_moulds', 'tool_chest',
              'broken_crystals', 'watcher_wreck', 'sealed_chest'):
    KIND[_name] = 'floor'
    ANCHOR[_name] = (SIZE[_name][0] // 2, SIZE[_name][1])
for _name in ('barred_window', 'wanted_poster', 'warning_sign', 'wall_gauge', 'teal_panel', 'broken_monitor'):
    KIND[_name] = 'back'
    ANCHOR[_name] = (SIZE[_name][0] // 2, 3)
for _name in ('sagging_wires', 'hanging_hook', 'watch_camera'):
    KIND[_name] = 'ceiling'
    ANCHOR[_name] = (SIZE[_name][0] // 2, 3)
DECOR_TARGET = 3
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


def _solid(room, col, row):
    return room.tile_at(col, row) == '#'


def _span_cols(left, w):
    t = config.TILE
    return range(int((left + MARGIN) // t), int((left + w - MARGIN) // t) + 1)


def _span_rows(room, bottom, h):
    return range(room.row_of(bottom + h - MARGIN), room.row_of(bottom + MARGIN) + 1)


def _supported(room, prop, left, bottom):
    """그림이 받침에 닿아 있는가 (받침 규칙)."""
    w, h = SIZE[prop]
    kind = KIND[prop]
    t = config.TILE
    if kind == 'floor':
        below = room.row_of(bottom - 1)
        return all(_solid(room, c, below) for c in _span_cols(left, w))
    above = room.row_of(bottom + h + 1)
    under_ceiling = all(_solid(room, c, above) for c in _span_cols(left, w))
    if kind == 'ceiling':
        return under_ceiling
    rows = _span_rows(room, bottom, h)
    on_left = all(_solid(room, int((left - 1) // t), r) for r in rows)
    on_right = all(_solid(room, int((left + w + 1) // t), r) for r in rows)
    if kind == 'wall':
        return on_left
    return under_ceiling or on_left or on_right


def _spots(room, prop):
    """이 소품을 놓을 수 있는 (left, bottom) 후보들 (받침 규칙을 지키는 것만)."""
    t = config.TILE
    kind = KIND[prop]
    ax, ay = ANCHOR[prop]
    w, h = SIZE[prop]
    out = []
    for row in range(1, room.nrows - 1):
        for col in range(1, room.cols - 1):
            if room.rows[row][col] != '.':
                continue
            ceil_y = room.height - row * t                  # 이 칸 윗변 (위 칸이 벽이면 천장 밑면)
            mid_y = ceil_y - t // 2
            cands = []
            if kind == 'ceiling' and _solid(room, col, row - 1):
                cands.append((col * t + t // 2 - ax, ceil_y - (h - ay)))
            elif kind == 'floor' and _solid(room, col, row + 1):
                cands.append((col * t + t // 2 - ax, ceil_y - t - (h - ay)))
            elif kind == 'wall' and _solid(room, col - 1, row):
                cands.append((col * t - ax, mid_y - (h - ay)))
            elif kind == 'back':
                if _solid(room, col, row - 1):                      # 천장 바로 아래에 붙인다
                    cands.append((col * t + t // 2 - w // 2, ceil_y - h + 3))
                if _solid(room, col - 1, row):                      # 왼쪽 벽에 붙인다
                    cands.append((col * t - 3, mid_y - h // 2))
                if _solid(room, col + 1, row):                      # 오른쪽 벽에 붙인다
                    cands.append(((col + 1) * t + 3 - w, mid_y - h // 2))
            out += [c for c in cands if _supported(room, prop, *c)]
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
    return _fill(room, theme, names, TARGET, blocked, rng)


def _fill(room, theme, names, target, blocked, rng):
    """names를 섞어 돌며 자리를 찾아 target개까지 놓는다. blocked(칸 집합)는 놓을 때마다 늘어난다."""
    placed = []
    order = list(names)
    rng.shuffle(order)
    tries = 0
    while len(placed) < target and tries < 3:
        tries += 1
        for prop in order:
            if len(placed) >= target:
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


def place_decor(room, theme, anim):
    """멈춘 장식 (Codex T31): 움직이는 소품(anim)과 기존 장식을 피해 DECOR_TARGET개. 그림 assets/decor/<테마>_<이름>.png."""
    names = DECOR.get(theme)
    if not names or room.name in FIXED:
        return []
    rng = random.Random(f'{room.name}:{room.cols}x{room.nrows}:{theme}:decor')
    blocked = set(room.near_marker) | {(col, row) for _k, col, row in room.decor}
    for p in anim:
        blocked |= _cells(room, p.left, p.bottom, p.w, p.h, pad=GAP)
    return _fill(room, theme, names, DECOR_TARGET, blocked, rng)
