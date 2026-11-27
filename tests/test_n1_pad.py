"""N1-3 (2026-11-27) 키 안내가 마지막으로 쓴 입력 장치를 따른다 (창 없이). 실행: python tests/test_n1_pad.py

U1-2 표 20번: 게임패드를 써도 모든 안내가 'Enter'·'Esc'·'F'·'W S'로 나왔다.
- 패드 버튼을 누르거나 스틱을 크게 기울이면 패드, 키보드를 누르거나 마우스를 누르거나 크게 움직이면 키보드.
  스틱의 미세한 흔들림·마우스의 작은 떨림은 장치를 바꾸지 않는다. 패드가 메뉴에 넣는 가짜 키 이벤트(창 번호 0)도 키보드로 치지 않는다.
- 패드 이름은 지금 패드 배치(gamepad.PLAY_BUTTONS, 메뉴: A 확인·B 뒤로·십자 이동)를 따른다.
- 키보드로 돌아오면 키 설정을 바꾼 키가 그대로 나온다(U1).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')
import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')

import sdl2  # noqa: E402

import gamepad  # noqa: E402
import input_device as dev  # noqa: E402
import keybinds  # noqa: E402


def _pad(buttons=(), lx=0.0, ly=0.0, rx=0.0, ry=0.0):
    return gamepad.PadState(set(buttons), lx, ly, rx, ry)


def _keyboard():
    dev.note_event(sdl2.SDL_KEYDOWN, window_id=1)
    dev.note_pad(_pad())                                     # 패드 버튼을 모두 뗀 상태로 (다음 테스트의 누름이 새로 누른 것이 되게)


def test_pad_press_switches_labels_to_pad_buttons_and_keyboard_switches_back():
    keybinds.reset()
    _keyboard()
    assert not dev.is_pad() and keybinds.label('interact', first=True) == 'F'
    dev.note_pad(_pad(['a']))
    assert dev.is_pad()
    assert keybinds.label('jump', first=True) == 'A' and keybinds.label('interact', first=True) == 'Y'
    assert keybinds.label('enhance', first=True) == 'RB' and keybinds.label('dash', first=True) == 'B'
    assert keybinds.label('swap', first=True) == 'LB'
    assert keybinds.badge('enhance') == 'R' and keybinds.badge('weapon1') == ''      # 지름 32px 배지: 한 글자, 무기 칸은 그리지 않음
    _keyboard()
    assert not dev.is_pad() and keybinds.label('jump', first=True) == 'Space'
    assert keybinds.badge('enhance') == 'E' and keybinds.badge('weapon2') == '2'


def test_small_stick_or_mouse_jitter_does_not_switch():
    _keyboard()
    dev.note_pad(_pad(lx=0.25, ry=-0.3))                   # 손을 얹은 스틱의 흔들림
    assert not dev.is_pad()
    dev.note_pad(_pad(lx=0.9))                              # 크게 기울임
    assert dev.is_pad()
    dev.note_event(sdl2.SDL_MOUSEMOTION, window_id=1, xrel=2, yrel=1)    # 책상 진동 정도
    assert dev.is_pad()
    dev.note_event(sdl2.SDL_MOUSEMOTION, window_id=1, xrel=30, yrel=4)
    assert not dev.is_pad()


def test_menu_keys_injected_by_the_pad_do_not_count_as_keyboard():
    dev.note_pad(_pad(['a']))
    dev.note_event(sdl2.SDL_KEYDOWN, window_id=0)          # gamepad._push_key가 넣은 Enter
    assert dev.is_pad()


def test_held_pad_button_does_not_steal_back_from_the_keyboard():
    dev.note_pad(_pad(['x']))
    dev.note_event(sdl2.SDL_KEYDOWN, window_id=1)           # X를 누른 채 키보드를 눌렀다
    dev.note_pad(_pad(['x']))                                # 계속 누르고 있던 버튼: 새로 누른 것이 아니다
    assert not dev.is_pad()


def test_footer_pairs_become_pad_buttons_and_keyboard_only_keys_drop():
    pairs = [('W S', '선택'), ('A D', '값 변경'), ('Enter', '확인'), ('Esc', '닫기'), ('O', '설정')]
    _keyboard()
    assert dev.footer(pairs) == pairs
    dev.note_pad(_pad(['b']))
    assert dev.footer(pairs) == [('↑↓', '선택'), ('←→', '값 변경'), ('A', '확인'), ('B', '닫기')]
    assert dev.key('Enter') == 'A'
    _keyboard()


def test_rebound_keys_still_show_on_the_keyboard():
    keybinds.reset()
    keys = dict(keybinds.to_json())
    keys['interact'] = [sdl2.SDLK_g, None]
    keybinds.load_json(keys)
    try:
        import pedestal
        _keyboard()
        assert pedestal.Pedestal(0, 0, 'cap', 'gold').prompt() == 'G 획득'
        dev.note_pad(_pad(['y']))
        assert pedestal.Pedestal(0, 0, 'cap', 'gold').prompt() == 'Y 획득'
    finally:
        keybinds.reset()
        _keyboard()


def test_pad_controls_and_hints_read_like_a_pad():
    import pause_mode
    import tutorial
    dev.note_pad(_pad(['a']))
    try:
        keys = ' '.join(k for k, _ in pause_mode.controls())
        assert '스틱' in keys and 'Space' not in keys and '좌클릭' not in keys, keys
        lines = ' '.join(tutorial.hint_text('move')[1])
        assert '스틱' in lines and '우클릭' not in lines and '좌클릭' not in lines, lines
        assert 'LB' in ' '.join(tutorial.hint_text('weapon')[1])
    finally:
        _keyboard()
    assert 'Space' in ' '.join(k for k, _ in pause_mode.controls())


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
