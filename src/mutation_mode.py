"""헤이즈 변이 3택 카드 창 (2026-11-22 v5 계획 3). 변이 보상 방을 깨면 위에 쌓아 연다(push_mode).

카드 셋이 나란히 놓인다: 위에 계열 문양, 이름, 효과, 아래에 계열 이름과 시너지 진행(가진 수/2).
A·D·왼쪽·오른쪽(또는 W·S)으로 고르고 Enter·Space, 마우스로 올리고 누르면 그 변이를 얻고 닫힌다.
Esc로는 닫지 않는다(반드시 하나 고른다). 카드 그림은 Codex T44가 오기 전까지 코드로 그린 판.
"""
from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDL_QUIT, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE,
                    SDLK_a, SDLK_d,
                    clear_canvas, get_events, update_canvas)

import sys

import assets
import config
import game_framework
import hud_kit as kit
import events
import forms
import mutations as mu

W, H = config.SCREEN_W, config.SCREEN_H
CARD_W, CARD_H, GAP = 360, 500, 60
CARD_Y = (H - CARD_H) // 2 - 30
OPEN_TIME = 0.25           # 카드가 아래에서 올라오는 시간(초)

player = None
choices = []
selected = 0
age = 0.0
_under = None


def setup(p, ids):
    """창을 열기 전에 play_mode가 부른다 (테스트도)."""
    global player, choices, selected, age
    player, choices, selected, age = p, list(ids), 0, 0.0


def choose():
    """고른 카드의 변이를 준다. 시너지가 켜졌으면 알려 준다."""
    mid = choices[selected]
    if mid.startswith(events.CARD):                       # v8 이벤트 방 카드: 이어서 고를 카드가 있으면 돌려준다
        got = events.take(player, mid)
        if got is None:
            return None
        text, color, follow = got
        assets.play_sound('enhance')
        import effects
        cx, cy = player.center
        effects.float_text(cx, cy + 110, text, color, big=True, life=1.2)
        return follow
    if mid.startswith(forms.CARD):                        # v8 무기 형태 카드
        name, color = forms.take_card(player, mid)
        assets.play_sound('enhance')
        import effects
        cx, cy = player.center
        effects.float_text(cx, cy + 110, name, color, big=True, life=1.2)
        return
    fam = mu.MUTATIONS[mid]['family']
    before = mu.synergy(player, fam)
    mu.give(player, mid)
    assets.play_sound('enhance')
    import effects
    cx, cy = player.center
    effects.float_text(cx, cy + 110, mu.MUTATIONS[mid]['name'], mu.FAMILIES[fam]['color'], big=True, life=1.2)
    if mu.synergy(player, fam) and not before:
        effects.float_text(cx, cy + 170, f'{mu.FAMILIES[fam]["name"]} 시너지', (255, 230, 140), life=1.6)


def card_x(i):
    total = len(choices) * CARD_W + (len(choices) - 1) * GAP
    return (W - total) // 2 + i * (CARD_W + GAP)


def enter():
    global _under
    _under = game_framework.stack[-2] if len(game_framework.stack) >= 2 else None
    assets.play_sound('zone_awake')


def exit():
    pass


def pause():
    pass


def resume():
    pass


def can_pick(i):
    """고를 수 있는 카드인가 (이벤트 카드는 체력·조각이 모자라면 못 고른다)."""
    mid = choices[i]
    return not mid.startswith(events.CARD) or events.card_info(player, mid)['ok']


def _pick(i):
    global selected
    selected = i
    if not can_pick(i):
        assets.play_sound('ui_move')
        return
    assets.play_sound('ui_select')
    follow = choose()
    if follow:                                            # 거래로 얻은 증강 선택처럼 카드가 이어진다
        setup(player, follow)
        return
    game_framework.pop_mode()


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if not choices:                                   # 고를 카드가 없다 (내놓을 증강이 바닥남 등): 튕기지 않고 닫는다
            game_framework.pop_mode()
            return
        if age < OPEN_TIME:                               # 올라오는 동안 누른 것은 무시 (공격 연타로 잘못 고르지 않게)
            continue
        if event.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN):
            mx, my = event.x, H - 1 - event.y
            for i in range(len(choices)):
                if card_x(i) <= mx < card_x(i) + CARD_W and CARD_Y <= my < CARD_Y + CARD_H:
                    if event.type == SDL_MOUSEBUTTONDOWN:
                        _pick(i)
                        return
                    if i != selected:
                        assets.play_sound('ui_move')
                    selected = i
            continue
        if event.type == SDL_KEYDOWN and event.key in (SDLK_LEFT, SDLK_a):
            selected = (selected - 1) % len(choices)
            assets.play_sound('ui_move')
            continue
        if event.type == SDL_KEYDOWN and event.key in (SDLK_RIGHT, SDLK_d):
            selected = (selected + 1) % len(choices)
            assets.play_sound('ui_move')
            continue
        if event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_SPACE):
            _pick(selected)
            return


def update():
    global age
    age += game_framework.frame_time if getattr(game_framework, 'frame_time', 0) else 1 / 60
    if not choices and game_framework.stack and game_framework.stack[-1] is _self():
        game_framework.pop_mode()                         # 카드 없이 열렸다: 입력을 기다리지 않고 닫는다


def _self():
    return sys.modules[__name__]


CORNER = 120               # 카드 테두리 그림(300x420)의 모서리 크기. 가운데 9칸 자르기 (Codex T44)


def _completes_synergy(m):
    """이 카드를 고르면 같은 계열이 2개가 되는가 (테두리를 희귀로 바꾼다)."""
    return player is not None and mu.family_count(player, m['family']) + 1 >= 2


def draw_frame(x, y, w, h, rarity='common'):
    """카드 테두리를 9칸 자르기로 (x, y) 왼쪽 아래에 w x h로 그린다: 모서리는 그대로, 변은 1배로 이어 붙인다."""
    img = assets.image(f'ui/card_frame_{rarity}.png')
    c, mid_w, mid_h = CORNER, img.w - 2 * CORNER, img.h - 2 * CORNER
    sw, sh = img.w, img.h
    for bx, by, dx, dy in ((0, 0, 0, 0), (sw - c, 0, w - c, 0), (0, sh - c, 0, h - c), (sw - c, sh - c, w - c, h - c)):
        assets.draw_clip(img, bx, by, c, c, x + dx, y + dy)
    off = c
    while off < w - c:                                    # 위·아래 변
        step = min(mid_w, w - c - off)
        assets.draw_clip(img, c, 0, step, c, x + off, y)
        assets.draw_clip(img, c, sh - c, step, c, x + off, y + h - c)
        off += step
    off = c
    while off < h - c:                                    # 왼쪽·오른쪽 변
        step = min(mid_h, h - c - off)
        assets.draw_clip(img, 0, c, c, step, x, y + off)
        assets.draw_clip(img, sw - c, c, c, step, x + w - c, y + off)
        off += step


def _draw_form_card(i, mid):
    """무기 형태 카드: 금색 테두리, 무기 그림, 형태 이름과 설명. 'form:skip'은 넘기기."""
    wid = mid[len(forms.CARD):]
    hot = i == selected
    k = min(1.0, age / OPEN_TIME)
    x = card_x(i)
    y = int(CARD_Y - (1 - k) * (1 - k) * 400) + (16 if hot else 0)
    skip = wid == 'skip'
    color = (150, 165, 190) if skip else forms.COLOR
    if hot:
        assets.draw_rect_color(x - 6, y - 6, CARD_W + 12, CARD_H + 12, color)
    assets.draw_rect_color(x + 8, y + 8, CARD_W - 16, CARD_H - 16, (10, 14, 26))
    draw_frame(x, y, CARD_W, CARD_H, 'common' if skip else 'legendary')
    if skip:
        name, sub, desc = '넘기기', '형태를 얻지 않습니다', f'대신 조각 {forms.SKIP_SHARDS}개를 받습니다'
    else:
        img = assets.image(f'ui/icon_w_{wid}.png')
        assets.draw_image(img, x + CARD_W // 2, y + CARD_H - 70 - img.h)
        kit.text(x + CARD_W // 2, y + CARD_H - 54, '형태', color, center=True, small=True)
        name, sub, desc = forms.FORMS[wid]['name'], mu.WEAPON_NAMES.get(wid, '') + ' · 기본 공격이 바뀝니다', forms.FORMS[wid]['desc']
    kit.text(x + CARD_W // 2, y + CARD_H - 200, name, (240, 244, 252), center=True, big=True)
    for j, line in enumerate(_wrap(sub, 13)):
        kit.text(x + CARD_W // 2, y + CARD_H - 250 - j * 28, line, color, center=True, small=True)
    for j, line in enumerate(_wrap(desc, 13)):
        kit.text(x + CARD_W // 2, y + CARD_H - 330 - j * 30, line, (205, 215, 235), center=True, small=True)


def _draw_event_card(i, mid):
    """이벤트 방 카드(헤이즈 샘·떠돌이 죄수): 아이콘, 이름, 대가(또는 구간), 설명. 고를 수 없으면 어둡게."""
    info = events.card_info(player, mid)
    hot = i == selected
    k = min(1.0, age / OPEN_TIME)
    x = card_x(i)
    y = int(CARD_Y - (1 - k) * (1 - k) * 400) + (16 if hot else 0)
    ok = info['ok']
    color = info['color'] if ok else (96, 104, 124)
    if hot:
        assets.draw_rect_color(x - 6, y - 6, CARD_W + 12, CARD_H + 12, color)
    assets.draw_rect_color(x + 8, y + 8, CARD_W - 16, CARD_H - 16, (10, 14, 26))
    draw_frame(x, y, CARD_W, CARD_H, 'rare' if ok and info['icon'] else 'common')
    if info['icon']:
        img = assets.image(info['icon'])
        assets.draw_image(img, x + CARD_W // 2, y + CARD_H - 70 - img.h)
    kit.text(x + CARD_W // 2, y + CARD_H - 200, info['name'], (240, 244, 252) if ok else (130, 140, 160), center=True, big=True)
    kit.text(x + CARD_W // 2, y + CARD_H - 250, info['sub'], color, center=True, small=True)
    for j, line in enumerate(_wrap(info['desc'], 13)):
        kit.text(x + CARD_W // 2, y + CARD_H - 300 - j * 30, line, (205, 215, 235) if ok else (110, 120, 140), center=True, small=True)
    if not ok:
        kit.text(x + CARD_W // 2, y + 84, info.get('why', '선택할 수 없습니다'), (255, 150, 150), center=True, small=True)


def _draw_card(i, mid):
    if mid.startswith(events.CARD):
        _draw_event_card(i, mid)
        return
    if mid.startswith(forms.CARD):
        _draw_form_card(i, mid)
        return
    m = mu.MUTATIONS[mid]
    fam = mu.FAMILIES[m['family']]
    hot = i == selected
    k = min(1.0, age / OPEN_TIME)
    x = card_x(i)
    y = int(CARD_Y - (1 - k) * (1 - k) * 400) + (16 if hot else 0)
    color = fam['color']
    if hot:                                               # 고른 카드: 계열 색 테두리
        assets.draw_rect_color(x - 6, y - 6, CARD_W + 12, CARD_H + 12, color)
    assets.draw_rect_color(x + 8, y + 8, CARD_W - 16, CARD_H - 16, (10, 14, 26))      # 카드 속
    info = mu.card_info(player, mid) if player is not None else {'rarity': 'common', 'note': fam['set'], 'hot': False}
    tier = mu.tier(mid)
    draw_frame(x, y, CARD_W, CARD_H, info['rarity'])      # v7: 기본 = 보통 / 진화 = 희귀 / 합성 = 전설 테두리
    img = assets.image(fam['icon'])
    assets.draw_image(img, x + CARD_W // 2, y + CARD_H - 70 - img.h)
    if tier != 'base':                                    # 진화·합성 띠
        label, band = ('진화', color) if tier == 'evo' else ('합성', (255, 214, 120))
        kit.text(x + CARD_W // 2, y + CARD_H - 54, label, band, center=True, small=True)
    kit.text(x + CARD_W // 2, y + CARD_H - 200, m['name'], (240, 244, 252), center=True, big=True)
    weapon = fam.get('weapon')
    sub = fam['name'] + (' 계열' if m['family'] in mu.GAUGE_FAMILIES else ' 갈래')
    if weapon:
        sub = mu.WEAPON_NAMES.get(weapon, '') + ' · ' + sub
    kit.text(x + CARD_W // 2, y + CARD_H - 250, sub, color, center=True, small=True)
    for j, line in enumerate(_wrap(m['desc'], 13)):
        kit.text(x + CARD_W // 2, y + CARD_H - 300 - j * 30, line, (205, 215, 235), center=True, small=True)   # 세 줄까지 (그 아래는 갈래 칸)
    if tier == 'base':                                    # 이걸 고르면 같은 갈래가 몇 개가 되는가 (진화까지 2개)
        have = (mu.family_count(player, m['family']) if m['family'] in mu.GAUGE_FAMILIES
                else mu.base_count(player, m['family'])) if player is not None else 0
        pips = min(2, have + 1)
        for k in range(2):                                # 칸 두 개: 찬 칸은 갈래 색
            px = x + CARD_W // 2 - 26 + k * 32
            assets.draw_rect_color(px - 2, y + 112, 24, 16, (12, 14, 22))
            assets.draw_rect_color(px, y + 114, 20, 12, color if k < pips else (54, 62, 82))
    for j, line in enumerate(_wrap(info['note'], 16)):
        kit.text(x + CARD_W // 2, y + 84 - j * 26, line, (255, 225, 140) if info['hot'] else (130, 145, 170), center=True,
                 small=True)


def _wrap(text, n):
    """한글 글자 수로 대략 자른다 (띄어쓰기에서)."""
    out, line = [], ''
    for word in text.split(' '):
        if line and len(line) + 1 + len(word) > n:
            out.append(line)
            line = word
        else:
            line = (line + ' ' + word).strip()
    if line:
        out.append(line)
    return out


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), 0.66)
    form = any(c.startswith(forms.CARD) for c in choices)
    title = '무기 형태' if form else '증강 선택'
    sub = ('무기 하나의 기본 공격이 달라집니다. ' if form else '하나를 선택하세요. ') + '이번 판이 끝날 때까지 유지됩니다'
    if choices and choices[0].startswith(events.CARD):    # v8 이벤트 방: 헤이즈 샘·떠돌이 죄수
        title, sub = events.TITLES['spring' if ':spring:' in choices[0] else 'drifter']
    kit.text(W // 2, CARD_Y + CARD_H + 110, title, (244, 236, 214), center=True, big=True)
    kit.text(W // 2, CARD_Y + CARD_H + 66, sub, (150, 165, 190), center=True, small=True)
    for i, mid in enumerate(choices):
        _draw_card(i, mid)
    kit.footer([('A D', '선택'), ('Enter', '확인')], y=CARD_Y - 80)
    update_canvas()
