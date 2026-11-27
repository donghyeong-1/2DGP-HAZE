"""게임 화면에 놓이는 소품(PixelLab v6)을 게임 그림으로 적용한다 (2026-11-27 Q1, docs/opus/TASKS.md '4차' Q1).

원본은 assets/sprites/pixellab/props_v6/<물건>/raw/ (고른 시안), 버린 시안은 raw_gen/. 생성 기록은 props_v6/GENERATION_LOG.md.
화풍 기준은 간수 assets/sprites/pixellab/guard_v6/raw/base.png (style_image로 넣어 뽑았다).

1. 알파 0/255. 몸통에서 떨어진 작은 점(3칸 이하 덩어리)은 지운다(떠 있는 점).
2. 색 고정: 물건마다 원본 색을 MAX_COLORS로 줄이고, 간수 그림의 색과 가까운 색(SNAP 안)은 간수 색으로 맞춘다
   (외곽선 남색·강철 회색을 캐릭터와 한 벌로).
3. 그림 둘레로 자르고 최근접 2배(도트 2px). 게임은 그림의 가운데 아래를 기준점으로 그린다(assets.draw_image).
4. 상태 그림은 같은 그림에서 코드로 만든다(모양이 어긋나지 않게):
   - 증기 분출구 달아오름(device_vent_hot): 격자 틈(외곽선과 이어지지 않은 어두운 칸)을 주황 불빛으로
   - 품절 진열대(pedestal_gone, pedestal_gone_shop): 제단·선반 그림의 색을 어둡고 차갑게
   부서진 상자만 같은 시안을 PixelLab으로 고친 그림(edit_image_pro_flash)이다.

결과
   assets/ui/hideout_armory.png, hideout_practice.png  (src/npc.py 무기 걸이·연습장 표지판)
   assets/ui/device_crate.png, device_crate_broken.png, device_vent.png, device_vent_hot.png, device_laser.png  (src/devices.py)
   assets/ui/pedestal_gold.png, pedestal_shop.png, pedestal_gone.png, pedestal_gone_shop.png  (src/pedestal.py, 120x150 캔버스 그대로)
   assets/props/hideout_anvil_1~4.png  (src/props_anim.py 은신처 모루, 132x117 캔버스·기준점 그대로): 몸통은 PixelLab 한 장,
       불똥은 옛 Codex T28 네 장(raw/codex_sparks_N.png)에서 몸통 위 점만 옮겨 달군 쇠 색으로
   assets/props/hideout_brazier_1~4.png  (은신처 화로, 99x120 캔버스·기준점 그대로): PixelLab 한 장 + animate_image_pixminimax 불꽃 4장,
       그릇·다리 줄(BRAZIER_STILL_Y 아래)은 0번 장 그대로 (흔들리지 않게), 튀는 불티는 지우지 않는다

실행: python tools/apply_pixellab_props.py [물건 ...]
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_pixellab_event import load, reduce_palette  # noqa: E402
from apply_pixellab_hero import lock_palette  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'props_v6')
GUARD = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'guard_v6', 'raw', 'base.png')
UI = os.path.join(ROOT, 'assets', 'ui')
SCALE = 2
MAX_COLORS = 32
SNAP = 20            # 간수 색과 이 거리(RGB) 안이면 간수 색으로
PEDESTAL_CANVAS = (120, 150)
OUTLINED = ('practice',)        # 바깥에 간수의 가장 어두운 남색 외곽선 1도트를 두를 것 (원본 외곽선이 흐려 은신처 배경에 묻혔다)    # tests/test_sprites.py: 진열대 그림 크기 (아이콘은 발 위 66px에 놓인다)

# 이름: (원본 폴더, [(raw 파일, 결과 이름)], 같은 틀로 자를 것인가)
SETS = {
    'armory': ('armory', [('base.png', 'hideout_armory')]),
    'practice': ('practice', [('base.png', 'hideout_practice')]),     # 원본 외곽선이 흐려 바깥 외곽선을 두른다 (OUTLINED)
    'crate': ('crate', [('base.png', 'device_crate'), ('broken.png', 'device_crate_broken')]),
    'vent': ('vent', [('base.png', 'device_vent')]),
    'laser': ('laser', [('base.png', 'device_laser')]),
    'pedestal': ('pedestal', [('altar.png', 'pedestal_gold'), ('shop.png', 'pedestal_shop')]),
    'anvil': ('anvil', [('base.png', 'hideout_anvil')]),
    'brazier': ('brazier', [(f'flicker/frame_{i}.png', f'hideout_brazier_{i + 1}') for i in range(4)]),
}
BRAZIER_CANVAS, BRAZIER_ANCHOR, BRAZIER_STILL_Y = (99, 130), (49, 128), 32   # props_anim 'brazier' 캔버스(Q1에 120 -> 130), 기준점 x·발 밑 줄(기준점 2px 아래, 옛 그림과 같다), 원본 줄
ANVIL_CANVAS, ANVIL_ANCHOR = (132, 117), (56, 112)    # props_anim.SIZE('anvil')의 캔버스, 옛 그림의 발 가운데 x와 발 밑 줄 (발을 같은 자리에)
EMBER = [(255, 226, 160), (240, 150, 70), (196, 92, 48)]   # 불똥: 밝은 칸부터


def guard_palette():
    g = load(GUARD)
    return np.unique(g[g[:, :, 3] == 255][:, :3], axis=0).astype(np.int32)


def snap_to_guard(pal, gpal):
    pal = pal.astype(np.int32).copy()
    for i, c in enumerate(pal):
        d = np.sqrt(((gpal - c) ** 2).sum(axis=1))
        if d.min() <= SNAP:
            pal[i] = gpal[d.argmin()]
    return np.unique(pal, axis=0).astype(np.uint8)


def drop_specks(a, keep=4):
    """8방향으로 이어진 불투명 덩어리 가운데 keep칸보다 작은 것을 지운다 (가장 큰 덩어리는 늘 남긴다)."""
    from scipy import ndimage
    lab, n = ndimage.label(a[:, :, 3] == 255, structure=np.ones((3, 3)))
    if n <= 1:
        return a
    sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, n + 1))
    big = int(np.argmax(sizes)) + 1
    out = a.copy()
    for k, s in enumerate(sizes, start=1):
        if k != big and s < keep:
            out[lab == k] = 0
    return out


def outer_outline(a, color):
    """투명 칸 가운데 불투명 칸과 위아래·좌우로 닿는 칸을 color로 (캔버스를 1칸씩 넓혀서)."""
    a = np.pad(a, ((1, 1), (1, 1), (0, 0)))
    op = a[:, :, 3] == 255
    near = np.zeros_like(op)
    near[1:] |= op[:-1]
    near[:-1] |= op[1:]
    near[:, 1:] |= op[:, :-1]
    near[:, :-1] |= op[:, 1:]
    ring = near & ~op
    a[ring] = (*color, 255)
    return a


def frame_box(frames):
    ys, xs = np.nonzero(np.maximum.reduce([f[:, :, 3] for f in frames]))
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def up(a):
    im = Image.fromarray(a, 'RGBA')
    return im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)


def vent_hot(a):
    """격자 틈을 불빛으로: 그림 바깥(투명)과 어두운 색으로 이어지지 않은 어두운 칸 = 틈. 위쪽 줄일수록 밝게."""
    from scipy import ndimage
    rgb = a[:, :, :3].astype(np.int32)
    lum = rgb @ np.array([3, 6, 1]) / 10
    op = a[:, :, 3] == 255
    dark = op & (lum < 62)
    outside = ~op
    reach = ndimage.binary_propagation(outside, mask=outside | dark, structure=np.ones((3, 3)))
    slot = dark & ~reach
    out = a.copy()
    ys = np.nonzero(slot)[0]
    if len(ys) == 0:
        return out
    top, bot = ys.min(), ys.max()
    hot = [(255, 236, 190), (255, 170, 80), (226, 96, 44)]     # 흰 주황 -> 주황 -> 붉은 주황 (위에서 아래로)
    for y, x in zip(*np.nonzero(slot)):
        k = 0 if bot == top else int(round((y - top) / (bot - top) * 2))
        out[y, x, :3] = hot[k]
    return out


def dim(a, cool=(54, 62, 84), mix=0.55, keep_outline=40):
    """품절 그림: 밝기를 낮추고 차가운 남회색 쪽으로 섞는다 (외곽선처럼 어두운 칸은 그대로)."""
    out = a.copy()
    m = out[:, :, 3] == 255
    rgb = out[m][:, :3].astype(np.float32)
    lum = rgb @ np.array([0.3, 0.6, 0.1], np.float32)
    grey = np.repeat(lum[:, None], 3, axis=1) * 0.75
    new = grey * (1 - mix) + np.array(cool, np.float32) * mix
    new = np.where(lum[:, None] < keep_outline, rgb, new)
    out[m, :3] = np.clip(new, 0, 255).astype(np.uint8)
    return out


def on_canvas(im, size):
    """가운데 아래 맞춰 정해진 캔버스에 놓는다."""
    w, h = size
    assert im.width <= w and im.height <= h, (im.size, size)
    c = Image.new('RGBA', size, (0, 0, 0, 0))
    c.paste(im, ((w - im.width) // 2 // 2 * 2, h - im.height))
    return c


def apply(name, gpal):
    folder, items = SETS[name]
    raw = os.path.join(SRC, folder, 'raw')
    frames = [load(os.path.join(raw, f)) for f, _ in items]
    if name == 'brazier':                        # 그릇·다리는 0번 장 그대로, 불티는 남긴다
        for f in frames[1:]:
            f[BRAZIER_STILL_Y:] = frames[0][BRAZIER_STILL_Y:]
    else:
        frames = [drop_specks(f) for f in frames]
    px = np.concatenate([f[f[:, :, 3] == 255][:, :3] for f in frames])
    pal, counts = np.unique(px, axis=0, return_counts=True)
    pal = snap_to_guard(reduce_palette(pal, counts, MAX_COLORS), gpal)
    frames = [lock_palette(f, pal) for f in frames]
    if name in OUTLINED:
        ink = tuple(int(v) for v in gpal[np.argmin(gpal.sum(axis=1))])
        frames = [outer_outline(f, ink) for f in frames]
    out = {}
    if name == 'pedestal':                       # 제단과 선반은 따로 자른다 (같은 캔버스에 가운데 아래로)
        for f, (_, o) in zip(frames, items):
            x0, y0, x1, y1 = frame_box([f])
            out[o] = f[y0:y1, x0:x1]
        out['pedestal_gone'] = dim(out['pedestal_gold'])
        out['pedestal_gone_shop'] = dim(out['pedestal_shop'])
    else:
        x0, y0, x1, y1 = frame_box(frames)
        for f, (_, o) in zip(frames, items):
            out[o] = f[y0:y1, x0:x1]
        if name == 'vent':
            out['device_vent_hot'] = vent_hot(out['device_vent'])
    if name == 'anvil':
        anvil_frames(out.pop('hideout_anvil'), raw)
        return
    if name == 'brazier':
        for o, a in out.items():
            im = up(a)
            W, H = BRAZIER_CANVAS
            c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            assert im.height <= BRAZIER_ANCHOR[1], im.size
            c.paste(im, (BRAZIER_ANCHOR[0] - im.width // 2 // 2 * 2, BRAZIER_ANCHOR[1] - im.height))
            c.save(os.path.join(ROOT, 'assets', 'props', o + '.png'))
        print(f'brazier: hideout_brazier_1~4.png {W}x{H}px, 그림 {im.width}x{im.height}px')
        return
    for o, a in out.items():
        im = up(a)
        if o.startswith('pedestal_'):
            im = on_canvas(im, PEDESTAL_CANVAS)
        im.save(os.path.join(UI, o + '.png'))
        print(f'{name}: {o}.png {im.size[0]}x{im.size[1]}px, {len(np.unique(a[a[:, :, 3] == 255][:, :3], axis=0))}색')


def anvil_frames(body, raw):
    """모루 네 장: 새 몸통(2배)을 옛 캔버스에 같은 기준점으로 놓고, 옛 장마다 몸통 위로 튄 불똥만 옮긴다."""
    from scipy import ndimage
    im = up(body)
    W, H = ANVIL_CANVAS
    al = np.array(im)[:, :, 3] > 0                          # 발(아래 20px)의 가로 가운데를 옛 발 자리에 (뿔이 오른쪽으로 길어 몸통 가운데와 다르다)
    ys, xs = np.nonzero(al)
    low = ys >= ys.max() - 20
    foot = (int(xs[low].min()) + int(xs[low].max()) + 1) // 2
    left, top = (ANVIL_ANCHOR[0] - foot) // 2 * 2, ANVIL_ANCHOR[1] - im.height
    assert left >= 0 and left + im.width <= W, (left, im.width)
    for n in range(1, 5):
        old = np.array(Image.open(os.path.join(raw, f'codex_sparks_{n}.png')).convert('RGBA'))
        lab, k = ndimage.label(old[:, :, 3] >= 128, structure=np.ones((3, 3)))
        sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, k + 1))
        big = int(np.argmax(sizes)) + 1
        canvas = np.zeros((H, W, 4), np.uint8)
        for c in range(1, k + 1):                       # 몸통이 아닌 작은 덩어리 = 불똥
            if c == big:
                continue
            ys, xs = np.nonzero(lab == c)
            lum = old[ys, xs, :3].astype(np.int32) @ np.array([3, 6, 1]) // 10
            order = np.argsort(-lum)
            for rank, i in enumerate(order):
                col = EMBER[min(2, rank * 3 // max(1, len(order)))]
                canvas[ys[i], xs[i]] = (*col, 255)
        frame = Image.fromarray(canvas, 'RGBA')
        frame.alpha_composite(im, (left, top))
        frame.save(os.path.join(ROOT, 'assets', 'props', f'hideout_anvil_{n}.png'))
    print(f'anvil: hideout_anvil_1~4.png {W}x{H}px, 몸통 {im.width}x{im.height}px')


def main(names):
    gpal = guard_palette()
    for name in names or SETS:
        apply(name, gpal)


if __name__ == '__main__':
    main(sys.argv[1:])
