"""타격·폭발·먼지 이펙트를 코드로 그린다 (이미지 모델 없음, numpy + Pillow). code-drawn, 전부 자체 제작.

이전에는 외부 MIT 라이브러리(pixelfx)로 렌더링한 시트를 썼다. 순수 창작 원칙에 맞춰 같은 역할의 이펙트를
직접 만든 것으로 바꿨다. 방식은 휘두르기(tools/make_slash_hq.py)와 같다: 프레임마다 '열(heat)' 값을 계산하고
4톤 + 베이어 디더링으로 양자화한다. 절반 해상도 격자에 그리고 게임에서 정수 2배로 키운다 (json의 scale=2).

시트 (assets/effects/<이름>.png + .json):
  hit-fade / hit-normal / hit-awake / hit-critical / hit-enhanced   명중 섬광 (구간·강화별 색과 가시 수)
  puff          먼지·연기 (적 소멸, 기절에서 깨어남)
  surge         위로 솟는 기운 (높은 구간 진입, E 강화 준비)
  haze-blast    헤이즈 폭발 (강화 일격에 맞은 적 주위)
  quake-blast   바닥 충격 폭발 (보스 내려찍기·착지, 바닥에서 솟는 반구)
  death-burst   적이 헤이즈 조각으로 흩어지는 소멸
  dust-land     착지·대시 출발 먼지 (바닥을 따라 좌우로)
  shockwave     보스 바닥 충격파 (반복 재생, 오른쪽 방향. 왼쪽은 좌우 반전)
  ult-nova-<무기>  궁극기 광역 폭발 (11/20, 11/21 무기별): 흰 섬광 -> 충격 고리 + 빛 가시 + 안쪽 소용돌이.
                 철파이프 청록, 식칼 은빛 긴 칼날 가시, 건틀릿 주황 굵은 고리, 사슬 보라 끊어진 고리

사용: python tools/make_fx.py [시트 이름 ...]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'effects')
INK = (11, 16, 32)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5
FLAT = True                                # v7 (2026-11-23): 점묘·어두운 외곽선 없이 깔끔한 단색 면 (INARI 참고)
CUTS = (0.46, 0.30, 0.16, 0.05)          # 열 -> 색 4단계 (흰 코어, 밝음, 중간, 짙음). v7: 흰 코어를 넓게 (예전 0.70, 0.46, 0.22)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(*cols):
    return [rgb(c) for c in cols]


WARM = ramp('#ffffff', '#fff1a6', '#ffb347', '#d0602a')
TEAL = ramp('#ffffff', '#e8fff4', '#33e39e', '#0d6b55')   # v7 A안
FIRE = ramp('#fff4d6', '#ffc457', '#ff6a2e', '#a3262a')
VIOLET = ramp('#ffffff', '#e6ccff', '#a46bff', '#5a2fb8')
DIM = ramp('#d9b4c4', '#a8657f', '#7a3a52', '#4a2238')
SMOKE = ramp('#dfe6f2', '#a9b6cc', '#6f7d99', '#454f68')
HAZE = ramp('#ffffff', '#e6fffb', '#2ee6d6', '#0b6a74')   # v7 A안: 흰 주 + 고대비 청록
QUAKE = ramp('#fff6d8', '#ffd27a', '#e8843a', '#8a4a2a')


def ease_out(p, k=2.4):
    return 1 - (1 - np.clip(p, 0, 1)) ** k


def ease_in(p, k=1.7):
    return np.clip(p, 0, 1) ** k


def smooth_noise(w, h, cells, seed):
    """부드러운 값 노이즈 (0~1). cells x cells 무작위 격자를 쌍선형 보간한다."""
    rng = np.random.RandomState(seed)
    g = rng.rand(cells + 1, cells + 1)
    ys = np.linspace(0, cells, h, endpoint=False)
    xs = np.linspace(0, cells, w, endpoint=False)
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


class Frame:
    """한 프레임. 열 배열을 색으로 바꿔 차례로 덧칠한다."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        self.Y, self.X = np.mgrid[0:h, 0:w].astype(float)
        self.bayer = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]

    def paint(self, heat, colors, dither=0.16, outline=True):
        if FLAT:                                   # v7: 점묘·외곽선 없이 단색 면
            dither, outline = 0.0, False
        th = heat + self.bayer * dither
        idx = np.full(heat.shape, -1)
        for i, cut in enumerate(CUTS):
            idx[(th >= cut) & (idx < 0)] = i
        idx[heat <= 0] = -1
        mask = idx >= 0
        if outline:
            pad = np.pad(mask, 1)
            edge = (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]) & ~mask & (self.a[:, :, 3] == 0)
            self.a[edge] = (*INK, 255)
        for i in range(4):
            self.a[idx == i] = (*colors[i], 255)

    def polar(self, cx, cy):
        dx, dy = self.X - cx, self.Y - cy
        return np.hypot(dx, dy), np.arctan2(dy, dx)

    def blob(self, x, y, radius):
        return np.clip(1 - np.hypot(self.X - x, self.Y - y) / max(radius, 0.01), 0, 1)


# ----- 명중 섬광 -----
def hit_frame(f, t, spikes, rmax, seed, sparks, big_ring):
    cx, cy = f.w / 2, f.h / 2
    r, th = f.polar(cx, cy)
    rout = rmax * ease_out(t / 0.32)
    life = 1 - ease_in((t - 0.3) / 0.7, 1.4)
    heat = np.zeros_like(r)
    if spikes:
        sharp = 2.5 + 14 * t
        star = np.abs(np.cos(spikes * (th + 0.4) / 2)) ** sharp
        rin = rout * 0.30 * (1 - t) + 0.5
        rstar = rin + (rout - rin) * star
        heat = np.clip(1 - r / np.maximum(rstar, 0.01), 0, 1) ** 0.55 * (0.35 + 0.65 * life)
        heat[r > rstar] = 0
    else:                                            # 가시가 없으면 작은 덩어리 (힘 빠진 타격)
        heat = np.clip(1 - r / (rmax * 0.5 * (0.5 + 0.5 * ease_out(t / 0.4))), 0, 1) * life * 0.7
    if big_ring and t > 0.3:                         # 별이 가늘어진 뒤에 충격 고리가 퍼진다
        rr = rmax * (0.45 + 0.6 * ease_out((t - 0.3) / 0.7))
        ring = (np.abs(r - rr) <= 0.5 + 1.0 * (1 - t)) * 0.5 * (1 - t) ** 0.7
        heat = np.maximum(heat, ring)
    rng = np.random.RandomState(seed)
    for _ in range(sparks):
        ang, dist, size = rng.rand() * math.tau, 0.55 + 0.75 * rng.rand(), 0.9 + 1.3 * rng.rand()
        d = rmax * dist * (0.35 + 0.9 * ease_out(t))
        heat = np.maximum(heat, f.blob(cx + math.cos(ang) * d, cy + math.sin(ang) * d, size * (1 - t) + 0.6) * (1 - t) ** 0.5)
    return heat


def build_hit(name, colors, spikes, grid, sparks, big_ring=False, frames=6):
    out = []
    for i in range(frames):
        f = Frame(grid, grid)
        t = (i + 0.4) / frames
        f.paint(hit_frame(f, t, spikes, grid * 0.46, 7 + spikes, sparks, big_ring), colors)
        out.append(f.a)
    return out, (grid // 2, grid // 2)


# ----- 먼지·연기 -----
def puff_heat(f, t, cx, cy, lobes, reach, radius, rise, seed, squash=1.0):
    rng = np.random.RandomState(seed)
    heat = np.zeros((f.h, f.w))
    for k in range(lobes):
        ang = math.tau * k / lobes + rng.rand() * 0.8
        d = reach * (0.25 + 0.75 * ease_out(t)) * (0.6 + 0.6 * rng.rand())
        x = cx + math.cos(ang) * d
        y = cy + math.sin(ang) * d * squash - rise * t
        heat = np.maximum(heat, f.blob(x, y, radius * (0.55 + 0.6 * ease_out(t)) * (0.7 + 0.5 * rng.rand())))
    noise = smooth_noise(f.w, f.h, 6, seed + 3)
    body = np.clip(heat * 1.25 + (noise - 0.5) * 0.35 - 0.95 * ease_in(t, 1.5), 0, 1)
    return np.where(heat > 0, body, 0.0)                   # 덩어리 밖에는 아무것도 그리지 않는다


def build_puff():
    out, g = [], 72
    for i in range(7):
        f = Frame(g, g)
        f.paint(puff_heat(f, (i + 0.3) / 7, g / 2, g * 0.58, 7, 15, 13, 8, 21), SMOKE, dither=0.34, outline=False)
        out.append(f.a)
    return out, (g // 2, int(g * 0.58))


def build_dust():
    out, w, h = [], 96, 36
    for i in range(6):
        f = Frame(w, h)
        t = (i + 0.3) / 6
        heat = np.zeros((h, w))
        for side in (-1, 1):
            for k in range(3):
                x = w / 2 + side * (8 + (12 + 9 * k) * ease_out(t))
                y = h - 6 - k * 2 - 5 * t
                heat = np.maximum(heat, f.blob(x, y, (7 - k) * (0.6 + 0.5 * ease_out(t))))
        noise = smooth_noise(w, h, 6, 5)
        body = np.clip(heat * 1.2 + (noise - 0.5) * 0.3 - 0.9 * ease_in(t, 1.4), 0, 1)
        f.paint(np.where(heat > 0, body, 0.0), SMOKE, dither=0.34, outline=False)
        out.append(f.a)
    return out, (w // 2, h - 2)


# ----- 솟는 기운 -----
def build_surge():
    out, w, h = [], 64, 88
    rng = np.random.RandomState(4)
    streaks = [(w / 2 + (k - 3) * 8 + rng.rand() * 3, 0.0 + 0.09 * abs(k - 3), 0.8 + 0.5 * rng.rand()) for k in range(7)]
    for i in range(7):
        f = Frame(w, h)
        t = (i + 0.3) / 7
        heat = np.zeros((h, w))
        for x, delay, power in streaks:
            tt = t - delay
            if tt <= 0:
                continue
            top = h - 10 - 66 * ease_out(tt) * power
            length = (20 * (1 - tt) + 5) * power
            width = 2.6 * (1 - tt) + 0.7
            inside = np.clip(1 - np.abs(f.X - x) / width, 0, 1) * np.clip(1 - np.abs(f.Y - (top + length / 2)) / (length / 2), 0, 1) ** 0.6
            heat = np.maximum(heat, inside * (1 - tt) ** 0.5)
        rr = 6 + 22 * ease_out(t)                      # 발밑에서 퍼지는 납작한 고리
        ring = np.abs(np.hypot((f.X - w / 2), (f.Y - (h - 8)) * 2.6) - rr) <= 1.0 + 1.4 * (1 - t)
        heat = np.maximum(heat, ring * 0.6 * (1 - t))
        f.paint(heat, HAZE)
        out.append(f.a)
    return out, (w // 2, h - 8)


# ----- 폭발 -----
def blast_heat(f, t, cx, cy, rmax, seed, squash=1.0):
    dx, dy = f.X - cx, (f.Y - cy) / squash
    r, th = np.hypot(dx, dy), np.arctan2(dy, dx)
    wobble = 1 + 0.13 * np.sin(7 * th + seed) + 0.08 * np.sin(13 * th + 2 * seed)
    R = rmax * ease_out(t / 0.42) * wobble
    noise = smooth_noise(f.w, f.h, 8, seed)
    heat = np.clip((1 - r / np.maximum(R, 0.01)) * 1.5 + (noise - 0.5) * 0.45, 0, 1)
    heat[r > R] = 0
    hole = R * ease_in((t - 0.22) / 0.7, 1.2) * 0.96          # 가운데부터 비어 고리 모양 연기로
    heat *= np.clip((r - hole) / 5.0 + 0.2, 0, 1)
    return np.clip(heat - 0.75 * ease_in((t - 0.45) / 0.55, 1.6), 0, 1)


def build_blast(colors, grid, seed):
    out = []
    for i in range(9):
        f = Frame(grid, grid)
        t = (i + 0.3) / 9
        heat = blast_heat(f, t, grid / 2, grid / 2, grid * 0.46, seed)
        if t < 0.25:                                           # 첫 순간의 흰 섬광
            heat = np.maximum(heat, f.blob(grid / 2, grid / 2, grid * 0.3 * (1 - t / 0.25) + 3))
        f.paint(heat, colors, dither=0.26)
        out.append(f.a)
    return out, (grid // 2, grid // 2)


def build_quake():
    out, w, h = [], 220, 120
    for i in range(9):
        f = Frame(w, h)
        t = (i + 0.3) / 9
        heat = blast_heat(f, t, w / 2, h - 4, w * 0.47, 11, squash=0.72)
        heat[f.Y > h - 3] = 0                                  # 바닥 아래는 그리지 않는다 (반구)
        rng = np.random.RandomState(3)
        for _ in range(9):                                     # 튀어 오르는 돌조각
            ang = -math.pi * (0.15 + 0.7 * rng.rand())
            d = w * 0.42 * (0.4 + 0.6 * rng.rand()) * ease_out(t)
            x, y = w / 2 + math.cos(ang) * d, h - 6 + math.sin(ang) * d * 0.9 + 40 * t * t
            heat = np.maximum(heat, f.blob(x, y, 2.4 * (1 - t) + 0.8) * (1 - t) ** 0.4)
        f.paint(heat, QUAKE, dither=0.26)
        out.append(f.a)
    return out, (w // 2, h - 4)


# ----- 적 소멸 -----
def build_death():
    out, g = [], 110
    rng = np.random.RandomState(9)
    shards = [(rng.rand() * math.tau, 0.45 + 0.55 * rng.rand(), 1.6 + 1.6 * rng.rand()) for _ in range(14)]
    for i in range(8):
        f = Frame(g, g)
        t = (i + 0.3) / 8
        cx, cy = g / 2, g / 2
        f.paint(puff_heat(f, t, cx, cy, 8, 22, 15, 6, 31), SMOKE, dither=0.34, outline=False)
        r, _ = f.polar(cx, cy)
        heat = np.zeros((g, g))
        if t < 0.3:
            heat = f.blob(cx, cy, 20 * (1 - t / 0.3) + 4)
        rr = 8 + 40 * ease_out(t)
        heat = np.maximum(heat, (np.abs(r - rr) <= 0.8 + 1.6 * (1 - t)) * 0.55 * (1 - t))
        for ang, dist, size in shards:                         # 헤이즈 조각이 흩어진다 (마름모)
            d = g * 0.44 * dist * ease_out(t)
            x, y = cx + math.cos(ang) * d, cy + math.sin(ang) * d + 14 * t * t
            diamond = np.clip(1 - (np.abs(f.X - x) + np.abs(f.Y - y) * 0.7) / (size * (1 - 0.6 * t) + 0.6), 0, 1)
            heat = np.maximum(heat, diamond * (1 - t) ** 0.35)
        f.paint(heat, HAZE)
        out.append(f.a)
    return out, (g // 2, g // 2)


# ----- 바닥 충격파 (반복) -----
def build_shockwave():
    """바닥을 달리는 불기둥 물결 (오른쪽 방향): 맨 앞 기둥이 가장 높고 뒤로 갈수록 낮다. 4프레임 반복으로 일렁인다."""
    out, w, h = [], 64, 52
    for i in range(4):
        f = Frame(w, h)
        ph = i / 4 * math.tau
        heat = np.zeros((h, w))
        for k in range(4):
            x = w - 12 - k * 13
            height = (h - 8) * (1 - 0.2 * k) * (0.82 + 0.18 * math.sin(ph + k * 1.7))
            width = 7.5 - k * 0.9
            top = h - 4 - height
            v = np.clip((f.Y - top) / max(height, 1), 0, 1)              # 0 꼭대기 -> 1 바닥
            half = width * (0.25 + 0.75 * v ** 0.8) + 1.2 * np.sin(ph * 2 + f.Y * 0.45 + k)
            tongue = np.clip(1 - np.abs(f.X - x) / np.maximum(half, 0.5), 0, 1) ** 0.7 * (0.45 + 0.55 * v)
            tongue[(f.Y < top) | (f.Y > h - 4)] = 0
            heat = np.maximum(heat, tongue * (1 - 0.13 * k))
        base = np.clip(1 - np.abs(f.Y - (h - 5)) / 3.0, 0, 1) * np.clip(f.X / (w * 0.5), 0.3, 1) * 0.7   # 바닥을 따라 깔린 불길
        f.paint(np.maximum(heat, base), FIRE)
        out.append(f.a)
    return out, (w // 2, h - 4)



# ----- 궁극기 광역 폭발 (무기마다 색·모양이 다르다, 11/21 퀄리티 계획 1-6) -----
NOVA_STYLES = {
    # 철파이프: 청록 헤이즈 소용돌이 + 흰·청록 고리, 빛 가시 16개
    'pipe': dict(ring=ramp('#ffffff', '#d8fbff', '#62d6f0', '#2a6f9e'), core=ramp('#ffffff', '#c8f7ff', '#5fd0ee', '#2f6fa8'),
                 spikes=16, spike_len=0.10, spike_w=1.6, rings=((0.47, 2.2, 1.0), (0.38, 4.5, 0.75)), arms=4, links=0),
    # 식칼: 은빛 칼날이 사방으로 길고 가늘게 (가시 28개), 소용돌이 팔 6개
    'knife': dict(ring=ramp('#ffffff', '#eef3fa', '#aab7cc', '#5d6a85'), core=ramp('#ffffff', '#e6edf7', '#9fb0c8', '#56637d'),
                  spikes=28, spike_len=0.16, spike_w=1.0, rings=((0.47, 1.6, 1.0),), arms=6, links=0),
    # 쌍권총 (v7, 2026-11-24): 흰·청록 총탄이 사방으로 길고 가늘게 (가시 32개), 고리 세 겹 (연사)
    'pistol': dict(ring=ramp('#ffffff', '#e6fffb', '#2ee6d6', '#0b6a74'), core=ramp('#ffffff', '#d8fff8', '#5fe8da', '#1a7f86'),
                   spikes=32, spike_len=0.17, spike_w=1.0, rings=((0.47, 1.6, 1.0), (0.40, 1.4, 0.8), (0.33, 1.2, 0.6)), arms=6, links=0),
    # 건틀릿: 주황 충격 + 청록 속, 굵은 고리 두 겹과 짧고 굵은 가시
    'gauntlet': dict(ring=ramp('#fff4d6', '#ffd27a', '#ff8a3a', '#a3402a'), core=ramp('#ffffff', '#b8fff0', '#3fd6a4', '#1f8a78'),
                     spikes=10, spike_len=0.07, spike_w=3.2, rings=((0.46, 3.6, 1.0), (0.36, 6.0, 0.85)), arms=3, links=0),
    # 사슬: 보라 고리가 사슬 고리처럼 끊어져 이어지고(마디 18개), 가시 없음
    'chain': dict(ring=ramp('#ffffff', '#f2e0ff', '#b98cff', '#6a3fd0'), core=ramp('#f6eaff', '#d9b8ff', '#9a62f0', '#4b2a9a'),
                  spikes=0, spike_len=0.0, spike_w=1.0, rings=((0.47, 3.0, 1.0), (0.40, 2.0, 0.8)), arms=5, links=18),
}


def build_nova(style):
    """궁극기 범위를 보여 주는 큰 폭발. 230칸 x 2배 = 지름 약 460px (궁극기 범위와 비슷)."""
    s = NOVA_STYLES[style]
    out, g = [], 230
    c = g / 2
    rng = np.random.RandomState(21)
    spikes = [(rng.rand() * math.tau, 0.65 + 0.35 * rng.rand()) for _ in range(s['spikes'])]
    for i in range(11):
        f = Frame(g, g)
        t = (i + 0.4) / 11
        r, th = f.polar(c, c)
        heat = np.zeros((g, g))
        # 안쪽 소용돌이: 돌면서 퍼지고 가운데부터 비어 간다
        swirl = smooth_noise(g, g, 7, 5 + i // 3)
        spiral = 0.5 + 0.5 * np.sin(s['arms'] * th + r * 0.09 - t * 9)
        inner_r = g * 0.36 * ease_out(t / 0.6)
        core = np.clip(1 - r / np.maximum(inner_r, 1), 0, 1) * (0.55 + 0.45 * spiral + (swirl - 0.5) * 0.35)
        core *= np.clip((r - inner_r * ease_in((t - 0.3) / 0.7, 1.3)) / 6 + 0.15, 0, 1)
        core = np.clip(core - 0.8 * ease_in((t - 0.5) / 0.5, 1.4), 0, 1)
        f.paint(core, s['core'], dither=0.3, outline=False)
        # 충격 고리 (앞 고리가 빠르고 얇다). 사슬은 고리가 마디마디 끊어진다
        for speed, width, fade in s['rings']:
            rr = g * speed * ease_out(t, 2.0)
            w = width * (1.4 - t)
            ring = np.clip(1 - np.abs(r - rr) / max(w, 0.6), 0, 1) * fade * (1 - t) ** 0.5
            if s['links']:
                ring *= (np.sin(s['links'] * th + t * 3) > -0.35)
            heat = np.maximum(heat, ring)
        # 바깥으로 튀는 빛 가시 (식칼은 길고 가늘게, 건틀릿은 짧고 굵게)
        for ang, length in spikes:
            d0 = g * 0.12 + g * 0.3 * ease_out(t)
            d1 = d0 + g * s['spike_len'] * length * (1 - t)
            ux, uy = math.cos(ang), math.sin(ang)
            along = (f.X - c) * ux + (f.Y - c) * uy
            across = np.abs(-(f.X - c) * uy + (f.Y - c) * ux)
            line = (along >= d0) & (along <= d1)
            width = s['spike_w'] * (1 - t) + 0.5
            heat = np.maximum(heat, np.where(line, np.clip(1 - across / width, 0, 1), 0) * (1 - t) ** 0.4)
        if t < 0.22:                                              # 첫 순간 흰 섬광
            heat = np.maximum(heat, f.blob(c, c, g * 0.22 * (1 - t / 0.22) + 4))
        f.paint(heat, s['ring'], dither=0.2)
        out.append(f.a)
    return out, (g // 2, g // 2)

SHEETS = {
    'hit-fade': lambda: build_hit('hit-fade', DIM, 0, 48, 0),
    'hit-normal': lambda: build_hit('hit-normal', WARM, 4, 64, 4),
    'hit-awake': lambda: build_hit('hit-awake', TEAL, 6, 76, 6, big_ring=True),
    'hit-critical': lambda: build_hit('hit-critical', FIRE, 8, 88, 9, big_ring=True),
    'hit-enhanced': lambda: build_hit('hit-enhanced', VIOLET, 8, 96, 10, big_ring=True),
    'puff': build_puff,
    'dust-land': build_dust,
    'surge': build_surge,
    'haze-blast': lambda: build_blast(HAZE, 190, 5),
    'quake-blast': build_quake,
    'death-burst': build_death,
    'shockwave': build_shockwave,
    'ult-nova-pipe': lambda: build_nova('pipe'),
    'ult-nova-knife': lambda: build_nova('knife'),
    'ult-nova-pistol': lambda: build_nova('pistol'),
    'ult-nova-gauntlet': lambda: build_nova('gauntlet'),
    'ult-nova-chain': lambda: build_nova('chain'),
}
LOOPS = {'shockwave'}


def save(name, frames, pivot):
    h, w = frames[0].shape[:2]
    sheet = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, a in enumerate(frames):
        sheet.paste(Image.fromarray(a, 'RGBA'), (i * w, 0))
    sheet.save(os.path.join(OUT, name + '.png'))
    meta = {'id': 'fx/' + name, 'frames': len(frames), 'frameSize': [w, h], 'columns': len(frames), 'fps': 20,
            'loop': name in LOOPS, 'pivot': list(pivot), 'scale': 2,
            'source': 'tools/make_fx.py (code-drawn, numpy, no image model)'}
    with open(os.path.join(OUT, name + '.json'), 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(meta, indent=1) + '\n')
    print('saved', name, sheet.size, len(frames), 'frames')


def main():
    for name in (sys.argv[1:] or list(SHEETS)):
        frames, pivot = SHEETS[name]()
        save(name, frames, pivot)


if __name__ == '__main__':
    main()
