"""T37 격자 원화의 바퀴·바닥을 등록하고 게임용 프레임을 묶는다."""

import argparse
import json
from pathlib import Path
from statistics import median

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
ACTIONS = {
    "roll": (2, 2, (90, 90, 90, 90)),
    "arm": (1, 3, (160, 150, 220)),
    "hurt": (1, 2, (100, 140)),
    "wreck": (1, 2, (180, 480)),
}
RAW_SIZE = (1320, 1120)
RAW_PIVOT = np.array((630, 957))
GAME_SIZE = (160, 122)
GAME_PIVOT = np.array((76, 104))
BG = "#252d3b"


def rgba(path):
    with Image.open(path) as img:
        return img.convert("RGBA")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def bounds(img):
    return img.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()


def cells(action):
    rows, cols, times = ACTIONS[action]
    img = rgba(SOURCE / (action + "_processed/raw-sheet-clean.png"))
    for i in range(len(times)):
        row, col = divmod(i, cols)
        box = (round(col * img.width / cols), round(row * img.height / rows),
               round((col + 1) * img.width / cols), round((row + 1) * img.height / rows))
        yield img.crop(box)


def inspect(action):
    print("MASTER", bounds(rgba(ROOT / "master/master_rgba.png")))
    for i, img in enumerate(cells(action), 1):
        print(action, i, img.size, bounds(img))


def prepare(action):
    images = list(cells(action))
    boxes = [bounds(img) for img in images]
    mbox = bounds(rgba(ROOT / "master/master_rgba.png"))
    raw_width = mbox[2] - mbox[0]
    factor = raw_width / median(b[2] - b[0] for b in boxes)
    out = ROOT / "registered" / action
    out.mkdir(parents=True, exist_ok=True)
    anchors_path = ROOT / "source/registration_anchors.json"
    overrides = read_json(anchors_path).get(action) if anchors_path.exists() else None
    frames = {}
    for i, (img, box) in enumerate(zip(images, boxes), 1):
        name = f"{action}-{i}"
        x0, y0, x1, y1 = box
        center, floor, scale = overrides[i-1] if overrides else [(x0+x1)/2, y1, factor]
        offset = np.array((center, floor)) - RAW_PIVOT / scale
        registered = img.transform(
            RAW_SIZE, Image.Transform.AFFINE,
            (1 / scale, 0, offset[0], 0, 1 / scale, offset[1]), Image.Resampling.BICUBIC,
        )
        placed = bounds(registered)
        assert placed and 0 < placed[0] < placed[2] < RAW_SIZE[0] and 0 < placed[1] < placed[3] < RAW_SIZE[1], (name, placed)
        registered.save(out / f"{name}.png")
        frames[name] = {"input_bounds": box, "source_pivot": [center, floor],
                        "registered_bounds": placed, "scale": scale}
    save_json(out / "registration.json", {"raw_pivot": RAW_PIVOT.tolist(), "frames": frames})


def package():
    out = ROOT / "frames"
    out.mkdir(exist_ok=True)
    frames = {}
    all_colors = set()
    for action, (_, _, delays) in ACTIONS.items():
        src = ROOT / f"enemy_cart_{action}"
        info = read_json(src / "finish.json")
        pivot = np.rint(np.array(info["anchor"]) + (RAW_PIVOT-np.array(info["anchorSource"])) * info["scale"]).astype(int)
        for i, delay in enumerate(delays, 1):
            name = f"{action}-{i}"
            img = rgba(src / "frames" / f"{name}.png")
            box = img.getbbox()
            offset = GAME_PIVOT - pivot
            # 바닥 기준을 공통으로 맞춘다. 피격 컷은 뒤 바퀴만 이 줄에 닿는다.
            offset[1] = GAME_PIVOT[1] - box[3]
            placed = Image.new("RGBA", GAME_SIZE)
            placed.paste(img, tuple(offset))
            expected = np.asarray(box) + np.tile(offset, 2)
            assert placed.getbbox() == tuple(expected), (name, expected)
            left, top, right, bottom = placed.getbbox()
            assert 0 < left < right < GAME_SIZE[0] and 0 < top < bottom < GAME_SIZE[1], (name, expected)
            if name == "arm-3":
                # 마지막 점멸은 같은 팔레트의 중간색으로 낮춘다.
                pixels = np.array(placed)
                lens = pixels[top:top+11, 92:118, :3]
                highlight = np.all(lens == (249, 104, 87), axis=2)
                assert highlight.any()
                lens[highlight] = (146, 79, 58)
                placed = Image.fromarray(pixels)
            pix = np.asarray(placed)
            assert set(np.unique(pix[:, :, 3])) == {0, 255}, name
            opaque = pix[pix[:, :, 3] == 255, :3]
            colors = {tuple(rgb) for rgb in opaque}
            all_colors.update(colors)
            placed.save(out / f"{name}.png")
            frames[name] = {"bounds": placed.getbbox(), "colors": len(colors), "alpha": [0, 255],
                            "bottom_opaque": bottom-1, "duration_ms": delay, "offset": offset.tolist()}
    assert len(all_colors) <= 41, len(all_colors)
    save_json(ROOT / "qa_frames.json", {"canvas": GAME_SIZE, "pivot": GAME_PIVOT.tolist(),
                                        "palette_colors": len(all_colors), "frames": frames})


def previews():
    for action, (_, _, delays) in ACTIONS.items():
        out = []
        for i in range(1, len(delays)+1):
            frame = rgba(ROOT / "frames" / f"{action}-{i}.png")
            tile = Image.new("RGBA", frame.size, BG)
            tile.alpha_composite(frame)
            out.append(tile.convert("RGB"))
        args = {"save_all": True, "append_images": out[1:], "duration": delays, "disposal": 2}
        if action == "roll":
            args["loop"] = 0
        path = ROOT / f"{action}_1x.gif"
        out[0].save(path, **args)
        with Image.open(path) as gif:
            assert gif.n_frames == len(delays), action
            for i, delay in enumerate(delays):
                gif.seek(i)
                assert gif.info["duration"] == delay
                assert np.array_equal(np.asarray(gif.convert("RGB")), np.asarray(out[i]))
    foundry()


def foundry():
    assets = ROOT.parents[2]
    board = rgba(assets / "backgrounds/far_foundry.png").crop((405, 464, 1545, 754))
    ground = 222
    tile = rgba(assets / "tiles/tile_set_foundry.png").crop((0, 0, 60, 60))
    for x in range(0, board.width, 60):
        board.alpha_composite(tile, (x, ground))
    entries = (
        (85, "Slum", "sprites/unified/enemy_slum_idle.png"),
        (236, "Thrower", "sprites/unified/enemy_thrower_idle.png"),
        (377, "Guard", "sprites/unified/enemy_guard_idle.png"),
        (527, "Hound", "sprites/unified/enemy_hound_idle.png"),
        (695, "Crasher", "sprites/unified/boss_crasher_idle_1.png"),
        (881, "Decor Cart", "decor/foundry_scrap_cart.png"),
    )
    draw = ImageDraw.Draw(board)
    for x, label, path in entries:
        image = rgba(assets / path)
        art = image.crop(image.getbbox())
        board.alpha_composite(art, (x-art.width//2, ground-art.height))
        draw.text((x, 257), label, fill="white", anchor="ms")
    board.alpha_composite(rgba(ROOT / "frames/roll-1.png"), (1041-int(GAME_PIVOT[0]), ground-int(GAME_PIVOT[1])))
    draw.text((1041, 257), "Foundry Cart", fill="white", anchor="ms")
    board.save(ROOT / "foundry_1x.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("inspect", "prepare", "package", "preview"))
    parser.add_argument("action", nargs="?", choices=ACTIONS)
    args = parser.parse_args()
    if args.step == "inspect":
        inspect(args.action)
    elif args.step == "prepare":
        prepare(args.action)
    elif args.step == "package":
        package()
    else:
        previews()
