"""설정 창. 타이틀과 일시정지에서 위에 쌓아 연다(push_mode). Esc나 '돌아가기'로 닫는다.

항목: 화면 흔들림(끔·약하게·보통), 번쩍임 줄이기(켬·끔), 음악 크기, 효과음 크기(0~10),
      해상도(1280x720·1600x900·1920x1080·전체 화면), 마우스 가두기(켬·끔), 처음 안내, 키 바꾸기(keys_mode 창), 돌아가기.
키보드: W/S·위/아래로 항목, A/D·좌/우로 값, Enter·Space로 켜고 끄기·돌아가기.
마우스: 칸을 누르면 그 값, 막대를 누르면 그 위치의 크기, 돌아가기 버튼.
바꾸면 바로 적용되고 저장된다(options.save). 부품 그림은 hud_kit(판·막대·버튼).
"""
from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDL_QUIT, SDLK_DOWN, SDLK_ESCAPE, SDLK_LEFT,
                    SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE, SDLK_UP, SDLK_a, SDLK_d, SDLK_o, SDLK_s, SDLK_w, clear_canvas,
                    get_events, update_canvas)

import assets
import config
import display
import game_framework
import hud_kit as kit
import options

W, H = config.SCREEN_W, config.SCREEN_H
ITEMS = ('shake', 'flash', 'music', 'sfx', 'resolution', 'confine', 'hints', 'damage', 'keys', 'back')
ROWS = ITEMS[:-1]
ROW_STEP = 74
PANEL_W, PANEL_H = 1440, 250 + ROW_STEP * len(ROWS)
PANEL_X, PANEL_Y = (W - PANEL_W) // 2, (H - PANEL_H) // 2 - 10
ROW_Y = [PANEL_Y + PANEL_H - 170 - i * ROW_STEP for i in range(len(ROWS))]     # 항목 줄의 가운데 y
VALUE_X = PANEL_X + 600                                          # 값 칸이 시작하는 x
VALUE_W = 800
NAMES = {'shake': '화면 흔들림', 'flash': '번쩍임 줄이기', 'music': '음악 크기', 'sfx': '효과음 크기',
         'resolution': '해상도', 'confine': '마우스 가두기', 'hints': '처음 안내', 'damage': '피해 숫자', 'keys': '키 바꾸기'}
DESCS = {'shake': '타격·폭발 때 흔들리는 세기', 'flash': '오버로드 섬광·큰 폭발을 약하게',
         'music': '배경음악', 'sfx': '타격·발소리·경고음',
         'resolution': '창 크기 (게임 화면 비율은 그대로)', 'confine': '마우스가 게임 창 밖으로 나가지 않게',
         'hints': '처음 보는 상황에 짧은 안내판', 'damage': '적이 맞은 자리에 피해 숫자 표시', 'keys': '키보드 동작 키 (마우스는 그대로)'}
SEGMENTED = ('shake', 'flash', 'resolution', 'confine', 'hints', 'damage')
back_button = kit.Button('back', '돌아가기', (W - 360) // 2, PANEL_Y + 40, 360, 64)
selected = 0
_under = None            # 아래에 깔린 모드 (멈춘 화면을 그대로 보여 준다)


def enter():
    global selected, _under
    selected = 0
    options.ensure_loaded()
    _under = game_framework.stack[-2] if len(game_framework.stack) >= 2 else None


def exit():
    pass


def pause():
    pass


def resume():
    pass


# ----- 값 바꾸기 -----
def open_keys():
    import keys_mode
    game_framework.push_mode(keys_mode)


def keys_summary():
    import keybinds
    return '기본' if keybinds.to_json() == keybinds.DEFAULTS else '바꿈'


def change(item, step):
    if item == 'keys':
        if step > 0:
            open_keys()
        return
    if item == 'shake':
        options.set_shake(options.shake_level + step)
    elif item == 'flash':
        options.toggle_flash()
    elif item == 'music':
        options.set_music(options.music_level + step)
        assets.apply_music_volume()
    elif item == 'sfx':
        options.set_sfx(options.sfx_level + step)
    elif item == 'resolution':
        options.set_resolution((options.resolution + step) % len(options.RESOLUTIONS))
        display.apply()
    elif item == 'confine':
        options.toggle_confine()
        display.apply()
    elif item == 'hints':
        options.toggle_hints()
    elif item == 'damage':
        options.toggle_damage()
    assets.play_sound('pickup')                    # 바뀐 효과음 크기를 바로 들려준다


def _segments(item):
    """칸이 나뉜 항목의 칸들: [(값, 글자, x, w)]."""
    if item == 'shake':
        labels = [(i, name) for i, (name, _) in enumerate(options.SHAKE_LEVELS)]
    elif item == 'resolution':
        labels = [(i, name) for i, (name, _w, _h) in enumerate(options.RESOLUTIONS)]
    else:
        labels = [(False, '끔'), (True, '켬')]
    seg_w = VALUE_W // len(labels)
    return [(v, t, VALUE_X + i * seg_w, seg_w - 8) for i, (v, t) in enumerate(labels)]


def click(mx, my):
    """마우스로 누른 곳의 항목을 고르고 값을 바꾼다. 처리했으면 True."""
    global selected
    if back_button.contains(mx, my):
        game_framework.pop_mode()
        return True
    for i, item in enumerate(ROWS):
        cy = ROW_Y[i]
        if not (cy - 30 <= my <= cy + 30 and VALUE_X - 10 <= mx <= VALUE_X + VALUE_W + 10):
            continue
        selected = i
        if item == 'keys':
            open_keys()
            return True
        if item in SEGMENTED:
            for value, _t, x, w in _segments(item):
                if x <= mx < x + w + 8:
                    if item == 'shake':
                        options.set_shake(value)
                    elif item == 'flash' and value != options.reduce_flash:
                        options.toggle_flash()
                    elif item == 'resolution' and value != options.resolution:
                        options.set_resolution(value)
                        display.apply()
                    elif item == 'confine' and value != options.confine_mouse:
                        options.toggle_confine()
                        display.apply()
                    elif item == 'hints' and value != options.show_hints:
                        options.toggle_hints()
                    elif item == 'damage' and value != options.show_damage:
                        options.toggle_damage()
        else:                                      # 막대: 누른 위치의 크기
            level = round((mx - VALUE_X) / VALUE_W * options.VOLUME_MAX)
            (options.set_music if item == 'music' else options.set_sfx)(level)
            if item == 'music':
                assets.apply_music_volume()
        assets.play_sound('pickup')
        return True
    return False


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_MOUSEMOTION:
            mx, my = event.x, H - 1 - event.y
            for i in range(len(ROWS)):
                if ROW_Y[i] - 40 <= my <= ROW_Y[i] + 40 and PANEL_X <= mx <= PANEL_X + PANEL_W:
                    selected = i
            if back_button.contains(mx, my):
                selected = len(ROWS)
        elif event.type == SDL_MOUSEBUTTONDOWN:
            click(event.x, H - 1 - event.y)
        elif event.type == SDL_KEYDOWN:
            item = ITEMS[selected]
            if event.key in (SDLK_ESCAPE, SDLK_o):
                game_framework.pop_mode()
                return
            if event.key in (SDLK_w, SDLK_UP):
                selected = (selected - 1) % len(ITEMS)
            elif event.key in (SDLK_s, SDLK_DOWN):
                selected = (selected + 1) % len(ITEMS)
            elif event.key in (SDLK_a, SDLK_LEFT) and item not in ('back', 'keys'):
                change(item, -1)
            elif event.key in (SDLK_d, SDLK_RIGHT) and item not in ('back', 'keys'):
                change(item, 1)
            elif event.key in (SDLK_RETURN, SDLK_SPACE):
                if item == 'back':
                    game_framework.pop_mode()
                    return
                change(item, 1)
                if item == 'keys':
                    return


def update():
    pass


def lines():
    """화면에 보일 (항목 이름, 현재 값, 설명) 목록. 테스트에서도 쓴다."""
    return [
        (NAMES['shake'], options.shake_name(), DESCS['shake']),
        (NAMES['flash'], '켬' if options.reduce_flash else '끔', DESCS['flash']),
        (NAMES['music'], str(options.music_level), DESCS['music']),
        (NAMES['sfx'], str(options.sfx_level), DESCS['sfx']),
        (NAMES['resolution'], options.resolution_name(), DESCS['resolution']),
        (NAMES['confine'], '켬' if options.confine_mouse else '끔', DESCS['confine']),
        (NAMES['hints'], '켬' if options.show_hints else '끔', DESCS['hints']),
        (NAMES['damage'], '켬' if options.show_damage else '끔', DESCS['damage']),
        (NAMES['keys'], keys_summary(), DESCS['keys']),
    ]


def draw_panel():
    """설정 화면 (11/22 메뉴 v2: 큰 판 없이 화면 전체 덮개 + 줄마다 카드 + 값은 알약 칸)."""
    kit.heading(PANEL_X, PANEL_Y + PANEL_H - 40, '설정')
    current_of = {'shake': options.shake_level, 'flash': options.reduce_flash,
                  'resolution': options.resolution, 'confine': options.confine_mouse, 'hints': options.show_hints,
                  'damage': options.show_damage}
    for i, item in enumerate(ROWS):
        cy = ROW_Y[i]
        on = i == selected
        kit.row(PANEL_X, cy - 34, PANEL_W, 68, on)
        kit.text(PANEL_X + 34, cy + 11, NAMES[item], (240, 248, 255) if on else (190, 202, 225))
        kit.text(PANEL_X + 34, cy - 17, DESCS[item], (140, 155, 182) if on else kit.FAINT, small=True)
        if item == 'keys':
            kit.pill(VALUE_X, cy - 24, VALUE_W - 8, 48, f'키 바꾸기 ({keys_summary()})  >', False, focus=on)
        elif item in SEGMENTED:
            current = current_of[item]
            for value, label, x, w in _segments(item):
                kit.pill(x, cy - 22, w, 44, label, value == current, focus=on)
        else:
            level = options.music_level if item == 'music' else options.sfx_level
            kit.bar('cyan', VALUE_X, cy - 6, VALUE_W - 70, 12, level / options.VOLUME_MAX)
            kx = VALUE_X + round((VALUE_W - 70) * level / options.VOLUME_MAX) - 11
            kit.icon('ui_knob', kx, cy - 17)
            kit.text(VALUE_X + VALUE_W - 24, cy, str(level), (235, 245, 255), center=True)
    back_button.draw(selected == len(ROWS))
    kit.footer([('W S', '항목'), ('A D', '값 바꾸기'), ('Enter', '결정'), ('Esc', '돌아가기')])


def draw_frozen():
    """키 바꾸기 창이 아래에 깔 때: 아래 화면 + 설정 판."""
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()
    kit.backdrop(0.97)
    draw_panel()


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()                       # 멈춘 화면 위에 덮는다
    kit.backdrop(0.97)
    draw_panel()
    update_canvas()
