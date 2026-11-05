"""헤이즈 게이지 단위 테스트 (pico2d 없이 실행). 실행: python tests/test_gauge.py 또는 pytest"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import config  # noqa: E402
from haze_gauge import AWAKE, CRITICAL, DEAD, FADE, NORMAL, HazeGauge  # noqa: E402


def gauge_at(value, cap=100):
    g = HazeGauge(cap)
    g.value = float(value)
    g.zone = g._zone_of(g.value)
    return g


def test_start_value_and_zone():
    g = HazeGauge()
    assert g.value == 30 and g.zone == NORMAL


def test_decay_every_3_seconds():
    g = HazeGauge()
    g.tick(2.9)
    assert g.value == 30
    g.tick(0.2)
    assert g.value == 29
    g.tick(6.0)
    assert g.value == 27


def test_high_haze_room_raises_instead_of_decay():
    g = HazeGauge()
    g.tick(2.0, high_haze=True)
    assert g.value == 31
    g.tick(3.0, high_haze=False)  # 방을 나가면 다시 감소
    assert g.value == 30


def test_zero_is_death():
    g = gauge_at(1)
    events = []
    g.listeners.append(lambda name, gauge: events.append(name))
    g.add(-1)
    assert g.value == 0 and g.zone == DEAD and 'dead' in events
    g.add(+50)  # 죽은 뒤에는 변하지 않는다
    assert g.value == 0


def test_overload_resets_to_30():
    g = gauge_at(95)
    events = []
    g.listeners.append(lambda name, gauge: events.append(name))
    g.add(+8)
    assert 'overload' in events
    assert g.value == config.OVERLOAD_RESET and g.zone == NORMAL
    assert g.stun_timer == config.OVERLOAD_STUN


def test_zone_boundaries_cap_100():
    expected = {1: FADE, 19: FADE, 20: NORMAL, 49: NORMAL, 50: AWAKE, 89: AWAKE, 90: CRITICAL, 99: CRITICAL}
    for value, zone in expected.items():
        assert gauge_at(value).zone == zone, (value, zone)


def test_zone_boundaries_cap_160():
    # 한계가 늘어도 각성 시작(50)과 페이드 경계는 절대값, 위험 시작만 cap-10을 따른다
    expected = {19: FADE, 20: NORMAL, 50: AWAKE, 149: AWAKE, 150: CRITICAL, 159: CRITICAL}
    for value, zone in expected.items():
        assert gauge_at(value, 160).zone == zone, (value, zone)


def test_enhance_threshold_and_cost():
    g = gauge_at(29)
    assert not g.can_enhance()
    g = gauge_at(30)
    assert g.can_enhance()
    assert g.use_enhance()
    assert g.value == 5 and g.enhanced
    assert not g.can_enhance()  # 강화 중에는 재사용 불가
    g.tick(config.ENHANCE_TIME + 0.1)
    assert not g.enhanced


def test_enhance_cost_upgrade_lowers_threshold():
    g = gauge_at(25)
    g.enhance_cost = 20  # 강화 효율 업그레이드
    assert g.can_enhance()


def test_drain_respects_floor():
    g = gauge_at(8)
    g.drain(10)
    assert g.value == config.GAUNTLET_FLOOR
    g.drain(10)
    assert g.value == config.GAUNTLET_FLOOR


def test_multipliers():
    assert gauge_at(10).zone_multipliers() == {'attack': 0.8, 'speed': 0.8}
    assert gauge_at(60).zone_multipliers() == {'attack': 1.5, 'speed': 1.25}
    assert gauge_at(95).zone_multipliers() == {'attack': 1.8, 'speed': 1.35}


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
