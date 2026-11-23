"""세계 그림(타일·소품·전경)을 v6 규격의 2배 픽셀로 바꾼다 (2026-11-23, docs/plan_v6.md).

v6은 게임 세계를 내부 해상도 960x540을 2배로 그린다(새 주인공 hero6_*가 2x2 픽셀). 코드로 그린 타일·소품은
1배 밀도라 픽셀이 더 잘다. 이 도구는 그림 크기는 그대로 두고 2x2 칸마다 원본에 실제 있던 색 하나를 골라 칠한다
(칸 평균에 가장 가까운 원본 픽셀 = 보간 없음, 새 색이 생기지 않음). 투명도도 같은 칸 단위로 0/255.
크기·기준점이 바뀌지 않아 게임 코드는 고칠 것이 없다.

원본(1배)은 처음 실행할 때 assets/concept/pixel1x_original/ 에 복사해 두고, 그 뒤로는 항상 원본에서 다시 만든다.
tools/make_world.py 등으로 원본을 다시 그렸다면 --refresh 로 원본 복사본을 새로 받는다.
실행: python tools/pixel2x.py [--refresh]
"""
import glob
import os
import shutil
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
ORIG = os.path.join(ASSETS, 'concept', 'pixel1x_original')
K = 2
# (경로, 방식) 'mean': 칸 평균을 원본 팔레트의 가장 가까운 색에 붙인다 (잔무늬가 많은 타일: 노이즈 없이 큰 색 덩어리)
#              'pick': 칸 평균에 가장 가까운 원본 픽셀 하나 (작은 소품: 윤곽·포인트 색이 살아남는다)
TARGETS = [('tiles/*.png', 'mean'), ('decor/*.png', 'pick'), ('props/*.png', 'pick'), ('props/boss/*.png', 'pick'),
           ('backgrounds/fg_*.png', 'pick')]


def to_2x(a):
    """RGBA 배열 -> 같은 크기, 2x2 칸마다 원본 픽셀 하나의 색(칸 평균에 가장 가까운 것)으로 채운 배열."""
    h, w = a.shape[:2]
    ph, pw = (h + K - 1) // K * K, (w + K - 1) // K * K
    pad = np.zeros((ph, pw, 4), np.uint8)
    pad[:h, :w] = a
    if ph > h:
        pad[h:, :w] = a[h - 1:h]                    # 홀수 크기: 끝 줄을 늘여 칸을 채운다 (잘라 버릴 부분)
    if pw > w:
        pad[:, w:] = pad[:, w - 1:w]
    cells = pad.reshape(ph // K, K, pw // K, K, 4).transpose(0, 2, 1, 3, 4).reshape(ph // K, pw // K, K * K, 4)
    f = cells.astype(np.float32)
    f[:, :, :, 3] *= 2.0                            # 투명/불투명 차이를 색 차이보다 무겁게
    mean = f.mean(axis=2, keepdims=True)
    idx = ((f - mean) ** 2).sum(axis=3).argmin(axis=2)
    pick = np.take_along_axis(cells, idx[:, :, None, None], axis=2)[:, :, 0, :]
    pick[:, :, 3] = np.where(pick[:, :, 3] >= 128, 255, 0)
    pick[pick[:, :, 3] == 0] = 0
    big = pick.repeat(K, axis=0).repeat(K, axis=1)
    return big[:h, :w]


def to_2x_mean(a):
    """2x2 칸의 불투명 픽셀 평균 색을 원본에 있던 색 중 가장 가까운 것으로. 칸의 절반 이상이 불투명하면 불투명."""
    h, w = a.shape[:2]
    ph, pw = (h + K - 1) // K * K, (w + K - 1) // K * K
    pad = np.zeros((ph, pw, 4), np.uint8)
    pad[:h, :w] = a
    if ph > h:
        pad[h:, :w] = a[h - 1:h]
    if pw > w:
        pad[:, w:] = pad[:, w - 1:w]
    c = pad.reshape(ph // K, K, pw // K, K, 4).transpose(0, 2, 1, 3, 4).reshape(ph // K, pw // K, K * K, 4).astype(np.float32)
    solid = c[:, :, :, 3] >= 128
    cnt = solid.sum(axis=2)
    rgb = (c[:, :, :, :3] * solid[..., None]).sum(axis=2) / np.maximum(cnt, 1)[..., None]
    pal = np.unique(a[a[:, :, 3] >= 128][:, :3], axis=0).astype(np.float32)
    out = np.zeros((ph // K, pw // K, 4), np.uint8)
    if len(pal):
        d = ((rgb[:, :, None, :] - pal[None, None]) ** 2).sum(axis=3)
        out[:, :, :3] = pal[d.argmin(axis=2)].astype(np.uint8)
    out[:, :, 3] = np.where(cnt * 2 >= K * K, 255, 0)
    out[out[:, :, 3] == 0] = 0
    return out.repeat(K, axis=0).repeat(K, axis=1)[:h, :w]


def main(refresh=False):
    n = 0
    for pattern, method in TARGETS:
        for path in sorted(glob.glob(os.path.join(ASSETS, pattern))):
            rel = os.path.relpath(path, ASSETS)
            keep = os.path.join(ORIG, rel)
            if refresh or not os.path.exists(keep):
                os.makedirs(os.path.dirname(keep), exist_ok=True)
                shutil.copy2(path, keep)
            src = Image.open(keep)
            had_alpha = src.mode in ('RGBA', 'LA', 'P')
            a = np.array(src.convert('RGBA'))
            out = Image.fromarray((to_2x_mean if method == 'mean' else to_2x)(a), 'RGBA')
            (out if had_alpha else out.convert('RGB')).save(path)
            n += 1
    print(f'{n}장을 2배 픽셀로 (원본: {os.path.relpath(ORIG, ROOT)})')


if __name__ == '__main__':
    main('--refresh' in sys.argv)
