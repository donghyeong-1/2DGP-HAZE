"""일시정지 창: 멈춘 게임 위에 메뉴(계속하기 · 설정 · 타이틀로)와 조작 안내를 띄운다.

Esc로 바로 돌아가고, O는 설정, H는 은신처로, Q는 타이틀. 판을 포기하는 두 항목은 두 번 눌러야 한다. 메뉴는 키보드(W/S, Enter)와 마우스로 고른다.
"""
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_h, SDLK_o, SDLK_q, clear_canvas, get_events, update_canvas)

import assets
import config
import game_framework
import game_world
import hud_kit as kit

W, H = config.SCREEN_W, config.SCREEN_H
LEFT_X = 150                       # 메뉴 줄 왼쪽 (11/22 메뉴 v2: 큰 판 없이 화면 전체를 덮는다)
MENU = [kit.Button(key, label, LEFT_X, H - 380 - i * 84, 420, 66)
        for i, (key, label) in enumerate((('resume', '계속하기'), ('options', '설정'),
                                          ('hideout', '판 포기하고 은신처로'), ('title', '판 포기하고 타이틀로')))]
CARD_H = 140 + 50 * 10            # 오른쪽 카드 두 장: 조작 / 이번 판 (조작 10줄 높이)
CARD_Y = H - 314 - CARD_H + 66


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
        (f'{k("swap")}  {k("weapon1")}  {k("weapon2")}', '무기 교체 (바꾸는 순간 교체기)'),
        (k('interact'), '진열대 아이템 줍기·구매'),
        (k('potion'), '물약 마시기 (체력 회복)'),
    ]


selected = 0
CONFIRM = ('hideout', 'title')                # 판을 포기하는 항목: 실수로 나가지 않게 두 번 누르게 한다
LABELS = {b.key: b.label for b in MENU}
GIVE_UP_ASK = '포기하려면 한 번 더 누르세요'
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
        _button(key).label = GIVE_UP_ASK           # 첫 입력은 묻기만 한다
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


def _key_tokens(keys):
    """'A  D', 'S + Space' -> 키 글자 판으로 그릴 조각들 ('+'는 글자 그대로)."""
    return [k for k in keys.replace('/', ' ').split() if k]


def _draw_controls(x, y, w, h):
    kit.card(x, y, w, h, '조작')
    for i, (keys, what) in enumerate(controls()):
        ry = y + h - 110 - i * 50
        kx = x + 28
        for tok in _key_tokens(keys):
            if tok == '+':
                kit.text(kx + 2, ry + 15, '+', kit.FAINT, small=True)
                kx += 22
                continue
            kx += kit.keycap(kx, ry, tok) + 6
        kit.text(x + 250, ry + 15, what, (205, 215, 235), small=True)


def _draw_build(x, y, w, h):
    """이번 판: 변이(계열 색)와 업그레이드."""
    import play_mode
    import items
    import mutations as mu
    p = play_mode.player
    kit.card(x, y, w, h, '이번 판')
    ty = y + h - 110
    muts = list(getattr(p, 'mutations', [])) if p is not None else []
    if not muts and not (p is not None and p.items):
        kit.text(x + 28, ty + 15, '아직 아이템이 없습니다', kit.FAINT, small=True)
        kit.text(x + 28, ty - 12, '진열대에서 얻을 수 있습니다', kit.FAINT, small=True)
        return
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
            kit.text(x + w - 28, ty + 20, f'{weapon} 미장착', kit.FAINT, small=True, right=True)
        ty -= 34
        for mid in mids:
            if ty < y + 40:
                break
            star = {'evo': '진화 ', 'duo': '합성 '}.get(mu.tier(mid), '')
            kit.text(x + 48, ty + 15, star + mu.MUTATIONS[mid]['name'],
                     ((255, 225, 140) if star else (235, 242, 252)) if on else kit.FAINT, small=True)
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
        kit.text(x + 84, ty + 15, items.ITEMS[item_id]['name'] + (f' x{n}' if n > 1 else ''), (205, 215, 235), small=True)
        ty -= 58


def draw():
    clear_canvas()
    draw_frozen()
    kit.backdrop(0.9)
    import play_mode
    st = getattr(play_mode, 'stage', None)
    kit.heading(LEFT_X, H - 150, '일시정지', getattr(st, 'title', '') or None)
    for i, b in enumerate(MENU):
        b.draw(i == selected, left=True)
    _draw_controls(660, CARD_Y, 700, CARD_H)
    _draw_build(1390, CARD_Y, 400, CARD_H)
    kit.footer([('Esc', '계속'), ('O', '설정'), ('H', '은신처로'), ('Q', '타이틀로'), ('W S', '선택'), ('Enter', '확인')])
    update_canvas()
