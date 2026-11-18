"""타이틀 화면. 아무 키나 누르면 게임을 시작한다."""
from pico2d import SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_c, SDLK_o, clear_canvas, get_events, update_canvas

import assets
import config
import game_framework


def enter():
    assets.play_music('title')


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
            elif event.key == SDLK_o:
                import options_mode
                game_framework.push_mode(options_mode)
            elif event.key == SDLK_c:
                import credits_mode
                game_framework.change_mode(credits_mode)
            else:
                game_framework.change_mode(play_mode)


def update():
    pass


def draw_frozen():
    """제목 화면 (설정 화면이 아래에 깔 때도 쓴다)."""
    assets.draw_image(assets.image('backgrounds/screen_title.png'), config.SCREEN_W // 2, 0)   # Codex T16 제목 화면 일러스트
    assets.draw_image(assets.image('ui/logo.png'), config.SCREEN_W // 2, 600)  # 코드로 그린 로고 (tools/make_codeart.py)
    assets.draw_text(config.SCREEN_W // 2, 545, '안개를 삼키고 탈출하라', (110, 190, 230), center=True)
    assets.draw_rect_color(config.SCREEN_W // 2 - 620, 192, 1240, 170, (11, 16, 32), 0.55)   # 밝은 성벽 위에서도 안내가 읽히게
    assets.draw_text(config.SCREEN_W // 2, 330, '아무 키나 누르세요', (235, 240, 250), center=True)
    assets.draw_text(config.SCREEN_W // 2, 270, 'A D 이동  Space 점프  마우스 조준·좌클릭 공격  Shift 대시  E 강화  F 상호작용', (185, 200, 225),
                     small=True, center=True)
    assets.draw_text(config.SCREEN_W // 2, 214, 'O 설정(화면 흔들림·번쩍임)   C 크레딧   Esc 종료', (150, 165, 190), small=True, center=True)


def draw():
    clear_canvas()
    draw_frozen()
    update_canvas()
