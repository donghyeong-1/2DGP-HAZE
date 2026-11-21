"""T33 원화를 1920×400으로 잡고 T16 방식으로 픽셀 마감한다."""

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
WIDTH, HEIGHT = 1920, 400
THEMES = ("cell", "foundry", "haze")
LABELS = dict(zip(THEMES, ("슬럼", "공장", "감시자의 탑")))
SAFE = (640, 0, 1280, HEIGHT)
TITLE_RGB = (234, 241, 247)


def read_rgba(path):
    with Image.open(path) as img:
        return img.convert("RGBA")


def run_script(script, *args):
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    scratch = ROOT / "finish"
    scratch.mkdir(exist_ok=True)
    env["TEMP"] = env["TMP"] = str(scratch)
    subprocess.run([sys.executable, "-B", str(SCRIPTS / script), *map(str, args)], env=env, check=True)


def finish(theme, focus, tag, source_name):
    root = ROOT / "finish" / theme / tag
    root.mkdir(parents=True, exist_ok=True)
    source = ROOT / "source" / (source_name or f"{theme}_source.png")
    frame = root / "conform"
    plate = root / "hibit"
    run_script(
        "conform_background.py", "conform", "--input", source, "--output-dir", frame,
        "--mode", "cover", "--size", f"{WIDTH}x{HEIGHT}",
        "--focus", f"0.5,{focus}", "--resampler", "lanczos",
    )
    run_script(
        "hibit_plate.py", "plate", "--input", frame / "background.png",
        "--output-dir", plate, "--size", f"{WIDTH}x{HEIGHT}",
        "--colors", 32, "--smooth", 0, "--preview-scale", 1,
    )
    shutil.copyfile(plate / "plate.png", ROOT / f"zone_{theme}.png")


def relative_luminance(rgb):
    srgb = np.asarray(rgb, dtype=float) / 255.0
    linear = np.where(srgb < 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    return linear @ np.array([0.2126, 0.7152, 0.0722])


def overlay_preview():
    font = ImageFont.truetype(str(REPO / "assets/fonts/Galmuri14.ttf"), 42)
    preview = Image.new("RGB", (WIDTH, HEIGHT * len(THEMES)))
    stats = {}
    ink = float(relative_luminance(TITLE_RGB))
    for i, theme in enumerate(THEMES):
        path = ROOT / f"zone_{theme}.png"
        art = read_rgba(path)
        pixels = np.asarray(art)
        assert art.size == (WIDTH, HEIGHT) and art.getchannel("A").getextrema() == (255, 255)
        count = len(art.getcolors(32) or [])
        assert 0 < count <= 32, theme
        art = art.convert("RGB")
        mask = Image.new("L", art.size)
        draw = ImageDraw.Draw(mask)
        word = LABELS[theme]
        x0, y0, x1, y1 = draw.textbbox((0, 0), word, font=font)
        draw.text(((WIDTH-x0-x1)//2, (HEIGHT-y0-y1)//2), word, fill=255, font=font)
        mask = mask.point(lambda value: 255 if value >= 128 else 0)
        luminance = relative_luminance(pixels[:, :, :3])
        safe = luminance[:, SAFE[0]:SAFE[2]]
        sides = np.concatenate((luminance[:, :SAFE[0]], luminance[:, SAFE[2]:]), axis=1)
        under_glyphs = luminance[np.asarray(mask) != 0]
        stats[theme] = {
            "canvas": list(art.size), "opaque_colors": count, "partial_alpha": 0,
            "title": word, "title_font_px": 42, "title_bounds": list(mask.getbbox()),
            "title_min_contrast": round((ink + 0.05) / (under_glyphs.max() + 0.05), 2),
            "safe_strip_min_contrast": round((ink + 0.05) / (safe.max() + 0.05), 2),
            "center_p95_luminance": round(float(np.percentile(safe, 95)), 4),
            "sides_p95_luminance": round(float(np.percentile(sides, 95)), 4),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        art.paste(TITLE_RGB, (0, 0, WIDTH, HEIGHT), mask)
        preview.paste(art, (0, i * HEIGHT))
    preview.save(ROOT / "preview_titles_1x.png")
    payload = {"safe_strip": list(SAFE), "glyph_rgb": list(TITLE_RGB), "cards": stats}
    (ROOT / "qa_zone_cards.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )


def checks():
    lines = []
    for theme in THEMES:
        path = ROOT / f"zone_{theme}.png"
        run = subprocess.run(
            [sys.executable, "-B", "tools/check_sprites.py", str(path.relative_to(REPO))],
            cwd=REPO, encoding="utf-8", capture_output=True,
        )
        lines.extend((f"## {path.name}\n", run.stdout, run.stderr, "\n"))
        if run.returncode:
            raise SystemExit("".join(lines))
    (ROOT / "check_sprites.txt").write_text("".join(lines), encoding="utf-8")
    print("check_sprites.py: 3/3 PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    steps = parser.add_subparsers(dest="step", required=True)
    make = steps.add_parser("finish")
    make.add_argument("theme", choices=THEMES)
    make.add_argument("--focus", type=float, default=0.5)
    make.add_argument("--tag", default="v1")
    make.add_argument("--source", help="다른 회차의 원화 파일명")
    steps.add_parser("preview")
    steps.add_parser("check")
    args = parser.parse_args()
    if args.step == "finish":
        finish(args.theme, args.focus, args.tag, args.source)
    elif args.step == "preview":
        overlay_preview()
    else:
        checks()
