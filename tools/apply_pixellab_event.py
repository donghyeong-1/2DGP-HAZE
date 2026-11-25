"""이벤트 방의 NPC·소품(PixelLab v6)을 게임 그림으로 적용한다 (2026-11-25).

게임 화면에서 캐릭터 옆에 서는 도트 그림은 PixelLab으로 만든다(AGENTS.md 역할 분담, docs/DECISIONS.md 2026-11-25).
원본은 assets/sprites/pixellab/<이름>_v6/raw/ (base.png = 고른 시안, 동작 폴더 frame_N.png). 생성 기록은 각 폴더의 GENERATION_LOG.md.

1. 알파 0/255, 색은 base(소품은 base + 마른 그림)의 색으로만 다시 칠한다. 색이 MAX_COLORS를 넘으면 가까운 색끼리 합친다
   (tests/test_pixel_assets.py: UI 그림은 64색 이하).
2. 모든 장을 같은 틀로 자른다: 가로 가운데 = 몸(아래 절반) 중심, 아래 가장자리 = 바닥 줄. 게임은 그림의 가운데 아래를 기준점으로 그린다.
3. 최근접 2배로 키워 쓴다(도트 2px).
   - 떠돌이 죄수: assets/sprites/unified/npc_drifter_idle_1~2.png (src/npc.py)
   - 헤이즈 샘: assets/ui/event_spring_1~4.png(물결), event_spring_dry.png(마름) (src/events.py Spot)

실행: python tools/apply_pixellab_event.py
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_pixellab_hero import lock_palette  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIX = os.path.join(ROOT, 'assets', 'sprites', 'pixellab')
SCALE = 2
MAX_COLORS = 48

# 이름: (원본 폴더, 장 목록(raw 아래 경로), 색 기준으로 삼는 그림들, 결과 폴더, 결과 이름들)
SETS = {
    # 숨쉬기 5장 중 0(= base)·2번(어깨가 올라가고 결정이 뜬다). src/npc.py가 0.6초마다 번갈아 그린다
    'drifter': ('drifter_v6', ['idle/frame_0.png', 'idle/frame_2.png'], ['base.png'],
                ('sprites', 'unified'), ['npc_drifter_idle_1', 'npc_drifter_idle_2']),
    # 물결 0~3번(2~3번에 관에서 방울이 떨어지고 결정이 반짝인다) + 마른 그림
    'spring': ('spring_v6', ['ripple/frame_0.png', 'ripple/frame_1.png', 'ripple/frame_2.png', 'ripple/frame_3.png', 'dry.png'],
               ['base.png', 'dry.png'], ('ui',),
               ['event_spring_1', 'event_spring_2', 'event_spring_3', 'event_spring_4', 'event_spring_dry']),
}


def load(path):
    a = np.array(Image.open(path).convert('RGBA'))
    a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
    a[a[:, :, 3] == 0] = 0
    return a


def reduce_palette(pal, counts, limit):
    """색이 limit개가 될 때까지 가장 가까운 두 색을 합친다(많이 쓰인 쪽 색을 남긴다)."""
    pal, counts = [tuple(int(v) for v in c) for c in pal], list(counts)
    while len(pal) > limit:
        arr = np.array(pal, np.int32)
        d = ((arr[:, None, :] - arr[None, :, :]) ** 2).sum(axis=2)
        d[np.arange(len(pal)), np.arange(len(pal))] = 1 << 30
        i, j = np.unravel_index(d.argmin(), d.shape)
        keep, drop = (i, j) if counts[i] >= counts[j] else (j, i)
        counts[keep] += counts[drop]
        del pal[drop], counts[drop]
    return np.array(pal, np.uint8)


def body_center(a):
    """아래 절반(다리·그릇) 불투명 칸의 가로 가운데. 내민 손·결정·관에 끌려가지 않는다."""
    ys, xs = np.nonzero(a[:, :, 3])
    low = ys >= (ys.min() + ys.max()) / 2
    return (int(xs[low].min()) + int(xs[low].max()) + 1) / 2


def apply(name):
    folder, rels, pal_src, dst, outs = SETS[name]
    raw = os.path.join(PIX, folder, 'raw')
    srcs = [load(os.path.join(raw, p)) for p in pal_src]
    px = np.concatenate([a[a[:, :, 3] == 255][:, :3] for a in srcs])
    pal, counts = np.unique(px, axis=0, return_counts=True)
    pal = reduce_palette(pal, counts, MAX_COLORS)
    frames = [lock_palette(load(os.path.join(raw, r)), pal) for r in rels]
    base = load(os.path.join(raw, 'base.png'))
    cx = int(round(body_center(base)))
    ys, xs = np.nonzero(np.maximum.reduce([f[:, :, 3] for f in frames]))
    half = max(cx - int(xs.min()), int(xs.max()) + 1 - cx) + 1      # 1칸 여백
    top, foot = int(ys.min()) - 1, int(np.nonzero(base[:, :, 3])[0].max()) + 1
    out_dir = os.path.join(ROOT, 'assets', *dst)
    for f, out in zip(frames, outs):
        canvas = np.zeros((foot - top, half * 2, 4), np.uint8)
        x0, x1 = max(0, cx - half), min(f.shape[1], cx + half)
        canvas[:, x0 - (cx - half):x1 - (cx - half)] = f[top:foot, x0:x1]
        im = Image.fromarray(canvas, 'RGBA')
        im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(os.path.join(out_dir, out + '.png'))
    print(f'{name}: {len(outs)}장, {half * 2 * SCALE}x{(foot - top) * SCALE}px -> assets/{"/".join(dst)}/')


def main(names):
    for name in names or SETS:
        apply(name)


if __name__ == '__main__':
    main(sys.argv[1:])
