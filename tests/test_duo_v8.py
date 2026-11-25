"""합성 증강 6종 추가 (v8 계획 1-4, docs/plan_v8.md). 창 없이: python tests/test_duo_v8.py

진화 둘이 만나 나오는 전설 카드(합성)를 2종에서 8종으로 늘린다. 5일 차까지 넣은 것(각인·격발, 교체기, 띄우기)과 엮인다.
- 끌어모아 한 방 (소용돌이 + 헤이즈 붕괴): 소용돌이가 끝나는 순간 그 자리에서 헤이즈 붕괴가 터진다.
- 볼링 내려찍기 (낙뢰 내려찍기 + 연쇄 충돌): 낙뢰에 맞은 적이 위로 뜨는 대신 옆으로 날아가 다른 적을 들이받는다.
- 집중 탄막 (난사 + 소용돌이): 쌍권총 총알이 소용돌이에 묶인 적에게 휘어 들어간다.
- 반격 탄막 (역류 + 탄막 회피): 반격하는 순간 쌍권총이 사방으로 탄막을 쏜다 (건틀릿을 든 채로).
- 각인 폭풍 (서로 다른 무기의 진화 둘): 격발이 가장 가까운 다른 적에게 한 번 더 번진다 (번진 격발은 다시 번지지 않는다).
- 교체 연무 (서로 다른 무기의 진화 둘): 교체기 쿨다운이 짧아지고, 대신 쓸 때마다 게이지가 줄어든다.
  게이지가 모자라면(DUO_MIST[2] 아래) 보통 쿨다운으로 쓰고 게이지는 줄지 않는다 (교체기로 죽지 않는다).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import combo  # noqa: E402
import config  # noqa: E402
import game_world  # noqa: E402
import mutations as mu  # noqa: E402
import test_combat as tc  # noqa: E402

NEW = ('duo_vortex_collapse', 'duo_bolt_bowl', 'duo_focus_barrage', 'duo_counter_ring', 'duo_imprint_storm', 'duo_swap_mist')


def _dummy(room, p, dx, hp=10 ** 5):
    e = tc.freeze(tc.add_enemy('slum', p.x + dx, room, p))
    e.hp = e.max_hp = hp
    return e


def _bullets():
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Bullet']


# ===================== 목록과 나오는 조건 =====================
def test_eight_duos_and_the_six_new_ones_are_ready_legendary_cards():
    duos = [m for m, v in mu.MUTATIONS.items() if v.get('tier') == 'duo']
    assert len(duos) == 8
    p = tc.make_world()[1]
    for mid in NEW:
        m = mu.MUTATIONS[mid]
        assert m['family'] == 'duo' and m.get('ready') and m['name'] and m['desc'], mid
        assert mu.card_info(p, mid)['rarity'] == 'legendary'
        assert mu.card_info(p, mid)['note'] and '합성' not in mu.card_info(p, mid)['note']   # 조건만 적는다 (카드 위에 '합성' 띠가 따로 있다)


def test_fixed_pair_duos_need_both_named_evolutions():
    pairs = {'duo_vortex_collapse': ('gather_evo', 'charge_evo'), 'duo_bolt_bowl': ('air_evo', 'crash_evo'),
             'duo_focus_barrage': ('rapid_evo', 'gather_evo'), 'duo_counter_ring': ('counter_evo', 'dshot_evo')}
    for mid, req in pairs.items():
        assert set(mu.MUTATIONS[mid]['requires']) == set(req), mid
        p = tc.make_world()[1]
        mu.give(p, req[0])
        assert not mu.available(p, mid)
        mu.give(p, req[1])
        assert mu.available(p, mid)


def test_combo_duos_need_evolutions_of_two_different_weapons():
    for mid in ('duo_imprint_storm', 'duo_swap_mist'):
        p = tc.make_world()[1]
        mu.give(p, 'combo_evo')
        mu.give(p, 'air_evo')                                             # 둘 다 철파이프
        assert not mu.available(p, mid)
        p = tc.make_world()[1]
        mu.give(p, 'combo_evo')
        mu.give(p, 'dash_evo')                                            # 대시는 무기가 아니다
        assert not mu.available(p, mid)
        mu.give(p, 'rapid_evo')                                           # 철파이프 + 쌍권총
        assert mu.available(p, mid)
        assert '다른 무기' in mu.card_info(p, mid)['note']


def test_an_open_new_duo_still_takes_a_card():
    p = tc.make_world()[1]
    for m in ('combo_evo', 'rapid_evo'):
        mu.give(p, m)
    rng = random.Random(4)
    for _ in range(20):
        cards = mu.offer(p, rng)
        assert any(mu.tier(m) == 'duo' for m in cards) and len(set(cards)) == len(cards)


# ===================== 효과 =====================
def _vortex(duo):
    import test_chain
    room, p, (a,) = test_chain.setup(35, [250])
    other = _dummy(room, p, -220)
    for m in ('gather_evo', 'charge_evo') + (('duo_vortex_collapse',) if duo else ()):
        mu.give(p, m)
    test_chain.fire_and_wait(p)
    tc.step(40)
    return other.max_hp - other.hp


def test_vortex_collapse_bursts_where_the_vortex_ends():
    plain, duo = _vortex(False), _vortex(True)
    assert plain > 0
    assert duo > plain + 5                                                # 소용돌이 끝에 붕괴 폭발이 더해진다


def _bolt(duo):
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    a = _dummy(room, p, 150)
    b = _dummy(room, p, 330)
    for m in ('air_evo', 'crash_evo') + (('duo_bolt_bowl',) if duo else ()):
        mu.give(p, m)
    p.request_jump()
    tc.step(14)
    p.mouse_x, p.mouse_y = p.x, p.y - 300
    p.invuln_left = 0
    assert p.request_attack() and p.weapon.last_kind == 'plunge'
    top = a.y
    for _ in range(90):
        tc.step(1)
        top = max(top, a.y)
    return a, b, top


def test_bolt_bowl_flings_struck_enemies_sideways_into_others():
    a, b, top = _bolt(False)
    assert a.hp < a.max_hp and b.hp == b.max_hp                          # 낙뢰만: 반경 밖의 b는 멀쩡하다
    assert top > tc.FLOOR_Y + 10                                         # 그리고 a는 위로 뜬다
    a, b, top = _bolt(True)
    assert b.hp < b.max_hp                                               # 옆으로 날아간 a가 b를 들이받았다
    assert top < tc.FLOOR_Y + 40                                         # 볼링공은 높이 뜨지 않는다


def _focus(duo):
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    p.give_weapon('chain')
    chain_w = p.weapon
    p.give_weapon('pistol')
    e = _dummy(room, p, 150)
    for m in ('rapid_evo', 'gather_evo') + (('duo_focus_barrage',) if duo else ()):
        mu.give(p, m)
    import weapon
    game_world.add_object(weapon.Vortex(chain_w, 1.0), game_world.LAYER_EFFECT)
    tc.step(40)                                                           # 끌어모아 묶었다
    hp = e.hp
    pistol = p.weapon
    sx, sy = e.x + 360, e.center[1]
    game_world.add_object(weapon.Bullet(pistol, sx, sy, -0.82, 0.57, 7.0, False, pistol._fx(False), 1),
                          game_world.LAYER_EFFECT)                        # 왼쪽 35도 위로: 그대로 가면 빗나간다
    tc.step(30)
    return hp - e.hp


def test_focus_barrage_bends_bullets_into_vortex_bound_enemies():
    assert _focus(False) == 0
    assert _focus(True) > 0


def _counter(duo):
    room, p = tc.make_world()
    tc.set_gauge(p, 40)
    p.give_weapon('gauntlet')
    p.give_weapon('pistol')
    p.swap_weapon(1 - p.slot)                                             # 쌍권총은 다른 칸에, 건틀릿을 든다
    assert p.weapon.weapon_id == 'gauntlet'
    for m in ('counter_evo', 'dshot_evo') + (('duo_counter_ring',) if duo else ()):
        mu.give(p, m)
    e = _dummy(room, p, 200, hp=9999)
    e.state, e.attack_time = 'ATTACK', 0.0
    e.stats = dict(e.stats, windup=10.0)
    import weapon
    before = len(_bullets())
    weapon._counter_success(p, e, p.weapon)
    return len(_bullets()) - before


def test_counter_ring_fires_a_ring_of_bullets_from_the_other_pistol():
    assert _counter(False) == 0
    assert _counter(True) >= mu.DSHOT_RING[0]


def _world(second='gauntlet', gauge=50):
    room, p = tc.make_world(player_x=300.0)
    p.give_weapon(second)
    p.swap_weapon(0)
    tc.set_gauge(p, gauge)
    return room, p


def _storm(duo):
    room, p = _world()
    if duo:
        mu.give(p, 'duo_imprint_storm')
    a, near, far = _dummy(room, p, 120), _dummy(room, p, 120 + mu.DUO_STORM[0] - 60), _dummy(room, p, -700)
    p.weapon._hit(a, 10.0, 0.0, config.ZONE_FX['NORMAL'], extra=False)   # 철파이프 각인
    p.swap_weapon(1)
    hn, hf = near.hp, far.hp
    p.weapon._hit(a, 10.0, 0.0, config.ZONE_FX['NORMAL'], extra=False)   # 건틀릿으로 격발 (분쇄)
    tc.run_frames(5)
    return hn - near.hp, hf - far.hp


def test_imprint_storm_spreads_a_detonation_to_the_nearest_enemy_once():
    near, far = _storm(False)
    assert near == 0 and far == 0                                         # 분쇄는 그 적만
    near, far = _storm(True)
    assert near >= combo.detonate_damage(tc.make_world()[1]) * config.DETONATE_CRUSH * mu.DUO_STORM[1] * 0.9
    assert far == 0                                                       # 반경 밖, 그리고 한 번만 번진다


def _mist(duo, gauge):
    room, p = _world(gauge=gauge)
    if duo:
        mu.give(p, 'duo_swap_mist')
    p.swap_cool = 0.0
    p.swap_weapon(1)
    g0 = p.gauge.value
    assert combo.swap_strike(p)
    spent = g0 - p.gauge.value
    tc.step(int(mu.DUO_MIST[0] * 60) + 4)
    p.swap_weapon(0)
    again = combo.swap_strike(p)
    return spent, again, p


def test_swap_mist_shortens_the_swap_cooldown_for_gauge():
    spent, again, _p = _mist(False, 50)
    assert spent < 0.5 and not again                                      # 보통은 3초 쿨다운
    spent, again, p = _mist(True, 50)
    assert abs(spent - mu.DUO_MIST[1]) < 0.5 and again                    # 짧은 쿨다운, 대신 게이지가 준다
    spent, again, p = _mist(True, mu.DUO_MIST[2] - 1)
    assert spent < 0.5 and not again and p.gauge.zone != 'DEAD'           # 게이지가 모자라면 보통 쿨다운


def test_every_card_text_fits_the_card():
    """카드 설명은 13자씩 세 줄까지(그 아래는 갈래 칸·조건 글자), 합성의 조건 글자는 16자 한 줄, 진화는 두 줄까지 들어간다.
    2026-11-25 화면 확인: 교체 연무의 설명 넷째 줄이 조건 글자와 닿았다."""
    import mutation_mode
    p = tc.make_world()[1]
    for mid, m in mu.MUTATIONS.items():
        assert len(mutation_mode._wrap(m['desc'], 13)) <= 3, (mid, mutation_mode._wrap(m['desc'], 13))
        lines = len(mutation_mode._wrap(mu.card_info(p, mid)['note'], 16))
        if mu.tier(mid) == 'duo':
            assert lines == 1, (mid, mu.card_info(p, mid)['note'])           # 합성: 조건만 한 줄
        elif mu.tier(mid) == 'evo':
            assert lines <= 2, (mid, mu.card_info(p, mid)['note'])           # 진화: '무기 장착 시 적용 · 갈래 진화' 두 줄까지


# ===================== 2026-11-26 카드 뽑기: 든 무기만, 짝이 정해진 합성을 더 자주 =====================
def _loadout(first, second):
    p = tc.make_world()[1]
    p.set_loadout(first, second)
    return p


def test_cards_of_weapons_not_held_are_never_offered():
    """안 든 무기의 증강은 카드에 나오지 않는다 (사용자 결정: 고를 수 없는 카드를 없앤다). 철파이프도 들지 않았으면 나오지 않는다."""
    for held in (('pipe', 'pistol'), ('pistol', 'gauntlet'), ('gauntlet', 'chain')):
        p = _loadout(*held)
        rng = random.Random(7)
        for _ in range(300):
            for m in mu.offer(p, rng):
                weapon = mu.FAMILIES[mu.MUTATIONS[m]['family']].get('weapon')
                assert weapon is None or weapon in held, (held, m)
    p = _loadout('pistol', 'gauntlet')                     # 예전에 얻어 둔 다른 무기의 진화·합성도 특별 칸에 나오지 않는다
    for m in ('gather_more', 'gather_stun'):
        mu.give(p, m)
    rng = random.Random(8)
    assert not any(m == 'gather_evo' for _ in range(100) for m in mu.offer(p, rng))


def test_a_paired_duo_takes_the_special_card_before_the_any_two_duos():
    """짝이 정해진 합성이 열려 있으면 특별 칸은 그것이 먼저 차지한다 ('다른 무기의 진화 둘' 합성 두 종에 밀려 못 보는 일이 없게)."""
    p = _loadout('pipe', 'pistol')
    for m in ('combo_evo', 'dash_evo', 'rapid_evo'):       # 분신 연타(짝) + 각인 폭풍·교체 연무(아무 진화 둘)가 모두 열린다
        mu.give(p, m)
    assert all(mu.available(p, m) for m in ('duo_echo_combo', 'duo_imprint_storm', 'duo_swap_mist'))
    rng = random.Random(9)
    assert all('duo_echo_combo' in mu.offer(p, rng) for _ in range(40))


def test_the_partner_family_of_an_owned_evolution_weighs_more():
    """진화 하나를 가지면, 그 진화와 짝인 합성의 다른 갈래가 OFFER_PARTNER배 무겁게 나온다 (그 무기를 들고 있을 때만, 짝 진화를 얻기 전까지)."""
    p = _loadout('pipe', 'gauntlet')
    plain = mu._weight(p, 'crash_stun')
    mu.give(p, 'air_evo')                                  # 낙뢰 내려찍기 + 연쇄 충돌 = 볼링 내려찍기
    assert abs(mu._weight(p, 'crash_stun') - mu.OFFER_WEIGHTS['owned'] * mu.OFFER_PARTNER) < 1e-9
    assert mu._weight(p, 'crash_stun') > plain
    assert mu._weight(p, 'counter_power') == plain         # 짝이 아닌 갈래는 그대로
    mu.give(p, 'crash_evo')
    assert mu._weight(p, 'crash_stun') == mu.OFFER_WEIGHTS['owned']    # 짝 진화를 얻었으면 더 밀어 주지 않는다 (가진 갈래 무게)
    p = _loadout('pipe', 'gauntlet')
    mu.give(p, 'air_evo')
    rng = random.Random(10)
    boosted = sum(any(mu.MUTATIONS[m]['family'] == 'gauntlet_crash' for m in mu.offer(p, rng)) for _ in range(300))
    q = _loadout('pipe', 'gauntlet')
    rng = random.Random(10)
    normal = sum(any(mu.MUTATIONS[m]['family'] == 'gauntlet_crash' for m in mu.offer(q, rng)) for _ in range(300))
    assert boosted > normal * 1.5, (boosted, normal)


def test_an_evolution_card_names_its_duo_partner():
    """진화 카드 아래에는 합성의 짝(다른 진화의 이름)이 적힌다: 조합법을 카드에서 알 수 있게. 짝 무기를 들지 않았으면 예전 글 그대로."""
    p = _loadout('pipe', 'gauntlet')
    import mutation_mode
    note = mu.card_info(p, 'air_evo')['note']
    assert note == '합성 짝: 연쇄 충돌', note
    assert len(mutation_mode._wrap(note, 16)) == 1
    p = _loadout('pipe', 'pistol')
    assert mu.card_info(p, 'air_evo')['note'] == '공중 갈래 진화'           # 건틀릿이 없으면 볼링 내려찍기를 만들 수 없다
    p = _loadout('gauntlet', 'chain')                       # 소용돌이는 짝이 둘(헤이즈 붕괴·난사): 든 무기 쪽을 적는다
    assert mu.card_info(p, 'gather_evo')['note'] == '합성 짝: 헤이즈 붕괴'
    p = _loadout('pipe', 'gauntlet')
    mu.give(p, 'air_evo')
    assert mu.card_info(p, 'crash_stun')['hot']             # 짝 갈래의 기본 카드는 금색 안내로 눈에 띈다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
