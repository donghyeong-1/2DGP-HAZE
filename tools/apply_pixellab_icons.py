"""무기 아이콘 넷과 아이템 아이콘(PixelLab v6)을 게임 그림으로 적용한다 (2026-11-27 I1, docs/opus/TASKS.md '4차' I1).

원본은 assets/sprites/pixellab/icons_v6/raw/ (한 장에 24x24 칸으로 여러 아이콘을 뽑은 것), 버린 시안은 raw_gen/. 기록은 icons_v6/GENERATION_LOG.md.
- 무기: weapons_a.png(seed 3)·weapons_b.png(seed 11), 96x24, 칸 순서 철파이프·쌍권총·건틀릿·사슬. 같은 프롬프트·같은 기준 그림(Q1 무기 걸이)이라
  칸마다 나은 쪽을 고른다(WEAPONS).
- 아이템: items.png("칸을 거의 채우는" 프롬프트 seed 29), 96x72, 4x3 칸 (ITEMS). 흡수·결핍 방지는 items_alt.png(같은 프롬프트 seed 11),
  공격력·균열의 분노는 power_fury.png(96x24 한 줄, seed 29) (I1-fix).

1. 칸을 잘라 알파 0/255, 몸통에서 떨어진 조각을 지운다(무기는 몸통 하나만, 아이템은 1칸 점과 칸 가장자리에 닿는 조각 = 이웃 칸에서 넘어온 끝.
   불꽃·반짝임 같은 2칸 이상 조각은 남긴다).
2. 무기 넷은 한 벌, 아이템은 한 벌로 색을 고정한다(벌마다 MAX_COLORS로 줄임).
3. 그림 둘레로 잘라 24x24 칸 가운데에 놓고 최근접 2배 -> 48x48 (지금 아이콘과 같은 크기, 쓰는 코드의 자리는 그대로).
4. 무기 넷은 바깥 외곽선을 두고 안쪽 칸의 밝기를 STAND 구간으로 편다: 어두운 강철색이라 어두운 HUD 칸에서 묻혔다
   (I1 첫 적용은 감마 0.62, I1-fix에서 칸 바탕과의 명암 차이 기준으로 다시).
5. 물약(heal)은 십자가가 청록으로 나와 물약 색(초록)으로 색상만 돌린다.

그 뒤 같은 그림에서 코드로 만드는 것: python tools/make_form_icons.py (형태 = 무기 + 금별).
균열의 분노는 I1-fix부터 따로 뽑은 그림이다(tools/make_fury_icon.py는 쓰지 않는다: 공격력의 색만 바꾼 같은 그림이라 뜻이 갈리지 않았다).
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
MAX_COLORS = {'weapons': 32, 'items': 60}
SPECK = {'weapons': None, 'items': 2}   # 이보다 작은 떨어진 조각은 지운다. None = 가장 큰 덩어리만 (무기는 한 덩어리다, 옆 칸에서 넘어온 조각을 지운다). 아이템은 불꽃·반짝임 2칸부터 남긴다

# 결과 이름: (raw 파일, 칸 열, 칸 줄)
WEAPONS = {
    'icon_w_pipe': ('weapons_b.png', 0, 0),        # seed 11: 걸이처럼 녹슨 갈색 파이프
    'icon_w_pistol': ('weapons_a.png', 1, 0),      # seed 3: 두 자루가 따로 읽힌다
    'icon_w_gauntlet': ('weapons_b.png', 2, 0),    # seed 11: 주먹 마디가 또렷하다
    'icon_w_chain': ('chain.png', 0, 0),           # 따로 뽑은 24x24 (seed 3): 사슬 고리가 보이고 끝에 네모 추 (시트의 사슬은 갈고리처럼 읽혔다)
}
ITEMS = {
    'icon_cap': ('items.png', 0, 0), 'icon_absorb': ('items_alt.png', 1, 0), 'icon_steady': ('items_alt.png', 2, 0),
    'icon_enhance': ('items.png', 3, 0), 'icon_resist': ('items.png', 0, 1), 'icon_dash': ('items.png', 1, 1),
    'icon_power': ('power_fury.png', 0, 0), 'icon_vigor': ('items.png', 3, 1), 'icon_heal': ('items.png', 0, 2),
    'icon_shard': ('items.png', 1, 2), 'icon_fury': ('power_fury.png', 2, 0),
}
# I1-fix(11/27): 흡수(손이 굽은 관처럼 보였다)·결핍 방지(모래에 체크 무늬)는 같은 프롬프트의 다른 장(items_alt = items_big_s11)에서,
# 공격력(세운 파이프 + 불꽃이 풀처럼 보였다)·균열의 분노(공격력의 색만 바꾼 것이었다)는 따로 뽑은 장(power_fury, seed 29)에서:
# 공격력 = 쇠파이프가 내리쳐 터지는 주황 충격, 균열의 분노 = 보라 불꽃에 휩싸인 주먹 (효과가 다르니 모양도 다르게)
HEAL_HUE = 0.37            # 물약 색 (120, 235, 150) 근처의 초록
# 무기 몸통 밝기 (I1-fix 11/27): 바깥 외곽선(투명 칸과 맞닿은 칸)은 그대로 어둡게, 그 안쪽 칸은 밝기 순서를 지킨 채
# [STAND_LO, STAND_HI] 구간으로 펴서 올린다(안쪽의 어두운 선은 구간 아래쪽으로 남아 세부가 된다). 어두운 HUD 칸에서
# 곁눈으로 읽히게: 칸 바탕과의 명암 차이가 I1 전 코드 그림 아이콘 이상 (tests/test_i1_icons.py). I1 첫 적용은 감마 0.62였다.
STAND = {'weapons': (118, 250), 'items': None}
STAND_ICON = {'icon_w_pistol': (168, 252), 'icon_w_gauntlet': (150, 252), 'icon_w_chain': (128, 250)}   # 쌍권총·건틀릿·사슬: 바깥 외곽선 비율이 커서(I1 전 그림은 외곽선이 1px) 구간을 높게


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


def stand(a, band):
    """바깥 외곽선은 두고 안쪽 칸의 밝기를 band 구간으로 편다. 밝기만 더해 칸끼리의 색 차이는 그대로 둔다."""
    if band is None:
        return a
    from scipy import ndimage
    lo, hi = band
    out = a.copy()
    op = out[:, :, 3] == 255
    inner = ndimage.binary_erosion(op)                    # 바깥 외곽선(투명과 맞닿은 칸) = op & ~inner
    rgb = out[:, :, :3].astype(np.float32)
    lum = rgb @ np.array([0.3, 0.6, 0.1], np.float32)
    l0, l1 = float(lum[inner].min()), float(lum[inner].max())
    target = lo + (lum - l0) / max(1.0, l1 - l0) * (hi - lo)
    new = rgb + (target - lum)[:, :, None]                       # 밝기만 더한다: 칸끼리의 색 차이(녹·강철의 푸른 기)는 그대로
    for _ in range(3):                                          # 255에서 잘린 만큼은 다른 채널에 다시 나눠 목표 밝기를 맞춘다
        clipped = np.clip(new, 0, 255)
        short = target - clipped @ np.array([0.3, 0.6, 0.1], np.float32)
        room = (clipped < 255).astype(np.float32) @ np.array([0.3, 0.6, 0.1], np.float32)
        new = clipped + np.where(clipped < 255, (short / np.maximum(0.1, room))[:, :, None], 0)
    out[inner, :3] = np.clip(new[inner], 0, 255).round().astype(np.uint8)
    return out


def apply_set(kind, table):
    cells = {name: drop_single_specks(cell(*spec), SPECK[kind]) for name, spec in table.items()}
    px = np.concatenate([a[a[:, :, 3] == 255][:, :3] for a in cells.values()])
    pal, counts = np.unique(px, axis=0, return_counts=True)
    pal = reduce_palette(pal, counts, MAX_COLORS[kind])
    for name, a in cells.items():
        a = stand(centered(lock_palette(a, pal)), STAND_ICON.get(name, STAND[kind]))
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
