"""타이틀(로비) 화면: 제목 일러스트, 로고, 메뉴(게임 시작 · 설정 · 크레딧 · 종료), 조작 안내.

키보드(W/S·위/아래, Enter·Space)나 마우스(올리면 고르고 누르면 실행)로 메뉴를 고른다.
단축키: O 설정, C 크레딧, Esc 종료. 부품 그림은 hud_kit(판·버튼).
"""
from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_c, SDLK_o, clear_canvas, get_events,
                    update_canvas)

import assets
import config
import game_framework
import hud_kit as kit

W, H = config.SCREEN_W, config.SCREEN_H
BUTTON_W, BUTTON_H, GAP = 420, 62, 16
MENU_TOP = 470                             # 첫 버튼의 위쪽 y
MENU = [kit.Button(key, label, (W - BUTTON_W) // 2, MENU_TOP - BUTTON_H - i * (BUTTON_H + GAP), BUTTON_W, BUTTON_H)
        for i, (key, label) in enumerate((('start', '게임 시작'), ('options', '설정'), ('credits', '크레딧'),
                                           ('quit', '종료')))]


def controls_text():
    """타이틀 아래 조작 줄. 키 이름은 키 설정을 따른다."""
    import keybinds
    k = lambda a: keybinds.label(a, first=True)  # noqa: E731
    return (f'{k("left")} {k("right")} 이동   {k("jump")} 점프   마우스 조준·좌클릭 공격   {k("dash")}·우클릭 대시   '
            f'{k("enhance")} 강화   {k("swap")} 무기 바꾸기   {k("interact")} 상호작용')


selected = 0


def enter():
    global selected
    selected = 0
    import transition
    transition.reveal()
    assets.play_music('title')


def exit():
    pass


def pause():
    pass


def resume():
    pass


def run(key):
    """메뉴 항목 실행."""
    assets.play_sound('pickup')
    if key == 'start':
        import play_mode
        game_framework.change_mode(play_mode)
    elif key == 'options':
        import options_mode
        game_framework.push_mode(options_mode)
    elif key == 'credits':
        import credits_mode
        game_framework.change_mode(credits_mode)
    else:
        game_framework.quit()


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN and event.key in (SDLK_ESCAPE, SDLK_o, SDLK_c):
            run({SDLK_ESCAPE: 'quit', SDLK_o: 'options', SDLK_c: 'credits'}[event.key])
            return
        before = selected
        selected, action = kit.menu_pick(MENU, selected, event, H)
        if selected != before and event.type != SDL_MOUSEBUTTONDOWN:
            assets.play_sound('swing_fade')                # 고르는 소리 (작게)
        if action == 'click':
            run(MENU[selected].key)
            return


def update():
    pass


def draw_frozen():
    """제목 화면 (설정 창이 아래에 깔 때도 쓴다)."""
    assets.draw_image(assets.image('backgrounds/screen_title.png'), W // 2, 0)   # Codex T16 제목 화면 일러스트
    assets.draw_image(assets.image('ui/logo_title.png'), W // 2, 588)          # 상점 로고(T29)를 1배로 (tools/make_store_art.py)
    kit.text(W // 2, 556, '안개를 삼키고 탈출하라', (150, 220, 245), center=True)
    for i, b in enumerate(MENU):
        b.draw(i == selected)
    kit.panel('plate', (W - 1500) // 2, 22, 1500, 44)
    kit.text(W // 2, 44, controls_text(), (175, 190, 215), small=True, center=True)


def draw():
    clear_canvas()
    draw_frozen()
    import transition
    transition.draw()                              # 화면 전환 점묘 (계획 4-3, 가장 위)
    update_canvas()
