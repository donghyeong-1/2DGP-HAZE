"""T21 원화 8장의 허리 위치와 접지·체공 높이를 등록한다."""
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("prior_register", ROOT.parent / "hero_run_v1/register.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
BELTS = {
    "A": [(321, 308), (306, 312), (330, 294), (329, 276)],
    "B": [(324, 300), (317, 306), (318, 287), (328, 272)],
}
HEIGHTS = [(121, 65, 0), (119, 62, 0), (122, 65, 0), (125, 68, 8)]
RAW_X_SCALE = 0.18


def main():
    attempt = sys.argv[1] if len(sys.argv) > 1 else ""
    raw = ROOT / (sys.argv[2] if len(sys.argv)>2 else f"registered_{attempt}" if attempt else "registered")
    raw.mkdir(exist_ok=False)
    records = []
    for step in ("A", "B"):
        sheet = Image.open(ROOT / step / attempt / "processed/raw-sheet-clean.png").convert("RGBA")
        width, height = sheet.width // 2, sheet.height // 2
        for i, (belt, pose_height) in enumerate(zip(BELTS[step], HEIGHTS)):
            row, col = divmod(i, 2)
            cell = sheet.crop((col*width, row*height, (col+1)*width, (row+1)*height))
            final, top, bottom = prior.measure_and_place(cell, belt, pose_height, RAW_X_SCALE, 0)
            index = i + (1 if step == "A" else 5)
            final.save(raw / f"run-{index}.png")
            records.append({
                "frame": index, "source_step": step, "source_cell": i+1, "source_belt": belt,
                "source_bbox_top": top, "source_bbox_bottom": bottom,
                "head_height_target": pose_height[0], "belt_height_target": pose_height[1],
                "air_clearance_target": pose_height[2],
            })
    (raw / "registration.json").write_text(json.dumps({
        "source_anchor": prior.ANCHOR, "raw_x_scale": RAW_X_SCALE, "frames": records,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
