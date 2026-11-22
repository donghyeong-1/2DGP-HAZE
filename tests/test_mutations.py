"""헤이즈 변이·방 보상 테스트 (창 없이). 실행: python tests/test_mutations.py

2026-11-22 v5 계획 3 (docs/plan_v5.md, 하데스 축복·방 보상 참고):
- 변이 12종, 4계열(각성 bloom / 위험 ember / 페이드 hollow / 강화 tide). 계열마다 그 게이지 구간에서 힘을 낸다.
- 같은 계열 2개면 시너지(계열 보너스)가 켜진다.
- 전투방마다 시드로 정해진 보상(조각·회복·변이·헤이즈 결정)이 있고, 그 방으로 가는 문 위에 미리 보인다.
- 방을 깨면 보상을 준다. 변이면 셋 중 하나를 고르는 카드 창(on_mutation)이 열린다.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import haze_gauge  # noqa: E402
import mutations as mu  # noqa: E402
import test_combat as tc  # noqa: E402


def world(gauge=40.0):
    room, p = tc.make_world()
    p.gauge.value = gauge
    p.gauge.zone = p.gauge._zone_of(gauge)
    return room, p


# ----- 목록 -----
def test_twelve_mutations_in_four_families():
    assert len(mu.MUTATIONS) == 12
    fams = [m['family'] for m in mu.MUTATIONS.values()]
    assert set(fams) == set(mu.FAMILIES) and len(mu.FAMILIES) == 4
    assert all(fams.count(f) == 3 for f in mu.FAMILIES)
    assert all(m['name'] and m['desc'] for m in mu.MUTATIONS.values())
    assert all(f['set'] for f in mu.FAMILIES.values())          # 계열마다 시너지 설명


def test_offer_three_distinct_unowned_and_seeded():
    _room, p = world()
    a = mu.offer(p, random.Random(5))
    b = mu.offer(p, random.Random(5))
    assert a == b and len(a) == 3 and len(set(a)) == 3          # 같은 시드면 같은 셋
    mu.give(p, a[0])
    for s in range(30):
        assert a[0] not in mu.offer(p, random.Random(s))         # 가진 것은 다시 나오지 않는다
    assert len({mu.MUTATIONS[m]['family'] for m in a}) >= 2      # 한 계열로 몰리지 않는다


# ----- 각성 bloom -----
def test_bloom_crit_only_while_awake():
    _room, p = world(gauge=40.0)
    base = p.weapon._damage(1.0)
    mu.give(p, 'bloom_crit')
    assert abs(p.weapon._damage(1.0) - base) < 1e-6              # 보통 구간: 그대로
    _room, p = world(gauge=75.0)
    base = p.weapon._damage(1.0)
    mu.give(p, 'bloom_crit')
    assert p.weapon._damage(1.0) > base * 1.15                    # 각성: 더 세다


def test_bloom_gain_and_tide_chain_kill_gain():
    _room, p = world(gauge=75.0)
    base = p.kill_gain()
    mu.give(p, 'bloom_gain')
    assert p.kill_gain() == base + mu.BLOOM_GAIN
    mu.give(p, 'tide_chain')
    assert p.kill_gain(enhanced=True) == base + mu.BLOOM_GAIN + mu.TIDE_CHAIN
    assert p.kill_gain(enhanced=False) == base + mu.BLOOM_GAIN


def test_bloom_dash_shockwave_hits_nearby_enemies():
    room, p = world(gauge=75.0)
    e = tc.add_enemy('slum', p.x + 380, room, p)
    tc.freeze(e)
    mu.give(p, 'bloom_dash')
    hp = e.hp
    p.mouse_x = p.x + 400
    p.right = True
    p.request_dash()
    tc.step(40)
    assert e.hp < hp                                              # 대시가 끝난 자리에서 충격파


# ----- 위험 ember -----
def test_ember_guard_cuts_damage_in_critical():
    _room, p = world(gauge=92.0)
    mu.give(p, 'ember_guard')
    p.invuln_left = 0.0
    p.take_hit(20)
    assert p.hp == p.max_hp - round(20 * mu.EMBER_GUARD)


def test_ember_burst_overload_damages_enemies():
    room, p = world(gauge=96.0)
    e = tc.add_enemy('slum', p.x + 200, room, p)
    tc.freeze(e)
    mu.give(p, 'ember_burst')
    hp = e.hp
    p.gauge.add(20, 'test')                                       # 오버로드
    assert e.hp < hp


def test_ember_cool_halves_overload_damage():
    _room, p = world(gauge=96.0)
    mu.give(p, 'ember_cool')
    p.gauge.add(20, 'test')
    lost = p.max_hp - p.hp
    assert 0 < lost <= int(p.max_hp * config.OVERLOAD_DAMAGE_RATIO * 0.5) + 1


# ----- 페이드 hollow -----
def test_hollow_leech_heals_on_hit_in_fade():
    room, p = world(gauge=12.0)
    e = tc.add_enemy('slum', p.x + 80, room, p)
    tc.freeze(e)
    mu.give(p, 'hollow_leech')
    p.hp = 50
    p.weapon._hit(e, 1, 0, p.weapon._fx(False))
    assert p.hp == 50 + mu.HOLLOW_LEECH


def test_hollow_dash_faster_recharge():
    _room, p = world()
    before = p.dash_recharge
    mu.give(p, 'hollow_dash')
    assert abs(p.dash_recharge - before * mu.HOLLOW_DASH) < 1e-6


def test_hollow_floor_revives_once():
    _room, p = world(gauge=3.0)
    mu.give(p, 'hollow_floor')
    p.gauge.add(-10, 'test')
    assert p.gauge.zone != haze_gauge.DEAD and p.gauge.value == mu.HOLLOW_FLOOR
    p.gauge.add(-50, 'test')
    assert p.gauge.zone == haze_gauge.DEAD                        # 판에 한 번뿐


# ----- 강화 tide -----
def test_tide_cost_cheaper_enhance():
    _room, p = world(gauge=60.0)
    mu.give(p, 'tide_cost')
    g0 = p.gauge.value
    assert p.gauge.use_enhance()
    assert abs((g0 - p.gauge.value) - (p.gauge.enhance_cost - mu.TIDE_COST)) < 1e-6


def test_tide_wave_spreads_enhanced_hits():
    room, p = world(gauge=60.0)
    a = tc.add_enemy('slum', p.x + 80, room, p)
    b = tc.add_enemy('slum', p.x + 200, room, p)
    for e in (a, b):
        tc.freeze(e)
    mu.give(p, 'tide_wave')
    hp = b.hp
    fx = p.weapon._fx(True)
    p.weapon._hit(a, 20, 0, fx, extra=False)
    assert b.hp < hp                                              # 강화 타격이 옆 적에게 번진다


# ----- 시너지 -----
def test_synergy_needs_two_of_a_family():
    _room, p = world(gauge=75.0)
    s0 = p.speed_mult()
    mu.give(p, 'bloom_crit')
    assert not mu.synergy(p, 'bloom') and abs(p.speed_mult() - s0) < 1e-6
    mu.give(p, 'bloom_gain')
    assert mu.synergy(p, 'bloom') and p.speed_mult() > s0          # 각성 2개: 각성 구간 이동 속도


def test_hollow_and_tide_and_ember_synergies():
    _room, p = world(gauge=12.0)
    slow = p.speed_mult()
    mu.give(p, 'hollow_leech')
    mu.give(p, 'hollow_dash')
    assert p.speed_mult() > slow                                   # 페이드 감속이 사라진다
    _room, p = world(gauge=60.0)
    mu.give(p, 'tide_cost')
    mu.give(p, 'tide_chain')
    p.gauge.use_enhance()
    assert p.gauge.enhance_timer > config.ENHANCE_TIME              # 강화 준비 시간이 길다
    _room, p = world(gauge=90.0)
    mu.give(p, 'ember_guard')
    mu.give(p, 'ember_cool')
    g0 = p.gauge.value
    p.gauge.add(4, 'hit')
    assert p.gauge.value - g0 < 4                                  # 위험 구간에서 덜 오른다


# ----- 방 보상 -----
def make_stage(seed=3):
    import stage as stage_mod
    room, p = tc.make_world()
    st = stage_mod.Stage(p, seed=seed, name='stage1')
    st.start()
    return st, p


def test_rewards_seeded_for_combat_rooms():
    st, _p = make_stage(3)
    st2, _p2 = make_stage(3)
    combat = [c for c in st.layout if st.type_of(c) == 'combat']
    assert combat
    assert all(st.reward_of(c) in mu.REWARDS for c in combat)
    assert [st.reward_of(c) for c in combat] == [st2.reward_of(c) for c in combat]
    assert all(st.reward_of(c) is None for c in st.layout if st.type_of(c) not in ('combat',))


def test_reward_shown_on_doors_to_uncleared_combat_rooms():
    st, _p = make_stage(3)
    for d in st.room.links:
        n = st.neighbour(st.coord, d)
        if n in st.layout and st.type_of(n) == 'combat' and n not in st.cleared:
            assert st.room.door_rewards[d] == st.reward_of(n)
        else:
            assert d not in st.room.door_rewards


def test_clear_grants_reward_and_mutation_opens_choice():
    st, p = make_stage(3)
    got = []
    st.on_mutation = got.append
    for kind in ('shards', 'heal', 'crystal', 'mutation'):
        p.hp, s0, c0 = 40, p.shards, getattr(p, 'bonus_crystals', 0)
        st.grant_reward(kind)
        if kind == 'shards':
            assert p.shards > s0
        elif kind == 'heal':
            assert p.hp > 40
        elif kind == 'crystal':
            assert p.bonus_crystals > c0
    assert len(got) == 1 and len(got[0]) == 3                     # 변이: 셋을 골라 창을 연다


def test_choice_mode_gives_picked_mutation():
    import mutation_mode
    _room, p = world()
    mutation_mode.setup(p, ['bloom_crit', 'ember_guard', 'tide_cost'])
    mutation_mode.selected = 1
    mutation_mode.choose()
    assert p.mutations == ['ember_guard']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
