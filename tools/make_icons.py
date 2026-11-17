"""아이템 아이콘 10종과 진열대를 코드로 그린다 (이미지 모델 없음, numpy + Pillow). code-drawn.

아이콘은 24x24 격자에 그린 뒤 정수 2배로 키워 48x48로 저장한다 (다른 픽셀 에셋과 같은 굵기).
색은 공통 어두운 외곽선 + 회색·청회색 재질 3단계 + 아이템마다 포인트 색 3단계(밝음·기본·어두움)다. 아이콘 한 장 색 16개 이하.
진열대는 60x60 타일 단위(120x150)로, 황금방 제단·정비방 선반·품절(빛이 꺼진) 3장이다.

결과: assets/ui/icon_<id>.png (cap absorb steady enhance resist dash power vigor heal shard),
      assets/ui/pedestal_gold.png, pedestal_shop.png, pedestal_gone.png
Codex T13(아이콘)·T14(진열대) 결과가 합격하면 같은 파일 이름으로 교체한다. 사용: python tools/make_icons.py
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = os.path.join(ROOT, 'assets', 'ui')
sys.path.insert(0, os.path.join(ROOT, 'src'))

K = (11, 16, 32)                                   # 외곽선
STEEL = ((38, 48, 74), (82, 100, 138), (170, 186, 214))      # 어두움, 기본, 밝음
WHITE = (240, 248, 255)
GLASS = (150, 200, 220)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = (*c, 255)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            x = round(x0 + (x1 - x0) * i / n)
            y = round(y0 + (y1 - y0) * i / n)
            for dx in range(t):
                for dy in range(t):
                    self.px(x + dx, y + dy, c)

    def poly(self, pts, c):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                inside = False
                j = len(pts) - 1
                for i in range(len(pts)):
                    xi, yi, xj, yj = pts[i][0], pts[i][1], pts[j][0], pts[j][1]
                    if (yi > y + 0.5) != (yj > y + 0.5) and x + 0.5 < (xj - xi) * (y + 0.5 - yi) / (yj - yi + 1e-9) + xi:
                        inside = not inside
                    j = i
                if inside:
                    self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c)

    def outline(self, c=K):
        mask = self.a[:, :, 3] > 0
        pad = np.pad(mask, 1)
        edge = (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]) & ~mask
        self.a[edge] = (*c, 255)


def accent(c):
    return shade(c, 1.25), c, shade(c, 0.6)         # 밝음, 기본, 어두움


def icon(kind, color):
    cv = Canvas(24, 24)
    hi, mid, lo = accent(color)
    if kind == 'cap':                                              # 눈금 유리관과 가득 찬 안개
        cv.rect(8, 3, 15, 20, GLASS)
        cv.rect(8, 8, 15, 20, mid)
        cv.rect(9, 8, 10, 20, hi)
        cv.rect(8, 8, 15, 8, hi)
        cv.rect(7, 2, 16, 4, STEEL[1])
        cv.rect(7, 20, 16, 22, STEEL[1])
        for y in (11, 14, 17):
            cv.rect(5, y, 7, y, STEEL[2])
    elif kind == 'absorb':                                         # 중심의 결정으로 빨려 드는 화살표
        cv.poly([(12, 6), (17, 12), (12, 18), (7, 12)], mid)
        cv.poly([(12, 6), (7, 12), (12, 12)], hi)
        cv.poly([(12, 18), (17, 12), (12, 12)], lo)
        for (x0, y0, x1, y1) in ((2, 2, 7, 7), (21, 2, 16, 7), (2, 21, 7, 16), (21, 21, 16, 16)):
            cv.line(x0, y0, x1, y1, hi)
        cv.px(7, 7, WHITE)
        cv.px(16, 7, WHITE)
    elif kind == 'steady':                                         # 모래시계
        cv.rect(6, 2, 17, 3, STEEL[2])
        cv.rect(6, 20, 17, 21, STEEL[2])
        cv.poly([(7, 4), (16, 4), (12, 11)], GLASS)
        cv.poly([(12, 12), (7, 19), (16, 19)], GLASS)
        cv.poly([(8, 5), (15, 5), (12, 9)], mid)
        cv.poly([(12, 15), (9, 19), (14, 19)], mid)
        cv.rect(11, 10, 12, 14, hi)
    elif kind == 'enhance':                                        # 불꽃이 감싼 파이프 끝
        cv.line(4, 21, 14, 11, STEEL[1], 3)
        cv.line(4, 20, 13, 11, STEEL[2], 1)
        cv.poly([(14, 11), (12, 6), (15, 8), (16, 2), (19, 8), (21, 11), (17, 14)], mid)
        cv.poly([(15, 11), (16, 6), (18, 10), (17, 13)], hi)
        cv.px(17, 9, WHITE)
    elif kind == 'resist':                                         # 금 간 방패
        cv.poly([(12, 2), (20, 5), (19, 14), (12, 22), (5, 14), (4, 5)], mid)
        cv.poly([(12, 2), (4, 5), (5, 14), (12, 22)], hi)
        cv.line(13, 4, 11, 10, K)
        cv.line(11, 10, 14, 14, K)
        cv.line(14, 14, 12, 19, K)
        cv.rect(10, 8, 10, 9, WHITE)
    elif kind == 'dash':                                           # 속도선이 달린 부츠
        cv.poly([(10, 4), (16, 4), (16, 14), (21, 17), (21, 21), (10, 21)], STEEL[1])
        cv.poly([(10, 4), (12, 4), (12, 21), (10, 21)], STEEL[2])
        cv.rect(10, 18, 21, 21, STEEL[0])
        cv.rect(10, 7, 16, 8, mid)
        for y in (6, 11, 16):
            cv.line(1, y, 7, y, hi)
        cv.poly([(16, 6), (22, 2), (19, 9)], hi)                   # 작은 날개
    elif kind == 'power':                                          # 갈린 파이프와 불꽃
        cv.line(3, 21, 17, 7, STEEL[1], 4)
        cv.line(3, 20, 16, 7, STEEL[2], 1)
        cv.line(3, 22, 17, 8, STEEL[0], 1)
        for (x, y) in ((19, 3), (21, 7), (18, 1), (22, 4)):
            cv.px(x, y, hi)
        cv.line(18, 6, 22, 2, mid, 1)
        cv.px(21, 3, WHITE)
    elif kind == 'vigor':                                          # 하트와 십자 보호대
        cv.ellipse(8, 8, 4.2, 4, mid)
        cv.ellipse(15.5, 8, 4.2, 4, mid)
        cv.poly([(3, 9), (21, 9), (12, 21)], mid)
        cv.ellipse(7, 7, 1.6, 1.6, hi)
        cv.poly([(5, 10), (12, 10), (12, 19)], shade(color, 1.1))
        cv.rect(11, 8, 12, 15, WHITE)
        cv.rect(9, 11, 14, 12, WHITE)
    elif kind == 'heal':                                           # 십자 붕대 약병
        cv.rect(9, 2, 14, 5, STEEL[2])
        cv.rect(8, 5, 15, 7, GLASS)
        cv.rect(5, 8, 18, 21, GLASS)
        cv.rect(6, 12, 17, 21, mid)
        cv.rect(6, 12, 17, 13, hi)
        cv.rect(11, 14, 12, 19, WHITE)
        cv.rect(9, 16, 14, 17, WHITE)
    elif kind == 'shard':                                          # 청록 결정 한 덩어리
        cv.poly([(12, 1), (17, 8), (15, 22), (9, 22), (7, 8)], mid)
        cv.poly([(12, 1), (7, 8), (9, 22), (12, 22)], hi)
        cv.poly([(12, 1), (17, 8), (15, 22), (12, 22)], lo)
        cv.poly([(3, 12), (6, 9), (8, 22), (3, 22)], mid)
        cv.poly([(21, 14), (18, 10), (16, 22), (21, 22)], lo)
        cv.px(11, 6, WHITE)
        cv.px(11, 7, WHITE)
    cv.outline()
    return cv


ICONS = {
    'cap': (90, 210, 240), 'absorb': (130, 235, 225), 'steady': (110, 150, 220), 'enhance': (240, 150, 60),
    'resist': (250, 220, 90), 'dash': (170, 200, 255), 'power': (255, 120, 120), 'vigor': (255, 150, 170),
    'heal': (120, 235, 150), 'shard': (95, 214, 232),
}


def up2(arr):
    return np.repeat(np.repeat(arr, 2, axis=0), 2, axis=1)


# ----- 진열대 -----
def pedestal(kind):
    """120x150 (논리 60x75). kind: gold(황동 제단) / shop(청색 선반) / gone(품절, 빛이 꺼짐). 위 가운데에 48x48 아이콘이 놓인다."""
    cv = Canvas(60, 75)
    if kind == 'gold':
        base = ((62, 46, 20), (118, 90, 36), (200, 160, 60), (250, 224, 130))
        glow = (255, 240, 160)
    elif kind == 'shop':
        base = ((16, 40, 58), (34, 84, 116), (70, 140, 180), (160, 220, 250))
        glow = (127, 232, 255)
    else:
        base = ((30, 34, 44), (52, 58, 72), (82, 90, 108), (112, 122, 142))
        glow = None
    d, m, l, h = base
    cv.rect(8, 60, 51, 72, m)                          # 받침 몸통
    cv.rect(8, 60, 51, 62, l)
    cv.rect(8, 60, 10, 72, l)
    cv.rect(49, 63, 51, 72, d)
    cv.rect(4, 68, 55, 74, d)
    cv.rect(4, 68, 55, 69, m)
    if kind == 'shop':                                 # 선반 + 가격표 걸이
        cv.rect(10, 48, 49, 51, l)
        cv.rect(10, 48, 49, 48, h)
        cv.rect(10, 52, 49, 52, d)
        cv.rect(12, 52, 13, 60, d)
        cv.rect(46, 52, 47, 60, d)
        cv.rect(26, 53, 33, 58, h if glow else m)      # 가격표
        cv.rect(27, 54, 32, 55, d)
    else:                                              # 제단: 열린 보관함 테두리
        cv.rect(12, 46, 47, 48, l)
        cv.rect(12, 46, 47, 46, h)
        cv.rect(12, 46, 13, 58, l)
        cv.rect(46, 46, 47, 58, d)
        cv.rect(14, 49, 45, 58, d)
        if glow:
            for y in range(49, 59):
                for x in range(14, 46):
                    if (x + y) % 2 == 0 and (y - 49) < 6:
                        cv.px(x, y, shade(glow, 0.55))
    if glow:                                           # 위로 새는 빛 (엇갈린 점)
        for y in range(10, 46):
            spread = (46 - y) // 5
            for x in range(30 - 10 - spread, 30 + 10 + spread):
                if (x + y) % 3 == 0 and (hash((x, y)) % 100) < 40 - (46 - y):
                    cv.px(x, y, glow)
    cv.outline()
    return cv


def main():
    os.makedirs(UI, exist_ok=True)
    for name, color in ICONS.items():
        cv = icon(name, color)
        Image.fromarray(up2(cv.a), 'RGBA').save(os.path.join(UI, f'icon_{name}.png'))
    for kind in ('gold', 'shop', 'gone'):
        Image.fromarray(up2(pedestal(kind).a), 'RGBA').save(os.path.join(UI, f'pedestal_{kind}.png'))
    print('saved', len(ICONS), 'icons and 3 pedestals to assets/ui')


if __name__ == '__main__':
    main()
