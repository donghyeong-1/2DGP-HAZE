"""E 중첩 강화와 단계별 기술 테스트 (창 없이). 실행: python tests/test_ultimate.py

2026-11-19 사용자 결정(docs/plan_v4.md 1절): E를 누를 때마다 강화 단계가 쌓인다(최대 3, 단계마다 게이지 25%).
다음 공격 한 번에 쌓인 단계가 모두 쓰인다. 1단계 = 지금의 강화 일격, 2단계 = 더 강한 판, 3단계 = 궁극기.
2026-11-24 궁극기 v2: 무기마다 기술 하나, 구성이 다르다 (철파이프 안개 난무 = 적마다 순간이동 베기 / 쌍권총 록온 난사 =
보이는 적 모두 조준, 움직이며 / 건틀릿 유성 돌진 = 적을 끌고 가 끝에서 폭발 / 사슬 감옥 = 끌어모아 묶어 둔다).
화면 멈춤과 컷인 띠는 없앴다(흐름 방해). 적 하나가 받는 피해 합은 무기와 상관없이 같고, 보스에게는 최대 체력의 15%까지만.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402
from haze_gauge import HazeGauge  # noqa: E402


def gauge_at(value):
    g = HazeGauge()
    g.value = float(value)
    g.zone = g._zone_of(float(value))
    return g


# ----- 게이지: 단계 쌓기 -----
def test_each_e_press_adds_a_stage_up_to_three():
    g = gauge_at(90)
    for lv, left in ((1, 65), (2, 40), (3, 15)):
        assert g.use_enhance() and g.enhance_level == lv and abs(g.value - left) < 1e-9
    assert not g.use_enhance() and g.enhance_level == 3                 # 최대 3단계
    assert g.enhanced


def test_stacking_needs_gauge_left_after_each_stage():
    g = gauge_at(50)
    assert g.use_enhance() and g.value == 25
    assert not g.use_enhance() and g.enhance_level == 1                 # 25%에서는 더 쌓지 못한다 (쓴 뒤 5% 이상 남아야)


def test_attack_or_timeout_clears_all_stages():
    g = gauge_at(90)
    g.use_enhance()
    g.use_enhance()
    g.consume_enhance()
    assert g.enhance_level == 0 and not g.enhanced
    g = gauge_at(90)
    g.use_enhance()
    g.use_enhance()
    g.tick(config.ENHANCE_TIME + 0.1, False)
    assert g.enhance_level == 0                                         # 준비 시간이 지나면 사라진다


def test_each_press_refreshes_the_ready_time():
    g = gauge_at(90)
    g.use_enhance()
    g.tick(5.0, False)
    g.use_enhance()
    assert abs(g.enhance_timer - config.ENHANCE_TIME) < 1e-9


# ----- 무기: 단계별 기술 -----
FLOOR = float(2 * config.TILE)


def stacked(gauge, stages, gaps, player_x=1100.0):
    """게이지를 맞추고 E를 stages번 눌러 둔 플레이어와, 오른쪽 gaps 거리마다 움직이지 않는 슬럼(체력 크게).
    궁극기 범위를 재려고 벽 없는 평평한 시험장(balance_sim.arena, 44칸 = 2640px)을 쓴다."""
    sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
    import balance_sim
    from player import Player
    game_world.clear()
    effects.reset()
    room = balance_sim.arena()
    p = Player(player_x, FLOOR, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    tc.step(30)
    tc.set_gauge(p, gauge)
    for _ in range(stages):
        assert p.request_enhance()
    foes = []
    for gap in gaps:
        e = tc.freeze(add_slum(p.x + gap, room, p))
        e.hp = e.max_hp = 10 ** 5
        foes.append(e)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    return room, p, foes


def add_slum(x, room, p):
    from enemy import Enemy
    e = Enemy('slum', x, FLOOR, room, p)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return e


def ultimates():
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if getattr(o, 'is_ultimate', False)]


def run_out_ultimate(limit=420, each=None):
    for _ in range(limit):
        if not ultimates():
            return
        effects.hit_stop_left = 0.0
        tc.step(1)
        if each:
            each()
    raise AssertionError('궁극기가 끝나지 않았다')


def budget(p):
    """궁극기 하나가 적 하나에게 주는 피해 합 (무기와 상관없이 같다)."""
    return (config.ULT_BASE_DAMAGE * p.gauge.zone_multipliers()['attack'] * p.attack_bonus *
            config.ULT_HIT_MULT * config.ULT_HITS)


def give(p, weapon_id):
    level = p.gauge.enhance_level
    p.give_weapon(weapon_id)
    assert p.gauge.enhance_level == level


def cast(wid, gaps, player_x=1100.0):
    room, p, foes = stacked(90, 3, gaps, player_x=player_x)
    if wid != 'pipe':
        give(p, wid)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    assert p.request_attack() and ultimates() and p.gauge.enhance_level == 0
    return room, p, foes, ultimates()[0]


def test_second_stage_strike_is_stronger_than_first():
    hits = []
    for stages, gauge in ((1, 65), (2, 90)):                            # 쓰고 난 게이지가 둘 다 40% (같은 노멀 구간)
        room, p, (e,) = stacked(gauge, stages, [100])
        p.request_attack()
        tc.step(50)                                                     # 2단계는 내려찍기가 바닥에 닿을 때(약 0.27초 뒤) 크게 맞는다
        hits.append(e.max_hp - e.hp)
        assert p.gauge.enhance_level == 0
    assert hits[1] > hits[0] * 1.4, hits                                # 2단계는 1단계보다 확실히 세다


# ----- 궁극기 v2 (2026-11-24 사용자: "무기별로 다르게 구성, 잠시 나오는 애니메이션 화면은 지우자 흐름에 방해된다") -----
def test_ultimate_never_freezes_the_screen_or_shows_a_cutin():
    import weapon
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        room, p, foes, u = cast(wid, [300])
        assert effects.hit_stop_left == 0, wid                           # 시전 순간 화면이 멈추지 않는다
        assert not hasattr(u, 'born'), wid                               # 컷인 띠(실제 시간으로 움직이던 그림)가 없다
        assert u.name == weapon.ULT_NAMES[wid]                           # 무기마다 기술 하나, 이름은 주인공 위 글자로만
        assert p.invuln_left > 0
    assert not hasattr(config, 'ULT_FREEZE') and not hasattr(config, 'ULT_BANNER_TIME')


def test_pipe_flurry_blinks_to_each_enemy_then_returns():
    room, p, (a, b, far), u = cast('pipe', [220, -380, 900])
    x0, g0 = p.x, p.gauge.value
    near = {id(a): 9999.0, id(b): 9999.0}

    def watch():
        for e in (a, b):
            near[id(e)] = min(near[id(e)], abs(p.x - e.x))
    run_out_ultimate(each=watch)
    assert near[id(a)] < 130 and near[id(b)] < 130, near                 # 적마다 옆으로 순간이동해 벤다 (앞뒤 가리지 않는다)
    assert abs(p.x - x0) < 6                                             # 끝나면 제자리로
    assert abs((a.max_hp - a.hp) - budget(p)) < 1e-3 and abs((b.max_hp - b.hp) - budget(p)) < 1e-3
    assert far.hp == far.max_hp                                          # 범위 밖
    assert p.gauge.value <= g0 + 0.01                                    # 궁극기 타격은 게이지를 올리지 않는다


def test_finale_blur_also_smears_the_enemies_that_were_hit():
    """2026-11-24 사용자: 궁극기가 끝나며 번지는 블러가 주인공에게만 있다 -> 맞은 적들도 같이 번져야 한다."""
    room, p, (a, b, far), u = cast('pipe', [220, -380, 900])
    seen = []

    def watch():
        for o in game_world.world[game_world.LAYER_EFFECT]:
            if type(o).__name__ == 'BlurSmear' and o.victims and o not in seen:
                seen.append(o)
    run_out_ultimate(each=watch)
    for _ in range(90):
        effects.hit_stop_left = 0.0
        tc.step(1)
        watch()
    assert seen, '맞은 적을 담은 블러가 없다'
    blur = seen[-1]
    assert len(blur.victims) == 2, blur.victims                          # 맞은 둘만 (범위 밖의 적은 아니다)
    for frame, x, y, face in blur.victims:
        assert frame[0] is not None and face in (-1, 1)


def test_pistol_lockon_shoots_every_enemy_in_sight_and_lets_you_move():
    room, p, (a, b, far), u = cast('pistol', [150, -700, 1250], player_x=1300.0)
    x0 = p.x
    p.right = True                                                       # 쏘는 동안 걸어간다
    run_out_ultimate()
    assert a.hp < a.max_hp and b.hp < b.max_hp                           # 보이는 적은 앞뒤 모두 조준
    assert far.hp == far.max_hp                                          # 너무 먼 적은 아니다
    assert abs((b.max_hp - b.hp) - budget(p)) < 1e-3
    assert abs(p.x - x0) > 60                                            # 묶이지 않는다


def test_gauntlet_meteor_carries_enemies_along_and_bursts_at_the_end():
    room, p, (a, b, far), u = cast('gauntlet', [160, 360, 1400], player_x=500.0)
    x0, ax0, bx0 = p.x, a.x, b.x
    run_out_ultimate()
    tc.step(30)
    assert p.x - x0 > config.ULT_METEOR_LENGTH * 0.8                     # 길게 돌진한다 (첫 적에서 멈추지 않는다)
    assert a.x - ax0 > 250 and b.x - bx0 > 120                           # 닿은 적을 끌고 간다
    assert abs((a.max_hp - a.hp) - budget(p)) < 1e-3 and abs((b.max_hp - b.hp) - budget(p)) < 1e-3
    assert far.hp == far.max_hp


def test_chain_prison_drags_everyone_together_and_holds_them():
    room, p, (a, b, far), u = cast('chain', [420, -420, 1300])
    run_out_ultimate()
    assert abs(a.x - p.x) < 260 and abs(b.x - p.x) < 260                 # 둘레의 적이 끌려왔다
    assert abs((a.max_hp - a.hp) - budget(p)) < 1e-3
    assert a.state == 'HIT' and a.hit_left > config.ULT_PRISON_HOLD * 0.7   # 끝난 뒤에도 묶여 있다 (이어 치는 시간)
    assert far.hp == far.max_hp


def test_ultimate_damage_to_a_boss_is_capped_for_every_weapon():
    from boss import Boss
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        room, p, _ = stacked(99, 3, [])
        if wid != 'pipe':
            give(p, wid)
        tc.set_gauge(p, 99)
        boss = Boss(p.x + 250, FLOOR, room, p)
        boss.stats = dict(boss.stats, speed=0.0, sight=0)
        boss.cooldown = 99.0
        game_world.add_object(boss, game_world.LAYER_ENEMY)
        p.attack_bonus = 50.0                                            # 상한이 없으면 한 방에 끝날 만큼 세게
        p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
        x0 = boss.x
        p.request_attack()
        run_out_ultimate()
        tc.step(20)
        dealt = boss.max_hp - boss.hp
        assert boss.alive and 0 < dealt <= boss.max_hp * config.ULT_BOSS_CAP + 1e-6, (wid, dealt)
        assert abs(boss.x - x0) < 40, wid                                # 보스는 끌려가지 않는다


def test_ultimate_damage_is_the_same_for_every_weapon():
    """궁극기는 게이지 75%를 쓰는 값이 무기마다 같아야 한다 (적 하나 기준)."""
    dealt = {}
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        room, p, (e,), u = cast(wid, [300])
        run_out_ultimate()
        tc.step(20)
        dealt[wid] = round(e.max_hp - e.hp, 3)
    assert len(set(dealt.values())) == 1 and dealt['pipe'] > 0, dealt


def test_chain_cast_uses_the_gather_and_release_pose():
    import sprites
    room, p, (e,), u = cast('chain', [300])
    tc.step(1)
    assert p._body_frame() == ('n09_ult', 1)                             # 모으기
    for _ in range(int(config.ULT_POSE_GATHER * 60) + 3):
        tc.step(1)
    assert p._body_frame() == ('n09_ult', 2)                             # 해방
    assert sprites.count('n09_ult') == 2


def test_every_ultimate_bursts_twice_with_its_own_nova():
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        room, p, (e,), u = cast(wid, [300])
        run_out_ultimate()
        assert u.nova_count >= 2, (wid, u.nova_count)                  # 시작과 마지막 일격
        assert u.nova_name == 'ult-nova-' + wid                          # 무기마다 색·모양이 다른 폭발
    root = os.path.join(HERE, '..', 'assets', 'effects')
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        assert os.path.exists(os.path.join(root, f'ult-nova-{wid}.png')), wid


def test_second_stage_pipe_is_a_new_motion_rising_slash_then_ground_slam():
    """2026-11-20 사용자: 2단계 강화 공격도 1단계와 다른 동작으로. 철파이프 2단계 = 올려베기 -> (0.16초 뒤) 내려찍기 충격."""
    room, p, (e,) = stacked(65, 1, [100])
    p.request_attack()
    assert p.swing_dir != 'up'                                          # 1단계는 지금까지의 큰 일격 (올려베기가 아니다)
    room, p, (e,) = stacked(90, 2, [100])
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_attack()
    assert p.swing_dir == 's2rise' and p.weapon.last_kind == 'pipe' and p.weapon.level == 2
    assert p._body_frame() == ('n09_s2rise', 1)                         # T24 전용 그림: 웅크려 낮춤
    first = e.max_hp - e.hp
    assert first > 0                                                    # 첫 타: 올려베기
    seen_slam = False
    for _ in range(30):
        effects.hit_stop_left = 0.0
        tc.step(1)
        if p.swing_dir == 's2slam':
            seen_slam = True
            assert p._body_frame()[0] == 'n09_s2slam'
    assert seen_slam                                                    # 이어서 앞 아래로 내려찍는 자세
    import sprites
    assert sprites.count('n09_s2rise') == 3 and sprites.count('n09_s2slam') == 3
    assert e.max_hp - e.hp > first * 1.5                                # 둘째 타가 더 세다
    assert 'quake-blast' in tc.spawned_names()                          # 바닥 충격
    assert p.gauge.enhance_level == 0

if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
