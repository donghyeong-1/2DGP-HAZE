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
    ps = Particles(rng, R, ground=46)
    smoke = Particles(rng, [R[0], R[0], R[1], R[2], R[3]])     # 연기는 색 띠의 어두운 쪽
    lights = Lights()
    lights.add(0, 0, 74, R[2], 110, 0.55)
    lights.add(0, 0, 30, WHITE, 170, 0.2)
    ps.burst(SPARK, 0, 0, 22, (220, 620), (0.25, 0.6), up=90)
    ps.burst(SHARD, 0, 0, 7, (160, 420), (0.35, 0.6), up=130, size=(0.8, 1.6))
    ps.burst(MOTE, 0, 0, 16, (80, 340), (0.3, 0.6), size=(0.8, 1.8))
    ps.burst(EMBER, 0, 0, 10, (30, 120), (0.5, 0.78), delay=(0.15, 0.3))
    smoke.burst(SHARD, 0, 0, 9, (90, 260), (0.4, 0.7), up=60, size=(1.4, 2.4), delay=(0.03, 0.08))   # 연기 대신 어두운 큰 조각 (공 모양 연기는 어색했다)
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
                    ln = (34 if i % 2 == 0 else 22) * s
                    p.needle(0, 0, math.cos(ang) * ln, math.sin(ang) * ln, WHITE, 16 * s)
                p.disc(0, 0, 15 * s, WHITE)
                p.ring(0, 0, 16 * s, 1.5, R[3])
            if u < 0.3:                                            # 빛 가시: 안쪽이 굵고 끝이 흰 삼각 줄기
                v = u / 0.3
                for ang, ln in spikes:
                    head = (20 + 52 * out_expo(v * 1.4)) * ln
                    tail = 6 + 46 * out_cubic(v) * ln
                    if head - tail < 2:
                        continue
                    c, s_ = math.cos(ang), math.sin(ang)
                    p.needle(c * tail, s_ * tail, c * head, s_ * head, R[3] if v < 0.4 else R[2], 6 * (1 - v) + 1.5, tip=WHITE)
            if 0.04 < u < 0.5:                                     # 충격 고리 둘: 큰 것과 한 박자 늦은 작은 것
                for delay, rmax, w in ((0.04, 66, 3.0), (0.1, 44, 2.0)):
                    v = (u - delay) / 0.36
                    if 0 < v < 1:
                        r = 10 + rmax * out_expo(v)
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


EXEC_DISC_META = dict(size=[248, 248], origin=[124, 124], duration=6 / 30, fps=30, options=dict(seed=3))


def exec_disc_create(o):
    """0 작은 원반 / 1·2 큰 진한 원반 + 밝은 테두리 + 흰 여덟 갈래 별 + 흰 불티 / 3 비워진 굵은 고리 + 작은 별 / 4·5 가늘어지는 고리."""
    core = o['layer'] == 'core'
    rng = Rng(o['seed'])
    sparks = [(rng.range(0, TAU), rng.range(0.8, 1.25), rng.range(5, 12)) for _ in range(14)]
    star8 = [(TAU * i / 8, 40 if i % 2 == 0 else 20, 1.0 if i % 2 == 0 else 0.6) for i in range(8)]

    def draw(p, i):
        if i == 0:
            if not core:
                p.disc(0, 0, 22, G[3])
                p.ring(0, 0, 22, 2.5, G[3])
                p.glow(0, 0, 44, WHITE, 120)
        elif i in (1, 2):
            r = 45 if i == 1 else 48
            if not core:
                p.disc(0, 0, r, G[3])                                  # 진한 색 면 (주인공): 색을 그대로 받는다
                p.ring(0, 0, r, 3.5, G[1])                             # 조금 어두운 테두리 (면이 더 밝다)
                p.ring(0, 0, r * 0.72, 1.5, G[3], gaps=6, phase=i)
                p.glow(0, 0, r * 2.1, WHITE, 150)
                p.glow(0, 0, r * 1.3, WHITE, 110)
            else:
                k = 1.0 if i == 1 else 0.82
                _star(p, [(a, ln * k, w) for a, ln, w in star8], WHITE, 5.5)
                p.disc(0, 0, 4.5 * k, WHITE)
                for ang, far, ln in sparks:                             # 흰 불티: 꼬리를 끌며 바깥으로
                    d0 = (r + 6 + (14 if i == 2 else 0)) * far
                    c, s_ = math.cos(ang), math.sin(ang)
                    p.needle(c * d0, s_ * d0, c * (d0 + ln), s_ * (d0 + ln), WHITE, 2.4)
        elif i == 3:
            if not core:
                p.ring(0, 0, 50, 7, G[3])
                p.ring(0, 0, 53, 1.5, G[3])
                p.glow_ring(0, 0, 50, 16, WHITE, 110)
            else:
                _star(p, [(a, ln * 0.45, w) for a, ln, w in star8], WHITE, 4.0)
                for ang, far, ln in sparks[::2]:
                    d0 = 78 * far
                    c, s_ = math.cos(ang), math.sin(ang)
                    p.needle(c * d0, s_ * d0, c * (d0 + ln * 0.7), s_ * (d0 + ln * 0.7), WHITE, 1.6)
        elif i == 4 and not core:
            p.ring(0, 0, 53, 3.5, G[1], gaps=7, phase=1.0)
            p.glow_ring(0, 0, 53, 10, WHITE, 60)
        elif i == 5 and not core:
            p.ring(0, 0, 55, 1.5, G[0], a=0.7, gaps=9, phase=2.0)
    return _frame_fx(draw)


EXEC_STAR_META = dict(size=[248, 248], origin=[124, 124], duration=2 / 30, fps=30, options=dict(seed=3))


def exec_star_create(o):
    """0 첫 일격: 위아래로 긴 색 가시 + 작은 흰 별 / 1 둘째 일격: 큰 색 네 갈래 별(면이 크다) + 가운데 흰 십자."""
    core = o['layer'] == 'core'

    def draw(p, i):
        q = TAU / 4
        if i == 0:
            if not core:
                _star(p, [(q, 96, 1.0), (-q, 96, 1.0), (0, 34, 0.7), (2 * q, 34, 0.7)], G[3], 13)
                p.glow(0, 0, 70, WHITE, 140)
            else:
                _star(p, [(a, 24 if k % 2 == 0 else 13, 1.0) for k, a in enumerate(TAU * j / 8 for j in range(8))], WHITE, 3.5)
                p.disc(0, 0, 4, WHITE)
        else:
            if not core:
                _star(p, [(q, 108, 1.0), (-q, 108, 1.0), (0, 88, 0.9), (2 * q, 88, 0.9)], G[3], 30)
                _star(p, [(q / 2 + q * j, 40, 1.0) for j in range(4)], G[2], 14)
                p.glow(0, 0, 110, WHITE, 150)
            else:
                _star(p, [(q * j, 44, 1.0) for j in range(4)], WHITE, 4.5)
                p.disc(0, 0, 6, WHITE)
    return _frame_fx(draw)


EXEC_CRESCENT_META = dict(size=[216, 128], origin=[108, 64], duration=5 / 30, fps=30, options=dict(seed=3))


def exec_crescent_create(o):
    """적을 감싸는 예고 초승달 (왼쪽이 굵고 오른쪽 끝이 가늘게 올라간다). 0·1·2 꽉 찬 모양 / 3·4 가늘어져 줄기로.
    색은 게임이 장면마다 바꾼다: 회색(예고) -> 흰색 -> 진한 자홍."""
    core = o['layer'] == 'core'

    def draw(p, i):
        if core:
            return
        s = (1.0, 1.0, 1.0, 0.62, 0.3)[min(i, 4)]

        def fn(X, Y):
            outer = (X / 100.0) ** 2 + ((Y - 6) / 44.0) ** 2 <= 1.0
            inner = ((X - 22 * s) / 96.0) ** 2 + ((Y + 12 * s - 6) / 40.0) ** 2 <= 1.0
            keep = outer & ~inner & (Y > -14 - 20 * (X < 0))
            return fx.np.where(keep, 3, -1)
        p.shade(-104, -60, 104, 60, fn, G)
        if i >= 1:
            p.glow(-40, 18, 70, WHITE, 90 if i < 3 else 40)
    return _frame_fx(draw)


TINTS['exec-disc'] = [(EXEC_DISC_META, exec_disc_create)]
TINTS['exec-star'] = [(EXEC_STAR_META, exec_star_create)]
TINTS['exec-crescent'] = [(EXEC_CRESCENT_META, exec_crescent_create)]


def build_tint(name, look):
    variants = TINTS[name]
    tint = [fx.render(meta, create, layer='tint') for meta, create in variants]
    core = [fx.render(meta, create, layer='core') for meta, create in variants]
    meta = variants[0][0]
    show = []                                              # 모아 보기: 색 층에 청록을 입히고 흰 심을 얹어서
    for r in (0, len(variants) // 3, (2 * len(variants)) // 3) if len(variants) > 1 else (0,):
        for (tc, tl), (cc, _) in zip(tint[r], core[r]):
            arr = fx.np.asarray(tc, fx.np.float32)
            arr[..., :3] *= fx.np.array([46, 230, 214], fx.np.float32) / 255.0
            body = fx.Image.fromarray(arr.astype(fx.np.uint8), 'RGBA')
            body.paste(cc, (0, 0), cc)
            la = fx.np.asarray(tl, fx.np.float32)
            la[..., :3] *= fx.np.array([46, 230, 214], fx.np.float32) / 255.0
            show.append((body, fx.Image.fromarray(la.astype(fx.np.uint8), 'RGBA')))
    path = fx.contact(show, os.path.join(fx.ROOT, 'shots', 'fx', name + '.png'), actor=HERO, origin=meta['origin'],
                      cols=len(tint[0]), label=f"{name}  {meta['size'][0]}x{meta['size'][1]}  {len(tint[0])}f  variants {len(variants)}")
    if look:
        print('본다', path)
        return
    info = fx.export_tint(name, meta, tint, core)
    print('구움', name, info['frames'], '프레임')


def main(argv):
    look = '--look' in argv
    names = [a for a in argv if not a.startswith('--')] or list(EFFECTS) + list(TINTS)
    for name in names:
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
