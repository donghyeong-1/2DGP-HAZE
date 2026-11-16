"""타일·소품·배경을 코드로 새로 그린다 (이미지 모델 없음, numpy + Pillow).

예전 타일(tools/codeart의 SVG 5종)은 같은 벽돌 모양 하나였다. 이 판은 다음을 한다:
  * **자동 타일링**: 벽 타일이 위·오른쪽·아래·왼쪽 이웃이 비었는지(16가지)에 따라 모서리와 테두리가 다르게 그려진다.
    윗면은 밝은 테두리, 아랫면은 녹물이 흐르는 어두운 밑면, 옆면은 빛과 그림자. 안쪽은 판 이음매·리벳·환기구·균열 3변형.
  * **방마다 다른 테마 6종**: cell(감방 청회색) foundry(제련소 녹슨 주황) haze(헤이즈 청록) gold(황금방 황동)
    shop(정비방 청색) boss(보스 붉은색). 같은 모양을 다른 팔레트로 칠한다.
  * **뒷벽·소품**: 방 안쪽 뒷벽 판넬, 천장에서 내려오는 사슬·램프·배너·파이프, 철창 창문, 바닥의 상자·통·헤이즈 분출구.
  * **배경**: 테마별 1920x1080 (먼 기둥·아치·수정·바닥 안개를 4톤 디더링으로).
논리 해상도는 타일 30x30, 배경 960x540이고 정수 2배(최근접)로 키워 저장한다 (다른 픽셀 에셋과 같은 굵기).

결과: assets/tiles/tile_set_<테마>.png (16열 x 5줄, 칸 60x60)와 assets/backgrounds/bg_<테마>.png
  줄 0~2: 벽 3변형 x 16가지 이웃 마스크(비트 1 위, 2 오른쪽, 4 아래, 8 왼쪽이 비어 있음)
  줄 3: 얇은 바닥 4(단독·왼끝·가운데·오른끝), 가시 2, 뒷벽 4
  줄 4: 사슬 위·사슬 가운데·램프·가로 파이프·배너·창문·상자·통·분출구
사용: python tools/make_tiles_hq.py
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILE_DIR = os.path.join(ROOT, 'assets', 'tiles')
BG_DIR = os.path.join(ROOT, 'assets', 'backgrounds')
N = 30                     # 타일 논리 크기 (x2 = 60px)

THEMES = {
    #           K 외곽       D 어두움     B 바탕       M 중간       L 밝음       H 하이라이트  A 포인트      C 빛
    'cell':    ('#0b1020', '#151c30', '#26304a', '#34415f', '#50648a', '#8fa5c8', '#7a4a3a', '#5fd6e8'),
    'foundry': ('#140a0a', '#2a1612', '#40251c', '#5a3425', '#8a5836', '#d08a4a', '#e06a2c', '#ffb347'),
    'haze':    ('#061418', '#0e2a30', '#164048', '#1f5a64', '#2f8a92', '#7fe8e8', '#2a6a8a', '#b8fff4'),
    'gold':    ('#140e04', '#2a200c', '#4a3a18', '#6a5420', '#a8862e', '#f0d070', '#a04a2a', '#fff0a0'),
    'shop':    ('#04141a', '#0c2a36', '#164256', '#1f5a74', '#3a8aaa', '#9fe4ff', '#c8a040', '#7fe8ff'),
    'boss':    ('#12060a', '#2a0e16', '#44141f', '#5e1c2a', '#8c2c40', '#e0606c', '#ffb040', '#ff6070'),
}
WOOD = ('#4a3220', '#6b4a2e', '#8a6038')


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hsh(a, b=0, c=0):
    return ((a * 73856093) ^ (b * 19349663) ^ (c * 83492791)) & 0xFFFF


class Pal:
    def __init__(self, cols):
        names = 'K D B M L H A C'.split()
        for n, c in zip(names, cols):
            setattr(self, n, rgb(c))
        dark = lambda c, f: tuple(min(255, int(v * f)) for v in c)
        self.W0 = tuple(int(v * 0.62) for v in self.D)             # 뒷벽 바탕 (벽 타일보다 어둡다)
        self.W1 = tuple(int(v * 0.85) for v in self.D)
        self.W2 = tuple(min(255, int(v * 0.8) + 8) for v in self.B)
        self.wood = [rgb(c) for c in WOOD]


class Tile:
    def __init__(self):
        self.a = np.zeros((N, N, 4), np.uint8)

    def put(self, x, y, col):
        if 0 <= x < N and 0 <= y < N:
            self.a[y, x] = (*col, 255)

    def clear(self, x, y):
        if 0 <= x < N and 0 <= y < N:
            self.a[y, x] = (0, 0, 0, 0)

    def rect(self, x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, col)

    def at(self, x, y):
        return tuple(self.a[y, x][:3])


# ----- 벽 -----
def solid_tile(p, variant, mask, tx, ty):
    t = Tile()
    seed = variant * 17 + 3
    for y in range(N):
        j = y // 15
        off = (j % 2) * 7
        for x in range(N):
            px, py = (x + off) % 15, y % 15
            if px == 0 or py == 0:
                col = p.D
            else:
                col = p.B
                if py == 1 or px == 1:
                    col = p.M                                      # 판의 위·왼 모서리 빛
                r = hsh(x, y, seed) % 100
                if r < 6:
                    col = p.M
                elif r < 8:
                    col = p.D
            t.put(x, y, col)
    if variant == 1:                                               # 리벳 + 환기구
        for j in range(2):
            off = (j % 2) * 7
            for x0 in (3, 11):
                t.put((x0 - off) % N, j * 15 + 3, p.L)
        for k in range(5):
            t.rect(8, 21 + k, 20, 21 + k, p.D if k % 2 == 0 else p.M)
        t.rect(7, 20, 21, 20, p.K)
        t.rect(7, 26, 21, 26, p.K)
    elif variant == 2:                                             # 균열과 녹물
        x, y = 8 + hsh(tx, ty, 5) % 10, 3
        for _ in range(16):
            t.put(x, y, p.D)
            y += 1
            x += (hsh(x, y, tx + ty) % 3) - 1
        for k in range(1, 5):
            t.put(x, y + k, p.A)
    exposed_edges(t, p, mask, tx, ty)
    return t


def exposed_edges(t, p, mask, tx, ty):
    up, right, down, left = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
    if right:
        for y in range(N):
            t.put(N - 1, y, p.K)
            t.put(N - 2, y, p.D)
            t.put(N - 3, y, p.D if y % 2 == 0 else p.B)
    if left:
        for y in range(N):
            t.put(0, y, p.K)
            t.put(1, y, p.L)
            t.put(2, y, p.M)
    if down:
        for x in range(N):
            t.put(x, N - 1, p.K)
            t.put(x, N - 2, p.D)
            t.put(x, N - 3, p.D if x % 2 == 0 else p.B)
            if hsh(x, tx, ty) % 9 == 0:                            # 녹물이 흘러내린 자국
                for k in range(3 + hsh(x, ty) % 3):
                    t.put(x, N - 4 - k, p.A)
    if up:
        for x in range(N):
            t.put(x, 0, p.K)
            t.put(x, 1, p.H)
            t.put(x, 2, p.H)
            t.put(x, 3, p.L)
            t.put(x, 4, p.L)
            t.put(x, 5, p.M if x % 2 == 0 else p.B)
            if hsh(x, tx, ty + 9) % 13 == 0:                       # 윗면에 쌓인 헤이즈 가루
                t.put(x, 1, p.C)
    for (cx, cy, e1, e2, dx, dy) in ((0, 0, up, left, 1, 1), (N - 1, 0, up, right, -1, 1),
                                     (0, N - 1, down, left, 1, -1), (N - 1, N - 1, down, right, -1, -1)):
        if e1 and e2:                                              # 바깥 모서리를 둥글게
            t.clear(cx, cy)
            t.put(cx + dx, cy, p.K)
            t.put(cx, cy + dy, p.K)


# ----- 얇은 바닥, 가시 -----
def oneway_tile(p, kind):
    t = Tile()
    left_cap, right_cap = kind in (0, 1), kind in (0, 3)
    for x in range(N):
        t.put(x, 0, p.K)
        t.put(x, 1, p.H)
        for y in (2, 3, 4):
            stripe = ((x + y) // 4) % 2 == 0
            t.put(x, y, p.A if stripe else p.L)
        t.put(x, 5, p.M)
        t.put(x, 6, p.D if x % 3 else p.K)
        t.put(x, 7, p.K)
    if left_cap:
        for y in range(0, 8):
            t.put(0, y, p.K)
            if 1 < y < 7:
                t.put(1, y, p.H)
        for k in range(10):                                        # 버팀대
            t.put(2, 8 + k, p.D)
            t.put(1, 8 + k, p.K)
    if right_cap:
        for y in range(0, 8):
            t.put(N - 1, y, p.K)
        for k in range(10):
            t.put(N - 3, 8 + k, p.D)
            t.put(N - 2, 8 + k, p.K)
    if kind in (1, 2, 3) and not left_cap:
        pass
    if kind == 2 or kind == 0:
        for x in (14, 15):                                         # 가운데 보조 버팀
            for k in range(6):
                t.put(x, 8 + k, p.D)
    return t


def spike_tile(p, kind):
    t = Tile()
    for s in range(3):
        x0 = s * 10
        for y in range(15, N):
            half = 1 + int((y - 15) / 14 * 4.2)
            for x in range(5 - half, 5 + half + 1):
                col = p.L if x < 5 else p.M
                if y - 15 < 2:
                    col = p.H
                t.put(x0 + x, y, col)
            t.put(x0 + 5 - half - 1, y, p.K)
            t.put(x0 + 5 + half + 1, y, p.K)
        t.put(x0 + 5, 14, p.K)
        if kind == 1:                                              # 녹과 피
            for y in range(19, 24):
                t.put(x0 + 5, y, p.A)
    t.rect(0, 27, N - 1, 28, p.D)
    t.rect(0, 29, N - 1, 29, p.K)
    return t


# ----- 뒷벽 -----
def backwall_tile(p, kind):
    t = Tile()
    for y in range(N):
        for x in range(N):
            seam = x % 15 == 0 or y % 15 == 0
            col = p.W1 if seam else p.W0
            if not seam and hsh(x, y, kind) % 100 < 4:
                col = p.W1
            t.put(x, y, col)
    if kind == 1:                                                  # 세로 파이프
        for y in range(N):
            for x in range(12, 18):
                t.put(x, y, p.W2 if x in (13, 14) else p.W1)
            t.put(11, y, p.W0)
            t.put(18, y, p.W0)
        for y in (6, 22):
            t.rect(10, y, 19, y + 1, p.W2)
    elif kind == 2:
        for x0, y0 in ((4, 4), (24, 4), (4, 24), (24, 24)):
            t.put(x0, y0, p.W2)
    elif kind == 3:                                                # 환기구
        t.rect(7, 8, 22, 21, p.W0)
        for k in range(7):
            t.rect(8, 9 + k * 2, 21, 9 + k * 2, p.W2)
        t.rect(6, 7, 23, 7, p.W1)
        t.rect(6, 22, 23, 22, p.W1)
    return t


# ----- 소품 -----
def chain_tile(p, top):
    t = Tile()
    for y in range(N):
        k = (y // 4) % 2
        col = p.L if k == 0 else p.D
        for x in (13, 16):
            t.put(x, y, p.K)
        for x in (14, 15):
            t.put(x, y, col)
    if top:
        t.rect(9, 0, 20, 3, p.K)
        t.rect(10, 0, 19, 2, p.M)
        t.rect(10, 0, 19, 0, p.H)
    return t


def lamp_tile(p):
    t = Tile()
    for y in range(0, 8):
        for x in (14, 15):
            t.put(x, y, p.D)
    t.rect(9, 8, 20, 10, p.K)                                      # 갓
    t.rect(10, 8, 19, 9, p.M)
    t.rect(10, 8, 19, 8, p.L)
    for y in range(11, 18):                                        # 전구와 퍼지는 빛
        half = 4 if y < 15 else 3 - (y - 15)
        for x in range(15 - half, 15 + half):
            t.put(x, y, p.C)
    t.rect(12, 18, 17, 18, p.K)
    for y in range(8, N):                                          # 빛 번짐 (엇갈린 점)
        for x in range(2, 28):
            d = ((x - 14.5) ** 2 + ((y - 14) * 1.1) ** 2) ** 0.5
            if 6.5 < d < 13 and (x + y) % 2 == 0 and hsh(x, y) % 100 < 70 - d * 4 and t.a[y, x][3] == 0:
                t.put(x, y, p.C)
    return t


def pipe_tile(p):
    t = Tile()
    for x in range(N):
        t.put(x, 7, p.K)
        t.put(x, 8, p.H if x % 15 > 1 else p.L)
        t.put(x, 9, p.L)
        t.put(x, 10, p.M)
        t.put(x, 11, p.M)
        t.put(x, 12, p.D)
        t.put(x, 13, p.K)
    for x0 in (0, 15):                                             # 플랜지 이음
        t.rect(x0, 5, x0 + 1, 15, p.K)
        t.rect(x0, 6, x0, 14, p.L)
    return t


def banner_tile(p):
    t = Tile()
    t.rect(7, 0, 22, 1, p.K)
    t.rect(8, 0, 21, 0, p.H)
    for y in range(2, 27):
        w = 7 if y < 22 else 7 - (y - 21) * 2 // 1 // 2
        for x in range(15 - w, 15 + w):
            col = p.A
            if x in (15 - w, 14 + w):
                col = p.H
            t.put(x, y, col)
        t.put(15 - w - 1, y, p.K)
        t.put(15 + w, y, p.K)
    for k in range(4):                                             # 가운데 무늬(마름모)
        for x in range(14 - k, 16 + k):
            t.put(x, 9 + k, p.C)
            t.put(x, 15 - k, p.C)
    return t


def window_tile(p):
    t = Tile()
    t.rect(7, 4, 22, 25, p.K)
    for y in range(6, 24):
        for x in range(9, 21):
            f = (y - 6) / 18
            col = p.C if (f < 0.35 or (f < 0.6 and (x + y) % 2 == 0)) else p.M
            t.put(x, y, col)
    for x in (11, 14, 17):
        t.rect(x, 5, x, 24, p.K)                                   # 철창
    t.rect(8, 14, 21, 14, p.K)
    t.rect(6, 25, 23, 26, p.D)
    return t


def crate_tile(p):
    t = Tile()
    d, m, l = p.wood
    t.rect(4, 8, 25, 29, p.K)
    t.rect(5, 9, 24, 28, m)
    for k in range(5, 25):
        t.put(k, 9, l)
        t.put(k, 28, d)
    for x in (5, 24):
        t.rect(x, 9, x, 28, d)
    for k in range(18):                                            # 가새
        t.put(6 + k, 10 + k, d)
        t.put(23 - k, 10 + k, d)
    return t


def barrel_tile(p):
    t = Tile()
    d, m, l = p.wood
    for y in range(6, 30):
        half = 7 + int(3 * (1 - abs(y - 18) / 12))
        for x in range(15 - half, 15 + half):
            t.put(x, y, m if x > 15 - half + 1 else l)
        t.put(15 - half - 1, y, p.K)
        t.put(15 + half, y, p.K)
    for y in (10, 25):
        for x in range(8, 22):
            t.put(x, y, p.L)
    t.rect(8, 5, 21, 5, p.K)
    t.rect(8, 30 - 1, 21, 29, p.K)
    return t


def vent_tile(p):
    t = Tile()
    for x in range(6, 25):
        t.put(x, 27, p.K)
        t.put(x, 28, p.D)
        t.put(x, 29, p.K)
    for x in range(10, 21):
        t.put(x, 26, p.C)
    for y in range(8, 26):                                         # 솟는 헤이즈
        spread = (26 - y) // 4
        for x in range(10 - spread, 21 + spread):
            if (x + y) % 2 == 0 and hsh(x, y) % 100 < 55 - (26 - y) * 2:
                t.put(x, y, p.C)
    return t


SPRITES = [lambda p: chain_tile(p, True), lambda p: chain_tile(p, False), lamp_tile, pipe_tile, banner_tile, window_tile,
           crate_tile, barrel_tile, vent_tile]


def up2(arr):
    return np.repeat(np.repeat(arr, 2, axis=0), 2, axis=1)


def build_atlas(name, p):
    S = N * 2
    sheet = Image.new('RGBA', (S * 16, S * 5), (0, 0, 0, 0))

    def paste(tile, col, row):
        sheet.paste(Image.fromarray(up2(tile.a), 'RGBA'), (col * S, row * S))
    for variant in range(3):
        for mask in range(16):
            paste(solid_tile(p, variant, mask, mask, variant), mask, variant)
    for kind in range(4):
        paste(oneway_tile(p, kind), kind, 3)
    for kind in range(2):
        paste(spike_tile(p, kind), 4 + kind, 3)
    for kind in range(4):
        paste(backwall_tile(p, kind), 6 + kind, 3)
    for i, fn in enumerate(SPRITES):
        paste(fn(p), i, 4)
    sheet.save(os.path.join(TILE_DIR, f'tile_set_{name}.png'))
    print('saved tile_set', name, sheet.size)


# ----- 배경 -----
def bayer(h, w, n=4):
    m = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    return np.tile(m, (h // 4 + 1, w // 4 + 1))[:h, :w]


def build_bg(name, p):
    W, H = 960, 540
    rng = np.random.RandomState(hsh(len(name), 7))
    ramp = [p.K, tuple(int(v * 0.6) for v in p.D), p.D, tuple(int((a + b) / 2) for a, b in zip(p.D, p.B)), p.B]
    yy = np.linspace(0, 1, H)[:, None]
    base = 0.25 + 0.9 * yy ** 1.3                                  # 위는 어둡고 아래로 갈수록 밝다
    idx = np.clip((base * 3.2 + (bayer(H, W) - 0.5) * 0.9).astype(int), 0, 3)
    img = np.zeros((H, W, 3), np.uint8)
    for i in range(4):
        img[idx == i] = ramp[i]
    # 먼 기둥과 아치 (한 단계 밝은 실루엣)
    sil = ramp[3]
    rim = p.B
    X, Y = np.meshgrid(np.arange(W), np.arange(H))
    period = 190 + hsh(len(name)) % 40
    for c0 in range(-30, W, period):
        w = 46
        m = (X >= c0) & (X < c0 + w) & (Y > 60)
        img[m] = sil
        img[m & (X < c0 + 3)] = rim
        for y0 in range(110, H, 70):                                # 기둥 이음
            img[(Y == y0) & (X >= c0) & (X < c0 + w)] = ramp[2]
        # 아치
        ax = c0 + w
        span = period - w
        cy = 120
        arch = ((X - (ax + span / 2)) ** 2 / (span / 2) ** 2 + (Y - cy) ** 2 / 70.0 ** 2 <= 1.0) & (Y <= cy)
        archband = (Y > 40) & (Y <= cy) & (X >= ax) & (X < ax + span)
        img[archband & ~arch] = sil
    img[(Y >= 40) & (Y < 54)] = sil                                # 가로 대들보
    img[(Y >= 54) & (Y < 56)] = ramp[2]
    # 헤이즈 수정: 바닥과 천장에서 자란 큰 결정
    for k in range(7):
        cx = int(rng.rand() * W)
        base_y = H if k % 2 == 0 else 0
        h = 90 + int(rng.rand() * 120)
        wid = 18 + int(rng.rand() * 22)
        sign = -1 if base_y == H else 1
        for y in range(h):
            half = int(wid * (1 - y / h))
            ys = base_y + sign * y
            if 0 <= ys < H:
                x0, x1 = max(0, cx - half), min(W, cx + half)
                if x1 > x0:
                    mid = (x0 + x1) // 2
                    img[ys, x0:mid] = p.M                               # 면이 갈린 결정: 왼쪽은 밝고 오른쪽은 어둡다
                    img[ys, mid:x1] = p.B
                    img[ys, x0:min(W, x0 + 2)] = p.L
                    img[ys, mid:min(W, mid + 1)] = p.D
    # 아래에서 올라오는 헤이즈 안개
    fog = (np.clip((Y - H * 0.62) / (H * 0.38), 0, 1) ** 1.6 * 0.6 + (bayer(H, W) - 0.5) * 0.5) > 0.42
    img[fog & ((X + Y) % 2 == 0)] = tuple(int(v * 0.55) for v in p.C)
    # 비네트
    vx = np.minimum(X, W - 1 - X) / (W * 0.22)
    dark = (np.clip(vx, 0, 1) + (bayer(H, W) - 0.5) * 0.5) < 0.18
    img[dark] = ramp[0]
    big = np.repeat(np.repeat(img, 2, axis=0), 2, axis=1)
    Image.fromarray(big, 'RGB').save(os.path.join(BG_DIR, f'bg_{name}.png'))
    print('saved bg', name, big.shape)


def main():
    os.makedirs(TILE_DIR, exist_ok=True)
    os.makedirs(BG_DIR, exist_ok=True)
    names = sys.argv[1:] or list(THEMES)
    for name in names:
        p = Pal(THEMES[name])
        build_atlas(name, p)
        build_bg(name, p)


if __name__ == '__main__':
    main()
