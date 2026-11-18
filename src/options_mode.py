"""설정(접근성) 화면. 타이틀(O)과 일시정지(O)에서 위에 쌓아 연다(push_mode). Esc로 돌아간다.

W/S·위/아래로 항목을 고르고, A/D·좌/우·Enter·Space로 값을 바꾼다. 바꾸면 바로 저장된다(options.save).
"""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_DOWN, SDLK_ESCAPE, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE, SDLK_UP,
                    SDLK_a, SDLK_d, SDLK_o, SDLK_s, SDLK_w, clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import options

ITEMS = ('shake', 'flash')
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


def change(step):
    if ITEMS[selected] == 'shake':
        options.cycle_shake(step)
    else:
        options.toggle_flash()
    assets.play_sound('pickup')


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN:
            if event.key in (SDLK_ESCAPE, SDLK_o):
                game_framework.pop_mode()
                return
            if event.key in (SDLK_w, SDLK_UP):
                selected = (selected - 1) % len(ITEMS)
            elif event.key in (SDLK_s, SDLK_DOWN):
                selected = (selected + 1) % len(ITEMS)
            elif event.key in (SDLK_a, SDLK_LEFT):
                change(-1)
            elif event.key in (SDLK_d, SDLK_RIGHT, SDLK_RETURN, SDLK_SPACE):
                change(1)


def update():
    pass


def lines():
    """화면에 보일 (항목 이름, 현재 값, 설명) 목록. 테스트에서도 쓴다."""
    return [
        ('화면 흔들림', options.shake_name(), '타격·폭발 때 화면이 흔들리는 세기'),
        ('번쩍임 줄이기', '켬' if options.reduce_flash else '끔', '오버로드 섬광과 큰 폭발의 하얀 빛을 약하게'),
    ]


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()                       # 멈춘 화면 위에 덮는다
    W, H = config.SCREEN_W, config.SCREEN_H
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), 0.7)
    cx = W // 2
    assets.draw_rect_color(cx - 532, 252, 1064, 588, (110, 150, 190), 1.0)      # 설정 판 테두리
    assets.draw_rect_color(cx - 528, 256, 1056, 580, (12, 18, 32), 1.0)         # 설정 판 (뒤 화면 글자가 비치지 않게 불투명)
    assets.draw_text(cx, 760, '설정', (235, 240, 250), center=True, big=True)
    for i, (name, value, desc) in enumerate(lines()):
        y = 620 - i * 130
        on = i == selected
        if on:
            assets.draw_rect_color(cx - 460, y - 50, 920, 104, (60, 120, 150), 0.35)
        color = (235, 240, 250) if on else (150, 165, 190)
        assets.draw_text(cx - 420, y + 14, name, color)
        arrow = f'<  {value}  >' if on else value
        assets.draw_text(cx + 300, y + 14, arrow, (130, 235, 225) if on else (120, 170, 190), center=True)
        assets.draw_text(cx - 420, y - 26, desc, (120, 135, 160), small=True)
    assets.draw_text(cx, 300, 'W S 항목 선택   A D 값 바꾸기   Esc 돌아가기 (바꾼 값은 저장된다)', (110, 190, 230), small=True,
                     center=True)
    update_canvas()
