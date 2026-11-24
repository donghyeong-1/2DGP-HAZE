"""쌍권총 갈래 3개 (v7, 2026-11-24, docs/plan_v7.md 2절). 창 없이: python tests/test_pistol_paths.py

연사: 연사 +20% / 탄 +1(부채꼴) / 멈춰 서서 쏘면 연사 +30% / 진화 '난사': 누르고 있으면 끊김 없는 탄막과 탄피.
도탄: 벽에 1번 반사 / 반사한 총알 피해 +30% / 반사 +1번 / 진화 '도탄 사슬': 맞힌 총알이 가까운 적으로 튕김(최대 3).
대시 사격: 대시 중 자동 사격 / 대시 직후 0.5초 연사 2배 / 저스트 대시로 피하면 강화탄 장전 / 진화 '탄막 회피': 대시 끝 자리 8방향 탄막.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import mutations as mu  # noqa: E402
import test_combat as tc  # noqa: E402

FAMS = ('pistol_rapid', 'pistol_ricochet', 'pistol_dash')


def _bullets():
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Bullet']


def _armed(*mids, gauge=35):
    room, p = tc.make_world()
    p.give_weapon('pistol')
    p.gauge.value = gauge
    p.gauge.zone = p.gauge._zone_of(gauge)
    for m in mids:
        mu.give(p, m)
    return room, p


def _fire(p, dx=400, dy=0):
    p.mouse_x, p.mouse_y = p.x + dx, p.center[1] + dy
    p.weapon.cooldown = 0
    assert p.request_attack()


def test_three_pistol_families_with_three_bases_and_a_ready_evolution():
    for fam in FAMS:
        assert mu.FAMILIES[fam]['weapon'] == 'pistol'
        base = [m for m, v in mu.MUTATIONS.items() if v['family'] == fam and mu.tier(m) == 'base']
        evo = [m for m, v in mu.MUTATIONS.items() if v['family'] == fam and mu.tier(m) == 'evo']
        assert len(base) == 3 and len(evo) == 1 and mu.MUTATIONS[evo[0]]['ready'], fam


def test_rapid_speed_still_and_extra_bullet():
    room, p = _armed()
    _fire(p)
    plain = p.weapon.cooldown
    room, p = _armed('rapid_speed')
    _fire(p)
    assert p.weapon.cooldown < plain
    fast = p.weapon.cooldown
    room, p = _armed('rapid_speed', 'rapid_still')
    _fire(p)
    assert p.weapon.cooldown < fast                                      # 멈춰 서서 쏘면 더 빠르다
    room, p = _armed('rapid_extra')
    _fire(p)
    assert len(_bullets()) == 2                                          # 노멀 1발 + 1


def test_rapid_evolution_holds_a_continuous_barrage_with_casings():
    room, p = _armed('rapid_evo')
    _fire(p)
    tapped = p.weapon.cooldown
    room, p = _armed('rapid_evo')
    p.attack_held = True
    _fire(p)
    assert p.weapon.cooldown < tapped * 0.7                              # 누르고 있으면 끊김 없이
    assert any(type(o).__name__ == 'ShellCasing' for o in game_world.world[game_world.LAYER_EFFECT])


def test_ricochet_bounces_off_walls_and_hits_harder_after():
    room, p = _armed()
    _fire(p, dx=-400)                                                    # 왼쪽 벽으로
    tc.run_frames(30)
    assert not _bullets()                                                # 반사가 없으면 벽에서 사라진다
    room, p = _armed('ric_bounce', 'ric_power')
    _fire(p, dx=-400)
    b = _bullets()[0]
    d0 = b.damage
    for _ in range(30):
        tc.run_frames(1)
        if b.bounced:
            break
    assert b.bounced == 1 and b.dx > 0 and b.damage > d0                 # 벽에서 튕겨 오른쪽으로, 피해 +30%
    room, p = _armed('ric_bounce', 'ric_more')
    _fire(p, dx=-400)
    assert _bullets()[0].bounces == 2


def test_ricochet_chain_jumps_to_nearby_enemies():
    room, p = _armed('ric_evo')
    a = tc.freeze(tc.add_enemy('slum', p.x + 300, room, p))
    b = tc.freeze(tc.add_enemy('slum', p.x + 300, room, p))
    b.y += 260                                                           # 총알 줄에서 벗어난 위쪽
    a.hp = a.max_hp = b.hp = b.max_hp = 999
    _fire(p, dy=0)
    tc.run_frames(40)
    assert a.hp < 999 and b.hp < 999                                     # 맞힌 총알이 가까운 적으로 튕겼다


def test_dash_auto_fire_after_dash_speed_and_loaded_round():
    room, p = _armed('dshot_auto')
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_dash()
    seen = set()
    for _ in range(8):
        tc.run_frames(1)
        seen |= {id(b) for b in _bullets()}
    assert len(seen) >= 2                                                # 누르지 않아도 대시 중에 쏜다
    room, p = _armed('dshot_after')
    p.request_dash()
    tc.run_frames(int(config.DASH_TIME * 60) + 2)
    _fire(p)
    assert p.weapon.cooldown <= config.PISTOL_COOLDOWN * 0.5 + 1e-6      # 대시 직후 연사 2배
    room, p = _armed('dshot_load', gauge=35)
    p.request_dash()
    tc.run_frames(1)
    assert p.try_just_dash()
    assert p.weapon.loaded
    g = p.gauge.value
    tc.run_frames(20)
    _fire(p)
    assert _bullets()[-1].big and not p.weapon.loaded                    # 강화탄: 게이지를 쓰지 않는 큰 한 발
    assert p.gauge.value > g - 5                                         # E 강화 비용(25%)을 내지 않았다


def test_dash_evolution_leaves_a_ring_of_bullets():
    room, p = _armed('dshot_evo')
    p.request_dash()
    seen = set()
    for _ in range(int(config.DASH_TIME * 60) + 6):                     # 아래쪽 총알은 바닥에 바로 닿으니 나타난 것을 모두 센다
        tc.run_frames(1)
        seen |= {id(b) for b in _bullets()}
    assert len(seen) >= 8


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
