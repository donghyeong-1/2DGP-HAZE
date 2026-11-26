"""'mist' 스킨(타이틀 감시 단말 + 증강 선택 안개 미니멀) 확인 촬영: 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. python tools/ui_mist_shots.py <출력 폴더>
결과: title_<n>.png (메뉴 고른 항목별), cards_<방>_<셋>.png, 그리고 원래 크기를 잘라 붙인 비교판 board.png."""
import ctypes
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
import pico2d.pico2d as p2  # noqa: E402
import sdl2  # noqa: E402
from pico2d import open_canvas, close_canvas  # noqa: E402
from PIL import Image  # noqa: E402

import config  # noqa: E402
import meta  # noqa: E402
import options  # noqa: E402
meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')
meta.reset()
options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
open_canvas(config.SCREEN_W, config.SCREEN_H)
from window_place import place_window  # noqa: E402
place_window(2)
W, H = config.SCREEN_W, config.SCREEN_H
import curse  # noqa: E402
import game_framework  # noqa: E402
import game_world  # noqa: E402
import mutation_mode  # noqa: E402
import mutations as mu  # noqa: E402
import play_mode  # noqa: E402
import title_mode  # noqa: E402
import transition  # noqa: E402
import zone_card  # noqa: E402

assert config.UI_SKIN == 'mist', config.UI_SKIN
mutation_mode.update_canvas = lambda: None          # 화면에 내보내기 전에 읽는다
title_mode.update_canvas = lambda: None
shots = []


def grab(name):
    buf = (ctypes.c_ubyte * (W * H * 4))()
    sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
    Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(OUT, name + '.png'))
    p2.update_canvas()
    shots.append(name)


# ----- 타이틀 -----
title_mode.enter()
transition.tick(5.0)
for _ in range(120):
    title_mode.update()
for sel in (0, 2):
    title_mode.selected = sel
    title_mode.draw()
    grab(f'title_{sel}')

# ----- 증강 카드 -----
game_framework.stack[:] = [play_mode]
play_mode.enter()
p = play_mode.player
p.set_loadout('pipe', 'pistol')
for m in ('tide_cost', 'bloom_crit'):
    mu.give(p, m)


def settle():
    for _ in range(240):
        zone_card.freezing = False
        for o in list(game_world.world[game_world.LAYER_UI]):
            if isinstance(o, zone_card.ZoneCard):
                game_world.remove_object(o)
        play_mode.update()
    transition.tick(5.0)


base = [m for m in mu.MUTATIONS if mu.tier(m) == 'base' and mu.available(p, m) and not mu.has(p, m)]
duo = [m for m in mu.MUTATIONS if mu.tier(m) == 'duo' and mu.MUTATIONS[m].get('ready')]
evo = [m for m in mu.MUTATIONS if mu.tier(m) == 'evo' and mu.MUTATIONS[m].get('ready')]
SETS = {'base': (base[:3], 1), 'duo': ([base[3], duo[0], evo[0] if evo else base[4]], 1),
        'curse': ([base[5], base[6], curse.CARD + 'frail'], 2)}
ROOMS = [('slum', 'stage1', False), ('foundry', 'stage2', False), ('tower', 'stage3', False), ('boss', 'stage1', True)]
game_framework.stack.append(mutation_mode)
for rname, target, boss in ROOMS:
    play_mode._test_jump(target)
    if boss:
        play_mode._test_jump('boss')
    settle()
    for sname, (ids, sel) in SETS.items():
        mutation_mode.setup(p, ids)
        mutation_mode.enter()
        mutation_mode.age = 5.0
        mutation_mode.selected = sel
        mutation_mode.draw()
        grab(f'cards_{rname}_{sname}')
close_canvas()

# ----- 비교판: 원래 크기로 잘라 붙인다 -----
cw, ch = 1260, 800                                   # 카드 셋 + 제목 + 아래 안내 (가운데)
board = Image.new('RGB', (cw * 3 + 40, ch * 4 + 30), (20, 20, 24))
y = 0
for rname, _t, _b in ROOMS:
    for j, sname in enumerate(SETS):
        im = Image.open(os.path.join(OUT, f'cards_{rname}_{sname}.png'))
        board.paste(im.crop(((W - cw) // 2, (H - ch) // 2 + 10, (W + cw) // 2, (H + ch) // 2 + 10)), (j * (cw + 20), y))
    y += ch + 10
board.save(os.path.join(OUT, 'board_cards.png'))
t = Image.new('RGB', (W * 2 + 20, H), (20, 20, 24))
for j, sel in enumerate((0, 2)):
    t.paste(Image.open(os.path.join(OUT, f'title_{sel}.png')), (j * (W + 20), 0))
t.save(os.path.join(OUT, 'board_title.png'))
print('ok', len(shots), OUT)
