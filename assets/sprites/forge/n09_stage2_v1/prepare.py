"""T24 원화의 파이프·바닥선 보정과 1배 검토본 패키징."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
UNIFIED = ROOT.parent.parent / "unified"
POSES = {
    "s2rise": [
        # 원화 좌우 경계, 몸 중심 x, 밑창 y, 손과 파이프 경계, 파이프 끝, 반경, 몸 배율
        (0, 492, 160, 935, (273, 835), (462, 927), 13, 1.04),
        (492, 1083, 678, 935, (826, 552), (1080, 552), 12, 1.05),
        (1083, 1536, 1249, 935, (1350, 197), (1106, 56), 13, 1.06),
    ],
    "s2slam": [
        (0, 408, 272, 784, (257, 136), (34, 159), 11, 1.13),
        (408, 927, 604, 867, (757, 631), (906, 801), 12, 1.10),
        (927, 1536, 1149, 867, (1333, 724), (1478, 868), 12, 1.09),
    ],
}
STEPS = [f"{action}-{i}" for action in POSES for i in range(1, 4)]
DELAYS_MS = [50, 50, 80, 60, 40, 120]
SOURCE_ANCHOR = np.array([700, 1220])
SOURCE_SIZE = (1500, 1290)
IMPACT = (0, 1536, 644, 935, (1090, 558), (1384, 935), 19, 0.65)
CELL_W = 680
GUTTER = 32
FRAME_PADDING = 5


def rgba(path):
    return Image.open(path).convert("RGBA")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def layout():
    for action, poses in POSES.items():
        sheet = rgba(ROOT / "raw" / f"{action}.png")
        grid = Image.new("RGBA", (CELL_W * len(poses), sheet.height), "#ff00ff")
        for i, (left, right, *_) in enumerate(poses):
            grid.paste(sheet.crop((left, 0, right, sheet.height)), (i * CELL_W + GUTTER, 0))
        grid.save(ROOT / "raw" / f"{action}_grid.png")


def affine(layer, mapping, shift):
    return layer.transform(
        SOURCE_SIZE, Image.Transform.AFFINE,
        (mapping[0, 0], mapping[0, 1], shift[0],
         mapping[1, 0], mapping[1, 1], shift[1]),
        Image.Resampling.BICUBIC,
    )


def prepare():
    destination = ROOT / "frames_raw"
    destination.mkdir(exist_ok=True)
    reference = json.loads((ROOT.parent / "n09_v3b/finish.json").read_text(encoding="utf-8"))
    scale = reference["scale"]
    registration = {}
    for action, poses in POSES.items():
        cleaned = rgba(ROOT / "processed" / action / "raw-sheet-clean.png")
        for i, pose in enumerate(poses):
            name = f"{action}-{i + 1}"
            left, right, hip, sole, grip, tip, radius, body_scale = (
                IMPACT if name == "s2slam-3" else pose
            )
            if name == "s2slam-3":
                cell = rgba(ROOT / "processed/s2slam_impact/raw-sheet-clean.png")
            else:
                start = i * CELL_W + GUTTER
                cell = cleaned.crop((start, 0, start + right - left, cleaned.height))
            pixels = np.array(cell)
            grip = np.array(grip, dtype=float) - (left, 0)
            tip = np.array(tip, dtype=float) - (left, 0)
            delta = tip - grip
            length = np.linalg.norm(delta)
            axis = delta / length
            normal = np.array([-axis[1], axis[0]])
            ys, xs = np.indices(pixels.shape[:2])
            axial = (xs - grip[0]) * axis[0] + (ys - grip[1]) * axis[1]
            cross = (xs - grip[0]) * normal[0] + (ys - grip[1]) * normal[1]
            warm_skin = (pixels[:, :, 0].astype(int) - pixels[:, :, 2].astype(int) > 32)
            pipe_mask = (axial >= -2) & (abs(cross) <= radius + 3) & ~warm_skin
            shaft = pixels.copy()
            shaft[~pipe_mask] = 0
            pixels[pipe_mask] = 0

            # 공중 준비 자세만 기준 바닥에서 발을 띄운다.
            air_px = 14 if name == "s2slam-1" else 0
            source_pivot = np.array([hip - left, sole], dtype=float)
            dest_pivot = SOURCE_ANCHOR - (0, air_px / scale)
            body_mapping = np.eye(2) / body_scale
            body = affine(Image.fromarray(pixels), body_mapping, source_pivot - body_mapping @ dest_pivot)
            grip_out = dest_pivot + (grip - source_pivot) * body_scale

            length_px, width = {
                "s2rise-1": (65, 25), "s2rise-2": (66, 26), "s2rise-3": (62, 27),
                "s2slam-1": (61, 25), "s2slam-2": (51, 30), "s2slam-3": (60, 30),
            }[name]
            # 45도 하강 자세는 손에서 바닥까지의 공간을 넘기지 않고,
            # 바닥에 닿는 두 자세는 파이프 끝 아랫면으로 높이를 맞춘다.
            length_out = length_px / scale
            angle = math.atan2(*axis[::-1])
            contact_y = {"s2rise-1": SOURCE_ANCHOR[1] - 2 / scale - 5,
                         "s2slam-3": SOURCE_ANCHOR[1] + 2}
            if name in contact_y:
                tip_y = contact_y[name]
                angle = math.asin((tip_y - grip_out[1]) / length_out)
            elif name == "s2slam-2":
                angle = math.pi / 4
            direction = np.array([math.cos(angle), math.sin(angle)])
            dest_normal = np.array([-direction[1], direction[0]])
            tip_out = grip_out + length_out * direction
            pipe_mapping = np.outer(axis, direction) * length / length_out
            pipe_mapping += np.outer(normal, dest_normal) * (2 * radius / width)
            pipe = affine(Image.fromarray(shaft), pipe_mapping, grip - pipe_mapping @ grip_out)
            pipe.alpha_composite(body)
            assert all(2 < a < n - 2 for a, n in zip(pipe.getbbox()[:2], SOURCE_SIZE))
            assert all(a < n - 2 for a, n in zip(pipe.getbbox()[2:], SOURCE_SIZE))
            pipe.save(destination / f"{name}.png")
            registration[name] = {
                "body_scale": body_scale, "central_foot_anchor_source": SOURCE_ANCHOR.tolist(),
                "air_px": air_px, "grip": grip_out.tolist(), "tip": tip_out.tolist(),
                "angle_deg": math.degrees(angle), "exposed_length_px": length_px,
            }
    write_json(ROOT / "registration.json", registration)


def strip(frames, gap=12, bg=None):
    width = sum(frame.width for frame in frames) + gap * (len(frames) - 1)
    canvas = Image.new("RGBA", (width, max(frame.height for frame in frames)), bg)
    x = 0
    for frame in frames:
        canvas.alpha_composite(frame, (x, 0))
        x += frame.width + gap
    return canvas


def finish_metrics(frame, name, record, point):
    # 손과 끝 사이의 중앙부에서 실제 불투명 단면을 잰다.
    grip, tip = (point(record[key]) for key in ("grip", "tip"))
    direction = (tip - grip) / np.linalg.norm(tip - grip)
    normal = np.array([-direction[1], direction[0]])
    matte = frame.getchannel("A")
    alpha = np.asarray(matte)
    cuts = []
    for phase in np.linspace(0.27, 0.84, 13):
        center = grip + (tip - grip) * phase
        x, y = np.rint(center + np.arange(-7, 7, 0.25)[:, None] * normal).astype(int).T
        valid = (x >= 0) & (x < frame.width) & (y >= 0) & (y < frame.height)
        cuts.append(np.count_nonzero(alpha[y[valid], x[valid]]) / 4)
    tip_x = round(tip[0])
    cap = matte.crop((max(0, tip_x - 5), 0, min(frame.width, tip_x + 6), frame.height))
    # 바닥 가까이에서 몸보다 오른쪽에 있는 파이프 끝을 뺀다.
    feet_cut = 115 if name in {"s2rise-1", "s2slam-2", "s2slam-3"} else frame.width
    feet = matte.crop((0, 0, feet_cut, frame.height))
    return {
        "actual_opaque_bbox": frame.getbbox(), "pipe_grip": grip.round(1).tolist(),
        "pipe_tip_center": tip.round(1).tolist(),
        "shaft_median_px": round(float(np.median(cuts)), 2),
        "sole_bottom_y": feet.getbbox()[3] - 1,
        "tip_bottom_y": cap.getbbox()[3] - 1,
    }


def package(finished):
    metadata = json.loads((finished / "finish.json").read_text(encoding="utf-8"))
    records = json.loads((ROOT / "registration.json").read_text(encoding="utf-8"))
    final_native = sorted((finished / "frames").glob("*.png"))
    assert len(final_native) == len(STEPS)
    source_anchor = np.array(metadata["anchorSource"])
    scaled_anchor = np.array(metadata["anchor"])
    scale = metadata["scale"]

    def point(p):
        return scaled_anchor + (np.array(p) - source_anchor) * scale + FRAME_PADDING

    anchor = np.rint(point(SOURCE_ANCHOR)).astype(int)
    frames_folder = ROOT / "frames"
    frames_folder.mkdir(exist_ok=True)
    final_frames = []
    for name, path, delay in zip(STEPS, final_native, DELAYS_MS):
        original = rgba(path)
        frame = Image.new("RGBA", (original.width + 2 * FRAME_PADDING,
                                   original.height + 2 * FRAME_PADDING))
        frame.paste(original, (FRAME_PADDING, FRAME_PADDING))
        frame.save(frames_folder / f"{name}.png")
        final_frames.append(frame)
        records[name].update(finish_metrics(frame, name, records[name], point))
        records[name]["foot_anchor"] = anchor.tolist()
        records[name]["duration_ms"] = delay
        ground = anchor[1] - 1
        assert records[name]["sole_bottom_y"] == ground - records[name]["air_px"]
        if name == "s2slam-3":
            assert abs(records[name]["tip_bottom_y"] - ground) <= 1
        box = frame.getbbox()
        assert 0 < box[0] < box[2] < frame.width and 0 < box[1] < box[3] < frame.height, box
    strip(final_frames).save(ROOT / "strip_1x.png")
    previews = []
    for frame in final_frames:
        background = Image.new("RGBA", frame.size, "#252d3b")
        background.alpha_composite(frame)
        previews.append(background.convert("RGB"))
    previews[0].save(ROOT / "preview.gif", save_all=True, append_images=previews[1:],
                     duration=DELAYS_MS, loop=0, disposal=2)
    with Image.open(ROOT / "preview.gif") as gif:
        actual_delays = []
        for i in range(gif.n_frames):
            gif.seek(i)
            actual_delays.append(gif.info["duration"])
        assert actual_delays == DELAYS_MS
    write_json(ROOT / "checks.json", records)

    groups = [
        ("n09_swing_side", 4, (64, 149)), ("n09_plunge", 2, (58, 142)), ("n09_ult", 2, None),
    ]
    tracks = [[(frame, tuple(anchor)) for frame in final_frames[:3]],
              [(frame, tuple(anchor)) for frame in final_frames[3:]]]
    for stem, count, ref_anchor in groups:
        images = [rgba(UNIFIED / f"{stem}_{i}.png") for i in range(1, count + 1)]
        tracks.append([(frame, ref_anchor or (frame.width // 2, frame.getbbox()[3] - 1))
                       for frame in images])

    # 원본 크기로만 붙이고 각 행에 기준 바닥선을 그린다.
    left = 8 + max(anchor[0] for track in tracks for _, anchor in track)
    floor = 8 + max(anchor[1] for track in tracks for _, anchor in track)
    right = 8 + max(frame.width - anchor[0] for track in tracks for frame, anchor in track)
    bottom = 9 + max(frame.height - anchor[1] for track in tracks for frame, anchor in track)
    rows = []
    for track in tracks:
        tiles = []
        for frame, (x, y) in track:
            tile = Image.new("RGBA", (left + right, floor + bottom), "#252d3b")
            tile.paste("#526079", (0, floor, tile.width, floor + 1))
            tile.alpha_composite(frame, (left - x, floor - y))
            tiles.append(tile)
        rows.append(strip(tiles, gap=4))
    comparison = Image.new("RGBA", (max(row.width for row in rows), sum(row.height for row in rows)),
                           "#161c27")
    y = 0
    for row in rows:
        comparison.alpha_composite(row, (0, y))
        y += row.height
    comparison.save(ROOT / "comparison_1x.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["layout", "prepare", "package"])
    parser.add_argument("--finished", type=Path)
    args = parser.parse_args()
    if args.step == "layout":
        layout()
    elif args.step == "prepare":
        prepare()
    else:
        package(args.finished)


if __name__ == "__main__":
    main()

