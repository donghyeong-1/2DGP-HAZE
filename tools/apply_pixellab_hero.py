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

# 세트 이름: (프레임 목록 [(원본 폴더, 번호)], 맞추기)
#   'hair': 반복 동작. 머리 가로 위치를 구간 평균에 맞춘다(몸통 흔들림 제거), 기준점 x도 그 평균
#   'air' : 공중 동작. 머리 가로 위치를 서 있는 그림에 맞추고, 몸 아래 끝을 발 줄에 맞춘다
#   'none': 원본 위치 그대로 (0번이 서 있는 그림이라 같은 좌표계다. 공격·피격·사망처럼 발이 땅에 붙은 동작)
# 번호를 고른 이유는 shots/pixellab_test/all62_review.png 참고. 게임 쪽 상태 연결은 src/sprites.py SKIN.
def _f(src, numbers):
    return [(src, n) for n in numbers]


RUN = 'run62_whitehair_pixminimax'
SETS = {
    'hero6_idle': (_f('idle62', range(1, 9)), 'hair'),                    # 0번 = 8번(반복)이라 1~8
    'hero6_run': (_f(RUN, [3, 4, 5, 6, 7, 8]), 'hair'),                   # 0 입력, 1~2 출발, 3~8 반복 구간
    # 출발 1·2, 멈춤 3·4(착지의 무릎 굽힘을 제동으로), 방향 전환 5
    'hero6_run_trans': (_f(RUN, [1, 2]) + _f('land62', [2, 3]) + _f(RUN, [2]), 'none'),
    'hero6_jump': (_f('jump62', [1, 3, 6, 8]), 'air'),                    # 게임은 2 상승·3 정점·4 낙하를 쓴다
    'hero6_dash': (_f('dash62', [5, 7]), 'none'),
    'hero6_swing_side': (_f('attack162', [2, 3, 4, 5, 6]), 'none'),      # 3번째가 타격(청록 궤적)
    'hero6_swing_up': (_f('attack262', [3, 4, 5, 6, 7]), 'none'),        # 올려치기
    'hero6_swing_down': (_f('attack362', [2, 3, 4, 5, 6]), 'none'),      # 내려찍기
    'hero6_s2rise': (_f('attack262', [4, 5, 6]), 'none'),
    'hero6_s2slam': (_f('attack362', [3, 4, 5]), 'none'),
    'hero6_plunge': (_f('attack362', [4, 5]), 'none'),
    'hero6_hurt': (_f('hurt62', [2, 3]), 'none'),
    'hero6_death': (_f('death62', [3, 5, 8]), 'none'),
}


def remove_white_arcs(a):
    """몸과 떨어진 흰 궤적(테두리 없는 밝은 색만으로 된 덩어리)을 지운다. 효과는 게임이 코드로 따로 그린다.
    흰 머리는 검은 테두리와 붙어 있어 남는다. 청록 궤적은 어두운 색이 섞여 있어 남는다."""
    from scipy import ndimage
    opaque = a[:, :, 3] == 255
    lab, n = ndimage.label(opaque, structure=np.ones((3, 3)))
    light = opaque & (a[:, :, :3].min(axis=2) > 200)
    out = a.copy()
    for k in range(1, n + 1):
        comp = lab == k
        if (light[comp]).all():
            out[comp] = 0
    return out


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
    still_hair = hair_x(still)
    still_foot = foot_row([still])
    meta = {}
    for name, (frames_src, align) in SETS.items():
        frames = [lock_palette(remove_white_arcs(load(src, n)), pal) for src, n in frames_src]
        hx = [hair_x(f) for f in frames]
        anchor_x = still_hair
        if align == 'hair':
            anchor_x = float(np.mean([h for h in hx if h is not None]))
            frames = [shift_x(f, int(round(anchor_x - h))) if h is not None else f for f, h in zip(frames, hx)]
        elif align == 'air':
            frames = [shift_x(f, int(round(still_hair - h))) if h is not None else f for f, h in zip(frames, hx)]
            frames = [np.roll(f, still_foot - foot_row([f]), axis=0) for f in frames]
        for i, f in enumerate(frames, 1):
            im = Image.fromarray(f, 'RGBA')
            im = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
            im.save(os.path.join(DST, f'{name}_{i}.png'))
        meta[name] = [len(frames), int(round(anchor_x * SCALE)) + 1, still_foot * SCALE]
        colors = len(np.unique(np.concatenate([palette_of(f) for f in frames]), axis=0))
        print(f'{name}: {len(frames)}장, 기준점 {meta[name][1:]}, 색 {colors}')
    path = os.path.join(DST, 'hero6.json')
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    print('저장', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    main()
