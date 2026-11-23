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
STILL = 'base96.png'          # 사용자가 고른 그림(Gemini 원화를 62px로 줄여 24색으로 정리) = 색·눈 기준
SCALE = 2

# 세트 이름: (프레임 목록 [(원본 폴더, 번호)], 맞추기)
#   'hair': 반복 동작. 머리 가로 위치를 구간 평균에 맞춘다(몸통 흔들림 제거), 기준점 x도 그 평균
#   'air' : 공중 동작. 머리 가로 위치를 서 있는 그림에 맞추고, 몸 아래 끝을 발 줄에 맞춘다
#   'none': 원본 위치 그대로 (0번이 서 있는 그림이라 같은 좌표계다. 공격·피격·사망처럼 발이 땅에 붙은 동작)
# 번호를 고른 이유는 shots/pixellab_test/all62_review.png 참고. 게임 쪽 상태 연결은 src/sprites.py SKIN.
def _f(src, numbers):
    return [(src, n) for n in numbers]


# v2 (2026-11-23 결제 후): base96을 첫 프레임으로 다시 만든 동작. skeleton 폴더는 0번부터 생성 프레임이다.
# 번호를 고른 이유는 shots/pixellab_test/all96_review.png 참고. 휘두르기는 게임의 타격 순간(3번째)에 타격 프레임이 오게.
SETS = {
    'hero6_idle': (_f('idle96', range(1, 9)), 'hair'),                     # 0번 = 8번(반복)이라 1~8
    'hero6_run': (_f('run96', range(0, 8)), 'hair'),
    # 출발 1·2, 멈춤 3·4(착지의 무릎 굽힘), 방향 전환 5
    'hero6_run_trans': (_f('run_start96', [1, 2]) + _f('land96', [0, 1]) + _f('run_start96', [0]), 'none'),
    'hero6_jump': (_f('jump96', [0, 2, 4, 5]), 'air'),                     # 게임은 2 상승·3 정점·4 낙하를 쓴다
    'hero6_dash': (_f('dash96', [2, 3]), 'none'),
    # 공격 v3 (2026-11-24, plan_v7 8절, 배치는 shots/pixellab_test/v3_*.png 검토). 휘두르기 세트는 5장:
    # 젖힘 -> 휘두르는 중 -> 타격(3번째) -> 마무리 -> 회수. 게임의 SWING_STYLE_PHASES가 이 순서로 고른다.
    'hero6_swing_side': (_f('v3_combo5', [1, 3, 4, 5, 6]), 'none'),       # 땅 1타: 뒤로 당겼다 수평으로 (가로 베기)
    'hero6_swing_side2': (_f('v3_g2', [3, 4, 5, 6, 7]), 'none'),          # 땅 2타: 머리 위에서 앞 아래로 사선 반원
    'hero6_swing_side3': (_f('v3_up', [2, 3, 4, 5, 7]), 'none'),          # 땅 3타(마무리): 올려베기
    'hero6_swing_up': (_f('v3_up', [2, 3, 4, 5, 7]), 'none'),             # 위·앞 위로 겨눔
    'hero6_swing_down': (_f('v3_low', [1, 2, 3, 4, 6]), 'none'),          # 아래·앞 아래로 겨눔: 발밑 훑기
    'hero6_air1': (_f('v3_air1', [2, 3, 4, 5, 6]), 'none'),               # 공중 1타: 가로 베기
    'hero6_air2': (_f('v3_air2', [3, 4, 5, 5, 7]), 'none'),               # 공중 2타: 반원 (6번은 파이프에 초승달이 붙어 5번을 한 번 더)
    'hero6_airup': (_f('v3_air_up', [2, 3, 4, 5, 6]), 'none'),            # 공중에서 위로 겨눔
    'hero6_dashcut': (_f('v3_dash', [1, 2, 3, 4, 5]), 'none'),            # 대시 평타: 낮은 돌진 가로 베기
    'hero6_e1': (_f('v3_e1', [1, 1, 4, 5, 6]), 'none'),                   # E 1단계: X베기 (초승달이 붙은 2·3·7번은 뺀다)
    'hero6_s2rise': (_f('v3_e2_rise', [2, 4, 6]), 'none'),                # E 2단계 첫 타: 웅크림 -> 올려베기 -> 뛰어오름 (기존과 같은 3장)
    'hero6_s2slam': (_f('v3_e2_slam', [2, 3, 5]), 'none'),                # E 2단계 둘째 타: 머리 위 -> 내림 -> 바닥 타격(머문다)
    'hero6_plunge': (_f('v3_air_down2', [1, 4]), 'none'),                 # 내려찍기: 머리 위로 듦 -> 파이프를 수직 아래로 내리꽂음
    'hero6_hurt': (_f('hurt96', [0, 1]), 'none'),
    'hero6_death': (_f('death96', [2, 4, 7]), 'none'),
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


def remove_loose_grey(a, min_size=4):
    """몸과 떨어진 회색 덩어리(생성 모델이 그린 회색 초승달·궤적 조각)를 지운다.
    가장 큰 덩어리(몸)에 붙은 것은 남기고, 떨어진 것 중 채도가 낮은(회색) 덩어리만 지운다. 목도리 끝 청록 조각은 남는다."""
    from scipy import ndimage
    opaque = a[:, :, 3] == 255
    lab, n = ndimage.label(opaque, structure=np.ones((3, 3)))
    if n <= 1:
        return a
    sizes = ndimage.sum(opaque, lab, range(1, n + 1))
    body = int(np.argmax(sizes)) + 1
    rgb = a[:, :, :3].astype(int)
    grey = (rgb.max(axis=2) - rgb.min(axis=2)) < 40
    out = a.copy()
    for k in range(1, n + 1):
        if k == body:
            continue
        comp = lab == k
        if comp.sum() >= min_size and grey[comp].mean() > 0.8:
            out[comp] = 0
    return out


HEAD_LIGHT = 140          # 흰 머리·옆얼굴로 보는 밝기 (RGB 최솟값)
HEAD_ROWS = 9             # 머리 꼭대기부터 이만큼 줄 안에서 머리 오른쪽 끝을 잰다


def head_ref(a):
    """머리 기준점: (밝은 덩어리 맨 위 줄, 그 아래 HEAD_ROWS줄 안의 오른쪽 끝 x). 오른쪽을 보는 그림 기준."""
    light = (a[:, :, 3] == 255) & (a[:, :, :3].min(axis=2) > HEAD_LIGHT)
    ys = np.nonzero(light.any(axis=1))[0]
    if not len(ys):
        return None
    top = int(ys[0])
    xs = np.nonzero(light[top:top + HEAD_ROWS].any(axis=0))[0]
    return top, int(xs.max())


def find_eye(base):
    """기준 그림에서 눈 픽셀(머리 안의 청록 계열 한 점)과 머리 기준점으로부터의 거리를 찾는다."""
    top, right = head_ref(base)
    rgb = base[:, :, :3].astype(int)
    tealish = (base[:, :, 3] == 255) & (rgb[:, :, 1] - rgb[:, :, 0] > 25) & (rgb[:, :, 2] - rgb[:, :, 0] > 25)
    region = np.zeros_like(tealish)
    region[top:top + HEAD_ROWS + 4, right - 8:right + 1] = True
    ys, xs = np.nonzero(tealish & region)
    if not len(ys):
        return None
    y, x = int(ys[0]), int(xs[0])
    return y - top, x - right, base[y, x].copy()


def restore_eye(a, eye):
    """생성 결과에서 눈이 사라지거나 검게 바뀐 프레임에 기준 그림의 눈을 같은 자리(머리 기준)에 다시 찍는다.
    그 자리가 얼굴·머리처럼 밝거나 검은 눈구멍일 때만 찍는다 (머리가 크게 가려진 프레임은 건드리지 않는다)."""
    if eye is None:
        return a
    ref = head_ref(a)
    if ref is None:
        return a
    dy, dx, color = eye
    y, x = ref[0] + dy, ref[1] + dx
    if not (0 <= y < a.shape[0] and 0 <= x < a.shape[1]) or a[y, x, 3] != 255:
        return a
    out = a.copy()
    region = out[max(0, y - 2):y + 3, max(0, x - 3):x + 2]
    rgb = region[:, :, :3].astype(int)
    black = (region[:, :, 3] == 255) & (rgb.max(axis=2) < 40)
    region[black] = out[y, x + 1] if x + 1 < out.shape[1] and out[y, x + 1, 3] == 255 else region[black]   # 검은 눈구멍은 옆 살색으로
    if out[y, x, :3].min() > HEAD_LIGHT - 60 or out[y, x, :3].max() < 40:
        out[y, x] = color
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
    eye = find_eye(still)
    meta = {}
    for name, (frames_src, align) in SETS.items():
        frames = [restore_eye(lock_palette(remove_loose_grey(remove_white_arcs(load(src, n))), pal), eye) for src, n in frames_src]
        hx = [hair_x(f) for f in frames]
        anchor_x = still_hair
        if align == 'hair':
            anchor_x = float(np.mean([h for h in hx if h is not None]))
            frames = [shift_x(f, int(round(anchor_x - h))) if h is not None else f for f, h in zip(frames, hx)]
            # 바닥 고정 (2026-11-23): 달리기·대기는 프레임마다 가장 아래 픽셀을 발 줄에 붙인다.
            # PixelLab 달리기는 장마다 발이 최대 8px 떠서(두 발이 다 뜬 장) 둥둥 튀어 보였다
            frames = [np.roll(f, still_foot - foot_row([f]), axis=0) for f in frames]
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
