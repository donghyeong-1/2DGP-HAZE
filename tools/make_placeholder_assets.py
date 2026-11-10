"""개발용 임시 이미지(배경, 단색 점)를 만든다. 타일은 tools/make_codeart.py가 만든다. 직접 만든 이미지라 저작권 문제가 없다.

사용: python tools/make_placeholder_assets.py
결과: assets/placeholder/*.png  (실제 타일·UI 에셋으로 교체하면 이 파일들은 지운다)
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "placeholder"
T = 40

COLORS = {
    "px_white": (235, 240, 250),
    "px_black": (6, 10, 20),
    "px_gray": (70, 80, 100),
    "px_red": (225, 70, 80),
    "px_orange": (240, 150, 60),
    "px_blue": (70, 130, 200),
    "px_cyan": (90, 210, 240),
    "px_yellow": (250, 220, 90),
}


def background():
    w, h = 1920, 1080  # 화면 크기 (src/config.py SCREEN_W/H)
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=(int(8 + 14 * k), int(14 + 20 * k), int(30 + 34 * k), 255))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    background().save(OUT / "bg.png")
    for name, rgb in COLORS.items():
        Image.new("RGBA", (2, 2), rgb + (255,)).save(OUT / f"{name}.png")
    print("saved", OUT)


if __name__ == "__main__":
    main()
