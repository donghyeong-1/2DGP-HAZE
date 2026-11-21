"""T26 원화를 몸 중심과 바닥선에 등록하고 1배 검토 파일을 만든다."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
UNIFIED = FORGE.parent / "unified"
SOURCE_SIZE = (1280, 930)
SOURCE_PIVOT = (570, 860)
BG = "#252d3b"
FLOOR = "#515e74"
ACTIONS = {
    # 행/열, 원화 배율, 몸 중심 x, 의도한 체공 높이, 검토본 프레임 시간
    "knife": (1, 3, 1.16, (295, 995, 1720), (0, 0, 0), (110, 50, 110)),
    "gauntlet": (2, 2, 1.28, (291, 916, 284, 877), (0, 0, 0, 17), (140, 70, 110, 130)),
    "chain": (1, 3, 1.16, (352, 1013, 1724), (0, 0, 0), (120, 60, 130)),
}
KNIFE_READY_SCALE = 0.705
KNIFE_READY_HIP = 545
LABELS = {
    "knife": ("ready", "throw", "follow-through"),
    "gauntlet": ("charge", "fire", "recover", "air down"),
    "chain": ("wind-up", "cast", "pull"),
}


def rgba(path):
    return Image.open(path).convert("RGBA")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(weapon):
    rows, cols, factor, centers, air, _ = ACTIONS[weapon]
    scale = read_json(FORGE / "n09_v3b/finish.json")["scale"]
    folder = ROOT / weapon
    raw = folder / "frames_raw"
    raw.mkdir(exist_ok=True)
    sheet = rgba(folder / "processed/raw-sheet-clean.png")
    width, height = sheet.width // cols, sheet.height // rows
    for index, (hip, lift) in enumerate(zip(centers, air), 1):
        left, top = (index - 1) % cols * width, (index - 1) // cols * height
        cell = sheet.crop((left, top, left + width, top + height))
        root_x = hip - left
        frame_scale = factor
        if weapon == "knife" and index == 1:
            cell = rgba(folder / "ready_processed/raw-sheet-clean.png")
            root_x = KNIFE_READY_HIP
            frame_scale = KNIFE_READY_SCALE
        foot = cell.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()[3]
        dest_y = SOURCE_PIVOT[1] - lift / scale
        registered = cell.transform(
            SOURCE_SIZE, Image.Transform.AFFINE,
            (1 / frame_scale, 0, root_x - SOURCE_PIVOT[0] / frame_scale,
             0, 1 / frame_scale, foot - dest_y / frame_scale),
            Image.Resampling.BICUBIC,
        )
        x0, y0, x1, y1 = registered.getbbox()
        assert 0 < x0 < x1 < SOURCE_SIZE[0] and 0 < y0 < y1 < SOURCE_SIZE[1], (weapon, index)
        registered.save(raw / f"{weapon}-{index}.png")


def package(weapon, finished):
    _, _, factor, centers, flight, durations = ACTIONS[weapon]
    metadata = read_json(finished / "finish.json")
    guess_x, guess_y = (round(a + (p - s) * metadata["scale"]) for a, p, s in
                        zip(metadata["anchor"], SOURCE_PIVOT, metadata["anchorSource"]))
    names = [f"{weapon}-{i}.png" for i in range(1, len(centers) + 1)]
    native = [rgba(finished / "frames" / name) for name in names]
    bottoms = [frame.getbbox()[3] for frame in native]
    floor = max(y for y, lift in zip(bottoms, flight) if lift == 0)
    assert abs(floor - guess_y) <= 2
    pad = 4
    anchor = (guess_x + pad, floor + pad)
    size = (native[0].width + 2 * pad, native[0].height + 2 * pad)
    folder = ROOT / weapon
    result = folder / "frames"
    result.mkdir(exist_ok=True)
    colors = set()
    metrics = {}
    frames = []
    for index, (name, frame, y, lift, duration) in enumerate(zip(names, native, bottoms, flight, durations)):
        dy = floor - lift - y
        assert abs(dy) <= 2, (name, dy)
        out = Image.new("RGBA", size)
        out.paste(frame, (pad, pad + dy))
        box = out.getbbox()
        assert 0 < box[0] < box[2] < size[0] and 0 < box[1] < box[3] < size[1]
        assert box[3] == anchor[1] - lift
        palette = {c[:3] for c in out.get_flattened_data() if c[3] == 255}
        colors |= palette
        ready = weapon == "knife" and index == 0
        metrics[name] = {"anchor": anchor, "bounds": box, "bottom_y": box[3] - 1,
                         "air_px": lift, "source_hip_x": KNIFE_READY_HIP if ready else centers[index],
                         "source_scale": KNIFE_READY_SCALE if ready else factor,
                         "colors": len(palette), "preview_duration_ms": duration}
        out.save(result / name)
        frames.append(out)
    stats = {"canvas": size, "anchor": anchor, "palette_colors": len(colors), "frames": metrics}
    (folder / "checks.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    item_specs = [(frame, anchor, label) for frame, label in zip(frames, LABELS[weapon])]
    tiles = draw_at_common_floor(item_specs)
    strip(tiles).save(folder / "strip_1x.png")
    images = [tile.convert("RGB") for tile in tiles]
    gif_path = folder / "preview.gif"
    images[0].save(gif_path, save_all=True, append_images=images[1:],
                   duration=durations, disposal=2, loop=0)
    with Image.open(gif_path) as gif:
        assert gif.n_frames == len(durations)
        for index, duration in enumerate(durations):
            gif.seek(index)
            assert gif.info["duration"] == duration
    print(f"{weapon}: {size}, anchor={anchor}, colors={len(colors)}")


def draw_at_common_floor(items):
    left = 8 + max(anchor[0] for _, anchor, _ in items)
    right = 8 + max(frame.width - x for frame, (x, _), _ in items)
    baseline = 20 + max(anchor[1] for _, anchor, _ in items)
    below = 8 + max(frame.height - y for frame, (_, y), _ in items)
    width, height = left + right, baseline + below
    tiles = []
    for frame, (x, y), label in items:
        tile = Image.new("RGBA", (width, height), BG)
        tile.paste(FLOOR, (0, baseline, width, baseline + 1))
        tile.alpha_composite(frame, (left - x, baseline - y))
        ImageDraw.Draw(tile).text((5, 4), label, fill="white")
        tiles.append(tile)
    return tiles


def strip(tiles):
    width, height = tiles[0].size
    row = Image.new("RGBA", ((width + 4) * len(tiles) - 4, height), "#151a24")
    for index, tile in enumerate(tiles):
        row.alpha_composite(tile, (index * (width + 4), 0))
    return row


def comparison():
    idle = rgba(UNIFIED / "n09_idle_1.png")
    groups = [[(idle, (21, 124), "idle"), *[
        (rgba(UNIFIED / f"n09_punch_{i}.png"), (36, 124), f"punch {i}")
        for i in range(1, 5)
    ]]]
    for weapon in ACTIONS:
        folder = ROOT / weapon
        checks = read_json(folder / "checks.json")
        groups.append([
            (rgba(folder / "frames" / name), stats["anchor"], f"{weapon} {label}")
            for (name, stats), label in zip(checks["frames"].items(), LABELS[weapon])
        ])
    tiles = iter(draw_at_common_floor([item for row in groups for item in row]))
    rows = [strip([next(tiles) for _ in row]) for row in groups]
    width = max(row.width for row in rows)
    sheet = Image.new("RGBA", (width, sum(row.height + 3 for row in rows) - 3), "#151a24")
    y = 0
    for row in rows:
        sheet.alpha_composite(row, (0, y))
        y += row.height + 3
    sheet.save(ROOT / "comparison_1x.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("prepare", "package", "comparison"))
    parser.add_argument("weapon", choices=ACTIONS, nargs="?")
    parser.add_argument("--finished", type=Path)
    args = parser.parse_args()
    if args.step == "prepare":
        prepare(args.weapon)
    elif args.step == "package":
        package(args.weapon, args.finished)
    else:
        comparison()


if __name__ == "__main__":
    main()
