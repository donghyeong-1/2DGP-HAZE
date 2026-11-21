"""처음 하는 사람 안내 테스트 (창 없이). 실행: python tests/test_tutorial.py

2026-11-21 퀄리티 상승 계획 2-5 (docs/quality_plan.md): 설명서 없이 3분 안에 게이지 규칙을 알게 한다.
처음 그 상황이 되었을 때 한 번만 짧은 안내판을 띄운다(조작, 게이지, 페이드·각성·위험 구간, E 강화, 무기 바꾸기).
본 안내는 저장(meta)에 남아 다음 판에는 다시 나오지 않는다. 설정에서 끌 수 있다.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import config  # noqa: E402
import meta  # noqa: E402
import options  # noqa: E402
import tutorial  # noqa: E402
from haze_gauge import HazeGauge  # noqa: E402


class FakePlayer:
    def __init__(self, value=35.0):
        self.gauge = HazeGauge()
        self.gauge.value = float(value)
        self.gauge.zone = self.gauge._zone_of(float(value))
        self.weapons = [object(), None]


class FakeStage:
    def __init__(self, name):
        self.name = name


def fresh():
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')     # 사용자 저장 파일은 건드리지 않는다
    meta.reset()
    options.reset()


def shown(t, player, stage, seconds=0.1):
    t.update_with(player, stage, seconds)
    return t.current_id()


def test_controls_hint_in_the_hideout_once_per_save():
    fresh()
    t = tutorial.Tutorial()
    assert shown(t, FakePlayer(), FakeStage('hideout')) == 'move'
    t2 = tutorial.Tutorial()                                    # 다음 판 (같은 저장)
    assert shown(t2, FakePlayer(), FakeStage('hideout')) is None
    assert 'move' in meta.state['hints']


def test_gauge_and_zone_hints_come_the_first_time_each_zone_is_reached():
    fresh()
    meta.state['hints'].append('enhance')                       # 이 테스트는 구간 안내만 본다
    t = tutorial.Tutorial()
    p, s = FakePlayer(35), FakeStage('stage1')
    assert shown(t, p, s) == 'gauge'                           # 첫 전투 구역: 게이지 설명
    t.update_with(p, s, config.HINT_TIME + 0.1)                 # 다 보여 주고 넘어감
    for value, hint in ((10, 'fade'), (60, 'awake'), (95, 'critical')):
        p.gauge.value = float(value)
        p.gauge.zone = p.gauge._zone_of(float(value))
        assert shown(t, p, s) == hint, (value, t.current_id())
        t.update_with(p, s, config.HINT_TIME + 0.1)
    p.gauge.value, p.gauge.zone = 10.0, p.gauge._zone_of(10.0)
    assert shown(t, p, s) is None                               # 같은 구간은 다시 안 나온다


def test_enhance_hint_when_e_is_first_usable_and_weapon_hint_with_two_weapons():
    fresh()
    for hid in ('gauge', 'fade', 'awake', 'critical', 'move'):
        meta.state['hints'].append(hid)
    t = tutorial.Tutorial()
    p, s = FakePlayer(40), FakeStage('stage1')
    assert p.gauge.can_enhance() and shown(t, p, s) == 'enhance'
    t.update_with(p, s, config.HINT_TIME + 0.1)
    p.weapons[1] = object()
    assert shown(t, p, s) == 'weapon'


def test_hints_can_be_turned_off_in_options():
    fresh()
    options.show_hints = False
    t = tutorial.Tutorial()
    assert shown(t, FakePlayer(), FakeStage('hideout')) is None
    options.reset()
    assert options.show_hints is True


def test_every_hint_has_a_title_and_short_lines():
    for hid, (title, lines) in tutorial.HINTS.items():
        assert title and 1 <= len(lines) <= 3, hid
        assert all(len(line) <= 46 for line in lines), hid       # 한눈에 읽히게 짧게


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
