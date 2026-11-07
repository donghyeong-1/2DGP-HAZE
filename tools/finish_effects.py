"""pixelfx로 만든 이펙트 시트를 우리 픽셀 규칙(docs/pixel_rules.md)에 맞게 마무리한다.

- 반투명 픽셀 -> 4x4 순서 디더(Bayer)로 불투명/투명 점무늬로 바꾼다 (알파는 0 또는 255만)
- 색 수 -> 이펙트 전체가 공유하는 팔레트(기본 32색)로 줄인다
- 프레임 수 -> 30fps 원본을 step 간격으로 솎는다 (기본 2 -> 15fps), 마지막 프레임은 항상 남긴다
- 빈 여백 -> 모든 프레임의 합집합 영역으로 잘라 낸다 (pivot도 함께 옮긴다)

사용:
  node <pixelfx>/tools/render.mjs impacts/hit-spark --sheet   # 먼저 시트를 굽는다
  python tools/finish_effects.py <pixelfx 폴더> impacts/hit-spark melee/heavy-cleave ...
결과: assets/effects/<이름>.png, <이름>.json, CREDITS.txt (pixelfx MIT 고지)
"""
import argparse
import json
import math
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "effects"

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
ALPHA_DROP = 24      # 이보다 옅은 픽셀은 버린다
ALPHA_KEEP = 224     # 이보다 진한 픽셀은 그대로 남긴다


def load_frames(sheet_path, meta_path):
    sheet = Image.open(sheet_path).convert("RGBA")
    meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    frames = []
    for f in meta["frames"]:
        r = f["frame"]
        frames.append(sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])))
    return frames, meta["meta"]["pixelfx"]


def thin(frames, step):
    keep = list(range(0, len(frames), step))
    if keep[-1] != len(frames) - 1:
        keep.append(len(frames) - 1)  # 끝 모양은 남긴다
    return [frames[i] for i in keep]


def dither_alpha(img):
    """반투명을 점무늬로: 알파가 클수록 점이 촘촘해진다."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a >= ALPHA_KEEP:
                px[x, y] = (r, g, b, 255)
            elif a < ALPHA_DROP:
                px[x, y] = (0, 0, 0, 0)
            else:
                threshold = (BAYER4[y % 4][x % 4] + 0.5) / 16 * 255
                px[x, y] = (r, g, b, 255) if a > threshold else (0, 0, 0, 0)
    return img


def build_palette(all_frames, colors):
    """모든 이펙트의 불투명 픽셀 색으로 공유 팔레트를 만든다."""
    pixels = []
    for frames in all_frames:
        for fr in frames:
            pixels.extend(p[:3] for p in fr.getdata() if p[3] == 255)
    strip = Image.new("RGB", (len(pixels), 1))
    strip.putdata(pixels)
    return strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def apply_palette(img, palette_img):
    rgb = img.convert("RGB").quantize(palette=palette_img, dither=Image.Dither.NONE).convert("RGB")
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    alpha = img.getchannel("A")
    out.paste(rgb, (0, 0), alpha.point(lambda a: 255 if a else 0))
    return out


def union_bbox(frames):
    boxes = [fr.getchannel("A").getbbox() for fr in frames]
    boxes = [b for b in boxes if b]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pixelfx_dir")
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--step", type=int, default=2, help="프레임 솎기 간격 (2 = 30fps -> 15fps)")
    ap.add_argument("--colors", type=int, default=48, help="이펙트 공유 팔레트 색 수")
    args = ap.parse_args()

    src = Path(args.pixelfx_dir)
    loaded = {}
    for fx_id in args.ids:
        name = fx_id.split("/")[1]
        frames, info = load_frames(src / "records" / fx_id / f"{name}.png", src / "records" / fx_id / f"{name}.json")
        frames = [dither_alpha(fr) for fr in thin(frames, args.step)]
        loaded[fx_id] = (frames, info)

    palette = build_palette([f for f, _ in loaded.values()], args.colors)
    OUT.mkdir(parents=True, exist_ok=True)

    for fx_id, (frames, info) in loaded.items():
        name = fx_id.split("/")[1]
        frames = [apply_palette(fr, palette) for fr in frames]
        x0, y0, x1, y1 = union_bbox(frames)
        frames = [fr.crop((x0, y0, x1, y1)) for fr in frames]
        w, h = frames[0].size
        cols = min(len(frames), max(1, math.ceil(math.sqrt(len(frames)))))
        rows = math.ceil(len(frames) / cols)
        sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
        for i, fr in enumerate(frames):
            sheet.paste(fr, ((i % cols) * w, (i // cols) * h))
        sheet.save(OUT / f"{name}.png")
        fps = round(info["fps"] / args.step)
        meta = {
            "id": fx_id, "frames": len(frames), "frameSize": [w, h], "columns": cols, "fps": fps, "loop": info["loop"],
            "pivot": [info["pivot"][0] - x0, info["pivot"][1] - y0],
            "source": "pixelfx (MIT, https://github.com/patch-gg/pixelfx), finished by tools/finish_effects.py",
        }
        (OUT / f"{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        used = len({p for p in sheet.getdata() if p[3] == 255})
        print(f"{fx_id:30s} {len(frames):3d}프레임 {w}x{h} {fps}fps 색 {used}")

    for name in ("LICENSE", "NOTICE.md"):
        if (src / name).exists():
            shutil.copy(src / name, OUT / f"pixelfx-{name}")
    (OUT / "CREDITS.txt").write_text(
        "이 폴더의 이펙트는 pixelfx(patch-gg, MIT)로 만든 뒤 tools/finish_effects.py로 마무리했다.\n"
        "pixelfx-LICENSE, pixelfx-NOTICE.md를 함께 둔다. 게임 엔딩 크레딧에 pixelfx와 Hugo Duprez(Sprite Fusion VFX, MIT),\n"
        "rehan-remade(Hollow Crown, MIT)를 표기한다.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
