"""화면 분위기 그림을 코드로 그린다 (numpy + Pillow, code-drawn, 자체 제작). 2026-11-21 퀄리티 계획 2-2.

  assets/ui/vignette.png          1920x1080 가장자리 어둡게. 짙은 남색 한 색, 알파는 켜짐·꺼짐(픽셀 규칙)이고
                                  가장자리로 갈수록 점묘(베이어 4x4, 2px 칸)가 촘촘해진다. 게임이 opacify로 옅게 그린다.
  assets/backgrounds/fog_strip.png 960x300 가로로 이어지는 안개 띠 (흐린 청록 두 톤, 점묘). 게임이 두 겹으로 흘려 그린다.
  assets/ui/wipe_01~15.png        128x128 화면 전환 타일 (계획 4-3, 베이어 4x4를 8px 칸으로, 번호/16 만큼 켜짐).
사용: python tools/make_atmosphere.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
INK = (6, 8, 18)
FOG = ((150, 215, 228), (110, 170, 196))
W, H = 1920, 1080
CELL = 2                        # 점묘 칸 크기(px): 1px 점은 화면에서 너무 자글거린다


def dither(density, w, h):
    """밀도(0~1) 배열 -> 켜짐 여부. 칸(CELL) 단위 베이어 점묘."""
    ys, xs = np.mgrid[0:h, 0:w]
    th = BAYER[(ys // CELL) % 4, (xs // CELL) % 4]
    return density > th


def vignette():
    ys, xs = np.mgrid[0:H, 0:W].astype(float)
    cx, cy = (xs + 0.5) / W * 2 - 1, (ys + 0.5) / H * 2 - 1                 # -1 ~ 1
    r = np.sqrt((cx * 1.0) ** 2 + (cy * 1.15) ** 2)                         # 위아래가 조금 더 빨리 어두워진다
    density = np.clip((r - 0.62) / 0.75, 0, 1) ** 1.5
    density = density.reshape(H // CELL, CELL, W // CELL, CELL)[:, 0, :, 0].repeat(CELL, 0).repeat(CELL, 1)
    on = dither(density, W, H)
    a = np.zeros((H, W, 4), np.uint8)
    a[on] = (*INK, 255)
    return Image.fromarray(a, 'RGBA')


def smooth_noise(w, h, cells_x, cells_y, seed):
    """가로로 끊김 없이 이어지는 값 노이즈 (0~1)."""
    rng = np.random.RandomState(seed)
    g = rng.rand(cells_y + 1, cells_x)
    g = np.concatenate([g, g[:, :1]], axis=1)                              # 오른쪽 끝 = 왼쪽 끝
    ys = np.linspace(0, cells_y, h, endpoint=False)
    xs = np.linspace(0, cells_x, w, endpoint=False)
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[y0][:, x0], g[y0][:, x0 + 1]
    c, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def fog_strip():
    w, h = 960, 300
    n = 0.6 * smooth_noise(w, h, 6, 3, 4) + 0.4 * smooth_noise(w, h, 15, 6, 9)
    fall = np.clip(np.linspace(1.0, -0.2, h), 0, 1)[:, None] ** 0.8 * np.clip(np.linspace(0, 4, h), 0, 1)[:, None]
    density = np.clip((n - 0.42) * 1.6, 0, 1) * fall * 0.55                 # 아래가 짙고 위로 옅어진다, 성기게
    on = dither(density, w, h)
    dense = dither(np.clip(density * 1.6 - 0.35, 0, 1), w, h)
    a = np.zeros((h, w, 4), np.uint8)
    a[on] = (*FOG[1], 255)
    a[on & dense] = (*FOG[0], 255)
    return Image.fromarray(a, 'RGBA')


def wipe(level, size=128, cell=8):
    """화면 전환 타일: 베이어 4x4 문턱값을 cell px 칸으로, level/16 만큼의 칸을 켠다 (타일이 이어 붙는다)."""
    ys, xs = np.mgrid[0:size, 0:size]
    th = BAYER[(ys // cell) % 4, (xs // cell) % 4]
    on = th < level / 16.0
    a = np.zeros((size, size, 4), np.uint8)
    a[on] = (*INK, 255)
    return Image.fromarray(a, 'RGBA')


def main():
    for lv in range(1, 16):
        wipe(lv).save(os.path.join(ROOT, 'assets', 'ui', f'wipe_{lv:02d}.png'))
    vignette().save(os.path.join(ROOT, 'assets', 'ui', 'vignette.png'))
    fog_strip().save(os.path.join(ROOT, 'assets', 'backgrounds', 'fog_strip.png'))
    print('saved vignette.png, fog_strip.png')


if __name__ == '__main__':
    main()
