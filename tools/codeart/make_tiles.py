"""타일 5종(벽 3변형, 얇은 바닥, 가시)을 SVG(포터블 프로필)로 코드에서 그린다. 60x60, 도트 1px, 이미지 모델 없음.

벽은 판금 패널이다. 가장자리에 밝은/어두운 면을 두고 가운데에 환풍구, 파이프, 균열 같은 디테일을 넣는다.
사용: python tools/codeart/make_tiles.py   (SVG만 만든다. 렌더링은 tools/make_codeart.py)
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
T = 60


def svg(body, name):
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{T}" height="{T}" viewBox="0 0 {T} {T}" '
            f'shape-rendering="crispEdges" data-codeart="{name}">\n{body}\n</svg>\n')
    (OUT / f"{name}.svg").write_text(text, encoding="utf-8")


def r(cls, x, y, w, h):
    return f'  <rect class="c-{cls}" x="{x}" y="{y}" width="{w}" height="{h}"/>'


def rivet(x, y):
    return [r("rivet", x, y, 3, 3), r("steel-light", x, y, 1, 1), r("steel-deep", x + 2, y + 2, 1, 1)]


def panel():
    """공통 판금 바탕: 어두운 외곽 1px, 위·왼쪽 밝은 면, 아래·오른쪽 어두운 면, 안쪽 홈, 모서리 리벳."""
    parts = [r("outline", 0, 0, T, T), r("steel-base", 1, 1, T - 2, T - 2),
             r("steel-light", 1, 1, T - 2, 2), r("steel-light", 1, 1, 2, T - 2),
             r("steel-dark", 3, T - 3, T - 4, 2), r("steel-dark", T - 3, 3, 2, T - 4),
             # 안쪽 홈(안쪽 패널): 어두운 선 위, 밝은 선 아래
             r("steel-dark", 8, 8, T - 16, 1), r("steel-dark", 8, 8, 1, T - 16),
             r("steel-light", 9, T - 9, T - 17, 1), r("steel-light", T - 9, 9, 1, T - 17)]
    for x, y in ((5, 5), (T - 8, 5), (5, T - 8), (T - 8, T - 8)):
        parts += rivet(x, y)
    return parts


def solid_a():
    """환풍구: 가운데 가로 슬릿 3줄."""
    parts = panel()
    for y in (22, 29, 36):
        parts += [r("steel-deep", 17, y, 26, 3), r("steel-light", 17, y + 3, 26, 1), r("outline", 17, y, 26, 1)]
    svg("\n".join(parts), "tile_solid_a")


def solid_b():
    """파이프와 청록 표시등."""
    parts = panel()
    parts += [r("outline", 10, 22, 40, 16), r("steel-light", 10, 23, 40, 2), r("steel-mid", 10, 25, 40, 8),
              r("steel-dark", 10, 33, 40, 4), r("outline", 10, 37, 40, 1)]
    for x in (14, 44):
        parts += [r("steel-light", x, 22, 2, 16), r("steel-dark", x + 2, 22, 1, 16)]  # 이음 고리
    parts += [r("outline", 25, 26, 10, 7), r("crystal-dark", 26, 27, 8, 5), r("crystal-mid", 27, 28, 6, 3),
              r("crystal-light", 27, 28, 3, 1), r("crystal-core", 27, 28, 1, 1)]
    svg("\n".join(parts), "tile_solid_b")


def solid_c():
    """균열과 얼룩."""
    parts = panel()
    parts += [r("steel-deep", 15, 33, 8, 5), r("steel-deep", 17, 31, 4, 2), r("steel-dark", 38, 40, 7, 4)]  # 얼룩
    crack = [(31, 12, 1, 6), (30, 18, 1, 5), (29, 23, 1, 4), (30, 27, 3, 1), (32, 28, 1, 5), (33, 33, 1, 4), (34, 36, 3, 1)]
    for x, y, w, h in crack:
        parts += [r("outline", x, y, w, h), r("steel-light", x + 1, y, 1 if w == 1 else w, 1)]
    svg("\n".join(parts), "tile_solid_c")


def oneway():
    """위쪽 15px만 칠하는 얇은 바닥: 격자 철판, 아래쪽 받침, 청록 불빛."""
    h = 15
    parts = [r("outline", 0, 0, T, h), r("steel-light", 0, 1, T, 2), r("steel-base", 0, 3, T, 7),
             r("steel-dark", 0, 10, T, 2), r("steel-deep", 0, 12, T, 2), r("outline", 0, 14, T, 1)]
    for x in range(3, T, 8):
        parts += [r("steel-deep", x, 4, 4, 5), r("steel-light", x, 9, 4, 1)]  # 구멍과 아랫면 반사
    for x in (10, 30, 50):
        parts += [r("outline", x - 1, 11, 4, 3), r("crystal-mid", x, 12, 2, 1), r("crystal-light", x, 12, 1, 1)]
    svg("\n".join(parts), "tile_oneway")


def spike():
    parts = []
    widths = (10, 10, 8, 8, 6, 6, 4, 4, 2)
    for i in range(6):
        x0 = i * 10
        for k, w in enumerate(widths):
            y = T - 3 * (k + 1)
            left = x0 + (10 - w) // 2
            parts += [r("danger-dark", left, y, w, 3), r("danger", left, y, max(w - 3, 1), 3)]
        parts.append(r("steel-light", x0 + 4, T - 3 * len(widths), 2, 1))  # 끝점 반짝임
    parts += [r("outline", 0, T - 3, T, 3), r("steel-dark", 0, T - 3, T, 1)]
    svg("\n".join(parts), "tile_spike")


def main():
    for fn in (solid_a, solid_b, solid_c, oneway, spike):
        fn()
    print("saved 5 tile SVGs")


if __name__ == "__main__":
    main()
