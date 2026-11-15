"""주인공 주변 오라(게이지 구간별)와 오버로드 폭발을 codeart2d 스킬의 fx.v1 경로로 만들어 assets/effects/ 에 묶는다.

게이지 구간마다 주인공 **몸 한가운데에서 기운이 흘러나오는** 모양이 다르다 (docs/기획서.md 5.12). 발밑에 깔리는 링이 아니라
몸을 중심으로 사방으로 뻗는 기운, 위로 솟는 불꽃, 안으로 빨려 드는 기운이다.
  aura-fade      페이드(1~19%): 몸에서 기운이 힘없이 **빨려 나간다**(바깥에서 안으로 흩어지는 어두운 줄기)
  aura-awake     각성(50~89%): 몸 중심의 별빛이 맥동하며 **청록 기운이 사방으로 뻗고** 위로 피어오른다
  aura-critical  위험(90~99%): 별빛이 크게 터지며 **주황 기운이 거세게 분출**하고 몸을 따라 불꽃이 솟는다
  aura-enhanced  E 강화 준비: 보라색 기운이 **몸으로 모여든다**(강화 일격 1회를 충전 중)
  overload-burst 오버로드 폭발 한 번 (게이지 100%)
노멀(20~49%)은 오라가 없다. 오라는 반복(loop) 재생이며 발 아래 중앙이 기준점(pivot)이다.

이미지 모델 없이 코드로 그린 에셋이다 (codeart2d 스킬 fx_build.py, 문서에 code-drawn으로 표기).
사용: python tools/make_aura.py [이름 ...]   (굽는 데 몇 분 걸린다)
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "effects"
SKILL_CANDIDATES = [Path.home() / ".claude" / "skills" / "codeart2d", Path.home() / ".codex" / "skills" / "codeart2d"]
SKILL = next((p for p in SKILL_CANDIDATES if (p / "scripts" / "fx_build.py").exists()), SKILL_CANDIDATES[0])

W, H = 380, 440                 # 오라 캔버스. 기준점은 발 아래 중앙. 몸 중심에서 사방으로 뻗는 줄기 여유를 둔다
OX, OY = 190, 306
INK = "#0b1020"
PERIOD = 800                    # 오라 한 바퀴(ms). 두 번 맥동한다
FRAME_MS = 50
BODY = OY - 66                  # 몸 한가운데 (가슴) 높이: 기운이 여기서 흘러나온다
import math


def sparks(colors, origin, at, count, angle, spread, speed, life, length, gravity=0):
    return {"type": "sparks", "colors": colors, "origin": origin, "atMs": at, "count": count, "angle": angle,
            "spread": spread, "speed": speed, "lifeMs": life, "length": length, "width": 2, "gravity": gravity}


def ring(colors, origin, at, radius, width, squash=1.0, life=420):
    return {"type": "ring", "colors": colors, "origin": origin, "atMs": at, "lifeMs": life, "radius": radius,
            "width": width, "squash": squash}


def star(colors, at, radius, rays, ray_length, life=420):
    return {"type": "flash", "colors": colors, "origin": [OX, BODY], "atMs": at, "radius": radius, "rays": rays,
            "rayLength": ray_length, "lifeMs": life}


def inward(colors, count_dirs, dist, at, speed, life, length, per=3):
    """바깥 고리 위에서 몸 중심으로 향하는 줄기들 (기운이 빨려 나가거나 모여드는 모양)."""
    out = []
    for k in range(count_dirs):
        deg = k * 360 / count_dirs + (at / 400) * 20
        o = [round(OX + dist * math.cos(math.radians(deg)), 1), round(BODY + dist * 0.9 * math.sin(math.radians(deg)), 1)]
        out.append(sparks(colors, o, at, per, deg + 180, 14, speed, life, length))
    return out


AURAS = {
    "aura-fade": dict(
        palette={"a": "#c9a3b8", "b": "#8a4a63", "c": "#52293f", "d": "#2c1626"},
        primitives=[
            *inward(["a", "b", "c"], 7, 120, 0, 280, 420, 12), *inward(["a", "b", "c"], 7, 120, 400, 280, 420, 12),
            {"type": "dust", "colors": ["b", "c", "d"], "origin": [OX, BODY + 30], "count": 5, "spread": 40, "rise": 10,
             "drift": 6, "radius": [3, 6], "lifeMs": 790},
        ]),
    "aura-awake": dict(
        palette={"a": "#f4fff9", "b": "#a2f7d2", "c": "#3fd6a4", "d": "#1f8a78"},
        primitives=[
            star(["a", "b", "c"], 0, 14, 8, 78), star(["a", "b", "c"], 400, 14, 8, 78),
            sparks(["a", "b", "c"], [OX, BODY], 0, 14, 0, 360, 300, 420, 22),
            sparks(["a", "b", "c"], [OX, BODY], 400, 14, 0, 360, 300, 420, 22),
            ring(["b", "c", "d"], [OX, BODY], 0, [20, 130], [5, 1], 1.25),
            ring(["b", "c", "d"], [OX, BODY], 400, [20, 130], [5, 1], 1.25),
            {"type": "dust", "colors": ["a", "b", "c", "d"], "origin": [OX, BODY + 10], "count": 8, "spread": 44, "rise": 110,
             "drift": 8, "radius": [3, 7], "lifeMs": 790},
        ]),
    "aura-critical": dict(
        palette={"a": "#fff4d6", "b": "#ffb347", "c": "#ff5a2e", "d": "#a3262a"},
        primitives=[
            star(["a", "b", "c"], 0, 20, 10, 118), star(["a", "b", "c"], 400, 20, 10, 118),
            sparks(["a", "b", "c"], [OX, BODY], 0, 26, 0, 360, 340, 420, 28),
            sparks(["a", "b", "c"], [OX, BODY], 400, 26, 0, 360, 340, 420, 28),
            ring(["b", "c", "d"], [OX, BODY], 0, [24, 150], [8, 1], 1.2),
            ring(["b", "c", "d"], [OX, BODY], 400, [24, 150], [8, 1], 1.2),
            {"type": "dust", "colors": ["a", "b", "c", "d"], "origin": [OX, OY - 6], "count": 16, "spread": 66, "rise": 215,
             "drift": 16, "radius": [7, 15], "lifeMs": 790},
            sparks(["a", "b"], [OX, BODY - 60], 0, 10, -90, 60, 360, 420, 24),
            sparks(["a", "b"], [OX, BODY - 60], 400, 10, -90, 60, 360, 420, 24),
        ]),
    "aura-enhanced": dict(
        palette={"a": "#ffffff", "b": "#e6ccff", "c": "#a46bff", "d": "#5a2fb8"},
        primitives=[
            *inward(["a", "b", "c"], 9, 150, 0, 380, 420, 16, per=4), *inward(["a", "b", "c"], 9, 150, 400, 380, 420, 16, per=4),
            star(["a", "b", "c"], 0, 10, 6, 46), star(["a", "b", "c"], 400, 10, 6, 46),
            ring(["b", "c", "d"], [OX, BODY], 0, [10, 60], [6, 1], 1.3), ring(["b", "c", "d"], [OX, BODY], 400, [10, 60], [6, 1], 1.3),
        ]),
}

BURST = dict(size=460, palette={"a": "#ffffff", "b": "#fff1a6", "c": "#ffb347", "d": "#ff5a2e"})


def run_fx(spec, tmp):
    spec_path = Path(tmp) / "spec.fx.json"
    spec_path.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    out = Path(tmp) / "out"
    cmd = [sys.executable, str(SKILL / "scripts" / "fx_build.py"), "--spec", str(spec_path), "--output-dir", str(out),
           "--route", "pixel", "--strict-qc"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})
    if result.returncode != 0:
        sys.exit(result.stdout + result.stderr)
    return out


def pack(name, frames, size, pivot, loop, fps):
    cols = min(len(frames), 8)
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (size[0] * cols, size[1] * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % cols) * size[0], (i // cols) * size[1]))
    sheet.save(OUT / f"{name}.png")
    meta = {"id": f"aura/{name}", "frames": len(frames), "frameSize": list(size), "columns": cols, "fps": fps,
            "loop": loop, "pivot": list(pivot), "scale": 1,
            "source": "codeart2d fx_build.py (code-drawn, no image model), tools/make_aura.py"}
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print("saved", name, sheet.size, len(frames), "frames")


def build_aura(name, cfg):
    spec = {"schema": "codeart2d.fx.v1", "canvas": [W, H], "origin": [OX, OY], "palette": {**cfg["palette"], "ink": INK},
            "effects": [{"id": "a", "durationMs": PERIOD, "impactMs": 0, "frameMs": FRAME_MS, "seed": 5, "loop": True,
                         "outline": "ink", "primitives": cfg["primitives"]}]}
    with tempfile.TemporaryDirectory() as tmp:
        out = run_fx(spec, tmp)
        frames = [Image.open(f).convert("RGBA") for f in sorted((out / "frames").glob("a-*.png"))]
    pack(name, frames, (W, H), (OX, OY), True, round(1000 / FRAME_MS))


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
        out = run_fx(spec, tmp)
        frames = [Image.open(f).convert("RGBA") for f in sorted((out / "frames").glob("b-*.png"))]
    pack("overload-burst", frames, (size, size), (size // 2, size // 2), False, 25)


def main():
    if not (SKILL / "scripts" / "fx_build.py").exists():
        sys.exit(f"codeart2d 스킬이 없습니다: {SKILL} (docs/SETUP.md의 agent-sprite-forge 설치 참고)")
    wanted = sys.argv[1:] or [*AURAS, "overload-burst"]
    for name in wanted:
        if name == "overload-burst":
            build_burst()
        else:
            build_aura(name, AURAS[name])


if __name__ == "__main__":
    main()
