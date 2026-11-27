"""A1 화면 일러스트 적용 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' A1).

실제 창(모니터 2)에서 게임의 그리기 코드 그대로 찍는다. 설정·저장 파일은 임시 폴더로 돌린다. 같은 시드라 전·후가 같은 순간이다.

  python tools/a1_illust_shots.py <출력 폴더>
      a1_death_<n>.png  사망 결과, 맡길 물건 n개(+ '없음' 칸): 1, 4, 6, 11 (11 = 아이템 10 + 무기, 가장 많을 때)
      a1_escape.png      탈출 결과 (맡길 물건 6개)
      a1_credits_<1~3>.png  크레딧 세 장면, a1_credits_ai.png  크레딧 'AI 도구' 절
  python tools/a1_illust_shots.py --board <전 폴더> <후 폴더> <비교판 폴더>
      A1_screens.png, A1_death_cells.png, A1_diff.png
"""
import ctypes
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1920, 1080
ITEMS = ('cap', 'absorb', 'steady', 'enhance', 'resist', 'dash', 'power', 'vigor', 'heal', 'fury')


def shoot(out):
    os.makedirs(out, exist_ok=True)
    import pico2d.pico2d as p2
    import sdl2
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

    import config
    import meta
    import options
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')     # 사용자 저장을 건드리지 않는다
    meta.reset()
    options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')   # 사용자 설정을 건드리지 않는다
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window(2)
    import boss_intro
    import credits_mode
    import effects
    import ending_mode
    import game_framework
    import items
    import play_mode
    import transition
    for mod in (play_mode, ending_mode, credits_mode):
        mod.update_canvas = lambda: None
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(mod, name):
        transition._left = 0.0
        mod.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'a1_{name}.png'))
        p2.update_canvas()

    def result_screen(result, n, seed):
        random.seed(seed)
        boss_intro.reset_all()
        effects.reset()
        game_framework.stack[:] = [play_mode]
        play_mode.enter()
        p = play_mode.player
        p.set_loadout('pipe', 'pistol' if n > 1 else None)       # 둘째 칸 무기도 맡길 물건 하나
        for it in ITEMS[:n - 1 if n > 1 else 1]:
            items.apply(p, it)
        p.run_rooms, p.run_kills, p.run_ends, p.run_clock = 9, 41, 1, 754.0
        p.death_cause = '크래셔의 강타'
        meta.state['keeper'] = True
        ending_mode.result = result
        game_framework.stack[:] = [ending_mode]
        ending_mode.enter()
        ending_mode.choice = 0

    for n in (1, 4, 6, 11):
        result_screen('dead', n, 13)
        grab(ending_mode, f'death_{n}')
    result_screen('clear', 6, 14)
    grab(ending_mode, 'escape')
    game_framework.stack[:] = [credits_mode]
    credits_mode.enter()
    total = credits_mode.total_height() + config.SCREEN_H * 0.5 + 180
    for i in range(3):
        sc = total * (i + 0.5) / 3
        credits_mode.scroll = sc
        credits_mode._scene = credits_mode.scene_for(sc)
        grab(credits_mode, f'credits_{i + 1}')
    off = 0                                                    # 'AI 도구' 절이 화면 가운데쯤 (크레딧 줄 전·후 확인)
    for kind, text in credits_mode.CREDITS:
        if text == 'AI 도구':
            break
        off += credits_mode.STYLE[kind][0]
    credits_mode.scroll = 600 + off
    credits_mode._scene = credits_mode.scene_for(credits_mode.scroll)
    grab(credits_mode, 'credits_ai')
    close_canvas()
    print('ok', out)


BG = (20, 20, 24)
try:
    FONT = ImageFont.truetype('malgun.ttf', 18)
except OSError:
    FONT = ImageFont.load_default()


def row_board(rows, path, label_w=180):
    pad = 10
    w = label_w + max(sum(im.width + pad for im in ims) for _l, ims in rows) + pad
    h = sum(max(im.height for im in ims) + pad for _l, ims in rows) + pad
    board = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(board)
    y = pad
    for label, ims in rows:
        d.text((pad, y + 4), label, fill=(230, 230, 230), font=FONT)
        x = label_w
        for im in ims:
            board.paste(im, (x, y))
            x += im.width + pad
        y += max(im.height for im in ims) + pad
    board.save(path)
    print('saved', path, board.size)


def board(before, after, out):
    import numpy as np
    os.makedirs(out, exist_ok=True)
    half = lambda im: im.resize((960, 540), Image.NEAREST)  # noqa: E731
    rows = []
    for n in ('death_4', 'escape', 'credits_1', 'credits_2', 'credits_3', 'credits_ai'):
        a, z = (Image.open(os.path.join(f, f'a1_{n}.png')) for f in (before, after))
        rows.append((f'{n} 전·후 (절반)', [half(a), half(z)]))
    row_board(rows, os.path.join(out, 'A1_screens.png'))
    rows = []
    for n in (1, 4, 6, 11):
        a, z = (Image.open(os.path.join(f, f'a1_death_{n}.png')).crop((240, 540, 1680, 860)) for f in (before, after))
        rows.append((f'물건 {n}개 전', [a]))
        rows.append((f'물건 {n}개 후', [z]))
    a, z = (Image.open(os.path.join(f, 'a1_escape.png')).crop((240, 540, 1920, 860)) for f in (before, after))
    rows += [('탈출 물건 6개 전', [a]), ('탈출 물건 6개 후', [z])]
    row_board(rows, os.path.join(out, 'A1_death_cells.png'))
    rows = []
    edit = {'credits_1': (0, 80, 768, 848), 'credits_3': (80, 440, 620, 845), 'screen_death': (0, 520, 960, 1060),
            'screen_ending': (1152, 312, 1920, 1080)}
    for n, c in edit.items():
        old = np.array(Image.open(os.path.join(ROOT, 'assets', 'sprites', 'gemini', 'illust_v2', 'before', n + '.png')).convert('RGB')).astype(int)
        new = np.array(Image.open(os.path.join(ROOT, 'assets', 'backgrounds', n + '.png')).convert('RGB')).astype(int)
        d = np.abs(old - new).max(axis=2)
        vis = (new * 0.35).astype(np.uint8)
        vis[d > 16] = (200, 160, 40)
        vis[d > 48] = (255, 60, 60)
        im = Image.fromarray(vis)
        ImageDraw.Draw(im).rectangle(c, outline=(80, 220, 255), width=3)
        m = np.zeros(d.shape, bool)
        m[c[1]:c[3], c[0]:c[2]] = True
        label = f'{n}: 편집 상자 밖 >16 {100 * ((d > 16) & ~m).mean():.2f}% >48 {100 * ((d > 48) & ~m).mean():.3f}%'
        rows.append((label, [half(im)]))
    row_board(rows, os.path.join(out, 'A1_diff.png'), label_w=520)


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:5])
    else:
        shoot(sys.argv[1])
