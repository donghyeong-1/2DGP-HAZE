"""빛줄기 (O3, 2026-11-26, docs/opus/TASKS.md). 자리 정하기는 pico2d 없이 돌아가고 그리기만 화면을 쓴다.

방에 빛을 더해 빛이 더 눈에 띄게 한다 (참고: Coggly Town의 픽셀 조명 단계 중 우리에게 없던 '빛줄기'만).
- 등 장식(DECOR_LAMP) 아래로 바닥까지 내려오는 옅은 빛 원뿔(cone) 하나씩.
- 방마다 천장 바로 아래에서 내려오는 빛줄기 0~2개(곧은 것 straight, 기운 것 slant). 보스방은 0~1개.
  문·스폰 근처(room.near_marker)와 그 아래 CLEAR_ROWS칸이 문·스폰 근처인 자리는 피한다.
- 자리는 방 이름으로 정한 난수(zlib.crc32): 같은 방이면 늘 같은 자리. 등은 원래 방 이름으로 정해진 자리다.
- 색은 구역 테마의 빛 색(슬럼 차가운 청백, 용광로 주황, 탑 청록, 은신처 따뜻한 색).
- 그리기: 더하기 섞기로 두 번. 배경 바로 위(atmosphere.draw_back, BACK_ALPHA)와 캐릭터 위(atmosphere.draw, FRONT_ALPHA:
  빛 속에 들어간 느낌, 아주 옅게). 세기는 BREATH_PERIOD초로 천천히 숨 쉰다. 빛줄기 안에 떠다니는 먼지 알갱이 몇 개(뒤 겹에만).
- 그림: assets/light/shaft_*.png (tools/make_light.py, code-drawn, 빛 층이라 반투명 예외). 2배로 그린다(정수 배).
"""
import math
import random
import zlib

import config

BACK_ALPHA = 0.24          # 배경 바로 위 (캐릭터 아래). 0.18은 원경 그림 위에서 거의 보이지 않았다
FRONT_ALPHA = 0.05         # 캐릭터 위 (빛 속에 들어간 느낌)
BREATH_PERIOD = 5.0        # 세기가 숨 쉬는 주기(초)
SCALE = 2                  # 그림 배율 (정수)
CLEAR_ROWS = 4             # 천장 빛줄기가 내려가는 칸 수만큼 문·스폰 근처가 아니어야 한다
MIN_GAP = 6                # 천장 빛줄기끼리 떨어진 칸 수
MOTES = 3                  # 빛줄기 하나의 먼지 알갱이 수
# 종류 -> 그림과 위쪽 기준점(그림 왼쪽에서 잰 가로 위치, 논리 px)
KINDS = {
    'cone': {'image': 'light/shaft_cone.png', 'anchor': 48},
    'straight': {'image': 'light/shaft_straight.png', 'anchor': 32},
    'slant': {'image': 'light/shaft_slant.png', 'anchor': 20},
}
COLORS = {                 # 방 테마 -> 빛 색
    'cell': (176, 206, 255),       # 슬럼: 차가운 청백
    'foundry': (255, 156, 84),     # 용광로: 주황
    'haze': (96, 232, 214),        # 탑: 청록
    'hideout': (255, 206, 140),    # 은신처: 따뜻한 색
    'gold': (255, 220, 140),
    'shop': (255, 214, 150),
    'boss': (214, 210, 236),
}


def is_boss_room(room):
    name = getattr(room, 'name', '') or ''
    return getattr(room, 'theme', '') == 'boss' or name.endswith('_arena') and name != 'arena_05'


def color_for(room):
    return COLORS.get(getattr(room, 'theme', 'cell'), COLORS['cell'])


def breath(t, phase):
    """세기 배율 0.7~1.0 (천천히 숨 쉬듯)."""
    return 0.85 + 0.15 * math.sin(math.tau * t / BREATH_PERIOD + phase)


def plan(room):
    """[(종류, x, y, 뒤집기, 위상)] 세계 좌표. x = 빛의 위쪽 기준점, y = 빛이 시작하는 높이(위쪽 끝). 방마다 한 번 계산해 둔다."""
    cached = room.__dict__.get('_shafts')
    if cached is not None:
        return cached
    import room as room_mod
    T = config.TILE
    rng = random.Random(zlib.crc32((room.name or '').encode('utf-8')))
    out = []
    lamp_cols = set()
    for kind, col, row in room.decor:
        if kind == room_mod.DECOR_LAMP:
            lamp_cols.add(col)
            out.append(('cone', col * T + T // 2, room.tile_top(row) - T // 2, False, rng.uniform(0, math.tau)))
    spots = []
    for row in range(1, room.nrows - CLEAR_ROWS):
        for col in range(2, room.cols - 2):
            if room.rows[row][col] != room_mod.EMPTY or room.rows[row - 1][col] != room_mod.SOLID:
                continue
            if any((col, row + k) in room.near_marker or room.rows[row + k][col] != room_mod.EMPTY for k in range(CLEAR_ROWS)):
                continue
            if any(abs(col - c) < 3 for c in lamp_cols):
                continue
            spots.append((col, row))
    want = rng.randint(0, 1 if is_boss_room(room) else 2)
    rng.shuffle(spots)
    chosen = []
    for col, row in spots:
        if len(chosen) >= want:
            break
        if all(abs(col - c) >= MIN_GAP for c, _ in chosen):
            chosen.append((col, row))
    for col, row in sorted(chosen):
        kind = 'slant' if rng.random() < 0.7 else 'straight'
        out.append((kind, col * T + T // 2, room.tile_top(row), rng.random() < 0.5, rng.uniform(0, math.tau)))
    room.__dict__['_shafts'] = out
    return out


def draw(room, t, alpha, motes=False):
    """화면 좌표로 그린다 (draw_offset이 (0, 0)인 상태에서 부른다). 화면 밖은 건너뛴다."""
    import assets
    import camera
    if room is None or not hasattr(room, 'decor'):
        return
    ox, oy = camera.offset()
    color = color_for(room)
    for kind, x, y, flip, phase in plan(room):
        info = KINDS[kind]
        img = assets.image(info['image'])
        w, h = img.w * SCALE, img.h * SCALE
        ax = info['anchor'] * SCALE
        left = int(x + ox - ((img.w * SCALE - ax) if flip else ax)) // 2 * 2
        top = int(y + oy) // 2 * 2
        if left > config.SCREEN_W or left + w < 0 or top < 0 or top - h > config.SCREEN_H:
            continue
        k = alpha * breath(t, phase)
        assets.draw_clip_added(img, 0, 0, img.w, img.h, left, top - h, 'h' if flip else '', SCALE, k, color)
        if motes:
            _motes(left, top, w, h, kind, flip, t, phase, color)


def _motes(left, top, w, h, kind, flip, t, phase, color):
    """빛줄기 안에 떠다니는 먼지 알갱이 (2px, 느리게 내려오며 옆으로 흔들린다)."""
    import effects
    for i in range(MOTES):
        u = (t * 0.035 + i / MOTES + phase / math.tau) % 1.0
        down = 0.15 + 0.7 * u
        if kind == 'slant':
            cx = 0.2 + 0.55 * down
            cx = 1.0 - cx if flip else cx
        else:
            cx = 0.5
        x = left + w * cx + 10 * math.sin(t * 0.7 + i * 2.1 + phase)
        y = top - h * down
        fade = math.sin(math.pi * u)                              # 위아래 끝에서는 흐려진다
        effects.draw_dot(int(x), int(y), color, 0, alpha=0.55 * fade, glow=False)
