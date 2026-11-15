"""주인공 오라(게이지 구간별)와 오버로드 폭발을 코드로 그려 codeart2d 스킬로 검사·렌더링해 assets/effects/ 에 묶는다.

오라는 **캐릭터 실루엣을 따라 일렁이는 큰 기운**이다 (드래곤볼의 기, 던그리드·데드셀 류 화염 오라처럼 몸 윤곽에서 불꽃 혀가 위로
피어오르는 모양). 발밑 링이나 먼지 몇 개가 아니라 다음 방식으로 만든다:
  1. 주인공 스프라이트(n09_idle.png)의 알파를 실루엣 마스크로 쓴다. 위로 번지게 늘린 마스크까지의 거리장을 구한다.
  2. 위로 흘러 올라가는 주기적 노이즈(fBm)로 반지름을 일렁이게 해서 가는 끝을 가진 **불꽃 혀**를 만든다 (시간이 한 바퀴 돌면
     노이즈가 정확히 한 주기 이동하므로 반복이 매끄럽게 닫힌다).
  3. 세기를 4톤 + 베이어 디더링으로 양자화해 도트 질감을 낸다. 몸 가까이는 밝은 림 라이트, 바깥은 어두운 끝.
  4. 불씨 입자가 위로 떠올라 사라진다. 발밑에는 납작한 지면 광채.
구간마다 모양이 다르다 (docs/기획서.md 5.12):
  aura-fade      페이드(1~19%): 작고 흐릿한 적갈색 기운이 **몸으로 빨려 들어가듯** 아래로 흩어짐
  aura-awake     각성(50~89%): 청록 불꽃이 몸을 감싸고 머리 위로 피어오름
  aura-critical  위험(90~99%): 크고 거센 주황 화염, 흩날리는 불씨, 발밑 지면 광채
  aura-enhanced  E 강화 준비: 보라색 기운이 소용돌이치며 **몸으로 모여든다**
  aura-stun      오버로드 기절: 몸 윤곽을 감싸며 튀는 **전기 아크**와 머리 위를 도는 별 (반복)
  overload-burst 오버로드 폭발 한 번 (codeart2d fx_build, 화면을 가로지르는 큰 충격 링)
노멀(20~49%)은 오라가 없다. 오라는 반복(loop) 재생이며 발 아래 중앙이 기준점(pivot)이다.

그림은 PixelSpec(codeart2d.pixelspec.v1)으로 만들어 스킬의 render_pixelspec.py에 넣는다: 팔레트 정확성(알파 0/255, 팔레트 밖 색 0)을
스킬이 검사한다(--strict-qc). 이미지 모델 없이 코드로 그린 에셋이다 (문서에 code-drawn으로 표기).
참고 방향: 픽셀 아트 화염 오라 에셋팩들(OpenGameArt fire aura 128x128 14프레임 반복, 에너지 오라 56x56 팩)의 크기·프레임 수와
"몸 윤곽에서 위로 번지는 불꽃" 구성을 참고했다. 도면을 옮긴 것은 없다.

사용: python tools/make_aura.py [이름 ...]
"""
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "effects"
SPRITE = ROOT / "assets" / "sprites" / "unified" / "n09_idle.png"
SKILL_CANDIDATES = [Path.home() / ".claude" / "skills" / "codeart2d", Path.home() / ".codex" / "skills" / "codeart2d"]
SKILL = next((p for p in SKILL_CANDIDATES if (p / "scripts" / "render_pixelspec.py").exists()), SKILL_CANDIDATES[0])

W, H = 240, 320            # 오라 캔버스(1배). 캐릭터는 42x125라 사방으로 큼직하게 번진다
FEET = 296                 # 발 아래 모서리 줄 (아래 여유는 지면 광채)
CX = W // 2
FRAMES = 16
PERIOD_MS = 800
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


# ----- 노이즈 -----
def _table(seed, rows, cols):
    return np.random.default_rng(seed).random((rows, cols))


def vnoise(xs, ys, cell, rows, seed, scroll, stretch=1.0):
    """y 방향으로 rows칸 주기인 값 노이즈. scroll(칸)만큼 위로 흘러간다. rows칸 이동하면 정확히 같은 모양이 된다."""
    tbl = _table(seed, rows, 64)
    gx = xs / (cell / stretch)                 # stretch > 1이면 가로를 촘촘하게 = 세로로 긴 줄기(불꽃 혀)
    gy = ys / (cell * stretch) + scroll
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0, gy - y0
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def at(ix, iy):
        return tbl[iy % rows, ix % 64]
    top = at(x0, y0) * (1 - sx) + at(x0 + 1, y0) * sx
    bot = at(x0, y0 + 1) * (1 - sx) + at(x0 + 1, y0 + 1) * sx
    return top * (1 - sy) + bot * sy


def fbm(xs, ys, t, seed, rising=1, stretch=1.0):
    """세 옥타브. 한 바퀴(t=1)에 각 옥타브가 자기 주기(rows칸)를 정수 번 이동한다. rising이 -1이면 아래로 흘러간다."""
    total, weight, norm = 0.0, 0.5, 0.0
    for octave, (cell, rows, wraps) in enumerate(((46, 8, 1), (23, 8, 2), (11.5, 8, 4))):
        total += weight * vnoise(xs, ys, cell, rows, seed + octave, rising * t * rows * wraps, stretch)
        norm += weight
        weight *= 0.55
    return total / norm


# ----- 실루엣 -----
def silhouette_mask():
    im = Image.open(SPRITE).convert("RGBA")
    mask = np.zeros((H, W), dtype=bool)
    a = np.array(im)[:, :, 3] > 0
    h, w = a.shape
    mask[FEET - h + 2:FEET + 2, CX - w // 2:CX - w // 2 + w] = a        # 스프라이트 아래 여백 1~2px를 발 줄에 맞춘다
    return mask


def smear_up(mask, k, step=2):
    """실루엣을 위로 k픽셀까지 늘린 마스크 (불꽃이 머리 위로 피어오르는 길)."""
    out = mask.copy()
    for s in range(step, k + 1, step):
        out[:-s] |= mask[s:]
    return out


# ----- 구간별 설정 -----
# ramp: 밝음 -> 어두움 4톤, ember: 불씨 색. r0: 몸 둘레 기본 반지름(px), smear: 위로 번지는 길이(px)
STYLES = {
    "aura-fade": dict(kind="flame", ramp=["#d7bccb", "#9d6a80", "#6a3f55", "#3a2233"], ember="#d7bccb", r0=24, vscale=0.8, stretch=1.6,
                      amp=0.8, bias=0.1, rising=-1, embers=10, ember_rise=-46, ember_size=1, ground=0.5, gain=1.0, seed=11),
    "aura-awake": dict(kind="flame", ramp=["#f4fff9", "#a2f7d2", "#3fd6a4", "#1f8a78"], ember="#f4fff9", r0=26, vscale=0.42, stretch=2.4,
                       amp=0.95, bias=0.45, rising=1, embers=16, ember_rise=120, ember_size=1, ground=0.7, gain=1.0, seed=23),
    "aura-critical": dict(kind="flame", ramp=["#fff4d6", "#ffb347", "#ff5a2e", "#a3262a"], ember="#ffe9a8", r0=30, vscale=0.52, stretch=2.6,
                          amp=1.15, bias=0.7, rising=1, embers=34, ember_rise=170, ember_size=2, ground=1.0, gain=1.15, seed=37),
    "aura-enhanced": dict(kind="spiral", ramp=["#ffffff", "#e6ccff", "#a46bff", "#5a2fb8"], ember="#ffffff", r0=40, vscale=0.62, stretch=1.5,
                          amp=0.9, bias=0.35, rising=1, embers=26, ember_rise=-110, ember_size=1, ground=0.6, gain=1.15, seed=51),
}
STYLES["aura-stun"] = dict(kind="crackle", ramp=["#ffffff", "#fff6a8", "#ffd34a", "#b8741a"], ember="#fff6a8", r0=34, vscale=0.9,
                           stretch=1.0, amp=1.0, bias=0.2, rising=1, embers=0, ember_rise=0, ember_size=1, ground=0.4, gain=1.0,
                           seed=63)
PALETTE_CHARS = "abcd"      # 4톤. 불씨는 e


def draw_frame(cfg, mask, d, frame):
    """한 프레임의 팔레트 인덱스 배열 (0 투명, 1~4 톤, 5 불씨)."""
    t = frame / FRAMES
    ys, xs = np.mgrid[0:H, 0:W].astype(float)
    n = fbm(xs, ys, t, cfg["seed"], cfg["rising"], cfg["stretch"])
    height = np.clip((FEET - ys) / 125.0, 0, 1.6)                       # 발 위 높이(몸 키 단위)
    radius = cfg["r0"] * (0.25 + cfg["amp"] * n * n * 2.2) * (0.7 + cfg["bias"] * height)     # 노이즈를 제곱해 혀와 틈이 뚜렷하게
    a = np.clip(1.0 - d / np.maximum(radius, 1e-3), 0, 1) ** 1.25
    if cfg["kind"] == "spiral":                                          # 몸으로 모여드는 소용돌이 줄기
        yc = FEET - 62
        theta = np.arctan2((ys - yc) * 0.8, xs - CX)
        r = np.hypot(xs - CX, (ys - yc) * 0.8)
        streak = 0.5 + 0.5 * np.sin(5 * theta + r * 0.09 + 2 * math.pi * t * 2)      # r이 클수록 위상이 앞서 안쪽으로 흐른다
        a = a * (0.12 + 1.2 * streak ** 1.5)                              # 줄기가 뚜렷하게 보이도록 대비를 키운다
        a = np.maximum(a, np.clip(1.0 - d / (cfg["r0"] * 0.32), 0, 1) * 0.7)           # 몸 가까이는 은은한 림 라이트
    if cfg["kind"] == "crackle":
        return draw_crackle(cfg, mask, d, frame, xs, ys)
    a = np.clip(a * cfg["gain"], 0, 1)
    dither = (BAYER[ys.astype(int) % 4, xs.astype(int) % 4] - 0.5) * 0.16
    v = a + dither * (a > 0)
    tone = np.zeros((H, W), dtype=np.uint8)
    tone[(a > 0.02) & (v > 0.04)] = 4
    tone[v > 0.2] = 3
    tone[v > 0.46] = 2
    tone[v > 0.78] = 1
    tone[mask] = 0                                                        # 몸 안쪽은 비운다 (스프라이트가 위에 그려진다)
    # 지면 광채: 발밑의 납작한 타원
    gy = (ys - (FEET + 1)) / 9.0
    gx = (xs - CX) / (42 + 40 * cfg["ground"])
    ground = np.clip(1.0 - (gx * gx + gy * gy), 0, 1) * cfg["ground"]
    gt = (ground + dither * (ground > 0)) > 0.34
    tone[gt & (tone == 0)] = 3
    tone[(ground + dither) > 0.7] = 2
    # 불씨: 위(또는 아래)로 떠오르며 사라진다. 한 바퀴에 한 번 올라가고 80%만 보여서 다시 시작하는 순간이 안 보인다
    rng = np.random.default_rng(cfg["seed"] * 7)
    for i in range(cfg["embers"]):
        ex = CX + rng.normal(0, 34)
        ey = FEET - rng.uniform(8, 120)
        phase = rng.random()
        prog = (t + phase) % 1.0
        if prog > 0.8:
            continue
        px = int(round(ex + 6 * math.sin(2 * math.pi * (prog + phase) * 1.5 + i)))
        py = int(round(ey - cfg["ember_rise"] * prog))
        size = cfg["ember_size"] if prog < 0.55 else 1
        if 0 <= px < W - size and 0 <= py < H - size and not mask[py, px]:
            tone[py:py + size, px:px + size] = 5
    return tone


def draw_crackle(cfg, mask, d, frame, xs, ys):
    """기절 오라: 몸 윤곽 둘레를 따라 튀는 전기 아크(가는 번개선)와 머리 위를 도는 별. 프레임마다 번개가 다른 자리로 튄다."""
    t = frame / FRAMES
    tone = np.zeros((H, W), dtype=np.uint8)
    halo = np.clip(1.0 - d / cfg["r0"], 0, 1)
    for k, (seed_off, width) in enumerate(((0, 0.011), (97, 0.008))):          # 두 가닥의 아크
        n = fbm(xs, ys, t, cfg["seed"] + seed_off + 5 * (frame % 4), 1, 1.0)     # 4프레임마다 같은 번개 모양이 돌아와 반복이 닫힌다
        ridge = np.abs(n - 0.5)                                               # 0.5 등고선을 따라 가는 선이 생긴다
        line = (ridge < width) & (halo > 0.05 + 0.1 * k)
        glow = (ridge < width * 2.8) & (halo > 0.15)
        tone[glow & (tone == 0)] = 3
        tone[line] = 1 if k == 0 else 2
    # 몸에 달라붙은 깜빡이는 전기 광채
    flick = 0.5 + 0.5 * math.sin(2 * math.pi * t * 4)
    rim = (d < 3.5) & (halo > 0.8) & (flick > 0.35)
    tone[rim & (tone == 0)] = 2
    tone[mask] = 0
    # 머리 위를 도는 별 네 개 (뒤쪽 별은 작고 어둡다: 타원 궤도로 입체감)
    head_top = FEET - 125
    cy = head_top - 12
    for k in range(4):
        ang = 2 * math.pi * (t + k / 4)
        sx = int(round(CX + 48 * math.cos(ang)))
        sy = int(round(cy + 11 * math.sin(ang)))
        front = math.sin(ang) > 0
        arm = 6 if front else 3                                         # 앞쪽 별은 크고 밝고, 뒤쪽 별은 작고 어둡다
        for i in range(-arm, arm + 1):
            for (ox, oy) in ((i, 0), (0, i)):
                tone[sy + oy, sx + ox] = 2 if abs(i) > 1 else 1
        if front:
            for i in range(-3, 4):                                      # 대각 짧은 팔: 반짝이는 4각 별
                if abs(i) > 0:
                    tone[sy + i, sx + i] = 3
                    tone[sy + i, sx - i] = 3
            tone[sy - 1:sy + 2, sx - 1:sx + 2] = 1
    # 지면의 번쩍임
    gy = (ys - (FEET + 1)) / 8.0
    gx = (xs - CX) / 70.0
    ground = np.clip(1.0 - (gx * gx + gy * gy), 0, 1)
    tone[(ground > 0.45 + 0.25 * flick) & (tone == 0)] = 3
    return tone


def to_segments(tone):
    """팔레트 인덱스 배열을 PixelSpec 세그먼트(줄마다 '13.6a13.' 형식)로 바꾼다."""
    chars = ".abcde"
    rows = []
    for row in tone:
        out, run, cur = [], 0, None
        for v in row:
            if v == cur:
                run += 1
                continue
            if cur is not None:
                out.append((f"{run}" if run > 1 else "") + chars[cur])
            cur, run = v, 1
        out.append((f"{run}" if run > 1 else "") + chars[cur])
        rows.append("".join(out))
    return rows


def make_spec(name, cfg, frames):
    palette = {c: col for c, col in zip(PALETTE_CHARS, cfg["ramp"])}
    palette["e"] = cfg["ember"]
    layers = [{"name": "aura", "origin": [0, 0], "segments": to_segments(frames[0])}]
    fl = [{"name": f"f{i:02d}", "layers": {"aura": {"segments": to_segments(f)}}} for i, f in enumerate(frames)]
    return {"schema": "codeart2d.pixelspec.v1", "name": name, "canvas": [W, H], "anchor_px": [CX, FEET],
            "palette": palette, "layers": layers, "frames": fl}


def run_skill(script, args, tmp):
    cmd = [sys.executable, str(SKILL / "scripts" / script), *args]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})
    if result.returncode != 0:
        sys.exit(f"{script}: " + result.stdout + result.stderr)
    return result.stdout


def pack(name, frames, size, pivot, loop, fps, scale=1):
    cols = min(len(frames), 8)
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (size[0] * cols, size[1] * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % cols) * size[0], (i // cols) * size[1]))
    sheet.save(OUT / f"{name}.png")
    meta = {"id": f"aura/{name}", "frames": len(frames), "frameSize": list(size), "columns": cols, "fps": fps,
            "loop": loop, "pivot": list(pivot), "scale": scale,
            "source": "tools/make_aura.py (code-drawn, codeart2d render QA, no image model)"}
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print("saved", name, sheet.size, len(frames), "frames")


def build_aura(name):
    cfg = STYLES[name]
    mask = silhouette_mask()
    d = ndimage.distance_transform_edt(~mask, sampling=(cfg["vscale"], 1.0))     # 세로 거리를 줄여 불꽃이 위아래로 길게 닿는다
    frames = [draw_frame(cfg, mask, d, i) for i in range(FRAMES)]
    spec = make_spec(name, cfg, frames)
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / f"{name}.pixelspec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        out = Path(tmp) / "out"
        run_skill("render_pixelspec.py", ["--spec", str(spec_path), "--output-dir", str(out), "--strict-qc"], tmp)
        files = sorted(out.rglob("f*.png"))
        images = [Image.open(f).convert("RGBA") for f in files]
    assert len(images) == FRAMES, f"프레임 수가 다르다: {len(images)} (같은 프레임은 한 번만 저장되므로 디자인을 확인)"
    pack(name, images, (W, H), (CX, FEET), True, round(1000 / (PERIOD_MS / FRAMES)))


# ----- 오버로드 폭발 (fx_build) -----
BURST = dict(size=460, palette={"a": "#ffffff", "b": "#fff1a6", "c": "#ffb347", "d": "#ff5a2e"})
INK = "#0b1020"


def build_burst():
    size = BURST["size"]
    c = size / 2
    spec = {"schema": "codeart2d.fx.v1", "canvas": [size, size], "origin": [c, c], "palette": {**BURST["palette"], "ink": INK},
            "effects": [{"id": "b", "durationMs": 600, "impactMs": 0, "frameMs": 40, "seed": 9, "outline": "ink",
                         "primitives": [
                             {"type": "ring", "colors": ["a", "b", "c", "d"], "origin": [c, c], "lifeMs": 520,
                              "radius": [20, 214], "width": [28, 2]},
                             {"type": "flash", "colors": ["a", "b", "c"], "origin": [c, c], "lifeMs": 260, "radius": 46,
                              "rays": 8, "rayLength": 190},
                             {"type": "sparks", "colors": ["a", "b", "c"], "origin": [c, c], "count": 30, "spread": 360,
                              "speed": 420, "lifeMs": 480, "length": 20, "width": 3}]}]}
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / "spec.fx.json"
        spec_path.write_text(json.dumps(spec, indent=1), encoding="utf-8")
        out = Path(tmp) / "out"
        run_skill("fx_build.py", ["--spec", str(spec_path), "--output-dir", str(out), "--route", "pixel", "--strict-qc"], tmp)
        frames = [Image.open(f).convert("RGBA") for f in sorted((out / "frames").glob("b-*.png"))]
    pack("overload-burst", frames, (size, size), (size // 2, size // 2), False, 25, scale=2)   # 정수 2배: 화면을 가로지르는 충격 링


def main():
    if not (SKILL / "scripts" / "render_pixelspec.py").exists():
        sys.exit(f"codeart2d 스킬이 없습니다: {SKILL} (docs/SETUP.md의 agent-sprite-forge 설치 참고)")
    wanted = sys.argv[1:] or [*STYLES, "overload-burst"]
    for name in wanted:
        if name == "overload-burst":
            build_burst()
        else:
            build_aura(name)


if __name__ == "__main__":
    main()
