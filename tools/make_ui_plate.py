"""UI 3차 '교도소 철판' 부품을 코드로 굽는다 (2026-11-26, docs/opus/TASKS.md 3차 O8). code-drawn.

지금 부품(assets/ui/uc_*.png, Gemini G06 결정형)과 **이름·크기가 같은** assets/ui/up_*.png를 만든다.
config.UI_SKIN = 'plate'이면 hud_kit이 up_*를, 'crystal'이면 예전 uc_*를 쓴다. 예전 그림은 지우지 않는다.

그리는 방식: 960x540 격자(1점 = 화면 2px)에 점을 직접 찍고 최근접 2배로 저장한다(캐릭터와 같은 도트 크기).
- 재질: 어두운 강철판, 명암 4단(면 FACE, 가운데 톤 MID, 밝은 모서리 HI, 어두운 모서리 LO). 위·왼쪽이 밝고 아래·오른쪽이 어둡다.
- 모양: 모서리를 잘라 낸 사각판, 귀퉁이 리벳, 긁힘·녹은 판 하나에 두세 군데. 빛 번짐·그라데이션·반투명 없음.
- 색 쓰임: 글자·표시 흰색, 고른 것 경고 노랑, 녹 주황은 작게, 빨강은 체력·위험·저주, 청록은 헤이즈에만, 금은 전설·강화 2단계에만.
시안(LOOK): 'clean' 리벳 귀퉁이만 / 'worn' 리벳 + 긁힘 둘셋 + 리벳 둘레 녹 / 'heavy' 변 가운데 리벳 + 긁힘·녹 더 + 두꺼운 테.

사용: python tools/make_ui_plate.py [--look clean|worn|heavy] [--out assets/ui] [--sheet 모아보기.png]
"""
import argparse
import os
import random

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(ROOT, 'assets', 'ui')

# ----- 팔레트 (TASKS.md 3차 디자인 기준) -----
FACE = (29, 34, 43)        # #1d222b 면
MID = (42, 48, 59)         # #2a303b 가운데 톤
HI = (59, 67, 82)          # #3b4352 밝은 모서리
LO = (12, 14, 19)          # #0c0e13 어두운 모서리
SHADE = (21, 25, 32)       # 아래·오른쪽 안쪽 그늘 (면과 LO 사이)
EDGE = (6, 7, 10)          # 바깥 윤곽
WHITE = (216, 221, 230)    # #d8dde6 스텐실 흰색
GREY = (138, 147, 163)     # #8a93a3 덜 중요한 글·꺼진 표시
YEL = (226, 178, 58)       # #e2b23a 경고 노랑 (고른 것)
YEL_LO = (138, 102, 26)
RUST = (164, 85, 42)       # #a4552a 녹
RUST_LO = (104, 52, 28)
RED = (226, 58, 72)        # #e23a48
RED_LO = (130, 28, 40)
RED_HI = (255, 120, 128)
CYAN = (46, 230, 214)      # #2ee6d6 헤이즈에만
CYAN_LO = (14, 120, 118)
CYAN_HI = (160, 248, 238)
GOLD = (240, 180, 50)      # #f0b432 전설·강화 2단계에만
GOLD_LO = (150, 98, 24)
GOLD_HI = (255, 222, 140)
BRASS = (182, 132, 52)

LOOKS = ('clean', 'worn', 'heavy')
LOOK = 'worn'


# ----- 1배 그림판 -----
class Pix:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)

    def put(self, x, y, c):
        """(x, y)는 왼쪽 위 기준. 판 밖은 무시."""
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.a[y, x] = (*c, 255)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c)

    def get(self, x, y):
        return self.a[y, x]

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = 0

    def save(self, name, out=UI, scale=2):
        im = Image.fromarray(self.a, 'RGBA')
        im.resize((self.w * scale, self.h * scale), Image.NEAREST).save(os.path.join(out, f'up_{name}.png'))
        return im


def inside_cut(x, y, w, h, cut):
    """모서리를 cut점 잘라 낸 판 안쪽인가."""
    for cx, cy in ((x, y), (w - 1 - x, y), (x, h - 1 - y), (w - 1 - x, h - 1 - y)):
        if cx + cy < cut:
            return False
    return True


def plate(p, x0, y0, w, h, cut=3, face=FACE, hi=HI, mid=MID, shade=SHADE, edge=EDGE, bevel=None):
    """철판 하나: 바깥 윤곽 1점, 위·왼쪽 밝은 테, 아래·오른쪽 그늘, 면. bevel=None이면 LOOK에 따라 1~2점."""
    bevel = bevel or (2 if LOOK == 'heavy' else 1)
    for y in range(h):
        for x in range(w):
            if not inside_cut(x, y, w, h, cut):
                continue
            edge_px = not (inside_cut(x - 1, y, w, h, cut) and inside_cut(x + 1, y, w, h, cut) and
                           inside_cut(x, y - 1, w, h, cut) and inside_cut(x, y + 1, w, h, cut)) or x in (0, w - 1) or y in (0, h - 1)
            if edge_px:
                c = edge
            else:
                d_top, d_left, d_bot, d_right = y - 1, x - 1, h - 2 - y, w - 2 - x
                # 잘린 모서리 사선 쪽도 테로 친다
                diag_tl = (x + y) - cut - 1
                diag_br = ((w - 1 - x) + (h - 1 - y)) - cut - 1
                diag_tr = ((w - 1 - x) + y) - cut - 1
                diag_bl = (x + (h - 1 - y)) - cut - 1
                lit = min(d_top, d_left, diag_tl, diag_tr if d_top < d_right else 99)
                dark = min(d_bot, d_right, diag_br, diag_bl if d_bot < d_left else 99)
                if lit < bevel and lit <= dark:
                    c = hi if lit == 0 else mid
                elif dark < bevel:
                    c = shade if dark == 0 else (shade if bevel == 1 else LO)
                else:
                    c = face
            p.put(x0 + x, y0 + y, c)


RIVET_HI = (100, 110, 128)     # 낡음·거침 시안의 리벳 머리 (깔끔 시안은 HI)


def rivet(p, x, y, rust=False):
    """리벳 2x2점(화면 4px): 밝은 왼쪽 위, 어두운 오른쪽 아래 + 그림자. rust면 둘레에 녹 몇 점."""
    p.put(x, y, HI if LOOK == 'clean' else RIVET_HI)
    p.put(x + 1, y, MID)
    p.put(x, y + 1, MID)
    p.put(x + 1, y + 1, LO)
    p.put(x + 2, y + 1, SHADE)
    p.put(x + 1, y + 2, SHADE)
    if rust:
        for dx, dy in ((-1, 1), (2, 0), (0, 2), (2, 2)):
            if (dx + dy + x) % 2 == 0:
                p.put(x + dx, y + dy, RUST_LO)
        p.put(x - 1, y, RUST)


def scratch(p, x, y, length, rng):
    """긁힌 자국: 짧은 사선(밝은 점 + 아래 어두운 점)."""
    dx = rng.choice((1, -1))
    for i in range(length):
        p.put(x + i * dx, y + i // 2, HI if i % 3 else MID)
        p.put(x + i * dx, y + i // 2 + 1, SHADE)


def scuff(p, x0, y0, w, h, rng, n=None):
    """판 안쪽에 긁힘·녹을 LOOK만큼 흩는다 (가장자리 3점 안쪽)."""
    if LOOK == 'clean' or w < 10 or h < 8:
        return
    n = n if n is not None else (2 if LOOK == 'worn' else 4)
    for _ in range(n):
        x = rng.randrange(x0 + 3, max(x0 + 4, x0 + w - 6))
        y = rng.randrange(y0 + 3, max(y0 + 4, y0 + h - 4))
        scratch(p, x, y, rng.randint(2, 4), rng)
    if LOOK == 'heavy':
        for _ in range(2):
            x = rng.randrange(x0 + 2, max(x0 + 3, x0 + w - 3))
            y = rng.randrange(y0 + 2, max(y0 + 3, y0 + h - 3))
            p.put(x, y, RUST)
            p.put(x + 1, y, RUST_LO)


def corner_rivets(p, x0, y0, w, h, inset=None):
    inset = inset if inset is not None else (3 if LOOK != 'heavy' else 4)
    rust = LOOK != 'clean'
    pts = [(x0 + inset, y0 + inset), (x0 + w - inset - 2, y0 + inset), (x0 + inset, y0 + h - inset - 2),
           (x0 + w - inset - 2, y0 + h - inset - 2)]
    for i, (x, y) in enumerate(pts):
        rivet(p, x, y, rust=rust and i == 3)                  # 녹은 한 귀퉁이만


# ----- 9칸 판 (hud_kit.KITS 크기 그대로: 그림 한 변, 모서리) -----
def kit_plate(name, size, corner, cut, rivets=True, hot=False, face=FACE, key=False):
    """size x size(화면) 9칸 판. 모서리 영역에 잘린 모서리·리벳, 변은 테만(이어 붙여도 이음매가 없게)."""
    n, c = size // 2, corner // 2
    p = Pix(n, n)
    plate(p, 0, 0, n, n, cut=cut, face=face, bevel=1 if key else None)
    if key:                                                   # 키캡: 아래가 두꺼운 키 (아래 2점 어둡게)
        for x in range(1, n - 1):
            if p.get(x, n - 2)[3]:
                p.put(x, n - 2, LO)
            if p.get(x, n - 3)[3] and x not in (0, n - 1):
                p.put(x, n - 3, SHADE)
    if LOOK == 'clean' and size < 96:                     # 깔끔: 작은 판에는 리벳이 없다
        rivets = False
    if rivets and c >= 5:
        inset = max(2, min(c - 3, 3))
        corner_rivets(p, 0, 0, n, n, inset=inset)
        if LOOK == 'heavy' and n - 2 * c >= 6:                # 변 가운데 리벳 (이어 붙이면 m마다 반복)
            m = n // 2 - 1
            for x, y in ((m, 2), (m, n - 4), (2, m), (n - 4, m)):
                rivet(p, x, y)
    if LOOK != 'clean' and c >= 6:                           # 모서리 영역 안의 긁힘 한두 개 (가운데는 단색이라 모서리에)
        rng = random.Random(size * 7 + corner)
        for (sx, sy) in ((c - 3, 2), (n - c + 1, n - 4))[:1 if LOOK == 'worn' else 2]:
            scratch(p, sx, sy, 3, rng)
    if LOOK == 'heavy' and c >= 6:                            # 거침: 왼쪽 아래 귀퉁이 녹
        p.put(2, n - 5, RUST); p.put(3, n - 5, RUST_LO); p.put(2, n - 6, RUST_LO)
    if hot:                                                   # 고른 칸: 네 귀퉁이 노란 꺾쇠 (안쪽 1점 띄워서)
        L = max(3, c - 1)
        for (cx, cy, sx, sy) in ((1, 1, 1, 1), (n - 2, 1, -1, 1), (1, n - 2, 1, -1), (n - 2, n - 2, -1, -1)):
            for i in range(L):
                p.put(cx + sx * i, cy, YEL)
                p.put(cx, cy + sy * i, YEL)
            p.put(cx + sx * 1, cy + sy * 1, YEL_LO)
    return p


# ----- 막대 속 (색 10가지 x 높이 5가지, 1024 폭) -----
FILLS = {   # 이름 -> (밝은 줄, 면, 어두운 줄). 구간 색은 규칙이라 예전 색과 같은 계열로
    'blue': ((140, 176, 240), (92, 134, 220), (52, 80, 150)),
    'boss': ((255, 120, 110), (214, 52, 52), (120, 24, 32)),
    'cyan': (CYAN_HI, CYAN, CYAN_LO),
    'empty': (LO, (16, 19, 25), (8, 9, 12)),
    'gray': ((170, 178, 192), (128, 137, 152), (80, 87, 100)),
    'orange': ((255, 178, 100), (236, 128, 48), (140, 70, 24)),
    'red': (RED_HI, RED, RED_LO),
    'violet': ((196, 170, 255), (150, 118, 236), (84, 62, 150)),
    'white': ((240, 244, 250), WHITE, (140, 148, 164)),
    'yellow': ((255, 220, 120), YEL, YEL_LO),
}


def fill_strip(color, h):
    """막대 속: 위 1점 밝게, 아래 1점 어둡게, 16점마다 새긴 눈금(어두운 세로 1점). 빈 칸은 눈금 없이 홈."""
    hi, face, lo = FILLS[color]
    n, hh = 512, h // 2
    p = Pix(n, hh)
    for y in range(hh):
        c = hi if y == 0 else lo if y == hh - 1 else face
        for x in range(n):
            p.put(x, y, c)
    if color != 'empty' and hh >= 4:
        for x in range(15, n, 16):
            for y in range(1, hh - 1):
                p.put(x, y, lo)
    return p


# ----- HUD 작은 부품 -----
def heart():
    p = Pix(14, 13)
    shape = ['..XXX..XXX....',
             '.XXXXXXXXXX...',
             'XXXXXXXXXXXX..',
             'XXXXXXXXXXXX..',
             'XXXXXXXXXXXX..',
             '.XXXXXXXXXX...',
             '..XXXXXXXX....',
             '...XXXXXX.....',
             '....XXXX......',
             '.....XX.......']
    for y, row in enumerate(shape):
        for x, ch in enumerate(row):
            if ch == 'X':
                p.put(x, y + 1, RED)
    # 윤곽·명암
    out = p.a.copy()
    for y in range(p.h):
        for x in range(p.w):
            if not out[y, x, 3]:
                if any(0 <= x + dx < p.w and 0 <= y + dy < p.h and out[y + dy, x + dx, 3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    p.put(x, y, EDGE)
    p.put(2, 2, RED_HI); p.put(3, 2, RED_HI); p.put(2, 3, RED_HI)
    for x, y in ((9, 5), (8, 6), (7, 7), (6, 8), (10, 4)):
        p.put(x, y, RED_LO)
    return p


def bolt(w, h):
    """작은 볼트 판 (하트 옆 결정·보스 막대 끝 대신)."""
    p = Pix(w, h)
    plate(p, 0, 0, w, h, cut=1, bevel=1)
    rivet(p, w // 2 - 1, h // 2 - 1)
    return p


def hp_frame():
    """체력 막대 틀 398x30 (속 380x24 둘레 2px + 오른쪽 끝 사선): 철 테 2점, 오른쪽 끝을 잘라 낸 모양, 속은 비운다."""
    n, hh = 199, 15
    p = Pix(n, hh)
    for y in range(hh):
        for x in range(n):
            cutr = x > n - 1 - (hh - 1 - y) // 2 - 1          # 오른쪽 끝 사선
            if cutr:
                continue
            border = y in (0, hh - 1) or x == 0 or x == n - 2 - (hh - 1 - y) // 2
            if border:
                p.put(x, y, EDGE)
            elif y == 1 or x == 1:
                p.put(x, y, HI)
            elif y == hh - 2:
                p.put(x, y, SHADE)
    # 안쪽(막대 자리)은 투명으로 비운다: 속 1..190 x 1..12 (화면 2..380, 2..26)
    for y in range(2, hh - 2):
        for x in range(2, 191):
            p.clear(x, y)
    # 오른쪽 끝 판(사선 부분)은 철판으로 채우고 리벳 하나
    for y in range(1, hh - 1):
        for x in range(191, n):
            if p.get(x, y)[3] == 0 and x <= n - 2 - (hh - 1 - y) // 2:
                p.put(x, y, FACE if y > 1 else HI)
    rivet(p, 192, 6)
    return p


def gauge_body():
    """게이지 몸통 32x32 (속 20px 위아래 6px): 쇠 받침. 위·아래 철 테 3점, 가운데(속 자리)는 비운다. 8점마다 볼트 자국."""
    n = 16
    p = Pix(n, n)
    for x in range(n):
        p.put(x, 0, EDGE); p.put(x, 1, HI); p.put(x, 2, MID)
        p.put(x, n - 3, SHADE); p.put(x, n - 2, LO); p.put(x, n - 1, EDGE)
    p.put(7, 1, LO); p.put(7, n - 2, HI)                     # 이음매
    return p


def gauge_cap(right):
    """게이지 양끝 32x50: 유리관을 무는 쇠 집게 (결정 첨탑 대신). 가운데 높이에 관 끝이 들어간다."""
    w, h = 16, 25
    p = Pix(w, h)
    x0 = 3 if not right else 0
    plate(p, x0, 2, 13, 21, cut=3)
    for y in (5, 18):                                        # 위아래 볼트
        rivet(p, x0 + 5, y)
    # 관이 물리는 홈 (가운데 높이 화면 속 자리: BAR_Y-15 기준 -> 그림 y 15..35px = 1배 7..17)
    for y in range(9, 16):
        for x in range(x0 + (9 if not right else 0), x0 + (13 if not right else 4)):
            p.put(x, y, LO)
    if LOOK != 'clean':
        p.put(x0 + 3, 20, RUST); p.put(x0 + 4, 21, RUST_LO)
    return p


def needle():
    """현재 값 바늘 10x44: 흰 스텐실 바늘 + 어두운 윤곽, 위아래 끝은 삼각."""
    p = Pix(5, 22)
    for y in range(22):
        if y < 2 or y > 19:
            p.put(2, y, EDGE if y in (0, 21) else WHITE)
            p.put(1, y, EDGE); p.put(3, y, EDGE)
        else:
            p.put(1, y, EDGE); p.put(2, y, WHITE); p.put(3, y, EDGE)
    for x in range(5):
        p.put(x, 1, EDGE if x in (0, 4) else WHITE)
        p.put(x, 20, EDGE if x in (0, 4) else WHITE)
    return p


def dash(on):
    """대시 칸 28x18: 노란·흰 스텐실 화살 꺾쇠(>>) 판. 꺼지면 어두운 홈."""
    p = Pix(14, 9)
    plate(p, 0, 0, 14, 9, cut=2, bevel=1, face=FACE if on else LO)
    if on:
        for i in range(3):
            for x0 in (3, 7):
                p.put(x0 + i, 2 + i, WHITE); p.put(x0 + i, 6 - i, WHITE)
    else:
        for i in range(3):
            for x0 in (3, 7):
                p.put(x0 + i, 2 + i, MID); p.put(x0 + i, 6 - i, MID)
    return p


def potion(on):
    """물약 18x26: 쇠 마개 병. 찬 병은 빨간 액체, 빈 병은 어두운 병."""
    p = Pix(9, 13)
    for y in range(13):
        for x in range(9):
            body = (1 <= x <= 7 and 5 <= y <= 11) or (3 <= x <= 5 and 2 <= y <= 4)
            if not body:
                continue
            p.put(x, y, LO)
    for y in range(6, 11):
        for x in range(2, 7):
            p.put(x, y, (RED if y > 6 else RED_HI) if on else SHADE)
    p.put(2, 7, RED_HI if on else MID)
    p.rect(3, 0, 3, 2, HI)                                   # 쇠 마개
    p.put(5, 1, MID)
    for x in range(9):                                       # 윤곽
        for y in range(13):
            if p.get(x, y)[3] == 0 and any(0 <= x + dx < 9 and 0 <= y + dy < 13 and p.get(x + dx, y + dy)[3]
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.put(x, y, EDGE)
    return p


def lamp(size, on, color=YEL, color_lo=YEL_LO):
    """작은 표시등 (단계 점·콤보): 쇠 테 안 등. 켜지면 color, 꺼지면 어두운 유리."""
    n = size // 2
    p = Pix(n, n)
    plate(p, 0, 0, n, n, cut=1, bevel=1)
    for y in range(2, n - 2):
        for x in range(2, n - 2):
            p.put(x, y, (color if (x + y) > 4 else GOLD_HI if color == GOLD else (255, 228, 150)) if on else LO)
    if on:
        p.put(n - 3, n - 3, color_lo)
    return p


def step(on):
    """진행 칸 24x12: 쇠 홈 (찬 칸은 mutation_mode가 갈래 색으로 속을 채운다)."""
    p = Pix(12, 6)
    plate(p, 0, 0, 12, 6, cut=1, bevel=1, face=LO if not on else FACE)
    return p


def reticle(ready):
    """조준점 56x56: 네 갈래 꺾쇠 + 가운데 점. 준비되면 흰색, 아니면 회색."""
    n = 28
    p = Pix(n, n)
    c = WHITE if ready else GREY
    m = n // 2
    for i in range(4, 10):                                   # 네 갈래
        for (x, y) in ((m - 1, i), (m, i), (m - 1, n - 1 - i), (m, n - 1 - i), (i, m - 1), (i, m), (n - 1 - i, m - 1), (n - 1 - i, m)):
            p.put(x, y, c)
    for (x, y) in ((m - 1, m - 1), (m, m - 1), (m - 1, m), (m, m)):
        p.put(x, y, YEL if ready else c)
    for k in range(3):                                       # 귀퉁이 꺾쇠
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            bx, by = (m - 1 - 6) if sx > 0 else (m + 6), (m - 1 - 6) if sy > 0 else (m + 6)
            p.put(bx + sx * k, by, c); p.put(bx, by + sy * k, c)
    out = p.a.copy()
    for y in range(n):
        for x in range(n):
            if not out[y, x, 3] and any(0 <= x + dx < n and 0 <= y + dy < n and out[y + dy, x + dx, 3]
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.put(x, y, EDGE)
    return p


def cursor():
    """고른 항목 표시 8x24: 노란 꺾쇠(>)."""
    p = Pix(4, 12)
    for i in range(6):
        x = min(i, 5 - i) if i < 6 else 0
        p.put(x, 3 + i, YEL); p.put(x + 1, 3 + i, YEL)
    for y in range(12):
        for x in range(4):
            if p.get(x, y)[3] == 0 and any(0 <= x + dx < 4 and 0 <= y + dy < 12 and tuple(p.get(x + dx, y + dy)[:3]) == YEL
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.put(x, y, EDGE)
    return p


def strip_hot():
    """고른 메뉴 띠 98x44: 철판 + 노란 밑줄 + 오른쪽 끝 경고 줄무늬. hud_kit.strip이 왼쪽 2·오른쪽 16px을 그대로 두고
    가운데 64px을 이어 붙이므로, 가운데에는 세로로 바뀌는 무늬가 없어야 한다(가로 줄만)."""
    w, h = 49, 22
    p = Pix(w, h)
    rows = [EDGE, HI, MID] + [FACE] * (h - 7) + [YEL, YEL_LO, SHADE, EDGE]
    for y, c in enumerate(rows):
        for x in range(w):
            p.put(x, y, c)
    for y in range(h):                                       # 왼쪽 끝 1점 윤곽 (화면 2px = 그대로 두는 왼쪽)
        p.put(0, y, EDGE)
    for y in range(1, h - 4):                                # 오른쪽 끝 8점: 경고 줄무늬 (화면 16px = 그대로 두는 오른쪽)
        for x in range(w - 8, w - 1):
            p.put(x, y, YEL if ((x + y) // 2) % 2 == 0 else LO)
    for y in range(h):
        p.put(w - 1, y, EDGE)
        p.put(w - 9, y, EDGE)
    return p


def tag():
    """이름표 64x40: 양끝 16px 철판 귀(리벳), 가운데 이어 붙이는 판. 거침 시안은 양끝 귀에 경고 줄무늬."""
    w, h = 32, 20
    p = Pix(w, h)
    plate(p, 0, 0, w, h, cut=3)
    if LOOK == 'heavy':
        for y in range(3, h - 3):
            for x in list(range(3, 7)) + list(range(w - 7, w - 3)):
                p.put(x, y, YEL if ((x + y) // 2) % 2 == 0 else LO)
    elif LOOK == 'worn':
        rivet(p, 3, h // 2 - 1, rust=True)
        rivet(p, w - 5, h // 2 - 1)
    return p


def map_cell(kind):
    """미니맵 칸 20x16: 철판 칸. 지금 방 노랑, 보스 빨강, 황금 금, 헤이즈 청록, 상점 흰색, 가 본 방 밝은 철, 모르는 방 어두운 홈."""
    p = Pix(10, 8)
    face = {'unknown': LO, 'visited': MID}.get(kind, FACE)
    plate(p, 0, 0, 10, 8, cut=1, bevel=1, face=face)
    mark = {'current': YEL, 'boss': RED, 'gold': GOLD, 'haze': CYAN, 'shop': WHITE}.get(kind)
    if kind == 'current':
        p.rect(2, 2, 6, 4, YEL); p.rect(3, 3, 4, 2, (255, 214, 110))
    elif kind == 'boss':                                     # 해골 대신 X 표
        for i in range(4):
            p.put(3 + i, 2 + i, RED); p.put(6 - i, 2 + i, RED)
    elif mark:
        p.rect(4, 3, 2, 2, mark)
        p.put(4, 2, mark); p.put(5, 5, mark)
    return p


def shard():
    """헤이즈 조각 12x24 (재화: 청록 그대로)."""
    p = Pix(6, 12)
    for y in range(12):
        half = min(y, 11 - y) // 2
        for x in range(3 - half - 1, 3 + half + 1):
            p.put(x, y, CYAN if x >= 3 else CYAN_HI)
    for y in range(12):
        for x in range(6):
            if p.get(x, y)[3] == 0 and any(0 <= x + dx < 6 and 0 <= y + dy < 12 and p.get(x + dx, y + dy)[3] and tuple(p.get(x + dx, y + dy)[:3]) != EDGE
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.put(x, y, EDGE)
    p.put(3, 8, CYAN_LO); p.put(3, 9, CYAN_LO)
    return p


def crystal_mark():
    """결정 표시 32x28 (재화·보상 결정, 헤이즈): 청록 결정 그대로 쓰되 도트 명암 3단."""
    p = Pix(16, 14)
    pts = [(8, 1), (13, 6), (8, 13), (3, 6)]
    for y in range(14):
        for x in range(16):
            if abs(x - 8) * 13 / 5 + abs(y - 7) * 1.0 <= 12.5 and 1 <= y <= 13:
                p.put(x, y, CYAN if x >= 8 else CYAN_HI)
    for y in range(14):
        for x in range(16):
            if p.get(x, y)[3] == 0 and any(0 <= x + dx < 16 and 0 <= y + dy < 14 and p.get(x + dx, y + dy)[3] and tuple(p.get(x + dx, y + dy)[:3]) != EDGE
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.put(x, y, EDGE)
    for y in range(8, 13):
        p.put(9, y, CYAN_LO)
    del pts
    return p


def diamond():
    """등급 결정 20x16 (저주 보상 등급: 결정 개수 = 헤이즈 보상)."""
    p = Pix(10, 8)
    for y in range(8):
        half = 4 - abs(y - 3.5) + 0.5
        for x in range(10):
            if abs(x - 4.5) <= half:
                p.put(x, y, CYAN if x >= 5 else CYAN_HI)
    for y in range(8):
        for x in range(10):
            if p.get(x, y)[3] == 0 and any(0 <= x + dx < 10 and 0 <= y + dy < 8 and p.get(x + dx, y + dy)[3] and tuple(p.get(x + dx, y + dy)[:3]) != EDGE
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p.put(x, y, EDGE)
    return p


# ----- 카드 틀 300x420 -----
def card(kind, seed):
    """증강 카드 틀: common 맨 철판 / rare 칠한 띠 + 리벳 더 / legendary 황동·금 테 / curse 위아래 빨강·검정 경고 줄무늬."""
    w, h = 150, 210
    p = Pix(w, h)
    rng = random.Random(seed)
    if kind == 'legendary':                                  # 황동 테 4점 + 안쪽 철판
        plate(p, 0, 0, w, h, cut=6, face=BRASS, hi=GOLD_HI, mid=GOLD, shade=GOLD_LO, bevel=2)
        plate(p, 4, 4, w - 8, h - 8, cut=4)
        for x, y in ((6, 6), (w - 8, 6), (6, h - 8), (w - 8, h - 8)):
            p.put(x, y, GOLD_HI); p.put(x + 1, y, GOLD); p.put(x, y + 1, GOLD); p.put(x + 1, y + 1, GOLD_LO)
        for x in range(26, w - 26, 14):                      # 위아래 금 리벳 줄 (9칸 자르기 가운데 길이 70점의 약수 간격)
            for y in (1, h - 3):
                p.put(x, y, GOLD_HI); p.put(x + 1, y + 1, GOLD_LO)
    else:
        plate(p, 0, 0, w, h, cut=6, bevel=2 if kind != 'common' else None)
        corner_rivets(p, 0, 0, w, h, inset=5)
        if kind == 'rare':                                   # 칠한 띠: 위쪽 밝은 철 띠 + 리벳 줄
            for y in range(12, 22):
                for x in range(3, w - 3):
                    p.put(x, y, HI if y in (12,) else MID if y < 21 else SHADE)
            for x in range(12, w - 12, 14):
                rivet(p, x, 15)
            for x in range(12, w - 12, 14):
                rivet(p, x, h - 10)
        if kind == 'curse':                                  # 위아래 경고 줄무늬 (빨강·검정 사선)
            for y0 in (6, h - 18):
                for y in range(y0, y0 + 12):
                    for x in range(6, w - 6):
                        p.put(x, y, RED if ((x + y) // 5) % 2 == 0 else LO)      # 주기 10점: 가운데 70점에 맞물린다
                for x in range(6, w - 6):
                    p.put(x, y0 - 1, EDGE); p.put(x, y0 + 12, EDGE)
        if LOOK != 'clean':                                  # 가운데 용접선 (세로, 카드 아래쪽 1/3에만)
            pass
        scuff(p, 8, 30, w - 16, h - 60, rng, n={'clean': 0, 'worn': 3, 'heavy': 5}[LOOK])
    return p


def kit_frame():
    """얇은 막대 틀 16x16 (모서리 6): 철 테 2점."""
    p = Pix(8, 8)
    plate(p, 0, 0, 8, 8, cut=1, bevel=1)
    return p


# ----- 증강 갈래 아이콘 (PixelLab 기호 + 코드 원판) -----
RAW = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'ui_plate_v1', 'raw')
ICON_PICK = {'hollow': 'hollow_s13'}           # 갈래 -> 고른 원본 (없으면 <갈래>_s11). 고른 이유는 ui_plate_v1/GENERATION_LOG.md
CURSE_ICON_COLOR = RED
ICON_COLOR = {'pipe_dash': (150, 190, 255), 'pistol_rapid': (226, 230, 238)}   # 갈래 색이 청록 계열인데 헤이즈가 아닌 갈래 (청록은 헤이즈에만)
GREYS = {(12, 14, 19): 0, (90, 98, 114): 1, (167, 175, 189): 2, (238, 241, 246): 3}   # PixelLab 팔레트 4단 -> 윤곽·어두움·가운데·밝음


def _tones(color):
    """갈래 색 하나에서 명암 3단 (어두움, 가운데, 밝음)."""
    c = np.array(color, float)
    return tuple(int(v) for v in c * 0.55), tuple(int(v) for v in c), tuple(int(v) for v in c + (255 - c) * 0.5)


def disc(n=32):
    """어두운 철 원판 (지름 n-2점): 위·왼쪽 밝은 테, 아래·오른쪽 그늘, 리벳 넷."""
    p = Pix(n, n)
    r = n / 2 - 1
    cx = cy = n / 2 - 0.5
    for y in range(n):
        for x in range(n):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d > r:
                continue
            if d > r - 1:
                c = EDGE
            elif d > r - 2:
                c = HI if (x - cx) + (y - cy) < 0 else SHADE
            else:
                c = FACE
            p.put(x, y, c)
    for ang in (45, 135, 225, 315):                          # 테 안쪽 리벳 넷 (비스듬히)
        import math
        rx = int(round(cx + (r - 3.5) * math.cos(math.radians(ang)))) - 0
        ry = int(round(cy + (r - 3.5) * math.sin(math.radians(ang)))) - 0
        p.put(rx, ry, RIVET_HI if LOOK != 'clean' else HI)
        p.put(rx + 1, ry + 1, LO)
    return p


def icon(raw_name, color):
    """PixelLab 기호(회색 4단)를 color 3단으로 바꿔 철 원판 위 가운데에 얹는다. 64x64(화면) 한 장."""
    src = np.array(Image.open(os.path.join(RAW, raw_name + '.png')).convert('RGBA'))
    lo, mid, hi = _tones(color)
    tone = {0: EDGE, 1: lo, 2: mid, 3: hi}
    ys, xs = np.nonzero(src[:, :, 3] > 0)
    x0, y0 = xs.min(), ys.min()
    w, h = xs.max() - x0 + 1, ys.max() - y0 + 1
    p = disc(32)
    ox, oy = (32 - w) // 2, (32 - h) // 2
    for y, x in zip(ys, xs):
        rgb = tuple(int(v) for v in src[y, x, :3])
        k = GREYS.get(rgb)
        if k is None:                                        # 팔레트 밖 색은 가장 가까운 단으로
            k = min(GREYS, key=lambda g: sum((a - b) ** 2 for a, b in zip(g, rgb)))
            k = GREYS[k]
        p.put(int(x - x0 + ox), int(y - y0 + oy), tone[k])
    return p


def family_icons(out=UI):
    """갈래 18개 + 저주 아이콘: assets/ui/up_mut_<갈래>.png, up_mut_curse.png (64x64)."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import mutations as mu
    made = []
    for fid, fam in mu.FAMILIES.items():
        p = icon(ICON_PICK.get(fid, fid + '_s11'), ICON_COLOR.get(fid, fam['color']))
        p.save(f'mut_{fid}', out)
        made.append(f'mut_{fid}')
    icon('curse_s11', CURSE_ICON_COLOR).save('mut_curse', out)
    made.append('mut_curse')
    return made


def build(out=UI, look='worn', seed=7):
    """부품을 모두 굽는다. 돌려주는 값은 만든 이름 목록."""
    global LOOK
    LOOK = look
    rng = random.Random(seed)
    made = []

    def keep(p, name):
        p.save(name, out)
        made.append(name)

    # 9칸 판 (크기는 hud_kit.KITS와 같다)
    keep(kit_plate('panel', 96, 24, cut=4), 'kit_panel')
    keep(kit_plate('plate', 48, 12, cut=3), 'kit_plate')
    keep(kit_frame(), 'kit_frame')
    keep(kit_plate('slot', 80, 16, cut=3), 'kit_slot')
    keep(kit_plate('slot', 80, 16, cut=3, hot=True), 'kit_slot_hot')
    keep(kit_plate('key', 24, 8, cut=1, rivets=False, key=True, face=MID), 'kit_key')
    keep(kit_plate('key', 24, 8, cut=1, rivets=False, key=True), 'kit_key_dim')
    for color in FILLS:
        for h in (8, 12, 16, 20, 24):
            keep(fill_strip(color, h), f'fill_{color}_{h}')
    keep(heart(), 'heart')
    keep(bolt(5, 10), 'gem')
    keep(hp_frame(), 'hp_frame')
    keep(gauge_body(), 'gauge_body')
    keep(gauge_cap(False), 'gauge_l')
    keep(gauge_cap(True), 'gauge_r')
    keep(needle(), 'needle')
    keep(dash(True), 'dash_on')
    keep(dash(False), 'dash_off')
    keep(potion(True), 'potion_on')
    keep(potion(False), 'potion_off')
    keep(lamp(10, True), 'dot_on')
    keep(lamp(10, False), 'dot_off')
    keep(lamp(22, True), 'combo_on')
    keep(lamp(22, True, RED, RED_LO), 'combo_fin')
    keep(lamp(22, False), 'combo_off')
    keep(step(True), 'step_on')
    keep(step(False), 'step_off')
    keep(reticle(True), 'reticle_ready')
    keep(reticle(False), 'reticle_wait')
    keep(cursor(), 'cursor')
    keep(strip_hot(), 'strip_hot')
    keep(tag(), 'tag')
    for kind in ('unknown', 'visited', 'current', 'boss', 'gold', 'haze', 'shop'):
        keep(map_cell(kind), f'map_{kind}')
    keep(shard(), 'shard')
    keep(crystal_mark(), 'crystal')
    keep(diamond(), 'diamond')
    keep(bolt(3, 10), 'boss_l')
    keep(bolt(3, 10), 'boss_r')
    for kind in ('common', 'rare', 'legendary', 'curse'):
        keep(card(kind, rng.randrange(1000)), f'card_{kind}')
    del rng
    made += family_icons(out)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--look', default='worn', choices=LOOKS)
    ap.add_argument('--out', default=UI)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    made = build(a.out, a.look)
    print(f'{len(made)}개 ({a.look}) -> {a.out}')


if __name__ == '__main__':
    main()
