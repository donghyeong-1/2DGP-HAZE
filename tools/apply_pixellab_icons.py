"""무기 아이콘 넷과 아이템 아이콘(PixelLab v6)을 게임 그림으로 적용한다 (2026-11-27 I1, docs/opus/TASKS.md '4차' I1).

원본은 assets/sprites/pixellab/icons_v6/raw/ (한 장에 24x24 칸으로 여러 아이콘을 뽑은 것), 버린 시안은 raw_gen/. 기록은 icons_v6/GENERATION_LOG.md.
- 무기: weapons_a.png(seed 3)·weapons_b.png(seed 11), 96x24, 칸 순서 철파이프·쌍권총·건틀릿·사슬. 같은 프롬프트·같은 기준 그림(Q1 무기 걸이)이라
  칸마다 나은 쪽을 고른다(WEAPONS).
- 아이템: items.png("칸을 거의 채우는" 프롬프트 seed 29), 96x72, 4x3 칸 (ITEMS).

1. 칸을 잘라 알파 0/255, 몸통에서 떨어진 조각을 지운다(무기는 몸통 하나만, 아이템은 1칸 점과 칸 가장자리에 닿는 조각 = 이웃 칸에서 넘어온 끝.
   불꽃·반짝임 같은 2칸 이상 조각은 남긴다).
2. 무기 넷은 한 벌, 아이템은 한 벌로 색을 고정한다(벌마다 MAX_COLORS로 줄임).
3. 그림 둘레로 잘라 24x24 칸 가운데에 놓고 최근접 2배 -> 48x48 (지금 아이콘과 같은 크기, 쓰는 코드의 자리는 그대로).
4. 무기 넷은 외곽선을 두고 몸통 색을 밝게 들어 올린다(LIFT): 어두운 강철색이라 어두운 HUD 칸에서 묻혔다.
5. 물약(heal)은 십자가가 청록으로 나와 물약 색(초록)으로 색상만 돌린다.

그 뒤 같은 그림에서 코드로 만드는 것: python tools/make_form_icons.py (형태 = 무기 + 금별), python tools/make_fury_icon.py (분노 = 공격력을 보라로).
실행: python tools/apply_pixellab_icons.py
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_pixellab_event import load, reduce_palette  # noqa: E402
from apply_pixellab_hero import lock_palette  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'icons_v6', 'raw')
UI = os.path.join(ROOT, 'assets', 'ui')
CELL, SCALE = 24, 2
MAX_COLORS = {'weapons': 32, 'items': 48}
SPECK = {'weapons': None, 'items': 2}   # 이보다 작은 떨어진 조각은 지운다. None = 가장 큰 덩어리만 (무기는 한 덩어리다, 옆 칸에서 넘어온 조각을 지운다). 아이템은 불꽃·반짝임 2칸부터 남긴다

# 결과 이름: (raw 파일, 칸 열, 칸 줄)
WEAPONS = {
    'icon_w_pipe': ('weapons_b.png', 0, 0),        # seed 11: 걸이처럼 녹슨 갈색 파이프
    'icon_w_pistol': ('weapons_a.png', 1, 0),      # seed 3: 두 자루가 따로 읽힌다
    'icon_w_gauntlet': ('weapons_b.png', 2, 0),    # seed 11: 주먹 마디가 또렷하다
    'icon_w_chain': ('chain.png', 0, 0),           # 따로 뽑은 24x24 (seed 3): 사슬 고리가 보이고 끝에 네모 추 (시트의 사슬은 갈고리처럼 읽혔다)
}
ITEMS = {
    'icon_cap': ('items.png', 0, 0), 'icon_absorb': ('items.png', 1, 0), 'icon_steady': ('items.png', 2, 0),
    'icon_enhance': ('items.png', 3, 0), 'icon_resist': ('items.png', 0, 1), 'icon_dash': ('items.png', 1, 1),
    'icon_power': ('items.png', 2, 1), 'icon_vigor': ('items.png', 3, 1), 'icon_heal': ('items.png', 0, 2),
    'icon_shard': ('items.png', 1, 2),
}
HEAL_HUE = 0.37            # 물약 색 (120, 235, 150) 근처의 초록
LIFT = {'weapons': 0.62, 'items': 1.0}   # 몸통 색 감마(1보다 작으면 밝게, 어두운 칸일수록 많이 오른다. 외곽선은 그대로). 무기는 어두운 HUD 칸에서 읽히게
OUTLINE_LUM = 34          # 이보다 어두운 칸은 외곽선으로 보고 건드리지 않는다


def cell(raw, col, row):
    return load(os.path.join(RAW, raw))[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL].copy()


def drop_single_specks(a, keep=2):
    """8방향으로 이어진 불투명 덩어리 가운데 keep칸보다 작은 것과, 가장 큰 덩어리가 아니면서 칸 가장자리에 닿는 것
    (칸을 거의 채운 이웃 아이콘의 끝이 넘어온 조각)을 지운다. keep이 None이면 가장 큰 덩어리만 남긴다."""
    from scipy import ndimage
    lab, n = ndimage.label(a[:, :, 3] == 255, structure=np.ones((3, 3)))
    sizes = ndimage.sum(np.ones_like(lab), lab, index=range(1, n + 1))
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    out = a.copy()
    big = int(np.argmax(sizes)) + 1 if n else 0
    for k, s in enumerate(sizes, start=1):
        if k == big:
            continue
        if keep is None or s < keep or k in edge:
            out[lab == k] = 0
    return out


def centered(a):
    """그림 둘레로 잘라 24x24 칸 가운데에 (남는 칸이 홀수면 왼쪽·위로 한 칸 더)."""
    ys, xs = np.nonzero(a[:, :, 3])
    part = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = part.shape[:2]
    out = np.zeros((CELL, CELL, 4), np.uint8)
    y0, x0 = (CELL - h) // 2, (CELL - w) // 2
    out[y0:y0 + h, x0:x0 + w] = part
    return out


def heal_green(a):
    out = a.copy()
    m = out[:, :, 3] == 255
    for y, x in zip(*np.nonzero(m)):
        r, g, b = (int(v) / 255 for v in out[y, x, :3])
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        if s > 0.25 and 0.40 <= h <= 0.55:          # 청록만 초록으로
            nr, ng, nb = colorsys.hls_to_rgb(HEAL_HUE, l, s)
            out[y, x, :3] = (round(nr * 255), round(ng * 255), round(nb * 255))
    return out


def lift(a, k):
    """외곽선(아주 어두운 칸)은 두고 나머지 색에 감마 k를 건다: 명암 순서와 색상은 그대로, 밝은 면은 더 밝게(대비 유지)."""
    if k >= 1:
        return a
    out = a.copy()
    m = out[:, :, 3] == 255
    rgb = out[m][:, :3].astype(np.float32)
    lum = rgb @ np.array([0.3, 0.6, 0.1], np.float32)
    new = 255 * (rgb / 255) ** k
    out[m, :3] = np.where(lum[:, None] < OUTLINE_LUM, rgb, new).round().astype(np.uint8)
    return out


def apply_set(kind, table):
    cells = {name: drop_single_specks(cell(*spec), SPECK[kind]) for name, spec in table.items()}
    px = np.concatenate([a[a[:, :, 3] == 255][:, :3] for a in cells.values()])
    pal, counts = np.unique(px, axis=0, return_counts=True)
    pal = reduce_palette(pal, counts, MAX_COLORS[kind])
    for name, a in cells.items():
        a = lift(centered(lock_palette(a, pal)), LIFT[kind])
        if name == 'icon_heal':
            a = heal_green(a)
        im = Image.fromarray(a, 'RGBA')
        im.resize((CELL * SCALE, CELL * SCALE), Image.NEAREST).save(os.path.join(UI, name + '.png'))
        print(f'{kind}: {name}.png 48x48, {len(np.unique(a[a[:, :, 3] == 255][:, :3], axis=0))}색')


def main():
    apply_set('weapons', WEAPONS)
    apply_set('items', ITEMS)


if __name__ == '__main__':
    main()
