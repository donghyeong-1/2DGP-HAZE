"""효과음 듣는 방 (v8 계획 4-6, 2026-11-25). 연습 메뉴의 '효과음 듣기'에서 연다.

효과음을 종류별로 하나씩 들어 보고 '좋음'·'바꿔'를 표시한다. 표시는 저장소 폴더의 sfx_review.json에 남는다.
Claude는 소리를 들을 수 없다: 사용자가 '바꿔'로 표시한 것만 다시 만든다.

A/D 종류, W/S 소리, Enter·Space 듣기, G 좋음, B 바꿔, X 표시 지우기, Esc·F 닫기.
S2-2 (11/27): 효과음 v3(config.SFX_SET). V로 듣는 묶음을 새 것 <-> 예전 것(v2)으로 바꿔 같은 소리를 번갈아 들어 본다.
표시는 게임이 쓰는 묶음(config.SFX_SET)의 것으로 남는다: v2는 'marks', 그 밖은 'marks_<묶음>'.
"""
import json
import os

from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_DOWN, SDLK_ESCAPE, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE,
                    SDLK_UP, SDLK_a, SDLK_b, SDLK_d, SDLK_f, SDLK_g, SDLK_s, SDLK_v, SDLK_w, SDLK_x, clear_canvas, get_events,
                    update_canvas)

import assets
import config
import game_framework
import keybinds
import hud_kit as kit

W, H = config.SCREEN_W, config.SCREEN_H
PANEL_X, PANEL_W = 460, 1000
ROW_H, ROW_STEP = 52, 60
TOP_Y = H - 290
VISIBLE = 10
PATH = os.path.join(os.path.dirname(assets.ASSET_DIR), 'sfx_review.json')     # 저장소 폴더 (Claude가 읽는다)
# 파일 이름의 첫 낱말 -> 종류 이름. 없는 것은 '그 밖'
GROUPS = [('swing', '휘두르기'), ('impact', '타격'), ('hit', '맞는 소리'), ('shot', '총'), ('throw', '던지기'), ('chain', '사슬'),
          ('ult', '궁극기'), ('enhance', '강화'), ('overload', '오버로드'), ('kill', '연속 처치'), ('absorb', '흡수'),
          ('dash', '대시'), ('jump', '점프'), ('land', '착지'), ('windup', '적 예고'), ('ark', '아크'), ('amb', '환경'),
          ('warn', '경고'), ('ui', '메뉴'), ('potion', '물약'), ('step', '발소리')]
OTHER = '기타'
MARKS = {'good': ('좋음', (150, 240, 170)), 'bad': ('다시 만들기', (255, 130, 130))}
cat = 0
row = 0
marks = {}
_catalog = None
_under = None
listen = None                  # 지금 듣는 묶음 (None이면 게임이 쓰는 묶음 config.SFX_SET). V로 예전 'v2'와 번갈아


def catalog():
    """[(종류 이름, [소리 이름...])]: assets/sfx의 wav를 파일 이름 첫 낱말로 묶는다. 빈 종류는 뺀다."""
    global _catalog
    if _catalog is None:
        names = assets.sfx_names()                         # S2-2: 예전 묶음 + 새 묶음의 이름
        labels = dict(GROUPS)
        buckets = {label: [] for _, label in GROUPS}
        buckets[OTHER] = []
        for n in names:
            buckets[labels.get(n.split('_')[0], OTHER)].append(n)
        _catalog = [(label, buckets[label]) for label in [g[1] for g in GROUPS] + [OTHER] if buckets[label]]
    return _catalog


def mark_key(prefix='marks'):
    """표시를 적는 칸 이름: 게임이 쓰는 묶음이 v2면 'marks'(예전 그대로), 그 밖은 'marks_v3'처럼."""
    return prefix if config.SFX_SET == 'v2' else f'{prefix}_{config.SFX_SET}'


def _read():
    try:
        with open(PATH, encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load():
    global marks
    data = _read()
    got = data.get(mark_key(), {})
    marks = {k: v for k, v in got.items() if v in MARKS} if isinstance(got, dict) else {}
    return marks


def save():
    """표시를 저장한다. '바꿔'인 것은 종류별 목록으로도 적어 둔다(읽기 쉽게). 다른 묶음의 표시는 그대로 둔다."""
    redo = {}
    for label, names in catalog():
        bad = [n for n in names if marks.get(n) == 'bad']
        if bad:
            redo[label] = bad
    data = _read()
    data[mark_key()] = marks
    data[mark_key('redo')] = redo
    tmp = PATH + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, PATH)
    except OSError as e:                                   # 쓸 수 없는 폴더(실행 파일 등): 표시는 이번 실행 동안만, 게임은 계속
        import log
        log.error(f'효과음 표시를 저장하지 못했다: {PATH}', e)
        return False
    return True


def mark(name, value):
    """value: 'good' / 'bad' / None(지우기). 저장까지 한다."""
    if value is None:
        marks.pop(name, None)
    elif value in MARKS:
        marks[name] = value
    save()


def current():
    names = catalog()[cat][1]
    return names[min(row, len(names) - 1)]


def listening():
    """지금 듣는 묶음: V를 누르지 않았으면 게임이 쓰는 묶음."""
    return listen or config.SFX_SET


LISTEN_SETS = ('v3', 'v3s2', 'v2')
LISTEN_NAMES = {'v3': '새 소리', 'v3s2': 'S2 소리', 'v2': '예전 소리'}


def listen_order(name):
    """V로 돌아가며 들을 묶음 (S3): 게임이 쓰는 묶음부터, 그 소리의 파일이 앞 묶음과 다른 것만. 예: 메뉴 소리는 새 -> S2판 -> 예전."""
    order, seen = [], set()
    for s in (config.SFX_SET,) + tuple(x for x in LISTEN_SETS if x != config.SFX_SET):
        p = assets.sfx_path(name, s)
        if p and p not in seen:
            seen.add(p)
            order.append(s)
    return order or [config.SFX_SET]


def toggle_listen(name=None):
    """V: 지금 소리의 다른 판으로 (새 -> S2판 -> 예전 -> 새). 게임이 v2를 쓰면 바꿀 것이 없다."""
    global listen
    order = listen_order(name or current())
    now = listening()
    i = order.index(now) if now in order else -1
    nxt = order[(i + 1) % len(order)]
    listen = None if nxt == config.SFX_SET else nxt
    return listening()


def play(name):
    """그 파일 그대로 들려준다 (게임 중의 변형 고르기 없이). 크기는 설정의 효과음 크기 x 게임에서와 같은 소리별 균형
    (S2-2: 예전과 새 것을 같은 조건으로 비교하려고. 예전 묶음은 파일마다 SFX_GAIN, 새 묶음은 SFX_V3_LEVEL)."""
    s = listening()
    wav = assets.sound(name, s)
    if wav is not None:
        import options
        wav.set_volume(options.volume(config.SFX_VOLUME * assets.sfx_gain(name, s), options.sfx_level))
        wav.play()


def listen_label():
    """화면 한 줄: 지금 듣는 묶음 (게임이 v2만 쓰면 빈 글)."""
    if config.SFX_SET == 'v2':
        return ''
    return '지금 듣는 소리: ' + LISTEN_NAMES.get(listening(), listening())



def enter():
    global cat, row, _under, listen
    cat = row = 0
    listen = None
    load()
    _under = game_framework.stack[-2] if len(game_framework.stack) >= 2 else None


def exit():
    pass


def pause():
    pass


def resume():
    pass


def handle_events():
    global cat, row
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type != SDL_KEYDOWN:
            continue
        k = event.key
        n = len(catalog()[cat][1])
        if k == SDLK_ESCAPE or keybinds.is_interact(k):       # U1-2: 'F' 대신 상호작용 키
            game_framework.pop_mode()
            return
        if k in (SDLK_w, SDLK_UP):
            row = (row - 1) % n
            play(current())
        elif k in (SDLK_s, SDLK_DOWN):
            row = (row + 1) % n
            play(current())
        elif k in (SDLK_a, SDLK_LEFT):
            cat, row = (cat - 1) % len(catalog()), 0
        elif k in (SDLK_d, SDLK_RIGHT):
            cat, row = (cat + 1) % len(catalog()), 0
        elif k in (SDLK_RETURN, SDLK_SPACE):
            play(current())
        elif k == SDLK_g:
            mark(current(), 'good')
        elif k == SDLK_b:
            mark(current(), 'bad')
        elif k == SDLK_x:
            mark(current(), None)
        elif k == SDLK_v:
            toggle_listen()
            play(current())


def update():
    pass


FOOTER = [('A D', '종류'), ('W S', '선택'), ('Enter', '듣기'), ('V', '예전과 비교'), ('G', '좋음'), ('B', '다시 만들기'),
          ('X', '표시 지우기'), ('Esc', '닫기')]


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        kit.frozen_backdrop(_under.draw_frozen)
    if kit.is_mist():
        frozen = getattr(_under, '_under', None)                 # 연습 메뉴 아래의 멈춘 연습장 (연습 메뉴에는 draw_frozen이 없다)
        if not (_under is not None and hasattr(_under, 'draw_frozen')) and frozen is not None and hasattr(frozen, 'draw_frozen'):
            kit.frozen_backdrop(frozen.draw_frozen)              # R1: '초당 피해'·안내 카드·이름표 없이
        _draw_mist()
        update_canvas()
        return
    kit.backdrop(0.92)
    groups = catalog()
    total = sum(len(names) for _, names in groups)
    done = sum(1 for names in (g[1] for g in groups) for n in names if n in marks)
    bad = sum(1 for v in marks.values() if v == 'bad')
    kit.heading(PANEL_X, H - 150, '효과음 듣기', f'표시 {done}/{total} · 다시 만들기 {bad}')
    label, names = groups[cat]
    kit.text(PANEL_X + PANEL_W // 2, H - 220, f'<  {label}  ({cat + 1}/{len(groups)})  >', (255, 230, 150), center=True)
    first = max(0, min(row - VISIBLE // 2, len(names) - VISIBLE))
    for j, name in enumerate(names[first:first + VISIBLE]):
        i = first + j
        cy = TOP_Y - j * ROW_STEP
        on = i == row
        kit.row(PANEL_X, cy - ROW_H // 2, PANEL_W, ROW_H, on)
        kit.text(PANEL_X + 34, cy, name, (240, 248, 255) if on else (190, 202, 225), small=True)
        m = marks.get(name)
        if m:
            text, color = MARKS[m]
            kit.text(PANEL_X + PANEL_W - 34, cy, text, color, small=True, right=True)
    if len(names) > VISIBLE:
        kit.text(PANEL_X + PANEL_W - 10, TOP_Y - VISIBLE * ROW_STEP + 14, f'{row + 1}/{len(names)}', kit.FAINT, small=True, right=True)
    if listen_label():
        kit.text(PANEL_X + PANEL_W, H - 150, listen_label(), (255, 230, 150), small=True, right=True)
    kit.footer(FOOTER)
    update_canvas()


def _draw_mist():
    """'mist' (11/27 S1): M1 메뉴 화면과 같은 감시 단말 모양. 판·줄 띠·키캡 없이 글자, 고른 소리는 이름만 글자 폭으로 뒤집기 + 커서.
    표시(좋음·바꿔)의 글자와 색, 줄의 자리는 그대로."""
    import mist_menu as mm
    groups = catalog()
    total = sum(len(names) for _, names in groups)
    done = sum(1 for names in (g[1] for g in groups) for n in names if n in marks)
    bad = sum(1 for v in marks.values() if v == 'bad')
    label, names = groups[cat]
    first = max(0, min(row - VISIBLE // 2, len(names) - VISIBLE))
    shown = names[first:first + VISIBLE]
    mm.dim(mm.DIM_GAME)
    mm.shade(PANEL_X - 10, H - 150 - 66, PANEL_X + 420, H - 150 + 24)
    mm.text_shade(PANEL_X + PANEL_W // 2, H - 220, f'<  {label}  ({cat + 1}/{len(groups)})  >', center=True)
    mm.shade(PANEL_X, TOP_Y - (len(shown) - 1) * ROW_STEP - 28, PANEL_X + PANEL_W, TOP_Y + 28)
    mm.footer_shade(FOOTER)
    mm.terminal([('TOWER SURVEILLANCE // AUDIO CHECK', mm.PH)])
    mm.title(PANEL_X, H - 150, '효과음 듣기')
    kit.text(PANEL_X + 2, H - 192, f'표시 {done}/{total} · 다시 만들기 {bad}', mm.PH_SOFT, small=True)
    if listen_label():
        kit.text(PANEL_X + PANEL_W, H - 192, listen_label(), mm.PH if listening() != 'v2' else mm.PH_SOFT, small=True, right=True)
    kit.text(PANEL_X + PANEL_W // 2, H - 220, f'<  {label}  ({cat + 1}/{len(groups)})  >', mm.PH, center=True)
    for j, name in enumerate(shown):
        i = first + j
        cy = TOP_Y - j * ROW_STEP
        on = i == row
        # R1: 블록을 아래로 2px 더 (영문 소문자 g·y 아래 여유가 1px였다 -> 3px). 위는 그대로
        mm.pick(PANEL_X + 34, cy, name, on, mm.PH_SOFT, center=False, small=True, span=(16, 14))
        m = marks.get(name)
        if m:
            text, color = MARKS[m]
            kit.text(PANEL_X + PANEL_W - 34, cy, text, color, small=True, right=True)
    if len(names) > VISIBLE:
        kit.text(PANEL_X + PANEL_W - 10, TOP_Y - VISIBLE * ROW_STEP + 14, f'{row + 1}/{len(names)}', mm.PH_MENU, small=True, right=True)
    mm.footer(FOOTER)
