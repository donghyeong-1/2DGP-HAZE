"""키 설정 테스트 (창 없이). 실행: python tests/test_keybinds.py

2026-11-21 퀄리티 상승 계획 2-6 (docs/quality_plan.md): 키보드 동작 키를 설정에서 바꾼다.
- 동작마다 키 두 칸(기본·보조). 기본 칸은 비울 수 없고 보조 칸은 비울 수 있다.
- 이미 다른 동작이 쓰는 키를 넣으면 두 칸이 맞바뀐다 (한 키가 두 동작을 하지 않게).
- Esc(일시정지)·F1 같은 예약 키는 넣을 수 없다. 마우스(좌클릭 공격·우클릭 대시)는 그대로다.
- 바꾸면 설정 파일(~/.haze_options.json)에 저장되고, '기본값으로'로 되돌린다.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')   # 깨진 저장 시험이 사용자 폴더에 기록을 남기지 않게

import sdl2  # noqa: E402

import keybinds  # noqa: E402
import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')     # 사용자 설정 파일을 건드리지 않는다


def test_defaults_match_old_controls():
    keybinds.reset()
    assert keybinds.action_for(sdl2.SDLK_a) == 'left'
    assert keybinds.action_for(sdl2.SDLK_d) == 'right'
    assert keybinds.action_for(sdl2.SDLK_SPACE) == 'jump'
    assert keybinds.action_for(sdl2.SDLK_w) == 'jump'                 # 보조 칸
    assert keybinds.action_for(sdl2.SDLK_LSHIFT) == 'dash'
    assert keybinds.action_for(sdl2.SDLK_e) == 'enhance'
    assert keybinds.action_for(sdl2.SDLK_1) == 'weapon1'
    assert keybinds.action_for(sdl2.SDLK_z) is None


def test_bind_moves_key_and_swaps_conflicts():
    keybinds.reset()
    assert keybinds.bind('enhance', 0, sdl2.SDLK_r)
    assert keybinds.action_for(sdl2.SDLK_r) == 'enhance'
    assert keybinds.action_for(sdl2.SDLK_e) is None                  # 예전 키는 더 이상 아무것도 안 한다
    assert keybinds.bind('enhance', 0, sdl2.SDLK_f)                    # F는 상호작용이 쓰고 있다 -> 맞바꾼다
    assert keybinds.action_for(sdl2.SDLK_f) == 'enhance'
    assert keybinds.action_for(sdl2.SDLK_r) == 'interact'
    assert keybinds.bind('dash', 1, sdl2.SDLK_SPACE)                   # 점프의 기본 칸 키를 대시 보조로 -> 점프가 빈 키를 받는다
    assert keybinds.action_for(sdl2.SDLK_SPACE) == 'dash'
    assert keybinds.keys('jump')[0] is not None                        # 기본 칸은 비지 않는다


def test_reserved_keys_and_clearing():
    keybinds.reset()
    assert not keybinds.bind('jump', 0, sdl2.SDLK_ESCAPE)              # 일시정지 키는 못 넣는다
    assert not keybinds.bind('jump', 0, sdl2.SDLK_F1)
    assert keybinds.action_for(sdl2.SDLK_SPACE) == 'jump'
    keybinds.clear('jump', 1)                                          # 보조 칸 비우기
    assert keybinds.action_for(sdl2.SDLK_w) is None
    keybinds.clear('jump', 0)                                          # 기본 칸은 비우지 않는다
    assert keybinds.action_for(sdl2.SDLK_SPACE) == 'jump'


def test_key_names_are_short_and_readable():
    keybinds.reset()
    assert keybinds.key_name(sdl2.SDLK_LSHIFT) == 'Shift'
    assert keybinds.key_name(sdl2.SDLK_SPACE) == 'Space'
    assert keybinds.key_name(sdl2.SDLK_a) == 'A'
    assert keybinds.key_name(sdl2.SDLK_UP) == '↑'
    assert keybinds.key_name(None) == '-'
    assert keybinds.label('jump') == 'Space/W'                        # 안내판·일시정지에 쓰는 글자
    assert keybinds.label('jump', first=True) == 'Space'


def test_saved_with_options_and_bad_data_ignored():
    keybinds.reset()
    options.reset()
    path = os.path.join(tempfile.mkdtemp(), 'opt.json')
    old = options.PATH
    options.PATH = path
    try:
        keybinds.bind('enhance', 0, sdl2.SDLK_r)                       # 바꾸면 바로 저장된다
        keybinds.reset()
        options.load(path)
        assert keybinds.action_for(sdl2.SDLK_r) == 'enhance'
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        data['keys'] = {'jump': ['x', None], 'left': [sdl2.SDLK_ESCAPE, None], 'nope': [1, 2]}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        keybinds.reset()
        options.load(path)                                             # 이상한 값은 무시하고 기본을 쓴다
        assert keybinds.action_for(sdl2.SDLK_SPACE) == 'jump'
        assert keybinds.action_for(sdl2.SDLK_a) == 'left'
        keybinds.bind('swap', 0, sdl2.SDLK_r)
        keybinds.reset_defaults()                                      # '기본값으로' (v7: 무기 바꾸기 기본 Tab, Q는 물약)
        assert keybinds.action_for(sdl2.SDLK_TAB) == 'swap' and keybinds.action_for(sdl2.SDLK_q) == 'potion'
    finally:
        options.PATH = old
        keybinds.reset()
        options.reset()


class Ev:
    def __init__(self, kind, key):
        self.type, self.key = kind, key


def test_player_uses_bound_keys():
    import player as player_mod
    keybinds.reset()
    keybinds.bind('right', 0, sdl2.SDLK_l)
    p = player_mod.Player.__new__(player_mod.Player)
    p.left = p.right = p.down = False
    p.handle_event(Ev(sdl2.SDL_KEYDOWN, sdl2.SDLK_l))
    assert p.right
    p.handle_event(Ev(sdl2.SDL_KEYUP, sdl2.SDLK_l))
    assert not p.right
    p.handle_event(Ev(sdl2.SDL_KEYDOWN, sdl2.SDLK_d))                # 예전 키는 안 먹는다
    assert not p.right
    keybinds.reset()


def test_options_row_opens_key_screen_and_screen_binds():
    import game_framework
    import keys_mode
    import options_mode
    keybinds.reset()
    game_framework.stack[:] = [options_mode]
    row = options_mode.ITEMS.index('keys')
    x = options_mode.VALUE_X + 20
    assert options_mode.click(x, options_mode.ROW_Y[row])               # '키 바꾸기' 칸을 누르면 키 창이 열린다
    assert game_framework.stack[-1] is keys_mode
    assert options_mode.lines()[row][1] == '기본'
    keys_mode.listening = ('enhance', 0)
    keys_mode.press_key(sdl2.SDLK_f)                                    # 상호작용 키 -> 맞바꿈 안내
    assert keybinds.action_for(sdl2.SDLK_f) == 'enhance' and '서로 바꿨습니다' in keys_mode.message
    assert options_mode.lines()[row][1] == '변경됨'
    keys_mode.listening = ('jump', 1)
    keys_mode.press_key(sdl2.SDLK_BACKSPACE)                            # 보조 칸 비우기
    assert keybinds.keys('jump')[1] is None
    keys_mode.listening = ('jump', 0)
    keys_mode.press_key(sdl2.SDLK_ESCAPE)                               # 취소: 그대로
    assert keybinds.keys('jump')[0] == sdl2.SDLK_SPACE and keys_mode.listening is None
    keys_mode.listening = ('jump', 0)
    keys_mode.press_key(sdl2.SDLK_F1)                                   # 예약 키: 안 들어간다
    assert keybinds.keys('jump')[0] == sdl2.SDLK_SPACE and '쓸 수 없습니다' in keys_mode.message
    assert keys_mode.ROW_Y[-1] - 30 > keys_mode.buttons[0].y + keys_mode.buttons[0].h   # 버튼과 겹치지 않는다
    assert keys_mode.PANEL_Y > 66 and keys_mode.PANEL_Y + keys_mode.PANEL_H <= 1080
    game_framework.stack[:] = []
    keybinds.reset()


def test_help_texts_follow_bound_keys():
    import pause_mode
    import title_mode
    import tutorial
    keybinds.reset()
    assert 'Shift' in title_mode.controls_text() and 'E 강화' in title_mode.controls_text()
    keybinds.bind('enhance', 0, sdl2.SDLK_r)
    keybinds.bind('dash', 0, sdl2.SDLK_LCTRL)
    assert 'R 강화' in title_mode.controls_text() and 'Ctrl' in title_mode.controls_text()
    keys = [k for k, _ in pause_mode.controls()]
    assert 'R' in keys and any('Ctrl' in k for k in keys)
    title, lines = tutorial.hint_text('enhance')
    assert title.startswith('R') and lines[0].startswith('R')
    assert any('Ctrl' in line for line in tutorial.hint_text('move')[1])
    keybinds.reset()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
