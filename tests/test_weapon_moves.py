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


# ----- 식칼 -----
def test_knife_kinds_follow_dash_and_air():
    room, p = world('knife')
    assert p.weapon.current_kind() == 'knife'
    p.dash_window = 0.2
    assert p.weapon.current_kind() == 'knife_dash'
    p.dash_window = 0.0
    airborne(p)
    assert p.weapon.current_kind() == 'knife_air'


def test_knife_dash_throws_one_more_in_a_line_and_pierces():
    room, p = world('knife')
    ground, _, pierce = p.weapon.volley()
    assert not pierce                                                   # 노멀 기본은 관통하지 않는다
    p.dash_window = 0.2
    p.request_attack()
    ks = objects('ThrownKnife')
    assert len(ks) == ground + 1 and all(k.pierce for k in ks)
    spread = max(k.dy for k in ks) - min(k.dy for k in ks)
    assert spread < 0.15                                                # 거의 일자


def test_knife_air_throws_a_wider_fan():
    room, p = world('knife')
    p.request_attack()
    ground = objects('ThrownKnife')
    g_spread = max(k.dy for k in ground) - min(k.dy for k in ground)
    room, p = world('knife')
    airborne(p)
    p.request_attack()
    air = objects('ThrownKnife')
    assert len(air) == len(ground) + 1
    assert max(k.dy for k in air) - min(k.dy for k in air) > g_spread + 0.2


# ----- 건틀릿 -----
def test_gauntlet_dash_and_air_fire_at_once_for_a_little_gauge():
    for setup in ('dash', 'air'):
        room, p = world('gauntlet', gauge=50)
        if setup == 'dash':
            p.dash_window = 0.2
        else:
            airborne(p)
        p.attack_held = True
        assert p.request_attack()
        assert not p.weapon.charging and objects('Blast'), setup        # 충전 없이 바로
        assert abs(p.gauge.value - (50 - config.GAUNTLET_QUICK_COST)) < 1e-6, setup
    room, p = world('gauntlet', gauge=50)
    p.attack_held = True
    p.request_attack()
    assert p.weapon.charging and not objects('Blast')                    # 땅 위 기본은 그대로 충전


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
