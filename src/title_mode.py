"""타이틀 화면. 아무 키나 누르면 게임을 시작한다."""
from pico2d import SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, clear_canvas, get_events, update_canvas

import assets
import config
import game_framework


def enter():
    pass


def exit():
    pass


def pause():
    pass


def resume():
    pass


def handle_events():
    import play_mode
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                game_framework.quit()
            else:
                game_framework.change_mode(play_mode)


def update():
    pass


def draw():
    clear_canvas()
    assets.draw_image(assets.image('placeholder/bg.png'), config.SCREEN_W // 2, 0)
    # TODO: 큰 제목은 픽셀 폰트를 키우지 않고 로고 이미지(스프라이트)로 교체한다
    assets.draw_text(config.SCREEN_W // 2, 430, 'HAZE', (170, 230, 250), center=True)
    assets.draw_text(config.SCREEN_W // 2, 380, '안개를 삼키고 탈출하라', (110, 190, 230), center=True)
    assets.draw_text(config.SCREEN_W // 2, 200, '아무 키나 누르세요', (150, 160, 185), center=True)
    update_canvas()
