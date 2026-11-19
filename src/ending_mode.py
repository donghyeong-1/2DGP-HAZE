"""엔딩 화면 (클리어 / 사망). 판이 끝났으니 헤이즈 결정을 받고(영구 재화), 보관인 칸이 열려 있으면
들고 있던 것 중 하나를 골라 맡긴다(다음 판 시작 때 받는다). 그다음 키를 누르면 사망은 은신처로, 탈출은 크레딧으로.

맡기기: A·D·좌·우로 고르고 Enter·Space·F로 맡긴다. 맨 끝 '맡기지 않기'도 고를 수 있다. (2026-11-19, docs/plan_v4.md 4절)
"""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE, SDLK_a, SDLK_d, SDLK_f,
                    clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import items
import meta

result = 'dead'  # 'clear' 또는 'dead'. 모드로 들어가기 전에 play_mode가 정한다.
_ignore_input = 0.0  # 사망 직후 누르고 있던 키로 바로 넘어가지 않게 잠시 입력을 막는다
reward = 0           # 이번 판에 받은 헤이즈 결정
choices = []         # 맡길 수 있는 것 (아이템 id), 맨 끝 None = 맡기지 않기
choice = 0
choosing = False     # 지금 맡길 것을 고르는 중인가
kept = None          # 맡긴 것 (보여 주기용)


def enter():
    global _ignore_input, reward, choices, choice, choosing, kept
    import play_mode
    _ignore_input = 0.6
    assets.play_music('title')   # 사망·탈출 화면은 차분한 곡으로 돌아간다
    p = play_mode.player
    reward = meta.finish_run(p, escaped=result == 'clear') if p is not None else 0
    options = meta.keepsake_options(p) if p is not None and meta.keeper_open() else []
    choices = options + [None] if options else []
    choice, kept = 0, None
    choosing = bool(choices)


def exit():
    pass


def pause():
    pass


def resume():
    pass


def _leave():
    if result == 'clear':                      # 탈출하면 크레딧으로 이어진다
        import credits_mode
        game_framework.change_mode(credits_mode)
    else:                                      # 죽으면 은신처로 (새 판)
        import play_mode
        game_framework.change_mode(play_mode)


def handle_events():
    global choice, choosing, kept
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
        elif event.type == SDL_KEYDOWN and _ignore_input <= 0:
            if choosing:
                if event.key in (SDLK_a, SDLK_LEFT):
                    choice = (choice - 1) % len(choices)
                elif event.key in (SDLK_d, SDLK_RIGHT):
                    choice = (choice + 1) % len(choices)
                elif event.key in (SDLK_RETURN, SDLK_SPACE, SDLK_f):
                    kept = choices[choice]
                    meta.set_keepsake(kept)
                    choosing = False
                    assets.play_sound('pickup')
                continue
            _leave()


def update():
    global _ignore_input
    _ignore_input = max(0.0, _ignore_input - game_framework.frame_time)


def _icon_of(item_id):
    info = items.ITEMS[item_id]
    return f'ui/icon_w_{info["weapon"]}.png' if 'weapon' in info else f'ui/icon_{item_id}.png'


def draw():
    clear_canvas()
    cx = config.SCREEN_W // 2
    nxt = '크레딧' if result == 'clear' else '은신처로'
    if result == 'clear':
        assets.draw_image(assets.image('backgrounds/screen_ending.png'), cx, 0)
        assets.draw_text(cx, 640, '탈출 성공', (170, 230, 250), center=True, big=True)
    else:                                                          # 사망 화면: 쓰러진 인물 위쪽에 글자를 둔다
        assets.draw_image(assets.image('backgrounds/screen_death.png'), cx, 0)
        assets.draw_text(cx, 660, '사망', (225, 90, 100), center=True, big=True)
        assets.draw_text(cx, 605, '게이지 또는 체력이 0이 되었습니다', (170, 185, 210), center=True)
    assets.draw_text(cx, 545, f'헤이즈 결정 +{reward}   (보유 {meta.state.get("crystals", 0)})', (130, 235, 225),
                     center=True)
    if choosing:                                                   # 보관인에게 맡길 것 고르기
        assets.draw_text(cx, 480, '보관인에게 하나를 맡긴다 (다음 판 시작 때 받는다)', (200, 210, 230), center=True)
        n = len(choices)
        gap = 96
        x0 = cx - (n - 1) * gap // 2
        for i, item_id in enumerate(choices):
            x = x0 + i * gap
            hot = i == choice
            assets.draw_rect_color(x - 34, 372, 68, 68, (11, 16, 32))
            assets.draw_rect_color(x - 32, 374, 64, 64, (90, 70, 150) if hot else (34, 40, 60))
            if item_id is None:
                assets.draw_text(x, 406, '없음', (200, 210, 230), small=True, center=True)
            else:
                assets.draw_image(assets.image(_icon_of(item_id)), x, 382)
        sel = choices[choice]
        name = '맡기지 않기' if sel is None else items.ITEMS[sel]['name'] + (
            ' (1단계로)' if sel in items.UPGRADES else '')
        assets.draw_text(cx, 330, name, (255, 225, 140), center=True)
        assets.draw_text(cx, 270, 'A D 고르기   Enter 맡기기', (150, 160, 185), small=True, center=True)
    else:
        if kept:
            assets.draw_text(cx, 470, f'맡긴 물건: {items.ITEMS[kept]["name"]}', (255, 225, 140), center=True)
        assets.draw_text(cx, 400, f'아무 키나 누르면 {nxt}', (150, 160, 185), center=True)
    update_canvas()
