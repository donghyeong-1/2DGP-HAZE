"""방의 겉모습 에셋을 만든다: 타일 세트, 원경, 중경 (이미지 모델 없음, numpy + Pillow). code-drawn.

v2 (2026-11-17): 캐릭터와 같은 **1배 픽셀 밀도**로 다시 그렸다 (이전 판은 30x30 격자를 2배로 키워 캐릭터보다 굵었다).
  * 벽은 이어지는 석조 무늬(120px 주기)를 잘라 쓰므로 타일 경계가 보이지 않는다. 벽돌마다 밝기·모서리 빛이 다르고,
    얼룩·균열이 있다. 드러난 면(16가지 이웃 마스크)은 강철 테두리(윗면), 들쭉날쭉한 밑면, 빛·그림자 옆면으로 덮는다.
    벽 안쪽 깊은 곳은 어둡게 눌러 덩어리로 보이게 한다.
  * 소품(천장·벽·바닥), 문틀·쇠창살·문 빛, 램프 빛 번짐도 같은 세트에 넣는다.
  * 원경은 Codex가 그린 배경판(assets/sprites/forge/backgrounds_v1)을 테마 색으로 다시 입힌 것이고(화면 고정),
    중경은 코드로 그린 기둥·들보·사슬 실루엣이다(카메라를 따라 조금씩 움직이는 시차 배경, 가로로 이어 붙는다).

결과:
  assets/tiles/tile_set_<테마>.png   16열 x 9줄, 칸 60x60 (줄·칸 배치는 src/room.py의 ATLAS 표와 같다)
  assets/backgrounds/far_<테마>.png  1920x1080 원경 (불투명)
  assets/backgrounds/mid_<테마>.png  1920x1200 중경 (투명, 가로 반복)
테마: cell(감방 청회색) foundry(제련소 주황) haze(헤이즈 청록) gold(황금방 황동) shop(정비방 청색) boss(보스 붉은색)
사용: python tools/make_world.py [테마 ...]   (타일만 만든다. 원경·중경은 2026-11-25부터 tools/apply_backdrops_v6.py가 만든다.
      예전 원경·중경으로 되돌리려면 --backdrops-v1)
"""
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE_DIR = os.path.join(ROOT, 'assets', 'tiles')
BG_DIR = os.path.join(ROOT, 'assets', 'backgrounds')
FORGE_BG = os.path.join(ROOT, 'assets', 'sprites', 'forge', 'backgrounds_v1')
T = 60                     # 타일 한 칸(px)
PERIOD = 120               # 석조 무늬가 반복되는 주기 (2x2칸)
COLS, ROWS = 16, 9

#            K 외곽       D 어두움     B 바탕       M 중간       L 밝음       H 하이라이트  A 포인트      C 빛
THEMES = {
    'cell':    ('#0b1020', '#1a2238', '#2a3552', '#3a4a6c', '#566c96', '#9bb2d6', '#8a5a44', '#5fd6e8'),
    'foundry': ('#140a0a', '#2c1812', '#44281d', '#603a28', '#8e5c38', '#d89250', '#e06a2c', '#ffb347'),
    'haze':    ('#061418', '#0f2c33', '#17444c', '#205e68', '#318e96', '#86eaea', '#3c7a9a', '#b8fff4'),
    'gold':    ('#140e04', '#2c220e', '#4c3c1a', '#6c5622', '#aa8830', '#f2d274', '#a8502e', '#fff0a0'),
    'shop':    ('#04141a', '#0d2c38', '#174458', '#205c76', '#3c8cac', '#a4e6ff', '#c8a040', '#7fe8ff'),
    'boss':    ('#12060a', '#2c0f18', '#461621', '#601e2c', '#8e2e42', '#e2646e', '#ffb040', '#ff6070'),
}
BG_SOURCE = {'cell': 'bg_prison_corridor', 'gold': 'bg_prison_corridor', 'foundry': 'bg_iron_factory',
             'shop': 'bg_iron_factory', 'haze': 'bg_warden_tower', 'boss': 'bg_warden_tower'}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5

# 팔레트 번호
MORTAR, D, B, M, L, H, K, A, C, A2, C2, W0, W1, W2, WHITE = range(15)
CLEAR = -1


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def palette(theme):
    k, d, b, m, l, h, a, c = (rgb(x) for x in THEMES[theme])
    return [mix(k, d, 0.55), d, b, m, l, h, k, a, c, mix(a, k, 0.45), mix(c, k, 0.5),
            (74, 50, 32), (107, 74, 46), (142, 98, 58), (244, 250, 255)]


def hsh(a, b=0, c=0):
    return ((a * 73856093) ^ (b * 19349663) ^ (c * 83492791)) & 0xFFFF


def periodic_noise(size, cells, seed):
    """가장자리가 이어지는 부드러운 노이즈 (0~1)."""
    rng = np.random.RandomState(seed)
    g = rng.rand(cells, cells)
    g = np.pad(g, ((0, 1), (0, 1)), mode='wrap')
    xs = np.linspace(0, cells, size, endpoint=False)
    i = xs.astype(int)
    f = xs - i
    f = f * f * (3 - 2 * f)
    fy, fx = f[:, None], f[None, :]
    a, b_, c_, d_ = g[i][:, i], g[i][:, i + 1], g[i + 1][:, i], g[i + 1][:, i + 1]
    return a * (1 - fx) * (1 - fy) + b_ * fx * (1 - fy) + c_ * (1 - fx) * fy + d_ * fx * fy


# ====================================================================== 석조 무늬
def stone_texture(seed):
    """120x120 반복 석조 무늬의 밝기(0~1). 줄 높이가 섞인 벽돌, 모서리 빛, 얼룩, 균열."""
    S = PERIOD
    rng = np.random.RandomState(seed)
    lum = np.zeros((S, S))
    heights = [24, 16, 20, 24, 16, 20]                      # 60px마다 줄눈이 맞는다 (24+16+20)
    y = 0
    for h in heights:
        x = rng.randint(0, 20)
        end = x + S
        while x < end:
            w = min(int(rng.randint(16, 38)), end - x)
            if end - (x + w) < 12:                           # 자투리가 너무 좁으면 합친다
                w = end - x
            yy, xx = np.mgrid[0:h, 0:w]
            base = 0.50 + (rng.rand() - 0.5) * 0.16
            cell = np.full((h, w), base)
            cell[(yy == 1) | (xx == 1)] += 0.15              # 위·왼쪽 모서리 빛
            cell[(yy == h - 1) | (xx == w - 1)] -= 0.13      # 아래·오른쪽 그림자
            cell[(yy == 0) | (xx == 0)] = 0.10               # 줄눈
            if rng.rand() < 0.18:                            # 깨진 모서리
                chip = (xx + yy) < rng.randint(4, 8)
                cell[chip] = 0.12
            lum[(y + yy) % S, (x + xx) % S] = cell
            x += w
        y += h
    lum += (periodic_noise(S, 6, seed + 1) - 0.5) * 0.20     # 큰 얼룩
    lum += (rng.rand(S, S) - 0.5) * 0.07                     # 잔 입자
    for _ in range(4):                                       # 균열
        cx, cy = rng.randint(0, S), rng.randint(0, S)
        for _ in range(rng.randint(10, 22)):
            lum[cy % S, cx % S] = 0.08
            lum[cy % S, (cx + 1) % S] += 0.10
            cy += 1
            cx += rng.randint(-1, 2)
    return np.clip(lum, 0, 1)


def tones(lum):
    """밝기 -> 석조 6톤 (MORTAR, D, B, M, L, H)."""
    h, w = lum.shape
    v = lum + np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w] * 0.035
    out = np.full(lum.shape, MORTAR)
    for cut, tone in ((0.22, D), (0.40, B), (0.52, M), (0.64, L), (0.80, H)):
        out[v >= cut] = tone
    return out


def solid_tile(tex, deep_tex, variant, mask, seed):
    """벽 한 칸. variant는 무늬의 2x2 사분면, mask는 드러난 면(1 위, 2 오른쪽, 4 아래, 8 왼쪽)."""
    qx, qy = variant % 2, variant // 2
    t = tex[qy * T:(qy + 1) * T, qx * T:(qx + 1) * T].copy()
    up, right, down, left = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
    X = np.arange(T)
    if right:
        t[:, T - 4] = np.where(t[:, T - 4] > D, t[:, T - 4] - 1, t[:, T - 4])
        t[:, T - 3:T - 1] = D
        t[:, T - 1] = K
    if left:
        t[:, 3] = np.where(t[:, 3] < H, t[:, 3] + 1, t[:, 3])
        t[:, 1:3] = L
        t[::7, 2] = M
        t[:, 0] = K
    if down:                                                 # 들쭉날쭉한 밑면과 흘러내린 녹물
        notch = (periodic_noise(T, 6, seed + 9)[0] * 3.4).astype(int)
        for x in X:
            n = int(notch[x])
            t[T - 5 - n:T - 1 - n, x] = D
            t[T - 1 - n, x] = K
            t[T - n:, x] = CLEAR
            if hsh(x, seed, mask) % 11 == 0:
                length = 4 + hsh(x, seed) % 9
                t[T - 5 - n - length:T - 5 - n, x] = A2
    if up:                                                   # 강철 테두리 윗면
        t[0, :] = K
        t[1:3, :] = H
        t[1, (X * 7 + seed) % 13 == 0] = L
        t[3:7, :] = M
        t[3, :] = L
        t[7, :] = D
        t[8:11, :] = np.where(t[8:11, :] > MORTAR, t[8:11, :] - 1, t[8:11, :])      # 테두리 아래 그늘
        for x0 in (9, 29, 49):                               # 리벳
            t[4:6, x0:x0 + 2] = D
            t[4, x0] = H
    for (cx, cy, e1, e2) in ((0, 0, up, left), (T - 1, 0, up, right)):
        if e1 and e2:                                        # 위쪽 바깥 모서리를 둥글게
            t[cy, cx] = CLEAR
    if up and left:
        t[1, 1] = K
    if up and right:
        t[1, T - 2] = K
    return t


def deep_tile(deep_tex, variant):
    qx, qy = variant % 2, variant // 2
    return deep_tex[qy * T:(qy + 1) * T, qx * T:(qx + 1) * T].copy()


# ====================================================================== 그리기 도구 (소품)
class Art:
    def __init__(self, w=T, h=T):
        self.w, self.h = w, h
        self.a = np.full((h, w), CLEAR, dtype=int)

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = c

    def rect(self, x0, y0, x1, y1, c):
        self.a[max(0, y0):min(self.h, y1 + 1), max(0, x0):min(self.w, x1 + 1)] = c

    def line(self, x0, y0, x1, y1, c, t=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0), 1))
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
            self.rect(x, y, x + t - 1, y + t - 1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        self.a[((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1.0] = c

    def poly(self, pts, c):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        x, y = xx + 0.5, yy + 0.5
        inside = np.zeros((self.h, self.w), bool)
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi, xj, yj = pts[i][0], pts[i][1], pts[j][0], pts[j][1]
            cross = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
            inside ^= cross
            j = i
        self.a[inside] = c

    def outline(self, c=K):
        mask = self.a != CLEAR
        pad = np.pad(mask, 1)
        edge = (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]) & ~mask
        self.a[edge] = c
        return self

    def dither_glow(self, cx, cy, r0, r1, c, density=0.75, squash=1.0):
        """(cx, cy) 둘레에 엇갈린 점으로 빛 번짐을 그린다 (반투명 대신 점의 밀도로 옅어진다)."""
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        d = np.hypot(xx - cx, (yy - cy) / squash)
        t = np.clip((d - r0) / max(r1 - r0, 1), 0, 1)
        bay = np.tile(BAYER + 0.5, (self.h // 4 + 1, self.w // 4 + 1))[:self.h, :self.w]
        on = (bay < density * (1 - t) ** 1.6) & (d >= r0) & (d <= r1) & (self.a == CLEAR)
        self.a[on] = c


# ---------- 얇은 바닥, 가시 ----------
def oneway(kind):
    """강철 발판. kind: 0 단독, 1 왼끝, 2 가운데, 3 오른끝."""
    a = Art()
    a.rect(0, 0, T - 1, 0, K)
    a.rect(0, 1, T - 1, 1, H)
    a.rect(0, 2, T - 1, 6, L)
    for x in range(T):                                       # 미끄럼 방지 무늬
        for y in (3, 5):
            if (x + (y // 2) * 3) % 6 == 0:
                a.px(x, y, M)
    a.rect(0, 7, T - 1, 7, M)
    a.rect(0, 8, T - 1, 9, D)
    a.rect(0, 10, T - 1, 10, K)
    for x0 in (14, 44):                                      # 아래 버팀 삼각대
        a.line(x0, 11, x0 - 7, 18, D)
        a.line(x0, 11, x0 + 7, 18, D)
        a.rect(x0 - 8, 19, x0 + 8, 19, K)
    if kind in (0, 1):
        a.rect(0, 0, 0, 10, K)
        a.rect(1, 2, 3, 6, A)
        a.rect(1, 11, 2, 26, D)
        a.rect(0, 11, 0, 26, K)
        a.rect(3, 11, 3, 26, K)
    if kind in (0, 3):
        a.rect(T - 1, 0, T - 1, 10, K)
        a.rect(T - 4, 2, T - 2, 6, A)
        a.rect(T - 3, 11, T - 2, 26, D)
        a.rect(T - 1, 11, T - 1, 26, K)
        a.rect(T - 4, 11, T - 4, 26, K)
    return a.a


def spike(kind):
    """가시 (타일 아래쪽 30px이 판정). kind 1은 녹이 묻었다."""
    a = Art()
    for s in range(4):
        x0 = s * 15
        for y in range(30, 57):
            half = (y - 30) / 26 * 6.5
            for x in range(int(7 - half), int(8 + half) + 1):
                a.px(x0 + x, y, L if x < 7 else M)
            if y < 34:
                a.px(x0 + 7, y, H)
        a.line(x0 + 7, 29, x0, 56, K)
        a.line(x0 + 8, 29, x0 + 14, 56, K)
        a.px(x0 + 7, 28, K)
        if kind == 1:
            a.line(x0 + 7, 36, x0 + 6, 44, A2)
    a.rect(0, 56, T - 1, 58, D)
    a.rect(0, 59, T - 1, 59, K)
    a.rect(0, 56, T - 1, 56, M)
    return a.a


# ---------- 벽에 붙는 소품 (벽 타일 위에 덧그린다) ----------
def wall_window():
    a = Art()
    a.rect(14, 10, 45, 49, K)
    a.rect(16, 12, 43, 47, C2)
    a.rect(16, 12, 43, 24, C)
    for y in range(25, 34):
        for x in range(16, 44):
            if (x + y) % 2 == 0:
                a.px(x, y, C)
    for x in (22, 29, 36):
        a.rect(x, 11, x + 1, 48, K)
    a.rect(15, 29, 44, 30, K)
    a.rect(12, 50, 47, 52, M)
    a.rect(12, 53, 47, 53, K)
    a.rect(12, 49, 47, 49, K)
    return a.a


def wall_vent():
    a = Art()
    a.rect(12, 16, 47, 43, K)
    a.rect(14, 18, 45, 41, D)
    for y in range(20, 41, 4):
        a.rect(15, y, 44, y + 1, M)
        a.rect(15, y, 44, y, L)
    for x, y in ((13, 17), (46, 17), (13, 42), (46, 42)):
        a.px(x, y, H)
    return a.a


def wall_outlet():
    """배수관 구멍과 흘러내린 헤이즈."""
    a = Art()
    a.ellipse(30, 22, 11, 11, K)
    a.ellipse(30, 22, 9, 9, M)
    a.ellipse(30, 23, 6.5, 6.5, K)
    a.rect(28, 28, 31, 54, C2)
    a.rect(29, 28, 30, 50, C)
    a.px(29, 57, C)
    return a.a


def wall_stencil(n):
    """벽에 찍힌 구역 번호 (감옥 느낌)."""
    a = Art()
    glyphs = {0: ('111', '101', '101', '101', '111'), 9: ('111', '101', '111', '001', '111'),
              7: ('111', '001', '010', '010', '010'), 3: ('111', '001', '111', '001', '111')}
    x = 12
    for d in (n // 10, n % 10):
        g = glyphs.get(d, glyphs[0])
        for r, row in enumerate(g):
            for c_, ch in enumerate(row):
                if ch == '1':
                    a.rect(x + c_ * 5, 18 + r * 5, x + c_ * 5 + 3, 18 + r * 5 + 3, L)
        x += 20
    a.rect(10, 46, 49, 47, L)
    return a.a


def wall_crack():
    a = Art()
    x, y = 30, 4
    rng = np.random.RandomState(4)
    for _ in range(50):
        a.px(x, y, MORTAR)
        a.px(x + 1, y, D)
        y += 1
        x += rng.randint(-1, 2)
        if y > 56:
            break
    return a.a


def wall_stain():
    """벽에 번진 헤이즈 얼룩."""
    a = Art()
    a.dither_glow(30, 24, 0, 22, C2, density=0.5, squash=1.5)
    return a.a


# ---------- 천장에서 내려오는 소품 ----------
def chain(part):
    """사슬. part: 0 고정판이 있는 맨 위, 1 가운데, 2 갈고리가 달린 끝."""
    a = Art()
    end = 40 if part == 2 else T
    for y0 in range(0, end, 10):
        a.rect(28, y0, 31, y0 + 6, L)                        # 세로 고리
        a.rect(29, y0 + 1, 30, y0 + 5, CLEAR)
        a.rect(29, y0 + 6, 30, y0 + 10, M)                   # 옆으로 선 고리
    a.outline()
    if part == 0:
        a.rect(20, 0, 39, 4, M)
        a.rect(20, 0, 39, 0, H)
        a.rect(19, 5, 40, 5, K)
        a.rect(19, 0, 19, 4, K)
        a.rect(40, 0, 40, 4, K)
    if part == 2:                                            # 갈고리
        b = Art()
        b.rect(28, 40, 31, 50, L)
        b.rect(28, 50, 36, 53, L)
        b.rect(34, 44, 37, 50, L)
        b.outline()
        a.a[b.a != CLEAR] = b.a[b.a != CLEAR]
    return a.a


def lamp():
    a = Art()
    a.rect(29, 0, 30, 14, D)
    a.poly([(20, 22), (39, 22), (35, 14), (24, 14)], M)
    a.rect(24, 14, 35, 15, L)
    a.rect(23, 23, 36, 34, C)
    a.rect(26, 25, 33, 31, WHITE)
    for x in (23, 28, 32, 36):
        a.rect(x, 23, x, 35, K)
    a.rect(23, 35, 36, 36, D)
    a.outline()
    return a.a


def banner():
    a = Art()
    a.rect(14, 0, 45, 2, M)
    a.rect(14, 0, 45, 0, H)
    a.poly([(17, 3), (43, 3), (43, 48), (37, 54), (30, 47), (23, 55), (17, 48)], A)
    a.rect(17, 3, 19, 46, A2)
    a.rect(41, 3, 43, 46, A2)
    a.poly([(30, 12), (37, 24), (30, 36), (23, 24)], C)       # 결정 문장
    a.poly([(30, 12), (23, 24), (30, 24)], WHITE)
    a.rect(17, 3, 43, 4, A2)
    a.outline()
    return a.a


def pipe_h(valve):
    a = Art()
    a.rect(0, 14, T - 1, 15, H)
    a.rect(0, 16, T - 1, 19, L)
    a.rect(0, 20, T - 1, 23, M)
    a.rect(0, 24, T - 1, 26, D)
    a.rect(0, 13, T - 1, 13, K)
    a.rect(0, 27, T - 1, 27, K)
    for x0 in (4, 34):                                       # 이음 플랜지
        a.rect(x0, 10, x0 + 5, 30, K)
        a.rect(x0 + 1, 11, x0 + 4, 29, M)
        a.rect(x0 + 1, 11, x0 + 2, 29, L)
    if valve:
        a.rect(18, 3, 27, 12, K)
        a.rect(20, 5, 25, 10, A)
        a.rect(22, 0, 23, 12, K)
        a.rect(14, 5, 31, 6, A)
        a.rect(14, 4, 31, 4, K)
        a.rect(14, 7, 31, 7, K)
    return a.a


def cable():
    """천장 아래로 늘어진 전선."""
    a = Art()
    for x in range(T):
        y = int(4 + 16 * math.sin(math.pi * x / (T - 1)))
        a.rect(x, y, x, y + 1, K)
    return a.a


# ---------- 바닥에 놓이는 소품 ----------
def crate():
    a = Art()
    a.rect(8, 18, 51, 59, W1)
    a.rect(8, 18, 51, 20, W2)
    a.rect(8, 56, 51, 59, W0)
    for x in (8, 9, 50, 51):
        a.rect(x, 18, x, 59, W0)
    a.line(11, 22, 48, 55, W0, 2)
    a.line(48, 22, 11, 55, W0, 2)
    for x in (22, 37):
        a.rect(x, 21, x, 55, W0)
    a.outline()
    return a.a


def barrel():
    a = Art()
    for y in range(14, 60):
        half = 13 + int(5 * (1 - abs(y - 37) / 23) ** 0.8)
        a.rect(30 - half, y, 29 + half, y, W1)
        a.rect(30 - half, y, 30 - half + 3, y, W2)
        a.rect(29 + half - 3, y, 29 + half, y, W0)
    for y in (20, 36, 52):
        a.rect(13, y, 46, y + 2, M)
        a.rect(13, y, 46, y, L)
    a.outline()
    return a.a


def crystal(big):
    """바닥에서 자란 헤이즈 결정 (스스로 빛난다)."""
    a = Art()
    shards = [(30, 8, 9, 60), (18, 26, 6, 60), (43, 20, 7, 60), (10, 42, 4, 60)] if big else \
             [(30, 32, 6, 60), (20, 44, 4, 60), (41, 40, 5, 60)]
    for cx, top, half, base in shards:
        a.poly([(cx, top), (cx + half, top + half * 2), (cx + half - 1, base), (cx - half + 1, base), (cx - half, top + half * 2)], C)
        a.poly([(cx, top), (cx - half, top + half * 2), (cx - half + 1, base), (cx, base)], WHITE)
        a.poly([(cx + 1, top + 3), (cx + half, top + half * 2), (cx + half - 1, base), (cx + 2, base)], C2)
    a.outline()
    return a.a


def debris():
    a = Art()
    a.poly([(6, 59), (16, 46), (30, 50), (42, 42), (54, 59)], D)
    a.poly([(16, 46), (22, 59), (6, 59)], B)
    a.poly([(42, 42), (48, 59), (34, 59)], M)
    a.rect(24, 52, 30, 56, L)
    a.outline()
    return a.a


def haze_vent():
    a = Art()
    a.rect(12, 53, 47, 59, D)
    a.rect(12, 53, 47, 53, M)
    for x in range(16, 46, 6):
        a.rect(x, 55, x + 2, 58, K)
    a.outline()
    a.dither_glow(30, 54, 0, 46, C, density=0.55, squash=2.2)
    a.a[54:, :][a.a[54:, :] == C] = CLEAR
    return a.a


# ---------- 문 ----------
def door_v(part, bars):
    """좌우 벽의 문 (왼쪽 벽 기준, 오른쪽은 좌우 반전). part: 0 위, 1 가운데, 2 아래. bars면 잠긴 쇠창살."""
    a = Art()
    a.rect(0, 0, T - 1, T - 1, MORTAR)                       # 문 안쪽은 어둡다
    a.rect(T - 8, 0, T - 1, T - 1, M)                        # 방 쪽 문설주
    a.rect(T - 8, 0, T - 7, T - 1, H)
    a.rect(T - 2, 0, T - 1, T - 1, D)
    a.rect(T - 9, 0, T - 9, T - 1, K)
    if part == 0:
        a.rect(0, 0, T - 1, 9, M)                            # 상인방
        a.rect(0, 0, T - 1, 1, H)
        a.rect(0, 8, T - 1, 9, D)
        a.rect(0, 10, T - 1, 10, K)
        a.rect(T - 6, 12, T - 3, 17, A if bars else C)       # 문 위 표시등
        a.rect(T - 7, 11, T - 2, 11, K)
        a.rect(T - 7, 18, T - 2, 18, K)
    if part == 2:
        a.rect(0, T - 4, T - 1, T - 1, D)                    # 문턱
        a.rect(0, T - 5, T - 1, T - 5, K)
    if bars:
        for x in (8, 20, 32, 44):
            a.rect(x, 11 if part == 0 else 0, x + 3, T - 6 if part == 2 else T - 1, L)
            a.rect(x + 3, 11 if part == 0 else 0, x + 3, T - 6 if part == 2 else T - 1, D)
            a.rect(x - 1, 11 if part == 0 else 0, x - 1, T - 6 if part == 2 else T - 1, K)
            a.rect(x + 4, 11 if part == 0 else 0, x + 4, T - 6 if part == 2 else T - 1, K)
        if part == 1:
            a.rect(0, 26, T - 10, 31, M)
            a.rect(0, 26, T - 10, 26, L)
            a.rect(0, 25, T - 10, 25, K)
            a.rect(0, 32, T - 10, 32, K)
    return a.a


def door_h(part, bars):
    """위·아래의 문 (가로 3칸). part: 0 왼쪽, 1 가운데, 2 오른쪽. 아래쪽 문은 상하 반전 없이 같은 그림을 쓴다."""
    a = Art()
    a.rect(0, 0, T - 1, T - 1, MORTAR)
    a.rect(0, T - 8, T - 1, T - 1, M)                        # 방 쪽 테두리
    a.rect(0, T - 8, T - 1, T - 7, H)
    a.rect(0, T - 2, T - 1, T - 1, D)
    a.rect(0, T - 9, T - 1, T - 9, K)
    if part == 0:
        a.rect(0, 0, 8, T - 1, M)
        a.rect(0, 0, 1, T - 1, H)
        a.rect(9, 0, 9, T - 9, K)
    if part == 2:
        a.rect(T - 9, 0, T - 1, T - 1, M)
        a.rect(T - 2, 0, T - 1, T - 1, D)
        a.rect(T - 10, 0, T - 10, T - 9, K)
    if bars:
        for y in (8, 22, 36):
            a.rect(10 if part == 0 else 0, y, T - 11 if part == 2 else T - 1, y + 3, L)
            a.rect(10 if part == 0 else 0, y + 3, T - 11 if part == 2 else T - 1, y + 3, D)
            a.rect(10 if part == 0 else 0, y - 1, T - 11 if part == 2 else T - 1, y - 1, K)
            a.rect(10 if part == 0 else 0, y + 4, T - 11 if part == 2 else T - 1, y + 4, K)
    return a.a


def door_glow(vertical):
    """문틈으로 새는 빛. 흰색으로 그려 두고 게임에서 문 너머 방 종류 색을 곱한다."""
    a = Art()
    bay = np.tile(BAYER + 0.5, (T // 4 + 1, T // 4 + 1))[:T, :T]
    yy, xx = np.mgrid[0:T, 0:T]
    t = (xx / (T - 10)) if vertical else (yy / (T - 10))      # 바깥(0) -> 방 쪽(1)으로 옅어진다
    on = (bay < 0.85 * (1 - np.clip(t, 0, 1)) ** 1.2) & ((xx < T - 9) if vertical else (yy < T - 9))
    a.a[on] = WHITE
    return a.a


def lamp_glow():
    """램프 아래로 번지는 빛 (120x120, 네 칸)."""
    a = Art(120, 120)
    a.dither_glow(60, 34, 6, 62, C2, density=0.5, squash=1.25)
    a.dither_glow(60, 34, 0, 26, C, density=0.6)
    return a.a


# ====================================================================== 세트 조립
def to_rgba(idx, pal):
    out = np.zeros((*idx.shape, 4), np.uint8)
    for i, col in enumerate(pal):
        out[idx == i] = (*col, 255)
    return out


def build_atlas(theme):
    pal = palette(theme)
    seed = sum(ord(ch) for ch in theme)
    lum = stone_texture(seed)
    tex = tones(lum)
    deep = tones(0.13 + (lum - 0.5) * 0.42)
    sheet = np.full((ROWS * T, COLS * T), CLEAR, dtype=int)

    def put(tile, col, row):
        h, w = tile.shape
        sheet[row * T:row * T + h, col * T:col * T + w] = tile

    for variant in range(4):
        for mask in range(16):
            put(solid_tile(tex, deep, variant, mask, seed + variant * 31 + mask), mask, variant)
    for v in range(4):
        put(deep_tile(deep, v), v, 4)
        put(oneway(v), 4 + v, 4)
    put(spike(0), 8, 4)
    put(spike(1), 9, 4)
    for i, art in enumerate((wall_window(), wall_vent(), wall_outlet(), wall_stencil(9 + seed % 3 * 30), wall_crack(), wall_stain())):
        put(art, 10 + i, 4)
    row5 = (chain(0), chain(1), chain(2), lamp(), banner(), pipe_h(False), pipe_h(True), cable(),
            crate(), barrel(), crystal(False), crystal(True), debris(), haze_vent())
    for i, art in enumerate(row5):
        put(art, i, 5)
    row6 = (door_v(0, False), door_v(1, False), door_v(2, False), door_v(0, True), door_v(1, True), door_v(2, True),
            door_glow(True), door_h(0, False), door_h(1, False), door_h(2, False), door_h(0, True), door_h(1, True),
            door_h(2, True), door_glow(False))
    for i, art in enumerate(row6):
        put(art, i, 6)
    put(lamp_glow(), 0, 7)
    Image.fromarray(to_rgba(sheet, pal), 'RGBA').save(os.path.join(TILE_DIR, f'tile_set_{theme}.png'))
    print('saved tile_set', theme)


# ====================================================================== 원경 (Codex 배경판에 테마 색 입히기)
def build_far(theme):
    pal = palette(theme)
    k, d, b_, c = pal[K], pal[D], pal[B], pal[C]
    src = Image.open(os.path.join(FORGE_BG, BG_SOURCE[theme] + '.png')).convert('RGB')
    arr = np.asarray(src).astype(float)
    lum = arr @ np.array([0.30, 0.59, 0.11])
    sat = arr.max(axis=2) - arr.min(axis=2)
    lamp_mask = (lum > 150) & (sat > 60)                      # 원화의 밝은 등불·수정
    body = lum[~lamp_mask]
    lo, hi = np.percentile(body, 1), np.percentile(body, 99.5)
    t = np.clip((lum - lo) / max(hi - lo, 1), 0, 1) ** 0.9
    stops = [(0.0, mix(k, (0, 0, 0), 0.35)), (0.35, mix(k, d, 0.45)), (0.7, mix(k, d, 0.95)), (1.0, mix(d, b_, 0.55))]
    out = np.zeros_like(arr)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        m = (t >= t0) & (t <= t1)
        f = ((t - t0) / (t1 - t0))[..., None]
        out[m] = (np.array(c0) + (np.array(c1) - np.array(c0)) * f)[m]
    out[lamp_mask] = mix(c, k, 0.25)
    img = Image.fromarray(out.astype(np.uint8), 'RGB').quantize(24, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    img.convert('RGB').save(os.path.join(BG_DIR, f'far_{theme}.png'))
    print('saved far', theme)


# ====================================================================== 중경 (시차 실루엣)
def build_mid(theme):
    pal = palette(theme)
    W, Hh = 1920, 1200
    body, rim, glow = mix(pal[K], pal[D], 0.72), mix(pal[D], pal[B], 0.35), pal[C2]
    img = np.zeros((Hh, W, 4), np.uint8)
    rng = np.random.RandomState(sum(ord(ch) for ch in theme) * 7 + 1)

    def box(x0, y0, x1, y1, col):
        for xa, xb in ((x0, x1),) if x1 <= W else ((x0, W), (0, x1 - W)):
            img[max(0, y0):min(Hh, y1), max(0, xa):xb] = (*col, 255)

    x = rng.randint(0, 200)
    cols = []
    while x < W - 120:                                        # 기둥
        w = int(rng.randint(54, 96))
        broken = rng.rand() < 0.3
        top = int(rng.randint(420, 700)) if broken else 0
        box(x, top, x + w, Hh, body)
        box(x, top, x + 3, Hh, rim)
        if not broken:
            box(x - 14, 150, x + w + 14, 186, body)           # 기둥머리
            box(x - 14, 150, x + w + 14, 153, rim)
        else:
            for i in range(0, w, 6):                          # 부러진 윗면
                box(x + i, top - int(rng.randint(0, 22)), x + i + 6, top + 2, body)
        for y0 in range(top + 120, Hh, 150):                  # 이음매
            box(x, y0, x + w, y0 + 3, rim)
        cols.append((x, w))
        x += w + int(rng.randint(260, 470))
    box(0, 96, W, 150, body)                                  # 들보
    box(0, 96, W, 99, rim)
    box(0, 147, W, 150, mix(pal[K], pal[D], 0.4))
    for _ in range(9):                                        # 들보에서 늘어진 사슬과 추
        cx = int(rng.randint(40, W - 40))
        length = int(rng.randint(120, 520))
        for y0 in range(150, 150 + length, 12):
            box(cx, y0, cx + 4, y0 + 8, body)
            box(cx + 1, y0 + 8, cx + 3, y0 + 12, rim)
        if rng.rand() < 0.5:
            box(cx - 12, 150 + length, cx + 16, 150 + length + 34, body)
            box(cx - 12, 150 + length, cx + 16, 150 + length + 3, rim)
        elif theme in ('haze', 'cell', 'boss'):                # 매달린 결정 등
            for i in range(14):
                half = 7 - abs(i - 6) if i < 12 else 2
                box(cx + 2 - half, 150 + length + i * 2, cx + 2 + half, 150 + length + i * 2 + 2, glow)
    yy, xx = np.mgrid[0:Hh, 0:W]
    bay = np.tile(BAYER + 0.5, (Hh // 4 + 1, W // 4 + 1))[:Hh, :W]
    fog = (bay < 0.34 * np.clip((yy - 860) / 300, 0, 1) ** 1.3) & (img[:, :, 3] == 0)   # 바닥에 깔린 안개
    img[fog] = (*mix(pal[C], pal[K], 0.72), 255)
    Image.fromarray(img, 'RGBA').save(os.path.join(BG_DIR, f'mid_{theme}.png'))
    print('saved mid', theme)


def main():
    os.makedirs(TILE_DIR, exist_ok=True)
    os.makedirs(BG_DIR, exist_ok=True)
    old = '--backdrops-v1' in sys.argv          # 2026-11-25: 원경·중경은 Codex T49 그림을 쓴다 (tools/apply_backdrops_v6.py)
    for theme in ([a for a in sys.argv[1:] if not a.startswith('--')] or list(THEMES)):
        build_atlas(theme)
        if old:                                 # 예전 원경·중경(코드 그림)으로 되돌릴 때만
            build_far(theme)
            build_mid(theme)


if __name__ == '__main__':
    main()
