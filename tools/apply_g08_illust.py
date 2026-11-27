"""Gemini G08로 인물을 다시 그린 화면 일러스트 넷을 게임 그림으로 적용한다 (2026-11-27 A1, docs/opus/TASKS.md '4차' A1).

원본: assets/sprites/gemini/illust_v2/<이름>.png (G08 최종, 1920x1080, 32색. 보고 docs/gemini/reports/G08.md)
결과: assets/backgrounds/credits_1.png, credits_3.png, screen_death.png, screen_ending.png (같은 이름, 예전 파일과 같은 모드)
예전 그림: 처음 한 번 assets/sprites/gemini/illust_v2/before/<이름>.png에 복사해 둔다
(credits_3만 Codex 원본 assets/sprites/forge/credits_scenes_v1/과 같고, 나머지 셋은 인물 영역을 픽셀화한 판이라 forge에 없다).

손질 (A1 검토):
- credits_3: 작은 인물의 목도리 끝 청록 불꽃이 32색 팔레트에 청록이 없어 하늘색으로 떨어졌다 -> 목도리 끝 상자(SCARF_BOX) 안의
  하늘색 칸만 헤이즈 청록 단계로 바꾼다(상자 안 배경은 길·벽이라 그 색을 쓰지 않는다). 색이 셋 늘어 35색.

실행: python tools/apply_g08_illust.py
"""
import os
import shutil

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'sprites', 'gemini', 'illust_v2')
DST = os.path.join(ROOT, 'assets', 'backgrounds')
NAMES = ('credits_1', 'credits_3', 'screen_death', 'screen_ending')
SCARF_BOX = (262, 608, 306, 668)            # credits_3 목도리 끝 둘레 (x0, y0, x1, y1, 위가 0)
SCARF_TEAL = {                              # 하늘색 -> 헤이즈 청록 (어두운 것부터, 밝기 순서 그대로)
    (98, 164, 240): (30, 150, 150), (106, 170, 244): (40, 176, 170), (115, 177, 247): (58, 200, 190),
    (126, 186, 251): (90, 222, 208), (140, 195, 252): (130, 236, 222), (155, 206, 252): (170, 244, 232),
}


def fix_credits_3(a):
    x0, y0, x1, y1 = SCARF_BOX
    box = a[y0:y1, x0:x1]
    n = 0
    for src, dst in SCARF_TEAL.items():
        m = (box[:, :, :3] == src).all(axis=2)
        box[m, :3] = dst
        n += int(m.sum())
    return n


def main():
    os.makedirs(os.path.join(SRC, 'before'), exist_ok=True)
    for name in NAMES:
        old = os.path.join(DST, name + '.png')
        keep = os.path.join(SRC, 'before', name + '.png')
        if not os.path.exists(keep):
            shutil.copyfile(old, keep)
        mode = Image.open(keep).mode
        a = np.array(Image.open(os.path.join(SRC, name + '.png')).convert('RGBA'))
        assert a.shape[:2] == (1080, 1920) and (a[:, :, 3] == 255).all(), name
        note = ''
        if name == 'credits_3':
            note = f', 목도리 끝 {fix_credits_3(a)}칸 청록으로'
        Image.fromarray(a, 'RGBA').convert(mode).save(old)
        colors = len(np.unique(a[:, :, :3].reshape(-1, 3), axis=0))
        print(f'{name}: {mode} {colors}색{note}')


if __name__ == '__main__':
    main()
