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
    import play_mode
    clear_canvas()
    game_world.render(play_mode._apply_shake)  # 멈춘 화면도 카메라 위치 그대로 보여 준다
    assets.draw_offset = (0, 0)
    shade = assets.image('placeholder/px_black.png')
    shade.opacify(0.6)
    assets.draw_rect_image(shade, 0, 0, config.SCREEN_W, config.SCREEN_H)
    shade.opacify(1.0)
    assets.draw_text(config.SCREEN_W // 2, 680, '일시정지', (235, 240, 250), center=True, big=True)
    assets.draw_text(config.SCREEN_W // 2, 600, 'A D 이동 / Space 점프(2단) / S+Space 아래 점프', (170, 185, 210), center=True)
    assets.draw_text(config.SCREEN_W // 2, 550, '마우스 조준 + 좌클릭 공격(3연타) / Shift·우클릭 대시', (170, 185, 210), center=True)
    assets.draw_text(config.SCREEN_W // 2, 500, 'E 무기 강화 (게이지 25% 사용, 30% 이상일 때) / F 진열대 상호작용 (황금방·정비방)', (170, 185, 210), center=True)
    assets.draw_text(config.SCREEN_W // 2, 420, 'Esc 계속하기   Q 타이틀로', (110, 190, 230), center=True)
    update_canvas()
