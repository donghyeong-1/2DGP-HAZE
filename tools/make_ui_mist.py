"""UI 컨셉 확정(2026-11-27, docs/opus/TASKS.md '3차 변경 2'): 타이틀 = B 감시 단말, 증강 선택 = A 안개 미니멀.
config.UI_SKIN = 'mist'가 쓰는 그림을 굽는다. 그림(로고·테두리·장식·표시)은 전부 PixelLab 원본에서 자르고 색만 바꾼다.

결과 (assets/ui/um_*.png, 도트 1칸 = 화면 2px, 알파 0/255, 64색 이하):
- 증강 카드 테두리 um_card_<등급>.png / um_card_<등급>_hot.png (360x500, 속은 비어 있다. 어두운 바탕은 실행 중 코드가 깐다)
  원본: assets/sprites/pixellab/ui_mist_v1/raw/frame_white_s22.png (create_image_pro_flash 128x176, 도트 2px로 와서 반으로)
  가는 선(도트 1칸) 하나 + 네 모서리 작은 마디. 변은 모서리 바로 안쪽 한 줄을 이어 붙인다(가운데 마름모는 A 장식선이 대신한다).
  등급 색: 보통 회백(원본 그대로), 진화 청록, 합성 금, 저주 빨강 — A 장식선(PixelLab)의 색 셋으로 밝기 단계를 바꿔 끼운다.
  고른 카드(_hot)는 한 단계씩 밝게.
- A 장식선 um_divider_<색>.png, 고른 카드 아래 안개 um_mist_pool.png (ui_concepts_v2/a_mist). 장식선은 선 줄이 그림의
  세로 가운데 도트에, 가운데 장식이 가로 가운데에 오도록 비워 둔다(테두리 선 위 카드 가운데에 바로 얹게).
- B 타이틀: um_logo_title.png(64색으로 줄임), um_cursor.png, um_lamps.png, um_bracket.png (ui_concepts_v2/b_terminal)
- 타이틀 글자 뒤 어둠 assets/light/title_shade.png (960x540, 화면에는 2배): 빛 층과 같은 예외로 부드러운 알파.
  로고·메뉴·머리글·판번호 글자 상자에서 멀어질수록 옅어진다(exp(-(d/sigma)^2)). 체크무늬 디더 없음, 화면 가장자리는 0.
  title_shade_flash.png: 대비 판(번쩍) 때 쓰는 것. 왼쪽 위 머리글 뒤 어둠만 뺐다(흰 하늘 위 회색 얼룩, 11/27 L1).
- 플레이 중 HUD (11/27 H1): um_hud_frame_<색>.png(9칸 테두리 한 줄, 속 투명), um_fill_<색>_<높이>.png(막대 속: 한 색 + 위 밝은 줄),
  um_dash_on/off·um_combo_on/off/fin·um_dot_off(작은 표시). PixelLab 원본 없이 코드로 굽는다(단색 바탕과 2px 테두리).
- 타이틀 배경 title_mist.png, 대비 판 title_flash_<n>.png, 잔광 판 title_glow.png, 줄기 판 title_bolt_<n>.png (assets/backgrounds).
  줄기 판: 대비 판 n과 같은 자리의 번갯줄기만(나머지는 알파 0). 번쩍이기 직전·두 깜빡임 사이에 원래 배경 위에 얹는다.
  줄기 모양은 PixelLab 원본 그대로, 색만 BOLT_COLORS(흰 심 + 옅은 푸른 흰 가장자리)로 바꾼다. 대비 판의 줄기도 같은 색.

- 메뉴 화면 (11/27 M1): 글자 뒤 어둠 조각 시트 assets/light/menu_shade_<soft|wide>.png(9칸으로 이어 붙인다),
  키 글자 판·음량 막대의 인광색 테두리 um_hud_frame_ph·ph_dim, 막대 속 um_fill_phos_<높이>.
- 고르는 화면 (11/27 S1): 고른 줄 앞 삼각 커서 um_pick_cursor(밝은 회백)·um_pick_cursor_off(살 수 없는 줄, 흐린 회색). 코드로 찍는다.

사용: python tools/make_ui_mist.py          (전부)
      python tools/make_ui_mist.py --hud    (플레이 중 HUD 부품만)
      python tools/make_ui_mist.py --menu   (메뉴 화면 부품만)
      python tools/make_ui_mist.py --pick   (고르는 화면 부품만: um_pick_cursor·um_pick_cursor_off)
      python tools/make_ui_mist.py --wp     (무기·E 패널 시안 부품만: um_wp_a_*·um_wp_b_*·um_wp_c_*(W1)·um_wp_d_*(W2)·um_wp_da_*(W3)·um_wp_row_*(W4))
      python tools/make_ui_mist.py --storm  (타이틀 배경·대비 판·줄기 판·잔광 판·글자 뒤 어둠만, R1)
      python tools/make_ui_mist.py --step   (증강 카드 진행 칸 um_step_off·um_step_on만, R1)
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
    # 가로: 가운데 장식(가장 키 큰 세로 줄들의 가운데)이 그림 가운데에 오게 한쪽을 비운다 (흰 장식선은 원본이 왼쪽으로 치우쳐 있었다)
    col = (out[:, :, 3] > 0).sum(axis=0)
    mid = int(round(np.nonzero(col == col.max())[0].mean()))
    left, right = mid, out.shape[1] - 1 - mid
    side = max(left, right)
    wide = np.zeros((out.shape[0], 2 * side + 1, 4), np.uint8)
    wide[:, side - mid:side - mid + out.shape[1]] = out
    return save2(wide, name)


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
    for src, dst in (('logo', 'logo_title'), ('cursor', 'cursor'), ('bracket', 'bracket')):     # 표시등 판은 11/27 사용자가 지웠다
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
    boxes.append((W // 2 - lw // 2 + 40, tm.LOGO_Y - 30, W // 2 + lw // 2 - 40, tm.LOGO_Y + lh - 20, 0.80, 170, 'logo'))   # 로고 + '헤이즈'
    for b in tm.MENU:
        cy = b.y + b.h // 2
        boxes.append((W // 2 - 80, cy - 16, W // 2 + 80, cy + 16, 0.74, 150, 'menu'))            # 메뉴 한 줄 (글자 폭 정도)
    hx, hy = tm.TERM_HEAD
    boxes.append((hx, hy - 30, hx + 520, hy + 6, 0.62, 110, 'head'))                          # 왼쪽 위 머리글 두 줄
    boxes.append((W - tm.TERM_MARGIN - 130, 54, W - tm.TERM_MARGIN, 66, 0.55, 80))                  # 오른쪽 아래 판번호
    return boxes


FLASH_NO_SHADE = ('head', 'logo', 'menu')   # 대비 판(번쩍)에서 뒤 어둠을 깔지 않는 글자 상자


def title_shade(scale=2, flash=False):
    """flash면 머리글·로고·메뉴 상자를 빼고 굽는다 (대비 판의 흰 하늘 위에서 회색 얼룩·둥근 그늘로 보여서.
    11/27 L1: 머리글, 11/27 R1: 로고·메뉴. 로고는 대비 판에 구운 어두운 실루엣 위에, 메뉴는 검은 땅 실루엣 위에 놓인다)."""
    import config
    W, H = config.SCREEN_W // scale, config.SCREEN_H // scale
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xx = (xx + 0.5) * scale
    yy = (H - 1 - yy + 0.5) * scale                        # 그림 줄 0 = 화면 맨 위
    keep = np.ones((H, W), np.float32)                  # 겹치는 곳은 부드럽게 더 진하게: 1 - (1-a1)(1-a2)...
    for x0, y0, x1, y1, k, sigma, *tag in shade_boxes():
        if flash and tag and tag[0] in FLASH_NO_SHADE:
            continue
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
    name = 'title_shade_flash.png' if flash else 'title_shade.png'
    Image.fromarray(out, 'RGBA').save(os.path.join(LIGHT, name), optimize=True)
    return 'light/' + name


# ----- 타이틀 배경과 번개 (2026-11-27) -----
BG = os.path.join(ROOT, 'assets', 'backgrounds')
SKY_WHITE = (176, 190, 232)            # 번쩍일 때 하늘 (푸른 흰색. 11/27 L1: 196,208,242에서 낮췄다. 줄기의 흰 심과 옅은 가장자리가 하늘보다 밝게)
BOLT_SPOTS = ((1090, 84), (760, 84), (420, 250))   # (L1) 대비 판마다 번갯줄기 자리: 조각 하나의 (화면 x 가운데, 위 끝). R1부터는 아래 끝 자리만 쓴다
# R1(11/27): 줄기가 약 230px로 하늘 한가운데 떠 있었다 -> PixelLab 조각 um_bolt_1~3을 잘라 위아래로 이어 붙여(좌우 반전, 회전·확대 없음)
# 화면 위 끝에서 L1 줄기가 끝나던 자리까지 내려오게 한다. (조각 번호, 첫 줄, 끝 줄(포함), 좌우 반전) — 줄 번호는 1배 도트.
# 이음매는 줄기 한 가닥만 있는 줄끼리 가운데를 맞춘다(끊기지 않게). 앞 조각은 굵은 윗부분, 마지막 조각은 통째(가늘어지며 갈라지는 끝).
BOLT_RECIPES = (
    [(3, 0, 45, True), (2, 0, 112, False)],
    [(1, 0, 41, False), (3, 0, 114, True)],
    [(2, 0, 45, False), (1, 0, 59, True), (2, 0, 25, True), (3, 0, 114, False)],
)
# 곁가지: (붙일 이음매 번호(0 = 첫 이음매), 조각, 첫 줄, 끝 줄, 좌우 반전, 줄기 쪽 'l'|'r') — 조각의 가늘어지는 아랫부분을 이음매에서 비스듬히
BOLT_BRANCHES = (
    [(0, 1, 76, 115, True, 'l')],
    [(0, 2, 81, 112, False, 'r')],
    [(1, 3, 79, 114, False, 'r')],
)
# 줄기 색 (PixelLab 줄기 팔레트 -> 흰 심 + 옅은 푸른 흰 가장자리). 어두운 하늘(줄기 판)과 대비 판에 같은 색을 쓴다
# (11/27 L1: 전에는 대비 판에서 가장자리를 더 어두운 파랑으로 바꿔 '흰 하늘 위 가는 푸른 선'으로 보였다)
BOLT_EDGE = (208, 222, 252)
BOLT_COLORS = {(255, 255, 255): (255, 255, 255), (220, 232, 255): (255, 255, 255),
               (159, 182, 238): BOLT_EDGE, (93, 116, 184): BOLT_EDGE}
SILHOUETTE = (6, 8, 15)                # 번쩍일 때 건물·전선·탑
GLOW_ADD = (30, 40, 66)                # 잔광 판: 원래 그림에 더하는 푸른 빛 (조금 밝은 푸른 톤)


def skyline(far, T=36, smooth=9):
    """원경 그림(far_cell)의 하늘 아래 경계: 열마다 위에서 처음 세로 밝기 차이가 T를 넘는 줄(지붕·성벽 윗선).
    빗줄기(세로 줄)는 세로 차이가 작아 걸리지 않는다. 가운데값·열고 닫기로 튀는 줄을 고른다."""
    from scipy import ndimage
    a = far.astype(int)
    g = ndimage.uniform_filter1d(np.abs(np.diff(a, axis=0)).sum(2).astype(float), 3, axis=1)
    h, w = g.shape
    line = np.full(w, h + 1)
    for x in range(w):
        ys = np.nonzero(g[:, x] > T)[0]
        if len(ys):
            line[x] = ys[0]
    line = ndimage.median_filter(line, size=smooth)
    line = ndimage.grey_closing(ndimage.grey_opening(line, size=5), size=5)
    return line


def _runs(row):
    xs = np.nonzero(row)[0]
    return np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1) if len(xs) else []


def long_bolt(n):
    """대비 판 n의 긴 줄기 (1배 도트 RGBA, 위가 0)와 그 왼쪽 위 화면 자리 (x, y, 2px 단위로 짝수). PixelLab 조각을 잘라 잇는다."""
    pieces = {k: load(os.path.join(UI, f'um_bolt_{k}.png'))[::2, ::2] for k in (1, 2, 3)}   # 2배로 저장된 조각 -> 1배 도트
    segs = []
    for k, r0, r1, flip in BOLT_RECIPES[n - 1]:
        a = pieces[k][r0:r1 + 1]
        segs.append(a[:, ::-1] if flip else a)
    # 이음매: 위 조각 끝 줄의 한 가닥 가운데 = 아래 조각 첫 줄의 한 가닥 가운데
    xs, joints = [0], []
    for up, down in zip(segs, segs[1:]):
        ru, rd = _runs(up[-1, :, 3] > 0), _runs(down[0, :, 3] > 0)
        assert len(ru) == 1 and len(rd) == 1, '이음매 줄에 줄기가 한 가닥이 아니다'
        xs.append(xs[-1] + int(round(ru[0].mean() - rd[0].mean())))
    ys = np.cumsum([0] + [len(a) for a in segs])
    branches = []
    for j, k, r0, r1, flip, side in BOLT_BRANCHES[n - 1]:
        b = pieces[k][r0:r1 + 1]
        b = b[:, ::-1] if flip else b
        top = _runs(b[0, :, 3] > 0)
        seg_row = segs[j + 1][0, :, 3] > 0
        trunk = _runs(seg_row)[0] + xs[j + 1]
        bx = (trunk[0] - 1 - top[0][-1]) if side == 'l' else (trunk[-1] + 1 - top[0][0])   # 줄기 옆에 바로 붙는다
        branches.append((b, bx, int(ys[j + 1])))
    lo = min(xs + [bx for _b, bx, _y in branches])
    hi = max([x + a.shape[1] for x, a in zip(xs, segs)] + [bx + b.shape[1] for b, bx, _y in branches])
    out = np.zeros((int(ys[-1]), hi - lo, 4), np.uint8)
    for b, bx, by in branches:                              # 곁가지 먼저, 줄기를 위에
        h = min(len(b), len(out) - by)
        dst = out[by:by + h, bx - lo:bx - lo + b.shape[1]]
        m = b[:h, :, 3] > 0
        dst[m] = b[:h][m]
    for a, x, y in zip(segs, xs, ys):
        dst = out[y:y + len(a), x - lo:x - lo + a.shape[1]]
        m = a[:, :, 3] > 0
        dst[m] = a[m]
    # 아래 끝을 L1 줄기의 아래 끝 자리에 (조각 하나일 때의 아래 끝 가운데 x, 아래 끝 y)
    old = pieces[n]
    bx, top = BOLT_SPOTS[n - 1]
    end_x = (bx - old.shape[1]) // 2 + _runs(old[-1, :, 3] > 0)[0].mean()   # 도트 단위
    end_y = top // 2 + len(old)
    last = _runs(out[-1, :, 3] > 0)[0].mean()
    x0 = int(round(end_x - last))
    y0 = end_y - len(out)
    if y0 > 0:                                              # 화면 위 끝까지 닿지 않는다 -> BOLT_RECIPES에 조각을 더 잇는다
        raise ValueError(f'줄기 {n}이 짧다: 위 끝 {y0 * 2}px')
    return out, 2 * x0, 2 * y0                              # 위로 넘친 부분은 부르는 쪽이 자른다


def logo_silhouette(H, W):
    """대비 판에서 로고 둘레를 어두운 실루엣으로 (R1, 11/27): 로고 글자 모양을 도트 3칸(6px) 넓힌 덩어리. 화면 크기 bool, 위가 0.
    뒤 어둠(부드러운 알파)을 흰 하늘 위에 깔면 둥근 회색 그늘로 보여서, 번쩍일 때는 이 실루엣이 그늘 대신 로고를 받친다."""
    from scipy import ndimage
    import config
    import title_mode as tm
    logo = load(os.path.join(UI, 'um_logo_title.png'))
    m = logo[::2, ::2, 3] > 0                                 # 1배 도트
    cross, square = ndimage.generate_binary_structure(2, 1), ndimage.generate_binary_structure(2, 2)
    pad = 4
    m = np.pad(m, pad)
    for st in (square, cross, square):                      # 모서리가 둥근 팔각 쪽으로 넓힌다
        m = ndimage.binary_dilation(m, st)
    big = m.repeat(2, 0).repeat(2, 1)
    out = np.zeros((H, W), bool)
    top = config.SCREEN_H - tm.LOGO_Y - logo.shape[0] - 2 * pad
    left = config.SCREEN_W // 2 - logo.shape[1] // 2 - 2 * pad
    out[top:top + big.shape[0], left:left + big.shape[1]] = big
    return out


def title_backgrounds():
    """title_mist.png(발판 없는 배경), title_flash_<n>.png(대비 판 셋, 번갯줄기 자리만 다르다), title_glow.png(잔광 판). 1920x1080, 불투명.
    title_bolt_<n>.png: 대비 판 n의 줄기만 같은 자리에 (1920x1080, 줄기 밖은 알파 0, 알파 0/255)."""
    import make_title_plate as tp
    base = tp.background(ledge=False)
    base.save(os.path.join(BG, 'title_mist.png'))
    W, H = base.size
    far = np.array(Image.open(os.path.join(BG, 'far_cell.png')).convert('RGB'))
    mid = np.array(Image.open(os.path.join(BG, 'mid_cell.png')).convert('RGBA'))
    line = skyline(far)
    sky = np.zeros((H, W), bool)
    sky[:tp.FAR_DROP] = True                                   # 원경을 내린 위쪽 빈 곳 = 하늘
    rows = np.arange(H - tp.FAR_DROP)[:, None]
    sky[tp.FAR_DROP:] = rows < line[None, :W]
    off = (mid.shape[1] - W) // 2
    sky &= mid[:, off:off + W, 3] == 0                         # 중경(지붕·전선·관)은 실루엣
    sky &= ~logo_silhouette(H, W)                             # R1: 로고 둘레는 실루엣 (흰 하늘 위 회색 그늘 대신)
    flash = np.where(sky[:, :, None], SKY_WHITE, SILHOUETTE).astype(np.uint8)
    # 2px 격자: 2x2 칸이 모두 하늘이어야 그 칸에 줄기가 보인다 (줄기 가림도 도트 단위)
    sky2 = sky[0::2, 0::2] & sky[1::2, 0::2] & sky[0::2, 1::2] & sky[1::2, 1::2]
    sky2 = sky2.repeat(2, 0).repeat(2, 1)
    made = []
    for n in range(1, len(BOLT_SPOTS) + 1):                # 번갯줄기는 하늘이 보이는 곳에만 (건물·전선 뒤에서 친다)
        plate = flash.copy()
        b1, x0, top = long_bolt(n)
        b = b1.repeat(2, 0).repeat(2, 1)
        if top < 0:                                         # 화면 위로 넘친 부분은 자른다
            b, top = b[-top:], 0
        box = (slice(top, top + b.shape[0]), slice(x0, x0 + b.shape[1]))
        on = (b[:, :, 3] > 0) & sky2[box]
        rgb = b[:, :, :3].copy()
        for src, dst in BOLT_COLORS.items():
            rgb[(b[:, :, :3] == src).all(axis=2)] = dst
        assert all(tuple(c) in BOLT_COLORS for c in b[b[:, :, 3] > 0][:, :3]), '줄기 원본에 모르는 색'
        plate[box][on] = rgb[on]
        Image.fromarray(plate, 'RGB').save(os.path.join(BG, f'title_flash_{n}.png'), optimize=True)
        made.append(f'backgrounds/title_flash_{n}.png')
        only = np.zeros((H, W, 4), np.uint8)                # 같은 자리, 같은 하늘 가림의 줄기만
        only[box][on] = np.concatenate([rgb, np.full(rgb.shape[:2] + (1,), 255, np.uint8)], axis=2)[on]
        Image.fromarray(only, 'RGBA').save(os.path.join(BG, f'title_bolt_{n}.png'), optimize=True)
        made.append(f'backgrounds/title_bolt_{n}.png')
    glow = np.clip(np.array(base).astype(int) + GLOW_ADD + (np.array(base).astype(int) * 0.25).astype(int), 0, 255)
    # RGBA로 저장한다: RGB 그림은 텍스처 섞기가 꺼져 실행 중 불투명도(opacify)가 먹지 않는다 (잔광이 서서히 옅어져야 한다)
    Image.fromarray(glow.astype(np.uint8), 'RGB').convert('RGBA').save(os.path.join(BG, 'title_glow.png'), optimize=True)
    return ['backgrounds/title_mist.png', 'backgrounds/title_glow.png'] + made


def bolts():
    """번갯줄기 셋 (PixelLab create_image_pro_flash 64x160, seed 31~33) -> ui/um_bolt_<n>.png (2배)."""
    made = []
    for n, seed in enumerate((31, 32, 33), 1):
        a = load(os.path.join(PX, 'ui_mist_v1', 'raw', f'bolt_s{seed}.png'))
        a[a[:, :, 3] < 128] = 0
        a[a[:, :, 3] > 0, 3] = 255
        ys, xs = np.nonzero(a[:, :, 3])
        made.append(save2(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], f'um_bolt_{n}.png'))
    return made


# ----- 플레이 중 HUD (2026-11-27 H1, docs/opus/TASKS.md '4차'): 증강 카드(A 안개 미니멀)와 같은 말투 -----
# 판 = 가는 테두리 한 줄(도트 1칸 = 화면 2px) + 안쪽 어두운 바탕. 바탕은 실행 중 코드가 한 장으로 깐다(카드와 같은 색·불투명도).
# 리벳·두꺼운 금속 틀·입체 테두리·경고 줄무늬·잘린 철판 모서리 없음. 테두리 색: 기본 회백 한 가지, 지금 것 = 밝은 회백,
# 청록 = 헤이즈에만, 빨강 = 위험·저주에만, 금 = 합성·보상에만, 강화 단계 색 = E 칸(1~3단계). 경고 노랑은 쓰지 않는다.
HUD_FRAME = 8                                   # 9칸 테두리 그림 한 변 (1배 도트. 화면 16px). 모서리 2도트(화면 4px)
HUD_TONES = {
    'line': (128, 137, 152),                    # 기본: 차분한 회백
    'dim': (70, 78, 94),                        # 들고 있지 않은 칸·준비 안 된 칸
    'hot': (222, 228, 236),                     # 지금 것 (든 무기 칸)
    'red': (226, 58, 72),                       # 위험·저주
    'cyan': (46, 230, 214),                     # 헤이즈
    'gold': (240, 180, 50),                     # 합성·보상
    'e1': (200, 160, 255), 'e2': (255, 206, 92), 'e3': (255, 96, 110),   # config.ENHANCE_LEVEL_COLOR (E 칸 강화 단계)
    # H2(11/27): 위험·페이드 맥박이 켜진 프레임의 게이지 테두리 (ui.ZONE_COLOR와 같은 색. 예전 바깥 띠가 쓰던 색)
    'crit': (250, 165, 80), 'fade': (240, 96, 104),
}
PULSE_THICK = ('crit', 'fade')                  # 이 색들은 굵은 테두리(um_hud_frame_<색>_thick, 선 2도트)도 굽는다
# 막대 속: 한 색 + 위 1도트 밝은 줄 (철판 막대의 마디·아래 그늘 없이). 색은 철판 막대의 바탕색 그대로(뜻이 같게)
HUD_FILLS = {
    'red': ((226, 58, 72), (255, 120, 128)), 'orange': ((236, 128, 48), (255, 178, 100)),
    'gray': ((128, 137, 152), (170, 178, 192)), 'cyan': ((46, 230, 214), (160, 248, 238)),
    'white': ((216, 221, 230), (240, 244, 250)), 'boss': ((214, 52, 52), (255, 120, 110)),
    'blue': ((92, 134, 220), (140, 176, 240)), 'violet': ((150, 118, 236), (196, 170, 255)),
    'empty': ((22, 26, 36), (22, 26, 36)),
}
FILL_W = 512                                    # 1배 도트 (화면 1024px, 철판 막대와 같은 길이)
HUD_FILL_HEIGHTS = (8, 12, 16, 20, 24)
INK = (8, 10, 16)                               # 작은 표시의 어두운 윤곽 (밝은 벽 위에서도 보이게)


def _rgba(c):
    return (*c, 255)


def hud_frames():
    """um_hud_frame_<tone>.png: 테두리 한 줄만, 속은 투명 (바탕은 hud_kit이 한 장으로 깐다)."""
    made = []
    n = HUD_FRAME
    for tone, c in HUD_TONES.items():
        a = np.zeros((n, n, 4), np.uint8)
        a[0, :], a[-1, :], a[:, 0], a[:, -1] = _rgba(c), _rgba(c), _rgba(c), _rgba(c)
        made.append(save2(a, f'um_hud_frame_{tone}.png'))
    for tone in PULSE_THICK:                      # H2: 맥박이 켜진 프레임의 게이지 테두리는 그 순간만 한 단계 굵게 (도트 2칸 = 화면 4px)
        c = HUD_TONES[tone]
        a = np.zeros((n, n, 4), np.uint8)
        a[:2, :], a[-2:, :], a[:, :2], a[:, -2:] = _rgba(c), _rgba(c), _rgba(c), _rgba(c)
        made.append(save2(a, f'um_hud_frame_{tone}_thick.png'))
    return made


def hud_fills():
    made = []
    for name, (main, light) in HUD_FILLS.items():
        for h in HUD_FILL_HEIGHTS:
            a = np.zeros((h // 2, FILL_W, 4), np.uint8)
            a[:, :] = _rgba(main)
            a[0, :] = _rgba(light)
            made.append(save2(a, f'um_fill_{name}_{h}.png'))
    return made


def hud_marks():
    """작은 표시: 대시 칸(켜짐·꺼짐), 철파이프 콤보 칸(켜짐·꺼짐·마무리), E 강화 단계 점 자리. 철판 것과 크기가 같다."""
    made = []
    line, dim, hot = HUD_TONES['line'], HUD_TONES['dim'], HUD_TONES['hot']
    well = (9, 12, 21)

    def box(w, h, edge, inside):
        a = np.zeros((h, w, 4), np.uint8)
        a[:, :] = _rgba(edge)
        a[1:-1, 1:-1] = _rgba(inside)
        return a

    for on in (True, False):                     # 대시 칸 14x9 도트: 가는 테두리 + 겹친 꺾쇠 둘(>>)
        a = box(14, 9, hot if on else dim, well)
        chev = hot if on else dim
        for ox in (4, 8):
            for dy, dx in ((-2, 0), (-1, 1), (0, 2), (1, 1), (2, 0)):
                a[4 + dy, ox + dx] = _rgba(chev)
        made.append(save2(a, f'um_dash_{"on" if on else "off"}.png'))
    # 콤보 칸 11x11 도트: 켜짐 = 밝은 회백 속, 꺼짐 = 어두운 속 + 흐린 테두리, 마무리 = 빨강 속 (철판과 같은 뜻)
    for name, edge, inside in (('on', INK, hot), ('off', dim, well), ('fin', INK, (226, 58, 72))):
        a = np.zeros((11, 11, 4), np.uint8)
        a[1:10, 1:10] = _rgba(edge)
        a[2:9, 2:9] = _rgba(inside)
        made.append(save2(a, f'um_combo_{name}.png'))
    a = np.zeros((5, 5, 4), np.uint8)             # 단계 점 자리 5x5 도트: 흐린 테두리
    a[:, :] = _rgba(dim)
    a[1:4, 1:4] = _rgba(well)
    made.append(save2(a, 'um_dot_off.png'))
    return made


def step_parts():
    """증강 카드의 진행 칸 (R1, 11/27): 철판 칸 up_step_off와 같은 크기(12x6 도트 = 화면 24x12)의 가는 테두리 한 줄 + 어두운 속.
    off = 기본 회백 테두리, on = 밝은 회백 테두리(찬 칸. 속은 실행 중 코드가 갈래 색으로 채운다 — 색의 뜻은 그대로)."""
    made = []
    for name, edge in (('off', HUD_TONES['line']), ('on', HUD_TONES['hot'])):
        a = np.zeros((6, 12, 4), np.uint8)
        a[:, :] = _rgba(edge)
        a[1:-1, 1:-1] = _rgba((9, 12, 21))
        made.append(save2(a, f'um_step_{name}.png'))
    return made


# ----- 메뉴 화면 (2026-11-27 M1, docs/opus/TASKS.md '4차'): 일시정지·설정·키 설정·결과·크레딧을 타이틀(감시 단말)과 한 벌로 -----
# 글자 뒤 어둠 조각 시트 assets/light/menu_shade_<이름>.png: 타이틀 title_shade와 같은 식(글자 상자에서 거리 d만큼 떨어지면
# k * exp(-(d/sigma)^2))을 한 상자에 대해 굽고, 9칸(네 모서리·네 변·가운데)으로 나눠 어떤 크기 상자에도 이어 붙인다(src/mist_menu.shade).
# 변 조각은 길이 방향으로 값이 같아 이어 붙여도 이음매가 없고, 가운데는 k 한 색이라 실행 중 사각형 한 장으로 깐다.
# 겹치는 상자는 같은 색을 알파로 겹쳐 1 - (1-a1)(1-a2)... (타이틀 시트를 구울 때와 같은 식). 절반 크기로 굽고 화면에는 2배 (빛 층 예외).
MENU_SHADES = {'soft': (0.80, 64), 'wide': (0.80, 130)}       # 이름 -> (가장 진한 곳 k, 번지는 거리 sigma 화면 px)
SHADE_MID = 64                                               # 시트 가운데(상자) 한 변 (절반 크기 px. 화면 128px)
# 키 글자 판·음량 막대 테두리와 속: 타이틀 인광색 (title_mode.PH 계열, src/mist_menu.py)
MENU_TONES = {'ph': (168, 240, 200), 'ph_dim': (60, 110, 100)}
MENU_FILLS = {'phos': ((112, 170, 150), (168, 240, 200))}


def shade_radius(sigma):
    """조각 시트의 번지는 폭 (절반 크기 px): exp(-(d/sigma)^2)가 1/255 아래로 떨어지는 거리까지."""
    return int(math.ceil(2.4 * sigma / 2))


def menu_shade(name):
    k, sigma = MENU_SHADES[name]
    r, m = shade_radius(sigma), SHADE_MID
    n = 2 * r + m
    idx = (np.arange(n) + 0.5) * 2                               # 화면 px (가운데 = 상자 [2r, 2r+2m])
    lo, hi = 2 * r, 2 * (r + m)
    dx = np.maximum(np.maximum(lo - idx, idx - hi), 0)
    d = np.sqrt(dx[None, :] ** 2 + dx[:, None] ** 2)
    alpha = k * np.exp(-(d / sigma) ** 2)
    a8 = np.round(alpha * 255).astype(np.uint8)
    a8[a8 < 3] = 0
    out = np.zeros((n, n, 4), np.uint8)
    out[:, :, :3] = SHADE_COLOR
    out[:, :, 3] = a8
    Image.fromarray(out, 'RGBA').save(os.path.join(LIGHT, f'menu_shade_{name}.png'), optimize=True)
    return f'light/menu_shade_{name}.png'


def menu_parts():
    made = [menu_shade(name) for name in MENU_SHADES]
    n = HUD_FRAME
    for tone, c in MENU_TONES.items():                           # um_hud_frame_ph·ph_dim: HUD 테두리와 같은 한 줄
        a = np.zeros((n, n, 4), np.uint8)
        a[0, :], a[-1, :], a[:, 0], a[:, -1] = _rgba(c), _rgba(c), _rgba(c), _rgba(c)
        made.append(save2(a, f'um_hud_frame_{tone}.png'))
    for name, (main, light) in MENU_FILLS.items():               # um_fill_phos_<높이>: HUD 막대 속과 같은 모양
        for h in HUD_FILL_HEIGHTS:
            a = np.zeros((h // 2, FILL_W, 4), np.uint8)
            a[:, :] = _rgba(main)
            a[0, :] = _rgba(light)
            made.append(save2(a, f'um_fill_{name}_{h}.png'))
    return made


# ----- 고르는 화면 (2026-11-27 S1, docs/opus/TASKS.md '4차'): 은신처 NPC 창 넷을 증강 카드와 한 벌로 -----
# 줄 고르기는 M1처럼 글자 폭만 색을 뒤집고 앞에 커서. 감시 단말 커서(um_cursor, 청록·인광)는 카드 말투와 맞지 않아
# 카드의 밝은 회백(고른 카드 테두리 um_hud_frame_hot과 같은 색)으로 작은 삼각 커서를 코드로 찍는다. _off는 살 수 없는 줄.
PICK_TONES = {'um_pick_cursor': (222, 228, 236), 'um_pick_cursor_off': (112, 120, 138)}   # src/mist_pick.HOT_BG / HOT_OFF


def pick_parts():
    made = []
    for name, c in PICK_TONES.items():
        a = np.zeros((11, 6, 4), np.uint8)                        # 도트 6x11 (화면 12x22): 오른쪽을 가리키는 삼각
        for y in range(11):
            a[y, :min(y, 10 - y) + 1] = _rgba(c)
        made.append(save2(a, f'{name}.png'))
    return made


# ----- 무기·E 패널 시안 셋 (2026-11-27 W1, docs/opus/TASKS.md '4차' W1): config.HUD_WEAPON_STYLE = 'a'·'b'·'c' -----
# 사용자 "무기, E 나오는 UI창이 너무 밋밋하게 변경이 되었는데 조금의 특색이 들어가면 좋겠다". 네모 셋 대신 실루엣·크기의 위계·세계의 소재.
# 판은 모두 테두리 한 줄(도트 1칸 = 화면 2px) + 속까지 칠한 불투명한 어두운 바탕(카드와 같은 색)을 한 장으로 굽는다(실행 중 겹쳐 그리지 않는다).
# 색: 기본 회백 line, 지금 것 hot, 흐린 것, 헤이즈 결정만 청록, 강화 단계 색은 강화에만. 경고 노랑·리벳·철판 없음.
#  a '결정 소켓': E = 마름모 소켓에 박힌 헤이즈 결정(쓸 수 있음 = 결정이 참, 못 씀 = 빈 소켓, 켬 = 단계 색). 단계 = 소켓 둘레 결정 조각 셋.
#                무기 칸 = 두 모서리를 깎은 결정 면(든 칸이 크다).
#  b '감시 단말': 칸을 닫지 않고 네 귀퉁이 꺾쇠(타이틀 um_bracket 말투) + 주사선 바탕. 든 칸 = 긴 꺾쇠, 다른 칸 = 짧은 꺾쇠.
#                E = 둥근 조준 계기(못 씀 = 끊긴 원, 쓸 수 있음 = 이어진 원 + 눈금, 켬 = 단계 색). 단계 = 원 위 호 셋.
#  c '문장':     세 칸을 한 덩어리로. 가운데 마름모 E 문장 앞에, 양옆에 방패 모양 무기 칸이 물리고(든 칸이 크다),
#                증강 카드의 장식선 말투로 가로선이 덩어리 위를 지나 무기 이름 줄과 잇는다. 단계 = 가로선 위 작은 마름모 셋.
WP_WELL = (9, 12, 21)
WP_SCAN = (14, 19, 31)                                  # b 주사선 (바탕보다 조금 밝은 줄)
WP_LINE, WP_DIM, WP_HOT = HUD_TONES['line'], HUD_TONES['dim'], HUD_TONES['hot']
WP_GHOST = (96, 106, 124)                               # 빈 결정·꺼진 단계 표시의 윤곽 (색 없는 빈 모양. 어두운 방에서도 보이게 dim보다 밝게)
WP_TIER = {1: HUD_TONES['e1'], 2: HUD_TONES['e2'], 3: HUD_TONES['e3']}
# 헤이즈 결정 (쓸 수 있음): 카드 청록 단계를 한 단 낮춰 든 무기 칸보다 눈에 덜 띄게
WP_HAZE = ((92, 210, 200), (26, 146, 140), (12, 96, 94), (6, 52, 56))


def _mix(c, d, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c, d))


def _tier_ramp(c):
    """강화 단계 색 -> (밝음, 몸, 그늘, 윤곽)."""
    return (_mix(c, (255, 255, 255), 0.5), c, _mix(c, (0, 0, 0), 0.42), _mix(c, (0, 0, 0), 0.72))


def _grid(h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    return yy + 0.5, xx + 0.5


def _edge(mask):
    """마스크의 바깥 한 줄 (4방향 이웃 중 하나라도 밖이면 가장자리)."""
    m = np.pad(mask, 1)
    inner = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    return mask & ~inner


def _put(a, mask, c):
    a[mask] = _rgba(c)


def _diamond(h, w, cy, cx, ry, rx):
    yy, xx = _grid(h, w)
    return np.abs(yy - cy) / ry + np.abs(xx - cx) / rx <= 1.0 + 1e-6


def _plate(mask, line, well=WP_WELL):
    """테두리 한 줄 + 속은 불투명한 바탕."""
    a = np.zeros(mask.shape + (4,), np.uint8)
    _put(a, mask, well)
    _put(a, _edge(mask), line)
    return a


def _crystal(ramp, hollow=False):
    """헤이즈 결정 12x26 도트 (위아래가 뾰족한 육각 기둥). 왼쪽 면 밝음, 오른쪽 면 몸, 가운데 모서리 밝은 줄, 윤곽 그늘.
    hollow: 속을 비운 윤곽만 (빈 소켓). 이때 ramp는 한 색."""
    h, w = 26, 12
    yy, xx = _grid(h, w)
    d = np.abs(xx - 6)
    mask = ((yy >= 6) & (yy <= 20)) | ((yy < 6) & (d <= yy)) | ((yy > 20) & (d <= 26 - yy))
    a = np.zeros((h, w, 4), np.uint8)
    edge = _edge(mask)
    if hollow:
        _put(a, edge, ramp)
        return a
    light, body, shade, rim = ramp
    _put(a, mask & (xx < 6), light)
    _put(a, mask & (xx >= 6), body)
    _put(a, mask & (np.abs(xx - 6.5) < 0.6) & (yy > 4) & (yy < 22), _mix(light, (255, 255, 255), 0.4))
    _put(a, edge & (xx >= 6), shade)
    _put(a, edge & (xx < 6), _mix(light, shade, 0.5))
    _put(a, edge & ((yy < 2) | (yy > 24)), rim)
    return a


def _shard(c, on):
    """작은 결정 조각 6x11 도트 (단계 표시). on: 단계 색으로 참 / off: 흐린 윤곽 + 어두운 속."""
    m = _diamond(11, 6, 5.5, 3.0, 5.5, 3.0)
    if not on:
        return _plate(m, WP_GHOST)
    light, body, shade, rim = _tier_ramp(c)
    yy, xx = _grid(11, 6)
    a = np.zeros((11, 6, 4), np.uint8)
    _put(a, m, body)
    _put(a, m & (xx < 3.0), light)
    _put(a, _edge(m) & (xx > 3.0), shade)
    return a


def _facet(n, line):
    """a 무기 칸: n x n 도트, 오른쪽 위·왼쪽 아래 모서리를 4도트 비스듬히 깎은 결정 면."""
    yy, xx = _grid(n, n)
    k = 5
    mask = ~(((n - xx) + yy < k) | (xx + (n - yy) < k))          # 그림의 위 = 화면 위: 오른쪽 위 / 왼쪽 아래를 깎는다
    return _plate(mask, line)


def _socket(tone):
    """a E 소켓: 56x56 도트 캔버스 가운데 52x52 마름모. 겉 테두리 한 줄 + 5도트 안쪽에 흐린 자리 선(결정이 박히는 자리).
    단계 색이면 겉에 그늘 색 한 줄을 더 둘러 빛나 보이게."""
    n = 56
    tier = tone in WP_TIER.values()
    outer = _diamond(n, n, 28, 28, 26, 26)
    seat = _diamond(n, n, 28, 28, 21, 21)
    a = _plate(outer, tone)
    _put(a, _edge(seat), _mix(tone, WP_WELL, 0.55) if tier else WP_DIM)
    if tier:
        halo = _diamond(n, n, 28, 28, 27.5, 27.5)
        _put(a, _edge(halo) & ~outer, _mix(tone, (0, 0, 0), 0.45))
    return a


def _brackets(n, arm, c):
    """b 꺾쇠 넷: n x n 도트 캔버스의 네 귀퉁이에 팔 길이 arm 도트, 두께 1 도트. 속은 비어 있다."""
    a = np.zeros((n, n, 4), np.uint8)
    for ys, xs in ((0, 0), (0, n - arm), (n - 1, 0), (n - 1, n - arm)):
        a[ys, xs:xs + arm] = _rgba(c)
    for xs, ys in ((0, 0), (n - 1, 0), (0, n - arm), (n - 1, n - arm)):
        a[ys:ys + arm, xs] = _rgba(c)
    return a


def _scan(n):
    """b 칸 바탕: 불투명한 어두운 바탕 + 세 도트마다 한 줄 조금 밝은 주사선."""
    a = np.zeros((n, n, 4), np.uint8)
    a[:, :] = _rgba(WP_WELL)
    a[1::3, :] = _rgba(WP_SCAN)
    return a


def _dial(state):
    """b E 계기: 56x56 도트 캔버스, 반지름 23.5 원(두께 1) + 속은 불투명한 바탕. 상하좌우 안쪽 눈금 3도트.
    state: 'low' = 끊긴 원(30도마다 20도 선, 10도 틈) 회백, 눈금 없음 / 'line' = 이어진 원 + 눈금 / 단계 색 = 그 색 원 + 눈금 + 바깥 그늘."""
    n, c, r = 56, 28.0, 23.5
    yy, xx = _grid(n, n)
    d = np.hypot(yy - c, xx - c)
    disk = d <= r + 0.5
    ring = _edge(disk)
    a = np.zeros((n, n, 4), np.uint8)
    _put(a, disk, WP_WELL)
    if state == 'low':
        ang = (np.degrees(np.arctan2(yy - c, xx - c)) + 360 + 10) % 360
        _put(a, ring & ((ang % 30) < 20), WP_LINE)
        return a
    col = WP_LINE if state == 'line' else state
    _put(a, ring, col)
    tick = _mix(col, WP_WELL, 0.25)
    for k in range(4):                                         # 상하좌우 눈금: 원 안쪽에서 가운데 쪽으로 4도트, 굵기 2도트
        a[6 + k, 27:29] = a[49 - k, 27:29] = _rgba(tick)
        a[27:29, 6 + k] = a[27:29, 49 - k] = _rgba(tick)
    if state != 'line':
        _put(a, _edge(d <= r + 1.5) & ~disk, _mix(col, (0, 0, 0), 0.45))
    return a


def _arc(i, c):
    """b 단계 호: 계기와 같은 56x56 캔버스, 반지름 26~28의 원 위쪽 호 하나(두께 2도트) (i = 0 왼쪽, 1 가운데, 2 오른쪽). 각 26도."""
    n, cc = 56, 28.0
    yy, xx = _grid(n, n)
    d = np.hypot(yy - cc, xx - cc)
    ang = np.degrees(np.arctan2(cc - yy, xx - cc))               # 위 = 90도
    mid = (138, 90, 42)[i]
    m = (d >= 25.8) & (d <= 27.9) & (np.abs(ang - mid) <= 13)
    a = np.zeros((n, n, 4), np.uint8)
    _put(a, m, c)
    return a


def _shield(w, h, line):
    """c 무기 칸: 방패 모양 (위 평평, 옆은 아래 0.62까지 곧고, 거기서 아래 가운데 뾰족 끝으로)."""
    yy, xx = _grid(h, w)
    k = h * 0.62
    half = w / 2
    lim = np.where(yy <= k, half, half * (h - yy) / (h - k))
    return _plate(np.abs(xx - half) <= lim + 1e-6, line)


def _crest(tone, inner):
    """c E 문장: 48x58 도트 마름모. 겉 테두리 + (inner면) 안쪽 마름모 한 줄. 단계 색이면 속 마름모를 단계 색 그늘로 칠한다."""
    h, w = 58, 48
    tier = tone in WP_TIER.values()
    outer = _diamond(h, w, 29, 24, 29, 24)
    core = _diamond(h, w, 29, 24, 23.5, 19.4)
    a = _plate(outer, tone)
    if tier:
        _put(a, core, _mix(tone, WP_WELL, 0.78))
        _put(a, _edge(core), _mix(tone, WP_WELL, 0.35))
    elif inner:
        _put(a, _edge(core), WP_DIM)
    return a


def _rule(c, ends=True):
    """c 가로선 122x7 도트: 가운데 줄 한 줄 + 양끝 장식(증강 카드 장식선 말투: 끝에서 떨어진 점 둘). ends=False면 줄만 (강화 시간 채움)."""
    w, h = 122, 7
    a = np.zeros((h, w, 4), np.uint8)
    a[3, 8:w - 8] = _rgba(c)
    if ends:
        for x0, x1 in ((1, 2), (4, 6), (w - 6, w - 4), (w - 2, w - 1)):
            a[3, x0:x1] = _rgba(c)
    return a


def _pip(c, on):
    """c 단계 표시 7x7 도트 마름모."""
    m = _diamond(7, 7, 3.5, 3.5, 3.5, 3.5)
    if not on:
        return _plate(m, WP_GHOST)
    a = np.zeros((7, 7, 4), np.uint8)
    _put(a, m, c)
    _put(a, _diamond(7, 7, 3.5, 3.5, 1.5, 1.5), _mix(c, (255, 255, 255), 0.5))
    return a


WP_SIZES = {'a': (48, 38), 'b': (46,), 'c': ((50, 54), (38, 42))}     # 칸 크기 (도트). a·c는 (든 칸, 다른 칸), c는 (폭, 높이)


# ----- W2 시안 D '떠 있는 칸' (2026-11-27, docs/opus/TASKS.md '4차' W2): 사용자가 참고 그림과 함께 "이런 느낌 안되나?" -----
# 칸이 하나씩 따로 떠 있다: 칸마다 바탕(한 색, 실행 중 불투명도를 낮춰 반투명으로 그린다)과 테두리(속 투명)를 따로 굽는다.
# 든 칸 테두리 = 그 무기의 색을 밝힌 선 + 안쪽에 무기 색 한 줄(빛), 들지 않은 칸 = 회백 한 줄. E 칸은 왼쪽 위를 깎은 정사각, 켜면 단계 색.
# 칸 바깥에 반쯤 걸치는 동그란 키 배지(불투명), E 칸 모서리의 단계 배지(둥근 네모, 단계 색으로 차고 숫자는 실행 중 글자).
D_SLOT = (50, 32)                       # 무기 칸 (도트. 화면 100x64)
D_E = 42                                # E 칸 한 변 (도트. 화면 84)
D_KEY = 16                              # 키 배지 지름 (도트. 화면 32)
D_LV = 13                               # 단계 배지 한 변 (도트. 화면 26)
D_IDLE = (120, 128, 144)                # 들지 않은 칸 테두리 (밝기 약 127: H2 기준 120 이상, 든 칸보다 60 넘게 어둡다)
D_WELL = (9, 12, 21)
D_KEY_FILL = (16, 20, 31)


def _weapon_colors():
    """무기의 색 = src/combo.py COLORS (교체기 막대·각인 빛과 같은 색). 굽는 도구가 게임 모듈 전체를 불러오지 않게 그 줄만 읽는다."""
    import ast
    src = open(os.path.join(ROOT, 'src', 'combo.py'), encoding='utf-8').read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'COLORS':
            return ast.literal_eval(node.value)
    raise RuntimeError('combo.COLORS 없음')


def _round_rect(h, w, r):
    """모서리를 r 도트만큼 둥글게 깎은 사각 마스크 (도트 원 모양 모서리)."""
    yy, xx = _grid(h, w)
    cy = np.clip(yy, r, h - r)
    cx = np.clip(xx, r, w - r)
    return np.hypot(yy - cy, xx - cx) <= r + 0.1


def _cut_rect(n, k):
    """n x n 사각, 왼쪽 위 모서리를 k 도트 비스듬히 깎는다 (나머지 셋은 1도트 둥글림)."""
    yy, xx = _grid(n, n)
    m = _round_rect(n, n, 1.5)
    return m & ~(xx + yy < k + 1)


def _frame_only(mask, outer, inner=None):
    a = np.zeros(mask.shape + (4,), np.uint8)
    e = _edge(mask)
    _put(a, e, outer)
    if inner is not None:
        _put(a, _edge(mask & ~e), inner)
    return a


def _well_only(mask):
    a = np.zeros(mask.shape + (4,), np.uint8)
    _put(a, mask, D_WELL)
    return a


def d_parts():
    made = []
    h, w = D_SLOT[1], D_SLOT[0]
    slot = _round_rect(h, w, 3)
    made.append(save2(_well_only(slot), 'um_wp_d_well.png'))
    made.append(save2(_frame_only(slot, D_IDLE), 'um_wp_d_slot_line.png'))
    for wid, c in _weapon_colors().items():                        # 든 칸: 무기 색을 반쯤 밝힌 겉선 + 무기 색 안쪽 선
        made.append(save2(_frame_only(slot, _mix(c, (255, 255, 255), 0.5), _mix(c, D_WELL, 0.35)), f'um_wp_d_slot_{wid}.png'))
    e = _cut_rect(D_E, 6)
    made.append(save2(_well_only(e), 'um_wp_d_e_well.png'))
    made.append(save2(_frame_only(e, WP_LINE), 'um_wp_d_e_line.png'))
    for lv, c in WP_TIER.items():
        made.append(save2(_frame_only(e, c, _mix(c, D_WELL, 0.45)), f'um_wp_d_e_e{lv}.png'))
    n = D_KEY                                                      # 키 배지: 불투명한 동그라미 + 테두리 한 줄
    yy, xx = _grid(n, n)
    disk = np.hypot(yy - n / 2, xx - n / 2) <= n / 2 - 0.2
    for name, c in (('hot', WP_HOT), ('line', D_IDLE)):
        a = np.zeros((n, n, 4), np.uint8)
        _put(a, disk, D_KEY_FILL)
        _put(a, _edge(disk), c)
        made.append(save2(a, f'um_wp_d_key_{name}.png'))
    m = _round_rect(D_LV, D_LV, 3)                                 # 단계 배지: 둥근 네모
    for lv, c in WP_TIER.items():
        a = np.zeros((D_LV, D_LV, 4), np.uint8)
        _put(a, m, c)
        _put(a, _edge(m), _mix(c, (0, 0, 0), 0.6))
        made.append(save2(a, f'um_wp_d_lv_e{lv}.png'))
    a = np.zeros((D_LV, D_LV, 4), np.uint8)
    _put(a, m, D_KEY_FILL)
    _put(a, _edge(m), WP_GHOST)
    made.append(save2(a, 'um_wp_d_lv_off.png'))
    return made


# ----- W3 무기·E 패널 확정 'da' = D 배치 + A 결정 소켓 (2026-11-27, docs/opus/TASKS.md '4차' W3) -----
# 소켓은 D의 다른 칸처럼 따로 떠 있게: 바탕(마름모 한 색, 실행 중 반투명)과 테두리(A 소켓의 겉선·자리 선·단계 색 빛, 속 투명)를 따로 굽는다.
# 결정은 A의 um_wp_a_crystal_*(빈 윤곽·단계 색)를 그대로 쓰고, 쓸 수 있는 청록 결정만 한 단 어둡게 다시 굽는다(um_wp_da_crystal_haze). '강화' 글자 밑 꼬리표 바탕(둥근 네모 한 색, 실행 중 반투명).
DA_TAG = (64, 14)                       # 꼬리표 (도트. 화면 128x28)
DA_HAZE = ((78, 186, 176), (22, 126, 120), (10, 82, 80), (6, 44, 46))   # 쓸 수 있는 헤이즈 결정 (WP_HAZE보다 한 단 어둡게)


def da_parts():
    made = []
    n = 56
    made.append(save2(_well_only(_diamond(n, n, 28, 28, 26, 26)), 'um_wp_da_socket_well.png'))
    for name, tone in (('line', WP_LINE), ('e1', WP_TIER[1]), ('e2', WP_TIER[2]), ('e3', WP_TIER[3])):
        a = _socket(tone)                                          # A 소켓에서 속 바탕만 비운다 (겉선·자리 선·빛은 그대로)
        well = (a[:, :, 3] > 0) & (a[:, :, :3] == WP_WELL).all(axis=2)
        a[well] = 0
        made.append(save2(a, f'um_wp_da_socket_{name}.png'))
    made.append(save2(_well_only(_round_rect(DA_TAG[1], DA_TAG[0], 3)), 'um_wp_da_tag_well.png'))
    made.append(save2(_crystal(DA_HAZE), 'um_wp_da_crystal_haze.png'))   # 쓸 수 있음: A보다 한 단 어둡게 (D 배치에서는 칸이 작아 결정이 든 무기 칸보다 먼저 눈에 띄었다)
    return made


# ----- W4 무기·E 패널 배치 다시 짜기 'row' (2026-11-27, docs/opus/TASKS.md '4차' W4, 조사 docs/REFERENCES.md) -----
# 한 줄, 아랫변 맞춤, 왼쪽부터 1·2·E. 든 칸은 크기(48x36 / 36x28 도트)·바탕 불투명도·아이콘 밝기·겉 테두리로 동시에 구분한다(색만 쓰지 않는다).
# 든 칸 테두리 = 밝은 회백 겉선(무기와 상관없이 같다) + 무기 색 안쪽 한 줄. 들지 않은 칸 = 회백 한 줄(밝기 약 127).
# E 결정 소켓은 W3(da)의 것을 한 변 88로 줄였다(마름모 반지름 22도트, 자리 선 18도트).
ROW_BIG, ROW_SMALL = (48, 36), (36, 28)     # 칸 (도트: 폭, 높이). 화면 96x72 / 72x56
ROW_SOCKET = 48                             # 소켓 캔버스 (도트. 화면 96, 마름모 88)


def _socket_small(tone, n=ROW_SOCKET, r=22, seat=18):
    """W3 소켓을 줄인 것: 겉선 한 줄 + 자리 선, 단계 색이면 바깥 그늘 한 줄. 속은 비어 있다(바탕은 따로)."""
    tier = tone in WP_TIER.values()
    c = n / 2
    outer = _diamond(n, n, c, c, r, r)
    a = np.zeros((n, n, 4), np.uint8)
    _put(a, _edge(outer), tone)
    _put(a, _edge(_diamond(n, n, c, c, seat, seat)), _mix(tone, WP_WELL, 0.55) if tier else WP_DIM)
    if tier:
        _put(a, _edge(_diamond(n, n, c, c, r + 1.5, r + 1.5)) & ~outer, _mix(tone, (0, 0, 0), 0.45))
    return a


def row_parts():
    made = []
    for (w, h), kind, rad in ((ROW_BIG, 'big', 3), (ROW_SMALL, 'small', 2)):
        made.append(save2(_well_only(_round_rect(h, w, rad)), f'um_wp_row_well_{kind}.png'))
    small = _round_rect(ROW_SMALL[1], ROW_SMALL[0], 2)
    made.append(save2(_frame_only(small, D_IDLE), 'um_wp_row_slot_line.png'))
    big = _round_rect(ROW_BIG[1], ROW_BIG[0], 3)
    for wid, c in _weapon_colors().items():                        # 든 칸: 밝은 회백 겉선(같은 색) + 무기 색 안쪽 한 줄
        made.append(save2(_frame_only(big, WP_HOT, c), f'um_wp_row_slot_{wid}.png'))
    made.append(save2(_well_only(_round_rect(14, 52, 3)), 'um_wp_row_tag_well.png'))   # '강화' 꼬리표 104x28
    for name, edge, inside in (('on', INK, WP_HOT), ('off', WP_GHOST, WP_WELL), ('fin', INK, (226, 58, 72))):   # W5: 든 칸 안 무기 표시 5x5 도트
        a = np.zeros((5, 5, 4), np.uint8)
        a[:, :] = _rgba(edge)
        a[1:4, 1:4] = _rgba(inside)
        made.append(save2(a, f'um_wp_row_combo_{name}.png'))
    n = ROW_SOCKET
    made.append(save2(_well_only(_diamond(n, n, n / 2, n / 2, 22, 22)), 'um_wp_row_socket_well.png'))
    for name, tone in (('line', WP_LINE), ('e1', WP_TIER[1]), ('e2', WP_TIER[2]), ('e3', WP_TIER[3])):
        made.append(save2(_socket_small(tone), f'um_wp_row_socket_{name}.png'))
    return made


def wp_parts():
    made = []
    # a 결정 소켓
    for n, kind in zip(WP_SIZES['a'], ('big', 'small')):
        for tone in ('hot', 'line'):
            made.append(save2(_facet(n, HUD_TONES[tone]), f'um_wp_a_slot_{kind}_{tone}.png'))
    for name, tone in (('line', WP_LINE), ('e1', WP_TIER[1]), ('e2', WP_TIER[2]), ('e3', WP_TIER[3])):
        made.append(save2(_socket(tone), f'um_wp_a_socket_{name}.png'))
    made.append(save2(_crystal(WP_HAZE), 'um_wp_a_crystal_haze.png'))
    made.append(save2(_crystal(WP_GHOST, hollow=True), 'um_wp_a_crystal_empty.png'))
    for lv, c in WP_TIER.items():
        made.append(save2(_crystal(_tier_ramp(c)), f'um_wp_a_crystal_e{lv}.png'))
        made.append(save2(_shard(c, True), f'um_wp_a_shard_e{lv}.png'))
    made.append(save2(_shard(None, False), 'um_wp_a_shard_off.png'))
    # b 감시 단말
    n = WP_SIZES['b'][0]
    made.append(save2(_scan(n), 'um_wp_b_well.png'))
    made.append(save2(_brackets(n, 11, WP_HOT), 'um_wp_b_bracket_hot.png'))
    made.append(save2(_brackets(n, 5, WP_LINE), 'um_wp_b_bracket_line.png'))
    for name, st in (('low', 'low'), ('line', 'line'), ('e1', WP_TIER[1]), ('e2', WP_TIER[2]), ('e3', WP_TIER[3])):
        made.append(save2(_dial(st), f'um_wp_b_dial_{name}.png'))
    for i in range(3):
        made.append(save2(_arc(i, WP_GHOST), f'um_wp_b_arc{i}_off.png'))
        made.append(save2(_arc(i, WP_TIER[i + 1]), f'um_wp_b_arc{i}_on.png'))
    # c 문장
    for (w, h), kind in zip(WP_SIZES['c'], ('big', 'small')):
        for tone in ('hot', 'line'):
            made.append(save2(_shield(w, h, HUD_TONES[tone]), f'um_wp_c_shield_{kind}_{tone}.png'))
    made.append(save2(_crest(WP_LINE, True), 'um_wp_c_crest_line.png'))
    made.append(save2(_crest(WP_LINE, False), 'um_wp_c_crest_low.png'))
    for lv, c in WP_TIER.items():
        made.append(save2(_crest(c, True), f'um_wp_c_crest_e{lv}.png'))
        made.append(save2(_rule(c, ends=False), f'um_wp_c_rule_e{lv}.png'))
        made.append(save2(_pip(c, True), f'um_wp_c_pip_e{lv}.png'))
    made.append(save2(_rule(WP_LINE), 'um_wp_c_rule_line.png'))
    made.append(save2(_pip(None, False), 'um_wp_c_pip_off.png'))
    made += d_parts()                             # W2 시안 D
    made += da_parts()                            # W3 확정 da (D 배치 + A 결정 소켓)
    made += row_parts()                           # W4 한 줄 배치 row (기본값)
    return made


def main():
    if '--pick' in sys.argv:                      # 고르는 화면 부품만 (S1)
        made = pick_parts()
        print(len(made), '개:', ', '.join(made))
        return
    if '--menu' in sys.argv:                      # 메뉴 화면 부품만 (M1)
        made = menu_parts()
        print(len(made), '개:', ', '.join(made))
        return
    if '--step' in sys.argv:                      # 증강 카드 진행 칸만 (R1)
        made = step_parts()
        print(len(made), '개:', ', '.join(made))
        return
    if '--storm' in sys.argv:                     # 타이틀 번개 판과 글자 뒤 어둠만 (R1)
        made = title_backgrounds() + [title_shade(), title_shade(flash=True)]
        print(len(made), '개:', ', '.join(made))
        return
    if '--wp' in sys.argv:                        # 무기·E 패널 시안 부품만 (W1)
        made = wp_parts()
        print(len(made), '개:', ', '.join(made))
        return
    made = hud_frames() + hud_fills() + hud_marks()
    if '--hud' in sys.argv:                       # HUD 부품만 (타이틀·카드 그림은 그대로 둔다)
        print(len(made), '개:', ', '.join(made))
        return
    made += card_frames() + parts() + bolts() + title_backgrounds()
    made.append(title_shade())
    made.append(title_shade(flash=True))
    made += menu_parts() + pick_parts() + wp_parts() + step_parts()
    print(len(made), '개:', ', '.join(made))


if __name__ == '__main__':
    main()
