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
        tc.step(30)
        hits.append(e.max_hp - e.hp)
        assert p.gauge.enhance_level == 0
    assert hits[1] > hits[0] * 1.4, hits                                # 2단계는 1단계보다 확실히 세다


def test_third_stage_basic_attack_is_an_ultimate_over_half_the_screen():
    room, p, (near, far) = stacked(90, 3, [150, 800])
    behind = tc.freeze(add_slum(p.x - 400, room, p))      # 방 안, 플레이어 뒤
    behind.hp = behind.max_hp = 10 ** 5
    assert p.request_attack()
    assert ultimates() and p.gauge.enhance_level == 0
    u = ultimates()[0]
    assert u.name and u.kind == 'basic'                                 # 기술 이름 띠
    assert effects.hit_stop_left > 0                                     # 화면이 멈춘다
    g0 = p.gauge.value
    run_out_ultimate()
    assert near.hp < near.max_hp and far.hp < far.max_hp                 # 앞쪽 화면 절반이 모두 맞는다
    assert behind.hp == behind.max_hp                                   # 뒤는 안 맞는다
    assert (far.max_hp - far.hp) > 5 * config.PIPE_DAMAGE               # 여러 번 크게
    assert p.gauge.value <= g0 + 0.01                                   # 궁극기 타격은 게이지를 올리지 않는다 (처치는 별개)


def test_third_stage_dash_attack_runs_through_a_long_line():
    room, p, (far,) = stacked(90, 3, [900])
    p.dash_window = 0.2                                                  # 대시 직후 = 대시 공격
    assert p.weapon.current_kind() == 'dash'
    p.request_attack()
    assert ultimates()[0].kind == 'dash'
    run_out_ultimate()
    assert far.hp < far.max_hp


def test_third_stage_jump_attack_slams_both_sides():
    room, p, (right,) = stacked(90, 3, [700])
    left = tc.freeze(add_slum(p.x - 700, room, p))
    left.hp = left.max_hp = 10 ** 5
    p.on_ground = False
    p.state = 'JUMP'
    p.y += 60
    assert p.weapon.current_kind() in ('spin', 'plunge')
    p.request_attack()
    assert ultimates()[0].kind == 'jump'
    run_out_ultimate()
    assert right.hp < right.max_hp and left.hp < left.max_hp           # 양쪽 모두


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
    for wid in ('pipe', 'knife', 'gauntlet', 'chain'):
        for kind in ('basic', 'dash', 'jump'):
            assert weapon.ULT_NAMES.get((wid, kind)), (wid, kind)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
