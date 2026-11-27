"""타이틀 번개(L1 번갯줄기, docs/opus/TASKS.md '4차') 확인 촬영: 실제 창(모니터 2)에서 실제 그리기 코드로 단계마다 찍는다.
설정·저장 파일은 임시 폴더로 돌린다(사용자 파일을 건드리지 않는다).

  python tools/title_storm_shots.py <출력 폴더> --before     고치기 전 기록 (평소, 대비 판 셋)
  python tools/title_storm_shots.py <출력 폴더>              고친 뒤 (평소, 줄기 단계 셋, 대비 판 셋, dark, 잔광, 번쩍임 줄이기)
                                                            + 같은 폴더에 before_*.png가 있으면 비교판을 shots/review/L1_*.png로
"""
import ctypes
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
BEFORE = '--before' in sys.argv
OUT = ARGS[0]
REVIEW = os.path.join(ROOT, 'shots', 'review')
os.makedirs(OUT, exist_ok=True)
os.makedirs(REVIEW, exist_ok=True)
import pico2d.pico2d as p2  # noqa: E402
import sdl2  # noqa: E402
from pico2d import open_canvas, close_canvas  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

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
import title_mode  # noqa: E402
import title_storm  # noqa: E402
import transition  # noqa: E402

assert config.UI_SKIN == 'mist', config.UI_SKIN
title_mode.update_canvas = lambda: None          # 화면에 내보내기 전에 읽는다
PRE = 'before_' if BEFORE else ''


def grab(name):
    buf = (ctypes.c_ubyte * (W * H * 4))()
    sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
    Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(OUT, PRE + name + '.png'))
    p2.update_canvas()


def shoot(name, phase, plate=0, glow_left=None):
    storm = title_storm.Storm(seed=1)
    if phase:
        storm.force(phase)
        storm.plate = plate
        if glow_left is not None:                # 잔광이 얼마나 남았는지 (1.0 = 막 시작)
            storm.seq[0][1] = storm._glow_total * glow_left
    title_mode._storm[0] = storm
    title_mode.draw()
    grab(name)


title_mode.enter()
transition.tick(5.0)
title_mode._storm[0] = title_storm.Storm(seed=1)
title_mode._storm[0].wait = 1e9                  # 준비하는 동안 번개가 치지 않게
for _ in range(120):
    title_mode.update()
title_mode.selected = 0
shoot('normal', None)
for n in range(title_storm.FLASH_PLATES):
    shoot(f'flash_{n + 1}', 'flash', n)
if not BEFORE:
    for n in range(title_storm.FLASH_PLATES):
        shoot(f'bolt_{n + 1}', 'bolt', n)
    shoot('dark', 'dark', 0)
    shoot('glow', 'glow', 0, glow_left=0.8)
    old = options.reduce_flash
    options.reduce_flash = True                  # 메모리에서만 (options.PATH는 임시 폴더, 저장도 하지 않는다)
    storm = title_storm.Storm(seed=1)
    storm._start()
    assert storm.phase() == 'glow' and storm.flash_plate() is None
    title_mode._storm[0] = storm
    title_mode.draw()
    grab('reduce')
    options.reduce_flash = old
close_canvas()
if BEFORE:
    print('ok before', OUT)
    sys.exit(0)

# ----- 비교판 (원래 크기로 잘라 붙인다. 줄이지 않는다) -----
BG = (20, 20, 24)
try:
    FONT = ImageFont.truetype('malgun.ttf', 22)
except OSError:
    FONT = ImageFont.load_default()


def load(name):
    return Image.open(os.path.join(OUT, name + '.png'))


def stack(rows, path, pad=10, label_h=34):
    """[(이름표, 그림)]을 세로로 쌓는다."""
    w = max(im.width for _l, im in rows)
    board = Image.new('RGB', (w + 2 * pad, sum(im.height + label_h + pad for _l, im in rows) + pad), BG)
    d = ImageDraw.Draw(board)
    y = pad
    for label, im in rows:
        d.text((pad, y + 4), label, fill=(230, 230, 230), font=FONT)
        board.paste(im, (pad, y + label_h))
        y += im.height + label_h + pad
    board.save(path)
    return path


made = []
has_before = os.path.exists(os.path.join(OUT, 'before_flash_1.png'))
TOP = (0, 0, W, 620)                              # 하늘·로고가 있는 위쪽 (원래 크기)
HEAD = (0, 0, 800, 220)                           # 왼쪽 위 감시 글자
if has_before:
    made.append(stack([('고치기 전: flash (판 1)', load('before_flash_1')), ('고친 뒤: flash (판 1)', load('flash_1'))],
                      os.path.join(REVIEW, 'L1_flash_before_after.png')))
    made.append(stack([('평소 (바뀌지 않아야 한다): 전', load('before_normal').crop(HEAD)), ('평소: 후', load('normal').crop(HEAD)),
                       ('flash: 전', load('before_flash_1').crop(HEAD)), ('flash: 후', load('flash_1').crop(HEAD)),
                       ('줄기 단계: 후', load('bolt_1').crop(HEAD)), ('잔광: 후', load('glow').crop(HEAD))],
                      os.path.join(REVIEW, 'L1_header_before_after.png')))
    LOGO = (560, 180, 1360, 560)                  # 로고 뒤 어둠이 대비 판에서 회색 그늘로 보이는 곳 (고치지 않음, 보고용)
    made.append(stack([('로고 둘레 flash: 전', load('before_flash_1').crop(LOGO)), ('로고 둘레 flash: 후', load('flash_1').crop(LOGO))],
                      os.path.join(REVIEW, 'L1_logo_shade_note.png')))
made.append(stack([('1. 줄기 (1~2프레임)', load('bolt_1').crop(TOP)), ('2. 대비 판 (2~3프레임)', load('flash_1').crop(TOP)),
                   ('3. 원래 화면 + 줄기 (2~3프레임)', load('dark').crop(TOP)), ('4. 대비 판 (3~4프레임)', load('flash_1').crop(TOP)),
                   ('5. 잔광 (0.3초에 걸쳐 원래대로)', load('glow').crop(TOP)), ('번쩍임 줄이기: 약한 잔광만', load('reduce').crop(TOP))],
                  os.path.join(REVIEW, 'L1_strike_strip.png')))
rows = []
for n in range(title_storm.FLASH_PLATES):
    rows.append((f'판 {n + 1}: 줄기 단계', load(f'bolt_{n + 1}').crop(TOP)))
    rows.append((f'판 {n + 1}: 대비 판', load(f'flash_{n + 1}').crop(TOP)))
made.append(stack(rows, os.path.join(REVIEW, 'L1_bolt_plates.png')))
print('ok', OUT)
for m in made:
    print(m)
