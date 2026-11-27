"""S2-1 (2026-11-27) 게임패드 십자 위 = 물약 마시기 (사용자 결정 "물약 버튼 십자 위로 결정"). 창 없이: python tests/test_s2_pad_potion.py

- 플레이 중 십자 위를 누른 순간 물약 한 병을 마신다(키보드 Q와 같은 drink_potion). 누르고 있어도 한 번만.
- 십자 위는 플레이 중 이동에 섞이지 않는다(전에는 y 방향에 들어갔지만 플레이에서 '위'는 쓰지 않았다.
  아래 스틱과 함께 누르면 '아래'를 지워 버렸다). 십자 아래·좌우는 그대로 이동.
- 메뉴(플레이가 아닌 모드)에서는 십자 위가 전처럼 항목 이동(↑)이고 물약은 줄지 않는다.
- 패드 조작표의 물약 줄은 십자 위, 패드일 때 물약 키 이름도 십자 위.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')
import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')

import sdl2  # noqa: E402

import config  # noqa: E402
import gamepad  # noqa: E402
import input_device as dev  # noqa: E402
import keybinds  # noqa: E402
import test_combat as tc  # noqa: E402

PAD_UP = '십자↑'


def pad(buttons=(), lx=0.0, ly=0.0, rx=0.0, ry=0.0):
    return gamepad.PadState(set(buttons), lx, ly, rx, ry)


def _keyboard():
    dev.note_event(sdl2.SDL_KEYDOWN, window_id=1)
    dev.note_pad(pad())


def test_dpad_up_in_play_drinks_a_potion_once():
    _room, p = tc.make_world()
    p.hp = 20
    t = gamepad.Translator()
    a = t.play(pad({'dpup'}), 1 / 60)
    assert 'potion' in a['press']
    gamepad.apply_play(p, a, origin=(0, 0))
    assert p.potions == config.POTION_START - 1
    assert p.hp == min(p.max_hp, 20 + config.POTION_HEAL)
    tc.step(int(config.POTION_COOLDOWN * 60) + 2)
    p.hp = 20
    a = t.play(pad({'dpup'}), 1 / 60)                   # 계속 누르고 있다: 새로 누른 것이 아니다
    assert 'potion' not in a['press']
    gamepad.apply_play(p, a, origin=(0, 0))
    assert p.potions == config.POTION_START - 1


def test_dpad_up_is_not_movement_in_play_and_does_not_cancel_down():
    t = gamepad.Translator()
    a = t.play(pad({'dpup'}, ly=0.9), 1 / 60)             # 스틱 아래 + 십자 위
    assert a['down'] is True and a['move'] == 0
    assert t.play(pad({'dpdown'}), 1 / 60)['down'] is True
    assert t.play(pad({'dpleft'}), 1 / 60)['move'] == -1


def test_dpad_up_in_menu_moves_the_cursor_and_keeps_potions():
    _room, p = tc.make_world()
    p.hp = 20
    t = gamepad.Translator()
    assert t.menu(pad({'dpup'}), 1 / 60) == ['up']
    assert p.potions == config.POTION_START and p.hp == 20


def test_pad_controls_list_dpad_up_for_potion():
    import pause_mode
    dev.note_pad(pad(['a']))
    try:
        rows = dict((what, keys) for keys, what in pause_mode.controls())
        row = [k for w, k in rows.items() if w.startswith('물약')]
        assert row == [PAD_UP], rows
        assert not any('키보드만' in w for w in rows)
        assert keybinds.label('potion') == PAD_UP
    finally:
        _keyboard()
    assert keybinds.label('potion') == 'Q'


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
