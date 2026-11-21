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


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
