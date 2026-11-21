"""T25 원화를 대기 스프라이트 크기로 등록하고 1배 검토본을 만든다."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
UNIFIED = FORGE.parent / "unified"
POSES = ("hurt-2", "death-1", "death-2", "death-3")
SOURCE_ANCHOR = (430, 660)
SOURCE_SIZE = (920, 710)
FLOOR_COLOR = "#526079"
TILE_COLOR = "#252d3b"
SPECIES = {
    # 원화 보정 배율, 네 포즈의 원화 몸 중심 x, 기존 피격 기준점, 마지막 컷 높이 상한
    "slum": (0.97, (315, 905, 284, 950), (39, 118), 39),
    "thrower": (0.89, (305, 925, 291, 942), (32, 124), 41),
    "guard": (0.92, (350, 925, 300, 924), (58, 136), 45),
    "hound": (1.15, (354, 908, 300, 1040), (46, 82), 27),
}
HOUND_FLAT_SCALE = 0.42


def rgba(path):
    return Image.open(path).convert("RGBA")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(name):
    factor, roots, _, _ = SPECIES[name]
    folder = ROOT / name
    sheet = rgba(folder / "processed/raw-sheet-clean.png")
    width, height = sheet.width // 2, sheet.height // 2
    raw = folder / "frames_raw"
    raw.mkdir(exist_ok=True)
    for index, (pose, source_x) in enumerate(zip(POSES, roots)):
        left, top = index % 2 * width, index // 2 * height
        cell = sheet.crop((left, top, left + width, top + height))
        root_x = source_x - left
        frame_scale = factor
        if name == "hound" and pose == "death-3":
            cell = rgba(folder / "flat_processed/raw-sheet-clean.png")
            root_x = source_x
            frame_scale = HOUND_FLAT_SCALE
        # 알파가 확실한 영역을 기준으로 접지 좌표를 잡는다.
        foot = cell.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()[3]
        registered = cell.transform(
            SOURCE_SIZE, Image.Transform.AFFINE,
            (1 / frame_scale, 0, root_x - SOURCE_ANCHOR[0] / frame_scale,
             0, 1 / frame_scale, foot - SOURCE_ANCHOR[1] / frame_scale),
            Image.Resampling.BICUBIC,
        )
        x0, y0, x1, y1 = registered.getbbox()
        assert 0 < x0 < x1 < SOURCE_SIZE[0] and 0 < y0 < y1 < SOURCE_SIZE[1], pose
        registered.save(raw / f"{pose}.png")


def measured_anchor(finished):
    meta = read_json(finished / "finish.json")
    return tuple(round(a + (p - s) * meta["scale"]) for a, p, s in
                 zip(meta["anchor"], SOURCE_ANCHOR, meta["anchorSource"]))


def package(name, finished):
    factor, roots, old_anchor, max_flat_height = SPECIES[name]
    folder = ROOT / name
    result = folder / "frames"
    result.mkdir(exist_ok=True)
    anchor_x, estimated_floor = measured_anchor(finished)
    frames = [rgba(finished / "frames" / f"{pose}.png") for pose in POSES]
    boxes = [frame.getbbox() for frame in frames]
    actual_floor = max(box[3] for box in boxes)
    offsets = [actual_floor - box[3] for box in boxes]
    assert abs(actual_floor - estimated_floor) <= 2
    assert max(offsets) <= 2
    padding = 3
    size = (frames[0].width + 2 * padding, frames[0].height + 2 * padding)
    anchor = (anchor_x + padding, actual_floor + padding)
    positions = {}
    colors = set()
    review_frames = []
    for pose, frame, offset in zip(POSES, frames, offsets):
        padded = Image.new("RGBA", size)
        padded.paste(frame, (padding, padding + offset))
        box = padded.getbbox()
        assert 0 < box[0] < box[2] < size[0] and 0 < box[1] < box[3] < size[1]
        assert box[3] == anchor[1]
        palette = {pixel[:3] for pixel in padded.get_flattened_data() if pixel[3] == 255}
        colors |= palette
        padded.save(result / f"{pose}.png")
        positions[pose] = {"bounds": box, "colors": len(palette), "y_adjustment_px": offset}
        review_frames.append(padded)

    flat_box = positions["death-3"]["bounds"]
    flat_height = flat_box[3] - flat_box[1]
    assert flat_height <= max_flat_height, (name, flat_height, max_flat_height)
    stats = {"canvas": size, "anchor": anchor, "old_hurt_anchor": old_anchor,
             "source_scales": (factor, factor, factor, HOUND_FLAT_SCALE if name == "hound" else factor),
             "source_root_x": roots, "colors_union": len(colors),
             "flat_height_px": flat_height, "flat_limit_px": max_flat_height, "frames": positions}
    (folder / "checks.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    idle_anchor = {
        "slum": (24, 118), "thrower": (27, 124), "guard": (35, 136), "hound": (51, 82),
    }[name]
    idle = rgba(UNIFIED / f"enemy_{name}_idle.png")
    hurt = rgba(UNIFIED / f"enemy_{name}_hurt_1.png")
    items = [(idle, idle_anchor), (hurt, old_anchor), *((f, anchor) for f in review_frames)]
    left = 8 + max(x for _, (x, _) in items)
    right = 8 + max(f.width - x for f, (x, _) in items)
    floor = 23 + max(y for _, (_, y) in items)
    under = 6 + max(f.height - y for f, (_, y) in items)
    tile_size = (left + right, floor + under)
    tiles = []
    for frame, (x, y) in items:
        tile = Image.new("RGBA", tile_size, TILE_COLOR)
        tile.paste(FLOOR_COLOR, (0, floor, tile.width, floor + 1))
        tile.alpha_composite(frame, (left - x, floor - y))
        tiles.append(tile)
    make_preview(folder, tiles)
    print(f"{name} {size}, anchor={anchor}, flat={flat_height}/{max_flat_height}px, colors={len(colors)}")


def make_preview(folder, tiles):
    names = ("idle", "hurt 1", "hurt 2", "death 1", "death 2", "death 3")
    w, h = tiles[0].size
    overview = Image.new("RGBA", ((w + 4) * len(tiles) - 4, h), "#151a24")
    draw = ImageDraw.Draw(overview)
    for i, (label, tile) in enumerate(zip(names, tiles)):
        overview.alpha_composite(tile, (i * (w + 4), 0))
        draw.text((i * (w + 4) + 5, 4), label, fill="white")
    overview.save(folder / "strip_1x.png")
    for action, frames, timing in (
        ("hurt", tiles[1:3], [110, 90]), ("death", tiles[3:], [90, 130, 240]),
    ):
        images = [frame.convert("RGB") for frame in frames]
        output = folder / f"{action}_preview.gif"
        images[0].save(output, save_all=True, append_images=images[1:],
                       duration=timing, disposal=2, loop=0)
        with Image.open(output) as gif:
            assert gif.n_frames == len(timing)
            for i, expected in enumerate(timing):
                gif.seek(i)
                assert gif.info["duration"] == expected


def comparison():
    strips = [rgba(ROOT / name / "strip_1x.png") for name in SPECIES]
    gap = 3
    width = max(strip.width for strip in strips)
    height = sum(strip.height for strip in strips) + gap * (len(strips) - 1)
    board = Image.new("RGBA", (width, height), "#151a24")
    y = 0
    for strip in strips:
        board.alpha_composite(strip, (0, y))
        y += strip.height + gap
    board.save(ROOT / "comparison_1x.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("prepare", "package", "comparison"))
    parser.add_argument("species", choices=SPECIES, nargs="?")
    parser.add_argument("--finished", type=Path)
    args = parser.parse_args()
    if args.step == "prepare":
        prepare(args.species)
    elif args.step == "package":
        package(args.species, args.finished)
    else:
        comparison()


if __name__ == "__main__":
    main()
