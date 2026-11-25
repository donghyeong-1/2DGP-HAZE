"""화면 밖 적 표시 (v8 남겨 둔 것, 2026-11-25). 큰 방에서 남은 적을 찾아 헤매지 않게 한다.

잠긴 방이 큰 방(stage.is_big)이거나 남은 적이 FEW 이하이면, 화면 밖에 있는 적마다 그쪽 화면 가장자리에
작은 화살표를 띄운다. 화살표는 주인공에서 적으로 가는 방향이 화면 가장자리(MARGIN 안쪽)와 만나는 자리에 놓는다.
그림은 네 방향을 미리 그린 것(assets/ui/hud_offscreen_<l·r·u·d>.png, tools/make_offscreen_marker.py)이고 회전하지 않는다.
markers·active는 pico2d와 무관한 순수 로직이라 창 없이 테스트한다(tests/test_offscreen.py).
"""
import math

import config

MARGIN = 44          # 화면 가장자리에서 화살표 가운데까지
MARGIN_TOP = 150     # 위쪽은 HUD(체력·게이지 띠) 아래로
MAX = 6              # 한 번에 띄우는 화살표 수 (가까운 적부터)
FEW = 3              # 큰 방이 아니어도 남은 적이 이만큼 이하이면 띄운다
SIDES = ('l', 'r', 'u', 'd')
MERGE = 30           # 이보다 가까운 화살표는 하나로 합친다(무리 지은 적)
PULSE = 0.8          # 화살표가 깜빡이는 주기(초): 켜짐 0.6 / 흐림 0.2


def active(stage):
    """지금 화살표를 띄울 때인가: 잠긴 방이고, 큰 방이거나 남은 적이 적다."""
    if stage is None or getattr(stage, 'room', None) is None or not stage.room.locked:
        return False
    return stage.is_big(stage.coord) or stage.enemy_count() <= FEW


def markers(enemies, cam, origin):
    """[(화면 x, 화면 y, 가장자리 'l'·'r'·'u'·'d', 거리)] 가까운 순, MAX개까지.
    cam: 카메라 (x, y) = 화면 왼쪽 아래의 세계 좌표, origin: 주인공의 화면 좌표."""
    w, h = config.SCREEN_W, config.SCREEN_H
    lo_x, hi_x, lo_y, hi_y = MARGIN, w - MARGIN, MARGIN, h - MARGIN_TOP
    ox = min(hi_x, max(lo_x, origin[0]))
    oy = min(hi_y, max(lo_y, origin[1]))
    out = []
    for e in enemies:
        if not getattr(e, 'alive', False):
            continue
        ex, ey = getattr(e, 'center', (e.x, e.y))
        sx, sy = ex - cam[0], ey - cam[1]
        fx, fy = e.x - cam[0], e.y - cam[1]                      # 발 (몸 아래쪽)
        if 0 <= sx <= w and (0 <= sy <= h or 0 <= fy <= h - 40):
            continue                                             # 화면 안: 몸이 보인다
        dx, dy = sx - ox, sy - oy
        tx = (hi_x - ox) / dx if dx > 0 else (lo_x - ox) / dx if dx < 0 else math.inf
        ty = (hi_y - oy) / dy if dy > 0 else (lo_y - oy) / dy if dy < 0 else math.inf
        t = min(tx, ty, 1.0)
        if tx <= ty:
            side = 'r' if dx > 0 else 'l'
        else:
            side = 'u' if dy > 0 else 'd'
        x = int(round(min(hi_x, max(lo_x, ox + dx * t))))
        y = int(round(min(hi_y, max(lo_y, oy + dy * t))))
        out.append((x, y, side, math.hypot(dx, dy)))
    out.sort(key=lambda m: m[3])
    kept = []
    for m in out:                                                # 겹치는 화살표는 하나만 (가까운 적의 것)
        if all(abs(m[0] - k[0]) > MERGE or abs(m[1] - k[1]) > MERGE for k in kept):
            kept.append(m)
    return kept[:MAX]


class OffscreenMarkers:
    """HUD 층(LAYER_UI)에 두는 객체. play_mode가 넣고, 구역이 바뀌면 stage를 바꿔 끼운다(hasattr(obj, 'stage'))."""

    def __init__(self, player, stage):
        self.player, self.stage = player, stage
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    def draw(self):
        if not active(self.stage):
            return
        import assets
        import camera
        import game_world
        cam = camera.to_world(0, 0)
        origin = camera.to_screen(*self.player.center)
        dim = (self.time % PULSE) > PULSE * 0.75                # 짧게 흐려졌다 돌아온다 (반투명 대신 그림 둘)
        for x, y, side, _d in markers(game_world.world[game_world.LAYER_ENEMY], cam, origin):
            img = assets.image(f'ui/hud_offscreen_{side}{"_dim" if dim else ""}.png')
            assets.draw_image(img, x, y - img.h // 2)
