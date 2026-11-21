"""T34 그림을 T33과 같은 1920×400 Hi-bit 카드로 마감한다."""

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
SIZE = (1920, 400)
LABELS = {"crasher": ("제4구역장", "크래셔"), "ark": ("총감시관", "아크")}
TITLE_EDGE = 1280
TEXT = ((28, 154, (130, 235, 225)), (42, 194, (240, 244, 252)))


def run_skill(script, *args):
    scratch = ROOT / "finish"
    scratch.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8="1", TEMP=str(scratch), TMP=str(scratch))
    command = [sys.executable, "-B", str(SCRIPTS / script), *map(str, args)]
    subprocess.run(command, env=env, check=True)


def finish_card(boss, source, focus, take):
    frame = ROOT / "finish" / boss / take / "conform"
    plate = frame.with_name("hibit")
    frame.parent.mkdir(parents=True, exist_ok=True)
    run_skill(
        "conform_background.py", "conform", "--input", ROOT / "source" / source,
        "--size", "1920x400", "--mode", "cover", "--focus", f"0.5,{focus}",
        "--resampler", "lanczos", "--output-dir", frame,
    )
    run_skill(
        "hibit_plate.py", "plate", "--input", frame / "background.png", "--output-dir", plate,
        "--size", "1920x400", "--colors", 32, "--smooth", 0, "--preview-scale", 1,
    )
    shutil.copyfile(plate / "plate.png", ROOT / f"boss_card_{boss}.png")


def relative_luminance(rgb):
    srgb = np.asarray(rgb, dtype=float) / 255.0
    linear = np.where(srgb < 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    return linear @ np.array([0.2126, 0.7152, 0.0722])


def title_mask(word, font, top):
    mask = Image.new("L", SIZE)
    draw = ImageDraw.Draw(mask)
    x0, y0, _, _ = draw.textbbox((0, 0), word, font=font)
    draw.text((168 - x0, top - y0), word, fill=255, font=font)
    return mask.point(lambda value: 255 if value >= 128 else 0)


def preview():
    width, height = SIZE
    panel = Image.new("RGB", (width, height * len(LABELS)))
    fonts = {
        px: ImageFont.truetype(str(REPO / "assets/fonts/Galmuri14.ttf"), px)
        for px, _, _ in TEXT
    }
    records = {}
    for row, (boss, labels) in enumerate(LABELS.items()):
        path = ROOT / f"boss_card_{boss}.png"
        with Image.open(path) as source:
            assert source.size == SIZE and source.mode == "RGBA"
            assert source.getchannel("A").getextrema() == (255, 255)
            assert 0 < len(source.getcolors(32) or []) <= 32
            count = len(source.getcolors(32))
            art = source.convert("RGB")
        luma = relative_luminance(art)
        left = luma[:, :TITLE_EDGE]
        right = luma[:, TITLE_EDGE:]
        glyphs = []
        for word, (px, top, color) in zip(labels, TEXT):
            mask = title_mask(word, fonts[px], top)
            value = float(luma[np.asarray(mask) == 255].max())
            contrast = (float(relative_luminance(color)) + 0.05) / (value + 0.05)
            glyphs.append({
                "text": word, "font_px": px, "rgb": list(color),
                "box": list(mask.getbbox()), "minimum_contrast": round(contrast, 2),
            })
            art.paste(color, (0, 0, width, height), mask)
        panel.paste(art, (0, row * height))
        records[boss] = {
            "canvas": list(SIZE), "colors": count, "alpha": [255],
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "title_lines": glyphs,
            "left_luma_p95": round(float(np.percentile(left, 95)), 4),
            "left_luma_max": round(float(left.max()), 4),
            "right_luma_p95": round(float(np.percentile(right, 95)), 4),
        }
    panel.save(ROOT / "preview_titles_1x.png")
    stats = {"left_title_area": [0, 0, TITLE_EDGE, SIZE[1]], "cards": records}
    (ROOT / "qa_boss_cards.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_sprites():
    lines = []
    failed = []
    for boss in LABELS:
        path = ROOT / f"boss_card_{boss}.png"
        result = subprocess.run(
            [sys.executable, "-B", "tools/check_sprites.py", str(path.relative_to(REPO))],
            cwd=REPO, encoding="utf-8", capture_output=True,
        )
        lines.extend((f"## {path.name}\n", result.stdout, result.stderr, "\n"))
        if result.returncode:
            failed.append(boss)
    (ROOT / "check_sprites.txt").write_text("".join(lines), encoding="utf-8")
    if failed:
        raise SystemExit(", ".join(failed))
    print("check_sprites.py: 2/2 PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="step", required=True)
    make = subcommands.add_parser("finish")
    make.add_argument("boss", choices=LABELS)
    make.add_argument("source")
    make.add_argument("--focus", type=float, default=0.5)
    make.add_argument("--take", default="v1")
    subcommands.add_parser("preview")
    subcommands.add_parser("check")
    options = parser.parse_args()
    if options.step == "finish":
        finish_card(options.boss, options.source, options.focus, options.take)
    elif options.step == "preview":
        preview()
    else:
        check_sprites()
