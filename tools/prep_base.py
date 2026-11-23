"""Gemini 원화(마젠타 배경) -> PixelLab 첫 프레임으로 쓸 기준 그림 (2026-11-23, docs/plan_v6.md).

주인공 때 손으로 한 과정을 도구로 만든 것이다 (assets/sprites/pixellab/hero_v6_test/GENERATION_LOG.md 4차):
1. 마젠타 배경을 허용치로 지운다 (Gemini는 정확한 #FF00FF가 아니라 약간 다른 마젠타를 낸다).
2. 몸 경계로 잘라 목표 키(원본 px, 화면에서는 2배)로 줄이고 알파를 0/255로.
3. 정해진 캔버스 바닥 가운데에 세운다 (발 아래 여백 2px).
4. 색을 N색으로 줄이되(FASTOCTREE, 디더 없음) 팔레트 색을 원화에 실제 있던 가장 가까운 색으로 되돌린다.
   마젠타와 섞인 가장자리 색은 팔레트 후보에서 뺀다.
결과는 PixelLab 동작의 첫 프레임(또는 기준 그림)으로 그대로 쓴다. 원화 모습이 곧 게임 모습이다.

실행: python tools/prep_base.py <원화.png> <출력.png> --height 62 --canvas 96 [--colors 24] [--flip]
  --flip : 왼쪽을 보는 원화를 오른쪽을 보게 뒤집는다 (PixelLab은 side/east로 생성하고 게임이 반전한다)
"""
import argparse

import numpy as np
from PIL import Image


def magenta_mask(rgb):
    r, g, b = (rgb[:, :, i].astype(int) for i in range(3))
    return (r > 200) & (b > 190) & (g < 120) & (abs(r - b) < 70)


def fringe_mask(rgb):
    """마젠타와 섞인 가장자리 색 (팔레트 후보에서 뺀다)."""
    r, g, b = (rgb[:, :, i].astype(int) for i in range(3))
    return (r - g > 18) & (b - g > 12)


def prep(src_path, height, canvas, colors=24, flip=False, margin=2):
    im = Image.open(src_path).convert('RGB')
    rgb = np.array(im)
    alpha = np.where(magenta_mask(rgb), 0, 255).astype(np.uint8)
    rgba = Image.fromarray(np.dstack([rgb, alpha]), 'RGBA')
    rgba = rgba.crop(rgba.getbbox())
    if flip:
        rgba = rgba.transpose(Image.FLIP_LEFT_RIGHT)
    w = max(1, round(rgba.width * height / rgba.height))
    if w > canvas or height + margin > canvas:
        raise SystemExit(f'캔버스 {canvas}에 안 들어간다: {w}x{height}')
    small = np.array(rgba.resize((w, height), Image.LANCZOS))
    small[:, :, 3] = np.where(small[:, :, 3] >= 128, 255, 0)
    out = np.zeros((canvas, canvas, 4), np.uint8)
    x0, y0 = (canvas - w) // 2, canvas - margin - height
    out[y0:y0 + height, x0:x0 + w] = small
    out[out[:, :, 3] == 0] = 0
    return quantize(out, rgb[~magenta_mask(rgb) & ~fringe_mask(rgb)], colors)


def quantize(a, source_pixels, colors):
    """불투명 픽셀을 N색으로. 팔레트 각 색은 원화에 실제 있던 가장 가까운 색으로 되돌린다."""
    op = a[:, :, 3] == 255
    px = a[op][:, :3]
    q = Image.fromarray(px.reshape(1, -1, 3)).quantize(colors=colors, method=Image.Quantize.FASTOCTREE,
                                                     dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:colors * 3], np.float32).reshape(-1, 3)
    src = np.unique(source_pixels.reshape(-1, 3), axis=0).astype(np.float32)
    snapped = np.empty_like(pal)
    for i, c in enumerate(pal):                       # 원화에 있던 색으로 (메모리를 아끼려고 한 색씩)
        snapped[i] = src[((src - c) ** 2).sum(axis=1).argmin()]
    snapped = np.unique(snapped, axis=0)
    d = ((px[:, None, :].astype(np.float32) - snapped[None]) ** 2).sum(axis=2)
    out = a.copy()
    out[op, :3] = snapped[d.argmin(axis=1)].astype(np.uint8)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--height', type=int, required=True)
    ap.add_argument('--canvas', type=int, required=True)
    ap.add_argument('--colors', type=int, default=24)
    ap.add_argument('--flip', action='store_true')
    a = ap.parse_args()
    out = prep(a.src, a.height, a.canvas, a.colors, a.flip)
    Image.fromarray(out, 'RGBA').save(a.dst)
    n = len(np.unique(out[out[:, :, 3] == 255][:, :3], axis=0))
    print(f'저장 {a.dst}: 캔버스 {a.canvas}, 키 {a.height}, {n}색')


if __name__ == '__main__':
    main()
