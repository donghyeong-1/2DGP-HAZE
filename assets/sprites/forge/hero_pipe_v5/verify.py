"""T18의 바닥선, 픽셀·GIF 보존 여부 및 1배 시트를 확인한다."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
DIRECTIONS = ("side", "upfwd", "downfwd", "up", "down")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_direction(direction, palette):
    work = ROOT / direction
    folder = FORGE / f"n09_swing_{direction}_v5"
    details = read_json(folder / "assembly.json")
    process = read_json(work / "processed/pipeline-meta.json")
    stage = FORGE / details["frames"][1]["source"]
    finish_path = stage.parent.parent / "finish.json"
    finish = read_json(finish_path)
    for data in (process, finish):
        assert all(x["status"] in ("pass", "skipped") for x in data["qa"]["checks"]), direction
    source_sha = hashlib.sha256((work / "source.png").read_bytes()).hexdigest()
    assert source_sha == process["provenance"]["input_sha256"]
    colors = set()
    sole_spans = []
    expected_floor = details["anchor"][1] - 1
    with Image.open(folder / "preview.gif") as preview:
        assert preview.n_frames == 5
        for index, row in enumerate(details["frames"], 1):
            frame = Image.open(folder / f"frames/sheet-{index}.png").convert("RGBA")
            left, top, right, bottom = frame.getbbox()
            assert [left, top, right, bottom] == row["opaque_box"]
            assert left > 0 and top > 0 and right < frame.width and bottom - 1 == expected_floor
            assert frame.size == tuple(details["size"])
            pixels = np.asarray(frame)
            assert set(np.unique(pixels[:, :, 3])) == {0, 255}
            rgb = np.unique(pixels[pixels[:, :, 3] > 0][:, :3], axis=0)
            colors |= {"#%02x%02x%02x" % tuple(color) for color in rgb}
            _, components = ndimage.label(pixels[:, :, 3] > 0, structure=np.ones((3, 3), int))
            assert components == 1, (direction, index, components)
            soles = np.nonzero(pixels[bottom-3, :, 3])[0] - details["anchor"][0]
            sole_spans.append([int(soles.min()), int(soles.max())])

            old_index = {1: 1, 3: 2, 4: 3}.get(index)
            if old_index:
                old = Image.open(FORGE.parent / f"unified/n09_swing_{direction}_{old_index}.png").convert("RGBA")
                x, y = details["translation_from_v4"]
                assert old.tobytes() == frame.crop((x, y, x + old.width, y + old.height)).tobytes()
                assert pixels[:, :, 3].sum() == np.asarray(old)[:, :, 3].sum()
            else:
                assert 5 <= row["shaft_width_median_px"] <= 6
                assert 121 <= row["hair_to_floor_px"] <= 124

            preview.seek(index - 1)
            background = Image.new("RGBA", frame.size, "#252d3b")
            background.alpha_composite(frame)
            assert preview.info["duration"] == details["timing_ms"][index - 1]
            assert preview.convert("RGB").tobytes() == background.convert("RGB").tobytes()

    assert colors <= palette
    print(direction, details["size"], details["anchor"], "bottom", expected_floor, "colors", len(colors),
          "sole X", sole_spans)
    return {
        "art_source": "host_image",
        "route": "Codex host image_gen",
        "model": None,
        "estimateUsd": None,
        "source": f"{direction}/source.png",
        "sourceSha256": source_sha,
        "size": process["provenance"]["size"],
        "prompt": f"{direction}/actual_prompt.txt",
        "body_reference": "../hero_v3b/master/master_rgba.png",
        "pose_reference": f"../n09_swing_{direction}_v4_strip_1x.png",
        "finish": finish_path.relative_to(ROOT).as_posix(),
        "finishToolVersion": finish["qa"]["tool"]["version"],
        "finishOverallStatus": finish["qa"]["status"],
        "paletteColorsUsed": len(colors),
        "floorOpaqueY": expected_floor,
        "soleXSpanRelativeToAnchor": sole_spans,
        "gifTimingVerified": details["timing_ms"],
        "exactKeyFrameRGBA": [1, 3, 4],
    }


def main():
    colors = read_json(FORGE / "n09_v3b/palette.json")["colors"]
    palette = {color["hex"] for color in colors} | {"#0b1020"}
    records = {direction: verify_direction(direction, palette) for direction in DIRECTIONS}
    sheets = [Image.open(FORGE / f"n09_swing_{direction}_v5/strip_1x.png").convert("RGBA")
              for direction in DIRECTIONS]
    combined = Image.new("RGBA", (max(row.width for row in sheets), sum(row.height for row in sheets) + 32), "#252d3b")
    y = 0
    for row in sheets:
        combined.alpha_composite(row, (0, y))
        y += row.height + 8
    combined.save(ROOT / "review_1x.png")
    dates = {direction: "2026-11-17" if direction in ("side", "upfwd") else "2026-11-18"
             for direction in DIRECTIONS}
    (ROOT / "provenance.json").write_text(json.dumps({
        "generatedDatesKST": dates, "directions": records,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
