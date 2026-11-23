"""v6 새 주인공(PixelLab 62px, 캔버스 96)을 게임 그림으로 적용한다 (2026-11-23, docs/plan_v6.md).

PixelLab 원본(assets/sprites/pixellab/hero_v6_test/raw/)을 받아:
1. 알파를 0/255로 정리한다.
2. 색을 서 있는 기준 그림(still)의 색으로만 다시 칠한다 (동작마다 생기는 작은 색 차이를 없앤다).
3. 반복 동작은 머리(흰 머리 덩어리) 가로 위치를 구간 평균에 맞춰 몸통 흔들림을 없앤다.
4. 최근접 2배로 키워 assets/sprites/unified/hero6_<동작>_<번호>.png 로 쓴다 (규격 960x540을 2배, 주인공 화면 키 약 124px).
5. 세트마다 (프레임 수, 발 기준점 x, y)를 assets/sprites/unified/hero6.json 에 쓴다. src/sprites.py가 읽어 FRAMES에 더한다.

실행: python tools/apply_pixellab_hero.py
새 동작이 오면 SETS에 (원본 폴더, 쓸 프레임 번호)를 더하고 다시 실행한다.
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'hero_v6_test', 'raw')
DST = os.path.join(ROOT, 'assets', 'sprites', 'unified')
STILL = 'still62_whitehair_try1.png'
SCALE = 2

# 세트 이름: (원본 폴더 또는 파일, 쓸 프레임 번호 목록, 머리 맞추기)
SETS = {
    'hero6_idle': (STILL, None, False),                                  # 대기 동작이 오기 전까지는 서 있는 한 장
    'hero6_run': ('run62_whitehair_pixminimax', [3, 4, 5, 6, 7, 8], True),   # 0 입력, 1~2 출발, 3~8 반복 구간
}


def load(rel, n=None):
    p = os.path.join(RAW, rel) if n is None else os.path.join(RAW, rel, f'frame_{n}.png')
    a = np.array(Image.open(p).convert('RGBA'))
    a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
    a[a[:, :, 3] == 0] = 0
    return a


def palette_of(a):
    return np.unique(a[a[:, :, 3] == 255][:, :3], axis=0)


def lock_palette(a, pal):
    """불투명 픽셀을 기준 색 중 가장 가까운 색으로 다시 칠한다."""
    out = a.copy()
    m = out[:, :, 3] == 255
    px = out[m][:, :3].astype(np.int32)
    d = ((px[:, None, :] - pal[None, :, :].astype(np.int32)) ** 2).sum(axis=2)
    out[m, :3] = pal[d.argmin(axis=1)]
    return out


def hair_x(a):
    """흰 머리 덩어리의 가로 가운데 (몸통 흔들림을 재는 기준)."""
    m = (a[:, :, 3] == 255) & (a[:, :, 0] > 190) & (a[:, :, 1] > 190) & (a[:, :, 2] > 190)
    xs = np.nonzero(m)[1]
    return float(xs.mean()) if len(xs) else None


def shift_x(a, dx):
    out = np.zeros_like(a)
    if dx > 0:
        out[:, dx:] = a[:, :-dx]
    elif dx < 0:
        out[:, :dx] = a[:, -dx:]
    else:
        out = a.copy()
    return out


def foot_row(frames):
    """발 기준 y: 모든 프레임에서 가장 아래 불투명 줄의 바로 아래 (원본 px)."""
    return max(int(np.nonzero(f[:, :, 3])[0].max()) + 1 for f in frames)


def main():
    still = load(STILL)
    pal = palette_of(still)
    meta = {}
    for name, (src, numbers, align) in SETS.items():
        frames = [load(src)] if numbers is None else [load(src, n) for n in numbers]
        frames = [lock_palette(f, pal) for f in frames]
        hx = [hair_x(f) for f in frames]
        target = float(np.mean([h for h in hx if h is not None]))
        if align:
            frames = [shift_x(f, int(round(target - h))) if h is not None else f for f, h in zip(frames, hx)]
        fy = foot_row(frames)
        for i, f in enumerate(frames, 1):
            im = Image.fromarray(f, 'RGBA')
            im = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
            im.save(os.path.join(DST, f'{name}_{i}.png'))
        meta[name] = [len(frames), int(round(target * SCALE)) + 1, fy * SCALE]
        colors = len(np.unique(np.concatenate([palette_of(f) for f in frames]), axis=0))
        print(f'{name}: {len(frames)}장, 기준점 {meta[name][1:]}, 색 {colors}, 머리 x {[round(h, 1) for h in hx if h is not None]}')
    path = os.path.join(DST, 'hero6.json')
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    print('저장', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    main()
