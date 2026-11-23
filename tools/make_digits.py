"""피해 숫자 전용 픽셀 글꼴 (2026-11-21, 코드로 그림): 0~9를 굵은 3x5 점 글꼴로 그려 한 줄 시트로 저장한다.

  assets/ui/dmg_tiny.png   점 하나 4px   게이지 증감 (+3%, -5%)
  assets/ui/dmg_small.png  점 하나 6px   보통 타격 (v7: 4 -> 6)
  assets/ui/dmg_big.png    점 하나 8px   강한 타격·궁극기 (v7: 6 -> 8)
글자: 0~9와 + - % (게이지 증감도 같은 글꼴).
흰 몸통(아래 한 줄은 옅은 회색으로 입체감) + 짙은 2px 테두리. 게임이 색을 곱해(SDL color mod) 구간·강화 색으로 칠한다
(흰색 -> 그 색, 테두리는 짙은 그대로). 알파는 켜짐·꺼짐뿐.
사용: python tools/make_digits.py
"""
import os

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
GLYPHS = {
    '0': ['###', '#.#', '#.#', '#.#', '###'],
    '1': ['##.', '.#.', '.#.', '.#.', '###'],
    '2': ['###', '..#', '###', '#..', '###'],
    '3': ['###', '..#', '.##', '..#', '###'],
    '4': ['#.#', '#.#', '###', '..#', '..#'],
    '5': ['###', '#..', '###', '..#', '###'],
    '6': ['###', '#..', '###', '#.#', '###'],
    '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['###', '#.#', '###', '#.#', '###'],
    '9': ['###', '#.#', '###', '..#', '###'],
    '+': ['...', '.#.', '###', '.#.', '...'],
    '-': ['...', '...', '###', '...', '...'],
    '%': ['#.#', '..#', '.#.', '#..', '#.#'],
}
ORDER = '0123456789+-%'          # src/drama.DIGITS와 같은 순서
INK = (22, 14, 30, 255)
WHITE = (255, 255, 255, 255)
SHADE = (196, 196, 204, 255)
OUTLINE = 2


def sheet(dot):
    cw, ch = 3 * dot + 2 * OUTLINE + 1, 5 * dot + 2 * OUTLINE + 1
    im = Image.new('RGBA', (cw * len(ORDER), ch), (0, 0, 0, 0))
    px = im.load()
    for k, g in enumerate(ORDER):
        ox, oy = k * cw + OUTLINE, OUTLINE
        on = set()
        for r, row in enumerate(GLYPHS[g]):
            for c, ch_ in enumerate(row):
                if ch_ == '#':
                    for y in range(dot):
                        for x in range(dot):
                            on.add((ox + c * dot + x, oy + r * dot + y))
        for (x, y) in on:                                    # 테두리: 몸통 둘레 OUTLINE px
            for dy in range(-OUTLINE, OUTLINE + 1):
                for dx in range(-OUTLINE, OUTLINE + 1):
                    q = (x + dx, y + dy)
                    if q not in on and 0 <= q[0] < im.width and 0 <= q[1] < ch:
                        px[q] = INK
        for (x, y) in on:
            bottom_row = (y - oy) >= 4 * dot                 # 맨 아래 점 줄은 옅게 (입체감)
            px[x, y] = SHADE if bottom_row else WHITE
    return im


def main():
    # v7 (2026-11-24 사용자: 피해 숫자가 작다): 점 4 -> 6, 6 -> 8. 게이지 증감(+3%)은 점 4(tiny)로 같은 글꼴
    for name, dot in (('dmg_tiny', 4), ('dmg_small', 6), ('dmg_big', 8)):
        im = sheet(dot)
        im.save(os.path.join(ROOT, 'assets', 'ui', name + '.png'))
        print('saved', name, im.size)


if __name__ == '__main__':
    main()
