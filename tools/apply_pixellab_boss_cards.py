"""보스 이름 카드를 지금 보스 그림에 맞춰 굽는다 (O4, 2026-11-26, docs/opus/TASKS.md). code + PixelLab.

예전 카드(Codex T34·T47)는 예전 디자인의 인물이었다(크래셔는 웃통 벗은 남자, 아크는 밝은 만화풍 장교, 문지기는 카드 없음).
- 배경: 구역 카드 배경(assets/backgrounds/zone_<테마>.png, 1920x400)을 어둡게 하고, 인물 뒤에 구역 빛 색을 옅게 번지게 한다.
- 인물: PixelLab 상반신(assets/sprites/pixellab/boss_cards_v6/raw_gen/<고른 시안>.png, 1배)을 알파 영역으로 잘라
  최근접 2배(도트 2px)로 오른쪽에 놓는다. 허리가 카드 아래 끝에 닿는다.
- 헤이즈 심장: 사람이 아니라 새로 뽑지 않고 지금 본체(열린 모습 v6_heart_core_3)와 손(heart_hand_idle_1)을 그대로 놓는다(이미 2배 그림).
- 예전 카드는 assets/concept/boss_cards_old/로 옮겨 둔다(이 도구는 옮기지 않는다: git mv로 한 번 옮겼다).
결과: assets/backgrounds/boss_card_<crasher|ark|gatekeeper|heart>.png (1920x400, RGB)

사용: python tools/apply_pixellab_boss_cards.py
"""
import os

from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'assets', 'sprites', 'pixellab', 'boss_cards_v6', 'raw_gen')
OUT = os.path.join(ROOT, 'assets', 'backgrounds')
W, H = 1920, 400
SCALE = 2
RIGHT = 140                 # 인물 오른쪽 끝과 카드 오른쪽 끝 사이
DARK = 0.5                  # 배경 밝기

# 보스 -> (고른 시안, 구역 배경, 인물 뒤 빛 색). 고른 이유는 boss_cards_v6/GENERATION_LOG.md
CARDS = {
    'crasher': ('crasher_2', 'zone_foundry', (255, 120, 50)),
    'ark': ('ark_1', 'zone_haze', (60, 220, 200)),
    'gatekeeper': ('gatekeeper_1', 'zone_cell', (120, 170, 230)),
    'heart': (None, 'zone_haze', (60, 230, 210)),
}


def background(zone, glow, center_x):
    bg = Image.open(os.path.join(OUT, zone + '.png')).convert('RGB').resize((W, H), Image.NEAREST)
    bg = Image.eval(bg, lambda v: int(v * DARK))
    halo = Image.new('L', (W, H), 0)                                   # 인물 뒤에 옅게 번지는 구역 빛
    from PIL import ImageDraw
    d = ImageDraw.Draw(halo)
    d.ellipse((center_x - 230, H - 330, center_x + 230, H + 120), fill=55)
    halo = halo.filter(ImageFilter.GaussianBlur(60))
    color = Image.new('RGB', (W, H), glow)
    return Image.composite(color, bg, halo)


def portrait(name):
    """고른 상반신: 알파 영역으로 잘라 최근접 2배. 알파는 0/255 그대로."""
    im = Image.open(os.path.join(RAW, name + '.png')).convert('RGBA')
    im = im.crop(im.getchannel('A').getbbox())
    return im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)


def place(kind):
    """(카드 그림, 인물 그림, 인물 왼쪽 위 좌표). 테스트가 2px 격자를 잰다."""
    name, zone, glow = CARDS[kind]
    if name is None:
        return heart_card(zone, glow), None, None
    fig = portrait(name)
    x, y = W - RIGHT - fig.width, H - fig.height
    card = background(zone, glow, x + fig.width // 2)
    card.paste(fig, (x, y), fig)
    return card, fig, (x, y)


def heart_card(zone, glow):
    unified = os.path.join(ROOT, 'assets', 'sprites', 'unified')
    core = Image.open(os.path.join(unified, 'v6_heart_core_3.png')).convert('RGBA')
    core = core.crop(core.getchannel('A').getbbox())
    hand = Image.open(os.path.join(unified, 'heart_hand_idle_1.png')).convert('RGBA')
    hand = hand.crop(hand.getchannel('A').getbbox())
    cx = W - RIGHT - core.width // 2
    card = background(zone, glow, cx)
    top = 24                                                           # 본체 위 끝을 보이고 아래는 카드 밖으로 잘린다
    card.paste(core, (cx - core.width // 2, top), core)
    for side in (-1, 1):
        h = hand if side > 0 else hand.transpose(Image.FLIP_LEFT_RIGHT)
        hx = cx + side * (core.width // 2 + 10) - (0 if side > 0 else h.width)
        hx = max(0, min(W - h.width, hx))
        card.paste(h, (hx // 2 * 2, H - h.height - 20), h)
    return card


def main():
    for kind in CARDS:
        card, _, _ = place(kind)
        card.save(os.path.join(OUT, f'boss_card_{kind}.png'))
        print('저장', f'assets/backgrounds/boss_card_{kind}.png', card.size)


if __name__ == '__main__':
    main()
