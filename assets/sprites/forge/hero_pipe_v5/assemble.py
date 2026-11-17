"""T15 원본과 두 hibit 삽입 프레임을 같은 발 기준점으로 묶는다."""
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
UNIFIED = FORGE.parent / "unified"
TIMING = [30, 40, 100, 80, 60]


def rgba(path):
    return Image.open(path).convert("RGBA")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pipe_checks(frame, origin, angle, length, anchor):
    """파이프 중앙부의 1배 불투명 단면과 머리·발 픽셀을 잰다."""
    alpha = np.array(frame.getchannel("A"))
    rgb = np.array(frame.convert("RGB"))
    bright_hair = (rgb[:, :, 0] >= 190) & (rgb[:, :, 2] >= 190) & (alpha == 255)
    foot_x, floor = anchor
    hair_y = next(
        y for y in range(max(0, floor - 128), floor - 105)
        if np.count_nonzero(bright_hair[y, max(0, foot_x - 23):foot_x + 27]) >= 3
    )
    axis = np.array([math.cos(angle), math.sin(angle)])
    normal = np.array([-axis[1], axis[0]])
    widths = []
    for distance in np.linspace(12, length - 10, 11):
        point = np.array(origin) + distance * axis
        coords = np.rint(point + np.arange(-6, 6, 0.25)[:, None] * normal).astype(int)
        x, y = coords.T
        inside = (x >= 0) & (x < frame.width) & (y >= 0) & (y < frame.height)
        x, y = x[inside], y[inside]
        widths.append(float(np.count_nonzero(alpha[y, x])) / 4)
    return {
        "shaft_width_median_px": float(np.median(widths)),
        "shaft_width_range_px": [min(widths), max(widths)],
        "hair_to_floor_px": floor - hair_y + 1,
        "bottom_opaque_y": frame.getbbox()[3] - 1,
    }


def main():
    direction = sys.argv[1]
    name = f"n09_swing_{direction}_v5"
    build = ROOT / direction
    staged = build / (sys.argv[2] if len(sys.argv) > 2 else name)
    prior = FORGE / f"n09_swing_{direction}_v4"
    old = read_json(prior / "assembly.json")
    new = read_json(staged / "finish.json")
    original = [prior / f"frames/sheet-{index}.png" for index in range(1, 4)]
    for index, path in enumerate(original, 1):
        assert rgba(UNIFIED / f"n09_swing_{direction}_{index}.png").tobytes() == rgba(path).tobytes()
    additions = sorted((staged / "frames").glob("*.png"))
    assert len(additions) == 2
    order = [original[0], additions[0], original[1], original[2], additions[1]]
    frames = list(map(rgba, order))
    shift = tuple(a - b for a, b in zip(old["anchor"], new["anchor"]))
    offsets = [(0, 0), shift, (0, 0), (0, 0), shift]
    rectangles = [
        (box[0] + x, box[1] + y, box[2] + x, box[3] + y)
        for frame, (x, y) in zip(frames, offsets)
        for box in [frame.getbbox()]
    ]
    left = min(0, min(box[0] for box in rectangles) - 1)
    top = min(0, min(box[1] for box in rectangles) - 1)
    width = max(old["size"][0], max(box[2] for box in rectangles) + 1) - left
    height = max(old["size"][1], max(box[3] for box in rectangles)) - top
    common_anchor = (old["anchor"][0] - left, old["anchor"][1] - top)

    out = FORGE / name
    (out / "frames").mkdir(parents=True, exist_ok=True)
    strip = Image.new("RGBA", (width * 5 + 16, height))
    all_frames = []
    check = []
    reg = iter(read_json(build / "registration.json"))
    for i, (frame, (x, y), source) in enumerate(zip(frames, offsets, order), 1):
        full = Image.new("RGBA", (width, height))
        origin = (x - left, y - top)
        full.paste(frame, origin)
        assert full.crop((origin[0], origin[1], origin[0] + frame.width, origin[1] + frame.height)).tobytes() == frame.tobytes()
        dest = out / f"frames/sheet-{i}.png"
        if (width, height) == frame.size and origin == (0, 0):
            shutil.copyfile(source, dest)
        else:
            full.save(dest)
        strip.paste(full, ((width + 4) * (i - 1), 0))
        all_frames.append(full)
        record = {"frame": i, "source": str(source.relative_to(FORGE)).replace("\\", "/"),
                  "anchor": common_anchor, "opaque_box": full.getbbox()}
        if i in (2, 5):
            measured = next(reg)
            grip = tuple(
                floor + (hand - pivot) * new["scale"]
                for hand, pivot, floor in zip(measured["grip"], new["anchorSource"], common_anchor)
            )
            record.update(pipe_checks(full, grip, math.radians(measured["angle_deg"]), 68, common_anchor))
            record["shaft_direction_deg"] = round(measured["angle_deg"], 2)
            record["shaft_length_target_px"] = 68
        check.append(record)

    strip.save(out / "strip_1x.png")
    # 불투명 배경의 검토용 GIF를 써서 각 GIF 플레이어의 프레임 투명 처리 차이를 피한다.
    previews = []
    for frame in all_frames:
        background = Image.new("RGBA", frame.size, "#252d3b")
        background.alpha_composite(frame)
        previews.append(background.convert("RGB"))
    previews[0].save(out / "preview.gif", save_all=True, append_images=previews[1:],
                     duration=TIMING, loop=0, disposal=2)
    (out / "assembly.json").write_text(json.dumps({
        "size": (width, height), "anchor": common_anchor,
        "translation_from_v4": (-left, -top), "timing_ms": TIMING, "frames": check,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
