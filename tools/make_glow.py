"""휘두르기·타격 시트의 빛 번짐 시트를 만든다 (2026-11-24 v7, 사용자: INARI 같은 빛나는 맛이 부족하다). code-drawn.

assets/effects/<시트>.png 의 각 칸을 흐리게 번지게(가우스 흐림) 해서 같은 칸 배치로 assets/light/glow_<시트>.png 에 쓴다.
게임(effects.SheetEffect)은 같은 칸을 더하기 섞기로 시트 아래에 깔아 그린다: 선명한 픽셀 모양 둘레로 부드러운 빛이 번진다.
**빛 층만** 반투명을 쓴다 (docs/pixel_rules.md v7 예외).

사용: python tools/make_glow.py [시트 이름 ...]   (이름이 없으면 GLOW_SHEETS 전부)
필요: numpy, Pillow
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'effects')
OUT = os.path.join(ROOT, 'assets', 'light')
RADIUS = 5            # 흐림 반지름 (시트 칸 px, 게임은 2배로 그린다 = 화면 10px)
GAIN = 2.2            # 흐려서 옅어진 빛을 다시 밝힌다
HALF = 2              # 빛은 흐리니 절반 크기로 저장한다 (게임이 시트 크기와의 비로 더 키워 그린다)
EXCLUDE_PREFIX = ('aura-', 'dust-', 'puff')      # 오라(이미 큰 빛)·먼지는 빛나지 않는다


def glow_sheets():
    names = sorted(f[:-5] for f in os.listdir(SRC) if f.endswith('.json'))
    return [n for n in names if not n.startswith(EXCLUDE_PREFIX)]


def glow_cell(cell):
    """한 칸(RGBA)을 번진 빛으로: 색은 알파로 가중한 평균 색, 알파는 흐린 알파 x GAIN."""
    a = np.asarray(cell, dtype=np.float32) / 255.0
    alpha = a[:, :, 3]
    out = np.zeros_like(a)
    blur = lambda x: np.asarray(Image.fromarray(np.uint8(np.clip(x, 0, 1) * 255)).filter(  # noqa: E731
        ImageFilter.GaussianBlur(RADIUS)), dtype=np.float32) / 255.0
    ba = blur(alpha)
    for ch in range(3):
        out[:, :, ch] = blur(a[:, :, ch] * alpha) / np.maximum(ba, 1e-3)
    out[:, :, :3] = np.clip(out[:, :, :3] * 0.6 + 0.4, 0, 1)          # 흰 쪽으로 (빛은 밝게)
    out[:, :, 3] = np.clip(ba * GAIN, 0, 1)
    return Image.fromarray(np.uint8(np.round(out * 255)), 'RGBA')


def build(name):
    sheet = Image.open(os.path.join(SRC, name + '.png')).convert('RGBA')
    with open(os.path.join(SRC, name + '.json'), encoding='utf-8') as fp:
        info = json.load(fp)
    fw, fh = info['frameSize']
    k = HALF if fw % HALF == 0 and fh % HALF == 0 and sheet.width % HALF == 0 and sheet.height % HALF == 0 else 1
    out = Image.new('RGBA', (sheet.width // k, sheet.height // k), (0, 0, 0, 0))
    for top in range(0, sheet.height - fh + 1, fh):
        for left in range(0, sheet.width - fw + 1, fw):
            cell = glow_cell(sheet.crop((left, top, left + fw, top + fh)))
            out.paste(cell.resize((fw // k, fh // k), Image.BILINEAR), (left // k, top // k))
    out.save(os.path.join(OUT, f'glow_{name}.png'))
    print('저장', f'assets/light/glow_{name}.png', out.size)


def main():
    """2026-11-24: fxkit 시트(json에 duration이 있다)는 빛 시트를 직접 굽는다. 여기서 흐려 만들면 덮어쓰니 건너뛴다."""
    import json
    os.makedirs(OUT, exist_ok=True)
    for name in (sys.argv[1:] or glow_sheets()):
        info = os.path.join(ROOT, 'assets', 'effects', name + '.json')
        if os.path.exists(info) and 'duration' in json.load(open(info, encoding='utf-8')):
            print('건너뜀 (fxkit 빛 시트):', name)
            continue
        build(name)


if __name__ == '__main__':
    main()
