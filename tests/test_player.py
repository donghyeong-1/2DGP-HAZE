"""플레이어 이동·점프·충돌 테스트 (창 없이 실행). 실행: python tests/test_player.py 또는 pytest"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import config  # noqa: E402
from player import Player  # noqa: E402
from room import Room  # noqa: E402

DT = 1 / 60
FLOOR_Y = 80.0


def make_player(x=None, y=None):
    room = Room.load('test_01')
    p = Player(x if x is not None else room.spawn[0], y if y is not None else room.spawn[1], room)
    step(p, 30)  # 착지시키기
    return p


def step(p, frames):
    for _ in range(frames):
        p.update(DT)


def test_spawn_lands_on_floor_and_idles():
    p = make_player()
    assert p.state == 'IDLE' and p.on_ground
    assert abs(p.y - FLOOR_Y) < 0.01


def test_run_right_then_stop():
    p = make_player()
    x0 = p.x
    p.right = True
    step(p, 30)
    assert p.state == 'RUN' and p.x > x0 + 100
    p.right = False
    step(p, 3)
    assert p.state == 'IDLE'


def test_wall_blocks_movement():
    p = make_player()
    p.left = True
    step(p, 200)
    assert p.x >= config.TILE + config.PLAYER_HB_W / 2 - 0.01  # 왼쪽 벽(타일 0)을 넘지 못한다


def test_pillar_blocks_movement():
    p = make_player()
    p.right = True
    step(p, 300)
    pillar_left = 23 * config.TILE
    assert p.x <= pillar_left - config.PLAYER_HB_W / 2 + 0.01


def test_single_jump_height():
    p = make_player()
    p.request_jump()
    top = 0.0
    for _ in range(120):
        p.update(DT)
        top = max(top, p.y - FLOOR_Y)
    assert 140 < top < 160, top
    assert p.state == 'IDLE' and p.jump_count == 0


def test_double_jump_allowed_third_blocked():
    p = make_player()
    p.request_jump()
    step(p, 15)
    p.request_jump()
    assert p.jump_count == 2 and p.state == 'JUMP'
    vy_after_second = p.vy
    step(p, 5)
    p.request_jump()  # 세 번째는 무시
    assert p.jump_count == 2 and p.vy < vy_after_second


def test_double_jump_reaches_higher_platform():
    # 플랫폼(r9, 위 y=360) 아래에서 2단 점프로 올라선다 (바닥 80 -> 360, 높이 280)
    p = make_player(x=20 * config.TILE + 20, y=FLOOR_Y)
    p.request_jump()
    step(p, 18)
    p.request_jump()
    step(p, 90)
    assert p.on_ground and abs(p.y - 360) < 0.01, p.y


def test_oneway_platform_passes_from_below_lands_from_above():
    # r13 판(x 160~480, 위 y=200). 단일 점프(150)로 판 아래에서 뚫고 올라가 착지할 수 있어야 한다
    p = make_player(x=6 * config.TILE + 20, y=FLOOR_Y)
    p.request_jump()
    for _ in range(120):
        p.update(DT)
        if p.on_ground and p.y > 150:
            break
    # 단일 점프는 높이 150이라 판 위(120 위)로 올라가 서야 한다
    assert p.on_ground and abs(p.y - 200) < 0.01, p.y


def test_drop_through_oneway_with_s_space():
    p = make_player(x=6 * config.TILE + 20, y=200.0)
    step(p, 20)
    assert p.on_ground and abs(p.y - 200) < 0.01
    p.down = True
    p.request_jump()
    step(p, 60)
    assert abs(p.y - FLOOR_Y) < 0.01 and p.on_ground


def test_walking_off_ledge_leaves_one_air_jump():
    p = make_player(x=4 * config.TILE + 5, y=200.0)  # 판의 왼쪽 끝 근처
    step(p, 5)
    p.left = True
    step(p, 20)
    assert p.state == 'FALL' and p.jump_count == 1
    p.request_jump()
    assert p.state == 'JUMP' and p.jump_count == 2
    p.request_jump()
    assert p.jump_count == 2


def test_dash_slots_consume_and_recharge():
    p = make_player()
    p.mouse_x, p.mouse_y = p.x + 300, p.y + 36
    p.request_dash()
    assert p.state == 'DASH' and p.dash_slots == 1
    x0 = p.x
    step(p, 10)
    assert p.x > x0 + 200 - 1  # 약 240px 이동 (0.15초)
    step(p, 60)
    p.request_dash()
    assert p.dash_slots == 0
    p.request_dash()  # 슬롯이 없으면 무시
    assert p.dash_slots == 0
    step(p, int(config.DASH_RECHARGE * 60) + 30)
    assert p.dash_slots >= 1


def test_dash_invulnerable():
    p = make_player()
    p.request_dash()
    p.take_hit(10)
    assert p.hp == config.PLAYER_HP and p.state == 'DASH'


def test_death_when_gauge_hits_zero():
    p = make_player()
    p.gauge.value = 1.0
    p.gauge.add(-1)
    step(p, 2)
    assert p.state == 'DEAD'


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
