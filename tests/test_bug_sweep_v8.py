"""버그 훑기 (v8 7일 차, 인계서 대기열 3): 창을 여닫는 길에서 None·빈 목록·쓰기 실패로 튕기는 경우.
창 없이: python tests/test_bug_sweep_v8.py

- 키 설정: 비어 있는 보조 칸(None)은 어떤 동작의 키도 아니다 (11/25 sync_inputs와 같은 종류).
- 효과음 듣기: 표시를 저장하지 못해도(폴더가 없거나 쓸 수 없음) 게임이 멈추지 않고 기록만 남긴다.
- 증강 선택 창: 카드가 하나도 없으면 A·D·Enter에 튕기지 않고 창을 닫는다.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import game_framework  # noqa: E402
import keybinds  # noqa: E402


class _Event:
    def __init__(self, type_, key=None):
        self.type, self.key = type_, key


def test_an_empty_key_slot_is_no_action():
    keybinds.reset()
    assert keybinds.keys('left')[1] is None
    assert keybinds.action_for(None) is None


def test_sfx_marks_that_cannot_be_saved_do_not_crash():
    import sfx_mode
    old = sfx_mode.PATH
    sfx_mode.PATH = os.path.join(tempfile.mkdtemp(), 'no', 'such', 'folder', 'sfx_review.json')
    try:
        name = sfx_mode.catalog()[0][1][0]
        sfx_mode.mark(name, 'bad')                        # 예전: FileNotFoundError로 게임이 꺼졌다
        assert sfx_mode.marks.get(name) == 'bad'          # 표시는 이번 실행 동안 남는다
        sfx_mode.mark(name, None)
    finally:
        sfx_mode.PATH = old
        sfx_mode.marks = {}


def test_card_window_with_no_cards_closes_instead_of_crashing():
    import pico2d
    import mutation_mode
    import test_combat as tc
    _room, p = tc.make_world()
    closed = []

    class Under:
        def resume(self):
            closed.append(True)

        def exit(self):
            pass
    game_framework.stack[:] = [Under(), mutation_mode]
    mutation_mode.setup(p, [])
    mutation_mode.age = 1.0
    keys = [pico2d.SDLK_d, pico2d.SDLK_a, pico2d.SDLK_RETURN]
    old = mutation_mode.get_events
    try:
        for k in keys:
            mutation_mode.get_events = lambda k=k: [_Event(pico2d.SDL_KEYDOWN, k)]
            mutation_mode.handle_events()
            if closed:
                break
        assert closed and game_framework.stack[-1] is not mutation_mode
        closed.clear()
        game_framework.stack[:] = [Under(), mutation_mode]
        mutation_mode.setup(p, [])
        mutation_mode.update()                            # 입력이 없어도 다음 프레임에 닫힌다
        assert closed
    finally:
        mutation_mode.get_events = old
        game_framework.stack.clear()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
