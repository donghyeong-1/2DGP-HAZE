"""E 중첩 강화와 단계별 기술 테스트 (창 없이). 실행: python tests/test_ultimate.py

2026-11-19 사용자 결정(docs/plan_v4.md 1절): E를 누를 때마다 강화 단계가 쌓인다(최대 3, 단계마다 게이지 25%).
다음 공격 한 번에 쌓인 단계가 모두 쓰인다. 1단계 = 지금의 강화 일격, 2단계 = 더 강한 판, 3단계 = 궁극기
(무기 x 기본·대시·점프마다 다른 기술, 화면 멈춤·어둡게·기술 이름 띠, 보스에게는 최대 체력의 15%까지만).
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
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Ultimate']


def run_out_ultimate(limit=240):
    for _ in range(limit):
        if not ultimates():
            return
        effects.hit_stop_left = 0.0
        tc.step(1)
    raise AssertionError('궁극기가 끝나지 않았다')


def test_second_stage_strike_is_stronger_than_first():
    hits = []
    for stages, gauge in ((1, 65), (2, 90)):                            # 쓰고 난 게이지가 둘 다 40% (같은 노멀 구간)
        room, p, (e,) = stacked(gauge, stages, [100])
        g0 = p.gauge.value
        p.request_attack()
        tc.step(50)                                                     # 2단계는 내려찍기가 바닥에 닿을 때(약 0.27초 뒤) 크게 맞는다
        hits.append(e.max_hp - e.hp)
        assert p.gauge.enhance_level == 0
    assert hits[1] > hits[0] * 1.4, hits                                # 2단계는 1단계보다 확실히 세다


def test_third_stage_basic_attack_is_a_wide_area_not_the_whole_screen():
    """2026-11-20 사용자: 화면 전체 공격이 아니라 새 이펙트의 광역 공격. 앞쪽 약 480px까지만 맞는다."""
    room, p, (near, mid, far) = stacked(90, 3, [150, 420, 800])
    behind = tc.freeze(add_slum(p.x - 400, room, p))      # 방 안, 플레이어 뒤
    behind.hp = behind.max_hp = 10 ** 5
    assert p.request_attack()
    assert ultimates() and p.gauge.enhance_level == 0
    u = ultimates()[0]
    assert u.name and u.kind == 'basic'                                 # 기술 이름 띠
    assert effects.hit_stop_left > 0                                     # 화면이 멈춘다
    g0 = p.gauge.value
    run_out_ultimate()
    assert near.hp < near.max_hp and mid.hp < mid.max_hp                 # 앞쪽 넓은 범위는 맞는다
    assert far.hp == far.max_hp                                         # 화면 끝까지는 닿지 않는다
    assert behind.hp == behind.max_hp                                   # 뒤는 안 맞는다
    assert (mid.max_hp - mid.hp) > 5 * config.PIPE_DAMAGE               # 여러 번 크게
    assert p.gauge.value <= g0 + 0.01                                   # 궁극기 타격은 게이지를 올리지 않는다 (처치는 별개)


def test_third_stage_dash_attack_runs_through_a_line():
    room, p, (hit, far) = stacked(90, 3, [600, 950])
    p.dash_window = 0.2                                                  # 대시 직후 = 대시 공격
    assert p.weapon.current_kind() == 'dash'
    p.request_attack()
    assert ultimates()[0].kind == 'dash'
    run_out_ultimate()
    assert hit.hp < hit.max_hp and far.hp == far.max_hp


def test_third_stage_jump_attack_slams_both_sides():
    room, p, (right, far) = stacked(90, 3, [380, 750])
    left = tc.freeze(add_slum(p.x - 380, room, p))
    left.hp = left.max_hp = 10 ** 5
    p.on_ground = False
    p.state = 'JUMP'
    p.y += 60
    assert p.weapon.current_kind() in ('spin', 'plunge')
    p.request_attack()
    assert ultimates()[0].kind == 'jump'
    run_out_ultimate()
    assert right.hp < right.max_hp and left.hp < left.max_hp           # 양쪽 모두
    assert far.hp == far.max_hp                                         # 멀리는 닿지 않는다


def test_ultimate_damage_to_a_boss_is_capped():
    from boss import Boss
    room, p, _ = stacked(99, 3, [])
    tc.set_gauge(p, 99)
    boss = Boss(p.x + 300, FLOOR, room, p)
    boss.stats = dict(boss.stats, speed=0.0, sight=0)
    boss.cooldown = 99.0
    game_world.add_object(boss, game_world.LAYER_ENEMY)
    p.attack_bonus = 50.0                                                # 상한이 없으면 한 방에 끝날 만큼 세게
    p.request_attack()
    run_out_ultimate()
    assert boss.alive and boss.max_hp - boss.hp <= boss.max_hp * config.ULT_BOSS_CAP + 1e-6


def test_every_weapon_has_named_ultimates_for_each_attack_kind():
    import weapon
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        for kind in ('basic', 'dash', 'jump'):
            assert weapon.ULT_NAMES.get((wid, kind)), (wid, kind)


# ----- 무기별 궁극기 모양 -----
def give(p, weapon_id):
    level = p.gauge.enhance_level
    p.give_weapon(weapon_id)
    assert p.gauge.enhance_level == level


def test_pistol_rain_falls_around_the_aim_point_not_around_the_player():
    room, p, (near, far) = stacked(90, 3, [120, 620], player_x=600.0)
    give(p, 'pistol')
    p.mouse_x, p.mouse_y = far.center                                    # 조준한 곳 일대에 탄우
    p.request_attack()
    assert ultimates()[0].name == '탄우'
    run_out_ultimate()
    assert far.hp < far.max_hp and near.hp == near.max_hp


def test_gauntlet_beam_reaches_far_along_the_aim_but_not_across_the_screen():
    room, p, (hit, far) = stacked(90, 3, [850, 1300], player_x=500.0)
    give(p, 'gauntlet')
    high = tc.freeze(add_slum(p.x + 400, room, p))
    high.y += 420                                                        # 광선 줄에서 위로 벗어남
    high.hp = high.max_hp = 10 ** 5
    p.mouse_x, p.mouse_y = p.x + 1000, p.center[1]
    p.request_attack()
    assert ultimates()[0].name == '헤이즈 포격'
    run_out_ultimate()
    assert hit.hp < hit.max_hp and far.hp == far.max_hp and high.hp == high.max_hp


def test_chain_capture_pulls_enemies_in_before_the_blast():
    room, p, (e,) = stacked(90, 3, [420])
    give(p, 'chain')
    p.request_attack()
    assert ultimates()[0].name == '포획 폭발'
    run_out_ultimate()
    assert e.hp < e.max_hp and abs(e.x - p.x) < 300                      # 끌려와서 터졌다


def test_ultimate_damage_is_the_same_for_every_weapon():
    """궁극기는 게이지 75%를 쓰는 값이 무기마다 같아야 한다 (식칼 기본 피해 11, 건틀릿 34와 무관)."""
    dealt = {}
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        room, p, (e,) = stacked(90, 3, [300])
        if wid != 'pipe':
            give(p, wid)
        p.mouse_x, p.mouse_y = e.center
        p.request_attack()
        run_out_ultimate()
        dealt[wid] = e.max_hp - e.hp
    assert len({round(v, 6) for v in dealt.values()}) == 1 and dealt['pipe'] > 0, dealt


def test_casting_pose_gathers_then_releases_and_cutin_art_exists():
    """T23: 시전하면 '모으기'(화면 정지 동안) -> '해방' 자세, 이름 띠 대신 주인공 컷인 그림."""
    import sprites
    room, p, (e,) = stacked(90, 3, [300])
    p.request_attack()
    assert p._body_frame() == ('n09_ult', 1)                             # 정지 중: 모으기
    for _ in range(int(config.ULT_POSE_GATHER * 60) + 3):
        tc.step(1)
    assert p._body_frame() == ('n09_ult', 2)                             # 해방
    assert sprites.count('n09_ult') == 2
    root = os.path.join(HERE, '..', 'assets')
    assert os.path.exists(os.path.join(root, 'ui', 'ult_cutin.png'))



def test_every_ultimate_shows_the_new_area_burst_and_dims_less():
    """광역 공격 이펙트(ult-nova)가 범위 한가운데에 터진다. 화면을 덮던 어둠은 옅게."""
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        room, p, (e,) = stacked(90, 3, [300])
        if wid != 'pipe':
            give(p, wid)
        p.mouse_x, p.mouse_y = e.center
        p.request_attack()
        u = ultimates()[0]
        run_out_ultimate()
        names = [getattr(o, 'name', '') for o in game_world.world[game_world.LAYER_EFFECT]]
        assert u.nova_count >= 2, (wid, u.nova_count)                  # 시작과 마지막 일격
        assert u.nova_name == 'ult-nova-' + wid                          # 무기마다 색·모양이 다른 폭발 (11/21 계획 1-6)
    assert config.ULT_DIM <= 0.35
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
