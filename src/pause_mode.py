"""일시정지 화면. Esc로 돌아가고, Q를 누르면 타이틀로 나간다."""
from pico2d import SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_q, clear_canvas, get_events, update_canvas

import assets
import config
import game_framework
import game_world


def enter():
    pass


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
        elif event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                game_framework.pop_mode()
            elif event.key == SDLK_q:
                game_framework.pop_mode()  # 일시정지 모드를 끝낸 뒤
                game_framework.change_mode(title_mode)  # 플레이 모드를 타이틀로 교체


def update():
    pass


def draw():
    clear_canvas()
    game_world.render()
    shade = assets.image('placeholder/px_black.png')
    shade.opacify(0.6)
    shade.draw(config.SCREEN_W / 2, config.SCREEN_H / 2, config.SCREEN_W, config.SCREEN_H)
    shade.opacify(1.0)
    assets.draw_text(config.SCREEN_W / 2 - 80, 440, '일시정지', 48, (235, 240, 250))
    assets.draw_text(config.SCREEN_W / 2 - 210, 360,
                     'A D 이동 / Space 점프(2단) / S+Space 아래 점프', 22, (170, 185, 210))
    assets.draw_text(config.SCREEN_W / 2 - 210, 325,
                     'Shift·우클릭 대시(마우스 방향) / 마우스 조준', 22, (170, 185, 210))
    assets.draw_text(config.SCREEN_W / 2 - 160, 260, 'Esc 계속하기   Q 타이틀로', 24, (110, 190, 230))
    update_canvas()
