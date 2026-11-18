"""설정 창. 타이틀과 일시정지에서 위에 쌓아 연다(push_mode). Esc나 '돌아가기'로 닫는다.

항목: 화면 흔들림(끔·약하게·보통), 번쩍임 줄이기(켬·끔), 음악 크기, 효과음 크기(0~10), 돌아가기.
키보드: W/S·위/아래로 항목, A/D·좌/우로 값, Enter·Space로 켜고 끄기·돌아가기.
마우스: 칸을 누르면 그 값, 막대를 누르면 그 위치의 크기, 돌아가기 버튼.
바꾸면 바로 적용되고 저장된다(options.save). 부품 그림은 hud_kit(판·막대·버튼).
"""
from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDL_QUIT, SDLK_DOWN, SDLK_ESCAPE, SDLK_LEFT,
                    SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE, SDLK_UP, SDLK_a, SDLK_d, SDLK_o, SDLK_s, SDLK_w, clear_canvas,
                    get_events, update_canvas)

import assets
import config
import game_framework
import hud_kit as kit
import options

W, H = config.SCREEN_W, config.SCREEN_H
PANEL_W, PANEL_H = 1000, 640
PANEL_X, PANEL_Y = (W - PANEL_W) // 2, (H - PANEL_H) // 2 - 20
ROW_Y = [PANEL_Y + PANEL_H - 190 - i * 100 for i in range(4)]     # 항목 줄의 가운데 y
VALUE_X = PANEL_X + 470                                          # 값 칸이 시작하는 x
VALUE_W = 470
ITEMS = ('shake', 'flash', 'music', 'sfx', 'back')
NAMES = {'shake': '화면 흔들림', 'flash': '번쩍임 줄이기', 'music': '음악 크기', 'sfx': '효과음 크기'}
DESCS = {'shake': '타격·폭발 때 흔들리는 세기', 'flash': '오버로드 섬광·큰 폭발을 약하게',
         'music': '배경음악', 'sfx': '타격·발소리·경고음'}
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
def change(item, step):
    if item == 'shake':
        options.set_shake(options.shake_level + step)
    elif item == 'flash':
        options.toggle_flash()
    elif item == 'music':
        options.set_music(options.music_level + step)
        assets.apply_music_volume()
    elif item == 'sfx':
        options.set_sfx(options.sfx_level + step)
    assets.play_sound('pickup')                    # 바뀐 효과음 크기를 바로 들려준다


def _segments(item):
    """칸이 나뉜 항목의 칸들: [(값, 글자, x, w)]."""
    if item == 'shake':
        labels = [(i, name) for i, (name, _) in enumerate(options.SHAKE_LEVELS)]
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
    for i, item in enumerate(ITEMS[:4]):
        cy = ROW_Y[i]
        if not (cy - 30 <= my <= cy + 30 and VALUE_X - 10 <= mx <= VALUE_X + VALUE_W + 10):
            continue
        selected = i
        if item in ('shake', 'flash'):
            for value, _t, x, w in _segments(item):
                if x <= mx < x + w + 8:
                    if item == 'shake':
                        options.set_shake(value)
                    elif value != options.reduce_flash:
                        options.toggle_flash()
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
            for i in range(4):
                if ROW_Y[i] - 40 <= my <= ROW_Y[i] + 40 and PANEL_X <= mx <= PANEL_X + PANEL_W:
                    selected = i
            if back_button.contains(mx, my):
                selected = 4
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
            elif event.key in (SDLK_a, SDLK_LEFT) and item != 'back':
                change(item, -1)
            elif event.key in (SDLK_d, SDLK_RIGHT) and item != 'back':
                change(item, 1)
            elif event.key in (SDLK_RETURN, SDLK_SPACE):
                if item == 'back':
                    game_framework.pop_mode()
                    return
                change(item, 1)


def update():
    pass


def lines():
    """화면에 보일 (항목 이름, 현재 값, 설명) 목록. 테스트에서도 쓴다."""
    return [
        (NAMES['shake'], options.shake_name(), DESCS['shake']),
        (NAMES['flash'], '켬' if options.reduce_flash else '끔', DESCS['flash']),
        (NAMES['music'], str(options.music_level), DESCS['music']),
        (NAMES['sfx'], str(options.sfx_level), DESCS['sfx']),
    ]


def draw_panel():
    """설정 판 (타이틀·일시정지 위에 덮는다)."""
    kit.panel('panel', PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    kit.text(W // 2, PANEL_Y + PANEL_H - 70, '설정', (235, 240, 250), center=True, big=True)
    for i, item in enumerate(ITEMS[:4]):
        cy = ROW_Y[i]
        on = i == selected
        if on:
            kit.panel('plate', PANEL_X + 30, cy - 42, PANEL_W - 60, 84)
        kit.text(PANEL_X + 60, cy + 12, NAMES[item], (235, 240, 250) if on else (160, 176, 205))
        kit.text(PANEL_X + 60, cy - 20, DESCS[item], (110, 125, 150), small=True)
        if item in ('shake', 'flash'):
            current = options.shake_level if item == 'shake' else options.reduce_flash
            for value, label, x, w in _segments(item):
                hot = value == current
                kit.panel('button_hot' if hot else 'button', x, cy - 26, w, 52)
                kit.text(x + w // 2, cy, label, (235, 245, 255) if hot else (120, 135, 160), small=True, center=True)
        else:
            level = options.music_level if item == 'music' else options.sfx_level
            kit.bar('cyan', VALUE_X, cy - 6, VALUE_W - 60, 12, level / options.VOLUME_MAX)
            kx = VALUE_X + round((VALUE_W - 60) * level / options.VOLUME_MAX) - 11
            kit.icon('ui_knob', kx, cy - 17)
            kit.text(VALUE_X + VALUE_W - 20, cy, str(level), (235, 245, 255), center=True)
    back_button.draw(selected == 4)
    kit.text(W // 2, PANEL_Y - 26, 'W S 항목   A D 값 바꾸기   마우스로 눌러도 된다   Esc 돌아가기', (110, 125, 150), small=True,
             center=True)


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()                       # 멈춘 화면 위에 덮는다
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), 0.6)
    draw_panel()
    update_canvas()
