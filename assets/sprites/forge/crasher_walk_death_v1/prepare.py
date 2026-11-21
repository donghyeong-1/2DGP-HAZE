"""T27 크래셔 원화를 등록하고 걷기·사망의 1배 검토본을 만든다."""
import argparse
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
UNIFIED = ROOT.parent.parent / "unified"
RAW_SIZE = (1320, 975)
RAW_ANCHOR = (590, 890)
BG = "#252d3b"
FLOOR_COLOR = "#526079"
ACTIONS = {
    # 행과 열, 원화 배율, 시트의 골반 기준 x, GIF 프레임 시간.
    # 걷기 시트의 아래 행이 원화에서 더 커서 위 행과 전신 높이를 맞춘다.
    "walk": (2, 2, (1.43, 1.43, 1.393, 1.393), (360, 974, 367, 974), (140, 140, 140, 140)),
    "death": (1, 2, (1.02, 1.02), (380, 1185), (230, 500)),
}
LABELS = {"walk": ("1 near contact", "2 near down", "3 far contact", "4 far down"),
          "death": ("1 kneel", "2 prone")}
BELT_MARKERS = ((403, 303), (1019, 321), (409, 919), (1019, 937))


def rgba(path):
    return Image.open(path).convert("RGBA")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, content):
    path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


def prepare(action):
    rows, cols, scales, roots, _ = ACTIONS[action]
    folder = ROOT / action
    raw = folder / "frames_raw"
    raw.mkdir(exist_ok=True)
    sheet = rgba(folder / "processed/raw-sheet-clean.png")
    width, height = sheet.width // cols, sheet.height // rows
    landmarks = []
    for i, (root_x, factor) in enumerate(zip(roots, scales)):
        left, top = i % cols * width, i // cols * height
        cell = sheet.crop((left, top, left + width, top + height))
        ground = cell.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()[3]
        registered = cell.transform(
            RAW_SIZE, Image.Transform.AFFINE,
            (1 / factor, 0, root_x - left - RAW_ANCHOR[0] / factor,
             0, 1 / factor, ground - RAW_ANCHOR[1] / factor),
            Image.Resampling.BICUBIC,
        )
        x0, y0, x1, y1 = registered.getbbox()
        assert 0 < x0 < x1 < RAW_SIZE[0] and 0 < y0 < y1 < RAW_SIZE[1], (action, i)
        registered.save(raw / f"{action}-{i + 1}.png")
        if action == "walk":
            belt_x, belt_y = BELT_MARKERS[i]
            landmarks.append((RAW_ANCHOR[0] + (belt_x - root_x) * factor,
                              RAW_ANCHOR[1] + (belt_y - top - ground) * factor))
    if landmarks:
        save_json(folder / "belt_landmarks.json", landmarks)


def measured_belt(frame, marker):
    cx, cy = marker
    pixels = frame.load()
    region = [(x, y) for x in range(cx - 8, cx + 9) for y in range(cy - 8, cy + 9)
              if (c := pixels[x, y])[3] == 255 and c[0] < 120 and c[1] > 140 and c[2] > 140]
    return [round(median(coords), 1) for coords in zip(*region)]


def package(action, finished):
    _, _, source_scales, roots, delays = ACTIONS[action]
    folder = ROOT / action
    data = read_json(finished / "finish.json")

    def point(pos):
        return tuple(round(a + (p - src) * data["scale"]) for a, p, src in
                     zip(data["anchor"], pos, data["anchorSource"]))

    pivot_x, pivot_y = point(RAW_ANCHOR)
    files = [f"{action}-{i}.png" for i in range(1, len(roots) + 1)]
    frames = [rgba(finished / "frames" / name) for name in files]
    bottoms = [frame.getbbox()[3] for frame in frames]
    ground = max(bottoms)
    assert abs(ground - pivot_y) <= 2
    pad = 4
    size = (frames[0].width + 2 * pad, frames[0].height + 2 * pad)
    pivot = (pivot_x + pad, ground + pad)

    final = ROOT / "frames"
    final.mkdir(exist_ok=True)
    metrics = {}
    palette = set()
    for i, (name, frame, bottom, delay) in enumerate(zip(files, frames, bottoms, delays)):
        move = ground - bottom
        assert 0 <= move <= 2
        out = Image.new("RGBA", size)
        out.paste(frame, (pad, pad + move))
        box = out.getbbox()
        assert 0 < box[0] < box[2] < size[0] and 0 < box[1] < box[3] < size[1]
        assert box[3] == pivot[1]
        colors = {c[:3] for c in out.get_flattened_data() if c[3] == 255}
        palette |= colors
        item = {"anchor": pivot, "bounds": box, "sole_y": box[3] - 1,
                "source_scale": source_scales[i],
                "visible_height": box[3] - box[1], "colors": len(colors),
                "duration_ms": delay}
        if action == "walk":
            mark_x, mark_y = point(read_json(folder / "belt_landmarks.json")[i])
            item["belt_xy"] = measured_belt(out, (mark_x + pad, mark_y + move + pad))
            assert len(item["belt_xy"]) == 2, name
        metrics[name] = item
        out.save(final / name)
    if action == "death":
        assert metrics["death-2.png"]["visible_height"] <= 65
    save_json(folder / "checks.json", {"size": size, "anchor": pivot,
              "palette_colors": len(palette), "frames": metrics})
    print(action, size, pivot, len(palette))


def draw_tiles(items):
    left = 8 + max(x for _, (x, _), _ in items)
    right = 8 + max(frame.width - x for frame, (x, _), _ in items)
    ground = 22 + max(y for _, (_, y), _ in items)
    below = 8 + max(frame.height - y for frame, (_, y), _ in items)
    width, height = left + right, ground + below
    tiles = []
    for frame, (x, y), label in items:
        tile = Image.new("RGBA", (width, height), BG)
        tile.paste(FLOOR_COLOR, (0, ground, width, ground + 1))
        tile.alpha_composite(frame, (left - x, ground - y))
        ImageDraw.Draw(tile).text((5, 4), label, fill="white")
        tiles.append(tile)
    return tiles


def strip(tiles):
    width, height = tiles[0].size
    row = Image.new("RGBA", ((width + 4) * len(tiles) - 4, height), "#151a24")
    for i, tile in enumerate(tiles):
        row.alpha_composite(tile, (i * (width + 4), 0))
    return row


def previews():
    def original(name, anchor, label):
        return rgba(UNIFIED / f"{name}.png"), anchor, label

    references = [
        original("boss_crasher_idle", (98, 196), "Crasher idle"),
        original("boss_crasher_idle_1", (96, 205), "Crasher idle 1"),
        original("boss_crasher_idle_2", (96, 205), "Crasher idle 2"),
        original("boss_crasher_smash_2", (94, 246), "Crasher smash"),
    ]
    ark = [original(f"boss_ark_walk_{i}", (67, 160), f"Ark walk {i}") for i in range(1, 5)]
    poses = []
    for action in ACTIONS:
        stats = read_json(ROOT / action / "checks.json")
        items = [(rgba(ROOT / "frames" / name), info["anchor"], label)
                 for (name, info), label in zip(stats["frames"].items(), LABELS[action])]
        tiles = draw_tiles(items)
        strip(tiles).save(ROOT / f"{action}_strip_1x.png")
        duration = [info["duration_ms"] for info in stats["frames"].values()]
        imgs = [tile.convert("RGB") for tile in tiles]
        out = ROOT / f"{action}_1x.gif"
        imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=duration, disposal=2, loop=0)
        with Image.open(out) as gif:
            assert gif.n_frames == len(duration)
            for i, ms in enumerate(duration):
                gif.seek(i)
                assert gif.info["duration"] == ms
        poses.append(items)

    groups = (references, *poses, ark)
    tiles = iter(draw_tiles([item for group in groups for item in group]))
    rows = [strip([next(tiles) for _ in group]) for group in groups]
    overview = Image.new("RGBA", (max(row.width for row in rows),
                         sum(row.height + 4 for row in rows) - 4), "#151a24")
    y = 0
    for row in rows:
        overview.alpha_composite(row, (0, y))
        y += row.height + 4
    overview.save(ROOT / "comparison_1x.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("prepare", "package", "previews"))
    parser.add_argument("action", choices=ACTIONS, nargs="?")
    parser.add_argument("--finished", type=Path)
    args = parser.parse_args()
    if args.step == "prepare":
        prepare(args.action)
    elif args.step == "package":
        package(args.action, args.finished)
    else:
        previews()


if __name__ == "__main__":
    main()
