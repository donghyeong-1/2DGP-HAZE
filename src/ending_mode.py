"""엔딩 화면 (클리어 / 사망). 판이 끝났으니 헤이즈 결정을 받고(영구 재화), 보관인 칸이 열려 있으면
들고 있던 것 중 하나를 골라 맡긴다(다음 판 시작 때 받는다). 그다음 키를 누르면 사망은 은신처로, 탈출은 크레딧으로.

판 기록(계획 4-2): 걸린 시간·도달한 구역·클리어한 방·쓰러뜨린 적·깬 보스·관문·받은 결정을 판에 보여 준다(run_summary).
맡기기: A·D·좌·우로 고르고 Enter·Space·F로 맡긴다. 맨 끝 '맡기지 않기'도 고를 수 있다. (2026-11-19, docs/plan_v4.md 4절)
"""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE, SDLK_a, SDLK_d, SDLK_f,
                    clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import hud_kit as kit
import items
import meta

result = 'dead'  # 'clear' 또는 'dead'. 모드로 들어가기 전에 play_mode가 정한다.
_ignore_input = 0.0  # 사망 직후 누르고 있던 키로 바로 넘어가지 않게 잠시 입력을 막는다
reward = 0           # 이번 판에 받은 헤이즈 결정
choices = []         # 맡길 수 있는 것 (아이템 id), 맨 끝 None = 맡기지 않기
choice = 0
choosing = False     # 지금 맡길 것을 고르는 중인가
kept = None          # 맡긴 것 (보여 주기용)
summary = []         # 판 기록 [(이름, 값)]
SUM_W, SUM_ROW = 760, 54


def run_summary(player, zone_title, reward):
    """판 기록 줄 [(이름, 값)]. 시간은 분:초."""
    secs = int(getattr(player, 'run_clock', 0.0))
    return [('도달한 구역', zone_title or '-'), ('걸린 시간', f'{secs // 60}:{secs % 60:02d}'),
            ('클리어한 방', str(player.run_rooms)), ('쓰러뜨린 적', str(getattr(player, 'run_kills', 0))),
            ('깬 보스·관문', str(player.run_ends)), ('받은 헤이즈 결정', f'+{reward}')] + (
        [('쓰러진 원인', player.death_cause)] if getattr(player, 'death_cause', '') else [])


def enter():
    global _ignore_input, reward, choices, choice, choosing, kept, summary
    import play_mode
    _ignore_input = 0.6
    import transition
    transition.reveal(0.6)                         # 쓰러진 뒤·탈출 뒤 천천히 드러난다
    assets.play_music('title')   # 사망·탈출 화면은 차분한 곡으로 돌아간다
    p = play_mode.player
    reward = meta.finish_run(p, escaped=result == 'clear') if p is not None else 0
    st = getattr(play_mode, 'stage', None)
    summary = run_summary(p, getattr(st, 'title', ''), reward) if p is not None else []
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


FULL_ROWS = ('도달한 구역', '쓰러진 원인')      # 글이 길어 한 줄을 다 쓰는 항목


def _draw_summary(cx):
    """판 기록 판: 도달한 구역·쓰러진 원인은 한 줄씩(넓게), 나머지는 두 칸씩, 맨 아래 보유 결정."""
    if not summary:
        return
    wide = [e for e in summary if e[0] in FULL_ROWS]
    rest = [e for e in summary if e[0] not in FULL_ROWS]
    rows = len(wide) + (len(rest) + 1) // 2
    h = 70 + rows * SUM_ROW
    x, y = cx - SUM_W // 2, 790 - h
    kit.panel('panel', x, y, SUM_W, h)
    top = y + h - 40
    for i, (name, value) in enumerate(wide):
        ty = top - i * SUM_ROW
        kit.text(x + 34, ty, name, (130, 145, 175), small=True)
        kit.text(x + SUM_W - 34, ty, value, (255, 150, 140) if name == '쓰러진 원인' else (235, 242, 252), right=True)
    half = SUM_W // 2
    for i, (name, value) in enumerate(rest):
        col, row = i % 2, i // 2 + len(wide)
        ty = top - row * SUM_ROW
        lx = x + 34 + col * half
        kit.text(lx, ty, name, (130, 145, 175), small=True)
        kit.text(lx + half - 60, ty, value, (255, 225, 140) if '결정' in name else (235, 242, 252), right=True)
    kit.text(cx, y + 24, f'보유 헤이즈 결정 {meta.state.get("crystals", 0)}', (130, 235, 225), small=True, center=True)


def draw():
    clear_canvas()
    cx = config.SCREEN_W // 2
    nxt = '크레딧' if result == 'clear' else '은신처로'
    if result == 'clear':
        assets.draw_image(assets.image('backgrounds/screen_ending.png'), cx, 0)
        assets.draw_text(cx, 880, '탈출 성공', (170, 230, 250), center=True, big=True)
        assets.draw_text(cx, 830, '안개를 삼키고 감옥을 벗어났다', (170, 185, 210), center=True)
    else:                                                          # 사망 화면: 쓰러진 인물 위쪽에 글자를 둔다
        assets.draw_image(assets.image('backgrounds/screen_death.png'), cx, 0)
        assets.draw_text(cx, 880, '사망', (225, 90, 100), center=True, big=True)
        assets.draw_text(cx, 830, '게이지 또는 체력이 0이 되었습니다', (170, 185, 210), center=True)
    _draw_summary(cx)
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
    import transition
    transition.draw()                              # 화면 전환 점묘 (계획 4-3, 가장 위)
    update_canvas()
