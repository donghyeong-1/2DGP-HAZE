"""화면 밖 적 표시 화살표를 만든다 (v8 남겨 둔 것, 2026-11-25). code-drawn, numpy + Pillow.

논리 16x16을 정수 2배(32x32)로. 오른쪽을 가리키는 그림 하나를 그려 90도 단위로 돌려 네 방향을 만든다
(실행 중 회전 금지 규칙 때문에 미리 굽는다). 흐린 그림(_dim)은 깜빡임용이다(반투명 대신).
  assets/ui/hud_offscreen_l.png, _r, _u, _d 와 각각의 _dim

사용: python tools/make_offscreen_marker.py
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from make_icons import Canvas, K, up2  # noqa: E402  (Canvas로 모양만 채운다)

UI = os.path.join(ROOT, 'assets', 'ui')
BRIGHT = ((150, 30, 44), (236, 74, 84), (255, 168, 160))      # 그림자, 기본, 밝은 면 (적 경고 빨강)
DIM = ((70, 20, 30), (128, 44, 56), (170, 92, 96))


def arrow(colors):
    """오른쪽을 가리키는 화살표: 삼각형 머리 + 짧은 꼬리. 모양을 먼저 채우고 바깥 1칸을 외곽선으로 두른다.
    음영은 위쪽 가장자리 밝게, 아래쪽 가장자리 어둡게 (빛은 왼쪽 위)."""
    d, m, l = colors
    shape = Canvas(16, 16)
    shape.poly([(5, 2), (14, 8), (5, 14)], m)        # 머리
    shape.rect(1, 6, 5, 9, m)                         # 꼬리
    mask = shape.a[:, :, 3] > 0
    out = np.zeros((16, 16, 4), np.uint8)
    ring = np.zeros_like(mask)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ring |= np.roll(np.roll(mask, dy, 0), dx, 1)
    ring &= ~mask
    out[ring] = (*K, 255)
    out[mask] = (*m, 255)
    above = np.roll(mask, 1, 0)                       # 위 칸이 모양 안인가
    below = np.roll(mask, -1, 0)
    out[mask & ~above] = (*l, 255)                    # 위쪽 가장자리
    out[mask & ~below] = (*d, 255)                    # 아래쪽 가장자리
    return out


def main():
    for suffix, colors in (('', BRIGHT), ('_dim', DIM)):
        right = up2(arrow(colors))
        turns = {'r': right, 'u': np.rot90(right, 1), 'l': np.rot90(right, 2), 'd': np.rot90(right, 3)}
        for side, arr in turns.items():
            path = os.path.join(UI, f'hud_offscreen_{side}{suffix}.png')
            Image.fromarray(np.ascontiguousarray(arr), 'RGBA').save(path)
            print(path)


if __name__ == '__main__':
    main()
