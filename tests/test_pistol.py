"""쌍권총 (v7, 2026-11-24, docs/plan_v7.md 1절: 식칼 대체). 창 없이: python tests/test_pistol.py

- 좌우 총을 번갈아 쏜다 (총알마다 side가 +1, -1, +1 ...). 누르고 있으면 쿨타임마다 이어서 쏜다.
- 쏘면서 움직이고 뛸 수 있다 (휘두르기처럼 멈추지 않는다).
- 구간: 노멀 1발, 각성 2발, 위험 3발(부채꼴). 페이드는 느리게 1발.
- 총알은 빠르게 날아가 첫 적에 맞고 사라진다. 벽에 닿으면 사라진다.
- 대시 중·직후: 일자로 모은 3발, 관통.
- E 강화: 두 총을 모아 큰 한 발(관통, 큰 피해)과 뒤로 밀리는 반동. 2단계는 맞은 자리에서 8방향 파편.
- 총구 섬광이 총알마다 하나.
- 식칼은 없어졌다. 예전 저장(두 번째 무기 'knife')은 쌍권총으로 읽는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def _bullets():
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Bullet']


def _armed(gauge=35):
    room, p = tc.make_world()
    p.give_weapon('pistol')
    p.gauge.value = gauge
    p.gauge.zone = p.gauge._zone_of(gauge)
    return room, p


def test_pistol_replaces_the_knife():
    import weapon
    import items
    import meta
    assert 'pistol' in weapon.WEAPONS and 'knife' not in weapon.WEAPONS
    assert items.ITEMS['w_pistol']['weapon'] == 'pistol' and 'w_knife' not in items.ITEMS
    assert 'pistol' in meta.START_WEAPONS and 'knife' not in meta.START_WEAPONS
    assert meta.migrate_weapon('knife') == 'pistol'


def test_alternates_guns_and_keeps_firing_while_held():
    room, p = _armed()
    assert p.request_attack()
    sides = [b.side for b in _bullets()]
    assert len(sides) == 1
    tc.run_frames(int(config.PISTOL_COOLDOWN * 60) + 2)
    p.request_attack()
    assert [b.side for b in _bullets()][-1] == -sides[0]                 # 다른 손의 총
    assert any(type(o).__name__ == 'MuzzleFlash' for o in game_world.world[game_world.LAYER_EFFECT])
    room, p = _armed()
    fired = [0]
    shoot = p.weapon.try_attack

    def counted():
        ok = shoot()
        fired[0] += bool(ok)
        return ok
    p.weapon.try_attack = counted
    p.attack_held = True
    p.request_attack()
    tc.run_frames(60)
    assert fired[0] >= 5                                                 # 1초 누르고 있으면 계속 쏜다


def test_can_move_while_shooting():
    room, p = _armed()
    p.right = True
    tc.run_frames(20)
    assert p.state == 'RUN'
    full = config.RUN_SPEED * p.speed_mult()
    x0 = p.x
    p.request_attack()
    tc.run_frames(12)
    assert p.x - x0 >= full * 12 / 60 * 0.85                             # 쏴도 거의 느려지지 않는다


def test_bullet_count_follows_the_gauge_zone():
    for gauge, n in ((35, 1), (60, 2), (95, 3)):
        room, p = _armed(gauge)
        p.request_attack()
        assert len(_bullets()) == n, (gauge, len(_bullets()))
    room, p = _armed(10)
    p.request_attack()
    assert len(_bullets()) == 1 and p.weapon.cooldown >= config.PISTOL_FADE_COOLDOWN - 1e-6


def test_bullet_hits_the_first_enemy_and_stops():
    room, p = _armed()
    a = tc.freeze(tc.add_enemy('slum', p.x + 300, room, p))
    b = tc.freeze(tc.add_enemy('slum', p.x + 360, room, p))
    p.request_attack()
    tc.run_frames(30)
    assert a.hp < a.max_hp and b.hp == b.max_hp
    assert not _bullets()


def test_dash_shot_is_three_piercing_bullets():
    room, p = _armed()
    p.request_dash()
    assert p.weapon.current_kind() == 'pistol_dash'
    p.request_attack()
    bs = _bullets()
    assert len(bs) == 3 and all(b.pierce for b in bs)


def test_enhanced_big_shot_pierces_and_recoils():
    room, p = _armed(60)
    p.request_enhance()
    p.request_attack()
    bs = _bullets()
    assert len(bs) == 1 and bs[0].big and bs[0].pierce
    assert p.lunge_vx < 0                                                # 오른쪽을 쐈으니 왼쪽으로 밀린다
    room, p = _armed(90)
    p.request_enhance()
    p.request_enhance()
    e = tc.freeze(tc.add_enemy('slum', p.x + 300, room, p))
    e.hp = e.max_hp = 9999
    p.request_attack()
    seen = set()
    for _ in range(20):                                                  # 아래쪽 파편은 바닥에 바로 닿아 사라지니 나타난 것을 모두 센다
        tc.run_frames(1)
        seen |= {id(b) for b in _bullets() if b.shrapnel}
    assert len(seen) >= 8                                                # 2단계: 맞은 자리에서 8방향 파편


def test_aiming_pose_follows_aim_running_and_air():
    import sprites
    if 'n09_pistol_up' not in sprites.SKIN:
        return
    room, p = _armed()
    for dy, name in ((0, 'n09_pistol'), (500, 'n09_pistol_up'), (200, 'n09_pistol_upfwd'),
                     (-200, 'n09_pistol_downfwd'), (-500, 'n09_pistol_down')):
        p.mouse_x, p.mouse_y = p.x + 300, p.center[1] + dy
        p.weapon.cooldown = 0
        p.request_attack()
        assert p._body_frame()[0] == name, (dy, p._body_frame())
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.right = True
    tc.run_frames(20)
    p.weapon.cooldown = 0
    p.request_attack()
    assert p._body_frame()[0] == 'n09_pistol_run'                         # 달리며 쏘기: 다리가 계속 움직인다
    p.right = False
    tc.run_frames(30)
    p.request_jump()
    tc.run_frames(8)
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]                         # 뛰어오른 높이에서 앞을 겨눈다
    p.weapon.cooldown = 0
    p.request_attack()
    assert p._body_frame() == ('n09_pistol_air', 1)                       # 공중 앞 겨눔


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
