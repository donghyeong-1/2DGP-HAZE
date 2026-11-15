"""고철 투척병이 던지는 고철 파이프 조각(투사체)을 SVG(포터블 프로필)로 그린다. 42x24, 도트 1px, 이미지 모델 없음.

오른쪽으로 날아가는 모습으로 그린다. 왼쪽은 실행 중 좌우 반전(회전 아님)으로 처리한다.
사용: python tools/codeart/make_scrap.py   (SVG만 만든다. 렌더링은 tools/make_codeart.py)
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
W, H = 42, 24


def r(cls, x, y, w, h):
    return f'  <rect class="c-{cls}" x="{x}" y="{y}" width="{w}" height="{h}"/>'


def main():
    p = [
        r("outline", 0, 3, 42, 18),                 # 외곽
        r("steel-base", 1, 4, 40, 16),              # 파이프 몸통
        r("steel-light", 1, 4, 40, 3),              # 위쪽 하이라이트
        r("steel-dark", 1, 15, 40, 5),              # 아래쪽 그림자
        r("danger-dark", 6, 7, 9, 8),               # 녹슨 얼룩
        r("danger", 8, 8, 4, 3),
        r("danger-dark", 24, 9, 6, 6),
        r("outline", 17, 4, 2, 16),                 # 이음 홈
        r("outline", 33, 4, 2, 16),
        r("rivet", 3, 6, 3, 3), r("steel-deep", 5, 8, 1, 1),   # 리벳
        r("rivet", 36, 6, 3, 3), r("steel-deep", 38, 8, 1, 1),
        r("outline", 38, 12, 4, 5),                 # 오른쪽 끝이 찌그러진 입구
        r("steel-deep", 39, 13, 3, 3),
        r("fog-light", 0, 9, 1, 3),                 # 청록빛 안개 자국 (앞쪽 끝에 약하게)
    ]
    text = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'shape-rendering="crispEdges" data-codeart="proj_scrap">\n' + "\n".join(p) + "\n</svg>\n")
    (OUT / "proj_scrap.svg").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
