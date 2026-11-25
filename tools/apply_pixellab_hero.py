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
    'hero6_pistol': ([('base_pistols.png', None)], 'none'),            # 쌍권총 겨눔 (v3 무기 기준 그림, 추천안)
    # 쌍권총 자세 (2026-11-24, raw/v3_kp/gen_pistol.py 뼈대로 skeleton v3): 조준 방향 4장, 달리며 쏘기 8장, 공중 3장
    'hero6_pistol_up': (_f('v3_pistol_aim', [0]), 'none'),
    'hero6_pistol_upfwd': (_f('v3_pistol_aim', [1]), 'none'),
    'hero6_pistol_downfwd': (_f('v3_pistol_aim', [2]), 'none'),
    'hero6_pistol_down': (_f('v3_pistol_aim', [3]), 'none'),
    'hero6_pistol_run': (_f('v3_pistol_run', range(8)), 'hair'),
    'hero6_pistol_air': (_f('v3_pistol_air', [0, 1, 2]), 'air'),
    # 건틀릿 자세 (2026-11-24, raw/v3_kp/gen_gauntlet.py): 예전 n09_gauntlet 순서(충전·앞 강타·회수·공중 아래) 그대로 4장
    'hero6_gauntlet': (_f('v3_gauntlet_ground', [0, 1, 2]) + _f('v3_gauntlet_air', [0]), 'none'),
    'hero6_gauntlet_upfwd': (_f('v3_gauntlet_ground', [3]), 'none'),
    'hero6_gauntlet_downfwd': (_f('v3_gauntlet_ground', [4]), 'none'),
    'hero6_gauntlet_air': (_f('v3_gauntlet_air', [1, 2]), 'air'),       # 공중 앞·앞 위 (발을 발 줄에 맞춘다)
    'hero6_gauntlet_airdown': (_f('v3_gauntlet_air', [0]), 'air'),      # 공중에서 아래로
    # 사슬 자세 (2026-11-24, raw/v3_kp/gen_chain.py): 예전 n09_chain 순서(돌리기·던지기·당기기) 그대로 3장
    'hero6_chain': (_f('v3_chain_ground', [0, 1, 2]), 'none'),
    'hero6_chain_upfwd': (_f('v3_chain_ground', [3]), 'none'),
    'hero6_chain_downfwd': (_f('v3_chain_ground', [4]), 'none'),
    'hero6_chain_air': (_f('v3_chain_air', [0, 1, 2]), 'air'),          # 공중 앞·앞 위·아래
    # 궁극기 시전 자세 (2026-11-25, pixminimax, 첫 장 = base_chain. 사슬 궁극기가 끝까지 쓴다): 낮게 웅크려 모음 -> 두 팔을 벌려 해방.
    # 4~6번은 섬광·고리가 그려져 뺐다 (shots/pixellab_test/v3_ult.png)
    'hero6_ult': (_f('v3_ult', [2, 8]), 'none'),
    # 맨손 자세 (당김·모음·뻗음·회수, 예전 n09_punch 순서): 전용 자세가 없는 무기에서만 쓰여 거의 안 나온다. 건틀릿 그림을 다시 쓴다
    'hero6_punch': (_f('v3_gauntlet_ground', [0, 0, 1, 2]), 'none'),
    'hero6_hurt': (_f('hurt96', [0, 1]), 'none'),
    'hero6_death': (_f('death96', [2, 4, 7]), 'none'),
}


# 쌍권총 세트 -> 장마다 조준 방향 (앞 +x, 위 +y). 총구(총열 끝)를 찾는 데 쓴다 (hero6_muzzle.json, 게임의 총알 나가는 자리)
MUZZLE_DIRS = {'hero6_pistol': [(1.0, 0.0)], 'hero6_pistol_up': [(0.17, 0.98)], 'hero6_pistol_upfwd': [(0.74, 0.67)],
               'hero6_pistol_downfwd': [(0.74, -0.67)], 'hero6_pistol_down': [(0.26, -0.97)], 'hero6_pistol_run': [(1.0, 0.0)],
               'hero6_pistol_air': [(1.0, 0.0), (0.74, 0.67), (0.74, -0.67)]}


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


def remove_muzzle_flash(a, x_cut):
    """생성 모델이 그려 넣은 총구 섬광을 지운다 (섬광은 게임이 코드로 그린다): 총열 끝보다 앞(x_cut 이상)을 모두 비운다.
    총열 끝은 섬광 없는 장에서 잰 값(손목 + 8~9px)으로 정한다."""
    out = a.copy()
    out[:, x_cut:] = 0
    return out


def remove_grey_behind(a, x_cut):
    """몸 뒤(x_cut보다 왼쪽)에 붙은 회색 궤적 덩어리를 지운다 (목도리의 청록은 남긴다)."""
    out = a.copy()
    rgb = out[:, :, :3].astype(int)
    grey = (out[:, :, 3] == 255) & (rgb.max(axis=2) - rgb.min(axis=2) < 40) & (rgb.max(axis=2) > 95)
    grey[:, x_cut:] = False
    out[grey] = 0
    from scipy import ndimage                     # 회색을 지운 뒤 흩어져 남은 작은 조각 (몸 뒤쪽만)
    lab, n = ndimage.label(out[:, :, 3] == 255, structure=np.ones((3, 3)))
    if n > 1:
        sizes = ndimage.sum(out[:, :, 3] == 255, lab, range(1, n + 1))
        body = int(np.argmax(sizes)) + 1
        for k in range(1, n + 1):
            comp = lab == k
            if k != body and sizes[k - 1] < 30 and np.nonzero(comp.any(axis=0))[0].max() < x_cut + 6:
                out[comp] = 0
    return out


GREY_CUT = {'hero6_gauntlet_downfwd': {0: 34},  # 세트 -> {번호: 원본 x}: 몸 뒤 회색 궤적 (v3_gauntlet_ground 4번)
            'hero6_chain': {2: 40}, 'hero6_chain_upfwd': {0: 40}, 'hero6_chain_air': {0: 40}}   # 사슬: 목도리 끝 회색 궤적


# 세트 -> {세트 안 번호(0부터): 자를 원본 x}. 섬광이 그려진 장만 (raw/v3_pistol_run의 2·4·6번, 4번은 총열이 짧아 80)
FLASH_CUT = {'hero6_pistol_run': {2: 82, 4: 80, 6: 82}}


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
        if name in GREY_CUT:
            frames = [remove_grey_behind(f, GREY_CUT[name][i]) if i in GREY_CUT[name] else f for i, f in enumerate(frames)]
        if name in FLASH_CUT:
            frames = [remove_muzzle_flash(f, FLASH_CUT[name][i]) if i in FLASH_CUT[name] else f for i, f in enumerate(frames)]
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
    muzzle = {}
    for name, dirs in MUZZLE_DIRS.items():                 # 쌍권총 총구 위치: 조준 방향으로 가장 멀리 나간 불투명 픽셀
        if name not in meta:
            continue
        count, px, py = meta[name]
        offs = []
        for i in range(1, count + 1):
            a = np.array(Image.open(os.path.join(DST, f'{name}_{i}.png')).convert('RGBA'))
            ys, xs = np.nonzero(a[:, :, 3] == 255)
            keep = (xs - px > 0) & (py - ys > 56)            # 몸 앞, 허리 위 (발·목도리 끝을 고르지 않게)
            ys, xs = ys[keep], xs[keep]
            dx, dy = dirs[min(i - 1, len(dirs) - 1)]
            k = int(np.argmax((xs - px) * dx + (py - ys) * dy))
            offs.append([int(xs[k] - px), int(py - ys[k])])     # 발 기준점에서 (앞 +, 위 +) 화면 px
        muzzle[name] = offs
    with open(os.path.join(DST, 'hero6_muzzle.json'), 'w', encoding='utf-8') as fp:
        json.dump(muzzle, fp, indent=1)
    path = os.path.join(DST, 'hero6.json')
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    print('저장', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    main()
