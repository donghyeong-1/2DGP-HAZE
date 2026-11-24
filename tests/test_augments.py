"""증강 v2 (헤이즈 변이 + 무기 갈래, docs/plan_v7.md 2절). 창 없이: python tests/test_augments.py

- 갈래(family): 게이지 4계열(각성·위험·페이드·강화, 지금 12종) + 철파이프 연타·공중·이동 베기 + 공통 대시.
- 카드 3장: 가진 갈래 x3, 들고 있는 무기 갈래 x2, 공통 x1, 안 든 무기 갈래 x0.2. 셋 중 하나는 아직 없는 갈래.
- 진화(tier 'evo')는 같은 갈래 기본 2개를 가졌고 구현이 끝났을 때만 나온다.
- 철파이프 갈래 기본 증강은 실제로 효과가 있다 (공속, 3타 피해, 공중 피해, 대시 공격 피해, 대시).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import mutations as mu  # noqa: E402
import test_combat as tc  # noqa: E402


def _player():
    _room, p = tc.make_world()
    return p


def test_every_augment_has_a_known_family_and_tier():
    for mid, m in mu.MUTATIONS.items():
        assert m['family'] in mu.FAMILIES, mid
        assert m.get('tier', 'base') in ('base', 'evo', 'duo'), mid
    for fam in ('pipe_combo', 'pipe_air', 'pipe_dash', 'dash', 'chain_gather', 'chain_pierce', 'chain_link'):
        base = [m for m in mu.MUTATIONS.values() if m['family'] == fam and m.get('tier', 'base') == 'base']
        evo = [m for m in mu.MUTATIONS.values() if m['family'] == fam and m.get('tier') == 'evo']
        assert len(base) == 3 and len(evo) == 1, fam
        assert evo[0].get('ready'), fam                                   # 진화는 모두 구현됐다
        assert '준비 중' not in mu.FAMILIES[fam]['set'], fam
    for fam in ('chain_gather', 'chain_pierce', 'chain_link'):
        assert mu.FAMILIES[fam]['weapon'] == 'chain'
    duos = [m for m, v in mu.MUTATIONS.items() if v.get('tier') == 'duo']
    assert len(duos) >= 2
    for mid in duos:
        req = mu.MUTATIONS[mid]['requires']
        assert len(req) == 2 and all(mu.MUTATIONS[r].get('tier') == 'evo' for r in req), mid


def test_owned_family_is_offered_more_often():
    p = _player()
    mu.give(p, 'combo_speed')
    rng = random.Random(1)
    hits = sum(any(mu.MUTATIONS[m]['family'] == 'pipe_combo' for m in mu.offer(p, rng)) for _ in range(300))
    p2 = _player()
    rng = random.Random(1)
    base = sum(any(mu.MUTATIONS[m]['family'] == 'pipe_combo' for m in mu.offer(p2, rng)) for _ in range(300))
    assert hits > base


def test_offer_always_has_a_new_family():
    p = _player()
    for mid in ('combo_speed', 'air_power', 'dashcut_power'):
        mu.give(p, mid)
    rng = random.Random(3)
    for _ in range(100):
        fams = {mu.MUTATIONS[m]['family'] for m in mu.offer(p, rng)}
        assert fams - {mu.MUTATIONS[m]['family'] for m in mu.owned(p)}


def test_evolution_needs_two_of_its_family_and_implementation():
    p = _player()
    evo = [m for m, v in mu.MUTATIONS.items() if v.get('tier') == 'evo']
    assert evo
    rng = random.Random(5)
    assert not any(m in evo for _ in range(200) for m in mu.offer(p, rng))
    for m in evo:
        fam = mu.MUTATIONS[m]['family']
        if mu.MUTATIONS[m].get('ready'):
            for b in [k for k, v in mu.MUTATIONS.items() if v['family'] == fam and v.get('tier', 'base') == 'base'][:2]:
                mu.give(p, b)
            assert mu.available(p, m)


def test_pipe_augments_change_numbers():
    p = _player()
    assert mu.attack_speed_mult(p) == 1.0
    mu.give(p, 'combo_speed')
    assert mu.attack_speed_mult(p) < 1.0
    assert mu.pipe_damage_mult(p, finisher=True, air=False, dash=False) == 1.0
    mu.give(p, 'combo_third')
    assert mu.pipe_damage_mult(p, finisher=True, air=False, dash=False) > 1.0
    mu.give(p, 'air_power')
    assert mu.pipe_damage_mult(p, finisher=False, air=True, dash=False) > 1.0
    mu.give(p, 'dashcut_power')
    assert mu.pipe_damage_mult(p, finisher=False, air=False, dash=True) > 1.0
    slots = p.dash_max
    mu.give(p, 'dash_extra')
    assert p.dash_max == slots + 1


def test_combo_speed_shortens_real_pipe_cooldown_and_dash_iframe_lasts_longer():
    _room, p = tc.make_world()
    p.weapon.try_attack()
    plain = p.weapon.cooldown_max
    _room, p = tc.make_world()
    mu.give(p, 'combo_speed')
    p.weapon.try_attack()
    assert p.weapon.cooldown_max < plain
    mu.give(p, 'dash_iframe')
    tc.step(30)
    p.request_dash()
    tc.step(1)
    assert p.invuln_left > config.DASH_INVULN - 1 / 60


# ===================== 진화 (철파이프·대시) =====================
def _dummy(room, p, x):
    e = tc.freeze(tc.add_enemy('slum', x, room, p))
    e.hp = e.max_hp = 1000
    return e


def _swing(p):
    assert p.weapon.try_attack()
    tc.step(int(p.weapon.cooldown * 60) + 2)


def test_combo_evo_adds_fourth_and_fifth_hit_and_the_fifth_spins():
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    behind = _dummy(room, p, p.x - 70)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    for _ in range(4):
        _swing(p)
    assert p.weapon.combo == 1                                            # 진화 없이는 3타 뒤 다시 1타
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    behind = _dummy(room, p, p.x - 70)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    mu.give(p, 'combo_evo')
    for n in range(1, 5):
        _swing(p)
        assert p.weapon.combo == n
    assert behind.hp == 1000                                              # 1~4타는 앞쪽만
    _swing(p)
    assert p.weapon.combo == 5 and behind.hp < 1000                       # 5타 회전 베기: 등 뒤도 맞는다
    _swing(p)
    assert p.weapon.combo == 1


def _plunge_and_land(air_evo):
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    side = _dummy(room, p, p.x + 150)
    if air_evo:
        mu.give(p, 'air_evo')
    p.request_jump()
    tc.step(14)
    p.mouse_x, p.mouse_y = p.x, p.y - 300
    p.invuln_left = 0
    assert p.request_attack() and p.weapon.last_kind == 'plunge'
    top = side.y
    for _ in range(90):
        tc.step(1)
        top = max(top, side.y)
    return side, top


def test_air_evo_plunge_landing_strikes_lightning_and_lifts_nearby_enemies():
    side, top = _plunge_and_land(False)
    assert side.hp == 1000
    side, top = _plunge_and_land(True)
    assert side.hp < 1000 and top > tc.FLOOR_Y + 10                      # 착지 충격파가 옆 적을 치고 띄운다


def _dash_strike(dashcut_evo):
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    e = _dummy(room, p, p.x + config.DASH_SPEED * config.DASH_TIME * 0.5)
    if dashcut_evo:
        mu.give(p, 'dashcut_evo')
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    tc.dash_until_done(p)
    tc.step(2)
    hp = e.hp
    tc.step(30)
    return hp, e.hp


def test_dashcut_evo_flashes_the_path_again_after_a_moment():
    first, later = _dash_strike(False)
    assert first < 1000 and later == first
    first, later = _dash_strike(True)
    assert first < 1000 and later < first                                # 0.3초 뒤 번쩍이며 다시 벤다


def _dash_past(mids, gap):
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    e = _dummy(room, p, p.x + gap)
    for m in mids:
        mu.give(p, m)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    tc.dash_until_done(p, attack=False)
    tc.step(30)
    return e


def test_dash_evo_leaves_an_afterimage_that_swings_once():
    assert _dash_past((), 90).hp == 1000
    assert _dash_past(('dash_evo',), 90).hp < 1000                         # 대시 시작 자리의 분신이 앞을 벤다


# ===================== 사슬 갈래 =====================
def _chain(gauge, gaps, mids):
    import test_chain
    room, p, foes = test_chain.setup(gauge, gaps)
    for m in mids:
        mu.give(p, m)
    hook = test_chain.fire_and_wait(p)
    return room, p, foes, hook


def test_gather_pulls_one_more_stuns_and_clashes():
    _r, _p, (a, b), hook = _chain(35, [250, 380], ['gather_more'])
    assert len(hook.pulled) == 2                                          # 노멀 1마리 + 1
    _r, _p, (a,), hook = _chain(35, [250], ['gather_stun'])
    assert a.state == 'HIT' and a.hit_left > 0.3                          # 끌려온 적 0.6초 기절
    _r, _p, (a, b), _h = _chain(35, [250, 380], ['gather_more'])
    plain = (1000 - a.hp) + (1000 - b.hp)
    _r, _p, (a, b), _h = _chain(35, [250, 380], ['gather_more', 'gather_clash'])
    assert (1000 - a.hp) + (1000 - b.hp) > plain                          # 끌려온 적끼리 부딪힌다 (노멀에서도)


def test_gather_evo_vortex_drags_in_enemies_that_were_not_hooked():
    import test_chain
    for evo in (False, True):
        room, p, (a,) = test_chain.setup(35, [250])
        other = _dummy(room, p, p.x - 220)
        if evo:
            mu.give(p, 'gather_evo')
        test_chain.fire_and_wait(p)
        tc.step(40)
        pulled_in = abs(other.x - p.x) < 180 and other.hp < 1000
        assert pulled_in == evo                                           # 소용돌이가 둘레의 적을 모아 묶는다


def test_pierce_goes_through_ramps_damage_and_reaches_further():
    _r, _p, (a, b), hook = _chain(35, [250, 380], [])
    assert b.hp == 1000
    _r, _p, (a, b), hook = _chain(35, [250, 380], ['pierce_through'])
    assert b.hp < 1000 and len(hook.pulled) == 1                          # 관통해 맞히지만 끌어오는 수는 그대로
    _r, _p, (a, b), _h = _chain(35, [250, 380], ['pierce_through', 'pierce_ramp'])
    assert (1000 - b.hp) > (1000 - a.hp) * 1.1                            # 관통할수록 세진다
    far = config.CHAIN_RANGE * 1.2
    _r, _p, (a,), _h = _chain(35, [far], [])
    assert a.hp == 1000
    _r, _p, (a,), _h = _chain(35, [far], ['pierce_reach'])
    assert a.hp < 1000


def _bounce(evo):
    room, p = tc.make_world_with(tc.walled_room(), 14 * config.TILE + 10)
    p.give_weapon('chain')
    tc.set_gauge(p, 35)
    back = _dummy(room, p, p.x - 200)
    if evo:
        mu.give(p, 'pierce_evo')
    p.mouse_x, p.mouse_y = p.x + 400, back.center[1]
    import test_chain
    test_chain.fire_and_wait(p)
    return back


def test_pierce_evo_chain_bounces_off_walls():
    assert _bounce(False).hp == 1000
    assert _bounce(True).hp < 1000                                         # 벽에 꺾여 돌아와 뒤쪽 적을 친다


def test_link_binds_hooked_enemies_and_shares_damage():
    for mids, share in ((['link_bind'], mu.LINK_SHARE[0]), (['link_bind', 'link_share'], mu.LINK_SHARE[1])):
        _r, p, (a, b), _h = _chain(65, [250, 380], mids)
        assert b in mu.linked(a)
        hp = b.hp
        p.weapon._hit(a, 100.0, 0, p.weapon._fx(False), extra=False)
        assert abs((hp - b.hp) - 100.0 * share) < 0.6, (mids, hp - b.hp)
    _r, p, (a, b), _h = _chain(65, [250, 380], ['link_burst'])
    a.hp = 10
    hp = b.hp
    p.weapon._hit(a, 100.0, 0, p.weapon._fx(False), extra=False)
    assert not a.alive and hp - b.hp >= 100.0 * mu.LINK_SHARE[0] + mu.LINK_BURST[1] - 0.6   # 묶인 적이 죽으면 터진다


def test_link_evo_nets_every_hooked_enemy():
    _r, p, (a, b, c), _h = _chain(65, [220, 320, 420], ['gather_more', 'link_evo'])
    assert b in mu.linked(a) and c in mu.linked(a)
    hb, hc = b.hp, c.hp
    p.weapon._hit(a, 100.0, 0, p.weapon._fx(False), extra=False)
    assert hb - b.hp >= 49 and hc - c.hp >= 49


# ===================== 합성 =====================
def test_duo_needs_both_evolutions_and_takes_a_card():
    p = _player()
    mu.give(p, 'combo_evo')
    assert not mu.available(p, 'duo_echo_combo')
    mu.give(p, 'dash_evo')
    assert mu.available(p, 'duo_echo_combo')
    rng = random.Random(2)
    assert all('duo_echo_combo' in mu.offer(p, rng) for _ in range(20))   # 열린 합성은 카드 한 장을 먼저 차지한다


def test_duo_echo_combo_afterimage_spins():
    assert _dash_past(('dash_evo',), -70).hp == 1000                      # 분신은 앞만 벤다
    assert _dash_past(('dash_evo', 'combo_evo', 'duo_echo_combo'), -70).hp < 1000   # 분신 연타: 회전 베기


def test_duo_flash_net_binds_what_the_flash_cuts():
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    a = _dummy(room, p, p.x + 120)
    b = _dummy(room, p, p.x + 220)
    for m in ('dashcut_evo', 'link_evo', 'duo_flash_net'):
        mu.give(p, m)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    tc.dash_until_done(p)
    tc.step(30)
    assert b in mu.linked(a)


# ===================== 카드·일시정지 화면에 보일 정보 =====================
def test_card_info_shows_rarity_and_steps_to_evolution():
    p = _player()
    assert mu.card_info(p, 'combo_speed')['rarity'] == 'common'
    assert '진화까지 1개' in mu.card_info(p, 'combo_speed')['note']
    mu.give(p, 'combo_speed')
    assert '진화 열림' in mu.card_info(p, 'combo_third')['note']
    assert mu.card_info(p, 'combo_evo')['rarity'] == 'rare'
    assert mu.card_info(p, 'duo_echo_combo')['rarity'] == 'legendary'


def test_second_weapon_augments_are_inactive_without_that_weapon():
    p = _player()
    mu.give(p, 'gather_more')
    assert not mu.active(p, 'gather_more') and mu.active(p, 'combo_speed')
    assert '사슬' in mu.card_info(p, 'gather_stun')['note']
    p.give_weapon('chain')
    assert mu.active(p, 'gather_more')


def test_build_is_grouped_by_family():
    p = _player()
    for m in ('combo_speed', 'air_power', 'combo_third'):
        mu.give(p, m)
    assert mu.grouped(p) == [('pipe_combo', ['combo_speed', 'combo_third']), ('pipe_air', ['air_power'])]


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
