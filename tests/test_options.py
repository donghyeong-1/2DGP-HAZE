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



def test_credits_list_v4_art_and_match_the_sound_files():
    """크레딧이 v4에서 더한 그림(은신처·NPC·궁극기 컷인)을 적고, 소리 수가 실제 파일 수와 같다 (2026-11-19)."""
    import re
    import credits_mode
    text = ' '.join(t for _, t in credits_mode.CREDITS)
    for must in ('은신처', 'NPC', '컷인'):
        assert must in text, must
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
    sfx = len([f for f in os.listdir(os.path.join(root, 'sfx')) if f.endswith('.wav')])
    music = len([f for f in os.listdir(os.path.join(root, 'music')) if f.endswith('.wav')])
    m = re.search(r'효과음 (\d+)종 · 배경음악 (\d+)곡', text)
    assert m, '크레딧에 소리 수가 없다'
    assert (int(m.group(1)), int(m.group(2))) == (sfx, music), (m.groups(), sfx, music)

def test_options_screen_shows_current_values():
    import options_mode
    options.reset()
    names = [n for n, _, _ in options_mode.lines()]
    assert names == ['화면 흔들림', '번쩍임 줄이기', '음악 크기', '효과음 크기']
    values = [v for _, v, _ in options_mode.lines()]
    assert values == ['보통', '끔', str(options.VOLUME_DEFAULT), str(options.VOLUME_DEFAULT)]


def test_volume_levels_scale_config_volume_and_clamp():
    options.reset()
    assert options.volume(64, options.VOLUME_DEFAULT) == 64                # 기본 단계는 config 그대로
    assert options.volume(64, 0) == 0 and options.volume(64, 4) == 32
    assert options.volume(120, options.VOLUME_MAX) == 128                   # 128을 넘지 않는다
    old = options.PATH
    options.PATH = os.path.join(tempfile.mkdtemp(), 'v.json')
    try:
        options.set_music(99)
        options.set_sfx(-3)
        assert options.music_level == options.VOLUME_MAX and options.sfx_level == 0
        options.reset()
        options.load()
        assert options.music_level == options.VOLUME_MAX and options.sfx_level == 0
    finally:
        options.PATH = old
        options.reset()


def test_options_click_sets_segment_and_slider():
    import options_mode
    options.reset()
    old = options.PATH
    options.PATH = os.path.join(tempfile.mkdtemp(), 'c.json')
    try:
        _v, _t, x, w = options_mode._segments('shake')[0]                    # '끔' 칸을 누른다
        assert options_mode.click(x + 5, options_mode.ROW_Y[0])
        assert options.shake_level == 0
        y = options_mode.ROW_Y[2]                                             # 음악 막대의 절반쯤
        options_mode.click(options_mode.VALUE_X + options_mode.VALUE_W // 2, y)
        assert options.music_level == options.VOLUME_MAX // 2
    finally:
        options.PATH = old
        options.reset()


def test_menus_have_buttons_that_do_not_overlap():
    import pause_mode
    import title_mode
    for menu in (title_mode.MENU, pause_mode.MENU):
        for a in menu:
            for b in menu:
                if a is not b:
                    assert a.y + a.h <= b.y or b.y + b.h <= a.y, (a.label, b.label)
    assert [b.key for b in title_mode.MENU] == ['start', 'options', 'credits', 'quit']


def test_ui_kit_images_exist_for_every_part():
    """HUD·메뉴가 쓰는 판·막대·칸 그림이 모두 있다 (tools/make_ui.py)."""
    import re
    from PIL import Image
    import hud_kit
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'ui')
    for kind, (size, corner, _) in hud_kit.KITS.items():
        im = Image.open(os.path.join(base, f'ui_kit_{kind}.png'))
        assert im.size == (size, size) and size > 2 * corner, kind
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'ui.py'), encoding='utf-8').read()
    src += open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'options_mode.py'), encoding='utf-8').read()
    colors = set(re.findall(r"kit\.(?:bar|fill)\('(\w+)'", src)) | {'red', 'blue', 'cyan', 'orange', 'empty', 'white', 'yellow'}
    for color in colors:
        for h in hud_kit.FILL_HEIGHTS:
            assert os.path.exists(os.path.join(base, f'ui_fill_{color}_{h}.png')), (color, h)
    for name in {n for n in re.findall(r"kit\.icon\('(\w+)'", src) if not n.endswith('_')}:   # 'hud_map_' + 종류는 빼고
        assert os.path.exists(os.path.join(base, name + '.png')), name


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
