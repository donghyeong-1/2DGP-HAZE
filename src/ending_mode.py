"""엔딩 화면 (클리어 / 사망). 아무 키나 누르면 타이틀로 돌아간다."""
from pico2d import SDL_KEYDOWN, SDL_QUIT, clear_canvas, get_events, update_canvas

import assets
import config
import game_framework

result = 'dead'  # 'clear' 또는 'dead'. 모드로 들어가기 전에 play_mode가 정한다.
_ignore_input = 0.0  # 사망 직후 누르고 있던 키로 바로 넘어가지 않게 잠시 입력을 막는다


def enter():
    global _ignore_input
    _ignore_input = 0.6


def exit():
    pass


def pause():
    pass


def resume():
    pass


def handle_events():
    import title_mode
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and _ignore_input <= 0:
            game_framework.change_mode(title_mode)


def update():
    global _ignore_input
    _ignore_input = max(0.0, _ignore_input - game_framework.frame_time)


def draw():
    clear_canvas()
    assets.image('placeholder/bg.png').draw(config.SCREEN_W / 2, config.SCREEN_H / 2)
    if result == 'clear':
        assets.draw_text(config.SCREEN_W / 2 - 150, 400, '탈출 성공', 80, (170, 230, 250))
    else:
        assets.draw_text(config.SCREEN_W / 2 - 110, 400, '사망', 80, (225, 90, 100))
        assets.draw_text(config.SCREEN_W / 2 - 160, 330, '게이지 또는 체력이 0이 되었습니다', 24, (170, 185, 210))
    assets.draw_text(config.SCREEN_W / 2 - 130, 220, '아무 키나 누르면 타이틀로', 24, (150, 160, 185))
    update_canvas()
