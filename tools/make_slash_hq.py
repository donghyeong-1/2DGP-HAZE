"""공격 이펙트(휘두르기 계열)를 코드로 다시 그려 assets/effects/ 의 시트를 덮어쓴다 (고품질판).

이전 판(tools/make_slash.py, fx_build 프리셋)은 부드러운 잎사귀 같은 한 덩어리였다. 이 판은 던그리드·할로우 나이트 같은 게임의
검기를 참고해 다음을 한다:
  * **뾰족한 초승달**: 꼬리와 머리 끝이 가늘게 모이고 가운데가 두껍다. 바깥 가장자리가 가장 밝다.
  * **휘두르는 움직임**: 머리가 빠르게 앞서 나가고(ease-out), 지난 뒤에는 꼬리가 따라잡아 줄어들며 사라진다.
  * **열 색조**: 바깥 가장자리·머리 쪽이 흰 코어, 안쪽으로 갈수록 색이 짙어진다. 4톤 + 베이어 디더링(픽셀 아트).
  * **1px 외곽선**, 보조 속도선(얇은 호), 충격 순간의 섬광·링·불꽃.
  * 190칸 격자에 그리고 **정수 2배**로 키워 쓴다 (다른 픽셀 에셋과 같은 굵기, json의 scale=2).
방향이 있는 효과는 5방향(동, 북동, 북, 남동, 남)을 미리 돌려 그리고, 왼쪽은 좌우 반전으로 쓴다 (실행 중 회전 금지).

게이지 구간·강화는 색뿐 아니라 모양이 다르다 (docs/기획서.md 5.12):
  pipe-slash 노멀(청백 초승달) / -fade 가늘고 짧고 어둡다 / -awake 겹 두 줄기 + 링 / -critical 세 겹 + 섬광 + 불씨
  -finisher 금색 큰 줄기 + 링 / -enhanced 엇갈린 X자 + 몸 둘레 링 + 섬광 / dash-strike 앞으로 뻗는 창 모양
  air-spin 몸 둘레 회전 베기 / air-spin-enhanced 보라색 큰 회전 베기

사용: python tools/make_slash_hq.py [시트 이름 ...]   (이름이 없으면 전부. 이미지 모델 없이 코드로 그린 에셋)
필요: numpy, Pillow
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "effects"

SWEEP = 95.0                             # v7: 65 -> 95 (길게 그어지는 궤적)
THICK = 1.0                              # v7: 두께 배율 1.45 -> 1.0 (가늘고 날카롭게)
AIMS = [0, 45, 90, -45, -90]            # 조준 각도(도, 동 0, 북 90). 시트의 줄 순서 (게임 규칙: 반시계가 +)
FRAMES = 6
FPS = 25
IMPACT_FRAME = 3                         # 이 프레임에서 충격 효과(링·섬광)가 시작한다
INK = (11, 16, 32)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(*cols):
    return [hexrgb(c) for c in cols]


BLUE = ramp("#ffffff", "#e6fffb", "#2ee6d6", "#0b6a74")      # v7 A안: 흰 주 + 고대비 청록 (예전 파스텔 #cdf0ff·#78d2eb·#3c8cb4)
DIM = ramp("#d9b4c4", "#a8657f", "#7a3a52", "#4a2238")
TEAL = ramp("#ffffff", "#e8fff4", "#33e39e", "#0d6b55")      # v7: 각성 (흰 주 + 초록빛 청록)
FIRE = ramp("#fff4d6", "#ffb347", "#ff5a2e", "#a3262a")
GOLD = ramp("#fffbe8", "#ffe08c", "#ff9a4a", "#b8502e")
VIOLET = ramp("#ffffff", "#e6ccff", "#a46bff", "#5a2fb8")
YELLOW = ramp("#ffffff", "#fff1b8", "#ffd35a", "#c98a1e")

# layer: kind arc/lance, r(반지름 격자칸), w(최대 두께), a0/a1(시작·끝 각도, 조준 기준), delay(0~1), rev(역방향), heat(최대 밝기)
SHEETS = {
    "pipe-slash": dict(grid=190, ramp=BLUE, layers=[dict(r=60, w=34), dict(r=44, w=8, a0=-52, a1=48, delay=0.12, heat=0.8)],
                       sparks=7),
    "pipe-slash-fade": dict(grid=170, ramp=DIM, layers=[dict(r=50, w=16, a0=-40, a1=40, heat=0.75)], sparks=0),
    "pipe-slash-awake": dict(grid=220, ramp=TEAL, layers=[dict(r=68, w=36), dict(r=48, w=22, a0=-55, a1=50, delay=0.1),
                                                          dict(r=34, w=6, a0=-48, a1=44, delay=0.2, heat=0.8)],
                             ring=(6, 26, 1), sparks=9),
    "pipe-slash-critical": dict(grid=250, ramp=FIRE, layers=[dict(r=80, w=38), dict(r=62, w=26, a0=-58, a1=54, delay=0.08),
                                                             dict(r=46, w=16, a0=-50, a1=46, delay=0.16),
                                                             dict(r=90, w=5, a0=-40, a1=60, delay=0.04, heat=0.8)],
                                ring=(8, 44, 1), flash=(7, 30), sparks=16, gravity=True),
    "pipe-slash-finisher": dict(grid=220, ramp=GOLD, layers=[dict(r=73, w=38), dict(r=55, w=10, a0=-52, a1=50, delay=0.1, heat=0.85)],
                                ring=(8, 34, 1), sparks=10),
    "pipe-slash-enhanced": dict(grid=280, ramp=VIOLET, layers=[dict(r=95, w=34), dict(r=87, w=26, rev=True, delay=0.1),
                                                               dict(r=70, w=8, a0=-52, a1=50, delay=0.18, heat=0.85)],
                                ring=(14, 88, 2, "center"), flash=(8, 36), sparks=14),
    "dash-strike": dict(grid=310, ramp=YELLOW, kind="lance", layers=[dict(r=125, w=30), dict(r=110, w=12, delay=0.12, heat=0.85)],
                        ring=(6, 30, 1), sparks=10, speed=True),
    "air-spin": dict(grid=210, ramp=BLUE, aims=[0], layers=[dict(r=62, w=30, a0=-200, a1=160),
                                                            dict(r=46, w=16, a0=-20, a1=340, delay=0.1, rev=True)],
                     ring=(8, 78, 1, "center"), sparks=10, spin=True),
    "air-spin-enhanced": dict(grid=290, ramp=VIOLET, aims=[0], layers=[dict(r=88, w=42, a0=-200, a1=160),
                                                                       dict(r=66, w=24, a0=-20, a1=340, delay=0.1, rev=True),
                                                                       dict(r=100, w=6, a0=-200, a1=160, delay=0.05, heat=0.8)],
                              ring=(12, 108, 2, "center"), flash=(8, 40), sparks=16, spin=True),
}


def ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 2.4


def ease_in(p):
    p = min(1.0, max(0.0, p))
    return p ** 1.7


def swing_state(t, delay):
    """t(0~1) 시각에서 머리·꼬리가 지나온 비율(0~1)과 흐려짐(0~1)."""
    tt = t - delay
    head = ease_out(tt / 0.36)
    tail = ease_in((tt - 0.42) / 0.62)
    return head, tail


def layer_heat(X, Y, c, cfg, layer, sa, t, kind):
    """한 겹의 열(heat) 배열(0~1, 없으면 음수)."""
    dx, dy = X - c, Y - c
    r = np.hypot(dx, dy)
    heat = np.full(X.shape, -1.0)
    delay = layer.get("delay", 0.0)
    head_p, tail_p = swing_state(t, delay)
    if head_p <= 0 or tail_p >= head_p - 0.005:
        return heat
    if kind == "arc":
        a0 = layer.get("a0", -SWEEP)
        a1 = layer.get("a1", SWEEP)
        theta = np.degrees(np.arctan2(dy, dx)) - sa
        if layer.get("rev"):
            theta = -theta
        rel = ((theta - a0) % 360.0) + a0
        span = a1 - a0
        head, tail = a0 + span * head_p, a0 + span * tail_p
        inside = (rel >= tail) & (rel <= head)
        u = np.clip((rel - tail) / max(1e-3, head - tail), 0, 1)
        along = r                                   # 호를 따라 두께를 재는 기준 반지름
        axis_off = r - layer["r"]
    else:                                           # lance: 조준 방향으로 곧게 뻗는 창 모양
        ang = math.radians(sa)
        s = dx * math.cos(ang) + dy * math.sin(ang)
        p = -dx * math.sin(ang) + dy * math.cos(ang)
        L = layer["r"]
        head, tail = -L * 0.35 + (L * 1.35) * head_p, -L * 0.35 + (L * 1.35) * tail_p
        inside = (s >= tail) & (s <= head)
        u = np.clip((s - tail) / max(1e-3, head - tail), 0, 1)
        axis_off = p
    taper = (u ** 0.62) * np.sqrt(np.clip(1 - u ** 7, 0, 1))      # 꼬리 가늘게, 머리 끝은 뾰족하게
    h = layer["w"] * THICK * taper * (1.0 - 0.35 * max(0.0, tail_p))       # 꼬리가 따라잡을수록 가늘어진다
    if kind == "arc":
        outer, inner = layer["r"] + h * 0.40, layer["r"] - h * 0.60
        v = (r - inner) / np.maximum(outer - inner, 1e-3)         # 0 안쪽 → 1 바깥 가장자리
        ok = inside & (r >= inner) & (r <= outer) & (h > 0.35)
    else:
        v = (axis_off + h * 0.5) / np.maximum(h, 1e-3)
        ok = inside & (np.abs(axis_off) <= h * 0.5) & (h > 0.35)
        v = 1 - np.abs(v - 0.5) * 2 * 0.0 - np.abs(axis_off) / np.maximum(h * 0.5, 1e-3)   # 중심선이 밝다
    peak = layer.get("heat", 1.0)
    base = 0.62 * np.clip(v, 0, 1) ** 1.2 + 0.5 * u ** 1.8        # v7: 흰 심이 넓게 (바깥 가장자리·머리)
    life = 1.0 - 0.55 * ease_in((t - 0.55) / 0.45)                # 끝으로 갈수록 식는다
    if t < 0.3:
        life *= 1.25                                              # v7: 처음 두 프레임은 하얗게 번쩍
    val = np.clip(base, 0, 1) * peak * life
    heat[ok] = val[ok]
    return heat


CUTS = (0.40, 0.27, 0.14, 0.05)   # v7 A안: 흰색이 넓게 (INARI 흰+진홍처럼 흰 주, 색은 가장자리). 예전 (0.70, 0.46, 0.22, 0.05)
DITHER = 0.0          # v7 (2026-11-23): 점묘 없이 단색 경계 (INARI처럼 깔끔하게). 예전 값 0.16
OUTLINE = False       # v7: 어두운 외곽선 없이 빛나게. 예전 True


def quantize(heat, ramp_cols, bayer_tiled):
    """열 → 4톤 색 (DITHER > 0이면 베이어 디더링). 불투명 마스크와 RGB를 돌려준다."""
    th = heat + bayer_tiled * DITHER
    idx = np.full(heat.shape, -1)
    cut = list(CUTS)                                              # 흰, 밝은, 중간, 짙은
    for i, cv in enumerate(cut):
        idx[(th >= cv) & (idx < 0)] = i
    idx[heat < 0] = -1
    return idx


def draw_extras(img, cfg, c, tip, sa, i, rng):
    """충격 링, 섬광, 불꽃 입자를 그린다 (img: 정수 인덱스 맵이 아닌 RGBA 배열)."""
    cols = cfg["ramp"]
    size = img.shape[0]
    Y, X = np.mgrid[0:size, 0:size]
    k = i - IMPACT_FRAME
    ring = cfg.get("ring")
    if ring and k >= 0:
        r0, r1, wd = ring[0], ring[1], ring[2]
        origin = (c, c) if len(ring) > 3 else tip
        p = min(1.0, (k + 0.5) / 3.0)
        rad = r0 + (r1 - r0) * ease_out(p)
        d = np.hypot(X - origin[0], Y - origin[1])
        m = np.abs(d - rad) <= wd * (1.0 - 0.5 * p) + 0.4
        if k >= 2:                                               # 끝으로 가며 띄엄띄엄 사라진다
            m &= ((X + Y) % 3 != 0)
        img[m] = (*cols[1 if k < 2 else 2], 255)
    flash = cfg.get("flash")
    if flash and 0 <= k <= 1:
        rays, length = flash
        for ri in range(rays):
            ang = math.tau * ri / rays + 0.2 + (0.0 if k == 0 else math.pi / rays)
            ln = length * (1.0 if k == 0 else 0.6) * (1.0 if ri % 2 == 0 else 0.55)
            for s in np.arange(0, ln, 0.6):
                px, py = int(round(tip[0] + math.cos(ang) * s)), int(round(tip[1] + math.sin(ang) * s))
                if 0 <= px < size and 0 <= py < size:
                    img[py, px] = (*cols[0 if s < ln * 0.55 else 1], 255)
        d = np.hypot(X - tip[0], Y - tip[1])
        img[d <= 4.5 - 2.5 * k] = (*cols[0], 255)
    n = cfg.get("sparks", 0)
    if n and k >= -1:
        for pi in range(n):
            ang = rng[pi][0]
            speed = rng[pi][1]
            tt = max(0.0, (k + 1.0) / 3.0)
            dist = speed * ease_out(tt)
            gx = 0.0
            gy = 26.0 * tt * tt if cfg.get("gravity") else 0.0
            ox, oy = (c, c) if cfg.get("spin") else tip
            px = ox + math.cos(ang) * dist + gx
            py = oy + math.sin(ang) * dist + gy
            if tt >= 1.0:
                continue
            ln = max(1, int(round(3 * (1 - tt))))
            for s in range(ln):
                qx, qy = int(round(px - math.cos(ang) * s)), int(round(py - math.sin(ang) * s))
                if 0 <= qx < size and 0 <= qy < size:
                    img[qy, qx] = (*cols[0 if tt < 0.5 else 1], 255)


def draw_speed_lines(img, cfg, c, sa, t):
    """대시 평타: 몸 뒤로 흐르는 속도선."""
    cols = cfg["ramp"]
    size = img.shape[0]
    ang = math.radians(sa + 180)
    px_dir = (-math.sin(ang), math.cos(ang))
    for j, off in enumerate((-18, -9, 0, 9, 18)):
        start = 22 + (j * 13) % 40 + 40 * t
        ln = 26 + (j * 7) % 18
        for s in np.arange(start, start + ln, 1.0):
            x = c + math.cos(ang) * s + px_dir[0] * off
            y = c + math.sin(ang) * s + px_dir[1] * off
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < size and 0 <= yi < size:
                img[yi, xi] = (*cols[1], 255)


def frame_image(name, cfg, aim, i):
    size = cfg["grid"]
    c = size / 2.0
    sa = -aim                                                    # 게임 각도(반시계) → 화면 각도(시계)
    kind = cfg.get("kind", "arc")
    t = (i + 0.35) / (FRAMES - 0.5)
    Y, X = np.mgrid[0:size, 0:size]
    bayer = np.tile(BAYER, (size // 4 + 1, size // 4 + 1))[:size, :size]
    cols = cfg["ramp"]
    img = np.zeros((size, size, 4), dtype=np.uint8)
    for layer in cfg["layers"]:
        heat = layer_heat(X, Y, c, cfg, layer, sa, t, kind)
        idx = quantize(heat, cols, bayer)
        for tone in range(4):
            m = idx == tone
            img[m] = (*cols[tone], 255)
        mask = idx >= 0
        if not OUTLINE:
            continue
        # 이 겹의 1px 외곽선 (기존 그림 위에는 그리지 않는다)
        pad = np.pad(mask, 1)
        ring = (pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]) & ~mask & (img[:, :, 3] == 0)
        img[ring] = (*INK, 255)
    end_rel = cfg["layers"][0].get("a1", SWEEP)
    tip_ang = math.radians(sa + end_rel) if kind == "arc" else math.radians(sa)
    tr = cfg["layers"][0]["r"] * (1.0 if kind == "arc" else 1.0)
    tip = (c + tr * math.cos(tip_ang), c + tr * math.sin(tip_ang))
    if cfg.get("spin"):
        tip = (c + tr * math.cos(math.radians(sa)), c + tr * math.sin(math.radians(sa)))
    rnd = np.random.RandomState(7 + i * 0)
    n = cfg.get("sparks", 0)
    spark_spec = []
    for pi in range(n):
        base = (tip_ang + math.pi / 2 if kind == "arc" and not cfg.get("spin") else 0.0)
        spread = math.radians(100) if kind == "arc" and not cfg.get("spin") else math.tau
        spark_spec.append((base + (rnd.rand() - 0.5) * spread, size * (0.12 + 0.18 * rnd.rand())))
    if cfg.get("speed"):
        draw_speed_lines(img, cfg, c, sa, t)
    draw_extras(img, cfg, c, tip, sa, i, spark_spec)
    return Image.fromarray(img, "RGBA")


def build(name):
    cfg = SHEETS[name]
    aims = cfg.get("aims", AIMS)
    size = cfg["grid"]
    sheet = Image.new("RGBA", (size * FRAMES, size * len(aims)), (0, 0, 0, 0))
    for vi, aim in enumerate(aims):
        for fi in range(FRAMES):
            sheet.paste(frame_image(name, cfg, aim, fi), (fi * size, vi * size))
    sheet.save(OUT / f"{name}.png")
    meta = {
        "id": f"melee/{name}", "frames": FRAMES * len(aims), "variants": len(aims), "variantAngles": aims,
        "frameSize": [size, size], "columns": FRAMES, "fps": FPS, "loop": False,
        "pivot": [size // 2, size // 2], "scale": 2, "impactMs": 120, "durationMs": 240,
        "source": "tools/make_slash_hq.py (code-drawn, numpy, no image model)",
    }
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print("saved", name, sheet.size)


def main():
    for name in (sys.argv[1:] or list(SHEETS)):
        build(name)


if __name__ == "__main__":
    main()
