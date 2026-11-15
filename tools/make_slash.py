"""방향형 휘두르기 이펙트를 codeart2d 스킬의 fx.v1 경로로 만들어 assets/effects/pipe-slash*.png 로 묶는다.

기존에는 위에서 아래로 찍는 모양 하나뿐이라 위·공중·아래 조준에서 어색했다. 실행 중에는 회전할 수 없으므로(docs/pixel_rules.md 5번)
5방향(오른쪽, 오른쪽 위, 위, 오른쪽 아래, 아래)을 미리 돌려 그리고, 왼쪽은 좌우 반전으로 쓴다.
궤적은 조준 방향 기준 +65도에서 -65도로 휘둘러지며 이는 파이프 판정 부채꼴(config.PIPE_ARC_DEG)과 같다.

그리기는 codeart2d 스킬의 fx_build.py(slash 궤적 + 충격 불꽃)가 하고, 이 스크립트는 방향별 스펙을 만들어 호출한 뒤
프레임을 시트로 묶는다. 팔레트 정확성(alpha 0/255, 팔레트 밖 색 0)과 "궤적이 충격 프레임에서 끝난다"는 스킬의 QA가 보장한다.
이미지 모델 없이 코드로 그린 에셋이다 (문서에 code-drawn으로 표기).

사용: python tools/make_slash.py
필요: ~/.claude/skills/codeart2d (docs/SETUP.md의 agent-sprite-forge 설치)
결과: assets/effects/pipe-slash.png/.json (1~2타), pipe-slash-finisher (3타), pipe-slash-enhanced (E 강화)
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

# 시트 이름 -> (캔버스, 반지름, 굵기, 4톤 램프 밝음->어두움, 충격 불꽃 램프)
SHEETS = {
    "pipe-slash": dict(size=380, radius=118, width=84, ramp=["#ffffff", "#cdf0ff", "#78d2eb", "#3c8cb4"],
                       sparks=["#ffffff", "#cdf0ff", "#78d2eb"], sparks_count=7),
    "pipe-slash-finisher": dict(size=440, radius=146, width=100, ramp=["#fffbe8", "#ffe08c", "#ff9a4a", "#b8502e"],
                                sparks=["#fffbe8", "#ffe08c", "#ff9a4a"], sparks_count=10),
    "pipe-slash-enhanced": dict(size=540, radius=190, width=124, ramp=["#f0ffff", "#8cf8e8", "#3cc8c8", "#1e7896"],
                                sparks=["#f0ffff", "#8cf8e8", "#3cc8c8"], sparks_count=12),
}
DURATION_MS, IMPACT_MS, FRAME_MS = 260, 130, 40


def screen_angle(aim_deg):
    """게임 각도(반시계, 북쪽 +)를 스킬의 화면 각도(시계, 아래쪽 +)로 바꾼다."""
    return -aim_deg


def make_spec(cfg):
    size = cfg["size"]
    c = size / 2
    palette = {f"r{i}": col for i, col in enumerate(cfg["ramp"])}
    palette["ink"] = INK
    for i, col in enumerate(cfg["sparks"]):
        palette.setdefault(f"s{i}", col)
    effects = []
    for vi, aim in enumerate(VARIANT_AIMS):
        sa = screen_angle(aim)
        start, end = sa - SWEEP, sa + SWEEP            # 시계 방향으로 휘둘러 위쪽에서 아래쪽으로 내려간다
        end_x = c + cfg["radius"] * math.cos(math.radians(end))
        end_y = c + cfg["radius"] * math.sin(math.radians(end))
        effects.append({
            "id": f"v{vi}", "durationMs": DURATION_MS, "impactMs": IMPACT_MS, "frameMs": FRAME_MS, "seed": 11 + vi,
            "outline": "ink",
            "ramps": {"blade": [f"r{i}" for i in range(len(cfg["ramp"]))],
                      "spark": [f"s{i}" for i in range(len(cfg["sparks"]))]},
            "primitives": [
                {"type": "slash", "ramp": "blade", "center": [c, c], "radius": cfg["radius"], "from": start, "to": end,
                 "width": cfg["width"], "trail": 1.0},
                {"type": "sparks", "ramp": "spark", "origin": [round(end_x, 1), round(end_y, 1)],
                 "count": cfg["sparks_count"], "angle": end + 90, "spread": 100, "speed": cfg["size"] * 0.9,
                 "lifeMs": 120, "length": cfg["size"] * 0.07, "width": 2},
            ]})
    return {"schema": "codeart2d.fx.v1", "canvas": [size, size], "origin": [c, c], "palette": palette, "effects": effects}


def build_sheet(name, cfg):
    spec = make_spec(cfg)
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / f"{name}.fx.json"
        spec_path.write_text(json.dumps(spec, indent=1), encoding="utf-8")
        out = Path(tmp) / "out"
        cmd = [sys.executable, str(SKILL / "scripts" / "fx_build.py"), "--spec", str(spec_path), "--output-dir", str(out),
               "--route", "pixel", "--strict-qc"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})
        if result.returncode != 0:
            sys.exit(result.stdout + result.stderr)
        rows = []
        for vi in range(len(VARIANT_AIMS)):
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
        "id": f"melee/{name}", "frames": n * len(rows), "variants": len(rows), "variantAngles": VARIANT_AIMS,
        "frameSize": [size, size], "columns": n, "fps": round(1000 / FRAME_MS), "loop": False,
        "pivot": [size // 2, size // 2], "scale": 1, "impactMs": IMPACT_MS, "durationMs": DURATION_MS,
        "source": "codeart2d fx_build.py (code-drawn, no image model), tools/make_slash.py",
    }
    (OUT / f"{name}.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print("saved", name, sheet.size, "frames/variant", n)


def main():
    if not (SKILL / "scripts" / "fx_build.py").exists():
        sys.exit(f"codeart2d 스킬이 없습니다: {SKILL} (docs/SETUP.md의 agent-sprite-forge 설치 참고)")
    for name, cfg in SHEETS.items():
        build_sheet(name, cfg)


if __name__ == "__main__":
    main()
