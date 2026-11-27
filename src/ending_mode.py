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
import mist_menu as mm
import talk

result = 'dead'  # 'clear' 또는 'dead'. 모드로 들어가기 전에 play_mode가 정한다.
_ignore_input = 0.0  # 사망 직후 누르고 있던 키로 바로 넘어가지 않게 잠시 입력을 막는다
reward = 0           # 이번 판에 받은 헤이즈 결정
choices = []         # 맡길 수 있는 것 (아이템 id), 맨 끝 None = 맡기지 않기
choice = 0
choosing = False     # 지금 맡길 것을 고르는 중인가
kept = None          # 맡긴 것 (보여 주기용)
summary = []         # 판 기록 [(이름, 값)]
ending_line = ''     # 탈출 뒤 한 줄 (v8 6일 차, data/dialogue.py ENDING)
easy_hint = ''       # 구역 1에서 연달아 쓰러졌을 때의 초보자 모드 안내 (talk.easy_hint)
SUM_W, SUM_ROW = 760, 54
SUM_BASE = 504       # 판 기록 카드의 아랫변이 이 높이일 때를 기준으로 아래 글자들을 놓았다 (줄이 많아 더 내려오면 그만큼 함께 내린다)


def run_summary(player, zone_title, reward):
    """판 기록 줄 [(이름, 값)]. 시간은 분:초."""
    secs = int(getattr(player, 'run_clock', 0.0))
    return [('도달한 구역', zone_title or '-'), ('걸린 시간', f'{secs // 60}:{secs % 60:02d}'),
            ('클리어한 방', str(player.run_rooms)), ('처치한 적', str(getattr(player, 'run_kills', 0))),
            ('처치한 보스', str(player.run_ends)), ('받은 헤이즈 결정', f'+{reward}')] + (
        [('사망 원인', player.death_cause)] if getattr(player, 'death_cause', '') else [])


def enter():
    global _ignore_input, reward, choices, choice, choosing, kept, summary, ending_line, easy_hint
    import play_mode
    _ignore_input = 0.6
    import transition
    transition.reveal(0.6)                         # 쓰러진 뒤·탈출 뒤 천천히 드러난다
    assets.play_music('title')   # 사망·탈출 화면은 차분한 곡으로 돌아간다
    p = play_mode.player
    st = getattr(play_mode, 'stage', None)
    zone = getattr(st, 'name', None)                                     # 직전 판 기록 (NPC 대사): 어디서, 아크를 눕힌 뒤였나
    ark_down = getattr(getattr(st, 'boss', None), 'kind', '') == 'heart'
    reward = meta.finish_run(p, escaped=result == 'clear', zone=zone, ark_down=ark_down) if p is not None else 0
    ending_line = talk.ending_line(meta.state.get('escapes', 0)) if result == 'clear' else ''
    import options
    easy_hint = talk.easy_hint(meta.state.get('last'), options.easy_mode) if result != 'clear' else ''
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
    return items.icon_path(item_id)


FULL_ROWS = ('도달한 구역', '사망 원인')      # 글이 길어 한 줄을 다 쓰는 항목


def _draw_summary(cx):
    """판 기록 판: 도달한 구역·쓰러진 원인은 한 줄씩(넓게), 나머지는 두 칸씩, 맨 아래 보유 결정."""
    if not summary:
        return SUM_BASE
    wide = [e for e in summary if e[0] in FULL_ROWS]
    rest = [e for e in summary if e[0] not in FULL_ROWS]
    rows = len(wide) + (len(rest) + 1) // 2
    h = 70 + rows * SUM_ROW
    x, y = cx - SUM_W // 2, 790 - h
    kit.card(x, y, SUM_W, h)                       # 메뉴 v2 카드 (11/22)
    top = y + h - 40
    for i, (name, value) in enumerate(wide):
        ty = top - i * SUM_ROW
        kit.text(x + 34, ty, name, (130, 145, 175), small=True)
        kit.text(x + SUM_W - 34, ty, value, (255, 150, 140) if name == '사망 원인' else (235, 242, 252), right=True)
    half = SUM_W // 2
    for i, (name, value) in enumerate(rest):
        col, row = i % 2, i // 2 + len(wide)
        ty = top - row * SUM_ROW
        lx = x + 34 + col * half
        kit.text(lx, ty, name, (130, 145, 175), small=True)
        kit.text(lx + half - 60, ty, value, (255, 225, 140) if '결정' in name else (235, 242, 252), right=True)
    kit.text(cx, y + 24, f'보유 헤이즈 결정 {meta.state.get("crystals", 0)}', (130, 235, 225), small=True, center=True)
    return y


# ----- 'mist' (11/27 M1): 타이틀 감시 단말과 한 벌. 일러스트(screen_death·screen_ending)는 그대로 -----
CHOOSE_FOOTER = [('A D', '선택'), ('Enter', '맡기기')]
# 맡길 물건 묶음의 자리 (아래가 0, 판 기록이 길면 dy만큼 함께 내려간다). R1(11/27): 고른 물건 이름(뒤집힌 블록·커서)이 칸 아래에서
# 일러스트의 쓰러진 주인공 머리에 닿았다 -> 이름을 안내 줄과 칸 사이로 올리고 칸 간격을 96 -> 88로 좁혀 첫 칸을 머리에서 떼었다.
# 이 화면은 키(A D·Enter)로만 고른다: 마우스로 누르는 자리가 따로 없다
CHOOSE_PROMPT_Y, CHOOSE_NAME_Y, CHOOSE_SLOT_Y, CHOOSE_GAP = 480, 428, 318, 88
MIST_HEAD = {'dead': [('TOWER SURVEILLANCE // SIGNAL LOST', mm.PH), ('INMATE N-09 · 사망 기록', mm.PH_DIM)],
             'clear': [('TOWER SURVEILLANCE // INMATE ESCAPED', mm.PH), ('INMATE N-09 · 탈출 기록', mm.PH_DIM)]}


def _summary_box():
    """판 기록 자리 (x, y, h): 카드와 같은 자리·크기 (_draw_summary)."""
    wide = [e for e in summary if e[0] in FULL_ROWS]
    rest = [e for e in summary if e[0] not in FULL_ROWS]
    h = 70 + (len(wide) + (len(rest) + 1) // 2) * SUM_ROW
    return config.SCREEN_W // 2 - SUM_W // 2, 790 - h, h


def _draw_summary_mist(cx):
    """판 기록 (mist): 카드 없이 같은 자리에 글자 (뒤 어둠은 draw_mist가 먼저 깐다). 이름은 작은 흐린 글자, 값은 본문,
    사망 원인 빨강·받은 결정 금·보유 결정 청록은 그대로. 위아래에 가는 선 한 줄씩."""
    if not summary:
        return SUM_BASE
    x, y, h = _summary_box()
    wide = [e for e in summary if e[0] in FULL_ROWS]
    rest = [e for e in summary if e[0] not in FULL_ROWS]
    mm.rule(x + 24, y + h - 4, SUM_W - 48)
    mm.rule(x + 24, y + 2, SUM_W - 48)
    top = y + h - 40
    for i, (name, value) in enumerate(wide):
        ty = top - i * SUM_ROW
        kit.text(x + 34, ty, name, mm.PH_SOFT, small=True)
        kit.text(x + SUM_W - 34, ty, value, (255, 150, 140) if name == '사망 원인' else mm.PH_TEXT, right=True)
    half = SUM_W // 2
    for i, (name, value) in enumerate(rest):
        col, row = i % 2, i // 2 + len(wide)
        ty = top - row * SUM_ROW
        lx = x + 34 + col * half
        kit.text(lx, ty, name, mm.PH_SOFT, small=True)
        kit.text(lx + half - 60, ty, value, (255, 225, 140) if '결정' in name else mm.PH_TEXT, right=True)
    kit.text(cx, y + 24, f'보유 헤이즈 결정 {meta.state.get("crystals", 0)}', (130, 235, 225), small=True, center=True)
    return y


def draw_mist():
    """'mist' 결과 화면: 일러스트 위에 글자 뒤 어둠, 주사선, 네 귀퉁이 꺾쇠, 감시 머리글. 판 기록은 카드 없이 글자,
    맡길 물건 칸은 가는 테두리(고른 칸은 밝은 인광 테두리), 고른 물건 이름은 글자 폭으로 색 뒤집기 + 커서.
    자리·문구·키 조작은 그대로."""
    cx = config.SCREEN_W // 2
    nxt = '크레딧' if result == 'clear' else '은신처로'
    clear = result == 'clear'
    assets.draw_image(assets.image('backgrounds/screen_ending.png' if clear else 'backgrounds/screen_death.png'), cx, 0)
    title, sub = ('탈출 성공', '안개를 뚫고 교도소를 벗어났습니다') if clear else (
        '사망', '이번 판은 여기까지입니다. 영구 강화는 그대로 남습니다')
    # 글자 뒤 어둠: 제목 두 줄, 판 기록, 아래 글자들 (자리를 먼저 계산해 글자보다 먼저 깐다)
    mm.text_shade(cx, 880, title, big=True, center=True, pad=16, kind='wide')
    mm.text_shade(cx, 830, sub, center=True, pad=8)
    dy = 0
    if summary:
        x, y, h = _summary_box()
        mm.shade(x + 10, y + 4, x + SUM_W - 10, y + h - 6)
        dy = min(0, y - SUM_BASE)
    if choosing:
        prompt = '보관인에게 맡길 물건을 선택하세요 (다음 판 시작 때 돌려받습니다)'
        mm.text_shade(cx, 480 + dy, prompt, center=True, pad=8)
        n = len(choices)
        half = (n - 1) * CHOOSE_GAP // 2 + 36
        mm.shade(cx - half, CHOOSE_SLOT_Y - 24 + dy, cx + half, CHOOSE_NAME_Y + 18 + dy)
        mm.footer_shade(CHOOSE_FOOTER, y=256 + dy)
        if easy_hint:
            mm.text_shade(cx, 206 + dy, easy_hint, small=True, center=True, pad=8)
    else:
        lines = []
        if kept:
            lines.append((470 + dy, f'맡긴 물건: {items.ITEMS[kept]["name"]}'))
        if ending_line or easy_hint:
            lines.append(((425 if kept else 450) + dy, ending_line or easy_hint))
        for ty, s in lines:
            mm.text_shade(cx, ty, s, center=True, pad=8)
        mm.footer_shade([('아무 키', nxt)], y=380 + dy)
    mm.terminal(MIST_HEAD['clear' if clear else 'dead'])
    mm.title(cx, 880, title, mm.PH if clear else (225, 90, 100), center=True)
    kit.text(cx, 830, sub, mm.PH_TEXT, center=True)
    dy = min(0, _draw_summary_mist(cx) - SUM_BASE)
    if choosing:
        kit.text(cx, 480 + dy, '보관인에게 맡길 물건을 선택하세요 (다음 판 시작 때 돌려받습니다)', mm.PH_TEXT, center=True)
        n = len(choices)
        gap = CHOOSE_GAP
        x0 = cx - (n - 1) * gap // 2
        sy = CHOOSE_SLOT_Y + dy
        for i, item_id in enumerate(choices):
            x = x0 + i * gap
            hot = i == choice
            mm.frame(x - 36, sy, 72, 72, 'ph' if hot else 'ph_dim')
            if hot:                                   # 고른 칸: 밝은 테두리 + 아래 가는 밑줄 (설정의 고른 값과 같은 표시)
                assets.draw_rect_color(x - 36, sy - 10, 72, 2, mm.PH)
            if item_id is None:
                kit.text(x, sy + 36, '없음', mm.PH if hot else mm.PH_SOFT, small=True, center=True)
            else:
                assets.draw_image(assets.image(_icon_of(item_id)), x, sy + 12)
        sel = choices[choice]
        name = '맡기지 않기' if sel is None else items.ITEMS[sel]['name'] + (
            ' (1단계로)' if sel in items.UPGRADES else '')
        mm.pick(cx, CHOOSE_NAME_Y + dy, name, True)           # 고른 물건 이름: 글자 폭으로 색 뒤집기 + 커서 (칸 위, R1)
        mm.footer(CHOOSE_FOOTER, y=256 + dy)
        if easy_hint:
            kit.text(cx, 206 + dy, easy_hint, (255, 225, 140), center=True, small=True)
    else:
        if kept:
            kit.text(cx, 470 + dy, f'맡긴 물건: {items.ITEMS[kept]["name"]}', (255, 225, 140), center=True)
        if ending_line:
            kit.text(cx, (425 if kept else 450) + dy, ending_line, mm.PH_TEXT, center=True)
        if easy_hint:
            kit.text(cx, (425 if kept else 450) + dy, easy_hint, (255, 225, 140), center=True)
        mm.footer([('아무 키', nxt)], y=380 + dy)


def draw():
    clear_canvas()
    if kit.is_mist():
        draw_mist()
        import transition
        transition.draw()
        update_canvas()
        return
    cx = config.SCREEN_W // 2
    nxt = '크레딧' if result == 'clear' else '은신처로'
    if result == 'clear':
        assets.draw_image(assets.image('backgrounds/screen_ending.png'), cx, 0)
        assets.draw_text(cx, 880, '탈출 성공', (170, 230, 250), center=True, big=True)
        assets.draw_text(cx, 830, '안개를 뚫고 교도소를 벗어났습니다', (170, 185, 210), center=True)
    else:                                                          # 사망 화면: 쓰러진 인물 위쪽에 글자를 둔다
        assets.draw_image(assets.image('backgrounds/screen_death.png'), cx, 0)
        assets.draw_text(cx, 880, '사망', (225, 90, 100), center=True, big=True)
        assets.draw_text(cx, 830, '이번 판은 여기까지입니다. 영구 강화는 그대로 남습니다', (170, 185, 210), center=True)
    dy = min(0, _draw_summary(cx) - SUM_BASE)                      # 카드가 길어지면 아래 글자를 그만큼 내린다 (사망 화면은 '사망 원인' 줄이 하나 더 있다)
    if choosing:                                                   # 보관인에게 맡길 것 고르기
        assets.draw_text(cx, 480 + dy, '보관인에게 맡길 물건을 선택하세요 (다음 판 시작 때 돌려받습니다)', (200, 210, 230), center=True)
        n = len(choices)
        gap = 96
        x0 = cx - (n - 1) * gap // 2
        for i, item_id in enumerate(choices):
            x = x0 + i * gap
            hot = i == choice
            assets.draw_rect_color(x - 36, 370 + dy, 72, 72, kit.ACCENT if hot else kit.EDGE)
            assets.draw_rect_color(x - 33, 373 + dy, 66, 66, kit.ROW_HOT if hot else kit.ROW_BG)
            if item_id is None:
                assets.draw_text(x, 406 + dy, '없음', (200, 210, 230), small=True, center=True)
            else:
                assets.draw_image(assets.image(_icon_of(item_id)), x, 382 + dy)
        sel = choices[choice]
        name = '맡기지 않기' if sel is None else items.ITEMS[sel]['name'] + (
            ' (1단계로)' if sel in items.UPGRADES else '')
        assets.draw_text(cx, 330 + dy, name, (255, 225, 140), center=True)
        kit.footer([('A D', '선택'), ('Enter', '맡기기')], y=256 + dy)
        if easy_hint:                                              # 초보자 모드 안내 (맡길 물건 고르기 아래)
            kit.text(cx, 206 + dy, easy_hint, (255, 225, 140), center=True, small=True)
    else:
        if kept:
            assets.draw_text(cx, 470 + dy, f'맡긴 물건: {items.ITEMS[kept]["name"]}', (255, 225, 140), center=True)
        if ending_line:                                            # 탈출 뒤 한 줄 (판 기록 아래, 안내 위. 맡긴 물건이 있으면 그 아래)
            kit.text(cx, (425 if kept else 450) + dy, ending_line, (215, 228, 240), center=True)
        if easy_hint:                                              # 초보자 모드 안내 (탈출 뒤 한 줄과 같은 자리: 사망 화면에만 나온다)
            kit.text(cx, (425 if kept else 450) + dy, easy_hint, (255, 225, 140), center=True)
        kit.footer([('아무 키', nxt)], y=380 + dy)
    import transition
    transition.draw()                              # 화면 전환 점묘 (계획 4-3, 가장 위)
    update_canvas()
