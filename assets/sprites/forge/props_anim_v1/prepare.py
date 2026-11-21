"""T28 소품 원화의 설치점을 고정하고 1배 반복 프레임을 만든다."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
ASSETS = PROJECT / "assets"
FINISH = Path.home() / ".codex/skills/video2dsprite/scripts/finish_frames.py"
SIZE = (460, 480)
COLORS = (
    "#111820", "#19232c", "#22313e", "#2a3c49", "#354957", "#425765", "#526775", "#637b87",
    "#111f25", "#162e33", "#1e3d43", "#24505a", "#326471", "#448390", "#4e95a1",
    "#241d1b", "#312621", "#3e2f28", "#514033", "#624636", "#73533f", "#81593c", "#50474a",
    "#353543", "#454551", "#55534c", "#686552", "#7d7051", "#988355", "#a45d39", "#bb8652",
)
SPECS = {
    "cell": (("drip", "top", 146), ("rag", "top", 116), ("bulb", "top", 91)),
    "foundry": (("steam", "left", 134), ("gear", "center", 102), ("piston", "top", 130)),
    "haze": (("crystal", "bottom", 133), ("searchlight", "top", 126), ("chain", "top", 130)),
    "hideout": (("brazier", "bottom", 105), ("anvil", "bottom", 118), ("fan", "center", 98)),
}
TONE_CAP = {"drip": 106, "rag": 96, "crystal": 122, "anvil": 105}
DITHER = np.array([[0, 8, 2, 10], [12, 4, 14, 6],
                   [3, 11, 1, 9], [15, 7, 13, 5]])


def luminance(rgb):
    return np.dot(rgb, (0.2126, 0.7152, 0.0722))


def tone_down(pixels, limit):
    values = np.array([tuple(bytes.fromhex(c[1:])) for c in ("#0b1020", *COLORS)])
    choices = values[luminance(values) <= limit]
    for color in values[luminance(values) > limit]:
        replacement = choices[np.square(choices - color).sum(axis=1).argmin()]
        selected = np.all(pixels[:,:,:3] == color, axis=2) & (pixels[:,:,3] == 255)
        pixels[selected, :3] = replacement


def lock_fixture(name, current, reference, anchor, scale):
    ax, ay = anchor
    y, x = np.indices(current.shape[:2])
    if name in {"drip", "rag", "bulb", "chain", "searchlight"}:
        height = {"drip": 90, "rag": 25, "bulb": 162, "chain": 29, "searchlight": 103}[name]
        fixed = y <= ay + round(height * scale)
    elif name in {"brazier", "anvil", "crystal"}:
        lower = {"brazier": 120, "anvil": 144, "crystal": 59}[name]
        fixed = y >= ay - round(lower * scale)
    elif name == "steam":
        fixed = x < ax + round(149 * scale)
    elif name == "piston":
        opening = ((abs(x-ax) <= round(40 * scale)) & (y >= ay + round(102 * scale))
                   & (y <= ay + round(242 * scale)))
        fixed = ~opening
    elif name == "fan":
        fixed = (x-ax)**2 + (y-ay)**2 > (round(95 * scale)+1)**2
    else:
        fixed = np.zeros(current.shape[:2], dtype=bool)
    current[fixed] = reference[fixed]
    if name == "searchlight":
        beam = ~fixed & (current[:,:,3] == 255)
        depth = (y - ay) / scale
        coverage = np.where(depth < 174, 8, 6)
        current[beam & (DITHER[y % 4, x % 4] >= coverage)] = 0
    if name in TONE_CAP:
        tone_down(current, TONE_CAP[name])


def rgba(path):
    return Image.open(path).convert("RGBA")


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def box(image):
    return image.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()


def raw_anchor(image, anchor):
    x0, y0, x1, y1 = box(image)
    mask = image.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    if anchor == "top":
        lo, _, hi, _ = mask.crop((0, y0, image.width, y0 + 18)).getbbox()
        return ((lo + hi) // 2, y0)
    if anchor == "bottom":
        lo, _, hi, _ = mask.crop((0, y1 - 15, image.width, y1)).getbbox()
        return ((lo + hi) // 2, y1)
    if anchor == "left":
        _, lo, _, hi = mask.crop((x0, 0, x0 + 22, image.height)).getbbox()
        return (x0, (lo + hi) // 2)
    return ((x0 + x1) // 2, (y0 + y1) // 2)


def registered(image, anchor, destination):
    x, y = raw_anchor(image, anchor)
    canvas = Image.new("RGBA", SIZE)
    canvas.paste(image, (destination[0] - x, destination[1] - y))
    assert box(canvas) is not None
    return canvas


def rotation_frames(frame, center, radius=None):
    # 생성 원화 사분면을 재사용해 90도마다 같은 모양이 되도록 만든다.
    cx, cy = center
    half = radius or 150
    extent = (cx - half, cy - half, cx + half, cy + half)
    patch = frame.crop(extent)
    quarter = patch.crop((half, 0, 2 * half, half))
    seed = Image.new("RGBA", patch.size)
    seed.paste(quarter, (half, 0))
    rotor = Image.new("RGBA", patch.size)
    for _ in range(4):
        rotor.alpha_composite(seed)
        seed = seed.transpose(Image.Transpose.ROTATE_90)
    if radius:
        yy, xx = np.indices(rotor.size)
        inner = Image.fromarray(
            np.where((xx - half + 0.5)**2 + (yy - half + 0.5)**2 < (half - 1)**2, 255, 0)
            .astype("uint8")
        )
    frames = []
    for degrees in (0, -22.5, -45, -67.5):
        moved = rotor.rotate(degrees, Image.Resampling.BICUBIC)
        canvas = frame.copy() if radius else Image.new("RGBA", frame.size)
        if radius:
            canvas.paste(moved, extent[:2], inner)
        else:
            canvas.paste(moved, extent[:2])
        frames.append(canvas)
    return frames


def pulse_frames(dark, bright):
    mask = dark.getchannel("A")
    # 점등 단계는 동일한 실루엣을 사용하고 원본 색면 사이만 보간한다.
    frames = []
    for amount in (0, 0.43, 1, 0.60):
        frame = Image.blend(dark, bright, amount)
        frame.putalpha(mask)
        frames.append(frame)
    return frames


def prepare(theme):
    folder = ROOT / theme
    source = rgba(folder / "processed/raw-sheet-clean.png")
    cell_w, cell_h = source.width // 4, source.height // 3
    dests = {"top": (225, 75), "bottom": (225, 385),
             "left": (75, 225), "center": (225, 225)}
    for row, (name, anchor, limit) in enumerate(SPECS[theme]):
        cells = [source.crop((i * cell_w, row * cell_h, (i + 1) * cell_w, (row + 1) * cell_h))
                 for i in range(4)]
        if name == "gear":
            cells = rotation_frames(cells[0], (182, 178))
        elif name == "fan":
            cells = rotation_frames(cells[0], (181, 174), radius=95)
        dest = dests[anchor]
        # 회전축은 바운딩 박스의 미세한 변화와 무관하게 고정한다.
        if name in {"gear", "fan"}:
            pivot = (182, 178) if name == "gear" else (181, 174)
            sequence = []
            for cell in cells:
                canvas = Image.new("RGBA", SIZE)
                canvas.paste(cell, (dest[0] - pivot[0], dest[1] - pivot[1]))
                sequence.append(canvas)
        else:
            sequence = [registered(cell, anchor, dest) for cell in cells]
        if name in {"bulb", "crystal"}:
            sequence = pulse_frames(sequence[0], sequence[2])
        frame_dir = folder / name / "raw_frames"
        frame_dir.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(sequence, 1):
            frame.save(frame_dir / f"{i}.png")
        bounds = [box(frame) for frame in sequence]
        longest = max(max(b[2] - b[0], b[3] - b[1]) for b in bounds)
        rest = max(range(4), key=lambda i: bounds[i][3] - bounds[i][1])
        rest_height = bounds[rest][3] - bounds[rest][1]
        target = max(15, round(limit * rest_height / longest))
        save_json(folder / name / "registration.json",
                  {"anchor_source": dest, "target_height": target, "rest": rest})


def run_finish(theme):
    for name, _, _ in SPECS[theme]:
        prop = ROOT / theme / name
        meta = json.loads((prop / "registration.json").read_text(encoding="utf-8"))
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["TEMP"] = env["TMP"] = str(ROOT / "tmp")
        command = [
            sys.executable, "-B", str(FINISH), "hibit",
            "--frames", str(prop / "raw_frames"), "--output-dir", str(prop / "finish"),
            "--target-height", str(meta["target_height"]), "--rest-frame", str(meta["rest"]),
            "--anchor", "center", "--loop-policy", "cycle", "--palette", str(ROOT / "palette.json"),
            "--outline", "#0b1020", "--coverage", "0.30",
        ]
        subprocess.run(command, check=True, env=env)


def pack(theme, name):
    prop = ROOT / theme / name
    build = prop / "finish"
    info = json.loads((build / "finish.json").read_text(encoding="utf-8"))
    setup = json.loads((prop / "registration.json").read_text(encoding="utf-8"))
    source_anchor = setup["anchor_source"]
    ax, ay = (round(a + (p - src) * info["scale"]) for a, p, src in
              zip(info["anchor"], source_anchor, info["anchorSource"]))
    originals = [rgba(build / "frames" / f"{i}.png") for i in range(1, 5)]
    if name == "crystal":
        # 양자화 뒤에도 같은 중간 밝기를 거쳐 감쇠하도록 복귀 프레임을 맞춘다.
        originals[3] = originals[1]
    pad = 5
    size = (originals[0].width + 2*pad, originals[0].height + 2*pad)
    output = prop / "frames"
    output.mkdir(exist_ok=True)
    frames = []
    total_colors = set()
    reference = Image.new("RGBA", size)
    reference.paste(originals[0], (pad, pad))
    reference_pixels = np.asarray(reference)
    for i, original in enumerate(originals, 1):
        frame = Image.new("RGBA", size)
        frame.paste(original, (pad, pad))
        pixels = np.array(frame)
        lock_fixture(name, pixels, reference_pixels, (ax+pad, ay+pad), info["scale"])
        frame = Image.fromarray(pixels)
        frame.save(output / f"{i}.png")
        frames.append(frame)
        total_colors |= {c[:3] for c in frame.get_flattened_data() if c[3] == 255}
    assert len(total_colors) <= 32
    assert 60 <= max(size) <= 180, (theme, name, size)
    backgrounds = [Image.new("RGBA", size, "#1c2430") for _ in frames]
    for bg, frame in zip(backgrounds, frames):
        bg.alpha_composite(frame)
    first = backgrounds[0].convert("RGB")
    first.save(prop / "preview.gif", save_all=True, append_images=[f.convert("RGB") for f in backgrounds[1:]],
               duration=120, disposal=2, loop=0, optimize=False)
    with Image.open(prop / "preview.gif") as gif:
        assert gif.n_frames == 4, (name, gif.n_frames)
        for i in range(4):
            gif.seek(i)
            assert gif.info["duration"] == 120
    strip = Image.new("RGBA", (size[0]*4+12, size[1]))
    for i, frame in enumerate(frames):
        strip.alpha_composite(frame, (i*(size[0]+4),0))
    strip.save(prop / "strip_1x.png")
    arrays = [np.asarray(f).astype(int) for f in frames]
    motion = [int(np.any(np.abs(a-b)>7, axis=2).sum()) for a, b in zip(arrays, arrays[1:]+arrays[:1])]
    assert all(motion), (name, motion)
    luma = sorted(round(0.2126*r + 0.7152*g + 0.0722*b) for r,g,b in total_colors)
    save_json(prop / "checks.json", {"canvas": size, "pivot": [ax+pad,ay+pad], "colors": len(total_colors),
              "max_luma": luma[-1], "step_changes_including_wrap": motion,
              "frame_duration_ms": 120, "source_to_output_scale": info["scale"],
              "bounds": [frame.getbbox() for frame in frames]})


def comparison():
    # 실제 게임 원경 위에 타일과 캐릭터를 확대 없이 합성한다.
    hero = rgba(ASSETS / "sprites/unified/n09_idle_1.png")
    columns, tile_height = 324, 182
    palette_board = Image.new("RGBA", (columns*3, (tile_height+18)*4), "#141b24")
    for row, (theme, specs) in enumerate(SPECS.items()):
        background = rgba(ASSETS / f"backgrounds/far_{theme}.png")
        atlas_name = "foundry" if theme == "hideout" else theme
        atlas = rgba(ASSETS / f"tiles/tile_set_{atlas_name}.png")
        tile = atlas.crop((0, 0, 60, 60))
        y = row*(tile_height+18)
        ImageDraw.Draw(palette_board).text((7,y+3),theme,fill="white")
        strips = []
        for col, (name, anchor, _) in enumerate(specs):
            frames = ROOT/theme/name/"frames"
            strips.append((name, rgba(frames.parent / "strip_1x.png")))
            frame = rgba(frames / "3.png")
            xy = (820+col*75, 340+col*35)
            sample = background.crop((*xy, xy[0]+columns, xy[1]+tile_height))
            for x in range(0, columns, 60):
                sample.alpha_composite(tile,(x,tile_height-36))
            sample.alpha_composite(frame, (84, tile_height-34-frame.getbbox()[3]))
            sample.alpha_composite(hero, (columns-83,tile_height-34-hero.getbbox()[3]))
            ImageDraw.Draw(sample).text((5,4),name,fill="white")
            palette_board.alpha_composite(sample,(col*columns,y+18))
        board = Image.new("RGBA", (max(strip.width for _, strip in strips)+8,
                          sum(strip.height+25 for _, strip in strips)), "#1c2430")
        y = 0
        for name, strip in strips:
            ImageDraw.Draw(board).text((4,y+4),name,fill="white")
            board.alpha_composite(strip,(4,y+20))
            y += strip.height + 25
        board.save(ROOT/theme/"all_frames_1x.png")
    palette_board.save(ROOT / "comparison_1x.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("prepare", "finish", "pack", "comparison"))
    parser.add_argument("theme", nargs="?", choices=SPECS)
    args = parser.parse_args()
    if args.step == "prepare":
        save_json(ROOT / "palette.json", {"schema": "generate2dsprite.palette.v1",
                                         "colors": [{"hex": value} for value in COLORS]})
        prepare(args.theme)
    elif args.step == "finish":
        run_finish(args.theme)
    elif args.step == "pack":
        for name, _, _ in SPECS[args.theme]:
            pack(args.theme, name)
    else:
        comparison()


if __name__ == "__main__":
    main()
