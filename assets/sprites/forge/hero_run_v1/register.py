"""원화의 허리와 착지선으로 프레임을 등록한다. 픽셀 마감은 프로젝트 도구가 한다."""
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
SCALE = json.loads((ROOT.parent / "n09_v3b/finish.json").read_text())["scale"]
SIZE = (1200, 1040)
ANCHOR = (600, 900)


def measure_and_place(cell, belt, shape, x_factor, lean):
    left, top, right, sole = cell.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()
    bx, by = belt
    assert left < bx < right and top < by < sole
    head, pelvis, clearance = shape
    dest_top = ANCHOR[1] - head / SCALE
    dest_belt = round(ANCHOR[1] - pelvis / SCALE)
    dest_sole = ANCHOR[1] - clearance / SCALE
    upper = (by - top) / (dest_belt - dest_top)
    lower = (sole - by) / (dest_sole - dest_belt)
    left_src = bx - ANCHOR[0] * SCALE / x_factor
    right_src = left_src + SIZE[0] * SCALE / x_factor
    top_src = by - dest_belt * upper
    bottom_src = by + (SIZE[1] - dest_belt) * lower
    top_shift = lean / x_factor * dest_belt / (dest_belt - dest_top)
    mesh = [
        ((0, 0, SIZE[0], dest_belt),
         (left_src - top_shift, top_src, left_src, by, right_src, by, right_src - top_shift, top_src)),
        ((0, dest_belt, *SIZE), (left_src, by, left_src, bottom_src, right_src, bottom_src, right_src, by)),
    ]
    out = cell.transform(SIZE, Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)
    a = out.getchannel("A").getbbox()
    assert a[0] > 2 and a[1] > 2 and a[2] < SIZE[0]-2 and a[3] < SIZE[1]-2
    return out, top, sole


def main():
    folder = ROOT / sys.argv[1]
    config = json.loads((folder / "landmarks.json").read_text(encoding="utf-8"))
    source = Image.open(folder / "processed/raw-sheet-clean.png").convert("RGBA")
    raw = folder / (sys.argv[2] if len(sys.argv) > 2 else "registered")
    raw.mkdir(exist_ok=False)
    columns, rows = config["columns"], config["rows"]
    recorded = []
    for index, pose in enumerate(config["poses"]):
        row, col = divmod(index, columns)
        x1, x2 = source.width * col // columns, source.width * (col + 1) // columns
        y1, y2 = source.height * row // rows, source.height * (row + 1) // rows
        cell = source.crop((x1, y1, x2, y2))
        belt = (pose["belt"][0] - x1, pose["belt"][1] - y1)
        converted, top, sole = measure_and_place(cell, belt, pose["height"], config["x_px_per_source_px"],
                                                pose.get("lean_px", 0))
        converted.save(raw / f"{folder.name}-{index + 1}.png")
        recorded.append({
            "frame": index + 1, "source_crop": (x1, y1, x2, y2), "source_belt": pose["belt"],
            "source_head_y": top + y1, "source_sole_y_exclusive": sole + y1,
            "belt_target_above_floor_px": pose["height"][1],
            "foot_clearance_target_px": pose["height"][2],
            "source_boot_centers_x": pose["boots_x"],
            "upper_lean_adjustment_px": pose.get("lean_px", 0),
        })
    (raw / "registration.json").write_text(json.dumps({
        "source_anchor": ANCHOR, "poses": recorded, "game_px_per_source_px_x": config["x_px_per_source_px"],
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
