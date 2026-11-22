"""배경 그림 속 캐릭터에만 픽셀 효과를 입힌다 (2026-11-22, 배경은 그대로 둔다).

원본 AI 그림은 assets/concept/bg_ai_original/ 에 있고, 이 도구가 캐릭터 영역(BOXES)만 진짜 픽셀로 바꿔
assets/backgrounds/ 에 쓴다. (1) 칸 안 색 편차가 가장 작은 위치로 가짜 격자를 진짜 격자에 맞춘다
(2) 칸마다 평균(보간)이 아니라 원본에 실제 있던 색 하나를 고른다 (3) 팔레트는 원본에 있던 색만으로 만들고
칸마다 그 팔레트 색으로 다시 입힌다 (4) 최근접 확대. 보간·채도 보정을 하지 않아 색이 변하지 않는다.
영역 가장자리는 FEATHER px 부드럽게 원본과 섞는다. 상자·배율·색 수는 장면마다 다르다.
실행: python tools/pixelize_chars.py [이름 ...]   (이름이 없으면 전부)
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'concept', 'bg_ai_original')
DST = os.path.join(ROOT, 'assets', 'backgrounds')
FEATHER = 24

# 이름: (상자 x0, y0, x1, y1 (위가 0), 줄이는 배율, 색 수)
BOXES = {
    'screen_title': ((250, 580, 430, 920), 3, 40),
    'screen_death': ((40, 700, 820, 940), 3, 40),
    'screen_ending': ((1470, 580, 1620, 920), 3, 40),
    'credits_1': ((270, 180, 450, 600), 3, 40),
    'boss_card_crasher': ((1250, 0, 1920, 400), 4, 48),
    'boss_card_ark': ((1380, 0, 1920, 400), 4, 48),
}


def best_offset(arr, scale):
    """가짜 격자를 진짜 격자에 맞춘다: 칸 안 색 편차가 가장 작은 (dx, dy) 시작 위치를 찾는다."""
    best, best_cost = (0, 0), None
    for dy in range(scale):
        for dx in range(scale):
            sub = arr[dy:, dx:]
            h, w = sub.shape[0] // scale * scale, sub.shape[1] // scale * scale
            cells = sub[:h, :w].reshape(h // scale, scale, w // scale, scale, 3).transpose(0, 2, 1, 3, 4)
            cost = cells.reshape(h // scale, w // scale, scale * scale, 3).var(axis=2).sum()
            if best_cost is None or cost < best_cost:
                best, best_cost = (dx, dy), cost
    return best


def cell_colors(arr, scale):
    """칸마다 원본에 실제로 있던 색 하나를 고른다 (평균 보간 없음): 칸 평균에 가장 가까운 원본 픽셀."""
    h, w = arr.shape[0] // scale, arr.shape[1] // scale
    cells = arr[:h * scale, :w * scale].reshape(h, scale, w, scale, 3).transpose(0, 2, 1, 3, 4).reshape(h, w, scale * scale, 3)
    mean = cells.mean(axis=2, keepdims=True)
    idx = ((cells.astype(np.float32) - mean) ** 2).sum(axis=3).argmin(axis=2)
    return np.take_along_axis(cells, idx[:, :, None, None], axis=2)[:, :, 0, :]


def source_palette(reg, colors):
    """원본 영역의 대표색 colors개. 양자화 결과를 가장 가까운 원본 색으로 되돌려 새 색이 없게 한다."""
    q = reg.quantize(colors=colors, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE)
    flat = q.getpalette()[:colors * 3]
    pal = np.array(flat, np.float32).reshape(-1, 3)
    src = np.unique(np.asarray(reg).reshape(-1, 3), axis=0)
    d = ((pal[:, None, :] - src[None, :, :].astype(np.float32)) ** 2).sum(axis=2)
    return src[d.argmin(axis=1)]


def pixelize_region(im, box, scale, colors, feather=FEATHER):
    im = im.convert('RGB')
    x0, y0, x1, y1 = box
    reg = im.crop(box)
    arr = np.asarray(reg)
    dx, dy = best_offset(arr, scale)
    cells = cell_colors(arr[dy:, dx:], scale)                       # 진짜 픽셀: 칸당 원본 색 하나
    pal = source_palette(reg, colors).astype(np.float32)             # 원본에 있던 색만 쓴다
    d = ((cells[:, :, None, :].astype(np.float32) - pal[None, None, :, :]) ** 2).sum(axis=3)
    snapped = pal[d.argmin(axis=2)].astype(np.uint8)                 # 칸마다 팔레트 색으로 다시 입힌다
    small = Image.fromarray(snapped)
    big = small.resize((small.width * scale, small.height * scale), Image.NEAREST)
    canvas = reg.copy()
    canvas.paste(big, (dx, dy))                                      # 격자 밖 가장자리는 원본 그대로
    w, h = reg.size
    m = np.ones((h, w), np.float32)
    for i in range(feather):
        a = i / feather
        if x0 > 0:
            m[:, i] = np.minimum(m[:, i], a)
        if x1 < im.width:
            m[:, w - 1 - i] = np.minimum(m[:, w - 1 - i], a)
        if y0 > 0:
            m[i, :] = np.minimum(m[i, :], a)
        if y1 < im.height:
            m[h - 1 - i, :] = np.minimum(m[h - 1 - i, :], a)
    out = im.copy()
    out.paste(canvas, (x0, y0), Image.fromarray((m * 255).astype('uint8')))
    return out


def main(names):
    for name in names or BOXES:
        box, scale, colors = BOXES[name]
        im = Image.open(os.path.join(SRC, name + '.png'))
        pixelize_region(im, box, scale, colors).save(os.path.join(DST, name + '.png'))
        print('저장', name)


if __name__ == '__main__':
    main(sys.argv[1:])
