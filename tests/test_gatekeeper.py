"""구역 1 중간 보스 '문지기' 테스트 (창 없이). 실행: python tests/test_gatekeeper.py

v8 6일 차 대기열 1 (docs/NEXT_SESSION.md 4절, plan_v8 6절): 구역 1 끝의 관문 정예 전투를 중간 보스로.
- 관문 방(gate)에 들어서면 문지기 하나가 보스로 선다(stage.boss, 체력 바·등장씬). 방은 새 관문 경기장(gate_arena).
- 패턴 셋: 방패 돌진(멀면, 벽에 부딪히면 멈추고 빈틈) / 내려찍기(가까우면, 큰 한 방 + 양옆 충격파, 맞으면 게이지 +15 = 간수 규칙) /
  증원 호출(슬럼 폐인·사냥개를 부른다, 살아 있는 증원은 최대 3).
- 같은 패턴을 연달아 쓰지 않는다. 경직되지 않고 사슬에 묶이지 않는다(보스).
- 체력 절반: 2페이즈 = 바로 증원 호출, 예고가 짧아지고 돌진은 되돌아 한 번 더. 한 줄 대사.
- 쓰러지면 증원도 흩어지고 관문이 열린다(구역 끝). config.GATEKEEPER를 끄면 예전 정예 전투.
- 그림은 간수 그림을 도구로 구운 것(tools/make_gatekeeper.py): 실행 중 확대하지 않는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))

from PIL import Image  # noqa: E402

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
from player import Player  # noqa: E402

DT = 1 / 60
UNI = os.path.join(HERE, '..', 'assets', 'sprites', 'unified')


def step(n=1):
    for _ in range(n):
        effects.hit_stop_left = 0.0
        effects.slow_left = 0.0
        game_world.update(DT)


def fight(gap=700.0):
    """평평한 시험장에 플레이어와 문지기. 문지기는 공격하지 않게 쿨다운을 길게 둔다(테스트가 직접 패턴을 시킨다)."""
    import balance_sim
    import boss_intro
    import gatekeeper
    game_world.clear()
    effects.reset()
    boss_intro.reset_all()
    room = balance_sim.arena()
    floor = float(2 * config.TILE)
    p = Player(6 * config.TILE, floor, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    g = gatekeeper.Gatekeeper(p.x + gap, floor, room, p)
    g.cooldown = 99.0
    game_world.add_object(g, game_world.LAYER_ENEMY)
    step(20)
    assert p.on_ground and g.on_ground
    p.hp = p.max_hp = 10 ** 6
    p.invuln_left = 0.0
    p.gauge.value = 50.0
    p.gauge.zone = p.gauge._zone_of(50.0)
    return room, p, g


def do(g, move):
    g.cooldown = 0.0
    g.move = move
    g.engage()


def adds():
    import gatekeeper
    return [o for o in game_world.world[game_world.LAYER_ENEMY] if getattr(o, 'alive', False)
            and not isinstance(o, gatekeeper.Gatekeeper)]


# ----- 그림 -----
def test_sprites_are_registered_with_binary_alpha_and_sit_between_guard_and_crasher():
    """2026-11-25 Codex T50 그림(키 165px)으로 교체: 간수(134)보다 크고 크래셔(194)보다 작다."""
    import sprites
    for name in ('idle', 'walk', 'heavy', 'bash', 'call', 'hurt', 'death'):
        key = f'boss_gatekeeper_{name}'
        assert key in sprites.FRAMES, key
        count = sprites.FRAMES[key][0]
        for n in range(1, count + 1):
            im = Image.open(os.path.join(UNI, f'{key}_{n}.png')).convert('RGBA')
            assert im.size == (360, 284)
            assert {a for *_, a in im.getdata()} <= {0, 255}
    g = Image.open(os.path.join(UNI, 'v6_guard_idle_1.png')).convert('RGBA').getbbox()
    k = Image.open(os.path.join(UNI, 'boss_gatekeeper_idle_1.png')).convert('RGBA').getbbox()
    c = Image.open(os.path.join(UNI, 'boss_crasher_idle_1.png')).convert('RGBA').getbbox()
    assert (g[3] - g[1]) < (k[3] - k[1]) == 165 < (c[3] - c[1])
    assert config.ENEMY_STATS['gatekeeper']['hb'][1] <= 165             # 판정이 그림보다 크지 않다


# ----- 관문 방 -----
def gate_stage(seed=1):
    import boss_intro
    import stage as stage_mod
    game_world.clear()
    effects.reset()
    boss_intro.reset_all()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    st = stage_mod.Stage(p, name='stage1', seed=seed)
    st.start()
    coord = stage_mod.boss_room(st)
    st.enter_room(coord, 'L')
    return st, p


def test_gate_room_has_gatekeeper_as_boss():
    for seed in (1, 2, 3):
        st, p = gate_stage(seed)
        assert st.type_of(st.coord) == 'gate' and st.template_of(st.coord) == 'gate_arena'
        assert st.boss is not None and st.boss.kind == 'gatekeeper' and st.boss.title == '문지기'
        assert st.room.locked and st.enemy_count() == 1


def test_switch_off_keeps_old_elite_gate():
    old = config.GATEKEEPER
    try:
        config.GATEKEEPER = False
        st, p = gate_stage()
        assert st.boss is None and st.enemy_count() >= 2
        kinds = {o.kind for o in game_world.world[game_world.LAYER_ENEMY]}
        assert kinds <= {'guard', 'hound'}
    finally:
        config.GATEKEEPER = old


def test_killing_gatekeeper_clears_gate_and_ends_zone():
    st, p = gate_stage()
    g = st.boss
    g.call_adds()
    assert len(adds()) == 2 and st.enemy_count() == 3
    g.take_damage(10 ** 6)
    assert not adds()                                              # 증원도 흩어진다
    st.update()
    assert st.coord in st.cleared and not st.room.locked
    for _ in range(200):
        st.update()
    assert st.finished and p.shards >= config.SHARDS_PER_KILL['gatekeeper']


# ----- 패턴 -----
def test_first_pattern_and_no_repeat():
    room, p, g = fight(gap=120.0)
    assert g._pick_move(120.0, 0.0) == 'slam'                      # 가까우면 첫 공격은 내려찍기
    room, p, g = fight(gap=600.0)
    assert g._pick_move(600.0, 0.0) == 'charge'                    # 멀면 첫 공격은 방패 돌진
    g.attacks, g.last_move = 3, 'charge'
    picks = {g._pick_move(600.0, 0.0) for _ in range(30)}
    assert 'charge' not in picks and picks                        # 같은 패턴을 연달아 쓰지 않는다


def test_shield_charge_runs_hits_once_and_stops_at_wall():
    room, p, g = fight(gap=700.0)
    hp = p.hp
    x0 = g.x
    do(g, 'charge')
    step(int(g._windup_time() * 60) - 2)
    assert abs(g.x - x0) < 4                                       # 예고 중에는 서 있다
    p.invuln_left = 0.0
    step(int(g._active_time() * 60) + 30)
    assert g.x < x0 - 300                                          # 플레이어 쪽으로 달려왔다
    assert p.hp == hp - config.ENEMY_STATS['gatekeeper']['charge_damage']   # 몸통 박치기는 한 번만
    room, p, g = fight(gap=700.0)
    p.x = 2 * config.TILE                                          # 플레이어는 벽 바로 앞: 문지기가 벽에 부딪힌다
    p.y += 400                                                     # (돌진을 맞지 않게 공중에 띄워 둔다)
    do(g, 'charge')
    for _ in range(300):
        step()
        if g.stunned_left > 0:
            break
    assert g.stunned_left > 0                                      # 벽에 부딪히면 잠깐 빈틈


def test_slam_hits_hard_adds_gauge_and_sends_shockwaves():
    import projectile
    room, p, g = fight(gap=150.0)
    p.invuln_left = 0.0
    hp, gauge = p.hp, p.gauge.value
    do(g, 'slam')
    step(int(g._windup_time() * 60) + 3)
    waves = [o for o in game_world.world[game_world.LAYER_EFFECT] if isinstance(o, projectile.Shockwave)]
    assert len(waves) == 2
    assert p.hp < hp
    assert p.gauge.value > gauge                                   # 간수 규칙: 맞으면 게이지가 오른다 (+15, 피격 -5)


def test_call_brings_reinforcements_up_to_limit():
    room, p, g = fight()
    do(g, 'call')
    step(int(g._windup_time() * 60) + 3)
    got = adds()
    assert len(got) == config.GATEKEEPER_CALL['count']
    assert {a.kind for a in got} <= set(config.GATEKEEPER_CALL['kinds'])
    g.call_adds()
    assert len(adds()) == config.GATEKEEPER_CALL['max_adds']       # 살아 있는 증원은 최대 3
    g.attacks, g.last_move, g.since_call = 3, 'slam', 0.0
    assert g._pick_move(600.0, 0.0) != 'call'                      # 꽉 찼거나 막 불렀으면 부르지 않는다


def test_no_stagger_and_no_chain_hold():
    room, p, g = fight()
    g.take_damage(30, from_x=p.x)
    assert g.state != 'HIT'                                        # 맞아도 움찔하지 않는다 (밀리지도 않는다)
    g.hold(2.0)
    assert g.state != 'HIT'
    assert g.pullable is False


def test_phase2_calls_at_once_and_speeds_up():
    import boss_intro
    room, p, g = fight()
    windup = g._windup_time()
    g.hp = g.max_hp / 2 - 1
    step()
    assert g.phase == 2 and boss_intro.current_bark()[1] == boss_intro.LINES['gatekeeper']['phase2']
    assert g._pick_move(600.0, 0.0) == 'call'                      # 2페이즈에 들어서면 바로 증원
    g.move = 'slam'
    slam2 = g._windup_time()
    g.phase = 1
    assert slam2 < g._windup_time()
    del windup


def test_phase2_charge_turns_and_charges_again():
    room, p, g = fight(gap=700.0)
    g.phase = 2
    p.x, g.x = 1200.0, 1900.0                                      # 벽에 닿지 않을 만큼 넓게 (벽에 부딪히면 비틀거리고 끝난다)
    do(g, 'charge')
    dirs = set()
    for _ in range(240):
        step()
        if abs(g.vx) > 300:
            dirs.add(1 if g.vx > 0 else -1)
        if g.state != 'ATTACK':
            break
    assert dirs == {-1, 1}                                         # 되돌아 한 번 더 달린다


def test_intro_lines_and_epithet():
    import boss_intro
    import ui
    lines = boss_intro.LINES['gatekeeper']
    assert 2 <= len(lines['intro']) <= 3 and lines['again'] and lines['death'] and lines['phase2']
    assert ui.BOSS_EPITHET['gatekeeper']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
