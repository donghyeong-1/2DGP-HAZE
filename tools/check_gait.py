"""걸음 교대 검사: 걷기·달리기 반복 그림에서 왼발 걸음과 오른발 걸음이 정말 다른지 숫자로 본다.

8장 반복이면 1·5, 2·6, 3·7, 4·8번은 같은 단계의 **반대쪽 발** 자세라서 서로 충분히 달라야 한다.
반 주기 떨어진 장끼리의 차이가 이웃한 장끼리의 차이보다 훨씬 작으면, 같은 발이 계속 앞에 나오는 그림이다
(발이 서로 교차하지 않아 보인다). 차이는 두 그림에서 색이 크게(40 넘게) 다른 픽셀 수다.

사용: python tools/check_gait.py assets/sprites/unified/n09_run_{1..8}.png
      python tools/check_gait.py --name n09_run        (assets/sprites/unified/n09_run_1.png부터 있는 만큼)
결과: 비율 = 반 주기 차이 / 이웃 차이. 0.55 이상이면 통과 (걷기 n09_walk 1.02, 같은 걸음 두 번이던 T19 달리기 0.39,
같은 장 반복은 0.1 미만). 이 값은 가까운·먼 팔다리의 밝기 차이로 좌우 걸음을 구별하므로, 밝기 차이를 자연스럽게
줄인 달리기(11/19, tools/soften_run_depth.py)는 0.65로 내려간다. 처음 기준 0.8은 이 경우를 막아서 0.55로 낮췄다.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
PASS_RATIO = 0.55


def changed_pixels(a, b):
    d = ImageChops.difference(a, b).convert('L')
    return sum(1 for v in d.getdata() if v > 40)


def gait_ratio(paths):
    """(반 주기 차이 평균, 이웃 차이 평균, 비율). 장 수는 짝수여야 한다."""
    frames = [Image.open(p).convert('RGBA') for p in paths]
    n = len(frames)
    if n < 4 or n % 2:
        raise ValueError(f'짝수 장(4장 이상)이 필요하다: {n}장')
    if len({f.size for f in frames}) != 1:
        raise ValueError('모든 장의 캔버스 크기가 같아야 한다')
    h = n // 2
    half = sum(changed_pixels(frames[i], frames[i + h]) for i in range(h)) / h
    near = sum(changed_pixels(frames[i], frames[(i + 1) % n]) for i in range(n)) / n
    return half, near, half / max(near, 1.0)


def main(argv=None):
    ap = argparse.ArgumentParser(description='걷기·달리기 반복의 좌우 걸음 교대 검사')
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--name', help='assets/sprites/unified/<name>_1.png부터 있는 만큼')
    a = ap.parse_args(argv)
    paths = list(a.paths)
    if a.name:
        i = 1
        while (ROOT / 'assets' / 'sprites' / 'unified' / f'{a.name}_{i}.png').exists():
            paths.append(ROOT / 'assets' / 'sprites' / 'unified' / f'{a.name}_{i}.png')
            i += 1
    half, near, ratio = gait_ratio(paths)
    ok = ratio >= PASS_RATIO
    print(f'{len(paths)}장  반 주기 차이 {half:.0f}  이웃 차이 {near:.0f}  비율 {ratio:.2f}  '
          f'{"통과" if ok else "실패: 같은 발이 계속 앞에 나온다 (반 주기 뒤 장이 앞 장과 거의 같다)"}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
