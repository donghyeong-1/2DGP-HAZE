"""구역 1 중간 보스 '문지기' 그림을 간수(v6 PixelLab) 그림에서 굽는다 (v8 6일 차 대기열 1, docs/NEXT_SESSION.md 4절).

실행 중 확대는 금지(docs/pixel_rules.md 4번)라 미리 구워 둔다:
1. v6 간수 그림(192x192)은 원본 도트(96x96)를 최근접 2배로 키운 것이다. 2칸마다 한 점을 집어 원본 도트로 되돌린다.
2. 색을 바꾼다: 푸른 강철 갑옷 -> 검은 무쇠 + 밝은 모서리는 황동, 주황 빛(면갑·몽둥이) -> 붉은 빛. 같은 밝기 차례를 지켜 명암을 그대로 둔다.
3. 원본 도트를 최근접 3배로 키운다(화면 기준 간수의 1.5배, 도트는 3px). 캔버스 288x288.
4. assets/sprites/unified/boss_gatekeeper_<동작>_<번호>.png, 정지 그림 boss_gatekeeper_idle.png 와 skin_gatekeeper.json(세트 장수·발 기준점)을 쓴다.
   src/sprites.py가 skin_*.json을 읽어 세트를 등록한다(기존 이름을 바꿔 그리지는 않는다: skin은 비어 있다).

실행: python tools/make_gatekeeper.py          (쓰기)
      python tools/make_gatekeeper.py --look   (모아 보기 그림 shots/gatekeeper_look.png)
"""
import colorsys
import json
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNI = os.path.join(ROOT, 'assets', 'sprites', 'unified')
SRC_SCALE, DST_SCALE = 2, 3
SETS = ('idle', 'walk', 'swing', 'heavy', 'bash', 'hurt', 'death')


def recolor(rgb):
    """간수 색 -> 문지기 색 (밝기는 지키고 색만 바꾼다)."""
    r, g, b = rgb
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if r > g + 40 and r > 140:                    # 주황 빛(면갑 틈·몽둥이 끝): 붉은 빛으로
        h, s = 0.995, min(1.0, s * 1.05)
        l = min(0.62, l * 0.95)
    elif b >= r and l >= 0.5:                     # 밝은 강철(모서리·하이라이트): 황동 테두리
        h, s = 0.11, 0.55
        l = min(0.72, l * 1.02)
    elif b >= r:                                  # 푸른 강철 몸판: 검은 무쇠 (어둡게, 채도는 낮게)
        h = 0.75                                  # 아주 옅은 보라 기운: 붉은 공장 배경(관문 테마)과 섞이지 않게
        s = min(0.16, 0.06 + s * 0.25)
        l = l * 0.9
    out = colorsys.hls_to_rgb(h, l, s)
    return tuple(int(round(v * 255)) for v in out)


def convert(path):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    small = im.resize((w // SRC_SCALE, h // SRC_SCALE), Image.NEAREST)   # 2칸마다 한 점 = 원본 도트
    px = small.load()
    cache = {}
    for y in range(small.height):
        for x in range(small.width):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            key = (r, g, b)
            if key not in cache:
                cache[key] = recolor(key)
            px[x, y] = cache[key] + (255,)
    return small.resize((small.width * DST_SCALE, small.height * DST_SCALE), Image.NEAREST)


def still_of(img, ax, ay):
    """정지 그림 한 장(sprites 번호 0 규칙): 발 기준점이 가로 가운데, 발 아래 투명 여백 1px."""
    box = img.getbbox()
    half = max(ax - box[0], box[2] - ax)
    return img.crop((ax - half, 0, ax + half + 1, ay + 1))


def build(write=True):
    with open(os.path.join(UNI, 'skin_guard.json'), encoding='utf-8') as fp:
        guard = json.load(fp)['frames']
    frames, images = {}, {}
    k = DST_SCALE / SRC_SCALE
    for name in SETS:
        count, ax, ay = guard[f'v6_guard_{name}']
        key = f'boss_gatekeeper_{name}'
        # 발 기준점: 원본 도트 좌표(ax/2, ay/2)를 3배. 정수로 (가로는 내림)
        frames[key] = [count, int(ax * k), int(ay * k)]
        for n in range(1, count + 1):
            img = convert(os.path.join(UNI, f'v6_guard_{name}_{n}.png'))
            images[f'{key}_{n}'] = img
            if write:
                img.save(os.path.join(UNI, f'{key}_{n}.png'))
    if write:
        still = still_of(images['boss_gatekeeper_idle_1'], *frames['boss_gatekeeper_idle'][1:])
        still.save(os.path.join(UNI, 'boss_gatekeeper_idle.png'))
        with open(os.path.join(UNI, 'skin_gatekeeper.json'), 'w', encoding='utf-8') as fp:
            json.dump({'frames': frames, 'skin': {}}, fp, ensure_ascii=False, indent=1)
            fp.write('\n')
    return frames, images


def look():
    """간수와 문지기를 1배로 나란히 놓은 모아 보기 (크기·색 비교)."""
    frames, images = build(write=False)
    names = ['idle_1', 'walk_2', 'swing_2', 'heavy_2', 'bash_1', 'hurt_1', 'death_3']
    sheet = Image.new('RGBA', (288 * len(names), 288 + 192), (34, 30, 44, 255))
    for i, n in enumerate(names):
        g = Image.open(os.path.join(UNI, f'v6_guard_{n}.png')).convert('RGBA')
        sheet.paste(g, (288 * i + 48, 288), g)
        im = images[f'boss_gatekeeper_{n}']
        sheet.paste(im, (288 * i, 0), im)
    out = os.path.join(ROOT, 'shots', 'gatekeeper_look.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print(out)


if __name__ == '__main__':
    if '--look' in sys.argv:
        look()
    else:
        f, _ = build()
        print('구웠다:', {k: v for k, v in f.items()})
