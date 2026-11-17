"""게임용 PNG와 같은 픽셀을 쓰는 1배 검토 자료를 만든다."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


ROOT = Path(__file__).resolve().parent
FORGE = ROOT.parent
UNIFIED = FORGE.parent / "unified"
RUN_TIMES = [80, 80, 70, 80] * 2  # GIF는 10ms 단위. 게임 기준 장당 약 78ms.
BG = "#252d3b"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def measure(frame, pose, pivot, game_x_ratio):
    x0, y0 = pivot
    belt_y = y0 - 1 - pose["belt_target_above_floor_px"]
    pixels = np.asarray(frame, dtype=np.int16)
    red, green, blue, alpha = pixels.transpose(2, 0, 1)
    teal = (green > 82) & (green >= red * 1.45) & (blue >= red * 1.36) & (alpha == 255)
    ys, xs = np.where(teal)
    within_belt = (abs(xs - x0) <= 7) & (abs(ys - belt_y) <= 3)
    assert within_belt.any()
    left, top, right, bottom = frame.getbbox()
    assert left > 0 and top > 0 and right < frame.width and bottom < frame.height
    colors = {"#%02x%02x%02x" % tuple(color) for color in np.unique(pixels[alpha == 255, :3], axis=0)}
    assert set(np.unique(alpha)) == {0, 255}
    _, components = ndimage.label(alpha == 255, structure=np.ones((3, 3), int))
    assert components == 1
    boots = [round(x0 + (boot_x - pose["source_belt"][0]) * game_x_ratio)
             for boot_x in pose["source_boot_centers_x"]]
    assert all((alpha[round(belt_y):, max(0, x-2):x+3] == 255).any() for x in boots)
    return {
        "index": pose["frame"], "belt_x": float(np.median(xs[within_belt])),
        "belt_y": float(np.median(ys[within_belt])), "bottom_y_exclusive": bottom,
        "floor_y_exclusive": y0, "air_clearance_px": y0 - bottom, "head_top_y": top,
        "boot_centers_x_estimate": boots, "boot_spacing_px_estimate": boots[1] - boots[0],
    }, colors


def strip_png(frames, path):
    w, h = frames[0].size
    strip = Image.new("RGBA", (len(frames) * (w + 4) - 4, h))
    for index, frame in enumerate(frames):
        assert frame.size == (w, h)
        strip.paste(frame, (index * (w + 4), 0))
    strip.save(path)


def save_gif(frames, timing, path):
    rgb_frames = []
    for frame in frames:
        background = Image.new("RGBA", frame.size, BG)
        background.alpha_composite(frame)
        rgb_frames.append(background.convert("RGB"))
    rgb_frames[0].save(path, save_all=True, append_images=rgb_frames[1:],
                       duration=timing, loop=0, disposal=2)
    with Image.open(path) as rendered:
        assert rendered.n_frames == len(rgb_frames)
        for i, (frame, duration) in enumerate(zip(rgb_frames, timing)):
            rendered.seek(i)
            assert rendered.info["duration"] == duration
            assert rendered.convert("RGB").tobytes() == frame.tobytes()


def align_for_preview(clips):
    left = max(pivot[0] for _, pivot in clips) + 2
    top = max(pivot[1] for _, pivot in clips) + 2
    width = left + max(frame.width - pivot[0] for frame, pivot in clips) + 2
    height = top + max(frame.height - pivot[1] for frame, pivot in clips) + 2
    aligned = []
    for frame, pivot in clips:
        canvas = Image.new("RGBA", (width, height))
        canvas.paste(frame, (left - pivot[0], top - pivot[1]))
        aligned.append(canvas)
    return aligned


def publish(group, folder_name, stage_name, source_reg):
    workspace = ROOT / group
    staged = workspace / stage_name
    finish = read_json(staged / "finish.json")
    registration = read_json(workspace / source_reg)
    process = read_json(workspace / "processed/pipeline-meta.json")
    for qa in (process["qa"], finish["qa"]):
        assert all(check["status"] in ("pass", "skipped") for check in qa["checks"])
    assert hashlib.sha256((workspace / "sheet_input.png").read_bytes()).hexdigest() == process["provenance"]["input_sha256"]
    anchor = [round(p + (q - r) * finish["scale"]) for p, q, r in
              zip(finish["anchor"], registration["source_anchor"], finish["anchorSource"])]
    sources = sorted((staged / "frames").glob("*.png"))
    assert len(sources) == len(registration["poses"])
    frames = [Image.open(source).convert("RGBA") for source in sources]
    measurements = []
    used = set()
    for frame, pose in zip(frames, registration["poses"]):
        record, colors = measure(frame, pose, anchor, registration["game_px_per_source_px_x"])
        measurements.append(record)
        used |= colors
    palette = {color["hex"] for color in read_json(FORGE / "n09_v3b/palette.json")["colors"]} | {"#0b1020"}
    assert used <= palette
    for record, pose in zip(measurements, registration["poses"]):
        assert abs(record["air_clearance_px"] - pose["foot_clearance_target_px"]) <= 1
        if group == "run":
            assert abs(record["belt_x"] - anchor[0]) <= 2
    out = FORGE / folder_name
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for source in sources:
        shutil.copyfile(source, out / "frames" / source.name)
    strip_png(frames, out / "strip_1x.png")
    document = {
        "size": frames[0].size, "anchor": anchor, "colors_used": len(used),
        "frames": measurements,
    }
    if group == "run":
        document["timing"] = {"distance_px_per_frame": 37.5, "nominal_ms_per_frame": 78,
                              "preview_ms": RUN_TIMES}
    else:
        document["timing"] = {"start_ms": [60, 60], "stop_ms": [80, 80], "turn_ms": 80}
    (out / "registration.json").write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(folder_name, document)
    return [(frame, anchor) for frame in frames]


def main():
    run = publish("run", "n09_run_v1", "n09_run_v1_refined", "registered_refined/registration.json")
    trans = publish("trans", "n09_run_trans_v1", "n09_run_trans_v1", "registration.json")
    save_gif([frame for frame, _ in run], RUN_TIMES, FORGE / "n09_run_v1/run_1x.gif")
    idle = (Image.open(UNIFIED / "n09_idle_1.png").convert("RGBA"), (21, 124))
    sequence = [idle, *trans[:2], *run, *run, *trans[2:4], idle]
    save_gif(align_for_preview(sequence), [300, 60, 60, *RUN_TIMES, *RUN_TIMES, 80, 80, 300],
             FORGE / "n09_run_trans_v1/start_run_stop_1x.gif")
    sample = [idle, (Image.open(UNIFIED / "n09_walk_1.png").convert("RGBA"), (36, 126)),
              run[0], run[3], run[4], run[7], *trans]
    strip_png(align_for_preview(sample), ROOT / "compare_1x.png")
    provenance = {
        "date_kst": "2026-11-18", "art_source": "host_image", "route": "Codex image_gen",
        "model": None, "estimateUsd": None, "tools": "generate2dsprite process / hibit 0.5.0",
    }
    for group in ("run", "trans"):
        folder = ROOT / group
        provenance[group] = {
            "source": f"{group}/source.png", "prompt": f"{group}/actual_prompt.txt",
            "guide": "run_pose_guide.png" if group == "run" else "transition_pose_guide.png",
            "raw_sha256": hashlib.sha256((folder / "source.png").read_bytes()).hexdigest(),
            "size": Image.open(folder / "source.png").size,
        }
    (ROOT / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
