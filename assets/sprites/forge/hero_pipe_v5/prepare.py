"""T18 원화에서 파이프의 비율을 맞춘 후 마감 입력을 만든다."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
SCALE = 0.15394402035623408


def main():
    folder = ROOT / sys.argv[1]
    config = json.loads((folder / "points.json").read_text(encoding="utf-8"))
    sheet = Image.open(folder / "processed/raw-sheet-clean.png").convert("RGBA")
    out = folder / "frames_raw"
    out.mkdir(exist_ok=True)
    registrations = []
    for index, points in enumerate(config):
        boundary = index * (sheet.width // 2)
        cell = sheet.crop((boundary, 0, boundary + sheet.width // 2, sheet.height))
        pixels = np.array(cell)
        grip = np.array(points["grip"], dtype=float) - (boundary, 0)
        tip = np.array(points["tip"], dtype=float) - (boundary, 0)
        axis = tip - grip
        length = np.linalg.norm(axis)
        axis = axis / length
        cross = np.array([-axis[1], axis[0]])
        ys, xs = np.indices(pixels.shape[:2])
        axial = (xs - grip[0]) * axis[0] + (ys - grip[1]) * axis[1]
        lateral = (xs - grip[0]) * cross[0] + (ys - grip[1]) * cross[1]
        shaft_mask = (axial >= 0) & (abs(lateral) <= points["shaft_radius"])
        shaft = pixels.copy()
        shaft[~shaft_mask] = 0
        pixels[shaft_mask] = 0

        # 발과 머리로 정한 한 스케일을 적용한다. 이미 마감한 PNG는 다시 샘플링하지 않는다.
        body_scale = 786 / (points["feet"] - points["hair"])
        foot_x = points["foot_x"] - boundary
        dest = np.array([550, 980] if folder.name == "side" else [654, 1110], dtype=float)
        src = np.array([foot_x, points["feet"]], dtype=float)
        offset = src - dest / body_scale
        size = (1170, 1160) if folder.name == "side" else (1450, 1320)
        body_rgba = Image.fromarray(pixels)
        body = body_rgba.transform(
            size, Image.Transform.AFFINE,
            (1 / body_scale, 0, offset[0], 0, 1 / body_scale, offset[1]),
            Image.Resampling.BICUBIC,
        )
        grip_out = (grip - src) * body_scale + dest
        angle = math.radians(points.get("angle", math.degrees(math.atan2(axis[1], axis[0]))))
        out_axis = np.array([math.cos(angle), math.sin(angle)])
        length_out = 68 / SCALE
        tip_out = grip_out + out_axis * length_out
        assert all(16 < x < dim - 16 for x, dim in zip(tip_out, size)), tip_out
        out_cross = np.array([-out_axis[1], out_axis[0]])
        width_scale = points["width_scale"]
        mapping = np.outer(axis, out_axis) * length / length_out
        mapping += np.outer(cross, out_cross) / width_scale
        shift = grip - mapping @ grip_out
        layer = Image.fromarray(shaft).transform(
            size, Image.Transform.AFFINE,
            (mapping[0, 0], mapping[0, 1], shift[0],
             mapping[1, 0], mapping[1, 1], shift[1]),
            Image.Resampling.BICUBIC,
        )
        # 원화 손 레이어를 위에 놓아 손잡이가 손 앞을 가리지 않게 한다.
        layer.alpha_composite(body)
        layer.save(out / f"insert-{index + 1}.png")
        registrations.append({
            "foot": dest.tolist(),
            "grip": grip_out.tolist(),
            "tip": tip_out.tolist(),
            "angle_deg": math.degrees(angle),
            "body_scale": body_scale,
        })
    (folder / "registration.json").write_text(json.dumps(registrations, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
