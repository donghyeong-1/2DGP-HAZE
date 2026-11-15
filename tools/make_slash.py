"""공격 이펙트를 codeart2d 스킬의 fx.v1 경로로 만들어 assets/effects/ 에 시트로 묶는다.

실행 중에는 회전할 수 없으므로(docs/pixel_rules.md 5번) 방향이 있는 효과는 5방향(오른쪽, 오른쪽 위, 위, 오른쪽 아래, 아래)을
미리 돌려 그리고, 왼쪽은 좌우 반전으로 쓴다. 방향 없는 효과(회전 베기)는 한 줄이다.

게이지 구간과 강화는 **색만 다른 것이 아니라 모양이 다르다** (docs/기획서.md 5.12):
  pipe-slash            노멀    초승달 한 줄기 (청백)
  pipe-slash-fade       페이드  가늘고 짧은 반달 하나, 불꽃 없음 (힘이 빠진 느낌, 어두운 적갈색)
  pipe-slash-awake      각성    겹친 두 줄기(바깥·안쪽 시차) + 끝에서 퍼지는 링 (청록)
  pipe-slash-critical   위험    세 겹 + 끝의 섬광과 충격 링 + 흩날리는 불씨 (주황)
  pipe-slash-finisher   3타     금색 큰 한 줄기 + 끝의 링
  pipe-slash-enhanced   강화    엇갈린 X자 두 줄기 + 몸 둘레 충격 링 + 큰 섬광 (보라, 강화 일격 1회)
  dash-strike           대시 평타  앞으로 길게 뻗는 돌진 베기 (두 줄기 + 뒤로 흐르는 속도선)
  air-spin              점프 평타  몸 둘레 한 바퀴 회전 베기 (두 겹 원)
  air-spin-enhanced     강화된 점프 평타  더 큰 보라색 회전 베기
(대시 평타는 시트가 아니라 지나온 경로를 훑는 직선이라 effects.PathSlash가 코드로 그린다)

그리기는 codeart2d 스킬의 fx_build.py가 하고, 이 스크립트는 스펙을 만들어 호출한 뒤 프레임을 시트로 묶는다. 팔레트 정확성과
"궤적이 충격 프레임에서 끝난다"는 스킬의 QA가 보장한다. 이미지 모델 없이 코드로 그린 에셋이다 (문서에 code-drawn으로 표기).

사용: python tools/make_slash.py [시트 이름 ...]   (굽는 데 몇 분 걸린다)
필요: ~/.claude/skills/codeart2d (docs/SETUP.md의 agent-sprite-forge 설치)
"""
import json
import math
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

SWEEP = 65.0                           # 조준 방향 기준 좌우 각도 (판정 부채꼴과 같다)
VARIANT_AIMS = [0, 45, 90, -45, -90]   # 조준 각도(도, 동쪽 0, 북쪽 90, 반시계). 시트의 줄 순서
INK = "#0b1020"                        # 캐릭터 외곽선과 같은 색
DURATION_MS, IMPACT_MS, FRAME_MS = 260, 130, 40

# 시트 이름 -> 설정. style이 모양을 정한다.
SHEETS = {
    "pipe-slash": dict(style="standard", size=380, radius=118, width=84, ramp=["#ffffff", "#cdf0ff", "#78d2eb", "#3c8cb4"],
                       sparks=["#ffffff", "#cdf0ff", "#78d2eb"], sparks_count=7),
    "pipe-slash-fade": dict(style="thin", size=340, radius=100, width=44, ramp=["#d9b4c4", "#a8657f", "#7a3a52", "#4a2238"],
                            sparks=["#d9b4c4", "#a8657f", "#7a3a52"], sparks_count=0),
    "pipe-slash-awake": dict(style="double", size=440, radius=134, width=84, ramp=["#f4fff9", "#a2f7d2", "#3fd6a4", "#1f8a78"],
                             sparks=["#f4fff9", "#a2f7d2", "#3fd6a4"], sparks_count=9),
    "pipe-slash-critical": dict(style="triple", size=500, radius=160, width=84, ramp=["#fff4d6", "#ffb347", "#ff5a2e", "#a3262a"],
                                sparks=["#fff4d6", "#ffb347", "#ff5a2e"], sparks_count=16),
    "pipe-slash-finisher": dict(style="finisher", size=440, radius=146, width=100, ramp=["#fffbe8", "#ffe08c", "#ff9a4a", "#b8502e"],
                                sparks=["#fffbe8", "#ffe08c", "#ff9a4a"], sparks_count=10),
    "pipe-slash-enhanced": dict(style="cross", size=560, radius=190, width=100, ramp=["#ffffff", "#e6ccff", "#a46bff", "#5a2fb8"],
                                sparks=["#ffffff", "#e6ccff", "#a46bff"], sparks_count=14),
    "dash-strike": dict(style="dash", size=620, radius=250, width=76, ramp=["#ffffff", "#fff1b8", "#ffd35a", "#c98a1e"],
                        sparks=["#ffffff", "#fff1b8", "#ffd35a"], sparks_count=10),
    "air-spin-enhanced": dict(style="spin", size=580, radius=176, width=96, ramp=["#ffffff", "#e6ccff", "#a46bff", "#5a2fb8"],
                              sparks=["#ffffff", "#e6ccff", "#a46bff"], sparks_count=16, aims=[0]),
    "air-spin": dict(style="spin", size=420, radius=124, width=66, ramp=["#ffffff", "#d6f3ff", "#8fd6ff", "#4a8fd0"],
                     sparks=["#ffffff", "#d6f3ff", "#8fd6ff"], sparks_count=10, aims=[0]),
}


def screen_angle(aim_deg):
    """게임 각도(반시계, 북쪽 +)를 스킬의 화면 각도(시계, 아래쪽 +)로 바꾼다."""
    return -aim_deg


def point(c, radius, deg):
    return [round(c + radius * math.cos(math.radians(deg)), 1), round(c + radius * math.sin(math.radians(deg)), 1)]


def slash(c, radius, start, end, width, start_ms=0, trail=1.0, ramp="blade"):
    p = {"type": "slash", "ramp": ramp, "center": [c, c], "radius": radius, "from": start, "to": end,
         "width": width, "trail": trail}
    if start_ms:
        p["startMs"] = start_ms
    return p


def sparks(origin, count, angle, spread, speed, life, length, gravity=0, ramp="spark"):
    return {"type": "sparks", "ramp": ramp, "origin": origin, "count": count, "angle": angle, "spread": spread,
            "speed": speed, "lifeMs": life, "length": length, "width": 2, "gravity": gravity}


def ring(origin, radius, width, life, squash=1.0, ramp="blade"):
    return {"type": "ring", "ramp": ramp, "origin": origin, "atMs": IMPACT_MS, "lifeMs": life, "radius": radius,
            "width": width, "squash": squash}


def flash(origin, radius, rays, ray_length, life=170, ramp="spark"):
    return {"type": "flash", "ramp": ramp, "origin": origin, "atMs": IMPACT_MS, "radius": radius, "rays": rays,
            "rayLength": ray_length, "lifeMs": life}


def primitives(cfg, aim):
    """스타일에 따라 한 방향의 프리미티브 목록을 만든다. 모양이 스타일마다 다르다."""
    size, R, W, style = cfg["size"], cfg["radius"], cfg["width"], cfg["style"]
    c = size / 2
    sa = screen_angle(aim)
    start, end = sa - SWEEP, sa + SWEEP          # 시계 방향으로 휘둘러 위쪽에서 아래쪽으로 내려간다
    tip = point(c, R, end)
    n = cfg["sparks_count"]
    spark = (lambda count=n: [sparks(tip, count, end + 90, 100, size * 0.9, 120, size * 0.07)]) if n else (lambda count=0: [])

    if style == "standard":
        return [slash(c, R, start, end, W)] + spark()
    if style == "thin":                           # 페이드: 짧고 가늘다. 불꽃도 없다
        return [slash(c, R, sa - 40, sa + 40, W, trail=0.45)]
    if style == "double":                         # 각성: 바깥 줄기와 안쪽 줄기가 시차로 겹치고 끝에서 링이 퍼진다
        return [slash(c, R, start, end, W),
                slash(c, R * 0.7, start + 12, end - 6, W * 0.62, start_ms=30)] + [
                ring(tip, [4, size * 0.1], [10, 1], 240)] + spark()
    if style == "triple":                         # 위험: 세 겹, 끝의 섬광과 충격 링, 흩날리는 불씨
        return [slash(c, R, start, end, W),
                slash(c, R * 0.78, start + 8, end - 4, W * 0.7, start_ms=25),
                slash(c, R * 0.58, start + 16, end - 8, W * 0.5, start_ms=50),
                flash(tip, size * 0.03, 6, size * 0.16),
                ring(tip, [6, size * 0.16], [14, 1], 300)] + [sparks(tip, n, end + 90, 160, size * 0.8, 260, size * 0.06, gravity=420)]
    if style == "finisher":                       # 3타: 금색 큰 줄기와 끝의 링
        return [slash(c, R, start, end, W), ring(tip, [6, size * 0.14], [16, 1], 280)] + spark()
    if style == "cross":                          # 강화 일격: 엇갈린 X자 두 줄기, 몸 둘레 충격 링, 큰 섬광
        return [slash(c, R, start, end, W),
                slash(c, R * 0.92, end, start, W * 0.8, start_ms=25),
                ring([c, c], [size * 0.06, size * 0.4], [22, 2], 320),
                flash(tip, size * 0.03, 8, size * 0.13, life=210)] + spark()
    if style == "dash":                           # 대시 평타: 앞으로 길게 뻗는 돌진 베기, 뒤로 흐르는 속도선
        return [slash(c, R, sa - 34, sa + 34, W, trail=1.0),
                slash(c, R * 0.86, sa - 26, sa + 26, W * 0.55, start_ms=20),
                sparks([c, c], 8, sa + 180, 30, size * 1.4, 160, size * 0.1)] + spark()
    if style == "spin":                           # 점프 평타: 몸 둘레를 한 바퀴 도는 두 겹 원
        return [slash(c, R, -200, 160, W),
                slash(c, R * 0.72, -20, 340, W * 0.62, start_ms=30),
                ring([c, c], [size * 0.1, size * 0.4], [14, 1], 260)] + [sparks([c, c], n, 0, 360, size * 0.8, 160, size * 0.07)]
    raise ValueError(style)


def make_spec(cfg):
    size = cfg["size"]
    c = size / 2
    palette = {f"r{i}": col for i, col in enumerate(cfg["ramp"])}
    palette["ink"] = INK
    for i, col in enumerate(cfg["sparks"]):
        palette.setdefault(f"s{i}", col)
    effects = []
    for vi, aim in enumerate(cfg.get("aims", VARIANT_AIMS)):
        effects.append({
            "id": f"v{vi}", "durationMs": DURATION_MS, "impactMs": IMPACT_MS, "frameMs": FRAME_MS, "seed": 11 + vi,
            "outline": "ink",
            "ramps": {"blade": [f"r{i}" for i in range(len(cfg["ramp"]))],
                      "spark": [f"s{i}" for i in range(len(cfg["sparks"]))]},
            "primitives": primitives(cfg, aim)})
    return {"schema": "codeart2d.fx.v1", "canvas": [size, size], "origin": [c, c], "palette": palette, "effects": effects}


def build_sheet(name, cfg):
    spec = make_spec(cfg)
    aims = cfg.get("aims", VARIANT_AIMS)
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / f"{name}.fx.json"
        spec_path.write_text(json.dumps(spec, indent=1), encoding="utf-8")
        out = Path(tmp) / "out"
        cmd = [sys.executable, str(SKILL / "scripts" / "fx_build.py"), "--spec", str(spec_path), "--output-dir", str(out),
               "--route", "pixel", "--strict-qc"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})
        if result.returncode != 0:
            sys.exit(f"{name}: " + result.stdout + result.stderr)
        rows = []
        for vi in range(len(aims)):
            frames = sorted((out / "frames").glob(f"v{vi}-*.png"))
            rows.append([Image.open(f).convert("RGBA") for f in frames])
    n = max(len(r) for r in rows)
    for r in rows:                       # 방향마다 프레임 수가 같아야 하므로 모자라면 마지막 프레임을 반복한다
        while len(r) < n:
            r.append(r[-1])
    size = cfg["size"]
    sheet = Image.new("RGBA", (size * n, size * len(rows)), (0, 0, 0, 0))
    for vi, frames in enumerate(rows):
        for fi, frame in enumerate(frames):
            sheet.paste(frame, (fi * size, vi * size))
    sheet.save(OUT / f"{name}.png")
    meta = {
        "id": f"melee/{name}", "frames": n * len(rows), "variants": len(rows), "variantAngles": aims,
        "frameSize": [size, size], "columns": n, "fps": round(1000 / FRAME_MS), "loop": False,
        "pivot": [size // 2, size // 2], "scale": 1, "impactMs": IMPACT_MS, "durationMs": DURATION_MS,
        "style": cfg["style"],
        "source": "codeart2d fx_build.py (code-drawn, no image model), tools/make_slash.py",
    }
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print("saved", name, sheet.size, "frames/variant", n)


def main():
    if not (SKILL / "scripts" / "fx_build.py").exists():
        sys.exit(f"codeart2d 스킬이 없습니다: {SKILL} (docs/SETUP.md의 agent-sprite-forge 설치 참고)")
    wanted = sys.argv[1:] or list(SHEETS)       # 이름을 주면 그것만 굽는다 (예: python tools/make_slash.py air-spin)
    for name in wanted:
        build_sheet(name, SHEETS[name])


if __name__ == "__main__":
    main()
