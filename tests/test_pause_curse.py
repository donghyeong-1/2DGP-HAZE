"""일시정지 화면 '이번 판' 카드의 저주 표시 (2026-11-26 사용자 결정). 창 없이: python tests/test_pause_curse.py

- 저주가 걸려 있을 때만 카드 맨 위(무기 형태보다 위)에 저주 이름·짧은 내용·남은 전투방 수를 진홍색으로 보인다.
- 저주만 걸려 있고 증강·형태·아이템이 없어도 '아직 아이템이 없습니다' 대신 카드 내용이 뜬다.
- 한 줄(저주 · 이름 · 내용 · 전투방 n)은 가장 긴 것이 500px로 카드 안쪽(344px)을 넘어서, 형태 줄처럼
  머리 줄('저주' + 오른쪽 '전투방 n')과 내용 줄('이름 · 내용')로 나눈다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import curse  # noqa: E402
import pause_mode  # noqa: E402
import test_combat as tc  # noqa: E402


def _bare_player():
    _room, p = tc.make_world()
    p.items = []
    p.mutations = []
    p.forms = set()
    return p


def test_no_curse_no_row():
    p = _bare_player()
    assert pause_mode.curse_row(p) is None
    assert pause_mode.curse_row(None) is None


def test_curse_row_shows_name_short_text_and_rooms_left():
    p = _bare_player()
    curse.take(p, curse.CARD + 'frail')
    assert pause_mode.curse_row(p) == ('유리 몸 · 받는 피해 2배', '전투방 2')
    curse.on_room_clear(p, __import__('random').Random(1))
    assert pause_mode.curse_row(p)[1] == '전투방 1'                   # 남은 수가 줄어든다


def test_curse_alone_counts_as_something_to_show():
    p = _bare_player()
    assert not pause_mode.has_build(p)
    curse.take(p, curse.CARD + 'weak')
    assert pause_mode.has_build(p)


def test_curse_rows_fit_inside_the_card():
    import sdl2.sdlttf as ttf
    import assets
    ttf.TTF_Init()
    p = _bare_player()
    inner = pause_mode.BUILD_W - pause_mode.CURSE_INDENT - 28           # 내용 줄이 들어갈 폭
    for cid in curse.CURSES:
        p.curse = None
        curse.take(p, curse.CARD + cid)
        text, rooms = pause_mode.curse_row(p)
        assert assets.text_width(text, small=True) <= inner, (cid, assets.text_width(text, small=True), inner)
        assert assets.text_width('저주', small=True) + assets.text_width(rooms, small=True) + 40 <= pause_mode.BUILD_W - 56
        curse._lift(p)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
