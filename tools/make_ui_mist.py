"""UI 컨셉 확정(2026-11-27, docs/opus/TASKS.md '3차 변경 2'): 타이틀 = B 감시 단말, 증강 선택 = A 안개 미니멀.
config.UI_SKIN = 'mist'가 쓰는 그림을 굽는다. 그림(로고·테두리·장식·표시)은 전부 PixelLab 원본에서 자르고 색만 바꾼다.

결과 (assets/ui/um_*.png, 도트 1칸 = 화면 2px, 알파 0/255, 64색 이하):
- 증강 카드 테두리 um_card_<등급>.png / um_card_<등급>_hot.png (360x500, 속은 비어 있다. 어두운 바탕은 실행 중 코드가 깐다)
  원본: assets/sprites/pixellab/ui_mist_v1/raw/frame_white_s22.png (create_image_pro_flash 128x176, 도트 2px로 와서 반으로)
  가는 선(도트 1칸) 하나 + 네 모서리 작은 마디. 변은 모서리 바로 안쪽 한 줄을 이어 붙인다(가운데 마름모는 A 장식선이 대신한다).
  등급 색: 보통 회백(원본 그대로), 진화 청록, 합성 금, 저주 빨강 — A 장식선(PixelLab)의 색 셋으로 밝기 단계를 바꿔 끼운다.
  고른 카드(_hot)는 한 단계씩 밝게.
- A 장식선 um_divider_<색>.png, 고른 카드 아래 안개 um_mist_pool.png (ui_concepts_v2/a_mist). 장식선은 선 줄이 그림의
  세로 가운데 도트에 오도록 위아래를 비워 둔다(테두리 선 위에 바로 얹게).
- B 타이틀: um_logo_title.png(64색으로 줄임), um_cursor.png, um_lamps.png, um_bracket.png (ui_concepts_v2/b_terminal)
- 타이틀 글자 뒤 어둠 assets/light/title_shade.png (960x540, 화면에는 2배): 빛 층과 같은 예외로 부드러운 알파.
  로고·메뉴·머리글·판번호 글자 상자에서 멀어질수록 옅어진다(exp(-(d/sigma)^2)). 체크무늬 디더 없음, 화면 가장자리는 0.

사용: python tools/make_ui_mist.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from apply_ui_plate import fit  # noqa: E402

PX = os.path.join(ROOT, 'assets', 'sprites', 'pixellab')
CON = os.path.join(PX, 'ui_concepts_v2')
UI = os.path.join(ROOT, 'assets', 'ui')
LIGHT = os.path.join(ROOT, 'assets', 'light')
CARD_W, CARD_H = 180, 250                     # 1배 (화면 360x500, mutation_mode.CARD_W/H)
CORNER = 6

# 원본 테두리의 밝기 단계 (밝음, 선, 그늘, 어둠) -> 등급 색 (A 장식선의 색)
WHITE = [(238, 241, 245), (184, 192, 204), (110, 120, 136), (52, 60, 74)]
RAMPS = {
    'common': WHITE,
    'rare': [(160, 248, 238), (46, 230, 214), (14, 120, 118), (8, 60, 60)],
    'legendary': [(255, 222, 140), (240, 180, 50), (150, 98, 26), (80, 52, 14)],
    'curse': [(255, 138, 146), (226, 58, 72), (168, 42, 54), (90, 16, 24)],
}


def half(a, oy=1, ox=1):
    """2px 도트로 온 그림을 반으로: (oy, ox)에서 시작하는 2x2 칸마다 가장 흔한 색(불투명 우선)."""
    a = a[oy:, ox:]
    h, w = a.shape[0] // 2, a.shape[1] // 2
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            cell = a[2 * y:2 * y + 2, 2 * x:2 * x + 2].reshape(-1, 4)
            cell = [tuple(c) for c in cell if c[3] > 0]
            if len(cell) >= 2:
                out[y, x] = max(set(cell), key=cell.count)
    return out


def recolor(a, ramp, step=0):
    """원본의 밝기 단계를 ramp로 바꿔 끼운다. step=1이면 한 단계씩 밝게 (고른 카드)."""
    out = a.copy()
    for i, c in enumerate(WHITE):
        m = (a[:, :, 3] > 0) & (a[:, :, :3] == c).all(axis=2)
        out[m, :3] = ramp[max(0, i - step)]
    return out


def save2(a, name, folder=UI):
    im = Image.fromarray(np.ascontiguousarray(a), 'RGBA')
    im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(folder, name))
    return name


def load(path):
    return np.array(Image.open(path).convert('RGBA'))


def card_frames():
    raw = load(os.path.join(PX, 'ui_mist_v1', 'raw', 'frame_white_s22.png'))
    f = half(raw)
    ys, xs = np.nonzero(f[:, :, 3])
    f = f[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    # 원본 색 중 단계에 없는 색(가장자리 한두 점)은 가장 가까운 단계로
    for y, x in zip(*np.nonzero(f[:, :, 3])):
        c = tuple(int(v) for v in f[y, x, :3])
        if c not in WHITE:
            f[y, x, :3] = min(WHITE, key=lambda w: sum((p - q) ** 2 for p, q in zip(w, c)))
    frame = fit(f, CARD_W, CARD_H, CORNER, CORNER, fill=False, uniform=True)
    made = []
    for kind, ramp in RAMPS.items():
        made.append(save2(recolor(frame, ramp), f'um_card_{kind}.png'))
        made.append(save2(recolor(frame, ramp, 1), f'um_card_{kind}_hot.png'))
    return made


def centered_divider(src, name):
    """장식선 그림(2배 조각)을 1배로 줄이고, 가장 많이 칠해진 줄(선)이 세로 가운데 도트에 오게 위아래를 비운다."""
    a = load(src)[::2, ::2]
    row = int(np.argmax((a[:, :, 3] > 0).sum(axis=1)))
    above, below = row, a.shape[0] - 1 - row
    pad = max(above, below)
    out = np.zeros((2 * pad + 1, a.shape[1], 4), np.uint8)
    out[pad - row:pad - row + a.shape[0]] = a
    return save2(out, name)


def copy_part(src, name, max_colors=64):
    a = load(src)
    colors = {tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}
    if len(colors) > max_colors:                           # 64색 넘으면 Pillow로 줄인다 (2x2 격자는 그대로)
        small = Image.fromarray(a[::2, ::2], 'RGBA')
        alpha = small.getchannel('A')
        q = small.convert('RGB').quantize(max_colors - 1, method=Image.Quantize.MEDIANCUT).convert('RGB')
        q.putalpha(alpha)
        a = np.array(q)
        a[a[:, :, 3] == 0] = 0
        return save2(a, name)
    Image.fromarray(a, 'RGBA').save(os.path.join(UI, name))
    return name


def parts():
    made = []
    for c in ('white', 'cyan', 'gold', 'red'):
        made.append(centered_divider(os.path.join(CON, 'a_mist', 'parts', f'divider_{c}.png'), f'um_divider_{c}.png'))
    made.append(copy_part(os.path.join(CON, 'a_mist', 'parts', 'mist_pool.png'), 'um_mist_pool.png'))
    for src, dst in (('logo', 'logo_title'), ('cursor', 'cursor'), ('lamps', 'lamps'), ('bracket', 'bracket')):
        made.append(copy_part(os.path.join(CON, 'b_terminal', 'parts', f'{src}.png'), f'um_{dst}.png'))
    return made


# ----- 타이틀 글자 뒤 어둠 -----
SHADE_COLOR = (4, 6, 12)


def shade_boxes():
    """(x0, y0, x1, y1, 진하기, 번지는 거리) — 화면 좌표(아래가 0). title_mode의 자리와 같다."""
    import config
    import title_mode as tm
    W, H = config.SCREEN_W, config.SCREEN_H
    boxes = []
    lw, lh = Image.open(os.path.join(UI, 'um_logo_title.png')).size
    boxes.append((W // 2 - lw // 2 + 40, tm.LOGO_Y - 30, W // 2 + lw // 2 - 40, tm.LOGO_Y + lh - 20, 0.80, 170))   # 로고 + '헤이즈'
    for b in tm.MENU:
        cy = b.y + b.h // 2
        boxes.append((W // 2 - 80, cy - 16, W // 2 + 80, cy + 16, 0.74, 150))                    # 메뉴 한 줄 (글자 폭 정도)
    hx, hy = tm.TERM_HEAD
    boxes.append((hx, hy - 30, hx + 520, hy + 6, 0.62, 110))                                  # 왼쪽 위 머리글 두 줄
    boxes.append((W - tm.TERM_MARGIN - 130, 54, W - tm.TERM_MARGIN, 66, 0.55, 80))                  # 오른쪽 아래 판번호
    return boxes


def title_shade(scale=2):
    import config
    W, H = config.SCREEN_W // scale, config.SCREEN_H // scale
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xx = (xx + 0.5) * scale
    yy = (H - 1 - yy + 0.5) * scale                        # 그림 줄 0 = 화면 맨 위
    keep = np.ones((H, W), np.float32)                  # 겹치는 곳은 부드럽게 더 진하게: 1 - (1-a1)(1-a2)...
    for x0, y0, x1, y1, k, sigma in shade_boxes():
        dx = np.maximum(np.maximum(x0 - xx, xx - x1), 0)
        dy = np.maximum(np.maximum(y0 - yy, yy - y1), 0)
        d = np.sqrt(dx * dx + dy * dy)
        keep *= 1 - k * np.exp(-(d / sigma) ** 2)
    alpha = np.minimum(1 - keep, 0.88)
    a8 = np.round(alpha * 255).astype(np.uint8)
    a8[a8 < 3] = 0
    out = np.zeros((H, W, 4), np.uint8)
    out[:, :, :3] = SHADE_COLOR
    out[:, :, 3] = a8
    Image.fromarray(out, 'RGBA').save(os.path.join(LIGHT, 'title_shade.png'), optimize=True)
    return 'light/title_shade.png'


def main():
    made = card_frames() + parts()
    made.append(title_shade())
    print(len(made), '개:', ', '.join(made))


if __name__ == '__main__':
    main()
