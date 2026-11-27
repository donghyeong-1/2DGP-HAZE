"""키 바꾸기 창 (2026-11-21 퀄리티 계획 2-6). 설정 창에서 '키 설정'로 위에 쌓아 연다.

동작마다 두 칸(기본·보조). 칸을 고르고 Enter(또는 마우스로 누르기)를 누르면 '키를 누르세요'가 되고,
다음에 누른 키가 그 칸에 들어간다. 다른 동작이 쓰던 키면 서로 맞바뀐다(keybinds.bind).
기다리는 중에 Esc는 취소, Backspace·Delete는 보조 칸 비우기. 마우스(공격·대시·조준)는 바꾸지 않는다.
키보드: 위/아래·W/S 줄, 좌/우·A/D 칸, Enter 바꾸기, Esc 돌아가기. 아래 줄은 '기본값으로'·'돌아가기'.
"""
from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDL_QUIT, SDLK_BACKSPACE, SDLK_DELETE,
                    SDLK_DOWN, SDLK_ESCAPE, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE, SDLK_UP, SDLK_a, SDLK_d,
                    SDLK_s, SDLK_w, clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import hud_kit as kit
import mist_menu as mm
import keybinds

W, H = config.SCREEN_W, config.SCREEN_H
ROW_STEP = 56                 # v7: 동작 11개(물약 추가)가 화면에 들어가게 (예전 60)
N = len(keybinds.IDS)
PANEL_W, PANEL_H = 1180, 290 + ROW_STEP * N
PANEL_X, PANEL_Y = (W - PANEL_W) // 2, (H - PANEL_H) // 2 - 10
ROW_Y = [PANEL_Y + PANEL_H - 160 - i * ROW_STEP for i in range(N)]
SLOT_X = (PANEL_X + 560, PANEL_X + 850)
SLOT_W = 270
BUTTON_ROW = N                                   # 맨 아래 줄 (기본값으로 · 돌아가기)
buttons = (kit.Button('defaults', '기본값으로', W // 2 - 390, PANEL_Y + 40, 360, 64),
           kit.Button('back', '돌아가기', W // 2 + 30, PANEL_Y + 40, 360, 64))
row, col = 0, 0
listening = None                                 # (동작, 칸): 다음 키를 기다리는 중
message = ''
_under = None


def enter():
    global row, col, listening, message, _under
    row, col, listening, message = 0, 0, None, ''
    _under = game_framework.stack[-2] if len(game_framework.stack) >= 2 else None


def exit():
    pass


def pause():
    pass


def resume():
    pass


def press_key(key):
    """기다리는 칸에 키를 넣는다 (테스트에서도 쓴다). 처리 결과 글을 message에 남긴다."""
    global listening, message
    action, slot = listening
    listening = None
    if key == SDLK_ESCAPE:
        message = '취소했습니다'
        return
    if key in (SDLK_BACKSPACE, SDLK_DELETE):
        if slot == 1:
            keybinds.clear(action, 1)
            message = f'{keybinds.NAMES[action]}: 보조 칸을 비웠습니다'
        else:
            message = '기본 칸은 비울 수 없습니다'
        return
    if key in keybinds.RESERVED:
        message = f'{keybinds.key_name(key)} 키는 쓸 수 없습니다 (일시정지·도움말에 쓰입니다)'
        return
    before = keybinds.action_for(key)
    if keybinds.bind(action, slot, key):
        name = keybinds.key_name(key)
        if before is not None and before != action:
            message = f'{name}: {keybinds.NAMES[action]} ({keybinds.NAMES[before]} 키와 서로 바꿨습니다)'
        else:
            message = f'{name}: {keybinds.NAMES[action]}'
        assets.play_sound('pickup')
    else:
        message = f'{keybinds.NAMES[before]}에 남는 키가 없어 바꿀 수 없습니다'


def _run_button(i):
    global message
    if i == 0:
        keybinds.reset_defaults()
        message = '기본 키로 되돌렸습니다'
        assets.play_sound('pickup')
    else:
        game_framework.pop_mode()


def _slot_at(mx, my):
    for i in range(N):
        for s in (0, 1):
            if SLOT_X[s] <= mx <= SLOT_X[s] + SLOT_W and ROW_Y[i] - 26 <= my <= ROW_Y[i] + 26:
                return i, s
    return None


def handle_events():
    global row, col, listening, message
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if listening is not None:
            if event.type == SDL_KEYDOWN:
                press_key(event.key)
            elif event.type == SDL_MOUSEBUTTONDOWN:
                listening = None
                message = '취소했습니다'
            continue
        if event.type == SDL_MOUSEMOTION:
            mx, my = event.x, H - 1 - event.y
            hit = _slot_at(mx, my)
            if hit:
                row, col = hit
            for i, b in enumerate(buttons):
                if b.contains(mx, my):
                    row, col = BUTTON_ROW, i
        elif event.type == SDL_MOUSEBUTTONDOWN:
            mx, my = event.x, H - 1 - event.y
            hit = _slot_at(mx, my)
            if hit:
                row, col = hit
                listening = (keybinds.IDS[row], col)
                message = ''
            for i, b in enumerate(buttons):
                if b.contains(mx, my):
                    _run_button(i)
                    return
        elif event.type == SDL_KEYDOWN:
            if event.key == SDLK_ESCAPE:
                game_framework.pop_mode()
                return
            if event.key in (SDLK_w, SDLK_UP):
                row = (row - 1) % (N + 1)
            elif event.key in (SDLK_s, SDLK_DOWN):
                row = (row + 1) % (N + 1)
            elif event.key in (SDLK_a, SDLK_LEFT, SDLK_d, SDLK_RIGHT):
                col = 1 - col
            elif event.key in (SDLK_RETURN, SDLK_SPACE):
                if row == BUTTON_ROW:
                    _run_button(col)
                    return
                listening = (keybinds.IDS[row], col)
                message = ''


def update():
    pass


def draw_panel():
    """키 바꾸기 화면 (11/22 메뉴 v2): 줄마다 카드, 기본·보조 칸은 키 글자 알약."""
    kit.heading(PANEL_X, PANEL_Y + PANEL_H - 22, '키 설정', '마우스: 조준 · 좌클릭 공격 · 우클릭 대시 (바꿀 수 없습니다)')
    kit.text(SLOT_X[0] + SLOT_W // 2, PANEL_Y + PANEL_H - 112, '기본', kit.FAINT, small=True, center=True)
    kit.text(SLOT_X[1] + SLOT_W // 2, PANEL_Y + PANEL_H - 112, '보조', kit.FAINT, small=True, center=True)
    for i, action in enumerate(keybinds.IDS):
        cy = ROW_Y[i]
        on = i == row
        kit.row(PANEL_X, cy - 25, PANEL_W, 50, on)
        kit.text(PANEL_X + 34, cy, keybinds.NAMES[action], (240, 248, 255) if on else (190, 202, 225))
        for s in (0, 1):
            wait = listening == (action, s)
            hot = wait or (on and col == s)
            label = '키를 누르세요' if wait else keybinds.key_name(keybinds.keys(action)[s])
            kit.pill(SLOT_X[s], cy - 19, SLOT_W, 38, label, hot)
    if message:
        kit.text(W // 2, PANEL_Y + 150, message, kit.ACCENT, small=True, center=True)
    for i, b in enumerate(buttons):
        b.draw(row == BUTTON_ROW and col == i)
    if listening:
        kit.footer([('아무 키', '그 칸에 넣기'), ('Backspace', '보조 칸 비우기'), ('Esc', '취소')])
    else:
        kit.footer([('W S', '줄'), ('A D', '칸'), ('Enter', '변경'), ('Esc', '돌아가기')])


# ----- 'mist' (11/27 M1): 타이틀 감시 단말과 한 벌 -----
KEYS_FOOTER = [('W S', '줄'), ('A D', '칸'), ('Enter', '변경'), ('Esc', '돌아가기')]
LISTEN_FOOTER = [('아무 키', '그 칸에 넣기'), ('Backspace', '보조 칸 비우기'), ('Esc', '취소')]


def draw_mist_panel():
    """'mist' 키 설정: 판·줄 띠 없이 글자. 고른 줄은 이름 앞 커서 + 밝은 이름, 고른 칸(또는 키를 기다리는 칸)은 키 글자 판을
    인광색으로 채워 뒤집는다. 키 글자 판은 H1과 같은 가는 테두리. 칸·버튼 자리(마우스로 누르는 자리)는 그대로."""
    head_y = PANEL_Y + PANEL_H - 22
    mm.shade(PANEL_X - 10, head_y - 60, PANEL_X + 900, head_y + 24)
    mm.shade(PANEL_X, ROW_Y[-1] - 28, PANEL_X + PANEL_W, PANEL_Y + PANEL_H - 96)
    for b in buttons:
        mm.text_shade(b.x + b.w // 2, b.y + b.h // 2, b.label, center=True)
    if message:
        mm.text_shade(W // 2, PANEL_Y + 150, message, small=True, center=True)
    mm.footer_shade(LISTEN_FOOTER if listening else KEYS_FOOTER)
    mm.terminal([('TOWER SURVEILLANCE // INPUT MAP', mm.PH)])
    mm.title(PANEL_X, head_y, '키 설정')
    kit.text(PANEL_X + 2, head_y - 42, '마우스: 조준 · 좌클릭 공격 · 우클릭 대시 (바꿀 수 없습니다)', mm.PH_SOFT, small=True)
    kit.text(SLOT_X[0] + SLOT_W // 2, PANEL_Y + PANEL_H - 112, '기본', mm.PH_MENU, small=True, center=True)
    kit.text(SLOT_X[1] + SLOT_W // 2, PANEL_Y + PANEL_H - 112, '보조', mm.PH_MENU, small=True, center=True)
    for i, action in enumerate(keybinds.IDS):
        cy = ROW_Y[i]
        on = i == row
        if on:
            mm.cursor(PANEL_X + 34, cy)
        kit.text(PANEL_X + 34, cy, keybinds.NAMES[action], mm.PH if on else mm.PH_SOFT)
        for s in (0, 1):
            wait = listening == (action, s)
            hot = wait or (on and col == s)
            label = '키를 누르세요' if wait else keybinds.key_name(keybinds.keys(action)[s])
            w = max(34, assets.text_width(label, True) + 16) // 2 * 2
            mm.keycap(SLOT_X[s] + SLOT_W // 2 - w // 2, cy - 15, label, hot=on, inverted=hot)
    if message:
        kit.text(W // 2, PANEL_Y + 150, message, mm.PH, small=True, center=True)
    for i, b in enumerate(buttons):
        mm.pick(b.x + b.w // 2, b.y + b.h // 2, b.label, row == BUTTON_ROW and col == i)
    mm.footer(LISTEN_FOOTER if listening else KEYS_FOOTER)


def draw():
    clear_canvas()
    if kit.is_mist():
        if _under is not None and hasattr(_under, 'draw_scene'):
            kit.frozen_backdrop(_under.draw_scene)     # R1: 멈춘 게임이면 안내 카드·이름표 없이
        mm.dim(mm.scene_dim(_under))
        draw_mist_panel()
        update_canvas()
        return
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()
    kit.backdrop(1.0)                # 설정 화면 위에 겹치므로 완전히 가린다
    draw_panel()
    update_canvas()
