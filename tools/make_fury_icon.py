"""균열방 보상 '균열의 분노' 아이콘(assets/ui/icon_fury.png)을 만든다.

공격력 아이콘(assets/ui/icon_power.png, Codex T13)의 색상만 균열 색(보라)으로 돌린다. 모양·크기(48x48)·외곽선은 그대로라
아이템 아이콘들과 화풍이 같다. 어두운 외곽선과 투명 픽셀은 건드리지 않는다.

사용: python tools/make_fury_icon.py --force

I1-fix(2026-11-27)부터 쓰지 않는다: 균열의 분노는 공격력과 효과가 달라 따로 뽑은 PixelLab 그림(보라 불꽃 주먹)이고
tools/apply_pixellab_icons.py가 만든다. 이 도구를 돌리면 그 그림을 공격력의 색만 바꾼 그림으로 덮어쓰므로 --force 없이는 멈춘다.
"""
import colorsys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets' / 'ui' / 'icon_power.png'
OUT = ROOT / 'assets' / 'ui' / 'icon_fury.png'
TARGET_HUE = 0.78          # 보라 (균열 문 색 (200, 130, 255) 근처)


def recolor(img):
    img = img.convert('RGBA')
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            hh, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if s < 0.15 or l < 0.12:                 # 외곽선·회색은 그대로
                continue
            nr, ng, nb = colorsys.hls_to_rgb(TARGET_HUE, l, s)
            px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)
    return img


def main():
    import sys
    if '--force' not in sys.argv:
        print('icon_fury.png는 tools/apply_pixellab_icons.py가 만든다 (I1-fix). 덮어쓰려면 --force')
        return
    recolor(Image.open(SRC)).save(OUT)
    print('saved', OUT.relative_to(ROOT))


if __name__ == '__main__':
    main()
