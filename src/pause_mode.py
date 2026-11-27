"""일시정지 창: 멈춘 게임 위에 메뉴(계속하기 · 설정 · 타이틀로)와 조작 안내를 띄운다.

Esc로 바로 돌아가고, O는 설정, H는 은신처로, Q는 타이틀. 판을 포기하는 두 항목은 두 번 눌러야 한다. 메뉴는 키보드(W/S, Enter)와 마우스로 고른다.
"""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_h, SDLK_o, SDLK_q, clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import game_world
import hud_kit as kit
import mist_menu as mm

W, H = config.SCREEN_W, config.SCREEN_H
LEFT_X = 150                       # 메뉴 줄 왼쪽 (11/22 메뉴 v2: 큰 판 없이 화면 전체를 덮는다)
MENU = [kit.Button(key, label, LEFT_X, H - 380 - i * 84, 420, 66)
        for i, (key, label) in enumerate((('resume', '계속하기'), ('options', '설정'),
                                          ('hideout', '판 포기하고 은신처로'), ('title', '판 포기하고 타이틀로')))]
CARD_H = 140 + 50 * 10            # 오른쪽 카드 두 장: 조작 / 이번 판 (조작 10줄 높이)
CARD_Y = H - 314 - CARD_H + 66


def pad_controls():
    """게임패드 조작표 (N1-3). gamepad.PLAY_BUTTONS와 같은 배치. 물약은 패드 버튼이 없어 키보드 키를 적는다."""
    import keybinds
    potion = keybinds.key_name(keybinds.keys('potion')[0])
    return [
        ('L스틱', '좌우 이동'),
        ('A', '점프 (2단, 짧게 누르면 낮게)'),
        ('↓ + A', '얇은 발판 아래로'),
        ('R스틱', '조준'),
        ('X', '공격 (공중·대시 중에는 특수 공격)'),
        ('B  LT', '대시 (아래로 겨누면 발판 통과)'),
        ('RB  RT', '강화 (게이지 25%, 세 번이면 궁극기)'),
        ('LB', '무기 교체 (교체하는 순간 교체기)'),
        ('Y', '말 걸기·줍기·구매'),
        (potion, '물약 마시기 (키보드만)'),
    ]


def controls():
    """(키, 설명) 목록. 키 이름은 키 설정(설정 > 키 바꾸기)을 따른다. 마지막 장치가 패드면 패드 조작표 (N1-3)."""
    import input_device
    if input_device.is_pad():
        return pad_controls()
    import keybinds
    k = keybinds.label
    j = keybinds.label('jump').replace('/', '  ')
    return [
        (f'{k("left")}  {k("right")}', '좌우 이동'),
        (j, '점프 (2단, 짧게 누르면 낮게)'),
        (f'{k("down")} + {k("jump", first=True)}', '얇은 발판 아래로'),
        ('마우스', '조준'),
        ('좌클릭', '공격 (공중·대시 중에는 특수 공격)'),
        (f'{k("dash")}  우클릭', '대시 (아래로 겨누면 발판 통과)'),
        (k('enhance'), '강화 (게이지 25%, 세 번이면 궁극기)'),
        (f'{k("swap")}  {k("weapon1")}  {k("weapon2")}', '무기 교체 (교체하는 순간 교체기)'),
        (k('interact'), '말 걸기·줍기·구매'),
        (k('potion'), '물약 마시기 (체력 회복)'),
    ]


selected = 0
CONFIRM = ('hideout', 'title')                # 판을 포기하는 항목: 실수로 나가지 않게 두 번 누르게 한다
LABELS = {b.key: b.label for b in MENU}
GIVE_UP_ASK = {'hideout': '한 번 더: 판 포기, 은신처로', 'title': '한 번 더: 판 포기, 타이틀로'}   # U1-2: 어디로 가는지 (전 문구보다 짧게: 조작표와 겹치지 않게)
asking = None                                 # 한 번 눌러 확인을 기다리는 항목


def _button(key):
    return next(b for b in MENU if b.key == key)


def _reset_labels():
    global asking
    asking = None
    for b in MENU:
        b.label = LABELS[b.key]


def enter():
    global selected
    selected = 0
    _reset_labels()


def exit():
    pass


def pause():
    pass


def resume():
    pass


def run(key):
    global asking
    if key in CONFIRM and asking != key:
        _reset_labels()
        asking = key
        _button(key).label = GIVE_UP_ASK[key]      # 첫 입력은 묻기만 한다
        return
    _reset_labels()
    if key == 'resume':
        game_framework.pop_mode()
    elif key == 'options':
        import options_mode
        game_framework.push_mode(options_mode)
    elif key == 'hideout':                         # 판 포기: 은신처에서 새 판 (영구 성장은 meta에 남는다)
        import play_mode
        game_framework.pop_mode()
        game_framework.change_mode(play_mode)
    else:
        import title_mode
        game_framework.pop_mode()                  # 일시정지를 끝낸 뒤
        game_framework.change_mode(title_mode)     # 플레이 모드를 타이틀로 교체


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN and event.key in (SDLK_ESCAPE, SDLK_o, SDLK_h, SDLK_q):
            run({SDLK_ESCAPE: 'resume', SDLK_o: 'options', SDLK_h: 'hideout', SDLK_q: 'title'}[event.key])
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


def draw_scene():
    """위에 쌓인 설정 창(mist)이 깔 배경: 멈춘 게임 화면."""
    draw_frozen()


# 'mist'(11/27 M1): 판 없이 글자. 색은 타이틀 인광색 (mist_menu), 뜻이 있는 색(갈래·저주·형태·금)은 그대로
def _faint():
    return mm.PH_SOFT if kit.is_mist() else kit.FAINT


def _body():
    return mm.PH_TEXT if kit.is_mist() else (235, 242, 252)


def _note():
    return mm.PH_TEXT if kit.is_mist() else (205, 215, 235)


def _section(x, y, w, h, title):
    """조작·이번 판 묶음의 머리. 철판·결정형: 정보 카드 / mist: 판 없이 제목 글자 + 가는 선 한 줄."""
    if not kit.is_mist():
        kit.card(x, y, w, h, title)
        return
    kit.text(x + 28, y + h - 34, title, mm.PH)
    mm.rule(x + 28, y + h - 62, w - 56)


def _key_tokens(keys):
    """'A  D', 'S + Space' -> 키 글자 판으로 그릴 조각들 ('+'는 글자 그대로)."""
    return [k for k in keys.replace('/', ' ').split() if k]


def _draw_controls(x, y, w, h):
    _section(x, y, w, h, '조작')
    keycap = mm.keycap if kit.is_mist() else kit.keycap
    for i, (keys, what) in enumerate(controls()):
        ry = y + h - 110 - i * 50
        kx = x + 28
        for tok in _key_tokens(keys):
            if tok == '+':
                kit.text(kx + 2, ry + 15, '+', _faint(), small=True)
                kx += 22
                continue
            kx += keycap(kx, ry, tok) + 6
        kit.text(x + 250, ry + 15, what, _note(), small=True)


def form_rows(p):
    """이번 판에 얻은 무기 형태: (형태 이름, 무기 이름, 지금 든 무기인가). 든 무기의 형태가 먼저."""
    import forms
    import mutations as mu
    owned = getattr(p, 'forms', None) if p is not None else None
    if not owned:
        return []
    held = [w.weapon_id for w in getattr(p, 'weapons', ()) if w is not None]
    order = [wid for wid in held if wid in owned] + [wid for wid in forms.FORMS if wid in owned and wid not in held]
    return [(forms.FORMS[wid]['name'], mu.WEAPON_NAMES.get(wid, wid), wid in held) for wid in order]


BUILD_W = 400                  # '이번 판' 카드 폭
CURSE_INDENT = 48              # 저주 내용 줄의 왼쪽 여백 (형태·증강 줄과 같다)


def curse_row(p):
    """지금 걸린 저주: (이름 · 짧은 내용, 전투방 n). 없으면 None (2026-11-26 사용자 결정).
    한 줄로 쓰면 가장 긴 것이 카드 폭을 넘어서 머리 줄('저주' + 전투방 n)과 내용 줄로 나눠 그린다."""
    import curse
    cid = curse.active(p) if p is not None else None
    if cid is None:
        return None
    c = curse.CURSES[cid]
    return f'{c["name"]} · {c["short"]}', f'전투방 {curse.rooms_left(p)}'


def has_build(p):
    """'이번 판' 카드에 보일 것이 있는가 (저주·형태·증강·아이템)."""
    if p is None:
        return False
    return bool(curse_row(p) or form_rows(p) or getattr(p, 'mutations', None) or p.items)


def _draw_curse(p, x, ty, w):
    """저주 줄(머리 + 내용)을 그리고 다음 줄의 y를 돌려준다. 저주가 없으면 그대로."""
    import curse
    row = curse_row(p)
    if row is None:
        return ty
    text, rooms = row
    assets.draw_rect_color(x + 28, ty + 2, w - 56, 2, curse.COLOR, 0.5)
    kit.text(x + 28, ty + 20, '저주', curse.COLOR, small=True)
    kit.text(x + w - 28, ty + 20, rooms, curse.COLOR, small=True, right=True)
    ty -= 34
    kit.text(x + CURSE_INDENT, ty + 15, text, (255, 190, 196), small=True)
    return ty - 34 - 18


def _draw_forms(p, x, ty, w):
    """형태 줄들을 그리고 다음 줄의 y를 돌려준다."""
    import forms
    rows = form_rows(p)
    if not rows:
        return ty
    assets.draw_rect_color(x + 28, ty + 2, w - 56, 2, forms.COLOR, 0.5)
    kit.text(x + 28, ty + 20, '무기 형태', forms.COLOR, small=True)
    ty -= 34
    for name, weapon, on in rows:
        kit.text(x + 48, ty + 15, name, (255, 225, 140) if on else _faint(), small=True)
        kit.text(x + w - 28, ty + 15, weapon if on else f'{weapon} 미장착', _faint(), small=True, right=True)
        ty -= 34
    return ty - 18


def _draw_build(x, y, w, h):
    """이번 판: 저주, 무기 형태, 증강(갈래 색), 아이템."""
    import play_mode
    import items
    import mutations as mu
    p = play_mode.player
    _section(x, y, w, h, '이번 판')
    ty = y + h - 110
    muts = list(getattr(p, 'mutations', [])) if p is not None else []
    if not has_build(p):
        kit.text(x + 28, ty + 15, '아직 얻은 증강·아이템이 없습니다', _faint(), small=True)
        kit.text(x + 28, ty - 12, '방 보상과 진열대에서 얻습니다', _faint(), small=True)
        return
    ty = _draw_curse(p, x, ty, w)                                  # 걸린 저주가 맨 위 (2026-11-26)
    ty = _draw_forms(p, x, ty, w)
    for fam_id, mids in (mu.grouped(p) if p is not None else []):     # v7: 갈래별로 묶어 보인다
        if ty < y + 60:
            break
        fam = mu.FAMILIES[fam_id]
        on = mu.active(p, mids[0])
        color = fam['color'] if on else (96, 104, 124)                  # 안 든 무기의 갈래는 흐리게
        assets.draw_rect_color(x + 28, ty + 2, w - 56, 2, color, 0.5)
        head = fam['name'] + (f' {sum(1 for m in mids if mu.tier(m) == "base")}/2' if fam_id != 'duo' else '')
        kit.text(x + 28, ty + 20, head, color, small=True)
        if not on:
            weapon = mu.WEAPON_NAMES.get(fam.get('weapon'), '')
            kit.text(x + w - 28, ty + 20, f'{weapon} 미장착', _faint(), small=True, right=True)
        ty -= 34
        for mid in mids:
            if ty < y + 40:
                break
            star = {'evo': '진화 ', 'duo': '합성 '}.get(mu.tier(mid), '')
            kit.text(x + 48, ty + 15, star + mu.MUTATIONS[mid]['name'],
                     ((255, 225, 140) if star else _body()) if on else _faint(), small=True)
            ty -= 34
        ty -= 8
    if muts:
        ty -= 10
    counts = {}
    for item_id in (p.items if p is not None else []):
        counts[item_id] = counts.get(item_id, 0) + 1
    for item_id, n in counts.items():
        if ty < y + 20:
            break
        kit.icon(f'icon_{item_id}', x + 24, ty - 12)
        kit.text(x + 84, ty + 15, items.ITEMS[item_id]['name'] + (f' x{n}' if n > 1 else ''), _note(), small=True)
        ty -= 58


FOOTER = [('Esc', '계속'), ('O', '설정'), ('H', '은신처로'), ('Q', '타이틀로'), ('W S', '선택'), ('Enter', '확인')]
MIST_DIM = mm.DIM_GAME         # mist: 멈춘 게임 화면 전체를 어둡게 (그 위 글자 둘레는 글자 뒤 어둠이 한 번 더)
CONTROLS_X, BUILD_X, CONTROLS_W = 660, 1390, 700


def _draw_mist():
    """'mist' 일시정지 (11/27 M1, 타이틀 감시 단말과 한 벌): 멈춘 게임을 어둡게 한 위에 글자 뒤 어둠, 주사선, 네 귀퉁이 꺾쇠,
    감시 머리글. 판·띠·노란 꺾쇠 없이 메뉴는 고른 항목만 글자 폭으로 색 뒤집기 + 커서. 조작·이번 판도 판 없이 글자."""
    import play_mode
    kit.frozen_backdrop(draw_frozen)                # R1: 처음 안내 카드·이름표 없이 (제목·메뉴 뒤에 비쳐 겹쳤다)
    mm.dim(MIST_DIM)
    st = getattr(play_mode, 'stage', None)
    sub = getattr(st, 'title', '') or None
    hy = H - 150
    widths = [assets.text_width(b.label, False) for b in MENU]
    tx = LEFT_X + 40
    # 제목·부제와 메뉴 줄을 한 기둥으로 (사이에 비치는 처음 안내 카드 글자가 메뉴 글자와 겹쳐 보이지 않게)
    mm.shade(LEFT_X - 10, MENU[-1].y + 14, max(tx + max(widths) + 20, LEFT_X + 330), hy + 24)
    top = CARD_Y + CARD_H - 10
    mm.shade(CONTROLS_X + 12, CARD_Y + 140, CONTROLS_X + CONTROLS_W - 20, top)        # 조작 (열 줄)
    mm.shade(BUILD_X + 12, CARD_Y + 140, BUILD_X + BUILD_W - 20, top)                 # 이번 판
    mm.footer_shade(FOOTER)
    mm.terminal([('TOWER SURVEILLANCE // FEED PAUSED', mm.PH), ('LIVE FEED · 화면 정지 · HOLD', mm.PH_DIM)])
    mm.title(LEFT_X, hy, '일시정지')
    if sub:
        kit.text(LEFT_X + 2, hy - 42, sub, mm.PH_SOFT, small=True)
    for i, b in enumerate(MENU):
        mm.pick(tx, b.y + b.h // 2, b.label, i == selected, center=False)
    _draw_controls(CONTROLS_X, CARD_Y, CONTROLS_W, CARD_H)
    _draw_build(BUILD_X, CARD_Y, BUILD_W, CARD_H)
    mm.footer(FOOTER)


def draw():
    clear_canvas()
    if kit.is_mist():
        _draw_mist()
        update_canvas()
        return
    draw_frozen()
    kit.backdrop(0.9)
    import play_mode
    st = getattr(play_mode, 'stage', None)
    kit.heading(LEFT_X, H - 150, '일시정지', getattr(st, 'title', '') or None)
    for i, b in enumerate(MENU):
        b.draw(i == selected, left=True)
    _draw_controls(660, CARD_Y, 700, CARD_H)
    _draw_build(1390, CARD_Y, BUILD_W, CARD_H)
    kit.footer(FOOTER)
    update_canvas()
