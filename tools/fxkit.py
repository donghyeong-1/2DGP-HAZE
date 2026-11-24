"""fxkit: 헤이즈 이펙트 제작 도구 (2026-11-24, 사용자 요청 "pixelfx가 이펙트를 만드는 방식을 채용해서 이나리처럼").
code-drawn, 전부 자체 구현 (numpy + Pillow, 이미지 모델 없음). 게임 실행 코드(src)는 이 파일을 쓰지 않는다.

방식은 patch-gg/pixelfx(MIT)와 그 바탕인 Hugo Duprez의 Sprite Fusion VFX 글에서 배웠다 (코드·결과물은 가져오지 않았다,
docs/REFERENCES.md):
  1. 이펙트 하나 = 작은 코드 하나. 시간에 따라 두 버퍼에 그린다: **색 층**(알파 0/255, 팔레트 몇 색)과 **빛 층**(부드러운 더하기 빛).
  2. 면을 칠하지 않고 **선과 빛**으로 만든다: 1px 테두리·고리·줄기·불티. 밝기는 빛 층이 맡는다.
  3. **진짜 움직임**: 불티는 속도만큼 늘어나고 떨어지고 튄다. 파편은 돌며 날아가다 사라진다. 끌림(drag)으로 빠르게 터지고 천천히 흩어진다.
  4. **단계가 있는 연출**: 모으기 -> 터지는 1~2프레임(흰 주인공 프레임) -> 퍼짐 -> 머무름(반짝임·불티) -> 긴 소멸.
  5. 그리고 **본다**: 프레임을 한 장에 모은 그림(contact sheet)을 캐릭터 크기와 함께 보고, 가장 어색한 것부터 고친다(3번 이상).

좌표: (0, 0)이 기준점(맞은 자리·발밑). x 오른쪽, y **아래**(그림 좌표). 1 = 논리 픽셀 1칸 = 화면 2px (json scale 2).
시뮬레이션은 120Hz로 돌리고 fps(기본 30)마다 한 장을 굽는다. 난수는 seed로만 (다시 구워도 같은 그림).

쓰는 법은 .claude/skills/haze-fx/SKILL.md, 실제 이펙트는 tools/make_fx2.py.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = math.tau
GRAVITY = 520.0                      # 논리 px/s^2 (화면 1040). 불티·파편이 떨어지는 세기
WHITE = (255, 255, 255)


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# 색 띠: 어두움 -> 밝음. 마지막은 늘 흰색에 가깝다 (docs/plan_v8.md 4-5 색 언어)
RAMPS = {
    'haze': [hexc(c) for c in ('#0b3f52', '#0e7f93', '#2ee6d6', '#a8fff4', '#ffffff')],      # 기본 청록
    'fade': [hexc(c) for c in ('#27314a', '#4a6288', '#8fb0d8', '#d4e6ff', '#ffffff')],      # 페이드 (힘 빠진 회청)
    'awake': [hexc(c) for c in ('#0a4a6a', '#1496c8', '#5cdcff', '#c4f6ff', '#ffffff')],     # 각성 (밝은 하늘)
    'critical': [hexc(c) for c in ('#4a0a1c', '#a81430', '#ec3a48', '#ffb4b4', '#ffffff')],  # 위험 (레드, 11/24 사용자)
    'violet': [hexc(c) for c in ('#2e1a6e', '#6a3fd0', '#a46bff', '#e6ccff', '#ffffff')],    # 강화 1 / 사슬
    'gold': [hexc(c) for c in ('#5a3608', '#b87a14', '#f0b432', '#ffecaa', '#ffffff')],      # 강화 2
    'crimson': [hexc(c) for c in ('#4a0a1c', '#a81430', '#ec3a48', '#ffb4b4', '#ffffff')],   # 강화 3·표식·처형
    'mint': [hexc(c) for c in ('#0f4a44', '#1fa890', '#7cf2d8', '#d8fff4', '#ffffff')],      # 쌍권총
    'ember': [hexc(c) for c in ('#5a2408', '#c85a1c', '#ff963c', '#ffdca0', '#ffffff')],     # 건틀릿
    'dust': [hexc(c) for c in ('#2a3340', '#4a5868', '#7a8a9a', '#b4c0cc', '#e6eef6')],      # 먼지·연기
}


def smooth(a, b, x):
    if a == b:
        return 1.0 if x >= b else 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def out_expo(t):
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


class Rng:
    def __init__(self, seed):
        self.r = random.Random(seed)

    def range(self, a, b):
        return self.r.uniform(a, b)

    def int(self, a, b):
        return self.r.randint(a, b)

    def pick(self, seq):
        return self.r.choice(seq)

    def chance(self, p):
        return self.r.random() < p


class Painter:
    """한 프레임을 그리는 그림판. 색 층은 칠하는 순간 0/255로 정해진다(반투명 없음). 빛 층은 부드럽게 더한다."""

    def __init__(self, w, h, ox, oy, seed=0):
        self.w, self.h, self.ox, self.oy, self.seed = w, h, ox, oy, seed
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.on = np.zeros((h, w), bool)
        self.light = np.zeros((h, w, 3), np.float32)
        ys, xs = np.mgrid[0:h, 0:w]
        self.X = xs + 0.5 - ox                      # 칸 가운데의 기준점 좌표
        self.Y = ys + 0.5 - oy
        n = ((xs // 2).astype(np.uint64) * 374761393 + (ys // 2).astype(np.uint64) * 668265263 + seed * 2147483647) & 0xffffffff
        n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
        self.grain = ((n ^ (n >> 16)) & 0xffff) / 65535.0          # 2x2 칸마다 고정된 0~1 난수 (조각나며 사라지는 데 쓴다)

    # ----- 바탕 -----
    def _box(self, x0, y0, x1, y1):
        c0, c1 = max(0, int(math.floor(x0 + self.ox))), min(self.w, int(math.ceil(x1 + self.ox)) + 1)
        r0, r1 = max(0, int(math.floor(y0 + self.oy))), min(self.h, int(math.ceil(y1 + self.oy)) + 1)
        if c0 >= c1 or r0 >= r1:
            return None
        return slice(r0, r1), slice(c0, c1)

    def put(self, box, mask, color, a=1.0):
        """box 안의 mask 칸을 color로. a < 1이면 조각 난수로 일부만 칠한다(부서지며 사라짐). color는 (r,g,b) 또는 칸마다의 배열."""
        if a < 1.0:
            mask = mask & (self.grain[box] < a)
        if not mask.any():
            return
        self.on[box] |= mask
        view = self.rgb[box]
        if isinstance(color, np.ndarray):
            view[mask] = color[mask]
        else:
            view[mask] = color

    def put_ramp(self, box, index, ramp, a=1.0):
        """index(칸마다 색 띠 번호, -1은 비움)를 ramp 색으로 칠한다."""
        mask = index >= 0
        if a < 1.0:
            mask = mask & (self.grain[box] < a)
        if not mask.any():
            return
        table = np.array(ramp, np.uint8)
        self.on[box] |= mask
        self.rgb[box][mask] = table[np.clip(index, 0, len(ramp) - 1)][mask]

    # ----- 도형 -----
    def px(self, x, y, color):
        c, r = int(math.floor(x + self.ox)), int(math.floor(y + self.oy))
        if 0 <= c < self.w and 0 <= r < self.h:
            self.rgb[r, c] = color
            self.on[r, c] = True

    def line(self, x0, y0, x1, y1, color, w=1.0, a=1.0):
        """굵기 w의 선 (끝이 둥글다). w=1이면 1px 선."""
        half = max(0.5, w / 2)
        box = self._box(min(x0, x1) - half, min(y0, y1) - half, max(x0, x1) + half, max(y0, y1) + half)
        if box is None:
            return
        X, Y = self.X[box], self.Y[box]
        dx, dy = x1 - x0, y1 - y0
        ll = dx * dx + dy * dy or 1e-6
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / ll, 0, 1)
        d = np.hypot(X - (x0 + dx * t), Y - (y0 + dy * t))
        self.put(box, d <= half, color, a)

    def needle(self, x0, y0, x1, y1, color, w=2.0, tip=None, a=1.0):
        """(x0,y0)에서 굵고 (x1,y1)로 갈수록 가늘어지는 가시·줄기. tip을 주면 끝 1/3은 그 색(보통 흰색)."""
        half = max(0.5, w / 2)
        box = self._box(min(x0, x1) - half, min(y0, y1) - half, max(x0, x1) + half, max(y0, y1) + half)
        if box is None:
            return
        X, Y = self.X[box], self.Y[box]
        dx, dy = x1 - x0, y1 - y0
        ll = dx * dx + dy * dy or 1e-6
        t = np.clip(((X - x0) * dx + (Y - y0) * dy) / ll, 0, 1)
        d = np.hypot(X - (x0 + dx * t), Y - (y0 + dy * t))
        mask = d <= np.maximum(0.5, half * (1 - t))
        self.put(box, mask, color, a)
        if tip is not None:
            self.put(box, mask & (t > 0.62), tip, a)

    def disc(self, x, y, r, color, a=1.0):
        box = self._box(x - r, y - r, x + r, y + r)
        if box is None:
            return
        self.put(box, np.hypot(self.X[box] - x, self.Y[box] - y) <= r, color, a)

    def ring(self, x, y, r, w, color, a=1.0, sy=1.0, a0=None, a1=None, gaps=0, phase=0.0):
        """고리(두께 w). sy < 1이면 바닥에 누운 타원. a0~a1을 주면 그 각도 구간만. gaps > 0이면 그 수만큼 끊어진 고리."""
        box = self._box(x - r - w, y - (r + w) * sy, x + r + w, y + (r + w) * sy)
        if box is None:
            return
        X, Y = self.X[box] - x, (self.Y[box] - y) / sy
        d = np.hypot(X, Y)
        mask = np.abs(d - r) <= max(0.5, w / 2)
        if a0 is not None or gaps:
            ang = np.arctan2(Y, X)
            if a0 is not None:
                u = (ang - a0) % TAU
                mask &= u <= (a1 - a0) % TAU if a1 is not None else True
            if gaps:
                mask &= ((ang + phase) * gaps / TAU) % 1.0 < 0.7
        self.put(box, mask, color, a)

    def poly(self, pts, color, a=1.0):
        """볼록 다각형(삼각 파편·마름모). pts는 시계 방향이든 반대든 상관없다."""
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        box = self._box(min(xs), min(ys), max(xs), max(ys))
        if box is None:
            return
        X, Y = self.X[box], self.Y[box]
        n = len(pts)
        pos = np.ones(X.shape, bool)
        neg = np.ones(X.shape, bool)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            cross = (bx - ax) * (Y - ay) - (by - ay) * (X - ax)
            pos &= cross >= -0.35
            neg &= cross <= 0.35
        self.put(box, pos | neg, color, a)

    def shade(self, x0, y0, x1, y1, fn, ramp, a=1.0):
        """칸마다 계산하는 그림: fn(X, Y) -> 색 띠 번호 배열(-1은 비움). 초승달·불꽃처럼 식으로 그리는 모양."""
        box = self._box(x0, y0, x1, y1)
        if box is None:
            return
        self.put_ramp(box, fn(self.X[box], self.Y[box]), ramp, a)

    # ----- 빛 (더하기) -----
    def glow(self, x, y, r, color, k=1.0):
        """부드러운 둥근 빛. k는 가운데 세기(0~255, 겹치면 더해진다). 색 층에는 아무것도 그리지 않는다.
        기준: 넓은 바탕 빛 60~110, 터지는 순간의 심 120~170, 불티 하나 20~35. 합이 255를 넘는 넓은 면이 생기면 원반처럼 보인다."""
        box = self._box(x - r, y - r, x + r, y + r)
        if box is None or k <= 0:
            return
        d = np.hypot(self.X[box] - x, self.Y[box] - y) / r
        f = np.clip(1 - d, 0, 1) ** 3 * k                    # 가운데만 밝고 넓게 옅어진다
        self.light[box] += f[..., None] * np.array(color, np.float32) / 255.0

    def glow_line(self, x0, y0, x1, y1, r, color, k=1.0):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / max(2.0, r * 0.6)))
        for i in range(n + 1):
            t = i / n
            self.glow(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, color, k / 1.6)

    def glow_ring(self, x, y, r, w, color, k=1.0, sy=1.0):
        box = self._box(x - r - w, y - (r + w) * sy, x + r + w, y + (r + w) * sy)
        if box is None or k <= 0:
            return
        d = np.abs(np.hypot(self.X[box] - x, (self.Y[box] - y) / sy) - r) / w
        f = np.clip(1 - d, 0, 1) ** 2 * k
        self.light[box] += f[..., None] * np.array(color, np.float32) / 255.0

    # ----- 결과 -----
    def images(self):
        rgba = np.zeros((self.h, self.w, 4), np.uint8)
        rgba[..., :3] = self.rgb
        rgba[..., 3] = np.where(self.on, 255, 0)
        lum = np.clip(self.light, 0, 255)
        peak = lum.max(axis=2)
        light = np.zeros((self.h, self.w, 4), np.uint8)
        nz = peak > 1
        light[..., :3][nz] = (lum[nz] / peak[nz][:, None] * 255).astype(np.uint8)     # 색은 가득, 세기는 알파로
        light[..., 3] = np.clip(peak, 0, 255).astype(np.uint8)
        return Image.fromarray(rgba, 'RGBA'), Image.fromarray(light, 'RGBA')


# ----- 입자 -----
SPARK, MOTE, SHARD, EMBER, PUFF = range(5)


class Particles:
    """불티(SPARK: 속도만큼 늘어난 두 색 줄기, 중력, 바닥에서 튄다, 빛남) / 알갱이(MOTE: 끌림이 큰 점, 식으며 사라짐) /
    파편(SHARD: 돌며 날아가는 삼각 조각) / 잿불(EMBER: 떠오르며 흔들리는 점) / 연기 덩이(PUFF: 부풀다 부서지는 덩이)."""

    def __init__(self, rng, ramp, ground=None, sparks=None):
        self.rng, self.ramp, self.ground = rng, ramp, ground
        self.sparks = sparks or ramp
        self.items = []

    def spawn(self, kind, x, y, vx, vy, life, size=1.0, delay=0.0, ramp=None):
        self.items.append(dict(k=kind, x=x, y=y, vx=vx, vy=vy, life=life, age=-delay, s=size, ramp=ramp,
                               rot=self.rng.range(0, TAU), spin=self.rng.range(-14, 14), seed=self.rng.range(0, 100)))

    def burst(self, kind, x, y, n, speed, life, spread=TAU, aim=0.0, up=0.0, size=1.0, delay=(0.0, 0.0), ramp=None):
        """한 점에서 n개를 뿌린다. speed·life·size·delay는 (최소, 최대). aim±spread/2 방향, up만큼 위로 더 민다."""
        for _ in range(n):
            a = aim + self.rng.range(-spread / 2, spread / 2)
            sp = self.rng.range(*speed)
            sz = self.rng.range(*size) if isinstance(size, tuple) else size
            self.spawn(kind, x, y, math.cos(a) * sp, math.sin(a) * sp - up, self.rng.range(*life), sz,
                       self.rng.range(*delay), ramp)

    def update(self, dt):
        keep = []
        for q in self.items:
            q['age'] += dt
            if q['age'] < 0:
                keep.append(q)
                continue
            if q['age'] >= q['life']:
                continue
            k = q['k']
            drag = {SPARK: 2.2, MOTE: 5.5, SHARD: 1.6, EMBER: 2.5, PUFF: 4.5}[k]
            grav = {SPARK: GRAVITY, MOTE: GRAVITY * 0.15, SHARD: GRAVITY * 0.9, EMBER: -60.0, PUFF: -25.0}[k]
            q['vx'] -= q['vx'] * drag * dt
            q['vy'] += (grav - q['vy'] * drag) * dt
            if k == EMBER:
                q['vx'] += math.sin(q['age'] * 9 + q['seed']) * 60 * dt
            q['x'] += q['vx'] * dt
            q['y'] += q['vy'] * dt
            q['rot'] += q['spin'] * dt
            if self.ground is not None and k in (SPARK, SHARD) and q['y'] > self.ground and q['vy'] > 0:
                q['y'] = self.ground
                q['vy'] *= -0.42
                q['vx'] *= 0.6
                q['spin'] *= 0.5
            keep.append(q)
        self.items = keep

    def draw(self, p):
        for q in self.items:
            if q['age'] < 0:
                continue
            u = q['age'] / q['life']                       # 0 태어남 -> 1 사라짐
            ramp = q['ramp'] or (self.sparks if q['k'] == SPARK else self.ramp)
            n = len(ramp)
            hot = ramp[max(0, n - 1 - int(u * 2.4))]       # 식으며 색 띠를 내려간다
            cool = ramp[max(0, n - 2 - int(u * 2.4))]
            x, y, s = q['x'], q['y'], q['s']
            if q['k'] == SPARK:
                sp = math.hypot(q['vx'], q['vy'])
                ln = min(9.0, max(1.0, sp * 0.028)) * (1 - u * 0.5) * s
                dx, dy = (q['vx'] / sp, q['vy'] / sp) if sp > 1 else (0.0, 1.0)
                p.line(x - dx * ln, y - dy * ln, x, y, cool)              # 꼬리
                p.line(x - dx * ln * 0.45, y - dy * ln * 0.45, x, y, hot)  # 머리
                p.glow(x, y, 4 * s, ramp[-2], 30 * (1 - u))
            elif q['k'] == MOTE:
                if u < 0.85 or int(q['age'] * 30) % 2 == 0:            # 사라지기 직전엔 깜빡인다
                    p.px(x, y, hot)
                    if s > 1.2 and u < 0.4:
                        p.px(x + 1, y, hot)
                        p.px(x, y + 1, cool)
            elif q['k'] == SHARD:
                r = (2.2 + 1.6 * s) * (1 - u * 0.6)
                a = round(q['rot'] / (TAU / 8)) * (TAU / 8)            # 8방향으로만 돈다 (픽셀이 떨리지 않게)
                pts = [(x + math.cos(a + t) * r * k2, y + math.sin(a + t) * r * k2) for t, k2 in
                       ((0, 1.0), (2.2, 0.55), (3.9, 0.7))]
                p.poly(pts, cool)
                p.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], hot)    # 빛 받은 한 변
            elif q['k'] == EMBER:
                if int(q['age'] * 20 + q['seed']) % 3 != 0:
                    p.px(x, y, hot)
                    p.glow(x, y, 3, ramp[-2], 24 * (1 - u))
            elif q['k'] == PUFF:
                grow = out_cubic(min(1.0, u * 2.6))
                shrink = 1.0 if u < 0.4 else 1.0 - ((u - 0.4) / 0.6) ** 1.5   # 점무늬로 흩지 않고 줄어들며 사라진다
                r = s * (2.0 + 4.5 * grow) * shrink
                if r >= 0.8:
                    p.disc(x, y, r, ramp[1])
                    if r >= 2.2:
                        p.disc(x - r * 0.28, y - r * 0.32, r * 0.55, ramp[2])     # 빛 받은 윗면


class Lights:
    """터지는 순간 번쩍이고 스러지는 빛 (세기는 남은 수명의 제곱)."""

    def __init__(self):
        self.items = []

    def add(self, x, y, r, color, k, life):
        self.items.append([x, y, r, color, k, life, 0.0])

    def update(self, dt):
        for it in self.items:
            it[6] += dt
        self.items = [it for it in self.items if it[6] < it[5]]

    def draw(self, p):
        for x, y, r, color, k, life, age in self.items:
            p.glow(x, y, r, color, k * (1 - age / life) ** 2)


# ----- 굽기 -----
def render(meta, create, **opts):
    """이펙트를 프레임 목록 [(색 그림, 빛 그림)]으로 굽는다. create(o) -> update(dt)·draw(p)를 가진 객체."""
    w, h = meta['size']
    ox, oy = meta['origin']
    fps = meta.get('fps', 30)
    o = dict(meta.get('options', {}), **opts)
    fx = create(o)
    n = int(round(meta['duration'] * fps))
    frames = []
    sub = max(1, int(round(120 / fps)))
    for i in range(n):
        p = Painter(w, h, ox, oy, seed=o.get('seed', 1) * 131 + i * 7)
        fx.draw(p)
        frames.append(p.images())
        for _ in range(sub):
            fx.update(1.0 / fps / sub)
    return frames


def export(name, meta, variants):
    """assets/effects/<name>.png(+json)과 빛 시트 assets/light/glow_<name>.png를 쓴다. variants는 프레임 목록의 목록
    (방향 변형이 없으면 [frames]). 한 줄에 한 변형."""
    w, h = meta['size']
    n = len(variants[0])
    sheet = Image.new('RGBA', (w * n, h * len(variants)), (0, 0, 0, 0))
    glow = Image.new('RGBA', (w * n, h * len(variants)), (0, 0, 0, 0))
    for r, frames in enumerate(variants):
        assert len(frames) == n
        for c, (color, light) in enumerate(frames):
            sheet.paste(color, (c * w, r * h))
            glow.paste(light, (c * w, r * h))
    sheet.save(os.path.join(ROOT, 'assets', 'effects', name + '.png'))
    glow.save(os.path.join(ROOT, 'assets', 'light', 'glow_' + name + '.png'))
    info = {'id': 'fx/' + name, 'frames': n * len(variants), 'frameSize': [w, h], 'columns': n, 'fps': meta.get('fps', 30),
            'loop': False, 'pivot': list(meta['origin']), 'scale': 2, 'duration': meta['duration'],
            'source': 'tools/make_fx2.py + tools/fxkit.py (code-drawn, numpy, no image model)'}
    if len(variants) > 1:
        info['variants'] = len(variants)
    with open(os.path.join(ROOT, 'assets', 'effects', name + '.json'), 'w', encoding='utf-8') as fp:
        json.dump(info, fp, indent=1)
    return info


def contact(frames, path, zoom=3, cols=8, bg=(9, 14, 24), actor=None, origin=None, label=None):
    """프레임을 한 장에 모아 본다 (색 층 + 빛 층 더하기, 어두운 바탕). actor(주인공 그림 경로)를 주면 크기 비교용으로
    기준점 왼쪽에 반 크기로 세운다. 눈으로 보고 고치는 데 쓴다 (게임에 들어가는 파일이 아니다)."""
    w, h = frames[0][0].size
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGB', (cols * w * zoom, rows * h * zoom + (14 if label else 0)), bg)
    body = None
    if actor and os.path.exists(actor):
        a = Image.open(actor).convert('RGBA')
        a = a.crop(a.getbbox())
        body = a.resize((a.width // 2, a.height // 2), Image.NEAREST)
    for i, (color, light) in enumerate(frames):
        cell = Image.new('RGB', (w, h), bg)
        if body is not None and origin is not None:
            cell.paste(body, (int(origin[0] - body.width - 6), int(origin[1] - body.height // 2)), body)
        base = np.asarray(cell, np.float32)
        la = np.asarray(light, np.float32)
        base = np.clip(base + la[..., :3] * (la[..., 3:4] / 255.0) * 0.85, 0, 255)
        cell = Image.fromarray(base.astype(np.uint8), 'RGB')
        cell.paste(color, (0, 0), color)
        cell = cell.resize((w * zoom, h * zoom), Image.NEAREST)
        d = ImageDraw.Draw(cell)
        d.text((3, 2), str(i), fill=(120, 130, 150))
        out.paste(cell, ((i % cols) * w * zoom, (i // cols) * h * zoom))
    if label:
        ImageDraw.Draw(out).text((4, rows * h * zoom + 1), label, fill=(200, 210, 230))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path)
    return path


# ----- 색을 게임에서 입히는 시트 (베기 자국·방사선·고리처럼 색이 공격마다 다른 것) -----
GRAY = [(96, 96, 96), (150, 150, 150), (205, 205, 205), (255, 255, 255), (255, 255, 255)]   # 색 층: 밝기만 굽고 게임이 색을 곱한다


def export_tint(name, meta, tint_variants, core_variants):
    """두 겹 시트: 위쪽 줄들 = 색을 입힐 층(회색조), 아래쪽 줄들 = 흰 심(색을 안 입힌다). 변형(각도)마다 한 줄씩.
    게임은 effects.draw_tint_sheet가 색 층에 공격 색을 곱해 그리고 그 위에 흰 심을 그린다. 빛 시트는 색 층의 빛만 (게임이 색을 곱한다)."""
    w, h = meta['size']
    v = len(tint_variants)
    n = len(tint_variants[0])
    sheet = Image.new('RGBA', (w * n, h * v * 2), (0, 0, 0, 0))
    glow = Image.new('RGBA', (w * n, h * v), (0, 0, 0, 0))
    for r in range(v):
        for c in range(n):
            sheet.paste(tint_variants[r][c][0], (c * w, r * h))
            sheet.paste(core_variants[r][c][0], (c * w, (r + v) * h))
            glow.paste(tint_variants[r][c][1], (c * w, r * h))
    sheet.save(os.path.join(ROOT, 'assets', 'effects', name + '.png'))
    glow.save(os.path.join(ROOT, 'assets', 'light', 'glow_' + name + '.png'))
    info = {'id': 'fx/' + name, 'frames': n * v * 2, 'frameSize': [w, h], 'columns': n, 'fps': meta.get('fps', 30),
            'loop': False, 'pivot': list(meta['origin']), 'scale': 2, 'duration': meta['duration'], 'variants': v * 2, 'tint': v,
            'source': 'tools/make_fx2.py + tools/fxkit.py (code-drawn, numpy, no image model)'}
    with open(os.path.join(ROOT, 'assets', 'effects', name + '.json'), 'w', encoding='utf-8') as fp:
        json.dump(info, fp, indent=1)
    return info
