"""실루엣 컷인 테스트 (창 없이). 실행: python tests/test_cut_in.py

O1 (2026-11-26, docs/opus/TASKS.md):
- cut_in.play(color, actors, word): 화면을 한 색으로 덮고 검은 실루엣만 움직이는 0.7초 연출. 한 번에 하나만, 도는 동안 게임이 멈춘다.
- 보스가 페이즈를 바꿀 때(크래셔·아크·문지기·헤이즈 심장) 한 번씩.
- 새 증강 '궁극기 각성'(강화 갈래 진화): 궁극기 피해 x1.4, 보스 상한 20%, 시전할 때 컷인. 없으면 궁극기는 그대로.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))

import config  # noqa: E402
import cut_in  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import mutations  # noqa: E402

DT = 1 / 60
RED = (230, 80, 60)


def fresh():
    game_world.clear()
    effects.reset()
    cut_in.reset()


def run(seconds):
    for _ in range(int(round(seconds / DT))):
        cut_in.update(DT)


# ----- 컷인 자체 -----
def test_play_lasts_point_seven_seconds_and_ignores_a_second_request():
    fresh()
    ended = []
    assert cut_in.play(RED, [], word='분노', on_end=lambda: ended.append(1))
    assert cut_in.running()
    assert not cut_in.play((0, 0, 255), [], word='각성')           # 도는 중이면 새 요청은 무시
    assert cut_in.current().word == '분노'
    run(0.65)
    assert cut_in.running() and not ended
    run(0.1)
    assert not cut_in.running() and ended == [1]                  # 0.7초 뒤 끝나고 이어서 할 일을 부른다
    assert cut_in.DURATION <= 0.8


def test_switch_off_does_nothing():
    fresh()
    old = config.CUT_IN
    try:
        config.CUT_IN = False
        assert not cut_in.play(RED, [], word='분노')
        assert not cut_in.running()
    finally:
        config.CUT_IN = old


def test_timeline_has_flash_hold_and_close():
    fresh()
    cut_in.play(RED, [], word='분노')
    c = cut_in.current()
    assert c.phase() == 'in'
    run(0.2)
    assert c.phase() == 'hold'
    run(0.35)
    assert c.phase() == 'close'
    a = cut_in.slide(0.1)
    b = cut_in.slide(0.3)
    assert 0 <= a < b <= 1.0 and a > 0.4                           # 빠르게 시작해 느려진다


def test_game_is_frozen_while_the_cut_in_runs():
    """컷인이 도는 동안 play_mode.update가 세계를 갱신하지 않는다: 적이 움직이지 않고 플레이어가 맞지 않는다."""
    import boss_intro
    import game_framework
    import play_mode
    import stage as stage_mod
    import zone_card
    from player import Player
    fresh()
    boss_intro.reset_all()
    zone_card.freezing = zone_card.showing = False
    old = config.BOSS_INTRO
    try:
        config.BOSS_INTRO = False
        p = Player(0, 0, None)
        game_world.add_object(p, game_world.LAYER_PLAYER)
        st = stage_mod.Stage(p, name='stage2', seed=1)
        st.start()
        st.enter_room(stage_mod.boss_room(st), 'L')
        boss = st.boss
        play_mode.stage, play_mode.player, play_mode.room = st, p, st.room
        game_framework.frame_time = DT
        for _ in range(5):
            play_mode.update()
        boss.x = p.x + 60                                          # 바로 앞에서 공격을 시작하려는 보스
        boss.cooldown = 0.0
        hp, bx, t = p.hp, boss.x, boss.anim_time
        assert cut_in.play(RED, [], word='분노')
        for _ in range(int(0.6 / DT)):
            play_mode.update()
        assert boss.x == bx and boss.anim_time == t and p.hp == hp
        for _ in range(10):
            play_mode.update()
        assert not cut_in.running() and boss.anim_time != t        # 끝나면 그대로 이어진다
    finally:
        config.BOSS_INTRO = old
        game_world.clear()


# ----- 보스 페이즈 전환 -----
def arena(make_boss):
    import balance_sim
    from player import Player
    fresh()
    room = balance_sim.arena()
    floor = float(2 * config.TILE)
    p = Player(6 * config.TILE, floor, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    boss = make_boss(room, p, floor)
    game_world.add_object(boss, game_world.LAYER_ENEMY)
    p.hp = p.max_hp = 10 ** 6
    return room, p, boss


def step(n=1):
    for _ in range(n):
        effects.hit_stop_left = 0.0
        effects.slow_left = 0.0
        game_world.update(DT)


def finish():
    while cut_in.running():
        cut_in.update(DT)


def test_crasher_phase2_requests_one_cut_in():
    from boss import Boss
    room, p, b = arena(lambda room, p, floor: Boss(p.x + 600, floor, room, p))
    b.cooldown = 99.0
    b.hp = b.max_hp / 2 - 1
    step()
    assert b.phase == 2 and cut_in.history == ['분노']
    finish()
    b._enter_phase2()                                              # 같은 페이즈로 또 불려도 한 번만
    assert cut_in.history == ['분노']


def test_ark_phases_request_one_cut_in_each():
    from ark import Ark
    room, p, a = arena(lambda room, p, floor: Ark(p.x + 600, floor, room, p))
    a.cooldown = 99.0
    a.hp = a.max_hp * config.ARK_PHASES[0] - 1
    step()
    finish()
    a.hp = a.max_hp * config.ARK_PHASES[1] - 1
    step()
    finish()
    assert a.phase == 3 and cut_in.history == ['각성', '폭주']
    a._enter_phase(3, '폭주')
    assert cut_in.history == ['각성', '폭주']


def test_gatekeeper_phase2_requests_one_cut_in():
    from gatekeeper import Gatekeeper
    room, p, g = arena(lambda room, p, floor: Gatekeeper(p.x + 600, floor, room, p))
    g.cooldown = 99.0
    g.hp = g.max_hp / 2 - 1
    step()
    assert g.phase == 2 and cut_in.history == ['비상']
    finish()
    g._enter_phase2()
    assert cut_in.history == ['비상']


def test_heart_phases_request_one_cut_in_each():
    import heart as hm
    from player import Player
    from room import Room
    fresh()
    room = Room.load('boss_arena', ('L',))
    p = Player(12 * config.TILE, 2 * config.TILE + 5, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    step(20)
    p.hp = p.max_hp = 10 ** 6
    core = hm.spawn(room, p)
    core.cooldown = 99.0
    step(int(config.HEART['intro'] * 60) + 3)
    a, b = config.HEART['phases']
    core.hp = core.max_hp * a - 1
    step()
    finish()
    core.hp = core.max_hp * b - 1
    step()
    finish()
    assert core.phase == 3 and cut_in.history == ['맥동', '범람']
    assert cut_in.colors[-1] == cut_in.BOSS_COLORS['heart3']      # 심장 3페이즈는 진홍


# ----- 궁극기 각성 -----
def test_ult_awaken_is_a_tide_evolution_that_needs_two_tide_cards():
    m = mutations.MUTATIONS['ult_awaken']
    assert m['family'] == 'tide' and m['tier'] == 'evo' and m['ready']
    assert mutations.evolution_of('tide') == 'ult_awaken'

    class P:
        mutations = []
        weapons = []
    p = P()
    assert not mutations.available(p, 'ult_awaken')
    p.mutations = ['tide_cost']
    assert not mutations.available(p, 'ult_awaken')
    p.mutations = ['tide_cost', 'tide_chain']
    assert mutations.available(p, 'ult_awaken') and mutations.offerable(p, 'ult_awaken')
    info = mutations.card_info(p, 'ult_awaken')
    assert len(info['note']) <= 16, info['note']


def _ult_dealt(wid, awaken, boss=False):
    import test_ultimate as tu
    room, p, _ = tu.stacked(99 if boss else 90, 3, [] if boss else [300])
    foes = [o for o in game_world.world[game_world.LAYER_ENEMY]]
    if wid != 'pipe':
        tu.give(p, wid)
    if awaken:
        p.mutations = list(getattr(p, 'mutations', [])) + ['tide_cost', 'tide_chain', 'ult_awaken']
    target = foes[0] if foes else None
    if boss:
        from boss import Boss
        tu.tc.set_gauge(p, 99)
        target = Boss(p.x + 250, tu.FLOOR, room, p)
        target.stats = dict(target.stats, speed=0.0, sight=0)
        target.cooldown = 99.0
        game_world.add_object(target, game_world.LAYER_ENEMY)
        p.attack_bonus = 50.0
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    assert p.request_attack()
    if awaken:
        assert cut_in.running() and not tu.ultimates()            # 컷인이 끝난 뒤 궁극기가 나간다
        assert cut_in.current().word == __import__('weapon').ULT_NAMES[wid]
        finish()
    else:
        assert not cut_in.running()
    assert tu.ultimates()
    tu.run_out_ultimate()
    tu.tc.step(20)
    return target.max_hp - target.hp, target.max_hp


def test_ult_awaken_multiplies_damage_and_raises_the_boss_cap():
    fresh()
    for wid in ('pipe', 'pistol'):
        plain, _ = _ult_dealt(wid, False)
        fresh()
        strong, _ = _ult_dealt(wid, True)
        fresh()
        assert abs(strong - plain * config.ULT_AWAKEN_MULT) < 1e-3, (wid, plain, strong)
    dealt, max_hp = _ult_dealt('pipe', True, boss=True)
    assert config.ULT_BOSS_CAP * max_hp < dealt <= config.ULT_AWAKEN_BOSS_CAP * max_hp + 1e-6
    assert config.ULT_AWAKEN_MULT == 1.4 and config.ULT_AWAKEN_BOSS_CAP == 0.20


def test_without_the_mutation_the_ultimate_is_unchanged():
    fresh()
    dealt, max_hp = _ult_dealt('pipe', False, boss=True)
    assert dealt <= config.ULT_BOSS_CAP * max_hp + 1e-6
    assert cut_in.history == []


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
