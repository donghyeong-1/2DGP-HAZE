"""고해상도 스프라이트를 통일 규격(키, 공통 팔레트, 외곽선)의 도트 이미지로 가공한다.

입력: assets/sprites/detailed/{name}_idle.png (투명 배경)
출력: assets/sprites/unified/{name}_idle.png 와 확인용 미리보기 build/unified_preview.png
규격은 docs/sprite_spec.md 를 따른다.
"""
import os
import sys

from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "assets", "sprites", "detailed")
DST = os.path.join(ROOT, "assets", "sprites", "unified")
PREVIEW = os.path.join(ROOT, "build", "unified_preview.png")

# 이름: 목표 키(px, 외곽선 제외). 크기 비례는 게임 안에서의 상대 크기이다.
TARGET_HEIGHT = {
    "n09": 80,
    "enemy_slum": 76,
    "enemy_thrower": 80,
    "enemy_hound": 52,
    "enemy_guard": 88,
    "boss_crasher": 128,
    "boss_ark": 104,
}
PALETTE_SIZE = 60
OUTLINE_COLOR = (11, 16, 32)
# 공통 팔레트에 항상 포함할 색 (외곽선, 헤이즈 청록 계열)
FIXED_COLORS = [OUTLINE_COLOR, (40, 120, 160), (79, 195, 247), (190, 240, 255), (235, 240, 255), (200, 210, 228)]
ALPHA_CUT = 140


def main_bbox(im, shrink=8, keep_ratio=0.04):
    """이펙트 파편과 잡티를 제외하고 캐릭터 본체의 경계 상자를 구한다."""
    alpha = im.getchannel("A").point(lambda a: 255 if a > 128 else 0)
    small = alpha.resize((im.width // shrink, im.height // shrink), Image.BOX)
    small = small.point(lambda a: 255 if a > 40 else 0).filter(ImageFilter.MaxFilter(5))
    w, h = small.size
    px = small.load()
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sy in range(h):
        for sx in range(w):
            if px[sx, sy] and not seen[sy][sx]:
                stack = [(sx, sy)]
                seen[sy][sx] = True
                area, x0, y0, x1, y1 = 0, sx, sy, sx, sy
                while stack:
                    x, y = stack.pop()
                    area += 1
                    x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < w and 0 <= ny < h and px[nx, ny] and not seen[ny][nx]:
                                seen[ny][nx] = True
                                stack.append((nx, ny))
                comps.append((area, x0, y0, x1, y1))
    biggest = max(c[0] for c in comps)
    kept = [c for c in comps if c[0] >= biggest * keep_ratio]
    x0 = min(c[1] for c in kept) * shrink
    y0 = min(c[2] for c in kept) * shrink
    x1 = (max(c[3] for c in kept) + 1) * shrink
    y1 = (max(c[4] for c in kept) + 1) * shrink
    return max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1)


def load_cropped(name):
    im = Image.open(os.path.join(SRC, f"{name}_idle.png")).convert("RGBA")
    box = main_bbox(im)
    cropped = im.crop(box)
    # 경계 상자 안에서 다시 실제 불투명 영역으로 줄인다
    return cropped.crop(cropped.getbbox())


def downscale(im, height):
    """BOX 필터로 줄여 원본의 도트 느낌과 선명도를 최대한 유지한다."""
    w = max(1, round(im.width * height / im.height))
    small = im.resize((w, height), Image.BOX)
    alpha = small.getchannel("A").point(lambda a: 255 if a >= ALPHA_CUT else 0)
    return small.convert("RGB"), alpha


def build_palette(images):
    """모든 스프라이트의 불투명 픽셀을 모아 공통 팔레트를 만든다."""
    pixels = []
    for rgb, alpha in images.values():
        pixels.extend(p for p, a in zip(rgb.getdata(), alpha.getdata()) if a)
    side = int(len(pixels) ** 0.5) + 1
    pixels += [pixels[-1]] * (side * side - len(pixels))
    sheet = Image.new("RGB", (side, side))
    sheet.putdata(pixels)
    quant = sheet.quantize(colors=PALETTE_SIZE, method=Image.MEDIANCUT, dither=Image.NONE)
    flat = quant.getpalette()[: PALETTE_SIZE * 3]
    colors = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
    return colors + [c for c in FIXED_COLORS if c not in colors]


def apply_palette(rgb, alpha, colors):
    pal = Image.new("P", (1, 1))
    flat = [v for c in colors for v in c]
    pal.putpalette(flat + [0] * (768 - len(flat)))
    mapped = rgb.quantize(palette=pal, dither=Image.NONE).convert("RGB")
    out = Image.merge("RGBA", (*mapped.split(), alpha))
    return out


def add_outline(im):
    """불투명 영역 바깥에 1px 외곽선을 입힌다."""
    w, h = im.size
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    alpha = im.getchannel("A")
    a = alpha.load()
    o = out.load()
    for y in range(h + 2):
        for x in range(w + 2):
            sx, sy = x - 1, y - 1
            if 0 <= sx < w and 0 <= sy < h and a[sx, sy]:
                continue
            near = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = sx + dx, sy + dy
                if 0 <= nx < w and 0 <= ny < h and a[nx, ny]:
                    near = True
                    break
            if near:
                o[x, y] = OUTLINE_COLOR + (255,)
    out.alpha_composite(im, (1, 1))
    return out


def make_preview(results, scale=5):
    pad = 8
    base_h = max(im.height for im in results.values()) * scale + pad * 2
    width = sum(im.width * scale + pad * 2 for im in results.values())
    sheet = Image.new("RGBA", (width, base_h), (15, 22, 35, 255))
    x = 0
    for im in results.values():
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        sheet.alpha_composite(big, (x + pad, base_h - pad - big.height))
        x += big.width + pad * 2
    return sheet.convert("RGB")


def main():
    os.makedirs(DST, exist_ok=True)
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    scaled = {n: downscale(load_cropped(n), h) for n, h in TARGET_HEIGHT.items()}
    colors = build_palette(scaled)
    results = {}
    for name, (rgb, alpha) in scaled.items():
        im = add_outline(apply_palette(rgb, alpha, colors))
        im.save(os.path.join(DST, f"{name}_idle.png"))
        results[name] = im
    make_preview(results, scale=3).save(PREVIEW)
    print("palette colors:", len(colors))
    for name, im in results.items():
        used = {p for p in im.getdata() if p[3]}
        print(f"{name}: {im.size}, colors {len(used)}")


if __name__ == "__main__":
    if "--legacy" not in sys.argv:
        sys.exit("구 방식(2026-11-07 폐기)이라 assets/sprites/unified/의 새 hibit 스프라이트를 덮어씁니다. 정말 필요하면 --legacy를 붙이세요. 새 방식은 docs/sprite_spec.md, tools/finish_character.py")
    main()
