"""S3 발소리와 메뉴 소리 (2026-11-28, 사용자가 받아 준 OpenGameArt "Footsteps"·Kenney UI Audio). 창 없이: python tests/test_sfx_s3.py

- 발소리(그 전에는 게임에 없었다): 주인공이 땅에서 달리거나 뒷걸음질할 때, 달리기 그림에서 발이 땅에 닿는 장(1·5번)으로
  넘어가는 순간마다 한 번. 공중·대시·기절 중에는 안 난다. config.FOOTSTEP_ON으로 끄고, config.FOOTSTEP_VOLUME으로 크기.
  변주 여섯(step, step_v2~v6)에서 직전과 다른 것을 고른다. 예전 묶음(v2)에는 발소리가 없다(그대로 조용).
- 메뉴 소리: ui_move·ui_select·ui_back + 메뉴처럼 쓰던 소리에 제 이름(값 변경 ui_value, 타이틀 시작 ui_start, 타이틀 줄 이동 ui_title_move).
  예전 묶음에서는 전과 같은 소리(pickup·swing_fade)로 풀린다. S2판 메뉴·착지 소리는 'v3s2' 묶음(assets/sfx_v3_s2)에 남긴다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import assets  # noqa: E402
import config  # noqa: E402
import test_combat as tc  # noqa: E402


class Heard:
    def __enter__(self):
        self.names, self._old = [], assets.play_sound
        assets.play_sound = self.names.append
        return self

    def __exit__(self, *exc):
        assets.play_sound = self._old


def _run(p, seconds, right=True):
    p.right, p.left = right, not right
    with Heard() as h:
        tc.step(int(seconds * 60))
    p.right = p.left = False
    return h.names.count('step')


def test_one_step_per_foot_contact_while_running_on_ground():
    _room, p = tc.make_world(300.0)
    p.mouse_x = p.x + 400
    n = _run(p, 1.0)
    per_step = config.RUN_FRAME_PX * 4                     # 8장 중 1·5번이 디딤: 네 장마다 한 걸음
    want = config.RUN_SPEED / per_step
    assert abs(n - want) <= 1.5, (n, want)


def test_backpedal_also_steps():
    _room, p = tc.make_world(900.0)
    p.mouse_x = p.x + 400                                  # 오른쪽을 겨눈 채 왼쪽으로: 뒷걸음
    assert _run(p, 1.0, right=False) >= 2


def test_no_steps_in_the_air_or_dashing_or_when_off():
    _room, p = tc.make_world(300.0)
    p.request_jump()
    tc.step(2)
    p.right = True
    with Heard() as h:
        tc.step(20)                                        # 떠 있는 동안
    p.right = False
    assert 'step' not in h.names, h.names
    _room, p = tc.make_world(300.0)
    p.right = True
    tc.step(10)
    with Heard() as h:
        p.request_dash()
        while p.state == 'DASH':
            tc.step(1)
    p.right = False
    assert 'step' not in h.names, h.names
    _room, p = tc.make_world(300.0)
    old = config.FOOTSTEP_ON
    try:
        config.FOOTSTEP_ON = False
        assert _run(p, 1.0) == 0
    finally:
        config.FOOTSTEP_ON = old


def test_step_has_six_variants_and_never_repeats_the_last():
    for i in range(1, 7):
        suffix = '' if i == 1 else f'_v{i}'
        assert os.path.exists(os.path.join(ROOT, 'assets', 'sfx_v3', 'step' + suffix + '.wav')), suffix
    picks = [assets.variant_of('step') for _ in range(60)]
    assert all(a != b for a, b in zip(picks, picks[1:]))
    assert len(set(picks)) == 6
    assert assets.sfx_path('step', 'v2') is None            # 예전 묶음에는 발소리가 없다


def test_step_volume_is_its_own_setting():
    old = config.FOOTSTEP_VOLUME
    try:
        config.FOOTSTEP_VOLUME = 0.5
        assert abs(assets.sfx_gain('step', 'v3') - config.SFX_V3_LEVEL * 0.5) < 1e-9
    finally:
        config.FOOTSTEP_VOLUME = old


def test_menu_sounds_new_names_fall_back_to_the_old_sounds_on_v2():
    for name, old in (('ui_value', 'pickup'), ('ui_start', 'pickup'), ('ui_title_move', 'swing_fade')):
        assert os.path.basename(assets.sfx_path(name, 'v3')) == name + '.wav'
        assert os.path.basename(assets.sfx_path(name, 'v2')) == old + '.wav', name


def test_s2_menu_and_land_kept_as_set_v3s2():
    for name in ('ui_move', 'ui_select', 'ui_back', 'land', 'land_v2', 'land_v3'):
        p = assets.sfx_path(name, 'v3s2')
        assert os.path.basename(os.path.dirname(p)) == 'sfx_v3_s2', name
    assert os.path.basename(os.path.dirname(assets.sfx_path('impact_pipe', 'v3s2'))) == 'sfx_v3'   # 그 밖은 v3 그대로


def test_menu_callers_use_menu_sounds():
    src = {f: open(os.path.join(ROOT, 'src', f), encoding='utf-8').read() for f in ('options_mode.py', 'keys_mode.py', 'title_mode.py')}
    assert "play_sound('pickup')" not in src['options_mode.py'] and "play_sound('ui_value')" in src['options_mode.py']
    assert "play_sound('pickup')" not in src['keys_mode.py']
    assert "play_sound('swing_fade')" not in src['title_mode.py'] and "play_sound('ui_title_move')" in src['title_mode.py']
    assert "play_sound('ui_start')" in src['title_mode.py']


def test_sfx_room_v_cycles_new_s2_old_for_menu_sounds():
    import sfx_mode
    sfx_mode.listen = None
    order = sfx_mode.listen_order('ui_move')
    assert order == ['v3', 'v3s2', 'v2'], order
    assert sfx_mode.listen_order('impact_pipe') == ['v3', 'v2']           # S2판이 따로 없는 소리
    assert sfx_mode.listen_order('step') == ['v3']                        # 예전에 없던 소리


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
