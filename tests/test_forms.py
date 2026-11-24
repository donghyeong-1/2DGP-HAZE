"""무기 형태 (v8 계획 2절, 2026-11-25): 형태 카드를 얻으면 그 무기의 기본 공격 자체가 달라진다.
창 없이: python tests/test_forms.py

- 형태는 판 동안 유지되고(무기를 다시 주워도), 무기마다 하나다. 대시 공격·공중 공격·E 강화·궁극기는 그대로다.
- 철파이프 '중량 타격': 누르고 있으면 힘을 모아 크게 한 번(멀리 닿고, 띄운다), 짧게 누르면 느리고 센 베기.
- 쌍권총 '산탄': 가까이 5발 부채꼴, 쏠 때마다 반동으로 밀린다. 멀리는 닿지 않는다.
- 건틀릿 '연타': 짧게 누르면 빠른 잽(게이지 소모 없음), 세 번째 잽 뒤 누르고 있으면 돌진 강타로 이어진다.
- 사슬 '갈고리 이동': 적에게 걸면 적을 끌어오는 대신 내가 날아가 걷어찬다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import forms  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def world(wid='pipe', form=True, gauge=45):
    room, p = tc.make_world(player_x=400.0)
    if wid != 'pipe':
        p.give_weapon(wid)
    if form:
        forms.give(p, wid)
    tc.set_gauge(p, gauge)
    p.mouse_x, p.mouse_y = p.x + 600, p.center[1]
    return room, p


def enemy(room, p, dx, hp=10 ** 5):
    e = tc.freeze(tc.add_enemy('slum', p.x + dx, room, p))
    e.hp = e.max_hp = hp
    return e


def press(p, hold_frames=0, after=30):
    """공격을 누른다. hold_frames 동안 누르고 있다가 뗀 뒤 after 프레임을 더 돌린다."""
    p.weapon.cooldown = 0.0
    p.attack_held = True
    ok = p.request_attack()
    tc.run_frames(hold_frames)
    p.attack_held = False
    tc.run_frames(after)
    return ok


def base_pipe_hit():
    room, p = world(form=False)
    e = enemy(room, p, 110)
    press(p)
    return e.max_hp - e.hp


def test_a_form_stays_for_the_run_and_only_its_weapon_changes():
    room, p = world('gauntlet', form=False)
    assert not forms.active(p.weapon)
    assert forms.give(p, 'gauntlet') and forms.active(p.weapon)
    assert not forms.give(p, 'gauntlet')                                 # 무기마다 하나
    p.swap_weapon(0)
    assert not forms.active(p.weapon)                                    # 철파이프는 그대로
    p.give_weapon('chain')
    p.give_weapon('gauntlet')                                            # 다시 주워도 형태는 남는다
    assert forms.active(p.weapon)


def test_pipe_heavy_charged_blow_reaches_far_hits_hard_and_launches():
    base = base_pipe_hit()
    room, p = world()
    far = enemy(room, p, int(config.PIPE_REACH * 1.45))                  # 기본 베기로는 닿지 않는 거리
    press(p, hold_frames=int(config.FORM_HEAVY_CHARGE * 60) + 6, after=2)   # 떼자마자 나간다: 맞은 직후를 본다
    dealt = far.max_hp - far.hp
    assert dealt >= base * 2.0, (dealt, base)
    assert far.vy > 0 or far.y > tc.FLOOR_Y + 1                          # 띄운다


def test_pipe_heavy_short_press_is_a_slow_strong_cut():
    base = base_pipe_hit()
    room, p = world()
    e = enemy(room, p, 110)
    press(p, hold_frames=2, after=3)
    assert e.max_hp - e.hp > base * 1.2
    assert p.weapon.cooldown > config.PIPE_COOLDOWN[0]                   # 느리다


def test_pipe_keeps_its_base_combo_without_the_form():
    room, p = world(form=False)
    e = enemy(room, p, 110)
    press(p, hold_frames=40)
    assert not getattr(p.weapon, 'heavy', None)
    assert e.hp < e.max_hp


def test_pistol_shotgun_fires_five_close_pellets_with_recoil():
    room, p = world('pistol')
    near, far = enemy(room, p, 150), enemy(room, p, config.FORM_SHOTGUN_REACH + 260)
    x0 = p.x
    p.weapon.cooldown = 0.0
    assert p.request_attack()
    pellets = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Bullet']
    assert len(pellets) == config.FORM_SHOTGUN_PELLETS
    tc.run_frames(30)
    assert near.hp < near.max_hp and far.hp == far.max_hp                # 가까이만 닿는다
    assert p.x < x0 - 10                                                 # 반동으로 밀린다


def test_gauntlet_flurry_jabs_for_free_and_flows_into_a_rush():
    room, p = world('gauntlet')
    e = enemy(room, p, 100)
    g0 = p.gauge.value
    hp = e.hp
    for _ in range(2):
        press(p, hold_frames=1, after=14)
    assert e.hp < hp and not p.weapon.charging                           # 충전 없이 바로 친다
    assert p.gauge.value >= g0 - 0.5                                     # 게이지를 태우지 않는다 (적중 게이지는 오른다)
    p.weapon.cooldown = 0.0                                              # 세 번째 잽: 누르고 있으면 돌진 강타로
    p.attack_held = True
    assert p.request_attack()
    rushed = False
    for _ in range(40):
        tc.run_frames(1)
        # 돌진이 나갔다: 돌진 중이거나, 바로 앞의 적에게 이미 박아 건틀릿 쿨다운이 걸렸다
        rushed = rushed or p.weapon.rush is not None or p.weapon.cooldown_max >= config.GAUNTLET_COOLDOWN - 1e-6
    p.attack_held = False
    assert rushed


def test_chain_hook_travel_flies_me_to_the_enemy_instead_of_pulling_it():
    room, p = world('chain')
    e = enemy(room, p, 420)
    ex, hp = e.x, e.hp
    p.weapon.cooldown = 0.0
    assert p.request_attack()
    tc.run_frames(50)
    assert abs(p.x - e.x) < 150                                          # 내가 날아간다
    assert abs(e.x - ex) < 30                                            # 적은 끌려오지 않는다
    assert e.hp < hp                                                     # 걷어찬다


def test_forms_offer_only_weapons_in_hand_that_have_no_form_yet():
    room, p = world('chain', form=False)
    assert sorted(forms.offer(p)) == ['chain', 'pipe']
    forms.give(p, 'chain')
    assert forms.offer(p) == ['pipe']
    forms.give(p, 'pipe')
    assert forms.offer(p) == []


# ----- 형태 카드를 얻는 곳 (docs/plan_v8.md 2절): 구역의 첫 전투방 보상은 늘 형태 카드 -----
def _stage(seed=3):
    import test_stage as ts
    return ts.make_stage(seed=seed)


def test_the_first_combat_room_of_a_zone_always_rewards_a_form_card():
    stage, p = _stage()
    combat = [c for c in stage.layout if stage.type_of(c) == 'combat']
    with_form = [c for c in combat if stage.reward_of(c) == 'form']
    assert len(with_form) == 1
    sx, sy = stage.coord
    nearest = min(abs(c[0] - sx) + abs(c[1] - sy) for c in combat)
    c = with_form[0]
    assert abs(c[0] - sx) + abs(c[1] - sy) == nearest                    # 출발 방에서 가장 가까운 전투방


def test_the_form_reward_offers_the_weapons_in_hand_plus_skip():
    stage, p = _stage()
    p.give_weapon('chain')
    got = []
    stage.on_mutation = got.append
    stage.grant_reward('form')
    assert got and sorted(got[0]) == ['form:chain', 'form:pipe', 'form:skip']
    import mutation_mode
    mutation_mode.setup(p, got[0])
    mutation_mode.selected = got[0].index('form:chain')
    mutation_mode.choose()
    assert 'chain' in p.forms and 'pipe' not in p.forms
    shards = p.shards
    mutation_mode.selected = got[0].index('form:skip')                   # 넘기면 조각을 조금 받는다
    mutation_mode.choose()
    assert p.shards > shards and 'pipe' not in p.forms


def test_with_every_form_owned_the_reward_becomes_an_augment_choice():
    stage, p = _stage()
    forms.give(p, 'pipe')
    got = []
    stage.on_mutation = got.append
    stage.grant_reward('form')
    assert got and not any(str(c).startswith('form:') for c in got[0])   # 증강 셋으로 대신한다


def test_a_form_makes_its_matching_augment_families_show_up_more():
    import mutations
    room, p = world('pipe', form=False)
    mid = next(m for m, v in mutations.MUTATIONS.items() if v['family'] == forms.MATCH['pipe'][0])
    before = mutations._weight(p, mid)
    forms.give(p, 'pipe')
    assert abs(mutations._weight(p, mid) - before * forms.MATCH_WEIGHT) < 1e-9


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
