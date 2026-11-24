"""식칼·건틀릿·사슬의 대시·점프 공격 테스트 (창 없이). 실행: python tests/test_weapon_moves.py

2026-11-19 사용자 결정: 무기마다 기본·대시·점프 공격이 따로 있다(철파이프는 이미 대시 평타·회전 베기·내려찍기).
대시 중·직후(dash_window) = 대시 공격, 공중 = 점프 공격, 그 밖 = 기본 공격 (철파이프와 같은 규칙).
- 식칼: 대시 = 한 자루 더, 거의 일자로 모아 관통 / 점프 = 한 자루 더, 넓은 부채꼴
- 건틀릿: 대시·점프 = 충전 없이 바로 작은 충격파 (게이지 조금)
- 사슬: 대시 = 사거리 x1.3, 한 마리 더 / 점프 = 피해 x1.3
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def world(weapon_id, gauge=35):
    room, p = tc.make_world()
    p.give_weapon(weapon_id)
    tc.set_gauge(p, gauge)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    return room, p


def airborne(p):
    p.on_ground = False
    p.state = 'JUMP'


def objects(name):
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == name]


# ----- 쌍권총 (2026-11-24 식칼 대체, 자세한 규칙은 tests/test_pistol.py) -----
def test_pistol_kinds_follow_dash_and_air():
    room, p = world('pistol')
    assert p.weapon.current_kind() == 'pistol'
    p.dash_window = 0.2
    assert p.weapon.current_kind() == 'pistol_dash'
    p.dash_window = 0.0
    airborne(p)
    assert p.weapon.current_kind() == 'pistol_air'


def test_pistol_dash_shot_is_a_tight_piercing_line():
    room, p = world('pistol')
    _, _, pierce = p.weapon.volley()
    assert not pierce                                                   # 노멀 기본은 관통하지 않는다
    p.dash_window = 0.2
    p.request_attack()
    bs = objects('Bullet')
    assert len(bs) == 3 and all(b.pierce for b in bs)
    assert max(b.dy for b in bs) - min(b.dy for b in bs) < 0.15         # 거의 일자


# ----- 건틀릿 -----
def test_gauntlet_dash_and_air_rush_at_once_for_a_little_gauge():
    for setup in ('dash', 'air'):
        room, p = world('gauntlet', gauge=50)
        if setup == 'dash':
            p.dash_window = 0.2
        else:
            airborne(p)
        p.attack_held = True
        assert p.request_attack()
        assert not p.weapon.charging and p.weapon.rushing, setup        # 충전 없이 바로 짧은 돌진 (11/24)
        assert abs(p.gauge.value - (50 - config.GAUNTLET_QUICK_COST)) < 1e-6, setup
    room, p = world('gauntlet', gauge=50)
    p.attack_held = True
    p.request_attack()
    assert p.weapon.charging and not p.weapon.rushing                    # 땅 위 기본은 그대로 충전


# ----- 사슬 -----
def test_chain_dash_reaches_further_and_hooks_one_more():
    room, p = world('chain')
    base_count, base_reach, _ = p.weapon.grip()
    p.dash_window = 0.2
    count, reach, _ = p.weapon.grip()
    assert count == base_count + 1 and abs(reach - base_reach * config.CHAIN_DASH_REACH) < 1e-6
    p.request_attack()
    assert p.weapon.hook.reach == reach


def test_chain_air_hits_harder():
    room, p = world('chain')
    p.request_attack()
    ground = p.weapon.hook.damage
    room, p = world('chain')
    airborne(p)
    p.request_attack()
    assert abs(p.weapon.hook.damage - ground * config.CHAIN_AIR_MULT) < 1e-6


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
