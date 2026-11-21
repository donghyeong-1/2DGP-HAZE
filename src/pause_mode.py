"""일시정지 창: 멈춘 게임 위에 메뉴(계속하기 · 설정 · 타이틀로)와 조작 안내를 띄운다.

Esc로 바로 돌아가고, O는 설정, Q는 타이틀. 메뉴는 키보드(W/S, Enter)와 마우스로 고른다.
"""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_o, SDLK_q, clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import game_world
import hud_kit as kit

W, H = config.SCREEN_W, config.SCREEN_H
PANEL_W, PANEL_H = 1240, 600
PANEL_X, PANEL_Y = (W - PANEL_W) // 2, (H - PANEL_H) // 2 - 10
MENU = [kit.Button(key, label, PANEL_X + 60, PANEL_Y + PANEL_H - 230 - i * 86, 380, 64)
        for i, (key, label) in enumerate((('resume', '계속하기'), ('options', '설정'), ('title', '타이틀로')))]


def controls():
    """(키, 설명) 목록. 키 이름은 키 설정(설정 > 키 바꾸기)을 따른다."""
    import keybinds
    k = keybinds.label
    j = keybinds.label('jump').replace('/', '  ')
    return [
        (f'{k("left")}  {k("right")}', '좌우 이동'),
        (j, '점프 (2단, 짧게 누르면 낮게)'),
        (f'{k("down")} + {k("jump", first=True)}', '얇은 발판 아래로'),
        ('마우스', '조준'),
        ('좌클릭', '공격 (3연타, 공중·대시 중 특수 공격)'),
        (f'{k("dash")}  우클릭', '대시 (아래로 겨누면 발판 통과)'),
        (k('enhance'), '강화 일격 (게이지 25% 사용)'),
        (f'{k("swap")}  {k("weapon1")}  {k("weapon2")}', '무기 바꾸기'),
        (k('interact'), '진열대 아이템 얻기·사기'),
    ]


selected = 0


def enter():
    global selected
    selected = 0


def exit():
    pass


def pause():
    pass


def resume():
    pass


def run(key):
    import title_mode
    if key == 'resume':
        game_framework.pop_mode()
    elif key == 'options':
        import options_mode
        game_framework.push_mode(options_mode)
    else:
        game_framework.pop_mode()                  # 일시정지를 끝낸 뒤
        game_framework.change_mode(title_mode)     # 플레이 모드를 타이틀로 교체


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN and event.key in (SDLK_ESCAPE, SDLK_o, SDLK_q):
            run({SDLK_ESCAPE: 'resume', SDLK_o: 'options', SDLK_q: 'title'}[event.key])
            return
        selected, action = kit.menu_pick(MENU, selected, event, H)
        if action == 'click':
            run(MENU[selected].key)
            return


def update():
    pass


def draw_frozen():
    """멈춘 게임 화면 (설정 창이 아래에 깔 때도 쓴다)."""
    import play_mode
    game_world.render(play_mode._apply_shake)      # 멈춘 화면도 카메라 위치 그대로 보여 준다
    assets.draw_offset = (0, 0)


def draw():
    clear_canvas()
    draw_frozen()
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), 0.62)
    kit.panel('panel', PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    kit.text(PANEL_X + 250, PANEL_Y + PANEL_H - 80, '일시정지', (235, 240, 250), center=True, big=True)
    for i, b in enumerate(MENU):
        b.draw(i == selected)
    # 조작 안내 (오른쪽)
    gx, gy = PANEL_X + 500, PANEL_Y + 40
    kit.panel('plate', gx, gy, PANEL_W - 540, PANEL_H - 80)
    kit.text(gx + 30, gy + PANEL_H - 130, '조작', (130, 235, 225))
    for i, (key, what) in enumerate(controls()):
        y = gy + PANEL_H - 180 - i * 42
        kit.text(gx + 30, y, key, (255, 225, 140), small=True)
        kit.text(gx + 230, y, what, (200, 212, 232), small=True)
    kit.text(PANEL_X + 250, PANEL_Y + 40, 'Esc 계속  O 설정  Q 타이틀', (110, 125, 150), small=True, center=True)
    update_canvas()
