"""빛 번짐(블룸) 그림을 코드로 그린다 (2026-11-23 v7, docs/plan_v7.md 3). code-drawn.

INARI처럼 타격·처치 순간 하얗게 번지는 빛을 내려고, 부드러운 둥근 빛(가운데 흰색, 가장자리로 갈수록 투명)을 만든다.
**빛 층만** 반투명을 쓴다 (docs/pixel_rules.md v7 예외). 캐릭터·타일·배경은 그대로 알파 0/255.
게임은 더하기 섞기로 색을 곱해 그린다 (effects.Bloom). 반지름이 다른 두 장.

결과: assets/light/bloom_128.png, bloom_256.png, dot_48.png, shaft_cone·shaft_straight·shaft_slant.png(O3 빛줄기)
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
    dot(48).save(os.path.join(OUT, 'dot_48.png'))       # v7 흡수 입자 둘레의 작은 빛
    print('저장', 'assets/light/dot_48.png')
    save_shafts()                                       # O3 빛줄기


def dot(size):
    """작은 부드러운 빛 점 (흡수 입자·불씨용): 흰 심 없이 넓게 퍼지는 빛만."""
    c = (size - 1) / 2
    y, x = np.mgrid[0:size, 0:size]
    r = np.hypot(x - c, y - c) / c
    a = np.exp(-(r / 0.45) ** 2) * np.clip((1 - r) / 0.2, 0, 1)
    img = np.zeros((size, size, 4), np.uint8)
    img[:, :, :3] = 255
    img[:, :, 3] = np.round(a * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


# ----- 빛줄기 (O3, 2026-11-26, src/light_shafts.py) -----
# 위가 좁고 아래로 퍼지며 옅어지는 부드러운 띠. 결(가는 세로 줄무늬)이 살짝 있어 먼지 낀 빛처럼 보인다. 게임이 색을 곱해 더한다.
def shaft(w, h, ax, dx_total, top_w, bottom_w, rays=5, seed=0):
    """ax: 위쪽 기준점의 가로 위치, dx_total: 아래 끝까지 옆으로 가는 거리(기운 빛줄기), top_w·bottom_w: 위·아래 폭."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    v = y / (h - 1)                                     # 0 위 -> 1 아래
    cx = ax + dx_total * v
    half = (top_w + (bottom_w - top_w) * v) / 2
    d = (x - cx) / np.maximum(half, 0.5)                # -1 ~ 1이 빛 안
    across = np.clip(1 - np.abs(d), 0, 1) ** 1.4        # 가장자리로 갈수록 부드럽게
    rng = np.random.default_rng(seed)
    streak = np.ones_like(d)
    for _ in range(rays):                               # 빛 안의 결: 축을 따라 가는 옅은 줄 몇 개
        off, k = rng.uniform(-0.7, 0.7), rng.uniform(0.15, 0.3)
        streak += k * np.exp(-((d - off) / 0.12) ** 2)
    down = np.clip(1 - v, 0, 1) ** 1.2 * np.clip(v / 0.06, 0, 1)   # 위쪽 끝은 짧게 켜지고 아래로 옅어진다
    a = np.clip(across * down * streak, 0, 1)
    img = np.zeros((h, w, 4), np.uint8)
    img[:, :, :3] = 255
    img[:, :, 3] = np.round(a * 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


SHAFTS = {   # 이름 -> (폭, 높이, 위쪽 기준점, 옆으로 가는 거리, 위 폭, 아래 폭, 시드). src/light_shafts.KINDS의 anchor와 같다
    'shaft_cone': (96, 200, 48, 0, 8, 92, 1),
    'shaft_straight': (64, 260, 32, 0, 18, 58, 2),
    'shaft_slant': (150, 260, 20, 100, 16, 52, 3),
}


def save_shafts():
    for name, (w, h, ax, dx, tw, bw, seed) in SHAFTS.items():
        shaft(w, h, ax, dx, tw, bw, seed=seed).save(os.path.join(OUT, name + '.png'))
        print('저장', f'assets/light/{name}.png')


if __name__ == '__main__':
    main()
