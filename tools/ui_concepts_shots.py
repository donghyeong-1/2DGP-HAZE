"""UI 컨셉 셋(안개 미니멀 / 감시 단말 / 수감 기록) 시안: 실제 창에서 게임 배경·글꼴 위에 PixelLab 조각을 얹어 찍는다.
python tools/ui_concepts_shots.py <출력 폴더> (먼저 python tools/ui_concepts_prep.py). 결과: <컨셉>_title.png, <컨셉>_cards.png (1920x1080)
글자 크기·위치는 지금 게임(title_mode·mutation_mode)과 같다. 판·틀·장식은 PixelLab 조각뿐, 코드는 글자·배치·배경과 화면 효과(주사선·어둡게 덮기)."""
import ctypes, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src')); sys.path.insert(0, os.path.join(ROOT, 'tools')); os.chdir(ROOT)
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
import pico2d.pico2d as p2
from pico2d import open_canvas, close_canvas, clear_canvas
import sdl2
from PIL import Image
import config
config.UI_SKIN = 'crystal'
import game_framework, meta, options
meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json'); meta.reset()
options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
open_canvas(config.SCREEN_W, config.SCREEN_H)
from window_place import place_window
place_window(2)
W, H = config.SCREEN_W, config.SCREEN_H
import assets, sprites, hud_kit as kit, atmosphere, game_world, mutations as mu, curse
import play_mode, title_mode, mutation_mode, transition, zone_card
PX = 'sprites/pixellab/ui_concepts_v2/'


def grab(name):
    buf = (ctypes.c_ubyte * (W * H * 4))()
    sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
    Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(OUT, name + '.png'))
    p2.update_canvas()


def img(rel):
    return assets.image(PX + rel)


def put(rel, cx, bottom, flip=''):
    """조각을 가운데 x, 아래 y에 1배(이미 2배로 구운 그림)로."""
    i = img(rel)
    assets.draw_image(i, int(cx), int(bottom), flip)
    return i


# ----- 배경 -----
rain = atmosphere.Weather(seed=3); rain.set_kind('rain')
for _ in range(90):
    rain.update(1 / 60)


def title_bg():
    clear_canvas()
    assets.draw_image(assets.image('backgrounds/title_plate.png'), W // 2, 0)
    rain.draw()
    sprites.draw('n09_idle', 2, title_mode.HERO_X, title_mode.HERO_Y, 1)


game_framework.stack[:] = [play_mode]
play_mode.enter()
play_mode._test_jump('stage1')
p = play_mode.player
p.set_loadout('pipe', 'pistol')
for m in ('tide_cost', 'bloom_crit'):
    mu.give(p, m)
for _ in range(300):
    zone_card.freezing = False
    for o in list(game_world.world[game_world.LAYER_UI]):
        if isinstance(o, zone_card.ZoneCard):
            game_world.remove_object(o)
    play_mode.update()
transition.tick(5.0)
UI_OBJS = list(game_world.world[game_world.LAYER_UI])


DIM = [0.66]


def cards_bg():
    clear_canvas()
    game_world.world[game_world.LAYER_UI][:] = []                 # 뒤에는 세계만 (HUD는 시안 밖)
    play_mode.draw_frozen()
    game_world.world[game_world.LAYER_UI][:] = UI_OBJS
    assets.draw_rect_color(0, 0, W, H, (6, 9, 18), DIM[0])        # 어둡게 덮기 (지금 게임 0.66, 틀 없는 A는 더 진하게)


# 카드 셋: 보통(기본 증강), 진화(희귀), 저주. 고른 카드 = 첫 장
base = [m for m in mu.MUTATIONS if mu.tier(m) == 'base' and mu.available(p, m) and not mu.has(p, m)]
evo = [m for m in mu.MUTATIONS if mu.tier(m) == 'evo' and mu.MUTATIONS[m].get('ready')]
duo = [m for m in mu.MUTATIONS if mu.tier(m) == 'duo' and mu.MUTATIONS[m].get('ready')]
CHOICES = [base[0], duo[0], curse.CARD + 'frail']
mutation_mode.choices = CHOICES
CW, CH, CY = mutation_mode.CARD_W, mutation_mode.CARD_H, mutation_mode.CARD_Y


def card_info(mid):
    """(등급, 위 띠 글, 이름, 갈래 줄, 설명 줄들, 아래 글, 아이콘 경로, 갈래 색)."""
    if mid.startswith(curse.CARD):
        info = curse.card_info(p, mid)
        return ('curse', '저주', info['name'], info['sub'], mutation_mode._wrap(info['desc'], 13), '보상 ???',
                'ui/up_mut_curse.png', curse.COLOR)
    m = mu.MUTATIONS[mid]
    fam = mu.FAMILIES[m['family']]
    tier = mu.tier(mid)
    rarity = {'base': 'common', 'evo': 'rare', 'duo': 'legendary'}[tier]
    label = {'evo': '진화', 'duo': '합성'}.get(tier, '')
    sub = fam['name'] + (' 계열' if m['family'] in mu.GAUGE_FAMILIES else ' 갈래')
    if fam.get('weapon'):
        sub = mu.WEAPON_NAMES.get(fam['weapon'], '') + ' · ' + sub
    note = mu.card_info(p, mid)['note']
    return (rarity, label, m['name'], sub, mutation_mode._wrap(m['desc'], 13), note, f'ui/up_mut_{m["family"]}.png', fam['color'])


def card_texts(x, y, info, ink=None, sub_ink=None, desc_ink=(205, 215, 235), name_ink=(240, 244, 252), note_ink=(255, 225, 140)):
    """지금 게임과 같은 자리에 글자: 위 띠 CH-54, 이름 CH-200(큰 글자), 갈래 CH-250, 설명 CH-300부터 30씩, 아래 글 y+84."""
    rarity, label, name, sub, desc, note, icon, color = info
    ic = assets.image(icon)
    assets.draw_image(ic, x + CW // 2, y + CH - 70 - ic.h)
    if label:
        kit.text(x + CW // 2, y + CH - 54, label, ink or color, center=True, small=True)
    kit.text(x + CW // 2, y + CH - 200, name, name_ink, center=True, big=True)
    kit.text(x + CW // 2, y + CH - 250, sub, sub_ink or color, center=True, small=True)
    for j, line in enumerate(desc):
        kit.text(x + CW // 2, y + CH - 300 - j * 30, line, desc_ink, center=True, small=True)
    for j, line in enumerate(mutation_mode._wrap(note, 16)):
        kit.text(x + CW // 2, y + 84 - j * 26, line, note_ink, center=True, small=True)


def card_title(title_ink, sub_ink):
    kit.text(W // 2, CY + CH + 110, '증강 선택', title_ink, center=True, big=True)
    kit.text(W // 2, CY + CH + 66, '하나를 선택하세요. 이번 판이 끝날 때까지 유지됩니다', sub_ink, center=True, small=True)


MENU = title_mode.MENU
SEL = 0


# ================= A 안개 미니멀 =================
def a_title():
    title_bg()
    put('a_mist/parts/logo.png', W // 2, 600)
    kit.text(W // 2, 580, '헤이즈', (160, 248, 238), center=True)
    for i, b in enumerate(MENU):
        cy = b.y + b.h // 2
        hot = i == SEL
        kit.text(W // 2, cy, b.label, (242, 246, 250) if hot else (110, 124, 150), center=True)
        if hot:
            tw = assets.text_width(b.label, False)
            put('a_mist/parts/ember.png', W // 2 - tw // 2 - 34, cy - 22)
    kit.text(W - 28, 30, title_mode.VERSION, (110, 124, 150), small=True, right=True)
    grab('A_title')


def a_cards():
    DIM[0] = 0.82
    cards_bg()
    DIM[0] = 0.66
    card_title((242, 246, 250), (130, 145, 170))
    orn = {'common': 'divider_white', 'rare': 'divider_cyan', 'legendary': 'divider_gold', 'curse': 'divider_red'}
    for i, mid in enumerate(CHOICES):
        info = card_info(mid)
        x = mutation_mode.card_x(i)
        y = CY + (16 if i == SEL else 0)
        if i == SEL:
            put('a_mist/parts/mist_pool.png', x + CW // 2, y - 40)
        o = orn[info[0]]
        put(f'a_mist/parts/{o}.png', x + CW // 2, y + CH - 32)
        put(f'a_mist/parts/{o}.png', x + CW // 2, y + 20)
        card_texts(x, y, info)
    kit.text(W // 2, CY - 80, 'A D  선택      Enter  확인', (130, 145, 170), center=True, small=True)
    grab('A_cards')


# ================= B 감시 단말 =================
PH = (168, 240, 200)        # 인광 글자
PH_DIM = (60, 110, 100)
PH_BG = (10, 16, 20)


def scanlines():
    for yy in range(0, H, 4):
        assets.draw_rect_color(0, yy, W, 2, (0, 0, 0), 0.18)


def corners(margin=24):
    b = img('b_terminal/parts/bracket.png')
    put('b_terminal/parts/bracket.png', margin + b.w // 2, H - margin - b.h)
    put('b_terminal/parts/bracket.png', W - margin - b.w // 2, H - margin - b.h, 'h')
    put('b_terminal/parts/bracket.png', margin + b.w // 2, margin, 'v')
    put('b_terminal/parts/bracket.png', W - margin - b.w // 2, margin, 'hv')


def b_title():
    title_bg()
    scanlines()
    corners()
    kit.text(110, H - 60, 'TOWER SURVEILLANCE // INMATE N-09', PH, small=True)
    kit.text(110, H - 86, 'CAM 04 · 제9구역 폐기물 슬럼 · REC', PH_DIM, small=True)
    put('b_terminal/parts/lamps.png', W - 200, H - 92)
    put('b_terminal/parts/logo.png', W // 2, 600)
    kit.text(W // 2, 580, '헤이즈', PH, center=True)
    for i, b in enumerate(MENU):
        cy = b.y + b.h // 2
        hot = i == SEL
        tw = assets.text_width(b.label, False)
        if hot:                                                    # 글자 색 뒤집기 (밝은 바탕에 어두운 글자), 앞에 커서
            assets.draw_rect_color(W // 2 - tw // 2 - 8, cy - 18, tw + 16, 36, PH)
            assets.draw_text(W // 2, cy, b.label, PH_BG, center=True)
            put('b_terminal/parts/cursor.png', W // 2 - tw // 2 - 34, cy - 21)
        else:
            kit.text(W // 2, cy, b.label, PH_DIM, center=True)
    kit.text(W - 110, 60, title_mode.VERSION, PH_DIM, small=True, right=True)
    grab('B_title')


def b_cards():
    cards_bg()
    scanlines()
    corners()
    kit.text(110, H - 60, 'TOWER SURVEILLANCE // INMATE N-09', PH, small=True)
    card_title(PH, PH_DIM)
    head = {'common': 'header', 'rare': 'header', 'legendary': 'header_gold', 'curse': 'header_red'}
    for i, mid in enumerate(CHOICES):
        info = card_info(mid)
        x = mutation_mode.card_x(i)
        y = CY + (16 if i == SEL else 0)
        put('b_terminal/parts/card.png', x + CW // 2, y)
        hb = put(f'b_terminal/parts/{head[info[0]]}.png', x + CW // 2, y + CH - 40)
        tag = {'common': 'AUGMENT', 'rare': 'AUGMENT // EVO', 'legendary': 'AUGMENT // FUSION', 'curse': 'CURSE'}[info[0]]
        assets.draw_text(x + 26, y + CH - 40 + hb.h // 2, tag, PH_BG if info[0] != 'common' else PH, small=True)
        rarity, label, name, sub, desc, note, icon, color = info
        info = (rarity, '', name, sub, desc, note, icon, color)
        card_texts(x, y - 14, info, sub_ink=PH_DIM, desc_ink=(150, 210, 180), name_ink=PH, note_ink=(240, 200, 110))
        if i == SEL:                                               # 고른 카드: 괄호 모서리 + 커서
            put('b_terminal/parts/screen_brackets.png', x + CW // 2, y - 30) if False else None
            b = img('b_terminal/parts/bracket.png')
            put('b_terminal/parts/bracket.png', x - 14 + b.w // 2, y + CH + 14 - b.h)
            put('b_terminal/parts/bracket.png', x + CW + 14 - b.w // 2, y + CH + 14 - b.h, 'h')
            put('b_terminal/parts/bracket.png', x - 14 + b.w // 2, y - 14, 'v')
            put('b_terminal/parts/bracket.png', x + CW + 14 - b.w // 2, y - 14, 'hv')
    kit.text(W // 2, CY - 80, '> A D 선택    ENTER 확인', PH, center=True, small=True)
    grab('B_cards')


# ================= C 수감 기록 =================
INK = (44, 36, 30)          # 타자기 잉크
INK_DIM = (96, 84, 70)
PAPER_TXT = (188, 171, 144)  # 어두운 화면 위 종이빛 글자


def c_title():
    title_bg()
    put('c_record/parts/logo.png', W // 2, 600)
    kit.text(W // 2, 580, '헤이즈', PAPER_TXT, center=True)
    kit.text(W // 2, 540, '수감 기록 · 수번 N-09', (150, 136, 116), center=True, small=True)
    for i, b in enumerate(MENU):
        cy = b.y + b.h // 2
        hot = i == SEL
        tw = assets.text_width(b.label, False)
        kit.text(W // 2, cy, b.label, PAPER_TXT if hot else (120, 110, 96), center=True)
        if hot:
            u = img('c_record/parts/underline.png')
            put('c_record/parts/underline.png', W // 2, cy - 30)
            put('c_record/parts/check.png', W // 2 - tw // 2 - 40, cy - 24)
    kit.text(W - 28, 30, title_mode.VERSION, (120, 110, 96), small=True, right=True)
    grab('C_title')


def c_cards():
    cards_bg()
    card_title(PAPER_TXT, (150, 136, 116))
    stamp = {'common': 'stamp_blue', 'rare': 'stamp_red', 'legendary': 'stamp_gold', 'curse': 'stamp_red'}
    for i, mid in enumerate(CHOICES):
        info = card_info(mid)
        x = mutation_mode.card_x(i)
        y = CY + (16 if i == SEL else 0)
        put('c_record/parts/card.png', x + CW // 2, y)
        rarity, label, name, sub, desc, note, icon, color = info
        card_texts(x, y, (rarity, label, name, sub, desc, note, icon, color), ink=(150, 40, 44), sub_ink=(120, 60, 50),
                   desc_ink=INK, name_ink=INK, note_ink=(122, 30, 34))
        s = img(f'c_record/parts/{stamp[rarity]}.png')
        put(f'c_record/parts/{stamp[rarity]}.png', x + 34 + s.w // 2, y + CH - 160)     # 왼쪽 위 (글자와 겹치지 않게)
        if rarity == 'curse':
            kit.text(x + 34 + s.w // 2, y + CH - 160 - 16, '경고', (168, 50, 54), center=True, small=True)
        if i == SEL:
            put('c_record/parts/clip.png', x + 50, y + CH - 60)
            put('c_record/parts/underline.png', x + CW // 2, y + CH - 234)
    kit.text(W // 2, CY - 80, 'A D 선택    Enter 확인', PAPER_TXT, center=True, small=True)
    grab('C_cards')


for f in (a_title, a_cards, b_title, b_cards, c_title, c_cards):
    f()
close_canvas()
print('ok', OUT)
