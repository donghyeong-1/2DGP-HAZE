"""기본 증강 손질 (v8 7일 차, docs/plan_v8.md 2절 끝). 창 없이: python tests/test_augment_cleanup_v8.py

- 겹침 정리: 페이드 '빈 몸'(대시 충전 -40%)이 대시 갈래 '가쁜 숨'(대시 충전 -25%)과 같은 일을 했다.
  '빈 몸'은 다른 게이지 계열처럼 **페이드 구간에서만** 대시 충전이 빨라진다.
- 수치뿐인 갈래에 동작이 보이는 증강 하나씩:
  - 연타 '긴 손잡이'(사거리 +15%) -> '검기': 3타가 앞으로 검기를 날린다 (사거리 밖의 적도 맞는다).
  - 충전 '버팀 자세'(충전 중 받는 피해 -30%) -> '쳐 내기': 충전하는 동안 가까이 온 적 투사체를 주먹으로 쳐 낸다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import mutations as mu  # noqa: E402
import test_combat as tc  # noqa: E402


def _dummy(room, p, dx, hp=10 ** 5):
    e = tc.freeze(tc.add_enemy('slum', p.x + dx, room, p))
    e.hp = e.max_hp = hp
    return e


def test_hollow_dash_only_speeds_dash_recharge_in_fade():
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    plain = mu.dash_recharge_time(p)
    mu.give(p, 'hollow_dash')
    assert abs(p.dash_recharge - plain) < 1e-9                            # 한 번 걸어 두는 값은 그대로
    assert abs(mu.dash_recharge_time(p) - plain) < 1e-9                   # 노멀: 그대로
    tc.set_gauge(p, 12)
    assert abs(mu.dash_recharge_time(p) - plain * mu.HOLLOW_DASH) < 1e-9  # 페이드: 빠르다
    mu.give(p, 'dash_recharge')
    assert abs(mu.dash_recharge_time(p) - plain * mu.HOLLOW_DASH * mu.DASH_RECHARGE) < 1e-9
    mu.remove(p, 'hollow_dash')
    mu.remove(p, 'dash_recharge')
    assert abs(mu.dash_recharge_time(p) - plain) < 1e-9


def test_fade_dash_slot_really_refills_faster_with_hollow_dash():
    def refill(mids):
        room, p = tc.make_world()
        tc.set_gauge(p, 12)
        for m in mids:
            mu.give(p, m)
        p.dash_slots, p.dash_charge = 0, 0.0
        n = 0
        while p.dash_slots == 0 and n < 600:
            tc.step(1)
            n += 1
        return n
    assert refill(('hollow_dash',)) < refill(()) * 0.75


def _three_swings(mids, gap):
    room, p = tc.make_world()
    tc.set_gauge(p, 35)
    e = _dummy(room, p, gap)
    for m in mids:
        mu.give(p, m)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    for _ in range(3):
        assert p.weapon.try_attack()
        tc.step(int(p.weapon.cooldown * 60) + 2)
    tc.step(30)
    return e


def test_combo_wave_replaces_long_handle_and_the_third_hit_sends_a_wave():
    assert 'combo_reach' not in mu.MUTATIONS and mu.MUTATIONS['combo_wave']['family'] == 'pipe_combo'
    far = config.PIPE_REACH * 2.2
    assert _three_swings((), far).hp == 10 ** 5                          # 사거리 밖
    e = _three_swings(('combo_wave',), far)
    assert e.hp < 10 ** 5                                                # 3타의 검기가 닿는다
    near = _three_swings(('combo_wave',), 100)
    plain = _three_swings((), 100)
    assert (10 ** 5 - near.hp) - (10 ** 5 - plain.hp) < 1                # 휘두르기에 맞은 적은 검기에 또 맞지 않는다


def _charge_with_scrap(mids):
    import projectile
    room, p = tc.make_world()
    p.give_weapon('gauntlet')
    tc.set_gauge(p, 60)
    for m in mids:
        mu.give(p, m)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.attack_held = True
    assert p.request_attack()
    tc.run_frames(2)
    assert p.weapon.charging
    shot = projectile.Scrap(p.x + 200, p.center[1], -1, 300.0, 5, room, p)
    game_world.add_object(shot, game_world.LAYER_EFFECT)
    hp = p.hp
    tc.run_frames(50)
    return shot in game_world.world[game_world.LAYER_EFFECT], hp - p.hp


def test_charge_parry_replaces_braced_stance_and_knocks_away_shots_while_charging():
    assert 'charge_guard' not in mu.MUTATIONS and mu.MUTATIONS['charge_parry']['family'] == 'gauntlet_charge'
    _alive, lost = _charge_with_scrap(())
    assert lost > 0                                                       # 그냥 충전하면 맞는다
    alive, lost = _charge_with_scrap(('charge_parry',))
    assert not alive and lost == 0                                        # 쳐 냈다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
