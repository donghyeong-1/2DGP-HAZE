"""은신처 NPC 창. 은신처에서 NPC 앞에 서서 F를 누르면 위에 쌓아 연다(push_mode). Esc나 '돌아가기'로 닫는다.

- 정비사: 기본 스탯 영구 강화 4종 (줄을 고르고 Enter, 헤이즈 결정을 낸다)
- 보관인: 보관 칸 열기 / 지금 맡긴 물건 (맡길 물건은 판이 끝날 때 사망·탈출 화면에서 고른다)
- 기록관: 짧은 이야기와 지금까지의 기록
- 무기 걸이(2026-11-23): 판을 시작할 두 번째 칸 무기. 고르면 지금 든 무기도 바로 바뀌고 다음 판에도 그대로다.
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
player = None            # 무기 걸이가 바로 무기를 바꿀 플레이어 (play_mode가 정한다)
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
                     '판이 끝날 때 물건 하나를 맡기면 다음 판 시작 때 돌려받습니다', 'unlock')]
        keep = meta.state['keepsake']
        name = items.ITEMS[keep]['name'] if keep else '없음'
        return [('맡긴 물건', name, '다음 판 시작 때 받습니다 (업그레이드는 1단계로, 무기는 그대로)', None),
                ('맡기는 법', '', '판이 끝나면 사망·탈출 화면에서 맡길 물건을 선택합니다', None)]
    if kind == 'armory':
        first, now = meta.state['start_first'], meta.state['start_weapon']   # v8 두 칸 자유: 첫 칸 넷 + 둘째 칸(비움 + 넷)
        out = []
        for wid in meta.ALL_WEAPONS:
            info = items.ITEMS['w_' + wid]
            out.append(('첫 칸 · ' + info['name'], '선택' if first == wid else '', info['desc'], 'f_' + wid))
        out.append(('둘째 칸 · 비움', '선택' if now is None else '', '둘째 칸을 비우고 시작합니다 (황금방에서 무기를 얻습니다)', 'w_none'))
        for wid in meta.ALL_WEAPONS:
            info = items.ITEMS['w_' + wid]
            desc = '첫 칸의 무기입니다 (첫 칸을 먼저 바꾸세요)' if wid == first else info['desc']
            out.append(('둘째 칸 · ' + info['name'], '선택' if now == wid else '', desc, 'w_' + wid))
        return out
    s = meta.state
    return [(line, '', '', None) for line in STORY['archivist']] + [
        ('지금까지', f'{s["runs"]}판 · 탈출 {s["escapes"]}번', f'헤이즈 결정 {s["crystals"]}', None)]


def act(key):
    """줄을 골랐다. 한 일을 note에 적는다."""
    global note, result
    if key is None:
        return
    if kind == 'armory' and key[:2] in ('w_', 'f_'):
        wid = None if key == 'w_none' else key[2:]
        ok = meta.set_start_first(wid) if key.startswith('f_') else meta.set_start_weapon(wid)
        if not ok:
            note, result = '두 칸에 같은 무기를 걸 수 없습니다', 'fail'
            return
        if player is not None:
            meta.equip_loadout(player)
        names = [items.ITEMS['w_' + w]['name'] for w in (meta.state['start_first'], meta.state['start_weapon']) if w]
        note, result = ' + '.join(names) + f'{_ro(names[-1])} 시작합니다', 'ok'
        return
    if key == 'unlock':
        ok = meta.unlock_keeper()
        note = '보관 칸을 열었습니다' if ok else '헤이즈 결정이 부족합니다'
        result = 'ok' if ok else 'fail'
    elif key in meta.UPGRADES:
        name = meta.UPGRADES[key]['name']
        if meta.price(key) is None:
            note, result = f'{name}: 이미 최대 단계입니다', None
        elif meta.buy(key):
            note, result = f'{name} {meta.level(key)}단계 (다음 판부터)', 'ok'
        else:
            note, result = '헤이즈 결정이 부족합니다', 'fail'
    assets.play_sound('pickup')


def _ro(word):
    """조사 '로/으로': 받침이 없거나 ㄹ 받침이면 '로'."""
    code = ord(word[-1]) - 0xAC00
    return '로' if not 0 <= code < 11172 or code % 28 in (0, 8) else '으로'


def faces():
    """(주인공 초상화, NPC 초상화) 이름. 샀으면 주인공은 결의·정비사는 씩 웃음, 모자라면 보관인은 걱정,
    기록관은 '지금까지' 기록 줄을 고르면 놀란다."""
    hero = 'n09_2' if result == 'ok' else 'n09_1'
    if kind == 'mechanic':
        mood = 2 if result == 'ok' else 1
    elif kind == 'keeper':
        mood = 2 if result == 'fail' else 1
    elif kind == 'armory':
        return hero, None                          # 무기 걸이는 사람이 아니다: 초상화 없음
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
    if kind == 'armory':                         # v8 두 칸 자유: 줄이 아홉이라 두 열로 (왼쪽 = 첫 칸 넷, 오른쪽 = 둘째 칸 다섯)
        cw, rh = (PANEL_W - 100) // 2, 80
        out = [kit.Button(str(i), r[0], PANEL_X + 40 + (0 if i < 4 else cw + 20), top - (i if i < 4 else i - 4) * rh - 28, cw, rh - 12)
               for i, r in enumerate(rs)]
    else:
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
    """NPC 창 (11/22 메뉴 v2): 덮개 + 큰 이름 제목 + 줄 카드, 양옆 대화 초상화, 결정 수는 오른쪽 위."""
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()
    kit.backdrop(0.9)
    color = npc_mod.COLORS[kind]
    kit.heading(PANEL_X, PANEL_Y + PANEL_H - 50, npc_mod.NAMES[kind], npc_mod.ROLES[kind], color=color)
    crystals = f'헤이즈 결정 {meta.state["crystals"]}'
    kit.text(PANEL_X + PANEL_W, PANEL_Y + PANEL_H - 50, crystals, (130, 235, 225), right=True)
    buttons = _buttons()
    for i, (title, value, desc, key) in enumerate(rows()):
        b = buttons[i]
        hot = i == selected
        kit.row(b.x, b.y, b.w, b.h, hot)
        if kind == 'armory':                                       # 두 열: 한 줄에 이름·무기 그림·고름만, 설명은 고른 줄 것만 아래에
            kit.text(b.x + 28, b.y + b.h // 2, title, (240, 248, 255) if hot else (190, 202, 225))
            if key != 'w_none':
                img = assets.image(f'ui/icon_w_{key[2:]}.png')     # 무기 그림 (1배)
                assets.draw_image(img, b.x + b.w - 116, b.y + (b.h - img.h) // 2)
            if hot and desc:
                kit.text(W // 2, PANEL_Y + 152, desc, (170, 185, 210), small=True, center=True)
        else:
            kit.text(b.x + 34, b.y + b.h - 30, title, (240, 248, 255) if hot or key else (190, 202, 225),
                     small=key is None and kind == 'archivist')
            if desc:
                kit.text(b.x + 34, b.y + 22, desc, (140, 155, 182) if hot else kit.FAINT, small=True)
        if value:
            ok = key is None or kind == 'armory' or key == 'unlock' and meta.state['crystals'] >= config.META_KEEPER_PRICE or (
                key in meta.UPGRADES and meta.can_buy(key))
            kit.text(b.x + b.w - (16 if kind == 'armory' else 30), b.y + b.h // 2, value, (255, 225, 140) if ok else (130, 140, 160), right=True)
    buttons[-1].draw(selected == len(buttons) - 1)
    for (x, y), name in zip(portrait_spots(), faces()):          # 대화 초상화 (1배)
        if name is None:
            continue
        assets.draw_image(assets.image(f'portraits/{name}.png'), x + PORTRAIT // 2, y)
    if note:
        kit.text(W // 2, PANEL_Y + 120, note, (255, 240, 150), center=True)
    kit.footer([('W S', '선택'), ('Enter', '확인'), ('Esc', '닫기')])
    update_canvas()
