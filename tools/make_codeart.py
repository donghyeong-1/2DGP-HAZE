"""코드 아트(tools/codeart/)를 한 번에 만든다: SVG 생성 -> codeart2d로 1배 렌더 -> assets/에 복사.

이미지 모델 없이 코드로 그린 에셋이다 (agent-sprite-forge의 codeart2d 스킬 렌더러 사용).
사용: python tools/make_codeart.py
결과: assets/ui/logo.png, assets/tiles/tile_*.png
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODEART = ROOT / "tools" / "codeart"
RENDER = Path.home() / ".codex" / "skills" / "codeart2d" / "scripts" / "svg_render.py"

TARGETS = {
    "logo": ROOT / "assets" / "ui" / "logo.png",
    "tile_solid_a": ROOT / "assets" / "tiles" / "tile_solid_a.png",
    "tile_solid_b": ROOT / "assets" / "tiles" / "tile_solid_b.png",
    "tile_solid_c": ROOT / "assets" / "tiles" / "tile_solid_c.png",
    "tile_oneway": ROOT / "assets" / "tiles" / "tile_oneway.png",
    "tile_spike": ROOT / "assets" / "tiles" / "tile_spike.png",
}


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(result.stdout + result.stderr)
    return result.stdout


def main():
    if not RENDER.exists():
        sys.exit(f"codeart2d 렌더러가 없습니다: {RENDER} (docs/SETUP.md의 agent-sprite-forge 설치 참고)")
    run([sys.executable, str(CODEART / "make_logo.py")])
    run([sys.executable, str(CODEART / "make_tiles.py")])
    for name, target in TARGETS.items():
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            run([sys.executable, str(RENDER), "render", "--svg", str(CODEART / f"{name}.svg"), "--palette",
                 str(CODEART / "palette.json"), "--output-dir", str(out), "--crisp", "--zoom", "1", "--strict-qc"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(out / "base" / f"{name}.png", target)
        print("saved", target.relative_to(ROOT))


if __name__ == "__main__":
    main()
