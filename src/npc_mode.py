"""은신처 NPC 창. 은신처에서 NPC 앞에 서서 F를 누르면 위에 쌓아 연다(push_mode). Esc나 '돌아가기'로 닫는다.

- 정비사: 기본 스탯 영구 강화 4종 (줄을 고르고 Enter, 헤이즈 결정을 낸다)
- 보관인: 보관 칸 열기 / 지금 맡긴 물건 (맡길 물건은 판이 끝날 때 사망·탈출 화면에서 고른다)
- 기록관: 짧은 이야기와 지금까지의 기록
판 양옆에 대화 초상화(Codex T32): 왼쪽 주인공, 오른쪽 NPC. 결과에 따라 표정이 바뀐다(faces).
키보드 W/S·위/아래로 줄, Enter·Space로 고르기. 마우스로 올리고 눌러도 된다. 그림 부품은 hud_kit(설정 창과 같은 판·버튼).
"""
from pico2d import SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_f, clear_canvas, get_events, update_canvas

import assets
import config
import game_framework
import hud_kit as kit
import items
import meta
import npc as npc_mod

W, H = config.SCREEN_W, config.SCREEN_H
PANEL_W, PANEL_H = 1100, 700
PANEL_X, PANEL_Y = (W - PANEL_W) // 2, (H - PANEL_H) // 2 - 20
ROW_H = 92

kind = 'mechanic'        # 들어가기 전에 play_mode가 정한다
selected = 0
note = ''                # 마지막으로 한 일 (산 것, 결정이 모자람 등)
result = None            # 마지막으로 한 일의 결과: 'ok', 'fail', None (초상화 표정)
PORTRAIT = 200           # 초상화 크기(px)
_under = None

STORY = {
    'archivist': ['"또 돌아왔군. 기록은 내가 남겨 둘 테니 걱정 마."',
                  '"헤이즈는 줄어도 죽고, 넘쳐도 터진다. 그 사이를 걸어."',
                  '"탑 꼭대기의 아크는 게이지를 위아래로 흔든다. 여유를 남겨 둬."'],
}


def enter():
    global selected, note, result, _under
    selected, note, result = 0, '', None
    meta.ensure_loaded()
    _under = game_framework.stack[-2] if len(game_framework.stack) >= 2 else None


def exit():
    pass


def pause():
    pass


def resume():
    pass


# ----- 줄 -----
def rows():
    """[(제목, 오른쪽 값, 설명, 동작 키 또는 None)]. 테스트에서도 쓴다."""
    if kind == 'mechanic':
        out = []
        for key in meta.ORDER:
            info, lv = meta.UPGRADES[key], meta.level(key)
            price = meta.price(key)
            value = f'{lv}/{info["max"]}  ' + ('최대' if price is None else f'{price} 결정')
            out.append((info['name'], value, info['desc'], key))
        return out
    if kind == 'keeper':
        if not meta.keeper_open():
            return [('보관 칸 열기', f'{config.META_KEEPER_PRICE} 결정',
                     '판이 끝날 때 들고 있던 것 하나를 맡기면 다음 판 시작 때 돌려준다', 'unlock')]
        keep = meta.state['keepsake']
        name = items.ITEMS[keep]['name'] if keep else '없음'
        return [('맡긴 물건', name, '다음 판 시작 때 받는다 (업그레이드는 1단계로, 무기는 그대로)', None),
                ('맡기는 법', '', '판이 끝나면 사망·탈출 화면에서 들고 있던 것 중 하나를 고른다', None)]
    s = meta.state
    return [(line, '', '', None) for line in STORY['archivist']] + [
        ('지금까지', f'{s["runs"]}판 · 탈출 {s["escapes"]}번', f'헤이즈 결정 {s["crystals"]}', None)]


def act(key):
    """줄을 골랐다. 한 일을 note에 적는다."""
    global note, result
    if key is None:
        return
    if key == 'unlock':
        ok = meta.unlock_keeper()
        note = '보관 칸을 열었다' if ok else '헤이즈 결정이 모자라다'
        result = 'ok' if ok else 'fail'
    elif key in meta.UPGRADES:
        name = meta.UPGRADES[key]['name']
        if meta.price(key) is None:
            note, result = f'{name}: 이미 최대 단계다', None
        elif meta.buy(key):
            note, result = f'{name} {meta.level(key)}단계 (다음 판부터)', 'ok'
        else:
            note, result = '헤이즈 결정이 모자라다', 'fail'
    assets.play_sound('pickup')


def faces():
    """(주인공 초상화, NPC 초상화) 이름. 샀으면 주인공은 결의·정비사는 씩 웃음, 모자라면 보관인은 걱정,
    기록관은 '지금까지' 기록 줄을 고르면 놀란다."""
    hero = 'n09_2' if result == 'ok' else 'n09_1'
    if kind == 'mechanic':
        mood = 2 if result == 'ok' else 1
    elif kind == 'keeper':
        mood = 2 if result == 'fail' else 1
    else:
        mood = 2 if selected == len(rows()) - 1 else 1
    return hero, f'{kind}_{mood}'


def portrait_spots():
    """초상화 왼쪽 아래 좌표: (주인공 - 판 왼쪽 바깥), (NPC - 판 오른쪽 바깥)."""
    y = PANEL_Y + 40
    return (PANEL_X - PORTRAIT - 12, y), (PANEL_X + PANEL_W + 12, y)


def _buttons():
    rs = rows()
    top = PANEL_Y + PANEL_H - 170
    out = [kit.Button(str(i), r[0], PANEL_X + 40, top - i * ROW_H - 40, PANEL_W - 80, ROW_H - 12) for i, r in enumerate(rs)]
    out.append(kit.Button('back', '돌아가기', (W - 360) // 2, PANEL_Y + 36, 360, 60))
    return out


def handle_events():
    global selected
    buttons = _buttons()
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN and event.key in (SDLK_ESCAPE, SDLK_f):
            game_framework.pop_mode()
            return
        selected, action = kit.menu_pick(buttons, selected, event, H)
        if action == 'click':
            if buttons[selected].key == 'back':
                game_framework.pop_mode()
                return
            act(rows()[selected][3])


def update():
    pass


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), 0.62)
    kit.panel('panel', PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    color = npc_mod.COLORS[kind]
    kit.text(PANEL_X + 50, PANEL_Y + PANEL_H - 70, f'{npc_mod.NAMES[kind]} · {npc_mod.ROLES[kind]}', color, big=True)
    kit.text(PANEL_X + PANEL_W - 50, PANEL_Y + PANEL_H - 66, f'헤이즈 결정 {meta.state["crystals"]}', (130, 235, 225),
             right=True)
    buttons = _buttons()
    for i, (title, value, desc, key) in enumerate(rows()):
        b = buttons[i]
        hot = i == selected
        kit.panel('plate' if hot else 'button', b.x, b.y, b.w, b.h)
        kit.text(b.x + 30, b.y + b.h - 30, title, (235, 240, 250) if hot or key else (175, 188, 210),
                 small=key is None and kind == 'archivist')
        if desc:
            kit.text(b.x + 30, b.y + 22, desc, (125, 140, 165), small=True)
        if value:
            ok = key is None or key == 'unlock' and meta.state['crystals'] >= config.META_KEEPER_PRICE or (
                key in meta.UPGRADES and meta.can_buy(key))
            kit.text(b.x + b.w - 30, b.y + b.h // 2, value, (255, 225, 140) if ok else (130, 140, 160), right=True)
    buttons[-1].draw(selected == len(buttons) - 1)
    for (x, y), name in zip(portrait_spots(), faces()):          # 대화 초상화 (1배)
        assets.draw_image(assets.image(f'portraits/{name}.png'), x + PORTRAIT // 2, y)
    if note:
        kit.text(W // 2, PANEL_Y + 120, note, (255, 240, 150), center=True)
    kit.text(W // 2, PANEL_Y - 26, 'W S 고르기   Enter 결정   Esc·F 닫기', (110, 125, 150), small=True, center=True)
    update_canvas()
