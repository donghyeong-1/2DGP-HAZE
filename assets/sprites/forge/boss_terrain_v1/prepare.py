"""T43 격자 원화를 보스방에서 사용할 정확한 크기의 Hi-bit PNG로 마감한다."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SOURCE = ROOT / "source"
FINISH = Path.home() / ".codex/skills/video2dsprite/scripts/finish_frames.py"
sys.path.insert(0, str(Path.home() / ".codex/skills/generate2dsprite/scripts"))
from forge_palette import build_palette

SPECS = {
    "scrap": ("scrap_pillar", (120, 240), ("Falling", "Planted", "Crumbling")),
    "valve": ("steam_valve", (90, 110), ("Open", "Struck", "Closed")),
    "vent": ("furnace_vent", (180, 60), ("Off", "Warning", "Imminent")),
    "crystal": ("crystal_pillar", (100, 260), ("Rising", "Standing", "Breaking")),
}
SWATCHES = {
    "scrap": ("#472f25", "#805432", "#b68b63"),
    "valve": ("#572d2c", "#a3493c", "#b5ccd2"),
    "vent": ("#372f29", "#801d1c", "#cc2b21", "#f47c32", "#ffd076"),
    "crystal": ("#155361", "#319895", "#80d5cb"),
}
OUTLINE = "#0b1020"
LUMA = [0.2126, 0.7152, 0.0722]


def rgba(path):
    with Image.open(path) as img:
        return img.convert("RGBA")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def crop_subject(img):
    bounds = img.getchannel("A").point(lambda value: 255 if value >= 128 else 0).getbbox()
    assert bounds
    # 키잉한 원화에서 실루엣과 가장자리 샘플만 남긴다.
    x0, y0, x1, y1 = bounds
    return img.crop((x0-3, y0-3, x1+3, y1+3)), (x1-x0, y1-y0)


def input_cells(kind):
    sheet = rgba(SOURCE / f"{kind}_processed/raw-sheet-clean.png")
    for i in range(3):
        yield crop_subject(sheet.crop((round(i*sheet.width/3), 0, round((i+1)*sheet.width/3), sheet.height)))


def layout(kind, sizes):
    width, height = SPECS[kind][1]
    if kind in {"scrap", "crystal"}:
        # 서 있는 소품의 외형을 기존 타일 충돌 높이에 맞춘다.
        solid_width, solid_height = (118, 239) if kind == "scrap" else (60, 180)
        ref_w, ref_h = sizes[1]
        scale = solid_height / ref_h
        stretch = (solid_width - 2) / (ref_w * scale)
    else:
        max_w, max_h = map(max, zip(*sizes))
        scale = min((width-4)/max_w, (height-3)/max_h)
        stretch = 1.0
    heights = [
        round(min(scale, (width-3)/(w*stretch), height/h)*h)
        for w, h in sizes
    ]
    return stretch, heights


def color_palette(kind, images, work):
    declared = [list(bytes.fromhex(s[1:])) for s in SWATCHES[kind]]
    palette = build_palette(images, 31, reserved=declared, seed=0)
    file = work / "palette.json"
    write_json(file, palette.to_json())
    return file


def finish_one(img, number, target, work, palette):
    env = dict(os.environ, PYTHONUTF8="1", TEMP=str(ROOT/"tmp"), TMP=str(ROOT/"tmp"))
    cell = work / str(number)
    incoming = cell / "input"
    incoming.mkdir(parents=True, exist_ok=True)
    img.save(incoming / "1.png")
    finished = cell / "finish"
    subprocess.run([
        sys.executable, "-B", str(FINISH), "hibit", "--frames", str(incoming),
        "--output-dir", str(finished), "--target-height", str(target),
        "--anchor", "center", "--loop-policy", "oneshot", "--palette", str(palette),
        "--outline", OUTLINE, "--coverage", "0.30",
    ], env=env, check=True, stdout=subprocess.DEVNULL)
    art = rgba(finished / "frames/1.png")
    return art.crop(art.getbbox()), finished / "finish.json"


def pipe_axis(img):
    # 밸브의 배기관 중심을 세 상태에서 같은 x 위치에 둔다.
    alpha = np.asarray(img)[:, :, 3]
    _, xs = np.where(alpha[-9:] == 255)
    return round(float(np.median(xs)))


def place(kind, number, art, size, valve_axis):
    width, height = size
    assert art.width <= width and art.height <= height, (kind, number, art.size)
    x = valve_axis - pipe_axis(art) if kind == "valve" else (width-art.width)//2
    x = max(0, min(width-art.width, x))
    y = height-art.height
    canvas = Image.new("RGBA", size)
    canvas.paste(art, (x, y))
    if kind == "scrap" and number == 2:
        # 1px 전후의 도트 높이 오차를 맞추기 위해 기존 평평한 cap 최상단을 이어 준다.
        assert y <= 3, y
        cap = canvas.crop((0, y, width, y+1))
        for row in range(y):
            canvas.paste(cap, (0, row))
    return canvas, (x, y)


def finish(kind, run_name):
    label, canvas_size, captions = SPECS[kind]
    frames = list(input_cells(kind))
    sizes = [size for _, size in frames]
    stretch, heights = layout(kind, sizes)
    work = ROOT / "processing" / kind / run_name
    work.mkdir(parents=True, exist_ok=True)
    images = [img if stretch == 1 else img.resize((round(img.width*stretch), img.height), Image.Resampling.LANCZOS)
              for img, _ in frames]
    palette = color_palette(kind, images, work)
    results = [finish_one(img, i, height, work, palette)
               for i, (img, height) in enumerate(zip(images, heights), 1)]
    # 증기 공간까지 들어갈 수 있도록 닫힘 상태의 배관 중심을 왼쪽에 둔다.
    valve_axis = 37
    assets = ROOT / label
    assets.mkdir(exist_ok=True)
    data = []
    palette_used = set()
    for i, ((art, meta), caption) in enumerate(zip(results, captions), 1):
        out, offset = place(kind, i, art, canvas_size, valve_axis)
        pixels = np.asarray(out)
        alpha = np.unique(pixels[:, :, 3]).tolist()
        assert 255 in alpha and set(alpha) <= {0, 255}
        color = pixels[pixels[:, :, 3] == 255, :3]
        distinct = set(map(tuple, color))
        assert len(distinct) <= 32
        palette_used.update(distinct)
        assert out.getbbox()[3] == out.height
        out.save(assets / f"{i}.png")
        data.append({
            "file": f"{i}.png", "state": caption, "bounds": out.getbbox(),
            "palette_colors": len(distinct), "alpha": alpha,
            "place_offset": offset, "source_subject_size": sizes[i-1],
            "requested_height": heights[i-1],
            "finish_metadata": meta.relative_to(ROOT).as_posix(),
            "luma_p95": round(float(np.percentile(color @ LUMA, 95)), 1),
        })
    assert len(palette_used) <= 32, len(palette_used)
    if kind == "scrap":
        img = rgba(assets / "2.png")
        xs = np.where(np.asarray(img)[0, :, 3] == 255)[0]
        assert len(xs) >= 110 and np.all(np.diff(xs) == 1), xs
        data[1]["top_cap_span"] = [int(xs[0]), int(xs[-1])]
    write_json(assets / "qa.json", {"size": canvas_size, "bottom_edge": canvas_size[1],
        "pivot": [valve_axis if kind == "valve" else canvas_size[0]//2, canvas_size[1]],
        "horizontal_source_normalization": round(stretch, 5),
        "palette_colors": len(palette_used), "states": data})
    print(kind, sizes, heights, [(result[0].size) for result in results], len(palette_used))


def environment():
    assets = REPO / "assets"
    row_width, row_height = 790, 330
    canvas = Image.new("RGBA", (row_width,row_height*2), "#172130")
    regions = (("foundry","far_foundry"), ("haze","far_boss"))
    for row, (tile_theme,bg) in enumerate(regions):
        scene = rgba(assets / f"backgrounds/{bg}.png").crop((520,432,520+row_width,432+row_height))
        atlas = rgba(assets / f"tiles/tile_set_{tile_theme}.png")
        tile = atlas.crop((0,0,60,60))
        floor = 276
        for x in range(0,row_width,60):
            scene.alpha_composite(tile,(x,floor))
        entries = [("scrap_pillar",2,160,floor),("steam_valve",1,388,floor-48),
                   ("furnace_vent",2,642,floor)] if row == 0 else [("crystal_pillar",i,x,floor)
                    for i,x in enumerate((170,395,620),1)]
        draw = ImageDraw.Draw(scene)
        draw.text((12,10), ("Foundry" if row == 0 else "Ark arena") + " / 1x", fill="white")
        for label,i,cx,bottom in entries:
            art = rgba(ROOT / label / f"{i}.png")
            scene.alpha_composite(art,(cx-art.width//2,bottom-art.height))
        canvas.alpha_composite(scene,(0,row*row_height))
    canvas.save(ROOT / "arena_1x.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("inspect", "finish", "arena"))
    parser.add_argument("kind", nargs="?", choices=SPECS)
    parser.add_argument("--run", default="v1")
    args = parser.parse_args()
    if args.step == "finish":
        finish(args.kind, args.run)
    elif args.step == "inspect":
        print(args.kind, [s for _, s in input_cells(args.kind)])
    else:
        environment()
