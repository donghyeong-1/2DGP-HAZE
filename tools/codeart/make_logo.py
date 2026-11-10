"""타이틀 로고 "HAZE"를 SVG(포터블 프로필)로 코드에서 그린다. 이미지 모델 없이 만든 코드 아트다.

글자는 직선만 쓴 각진 수정 모양이고, 외곽선 1px(#0b1020), 밝음·중간·어두움 면 분할, 아래쪽에 안개 점무늬를 둔다.
사용: python tools/codeart/make_logo.py   (SVG만 만든다. 렌더링은 tools/make_codeart.py)
"""
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "logo.svg"
K = 1.5  # 1280x720 기준 로고(320x96) 대비 배율. 좌표는 모두 정수로 반올림한다
W, H = 480, 144
ORIGINS = [(18, 12), (134, 12), (250, 12), (366, 12)]


def S(v):
    return round(v * K)


def scale_nums(text):
    """경로·점 목록의 모든 숫자를 K배 하고 정수로 반올림한다. (문자 L, M, Z 등은 그대로)"""
    import re
    return re.sub(r"-?\d+(?:\.\d+)?", lambda m: str(round(float(m.group()) * K)), text)

# 글자 윤곽 (글자 왼쪽 위가 0,0). A는 안쪽 구멍을 evenodd로 뚫는다.
LETTERS = {
    "H": "M0,0 L18,0 L18,22 L46,22 L46,0 L64,0 L64,62 L46,62 L46,40 L18,40 L18,62 L0,62 Z",
    "A": "M0,62 L22,0 L42,0 L64,62 L46,62 L42,48 L22,48 L18,62 Z M27,34 L37,34 L32,16 Z",
    "Z": "M0,0 L64,0 L64,16 L28,46 L64,46 L64,62 L0,62 L0,46 L36,16 L0,16 Z",
    "E": "M0,0 L64,0 L64,16 L18,16 L18,24 L52,24 L52,38 L18,38 L18,46 L64,46 L64,62 L0,62 Z",
}


def letter(idx, ch, x0, y0):
    d = scale_nums(LETTERS[ch])
    cid = f"clip{idx}"
    return f"""  <g transform="translate({x0} {y0})">
    <clipPath id="{cid}"><path fill-rule="evenodd" d="{d}"/></clipPath>
    <path class="c-outline" stroke-width="2" stroke-linejoin="miter" style="stroke:#0b1020" fill-rule="evenodd" d="{d}"/>
    <path class="c-crystal-mid" fill-rule="evenodd" d="{d}"/>
    <g clip-path="url(#{cid})">
      <rect class="c-crystal-light" x="-3" y="-3" width="102" height="{S(10)}"/>
      <rect class="c-crystal-core" x="-3" y="-3" width="102" height="{S(3)}"/>
      <polygon class="c-crystal-light" points="{scale_nums('-2,-2 12,-2 -2,40')}"/>
      <polygon class="c-crystal-dark" points="{scale_nums('70,20 70,70 24,70')}"/>
      <rect class="c-crystal-dark" x="-3" y="{S(50)}" width="102" height="{S(14)}"/>
      <rect class="c-crystal-deep" x="-3" y="{S(58)}" width="102" height="{S(6)}"/>
    </g>
  </g>"""


def fog(rng):
    parts = []
    for row, y in enumerate(range(S(76), S(94), 3)):
        density = 0.55 - row * 0.05
        x = 4
        while x < W - 4:
            w = rng.randint(4, 15)
            if rng.random() < density:
                cls = "c-fog-light" if rng.random() < 0.45 else "c-fog-dark"
                parts.append(f'  <rect class="{cls}" x="{x}" y="{y}" width="{w}" height="3"/>')
            x += w + rng.randint(2, 7)
    return "\n".join(parts)


def main():
    rng = random.Random(11)
    body = "\n".join(letter(i, ch, x, y) for i, (ch, (x, y)) in enumerate(zip("HAZE", ORIGINS)))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" shape-rendering="crispEdges" data-codeart="haze-logo" data-anchor="240 143">
{fog(rng)}
{body}
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
