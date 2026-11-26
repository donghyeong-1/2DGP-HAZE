"""등불 깜빡임과 보스 막타 줌 테스트 (창 없이). 실행: python tests/test_lamps_zoom.py

O6 (2026-11-26, docs/opus/TASKS.md, plan_v7 3절에서 빠진 것):
- 등 장식(DECOR_LAMP)의 빛 세기를 등마다 다르게, 느리고 불규칙하게 흔든다(가끔 한 번 짧게 꺼질 듯). 번쩍임 줄이기면 흔들지 않는다.
- 보스를 쓰러뜨린 순간 화면(세계 층)이 그 보스 쪽으로 고르게 당겨졌다가 돌아온다. 일반 적은 하지 않는다. config로 끈다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))

import config  # noqa: E402
import options  # noqa: E402
import postfx  # noqa: E402
import room as room_mod  # noqa: E402


# ----- 등불 -----
def test_lamp_level_stays_in_range_and_is_the_same_for_the_same_lamp_and_time():
    seeds = [room_mod.lamp_seed('start_hall', c, r) for c, r in ((3, 2), (9, 2), (15, 4))]
    assert len(set(seeds)) == 3                                          # 등마다 다르다
    for s in seeds:
        values = [room_mod.lamp_level(s, t / 30) for t in range(30 * 20)]
        assert all(room_mod.LAMP_MIN <= v <= 1.0 for v in values)
        assert values == [room_mod.lamp_level(s, t / 30) for t in range(30 * 20)]   # 같은 시각이면 같은 값
        assert max(values) - min(values) > 0.15                          # 흔들린다
        assert min(values) < 0.5                                         # 20초 안에 한 번은 꺼질 듯 어두워진다
    a = [room_mod.lamp_level(seeds[0], t / 30) for t in range(90)]
    b = [room_mod.lamp_level(seeds[1], t / 30) for t in range(90)]
    assert a != b                                                        # 등마다 박자가 다르다


def test_lamp_does_not_flicker_with_reduce_flash():
    old = options.reduce_flash
    try:
        options.reduce_flash = True
        s = room_mod.lamp_seed('start_hall', 3, 2)
        assert {room_mod.lamp_level(s, t / 10) for t in range(100)} == {1.0}
    finally:
        options.reduce_flash = old


def test_room_uses_the_flicker_for_its_lamps():
    src = open(os.path.join(HERE, '..', 'src', 'room.py'), encoding='utf-8').read()
    assert 'lamp_level(' in src and 'lamp_seed(' in src


# ----- 보스 막타 줌 -----
def _fight(make):
    import balance_sim
    import effects
    import game_world
    from player import Player
    game_world.clear()
    effects.reset()
    postfx.reset_zoom()
    room = balance_sim.arena()
    floor = float(2 * config.TILE)
    p = Player(6 * config.TILE, floor, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    e = make(room, p, floor)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return p, e


def test_killing_a_boss_requests_one_zoom_but_a_normal_enemy_does_not():
    from boss import Boss
    from enemy import Enemy
    p, b = _fight(lambda room, p, floor: Boss(p.x + 600, floor, room, p))
    b.take_damage(10 ** 6)
    assert postfx.zoom_requests == 1
    b.take_damage(10 ** 6)
    assert postfx.zoom_requests == 1                                      # 한 번만
    p, e = _fight(lambda room, p, floor: Enemy('slum', p.x + 300, floor, room, p))
    e.take_damage(10 ** 6)
    assert postfx.zoom_requests == 0


def test_every_boss_kind_zooms_on_its_death():
    from ark import Ark
    from gatekeeper import Gatekeeper
    for make in (lambda room, p, floor: Ark(p.x + 600, floor, room, p),
                 lambda room, p, floor: Gatekeeper(p.x + 600, floor, room, p)):
        p, b = _fight(make)
        b.take_damage(10 ** 6)
        assert postfx.zoom_requests == 1, type(b).__name__


def test_zoom_pulls_in_then_returns_to_one():
    postfx.reset_zoom()
    postfx.zoom(960, 540, now=100.0)
    a, t_in, t_out = config.BOSS_KILL_ZOOM
    assert postfx.zoom_scale(now=100.0) == 1.0
    assert abs(postfx.zoom_scale(now=100.0 + t_in) - (1.0 + a)) < 1e-6      # 다 당겨진 순간 6%
    mid = postfx.zoom_scale(now=100.0 + t_in + t_out / 2)
    assert 1.0 < mid < 1.0 + a
    assert postfx.zoom_scale(now=100.0 + t_in + t_out + 0.01) == 1.0      # 끝나면 1로 돌아온다
    assert (a, t_in, t_out) == (0.06, 0.25, 0.35)


def test_zoom_switch_off():
    old = config.BOSS_KILL_ZOOM_ON
    try:
        config.BOSS_KILL_ZOOM_ON = False
        postfx.reset_zoom()
        postfx.zoom(960, 540, now=0.0)
        assert postfx.zoom_requests == 0 and postfx.zoom_scale(now=0.1) == 1.0
    finally:
        config.BOSS_KILL_ZOOM_ON = old


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
