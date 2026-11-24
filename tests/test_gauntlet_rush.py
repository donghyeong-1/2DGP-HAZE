"""건틀릿 돌진 강타 (2026-11-24 사용자 요청: "기를 날리는게 아니라 돌진해서 박는 강력한 공격, 공속은 느리지만" - 권사 느낌).
창 없이: python tests/test_gauntlet_rush.py

- 누르는 동안 게이지를 태워 충전(그대로), 떼면 충격파 대신 주인공이 조준 쪽으로 돌진한다. 충전할수록 멀리 간다.
- 처음 닿은 적에서 멈추며 큰 일격(충전 비율만큼 피해) + 크게 밀려남. 둘레 적은 충격으로 조금 맞는다.
- 아무도 못 맞히면 돌진만 하고 끝난다. 공격 간격은 느리다 (GAUNTLET_COOLDOWN).
- 대시·공중: 충전 없이 짧은 돌진 (게이지 조금). 공중에서 아래로: 내리꽂기, 땅에 닿으면 둘레를 친다.
- 위험 구간: 충전 없이 바로 끝까지 돌진. 강화 2단계: 부딪힌 자리에서 양옆으로 충격파가 퍼진다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def _armed(gauge=40, x=300.0):
    room, p = tc.make_world(player_x=x)
    p.give_weapon('gauntlet')
    tc.set_gauge(p, gauge)
    p.mouse_x, p.mouse_y = p.x + 600, p.center[1]
    return room, p


def _enemy(room, p, dx, hp=10 ** 5):
    e = tc.freeze(tc.add_enemy('slum', p.x + dx, room, p))
    e.hp = e.max_hp = hp
    return e


def _charge(p, frames):
    p.attack_held = True
    assert p.request_attack() and p.weapon.charging
    tc.run_frames(frames)
    p.attack_held = False
    tc.run_frames(1)


def _blasts():
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Blast']


def test_release_dashes_toward_the_aim_instead_of_firing_a_shockwave():
    room, p = _armed()
    x0 = p.x
    _charge(p, int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60) + 5)
    assert p.weapon.rushing and not _blasts()                            # 충격파는 없다, 몸이 나간다
    tc.run_frames(30)
    assert not p.weapon.rushing
    moved = p.x - x0
    assert moved > config.GAUNTLET_RUSH_MAX * 0.8, moved                 # 완충: 거의 끝까지 돌진


def test_more_charge_dashes_further():
    dist = []
    for frames in (int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60 * 0.3), int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60) + 5):
        room, p = _armed()
        x0 = p.x
        _charge(p, frames)
        tc.run_frames(30)
        dist.append(p.x - x0)
    assert dist[1] > dist[0] * 1.5, dist


def test_rush_stops_at_the_first_enemy_with_a_heavy_knockback_hit():
    room, p = _armed()
    a = _enemy(room, p, 150)
    b = _enemy(room, p, 600)
    _charge(p, int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60) + 5)
    vx = 0.0
    for _ in range(30):
        tc.run_frames(1)
        vx = max(vx, a.vx)
        if not p.weapon.rushing:
            break
    assert a.hp < a.max_hp and b.hp == b.max_hp                          # 처음 닿은 적에서 멈췄다
    assert p.x < a.x                                                     # 꿰뚫고 지나가지 않는다
    assert a.max_hp - a.hp >= config.GAUNTLET_DAMAGE * 0.9               # 완충 일격 (피해 = 기본 피해)
    assert vx > config.GAUNTLET_KNOCK * 0.8                              # 크게 밀려난다


def test_impact_shock_hits_enemies_beside_the_target_weaker():
    room, p = _armed()
    a = _enemy(room, p, 150)
    b = _enemy(room, p, 150 + config.GAUNTLET_IMPACT_RADIUS * 0.6)
    _charge(p, int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60) + 5)
    tc.run_frames(30)
    da, db = a.max_hp - a.hp, b.max_hp - b.hp
    assert 0 < db < da                                                   # 옆 적은 충격으로 덜 맞는다


def test_whiff_rush_ends_and_the_gauntlet_is_slow_to_reuse():
    room, p = _armed()
    _charge(p, int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60) + 5)
    assert config.GAUNTLET_COOLDOWN >= 0.7                               # 공속이 느리다
    tc.run_frames(int(config.GAUNTLET_COOLDOWN * 60 * 0.6))
    assert not p.weapon.rushing and not p.weapon.ready                   # 돌진이 끝나도 한동안 못 쓴다


def test_dash_and_air_make_a_short_lunge_and_air_down_dives_into_the_floor():
    for setup in ('dash', 'air'):
        room, p = _armed(gauge=50)
        if setup == 'dash':
            p.dash_window = 0.2
        else:
            p.request_jump()
            tc.run_frames(10)
        p.attack_held = True
        assert p.request_attack()
        assert not p.weapon.charging and p.weapon.rushing, setup          # 충전 없이 바로 돌진
        assert abs(p.gauge.value - (50 - config.GAUNTLET_QUICK_COST)) < 1e-6, setup
    room, p = _armed(gauge=50)
    e = _enemy(room, p, 90)
    p.request_jump()
    tc.run_frames(7)                                                     # 위 발판(높이 300)보다 아래에서
    assert not p.on_ground and p.y < 300
    p.mouse_x, p.mouse_y = p.x + 60, p.y - 600                           # 아래로
    p.attack_held = True
    assert p.request_attack()
    p.attack_held = False
    for _ in range(40):
        tc.run_frames(1)
        if p.on_ground:
            break
    tc.run_frames(2)
    assert p.on_ground and e.hp < e.max_hp                               # 내리꽂아 땅에 닿은 자리 둘레를 쳤다


def test_critical_zone_rushes_at_once_to_full_distance():
    room, p = _armed(gauge=95)
    x0 = p.x
    p.attack_held = True
    assert p.request_attack()
    assert not p.weapon.charging and p.weapon.rushing
    assert p.gauge.value <= 95 - config.GAUNTLET_CRIT_COST + 0.01
    p.attack_held = False
    tc.run_frames(30)
    assert p.x - x0 > config.GAUNTLET_RUSH_MAX * 0.8


def test_rush_does_not_tunnel_through_walls():
    room, p = _armed(x=config.TILE * 19)
    _charge(p, int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60) + 5)
    tc.run_frames(30)
    assert room.tile_at_world(p.x, p.y + 10) != '#'                      # 벽 안에 박히지 않는다
    assert not p.weapon.rushing


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
