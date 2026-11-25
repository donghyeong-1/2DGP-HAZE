"""대화 초상화(PixelLab v6)를 게임 그림으로 적용한다 (2026-11-25).

은신처 대화창의 초상화 8장(주인공·정비사·보관인·기록관 x 표정 2)을 새 몸 그림과 같은 화풍으로 맞춘다.
원본: assets/sprites/pixellab/portraits_v6/raw_gen/<인물>_<1|2>.png (100x100, 화면에서는 2배 = 200x200)
  - <인물>_1 = 기본 표정. 주인공은 예전 초상화(Gemini G04 원화를 줄인 것)를 그대로 쓰고, 이 그림이 NPC 초상화의 화풍 기준이다.
  - <인물>_2 = 표정만 글로 편집한 것(edit_image_pro_flash). 편집본은 그림 전체가 조금씩 다시 그려지고 색 수도 줄어서,
    그대로 번갈아 보이면 옷·머리까지 출렁인다.
하는 일: 표정 2는 **기본 표정 그림에 얼굴 영역(FACE)만** 편집본에서 가져와 붙인다(색은 기본 표정의 색으로 다시 칠한다).
그래서 표정이 바뀌어도 얼굴 말고는 한 칸도 달라지지 않는다. 최근접 2배로 assets/portraits/<인물>_<1|2>.png 에 쓴다.

실행: python tools/apply_pixellab_portraits.py
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_pixellab_hero import lock_palette, palette_of  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'portraits_v6', 'raw_gen')
DST = os.path.join(ROOT, 'assets', 'portraits')
SCALE = 2
# 얼굴 영역 (x0, y0, x1, y1), 100x100 기준: 눈썹·눈·입이 들어가는 사각형. 머리카락·옷은 건드리지 않는다
FACE = {'n09': (48, 30, 80, 64), 'mechanic': (17, 24, 50, 60), 'keeper': (14, 20, 48, 66), 'archivist': (20, 24, 54, 64)}


def load(name):
    a = np.array(Image.open(os.path.join(RAW, name + '.png')).convert('RGBA'))
    a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
    a[a[:, :, 3] == 0] = 0
    return a


def main():
    for who, (x0, y0, x1, y1) in FACE.items():
        base = load(f'{who}_1')
        mood = lock_palette(load(f'{who}_2'), palette_of(base))
        out = base.copy()
        inside = np.zeros(base.shape[:2], bool)
        inside[y0:y1, x0:x1] = True
        take = inside & (base[:, :, 3] == 255) & (mood[:, :, 3] == 255)      # 윤곽(투명 여부)은 기본 표정 그대로
        out[take] = mood[take]
        changed = int((out != base).any(axis=2).sum())
        for n, a in ((1, base), (2, out)):
            im = Image.fromarray(a, 'RGBA')
            im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST).save(os.path.join(DST, f'{who}_{n}.png'))
        print(f'{who}: 표정 2에서 바뀐 칸 {changed}, 색 {len(palette_of(out))}')


if __name__ == '__main__':
    main()
