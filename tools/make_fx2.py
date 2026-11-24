"""헤이즈 전투 이펙트 v8 (2026-11-24): tools/fxkit.py로 굽는다. code-drawn, 전부 자체 제작 (이미지 모델 없음).

만드는 법·기준은 .claude/skills/haze-fx/SKILL.md. 이펙트마다 함수 하나(create)와 meta 하나.
  python tools/make_fx2.py --look hit-normal haze-blast     # 게임 파일은 그대로 두고 모아 보기만 (shots/fx/<이름>.png)
  python tools/make_fx2.py hit-normal                       # assets/effects·assets/light에 쓴다
  python tools/make_fx2.py                                   # 전부

시트 (assets/effects/<이름>.png + .json, 빛은 assets/light/glow_<이름>.png):
  hit-fade / hit-normal / hit-awake / hit-critical / hit-enhanced / hit-enhanced2 / hit-enhanced3   명중 불꽃
  haze-blast                                                                                       헤이즈 폭발
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


def main(argv):
    look = '--look' in argv
    names = [a for a in argv if not a.startswith('--')] or list(EFFECTS)
    for name in names:
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
