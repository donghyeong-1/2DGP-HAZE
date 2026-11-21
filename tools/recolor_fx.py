"""강화 단계별 색 이펙트 만들기 (2026-11-21): 보라색 강화 이펙트를 2단계 금색·3단계 진홍색으로 바꿔 칠한다.

원래 시트(tools/make_fx.py, 색 4~5개)의 색을 밝기 순으로 줄 세워 목표 색 띠(어두움 -> 밝음)에 하나씩 맞춘다.
모양·프레임·알파(켜짐·꺼짐)는 그대로다. 결과: assets/effects/<이름>2.png(금), <이름>3.png(진홍) + 같은 json.
사용: python tools/recolor_fx.py
"""
import json
import os
import shutil

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FX = os.path.join(ROOT, 'assets', 'effects')
SHEETS = ('hit-enhanced', 'pipe-slash-enhanced', 'air-spin-enhanced', 'aura-enhanced')
RAMPS = {
    2: [(96, 52, 12), (176, 104, 24), (236, 168, 44), (255, 216, 104), (255, 246, 214)],     # 금
    3: [(84, 10, 28), (172, 24, 48), (236, 58, 72), (255, 138, 136), (255, 238, 236)],       # 진홍
}


def luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def recolor(im, ramp):
    im = im.convert('RGBA')
    colors = sorted({p[:3] for p in im.getdata() if p[3] == 255}, key=luma)
    n = len(colors)
    table = {c: ramp[min(len(ramp) - 1, round(i * (len(ramp) - 1) / max(1, n - 1)))] for i, c in enumerate(colors)}
    out = Image.new('RGBA', im.size)
    out.putdata([(*table[p[:3]], 255) if p[3] == 255 else (0, 0, 0, 0) for p in im.getdata()])
    return out


def main():
    for name in SHEETS:
        src = Image.open(os.path.join(FX, name + '.png'))
        meta = json.load(open(os.path.join(FX, name + '.json'), encoding='utf-8'))
        for level, ramp in RAMPS.items():
            new = f'{name}{level}'
            recolor(src, ramp).save(os.path.join(FX, new + '.png'))
            m = dict(meta, id=f'fx/{new}', source=f'tools/recolor_fx.py ({name} 다시 칠함, 강화 {level}단계)')
            with open(os.path.join(FX, new + '.json'), 'w', encoding='utf-8') as f:
                json.dump(m, f, ensure_ascii=False, indent=1)
            print('saved', new)


if __name__ == '__main__':
    main()
