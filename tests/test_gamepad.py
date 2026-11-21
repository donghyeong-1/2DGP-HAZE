"""게임패드 테스트 (패드 없이, 변환 규칙만). 실행: python tests/test_gamepad.py

2026-11-21 퀄리티 상승 계획 2-6 (docs/quality_plan.md): 패드만으로 끝까지 플레이한다 (Xbox 배치).
플레이: 왼쪽 스틱·D패드 이동, A 점프, B 대시, X 공격(누르고 있으면 충전), RB 강화(E), LB 무기 바꾸기,
Y 상호작용(F), 오른쪽 스틱 조준, Start 일시정지.
메뉴: 위아래·좌우(스틱·D패드, 누르고 있으면 반복) -> 화살표 키, A -> Enter, B -> Esc (타이틀에서는 B 무시).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import gamepad  # noqa: E402
from gamepad import PadState  # noqa: E402


def pad(buttons=(), lx=0.0, ly=0.0, rx=0.0, ry=0.0):
    return PadState(set(buttons), lx, ly, rx, ry)


def test_stick_deadzone_and_move_direction():
    t = gamepad.Translator()
    assert t.play(pad(lx=0.12), 1 / 60)['move'] == 0             # 데드존 안: 안 움직인다
    assert t.play(pad(lx=0.8), 1 / 60)['move'] == 1
    assert t.play(pad(lx=-0.8), 1 / 60)['move'] == -1
    assert t.play(pad({'dpright'}), 1 / 60)['move'] == 1          # D패드도 된다
    assert t.play(pad(ly=0.9), 1 / 60)['down'] is True            # 아래 (SDL 축은 아래가 +)


def test_buttons_fire_once_on_press_and_report_release():
    t = gamepad.Translator()
    a = t.play(pad({'a'}), 1 / 60)
    assert 'jump' in a['press']
    a = t.play(pad({'a'}), 1 / 60)
    assert 'jump' not in a['press']                               # 누르고 있어도 한 번만
    a = t.play(pad(), 1 / 60)
    assert 'jump' in a['release']                                 # 떼면 낮은 점프 처리용
    names = {'b': 'dash', 'x': 'attack', 'rb': 'enhance', 'lb': 'swap', 'y': 'interact', 'start': 'pause'}
    for button, action in names.items():
        t = gamepad.Translator()
        assert action in t.play(pad({button}), 1 / 60)['press'], button


def test_right_stick_aims_and_keeps_last_direction():
    t = gamepad.Translator()
    assert t.play(pad(rx=0.1), 1 / 60)['aim'] is None              # 데드존: 조준 안 바꿈
    ax, ay = t.play(pad(rx=1.0, ry=0.0), 1 / 60)['aim']
    assert ax > 0.99 and abs(ay) < 1e-6
    ax, ay = t.play(pad(rx=0.0, ry=-1.0), 1 / 60)['aim']
    assert ay > 0.99                                               # 스틱 위 = 화면 위 (y 뒤집음)


def test_menu_keys_with_repeat_and_title_ignores_b():
    t = gamepad.Translator()
    assert t.menu(pad({'dpdown'}), 1 / 60) == ['down']
    assert t.menu(pad({'dpdown'}), 0.1) == []                      # 바로 반복하지 않는다
    keys = []
    for _ in range(60):
        keys += t.menu(pad({'dpdown'}), 1 / 60)                    # 1초 누르고 있으면 반복
    assert 3 <= len(keys) <= 10 and set(keys) == {'down'}
    t = gamepad.Translator()
    assert t.menu(pad(ly=-0.9), 1 / 60) == ['up']
    assert t.menu(pad({'a'}), 1 / 60) == ['enter']
    t = gamepad.Translator()
    assert t.menu(pad({'b'}), 1 / 60) == ['escape']
    t = gamepad.Translator()
    assert t.menu(pad({'b'}), 1 / 60, on_title=True) == []         # 타이틀에서 B로 게임이 꺼지지 않게


class FakePlayer:
    def __init__(self):
        self.left = self.right = self.down = False
        self.attack_held = False
        self.interact_pressed = False
        self.calls = []
        self.mouse_screen = (0, 0)

    def __getattr__(self, name):
        if name.startswith('request_') or name in ('release_jump', 'swap_weapon', '_sync_mouse'):
            return lambda *a: self.calls.append(name)
        raise AttributeError(name)


def test_play_actions_drive_the_player():
    p = FakePlayer()
    gamepad.apply_play(p, {'move': 1, 'down': False, 'press': {'jump', 'attack', 'enhance', 'dash', 'swap', 'interact'},
                           'release': set(), 'held': {'attack'}, 'aim': (1.0, 0.0)}, origin=(500, 400))
    assert p.right and not p.left and p.attack_held and p.interact_pressed
    for name in ('request_jump', 'request_attack', 'request_enhance', 'request_dash', 'swap_weapon', '_sync_mouse'):
        assert name in p.calls, name
    assert p.mouse_screen[0] > 500 and p.mouse_screen[1] == 400     # 조준점이 플레이어 오른쪽
    gamepad.apply_play(p, {'move': 0, 'down': False, 'press': set(), 'release': {'jump', 'attack'},
                           'held': set(), 'aim': None}, origin=(500, 400))
    assert not p.right and not p.attack_held and 'release_jump' in p.calls



def test_idle_pad_does_not_cancel_keyboard_movement():
    p = FakePlayer()
    p.right = True                                                  # 키보드 D를 누르고 있다
    idle = {'move': 0, 'down': False, 'press': set(), 'release': set(), 'held': set(), 'aim': None}
    gamepad.apply_play(p, idle, origin=(0, 0))
    assert p.right                                                  # 패드를 안 건드리면 그대로

if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
