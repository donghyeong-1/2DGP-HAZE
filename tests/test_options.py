"""접근성 옵션·설정 화면·크레딧 테스트 (창 없이 실행). 실행: python tests/test_options.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')   # 깨진 저장 시험이 사용자 폴더에 기록을 남기지 않게

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
    for must in ('Galmuri', 'SIL Open Font License', 'pico2d', 'transitions', 'Codex', 'Claude Code', 'agent-sprite-forge', 'Kenney'):
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
    sfx = len([f for f in os.listdir(os.path.join(root, 'sfx'))
               if f.endswith('.wav') and not re.search(r'_v\d\.wav$', f)])    # 3버전(_v2·_v3)은 같은 소리로 센다
    music = len([f for f in os.listdir(os.path.join(root, 'music')) if f.endswith(('.wav', '.ogg', '.mp3'))])
    m = re.search(r'효과음 (\d+)종 · 배경음악 (\d+)곡', text)
    assert m, '크레딧에 소리 수가 없다'
    assert (int(m.group(1)), int(m.group(2))) == (sfx, music), (m.groups(), sfx, music)

def test_options_screen_shows_current_values():
    import options_mode
    options.reset()
    names = [n for n, _, _ in options_mode.lines()]
    assert names == ['화면 흔들림', '번쩍임 줄이기', '음악 크기', '효과음 크기', '해상도', '마우스 가두기', '처음 안내', '피해 숫자', '테스트 모드', '키 설정']
    values = [v for _, v, _ in options_mode.lines()]
    assert values == ['보통', '끔', str(options.VOLUME_DEFAULT), str(options.VOLUME_DEFAULT), '1920x1080', '끔', '켬', '켬', '끔', '기본']


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


def test_pause_menu_can_return_to_hideout_with_confirm():
    """v7 (2026-11-23): 일시정지에서 '은신처로 돌아가기'. 판 도중 실수로 나가지 않게 두 번 눌러야 한다."""
    import game_framework
    import pause_mode
    import play_mode
    assert [b.key for b in pause_mode.MENU] == ['resume', 'options', 'hideout', 'title']
    calls = []
    saved = game_framework.pop_mode, game_framework.change_mode
    game_framework.pop_mode = lambda: calls.append('pop')
    game_framework.change_mode = lambda m: calls.append(m)
    try:
        pause_mode.enter()
        pause_mode.run('hideout')
        assert calls == []                                   # 첫 입력은 묻기만
        pause_mode.run('hideout')
        assert calls == ['pop', play_mode]                   # 두 번째에 은신처(새 판)로
    finally:
        game_framework.pop_mode, game_framework.change_mode = saved


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



# ----- 해상도·마우스 가두기 (2026-11-20 사용자 요청) -----
def test_resolution_and_mouse_confine_save_round_trip():
    options.reset()
    assert options.resolution_name() == '1920x1080' and options.confine_mouse is False
    old = options.PATH
    options.PATH = os.path.join(tempfile.mkdtemp(), 'r.json')
    try:
        options.set_resolution(0)
        options.toggle_confine()
        options.reset()
        options.load()
        assert options.resolution_name() == '1280x720' and options.confine_mouse is True
        options.set_resolution(99)                                            # 범위 밖은 끝 값으로
        assert options.resolution_name() == options.RESOLUTIONS[-1][0]
    finally:
        options.PATH = old
        options.reset()


def test_window_size_keeps_16_9_and_fits_the_monitor():
    """창 크기: 고른 해상도, 모니터보다 크면 들어가는 가장 큰 16:9로. 전체 화면은 모니터 크기 그대로(게임은 1920x1080 논리 화면)."""
    import display
    assert display.window_size('1600x900', 2560, 1440) == (1600, 900, False)
    assert display.window_size('1920x1080', 1600, 900) == (1600, 900, False)       # 작은 노트북 화면
    assert display.window_size('1920x1080', 1366, 768) == (1280, 720, False)
    assert display.window_size('전체 화면', 2560, 1440) == (2560, 1440, True)


def test_options_click_sets_resolution_and_confine():
    import options_mode
    options.reset()
    old = options.PATH
    options.PATH = os.path.join(tempfile.mkdtemp(), 'd.json')
    try:
        row = options_mode.ITEMS.index('resolution')
        _v, _t, x, w = options_mode._segments('resolution')[1]
        assert options_mode.click(x + 5, options_mode.ROW_Y[row])
        assert options.resolution_name() == '1600x900'
        row = options_mode.ITEMS.index('confine')
        _v, _t, x, w = options_mode._segments('confine')[1]                   # '켬'
        assert options_mode.click(x + 5, options_mode.ROW_Y[row])
        assert options.confine_mouse is True
        assert options_mode.ROW_Y[-1] > options_mode.back_button.y + options_mode.back_button.h   # 버튼과 겹치지 않는다
    finally:
        options.PATH = old
        options.reset()

def test_credits_scenes_change_as_credits_scroll():
    """Codex T35: 크레딧이 흐르는 동안 탈출 뒤 장면 3장이 차례로 바뀐다."""
    import credits_mode
    from PIL import Image
    total = credits_mode.total_height() + config.SCREEN_H * 0.5 + 180
    names = [credits_mode.scene_for(total * k) for k in (0.0, 0.2, 0.45, 0.7, 0.99)]
    assert names[0] == 'credits_1' and names[-1] == 'credits_3' and 'credits_2' in names
    assert names == sorted(names)                                     # 앞으로만 넘어간다
    for n in ('credits_1', 'credits_2', 'credits_3'):
        assert Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'backgrounds',
                                       n + '.png')).size == (1920, 1080)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
