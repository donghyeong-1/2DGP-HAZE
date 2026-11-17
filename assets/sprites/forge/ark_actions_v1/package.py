"""T20 프레임을 검사하고 1배 확인판과 GIF를 만든다."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from build import ACTIONS, FORGE, REFERENCE, REPO, ROOT, read_json, write_json


TIMINGS = {
    "barrage": [600, 160], "slash": [450, 100, 180], "absorb": [900, 220],
    "overcharge": [900, 220], "field": [700, 220], "idle": [400, 400],
    "walk": [180, 180, 180, 180], "vanish": [180], "appear": [160],
    "hurt": [100], "phase": [900], "death": [350, 900],
}
BG = "#252d3b"


def rgba(path):
    return Image.open(path).convert("RGBA")


def make_board(items, columns, destination):
    max_left = max(anchor[0] for _, _, anchor in items)
    max_top = max(anchor[1] for _, _, anchor in items)
    max_right = max(frame.width - anchor[0] for _, frame, anchor in items)
    max_bottom = max(frame.height - anchor[1] for _, frame, anchor in items)
    width, height = max_left + max_right + 12, max_top + max_bottom + 28
    board = Image.new("RGBA", (width*columns, height*((len(items)+columns-1)//columns)), BG)
    draw = ImageDraw.Draw(board)
    for index, (name, frame, anchor) in enumerate(items):
        y, x = divmod(index, columns)
        px, py = x*width+6+max_left-anchor[0], y*height+22+max_top-anchor[1]
        board.alpha_composite(frame, (px, py))
        draw.text((x*width+6, y*height+5), name, fill="#e8eef7")
    board.save(destination)


def make_gif(frames, timing, path):
    previews = []
    for frame in frames:
        canvas = Image.new("RGBA", frame.size, BG)
        canvas.alpha_composite(frame)
        previews.append(canvas.convert("RGB"))
    previews[0].save(path, save_all=True, append_images=previews[1:],
                     duration=timing, loop=0, disposal=2)
    with Image.open(path) as animated:
        assert animated.n_frames == len(frames)
        for index, expected in enumerate(previews):
            animated.seek(index)
            assert animated.info["duration"] == timing[index]
            assert animated.convert("RGB").tobytes() == expected.tobytes()


def check_command(files, options):
    result = subprocess.run([sys.executable, "-B", str(REPO / "tools/check_sprites.py"),
                             *map(str, files), *options],
                            capture_output=True, text=True, encoding="utf-8")
    return result.returncode, result.stdout + result.stderr


def main():
    palette = {color["hex"] for color in read_json(REFERENCE / "palette.json")["colors"]} | {"#0b1020"}
    master = rgba(REPO / "assets/sprites/unified/boss_ark_idle.png")
    master_finish = read_json(REFERENCE / "finish.json")
    all_items = [("master", master, master_finish["anchor"])]
    tells = []
    manifest = {"date_kst": "2026-11-18", "art_source": "host_image",
                "route": "Codex image_gen", "model": None, "estimateUsd": None, "actions": {}}
    checks = []
    for group, actions in ACTIONS.items():
        workspace = ROOT / group
        process = read_json(workspace / "processed/pipeline-meta.json")
        assert process["qa"]["status"] == "pass"
        assert hashlib.sha256((workspace / "input.png").read_bytes()).hexdigest() == process["provenance"]["input_sha256"]
        manifest[group] = {
            "source": f"{group}/source.png", "prompt": f"{group}/actual_prompt.txt",
            "sha256": hashlib.sha256((workspace / "source.png").read_bytes()).hexdigest(),
            "size": Image.open(workspace / "source.png").size,
        }
        for name, indices in actions:
            output = FORGE / f"boss_ark_{name}_v1"
            metadata = read_json(output / "finish.json")
            assert all(check["status"] in ("pass", "skipped") for check in metadata["qa"]["checks"])
            files = sorted((output / "frames").glob("*.png"))
            assert len(files) == len(indices)
            frames = list(map(rgba, files))
            all_colors = set()
            measured = []
            for index, (path, frame) in enumerate(zip(files, frames), 1):
                pixels = np.asarray(frame, dtype=np.int16)
                alpha = pixels[:, :, 3]
                assert set(np.unique(alpha)) == {0, 255}
                colors = {"#%02x%02x%02x" % tuple(color) for color in np.unique(pixels[alpha==255, :3], axis=0)}
                assert colors <= palette
                all_colors |= colors
                box = frame.getbbox()
                assert box[0] > 0 and box[1] > 0 and box[2] < frame.width and box[3] < frame.height
                record = {"frame": index, "size": frame.size, "box": box,
                          "opaque_height": box[3]-box[1], "bottom_y_exclusive": box[3],
                          "colors": len(colors), "semi_transparent": 0}
                if name == "walk":
                    red, green, blue = pixels[:, :, :3].transpose(2, 0, 1)
                    yy, xx = np.indices(alpha.shape)
                    cx, cy = metadata["anchor"][0], metadata["anchor"][1]-94
                    buckle = ((abs(red-green)<13) & (abs(green-blue)<13) & (red>68) &
                              (alpha==255) & (abs(xx-cx)<13) & (abs(yy-cy)<4))
                    y, x = np.where(buckle)
                    assert len(x)
                    record["belt_buckle_xy"] = [float(np.median(x)), float(np.median(y))]
                measured.append(record)
                all_items.append((f"{name}-{index}", frame, metadata["anchor"]))
            assert len({row["bottom_y_exclusive"] for row in measured}) == 1
            if name == "walk":
                xs = [row["belt_buckle_xy"][0] for row in measured]
                assert max(xs)-min(xs) <= 4
            make_gif(frames, TIMINGS[name], output / "preview.gif")
            if group == "A":
                tells.append((name, frames[0], metadata["anchor"]))
            code, text = check_command(files, [])
            checks.append(f"## {name} / 기본 (exit {code})\n{text}")
            if code:
                # 숙임·눕기·높이 든 주먹은 전신 서 있는 키와 다르다.
                options = ["--air"] if len(files)>1 else ["--height", str(measured[0]["opaque_height"])]
                code, text = check_command(files, options)
                checks.append(f"## {name} / {' '.join(options)} (exit {code})\n{text}")
                assert code == 0
            manifest["actions"][name] = {
                "folder": output.relative_to(FORGE).as_posix(), "size": metadata["size"],
                "anchor": metadata["anchor"], "colors_used": len(all_colors),
                "preview_timing_ms": TIMINGS[name], "frames": measured,
                "finish_status": metadata["qa"]["status"],
            }
    assert len(all_items) == 24 and len(tells) == 5
    make_board(tells, 5, ROOT / "telegraphs_1x.png")
    make_board(all_items, 4, ROOT / "review_1x.png")
    (ROOT / "check_sprites.txt").write_text("\n".join(checks), encoding="utf-8")
    write_json(ROOT / "provenance.json", manifest)
    for name, data in manifest["actions"].items():
        print(name, data["size"], data["anchor"], "colors", data["colors_used"],
              "height", [x["opaque_height"] for x in data["frames"]])


if __name__ == "__main__":
    main()
