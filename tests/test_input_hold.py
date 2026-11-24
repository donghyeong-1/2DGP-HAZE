"""다른 화면이 뜬 동안 놓친 키 떼기 (2026-11-25 사용자 보고).
창 없이: python tests/test_input_hold.py

A·D를 누른 채 증강 선택 창이나 NPC 창이 뜨면, 키를 떼는 신호가 그 창으로 가서 주인공에게 닿지 않는다.
창이 닫힌 뒤에도 '누르고 있다'로 남아 그쪽으로 계속 걸어갔다.
- 다른 화면이 위에 뜨는 순간(play_mode.pause): 이동·아래·공격 누름을 모두 뗀 것으로 한다.
- 그 화면이 닫히는 순간(play_mode.resume): 실제로 지금 눌려 있는 키만 다시 누른 것으로 한다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import keybinds  # noqa: E402
import test_combat as tc  # noqa: E402


def test_holding_a_direction_is_released_when_another_screen_opens():
    room, p = tc.make_world()
    p.right, p.down, p.attack_held = True, True, True
    p.release_inputs()
    assert not p.right and not p.left and not p.down and not p.attack_held
    x0 = p.x
    tc.run_frames(30)
    assert abs(p.x - x0) < 2.0                                          # 더는 걸어가지 않는다


def test_coming_back_reads_the_keys_that_are_really_down():
    room, p = tc.make_world()
    p.right = True                                                       # 창이 뜨기 전에 D를 누르고 있었다
    p.release_inputs()
    left_key = keybinds.keys('left')[0]
    p.sync_inputs(lambda key: key == left_key, mouse_left=False)         # 돌아와 보니 A만 눌려 있다
    assert p.left and not p.right and not p.attack_held
    p.sync_inputs(lambda key: False, mouse_left=True)                    # 아무 키도 없고 마우스 왼쪽만
    assert not p.left and not p.right and p.attack_held


def test_play_mode_releases_on_pause_and_syncs_on_resume():
    import play_mode
    room, p = tc.make_world()
    calls = []
    p.release_inputs = lambda: calls.append('release')
    p.sync_inputs = lambda *a, **k: calls.append('sync')
    play_mode.player = p
    play_mode.show_cursor = play_mode.hide_cursor = lambda: None         # 창이 없는 테스트: 커서 호출만 막는다
    play_mode.pause()
    play_mode.resume()
    assert calls == ['release', 'sync']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
