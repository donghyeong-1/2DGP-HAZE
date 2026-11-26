"""헤이즈 전투 이펙트 v8 (2026-11-24): tools/fxkit.py로 굽는다. code-drawn, 전부 자체 제작 (이미지 모델 없음).

만드는 법·기준은 .claude/skills/haze-fx/SKILL.md. 이펙트마다 함수 하나(create)와 meta 하나.
  python tools/make_fx2.py --look hit-normal haze-blast     # 게임 파일은 그대로 두고 모아 보기만 (shots/fx/<이름>.png)
  python tools/make_fx2.py hit-normal                       # assets/effects·assets/light에 쓴다
  python tools/make_fx2.py                                   # 전부

시트 (assets/effects/<이름>.png + .json, 빛은 assets/light/glow_<이름>.png):
  hit-fade / hit-normal / hit-awake / hit-critical / hit-enhanced / hit-enhanced2 / hit-enhanced3   명중 불꽃
  haze-blast                                                                                       헤이즈 폭발
  cut-mark / cut-mark-big (8각도), impact-rays / impact-rays-big (8방향), shock-ring-s·m·l          색을 게임에서 입히는 두 겹 시트
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fxkit as fx  # noqa: E402
from fxkit import (CHUNK, EMBER, FLAME, MOTE, PUFF, RAMPS, SHARD, SPARK, STREAK, TAU, WHITE, Lights, Particles, Rng, clamp,  # noqa: E402
                   out_cubic, out_expo)

HERO = os.path.join(fx.ROOT, 'assets', 'sprites', 'unified', 'hero6_idle_1.png')


# ----- 명중 불꽃: 흰 십자 섬광(1~2프레임) -> 바깥으로 쏘는 가는 줄기 + 얇은 고리 -> 불티·알갱이가 떨어지며 식는다 -----
def hit_meta(ramp, power, seed):
    size = 88 if power < 1.2 else 112
    return dict(size=[size, size], origin=[size // 2, size // 2], duration=0.42 if power < 1.2 else 0.5, fps=30,
                options=dict(ramp=ramp, power=power, seed=seed))


def hit_create(o):
    R = RAMPS[o['ramp']]
    k = o['power']
    rng = Rng(o['seed'])
    ps = Particles(rng, R)
    lights = Lights()
    lights.add(0, 0, 34 * k, R[2], 95, 0.32)
    lights.add(0, 0, 13 * k, WHITE, 150, 0.14)
    ps.burst(SPARK, 0, 0, int(9 * k), (150, 430 * k), (0.16, 0.36), up=40)
    ps.burst(MOTE, 0, 0, int(8 * k), (60, 260), (0.2, 0.4), size=(0.8, 1.6))
    if k >= 1.2:
        ps.burst(SHARD, 0, 0, int(3 * k), (120, 300), (0.25, 0.42), up=70, size=(0.6, 1.2))
    # 바깥으로 쏘는 줄기: 각도를 고르게 나눈 뒤 조금씩 흔든다 (한쪽으로 몰리지 않게)
    n = int(6 + 2 * k)
    rays = [(TAU * i / n + rng.range(-0.25, 0.25), rng.range(0.7, 1.25), rng.range(0.0, 0.03)) for i in range(n)]
    t = [0.0]

    class Hit:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            u = t[0]
            if u < 0.07:                                         # 주인공 프레임: 흰 십자 섬광 (가로가 길다)
                s = 1.0 if u < 0.034 else 0.6
                for ang, ln, w in ((0, 30, 5), (math.pi, 30, 5), (TAU / 4, 17, 4), (-TAU / 4, 17, 4)):
                    p.needle(0, 0, math.cos(ang) * ln * k * s, math.sin(ang) * ln * k * s, WHITE, w * s + 1)
                for ang in (TAU / 8, 3 * TAU / 8, 5 * TAU / 8, 7 * TAU / 8):
                    p.needle(0, 0, math.cos(ang) * 11 * k * s, math.sin(ang) * 11 * k * s, R[3], 2.5)
                p.disc(0, 0, 5.5 * k * s, WHITE)
            for ang, ln, delay in rays:                            # 줄기: 빠르게 나가서 가늘어지며 끊긴다
                v = u - delay
                if v < 0 or v > 0.2:
                    continue
                head = (8 + 34 * out_expo(v / 0.16) * ln) * k
                tail = (4 + 34 * out_cubic(v / 0.2) * ln) * k
                if head - tail < 1:
                    continue
                c, s_ = math.cos(ang), math.sin(ang)
                p.needle(c * tail, s_ * tail, c * head, s_ * head, R[3] if v > 0.07 else WHITE, 3.4 if v < 0.1 else 1.6,
                         tip=WHITE)
            if 0.03 < u < 0.26:                                    # 얇은 고리: 퍼지며 끊어져 사라진다
                v = (u - 0.03) / 0.23
                r = (7 + 26 * out_expo(v)) * k
                p.ring(0, 0, r, 2.0 if v < 0.3 else 1.0, R[3] if v < 0.5 else R[2], a=1.0 if v < 0.45 else 1.0 - (v - 0.45) / 0.55,
                       gaps=5, phase=o['seed'])
                p.glow_ring(0, 0, r, 4, R[2], 45 * (1 - v))
            ps.draw(p)
            lights.draw(p)
    return Hit()


# ----- 헤이즈 폭발: 흰 번쩍 -> 날카로운 빛 가시 + 고리 -> 연기 덩이가 부풀다 조각나고, 불티·파편·잿불이 남는다 -----
BLAST_META = dict(size=[176, 160], origin=[88, 96], duration=0.8, fps=30, options=dict(ramp='haze', seed=4))


def blast_create(o):
    R = RAMPS[o['ramp']]
    D = RAMPS['dust']
    rng = Rng(o['seed'])
    z = o.get('k', 1.0)                                      # 크기 배율 (궁극기 폭발 1.25, 오버로드 2.4)
    ps = Particles(rng, R, ground=46 * z)
    smoke = Particles(rng, [R[0], R[0], R[1], R[2], R[3]])     # 연기는 색 띠의 어두운 쪽
    lights = Lights()
    lights.add(0, 0, 74 * z, R[2], 110, 0.55)
    lights.add(0, 0, 30 * z, WHITE, 170, 0.2)
    ps.burst(SPARK, 0, 0, int(22 * z), (220 * z, 620 * z), (0.25, 0.6), up=90 * z)
    ps.burst(SHARD, 0, 0, int(7 * z), (160 * z, 420 * z), (0.35, 0.6), up=130 * z, size=(0.8 * z, 1.6 * z))
    ps.burst(MOTE, 0, 0, int(16 * z), (80 * z, 340 * z), (0.3, 0.6), size=(0.8, 1.8))
    ps.burst(EMBER, 0, 0, int(10 * z), (30 * z, 120 * z), (0.5, 0.78), delay=(0.15, 0.3))
    smoke.burst(SHARD, 0, 0, int(9 * z), (90 * z, 260 * z), (0.4, 0.7), up=60 * z, size=(1.4 * z, 2.4 * z), delay=(0.03, 0.08))   # 연기 대신 어두운 큰 조각 (공 모양 연기는 어색했다)
    n = 11
    spikes = [(TAU * i / n + rng.range(-0.2, 0.2), rng.range(0.6, 1.3)) for i in range(n)]
    t = [0.0]

    class Blast:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)
            smoke.update(dt)
            lights.update(dt)

        def draw(self, p):
            u = t[0]
            smoke.draw(p)                                          # 연기는 맨 아래
            if u < 0.1:                                            # 주인공 프레임: 흰 별 모양 덩어리 -> 줄어든다
                s = 1.0 if u < 0.034 else 0.8 if u < 0.067 else 0.45
                for i in range(12):
                    ang = TAU * i / 12 + 0.2
                    ln = (34 if i % 2 == 0 else 22) * s * z
                    p.needle(0, 0, math.cos(ang) * ln, math.sin(ang) * ln, WHITE, 16 * s * z)
                p.disc(0, 0, 15 * s * z, WHITE)
                p.ring(0, 0, 16 * s * z, 1.5, R[3])
            if u < 0.3:                                            # 빛 가시: 안쪽이 굵고 끝이 흰 삼각 줄기
                v = u / 0.3
                for ang, ln in spikes:
                    head = (20 + 52 * out_expo(v * 1.4)) * ln * z
                    tail = (6 + 46 * out_cubic(v) * ln) * z
                    if head - tail < 2:
                        continue
                    c, s_ = math.cos(ang), math.sin(ang)
                    p.needle(c * tail, s_ * tail, c * head, s_ * head, R[3] if v < 0.4 else R[2], (6 * (1 - v) + 1.5) * (0.6 + 0.4 * z), tip=WHITE)
            if 0.04 < u < 0.5:                                     # 충격 고리 둘: 큰 것과 한 박자 늦은 작은 것
                for delay, rmax, w in ((0.04, 66, 3.0), (0.1, 44, 2.0)):
                    v = (u - delay) / 0.36
                    if 0 < v < 1:
                        r = (10 + rmax * out_expo(v)) * z
                        p.ring(0, 0, r, w * (1 - v * 0.6) + 0.5, WHITE if v < 0.25 else R[3], a=1.0 if v < 0.5 else 1.0 - (v - 0.5) / 0.5,
                               gaps=4 if delay < 0.05 else 3, phase=o['seed'] + delay * 30 + v * 1.5)
                        p.glow_ring(0, 0, r, 5, R[2], 50 * (1 - v))
            ps.draw(p)
            lights.draw(p)
    return Blast()


HITS = {'hit-fade': ('fade', 0.75, 11), 'hit-normal': ('haze', 1.0, 3), 'hit-awake': ('awake', 1.12, 5),
        'hit-critical': ('critical', 1.25, 7), 'hit-enhanced': ('violet', 1.4, 9), 'hit-enhanced2': ('gold', 1.45, 13),
        'hit-enhanced3': ('crimson', 1.5, 17)}
EFFECTS = {name: (hit_meta(*args), hit_create) for name, args in HITS.items()}
EFFECTS['haze-blast'] = (BLAST_META, blast_create)


# =====================================================================================================
# 색을 게임에서 입히는 두 겹 시트 (fxkit.export_tint): 베기 자국 / 충격 방사선 / 충격 고리.
# 예전에는 실행 중 사각형(draw_rect_color)을 늘어놓아 그렸다 (블록처럼 보인다는 사용자 지적, 2026-11-24).
# create(o)의 o['layer']: 'tint' = 색 층(회색조), 'core' = 흰 심. 같은 seed로 두 번 굽는다.
# =====================================================================================================
G = fx.GRAY


def cut_meta(big, angle):
    size = 148 if big else 92
    return dict(size=[size, size], origin=[size // 2, size // 2], duration=0.28 if big else 0.2, fps=30,
                options=dict(big=big, angle=angle, seed=21 + int(angle)))


def cut_create(o):
    """베기 자국: 한쪽 끝에서 반대쪽까지 1~2프레임에 그어지고, 가운데가 굵은 방추형이 가늘어지며 끊긴다. 끝에서 불티가 튄다."""
    big, core = o['big'], o['layer'] == 'core'
    a = math.radians(o['angle'])
    dx, dy = math.cos(a), -math.sin(a)                      # 게임 각도(반시계 +) -> 그림 좌표(y 아래)
    nx, ny = -dy, dx
    L = 58 if big else 34                                   # 반 길이
    W = 9.0 if big else 5.5
    dur = 0.28 if big else 0.2
    rng = Rng(o['seed'])
    ps = Particles(rng, G)
    ps.burst(SPARK, dx * L * 0.7, dy * L * 0.7, 7 if big else 4, (160, 420), (0.12, 0.26), spread=0.9, aim=math.atan2(dy, dx))
    ps.burst(MOTE, 0, 0, 6 if big else 3, (40, 200), (0.14, 0.26), spread=1.4, aim=math.atan2(dy, dx))
    lights = Lights()
    lights.add(0, 0, L * 0.9, WHITE, 90, dur * 0.8)
    t = [0.0]

    class Cut:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            u = t[0] + 0.025                                 # 첫 장부터 그어져 있게
            head = -L + 2 * L * out_expo(u / 0.05)           # 긋는 끝
            thin = 1.0 - fx.smooth(0.07, dur, u)
            w = W * thin * (0.42 if core else 1.0)
            fade = 1.0 if u < dur * 0.6 else 1.0 - (u - dur * 0.6) / (dur * 0.4)
            if w >= 0.6:
                mid = (head - L) / 2
                for end in (-L, head):                       # 가운데에서 양 끝으로 가늘어지는 두 가시 = 방추형
                    p.needle(dx * mid, dy * mid, dx * end, dy * end, WHITE if core else G[2], w, a=fade)
            if not core:
                for side in (-1, 1):                         # 옆의 가는 속도선 두 줄 (조금 늦게, 짧게)
                    if 0.03 < u < dur * 0.7:
                        off = (W * 0.9 + 2) * side
                        s0, s1 = -L * 0.55, min(head, L * 0.7)
                        if s1 - s0 > 4:
                            p.line(dx * s0 + nx * off, dy * s0 + ny * off, dx * s1 + nx * off, dy * s1 + ny * off, G[1], a=fade)
                ps.draw(p)
                lights.draw(p)
                p.glow_line(-dx * L * 0.8, -dy * L * 0.8, dx * L * 0.8, dy * L * 0.8, 9 if big else 6, WHITE, 70 * thin)
            elif u < 0.09:                                   # 긋는 끝의 반짝임
                s = 1.0 if u < 0.05 else 0.6
                hx, hy = dx * head, dy * head
                for ang in (0, TAU / 4, TAU / 2, 3 * TAU / 4):
                    p.needle(hx, hy, hx + math.cos(ang) * 7 * s, hy + math.sin(ang) * 7 * s, WHITE, 2.4)
    return Cut()


def rays_meta(big, angle):
    size = 168 if big else 128
    return dict(size=[size, size], origin=[size // 2, size // 2], duration=0.22, fps=30,
                options=dict(big=big, angle=angle, seed=41 + int(angle)))


def rays_create(o):
    """충격 방사선: 맞은 방향 쪽이 길다. 줄기가 빠르게 튀어 나가 가늘어지고, 끝은 흰색."""
    big, core = o['big'], o['layer'] == 'core'
    base = math.radians(o['angle'])
    rng = Rng(o['seed'])
    n = 11 if big else 7
    k = 1.35 if big else 1.0
    rays = []
    for i in range(n):
        ang = base + TAU * i / n + rng.range(-0.22, 0.22)
        near = abs(((ang - base + math.pi) % TAU) - math.pi) < 0.8
        rays.append((ang, (58 if near else 32) * k * rng.range(0.8, 1.2), rng.range(0.0, 0.02), near))
    ps = Particles(rng, G)
    ps.burst(MOTE, 0, 0, 5 if big else 3, (80, 280), (0.12, 0.22), spread=1.6, aim=-base)
    t = [0.0]

    class Rays:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)

        def draw(self, p):
            u = t[0] + 0.03                                  # 첫 장부터 튀어 나와 있게
            for ang, ln, delay, near in rays:
                v = u - delay
                if v < 0:
                    continue
                head = 7 + ln * out_expo(v / 0.1)
                tail = 5 + ln * out_cubic(v / 0.2)
                if head - tail < 1.2:
                    continue
                c, s_ = math.cos(ang), -math.sin(ang)
                w = (5.0 if near else 3.6) * (1 - v / 0.27)
                if core:
                    cut = tail + (head - tail) * 0.6            # 끝 40%만 흰색
                    p.needle(c * cut, s_ * cut, c * head, s_ * head, WHITE, max(1.0, w * 0.7))
                else:
                    p.needle(c * tail, s_ * tail, c * head, s_ * head, G[2], max(1.0, w))
            if not core:
                ps.draw(p)
                p.glow(0, 0, 26 * k, WHITE, 70 * (1 - u / 0.22))
    return Rays()


def ring_meta(radius):
    size = int(radius * 2 + 20) // 2 * 2
    return dict(size=[size, size], origin=[size // 2, size // 2], duration=0.3, fps=30, options=dict(radius=radius, seed=radius))


def ring_create(o):
    """충격 고리: 굵게 시작해 얇아지며 퍼지고, 여러 토막으로 끊어져 사라진다. 한 박자 늦은 안쪽 고리와 가장자리 알갱이."""
    R_, core = o['radius'], o['layer'] == 'core'
    rng = Rng(o['seed'])
    ps = Particles(rng, G)
    for i in range(int(R_ / 5)):
        a = rng.range(0, TAU)
        sp = rng.range(R_ * 1.6, R_ * 3.2)
        ps.spawn(MOTE, math.cos(a) * 6, math.sin(a) * 6, math.cos(a) * sp, math.sin(a) * sp, rng.range(0.14, 0.28))
    t = [0.0]
    dur = 0.3

    class Ring:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)

        def draw(self, p):
            u = t[0]
            for delay, scale, w0, gaps in ((0.0, 1.0, 3.2, 5), (0.05, 0.62, 2.0, 4)):
                v = (u - delay) / (dur - delay)
                if not 0 <= v < 1:
                    continue
                r = 6 + (R_ * scale - 6) * out_expo(v * 1.25)
                w = w0 * (1 - v * 0.7)
                fade = 1.0 if v < 0.5 else 1.0 - (v - 0.5) / 0.5
                if core:
                    if v < 0.28 and delay == 0.0:               # 처음 몇 프레임은 흰 고리
                        p.ring(0, 0, r, max(1.0, w * 0.6), WHITE, gaps=gaps, phase=o['seed'] * 1.3 + v)
                else:
                    p.ring(0, 0, r, w, G[2] if v < 0.6 else G[1], a=fade, gaps=gaps, phase=o['seed'] * 1.3 + v)
                    p.glow_ring(0, 0, r, 5, WHITE, 55 * (1 - v))
            if not core:
                ps.draw(p)
    return Ring()


FLARE_META = dict(size=[208, 208], origin=[104, 104], duration=0.4, fps=30, options=dict(seed=5, k=1.0))
FLARE_S_META = dict(size=[112, 112], origin=[56, 56], duration=0.3, fps=30, options=dict(seed=8, k=0.5))   # 보통 타격용 작은 별


def flare_create(o):
    """별 섬광 (사용자가 준 INARI 그림): 크고 진한 색 빛 원반 한가운데에 흰 여덟 갈래 별, 둘레에 작은 반짝임과 불티.
    색 층 = 별의 색 가장자리·반짝임, 흰 심 = 별 가운데. 큰 빛 원반은 빛 층이 맡는다(게임이 색을 곱한다)."""
    core = o['layer'] == 'core'
    z = o['k']                                               # 크기 (1 = 큰 별, 0.5 = 작은 별)
    rng = Rng(o['seed'])
    ps = Particles(rng, G)
    ps.burst(SPARK, 0, 0, int(16 * z), (260 * z, 760 * z), (0.2, 0.42), up=60 * z)
    ps.burst(MOTE, 0, 0, int(14 * z), (120 * z, 420 * z), (0.22, 0.4), size=(0.8, 1.8))
    twinkles = [(rng.range(-80, 80) * z, rng.range(-70, 70) * z, rng.range(0.02, 0.2), rng.range(3, 7)) for _ in range(int(12 * z))]
    t = [0.0]

    class Flare:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)

        def draw(self, p):
            u = t[0]
            k = 1.0 if u < 0.07 else max(0.0, 1.0 - (u - 0.07) / 0.2)       # 별: 두 장 꽉 찼다가 빠르게 준다
            if k > 0.05:
                for i in range(8):
                    ang = TAU * i / 8
                    ln = (86 if i % 2 == 0 else 46) * (0.55 + 0.45 * k) * (1.15 if i % 4 == 0 else 1.0) * z
                    w = (9 if i % 2 == 0 else 6) * k * (0.5 + 0.5 * z)
                    c, s_ = math.cos(ang), math.sin(ang)
                    if core:
                        p.needle(0, 0, c * ln, s_ * ln, WHITE, max(1.0, w))
                    else:
                        p.needle(0, 0, c * ln * 1.06, s_ * ln * 1.06, G[2], w + 3.5)
                if core:
                    p.disc(0, 0, (9 * k + 1) * (0.4 + 0.6 * z), WHITE)
            for x, y, t0, arm in twinkles:                             # 둘레의 작은 십자 반짝임
                v = (u - t0) / 0.16
                if 0 <= v < 1 and core:
                    a_ = arm * math.sin(math.pi * v)
                    p.line(x - a_, y, x + a_, y, WHITE)
                    p.line(x, y - a_, x, y + a_, WHITE)
            if not core:
                ps.draw(p)
                g = 1.0 if u < 0.1 else max(0.0, 1.0 - (u - 0.1) / 0.3)
                p.glow(0, 0, 100 * z, WHITE, 150 * g)                 # 큰 빛 원반 (진하게: 이 이펙트의 주인공)
                p.glow(0, 0, 58 * z, WHITE, 130 * g)
                p.glow_ring(0, 0, (60 + 30 * out_expo(u / 0.3)) * z, 9 * z, WHITE, 70 * g)
    return Flare()


CUT_ANGLES = [i * 22.5 for i in range(8)]        # 베기 자국은 180도 대칭: 0~157.5도
RAY_ANGLES = [i * 45.0 for i in range(8)]
TINTS = {
    'cut-mark': [(cut_meta(False, a), cut_create) for a in CUT_ANGLES],
    'cut-mark-big': [(cut_meta(True, a), cut_create) for a in CUT_ANGLES],
    'impact-rays': [(rays_meta(False, a), rays_create) for a in RAY_ANGLES],
    'impact-rays-big': [(rays_meta(True, a), rays_create) for a in RAY_ANGLES],
    'shock-ring-s': [(ring_meta(38), ring_create)],
    'shock-ring-m': [(ring_meta(78), ring_create)],
    'shock-ring-l': [(ring_meta(150), ring_create)],
    'flare': [(FLARE_META, flare_create)],
    'flare-s': [(FLARE_S_META, flare_create)],
}


# =====================================================================================================
# 처형 연출용 도장 시트 (2026-11-24, 사용자가 준 INARI 영상을 프레임별로 분석): 시간으로 흐르는 이펙트가 아니라
# 장면마다 골라 쓰는 그림. 프레임 번호 = 장면. weapon.DashExecution이 순서대로 찍는다. 색은 게임이 입힌다.
# 원칙(사용자): 흰 부분보다 **진한 원래 색 면이 훨씬 크다**. 흰색은 가운데 작은 별과 불티뿐.
# =====================================================================================================
def _frame_fx(draw_frame):
    """프레임 번호로 그리는 이펙트: draw_frame(p, i)."""
    t = [0.0]

    class F:
        def update(self, dt):
            t[0] += dt

        def draw(self, p):
            draw_frame(p, int(t[0] * 30 + 0.001))
    return F()


def _star(p, arms, color, w0):
    for ang, ln, w in arms:
        p.needle(0, 0, math.cos(ang) * ln, math.sin(ang) * ln, color, w * w0)


EXEC_CRESCENT_META = dict(size=[216, 128], origin=[108, 64], duration=5 / 30, fps=30, options=dict(seed=3))


def exec_crescent_create(o):
    """적을 감싸는 예고 초승달 (왼쪽이 굵고 오른쪽 끝이 가늘게 올라간다): 왼쪽에서 그어지며 나타나 -> 꽉 찬 모양 두 장 ->
    가늘어지며 알갱이를 흘린다. 바깥 가장자리가 한 단계 밝다. 색은 게임이 장면마다 바꾼다: 회색(예고) -> 흰색 -> 진한 색."""
    core = o['layer'] == 'core'
    rng = Rng(o['seed'])
    motes = [(rng.range(-95, 60), rng.range(10, 46), rng.range(-40, 40), rng.range(20, 70)) for _ in range(16)]

    def draw(p, i):
        if core:
            return
        s = (1.0, 1.0, 1.0, 0.62, 0.3)[min(i, 4)]
        reach = -20 if i == 0 else 200                       # 첫 장은 왼쪽 절반만 (그어지는 중)

        def fn(X, Y):
            d = (X / 100.0) ** 2 + ((Y - 6) / 44.0) ** 2
            inner = ((X - 22 * s) / 96.0) ** 2 + ((Y + 12 * s - 6) / 40.0) ** 2 <= 1.0
            keep = (d <= 1.0) & ~inner & (Y > -14 - 20 * (X < 0)) & (X < reach)
            return fx.np.where(keep, fx.np.where(d > 0.86, 3, 2), -1)     # 바깥 가장자리가 밝다
        p.shade(-104, -60, 104, 60, fn, G)
        p.glow(-40, 18, 80, WHITE, 100 if i < 3 else 45)
        p.glow(30, 30, 50, WHITE, 60 if 0 < i < 3 else 0)
        if i >= 3:                                           # 가늘어지며 흘리는 알갱이
            k = i - 2
            for x, y, vx, vy in motes[:8 * k]:
                p.px(x + vx * 0.03 * k, y + vy * 0.03 * k, G[3])
                if k == 1:
                    p.px(x + vx * 0.03 + 1, y + vy * 0.03, G[2])
    return _frame_fx(draw)


TINTS['exec-crescent'] = [(EXEC_CRESCENT_META, exec_crescent_create)]


# =====================================================================================================
# 큰 마무리 폭발 fin-burst (2026-11-24, haze-fx 절차로 다시): 처형·궁극기 마무리의 첫 일격부터 끝까지 한 장의 흐르는 이펙트.
# 한 줄: 긴 색 가시와 작은 흰 별 -> 작은 원반 -> (검은 띠 동안 알갱이만) -> 큰 색 네 갈래 별 -> 크고 진한 원반이 부풀고
#        가운데 작은 흰 별, 흰 불티가 꼬리를 끌며 흩어진다 -> 원반이 가운데부터 비워져 고리가 되고 끊어지며 사라진다, 조각이 떨어진다.
# 원칙(사용자): 흰 부분보다 진한 원래 색 면이 훨씬 크다. 빛줄기·검은 띠·실루엣은 화면 전체라 게임(weapon.FinisherCut)이 그린다.
# =====================================================================================================
WHITES = [(150, 150, 150), (200, 200, 200), (235, 235, 235), WHITE, WHITE]      # 흰 심 층의 불티 색 띠
FIN_META = dict(size=[272, 272], origin=[136, 136], duration=0.54, fps=30, options=dict(seed=6))


def fin_create(o):
    core = o['layer'] == 'core'
    rng = Rng(o['seed'])
    pw = Particles(rng, WHITES, sparks=WHITES)              # 흰 불티 (흰 심 층)
    pc = Particles(rng, G)                                  # 색 조각·알갱이 (색 층, 게임이 색을 곱한다)
    lights = Lights()
    q = TAU / 4
    S1, S2 = 0.0, 0.10                                      # 첫 일격, 둘째 일격
    pw.burst(SPARK, 0, 0, 10, (260, 620), (0.12, 0.26))
    pc.burst(MOTE, 0, 0, 8, (120, 380), (0.14, 0.3), size=(0.8, 1.8))
    lights.add(0, 0, 80, WHITE, 150, 0.12)
    star8 = [(TAU * i / 8 + (0.0 if i % 2 == 0 else rng.range(-0.08, 0.08)), 33 if i % 2 == 0 else 17, 1.0 if i % 2 == 0 else 0.62)
             for i in range(8)]
    arcs = [(TAU * i / 7 + rng.range(-0.15, 0.15), rng.range(0.5, 0.82), rng.range(0.6, 1.6), rng.range(0.0, 0.07))
            for i in range(7)]                               # 고리 토막: 고르게 나눈 뒤 흔든다 (각도, 길이, 속도, 늦게 사라짐)
    twinkles = [(rng.range(-100, 100), rng.range(-90, 90), rng.range(0.16, 0.4), rng.range(2, 5)) for _ in range(10)]
    t = [0.0]
    fired = [False]

    class Fin:
        def update(self, dt):
            t[0] += dt
            if not fired[0] and t[0] >= S2:                 # 둘째 일격: 흰 불티가 크게 흩어지고 색 조각이 날아간다
                fired[0] = True
                pw.burst(SPARK, 0, 0, 22, (380, 1050), (0.2, 0.42), up=40)
                pc.burst(SHARD, 0, 0, 12, (240, 620), (0.3, 0.44), up=120, size=(1.5, 3.0))
                pc.burst(MOTE, 0, 0, 18, (160, 520), (0.22, 0.42), size=(0.8, 1.8))
                pc.burst(EMBER, 0, 0, 10, (40, 160), (0.3, 0.42), delay=(0.1, 0.2))
                lights.add(0, 0, 124, WHITE, 165, 0.3)
                lights.add(0, 0, 60, WHITE, 120, 0.16)
            pw.update(dt)
            pc.update(dt)
            lights.update(dt)

        def draw(self, p):
            u = t[0]
            i = int(u * 30 + 0.01)                           # 장면은 프레임 단위로 끊는다 (30fps)
            if i == 0:                                       # 첫 일격: 위아래로 긴 색 가시 + 작은 흰 별
                if core:
                    for a, ln, w in star8:
                        p.needle(0, 0, math.cos(a) * ln * 0.7, math.sin(a) * ln * 0.7, WHITE, 5.0 * w)
                    p.disc(0, 0, 4.5, WHITE)
                else:
                    for a, ln, w in ((q, 104, 13), (-q, 104, 13), (0, 36, 9), (2 * q, 36, 9)):
                        p.needle(0, 0, math.cos(a) * ln, math.sin(a) * ln, G[3], w)
            elif i == 1:                                     # 작은 진한 원반
                if not core:
                    p.disc(0, 0, 21, G[3])
                    p.ring(0, 0, 21, 2.5, G[1])
                    p.ring(0, 0, 27, 1.5, G[3], gaps=5, phase=1.0)
                    p.glow(0, 0, 46, WHITE, 110)
            elif i == 3:                                     # 둘째 일격: 큰 색 네 갈래 별 (면이 크다) + 흰 십자
                if core:
                    for j in range(4):
                        p.needle(0, 0, math.cos(q * j) * 46, math.sin(q * j) * 46, WHITE, 4.5)
                    p.disc(0, 0, 6, WHITE)
                else:
                    for a, ln, w in ((q, 112, 30), (-q, 112, 30), (0, 92, 27), (2 * q, 92, 27)):
                        p.needle(0, 0, math.cos(a) * ln, math.sin(a) * ln, G[3], w)
                    for j in range(4):
                        a = q / 2 + q * j
                        p.needle(0, 0, math.cos(a) * 42, math.sin(a) * 42, G[2], 14)
            elif i >= 4:                                     # 원반 -> 고리
                v = u - 4 / 30
                r = 40 + 9 * out_expo(v / 0.07)
                hole = 0.0 if v < 0.07 else (r - 5) * out_cubic((v - 0.07) / 0.06)         # 가운데부터 비워진다 (원반은 세 장 유지)
                late = max(0.0, v - 0.135)                                               # 고리가 된 뒤
                r += 8 * out_cubic(late / 0.27)
                if not core:
                    wide = (r - hole) * (1.0 if late == 0 else max(0.12, 1.0 - late / 0.2))
                    fade = 1.0 if late < 0.1 else max(0.0, 1.0 - (late - 0.1) / 0.17)
                    if hole < 1:
                        p.disc(0, 0, r, G[2])                                            # 진한 색 면 (이 이펙트의 주인공)
                        p.ring(0, 0, r - 1.5, 4.0, G[3])                                  # 밝은 테두리
                        p.ring(0, 0, r + 4, 1.5, G[3], gaps=6, phase=u * 5)
                        p.ring(0, 0, r * 0.66, 1.5, G[1], gaps=5, phase=u * 9)
                        p.ring(0, 0, r * 0.4, 1.5, G[1], gaps=3, phase=-u * 7)
                    elif late < 0.04 and wide >= 1:                                       # 막 비워진 굵은 고리 (온전하다)
                        p.ring(0, 0, r - wide / 2, wide, G[3])
                    else:                                                                # 토막 나서 저마다 퍼지며 가늘어진다
                        for a0, span, speed, stay in arcs:
                            life = 0.2 + stay
                            if late >= life:
                                continue
                            kk = late / life
                            rr = r + 16 * speed * out_cubic(kk)
                            ww = max(1.0, 7.0 * (1 - kk) ** 1.5)
                            p.ring(0, 0, rr, ww, G[3] if kk < 0.35 else G[2], a=1.0 if kk < 0.7 else 1.0 - (kk - 0.7) / 0.3,
                                   a0=a0, a1=a0 + span * (1 - kk * 0.5))
                    p.glow(0, 0, r * 2.2, WHITE, 130 * max(0.0, 1.0 - v / 0.3))
                    p.glow_ring(0, 0, r, 12, WHITE, 90 * max(0.0, 1.0 - v / 0.36))
                else:
                    k = max(0.0, 1.0 - v / 0.17)                                         # 가운데 작은 흰 별: 줄어든다
                    if k > 0.08:
                        for a, ln, w in star8:
                            p.needle(0, 0, math.cos(a) * ln * (0.2 + 0.8 * k), math.sin(a) * ln * (0.2 + 0.8 * k), WHITE,
                                     max(1.5, 8.0 * w * k))
                        p.disc(0, 0, 1.5 + 5 * k, WHITE)
            if core:
                pw.draw(p)
                for x, y, t0, arm in twinkles:                                           # 둘레의 작은 십자 반짝임
                    v = (u - t0) / 0.12
                    if 0 <= v < 1:
                        a_ = arm * math.sin(math.pi * v)
                        p.line(x - a_, y, x + a_, y, WHITE)
                        p.line(x, y - a_, x, y + a_, WHITE)
            else:
                pc.draw(p)
                lights.draw(p)
    return Fin()


TINTS['fin-burst'] = [(FIN_META, fin_create)]


LOOK_COLOR = [236, 30, 52]          # 모아 보기에서 색 층에 입혀 볼 색 (게임에서는 공격마다 다르다)


# =====================================================================================================
# haze-inari 스킬의 본보기 (2026-11-24): INARI 영상에서 읽어 낸 기법을 fxkit으로 옮긴 것.
# 보류: 사용자가 결과를 보고 쓰지 않기로 했다. 아래 둘(glint, inari-smear)은 보기 전용 시안이고 게임 파일로 굽지 않는다.
# =====================================================================================================
# ----- 반짝임 glint: 칼이 맞부딪치거나 강하게 스친 자리의 가는 빛. 색은 게임이 입힌다 -----
# 한 줄: 가로로 길고 세로는 짧은 네 갈래 별(가운데가 굵고 끝이 바늘처럼 가늘다)이 한 장 번쩍 -> 가운데가 비며 빛줄기가 양옆으로
#        밀려나 토막 나고 -> 별빛 두세 개만 남는다. (게임 화면에서 처음 본 판은 굵기가 고른 '+' 조준선으로 보여 다시 만들었다:
#        세로를 가로의 1/3로, 양팔 길이를 다르게, 막대 대신 끝이 뾰족한 삼각형으로)
GLINT_META = dict(size=[128, 64], origin=[64, 32], duration=0.2, fps=30, options=dict(seed=9))


def _star4(p, left, right, up, down, c, color):
    """가로·세로 팔 길이가 제각각인 네 갈래 별: 팔마다 가운데(폭 2c)에서 끝점으로 좁아지는 삼각형."""
    if right > 1:
        p.poly([(0, -c), (right, 0), (0, c)], color)
    if left > 1:
        p.poly([(0, -c), (-left, 0), (0, c)], color)
    if down > 1:
        p.poly([(-c, 0), (0, down), (c, 0)], color)
    if up > 1:
        p.poly([(-c, 0), (0, -up), (c, 0)], color)


def _sliver(p, x0, x1, w, color):
    """양 끝이 가늘어지는 가로 토막 (가운데가 가장 굵다)."""
    mid = (x0 + x1) / 2
    p.needle(mid, 0, x0, 0, color, w)
    p.needle(mid, 0, x1, 0, color, w)


def glint_create(o):
    core = o['layer'] == 'core'
    rng = Rng(o['seed'])
    ps = Particles(rng, WHITES)
    left, right, up, down = 58, 44, 17, 11                     # 팔 길이를 다르게 (같으면 조준선처럼 보인다)
    for x, y, d in ((-30, -8, 0.06), (30, 7, 0.09)):           # 빛줄기 곁의 별빛 둘
        ps.spawn(fx.TWINKLE, x, y, 0, 0, rng.range(0.1, 0.13), rng.range(1.0, 1.3), d)
    t = [0.0]

    class Glint:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)

        def draw(self, p):
            u = t[0]
            if u < 0.06:                                         # 꽉 찬 네 갈래 별 한 장 -> 가늘어진 별 한 장
                k = 1.0 if u < 0.03 else 0.55
                if core:
                    _star4(p, left * (0.9 + 0.1 * k), right * (0.9 + 0.1 * k), up * k, down * k, 2.6 * k + 0.2, WHITE)
                else:
                    _star4(p, left + 4, right + 4, (up + 3) * k, (down + 3) * k, 4.6 * k + 0.4, G[3])
                    p.glow(0, 0, 30, WHITE, 150 * k)
                    p.glow_line(-left * 0.7, 0, right * 0.7, 0, 8, WHITE, 70 * k)
            else:                                                # 가운데가 비며 빛줄기가 양옆으로 밀려나 짧아진다
                v = (u - 0.06) / 0.065
                if v < 1:
                    for side, reach, far in ((1, right, 0.62), (-1, left, 0.5)):
                        x0 = side * (6 + reach * far * out_expo(v))        # 안쪽 끝이 빠르게 바깥으로 달아난다
                        x1 = side * (reach + 3 * v)
                        if abs(x1 - x0) < 4:
                            continue
                        cut = x0 + (x1 - x0) * (0.3 if side > 0 else 0.42)  # 한 군데가 끊어져 긴 토막과 짧은 토막이 된다
                        if core:
                            _sliver(p, x0, cut - side * 2, 1.6 - 0.8 * v, WHITE)
                            _sliver(p, cut + side * 2, x1, 1.6 - 0.8 * v, WHITE)
                        else:
                            _sliver(p, x0 - side * 2, x1 + side * 3, 3.4 - 1.6 * v, G[3])
                            p.glow_line(x0, 0, x1, 0, 6, WHITE, 50 * (1 - v))
            if core:
                ps.draw(p)
    return Glint()


TINTS['glint'] = [(GLINT_META, glint_create)]

# ----- 붓질 초승달 시안 inari-smear (보기 전용: 게임 파일로 굽지 않는다) -----
# 한 줄: 회색 예고 한 장 -> 흰 초승달 한 장 -> 진한 색 면 두 장(바깥 가장자리가 밝고, 꼬리가 붓끝처럼 갈라진다) -> 뒤쪽이 가로 줄로
#        찢기며 가늘어짐 -> 가는 흰 호와 별빛만 남는다. (INARI 평타: 색 면은 2~3프레임뿐, 끝이 갈라지고 찢긴다)
SMEAR_META = dict(size=[190, 190], origin=[95, 95], duration=0.3, fps=30, options=dict(ramp='critical', seed=12))


def smear_create(o):
    R = RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    ps = Particles(rng, R, sparks=WHITES)
    lights = Lights()
    for _ in range(9):                                          # 지나온 쪽(왼쪽)에 남는 별빛
        ps.spawn(fx.TWINKLE, rng.range(-80, -10), rng.range(-30, 40), rng.range(-30, 10), rng.range(-10, 10), rng.range(0.12, 0.22),
                 rng.range(0.5, 1.2), rng.range(0.03, 0.14))
    CX, CY, RO = -6.0, -6.0, 62.0                               # 바깥 원
    tail = (CX + (RO - 9) * math.cos(1.0), CY + (RO - 9) * math.sin(1.0))    # 아래쪽 굵은 자리 (꼬리가 여기서 갈라져 나간다)
    t = [0.0]
    fired = [False]

    def crescent(p, s, mode='color'):
        """s: 두께 1 -> 0. 바깥 원에서 왼쪽(조금 위)으로 밀린 같은 크기의 안쪽 원을 뺀 모양: 위아래 끝은 저절로 가늘어지고
        오른쪽(조금 아래)이 가장 굵다. 잘라 낸 직선 가장자리가 생기지 않게 다른 조건으로 자르지 않는다."""
        def fn(X, Y):
            d = fx.np.hypot(X - CX, Y - CY) / RO
            inner = fx.np.hypot(X - CX + 24 * s, Y - CY + 7 * s) <= RO - 1
            keep = (d <= 1.0) & ~inner
            if mode == 'grey':
                return fx.np.where(keep & (d > 0.92) & (X > 14), 2, -1)     # 예고: 오른쪽 바깥 테두리만
            if mode == 'white':
                return fx.np.where(keep, 4, -1)
            return fx.np.where(keep, fx.np.where(d > 0.94, 3, 2), -1)       # 진한 색 면, 바깥 테두리만 한 단계 밝게
        p.shade(-70, -72, 70, 70, fn, RAMPS['dust'] if mode == 'grey' else R)

    def arc_glow(p, k):
        for a in (-1.2, -0.7, -0.2, 0.3, 0.8):                  # 호를 따라 번지는 빛 (예전 초승달처럼 빛나게)
            p.glow(CX + (RO - 10) * math.cos(a), CY + (RO - 10) * math.sin(a), 46, R[2], 130 * k)
            p.glow(CX + (RO - 8) * math.cos(a), CY + (RO - 8) * math.sin(a), 22, R[3], 110 * k)

    class Smear:
        def update(self, dt):
            t[0] += dt
            if not fired[0] and t[0] >= 0.03:
                fired[0] = True
                ps.burst(SPARK, tail[0] + 22, tail[1] + 22, 7, (180, 460), (0.12, 0.26), spread=1.0, aim=0.8)
                ps.burst(MOTE, 20, 10, 8, (40, 180), (0.14, 0.26), spread=2.0, aim=0.3)
                lights.add(30, 0, 70, R[2], 130, 0.22)
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            i = int(t[0] * 30 + 0.01)
            if i == 0:
                crescent(p, 1.0, 'grey')
            elif i == 1:
                crescent(p, 1.0, 'white')
                p.fork(tail[0], tail[1], 0.8, 40, 12, WHITE, n=3, spread=0.34, seed=o['seed'])
                arc_glow(p, 1.3)
            elif i in (2, 3, 4):
                s = (1.0, 0.9, 0.5)[i - 2]
                crescent(p, s)
                p.fork(tail[0], tail[1], 0.8, 40 * (1.0 if i < 4 else 0.75), 12 * s, R[2], n=3, spread=0.34, seed=o['seed'], tip=WHITE)
                # 찢김은 휘두르기가 시작된 위쪽 끝에만 (안쪽 가장자리 전체를 찢으면 빗처럼 보인다)
                p.streak_edges(-40, -72, 30, -46, -1, (6, 12, 20)[i - 2], seed=o['seed'] + i, band=1 if i < 4 else 2, trail=0.7)
                arc_glow(p, (1.0, 0.8, 0.45)[i - 2])
            elif i == 5:                                            # 가는 흰 호만 남는다
                def fn(X, Y):
                    d = fx.np.hypot(X - CX, Y - CY)
                    return fx.np.where((fx.np.abs(d - RO + 1) <= 1.0) & (X > 22) & (Y < 34), 4, -1)
                p.shade(-70, -72, 70, 70, fn, R)
                arc_glow(p, 0.2)
            ps.draw(p)
            lights.draw(p)
    return Smear()


LOOK_ONLY = {'inari-smear': (SMEAR_META, smear_create)}      # --look으로만 굽는 시안
# haze-inari 시안은 게임에 쓰지 않는다 (2026-11-24 사용자: 'INARI와 퀄리티 차이가 너무 난다. 스킬은 두되 쓰지 말자').
# 두 겹 시트 시안도 이름을 주고 --look일 때만 모아 보기를 만든다.
LOOK_ONLY_TINTS = {'glint'}


def build_tint(name, look):
    variants = TINTS[name]
    tint = [fx.render(meta, create, layer='tint') for meta, create in variants]
    core = [fx.render(meta, create, layer='core') for meta, create in variants]
    meta = variants[0][0]
    show = []                                              # 모아 보기: 색 층에 청록을 입히고 흰 심을 얹어서
    for r in (0, len(variants) // 3, (2 * len(variants)) // 3) if len(variants) > 1 else (0,):
        for (tc, tl), (cc, _) in zip(tint[r], core[r]):
            arr = fx.np.asarray(tc, fx.np.float32)
            arr[..., :3] *= fx.np.array(LOOK_COLOR, fx.np.float32) / 255.0
            body = fx.Image.fromarray(arr.astype(fx.np.uint8), 'RGBA')
            body.paste(cc, (0, 0), cc)
            la = fx.np.asarray(tl, fx.np.float32)
            la[..., :3] *= fx.np.array(LOOK_COLOR, fx.np.float32) / 255.0
            show.append((body, fx.Image.fromarray(la.astype(fx.np.uint8), 'RGBA')))
    path = fx.contact(show, os.path.join(fx.ROOT, 'shots', 'fx', name + '.png'), actor=HERO, origin=meta['origin'],
                      cols=len(tint[0]) if len(variants) > 1 else 4, zoom=2 if len(variants) == 1 else 3, label=f"{name}  {meta['size'][0]}x{meta['size'][1]}  {len(tint[0])}f  variants {len(variants)}")
    if look:
        print('본다', path)
        return
    info = fx.export_tint(name, meta, tint, core)
    print('구움', name, info['frames'], '프레임')


# =====================================================================================================
# 휘두르기 초승달 v8 (2026-11-24, haze-fx 절차): 대시 베기와 같은 구성.
# 한 줄: 흰 초승달이 두 장 만에 휘둘러지고 -> 진한 구간 색 면(바깥 테두리가 밝다)이 되어 -> 꼬리가 따라잡으며 가늘어지고,
#        끝에서 불티가 튀고 호를 따라 알갱이가 떨어진다. 안쪽에 한 박자 늦은 가는 호.
# 5방향(동·북동·북·남동·남)을 미리 굽는다(왼쪽은 좌우 반전). 시트 크기·기준점은 예전과 같다 (게임의 위치·판정 그대로).
# =====================================================================================================
SLASH_AIMS = [0, 45, 90, -45, -90]          # 게임 각도(반시계 +). 그림에서는 y가 아래라 부호를 뒤집는다
SLASH_DUR = 0.3


def slash_meta(grid, **opt):
    return dict(size=[grid, grid], origin=[grid // 2, grid // 2], duration=SLASH_DUR, fps=30, options=opt)


def _arc_shader(R_, W, a0, a1, head, tail, rot, sy, white, hot=3, body=2, edge=1):
    """초승달 한 겹: 각도 a0->a1 구간 중 tail~head(0~1)만. 가운데가 굵고 양 끝이 가늘다. 바깥 22%는 밝은 테두리.
    rot = 조준 방향(그림 좌표), sy < 1이면 납작한 타원(가로 베기)."""
    c, s_ = math.cos(rot), math.sin(rot)
    span = a1 - a0

    def fn(X, Y):
        lx = X * c + Y * s_
        ly = (-X * s_ + Y * c) / sy
        r = fx.np.hypot(lx, ly)
        th = fx.np.arctan2(ly, lx)
        u = (th - a0) / span
        u = fx.np.where(u < -0.3, u + TAU / abs(span), u)             # 한 바퀴 넘는 회전 베기
        v = (u - tail) / max(1e-4, head - tail)
        ok = (v >= 0) & (v <= 1)
        w = W * fx.np.sin(math.pi * fx.np.clip(v, 0, 1) ** 1.25) ** 0.65
        q = (R_ - r) / fx.np.maximum(w, 0.3)
        ok &= (w >= 0.6) & (q >= 0) & (q <= 1)
        idx = fx.np.where(q < 0.24, hot, fx.np.where(q > 0.86, edge, body))
        if white:
            idx = fx.np.full(X.shape, 4)
        return fx.np.where(ok, idx, -1)
    return fn


def slash_create(o):
    R = RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    rot = -math.radians(o['aim'])
    # [(반지름, 두께, a0도, a1도, 늦게, 뒤집기)]. 각도는 게임 기준(반시계 +, 위가 +)으로 적고 여기서 그림 좌표(y 아래)로 뒤집는다
    layers = [(r, w, -a0, -a1, d, rev) for (r, w, a0, a1, d, rev) in o['layers']]
    sy = o.get('flat', 1.0)
    ps = Particles(rng, R)
    lights = Lights()
    t = [0.0]
    landed = [False]
    main = layers[0]

    def tip(layer, k):
        r_, w, a0, a1, delay, rev = layer
        a = math.radians(a1 if not rev else a0)
        a = math.radians(a0) + (math.radians(a1) - math.radians(a0)) * (k if not rev else 1 - k)
        lx, ly = math.cos(a) * (r_ - w * 0.3), math.sin(a) * (r_ - w * 0.3) * sy
        return lx * math.cos(rot) - ly * math.sin(rot), lx * math.sin(rot) + ly * math.cos(rot)

    class Slash:
        def update(self, dt):
            t[0] += dt
            if not landed[0] and t[0] >= 0.06:                       # 다 휘두른 순간: 끝에서 불티, 호에서 알갱이
                landed[0] = True
                x, y = tip(main, 1.0)
                x2, y2 = tip(main, 0.93)
                aim = math.atan2(y - y2, x - x2)
                n = o.get('sparks', 6)
                ps.burst(SPARK, x, y, n, (160, 420), (0.12, 0.28), spread=0.9, aim=aim)
                for _ in range(n + 4):
                    k = rng.range(0.25, 1.0)
                    mx, my = tip(main, k)
                    d = math.hypot(mx, my) or 1.0
                    sp = rng.range(30, 110)
                    ps.spawn(MOTE, mx, my, mx / d * sp, my / d * sp, rng.range(0.14, 0.26), rng.range(0.8, 1.6))
                lights.add(x, y, 26, R[3], 110, 0.14)
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            u = t[0] + 0.03                                  # 첫 장부터 휘둘러져 있게
            g = o['grid'] / 2
            for li, (r_, w, a0, a1, delay, rev) in enumerate(layers):
                v = u - delay
                if v < 0:
                    continue
                head = out_expo(v / 0.055)
                tail = fx.smooth(0.085, 0.25 - delay * 0.5, v)
                if tail >= head - 0.01:
                    continue
                b0, b1 = (math.radians(a0), math.radians(a1)) if not rev else (math.radians(a1), math.radians(a0))
                white = v < 0.04 and li == 0                            # 주인공 프레임: 흰 초승달
                thin = 1.0 - 0.45 * fx.smooth(0.1, 0.27, v)
                p.shade(-g, -g, g, g, _arc_shader(r_, w * thin, b0, b1, head, tail, rot, sy, white,
                                                  hot=3, body=2 if li == 0 else 3, edge=1), R)
                if li == 0:
                    for k in (0.3, 0.55, 0.8):                         # 호를 따라 빛
                        if tail <= k <= head:
                            x, y = tip(layers[0], k)
                            p.glow(x, y, 16 + w * 0.5, R[2], 70 * (1 - v / 0.28))
            if u < 0.1:                                               # 끝의 반짝임
                x, y = tip(main, min(1.0, out_expo(u / 0.055)))
                s = 1.0 if u < 0.065 else 0.55
                for ang in (0, TAU / 4, TAU / 2, 3 * TAU / 4):
                    p.needle(x, y, x + math.cos(ang) * 9 * s, y + math.sin(ang) * 9 * s, WHITE, 2.6)
            ps.draw(p)
            lights.draw(p)
    return Slash()


def _L(r, w, a0=-95, a1=95, delay=0.0, rev=False):
    return (r, w, a0, a1, delay, rev)


def _flat(layers):
    """가로 베기: 몸 뒤에서 앞 아래를 지나 앞으로 도는 납작한 타원 호 (예전 make_slash_hq._flat과 같은 각도)."""
    return [(r * 1.25, w * 2.3, -185 + (a0 + 95) * 0.5, 10 + (a1 - 95) * 0.5, d, True) for (r, w, a0, a1, d, rev) in layers]


_N = [_L(60, 30), _L(44, 6, -52, 48, 0.03)]
_F = [_L(50, 15, -40, 40)]
_A = [_L(68, 32), _L(48, 9, -55, 50, 0.03), _L(34, 4, -48, 44, 0.05)]
_C = [_L(80, 34), _L(62, 12, -58, 54, 0.025), _L(46, 6, -50, 46, 0.045), _L(90, 4, -40, 60, 0.015)]
_G = [_L(73, 34), _L(55, 8, -52, 50, 0.03)]
_E = [_L(95, 30), _L(87, 22, rev=True, delay=0.03), _L(70, 6, -52, 50, 0.05)]
SLASHES = {
    'pipe-slash': dict(grid=190, ramp='haze', layers=_N, sparks=6, seed=31),
    'pipe-slash-fade': dict(grid=170, ramp='fade', layers=_F, sparks=2, seed=32),
    'pipe-slash-awake': dict(grid=220, ramp='awake', layers=_A, sparks=8, seed=33),
    'pipe-slash-critical': dict(grid=250, ramp='critical', layers=_C, sparks=12, seed=34),
    'pipe-slash-finisher': dict(grid=220, ramp='gold', layers=_G, sparks=9, seed=35),
    'pipe-slash-finisher-rise': dict(grid=220, ramp='gold', layers=[(r, w, a0, a1, d, True) for (r, w, a0, a1, d, _) in _G], sparks=9, seed=36),
    'pipe-slash-enhanced': dict(grid=280, ramp='violet', layers=_E, sparks=12, seed=37),
    'pipe-slash-enhanced2': dict(grid=280, ramp='gold', layers=_E, sparks=12, seed=38),
    'pipe-slash-enhanced3': dict(grid=280, ramp='crimson', layers=_E, sparks=12, seed=39),
    'pipe-slash-flat': dict(grid=236, ramp='haze', layers=_flat(_N), flat=0.42, sparks=6, seed=41),
    'pipe-slash-fade-flat': dict(grid=212, ramp='fade', layers=_flat(_F), flat=0.42, sparks=2, seed=42),
    'pipe-slash-awake-flat': dict(grid=274, ramp='awake', layers=_flat(_A), flat=0.42, sparks=8, seed=43),
    'pipe-slash-critical-flat': dict(grid=312, ramp='critical', layers=_flat(_C), flat=0.42, sparks=12, seed=44),
}
_SPIN = [_L(62, 26, -200, 160), _L(46, 10, 340, -20, 0.03)]
_SPIN_E = [_L(88, 36, -200, 160), _L(66, 16, 340, -20, 0.03), _L(100, 5, -200, 160, 0.015)]
SPINS = {
    'air-spin': dict(grid=210, ramp='haze', layers=_SPIN, sparks=8, seed=51),
    'air-spin-enhanced': dict(grid=290, ramp='violet', layers=_SPIN_E, sparks=12, seed=52),
    'air-spin-enhanced2': dict(grid=290, ramp='gold', layers=_SPIN_E, sparks=12, seed=53),
    'air-spin-enhanced3': dict(grid=290, ramp='crimson', layers=_SPIN_E, sparks=12, seed=54),
}


def build_slash(name, look):
    cfg = SLASHES.get(name) or SPINS[name]
    aims = SLASH_AIMS if name in SLASHES else [0]
    meta = dict(size=[cfg['grid']] * 2, origin=[cfg['grid'] // 2] * 2, duration=SLASH_DUR, fps=30, options=dict(cfg))
    variants = [fx.render(meta, slash_create, aim=a) for a in aims]
    show = variants[0] + (variants[1] + variants[4] if len(variants) > 1 else [])
    path = fx.contact(show, os.path.join(fx.ROOT, 'shots', 'fx', name + '.png'), actor=HERO, origin=meta['origin'],
                      cols=len(variants[0]), zoom=2, label=f"{name}  {cfg['grid']}  {len(variants[0])}f  variants {len(variants)}")
    if look:
        print('본다', path)
        return
    info = fx.export(name, meta, variants)
    print('구움', name, info['frames'], '프레임')


# =====================================================================================================
# 나머지 시트 v8 (2026-11-24, haze-fx 절차): 먼지·연기·솟는 기운·바닥 충격·소멸·궁극기 폭발·오버로드 폭발.
# 이름·크기·기준점은 예전(tools/make_fx.py)과 같다 (게임의 위치 그대로).
# =====================================================================================================
def _simple(setup, draw_fn):
    """setup(ps, lights, rng) 뒤에 draw_fn(p, u)를 그리는 이펙트 틀."""
    def create(o):
        R = RAMPS[o['ramp']]
        rng = Rng(o['seed'])
        ps = Particles(rng, R, ground=o.get('ground'))
        lights = Lights()
        extra = setup(ps, lights, rng, R, o) or {}
        t = [0.0]

        class F:
            def update(self, dt):
                t[0] += dt
                ps.update(dt)
                lights.update(dt)

            def draw(self, p):
                draw_fn(p, t[0] + 0.02, R, o, extra)
                ps.draw(p)
                lights.draw(p)
        return F()
    return create


# 착지·출발 먼지: 발밑에서 양옆으로 낮게 깔리는 덩이와 튀는 알갱이
def _dust_setup(ps, lights, rng, R, o):
    for side in (-1, 1):
        for _ in range(3):
            ps.spawn(PUFF, side * rng.range(2, 8), -3, side * rng.range(70, 190), -rng.range(5, 40), rng.range(0.16, 0.26), rng.range(0.55, 0.95))
        ps.burst(MOTE, side * 6, -3, 4, (60, 200), (0.1, 0.2), spread=0.7, aim=0 if side > 0 else math.pi, up=30)


def _dust_draw(p, u, R, o, x):
    if u < 0.1:
        w = 10 + 30 * out_expo(u / 0.08)
        p.line(-w, -1, w, -1, R[4])


# 연기 한 줌: 끊어진 고리가 퍼지고 작은 덩이가 흩어진다
def _puff_setup(ps, lights, rng, R, o):
    ps.burst(PUFF, 0, 0, 6, (40, 150), (0.2, 0.32), size=(0.6, 1.1), up=20)
    ps.burst(MOTE, 0, 0, 8, (60, 220), (0.14, 0.28))
    lights.add(0, 0, 26, R[3], 70, 0.2)


def _puff_draw(p, u, R, o, x):
    if u < 0.06:
        p.disc(0, 0, 7, R[4])
    v = u / 0.26
    if v < 1:
        p.ring(0, 0, 6 + 22 * out_expo(v), 2.0 * (1 - v) + 0.6, R[3], a=1.0 if v < 0.5 else 2 - 2 * v, gaps=5, phase=o['seed'])


# 솟는 기운: 발밑의 누운 고리에서 가는 빛줄기들이 올라가고 잿불이 뜬다
def _surge_setup(ps, lights, rng, R, o):
    ps.burst(EMBER, 0, -4, 10, (20, 90), (0.25, 0.34), spread=math.pi, aim=-math.pi / 2)
    lights.add(0, -10, 34, R[2], 100, 0.3)
    return dict(beams=[(rng.range(-20, 20), rng.range(0.6, 1.2), rng.range(0, 0.08)) for _ in range(8)])


def _surge_draw(p, u, R, o, x):
    v = u / 0.3
    if v < 1:
        p.ring(0, -2, 6 + 20 * out_expo(v), 2.2 * (1 - v) + 0.6, R[3], sy=0.3, a=1.0 if v < 0.6 else 1 - (v - 0.6) / 0.4)
    for bx, k, d in x['beams']:
        w = u - d
        if 0 < w < 0.24:
            top = -6 - 62 * k * out_expo(w / 0.14)
            bot = -4 - 62 * k * out_cubic(w / 0.24)
            if bot - top > 2:
                p.needle(bx, bot, bx, top, R[3] if w > 0.08 else WHITE, 2.4, tip=WHITE)


# 증기 분출 (v8 5-5 공장 장치): 바닥 틈에서 흰 줄기 다발이 솟구치고 -> 줄기가 끊어지며 위로 빠지고 -> 김 덩이가 옆으로 퍼지며 사라진다
# ----- 공장 증기 분출구 (devices.Vent) -----
# 한 줄: 틈에서 흰 김 덩이가 촘촘한 기둥으로 솟구치고(첫 두 장은 흰 심), 위로 갈수록 느려지며 옆으로 부풀어 회색으로 식고,
#        바닥에는 김이 양옆으로 깔리고 위에서 물방울이 흩어진다. 게임은 분출 동안 0.2초마다 이 시트를 겹쳐 띄워 끊기지 않는 기둥을 만든다.
STEAM_META = dict(size=[100, 172], origin=[50, 166], duration=0.46, fps=30, options=dict(ramp='dust', seed=66),
                  variant_seeds=[66, 71, 79])           # 세 줄: 분출구가 차례로 돌려 써서 기둥이 0.2초마다 똑같이 되풀이되지 않는다
# 김이 식어 가는 색: 흰색 -> 옅은 청회색 -> 공장 그늘색 (FLAME은 앞이 뜨겁고 뒤가 식은 색, 테두리는 두 칸 뒤 색)
STEAM_HEAT = [WHITE, (242, 247, 251), (226, 235, 242), (208, 220, 230), (186, 200, 214), (162, 178, 194), (138, 154, 172),
              (112, 128, 148), (88, 102, 122)]
STEAM_HOT = [WHITE] * 4 + STEAM_HEAT[1:6]                    # 처음 솟는 흰 심 (금방 식지 않는다)


# 보스의 헤이즈 증기 (projectile.SteamVent): 같은 기둥을 청록으로. 흰 심 -> 옅은 청록 -> 짙은 청록
HAZE_STEAM = [WHITE, (226, 255, 250), (190, 252, 243), (150, 244, 232), (110, 232, 220), (70, 206, 198), (40, 170, 170),
              (22, 128, 138), (12, 92, 108)]


def steam_create(o):
    haze = o.get('tone') == 'haze'
    STEAM_HEAT = HAZE_STEAM if haze else globals()['STEAM_HEAT']
    STEAM_HOT = [WHITE] * 4 + STEAM_HEAT[1:6]
    glow_color = (120, 240, 228) if haze else (196, 222, 236)
    rng = Rng(o['seed'])
    ps = Particles(rng, RAMPS[o['ramp']])
    ps.cool_pow = 1.8                                           # 오래 희게 (금방 회색이 되면 연기처럼 보인다): 희게 있다가 줄어들며 사라진다
    for k in range(14):                                         # 흰 심: 한 줄로 촘촘히 쏜다 (뒤로 갈수록 작고 빠르다)
        sp = 380 + 42 * k + rng.range(-25, 25)
        ps.spawn(FLAME, rng.range(-1.5, 1.5), -4, rng.range(-12, 12), -sp, rng.range(0.16, 0.26), max(3.0, 8.5 - 0.4 * k),
                 0.004 * k, ramp=STEAM_HOT)
    for i in range(52):                                         # 몸통: 0.22초 동안 쉬지 않고 뿜는다 (다음 시트와 이어진다). 위로 갈수록 퍼진다
        d = i / 52 * 0.22 + rng.range(0, 0.01)
        sp = rng.range(420, 760)
        ps.spawn(FLAME, rng.range(-3, 3), -4, rng.range(-80, 80), -sp, rng.range(0.24, 0.4), rng.range(3.5, 7.0), d, ramp=STEAM_HEAT)
    for i in range(16):                                         # 위의 뭉게: 기둥이 닿을 즈음 그 높이에서 느리게 부풀며 옆으로 번진다
        y = -rng.range(70, 140)
        ps.spawn(FLAME, rng.range(-12, 12) * (-y / 100), y, rng.range(-60, 60), -rng.range(40, 140), rng.range(0.22, 0.34),
                 rng.range(6.0, 10.5), 0.03 + (-y) / 900 + rng.range(0, 0.12), ramp=STEAM_HEAT[1:])
    for side in (-1, 1):                                        # 바닥에 깔리는 김: 작은 덩이 여럿이 짧게 번진다
        for _ in range(9):
            ps.spawn(FLAME, side * rng.range(2, 10), -3, side * rng.range(40, 130), -rng.range(5, 30), rng.range(0.18, 0.3),
                     rng.range(2.0, 4.0), rng.range(0.0, 0.2), ramp=STEAM_HEAT[1:])
    for _ in range(12):                                         # 가장자리에서 떨어져 나가는 작은 김 가닥
        y = -rng.range(30, 120)
        side = rng.pick((-1, 1))
        ps.spawn(FLAME, side * rng.range(6, 14), y, side * rng.range(90, 200), -rng.range(30, 160), rng.range(0.18, 0.3),
                 rng.range(1.5, 2.8), 0.02 + (-y) / 1000 + rng.range(0, 0.15), ramp=STEAM_HEAT[2:])
    ps.burst(MOTE, 0, -90, 16, (80, 260), (0.25, 0.42), spread=2.6, aim=-math.pi / 2, delay=(0.1, 0.24))   # 물방울
    lights = Lights()
    later = [(0.0, 0, -16, 26, 90, 0.3), (0.08, 0, -56, 32, 70, 0.34), (0.16, 0, -100, 32, 55, 0.3)]   # 빛도 김을 따라 오른다 (앞서지 않게)
    t = [0.0]

    class Steam:
        def update(self, dt):
            t[0] += dt
            while later and later[0][0] <= t[0]:
                _d, x, y, r, k, life = later.pop(0)
                lights.add(x, y, r, glow_color, k, life)
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            ps.draw(p)
            lights.draw(p)
    return Steam()


def _steam_setup(ps, lights, rng, R, o):
    light = [R[2], R[3], R[4], R[4], WHITE]             # 김은 밝게 (어두운 공처럼 보이지 않게)
    for i in range(12):                                 # 작은 김 덩이 여럿: 줄기를 따라 위로 빠르게, 위에서 옆으로 퍼진다
        ps.spawn(PUFF, rng.range(-4, 4), -8, rng.range(-46, 46), -rng.range(300, 620), rng.range(0.2, 0.36), rng.range(0.28, 0.5),
                 delay=i * 0.022, ramp=light)
    ps.burst(MOTE, 0, -6, 14, (200, 560), (0.16, 0.34), spread=0.45, aim=-math.pi / 2)
    lights.add(0, -30, 30, R[3], 80, 0.32)
    lights.add(0, -80, 24, R[3], 50, 0.36)
    return dict(beams=[((i - 3) * 2.6 + rng.range(-1, 1), rng.range(0.7, 1.2), rng.range(0, 0.1)) for i in range(7)])


def _steam_draw(p, u, R, o, x):
    if u < 0.07:                                        # 주인공 프레임: 틈에서 솟는 굵은 흰 줄기
        p.needle(0, -2, 0, -46, WHITE, 7.0, tip=WHITE)
        p.needle(-5, -2, -7, -26, WHITE, 3.0, tip=WHITE)
        p.needle(5, -2, 7, -26, WHITE, 3.0, tip=WHITE)
    for bx, k, d in x['beams']:
        w = u - d
        if 0 < w < 0.3:
            top = -8 - 118 * k * out_expo(w / 0.16)
            bot = -4 - 118 * k * out_cubic(max(0.0, (w - 0.1) / 0.2))      # 처음 0.1초는 바닥에 붙어 있다 (분출구에서 이어지게)
            if bot - top > 2:
                p.needle(bx * (1 + w * 2.5), bot, bx * (1 + w * 4), top, R[4] if w > 0.1 else WHITE, 3.0 if w < 0.12 else 2.0, tip=WHITE)
    v = u / 0.22
    if v < 1:                                           # 바닥에 누운 끊어진 고리
        p.ring(0, -2, 5 + 15 * out_expo(v), 1.8 * (1 - v) + 0.6, R[4], sy=0.3, a=1.0 if v < 0.5 else 2 - 2 * v, gaps=4, phase=o['seed'])


# 바닥 충격: 땅에서 위로 터지는 반원 가시 + 바닥에 누운 고리 + 튀는 돌 조각
def _quake_setup(ps, lights, rng, R, o):
    ps.burst(SPARK, 0, -4, 16, (200, 560), (0.2, 0.42), spread=2.4, aim=-math.pi / 2)
    ps.burst(SHARD, 0, -4, 9, (180, 430), (0.3, 0.42), spread=2.2, aim=-math.pi / 2, size=(1.0, 2.2))
    for side in (-1, 1):
        for _ in range(4):
            ps.spawn(PUFF, side * rng.range(6, 20), -4, side * rng.range(120, 300), -rng.range(10, 50), rng.range(0.24, 0.4), rng.range(0.8, 1.4), ramp=RAMPS['dust'])
    lights.add(0, -10, 80, R[2], 120, 0.3)
    n = 9
    return dict(spikes=[(-math.pi + math.pi * (i + 0.5) / n + rng.range(-0.1, 0.1), rng.range(0.6, 1.25)) for i in range(n)])


def _quake_draw(p, u, R, o, x):
    if u < 0.07:
        p.disc(0, -6, 18 if u < 0.045 else 11, WHITE)
    v = u / 0.26
    if v < 1:
        for ang, ln in x['spikes']:
            head = (18 + 62 * out_expo(v * 1.4)) * ln
            tail = 6 + 56 * out_cubic(v) * ln
            if head - tail > 2:
                c, s_ = math.cos(ang), math.sin(ang)
                p.needle(c * tail, -4 + s_ * tail, c * head, -4 + s_ * head, R[3] if v < 0.4 else R[2], 6 * (1 - v) + 1.5, tip=WHITE)
    v = u / 0.36
    if v < 1:
        p.ring(0, -3, 12 + 88 * out_expo(v), 3 * (1 - v) + 0.8, WHITE if v < 0.2 else R[3], sy=0.2, a=1.0 if v < 0.5 else 2 - 2 * v, gaps=6)


# 소멸: 작은 흰 별 -> 헤이즈 조각이 사방으로 흩어지고 잿불이 떠오른다
def _death_setup(ps, lights, rng, R, o):
    ps.burst(SHARD, 0, 0, 12, (120, 360), (0.3, 0.44), up=60, size=(1.0, 2.2))
    ps.burst(SPARK, 0, 0, 10, (160, 420), (0.16, 0.34))
    ps.burst(EMBER, 0, 0, 10, (20, 110), (0.3, 0.44), delay=(0.05, 0.16))
    lights.add(0, 0, 44, R[2], 120, 0.3)


def _death_draw(p, u, R, o, x):
    if u < 0.09:
        s = 1.0 if u < 0.055 else 0.6
        for i in range(8):
            a = TAU * i / 8
            p.needle(0, 0, math.cos(a) * (26 if i % 2 == 0 else 13) * s, math.sin(a) * (26 if i % 2 == 0 else 13) * s, WHITE, 4.5 * s)
        p.disc(0, 0, 5 * s, WHITE)
    v = (u - 0.03) / 0.3
    if 0 < v < 1:
        p.ring(0, 0, 8 + 38 * out_expo(v), 2.4 * (1 - v) + 0.6, R[3] if v < 0.5 else R[2], a=1.0 if v < 0.5 else 2 - 2 * v, gaps=5, phase=o['seed'] + v)


MISC = {
    'dust-land': (dict(size=[96, 36], origin=[48, 34], duration=0.28, fps=30, glow=False, options=dict(ramp='dust', seed=61)), _simple(_dust_setup, _dust_draw)),
    'puff': (dict(size=[72, 72], origin=[36, 41], duration=0.34, fps=30, glow=False, options=dict(ramp='dust', seed=62)), _simple(_puff_setup, _puff_draw)),
    'surge': (dict(size=[64, 88], origin=[32, 80], duration=0.36, fps=30, options=dict(ramp='haze', seed=63)), _simple(_surge_setup, _surge_draw)),
    # v8 7일 차(2026-11-25): 가는 흰 줄만 보여 '가늘다'는 지적 -> 김 덩이로 만든 굵은 기둥 (steam_create, 예전 판은 _steam_setup·_steam_draw)
    'steam-jet': (STEAM_META, steam_create),
    'quake-blast': (dict(size=[220, 120], origin=[110, 116], duration=0.46, fps=30, options=dict(ramp='ember', seed=64, ground=0)),
                    _simple(_quake_setup, _quake_draw)),
    'death-burst': (dict(size=[110, 110], origin=[55, 55], duration=0.46, fps=30, options=dict(ramp='haze', seed=65)),
                    _simple(_death_setup, _death_draw)),
}
EFFECTS.update(MISC)
EFFECTS['steam-jet-haze'] = (dict(STEAM_META, options=dict(ramp='haze', seed=67, tone='haze'), variant_seeds=[67, 73]), steam_create)
# 궁극기 광역 폭발: 헤이즈 폭발(blast_create)을 무기 색·크기로 (오버로드 폭발은 아래 over_create)
for _wid, _ramp, _seed in (('pipe', 'awake', 71), ('knife', 'fade', 72), ('pistol', 'mint', 73), ('gauntlet', 'ember', 74), ('chain', 'violet', 75)):
    EFFECTS['ult-nova-' + _wid] = (dict(size=[230, 230], origin=[115, 115], duration=0.66, fps=30, options=dict(ramp=_ramp, seed=_seed, k=1.25)),
                                   blast_create)


# ----- 오버로드 폭발 v3 (2026-11-24 사용자: "뾰족뾰족·동그라미 같은 단순한 도형 느낌을 지워라"): 도형을 그리지 않고 입자로만 만든다 -----
# 한 줄: 흰 불덩이 무더기가 팡 터지고 -> 식어 가는 붉은 불덩이들이 사방으로 밀려나며 몸통을 이루고 -> 작은 불덩이 띠가 고리처럼
#        화면 밖까지 번지고 -> 불덩이 줄기가 혀처럼 뻗고, 불티·픽셀 조각·잿불이 남는다.
OVER_META = dict(size=[460, 460], origin=[230, 230], duration=0.8, fps=30, options=dict(ramp='critical', seed=81))
WHITE_HEAT = [WHITE] * 5 + [(255, 236, 236), (255, 200, 200), (255, 150, 150), (236, 58, 72)]     # 처음 터지는 흰 덩어리


def over_create(o):
    R = RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    ps = Particles(rng, R)
    lights = Lights()
    ps.cool_pow = 1.0                                           # 오래 뜨겁게 (금방 검붉어지면 탁하다)
    lights.add(0, 0, 225, R[2], 160, 0.6)
    lights.add(0, 0, 150, R[3], 150, 0.4)
    lights.add(0, 0, 130, WHITE, 200, 0.24)
    for _ in range(14):                                         # 팡: 가운데 흰 불덩이 무더기 (금방 식는다)
        ps.spawn(FLAME, rng.range(-30, 30), rng.range(-30, 30), rng.range(-260, 260), rng.range(-260, 260), rng.range(0.12, 0.22),
                 rng.range(70, 115), ramp=WHITE_HEAT)
    for _ in range(46):                                         # 몸통: 식어 가는 불덩이들이 밀려난다 (크기·속도·수명 제각각)
        a = rng.range(0, TAU)
        sp = rng.range(160, 1150)
        ps.spawn(FLAME, math.cos(a) * 10, math.sin(a) * 10, math.cos(a) * sp, math.sin(a) * sp, rng.range(0.22, 0.5),
                 rng.range(18, 52), rng.range(0.0, 0.05))
    for i in range(150):                                        # 충격 띠: 작은 불덩이가 비슷한 속도로 퍼져 들쭉날쭉한 띠가 된다 (구슬처럼 고르면 안 된다)
        a = rng.range(0, TAU)
        sp = rng.range(1450, 2050)
        ps.spawn(FLAME, math.cos(a) * 24, math.sin(a) * 24, math.cos(a) * sp, math.sin(a) * sp, rng.range(0.2, 0.42),
                 rng.range(4, 17), rng.range(0.02, 0.05))
    for j in range(11):                                         # 혀: 한 방향으로 불덩이를 줄지어 쏜다 (뒤로 갈수록 작고 빠르다)
        a = TAU * j / 11 + rng.range(-0.2, 0.2)
        reach = rng.range(0.7, 1.3)
        for k in range(16):                                     # 촘촘히 겹쳐서 한 줄기로 (구슬처럼 떨어지면 안 된다)
            sp = (620 + 105 * k + rng.range(-40, 40)) * reach
            b = a + rng.range(-0.05, 0.05)
            ps.spawn(FLAME, 0, 0, math.cos(b) * sp, math.sin(b) * sp, rng.range(0.24, 0.42), max(3.0, 30 - 1.7 * k) * reach, 0.004 * k)
    ps.burst(SPARK, 0, 0, 50, (600, 1700), (0.3, 0.6), up=60, size=(1.4, 2.4))
    ps.burst(CHUNK, 0, 0, 40, (300, 1100), (0.4, 0.75), up=160, size=(2.0, 3.0))
    ps.burst(EMBER, 0, 0, 26, (80, 320), (0.45, 0.75), delay=(0.15, 0.35))
    t = [0.0]

    class Over:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            ps.draw(p)
            lights.draw(p)                                    # 빛은 번지는 둥근 빛뿐 (또렷한 원 모양 고리는 그리지 않는다)
    return Over()


EFFECTS['overload-burst'] = (OVER_META, over_create)

# ----- 오버로드 직전: 기운이 주인공에게 빨려든다 -----
# 한 줄: 사방에서 줄기와 픽셀 조각이 점점 빨라지며 한 점으로 모이고, 가운데 빛이 커지다가 마지막 장에 흰 점으로 오므라든다.
GATHER_META = dict(size=[460, 460], origin=[230, 230], duration=0.3, fps=30, options=dict(ramp='critical', seed=83))


def gather_create(o):
    R = RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    ps = Particles(rng, R)
    for _ in range(120):
        a = rng.range(0, TAU)
        d = rng.range(90, 228)
        delay = rng.range(0.0, 0.12)
        life = 0.3 - delay - rng.range(0.0, 0.03)
        v0 = d / max(0.05, life) * 0.36                         # 느리게 출발해 빨라져서 (STREAK) 수명 끝에 가운데에 닿는다
        ps.spawn(STREAK if rng.chance(0.7) else MOTE, math.cos(a) * d, math.sin(a) * d, -math.cos(a) * v0, -math.sin(a) * v0,
                 life, rng.range(1.2, 3.2), delay)
    t = [0.0]

    class Gather:
        def update(self, dt):
            t[0] += dt
            for q in ps.items:                                  # 알갱이(MOTE)도 가운데로 끌려간다
                if q['k'] == MOTE and q['age'] > 0:
                    d = math.hypot(q['x'], q['y']) or 1.0
                    q['vx'] -= q['x'] / d * 2600 * dt
                    q['vy'] -= q['y'] / d * 2600 * dt
            ps.update(dt)

        def draw(self, p):
            u = t[0]
            ps.draw(p)
            k = u / 0.3
            p.glow(0, 0, 40 + 150 * k, R[2], 70 + 110 * k)      # 가운데 빛이 커진다
            p.glow(0, 0, 16 + 30 * k, WHITE, 150 * k)
            if k > 0.55:                                        # 오므라드는 흰 심 (불규칙한 작은 불덩이 몇 개)
                for i in range(4):
                    a = i * 1.7 + u * 20
                    r = 7 * (k - 0.5) * 2
                    p.disc(math.cos(a) * 3, math.sin(a) * 3, r * (0.6 + 0.2 * (i % 2)), WHITE)
    return Gather()


EFFECTS['overload-gather'] = (GATHER_META, gather_create)


# =====================================================================================================
# 입자 폭발 pb_create (2026-11-24 사용자: '이제 haze-fx로 모두 개편'): 타격 불꽃·헤이즈 폭발·궁극기 폭발·소멸·바닥 충격을
# 선·고리·가시 도형에서 **불규칙한 입자 무더기**로. 사용자가 받아들인 오버로드 폭발(over_create)과 같은 구성을 크기 r로 줄여 쓴다.
# 한 줄: 흰 불덩이 무더기가 한두 장 번쩍 -> 식어 가는 불덩이들이 밀려나며 몸통이 되고, 작은 불덩이의 들쭉날쭉한 띠가 퍼지고,
#        몇 줄기 혀가 뻗고 -> 불티·조각·잿불이 남아 흩어진다.
# 옵션: r 반지름(논리 px), tl 수명 배율, white·body·band·tongues(개수), tongue_n(혀 하나의 불덩이 수), sparks·chunks·embers,
#       half=True면 위쪽 반원(바닥에서 솟는다), dust=양옆으로 깔리는 먼지 덩이 수
# 이전 판(hit_create·blast_create·_quake·_death)은 되돌릴 때를 위해 남겨 둔다.
# =====================================================================================================
def pb_create(o):
    layer = o.get('layer')                                      # None = 색 시트 / 'tint'·'core' = 게임이 색을 입히는 두 겹 시트
    R = G if layer else RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    ps = Particles(rng, R, ground=o.get('ground'))
    pc = Particles(Rng(o['seed'] + 9), WHITES)                  # 흰 심 층 (두 겹 시트의 'core'): 흰 불덩이와 불티 몇 개
    lights = Lights()
    ps.cool_pow = o.get('cool', 1.0)
    r = float(o['r'])
    k = r / 230.0
    tl = o.get('tl', 1.0)
    half = o.get('half', False)
    cone = o.get('cone')                                        # (방향 rad(그림 좌표), 벌어짐, 그쪽으로 가는 비율): 맞은 방향으로 쏠린다
    hot = [WHITE] * 5 + [R[3], R[3], R[2], R[2]]                 # 처음 터지는 흰 덩어리가 식는 색

    def ang():
        if cone and rng.chance(cone[2]):
            return cone[0] + rng.range(-cone[1] / 2, cone[1] / 2)
        return rng.range(-math.pi + 0.15, -0.15) if half else rng.range(0, TAU)

    gk = o.get('glow', 1.0)                                    # 빛의 세기 배율 (타격처럼 다른 빛과 겹치는 것은 낮춘다)
    lights.add(0, 0, r * 0.98, R[2], 150 * gk, 0.6 * tl)
    lights.add(0, 0, r * 0.65, R[3], 140 * gk, 0.4 * tl)
    lights.add(0, 0, r * 0.56, WHITE, o.get('flash', 190), 0.24 * tl)
    ws = o.get('ws', 1.0)
    for _ in range(o.get('white', 12)):                         # 팡: 가운데 흰 불덩이 무더기 (금방 식는다)
        x, y = rng.range(-30, 30) * k, rng.range(-30, 30 if not half else 0) * k
        vx, vy = rng.range(-260, 260) * k, rng.range(-260, 260 if not half else 0) * k
        life, size = rng.range(0.1, 0.18) * max(0.75, tl), rng.range(70, 115) * k * ws
        ps.spawn(FLAME, x, y, vx, vy, life, size, ramp=hot)
        pc.spawn(FLAME, x, y, vx, vy, life * 0.8, size * 0.8, ramp=[WHITE] * 4)
    for _ in range(o.get('body', 40)):                          # 몸통: 식어 가는 불덩이들이 밀려난다
        a_ = ang()
        sp = rng.range(160, 1150) * k
        ps.spawn(FLAME, math.cos(a_) * 10 * k, math.sin(a_) * 10 * k, math.cos(a_) * sp, math.sin(a_) * sp, rng.range(0.22, 0.5) * tl,
                 max(2.0, rng.range(18, 52) * k), rng.range(0.0, 0.05))
    for _ in range(o.get('band', 130)):                         # 띠: 작은 불덩이가 비슷한 속도로 퍼진다 (각도는 무작위)
        a_ = ang()
        sp = rng.range(1450, 2050) * k
        ps.spawn(FLAME, math.cos(a_) * 24 * k, math.sin(a_) * 24 * k, math.cos(a_) * sp, math.sin(a_) * sp, rng.range(0.2, 0.42) * tl,
                 max(1.0, rng.range(4, 17) * k), rng.range(0.02, 0.05))
    nt, tn = o.get('tongues', 9), o.get('tongue_n', 14)
    for j in range(nt):                                         # 혀: 한 방향으로 불덩이를 줄지어 쏜다
        if cone:
            a_ = cone[0] + cone[1] * ((j + 0.5) / nt - 0.5) + rng.range(-0.1, 0.1)
        else:
            a_ = (-math.pi + math.pi * (j + 0.5) / nt if half else TAU * j / nt) + rng.range(-0.22, 0.22)
        reach = rng.range(0.7, 1.3)
        for m in range(tn):
            sp = (620 + 105 * m * 16 / tn + rng.range(-40, 40)) * reach * k * o.get('tongue_k', 1.0)
            b_ = a_ + rng.range(-0.05, 0.05)
            size = max(1.2, (30 - 1.7 * m * 16 / tn) * reach * k)
            ps.spawn(FLAME, 0, 0, math.cos(b_) * sp, math.sin(b_) * sp, rng.range(0.24, 0.42) * tl, size, 0.004 * m)
            if m >= tn - 3:                                     # 혀끝은 흰 심으로도 (두 겹 시트)
                pc.spawn(FLAME, 0, 0, math.cos(b_) * sp, math.sin(b_) * sp, 0.16 * tl, size, 0.004 * m, ramp=[WHITE] * 4)
    sk = o.get('spark_k', k)
    aim, spread = (-math.pi / 2, math.pi * 0.9) if half else (cone[0], cone[1] * 1.5) if cone else (0.0, TAU)
    n_sp = o.get('sparks', 30)
    ps.burst(SPARK, 0, 0, n_sp, (600 * sk, 1700 * sk), (0.3 * tl, 0.6 * tl), spread=spread, aim=aim, up=60 * sk,
             size=o.get('spark_size', (1.0, 1.8)))
    pc.burst(SPARK, 0, 0, n_sp // 3, (600 * sk, 1700 * sk), (0.2 * tl, 0.4 * tl), spread=spread, aim=aim, up=60 * sk,
             size=o.get('spark_size', (1.0, 1.8)))
    ps.burst(CHUNK, 0, 0, o.get('chunks', 20), (300 * sk, 1100 * sk), (0.4 * tl, 0.75 * tl), spread=spread, aim=aim, up=160 * sk,
             size=o.get('chunk_size', (1.2, 2.2)))
    ps.burst(EMBER, 0, 0, o.get('embers', 14), (80 * sk, 320 * sk), (0.45 * tl, 0.75 * tl), spread=spread, aim=aim, delay=(0.12 * tl, 0.3 * tl))
    for side in (-1, 1):                                        # 바닥을 따라 깔리는 먼지 (바닥 충격)
        for _ in range(o.get('dust', 0)):
            ps.spawn(PUFF, side * rng.range(6, 20), -3, side * rng.range(120, 300), -rng.range(10, 50), rng.range(0.24, 0.4),
                     rng.range(0.8, 1.4), ramp=RAMPS['dust'])
    t = [0.0]

    class Burst:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)
            pc.update(dt)
            lights.update(dt)

        def draw(self, p):
            if layer == 'core':
                pc.draw(p)
                return
            ps.draw(p)
            lights.draw(p)
    return Burst()


# 충격 고리 (두 겹 시트): 또렷한 원 대신 작은 불덩이들이 비슷한 속도로 퍼져 만드는 들쭉날쭉한 띠. 반지름은 그대로(범위를 알려 주는 고리다).
def pring_create(o):
    R_, core = float(o['radius']), o['layer'] == 'core'
    rng = Rng(o['seed'])
    ps = Particles(rng, G)
    pc = Particles(Rng(o['seed'] + 9), WHITES)
    lights = Lights()
    ps.cool_pow = 1.1
    lights.add(0, 0, R_ * 0.95, WHITE, 70, 0.26)
    for i in range(int(R_ * 1.5) + 24):
        a_ = rng.range(0, TAU)
        life = rng.range(0.2, 0.3)
        sp = R_ * 0.72 * 5.0 / (1 - math.exp(-5.0 * life)) * rng.range(0.92, 1.05)      # 0.28R에서 출발해 R 언저리에 닿는다
        size = max(1.2, R_ * rng.range(0.02, 0.05))
        x, y = math.cos(a_) * R_ * 0.28, math.sin(a_) * R_ * 0.28
        delay = rng.range(0.0, 0.03)
        ps.spawn(FLAME, x, y, math.cos(a_) * sp, math.sin(a_) * sp, life, size, delay)
        if i % 4 == 0:                                          # 흰 심도 같은 박자로 (먼저 나오면 첫 장에 흰 점선 원이 보인다)
            pc.spawn(FLAME, x, y, math.cos(a_) * sp, math.sin(a_) * sp, life * 0.5, size * 0.8, delay, ramp=[WHITE] * 4)
    ps.burst(CHUNK, 0, 0, int(R_ / 7) + 3, (R_ * 3.2, R_ * 5.2), (0.18, 0.3), size=(1.0, 1.6))

    class Ring:
        def update(self, dt):
            ps.update(dt)
            pc.update(dt)
            lights.update(dt)

        def draw(self, p):
            if core:
                pc.draw(p)
                return
            ps.draw(p)
            lights.draw(p)
    return Ring()


def _prays(meta):
    """충격 방사선 시트의 크기·각도는 그대로 두고, 가시 대신 맞은 방향으로 쏠린 입자 분출로."""
    o = meta['options']
    big = o['big']
    meta = dict(meta, options=dict(seed=o['seed'] + 200, r=(64 if big else 48), tl=0.5, cone=(-math.radians(o['angle']), 1.5, 0.8),
                                   white=0, body=0, band=10 if big else 6, tongues=3 if big else 2, tongue_n=6, tongue_k=1.5, flash=0, glow=0.15,
                                   sparks=14 if big else 10, chunks=6 if big else 4, embers=0, spark_k=0.42 if big else 0.32,
                                   spark_size=(1.0, 1.8), chunk_size=(1.0, 1.6)))
    return (meta, pb_create)


PB_TINTS_LATE = dict()                                         # PB_TINTS는 아래에서 만들어진다: 여기서는 따로 모아 두었다가 합친다
PB_TINTS_LATE['impact-rays'] = [_prays(rays_meta(False, a)) for a in RAY_ANGLES]
PB_TINTS_LATE['impact-rays-big'] = [_prays(rays_meta(True, a)) for a in RAY_ANGLES]
for _nm, _rad in (('shock-ring-s', 38), ('shock-ring-m', 78), ('shock-ring-l', 150)):
    PB_TINTS_LATE[_nm + '-pb'] = [(dict(ring_meta(_rad), options=dict(radius=_rad, seed=_rad + 300)), pring_create)]


# 충격 고리 v3 (2026-11-24 사용자: '입자는 너무 별로', '원에 불투명도가 있고 겹친 느낌'): 색 층에는 튀는 알갱이 몇 개뿐이고,
# 고리는 빛 층의 **반투명한 띠**가 빠르게 퍼지며 옅어진다. 안쪽에는 더 옅은 반투명 면이 잠깐 깔린다(충격이 지나간 자리).
# 입자 띠(pring_create)는 처음에 한 점에 뭉쳐 흰 덩어리로 보이고, 퍼지면 구슬 꿴 것처럼 보여서 쓰지 않는다.
def soft_ring_create(o):
    R_, core = float(o['radius']), o['layer'] == 'core'
    rng = Rng(o['seed'])
    ps = Particles(rng, G)
    ps.burst(MOTE, 0, 0, int(R_ / 12) + 3, (R_ * 3.0, R_ * 5.0), (0.14, 0.26), size=(0.8, 1.4))
    t = [0.0]

    class Ring:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)

        def draw(self, p):
            if core:
                return
            u = t[0]
            v = min(1.0, u / 0.28)
            r = R_ * (0.32 + 0.68 * out_expo(v * 1.25))             # 빠르게 펴지고 느려진다
            fade = (1.0 - v) ** 1.4
            w = max(3.0, R_ * 0.11) * (1.0 - 0.45 * v)
            p.light_disc(0, 0, r, WHITE, 34 * fade * fade, edge=2.0)   # 안쪽의 옅은 반투명 면
            p.glow_ring(0, 0, r - w * 0.4, w, WHITE, 150 * fade)       # 반투명한 띠
            p.glow_ring(0, 0, r, max(1.6, w * 0.3), WHITE, 90 * fade)  # 띠의 바깥 가장자리가 조금 더 밝다
            ps.draw(p)
    return Ring()


for _nm, _rad in (('shock-ring-s', 38), ('shock-ring-m', 78), ('shock-ring-l', 150)):
    PB_TINTS_LATE[_nm] = [(dict(ring_meta(_rad), options=dict(radius=_rad, seed=_rad + 300)), soft_ring_create)]


def _pb(size, origin, duration, **opt):
    return (dict(size=list(size), origin=list(origin), duration=duration, fps=30, options=opt), pb_create)


# ----- 보류 (2026-11-24 사용자: '입자는 너무 별로', '일단은 우리 원래 이펙트를 쓰자') -----
# 아래 입자 구성은 게임에 쓰지 않는다. 원래 레시피(hit_create·blast_create·MISC·rays_create·ring_create)가 그대로 등록되어 있고,
# 이 판은 `python tools/make_fx2.py --pb --look <이름>`으로 모아 보기만 만들 수 있다.
PB_EFFECTS, PB_TINTS = {}, PB_TINTS_LATE
for _name, (_ramp, _power, _seed) in HITS.items():              # 타격 불꽃 7종: 작고 빠르게
    _size = 88 if _power < 1.2 else 112
    PB_EFFECTS[_name] = _pb((_size, _size), (_size // 2, _size // 2), 0.42 if _power < 1.2 else 0.5, ramp=_ramp, seed=_seed + 100,
                         r=34 * _power, tl=0.62, white=0, body=int(2 * _power), band=int(12 * _power), tongues=3, tongue_n=6,
                         tongue_k=1.35, sparks=int(15 * _power), chunks=int(8 * _power), embers=3, spark_k=0.3 * _power,
                         spark_size=(1.0, 1.9), chunk_size=(1.0, 1.8), flash=30, glow=0.3)   # 타격은 튀는 불티·조각이 주인공. 흰 번쩍임은 별 섬광이 맡는다 (겹치면 별이 묻힌다)
PB_EFFECTS['haze-blast'] = _pb((176, 160), (88, 96), 0.8, ramp='haze', seed=104, r=74, white=9, body=28, band=90, tongues=8, tongue_n=11,
                            sparks=22, chunks=14, embers=12, spark_k=0.3)
for _wid, _ramp, _seed in (('pipe', 'awake', 171), ('knife', 'fade', 172), ('pistol', 'mint', 173), ('gauntlet', 'ember', 174), ('chain', 'violet', 175)):
    PB_EFFECTS['ult-nova-' + _wid] = _pb((230, 230), (115, 115), 0.66, ramp=_ramp, seed=_seed, r=106, tl=0.85, white=11, body=36, band=120,
                                      tongues=10, tongue_n=13, sparks=30, chunks=18, embers=14, spark_k=0.36)
PB_EFFECTS['death-burst'] = _pb((110, 110), (55, 55), 0.46, ramp='haze', seed=165, r=46, tl=0.62, white=4, ws=0.7, body=12, band=34, tongues=0,
                             sparks=8, chunks=16, embers=10, spark_k=0.24, chunk_size=(1.2, 2.2))
PB_EFFECTS['quake-blast'] = _pb((220, 120), (110, 116), 0.46, ramp='ember', seed=164, ground=0, half=True, r=92, tl=0.6, white=6, ws=0.6, body=16,
                             band=46, tongues=9, tongue_n=12, tongue_k=1.5, sparks=14, chunks=18, embers=4, spark_k=0.4, dust=4, chunk_size=(1.4, 2.6))


# =====================================================================================================
# 오버로드 기절 오라 aura-stun v2 (2026-11-24 사용자: '감전되는 효과가 너무 별로'): 전기 아크 대신 **과열**.
# 한 줄: 몸에서 붉은 불길이 새어 올라가 식고(불덩이 입자), 잿불이 떠오르고, 발밑에 붉은 빛이 숨 쉬듯 번진다. 반복(0.8초, 16장).
# 반복이 이어지게: 같은 뿌리기 일정을 주기마다 되풀이하고(난수도 주기마다 같은 값), 한 주기를 먼저 돌린 뒤부터 굽는다.
# =====================================================================================================
STUN_T = 0.8
STUN_META = dict(size=[120, 170], origin=[60, 158], duration=STUN_T, fps=20, options=dict(ramp='critical', seed=91))


def stun_create(o):
    R = RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    # 불길 혀: 몸 윤곽(양옆·어깨·머리 위)에서 솟는다. (뿌리 x, y, 높이, 굵기, 흔들림 위상, 한 주기에 일렁이는 횟수, 기울기)
    tongues = []
    for side in (-1, 1):
        for y in (-6, -22, -38, -51):
            tongues.append((side * (rng.range(8, 12) - 2 * (y < -45)), y + rng.range(-4, 4), rng.range(16, 40), rng.range(5.0, 7.0),
                            rng.range(0, TAU), rng.pick((1, 2)), side * rng.range(0.25, 0.6)))
    for x in (-7, 1, 8):
        tongues.append((x + rng.range(-2, 2), -56 + rng.range(-3, 3), rng.range(22, 44), rng.range(5.0, 7.0), rng.range(0, TAU), rng.pick((1, 2)), rng.range(-0.3, 0.3)))
    events = []                                                 # (시각, 종류, x, y, vx, vy, 수명, 크기)
    for _ in range(18):                                         # 잿불
        events.append((rng.range(0, STUN_T), EMBER, rng.range(-22, 22), -rng.range(10, 70), rng.range(-12, 12), -rng.range(30, 80),
                       rng.range(0.4, 0.7), rng.range(0.8, 1.4)))
    for _ in range(8):                                          # 튀는 조각
        a_ = rng.range(-2.6, -0.5)
        sp = rng.range(70, 170)
        events.append((rng.range(0, STUN_T), CHUNK, rng.range(-10, 10), -rng.range(20, 50), math.cos(a_) * sp, math.sin(a_) * sp,
                       rng.range(0.25, 0.4), rng.range(1.0, 1.6)))
    events.sort(key=lambda e: e[0])
    state = dict(t=0.0, i=0, ps=None)

    def new_cycle():
        old = state['ps'].items if state['ps'] else []
        state['ps'] = Particles(Rng(o['seed'] + 5), R)          # 주기마다 같은 난수 -> 같은 모양이 되풀이된다
        state['ps'].items = old
        state['i'] = 0

    def step(dt):
        state['t'] += dt
        while state['t'] >= STUN_T - 1e-9:
            state['t'] -= STUN_T
            new_cycle()
        ps = state['ps']
        while state['i'] < len(events) and events[state['i']][0] <= state['t']:
            _, kind, x, y, vx, vy, life, size = events[state['i']]
            ps.spawn(kind, x, y, vx, vy, life, size)
            state['i'] += 1
        ps.update(dt)

    new_cycle()
    for _ in range(int(STUN_T * 120)):                          # 한 주기를 먼저 돌려 둔다
        step(1 / 120)

    def tongue(p, tg, ph, layer, n):
        """혀 하나: 뿌리에서 끝으로 갈수록 가늘어지는 울퉁불퉁한 덩이의 줄. 끝은 흔들리고, 맨 끝 한두 덩이는 떨어져 나간다."""
        bx, by, hgt, r0, phase, cyc, lean = tg
        beat = 0.5 + 0.5 * math.sin(TAU * cyc * ph + phase)       # 높이가 일렁인다
        hgt = hgt * (0.62 + 0.38 * beat)
        steps = 9
        for m in range(steps + 2):
            f = m / steps
            if f > 1.0 and beat < 0.55:                           # 떨어져 나간 불씨는 혀가 높이 솟은 때만
                continue
            wob = math.sin(TAU * (cyc * ph * 2 + f * 1.3) + phase * 1.7) * 5.5 * f
            x = bx + lean * hgt * f + wob
            y = by - hgt * f * (1.0 if f <= 1.0 else 1.12)
            r = r0 * max(0.0, 1.0 - f) ** 1.05 if f <= 1.0 else 1.1
            sd = phase * 7 + m * 3.1 + n * 0.37                   # 장마다 모양이 조금씩 달라 타오르는 것처럼 보인다
            if layer == 0 and r + 1.2 >= 0.8:
                p.blob(x, y, r + 1.3, R[1] if f < 0.75 else R[0], sd, rough=0.22)       # 어두운 테두리
            elif layer == 1 and r >= 0.8:
                p.blob(x, y, r, R[2] if f < 0.6 else R[1], sd + 1.0, rough=0.2)          # 몸 (끝으로 갈수록 식어 어둡다)
            elif layer == 2 and f < 0.34 and int(phase * 10) % 2 == 0 and r * 0.42 >= 0.8:
                p.blob(x - lean * 1.5, y + 1, r * 0.42, R[3], sd + 2.0, rough=0.3)       # 뜨거운 심 (몇 줄기의 뿌리 쪽만)

    class Stun:
        def update(self, dt):
            step(dt)

        def draw(self, p):
            ph = state['t'] / STUN_T
            n = int(round(ph * 16)) % 16
            k = 0.5 + 0.5 * math.sin(TAU * ph)                    # 숨 쉬듯 번지는 빛 (한 주기에 한 번)
            p.glow(0, -34, 50, R[1], 80 + 40 * k)
            p.glow(0, -40, 28, R[2], 60 + 50 * k)
            p.glow(0, -2, 30, R[2], 50 + 30 * k)
            for layer in (0, 1, 2):
                for tg in tongues:
                    tongue(p, tg, ph, layer, n)
            state['ps'].draw(p)
    return Stun()


LOOPS = {'aura-stun': (STUN_META, stun_create)}


def build_loop(name, look):
    """반복 오라: 주인공을 기준점(발)에 세워 놓고 본다. json은 반복(loop)으로 고쳐 쓴다."""
    import json
    meta, create = LOOPS[name]
    frames = fx.render(meta, create)
    w, h = meta['size']
    ox, oy = meta['origin']
    hero = fx.Image.open(HERO).convert('RGBA')
    hero = hero.crop(hero.getbbox())
    hero = hero.resize((hero.width // 2, hero.height // 2), fx.Image.NEAREST)
    cols = 8
    out = fx.Image.new('RGB', (cols * w * 2, ((len(frames) + cols - 1) // cols) * h * 2), (9, 14, 24))
    for i, (color, light) in enumerate(frames):
        cell = fx.Image.new('RGB', (w, h), (9, 14, 24))
        la = fx.np.asarray(light, fx.np.float32)
        base = fx.np.clip(fx.np.asarray(cell, fx.np.float32) + la[..., :3] * (la[..., 3:4] / 255.0) * 0.85, 0, 255)
        cell = fx.Image.fromarray(base.astype(fx.np.uint8), 'RGB')
        behind = i % 2 == 0                                      # 짝수 칸: 게임처럼 오라가 몸 뒤, 홀수 칸: 오라만
        if behind:
            cell.paste(color, (0, 0), color)
            cell.paste(hero, (ox - hero.width // 2, oy - hero.height), hero)
        else:
            cell.paste(color, (0, 0), color)
        out.paste(cell.resize((w * 2, h * 2), fx.Image.NEAREST), ((i % cols) * w * 2, (i // cols) * h * 2))
    path = os.path.join(fx.ROOT, 'shots', 'fx', name + '.png')
    out.save(path)
    if look:
        print('본다', path)
        return
    info = fx.export(name, dict(meta), [frames])
    jp = os.path.join(fx.ROOT, 'assets', 'effects', name + '.json')
    data = json.load(open(jp, encoding='utf-8'))
    data.update(id='aura/' + name, loop=True)
    data.pop('duration', None)
    json.dump(data, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('구움', name, info['frames'], '프레임 (반복)')


# =====================================================================================================
# 사각형으로 그리던 것들을 시트로 (2026-11-26, haze-fx 절차): 적 탄환·광선·파동·오염 장판·낙뢰·결정 조각·둥근 점.
# 반복 시트는 한 주기가 꼭 맞게 이어지도록 시간(ph = 0~1)의 주기 함수로만 그린다. 광선·장판은 세로·가로로 이어 붙이는 타일이다
# (길이가 실행 중에 정해진다: 게임은 effects.draw_beam / draw_strip으로 필요한 만큼 이어 그린다).
# =====================================================================================================
RAMPS.setdefault('toxic', [fx.hexc(c) for c in ('#0c4a3a', '#1f9a70', '#46d2a0', '#aaffd2', '#ffffff')])   # 오염 장판 (아크)


def _periodic(draw_fn):
    """한 주기를 그리는 반복 이펙트: draw_fn(p, ph, R, o) (ph = 0~1). 입자 시뮬레이션 없이 주기 함수로만 그려 처음과 끝이 이어진다."""
    def create(o):
        R = RAMPS[o['ramp']]
        t = [0.0]

        class F:
            def update(self, dt):
                t[0] += dt

            def draw(self, p):
                draw_fn(p, (t[0] / o['period']) % 1.0, R, o)
        return F()
    return create


def _frac(x):
    return x - math.floor(x)


# 헤이즈 탄환 (아크 탄막): 흰 심을 감싼 청록 덩이가 일렁이고, 작은 알갱이 셋이 둘레를 돈다. 방향이 없어 어느 쪽으로 날아도 된다
def _orb_draw(p, ph, R, o):
    wob = math.sin(TAU * ph)
    p.glow(0, 0, 13, R[2], 150)
    p.glow(0, 0, 6, R[3], 90 + 30 * wob)
    p.blob(0, 0, 5.6 + 0.4 * wob, R[1], 0.3 + 0.08 * wob, rough=0.16)
    p.blob(0, 0, 4.4 - 0.3 * wob, R[2], 0.7 + 0.08 * wob, rough=0.14)
    p.disc(-0.5, -0.5, 2.6 + 0.3 * wob, R[3])
    p.disc(-0.5, -0.5, 1.6, WHITE)
    for i in range(3):                                           # 도는 알갱이: 한 주기에 1/3바퀴 (셋이라 이어진다)
        a = TAU * (ph + i) / 3
        r = 8.5 + 1.2 * math.sin(TAU * (ph * 2 + i / 3))
        p.px(math.cos(a) * r, math.sin(a) * r * 0.8, WHITE if i == 0 else R[3])
        p.px(math.cos(a - 0.35) * r, math.sin(a - 0.35) * r * 0.8, R[2])


# 내리쏘는 광선 타일 (용접 드론의 불꽃, 심장 손의 광선): 흰 심 + 색 가장자리가 아래로 흐른다. 위아래로 이어 붙는다
def _beam_draw(p, ph, R, o):
    half, H = o['half'], o['tile']

    def fn(X, Y):
        u = Y / H
        er = half * (1 + 0.10 * fx.np.sin(TAU * (2 * u - 2 * ph)) + 0.07 * fx.np.sin(TAU * (5 * u - 3 * ph) + 1.0)
                     + 0.14 * (fx.np.sin(TAU * (9 * u - 5 * ph)) > 0.72))
        el = half * (1 + 0.10 * fx.np.sin(TAU * (3 * u - 2 * ph) + 2.0) + 0.07 * fx.np.sin(TAU * (4 * u - 3 * ph) + 0.4)
                     + 0.14 * (fx.np.sin(TAU * (8 * u - 5 * ph) + 1.7) > 0.72))
        ax = fx.np.where(X >= 0, X / er, -X / el)
        idx = fx.np.full(X.shape, -1)
        idx[ax < 1.0] = 1
        idx[ax < 0.84] = 2
        idx[ax < 0.64] = 3
        idx[ax < 0.46] = 4
        for sx, m, n, off in ((-0.26, 2, 3, 0.0), (0.08, 1, 4, 1.7), (0.3, 2, 5, 3.1)):           # 심 안에서 아래로 흐르는 긴 결 세 줄
            col = fx.np.abs(X - sx * half) < 0.5
            idx[col & (ax < 0.46) & (fx.np.sin(TAU * (m * u - n * ph) + off) > 0.35)] = 3
        return idx
    p.shade(-half * 2, 0, half * 2, H, fn, R)
    for i in range(6):                                           # 가장자리에서 떨어져 나와 아래로 흐르는 불티 (타일 위아래로 이어진다)
        side = -1 if i % 2 else 1
        y = _frac(i * 0.171 + ph * (1 if i < 3 else 2)) * H
        x = side * half * (1.18 + 0.2 * math.sin(TAU * (ph + i * 0.3)) + 0.12 * (i % 3))
        for yy in (y, y - H, y + H):
            p.line(x, yy - 3, x, yy, R[2])
            p.px(x, yy, R[3])
    p.glow_line(0, -half * 3, 0, H + half * 3, half * 2.6, R[2], 150)
    p.glow_line(0, -half * 3, 0, H + half * 3, half * 1.3, R[3], 90)


# 광선이 바닥에 닿은 자리: 흰 불덩이가 일렁이고 불티가 양옆으로 튀며 누운 고리가 퍼진다
def _beam_base_draw(p, ph, R, o):
    half = o['half']
    rng = Rng(o['seed'])
    p.glow(0, -4, 34, R[2], 150)
    p.glow(0, -3, 16, R[3], 110)
    v = _frac(ph * 2)
    p.ring(0, -2, half * 0.8 + half * 1.5 * out_expo(v), 2.0 * (1 - v) + 0.6, R[3], sy=0.24, a=1.0 if v < 0.5 else 2 - 2 * v, gaps=5,
           phase=o['seed'])
    for i in range(9):                                           # 바닥을 따라 낮게 타오르는 덩이
        bx = (i - 4) * half * 0.36 + rng.range(-1.5, 1.5)
        beat = 0.5 + 0.5 * math.sin(TAU * (ph * (2 if i % 2 else 3) + rng.range(0, 1)))
        r = (half * 0.42) * (1 - abs(i - 4) / 6.5) * (0.6 + 0.4 * beat)
        if r >= 0.9:
            p.blob(bx, -r * 0.9, r + 1.0, R[1], i + beat * 0.2, rough=0.2)
            p.blob(bx, -r * 0.9, r, R[2] if abs(i - 4) > 1 else R[3], i + 1.3 + beat * 0.2, rough=0.2)
    p.blob(0, -half * 0.3, half * 0.34 + 0.6 * math.sin(TAU * ph * 3), WHITE, 0.4, rough=0.16)
    for i in range(12):                                          # 튀는 불티: 저마다 다른 때에 나가 포물선으로 떨어진다
        off, cyc = rng.range(0, 1), rng.pick((1, 2))
        ang = rng.range(0.2, 1.15)
        side = -1 if i % 2 else 1
        sp = rng.range(70, 150)
        s = _frac(ph * cyc + off)
        life = 0.34

        def pos(q):
            tt = q * life
            return side * (half * 0.5 + math.cos(ang) * sp * tt), -(3 + math.sin(ang) * sp * tt - 0.5 * fx.GRAVITY * tt * tt)
        if s > 0.1:
            (x0, y0), (x1, y1) = pos(s - 0.1), pos(s)
            if y1 < 1:
                p.line(x0, y0, x1, y1, R[2] if s > 0.6 else R[3])
                p.px(x1, y1, WHITE if s < 0.6 else R[3])


# 게이지 파동 (아크): 바닥을 달리는 낮은 불길 벽. 나아가는 쪽으로 기울고 불길이 위로 흐른다. 오른쪽으로 가는 그림 (왼쪽은 게임이 뒤집는다)
def _wave_draw(p, ph, R, o):
    Hh, half = o['height'], o['half']

    def fn(X, Y):
        u = -Y                                                   # 바닥에서 위로
        best = fx.np.full(X.shape, 9.0)
        core = fx.np.zeros(X.shape, bool)
        # 혀 셋 (가운데 x, 높이 비율, 반폭, 흔들림 어긋남): 가운데가 가장 높고 앞뒤로 낮은 혀. 위쪽이 뒤(왼쪽)로 밀린다
        for cx, hk, hw0, off, m in ((1.0, 1.0, 8.5, 0.0, 2), (-7.5, 0.7, 6.5, 2.1, 3), (7.5, 0.55, 5.5, 4.0, 2), (-13.0, 0.38, 4.0, 1.2, 3)):
            top = Hh * hk * (0.9 + 0.1 * math.sin(TAU * (ph * m) + off))
            k = fx.np.clip(u / top, 0, 1)
            xc = X - cx + (5.0 + 3.0 * hk) * k ** 1.5 + 1.6 * fx.np.sin(TAU * (u / 15 - m * ph) + off) * k
            hw = hw0 * (1 - k) ** 0.6
            ax = fx.np.where((u >= 0) & (u <= top), fx.np.abs(xc) / fx.np.maximum(hw, 0.01), 9.0)
            best = fx.np.minimum(best, ax)
            core |= (ax < 0.34) & (k < 0.72) & (hk > 0.6)
        idx = fx.np.full(X.shape, -1)
        idx[best < 1.0] = 1
        idx[best < 0.8] = 2
        idx[best < 0.52] = 3
        idx[core] = 4
        return idx
    p.shade(-half * 2 - 8, -Hh - 2, half * 2, 0, fn, R)
    for i in range(5):                                           # 뒤로 떨어져 나가는 불씨
        s = _frac(ph * (1 if i % 2 else 2) + i * 0.23)
        x = -half * 0.4 - 16 * s - i * 1.5
        y = -Hh * (0.35 + 0.13 * i) - 6 * s
        if s < 0.8:
            p.px(x, y, R[3] if s < 0.4 else R[2])
            if s < 0.3:
                p.px(x + 1, y, WHITE)
    p.glow(0, -Hh * 0.45, Hh * 0.8, R[2], 140)
    p.glow(0, -Hh * 0.3, Hh * 0.4, R[3], 90)
    p.glow_ring(0, -1, half * 1.3, 5, R[2], 60, sy=0.25)


# 오염 장판 (아크) 타일: 바닥에 깔린 얕은 액체가 출렁이고 거품이 올라와 터진다. 가로로 이어 붙는다 (타일 너비 = 프레임 너비)
def _pollution_draw(p, ph, R, o):
    Wt = o['tile']

    def fn(X, Y):
        u = -Y
        hs = 6.4 + 1.6 * fx.np.sin(TAU * (X / Wt - ph)) + 0.9 * fx.np.sin(TAU * (2 * X / Wt + ph) + 1.0)
        idx = fx.np.full(X.shape, -1)
        ok = (u >= 0) & (u <= hs)
        idx[ok] = 1
        idx[ok & (u > hs - 1.2)] = 3                             # 수면의 밝은 선
        idx[ok & (u < 1.6)] = 0
        idx[ok & (u > hs - 2.4) & (u <= hs - 1.2)] = 2
        glint = ok & (u > hs - 1.2) & (fx.np.sin(TAU * (3 * X / Wt - 2 * ph)) > 0.9)
        idx[glint] = 4
        return idx
    p.shade(0, -11, Wt, 0, fn, R)
    for i, bx in enumerate((6.5, 18.5, 31.5)):                   # 거품: 올라오다 터진다
        s = _frac(ph + i * 0.37)
        y = -8 - 14 * s
        if s < 0.78:
            r = 1.0 + 1.2 * s
            p.ring(bx, y, r, 1.0, R[3])
            p.px(bx - 0.6, y - 0.6, WHITE)
        elif s < 0.9:
            for dx, dy in ((-3, -1), (3, -1), (-2, -3), (2, -3)):
                p.px(bx + dx, y + dy, R[3])
    p.glow_line(-16, -4, Wt + 16, -4, 16, R[2], 130)


# 떨어지는 결정 조각 (헤이즈 심장의 결정 비): 길쭉한 여섯 면 결정, 빛이 면을 타고 내려가고 위로 속도 줄기가 남는다
def _crystal_draw(p, ph, R, o):
    p.glow(0, -15, 18, R[2], 130)
    for i, lx in enumerate((-4, 0, 4)):                          # 위로 남는 속도 줄기
        ln = 9 + 7 * (0.5 + 0.5 * math.sin(TAU * (ph * 2 + i / 3)))
        if lx == 0 or int(ph * 12 + i) % 3:                       # 옆 줄기는 짧고 깜빡인다
            p.line(lx, -31 + abs(lx) * 1.6, lx, -31 + abs(lx) * 1.6 - ln * (1.0 if lx == 0 else 0.45), R[3] if lx == 0 else R[1])
    body = [(0, -31), (5, -23), (4, -7), (0, 0), (-4, -7), (-5, -23)]
    p.poly(body, R[0])
    p.poly([(0, -30), (4, -23), (3, -7.5), (0, -1.5), (-3, -7.5), (-4, -23)], R[1])
    p.poly([(0, -30), (0, -1.5), (-3, -7.5), (-4, -23)], R[2])   # 빛 받는 왼쪽 면
    p.line(-0.5, -28, -0.5, -4, R[3])                            # 가운데 모서리
    y = -27 + 22 * ph                                            # 흘러내리는 흰 빛
    p.line(-2.5, y, -2.5, min(-5, y + 4), WHITE)
    p.px(1.5, -23 + 14 * _frac(ph + 0.5), R[3])


# 낙뢰 (낙뢰 내려찍기): 하늘에서 꽂히는 굵은 흰 번개 -> 가늘어지며 다른 길로 한 번 더 번쩍 -> 끊어지며 사라진다. 바닥에 섬광과 불티
BOLT_META = dict(size=[96, 284], origin=[48, 278], duration=0.34, fps=30, options=dict(ramp='haze', seed=17, height=272))


def bolt_create(o):
    R = RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    Hh = o['height']

    def path(sway):
        pts, y, x = [(0.0, 0.0)], 0.0, 0.0
        while y > -Hh:
            y -= rng.range(11, 24)
            x = max(-26.0, min(26.0, x * 0.55 + rng.range(-sway, sway)))
            pts.append((x, max(y, -Hh - 4)))
        return pts
    main, second = path(13), path(16)
    branches = []
    for k in (3, 6, 9):                                          # 곁가지: 본줄기의 마디에서 옆으로 짧게
        if k < len(main):
            bx, by = main[k]
            side = rng.pick((-1, 1))
            pts = [(bx, by)]
            for _ in range(3):
                bx, by = bx + side * rng.range(5, 11), by + rng.range(4, 12)
                pts.append((bx, by))
            branches.append(pts)
    ps = Particles(rng, R, ground=0)
    ps.burst(SPARK, 0, -3, 16, (160, 460), (0.18, 0.34), spread=2.6, aim=-math.pi / 2)
    ps.burst(MOTE, 0, -6, 10, (60, 200), (0.16, 0.3), spread=3.0, aim=-math.pi / 2)
    lights = Lights()
    lights.add(0, -8, 46, R[2], 170, 0.26)
    lights.add(0, -8, 22, R[3], 150, 0.14)
    t = [0.0]

    def stroke(p, pts, w, color, skip=None):
        for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
            if skip is not None and skip(i):
                continue
            p.line(x0, y0, x1, y1, color, w)

    class Bolt:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            u = t[0]
            if u < 0.07:                                         # 주인공 프레임: 굵은 흰 줄기 + 색 테두리, 바닥의 흰 별
                stroke(p, main, 9.0, R[2])
                stroke(p, main, 6.0, R[3])
                stroke(p, main, 3.6, WHITE)
                for b in branches:
                    stroke(p, b, 2.6, R[3])
                    stroke(p, b, 1.0, WHITE)
                for i in range(7):
                    a = -math.pi + math.pi * (i + 0.5) / 7
                    ln = 30 if i % 2 == 0 else 17
                    p.needle(0, -3, math.cos(a) * ln, -3 + math.sin(a) * ln, WHITE, 5.0)
                p.disc(0, -4, 9, WHITE)
                for (x0, y0), (x1, y1) in zip(main, main[1:]):
                    p.glow_line(x0, y0, x1, y1, 20, R[2], 190)
            elif u < 0.14:                                       # 가늘어진다
                stroke(p, main, 5.0, R[2])
                stroke(p, main, 2.4, WHITE)
                for b in branches[:2]:
                    stroke(p, b, 1.0, R[3])
                for (x0, y0), (x1, y1) in zip(main, main[1:]):
                    p.glow_line(x0, y0, x1, y1, 16, R[2], 120)
            elif u < 0.2:                                        # 다른 길로 한 번 더
                stroke(p, second, 3.4, R[2])
                stroke(p, second, 1.4, WHITE)
                for (x0, y0), (x1, y1) in zip(second, second[1:]):
                    p.glow_line(x0, y0, x1, y1, 13, R[2], 90)
            elif u < 0.3:                                        # 끊어지며 사라진다
                gone = int((u - 0.2) / 0.1 * 3)
                stroke(p, main, 1.6, R[3] if gone < 2 else R[2], skip=lambda i: (i * 7 + 3) % 4 <= gone)
                for (x0, y0), (x1, y1) in zip(main[::2], main[1::2]):
                    p.glow_line(x0, y0, x1, y1, 10, R[2], 40)
            v = u / 0.26
            if v < 1:
                p.ring(0, -2, 8 + 34 * out_expo(v), 2.4 * (1 - v) + 0.6, WHITE if v < 0.25 else R[3], sy=0.24,
                       a=1.0 if v < 0.5 else 2 - 2 * v, gaps=6, phase=o['seed'])
            ps.draw(p)
            lights.draw(p)
    return Bolt()


EFFECTS['bolt-pillar'] = (BOLT_META, bolt_create)

# 보스 바닥 충격파 (크래셔·문지기, 2026-11-26 make_fx.py에서 옮김): 오른쪽으로 달리는 불길 물결.
# 앞(오른쪽)이 가장 높은 혀 다섯이 뒤로 기울어 일렁이고, 높이의 물결이 앞에서 뒤로 지나간다.
# 바닥에는 불길 띠가 깔리고, 앞쪽 땅에서 흙 조각이 튀어 오르며, 뒤로 불씨가 떨어져 나간다. 왼쪽으로 갈 때는 게임이 좌우 반전한다
RAMPS.setdefault('blaze', [fx.hexc(c) for c in ('#4a1010', '#a3262a', '#ff6a2e', '#ffc457', '#fff4d6')])   # 보스 불길 (예전 FIRE 색)

SHOCK_TONGUES = (   # (뿌리 x, 높이 비율, 반폭, 어긋남, 주파수)
    (12.0, 1.00, 7.5, 0.00, 1), (4.5, 0.72, 6.5, 0.22, 2), (-2.5, 0.50, 4.5, 0.41, 3), (-13.0, 0.40, 5.5, 0.63, 1), (-27.0, 0.20, 4.0, 0.86, 2))


def _shock_draw(p, ph, R, o):
    Hh = o['height']

    def fn(X, Y):
        u = -Y                                                   # 바닥에서 위로
        best = fx.np.full(X.shape, 9.0)
        core = fx.np.zeros(X.shape, bool)
        for cx, hk, hw0, off, m in SHOCK_TONGUES:
            swell = 0.78 + 0.22 * math.sin(TAU * (ph - off)) + 0.06 * math.sin(TAU * (3 * ph + off * 2))   # 앞에서 뒤로 지나가는 높이 물결
            top = Hh * hk * swell
            k = fx.np.clip(u / top, 0, 1)
            lean = (6.0 + 6.0 * hk) * k ** 1.6                   # 달리는 반대쪽(뒤)으로 기운다
            xc = X - cx + lean + 1.4 * fx.np.sin(TAU * (u / 13 - m * ph) + off * 5) * k
            hw = hw0 * (1 - k) ** 0.55 * (1 + 0.12 * fx.np.sin(TAU * (u / 9 + m * ph) + off * 3))
            ax = fx.np.where((u >= 0) & (u <= top), fx.np.abs(xc) / fx.np.maximum(hw, 0.01), 9.0)
            best = fx.np.minimum(best, ax)
            core |= (ax < 0.36) & (k < 0.66) & (hk > 0.5)
        # 바닥 불길 띠: 뒤로 갈수록 얇아지고 윗선이 출렁인다
        reach = fx.np.clip((X + 38) / 52, 0, 1)                 # 0 꼬리 -> 1 앞
        bed_top = 2.6 * reach + 1.2 * fx.np.sin(TAU * (X / 11 + 2 * ph)) + 0.7 * fx.np.sin(TAU * (X / 4.7 - 3 * ph) + 1.3)
        bed_top = fx.np.where(X > 15, bed_top + 4.0 - 0.75 * fx.np.maximum(X - 15, 0) ** 1.2, bed_top)   # 앞 발치: 비스듬히 낮아진다 (수직 벽처럼 잘리지 않게)
        bed = fx.np.where((u >= -1) & (u <= bed_top) & (X > -40) & (X < 25),
                          0.55 + 0.4 * fx.np.clip(u / fx.np.maximum(bed_top, 0.5), 0, 1) - 0.25 * reach, 9.0)   # 가장자리는 어두운 붉은색, 앞쪽만 밝다
        best = fx.np.minimum(best, bed)
        idx = fx.np.full(X.shape, -1)
        idx[best < 1.0] = 1
        idx[best < 0.78] = 2
        idx[best < 0.5] = 3
        idx[core] = 4
        idx[core & (fx.np.sin(TAU * (u / 11 - 2 * ph) + X * 0.8) > 0.62)] = 3      # 심 안에서 위로 흐르는 결 (민짜 면이 되지 않게)
        idx[(u < 0.5) & (idx >= 3)] = 2                         # 땅에 닿는 줄은 한 단계 어둡게
        return idx
    p.shade(-42, -Hh - 4, 26, 3, fn, R)
    for i in range(5):                                           # 앞쪽 땅에서 튀어 오르는 달궈진 파편 (포물선, 한 주기에 1~2번): 불길 앞으로 튄다
        s = _frac(ph * (1 + i % 2) + i * 0.41)
        x = 18 + 2 * (i % 3) + (5 + 3 * (i % 2)) * s
        y = -(24 + 7 * (i % 3)) * s + 28 * s * s - 1
        if y < -1:
            hot = s < 0.45
            p.px(x, y, R[3] if hot else R[2])
            p.px(x + 1, y, R[2] if hot else R[1])
            if i % 2 == 0:
                p.px(x, y + 1, R[1])
                p.px(x + 1, y + 1, R[0])
    for i in range(7):                                           # 뒤로 떨어져 나가는 불씨
        s = _frac(ph * (1 if i % 2 else 2) + i * 0.19)
        x = 4 - 6 * i - 18 * s
        y = -Hh * (0.25 + 0.09 * (i % 4)) - 10 * s
        if s < 0.75:
            p.px(x, y, R[4] if s < 0.25 else (R[3] if s < 0.5 else R[2]))
    p.glow(4, -Hh * 0.4, Hh * 0.85, R[2], 120)
    p.glow(10, -Hh * 0.25, Hh * 0.4, R[3], 80)
    p.glow(-10, -2, 26, R[1], 70)

# 반복 시트: 이름 -> (meta, create). period = duration (한 주기). json은 loop로 쓴다
PLAIN_LOOPS = {
    'orb-haze': (dict(size=[30, 30], origin=[15, 15], duration=0.4, fps=30, options=dict(ramp='haze', seed=21, period=0.4)), _periodic(_orb_draw)),
    'beam-flame': (dict(size=[48, 64], origin=[24, 0], duration=0.4, fps=30, options=dict(ramp='ember', seed=22, period=0.4, half=14, tile=64)),
                   _periodic(_beam_draw)),
    'beam-haze': (dict(size=[40, 64], origin=[20, 0], duration=0.4, fps=30, options=dict(ramp='haze', seed=23, period=0.4, half=11, tile=64)),
                  _periodic(_beam_draw)),
    'beam-flame-base': (dict(size=[100, 52], origin=[50, 46], duration=0.4, fps=30, options=dict(ramp='ember', seed=24, period=0.4, half=14)),
                        _periodic(_beam_base_draw)),
    'beam-haze-base': (dict(size=[100, 52], origin=[50, 46], duration=0.4, fps=30, options=dict(ramp='haze', seed=25, period=0.4, half=11)),
                       _periodic(_beam_base_draw)),
    'wave-absorb': (dict(size=[60, 56], origin=[32, 52], duration=0.4, fps=30, options=dict(ramp='violet', seed=26, period=0.4, height=42, half=13)),
                    _periodic(_wave_draw)),
    'wave-overcharge': (dict(size=[60, 56], origin=[32, 52], duration=0.4, fps=30, options=dict(ramp='haze', seed=27, period=0.4, height=42, half=13)),
                        _periodic(_wave_draw)),
    'pollution': (dict(size=[40, 30], origin=[0, 28], duration=0.8, fps=30, options=dict(ramp='toxic', seed=28, period=0.8, tile=40)),
                  _periodic(_pollution_draw)),
    'crystal-fall': (dict(size=[28, 60], origin=[14, 54], duration=0.4, fps=30, options=dict(ramp='haze', seed=29, period=0.4)),
                     _periodic(_crystal_draw)),
    'shockwave': (dict(size=[72, 56], origin=[44, 52], duration=0.4, fps=30, options=dict(ramp='blaze', seed=30, period=0.4, height=44)),
                  _periodic(_shock_draw)),
}


def build_plain_loop(name, look):
    """반복 시트를 굽는다. 모아 보기는 한 주기를 3배로, 그 아래에 타일 이음(세로·가로)과 주기 이음을 눈으로 볼 수 있게 붙여 놓는다."""
    import json
    meta, create = PLAIN_LOOPS[name]
    frames = fx.render(meta, create)
    w, h = meta['size']
    path = fx.contact(frames, os.path.join(fx.ROOT, 'shots', 'fx', name + '.png'), cols=12, origin=meta['origin'],
                      label=f"{name}  {w}x{h}  {len(frames)}f loop @{meta.get('fps', 30)}fps")
    tile = meta['options'].get('tile')
    if tile:                                                     # 타일 이음 확인: 같은 프레임을 세 번 이어 붙인다
        sheet = fx.Image.open(path).convert('RGB')
        vertical = tile == h
        strip = fx.Image.new('RGB', ((w if vertical else w * 3) * 3 * 4, (h * 3 if vertical else h) * 3), (9, 14, 24))
        for k, i in enumerate((0, 3, 6, 9)):
            color, light = frames[i % len(frames)]
            cell = fx.Image.new('RGB', (w if vertical else w * 3, h * 3 if vertical else h), (9, 14, 24))
            for r in range(3):
                at = (0, r * h) if vertical else (r * w, 0)
                la = fx.np.asarray(light, fx.np.float32)
                box = (at[0], at[1], at[0] + w, at[1] + h)
                base = fx.np.asarray(cell.crop(box), fx.np.float32)
                lit = fx.np.clip(base + la[..., :3] * (la[..., 3:4] / 255.0) * 0.85, 0, 255).astype(fx.np.uint8)
                cell.paste(fx.Image.fromarray(lit, 'RGB'), at)
                cell.paste(color, at, color)
            strip.paste(cell.resize((cell.width * 3, cell.height * 3), fx.Image.NEAREST), (k * cell.width * 3, 0))
        out = fx.Image.new('RGB', (max(sheet.width, strip.width), sheet.height + strip.height), (9, 14, 24))
        out.paste(sheet, (0, 0))
        out.paste(strip, (0, sheet.height))
        out.save(path)
    if look:
        print('본다', path)
        return
    info = fx.export(name, dict(meta), [frames])
    jp = os.path.join(fx.ROOT, 'assets', 'effects', name + '.json')
    data = json.load(open(jp, encoding='utf-8'))
    data.update(loop=True)
    data.pop('duration', None)
    if tile:
        data['tile'] = tile
    json.dump(data, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('구움', name, info['frames'], '프레임 (반복)')


# 둥근 점 (색은 게임이 입힌다): 예고 고리·조준선·소용돌이처럼 점을 늘어놓는 것들이 쓴다. 네 크기, 윗줄 = 색 층, 아랫줄 = 흰 심
DOT_SIZES = (1.6, 2.6, 3.6, 5.0)          # 반지름 (논리 px). 화면에서는 지름 약 6·10·14·20px
DOT_CELL = 16


def build_dots(look):
    import json
    w = DOT_CELL
    tint, core = [], []
    for r in DOT_SIZES:
        a = fx.Painter(w, w, w // 2, w // 2)
        a.disc(0, 0, r, fx.GRAY[2])
        if r > 2:
            a.disc(0, 0, r - 1.0, fx.GRAY[3])
        a.glow(0, 0, r * 2.6 + 2, (255, 255, 255), 150)
        b = fx.Painter(w, w, w // 2, w // 2)
        if r > 2:
            b.disc(-0.3, -0.3, max(0.8, r - 2.0), WHITE)
        tint.append(a.images())
        core.append(b.images())
    meta = dict(size=[w, w], origin=[w // 2, w // 2], duration=0.1, fps=30)
    if look:
        path = fx.contact(tint + core, os.path.join(fx.ROOT, 'shots', 'fx', 'dots.png'), zoom=6, cols=4, label='dots (tint / core)')
        print('본다', path)
        return
    fx.export_tint('dots', meta, [tint], [core])
    print('구움 dots', len(DOT_SIZES), '크기')


# ----- 크래셔 착지 등장의 바닥 그림자 (O2-2, 2026-11-26, src/boss_intro.py): 크기별 네 장 (실행 중 확대 없이 크기마다 그림) -----
# 납작한 어두운 타원 두 겹(가운데가 더 어둡다). 게임은 반투명으로 얹는다. 색 층만 쓴다 (빛 없음)
SHADOW_WIDTHS = (36, 64, 92, 120)
SHADOW_RAMP = [(4, 4, 8), (4, 4, 8), (72, 44, 44), (4, 4, 8), (4, 4, 8)]   # 가운데 검정, 바깥 겹은 어두운 바닥에서도 보이게 회갈색


def build_drop_shadow(look):
    w, h = SHADOW_WIDTHS[-1] + 8, 28
    frames = []
    for sw in SHADOW_WIDTHS:
        p = fx.Painter(w, h, w // 2, h // 2)
        rx, ry = sw / 2, max(3.0, sw * 0.09)

        def fn(X, Y, rx=rx, ry=ry):
            d = (X / rx) ** 2 + (Y / ry) ** 2
            idx = fx.np.full(X.shape, -1)
            idx[d < 1.0] = 2                                    # 바깥 겹 (조금 밝은 검보라)
            idx[d < 0.45] = 0                                   # 가운데 (더 어둡다)
            return idx
        p.shade(-w / 2, -h / 2, w / 2, h / 2, fn, SHADOW_RAMP)
        frames.append(p.images())
    meta = dict(size=[w, h], origin=[w // 2, h // 2], duration=len(frames) / 30, fps=30)
    if look:
        path = fx.contact(frames, os.path.join(fx.ROOT, 'shots', 'fx', 'drop-shadow.png'), zoom=4, cols=4, label='drop-shadow (4 sizes)')
        print('본다', path)
        return
    fx.export('drop-shadow', meta, [frames])
    print('구움 drop-shadow', len(frames), '크기')


# ----- 실루엣 컷인의 큰 원반 (O1, 2026-11-26, src/cut_in.py): 색은 게임이 입힌다 (윗줄 색 층, 아랫줄 흰 심) -----
# 단색 바탕 위의 큰 원반: 처음 네 장은 커지며(살짝 넘쳤다 돌아온다) 마지막 장에 머문다. 안쪽에 한 단계 어두운 띠와 끊어진 가는 고리,
# 바깥에 끊어진 고리 하나, 흰 심은 윗왼쪽 가장자리의 가는 호와 짧은 빗금 몇 개뿐 (원반 자체가 주인공, 흰색은 작게)
CUTIN_R = 140
CUTIN_CELL = 300
CUTIN_GROW = (0.6, 0.86, 1.04, 0.98, 1.0)


def _cutin_paint(a, b, R, i):
    """원반 한 장: a = 색 층, b = 흰 심."""
    a.disc(0, 0, R, fx.GRAY[3])                                          # 원반 몸통 (컷인의 그래픽 면: 반듯한 원)
    a.ring(0, 0, R - 3, 6.0, fx.GRAY[2])                                  # 가장자리만 한 단계 어둡게 (접시처럼 보이지 않게 안쪽 띠는 없다)
    a.ring(0, 0, R * 0.7, 2.0, fx.GRAY[2], gaps=5, phase=0.4 + i * 0.05)   # 끊어진 가는 고리 (장마다 조금 돈다)
    a.ring(0, 0, R + 7, 2.0, fx.GRAY[3], gaps=9, phase=1.1 - i * 0.06)     # 바깥 끊어진 고리
    if i < 2:
        a.ring(0, 0, R + 14 + 10 * i, 1.0, fx.GRAY[3], gaps=12, phase=0.2)  # 들어올 때 퍼지는 고리
    b.ring(0, 0, R - 2, 2.0, WHITE, a0=math.radians(190), a1=math.radians(262))   # 윗왼쪽 가장자리의 흰 호 (그림 좌표: y 아래)
    b.ring(0, 0, R - 2, 2.0, WHITE, a0=math.radians(20), a1=math.radians(38))     # 맞은편의 짧은 호
    for j, ang in enumerate((215, 228, 241)):
        c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        b.line(c * (R - 10), sn * (R - 10), c * (R - 16 - 3 * j), sn * (R - 16 - 3 * j), WHITE, 1.0)


def build_cutin_disc(look):
    w = CUTIN_CELL
    tint, core = [], []
    for i, k in enumerate(CUTIN_GROW):
        R = CUTIN_R * k
        a = fx.Painter(w, w, w // 2, w // 2)
        b = fx.Painter(w, w, w // 2, w // 2)
        _cutin_paint(a, b, R, i)
        tint.append(a.images())
        core.append(b.images())
    meta = dict(size=[w, w], origin=[w // 2, w // 2], duration=len(CUTIN_GROW) / 30, fps=30)
    if look:
        path = fx.contact([(t[0], t[1]) for t in tint] + [(c[0], c[1]) for c in core], os.path.join(fx.ROOT, 'shots', 'fx', 'cutin-disc.png'),
                          zoom=1, cols=5, label='cutin-disc (tint / core)')
        print('본다', path)
        return
    fx.export_tint('cutin-disc', meta, [tint], [core])
    print('구움 cutin-disc', len(CUTIN_GROW), '장')


# ----- 주인공 쪽 (2026-11-26): 쌍권총 탄환과 총구 섬광. 조준 방향이 실행 중에 정해져 32방향(11.25도 간격)을 미리 굽는다 -----
DIR_N = 32


def _dir(o):
    """게임 각도(위가 +y)를 그림 좌표(아래가 +y)의 단위 벡터로."""
    a = TAU * o['variant'] / DIR_N
    return math.cos(a), -math.sin(a)


# 탄환: 흰 머리에서 색 꼬리로 가늘어지는 줄기 + 머리의 빛. 꼬리 끝이 장마다 조금씩 일렁이고 불티가 떨어져 나간다. 기준점 = 머리
def _bullet_draw(p, ph, R, o):
    dx, dy = _dir(o)
    nx, ny = -dy, dx
    L, Wd = o['length'], o['width']
    flick = 1.0 + 0.12 * math.sin(TAU * ph)
    p.glow(0, 0, Wd * 3.2 + 4, R[2], 170)
    p.glow_line(-dx * L * 0.2, -dy * L * 0.2, -dx * L * 0.85, -dy * L * 0.85, Wd * 2.0 + 2, R[2], 90)
    p.needle(dx * 1.5, dy * 1.5, -dx * L * flick, -dy * L * flick, R[1], Wd + 2.0)
    p.needle(dx * 1.5, dy * 1.5, -dx * L * 0.82 * flick, -dy * L * 0.82 * flick, R[2], Wd + 0.8)
    p.needle(dx * 1.5, dy * 1.5, -dx * L * 0.6, -dy * L * 0.6, R[3], Wd)
    p.needle(dx * 2.0, dy * 2.0, -dx * L * 0.4, -dy * L * 0.4, WHITE, max(1.6, Wd * 0.62))
    p.disc(dx * 0.5, dy * 0.5, max(1.2, Wd * 0.55), WHITE)
    for i in range(3):                                           # 꼬리에서 옆으로 떨어져 나가는 불티
        s = _frac(ph + i / 3)
        back = L * (0.45 + 0.5 * s)
        side = (Wd * 0.6 + 2.5 * s) * (1 if i % 2 else -1)
        if s < 0.8:
            p.px(-dx * back + nx * side, -dy * back + ny * side, R[3] if s < 0.4 else R[2])


# 총구 섬광: 앞으로 길게 뻗는 흰 가시 + 양옆 짧은 가시 + 옆으로 벌어지는 가는 십자 -> 색으로 식으며 줄어든다 (세 장). 기준점 = 총구
def _muzzle_create(o):
    R = RAMPS[o['ramp']]
    k = o.get('k', 1.0)
    t = [0.0]

    class M:
        def update(self, dt):
            t[0] += dt

        def draw(self, p):
            dx, dy = _dir(o)
            nx, ny = -dy, dx
            u = t[0] / o['life']
            s = (1.0 if u < 0.34 else 0.66 if u < 0.67 else 0.36) * k
            hot = WHITE if u < 0.34 else R[3] if u < 0.67 else R[2]
            p.glow(dx * 4, dy * 4, 20 * k, R[2], 190 * (1 - u))
            p.glow(dx * 2, dy * 2, 9 * k, R[3], 140 * (1 - u))
            for ang, ln, w in ((0.0, 24, 5.0), (0.5, 12, 3.2), (-0.5, 12, 3.2), (0.95, 6, 2.2), (-0.95, 6, 2.2)):
                c, sn = math.cos(ang), math.sin(ang)
                ex, ey = (dx * c - dy * sn) * ln * s, (dy * c + dx * sn) * ln * s
                p.needle(0, 0, ex, ey, R[2] if u < 0.67 else R[1], w * s + 1.4)
                p.needle(0, 0, ex * 0.86, ey * 0.86, hot, w * s, tip=WHITE if u < 0.67 else None)
            if u < 0.67:                                         # 옆으로 벌어지는 가는 십자
                side = 7 * s
                p.line(dx * 1.5 + nx * side, dy * 1.5 + ny * side, dx * 1.5 - nx * side, dy * 1.5 - ny * side, R[3])
                p.disc(dx * 1.5, dy * 1.5, 3.4 * s, WHITE)
            else:                                                # 마지막 장: 앞으로 흩어지는 불티
                for i, (f, sd) in enumerate(((18, 2.5), (13, -3.5), (22, -1.0), (9, 4.0))):
                    p.px(dx * f * k + nx * sd, dy * f * k + ny * sd, R[3] if i % 2 else WHITE)
    return M()


# 이름 -> (meta, create, 반복인가). 방향 변형 32줄
DIR_SHEETS = {
    'bullet': (dict(size=[72, 72], origin=[36, 36], duration=4 / 30, fps=30,
                    options=dict(ramp='haze', seed=41, period=4 / 30, length=27, width=3.0)), _periodic(_bullet_draw), True),
    'bullet-big': (dict(size=[104, 104], origin=[52, 52], duration=4 / 30, fps=30,
                        options=dict(ramp='violet', seed=42, period=4 / 30, length=41, width=5.6)), _periodic(_bullet_draw), True),
    'bullet-s': (dict(size=[44, 44], origin=[22, 22], duration=4 / 30, fps=30,
                      options=dict(ramp='haze', seed=43, period=4 / 30, length=14, width=2.0)), _periodic(_bullet_draw), True),
    'muzzle': (dict(size=[72, 72], origin=[36, 36], duration=0.1, fps=30, options=dict(ramp='haze', seed=44, life=0.1)), _muzzle_create, False),
    'muzzle-big': (dict(size=[104, 104], origin=[52, 52], duration=0.1, fps=30, options=dict(ramp='violet', seed=45, life=0.1, k=1.5)),
                   _muzzle_create, False),
}


def build_dir(name, look):
    """32방향 시트를 굽는다 (한 줄 = 한 방향, 0번 = 오른쪽, 반시계로 11.25도씩). 모아 보기는 여덟 방향만 본다."""
    import json
    meta, create, loop = DIR_SHEETS[name]
    variants = [fx.render(meta, create, variant=v) for v in range(DIR_N)]
    w, h = meta['size']
    show = [f for v in (0, 1, 2, 4, 6, 8, 12, 16, 20, 29) for f in variants[v][:3]]
    path = fx.contact(show, os.path.join(fx.ROOT, 'shots', 'fx', name + '.png'), cols=6, origin=meta['origin'],
                      label=f"{name}  {w}x{h}  {len(variants[0])}f x {DIR_N} dirs")
    if look:
        print('본다', path)
        return
    info = fx.export(name, dict(meta), variants)
    jp = os.path.join(fx.ROOT, 'assets', 'effects', name + '.json')
    data = json.load(open(jp, encoding='utf-8'))
    data['directions'] = DIR_N
    if loop:
        data['loop'] = True
        data.pop('duration', None)
    json.dump(data, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('구움', name, info['frames'], '프레임', DIR_N, '방향')


def main(argv):
    look = '--look' in argv
    if '--pb' in argv:                                          # 보류한 입자 구성·반투명 띠 시안: 모아 보기만
        if not look:
            print('--pb 는 --look 과 함께만 쓴다 (게임 파일로 굽지 않는다)')
            return
        EFFECTS.update(PB_EFFECTS)
        TINTS.update(PB_TINTS)
    # 초승달·회전 베기(SLASHES·SPINS)는 이름을 직접 줄 때만 굽는다: 2026-11-24 사용자가 '찌그러지고 빛이 사라져 밋밋하다'며 반려,
    # 게임은 tools/make_slash_hq.py의 예전 그림을 쓴다. 다시 시도하려면 모양(가운데가 굵은 고른 초승달)과 빛부터 고칠 것
    names = ([a for a in argv if not a.startswith('--')]
             or list(EFFECTS) + [n for n in TINTS if n not in LOOK_ONLY_TINTS] + list(LOOPS) + list(PLAIN_LOOPS) + list(DIR_SHEETS) + ['dots', 'cutin-disc', 'drop-shadow'])
    for name in names:
        if name == 'drop-shadow':
            build_drop_shadow(look)
            continue
        if name == 'cutin-disc':
            build_cutin_disc(look)
            continue
        if name == 'dots':
            build_dots(look)
            continue
        if name in DIR_SHEETS:
            build_dir(name, look)
            continue
        if name in PLAIN_LOOPS:
            build_plain_loop(name, look)
            continue
        if name in LOOPS:
            build_loop(name, look)
            continue
        if name in SLASHES or name in SPINS:
            build_slash(name, look)
            continue
        if name in LOOK_ONLY_TINTS and not look:
            print('보기 전용 시안이라 굽지 않는다 (--look):', name)
            continue
        if name in TINTS:
            build_tint(name, look)
            continue
        if name in LOOK_ONLY and not look:
            print('보기 전용 시안이라 굽지 않는다 (--look):', name)
            continue
        meta, create = EFFECTS[name] if name in EFFECTS else LOOK_ONLY[name]
        # variant_seeds: 같은 레시피를 시드만 바꿔 여러 줄로 굽는다 (자주 겹쳐 띄우는 이펙트가 똑같이 되풀이되지 않게, 예: steam-jet)
        rows = [fx.render(meta, create, seed=sd) for sd in meta['variant_seeds']] if meta.get('variant_seeds') else [fx.render(meta, create)]
        frames = [f for row in rows for f in row]
        path = fx.contact(frames, os.path.join(fx.ROOT, 'shots', 'fx', name + '.png'), actor=HERO, origin=meta['origin'],
                          label=f"{name}  {meta['size'][0]}x{meta['size'][1]}  {len(frames)}f @{meta.get('fps', 30)}fps")
        if look:
            print('본다', path)
            continue
        meta = dict(meta)
        meta.pop('variant_seeds', None)
        info = fx.export(name, meta, rows)
        print('구움', name, info['frames'], '프레임')


if __name__ == '__main__':
    main(sys.argv[1:])
