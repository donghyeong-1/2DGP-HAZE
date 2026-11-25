"""Codex T49 구역 배경(v6, 960x540 픽셀 그림)을 게임 크기로 구워 적용한다 (2026-11-25 Claude Code 검토·적용).

원본: assets/sprites/forge/backdrops_v6/far_<구역>.png (960x540, 불투명), mid_<구역>.png (1440x540, 알파 0·255, 가로 이어짐)
결과: assets/backgrounds/far_<테마>.png (1920x1080), mid_<테마>.png (2880x1080)

- 정수 2배(최근접)로만 키운다: 원본 1픽셀 = 화면 2px, 게임의 다른 그림과 같은 칸 크기다. 실행 중에는 1배로 그린다.
- 슬럼(cell)·공장(foundry)·탑(haze)은 그대로 쓴다.
- 황금방(gold)·정비방(shop)·보스방(boss)은 전용 그림이 없어 같은 판을 테마 색으로 다시 입힌다
  (gold <- cell, shop <- foundry, boss <- haze. 예전 원경도 같은 짝으로 색만 바꾼 것이었다: tools/make_world.py BG_SOURCE).
  밝기 순서를 테마 색 띠에 옮기고, 원화의 등불·결정처럼 밝고 진한 색은 테마의 빛 색으로 남긴다.

사용: python tools/apply_backdrops_v6.py
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from make_world import B, C, D, K, mix, palette  # noqa: E402

SRC = os.path.join(ROOT, 'assets', 'sprites', 'forge', 'backdrops_v6')
OUT = os.path.join(ROOT, 'assets', 'backgrounds')
DIRECT = ('cell', 'foundry', 'haze')
DERIVED = {'gold': 'cell', 'shop': 'foundry', 'boss': 'haze'}


def up2(arr):
    return np.repeat(np.repeat(arr, 2, axis=0), 2, axis=1)


def recolor(arr, theme, lift=0.0):
    """RGBA 배열의 색을 테마 색 띠로 옮긴다 (알파는 그대로). lift는 가까운 층(중경)을 조금 밝게."""
    pal = palette(theme)
    k, d, b_, c = pal[K], pal[D], pal[B], pal[C]
    rgb = arr[:, :, :3].astype(float)
    solid = arr[:, :, 3] > 0
    lum = rgb @ np.array([0.30, 0.59, 0.11])
    sat = rgb.max(axis=2) - rgb.min(axis=2)
    lamp = (lum > 120) & (sat > 70) & solid                  # 등불·결정·용광로 불빛
    body = lum[solid & ~lamp]
    lo, hi = np.percentile(body, 1), np.percentile(body, 99.5)
    t = np.clip((lum - lo) / max(hi - lo, 1), 0, 1) ** 0.9
    stops = [(0.0, mix(k, (0, 0, 0), 0.35)), (0.35, mix(k, d, 0.45 + lift)), (0.7, mix(k, d, 0.95)), (1.0, mix(d, b_, 0.55 + lift))]
    out = np.zeros_like(rgb)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        f = ((t - t0) / (t1 - t0))[..., None]
        out[m] = (np.array(c0) + (np.array(c1) - np.array(c0)) * f)[m]
    out[lamp] = mix(c, k, 0.25)
    res = arr.copy()
    res[:, :, :3] = np.round(out / 4) * 4                    # 색 단계를 조금 묶어 색 수를 줄인다
    res[~solid] = 0
    return res


def load(name):
    return np.asarray(Image.open(os.path.join(SRC, name + '.png')).convert('RGBA')).copy()


def main():
    for theme in DIRECT + tuple(DERIVED):
        src = DERIVED.get(theme, theme)
        far, mid = load('far_' + src), load('mid_' + src)
        assert far.shape[:2] == (540, 960) and mid.shape[:2] == (540, 1440), (far.shape, mid.shape)
        assert set(np.unique(mid[:, :, 3])) <= {0, 255}
        if theme in DERIVED:
            far, mid = recolor(far, theme), recolor(mid, theme, lift=0.2)
        Image.fromarray(up2(far), 'RGBA').convert('RGB').save(os.path.join(OUT, f'far_{theme}.png'))
        Image.fromarray(up2(mid), 'RGBA').save(os.path.join(OUT, f'mid_{theme}.png'))
        print('saved', theme, '<-', src)


if __name__ == '__main__':
    main()
