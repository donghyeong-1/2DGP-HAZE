"""효과음 듣는 방 (v8 계획 4-6, 2026-11-25). 연습 메뉴의 '효과음 듣기'에서 연다.

효과음을 종류별로 하나씩 들어 보고 '좋음'·'바꿔'를 표시한다. 표시는 저장소 폴더의 sfx_review.json에 남는다.
Claude는 소리를 들을 수 없다: 사용자가 '바꿔'로 표시한 것만 다시 만든다.

A/D 종류, W/S 소리, Enter·Space 듣기, G 좋음, B 바꿔, X 표시 지우기, Esc·F 닫기.
"""
import json
import os

from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_DOWN, SDLK_ESCAPE, SDLK_LEFT, SDLK_RETURN, SDLK_RIGHT, SDLK_SPACE,
                    SDLK_UP, SDLK_a, SDLK_b, SDLK_d, SDLK_f, SDLK_g, SDLK_s, SDLK_w, SDLK_x, clear_canvas, get_events,
                    update_canvas)

import assets
import config
import game_framework
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
          ('warn', '경고'), ('ui', '메뉴')]
OTHER = '그 밖'
MARKS = {'good': ('좋음', (150, 240, 170)), 'bad': ('바꿔', (255, 130, 130))}
cat = 0
row = 0
marks = {}
_catalog = None
_under = None


def catalog():
    """[(종류 이름, [소리 이름...])]: assets/sfx의 wav를 파일 이름 첫 낱말로 묶는다. 빈 종류는 뺀다."""
    global _catalog
    if _catalog is None:
        names = sorted(f[:-4] for f in os.listdir(os.path.join(assets.ASSET_DIR, 'sfx')) if f.endswith('.wav'))
        labels = dict(GROUPS)
        buckets = {label: [] for _, label in GROUPS}
        buckets[OTHER] = []
        for n in names:
            buckets[labels.get(n.split('_')[0], OTHER)].append(n)
        _catalog = [(label, buckets[label]) for label in [g[1] for g in GROUPS] + [OTHER] if buckets[label]]
    return _catalog


def load():
    global marks
    try:
        with open(PATH, encoding='utf-8') as f:
            data = json.load(f)
        marks = {k: v for k, v in data.get('marks', {}).items() if v in MARKS}
    except (OSError, ValueError, AttributeError):
        marks = {}
    return marks


def save():
    """표시를 저장한다. '바꿔'인 것은 종류별 목록으로도 적어 둔다(읽기 쉽게)."""
    redo = {}
    for label, names in catalog():
        bad = [n for n in names if marks.get(n) == 'bad']
        if bad:
            redo[label] = bad
    tmp = PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump({'marks': marks, 'redo': redo}, f, ensure_ascii=False, indent=1)
    os.replace(tmp, PATH)


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


def play(name):
    """그 파일 그대로 들려준다 (게임 중의 변형 고르기·소리별 크기 보정 없이, 설정의 효과음 크기만)."""
    wav = assets.sound(name)
    if wav is not None:
        import options
        wav.set_volume(options.volume(config.SFX_VOLUME, options.sfx_level))
        wav.play()


def enter():
    global cat, row, _under
    cat = row = 0
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
        if k in (SDLK_ESCAPE, SDLK_f):
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


def update():
    pass


def draw():
    clear_canvas()
    if _under is not None and hasattr(_under, 'draw_frozen'):
        _under.draw_frozen()
    kit.backdrop(0.92)
    groups = catalog()
    total = sum(len(names) for _, names in groups)
    done = sum(1 for names in (g[1] for g in groups) for n in names if n in marks)
    bad = sum(1 for v in marks.values() if v == 'bad')
    kit.heading(PANEL_X, H - 150, '효과음 듣기', f'표시 {done}/{total} · 바꿔 {bad}')
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
    kit.footer([('A D', '종류'), ('W S', '선택'), ('Enter', '듣기'), ('G', '좋음'), ('B', '바꿔'), ('X', '표시 지우기'), ('Esc', '닫기')])
    update_canvas()
