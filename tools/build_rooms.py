"""방 템플릿(data/rooms/*.txt)을 코드로 설계해 만들고 room_check로 검사한다.

손으로 글자를 맞추면 어긋나기 쉬워서, 기둥·천장 돌출부·계단식 단·함정 구덩이 같은 구조물을 함수로 놓는다.
문 위치와 방 크기는 이웃 방과의 연결(data/stages/stage1.py)에 묶여 있으므로 바꾸지 않는다.

사용: python tools/build_rooms.py            (검사만)
      python tools/build_rooms.py --write    (파일로 쓴다)
      python tools/build_rooms.py --show 방이름
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import room_check  # noqa: E402

OUT = os.path.join(ROOT, 'data', 'rooms')


class B:
    """방 하나. 가장자리는 벽, 아래 두 줄은 바닥. stand는 바닥 위에 서는 줄."""

    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.g = [['.'] * cols for _ in range(rows)]
        for c in range(cols):
            self.g[0][c] = '#'
            self.g[rows - 2][c] = '#'
            self.g[rows - 1][c] = '#'
        for r in range(rows):
            self.g[r][0] = '#'
            self.g[r][cols - 1] = '#'
        self.stand = rows - 3

    # ----- 기본 -----
    def solid(self, r0, r1, c0, c1):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                self.g[r][c] = '#'
        return self

    def oneway(self, r, c0, c1):
        for c in range(c0, c1 + 1):
            self.g[r][c] = '='
        return self

    def spikes(self, r, c0, c1):
        for c in range(c0, c1 + 1):
            self.g[r][c] = '^'
        return self

    def mark(self, r, c, ch):
        self.g[r][c] = ch
        return self

    # ----- 구조물 -----
    def ceiling(self, c0, c1, depth):
        """천장에 매달린 돌출부 (맨 윗줄 아래로 depth줄)."""
        return self.solid(1, depth, c0, c1)

    def stalactite(self, c, length):
        """천장에서 내려온 뾰족한 돌기 (아래로 갈수록 좁아진다)."""
        for i in range(length):
            half = max(0, (length - 1 - i) // 2)
            for c2 in range(c - half, c + half + 1):
                self.g[1 + i][c2] = '#'
        return self

    def steps(self, c0, direction, heights, width=3):
        """바닥에서 솟은 계단식 단. direction=1이면 오른쪽으로 갈수록 높아진다. heights는 단마다 높이(줄)."""
        c = c0
        for h in heights:
            self.solid(self.stand - h + 1, self.stand, c, c + width - 1)
            c += width * direction if direction > 0 else -width
            if direction < 0:
                c = c
        return self

    def pit(self, c0, c1, deep=True):
        """바닥에 파인 가시 구덩이 (첫 바닥줄을 가시로 바꾼다)."""
        return self.spikes(self.rows - 2, c0, c1)

    def doorL(self, bottom=None):
        b = self.stand if bottom is None else bottom
        for r in (b - 2, b - 1, b):
            self.g[r][0] = 'L'
        return self

    def doorR(self, bottom=None):
        b = self.stand if bottom is None else bottom
        for r in (b - 2, b - 1, b):
            self.g[r][self.cols - 1] = 'R'
        return self

    def doorU(self, c0):
        for c in range(c0, c0 + 3):
            self.g[0][c] = 'U'
        return self

    def doorD(self, c0):
        for c in range(c0, c0 + 3):
            self.g[self.rows - 2][c] = 'D'
            self.g[self.rows - 1][c] = 'D'
        return self

    def lines(self):
        return [''.join(r) for r in self.g]


R = {}

# ============ 시작 홀 40x20: 오른쪽 문, 위 문. 낮은 천장 아래에서 시작해 굴뚝(위 문)까지 오르는 길 ============
b = B(40, 20)
b.doorR().doorU(18)
b.ceiling(1, 12, 3)                                                     # 시작 지점 위 낮은 천장
b.solid(1, 4, 14, 15).solid(1, 4, 25, 26)                               # 굴뚝 벽 (위 문으로 곧게 오른다)
b.oneway(15, 4, 9).oneway(12, 8, 13).oneway(9, 12, 17).oneway(6, 15, 23)
b.solid(15, 17, 28, 31).solid(13, 14, 29, 30)                           # 2단 제단
b.pit(21, 23)                                                           # 바닥 가시 구덩이
b.mark(b.stand, 4, 'P')
R['start_hall'] = b

# ============ 허브 동굴 48x27: 사방 문. 양쪽 돌계단 -> 가운데 사다리 -> 위 문, 가운데 구멍은 아래 문 ============
b = B(48, 27)
b.doorL().doorR().doorU(22).doorD(22)
b.solid(21, 23, 7, 10).solid(19, 23, 11, 13)                            # 왼쪽 돌계단 (2단)
b.solid(21, 23, 37, 40).solid(19, 23, 34, 36)                           # 오른쪽 돌계단
b.oneway(16, 14, 21).oneway(16, 26, 33)                                 # 계단 꼭대기에서 첫 발판
b.oneway(13, 17, 25).oneway(10, 20, 28).oneway(7, 19, 28)               # 가운데 사다리: 아래 문 위로 이어져 위 문 아래에서 끝
b.solid(1, 3, 16, 20).solid(1, 3, 26, 30)                               # 위 문 굴뚝
b.stalactite(5, 5).stalactite(11, 4).stalactite(37, 4).stalactite(43, 5)
b.solid(23, 23, 18, 19).solid(23, 23, 27, 28)                           # 아래 구멍 양옆 낮은 담 (1칸)
b.pit(15, 17).pit(31, 33)
for r, c in ((b.stand, 14), (15, 31), (20, 8), (20, 39), (15, 17), (15, 19)):
    b.mark(r, c, 'E')
R['hub_cavern'] = b

# ============ 교차로 48x22: 사방 문. 가운데 피라미드 위로 올라 위 문으로. 양끝 낮은 천장 회랑 ============
b = B(48, 22)
b.doorL().doorR().doorU(22).doorD(4)
b.solid(17, 19, 18, 29).solid(15, 16, 21, 26).solid(13, 14, 23, 24)     # 계단식 피라미드
b.oneway(10, 20, 27).oneway(7, 19, 28)                                  # 위 문으로 가는 발판
b.solid(1, 4, 16, 20).solid(1, 4, 26, 30)                               # 위 문 굴뚝
b.ceiling(1, 9, 2).ceiling(38, 46, 2)                                   # 양끝 낮은 천장
b.oneway(14, 10, 16).oneway(14, 31, 37)                                 # 피라미드 양옆 발판
b.pit(12, 14).pit(33, 35)
b.solid(16, 18, 8, 9).solid(16, 18, 38, 39)                             # 양쪽 낮은 기둥 (3칸, 뛰어 넘는다)
for r, c in ((b.stand, 16), (b.stand, 32), (13, 12), (13, 34), (b.stand, 36), (13, 15)):
    b.mark(r, c, 'E')
R['crossing'] = b

# ============ 우물 방 32x30: 아래 문(바닥 구멍)과 오른쪽 문. 두꺼운 돌 턱이 번갈아 이어지는 수직 갱도 ============
b = B(32, 30)
b.doorD(14).doorR()
b.solid(24, 25, 1, 9)                                                   # 왼쪽 두꺼운 턱
b.oneway(21, 11, 17).oneway(18, 19, 26).oneway(15, 12, 18).oneway(12, 4, 10).oneway(9, 12, 20)
b.solid(5, 6, 22, 30)                                                   # 위쪽 오른쪽 돌 턱 (장식 겸 엄폐)
b.stalactite(5, 4).stalactite(16, 3)
b.solid(22, 23, 28, 30)                                                 # 오른쪽 문 위 낮은 돌출
b.pit(24, 26)
for r, c in ((b.stand, 6), (b.stand, 10), (20, 12), (17, 22), (14, 15), (11, 7)):
    b.mark(r, c, 'E')
R['well_room'] = b

# ============ 아레나 33x18 (고농도): 기둥 두 개 사이의 다리. 바깥 계단으로 기둥 위에 올라 다리를 건넌다 ============
b = B(33, 18)
b.doorL().doorR()
b.solid(9, 14, 8, 9).solid(9, 14, 23, 24)                               # 기둥
b.solid(12, 14, 4, 5).solid(12, 14, 27, 28)                             # 바깥 계단
b.oneway(9, 10, 22)                                                     # 다리 (기둥 윗면 높이)
b.solid(1, 2, 12, 20)                                                   # 천장 돌출
b.pit(15, 17)
b.mark(b.stand, 12, 's').mark(b.stand, 20, 's').mark(8, 16, 't').mark(8, 11, 's')
R['arena_05'] = b

# ============ 구덩이 33x18: 가운데 큰 가시 구덩이를 사이에 둔 두 단. 위의 끊어진 다리 ============
b = B(33, 18)
b.doorL().doorR()
b.solid(13, 15, 8, 10).solid(13, 15, 22, 24)                            # 구덩이 양쪽 단
b.pit(11, 21)
b.oneway(11, 9, 15).oneway(11, 17, 23)                                  # 끊어진 다리 (사이 한 칸)
b.oneway(8, 12, 20)
b.stalactite(4, 4).stalactite(28, 4)
b.mark(12, 9, 's').mark(12, 23, 's').mark(10, 12, 't').mark(10, 20, 't').mark(7, 16, 's')
R['pit_02'] = b

# ============ 엄폐 골목 33x18: 높이가 다른 바리케이드와 지붕 낀 터널 ============
b = B(33, 18)
b.doorL().doorR()
b.solid(13, 15, 7, 8).solid(14, 15, 14, 15).solid(12, 15, 21, 22)       # 높이 3 · 2 · 4 바리케이드
b.solid(7, 8, 11, 19)                                                   # 가운데 지붕
b.oneway(10, 8, 10).oneway(10, 20, 24)
b.ceiling(1, 7, 2).ceiling(24, 31, 2)
b.mark(b.stand, 10, 's').mark(b.stand, 17, 's').mark(9, 9, 't').mark(9, 22, 't').mark(b.stand, 24, 's')
R['cover_04'] = b

# ============ 탑 33x18: 가운데 높은 탑과 양쪽 발코니 ============
b = B(33, 18)
b.doorL().doorR()
b.solid(8, 15, 14, 17)                                                  # 탑
b.solid(7, 7, 13, 18)                                                   # 탑 지붕
b.oneway(12, 5, 11).oneway(12, 20, 26)                                  # 발코니
b.solid(9, 10, 1, 5).solid(9, 10, 27, 31)                               # 벽에 붙은 돌 턱
b.oneway(9, 6, 11).oneway(9, 20, 25)
b.ceiling(1, 9, 2).ceiling(22, 31, 2)
b.mark(b.stand, 8, 's').mark(b.stand, 24, 's').mark(11, 8, 't').mark(11, 23, 't')
R['tower_03'] = b

# ============ 회랑 33x18: 이층 회랑. 양쪽 돌 층과 가운데 다리 ============
b = B(33, 18)
b.doorL().doorR()
b.solid(10, 11, 3, 11).solid(10, 11, 21, 29)                            # 양쪽 두꺼운 층
b.oneway(10, 12, 20)                                                    # 가운데 다리
b.oneway(13, 1, 4).oneway(13, 28, 31)                                   # 층에 오르는 계단 발판
b.solid(13, 15, 14, 19)                                                 # 바닥 가운데 낮은 단
b.stalactite(7, 3).stalactite(25, 3)
b.mark(b.stand, 9, 's').mark(b.stand, 23, 's').mark(9, 14, 's').mark(9, 18, 't')
R['hall_01'] = b

# ============ 보스 경기장 48x20: 왼쪽 문. 양끝 돌기둥, 낮은 단과 피할 발판 ============
b = B(48, 20)
b.doorL()
b.oneway(14, 6, 13).oneway(14, 34, 41).oneway(10, 18, 30)
b.solid(17, 17, 22, 27)                                                 # 낮은 단(1칸): 숨을 수 있는 높은 엄폐물은 두지 않는다
# 보스 방은 공중에 벽을 두지 않는다 (숨을 곳이 없어야 한다). 장식은 Room.draw가 배경에 얹는다
b.mark(b.stand, 38, 'B')
R['boss_arena'] = b

# ============ 황금방 28x16: 아래 문으로 들어온다. 제단 3개 ============
b = B(28, 16)
b.doorD(12)
b.solid(12, 12, 3, 5).solid(12, 12, 19, 25)                             # 제단 받침 (높이 1)
for c in (4, 20, 24):
    b.mark(11, c, 'I')
b.oneway(9, 8, 18)
b.stalactite(8, 3).stalactite(19, 3)
R['gold_room'] = b

# ============ 정비방 28x16: 위 문(떨어져 들어옴). 발판 계단으로 다시 올라간다. 진열대 4개 ============
b = B(28, 16)
b.doorU(12)
b.oneway(11, 3, 8).oneway(8, 9, 17)
b.solid(11, 12, 20, 26)                                                 # 진열 선반 받침
for c in (16, 19):
    b.mark(b.stand, c, 'I')
for c in (22, 25):
    b.mark(10, c, 'I')
b.stalactite(5, 3)
R['shop_room'] = b

# ============ 균열방 28x16: 왼쪽 문. 균열 앞 제단 2개 (체력을 내고 들어와 둘 중 하나) ============
b = B(28, 16)
b.doorL()
b.solid(12, 12, 9, 11).solid(12, 12, 17, 19)                            # 제단 받침 (높이 1)
for c in (10, 18):
    b.mark(11, c, 'I')
b.oneway(9, 4, 8).oneway(9, 20, 24)
b.stalactite(14, 4)
R['rift_room'] = b


def main():
    bad = False
    for name, bb in R.items():
        probs = room_check.analyze(bb.lines())
        print(name, f'{bb.cols}x{bb.rows}', 'OK' if not probs else probs)
        bad = bad or bool(probs)
        if '--write' in sys.argv:
            with open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(bb.lines()) + '\n')
        if '--show' in sys.argv and name in sys.argv:
            print('\n'.join(f'{i:2d} {r}' for i, r in enumerate(bb.lines())))
    print('limits', room_check.jump_limits())
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
