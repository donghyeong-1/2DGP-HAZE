"""달리기 그림(T21)의 앞뒤 팔다리 밝기 차이를 줄인다.

T21은 왼발·오른발 걸음을 구별하려고 가까운 쪽 바지를 밝은 회색, 먼 쪽 바지를 거의 검정, 먼 쪽 팔을 갈색으로 칠했다.
게임(1배, 달리는 속도)에서는 이 차이가 너무 커서 '두 다리가 자리를 바꾸는' 것처럼 끊겨 보였다(사용자 플레이 2026-11-19).
같은 팔레트 안의 가까운 색으로 옮겨 차이를 줄인다: 가까운 쪽은 한두 단계 어둡게, 먼 쪽은 한 단계 밝게.
원본(assets/sprites/forge/n09_run_v2/frames/run-1~8.png, Codex)은 그대로 두고 게임용 사본(assets/sprites/unified/n09_run_1~8.png)만 만든다.

사용: python tools/soften_run_depth.py            (적용)
      python tools/soften_run_depth.py --preview  (적용하지 않고 비교 그림만: scratch 경로를 인자로)
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets' / 'sprites' / 'forge' / 'n09_run_v2' / 'frames'
OUT = ROOT / 'assets' / 'sprites' / 'unified'
BELT_ROW = 66          # 이 줄 아래(다리 쪽)의 회색만 바꾼다: 위쪽 회색은 셔츠·머리 하이라이트일 수 있다

# 가까운 쪽 바지(밝은 회색) -> 한두 단계 어둡게 (대기 자세 바지 색에 가깝게)
NEAR_PANTS = {(120, 127, 133): (79, 80, 92), (99, 108, 111): (68, 71, 79), (151, 160, 163): (99, 108, 111)}
# 먼 쪽 바지(거의 검정) -> 한 단계 밝게
FAR_PANTS = {(22, 28, 26): (32, 38, 36), (32, 38, 36): (41, 43, 41)}
# 먼 쪽 팔(갈색으로 칠한 피부) -> 그늘진 피부색으로 (위치와 상관없이: 갈색은 먼 팔에만 쓰였다)
FAR_ARM = {(89, 76, 59): (165, 131, 93), (125, 102, 75): (204, 159, 107)}


def soften(img):
    img = img.convert('RGBA')
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            c = (r, g, b)
            if c in FAR_ARM:
                px[x, y] = FAR_ARM[c] + (a,)
            elif y >= BELT_ROW and c in NEAR_PANTS:
                px[x, y] = NEAR_PANTS[c] + (a,)
            elif y >= BELT_ROW and c in FAR_PANTS:
                px[x, y] = FAR_PANTS[c] + (a,)
    return img


def main(argv):
    preview = '--preview' in argv
    frames = [soften(Image.open(SRC / f'run-{i}.png')) for i in range(1, 9)]
    if preview:
        out = Path(argv[argv.index('--preview') + 1])
        out.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(frames, 1):
            f.save(out / f'n09_run_{i}.png')
        print('preview', out)
        return 0
    for i, f in enumerate(frames, 1):
        f.save(OUT / f'n09_run_{i}.png')
    print('saved', OUT / 'n09_run_1~8.png')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
