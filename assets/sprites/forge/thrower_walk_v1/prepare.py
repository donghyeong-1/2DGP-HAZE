"""투척병 원화의 골반과 접지점을 맞추고 공통 캔버스에 넣는다."""
import argparse
import json
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
UNIFIED = ROOT.parent.parent / "unified"
RAW_ANCHOR = (345, 565)
RAW_SIZE = (690, 625)
ACTIONS = {
    # 행/열, 원화 등록 배율, 시트 좌표의 골반 x, 고글 좌표
    "walk": (2, 2, 0.94, (330, 931, 330, 932),
             ((377, 120), (989, 130), (379, 749), (991, 757))),
    "back": (1, 2, 0.68, (481, 1247), ((652, 252), (1417, 252))),
}
LABELS = {"walk": ("1 near contact", "2 near support", "3 far contact", "4 far support"),
          "back": ("1 rear foot reaches", "2 front foot draws in")}
ALTERNATE_LEADS = ((0.66, 452, (525, 172)), (0.66, 1304, (1387, 182)))
BACKGROUND = "#252d3b"


def rgba(path):
    return Image.open(path).convert("RGBA")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def prepare(action):
    rows, cols, factor, roots, goggles = ACTIONS[action]
    folder = ROOT / action
    sheet = rgba(folder / "processed/raw-sheet-clean.png")
    alternate = rgba(folder / "alternate_processed/raw-sheet-clean.png") if action == "walk" else None
    out = folder / "frames_raw"
    out.mkdir(exist_ok=True)
    width, height = sheet.width // cols, sheet.height // rows
    points = []
    for i, (root_x, (gx, gy)) in enumerate(zip(roots, goggles)):
        scale = factor
        left, top = i % cols * width, i // cols * height
        cell = sheet.crop((left, top, left + width, top + height))
        if alternate is not None and i >= 2:
            scale, root_x, (gx, gy) = ALTERNATE_LEADS[i-2]
            half = alternate.width // 2
            left, top = (i-2)*half, 0
            cell = alternate.crop((left, top, left+half, alternate.height))
        sole = cell.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()[3]
        frame = cell.transform(RAW_SIZE, Image.Transform.AFFINE,
                               (1/scale, 0, root_x-left-RAW_ANCHOR[0]/scale,
                                0, 1/scale, sole-RAW_ANCHOR[1]/scale),
                               Image.Resampling.BICUBIC)
        x0, y0, x1, y1 = frame.getbbox()
        assert 0 < x0 < x1 < RAW_SIZE[0] and 0 < y0 < y1 < RAW_SIZE[1]
        frame.save(out / f"{action}-{i + 1}.png")
        points.append((RAW_ANCHOR[0] + (gx - root_x)*scale,
                       RAW_ANCHOR[1] + (gy - top - sole)*scale))
    save_json(folder / "goggles_source.json", points)


def game_point(meta, source):
    return tuple(round(a + (q-s)*meta["scale"])
                 for a, q, s in zip(meta["anchor"], source, meta["anchorSource"]))


def goggle_center(frame, rough):
    x0, y0 = rough
    pixels = frame.load()
    cyans = [(x, y) for y in range(y0-5, y0+6) for x in range(x0-5, x0+6)
             if (c := pixels[x, y])[3] == 255 and c[1] - c[0] > 38 and c[2] - c[0] > 38]
    return [round(median(values), 1) for values in zip(*cyans)]


def final_frames():
    final = ROOT / "frames"
    final.mkdir(exist_ok=True)
    items = []
    for action in ACTIONS:
        clip = "enemy_thrower_walk_alt" if action == "walk" else "enemy_thrower_back_v1"
        build = ROOT / "finish" / clip
        info = read_json(build / "finish.json")
        sx, sy = game_point(info, RAW_ANCHOR)
        markers = read_json(ROOT / action / "goggles_source.json")
        for i, marker in enumerate(markers, 1):
            name = f"{action}-{i}.png"
            image = rgba(build / "frames" / name)
            b = image.getbbox()
            assert abs(sy-b[3]) <= 2
            items.append((name, image, b, (sx, b[3]), game_point(info, marker)))

    pad = 4
    left = min(b[0]-sx for _, _, b, (sx, _), _ in items)
    right = max(b[2]-sx for _, _, b, (sx, _), _ in items)
    height = max(b[3]-b[1] for _, _, b, _, _ in items)
    anchor = (pad-left, height+pad)
    size = (right-left+2*pad, height+2*pad)
    metrics = {}
    colors = set()
    for name, native, b, (sx, sy), (gx, gy) in items:
        frame = Image.new("RGBA", size)
        dx, dy = anchor[0]-sx, anchor[1]-sy
        frame.paste(native.crop(b), (b[0]+dx, b[1]+dy))
        bounds = frame.getbbox()
        assert 0 < bounds[0] < bounds[2] < size[0] and bounds[3] == anchor[1]
        center = goggle_center(frame, (gx+dx, gy+dy))
        assert len(center) == 2, name
        palette = {px[:3] for px in frame.get_flattened_data() if px[3] == 255}
        colors |= palette
        metrics[name] = {"anchor": anchor, "bounds": bounds, "goggle_xy": center,
                         "height": bounds[3]-bounds[1], "colors": len(palette)}
        frame.save(final / name)
    save_json(ROOT / "checks.json", {"canvas": size, "anchor": anchor, "color_count":len(colors),
              "duration_ms":120, "frames":metrics})


def tiles(items):
    left = 8+max(anchor[0] for _,anchor,_ in items)
    floor = 22+max(anchor[1] for _,anchor,_ in items)
    right = 8+max(im.width-x for im,(x,_),_ in items)
    bottom = 8+max(im.height-y for im,(_,y),_ in items)
    tiles = []
    for im,(x,y),label in items:
        cell = Image.new("RGBA",(left+right,floor+bottom),BACKGROUND)
        cell.paste("#526079",(0,floor,cell.width,floor+1))
        cell.alpha_composite(im,(left-x,floor-y))
        ImageDraw.Draw(cell).text((5,4),label,fill="white")
        tiles.append(cell)
    return tiles


def strip(images):
    w,h = images[0].size
    board = Image.new("RGBA",((w+4)*len(images)-4,h),"#131a24")
    for i, im in enumerate(images):
        board.alpha_composite(im,(i*(w+4),0))
    return board


def previews():
    checks = read_json(ROOT / "checks.json")
    anchor = tuple(checks["anchor"])
    groups = []
    standards = [("enemy_thrower_idle",(27,124),"thrower idle")]
    standards.extend((f"enemy_thrower_throw_{i}",(41,124),f"throw {i}") for i in range(1,4))
    groups.append([(rgba(UNIFIED / f"{name}.png"),pos,label) for name,pos,label in standards])
    for action, labels in LABELS.items():
        items = [(rgba(ROOT / "frames" / f"{action}-{i+1}.png"),anchor,label)
                 for i,label in enumerate(labels)]
        groups.append(items)
        rendered = tiles(items)
        strip(rendered).save(ROOT / f"{action}_strip_1x.png")
        previews = [im.convert("RGB") for im in rendered]
        path = ROOT / f"{action}_1x.gif"
        previews[0].save(path,save_all=True,append_images=previews[1:],duration=120,loop=0,disposal=2)
        with Image.open(path) as gif:
            assert gif.n_frames == len(items)
            for i,original in enumerate(previews):
                gif.seek(i)
                assert gif.info["duration"] == 120
                assert gif.convert("RGB").tobytes() == original.tobytes()
    groups.append([(rgba(UNIFIED / f"enemy_slum_walk_{i}.png"),(43,118),f"slum {i}") for i in range(1,5)])
    common_tiles = iter(tiles([item for group in groups for item in group]))
    rows = [strip([next(common_tiles) for _ in group]) for group in groups]
    board = Image.new("RGBA",(max(im.width for im in rows),sum(im.height for im in rows)+12),"#131a24")
    y = 0
    for row in rows:
        board.alpha_composite(row,(0,y))
        y += row.height+4
    board.save(ROOT / "comparison_1x.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("prepare","package"))
    parser.add_argument("action", choices=ACTIONS, nargs="?")
    args = parser.parse_args()
    if args.step == "prepare":
        prepare(args.action)
    else:
        final_frames()
        previews()


if __name__ == "__main__":
    main()
