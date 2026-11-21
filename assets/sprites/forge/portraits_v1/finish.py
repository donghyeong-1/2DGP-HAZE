"""T32 원화 두 컷을 동일 배율의 200px 대화 초상화로 마감한다."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
sys.path.insert(0, str(Path.home() / ".codex/skills/generate2dsprite/scripts"))
from forge_matte import soft_matte
from forge_palette import build_palette, quantize_image, render_indices

ACTORS = ("n09", "mechanic", "keeper", "archivist")
MIRROR_SOURCE = {"archivist"}
SIZE = 200
ART = 180
JOIN = np.ones((3, 3), dtype=bool)

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def cut_cells(sheet):
    midpoint = sheet.width // 2
    result = []
    for left, right in ((0, midpoint), (midpoint, sheet.width)):
        cell = np.asarray(sheet.crop((left, 0, right, sheet.height)))
        matte = soft_matte(cell, key="magenta")
        opaque = matte[:, :, 3] >= 128
        components, _ = label(opaque, JOIN)
        areas = np.bincount(components[opaque])
        assert areas.size > 1, "원화에 초상화가 없다"
        # 축소 전에 배경에 떨어진 작은 키잉 잔여물만 제외한다.
        keep = np.flatnonzero(areas >= 64)
        keep = keep[keep != 0]
        matte[opaque & ~np.isin(components, keep), 3] = 0
        alpha = Image.fromarray(np.uint8(matte[:, :, 3] >= 128) * 255)
        box = alpha.getbbox()
        assert min(box[0], box[1], right - left - box[2], sheet.height - box[3]) > 0, box
        result.append((Image.fromarray(matte).crop(box), box))
    return result


def frame_pair(cells):
    width = max(crop.width for crop, _ in cells)
    height = max(crop.height for crop, _ in cells)
    scale = ART / max(width, height)
    assert scale < 1, scale
    fitted = []
    for crop, _ in cells:
        size = round(crop.width * scale), round(crop.height * scale)
        resized = crop.resize(size, Image.Resampling.NEAREST)
        frame = Image.new("RGBA", (SIZE, SIZE))
        frame.paste(resized, ((SIZE - resized.width) // 2, (SIZE - round(height * scale)) // 2))
        fitted.append(frame)
    return fitted, scale


def finish(actor):
    with Image.open(ROOT / "source" / f"{actor}.png") as source:
        sheet = source.convert("RGB")
    cells = cut_cells(sheet)
    mirrored = actor in MIRROR_SOURCE
    if mirrored:
        cells = [(crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT), box) for crop, box in cells]
    framed, scale = frame_pair(cells)
    palette = build_palette(framed, 32, seed=0)
    save_json(ROOT / "source" / f"{actor}_palette.json", palette.to_json())
    result = {"source_size": list(sheet.size), "source_mirrored": mirrored, "scale": scale, "portraits": []}
    rendered = []
    for i, (frame, (_, source_box)) in enumerate(zip(framed, cells), 1):
        rgba = render_indices(quantize_image(frame, palette, alpha_threshold=128), palette)
        opaque = rgba[:, :, 3] == 255
        rgb = rgba[opaque, :3].astype(int)
        colors = len(np.unique(rgb, axis=0))
        spill = ((rgb[:, 0] > 160) & (rgb[:, 2] > 140) &
                 (rgb[:, 0] - rgb[:, 1] > 100) & (rgb[:, 2] - rgb[:, 1] > 100)).sum()
        image = Image.fromarray(rgba)
        box = image.getbbox()
        assert image.size == (SIZE, SIZE)
        assert 0 < box[0] < box[2] < SIZE and 0 < box[1] < box[3] < SIZE
        assert 0 < colors <= 32 and set(np.unique(rgba[:, :, 3])) == {0, 255}
        assert spill == 0, (actor, i, spill)
        out = ROOT / f"{actor}_{i}.png"
        image.save(out)
        result["portraits"].append({
            "file": out.name, "source_box_in_cell": list(source_box),
            "opaque_bounds": list(box), "colors": colors, "partial_alpha": 0,
            "magenta_spill_pixels": int(spill),
        })
        rendered.append(rgba)
    a, b = rendered
    mask_a, mask_b = a[:, :, 3] == 255, b[:, :, 3] == 255
    common = mask_a & mask_b
    result["silhouette_iou"] = round(float(common.sum() / (mask_a | mask_b).sum()), 3)
    delta = np.max(np.abs(a.astype(int) - b.astype(int))[:, :, :3], axis=2)
    result["shared_opaque_pixels_changed_by_24_or_more"] = round(float((delta[common] >= 24).mean()), 3)
    save_json(ROOT / "source" / f"{actor}_qa.json", result)
    print(actor, [picture["colors"] for picture in result["portraits"]], "colors")


def checks():
    lines = []
    errors = []
    for actor in ACTORS:
        portraits = [str((ROOT / f"{actor}_{i}.png").relative_to(REPO)) for i in (1, 2)]
        # 표정 그림에는 전신 높이와 발 위치 기준을 적용하지 않는다.
        command = [sys.executable, "-B", "tools/check_sprites.py", *portraits, "--air"]
        run = subprocess.run(command, cwd=REPO, encoding="utf-8", capture_output=True)
        lines.extend([f"## {actor} 1·2 (--air)\n", run.stdout, run.stderr, "\n"])
        if run.returncode:
            errors.append(actor)
    (ROOT / "check_sprites.txt").write_text("".join(lines), encoding="utf-8")
    if errors:
        raise SystemExit(", ".join(errors))
    print("check_sprites.py: 4 pairs (8 PNG) PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("finish", "check"))
    parser.add_argument("actor", choices=ACTORS, nargs="?")
    options = parser.parse_args()
    if options.step == "finish":
        finish(options.actor)
    else:
        checks()
