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
from fxkit import EMBER, MOTE, PUFF, RAMPS, SHARD, SPARK, TAU, WHITE, Lights, Particles, Rng, clamp, out_cubic, out_expo  # noqa: E402

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
    'quake-blast': (dict(size=[220, 120], origin=[110, 116], duration=0.46, fps=30, options=dict(ramp='ember', seed=64, ground=0)),
                    _simple(_quake_setup, _quake_draw)),
    'death-burst': (dict(size=[110, 110], origin=[55, 55], duration=0.46, fps=30, options=dict(ramp='haze', seed=65)),
                    _simple(_death_setup, _death_draw)),
}
EFFECTS.update(MISC)
# 궁극기 광역 폭발: 헤이즈 폭발(blast_create)을 무기 색·크기로 (오버로드 폭발은 아래 over_create)
for _wid, _ramp, _seed in (('pipe', 'awake', 71), ('knife', 'fade', 72), ('pistol', 'mint', 73), ('gauntlet', 'ember', 74), ('chain', 'violet', 75)):
    EFFECTS['ult-nova-' + _wid] = (dict(size=[230, 230], origin=[115, 115], duration=0.66, fps=30, options=dict(ramp=_ramp, seed=_seed, k=1.25)),
                                   blast_create)


# ----- 오버로드 폭발 (2026-11-24 사용자: "팡 하고 터진다는 느낌이 없다"): 가는 선의 큰 고리가 아니라 꽉 찬 덩어리가 터져 나간다 -----
# 한 줄: 큰 흰 별 덩어리 두 장 -> 진한 붉은 원반이 순식간에 부풀고(밝은 충격 테두리) -> 가운데부터 비워져 굵은 고리로 화면 밖까지 밀려나며
#        토막 난다. 굵은 가시, 빠른 불티·큰 조각이 사방으로.
OVER_META = dict(size=[460, 460], origin=[230, 230], duration=0.7, fps=30, options=dict(ramp='critical', seed=81))


def over_create(o):
    R = RAMPS[o['ramp']]
    rng = Rng(o['seed'])
    ps = Particles(rng, R)
    lights = Lights()
    lights.add(0, 0, 225, R[2], 150, 0.5)
    lights.add(0, 0, 120, WHITE, 190, 0.22)
    lights.add(0, 0, 60, WHITE, 200, 0.14)
    ps.burst(SPARK, 0, 0, 46, (500, 1500), (0.25, 0.55), up=60, size=(1.6, 2.6))
    ps.burst(SHARD, 0, 0, 24, (360, 1000), (0.35, 0.6), up=140, size=(2.0, 4.0))
    ps.burst(MOTE, 0, 0, 34, (200, 800), (0.3, 0.6), size=(1.0, 2.0))
    ps.burst(EMBER, 0, 0, 16, (60, 240), (0.4, 0.62), delay=(0.12, 0.3))
    n = 16
    rays = [(TAU * i / n + rng.range(-0.14, 0.14), rng.range(0.65, 1.25), rng.range(0.0, 0.03)) for i in range(n)]
    arcs = [(TAU * i / 9 + rng.range(-0.12, 0.12), rng.range(0.42, 0.62), rng.range(0.7, 1.4), rng.range(0.0, 0.08)) for i in range(9)]
    t = [0.0]

    class Over:
        def update(self, dt):
            t[0] += dt
            ps.update(dt)
            lights.update(dt)

        def draw(self, p):
            u = t[0]
            i = int(u * 30 + 0.01)
            if i >= 2:                                         # 진한 원반 -> 굵은 고리 -> 토막
                v = u - 2 / 30
                r = 104 + 106 * out_expo(v / 0.16)           # 흰 별 크기에서 이어서 부푼다
                hole = 0.0 if v < 0.07 else (r - 10) * out_cubic((v - 0.07) / 0.1)
                late = max(0.0, v - 0.17)
                if hole < 1:
                    p.disc(0, 0, r, R[2])
                    p.ring(0, 0, r - 3, 8, R[3])                # 밝은 충격 테두리
                    p.ring(0, 0, r - 1, 2.5, WHITE)
                    p.ring(0, 0, r * 0.7, 2.5, R[1], gaps=7, phase=u * 9)
                    p.ring(0, 0, r * 0.42, 2.0, R[1], gaps=4, phase=-u * 7)
                elif late < 0.04:
                    w = max(3.0, r - hole)
                    p.ring(0, 0, r - w / 2, w, R[2])
                    p.ring(0, 0, r - 1, 3.0, R[3])
                else:
                    for a0, span, speed, stay in arcs:
                        life = 0.26 + stay
                        if late >= life:
                            continue
                        kk = late / life
                        p.ring(0, 0, r + 22 * speed * out_cubic(kk), max(1.5, 14.0 * (1 - kk) ** 1.4), R[3] if kk < 0.3 else R[2],
                               a=1.0 if kk < 0.7 else 1.0 - (kk - 0.7) / 0.3, a0=a0, a1=a0 + span * (1 - kk * 0.4))
                p.glow_ring(0, 0, r, 26, R[2], 120 * max(0.0, 1.0 - v / 0.4))
            for ang, ln, delay in rays:                         # 굵은 가시: 원반보다 먼저 튀어 나간다
                v = u - delay
                if v < 0 or v > 0.3:
                    continue
                head = (70 + 150 * out_expo(v / 0.12)) * ln
                tail = 30 + 170 * out_cubic(v / 0.3) * ln
                if head - tail < 3:
                    continue
                c, s_ = math.cos(ang), math.sin(ang)
                p.needle(c * tail, s_ * tail, c * head, s_ * head, R[3] if v > 0.08 else WHITE, 13 * (1 - v / 0.32) + 2, tip=WHITE)
            if i < 3:                                           # 주인공 프레임: 큰 흰 별 덩어리 ("팡")
                s = (1.0, 0.86, 0.5)[i]
                for j in range(14):
                    ang = TAU * j / 14 + 0.17
                    ln = (150 if j % 2 == 0 else 96) * s
                    p.needle(0, 0, math.cos(ang) * ln, math.sin(ang) * ln, WHITE, 46 * s)
                p.disc(0, 0, 62 * s, WHITE)
            ps.draw(p)
            lights.draw(p)
    return Over()


EFFECTS['overload-burst'] = (OVER_META, over_create)


def main(argv):
    look = '--look' in argv
    # 초승달·회전 베기(SLASHES·SPINS)는 이름을 직접 줄 때만 굽는다: 2026-11-24 사용자가 '찌그러지고 빛이 사라져 밋밋하다'며 반려,
    # 게임은 tools/make_slash_hq.py의 예전 그림을 쓴다. 다시 시도하려면 모양(가운데가 굵은 고른 초승달)과 빛부터 고칠 것
    names = [a for a in argv if not a.startswith('--')] or list(EFFECTS) + list(TINTS)
    for name in names:
        if name in SLASHES or name in SPINS:
            build_slash(name, look)
            continue
        if name in TINTS:
            build_tint(name, look)
            continue
        meta, create = EFFECTS[name]
        frames = fx.render(meta, create)
        path = fx.contact(frames, os.path.join(fx.ROOT, 'shots', 'fx', name + '.png'), actor=HERO, origin=meta['origin'],
                          label=f"{name}  {meta['size'][0]}x{meta['size'][1]}  {len(frames)}f @{meta.get('fps', 30)}fps")
        if look:
            print('본다', path)
            continue
        meta = dict(meta)
        info = fx.export(name, meta, [frames])
        print('구움', name, info['frames'], '프레임')


if __name__ == '__main__':
    main(sys.argv[1:])
