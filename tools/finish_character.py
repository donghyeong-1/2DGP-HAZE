"""AI 마스터 스틸컷(마젠타 배경을 지운 RGBA PNG) 또는 프레임 폴더를 우리 규격의 픽셀 스프라이트로 마무리한다.

agent-sprite-forge의 hibit 마무리(finish_frames.py)를 같은 설정으로 반복 실행하는 얇은 래퍼다.
- 팔레트 40색(캐릭터마다 원본에서 학습), 가장자리 커버리지 0.3, 외곽선 #0b1020(1px)
- 키(외곽선 포함)는 아래 BASE_HEIGHTS x SCALE. 화면 1920x1080, 타일 60px 기준이라 SCALE = 1.5 (기존 1280x720 값의 1.5배)

사용:
  python tools/finish_character.py <master_rgba.png> n09_v3                 # 마스터 한 장
  python tools/finish_character.py <프레임 폴더> n09_walk_v3 --like n09_v3   # 동작 프레임: n09_v3의 크기 비율·팔레트를 그대로 쓴다
  python tools/finish_character.py <master_rgba.png> enemy_guard_v3 --height 135
결과: assets/sprites/forge/<이름>/ (frames/, palette.json, finish.json)
      마스터 한 장이면 assets/sprites/forge/<이름>_idle.png, 프레임 폴더면 <이름>_strip_1x.png(가로 이어붙임)
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FORGE = ROOT / "assets" / "sprites" / "forge"
FINISH = Path.home() / ".codex" / "skills" / "video2dsprite" / "scripts" / "finish_frames.py"

SCALE = 1.5  # 1280x720 기준 대비 배율. 화면·타일·캐릭터 키를 모두 같은 배율로 키운다
# 1280x720 기준 키(외곽선 포함). docs/sprite_spec.md 표와 같은 값
BASE_HEIGHTS = {"n09": 82, "enemy_slum": 78, "enemy_thrower": 82, "enemy_guard": 90, "enemy_hound": 54,
                "boss_ark": 106, "boss_crasher": 130}


def base_name(name):
    """'n09_walk_v3' 같은 이름에서 캐릭터 이름('n09')을 찾는다."""
    for key in sorted(BASE_HEIGHTS, key=len, reverse=True):
        if name == key or name.startswith(key + "_"):
            return key
    return None


def target_height(name):
    key = base_name(name)
    return round(BASE_HEIGHTS[key] * SCALE) if key else None


def build_strip(frames_dir, out_png):
    """프레임을 바닥선을 맞춰 가로로 이어붙인 확인용 이미지(1배)."""
    frames = [Image.open(p).convert("RGBA") for p in sorted(frames_dir.glob("*.png"))]
    w = sum(f.width for f in frames) + 4 * (len(frames) - 1)
    h = max(f.height for f in frames)
    strip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for f in frames:
        strip.alpha_composite(f, (x, h - f.height))
        x += f.width + 4
    strip.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="마젠타 배경을 지운 RGBA PNG 한 장, 또는 프레임 PNG들이 든 폴더")
    ap.add_argument("name", help="결과 이름 (예: n09_v3, n09_walk_v3, enemy_guard_v3)")
    ap.add_argument("--height", type=int, help="키(px). 생략하면 규격표 값")
    ap.add_argument("--like", help="이미 마무리한 결과 이름(예: n09_v3). 그 크기 비율과 팔레트를 그대로 쓴다")
    ap.add_argument("--colors", type=int, default=40)
    ap.add_argument("--coverage", type=float, default=0.3)
    ap.add_argument("--outline", default="#0b1020")
    ap.add_argument("--root", help="결과를 저장할 상위 폴더 (기본: assets/sprites/forge)")
    args = ap.parse_args()

    if not FINISH.exists():
        sys.exit(f"finish_frames.py가 없습니다: {FINISH} (agent-sprite-forge 스킬을 설치하세요. docs/SETUP.md)")
    forge = Path(args.root) if args.root else FORGE
    out = forge / args.name
    if out.exists():
        sys.exit(f"이미 있습니다: {out} (지우지 말고 새 이름을 쓰세요. 예: {args.name}_2)")

    source = Path(args.source)
    cmd = [sys.executable, str(FINISH), "hibit", "--output-dir", str(out), "--outline", args.outline,
           "--coverage", str(args.coverage), "--loop-policy", "oneshot"]

    if args.like:
        ref = forge / args.like
        if not (ref / "finish.json").exists():
            sys.exit(f"--like 대상 결과가 없습니다: {ref}")
        character = json.loads((ref / "finish.json").read_text(encoding="utf-8")).get("character") or args.like
        cmd += ["--scale-ref", str(ref / "finish.json"), "--no-area-norm", "--palette", str(ref / "palette.json"),
                "--character", character]
    else:
        height = args.height or target_height(args.name)
        if not height:
            sys.exit(f"{args.name}의 키를 모릅니다. --height를 지정하세요. (기준: {BASE_HEIGHTS} x {SCALE})")
        cmd += ["--target-height", str(height), "--colors", str(args.colors), "--character", args.name]

    with tempfile.TemporaryDirectory() as tmp:
        if source.is_dir():
            frames_in = source
        else:
            frames_in = Path(tmp)
            shutil.copy(source, frames_in / "f000.png")
        result = subprocess.run(cmd + ["--frames", str(frames_in)], capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(result.stderr or result.stdout)

    frames = sorted((out / "frames").glob("*.png"))
    if source.is_dir():
        strip = forge / f"{args.name}_strip_1x.png"
        build_strip(out / "frames", strip)
        print(f"저장: {out}  /  {strip}  (프레임 {len(frames)}장)")
    else:
        idle = forge / f"{args.name}_idle.png"
        shutil.copy(frames[0], idle)
        print(f"저장: {out}  /  {idle}")


if __name__ == "__main__":
    main()
