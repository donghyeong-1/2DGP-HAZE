"""두 무기 조합 (v8 계획 1절, 2026-11-24): 각인과 격발, 교체기.
창 없이: python tests/test_combo.py

각인과 격발 (docs/plan_v8.md 1-3):
- 무기 둘을 들고 있을 때, 무기로 맞힌 적에게 그 무기의 각인이 IMPRINT_TIME 동안 남는다 (적마다 하나).
- 같은 무기로 다시 치면 시간만 새로 고친다. **다른 무기**로 치면 격발: 추가 피해 + 터뜨린 무기에 따른 효과, 각인은 사라진다.
- 격발된 적은 IMPRINT_LOCK 동안 다시 각인되지 않는다. 격발하면 게이지 +DETONATE_GAUGE.
- 격발 효과: 철파이프 = 다른 각인 적에게 베기가 튄다 / 쌍권총 = 둘레에 작은 폭발, 각인을 옮긴다 /
  건틀릿 = 큰 피해 + 띄움 / 사슬 = 각인된 적 모두를 터뜨린 적 쪽으로 끌어모은다.
- 무기가 하나뿐이면 각인하지 않는다 (섞을 것이 없다).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import combo  # noqa: E402
import config  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def world(second='gauntlet', gauge=50):
    room, p = tc.make_world(player_x=300.0)
    if second:
        p.give_weapon(second)
        p.swap_weapon(0)
    tc.set_gauge(p, gauge)
    return room, p


def enemy(room, p, dx, hp=10 ** 5):
    e = tc.freeze(tc.add_enemy('slum', p.x + dx, room, p))
    e.hp = e.max_hp = hp
    return e


def hit(p, e, damage=10.0):
    """지금 든 무기로 적을 한 번 맞힌다 (판정을 거치지 않고 맞는 처리만)."""
    return p.weapon._hit(e, damage, 0.0, config.ZONE_FX['NORMAL'], extra=False)


def test_a_hit_leaves_the_weapons_imprint_and_the_same_weapon_only_refreshes_it():
    room, p = world()
    e = enemy(room, p, 120)
    hit(p, e)
    assert combo.imprint_of(e) == 'pipe'
    tc.run_frames(60)
    left = e.imprint_left
    assert 0 < left < config.IMPRINT_TIME - 0.9
    hp = e.hp
    hit(p, e)
    assert combo.imprint_of(e) == 'pipe' and e.imprint_left > left      # 같은 무기: 시간만 새로
    assert abs((hp - e.hp) - 10.0) < 1e-6                                # 격발은 아니다


def test_the_other_weapon_detonates_the_imprint():
    room, p = world()
    e = enemy(room, p, 120)
    hit(p, e)
    p.swap_weapon(1)
    hp, g0 = e.hp, p.gauge.value
    hit(p, e)
    assert combo.imprint_of(e) is None                                   # 각인은 터져 사라진다
    assert (hp - e.hp) - 10.0 >= combo.detonate_damage(p) - 1e-6         # 추가 피해
    assert p.gauge.value >= g0 + config.DETONATE_GAUGE - 1e-6
    hit(p, e)
    assert combo.imprint_of(e) is None                                   # 잠깐은 다시 각인되지 않는다
    tc.run_frames(int(config.IMPRINT_LOCK * 60) + 5)
    hit(p, e)
    assert combo.imprint_of(e) == 'gauntlet'


def test_an_imprint_fades_after_its_time():
    room, p = world()
    e = enemy(room, p, 120)
    hit(p, e)
    tc.run_frames(int(config.IMPRINT_TIME * 60) + 5)
    assert combo.imprint_of(e) is None
    p.swap_weapon(1)
    hp = e.hp
    hit(p, e)
    assert abs((hp - e.hp) - 10.0) < 1e-6                                # 사라진 각인은 터지지 않는다 (새 각인이 될 뿐)
    assert combo.imprint_of(e) == 'gauntlet'


def test_one_weapon_alone_does_not_imprint():
    room, p = world(second=None)
    e = enemy(room, p, 120)
    hit(p, e)
    assert combo.imprint_of(e) is None


def test_pipe_detonation_sends_a_cut_to_every_other_imprinted_enemy():
    room, p = world('pistol')
    a, b, c = enemy(room, p, 120), enemy(room, p, 420), enemy(room, p, -380)
    p.swap_weapon(1)
    for e in (a, b):
        hit(p, e)                                                        # 쌍권총 각인 둘 (c는 각인 없음)
    p.swap_weapon(0)
    hb, hc = b.hp, c.hp
    hit(p, a)                                                            # 철파이프로 격발
    tc.run_frames(20)
    assert hb - b.hp >= combo.detonate_damage(p) - 1e-6                   # 각인된 다른 적에게 베기가 튄다
    assert c.hp == hc                                                    # 각인 없는 적은 그대로
    assert combo.imprint_of(b) == 'pistol'                               # 튄 베기는 그 적의 각인을 터뜨리지 않는다


def test_pistol_detonation_bursts_and_passes_the_imprint_to_neighbours():
    room, p = world('pistol')
    a, near, far = enemy(room, p, 140), enemy(room, p, 230), enemy(room, p, 700)
    hit(p, a)                                                            # 철파이프 각인
    p.swap_weapon(1)
    hn, hf = near.hp, far.hp
    hit(p, a)                                                            # 쌍권총으로 격발
    tc.run_frames(5)
    assert near.hp < hn and combo.imprint_of(near) == 'pistol'           # 둘레의 적: 폭발 피해 + 각인이 옮는다
    assert far.hp == hf and combo.imprint_of(far) is None


def test_gauntlet_detonation_hits_harder_and_launches():
    room, p = world('gauntlet')
    e = enemy(room, p, 120)
    hit(p, e)
    p.swap_weapon(1)
    hp = e.hp
    hit(p, e)
    assert (hp - e.hp) - 10.0 >= combo.detonate_damage(p) * config.DETONATE_CRUSH - 1e-6
    assert e.vy > 0                                                      # 뜬다


def test_chain_detonation_gathers_every_imprinted_enemy():
    room, p = world('chain')
    a, b, c = enemy(room, p, 160), enemy(room, p, 520), enemy(room, p, -420)
    for e in (a, b, c):
        hit(p, e)                                                        # 철파이프 각인 셋
    p.swap_weapon(1)
    db, dc = abs(b.x - a.x), abs(c.x - a.x)
    hit(p, a)                                                            # 사슬로 격발
    tc.run_frames(40)
    assert abs(b.x - a.x) < db - 150 and abs(c.x - a.x) < dc - 150       # 터뜨린 적 쪽으로 끌려온다


def test_a_boss_is_not_dragged_or_launched_but_still_takes_the_burst():
    room, p = world('gauntlet')
    e = enemy(room, p, 120)
    e.pullable = False
    hit(p, e)
    p.swap_weapon(1)
    hp = e.hp
    hit(p, e)
    assert hp - e.hp > 10.0 and e.vy <= 0


# ----- 교체기 (docs/plan_v8.md 1-2): 무기를 바꾸는 순간 들어오는 무기의 기술이 나간다 -----
def press_swap(p, index=None):
    """플레이어가 직접 바꾼다 (Tab·1·2). 줍거나 불러올 때의 교체와 달리 교체기가 나간다."""
    return p.swap_weapon(index, strike=True)


def test_swapping_to_the_pipe_draws_a_wide_cut_and_starts_the_cooldown():
    room, p = world('gauntlet')
    p.swap_weapon(1)                                                     # 건틀릿을 든 채로 시작
    e = enemy(room, p, 150)
    hp = e.hp
    assert press_swap(p, 0)                                              # 철파이프로: 발도 베기
    tc.run_frames(12)
    assert e.hp < hp
    assert abs(p.swap_cool - config.SWAP_COOLDOWN) < 0.3                 # 쿨다운이 돈다
    hp = e.hp
    press_swap(p, 1)
    tc.run_frames(12)
    assert e.hp == hp and p.weapon.weapon_id == 'gauntlet'               # 쿨 중에는 그냥 바뀌기만 한다


def test_picking_up_or_loading_a_weapon_does_not_fire_the_swap_strike():
    room, p = world(second=None)
    e = enemy(room, p, 150)
    hp = e.hp
    p.give_weapon('gauntlet')
    tc.run_frames(12)
    assert e.hp == hp and getattr(p, 'swap_cool', 0.0) == 0.0


def test_swapping_to_the_pistols_hops_back_and_shoots():
    room, p = world('pistol')
    e = enemy(room, p, 260)
    x0, hp = p.x, e.hp
    assert press_swap(p, 1)
    tc.run_frames(20)
    assert p.x < x0 - 20                                                 # 조준 반대쪽으로 물러난다
    assert e.hp < hp


def test_swapping_to_the_gauntlet_uppercuts_and_launches():
    room, p = world('gauntlet')
    e = enemy(room, p, 110)
    hp = e.hp
    assert press_swap(p, 1)
    assert e.hp < hp and e.vy > 0


def test_swapping_to_the_chain_yanks_the_nearest_enemy_in():
    room, p = world('chain')
    near, far = enemy(room, p, 380), enemy(room, p, 480)
    hp, far_x = near.hp, far.x
    assert press_swap(p, 1)
    tc.run_frames(30)
    assert abs(near.x - p.x) < 130 and near.hp < hp                      # 가장 가까운 적 하나가 끌려와 맞는다
    assert abs(far.x - far_x) < 5


def test_a_swap_strike_detonates_the_other_weapons_imprint_and_refunds_cooldown():
    room, p = world('gauntlet')
    e = enemy(room, p, 110)
    hit(p, e)                                                            # 철파이프 각인
    hp = e.hp
    assert press_swap(p, 1)                                              # 건틀릿 올려치기가 그 각인을 터뜨린다
    assert combo.imprint_of(e) is None
    assert hp - e.hp >= combo.detonate_damage(p) * config.DETONATE_CRUSH
    assert p.swap_cool <= config.SWAP_COOLDOWN - config.DETONATE_SWAP_REFUND + 1e-6


def test_the_swap_cooldown_runs_down_and_the_strike_returns():
    room, p = world('gauntlet')
    e = enemy(room, p, 110)
    assert press_swap(p, 1)
    tc.run_frames(int(config.SWAP_COOLDOWN * 60) + 10)
    assert p.swap_cool == 0.0
    hp = e.hp
    e.x = p.x + 150
    assert press_swap(p, 0)
    tc.run_frames(12)
    assert e.hp < hp


# ----- 두 칸 자유 (docs/plan_v8.md 1-1): 철파이프 고정 해제 -----
def test_a_found_weapon_fills_the_empty_slot_then_replaces_the_one_not_in_hand():
    room, p = world(second=None)
    p.give_weapon('gauntlet')
    assert [w.weapon_id for w in p.weapons] == ['pipe', 'gauntlet'] and p.weapon.weapon_id == 'gauntlet'   # 빈 칸에 넣고 든다
    p.give_weapon('chain')                                               # 두 칸이 찼다: 들고 있지 않은 철파이프와 바뀐다
    assert [w.weapon_id for w in p.weapons] == ['chain', 'gauntlet'] and p.weapon.weapon_id == 'chain'
    p.swap_weapon(1)
    p.give_weapon('pistol')                                              # 건틀릿을 들고 있다: 사슬과 바뀐다
    assert [w.weapon_id for w in p.weapons] == ['pistol', 'gauntlet'] and p.weapon.weapon_id == 'pistol'
    p.give_weapon('gauntlet')                                            # 이미 가진 무기: 그것을 들 뿐
    assert [w.weapon_id for w in p.weapons] == ['pistol', 'gauntlet'] and p.weapon.weapon_id == 'gauntlet'


def test_a_run_without_the_pipe_fights_and_combos_normally():
    import mutations
    room, p = tc.make_world(player_x=300.0)
    p.set_loadout('gauntlet', 'chain')
    assert [w.weapon_id for w in p.weapons] == ['gauntlet', 'chain']
    tc.set_gauge(p, 50)
    e = enemy(room, p, 120)
    p.swap_weapon(0)
    hit(p, e)
    assert combo.imprint_of(e) == 'gauntlet'
    p.swap_weapon(1)
    hit(p, e)
    assert combo.imprint_of(e) is None                                   # 사슬로 격발
    mutations.on_plunge_land(p)                                          # 철파이프 전용 낙뢰는 철파이프가 없으면 아무 일도 없다 (오류 없이)


# ----- O5 강화 교체기 (2026-11-26, docs/plan_v8.md 3절, docs/opus/TASKS.md) -----
def _ready(p, level):
    p.gauge.enhance_level = level
    p.gauge.enhance_timer = 5.0


def _uppercut_damage(level, cooldown=False):
    """건틀릿 올려치기(바로 맞는다) 한 번의 피해와 쓰고 난 강화 단계."""
    room, p = world('gauntlet')
    e = enemy(room, p, 110)
    if level:
        _ready(p, level)
    if cooldown:
        p.swap_cool = 1.0
    hp = e.hp
    press_swap(p, 1)
    return hp - e.hp, p.gauge.enhance_level, p, room, e


def test_enhanced_swap_strike_hits_one_and_a_half_or_two_times_harder():
    plain, _, _, _, _ = _uppercut_damage(0)
    one, left1, _, _, _ = _uppercut_damage(1)
    two, left2, _, _, _ = _uppercut_damage(2)
    assert plain > 0
    assert abs(one - plain * config.SWAP_ENHANCE_MULT[1]) < 1e-6 and config.SWAP_ENHANCE_MULT[1] == 1.5
    assert abs(two - plain * config.SWAP_ENHANCE_MULT[2]) < 1e-6 and config.SWAP_ENHANCE_MULT[2] == 2.0
    assert left1 == 0 and left2 == 0                                    # 쌓인 강화 단계를 모두 쓴다


def test_third_stage_keeps_the_ultimate_and_swaps_normally():
    plain, _, _, _, _ = _uppercut_damage(0)
    three, left, _, _, _ = _uppercut_damage(3)
    assert abs(three - plain) < 1e-6 and left == 3                      # 궁극기를 실수로 날리지 않는다


def test_a_swap_on_cooldown_does_not_spend_the_enhance():
    dealt, left, p, _, _ = _uppercut_damage(2, cooldown=True)
    assert dealt == 0 and left == 2 and p.weapon.weapon_id == 'gauntlet'


def test_enhanced_swap_spreads_the_incoming_imprint_around_the_target():
    for level, want in ((0, None), (1, 'gauntlet')):
        room, p = world('gauntlet')
        a = enemy(room, p, 110)
        b = enemy(room, p, 110 + 190)                                    # a에서 190px (220 안), 올려치기 사거리 밖
        if level:
            _ready(p, level)
        hp = b.hp
        press_swap(p, 1)
        assert b.hp == hp                                                # b는 맞지 않았다
        assert combo.imprint_of(b) == want, level                        # 강화 교체기면 들어오는 무기의 각인이 묻는다


def test_enhanced_swap_shows_the_enhanced_name_in_the_stage_color():
    room, p = world('gauntlet')
    enemy(room, p, 110)
    _ready(p, 2)
    press_swap(p, 1)
    texts = [o for o in game_world.world[game_world.LAYER_EFFECT] if getattr(o, 'text', None) == '강화 ' + combo.STRIKE_NAMES['gauntlet']]
    assert texts and tuple(texts[0].color) == tuple(config.ENHANCE_LEVEL_COLOR[2])


def test_enhanced_pistol_and_chain_swaps_also_hit_harder():
    for wid, dx, frames in (('pistol', 260, 20), ('chain', 380, 30)):
        dealt = []
        for level in (0, 2):
            room, p = world(wid)
            e = enemy(room, p, dx)
            if level:
                _ready(p, level)
            hp = e.hp
            press_swap(p, 1)
            tc.run_frames(frames)
            dealt.append(hp - e.hp)
        assert dealt[0] > 0 and dealt[1] > dealt[0] * 1.5, (wid, dealt)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
