"""접근성 옵션·설정 화면·크레딧 테스트 (창 없이 실행). 실행: python tests/test_options.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import config  # noqa: E402
import effects  # noqa: E402
import options  # noqa: E402


def test_shake_level_scales_screen_shake():
    options.reset()
    effects.reset()
    effects.add_trauma(1.0)
    effects.tick_shake(0.05)
    normal = effects.shake_offset()
    options.shake_level = 0                                   # 끔
    assert effects.shake_offset() == (0, 0)
    options.shake_level = 1                                   # 약하게: 보통보다 작다
    weak = effects.shake_offset()
    assert max(map(abs, weak)) <= max(map(abs, normal))
    options.reset()


def test_cycle_and_toggle_and_save_round_trip():
    options.reset()
    path = os.path.join(tempfile.mkdtemp(), 'opt.json')
    old = options.PATH
    options.PATH = path
    try:
        options.cycle_shake()                                 # 보통 -> 끔 (돌아간다)
        assert options.shake_name() == '끔'
        options.toggle_flash()
        assert options.reduce_flash and options.flash_mult() < 1.0
        options.reset()
        options.load(path)                                    # 저장한 값을 다시 읽는다
        assert options.shake_name() == '끔' and options.reduce_flash
    finally:
        options.PATH = old
        options.reset()


def test_bad_or_missing_file_keeps_defaults():
    options.reset()
    options.load(os.path.join(tempfile.mkdtemp(), 'none.json'))
    assert options.shake_name() == '보통' and not options.reduce_flash
    bad = os.path.join(tempfile.mkdtemp(), 'bad.json')
    with open(bad, 'w', encoding='utf-8') as f:
        f.write('{"shake_level": 99, "reduce_flash": "yes"')
    options.load(bad)
    assert options.shake_name() == '보통'


def test_reduce_flash_skips_bright_start_of_big_effects():
    options.reset()
    plain = effects.SheetEffect('haze-blast', 0, 0, duration=0.5)
    options.reduce_flash = True
    reduced = effects.SheetEffect('haze-blast', 0, 0, duration=0.5)
    small = effects.SheetEffect('puff', 0, 0, duration=0.5)
    options.reset()
    assert plain.time == 0 and reduced.time > 0 and reduced.frame > plain.frame
    assert small.time == 0                                    # 작은 이펙트는 그대로


def test_credits_cover_every_external_source_and_finish():
    import credits_mode
    text = ' '.join(t for _, t in credits_mode.CREDITS)
    for must in ('Galmuri', 'SIL Open Font License', 'pico2d', 'transitions', 'Codex', 'Claude Code', 'agent-sprite-forge'):
        assert must in text, must
    credits_mode.scroll = 0.0
    assert not credits_mode.finished()
    credits_mode.scroll = credits_mode.total_height() + config.SCREEN_H
    assert credits_mode.finished()


def test_options_screen_shows_current_values():
    import options_mode
    options.reset()
    names = [n for n, _, _ in options_mode.lines()]
    assert names == ['화면 흔들림', '번쩍임 줄이기']
    assert options_mode.lines()[0][1] == '보통' and options_mode.lines()[1][1] == '끔'


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
