"""T35 엔딩 장면을 32색 Hi-bit 배경으로 마감하고 크레딧 자리의 가독성을 확인한다."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SCRIPTS = Path.home() / ".codex/skills/generate2dmap/scripts"
SIZE = (1920, 1080)
SCENES = (1, 2, 3)
SAFE = (480, 720, 1440, 1080)
PREVIEW = (
    ("헤이즈 (HAZE)", 42, 72, (235, 240, 250)),
    ("기획 · 개발", 28, 142, (130, 235, 225)),
    ("2026년 2학기 2D 게임 프로그래밍 개인 프로젝트", 22, 196, (130, 145, 170)),
)


def run_skill(script, *args):
    scratch = ROOT / "finish"
    scratch.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1", TEMP=str(scratch), TMP=str(scratch))
    command = [sys.executable, "-B", str(SCRIPTS / script), *map(str, args)]
    subprocess.run(command, env=env, check=True)


def finish(scene, source, take):
    frame = ROOT / "finish" / str(scene) / take / "conform"
    plate = frame.with_name("hibit")
    frame.parent.mkdir(parents=True, exist_ok=True)
    run_skill(
        "conform_background.py", "conform", "--input", ROOT / "source" / source,
        "--size", "1920x1080", "--mode", "cover", "--resampler", "lanczos",
        "--output-dir", frame,
    )
    run_skill(
        "hibit_plate.py", "plate", "--input", frame / "background.png", "--output-dir", plate,
        "--size", "1920x1080", "--colors", 32, "--smooth", 0, "--preview-scale", 1,
    )
    shutil.copyfile(plate / "plate.png", ROOT / f"credits_{scene}.png")


def luminance(rgb):
    srgb = np.asarray(rgb, dtype=float) / 255.0
    linear = np.where(srgb < 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    return linear @ [0.2126, 0.7152, 0.0722]


def compact(luma):
    return {
        "p50": round(float(np.median(luma)), 4),
        "p95": round(float(np.percentile(luma, 95)), 4),
        "max": round(float(luma.max()), 4),
    }


def preview():
    width, height = SIZE
    bottom = height - SAFE[1]
    panel = Image.new("RGB", (width, bottom * len(SCENES)))
    entries = []
    for scene in SCENES:
        path = ROOT / f"credits_{scene}.png"
        with Image.open(path) as source:
            count = len(source.getcolors(32) or [])
            assert source.size == SIZE and source.mode == "RGBA"
            assert source.getchannel("A").getextrema() == (255, 255) and 0 < count <= 32
            art = source.convert("RGB")
        safe = luminance(art.crop(SAFE))
        top = luminance(art.crop((SAFE[0], 0, SAFE[2], SAFE[1])))
        portion = art.crop((0, SAFE[1], width, height))
        original = np.asarray(portion)
        luma = luminance(original)
        # 기존 게임의 덮개를 얹은 예상 수치도 계산한다.
        game_luma = luminance(np.rint(0.28 * original + 0.72 * np.array([6, 9, 18])))
        sample = []
        for text, px, y, color in PREVIEW:
            face = "Galmuri11.ttf" if px == 22 else "Galmuri14.ttf"
            font = ImageFont.truetype(str(REPO / "assets/fonts" / face), px)
            mask = Image.new("L", portion.size)
            draw = ImageDraw.Draw(mask)
            draw.text((width // 2, y), text, font=font, fill=255, anchor="mt")
            mask = mask.point(lambda value: 255 if value >= 128 else 0)
            active = np.asarray(mask) == 255
            text_luma = float(luminance(color))
            contrast = (text_luma + 0.05) / (float(luma[active].max()) + 0.05)
            game_contrast = (text_luma + 0.05) / (float(game_luma[active].max()) + 0.05)
            sample.append({
                "text": text, "px": px, "box_in_lower_third": list(mask.getbbox()),
                "min_contrast": round(contrast, 2), "min_contrast_with_existing_shade": round(game_contrast, 2),
            })
            portion.paste(color, (0, 0, width, bottom), mask)
        panel.paste(portion, (0, (scene - 1) * bottom))
        entries.append({
            "scene": scene, "size": list(SIZE), "colors": count, "alpha": [255],
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "lower_center": compact(safe),
            "upper_center": compact(top), "sample_text": sample,
        })
    panel.save(ROOT / "preview_credits_1x.png")
    info = {"lower_center_box": list(SAFE), "scenes": entries}
    (ROOT / "qa_credits.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check():
    lines = []
    failed = []
    for scene in SCENES:
        path = ROOT / f"credits_{scene}.png"
        result = subprocess.run(
            [sys.executable, "-B", "tools/check_sprites.py", str(path.relative_to(REPO))],
            cwd=REPO, encoding="utf-8", capture_output=True,
        )
        lines.extend((f"## {path.name}\n", result.stdout, result.stderr, "\n"))
        if result.returncode:
            failed.append(path.name)
    (ROOT / "check_sprites.txt").write_text("".join(lines), encoding="utf-8")
    if failed:
        raise SystemExit(", ".join(failed))
    print("check_sprites.py: 3/3 PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="step", required=True)
    make = subcommands.add_parser("finish")
    make.add_argument("scene", type=int, choices=SCENES)
    make.add_argument("source")
    make.add_argument("--take", default="v1")
    subcommands.add_parser("preview")
    subcommands.add_parser("check")
    args = parser.parse_args()
    if args.step == "finish":
        finish(args.scene, args.source, args.take)
    elif args.step == "preview":
        preview()
    else:
        check()
