"""저스트 대시 테스트 (창 없이). 실행: python tests/test_just_dash.py

2026-11-22 v5 계획 2-3 (docs/plan_v5.md): 맞기 직전에 대시하면(대시를 시작하고 JUST_WINDOW 안에 공격이 몸에 닿으면)
'저스트 대시': 짧은 슬로 모션, 게이지 +JUST_GAIN, 대시 한 칸을 돌려받는다. 대시 한 번에 한 번만.
피격 직후 무적·궁극기 무적 중에는 생기지 않는다(대시로 피했을 때만).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import projectile  # noqa: E402
import test_combat as tc  # noqa: E402


def dashing(p):
    p.dash_slots = 2
    p.mouse_x, p.mouse_y = p.x - 400, p.center[1]
    p.request_dash()
    tc.step(1)
    assert p.state == 'DASH'


def test_hit_right_after_dash_is_just_dash():
    room, p = tc.make_world()
    effects.reset()
    hp, g0 = p.hp, p.gauge.value
    dashing(p)
    slots = p.dash_slots
    p.take_hit(20, source='debug')
    assert p.hp == hp                                              # 맞지 않는다
    assert p.gauge.value >= g0 + config.JUST_GAIN - 0.01
    assert p.just_dashes == 1
    assert effects.slow_left > 0                                   # 슬로 모션
    assert p.dash_slots == slots + 1                               # 대시 한 칸을 돌려받는다


def test_only_once_per_dash():
    room, p = tc.make_world()
    dashing(p)
    p.take_hit(20, source='debug')
    p.take_hit(20, source='debug')
    assert p.just_dashes == 1


def test_late_in_dash_is_not_just():
    room, p = tc.make_world()
    dashing(p)
    p.dash_age = config.JUST_WINDOW + 0.01
    p.take_hit(20, source='debug')
    assert p.just_dashes == 0


def test_hit_invuln_without_dash_is_not_just():
    room, p = tc.make_world()
    p.invuln_left = 0.5
    p.take_hit(20, source='debug')
    assert p.just_dashes == 0


def test_projectile_through_dash_counts():
    room, p = tc.make_world()
    dashing(p)
    hp = p.hp
    s = projectile.Scrap(p.x, p.center[1], -1, 10.0, 12, room, p)
    game_world.add_object(s, game_world.LAYER_EFFECT)
    s.update(1 / 60)
    assert p.hp == hp and p.just_dashes == 1


def test_enemy_swing_during_dash():
    room, p = tc.make_world()
    e = tc.add_enemy('slum', p.x + 60, room, p)
    hp = p.hp
    dashing(p)
    e._melee()
    assert p.hp == hp and p.just_dashes == 1


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
