"""황금방 형태 진열대 아이콘을 만든다 (v8 남겨 둔 것, 2026-11-25). code-drawn, numpy + Pillow.

무기 아이콘(assets/ui/icon_w_<무기>.png, 48x48)을 논리 24x24로 되돌린 뒤 금색 형태 표시
(네 갈래 별, 외곽선 두름)를 왼쪽 위에 얹고 다시 정수 2배로 키운다. 형태 카드의 금색(forms.COLOR)과 같은 계열이다.
  assets/ui/icon_f_pipe.png, icon_f_pistol.png, icon_f_gauntlet.png, icon_f_chain.png

사용: python tools/make_form_icons.py (무기 아이콘을 바꾸면 다시 돌린다)
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from make_icons import Canvas, K, up2  # noqa: E402

UI = os.path.join(ROOT, 'assets', 'ui')
WEAPONS = ('pipe', 'pistol', 'gauntlet', 'chain')
GOLD = ((160, 104, 40), (255, 214, 120), (255, 246, 200))      # 그림자, 기본, 밝은 면


def badge():
    """논리 7x7 네 갈래 별(외곽선 포함 9x9). 가운데가 밝고 아래·오른쪽 갈래가 어둡다 (빛은 왼쪽 위)."""
    d, m, l = GOLD
    cv = Canvas(9, 9)                      # 바깥 1칸은 외곽선 자리
    cx = cy = 4
    for i in range(-3, 4):                 # 가로·세로 갈래
        cv.px(cx + i, cy, m)
        cv.px(cx, cy + i, m)
    cv.rect(cx - 1, cy - 1, cx + 1, cy + 1, m)
    for i in range(2, 4):                  # 아래·오른쪽 갈래 끝은 그림자
        cv.px(cx + i, cy, d)
        cv.px(cx, cy + i, d)
    cv.px(cx + 1, cy + 1, d)
    cv.px(cx, cy, l)
    cv.px(cx - 1, cy, l)
    cv.px(cx, cy - 1, l)
    cv.outline(K)
    return cv.a


def form_icon(wid):
    big = np.array(Image.open(os.path.join(UI, f'icon_w_{wid}.png')).convert('RGBA'))
    base = big[::2, ::2].copy()            # 2배로 저장된 것을 논리 격자로
    star = badge()
    h, w = star.shape[:2]
    x0, y0 = 0, 0                          # 왼쪽 위 구석 (네 무기 모두 이쪽이 가장 비었다)
    region = base[y0:y0 + h, x0:x0 + w]
    on = star[:, :, 3] > 0
    region[on] = star[on]
    return up2(base)


def main():
    for wid in WEAPONS:
        path = os.path.join(UI, f'icon_f_{wid}.png')
        Image.fromarray(np.ascontiguousarray(form_icon(wid)), 'RGBA').save(path)
        print(path)


if __name__ == '__main__':
    main()
