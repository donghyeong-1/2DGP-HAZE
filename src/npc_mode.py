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
import keybinds
import config
import game_framework
import hud_kit as kit
import items
import meta
import npc as npc_mod
import talk

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
    'archivist': ['"이 교도소는 운석 구덩이 위에 세웠대. 그래서 안개가 안 걷혀."',   # 인사는 한마디(대사)가 맡는다
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
            desc = '첫 칸의 무기입니다 (첫 칸을 먼저 변경하세요)' if wid == first else info['desc']
            out.append(('둘째 칸 · ' + info['name'], '선택' if now == wid else '', desc, 'w_' + wid))
        return out
    s = meta.state
    return [(line, '', '', None) for line in STORY['archivist']] + [
        ('지금까지', f'{s["runs"]}판 · 탈출 {s["escapes"]}번', '', None)]   # U1: 결정 수는 창 오른쪽 위에 이미 있다


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
        note, result = '시작 무기 변경: ' + ' + '.join(names), 'ok'      # 말투 규칙: 이름 뒤에 조사를 붙이지 않는다
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


def speech():
    """NPC의 한마디 (v8 6일 차): 직전 판 결과에 따라 다르다 (data/dialogue.py, src/talk.py). 무기 걸이는 None."""
    meta.ensure_loaded()
    got = talk.speech(kind, meta.state)
    return got[0] if got else None


def _speech_mood():
    meta.ensure_loaded()
    got = talk.speech(kind, meta.state)
    return got[1] if got else 1


def faces():
    """(주인공 초상화, NPC 초상화) 이름. 샀으면 주인공은 결의·정비사는 씩 웃음, 모자라면 보관인은 걱정,
    기록관은 '지금까지' 기록 줄을 고르면 놀란다."""
    hero = 'n09_2' if result == 'ok' else 'n09_1'
    if kind == 'mechanic':
        mood = 2 if result == 'ok' else 1 if result else _speech_mood()      # 아직 아무것도 안 했으면 대사의 표정
    elif kind == 'keeper':
        mood = 2 if result == 'fail' else 1 if result else _speech_mood()
    elif kind == 'armory':
        return hero, None                          # 무기 걸이는 사람이 아니다: 초상화 없음
    else:
        mood = 2 if selected == len(rows()) - 1 else 1 if result else _speech_mood()
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
        if event.type == SDL_KEYDOWN and (event.key == SDLK_ESCAPE or keybinds.is_interact(event.key)):   # U1-2: 'F' 대신 상호작용 키
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


def available(key):
    """그 줄을 지금 고를 수 있는가 (살 수 있음·바꿀 수 있음). 동작이 없는 안내 줄은 True."""
    if key is None:
        return True
    if key == 'unlock':
        return meta.state['crystals'] >= config.META_KEEPER_PRICE
    if key in meta.UPGRADES:
        return meta.can_buy(key)
    if kind == 'armory' and key.startswith('w_') and key != 'w_none':
        return key[2:] != meta.state['start_first']          # 둘째 칸에 첫 칸과 같은 무기는 걸 수 없다
    return True


def draw():
    """NPC 창 (11/22 메뉴 v2): 덮개 + 큰 이름 제목 + 줄 카드, 양옆 대화 초상화, 결정 수는 오른쪽 위."""
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        kit.frozen_backdrop(_under.draw_frozen)            # mist: 은신처 NPC 이름표·안내 카드 없이 (R1)
    if kit.is_mist():
        _draw_mist()
        update_canvas()
        return
    kit.backdrop(0.9)
    color = npc_mod.COLORS[kind]
    kit.heading(PANEL_X, PANEL_Y + PANEL_H - 50, npc_mod.NAMES[kind], npc_mod.ROLES[kind], color=color)
    crystals = f'헤이즈 결정 {meta.state["crystals"]}'
    kit.text(PANEL_X + PANEL_W, PANEL_Y + PANEL_H - 50, crystals, (130, 235, 225), right=True)
    line = speech()
    if line:                                                     # 한마디 (v8 6일 차): 제목 오른쪽, 결정 수 아래
        kit.text(PANEL_X + PANEL_W, PANEL_Y + PANEL_H - 92, f'"{line}"', (235, 228, 205), right=True)   # 기록관 이야기 줄처럼 따옴표
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


# ----- 'mist' (11/27 S1): 증강 카드와 한 벌 (src/mist_pick.py) -----
def _draw_mist():
    """mist NPC 창: 목록 전체를 가는 테두리 판 하나에 담고(무기 걸이는 칸마다 하나씩, 둘), 고른 줄은 이름만 글자 폭으로 뒤집기 + 커서.
    살 수 없는 줄은 흐린 글자. 제목·결정 수·한마디·초상화·값·무기 그림과 줄·버튼의 자리(마우스로 누르는 자리)는 그대로."""
    import mist_pick as mp
    mp.backdrop()
    color = npc_mod.COLORS[kind] if kind != 'armory' else mp.TEXT  # R1: 사람 NPC 이름은 인물 색, 사람이 아닌 무기 걸이는 밝은 회백 (옅은 노랑 대신)
    kit.text(PANEL_X, PANEL_Y + PANEL_H - 50, npc_mod.NAMES[kind], color, big=True)
    kit.text(PANEL_X + 2, PANEL_Y + PANEL_H - 92, npc_mod.ROLES[kind], mp.FAINT, small=True)
    kit.text(PANEL_X + PANEL_W, PANEL_Y + PANEL_H - 50, f'헤이즈 결정 {meta.state["crystals"]}', mp.HAZE, right=True)
    line = speech()
    if line:
        kit.text(PANEL_X + PANEL_W, PANEL_Y + PANEL_H - 92, f'"{line}"', (235, 228, 205), right=True)
    buttons = _buttons()
    rs = rows()
    groups = [range(0, 4), range(4, len(rs))] if kind == 'armory' else [range(len(rs))]
    lo = min(buttons[i].y for i in range(len(rs)))               # 목록 판 하나 (무기 걸이는 두 열을 함께, 가운데 세로 선으로 나눈다)
    hi = buttons[0].y + buttons[0].h
    left, right = buttons[0].x, max(buttons[i].x + buttons[i].w for i in range(len(rs)))
    pad_y = 8 if kind == 'armory' else mp.PAD_Y                 # 무기 걸이: 판 바로 아래에 고른 줄 설명이 온다
    mp.panel(left - mp.PAD, lo - pad_y, right - left + 2 * mp.PAD, hi - lo + 2 * pad_y)
    if kind == 'armory':
        gap = buttons[4].x - (buttons[0].x + buttons[0].w)
        mp.vsep(buttons[0].x + buttons[0].w + gap // 2 - 1, lo + 8, hi - lo - 16)
    for g in groups:
        for i in g[:-1]:                                         # 줄 사이 옅은 선 (다음 줄과의 틈 가운데)
            b = buttons[i]
            mp.sep(b.x + 16, b.y - (b.y - buttons[i + 1].y - buttons[i + 1].h) // 2 - 1, b.w - 32)
    for i, (title, value, desc, key) in enumerate(rs):
        b = buttons[i]
        hot = i == selected
        ok = available(key)
        if kind == 'armory':                                     # 두 열: 이름·무기 그림·지금 건 무기 표시, 설명은 고른 줄 것만 아래에
            mp.pick(b.x + 28, b.y + b.h // 2, title, hot, mp.TEXT if ok else mp.OFF, ok=ok)
            if key != 'w_none':
                img = assets.image(f'ui/icon_w_{key[2:]}.png')
                assets.draw_image(img, b.x + b.w - 116, b.y + (b.h - img.h) // 2)
            if hot and desc:
                kit.text(W // 2, PANEL_Y + 152, desc, mp.SOFT if ok else mp.OFF, small=True, center=True)
            if value:
                vx = b.x + b.w - 16 - assets.text_width(value) // 2
                kit.text(vx, b.y + b.h // 2, value, mp.TEXT, center=True)
                mp.underline(vx, b.y + b.h // 2 - 18, value)
            continue
        story = key is None and kind == 'archivist'
        # 이름은 철판보다 4px 올리고 설명은 2px 내린다: 뒤집힌 이름 블록(글자 위아래 18px)과 설명 글자가 붙지 않게
        mp.pick(b.x + 34, b.y + b.h - 26, title, hot, (mp.BODY if story else mp.TEXT) if ok else mp.OFF, small=story, ok=ok)
        if desc:
            kit.text(b.x + 34, b.y + 20, desc, mp.OFF if not ok else mp.BODY if hot else mp.SOFT, small=True)
        if value:
            vx, vy = b.x + b.w - 30, b.y + b.h // 2
            if key in meta.UPGRADES:                             # 정비사: 단계(회색)와 값(결정 = 헤이즈 = 청록)을 나눠서. 문구는 그대로 한 줄
                step, _sp, cost = value.partition('  ')
                kit.text(vx, vy, cost, (mp.HAZE if ok else mp.OFF) if meta.price(key) is not None else mp.SOFT, right=True)
                kit.text(vx - assets.text_width(cost) - assets.text_width('  '), vy, step, mp.SOFT if ok else mp.OFF, right=True)
            else:
                kit.text(vx, vy, value, (mp.HAZE if ok else mp.OFF) if key == 'unlock' else mp.TEXT, right=True)
    back = buttons[-1]
    import mist_menu as mm                                      # R1: '돌아가기' 뒤 어둠 한 겹 더 (은신처 무기 걸이 그림이 비쳐 겹쳤다)
    mm.text_shade(back.x + back.w // 2, back.y + back.h // 2, back.label, center=True, pad=24, kind='wide')
    mp.pick(back.x + back.w // 2, back.y + back.h // 2, back.label, selected == len(buttons) - 1, mp.SOFT, center=True)
    for (x, y), name in zip(portrait_spots(), faces()):
        if name is None:
            continue
        assets.draw_image(assets.image(f'portraits/{name}.png'), x + PORTRAIT // 2, y)
    if note:
        kit.text(W // 2, PANEL_Y + 120, note, mp.FAIL if result == 'fail' else mp.TEXT if result == 'ok' else mp.SOFT, center=True)
    mp.keys([('W S', '선택'), ('Enter', '확인'), ('Esc', '닫기')])
