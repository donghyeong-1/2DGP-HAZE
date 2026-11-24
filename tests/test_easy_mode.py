"""초보자 모드 테스트 (v8 7일 차, 2026-11-25, 창 없이 실행). 실행: python tests/test_easy_mode.py

설정의 '초보자 모드'를 켜면
- 받는 피해(적·투사체·장치·가시·오버로드)가 config.EASY_DAMAGE_MULT배가 되고,
- 피격·적 기술·시간 경과로 '줄어드는' 게이지가 config.EASY_GAUGE_LOSS_MULT배가 된다.
- 게이지가 오르는 것과 내가 쓰는 비용(건틀릿 충전, E 강화)은 그대로다. 게이지 규칙(0% 사망, 100% 오버로드)도 그대로다.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')

import config  # noqa: E402
import options  # noqa: E402
from haze_gauge import HazeGauge  # noqa: E402
from player import Player  # noqa: E402
from room import Room  # noqa: E402

DT = 1 / 60


def make_player():
    room = Room.load('test_01')
    p = Player(room.spawn[0], room.spawn[1], room)
    for _ in range(30):
        p.update(DT)
    p.invuln_left = 0.0
    return p


def with_easy(on):
    options.reset()
    options.easy_mode = on


def test_easy_mode_is_off_by_default_and_saves():
    options.reset()
    assert options.easy_mode is False
    assert options.damage_taken_mult() == 1.0 and options.gauge_loss_mult() == 1.0
    old = options.PATH
    options.PATH = os.path.join(tempfile.mkdtemp(), 'easy.json')
    try:
        options.toggle_easy()
        assert options.easy_mode and options.damage_taken_mult() == config.EASY_DAMAGE_MULT
        options.reset()
        assert not options.easy_mode                       # reset은 기본값
        options.load()
        assert options.easy_mode                           # 저장한 값이 다음 실행에 남는다
    finally:
        options.PATH = old
        options.reset()


def test_easy_mode_cuts_damage_taken():
    for on, want in ((False, 20), (True, round(20 * config.EASY_DAMAGE_MULT))):
        with_easy(on)
        p = make_player()
        hp = p.hp
        p.take_hit(20, source='test')
        assert hp - p.hp == want, (on, hp - p.hp)
    options.reset()


def test_easy_mode_never_turns_a_hit_into_zero_damage():
    with_easy(True)
    p = make_player()
    hp = p.hp
    p.take_hit(1, source='test')
    assert hp - p.hp == 1
    options.reset()


def test_easy_mode_softens_gauge_loss_from_hits():
    for on in (False, True):
        with_easy(on)
        p = make_player()
        p.gauge.value = 50.0
        p.take_hit(5, gauge_delta=-10, source='test')                  # 사냥개처럼 게이지를 깎는 공격
        loss = (config.LOSS_DAMAGED - 10) * (config.EASY_GAUGE_LOSS_MULT if on else 1.0)
        assert abs(p.gauge.value - (50.0 + loss)) < 1e-6, (on, p.gauge.value)
    options.reset()


def test_easy_mode_keeps_gauge_gains_and_player_costs():
    with_easy(True)
    p = make_player()
    p.gauge.value = 50.0
    p.take_hit(5, gauge_delta=15, source='test')                       # 간수처럼 게이지를 올리는 공격: 최종 +10 그대로
    assert abs(p.gauge.value - (50.0 + config.LOSS_DAMAGED + 15)) < 1e-6
    g = HazeGauge()
    g.value = 50.0
    g.add(3, 'hit')
    assert g.value == 53.0
    g.drain(10)                                                        # 건틀릿 충전 비용은 그대로
    assert g.value == 43.0
    g.add(-25, 'enhance')                                              # E 강화 비용도 그대로
    assert g.value == 18.0
    options.reset()


def test_easy_mode_slows_time_decay():
    for on in (False, True):
        with_easy(on)
        g = HazeGauge()
        g.value = 50.0
        for _ in range(int(config.GAUGE_DECAY_INTERVAL * 60) + 1):     # 감소 주기 한 번
            g.tick(DT)
        want = 50.0 - config.GAUGE_DECAY_AMOUNT * (config.EASY_GAUGE_LOSS_MULT if on else 1.0)
        assert abs(g.value - want) < 1e-6, (on, g.value)
    options.reset()


def test_easy_mode_keeps_gauge_death_and_overload_rules():
    with_easy(True)
    g = HazeGauge()
    g.value = 2.0
    g.add(-10, 'damaged')                                              # 줄어든 양이 작아져도 0이면 사망
    assert g.value == 0 and g.zone == 'DEAD'
    g = HazeGauge()
    g.value = 95.0
    g.add(10, 'hit')                                                   # 오버로드는 그대로
    assert g.value == config.OVERLOAD_RESET
    options.reset()


def test_easy_mode_cuts_overload_damage():
    for on in (False, True):
        with_easy(on)
        p = make_player()
        hp = p.hp
        p.gauge.value = p.gauge.cap - 1.0
        p.gauge.add(5, 'hit')
        full = int(p.max_hp * config.OVERLOAD_DAMAGE_RATIO)
        want = round(full * config.EASY_DAMAGE_MULT) if on else full
        assert hp - p.hp == want, (on, hp - p.hp)
    options.reset()


def test_options_screen_has_easy_mode_row_that_toggles():
    import options_mode
    options.reset()
    old = options.PATH
    options.PATH = os.path.join(tempfile.mkdtemp(), 'row.json')
    try:
        names = [n for n, _, _ in options_mode.lines()]
        assert '초보자 모드' in names
        row = options_mode.ROWS.index('easy')
        assert options_mode.lines()[row][1] == '끔'
        options_mode.change('easy', 1)
        assert options.easy_mode and options_mode.lines()[row][1] == '켬'
        _v, _t, x, w = options_mode._segments('easy')[0]                # '끔' 칸을 누른다
        assert options_mode.click(x + 5, options_mode.ROW_Y[row])
        assert not options.easy_mode
    finally:
        options.PATH = old
        options.reset()


def test_options_panel_still_fits_the_screen():
    import options_mode
    assert options_mode.PANEL_Y >= 0 and options_mode.PANEL_Y + options_mode.PANEL_H <= config.SCREEN_H
    lowest = min(options_mode.ROW_Y) - options_mode.ROW_H // 2
    b = options_mode.back_button
    assert b.y + b.h <= lowest                                         # 돌아가기 버튼이 마지막 줄과 겹치지 않는다
    assert b.y >= 34 + 40                                              # 아래 키 안내(kit.footer y=34)와도 겹치지 않는다
    top = max(options_mode.ROW_Y) + options_mode.ROW_H // 2
    assert top < options_mode.PANEL_Y + options_mode.PANEL_H - 40 - 21  # 제목(큰 글자)과 첫 줄이 겹치지 않는다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
