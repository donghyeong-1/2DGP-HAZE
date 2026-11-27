"""연습 메뉴 (v7, 2026-11-24, docs/plan_v7.md 5-F). 연습장에서 F로 연다. 멈춘 게임 위에 줄 목록을 띄운다.

W/S 줄 고르기, A/D 값 바꾸기, Enter 실행, Esc·F 닫기. 실제 일은 practice.py 함수가 한다.
play_mode._on_practice가 stage, player를 채우고 push_mode 한다.
"""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_DOWN, SDLK_ESCAPE, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE,
                    SDLK_UP, SDLK_a, SDLK_d, SDLK_f, SDLK_s, SDLK_w, clear_canvas, get_events, update_canvas)

import config
import assets
import keybinds
import game_framework
import hud_kit as kit
import practice

W, H = config.SCREEN_W, config.SCREEN_H
ROWS = ('enemy', 'reset', 'weapon', 'gauge', 'augment', 'clear', 'sfx', 'hideout', 'close')
NAMES = {'enemy': '적 불러내기', 'reset': '적 정리·허수아비 다시 세우기', 'weapon': '무기 받기',
         'gauge': '헤이즈 게이지', 'augment': '증강 넣기·빼기', 'clear': '증강 모두 빼기',
         'sfx': '효과음 듣기', 'hideout': '은신처로 돌아가기', 'close': '닫기'}     # v8: 효과음을 들어 보고 좋음·바꿔를 표시한다 (sfx_mode)
CHOICE = ('enemy', 'weapon', 'augment')          # A/D로 고르고 Enter로 실행하는 줄
GAUGE_STEP = 10
PANEL_X, PANEL_W = 460, 1000
ROW_H, ROW_STEP = 64, 76
TOP_Y = H - 250
ENEMY_NAMES = {'slum': '슬럼 폐인', 'thrower': '고철 투척병', 'hound': '사냥개', 'guard': '간수', 'rat': '헤이즈 쥐', 'shaman': '누더기 무당',
               'drone': '용접 드론', 'cart': '자폭 수레', 'eye': '감시 눈', 'knight': '결정 기사', 'wraith': '헤이즈 망령'}
WEAPON_NAMES = {'pistol': '쌍권총', 'gauntlet': '건틀릿', 'chain': '사슬'}

stage = None
player = None
selected = 0
index = {'enemy': 0, 'weapon': 0, 'augment': 0}
_under = None


def augment_ids():
    """고를 수 있는 증강 (구현이 끝난 것만)."""
    import mutations
    return [mid for mid, m in mutations.MUTATIONS.items() if m.get('ready', True)]


def _options(item):
    if item == 'enemy':
        return practice.ENEMY_KINDS
    if item == 'weapon':
        return practice.WEAPONS
    return augment_ids()


def enter():
    global selected, _under
    selected = 0
    _under = game_framework.stack[-2] if len(game_framework.stack) >= 2 else None


def exit():
    pass


def pause():
    pass


def resume():
    pass


def change(item, step):
    """A/D: 고르는 값을 옮긴다. 게이지는 바로 바꾼다."""
    if item == 'gauge':
        practice.set_gauge(player, player.gauge.value + step * GAUGE_STEP)
    elif item in CHOICE:
        n = len(_options(item))
        index[item] = (index[item] + step) % n


def run(item):
    """Enter: 그 줄을 실행한다."""
    if item == 'enemy':
        practice.spawn_enemy(stage, practice.ENEMY_KINDS[index['enemy']])
    elif item == 'reset':
        practice.reset(stage)
    elif item == 'weapon':
        practice.set_weapon(player, practice.WEAPONS[index['weapon']])
    elif item == 'augment':
        practice.toggle_augment(player, augment_ids()[index['augment']])
    elif item == 'clear':
        practice.clear_augments(player)
    elif item == 'sfx':
        import sfx_mode
        game_framework.push_mode(sfx_mode)
    elif item == 'hideout':
        import play_mode
        game_framework.pop_mode()
        game_framework.change_mode(play_mode)          # 새로 은신처에서 시작한다 (연습장 증강은 남지 않는다)
    else:
        game_framework.pop_mode()


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type != SDL_KEYDOWN:
            continue
        k = event.key
        if k == SDLK_ESCAPE or keybinds.is_interact(k):       # U1-2: 'F' 대신 상호작용 키
            game_framework.pop_mode()
            return
        if k in (SDLK_w, SDLK_UP):
            selected = (selected - 1) % len(ROWS)
            assets.play_sound('ui_move')                      # U1-2: 줄을 옮기면 소리 (다른 메뉴와 같게)
        elif k in (SDLK_s, SDLK_DOWN):
            selected = (selected + 1) % len(ROWS)
            assets.play_sound('ui_move')
        elif k in (SDLK_a, SDLK_LEFT):
            change(ROWS[selected], -1)
        elif k in (SDLK_d, SDLK_RIGHT):
            change(ROWS[selected], 1)
        elif k in (SDLK_RETURN, SDLK_SPACE):
            assets.play_sound('ui_select')
            run(ROWS[selected])
            return


def update():
    pass


def value_label(item):
    import mutations
    if item == 'enemy':
        kind = practice.ENEMY_KINDS[index['enemy']]
        return f'<  {ENEMY_NAMES.get(kind, kind)}  >'
    if item == 'weapon':
        wid = practice.WEAPONS[index['weapon']]
        return f'<  {WEAPON_NAMES.get(wid, wid)}  >'
    if item == 'gauge':
        return f'<  {player.gauge.value:.0f}%  >'
    if item == 'augment':
        mid = augment_ids()[index['augment']]
        mark = '적용 중' if mutations.has(player, mid) else '없음'
        return f'<  {mutations.MUTATIONS[mid]["name"]} ({mark})  >'
    if item == 'clear':
        return f'{len(mutations.owned(player))}개 적용 중'
    return ''


def footer():
    """아래 키 안내. 닫기 키는 Esc와 상호작용 키 (U1-2: 'F' 고정이었다)."""
    import input_device
    close = 'Esc' if input_device.is_pad() else f"Esc {keybinds.label('interact', first=True)}"   # 패드: B로 닫는다 (N1-3)
    return [(close, '닫기'), ('W S', '선택'), ('A D', '값 변경'), ('Enter', '실행')]


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        kit.frozen_backdrop(_under.draw_frozen)            # mist: '초당 피해'·안내 카드·이름표 없이 (R1)
    if kit.is_mist():
        _draw_mist()
        update_canvas()
        return
    kit.backdrop(0.9)
    kit.heading(PANEL_X, H - 150, '연습 메뉴', '연습장')
    for i, item in enumerate(ROWS):
        cy = TOP_Y - i * ROW_STEP
        on = i == selected
        kit.row(PANEL_X, cy - ROW_H // 2, PANEL_W, ROW_H, on)
        kit.text(PANEL_X + 34, cy, NAMES[item], (240, 248, 255) if on else (190, 202, 225))
        label = value_label(item)
        if label:
            kit.text(PANEL_X + PANEL_W - 34, cy, label, (255, 230, 150) if on else (170, 182, 205), small=True, right=True)
    kit.footer(footer())
    update_canvas()


def _draw_mist():
    """'mist' (11/27 S1): M1 메뉴 화면과 같은 감시 단말 모양. 판·줄 띠·키캡 없이 글자, 고른 줄은 이름만 글자 폭으로 뒤집기 + 커서.
    줄의 자리·값 글자는 그대로."""
    import mist_menu as mm
    mm.dim(mm.DIM_GAME)
    bottom = TOP_Y - (len(ROWS) - 1) * ROW_STEP
    mm.shade(PANEL_X - 10, H - 150 - 66, PANEL_X + 300, H - 150 + 24)
    mm.shade(PANEL_X, bottom - 32, PANEL_X + PANEL_W, TOP_Y + 32)
    mm.footer_shade(footer())
    mm.terminal([('TOWER SURVEILLANCE // TRAINING YARD', mm.PH)])
    mm.title(PANEL_X, H - 150, '연습 메뉴')
    for i, item in enumerate(ROWS):
        cy = TOP_Y - i * ROW_STEP
        on = i == selected
        mm.pick(PANEL_X + 34, cy, NAMES[item], on, mm.PH_SOFT, center=False)
        label = value_label(item)
        if label:
            kit.text(PANEL_X + PANEL_W - 34, cy, label, mm.PH if on else mm.PH_MENU, small=True, right=True)
    mm.footer(footer())
