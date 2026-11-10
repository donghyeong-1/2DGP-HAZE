"""플레이어 이동·점프·충돌 테스트 (창 없이 실행). 실행: python tests/test_player.py 또는 pytest

모든 위치는 config.TILE 기준이라 화면 배율을 바꿔도 그대로 통한다. 방은 data/rooms/test_01.txt:
바닥 윗면 = 16행 위, 얇은 판 3개(r13 x4~11, r9 x19~26, r5 x9~16), 기둥 x23~25(r14~15), 양쪽 벽.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import config  # noqa: E402
from player import Player  # noqa: E402
from room import Room  # noqa: E402

T = config.TILE
DT = 1 / 60
FLOOR_Y = float(config.SCREEN_H - 16 * T)     # 바닥 윗면
R13_TOP = float(config.SCREEN_H - 13 * T)     # 얇은 판(x 4~11칸) 윗면: 바닥에서 3칸 위
R9_TOP = float(config.SCREEN_H - 9 * T)       # 얇은 판(x 19~26칸) 윗면: 바닥에서 7칸 위
HB_W = config.PLAYER_HB_W


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
    assert p.state == 'RUN' and p.x > x0 + 1.5 * 100
    p.right = False
    step(p, 3)
    assert p.state == 'IDLE'


def test_wall_blocks_movement():
    p = make_player()
    p.left = True
    step(p, 200)
    assert p.x >= T + HB_W / 2 - 0.01  # 왼쪽 벽(타일 0)을 넘지 못한다


def test_pillar_blocks_movement():
    p = make_player()
    p.right = True
    step(p, 300)
    assert p.x <= 23 * T - HB_W / 2 + 0.01


def test_single_jump_height():
    p = make_player()
    p.request_jump()
    top = 0.0
    for _ in range(120):
        p.update(DT)
        top = max(top, p.y - FLOOR_Y)
    expected = config.JUMP_SPEED ** 2 / (2 * config.GRAVITY)
    assert expected * 0.93 < top < expected * 1.07, (top, expected)
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
    # 판(위 7칸 높이)에 2단 점프로 올라선다
    p = make_player(x=20 * T + T / 2, y=FLOOR_Y)
    p.request_jump()
    step(p, 18)
    p.request_jump()
    step(p, 90)
    assert p.on_ground and abs(p.y - R9_TOP) < 0.01, p.y


def test_oneway_platform_passes_from_below_lands_from_above():
    # 판(바닥에서 3칸 위)은 1단 점프(3.75칸)로 아래에서 뚫고 올라가 착지할 수 있어야 한다
    p = make_player(x=6 * T + T / 2, y=FLOOR_Y)
    p.request_jump()
    for _ in range(120):
        p.update(DT)
        if p.on_ground and p.y > FLOOR_Y + T:
            break
    assert p.on_ground and abs(p.y - R13_TOP) < 0.01, p.y


def test_drop_through_oneway_with_s_space():
    p = make_player(x=6 * T + T / 2, y=R13_TOP)
    step(p, 20)
    assert p.on_ground and abs(p.y - R13_TOP) < 0.01
    p.down = True
    p.request_jump()
    step(p, 60)
    assert abs(p.y - FLOOR_Y) < 0.01 and p.on_ground


def test_walking_off_ledge_leaves_one_air_jump():
    p = make_player(x=4 * T + 8, y=R13_TOP)  # 판의 왼쪽 끝 근처
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
    p.mouse_x, p.mouse_y = p.x + 450, p.y + config.PLAYER_HB_H / 2
    p.request_dash()
    assert p.state == 'DASH' and p.dash_slots == 1
    x0 = p.x
    step(p, 10)
    assert p.x > x0 + 0.8 * config.DASH_SPEED * config.DASH_TIME  # 약 360px 이동
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
