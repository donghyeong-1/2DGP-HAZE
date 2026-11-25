"""카메라: 방이 화면보다 클 때 플레이어(와 조준 방향)를 부드럽게 따라간다. pico2d와 무관한 순수 로직.

카메라 위치(x, y)는 화면 왼쪽 아래가 가리키는 세계 좌표다. 그릴 때는 항상 정수로 반올림해서 쓴다
(docs/pixel_rules.md 3번: 카메라와 모든 위치는 정수 픽셀). 방이 화면보다 작으면 가운데에 놓는다.
"""
import math

import config

x = 0.0
y = 0.0
LEAN = 0.18          # 마우스 쪽으로 카메라가 기우는 정도 (조준 방향을 더 많이 보여 준다)
LEAN_MAX = 220       # 기우는 최대 거리(px)
FOLLOW_SPEED = 9.0   # 따라가는 속도 (클수록 빠르다)


def _bounds(room):
    max_x = room.width - config.SCREEN_W
    max_y = room.height - config.SCREEN_H
    return ((max_x / 2, max_x / 2) if max_x < 0 else (0.0, float(max_x)),
            (max_y / 2, max_y / 2) if max_y < 0 else (0.0, float(max_y)))


def target_for(player, room):
    """플레이어를 화면 가운데에 두되 마우스 쪽으로 조금 기울이고, 방 가장자리를 넘지 않게 자른다."""
    cx, cy = player.center
    lean_x = max(-LEAN_MAX, min(LEAN_MAX, (player.mouse_x - cx) * LEAN))
    lean_y = max(-LEAN_MAX, min(LEAN_MAX, (player.mouse_y - cy) * LEAN))
    (x0, x1), (y0, y1) = _bounds(room)
    return (max(x0, min(x1, cx + lean_x - config.SCREEN_W / 2)),
            max(y0, min(y1, cy + lean_y - config.SCREEN_H / 2)))


def look_at(room, wx, wy):
    """세계 좌표 (wx, wy)를 화면 가운데에 두는 카메라 위치. 방 가장자리를 넘지 않게 자른다 (보스 등장씬, boss_intro)."""
    (x0, x1), (y0, y1) = _bounds(room)
    return (max(x0, min(x1, wx - config.SCREEN_W / 2)), max(y0, min(y1, wy - config.SCREEN_H / 2)))


def snap(player, room):
    """방에 들어간 직후 카메라를 바로 맞춘다 (부드럽게 날아오지 않는다)."""
    global x, y
    x, y = target_for(player, room)


def update(player, room, dt):
    global x, y
    tx, ty = target_for(player, room)
    k = 1.0 - math.exp(-FOLLOW_SPEED * dt)
    x += (tx - x) * k
    y += (ty - y) * k


def offset():
    """그리기 오프셋 (정수). 세계 좌표 + offset = 화면 좌표."""
    return (-int(round(x)), -int(round(y)))


def to_world(screen_x, screen_y):
    return (screen_x + int(round(x)), screen_y + int(round(y)))


def to_screen(world_x, world_y):
    return (world_x - int(round(x)), world_y - int(round(y)))
