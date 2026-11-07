"""AI 마스터 스틸컷(마젠타 배경을 지운 RGBA PNG)을 우리 규격의 픽셀 스프라이트로 마무리한다.

agent-sprite-forge의 hibit 마무리(finish_frames.py)를 같은 설정으로 반복 실행하는 얇은 래퍼다.
- 팔레트 24색(캐릭터마다 원본에서 학습), 가장자리 커버리지 0.3, 외곽선 #0b1020(1px)
- 키(외곽선 포함 높이)는 docs/sprite_spec.md 표를 따른다.

사용:
  python tools/finish_character.py <master_rgba.png> n09
  python tools/finish_character.py <master_rgba.png> enemy_guard --height 88
결과: assets/sprites/forge/<이름>/ (frames/, palette.json, finish.json) 와 assets/sprites/forge/<이름>_idle.png
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINISH = Path.home() / ".codex" / "skills" / "video2dsprite" / "scripts" / "finish_frames.py"

# docs/sprite_spec.md: 키(외곽선 제외) + 외곽선 2px
HEIGHTS = {"n09": 82, "enemy_slum": 78, "enemy_thrower": 82, "enemy_guard": 90, "enemy_hound": 54,
           "boss_ark": 106, "boss_crasher": 130}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("master", help="마젠타 배경을 지운 RGBA PNG")
    ap.add_argument("name", help="캐릭터 이름 (예: n09, enemy_guard)")
    ap.add_argument("--height", type=int, help="키(px). 생략하면 규격표 값")
    ap.add_argument("--colors", type=int, default=24)
    ap.add_argument("--coverage", type=float, default=0.3)
    ap.add_argument("--outline", default="#0b1020")
    args = ap.parse_args()

    height = args.height or HEIGHTS.get(args.name)
    if not height:
        sys.exit(f"{args.name}의 키를 모릅니다. --height를 지정하세요. (규격표: {HEIGHTS})")
    if not FINISH.exists():
        sys.exit(f"finish_frames.py가 없습니다: {FINISH} (agent-sprite-forge 스킬을 설치하세요)")

    out = ROOT / "assets" / "sprites" / "forge" / args.name
    if out.exists():
        sys.exit(f"이미 있습니다: {out} (지우고 다시 실행하거나 다른 이름을 쓰세요)")

    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(args.master, Path(tmp) / "f000.png")
        cmd = [sys.executable, str(FINISH), "hibit", "--frames", tmp, "--output-dir", str(out),
               "--target-height", str(height), "--colors", str(args.colors), "--coverage", str(args.coverage),
               "--outline", args.outline, "--loop-policy", "oneshot", "--character", args.name]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(result.stderr or result.stdout)

    frames = sorted((out / "frames").glob("*.png"))
    shutil.copy(frames[0], ROOT / "assets" / "sprites" / "forge" / f"{args.name}_idle.png")
    print(f"저장: {out}  /  assets/sprites/forge/{args.name}_idle.png")


if __name__ == "__main__":
    main()
