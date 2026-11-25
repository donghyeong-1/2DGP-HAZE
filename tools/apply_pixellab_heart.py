"""헤이즈 심장(본체·손)의 PixelLab v6 그림을 게임 그림으로 적용한다 (2026-11-25).

본체는 화면 896x480px(448x240점)이라 PixelLab 캔버스 한도(256)를 넘는다. 좌우 대칭이므로 **왼쪽 절반(224x240)만** 만들고
여기서 좌우로 뒤집어 붙인다(오른쪽 끝 = 가운데 절단선). 원본: assets/sprites/pixellab/heart_core_v6/raw/
  open/frame_0~8  문이 열리는 동작 (0 닫힘 = base, 1 살짝 열림, 7 다 열림)
  dying/frame_0~8 열린 채 부서지는 동작 (2 결정이 깨져 흩어짐, 4 불이 꺼지고 금이 감)
손은 assets/sprites/pixellab/heart_hand_v6/raw/ (base.png 128x128, idle·fist·palm·stun 폴더). 오른손 그림이고 왼손은 게임이 뒤집는다.

하는 일:
1. 알파 0/255. 본체는 열린 방 안쪽(투명으로 나온다)을 가장 어두운 색으로 막는다. 색은 기준 그림들의 색으로만 다시 칠한다(64색 이하).
2. 본체: 맞는 순간(hurt)은 열린 그림의 결정을 희게 밝힌 것. 손: 기절(stun)은 PixelLab 결과가 새까만 실루엣이라 쓰지 않고,
   기절 동작 3번(조금 기운 손)의 불빛을 반쯤/전부 끈 것.
3. 최근접 2배로 키워, 예전 그림과 같은 기준점 규칙으로 캔버스에 놓는다 (src/sprites.py의 옛 주석과 같다):
   - 본체 900x580, 기준점 (450,462): 결정 가운데가 (450,312) = 히트박스 가운데(발 위 150).
   - 손 260x260: 떠 있는 자세(대기·치켜든 주먹)는 손 가운데가 (130,130), 기준점 (130,185).
     내려친 주먹은 그림 아래 끝이 기준점 줄(185)에. 손바닥(광선)은 결정이 (130,130), 기준점 (130,130).
     기절은 그림 아래 끝이 250, 기준점 (130,250).
4. assets/sprites/unified/v6_heart_*.png 와 skin_heart.json(옛 세트 이름 -> 새 세트)을 쓴다. 장수는 src/heart.py 그대로.

실행: python tools/apply_pixellab_heart.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_pixellab_event import reduce_palette  # noqa: E402
from apply_pixellab_hero import lock_palette  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIX = os.path.join(ROOT, 'assets', 'sprites', 'pixellab')
DST = os.path.join(ROOT, 'assets', 'sprites', 'unified')
SCALE = 2
MAX_COLORS = 56


def load(*parts):
    a = np.array(Image.open(os.path.join(PIX, *parts)).convert('RGBA'))
    a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
    a[a[:, :, 3] == 0] = 0
    return a


def palette(frames):
    px = np.concatenate([a[a[:, :, 3] == 255][:, :3] for a in frames])
    pal, counts = np.unique(px, axis=0, return_counts=True)
    return reduce_palette(pal, counts, MAX_COLORS)


def is_teal(a):
    r, g, b = (a[:, :, i].astype(int) for i in range(3))
    return (a[:, :, 3] == 255) & (g > 150) & (b > 150) & (r < g - 40)


def recolor(a, mask, fn):
    out = a.copy()
    px = out[mask][:, :3].astype(float)
    out[mask, :3] = np.clip(fn(px), 0, 255).astype(np.uint8)
    return out


def save(a, name, canvas, at):
    """a(1배)를 2배로 키워 canvas(가로, 세로)의 at(왼쪽, 위)에 놓아 저장한다."""
    im = Image.fromarray(np.ascontiguousarray(a), 'RGBA')
    im = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
    out = Image.new('RGBA', canvas, (0, 0, 0, 0))
    out.alpha_composite(im, at)
    out.save(os.path.join(DST, name + '.png'))


# ----- 본체 -----
def core():
    raw = 'heart_core_v6'
    closed, ajar, opened = (load(raw, 'raw', 'open', f'frame_{n}.png') for n in (0, 1, 7))
    dying = [load(raw, 'raw', 'dying', f'frame_{n}.png') for n in (2, 4)]
    # 열린 방 안쪽: 오른쪽 끝(절단선)을 막힌 것으로 보고 열린 그림의 구멍을 찾는다. 그 자리의 투명 칸은 가장 어두운 색으로.
    solid = opened[:, :, 3] == 255
    closed_edge = np.concatenate([solid, np.ones((solid.shape[0], 1), bool)], axis=1)
    chamber = ndimage.binary_fill_holes(closed_edge)[:, :-1] & ~solid
    pal = palette([closed, opened] + dying)
    dark = pal[pal.astype(int).sum(axis=1).argmin()]

    def finish(a):
        a = a.copy()
        hole = chamber & (a[:, :, 3] == 0)
        a[hole] = (*dark, 255)
        a = lock_palette(a, pal)
        return np.concatenate([a, a[:, ::-1]], axis=1)             # 좌우로 뒤집어 붙인다

    filled = opened.copy()
    filled[chamber & (filled[:, :, 3] == 0)] = (*dark, 255)
    teal = is_teal(filled)
    rows = np.nonzero(teal[:, 170:222].sum(axis=1) > 4)[0]         # 절단선 옆의 결정이 차지하는 줄 (얇은 이음매 빛은 뺀다)
    cy = int(round((rows.min() + rows.max()) / 2))
    crystal = teal & (np.arange(filled.shape[1])[None, :] >= 170) & (np.arange(filled.shape[0])[:, None] >= rows.min()) \
        & (np.arange(filled.shape[0])[:, None] <= rows.max())
    hurt = recolor(filled, crystal, lambda px: px + (255 - px) * 0.75)   # 맞는 순간: 결정이 희게 번쩍
    pal = np.unique(np.concatenate([pal, hurt[crystal][:, :3]]), axis=0)[:64]
    canvas, at = (900, 580), (450 - closed.shape[1] * SCALE, 312 - cy * SCALE)
    sets = {'v6_heart_core': [closed, ajar, opened], 'v6_heart_core_hurt': [hurt], 'v6_heart_core_dying': dying}
    meta = {}
    for name, frames in sets.items():
        for i, f in enumerate(frames, 1):
            save(finish(f), f'{name}_{i}', canvas, at)
        meta[name] = [len(frames), 450, 462]
    print(f'본체: 결정 가운데 줄 {cy}, 캔버스 {canvas}, 그림 위치 {at}, 색 {len(pal)}')
    return meta


# ----- 손 -----
def hand():
    raw = 'heart_hand_v6'
    base = load(raw, 'raw', 'base.png')
    f = lambda folder, n: load(raw, 'raw', folder, f'frame_{n}.png')  # noqa: E731
    idle = [f('idle', 0), f('idle', 2)]
    fist = [f('fist', 5), f('fist', 7)]
    palm = [f('palm', 4), f('palm', 7)]
    limp = f('stun', 3)
    lights = is_teal(limp)
    stun = [recolor(limp, lights, lambda px: px * 0.55 + np.array([40, 48, 60]) * 0.45),      # 불빛이 반쯤 꺼짐
            recolor(recolor(limp, lights, lambda px: px * 0.0 + np.array([46, 56, 70])),       # 불빛이 다 꺼지고 몸도 어두워짐
                    limp[:, :, 3] == 255, lambda px: px * 0.72)]
    pal = palette([base] + palm + stun)

    def bbox(a):
        ys, xs = np.nonzero(a[:, :, 3])
        return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

    def crystal_center(a):
        """손바닥 결정 가운데: 손 가운데 근처의 밝은(청록·흰) 칸의 평균."""
        x0, y0, x1, y1 = bbox(base)
        r, g, b = (a[:, :, i].astype(int) for i in range(3))
        bright = (a[:, :, 3] == 255) & (g > 170) & (b > 170)
        ys, xs = np.nonzero(bright)
        keep = (abs(xs - (x0 + x1) / 2) < 14) & (ys > y0 + 20) & (ys < y0 + 62)
        return xs[keep].mean(), ys[keep].mean()

    canvas = (260, 260)
    meta = {}

    def tidy(a):
        """몸에서 떨어진 작은 점(8칸 미만)을 지운다."""
        a = a.copy()
        lab, n = ndimage.label(a[:, :, 3] == 255, structure=np.ones((3, 3)))
        for i, size in enumerate(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)) if n else [], 1):
            if size < 8:
                a[lab == i] = 0
        return a

    def put(name, frames, where):
        for i, a in enumerate(frames, 1):
            a = tidy(lock_palette(a, pal))
            x0, y0, x1, y1 = bbox(a)
            if where == 'center':                         # 손 가운데가 (130,130)
                at = (130 - int(round((x0 + x1) * SCALE / 2)), 130 - int(round((y0 + y1) * SCALE / 2)))
            elif where == 'crystal':                      # 결정이 (130,130)
                cx, cy = crystal_center(a)
                at = (130 - int(round(cx * SCALE)), 130 - int(round(cy * SCALE)))
            else:                                         # 그림 아래 끝이 where 줄에
                at = (130 - int(round((x0 + x1) * SCALE / 2)), where - y1 * SCALE)
            at = (at[0] // 2 * 2, at[1] // 2 * 2)         # 2px 격자
            save(a, f'{name}_{i}', canvas, at)

    put('v6_heart_hand_idle', idle, 'center')
    put('v6_heart_hand_fist', fist[:1], 'center')
    a2 = tidy(lock_palette(fist[1], pal))                 # 내려친 주먹: 아래 끝이 기준점 줄(185)에
    x0, y0, x1, y1 = bbox(a2)
    save(a2, 'v6_heart_hand_fist_2', canvas, ((130 - int(round((x0 + x1) * SCALE / 2))) // 2 * 2, (185 - y1 * SCALE) // 2 * 2))
    put('v6_heart_hand_palm', palm, 'crystal')
    put('v6_heart_hand_stun', stun, 250)
    meta.update({'v6_heart_hand_idle': [2, 130, 185], 'v6_heart_hand_fist': [2, 130, 185],
                 'v6_heart_hand_palm': [2, 130, 130], 'v6_heart_hand_stun': [2, 130, 250]})
    print(f'손: 캔버스 {canvas}, 색 {len(pal)}')
    return meta


def main():
    frames = core()
    frames.update(hand())
    skin = {name[3:]: name for name in frames}            # heart_core -> v6_heart_core ...
    path = os.path.join(DST, 'skin_heart.json')
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump({'frames': frames, 'skin': skin}, fp, ensure_ascii=False, indent=1)
    print('저장', os.path.relpath(path, ROOT), list(skin))


if __name__ == '__main__':
    main()
