"""T31 장식 원화를 Hibit으로 마감하고 정적 PNG 및 1배 비교판을 만든다."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import mkdtemp

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT.parents[2]
REPO = ASSETS.parent
FINISH = Path.home() / ".codex/skills/video2dsprite/scripts/finish_frames.py"
PROCESS = Path.home() / ".codex/skills/generate2dsprite/scripts/generate2dsprite.py"
LUMA = np.array([0.2126, 0.7152, 0.0722])
OUTLINE = "#0b1020"
SPECS = {
    "cell": (
        ("broken_crates", 72), ("rusty_drum", 81), ("rag_heap", 47),
        ("barred_window", 104), ("wanted_poster", 80), ("sagging_wires", 83),
    ),
    "foundry": (
        ("scrap_cart", 81), ("stacked_moulds", 74), ("tool_chest", 56),
        ("warning_sign", 58), ("wall_gauge", 66), ("hanging_hook", 94),
    ),
    "haze": (
        ("broken_crystals", 53), ("watcher_wreck", 61), ("sealed_chest", 62),
        ("teal_panel", 100), ("broken_monitor", 68), ("watch_camera", 58),
    ),
}
CAPS = {"cell": 98, "foundry": 93, "haze": 110}
TONES = {
    "broken_crates": 0.92, "rag_heap": 0.91, "wanted_poster": 0.70,
    "barred_window": 1.12, "broken_monitor": 1.13, "watch_camera": 1.13,
}
WIDTH = 960
CENTERS = (128, 368, 608)
FLOOR = 248


def rgba(path):
    with Image.open(path) as source:
        return source.convert("RGBA")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def luma_stats(image):
    pixels = np.asarray(image)
    values = pixels[pixels[:, :, 3] == 255, :3] @ LUMA
    p50, p95 = np.percentile(values, (50, 95))
    return {"p50": round(p50, 1), "p95": round(p95, 1), "max": round(values.max(), 1)}


def theme_palette(theme, work):
    template = ROOT.parent / "props_anim_v1/palette.json"
    palette = json.loads(template.read_text(encoding="utf-8"))
    for swatch in palette["colors"]:
        rgb = np.array(list(bytes.fromhex(swatch["hex"][1:])))
        factor = min(1, CAPS[theme] / (rgb @ LUMA))
        swatch["hex"] = "#" + "".join(f"{round(channel * factor):02x}" for channel in rgb)
    output = work / "palette.json"
    write_json(output, palette)
    return output


def tone(image, name):
    pixels = np.asarray(image).copy()
    luma = pixels[:, :, :3] @ LUMA
    # 낮은 대비를 유지하면서 왼쪽 위의 작은 강조색과 재질 색은 남긴다.
    factor = np.where(luma > 72, 0.68 + 23.04 / np.maximum(luma, 1), 1)
    factor *= TONES.get(name, 1)
    pixels[:, :, :3] = np.rint(pixels[:, :, :3] * factor[:, :, None]).clip(0, 255)
    if name == "broken_monitor":
        # 원화에서 화면을 가로지르는 균열만 골라 축소에 남을 만큼 굵게 한다.
        screen = np.s_[65:206, 32:206]
        highlights = Image.fromarray(np.uint8(luma[screen] >= 68) * 255)
        crack = np.asarray(highlights.filter(ImageFilter.MaxFilter(7))) > 0
        pixels[screen][:, :, :3][crack] = (61, 111, 124)
    return Image.fromarray(pixels)


def finish(theme):
    folder = ROOT / theme
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    work = Path(mkdtemp(prefix=f"{theme}-", dir=scratch))
    palette = theme_palette(theme, work)
    keyed = folder / "processed/raw-sheet-clean.png"
    if not keyed.is_file():
        processed = work / "processed"
        subprocess.run([
            sys.executable, "-B", str(PROCESS), "process", "--input", str(folder / "source.png"),
            "--rows", "2", "--cols", "3", "--target", "asset", "--mode", "sheet",
            "--key-quality", "soft", "--scale-strategy", "registered", "--cell-size", "600",
            "--trim-border", "2", "--strict-qc", "--output-dir", str(processed),
        ], check=True)
        keyed = processed / keyed.name
    sheet = rgba(keyed)
    width, height = sheet.size
    figures = []
    for i, (name, target) in enumerate(SPECS[theme]):
        row, col = divmod(i, 3)
        crop = (
            round(col * width / 3), round(row * height / 2),
            round((col + 1) * width / 3), round((row + 1) * height / 2),
        )
        cell = sheet.crop(crop)
        alpha = cell.getchannel("A")
        assert alpha.getbbox(), name
        x0, y0, x1, y1 = alpha.getbbox()
        source_box = (max(x0 - 3, 0), max(y0 - 3, 0), min(x1 + 3, cell.width), min(y1 + 3, cell.height))
        source = tone(cell.crop(source_box), name)
        input_dir = work / name / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        source.save(input_dir / "1.png")
        finished = work / name / "finished"
        subprocess.run([
            sys.executable, "-B", str(FINISH), "hibit", "--frames", str(input_dir),
            "--output-dir", str(finished), "--target-height", str(target),
            "--anchor", "center", "--loop-policy", "oneshot", "--palette", str(palette),
            "--outline", OUTLINE, "--coverage", "0.30",
        ], check=True, stdout=subprocess.DEVNULL)
        images = list((finished / "frames").glob("*.png"))
        assert len(images) == 1, images
        sprite = rgba(images[0])
        sprite = sprite.crop(sprite.getbbox())
        canvas = Image.new("RGBA", (sprite.width + 6, sprite.height + (3 if row == 0 else 6)))
        canvas.alpha_composite(sprite, (3, 3))
        canvas.save(folder / f"{name}.png")
        rgb = np.asarray(canvas)
        alpha_values = sorted(np.unique(rgb[:, :, 3]).tolist())
        colors = len(np.unique(rgb[rgb[:, :, 3] == 255, :3], axis=0))
        assert alpha_values == [0, 255] and colors <= 32, name
        assert 40 <= canvas.height <= (150 if row == 0 else 160), name
        assert row == 1 or canvas.getbbox()[3] == canvas.height, name
        info = json.loads((finished / "finish.json").read_text(encoding="utf-8"))
        figures.append({
            "name": name, "mount": "floor" if row == 0 else "wall",
            "canvas": list(canvas.size), "opaque_bounds": list(canvas.getbbox()),
            "placement": [canvas.width // 2, canvas.height - 1 if row == 0 else 3],
            "colors": colors, "alpha": alpha_values, "source_box": list(source_box),
            "luma": luma_stats(canvas), "finish_scale": info["scale"],
            "finish_qa": {key: info["qa"][key] for key in ("status", "checks")},
        })
    write_json(folder / "qa.json", figures)
    (folder / "palette.json").write_bytes(palette.read_bytes())


def preview(theme):
    samples = [rgba(ROOT / theme / f"{name}.png") for name, _ in SPECS[theme]]
    board = Image.new("RGBA", (684, 291), "#222c39")
    draw = ImageDraw.Draw(board)
    for i, ((name, _), sprite) in enumerate(zip(SPECS[theme], samples)):
        row, col = divmod(i, 3)
        left = col * 228
        base = (row + 1) * 138
        top = base - sprite.height - 23
        board.alpha_composite(sprite, (left + (228 - sprite.width) // 2, top))
        label = name.replace("_", " ")
        draw.text((left + 114, base - 4), label, fill="#c3cfde", anchor="ms")
    board.save(ROOT / f"{theme}_sheet_1x.png")
    return samples


def background_comparison():
    hero = rgba(ASSETS / "sprites/unified/n09_idle_1.png")
    hero = hero.crop(hero.getbbox())
    height = 308
    board = Image.new("RGBA", (WIDTH, height * len(SPECS)), "#151d28")
    light = {}
    for i, theme in enumerate(SPECS):
        sprites = preview(theme)
        far = rgba(ASSETS / f"backgrounds/far_{theme}.png")
        mid = rgba(ASSETS / f"backgrounds/mid_{theme}.png")
        tiles = rgba(ASSETS / f"tiles/tile_set_{theme}.png")
        offset = (480, 507)
        region = (*offset, offset[0] + WIDTH, offset[1] + height)
        scene = far.crop(region)
        scene.alpha_composite(mid.crop(region))
        tile = tiles.crop((0, 0, 60, 60))
        for x in range(0, WIDTH, 60):
            scene.alpha_composite(tile, (x, FLOOR))
        for j, sprite in enumerate(sprites):
            row, col = divmod(j, 3)
            top = FLOOR - sprite.height if row == 0 else 24
            scene.alpha_composite(sprite, (CENTERS[col] - sprite.width // 2, top))
        scene.alpha_composite(hero, (816 - hero.width // 2, FLOOR - hero.height))
        draw = ImageDraw.Draw(scene)
        draw.rectangle((0, 0, WIDTH, 20), fill="#151d28")
        draw.text((9, 5), f"{theme.upper()}    1x", fill="#e2eaf4")
        board.alpha_composite(scene, (0, i * height))
        light[theme] = {"tile": luma_stats(tile), "far_crop": luma_stats(far.crop(region)),
                        "mid_crop": luma_stats(mid.crop(region))}
    board.save(ROOT / "comparison_1x.png")
    write_json(ROOT / "comparison_luma.json", {"hero": luma_stats(hero), **light})


def check_sprites():
    output = []
    failures = []
    for theme, specs in SPECS.items():
        for name, target in specs:
            result = subprocess.run([
                sys.executable, "-B", "tools/check_sprites.py",
                str((ROOT / theme / f"{name}.png").relative_to(REPO)),
                "--height", str(target),
            ], cwd=REPO, capture_output=True, encoding="utf-8")
            output.extend((f"## {theme}/{name}.png\n", result.stdout, result.stderr, "\n"))
            if result.returncode:
                failures.append(name)
    (ROOT / "check_sprites.txt").write_text("".join(output), encoding="utf-8")
    if failures:
        raise SystemExit("check_sprites.py 실패: " + ", ".join(failures))
    print("check_sprites.py: 18/18 PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("finish", "preview", "check"))
    parser.add_argument("theme", choices=SPECS, nargs="?")
    args = parser.parse_args()
    if args.step == "finish":
        finish(args.theme)
    elif args.step == "preview":
        background_comparison()
    else:
        check_sprites()


if __name__ == "__main__":
    main()
