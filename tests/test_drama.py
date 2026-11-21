"""상황에 따른 효과음·연출·타격감 테스트 (창 없이). 실행: python tests/test_drama.py

2026-11-21 사용자 요청: 빠진 효과음을 채우고, 타격감과 체력·게이지 상태에 따른 극적인 효과를 더한다.
- 식칼 던지기: 구간마다 다른 소리(throw_fade·throw·throw_awake·throw_critical), E 강화는 throw_enhanced.
- 사슬 던지기: chain_throw_fade·chain_throw·chain_throw_awake·chain_throw_critical·chain_throw_enhanced.
  위험 구간·강화 갈고리는 묵직하게 박힌다(chain_latch_heavy).
- 궁극기 마지막 일격: 무기마다 다른 소리(ult_final_<무기>).
- 각성 구간에 들어서면 zone_awake. 구간이 바뀌면 그 구간 색으로 화면이 잠깐 번쩍인다(번쩍임 줄이기면 약하게).
- 체력 30% 이하·위험 구간에서는 심장 소리(heartbeat)가 뛰고(15% 이하면 더 빠르게), 체력이 낮으면 화면 가장자리가 붉게 맥동.
- 페이드 구간에서는 음악이 작아진다(먹먹하게).
- 피해 숫자: 적이 맞으면 그 자리에 피해가 떠오른다(구간·강화 색). 설정에서 끌 수 있다.
- 방의 마지막 적을 쓰러뜨리면 잠깐 멈추고(hit stop) kill_last 소리.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import assets  # noqa: E402
import config  # noqa: E402
import drama  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import options  # noqa: E402
import test_combat as tc  # noqa: E402
from test_sfx import Recorder  # noqa: E402

ZONE_GAUGE = {'FADE': 10, 'NORMAL': 35, 'AWAKE': 60, 'CRITICAL': 90}


def _fire(wid, zone, enhanced=False):
    room, p = tc.make_world()
    p.give_weapon(wid)
    tc.set_gauge(p, ZONE_GAUGE[zone] if not enhanced else 60)
    e = tc.freeze(tc.add_enemy('slum', p.x + 300, room, p))
    e.hp = e.max_hp = 10 ** 5
    p.mouse_x, p.mouse_y = p.x + 600, e.center[1]
    if enhanced:
        assert p.request_enhance()
    with Recorder() as rec:
        assert p.request_attack()
        tc.step(40)
    return rec.names


def test_knife_throw_sounds_follow_zone_and_enhance():
    want = {'FADE': 'throw_fade', 'NORMAL': 'throw', 'AWAKE': 'throw_awake', 'CRITICAL': 'throw_critical'}
    for zone, name in want.items():
        assert name in _fire('knife', zone), zone
    assert 'throw_enhanced' in _fire('knife', 'NORMAL', enhanced=True)


def test_chain_throw_sounds_follow_zone_and_heavy_latch():
    want = {'FADE': 'chain_throw_fade', 'NORMAL': 'chain_throw', 'AWAKE': 'chain_throw_awake',
            'CRITICAL': 'chain_throw_critical'}
    for zone, name in want.items():
        names = _fire('chain', zone)
        assert name in names, (zone, names)
    assert 'chain_latch_heavy' in _fire('chain', 'CRITICAL')
    names = _fire('chain', 'NORMAL', enhanced=True)
    assert 'chain_throw_enhanced' in names and 'chain_latch_heavy' in names
    assert 'chain_latch' in _fire('chain', 'NORMAL')


def test_ultimate_finisher_sound_per_weapon():
    import test_ultimate as tu
    for wid in ('pipe', 'knife', 'gauntlet', 'chain'):
        room, p, foes = tu.stacked(90, 3, [150])
        if wid != 'pipe':
            p.give_weapon(wid)
            for _ in range(3):
                p.gauge.enhance_level = 3
        with Recorder() as rec:
            assert p.request_attack()
            tu.run_out_ultimate()
        assert rec.names.count(f'ult_final_{wid}') == 1, (wid, rec.names)


def test_entering_awake_plays_sting_and_zone_flash():
    room, p = tc.make_world()
    tc.set_gauge(p, 45)
    drama.reset()
    with Recorder() as rec:
        p.gauge.add(10, 'hit')                                         # 45 -> 55: 각성
        tc.step(1)
    assert 'zone_awake' in rec.names, rec.names
    color, k = drama.zone_flash()
    assert k > 0 and color == drama.ZONE_FLASH['AWAKE'][0]
    drama.tick(1.0, p)
    assert drama.zone_flash()[1] == 0.0                                # 잠깐만 번쩍인다
    options.reduce_flash = True
    drama.on_zone('CRITICAL')
    assert drama.zone_flash()[1] <= drama.ZONE_FLASH['CRITICAL'][1] * options.FLASH_SCALE + 1e-9
    options.reduce_flash = False


def test_heartbeat_speeds_up_as_health_drops():
    assert drama.heartbeat_interval(0.8, 'NORMAL') is None
    assert drama.heartbeat_interval(0.3, 'NORMAL') == drama.HEART_SLOW
    assert drama.heartbeat_interval(0.1, 'NORMAL') == drama.HEART_FAST
    assert drama.heartbeat_interval(0.9, 'CRITICAL') == drama.HEART_CRITICAL
    room, p = tc.make_world()
    p.hp = int(p.max_hp * 0.1)
    drama.reset()
    with Recorder() as rec:
        for _ in range(int(3.0 * 60)):
            drama.tick(1 / 60, p)
    beats = rec.names.count('heartbeat')
    assert 3.0 / drama.HEART_FAST - 1 <= beats <= 3.0 / drama.HEART_FAST + 1, beats
    assert drama.low_hp_pulse(0.1, 0.0) >= 0 and drama.low_hp_pulse(0.8, 0.3) == 0.0   # 체력이 넉넉하면 붉은 가장자리 없음


def test_music_is_muffled_in_fade():
    assert drama.music_duck('FADE') < 1.0 and drama.music_duck('NORMAL') == 1.0
    assert options.volume(config.MUSIC_VOLUME, options.music_level) * drama.music_duck('FADE') < \
        options.volume(config.MUSIC_VOLUME, options.music_level)


def test_damage_numbers_pop_on_hits_and_can_be_turned_off():
    room, p = tc.make_world()
    tc.set_gauge(p, 60)                                                # 각성 색
    e = tc.freeze(tc.add_enemy('slum', p.x + 100, room, p))
    e.hp = e.max_hp = 1000
    e.take_damage(37)
    nums = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'DamageNumber']
    assert len(nums) == 1 and nums[0].text == '37' and nums[0].color == drama.DAMAGE_COLORS['AWAKE']
    options.show_damage = False
    try:
        e.take_damage(10)
        nums = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'DamageNumber']
        assert len(nums) == 1                                          # 꺼 두면 더 생기지 않는다
    finally:
        options.show_damage = True


def test_last_kill_in_room_freezes_and_sounds():
    import play_mode

    class FakeStage:
        boss = None

    effects.reset()
    with Recorder() as rec:
        play_mode._on_room_cleared(FakeStage())
    assert 'kill_last' in rec.names
    assert effects.hit_stop_left >= drama.LAST_KILL_STOP


def test_new_sounds_exist():
    for name in drama.NEW_SOUNDS:
        assert os.path.exists(os.path.join(HERE, '..', 'assets', 'sfx', name + '.wav')), name


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
