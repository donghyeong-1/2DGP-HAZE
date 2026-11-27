"""U1-3 (2026-11-27) 화면 후처리(색 번짐·볼록 렌즈·고리·보스 막타 줌)가 화면을 넘어 남지 않는다 (창 없이).
실행: python tests/test_u1_postfx.py

postfx는 실제 시간으로 약 1초(오버로드 1.05초, 처형 0.5초) 돌다 스스로 꺼진다. 그런데 새 판(판 포기 -> 은신처),
구역 이동, 방 이동 때 비우지 않아서, 오버로드 직후 1초 안에 판을 포기하면 은신처 첫 화면이 색이 갈라진 채 보였다.
고친 뒤: 새 판·구역 이동·방 이동에서 남은 연출을 비운다. 연출의 모양·세기·길이는 그대로다.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')
import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
import meta  # noqa: E402

meta.PATH = os.path.join(tempfile.mkdtemp(), 'meta.json')

import config  # noqa: E402
import game_framework  # noqa: E402
import postfx  # noqa: E402

KEYS = [(0.0, 0.0, 0.0, 0.0), (0.3, 0.22, 9.0, 0.0), (1.05, 0.0, 0.0, 0.0)]   # 오버로드와 같은 길이의 연출


def _start_effect():
    options.reduce_flash = False
    postfx.play(KEYS, 960, 540)
    postfx._start -= 0.1                                 # 이미 0.1초 지난 연출 (실제 시간으로 아직 0.95초 남음)
    config.BOSS_KILL_ZOOM_ON = True
    postfx.zoom(960, 540)
    postfx._zoom = (postfx._zoom[0] - 0.1,) + postfx._zoom[1:]    # 줌도 0.1초 지난 것으로
    assert postfx.state() is not None and postfx.zoom_scale() != 1.0


def _enter_play():
    import play_mode
    play_mode.hide_cursor = lambda: None
    game_framework.stack[:] = [play_mode]
    play_mode.enter()
    return play_mode


def test_new_run_clears_a_running_screen_effect():
    """오버로드 직후 판을 포기해 은신처로 가면 첫 화면이 갈라지지 않는다."""
    _start_effect()
    _enter_play()
    assert postfx.state() is None
    assert postfx.zoom_scale() == 1.0


def test_zone_jump_clears_a_running_screen_effect():
    play_mode = _enter_play()
    _start_effect()
    play_mode._go_stage('stage1')
    assert postfx.state() is None and postfx.zoom_scale() == 1.0


def test_room_change_clears_a_running_screen_effect():
    play_mode = _enter_play()
    play_mode._go_stage('stage1')
    st = play_mode.stage
    game_framework.frame_time = 1 / 60
    play_mode.update()
    _start_effect()
    nxt = next(c for c in st.layout if c != st.coord)
    st.enter_room(nxt, 'L')
    play_mode.update()                                  # (방 이동은 Stage.enter_room에서 연출을 끈다)
    assert postfx.state() is None and postfx.zoom_scale() == 1.0


def test_effect_still_runs_inside_the_same_room():
    """같은 방에서는 연출이 끝까지 돈다 (모양·길이는 그대로)."""
    play_mode = _enter_play()
    play_mode._go_stage('stage1')
    game_framework.frame_time = 1 / 60
    play_mode.update()
    _start_effect()
    play_mode.update()
    assert postfx.state() is not None


def test_reduce_flash_skips_the_lens_effect():
    options.reduce_flash = True
    postfx.stop()
    postfx.play(KEYS, 960, 540)
    assert postfx.state() is None
    options.reduce_flash = False


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
