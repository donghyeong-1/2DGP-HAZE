"""N1-2 (2026-11-27) 설정 화면(mist)은 고른 줄의 설명만 보인다 (창 없이). 실행: python tests/test_n1_options.py

U1-2 표 19번: 열한 줄 모두 이름 아래 설명이 늘 떠 있어 위계가 평평했다.
- mist: 고른 줄은 이름 + 설명(전과 같은 자리), 고르지 않은 줄은 이름만 줄의 세로 가운데(값 글자와 같은 높이)에.
- 줄의 가운데(ROW_Y)와 누르는 자리는 그대로. 다른 스킨은 그대로(설명 모두).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')
import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')

import config  # noqa: E402
import options_mode as om  # noqa: E402
import test_ui_skin as tu  # noqa: E402


def _texts(skin, sel):
    old = config.UI_SKIN
    config.UI_SKIN = skin
    om.selected = sel
    try:
        with tu._Recorder() as r:
            om.draw_mist_panel() if skin == 'mist' else om.draw_panel()
    finally:
        config.UI_SKIN = old
    return [row for row in r.log if row[0] == 'draw_text']


def test_only_the_selected_row_shows_its_description():
    for sel in (0, 5, len(om.ROWS) - 1):
        rows = _texts('mist', sel)
        shown = [item for item in om.ROWS if any(t[3] == om.DESCS[item] for t in rows)]
        assert shown == [om.ROWS[sel]], (sel, shown)


def test_unselected_names_sit_on_the_row_middle_and_rows_do_not_move():
    rows = _texts('mist', 0)
    for i, item in enumerate(om.ROWS):
        ys = {t[2] for t in rows if t[3] == om.NAMES[item]}
        if i == 0:
            assert om.ROW_Y[0] + om.MIST_NAME_DY in ys, ys            # 고른 줄: 전과 같은 자리 (설명 위)
        else:
            assert om.ROW_Y[i] + om.MIST_NAME_MID_DY in ys and om.ROW_Y[i] + om.MIST_NAME_DY not in ys, (item, ys)   # 글자 그림자(2px 아래)도 함께 기록된다
    a, b = _texts('mist', 0), _texts('mist', 3)
    ya = {t[3]: t[2] for t in a if t[3] == om.NAMES['hints']}
    yb = {t[3]: t[2] for t in b if t[3] == om.NAMES['hints']}
    assert ya == yb                                                       # 다른 줄을 골라도 이 줄은 그대로


def test_back_row_selected_shows_no_description():
    rows = _texts('mist', len(om.ROWS))                                  # '돌아가기'
    assert not any(t[3] in om.DESCS.values() for t in rows)


def test_other_skins_keep_every_description():
    rows = _texts('plate', 0)
    assert all(any(t[3] == om.DESCS[item] for t in rows) for item in om.ROWS)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
