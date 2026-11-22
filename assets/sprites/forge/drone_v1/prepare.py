"""T36 격자 원화를 등록하고 동일한 캔버스의 게임 프레임을 묶는다."""

import argparse
import json
from pathlib import Path
from statistics import median

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
REFERENCE = ROOT / "enemy_drone"
ACTIONS = {
    "fly": (2, 2, ("fly-1", "fly-2", "fly-3", "fly-4")),
    "attack": (2, 3, ("aim-1", "aim-2", "fire-1", "fire-2", "fire-3")),
    "hurt": (1, 2, ("hurt-1", "hurt-2")),
    "death": (1, 2, ("death-1", "death-2")),
}
DELAYS = {
    "fly": (90, 90, 90, 90),
    "aim": (160, 210),
    "fire": (110, 110, 150),
    "hurt": (100, 120),
    "death": (160, 450),
}
SOURCE_CANVAS = (1420, 1256)
MASTER_OFFSET = np.array([190, 100])
GAME_CANVAS = (160, 136)
PIVOT = np.array([73, 65])
PACKAGE_OFFSETS = {"hurt-2": (-4, 0)}
BG = "#252d3b"
JOIN = np.ones((3, 3), dtype=bool)


def rgba(path):
    with Image.open(path) as img:
        return img.convert("RGBA")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, doc):
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hard_box(img):
    return img.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()


def largest_box(mask):
    regions, _ = ndimage.label(mask, structure=JOIN)
    counts = np.bincount(regions[mask])
    assert len(counts) > 1
    points = np.where(regions == (1 + np.argmax(counts[1:])))
    y, x = points
    return np.array([x.min(), y.min(), x.max()+1, y.max()+1])


def markers(img):
    pixels = np.asarray(img).astype(np.int16)
    r, g, b, a = pixels.transpose(2, 0, 1)
    orange = (a >= 128) & (r > 85) & (r-g > 30) & (g-b > 6)
    cyan = (a >= 128) & (r + 38 < g) & (r + 38 < b) & (g > 104)
    shell = largest_box(orange)
    lens = largest_box(cyan) if cyan.any() else None
    return shell, lens


def cells(action):
    r, c, names = ACTIONS[action]
    path = SOURCE / f"{action}_processed/raw-sheet-clean.png"
    sheet = rgba(path)
    for i, name in enumerate(names):
        y, x = divmod(i, c)
        crop = (round(x*sheet.width/c), round(y*sheet.height/r),
                round((x+1)*sheet.width/c), round((y+1)*sheet.height/r))
        yield name, sheet.crop(crop)


def mid(box):
    return (box[:2] + box[2:]) / 2


def span(box):
    return box[2] - box[0]


def master_setup():
    master = rgba(ROOT / "master/master_rgba.png")
    shell, lens = markers(master)
    return shell, lens, mid(shell) + MASTER_OFFSET


def preserve_sparks(img):
    """원화에 이미 있는 불똥이 1px 고립점 정리에서 사라지지 않게 한다."""
    rgba_pixels = np.asarray(img).copy()
    alpha = rgba_pixels[:, :, 3] >= 128
    labels, _ = ndimage.label(alpha, structure=JOIN)
    sizes = np.bincount(labels[alpha])
    # 작은 불똥만 남긴다. 가장 큰 연결 성분은 드론 본체다.
    candidates = (sizes >= 45) & (sizes <= 180)
    sparks = alpha & candidates[labels]
    assert sparks.any()
    fringe = ndimage.binary_dilation(sparks, iterations=5) & ~alpha
    nearest = ndimage.distance_transform_edt(~sparks, return_distances=False, return_indices=True)
    rgba_pixels[fringe, :3] = rgba_pixels[nearest[0][fringe], nearest[1][fringe], :3]
    rgba_pixels[fringe, 3] = 255
    return Image.fromarray(rgba_pixels)


def inspect(action):
    shell, lens, anchor = master_setup()
    print("master", shell, lens, anchor)
    for name, img in cells(action):
        print(name, img.size, hard_box(img), *markers(img))


def prepare(action):
    shell, lens, pivot = master_setup()
    scale_ref = read_json(REFERENCE / "finish.json")["scale"]
    frames = [(name, img, *markers(img)) for name, img in cells(action)]
    widths = [span(orange) for _, _, orange, _ in frames]
    # 떨어진 뒤의 잔해 크기는 기울어지는 첫 컷과 같은 축척으로 유지한다.
    scale = span(shell) / median(widths[:1] if action == "death" else widths)
    out = ROOT / "registered" / ("death_sparks" if action == "death" else action)
    out.mkdir(parents=True, exist_ok=True)
    records = {}
    for i, (name, img, orange, eye) in enumerate(frames):
        dest = pivot.copy()
        center = mid(orange)
        factor = scale
        if action == "fly":
            dest[1] += (0, -1, -2, -1)[i] / scale_ref
        if action in ("fly", "attack") and eye is not None:
            # 렌즈를 보조 기준으로 삼아 토치 변화가 몸통 위치를 끌고 가지 않게 한다.
            center = 0.75 * center + 0.25 * mid(eye)
            dest += 0.25 * (mid(lens) - mid(shell))
        if action == "death" and i == 1:
            size = hard_box(img)
            factor = min(factor, 950 / (size[2] - size[0]))
            center = np.array([(size[0] + size[2]) / 2, size[3]])
            dest = np.array([pivot[0], 1000.0])
        elif action == "death":
            img = preserve_sparks(img)
        offset = center - dest / factor
        registered = img.transform(
            SOURCE_CANVAS, Image.Transform.AFFINE,
            (1 / factor, 0, offset[0], 0, 1 / factor, offset[1]),
            Image.Resampling.BICUBIC,
        )
        box = hard_box(registered)
        assert box and 0 < box[0] < box[2] < SOURCE_CANVAS[0] and 0 < box[1] < box[3] < SOURCE_CANVAS[1], (name, box)
        registered.save(out / f"{name}.png")
        records[name] = {"raw_box": hard_box(img), "placed_box": box, "scale": float(factor),
                         "body_anchor": dest.tolist(), "source_registration": center.tolist()}
    save_json(out / "registration.json", {"shared_body_pivot": pivot.tolist(), "frames": records})


def package():
    out = ROOT / "frames"
    out.mkdir(exist_ok=True)
    _, _, pivot = master_setup()
    metrics = {}
    family_results = [
        (action, names, ROOT / f"enemy_drone_{action}{'_sparks' if action == 'death' else ''}")
        for action, (_, _, names) in ACTIONS.items()
    ]
    for action, names, source in family_results:
        info = read_json(source / "finish.json")
        source_pivot = np.round(np.asarray(info["anchor"]) +
                                (pivot - np.asarray(info["anchorSource"])) * info["scale"]).astype(int)
        for name in names:
            offset = PIVOT - source_pivot + np.array(PACKAGE_OFFSETS.get(name, (0, 0)))
            original = rgba(source / "frames" / f"{name}.png")
            frame = Image.new("RGBA", GAME_CANVAS)
            frame.paste(original, tuple(offset))
            box = frame.getbbox()
            old = original.getbbox()
            assert box == tuple((np.asarray(old) + np.tile(offset, 2)).tolist()), (name, old, box, offset)
            pixels = np.asarray(frame)
            assert set(np.unique(pixels[:, :, 3])) == {0, 255}, name
            rgb = pixels[pixels[:, :, 3] == 255, :3]
            sample = np.unique(rgb, axis=0)
            assert 0 < len(sample) <= 41, name
            shell, eye = markers(frame)
            sample_eyes = None
            if eye is not None:
                eye_pixels = pixels[eye[1]:eye[3], eye[0]:eye[2], :3]
                eye_mask = (eye_pixels[:, :, 1].astype(int) - eye_pixels[:, :, 0] > 38)
                if eye_mask.any():
                    sample_eyes = round(float((eye_pixels[eye_mask] @ [0.2126, 0.7152, 0.0722]).mean()), 1)
            frame.save(out / f"{name}.png")
            metrics[name] = {
                "bounds": box, "shell_center": mid(shell).tolist(),
                "lens_bounds": eye.tolist() if eye is not None else None, "lens_luma_mean": sample_eyes,
                "colors": len(sample), "partial_alpha": 0, "duration_ms": DELAYS[name.split("-")[0]][int(name[-1])-1],
                "registration_offset": list(PACKAGE_OFFSETS.get(name, (0, 0))),
            }
    save_json(ROOT / "qa_frames.json", {"size": GAME_CANVAS, "pivot": PIVOT.tolist(), "frames": metrics})


def show_gifs():
    for action, delays in DELAYS.items():
        images = []
        for i in range(1, len(delays)+1):
            frame = rgba(ROOT / "frames" / f"{action}-{i}.png")
            card = Image.new("RGBA", frame.size, BG)
            card.alpha_composite(frame)
            images.append(card.convert("RGB"))
        path = ROOT / f"{action}_1x.gif"
        args = {"save_all": True, "append_images": images[1:], "duration": delays, "disposal": 2}
        if action == "fly":
            args["loop"] = 0
        images[0].save(path, **args)
        with Image.open(path) as gif:
            assert gif.n_frames == len(delays), action
            for i, delay in enumerate(delays):
                gif.seek(i)
                assert gif.info["duration"] == delay, (action, i, gif.info["duration"], delay)


def foundry_preview():
    assets = ROOT.parents[2]
    background = rgba(assets / "backgrounds/far_foundry.png")
    board = background.crop((414, 462, 1464, 772))
    ground = 241
    tile = rgba(assets / "tiles/tile_set_foundry.png").crop((0, 0, 60, 60))
    for x in range(0, board.width, 60):
        board.alpha_composite(tile, (x, ground))
    entries = (
        ("Slum", "enemy_slum_idle.png", 76), ("Thrower", "enemy_thrower_idle.png", 225),
        ("Guard", "enemy_guard_idle.png", 374), ("Hound", "enemy_hound_idle.png", 532),
        ("Crasher", "boss_crasher_idle_1.png", 700),
    )
    draw = ImageDraw.Draw(board)
    for label, name, x in entries:
        actor = rgba(assets / "sprites/unified" / name)
        actor = actor.crop(actor.getbbox())
        board.alpha_composite(actor, (x - actor.width // 2, ground - actor.height))
        draw.text((x, 278), label, fill="white", anchor="ms")
    drone = rgba(ROOT / "frames/fly-1.png")
    board.alpha_composite(drone, (915 - int(PIVOT[0]), 131 - int(PIVOT[1])))
    draw.text((915, 278), "Welding Drone", fill="white", anchor="ms")
    board.save(ROOT / "foundry_1x.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("inspect", "prepare", "package", "gifs", "foundry"))
    parser.add_argument("action", nargs="?", choices=ACTIONS)
    args = parser.parse_args()
    if args.step == "inspect":
        inspect(args.action)
    elif args.step == "prepare":
        prepare(args.action)
    elif args.step == "package":
        package()
    elif args.step == "gifs":
        show_gifs()
    else:
        foundry_preview()
