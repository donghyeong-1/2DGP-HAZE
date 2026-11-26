"""UI 3차 '교도소 철판' 타이틀 그림을 굽는다 (2026-11-26, docs/opus/TASKS.md 3차 O8-3). code-drawn + 게임 그림.

1. 배경 assets/backgrounds/title_plate.png (1920x1080): 새 일러스트를 만들지 않고 게임 속 슬럼 그림을 겹친다.
   원경 far_cell + 중경 mid_cell(가운데 1920) + 왼쪽 아래 주인공이 설 벽 덩어리(타일 세트 tile_set_cell의 벽 칸)
   + 아래쪽 안개(2px 점묘 띠, 반투명 없음). 비와 주인공은 title_mode가 실행 중에 그린다(게임의 날씨 코드·대기 동작).
2. 로고 assets/ui/up_logo_title.png: 철판(리벳·긁힘) 위에 스텐실로 찍은 'HAZE'(굵은 도트 글자, 스텐실 다리)와
   '헤이즈'(Galmuri14 2배), 양옆 경고 줄무늬. 광택·그라데이션 없음. 960x540 격자(1점 = 화면 2px)에 찍고 2배로 저장.

사용: python tools/make_title_plate.py
"""
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import make_ui_plate as mp  # noqa: E402

BG = os.path.join(ROOT, 'assets', 'backgrounds')
W, H = 1920, 1080
T = 60                                     # 타일 한 칸 (config.TILE)
LEDGE_COLS, LEDGE_ROWS = 9, 3             # 주인공이 서는 벽 덩어리 (왼쪽 아래)
FOG = (8, 12, 22)
FAR_DROP = 280                             # 원경을 아래로 내리는 거리 (위 빈 곳은 원경 맨 윗줄의 하늘색)


def wall_cell(atlas, mask, quad):
    """타일 세트의 벽 칸: 열 = 드러난 면 마스크(1 위, 2 오른쪽, 4 아래, 8 왼쪽), 줄 0~3 = 석조 무늬 사분면 (room.py와 같다)."""
    return atlas.crop((mask * T, quad * T, mask * T + T, quad * T + T))


def background():
    far = Image.open(os.path.join(BG, 'far_cell.png')).convert('RGBA')
    mid = Image.open(os.path.join(BG, 'mid_cell.png')).convert('RGBA')
    img = Image.new('RGBA', (W, H), tuple(int(v) for v in np.array(far)[:6].reshape(-1, 4).mean(0)[:3]) + (255,))
    img.alpha_composite(far.crop((0, 0, W, H - FAR_DROP)), (0, FAR_DROP))    # 도시가 화면 가운데에 오게 원경을 내린다
    off = (mid.width - W) // 2
    img.alpha_composite(mid.crop((off, 0, off + W, H)))
    # 아래쪽 안개: 위에서 아래로 짙어지는 2px 점묘 띠 (단계 4개, 점 비율 1/4 -> 4/4)
    a = np.array(img)
    for k, top in enumerate((820, 900, 970, 1030)):
        for y in range(top, H, 2):
            for x in range(0, W, 2):
                cell = ((x // 2) % 2) + 2 * ((y // 2) % 2)
                if cell <= k:
                    a[y:y + 2, x:x + 2, :3] = FOG
    img = Image.fromarray(a, 'RGBA')
    # 벽 덩어리 (왼쪽 아래): 맨 윗줄은 위가 드러난 칸, 오른쪽 끝 열은 오른쪽이 드러난 칸
    atlas = Image.open(os.path.join(ROOT, 'assets', 'tiles', 'tile_set_cell.png')).convert('RGBA')
    for r in range(LEDGE_ROWS):
        for c in range(LEDGE_COLS):
            mask = (1 if r == 0 else 0) | (2 if c == LEDGE_COLS - 1 else 0)
            quad = (c % 2) + 2 * (r % 2)
            img.alpha_composite(wall_cell(atlas, mask, quad), (c * T, H - (r + 1) * T))
    return img.convert('RGB')


# ----- 로고 -----
# 굵은 도트 글자 (8x9 칸, 획 굵기 2칸, 칸 하나 = 1배 CELL점). '-'는 스텐실 다리 (칠하지 않는 칸: 글자 하나에 한두 곳)
GLYPHS = {
    'H': ['XX....XX', 'XX....XX', 'XX....XX', 'XX....XX', 'XX-XXXXX', 'XX....XX', 'XX....XX', 'XX....XX', 'XX....XX'],
    'A': ['..XXXX..', '.XXXXXX.', 'XX....XX', 'XX....XX', 'XXXX-XXX', 'XX....XX', 'XX....XX', 'XX....XX', 'XX....XX'],
    'Z': ['XXXXXXXX', 'XXXXX-XX', '.....XX.', '....XX..', '...XX...', '..XX....', '.XX.....', 'XX-XXXXX', 'XXXXXXXX'],
    'E': ['XXXXXXXX', 'XXXXXX-X', 'XX......', 'XX......', 'XXXX-XX.', 'XX......', 'XX......', 'XXXXXX-X', 'XXXXXXXX'],
}
CELL = 5                                   # 1배 점 (화면 10px)
GAP = 2                                    # 글자 사이 칸


def stencil_word(p, word, x0, y0, color, shadow, rng):
    """굵은 도트 글자를 스텐실로 찍는다: 'X' 칸은 칠, '-' 칸은 스텐실 다리(비움). 그림자 1점, 칠이 벗겨진 점 몇 개."""
    for i, ch in enumerate(word):
        rows = GLYPHS[ch]
        gx = x0 + i * (8 + GAP) * CELL
        for layer, (dx, c) in enumerate(((1, shadow), (0, color))):
            for r, line in enumerate(rows):
                for col, on in enumerate(line):
                    if on == 'X':
                        p.rect(gx + col * CELL + dx, y0 + r * CELL + dx, CELL, CELL, c)
        for _ in range(7):                                   # 칠이 벗겨진 점 (글자당 일곱)
            r, col = rng.randrange(9), rng.randrange(8)
            if rows[r][col] == 'X':
                p.put(gx + col * CELL + rng.randrange(CELL), y0 + r * CELL + rng.randrange(CELL), mp.MID)


def logo():
    mp.LOOK = 'worn'
    rng = random.Random(9)
    w, h = 236, 100
    p = mp.Pix(w, h)
    mp.plate(p, 0, 0, w, h, cut=6, bevel=2)
    mp.corner_rivets(p, 0, 0, w, h, inset=5)
    for x in range(36, w - 36, 40):                          # 위아래 변 리벳
        mp.rivet(p, x, 4)
        mp.rivet(p, x, h - 6)
    mp.scuff(p, 10, 12, w - 20, h - 24, rng, n=4)
    word_w = (4 * (8 + GAP) - GAP) * CELL
    stencil_word(p, 'HAZE', (w - word_w) // 2, 12, mp.WHITE, mp.LO, rng)
    # '헤이즈': Galmuri14를 2배(28점)로 찍는다 (도트 글꼴의 정수 배)
    font = ImageFont.truetype(os.path.join(ROOT, 'assets', 'fonts', 'Galmuri14.ttf'), 28)
    tmp = Image.new('L', (200, 40), 0)
    ImageDraw.Draw(tmp).text((0, 0), '헤이즈', fill=255, font=font)
    m = np.array(tmp) > 127
    ys, xs = np.nonzero(m)
    tw = xs.max() - xs.min() + 1
    tx, ty = (w - tw) // 2 - xs.min(), 12 + 9 * CELL + 8 - ys.min()
    for y, x in zip(ys, xs):
        p.put(int(x + tx + 1), int(y + ty + 1), mp.LO)
    for y, x in zip(ys, xs):
        p.put(int(x + tx), int(y + ty), mp.YEL)
    # 양옆 경고 줄무늬 띠 (글자 줄 높이)
    sy0, sy1 = ty + ys.min() + 2, ty + ys.max() - 1
    for x0 in (16, w - 16 - 50):
        for y in range(sy0, sy1):
            for x in range(x0, x0 + 50):
                p.put(x, y, mp.YEL if ((x + y) // 4) % 2 == 0 else mp.LO)
        for x in range(x0 - 1, x0 + 51):
            p.put(x, sy0 - 1, mp.EDGE)
            p.put(x, sy1, mp.EDGE)
    return p


def main():
    background().save(os.path.join(BG, 'title_plate.png'))
    print('저장 assets/backgrounds/title_plate.png')
    logo().save('logo_title', os.path.join(ROOT, 'assets', 'ui'))
    print('저장 assets/ui/up_logo_title.png')


if __name__ == '__main__':
    main()
