"""스팀 상점 그림 마무리 (2026-11-21, Codex T29 그림): 캡슐 4장의 제목 자리에 로고를 합성해 assets/store/에 둔다.

입력: assets/sprites/forge/store_art_v1/ (캡슐·라이브러리 배경·로고, qa_store_art.json의 제목 자리 title_boxes)
출력: assets/store/capsule_header.png 등 (스팀 규격 크기 그대로), library_hero.png·library_logo.png는 그대로 복사,
      assets/ui/logo_title.png (타이틀 화면용 1배 로고).
게임 안에서 쓰는 그림이 아니라 상점·발표 자료용이다. 캡슐마다 픽셀 블록 크기가 달라(1·2·4배),
로고를 그 캡슐의 논리 해상도에서 줄인 뒤 블록 크기만큼 정수배로 키워 픽셀 격자를 맞춘다. 알파는 0·255.
실행: python tools/make_store_art.py
"""
import json
import os
import shutil

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'assets', 'sprites', 'forge', 'store_art_v1')
OUT = os.path.join(ROOT, 'assets', 'store')
CAPSULES = ('capsule_header', 'capsule_small', 'capsule_main', 'capsule_vertical')


def logo_fit(logo, box_w, box_h, block):
    """로고(내용 부분)를 상자에 맞게 줄인다: 논리 해상도(블록 1)에서 줄이고 알파를 0·255로, 그다음 block배 최근접 확대."""
    logo = logo.crop(logo.getbbox())
    lw, lh = box_w // block, box_h // block
    k = min(lw / logo.width, lh / logo.height)
    small = logo.resize((max(1, round(logo.width * k)), max(1, round(logo.height * k))), Image.LANCZOS)
    r, g, b, a = small.split()
    a = a.point(lambda v: 255 if v >= 128 else 0)
    small = Image.merge('RGBA', (r, g, b, a))
    return small.resize((small.width * block, small.height * block), Image.NEAREST)


def build():
    os.makedirs(OUT, exist_ok=True)
    qa = json.load(open(os.path.join(SRC, 'qa_store_art.json'), encoding='utf-8'))
    logo = Image.open(os.path.join(SRC, 'logo.png')).convert('RGBA')
    made = []
    for name in CAPSULES:
        base = Image.open(os.path.join(SRC, name + '.png')).convert('RGBA')
        block = qa['exports'][name]['pixel_block']
        x0, y0, x1, y1 = qa['title_boxes'][name]
        mark = logo_fit(logo, x1 - x0, y1 - y0, block)
        # 상자 가운데에, 블록 격자에 맞춘 위치로
        px = (x0 + (x1 - x0 - mark.width) // 2) // block * block
        py = (y0 + (y1 - y0 - mark.height) // 2) // block * block
        base.alpha_composite(mark, (px, py))
        path = os.path.join(OUT, name + '.png')
        base.convert('RGB').save(path)
        made.append((path, base.size))
    shutil.copyfile(os.path.join(SRC, 'library_hero.png'), os.path.join(OUT, 'library_hero.png'))
    shutil.copyfile(os.path.join(SRC, 'logo.png'), os.path.join(OUT, 'library_logo.png'))
    # 타이틀 화면 로고 (퀄리티 계획 4-1): 2x2 블록 로고를 정확히 절반(최근접)으로 줄이면 잃는 픽셀 없는 1배 그림이 된다
    half = logo.resize((logo.width // 2, logo.height // 2), Image.NEAREST)
    title = os.path.join(ROOT, 'assets', 'ui', 'logo_title.png')
    half.crop(half.getbbox()).save(title)
    made.append((title, half.crop(half.getbbox()).size))
    return made


if __name__ == '__main__':
    for path, size in build():
        print(os.path.relpath(path, ROOT), size)
