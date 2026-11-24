"""건틀릿 갈래 3개 (v7, 2026-11-24, docs/plan_v7.md 2절). 창 없이: python tests/test_gauntlet_paths.py

충전: 충전 시간 -25% / 완충 피해 +30% / 충전 중 받는 피해 -30% / 진화 '헤이즈 붕괴': 완충 강타가 폭발 원 + 번쩍 + 빛.
충돌: 넉백 +40% / 날아간 적이 벽에 부딪히면 피해 / 날아간 적이 멈추면 0.5초 기절 / 진화 '연쇄 충돌': 날아간 적이 부딪힌 적도 날아간다.
반격: 예고 중인 적을 치면 피해 2배 / 반격하면 0.3초 무적 / 반격하면 게이지 +5% / 진화 '역류': 반격 순간 고리 충격파가 적 투사체를 되돌린다.
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

FAMS = ('gauntlet_charge', 'gauntlet_crash', 'gauntlet_counter')


def _armed(*mids, gauge=40, x=300.0):
    room, p = tc.make_world(player_x=x)
    p.give_weapon('gauntlet')
    p.gauge.value = gauge
    p.gauge.zone = p.gauge._zone_of(gauge)
    for m in mids:
        mu.give(p, m)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    return room, p


def _full_charge(p):
    p.attack_held = True
    assert p.request_attack()
    for _ in range(120):
        tc.run_frames(1)
        if p.weapon.charge_ratio >= 1.0:
            break
    p.attack_held = False
    tc.run_frames(1)                                                     # 떼면 나간다


def _enemy(room, p, dx, hp=9999, kind='slum'):
    e = tc.add_enemy(kind, p.x + dx, room, p)
    e.stats = dict(e.stats, speed=0.0, sight=0)
    e.hp = e.max_hp = hp
    return e


def test_three_gauntlet_families_with_three_bases_and_a_ready_evolution():
    for fam in FAMS:
        assert mu.FAMILIES[fam]['weapon'] == 'gauntlet'
        base = [m for m, v in mu.MUTATIONS.items() if v['family'] == fam and mu.tier(m) == 'base']
        evo = [m for m, v in mu.MUTATIONS.items() if v['family'] == fam and mu.tier(m) == 'evo']
        assert len(base) == 3 and len(evo) == 1 and mu.MUTATIONS[evo[0]]['ready'], fam


def test_charge_faster_harder_and_guarded():
    room, p = _armed()
    need = p.weapon.charge_need()
    room, p = _armed('charge_fast')
    assert p.weapon.charge_need() < need
    dealt = []
    for mids in ((), ('charge_power',)):
        room, p = _armed(*mids)
        e = _enemy(room, p, 200)
        _full_charge(p)
        tc.run_frames(20)
        dealt.append(e.max_hp - e.hp)
    assert dealt[1] > dealt[0] * 1.2
    room, p = _armed('charge_guard')
    assert mu.taken_mult(p) == 1.0
    p.attack_held = True
    p.request_attack()
    tc.run_frames(2)
    assert p.weapon.charging and mu.taken_mult(p) < 1.0                  # 충전하는 동안만 덜 아프다


def test_collapse_evolution_bursts_around_the_first_hit():
    room, p = _armed('charge_evo')
    a = _enemy(room, p, 200)
    b = _enemy(room, p, 200)
    b.y += 150                                                           # 충격파 줄에서 벗어난 위쪽
    _full_charge(p)
    tc.run_frames(20)
    assert a.hp < a.max_hp and b.hp < b.max_hp                           # 폭발 원이 둘레 적도 친다


def test_crash_knocks_harder_hits_walls_and_stuns():
    vxs = []
    for mids in ((), ('crash_knock',)):
        room, p = _armed(*mids)
        e = _enemy(room, p, 150)
        _full_charge(p)
        for _ in range(10):
            tc.run_frames(1)
            if e.hp < e.max_hp:
                break
        vxs.append(abs(e.vx))
    assert vxs[1] > vxs[0] * 1.3
    room, p = _armed('crash_wall', 'crash_stun', x=config.TILE * 19)    # 오른쪽 벽 기둥(23~25열) 쪽으로 친다
    e = _enemy(room, p, 110)
    _full_charge(p)
    before, stunned = None, False
    for _ in range(60):
        tc.run_frames(1)
        if e.hp < e.max_hp and before is None:
            before = e.hp
        stunned = stunned or (e.state == 'HIT' and e.hit_left > 0.3)
    assert before is not None and e.hp < before                          # 날아가 벽에 부딪혀 한 번 더 아팠다
    assert stunned                                                       # 멈춘 뒤 기절


def test_chain_crash_bowls_into_another_enemy():
    room, p = _armed('crash_evo', 'crash_knock')
    a = _enemy(room, p, 140)
    b = _enemy(room, p, 330)
    _full_charge(p)
    tc.run_frames(40)
    assert b.hp < b.max_hp and b.x > p.x + 330                           # 날아간 a에 맞아 b도 밀려났다


def test_counter_hits_harder_guards_and_fills_gauge():
    dealt = []
    for mids in ((), ('counter_power',)):
        room, p = _armed(*mids)
        e = _enemy(room, p, 200)
        e.state, e.attack_time = 'ATTACK', 0.0                          # 공격 예고 중
        e.stats = dict(e.stats, windup=10.0)
        _full_charge(p)
        tc.run_frames(20)
        dealt.append(e.max_hp - e.hp)
    assert dealt[1] > dealt[0] * 1.8
    room, p = _armed('counter_guard', 'counter_gain')
    e = _enemy(room, p, 200)
    e.state, e.attack_time = 'ATTACK', 0.0
    e.stats = dict(e.stats, windup=10.0)
    _full_charge(p)
    g = p.gauge.value
    for _ in range(20):
        tc.run_frames(1)
        if e.hp < e.max_hp:
            break
    assert p.invuln_left >= 0.25 and p.gauge.value >= g + 4


def test_backflow_evolution_turns_enemy_shots_around():
    import projectile
    room, p = _armed('counter_evo')
    e = _enemy(room, p, 200)
    e.state, e.attack_time = 'ATTACK', 0.0
    e.stats = dict(e.stats, windup=10.0)
    shot = projectile.Scrap(p.x + 120, p.center[1] + 60, -1, 10.0, 5, room, p)
    game_world.add_object(shot, game_world.LAYER_EFFECT)
    _full_charge(p)
    for _ in range(20):
        tc.run_frames(1)
        if e.hp < e.max_hp:
            break
    effects = game_world.world[game_world.LAYER_EFFECT]
    assert shot not in effects                                           # 적 투사체가 사라지고
    assert any(type(o).__name__ == 'Blast' and getattr(o, 'reflected', False) for o in effects)   # 되돌아가는 충격파가 됐다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
