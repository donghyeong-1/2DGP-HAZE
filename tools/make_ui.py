"""UI 판·막대·칸·버튼·키 그림을 코드로 그린다 (이미지 모델 없음, numpy + Pillow). code-drawn, 자체 제작.

v3 (2026-11-18): HUD와 메뉴를 같은 부품으로 다시 짠다. 크기가 변하는 판은 '9칸 나누기'로 그린다:
네 모서리는 그림을 그대로, 네 변은 같은 무늬 조각을 길이만큼 이어 붙이고, 가운데는 단색으로 채운다.
(늘이지 않고 이어 붙이므로 확대 금지 규칙에 맞다. docs/pixel_rules.md)

부품 (assets/ui/ui_*.png, 모두 1배 도트, 알파는 0 또는 255, 외곽선 #0b1020)
  kit_<종류>.png      9칸 판 (모서리 크기는 src/hud_kit.py의 KITS 표). panel 어두운 강철 판, plate 글자 받침,
                      frame 막대 틀, button / button_hot 메뉴 버튼(평소 / 고름), slot 무기 칸 판, banner 안내 띠
  fill_<색>_<높이>.png 막대 속 무늬 (가로 1024, 높이 8·12·16·20·24). 위는 밝고 아래는 어둡고 사선 광택. 게임은 필요한 너비만큼 잘라 쓴다
  gauge_end_l/r.png   헤이즈 게이지 양끝 장식 (결정을 문 집게)
  key_<글자>.png      키 모양 표시 (E Q F)
  shard_s.png         작은 헤이즈 조각 (조각 개수 옆)
  knob.png            설정 막대(슬라이더)의 손잡이
사용: python tools/make_ui.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'ui')

K = (11, 16, 32)
STEEL = [(18, 24, 40), (26, 34, 56), (38, 50, 78), (56, 72, 106), (86, 108, 150), (150, 176, 214)]   # 어두움 -> 밝음
WELL = (13, 18, 31)                  # 판 속
WELL2 = (17, 24, 40)
TEAL = [(22, 74, 102), (31, 106, 138), (63, 177, 207), (166, 236, 251), (234, 255, 255)]
GOLD = [(96, 70, 26), (170, 136, 48), (242, 210, 116), (255, 244, 196)]
WHITE = (235, 240, 250)

FILLS = {   # 막대 속 색: (어두움, 기본, 밝음)
    'red': ((120, 30, 46), (214, 64, 76), (255, 140, 140)),
    'blue': ((36, 62, 120), (76, 128, 210), (150, 196, 255)),
    'cyan': ((20, 104, 132), (56, 196, 228), (176, 246, 255)),
    'orange': ((150, 70, 24), (236, 140, 52), (255, 210, 130)),
    'empty': ((22, 28, 44), (34, 42, 64), (46, 56, 84)),
    'yellow': ((150, 110, 20), (236, 200, 60), (255, 244, 170)),
    'violet': ((70, 40, 140), (150, 100, 240), (226, 200, 255)),
    'white': ((120, 136, 166), (206, 218, 236), (255, 255, 255)),
    'boss': ((100, 20, 34), (196, 40, 58), (255, 120, 110)),
}


def blank(w, h):
    return np.zeros((h, w, 4), np.uint8)


def put(a, x0, y0, x1, y1, col):
    a[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = (*col, 255)


def save(a, name):
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, f'ui_{name}.png'))
    print('saved ui_' + name, a.shape[1], 'x', a.shape[0])


# ---------------------------------------------------------------- 9칸 판
def kit(size, corner, band, well, accent=None, rivet=True, gem=None, inner_line=True):
    """size x size 판 하나. 바깥 외곽선 1, 강철 띠 band(밝은 위·왼쪽, 어두운 아래·오른쪽), 안쪽 외곽선 1, 속 well."""
    a = blank(size, size)
    put(a, 0, 0, size - 1, size - 1, K)
    b = band
    put(a, 1, 1, size - 2, size - 2, STEEL[3])
    put(a, 1, 1, size - 2, 1, STEEL[5])                       # 윗변 빛
    put(a, 1, 2, size - 2, 2, STEEL[4])
    put(a, 1, 1, 1, size - 2, STEEL[4])                       # 왼변 빛
    put(a, 1, size - 2, size - 2, size - 2, STEEL[1])         # 아랫변 그늘
    put(a, size - 2, 2, size - 2, size - 2, STEEL[2])         # 오른변 그늘
    if inner_line:
        put(a, b, b, size - 1 - b, size - 1 - b, K)
    put(a, b + 1, b + 1, size - 2 - b, size - 2 - b, well)
    if accent:                                                # 안쪽 테두리 강조선 (고른 버튼·슬롯)
        put(a, b + 1, b + 1, size - 2 - b, b + 1, accent)
        put(a, b + 1, b + 1, b + 1, size - 2 - b, accent)
    if rivet:                                                 # 모서리 리벳
        for cx, cy in ((corner // 2, corner // 2), (size - 1 - corner // 2, corner // 2),
                       (corner // 2, size - 1 - corner // 2), (size - 1 - corner // 2, size - 1 - corner // 2)):
            if b >= 4:
                put(a, cx - 1, cy - 1, cx, cy, STEEL[5])
                put(a, cx, cy, cx, cy, STEEL[2])
    if gem:                                                   # 위 두 모서리의 작은 헤이즈 결정
        for cx in (corner // 2, size - 1 - corner // 2):
            cy = corner // 2
            pts = [(cx, cy - 3), (cx + 2, cy), (cx, cy + 3), (cx - 2, cy)]
            for y in range(cy - 3, cy + 4):
                half = 2 - abs(y - cy) * 2 // 3
                put(a, cx - half, y, cx + half, y, gem[2])
            put(a, cx - 1, cy - 2, cx - 1, cy - 1, gem[3])
            for x, y in pts:
                a[y, x] = (*K, 255)
    return a


def build_kits():
    save(kit(48, 16, 5, WELL, rivet=True, gem=TEAL), 'kit_panel')
    save(kit(24, 8, 3, WELL2, rivet=False), 'kit_plate')
    save(kit(16, 5, 2, WELL, rivet=False, inner_line=False), 'kit_frame')
    save(kit(36, 12, 4, (24, 32, 52), rivet=True), 'kit_button')
    save(kit(36, 12, 4, (30, 66, 86), accent=TEAL[3], rivet=True, gem=TEAL), 'kit_button_hot')
    save(kit(36, 12, 4, (16, 22, 36), rivet=True), 'kit_slot')
    save(kit(36, 12, 4, (20, 40, 54), accent=TEAL[2], rivet=True), 'kit_slot_hot')
    # 안내 띠: 양끝이 화살촉처럼 접힌 띠 (가운데는 단색)
    a = kit(32, 12, 3, (16, 22, 36), rivet=False)
    for y in range(32):                                       # 양옆 바깥을 깎아 띠 끝을 뾰족하게
        cut = abs(y - 15.5) * 0.5
        a[y, :int(cut)] = 0
        a[y, 32 - int(cut):] = 0
        if int(cut) < 32:
            a[y, int(cut)] = (*K, 255)
            a[y, 31 - int(cut)] = (*K, 255)
    save(a, 'kit_banner')


# ---------------------------------------------------------------- 막대 속
FILL_HEIGHTS = (8, 12, 16, 20, 24)


def build_fills():
    """막대 속 무늬를 높이마다 따로 만든다 (잘라 쓰기만 하고 늘이지 않는다)."""
    W = 1024
    for name, (dark, mid, light) in FILLS.items():
        for H in FILL_HEIGHTS:
            a = blank(W, H)
            for y in range(H):
                t = y / (H - 1)
                col = light if t < 0.2 else mid if t < 0.7 else dark
                put(a, 0, y, W - 1, y, col)
            put(a, 0, 0, W - 1, 0, tuple(min(255, c + 40) for c in light))      # 맨 위 한 줄 빛
            if H >= 12:
                for x0 in range(0, W, 10):                                      # 사선 광택 (위쪽 절반)
                    for k in range(H // 2):
                        x, y = x0 + k, 1 + k
                        if x < W:
                            a[y, x] = (*tuple(min(255, (c + l) // 2) for c, l in zip(mid, light)), 255)
            save(a, f'fill_{name}_{H}')


# ---------------------------------------------------------------- 게이지 끝 장식
def gauge_end(right=False):
    w, h = 44, 64
    a = blank(w, h)
    # 집게 몸통 (강철)
    put(a, 18, 8, 43, 55, K)
    put(a, 19, 9, 42, 54, STEEL[3])
    put(a, 19, 9, 42, 10, STEEL[5])
    put(a, 19, 53, 42, 54, STEEL[1])
    put(a, 36, 18, 43, 45, K)                                 # 게이지를 무는 턱
    put(a, 37, 19, 43, 44, STEEL[2])
    for y in (14, 49):                                        # 리벳
        put(a, 24, y, 25, y + 1, STEEL[5])
    # 결정 (청록)
    cx, cy = 14, 32
    for y in range(4, 61):
        half = int(12 * (1 - abs(y - cy) / 28.5) ** 0.9)
        if half <= 0:
            continue
        put(a, cx - half, y, cx + half, y, TEAL[2])
        put(a, cx - half, y, cx - 1, y, TEAL[3])
        put(a, cx + half - 2, y, cx + half, y, TEAL[1])
        a[y, cx - half - 1] = (*K, 255) if cx - half - 1 >= 0 else a[y, 0]
        a[y, cx + half + 1] = (*K, 255)
    a[3, cx] = (*K, 255)
    a[61, cx] = (*K, 255)
    put(a, cx - 4, 18, cx - 3, 30, TEAL[4])                   # 결정 속 빛줄기
    put(a, cx, 34, cx + 1, 40, TEAL[4])
    if right:
        a = a[:, ::-1].copy()
    return a


# ---------------------------------------------------------------- 키 표시
GLYPH = {
    'E': ['11111', '10000', '11110', '10000', '11111'],
    'Q': ['01110', '10001', '10001', '10011', '01111'],
    'F': ['11111', '10000', '11110', '10000', '10000'],
}


def keycap(ch):
    s = 34
    a = blank(s, s)
    put(a, 0, 2, s - 1, s - 1, K)
    put(a, 1, 3, s - 2, s - 2, STEEL[1])                      # 키 옆면
    put(a, 0, 0, s - 1, s - 5, K)
    put(a, 1, 1, s - 2, s - 6, STEEL[4])                      # 키 윗면
    put(a, 1, 1, s - 2, 1, STEEL[5])
    put(a, 3, 3, s - 4, s - 8, STEEL[3])
    g = GLYPH[ch]
    ox, oy = (s - 5 * 3) // 2, 6
    for r, row in enumerate(g):
        for c, bit in enumerate(row):
            if bit == '1':
                put(a, ox + c * 3, oy + r * 3, ox + c * 3 + 2, oy + r * 3 + 2, WHITE)
    return a


def shard_small():
    a = blank(24, 24)
    pts = [(12, 1), (18, 8), (16, 22), (8, 22), (6, 8)]
    for y in range(24):
        xs = []
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        if len(xs) >= 2:
            l, r = int(min(xs)), int(max(xs))
            put(a, l, y, r, y, TEAL[2])
            put(a, l, y, (l + r) // 2, y, TEAL[3])
            put(a, r - 1, y, r, y, TEAL[1])
            a[y, l - 1] = (*K, 255)
            a[y, min(23, r + 1)] = (*K, 255)
    put(a, 8, 23, 16, 23, K)
    a[0, 12] = (*K, 255)
    put(a, 10, 6, 10, 9, TEAL[4])
    return a


def knob():
    a = blank(22, 34)
    put(a, 0, 0, 21, 33, K)
    put(a, 1, 1, 20, 32, STEEL[4])
    put(a, 1, 1, 20, 2, STEEL[5])
    put(a, 1, 30, 20, 32, STEEL[2])
    for y in (11, 16, 21):                                    # 손잡이 홈
        put(a, 6, y, 15, y, STEEL[2])
        put(a, 6, y + 1, 15, y + 1, STEEL[5])
    return a


def dash_pip(on):
    """대시 칸: 기울어진 결정 막대 (켜지면 청록, 비면 어두운 강철)."""
    a = blank(28, 18)
    body, light, dark = (TEAL[2], TEAL[3], TEAL[1]) if on else (STEEL[2], STEEL[3], STEEL[1])
    for y in range(18):
        x0 = 6 - y // 3
        put(a, x0, y, x0 + 21, y, K)
        if 0 < y < 17:
            put(a, x0 + 1, y, x0 + 20, y, body)
            if y < 6:
                put(a, x0 + 1, y, x0 + 20, y, light)
            if y > 12:
                put(a, x0 + 1, y, x0 + 20, y, dark)
    if on:
        put(a, 9, 3, 14, 3, TEAL[4])
    return a


def combo_pip(state):
    """콤보 칸: 마름모. off 어두움, on 흰빛, fin 주황(3타 마무리)."""
    a = blank(22, 22)
    body, light = {'off': (STEEL[2], STEEL[3]), 'on': ((206, 218, 236), WHITE), 'fin': ((236, 140, 52), (255, 210, 130))}[state]
    for y in range(22):
        half = 10 - abs(y - 10.5) + 0.5
        h = int(half)
        if h <= 0:
            continue
        put(a, 11 - h, y, 10 + h, y, K)
        if h > 1:
            put(a, 12 - h, y, 9 + h, y, body)
            if y < 10:
                put(a, 12 - h, y, 10, y, light)
    return a


def marker():
    """게이지 현재 값 바늘: 위아래 삼각 + 가운데 줄."""
    a = blank(16, 40)
    for i in range(7):
        put(a, 8 - 1 - i, i, 8 + i, i, K)                    # 위 삼각 (아래를 가리킨다)
        if 0 < i < 6:
            put(a, 8 - i, i, 7 + i, i, WHITE)
        put(a, 8 - 1 - i, 39 - i, 8 + i, 39 - i, K)          # 아래 삼각 (위를 가리킨다)
        if 0 < i < 6:
            put(a, 8 - i, 39 - i, 7 + i, 39 - i, WHITE)
    put(a, 6, 6, 9, 33, K)
    put(a, 7, 7, 8, 32, WHITE)
    return a


def main():
    os.makedirs(OUT, exist_ok=True)
    build_kits()
    build_fills()
    save(gauge_end(False), 'gauge_end_l')
    save(gauge_end(True), 'gauge_end_r')
    for ch in GLYPH:
        save(keycap(ch), 'key_' + ch.lower())
    save(shard_small(), 'shard_s')
    save(knob(), 'knob')
    save(dash_pip(True), 'dash_on')
    save(dash_pip(False), 'dash_off')
    for st in ('off', 'on', 'fin'):
        save(combo_pip(st), 'combo_' + st)
    save(marker(), 'marker')


if __name__ == '__main__':
    main()
