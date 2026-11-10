"""타일 5종(벽 3변형, 얇은 바닥, 가시)을 SVG(포터블 프로필)로 코드에서 그린다. 40x40, 도트 1px, 이미지 모델 없음.

벽은 이웃 타일과 이어 붙여도 이음매가 어색하지 않도록 가장자리에 밝은/어두운 1px 면을 두는 판금 모양이다.
사용: python tools/codeart/make_tiles.py   (SVG만 만든다. 렌더링은 tools/make_codeart.py)
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
T = 40


def svg(body, name):
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{T}" height="{T}" viewBox="0 0 {T} {T}" '
            f'shape-rendering="crispEdges" data-codeart="{name}">\n{body}\n</svg>\n')
    (OUT / f"{name}.svg").write_text(text, encoding="utf-8")


def r(cls, x, y, w, h):
    return f'  <rect class="c-{cls}" x="{x}" y="{y}" width="{w}" height="{h}"/>'


def panel():
    """공통 판금 바탕: 어두운 외곽 1px, 위·왼쪽 밝은 면, 아래·오른쪽 어두운 면, 모서리 리벳."""
    parts = [r("outline", 0, 0, T, T), r("steel-base", 1, 1, T - 2, T - 2),
             r("steel-light", 1, 1, T - 2, 2), r("steel-light", 1, 1, 2, T - 2),
             r("steel-dark", 3, T - 3, T - 4, 2), r("steel-dark", T - 3, 3, 2, T - 4)]
    for x, y in ((5, 5), (T - 7, 5), (5, T - 7), (T - 7, T - 7)):
        parts += [r("rivet", x, y, 2, 2), r("steel-deep", x + 2, y + 2, 1, 1)]
    return parts


def solid_a():
    parts = panel() + [r("steel-dark", 10, 19, 20, 1), r("steel-light", 10, 20, 20, 1)]  # 가운데 홈 한 줄
    svg("\n".join(parts), "tile_solid_a")


def solid_b():
    parts = panel()
    parts += [r("steel-dark", 9, 12, 22, 1), r("steel-light", 9, 13, 22, 1),
              r("steel-dark", 9, 26, 22, 1), r("steel-light", 9, 27, 22, 1),
              r("crystal-dark", 17, 17, 6, 6), r("crystal-mid", 18, 18, 4, 4), r("crystal-light", 18, 18, 2, 1)]  # 청록 표시등
    svg("\n".join(parts), "tile_solid_b")


def solid_c():
    parts = panel()
    parts += [r("steel-dark", 12, 8, 1, 10), r("steel-dark", 13, 17, 5, 1), r("steel-dark", 18, 17, 1, 8),
              r("steel-dark", 19, 24, 7, 1), r("steel-light", 13, 8, 1, 9)]  # 금
    svg("\n".join(parts), "tile_solid_c")


def oneway():
    """위쪽 10px만 칠하는 얇은 바닥 (격자 무늬 철판, 가운데 청록 불빛)."""
    parts = [r("outline", 0, 0, T, 10), r("steel-light", 0, 1, T, 1), r("steel-base", 0, 2, T, 6), r("steel-dark", 0, 8, T, 1)]
    for x in range(2, T, 6):
        parts.append(r("steel-dark", x, 3, 2, 4))
    for x in (6, 20, 34):
        parts += [r("crystal-mid", x, 3, 2, 2), r("crystal-light", x, 3, 1, 1)]
    svg("\n".join(parts), "tile_oneway")


def spike():
    parts = []
    for i in range(5):
        x = i * 8
        # 한 칸 8px 폭 삼각 가시: 아래에서 위로 줄어든다 (계단 모양)
        for k, w in enumerate((8, 8, 6, 6, 4, 4, 2, 2)):
            y = T - 1 - k * 2
            left = x + (8 - w) // 2
            parts.append(r("danger-dark", left, y - 1, w, 2))
            parts.append(r("danger", left, y - 1, max(w - 3, 1), 2))
        parts.append(r("outline", x + 3, T - 18, 2, 1))
    parts.append(r("outline", 0, T - 1, T, 1))
    svg("\n".join(parts), "tile_spike")


def main():
    for fn in (solid_a, solid_b, solid_c, oneway, spike):
        fn()
    print("saved 5 tile SVGs")


if __name__ == "__main__":
    main()
