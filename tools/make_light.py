"""빛 번짐(블룸) 그림을 코드로 그린다 (2026-11-23 v7, docs/plan_v7.md 3). code-drawn.

INARI처럼 타격·처치 순간 하얗게 번지는 빛을 내려고, 부드러운 둥근 빛(가운데 흰색, 가장자리로 갈수록 투명)을 만든다.
**빛 층만** 반투명을 쓴다 (docs/pixel_rules.md v7 예외). 캐릭터·타일·배경은 그대로 알파 0/255.
게임은 더하기 섞기로 색을 곱해 그린다 (effects.Bloom). 반지름이 다른 두 장.

결과: assets/light/bloom_128.png, bloom_256.png
사용: python tools/make_light.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'light')


def bloom(size):
    c = (size - 1) / 2
    y, x = np.mgrid[0:size, 0:size]
    r = np.hypot(x - c, y - c) / c                      # 0 가운데 -> 1 가장자리
    core = np.clip(1 - r / 0.18, 0, 1) ** 1.5           # 작고 단단한 흰 심
    halo = np.exp(-(r / 0.42) ** 2)                     # 넓게 퍼지는 빛
    a = np.clip(0.55 * halo + core, 0, 1) * np.clip((1 - r) / 0.15, 0, 1)   # 가장자리는 0으로
    img = np.zeros((size, size, 4), np.uint8)
    img[:, :, :3] = 255
    img[:, :, 3] = np.round(a * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def main():
    os.makedirs(OUT, exist_ok=True)
    for size in (128, 256):
        bloom(size).save(os.path.join(OUT, f'bloom_{size}.png'))
        print('저장', f'assets/light/bloom_{size}.png')


if __name__ == '__main__':
    main()
