"""손맛(피격 반응) 테스트 (창 없이). 실행: python tests/test_feel.py

2026-11-21 퀄리티 상승 계획 1-5 (docs/quality_plan.md):
- 맞은 적은 처음 잠깐 하얗게 번쩍이고(흰 번쩍임), 그 뒤 붉게 물든다.
- 밀려나는 거리는 적의 무게(사냥개 가볍게, 간수 무겁게)와 공격의 크기(큰 공격은 더 멀리)에 따라 다르다.
- 방의 마지막 적이 쓰러지면 잠깐 느려진다(슬로 모션). 보스는 더 길게.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import test_combat as tc  # noqa: E402


def _foe(kind, gap=120):
    room, p = tc.make_world()
    e = tc.freeze(tc.add_enemy(kind, p.x + gap, room, p))
    e.hp = e.max_hp = 1000
    return room, p, e


def test_hit_flashes_white_first_then_red():
    room, p, e = _foe('slum')
    e.take_damage(1, from_x=p.x)
    assert e.white_flash()                                  # 맞은 순간: 하얗게
    tc.step(int(config.ENEMY_WHITE_FLASH * 60) + 1)
    assert not e.white_flash() and e._tint() == (255, 90, 90)   # 그 뒤: 붉게


def test_light_enemies_fly_farther_than_heavy_ones():
    pushed = {}
    for kind in ('hound', 'slum', 'guard'):
        room, p, e = _foe(kind)
        e.take_damage(1, from_x=p.x)
        pushed[kind] = e.vx
    assert pushed['hound'] > pushed['slum'] > pushed['guard'] > 0, pushed


def test_big_hits_push_farther():
    room, p, e = _foe('slum')
    w = p.weapon
    w._hit(e, 1, 0, config.ZONE_FX['NORMAL'], extra=False)
    small = e.vx
    room, p, e = _foe('slum')
    p.weapon._hit(e, 1, 0, config.ENHANCED_FX, big=True, extra=False)
    assert e.vx > small * 1.4, (e.vx, small)


def test_slow_motion_scales_time_then_wears_off():
    effects.reset()
    assert effects.time_scale() == 1.0
    effects.request_slow_motion(0.4, 0.3)
    assert effects.time_scale() == 0.3
    effects.tick_slow_motion(0.2)
    assert effects.time_scale() < 1.0
    effects.tick_slow_motion(0.3)
    assert effects.time_scale() == 1.0


def test_clearing_a_room_slows_time_longer_for_a_boss():
    import play_mode

    class Dead:
        alive = False

    class FakeStage:
        boss = None

    effects.reset()
    play_mode._on_room_cleared(FakeStage())
    normal = effects.slow_left
    assert normal > 0 and effects.time_scale() < 1.0
    effects.reset()
    s = FakeStage()
    s.boss = Dead()
    play_mode._on_room_cleared(s)
    assert effects.slow_left > normal                       # 보스를 쓰러뜨리면 더 길게


# ----- Codex T25: 피격 2장, 쓰러지는 3장 (11/21) -----
def test_hurt_pose_alternates_two_frames():
    room, p, e = _foe('slum')
    e.take_damage(1, from_x=p.x)
    assert e._body_frame() == ('enemy_slum_hurt', 1)
    tc.step(7)
    assert e._body_frame() == ('enemy_slum_hurt', 2)                   # 뒤로 더 젖혀 비틀


def test_killed_enemy_collapses_then_scatters():
    import game_world
    import sprites
    for kind in ('slum', 'thrower', 'hound', 'guard'):
        assert sprites.count(f'enemy_{kind}_death') == 3 and sprites.count(f'enemy_{kind}_hurt') == 2, kind
    room, p, e = _foe('slum')
    e.hp = 1
    assert e.take_damage(5, from_x=p.x)
    corpses = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Corpse']
    assert len(corpses) == 1 and corpses[0].frame() == ('enemy_slum_death', 1)
    c = corpses[0]
    tc.step(30)
    assert c.frame() == ('enemy_slum_death', 3)                         # 쓰러져 누워 있다
    tc.step(int(config.CORPSE_TIME * 60) + 10)
    assert c not in game_world.world[game_world.LAYER_EFFECT]           # 헤이즈로 흩어져 사라진다



# ----- Codex T26: 무기별 전용 자세 (11/21) -----
def _poses(p, frames):
    seen = []
    for _ in range(frames):
        name = p._body_frame()
        if not seen or seen[-1] != name:
            seen.append(name)
        tc.step(1)
    return seen


def test_knife_throw_uses_its_own_three_poses():
    room, p = tc.make_world()
    p.give_weapon('knife')
    assert p.request_attack()
    seen = _poses(p, 30)
    assert [s for s in seen if s[0] == 'n09_knife'] == [('n09_knife', 1), ('n09_knife', 2), ('n09_knife', 3)], seen


def test_gauntlet_fire_and_air_down_poses():
    room, p = tc.make_world()
    p.give_weapon('gauntlet')
    tc.set_gauge(p, 60)
    p.attack_held = True
    assert p.request_attack() and p.weapon.charging
    tc.step(5)
    assert p._body_frame() == ('n09_gauntlet', 1)                         # 충전
    tc.step(int(config.GAUNTLET_CHARGE_TIME['AWAKE'] * 60) + 5)
    p.attack_held = False
    tc.step(1)
    assert p._body_frame() == ('n09_gauntlet', 2)                         # 발사
    seen = _poses(p, 30)
    assert ('n09_gauntlet', 3) in seen                                    # 회수
    p.start_punch('blast_down')
    assert p._body_frame() == ('n09_gauntlet', 4)                         # 공중에서 아래로 쏘는 자세


def test_chain_throw_then_pull_poses():
    room, p = tc.make_world()
    p.give_weapon('chain')
    e = tc.freeze(tc.add_enemy('slum', p.x + 300, room, p))
    e.hp = e.max_hp = 1000
    p.mouse_x, p.mouse_y = e.center
    assert p.request_attack()
    seen = _poses(p, 60)
    chain = [s for s in seen if s[0] == 'n09_chain']
    assert chain[:2] == [('n09_chain', 1), ('n09_chain', 2)] and ('n09_chain', 3) in chain, seen   # 돌림 -> 던짐 -> 당김

if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
