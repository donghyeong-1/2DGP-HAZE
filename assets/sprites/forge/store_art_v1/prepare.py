"""T29 원화를 최종 픽셀 격자에 굽고 분리 로고의 합성을 검토한다."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
PLATE = Path.home() / ".codex/skills/generate2dmap/scripts/hibit_plate.py"
SPECS = {
    "logo": ((1280, 720), 2, 44),
    "capsule_header": ((920, 430), 2, 44),
    "capsule_main": ((1232, 706), 2, 46),
    "capsule_small": ((462, 174), 1, 38),
    "capsule_vertical": ((748, 896), 4, 44),
    "library_hero": ((3840, 1240), 4, 48),
}
TITLE_BOXES = {
    "capsule_header": (52, 99, 484, 329),
    "capsule_main": (345, 23, 887, 171),
    "capsule_small": (13, 30, 267, 130),
    "capsule_vertical": (42, 85, 458, 252),
}
HERO_SAFE_AREA = (1490, 430, 2350, 810)
HERO_CROP = (81, 0, 2125, 660)
MASTER = "assets/sprites/forge/hero_v3b/master/master_rgba.png"
ARK = "assets/sprites/forge/remake_t01_t03/boss_ark/master/master_rgba.png"
TITLE = "assets/backgrounds/screen_title.png"
CUTIN = "assets/ui/ult_cutin.png"
REFS = {
    "logo": ["assets/ui/logo.png"],
    "capsule_header": [MASTER, TITLE, CUTIN],
    "capsule_main": [MASTER, ARK, "raw/capsule_header.png"],
    "capsule_small": ["raw/capsule_header.png", CUTIN],
    "capsule_vertical": [TITLE, "raw/capsule_header.png", MASTER],
    "library_hero": ["assets/backgrounds/far_cell.png", "assets/backgrounds/far_foundry.png",
                     "assets/backgrounds/far_haze.png", TITLE],
}


def rgba(path):
    return Image.open(path).convert("RGBA")


def save_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def bake_grid(plate, block):
    # 출력 픽셀 그룹을 한 번에 채워 규격 캔버스를 생성한다.
    source = np.asarray(plate)
    if block > 1:
        source = source.repeat(block, axis=0).repeat(block, axis=1)
    return Image.fromarray(source)


def alpha_wordmark(source, logical_size, palette_colors):
    alpha = source.getchannel("A")
    bounds = alpha.point(lambda a: 255 if a >= 128 else 0).getbbox()
    assert bounds and alpha.getextrema() == (0, 255)
    logo = source.crop(bounds)
    logo.thumbnail((logical_size[0] - 52, logical_size[1] - 72), Image.Resampling.BOX)
    pixels = np.array(logo)
    mask = pixels[:, :, 3] >= 128
    regions, count = ndimage.label(mask, structure=np.ones((3, 3)))
    region_sizes = np.bincount(regions.ravel(), minlength=count+1)
    selected = mask & (region_sizes[regions] >= 9)
    colors = Image.fromarray(pixels[selected, :3][:, None, :])
    colors = colors.quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    out = np.zeros_like(pixels)
    out[selected, :3] = np.asarray(colors)[:, 0, :]
    out[selected, 3] = 255
    canvas = Image.new("RGBA", logical_size)
    canvas.paste(Image.fromarray(out), ((canvas.width-logo.width)//2, (canvas.height-logo.height)//2))
    return canvas


def finish(name):
    size, block, colors = SPECS[name]
    logical = (size[0] // block, size[1] // block)
    raw = RAW / f"{name}.png"
    if name == "logo":
        plate = alpha_wordmark(rgba(raw), logical, colors)
    else:
        stage = ROOT / "finish" / name
        stage.parent.mkdir(exist_ok=True)
        if name == "library_hero":
            stage = stage.with_name("library_hero_safe")
            cropped = ROOT / "tmp/library_hero_crop.png"
            with Image.open(raw) as source:
                source.crop(HERO_CROP).save(cropped)
            raw = cropped
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["TEMP"] = env["TMP"] = str(ROOT / "tmp")
        subprocess.run([
            sys.executable, "-B", str(PLATE), "plate", "--input", str(raw),
            "--output-dir", str(stage), "--size", f"{logical[0]}x{logical[1]}",
            "--colors", str(colors), "--smooth", "0", "--preview-scale", "1",
        ], check=True, env=env)
        plate = Image.open(stage / "plate.png").convert("RGB")
    output = bake_grid(plate, block)
    assert output.size == size
    output.save(ROOT / f"{name}.png", optimize=True)


def add_title(name, wordmark):
    frame = rgba(ROOT / f"{name}.png")
    x0, y0, x1, y1 = TITLE_BOXES[name]
    mark = wordmark.copy()
    mark.thumbnail((x1-x0, y1-y0), Image.Resampling.NEAREST)
    frame.alpha_composite(mark, (x0+(x1-x0-mark.width)//2, y0+(y1-y0-mark.height)//2))
    return frame


def audit():
    assets, tests = [], {}
    for name, (size, block, _) in SPECS.items():
        source_path = RAW / f"{name}.png"
        src_size = rgba(source_path).size
        assets.append({"name":name, "source":f"raw/{name}.png", "source_size":src_size,
                       "prompt":f"raw/{name}_prompt.txt", "references":REFS[name],
                       "sha256":hashlib.sha256(source_path.read_bytes()).hexdigest()})
        image = rgba(ROOT / f"{name}.png")
        assert image.size == size
        pixels = np.asarray(image)
        assert set(np.unique(pixels[:,:,3])) == ({0,255} if name == "logo" else {255})
        opaque = pixels[pixels[:,:,3]==255,:3]
        color_count = len(np.unique(opaque, axis=0))
        assert 32 <= color_count <= 48, (name, color_count)
        logical = pixels[::block,::block]
        assert np.array_equal(pixels, logical.repeat(block,axis=0).repeat(block,axis=1))
        tests[name] = {"dimensions":size,"pixel_block":block,"logical_resolution":logical.shape[:2][::-1],
                       "color_count":color_count, "opacity_values":sorted(map(int,np.unique(pixels[:,:,3]))),
                       "content_bounds":image.getbbox()}
    save_json(ROOT / "provenance.json", {"task":"T29","date_kst":"2026-11-21",
        "art_source":"host_image","route":"Codex image_gen","model":None,"estimateUsd":None,
        "genre":"횡스크롤 액션 로그라이트","title":"헤이즈 (HAZE)","subtitle":"안개를 삼키고 탈출하라",
        "generated":assets})
    save_json(ROOT / "qa_store_art.json", {"title_boxes":TITLE_BOXES,"library_hero_source_crop":HERO_CROP,
              "library_hero_safe_area":HERO_SAFE_AREA,"exports":tests})
    return tests


def build_review():
    directory = ROOT / "review"
    directory.mkdir(exist_ok=True)
    wordmark = rgba(ROOT / "logo.png")
    wordmark = wordmark.crop(wordmark.getbbox())
    composites = {name:add_title(name,wordmark) for name in TITLE_BOXES}
    small = composites["capsule_small"]
    small.save(directory/"small_with_logo_462.png")
    mini_sizes = ((184,69),(120,45))
    for w,h in mini_sizes:
        small.resize((w,h), Image.Resampling.BOX).save(directory/f"small_with_logo_{w}.png")
    hero = rgba(ROOT / "library_hero.png")
    hero.crop(HERO_SAFE_AREA).save(directory/"library_hero_safe_area_1x.png")
    for label, color in (("dark", "#081524"), ("light", "#e2e9ee")):
        backing = Image.new("RGBA", wordmark.size, color)
        backing.alpha_composite(wordmark)
        backing.thumbnail((900,320),Image.Resampling.NEAREST)
        backing.save(directory/f"logo_{label}.png")

    # 검토판에만 로고를 합성한다. 최종 캡슐 PNG는 글자 없는 원본이다.
    board = Image.new("RGB",(1240,1260),"#101925")
    draw = ImageDraw.Draw(board)
    entries = (
        (composites["capsule_header"], (16,25), (760,356), "Header"),
        (composites["capsule_vertical"], (792,25), (432,518), "Vertical"),
        (composites["capsule_main"], (16,407), (760,435), "Main"),
        (small,(792,575),(432,174),"Small"),
        (rgba(directory/"small_with_logo_184.png"),(792,767),(184,69),"184 x 69"),
        (rgba(directory/"small_with_logo_120.png"),(992,767),(120,45),"120 x 45"),
        (hero,(16,875),(1208,373),"Library Hero"),
    )
    for frame,(x,y),maximum,label in entries:
        frame=frame.copy()
        frame.thumbnail(maximum,Image.Resampling.BOX)
        board.paste(frame.convert("RGB"),(x,y))
        draw.text((x,y-16),label,fill="#deebf7")
    board.save(directory/"overview.png",optimize=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("step",choices=("finish","audit"))
    parser.add_argument("name",nargs="?",choices=SPECS)
    args=parser.parse_args()
    if args.step=="finish":
        finish(args.name)
    else:
        data=audit()
        build_review()
        print(json.dumps(data,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
