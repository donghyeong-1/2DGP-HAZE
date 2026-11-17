"""단색 점 이미지(px_*.png)를 만든다. HUD 사각형과 화면 효과에 쓴다. 타일·배경은 tools/make_world.py가 만든다. 직접 만든 이미지라 저작권 문제가 없다.

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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rgb in COLORS.items():
        Image.new("RGBA", (2, 2), rgb + (255,)).save(OUT / f"{name}.png")
    print("saved", OUT)


if __name__ == "__main__":
    main()
