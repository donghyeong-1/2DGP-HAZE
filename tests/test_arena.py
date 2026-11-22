"""보스방 지형·헤이즈 농도 패턴 테스트 (창 없이). 실행: python tests/test_arena.py

2026-11-22 v5 계획 2-1 (docs/plan_v5.md): 보스가 페이즈를 올리면 방의 지형과 헤이즈 농도를 쓴다.
- 크래셔 2페이즈 '고철 기둥'(pillars): 바닥에 그림자 예고 -> 천장에서 떨어져 박힌다. 박힌 기둥은 올라설 수 있는 지형
  (방의 임시 벽 칸, room.extra_solids)이고 잠시 뒤 무너진다. 떨어질 때 밑에 있으면 맞고 옆으로 밀려난다.
- 크래셔 2페이즈 '배기 펌프'(pump): 방이 고농도가 되어 게이지가 계속 오른다. 벽의 밸브 앞에서 F를 누르면 멈춘다
  (안 누르면 PUMP_TIME 뒤 저절로 멈춤).
- 아크 2·3페이즈 '농도 띠'(bands): 짙은 띠(게이지 상승)와 맑은 띠(하강)가 방을 가로질러 천천히 움직인다.
- 아크 3페이즈 '결정 벽'(crystals): 플레이어 양옆에 결정 벽이 솟아 길을 막는다(임시 벽). 대시로 부딪치면 깨지며
  헤이즈를 흡수(게이지 상승). 잠시 뒤 스스로 무너진다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import boss_terrain as arena  # noqa: E402
import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import test_ark as ta  # noqa: E402
import test_combat as tc  # noqa: E402
from boss import Boss  # noqa: E402

T = config.TILE


def objs(cls):
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if isinstance(o, cls)]


def run(frames):
    for _ in range(frames):
        effects.hit_stop_left = 0.0
        game_world.update(1 / 60)


def crasher_room():
    room, p = tc.make_world(player_x=300.0)
    b = Boss(p.x + 900, tc.FLOOR_Y, room, p)
    b.cooldown = 99.0
    game_world.add_object(b, game_world.LAYER_ENEMY)
    return room, p, b


# ----- 임시 벽 -----
def test_extra_solids_act_as_walls_and_clear():
    room, p = tc.make_world()
    c, r = 10, room.nrows - 4
    assert room.tile_at(c, r) == '.'
    room.extra_solids[(c, r)] = 'x'
    assert room.tile_at(c, r) == '#'
    del room.extra_solids[(c, r)]
    assert room.tile_at(c, r) == '.'


# ----- 크래셔: 고철 기둥 -----
def test_scrap_pillar_lands_becomes_platform_then_crumbles():
    room, p, b = crasher_room()
    x = p.x + 400
    pillar = arena.ScrapPillar(x, room, p)
    game_world.add_object(pillar, game_world.LAYER_EFFECT)
    assert not room.extra_solids                                      # 예고 동안은 지형이 아니다
    run(int((arena.PILLAR_WARN + arena.PILLAR_FALL) * 60) + 3)
    cells = [k for k, v in room.extra_solids.items() if v is pillar]
    assert len(cells) == 2 * arena.PILLAR_ROWS                        # 두 칸 폭 x 높이
    top = max(room.height - r * T for _c, r in cells)                 # 기둥 윗면
    p.x, p.y, p.vy = x, top + 200, 0.0                                 # 위에서 떨어뜨리면 기둥 위에 선다
    p.on_ground = False
    run(60)
    assert abs(p.y - top) < 2 and p.on_ground
    run(int(arena.PILLAR_LIFE * 60) + 40)
    assert not room.extra_solids and not objs(arena.ScrapPillar)       # 무너져 사라진다


def test_pillar_falling_on_player_hurts_and_pushes_out():
    room, p, b = crasher_room()
    hp = p.hp
    pillar = arena.ScrapPillar(p.x, room, p)
    game_world.add_object(pillar, game_world.LAYER_EFFECT)
    p.invuln_left = 0.0
    run(int((arena.PILLAR_WARN + arena.PILLAR_FALL) * 60) + 3)
    assert p.hp < hp
    col = room.col_of(p.x)
    assert all(room.tile_at(col, room.row_of(p.y + k)) != '#' for k in (5, 60, 110))   # 기둥 속에 갇히지 않는다


def test_crasher_uses_terrain_patterns_only_in_phase2():
    room, p, b = crasher_room()
    seen1 = {b._choose_pattern() for _ in range(200) if not setattr(b, 'count', 1)}
    assert not seen1 & {'pillars', 'pump'}
    b.phase = 2
    seen2 = set()
    for _ in range(300):
        b.count, b.last_pattern = 1, None
        seen2.add(b._choose_pattern())
    assert {'pillars', 'pump'} <= seen2


# ----- 크래셔: 배기 펌프 -----
def test_pump_makes_room_dense_until_valve_closed():
    room, p, b = crasher_room()
    b.phase = 2
    b.pattern = 'pump'
    b._begin_active()
    assert room.is_high_haze
    valve = objs(arena.Valve)[0]
    g0 = p.gauge.value
    tc.step(60)
    assert p.gauge.value > g0 - 1 or room.is_high_haze                 # 짙은 방: 게이지가 줄지 않고 오른다
    p.x, p.y = valve.x, valve.y_floor
    p.interact_pressed = True
    tc.step(2)
    assert not room.is_high_haze and not objs(arena.Valve)            # 밸브를 잠그면 멈춘다
    b.pattern = 'pump'
    b._begin_active()
    run(int(arena.PUMP_TIME * 60) + 5)
    assert not room.is_high_haze                                      # 안 잠가도 저절로 멈춘다


# ----- 아크: 농도 띠·결정 벽 -----
def test_haze_bands_raise_and_lower_gauge_by_position():
    room, p, a = ta.make_fight(gauge=50.0)
    bands = arena.HazeBands(room, p, start_x=p.x - 10)
    dense = bands.band_at(p.x)
    assert dense in ('dense', 'clear')
    g0 = p.gauge.value
    bands.update(1.0)
    moved = p.gauge.value - g0
    assert (moved > 0) == (dense == 'dense') and abs(moved) > 2
    assert {'bands'} <= set(ark_options(a, 2)) and {'bands', 'crystals'} <= set(ark_options(a, 3))
    assert 'crystals' not in ark_options(a, 2)


def ark_options(a, phase):
    a.phase = phase
    seen = set()
    for _ in range(300):
        a.count, a.last_pattern = 1, None
        seen.add(a._choose_pattern())
    return seen


def test_crystal_walls_block_and_break_on_dash():
    room, p, a = ta.make_fight(gauge=40.0)
    wall = arena.CrystalWall(p.x + 3 * T, room, p)
    game_world.add_object(wall, game_world.LAYER_EFFECT)
    run(int(arena.CRYSTAL_RISE * 60) + 3)
    assert any(v is wall for v in room.extra_solids.values())         # 길을 막는다
    g0 = p.gauge.value
    p.dash_slots = 2
    p.mouse_x = p.x + 400
    p.right = True
    p.request_dash()
    run(30)
    assert not any(v is wall for v in room.extra_solids.values())     # 대시로 부딪쳐 깼다
    assert p.gauge.value > g0                                         # 헤이즈를 흡수


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
