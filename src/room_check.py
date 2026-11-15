"""방 템플릿 검사: 플레이어가 이동·점프로 갈 수 있는 곳을 계산해 설계가 막히거나 불가능하지 않은지 확인한다.

pico2d와 무관한 순수 로직이다. 플레이어의 실제 수치(config)에서 한계를 구한다 (level-design 스킬: 이동 한계는
기억이 아니라 컨트롤러에서 잰다). 방 안에서는 '서 있을 수 있는 칸'을 점으로 보고, 걷기·낙하·점프 연결을 간선으로 만든다.
점프 간선은 보수적이다 (직선 경로에 벽이 있으면 막힌다). 대시는 계산에 넣지 않는다 (여유분).

칸 좌표는 (열, 줄)이며 줄 0이 맨 위다. 서 있는 칸 = 몸이 들어갈 빈 칸 두 줄, 바로 아래가 바닥(# 또는 =).
방 크기는 가변이다. 출입구는 L R(좌우 벽 3칸), U(맨 윗줄 3칸), D(바닥 두 줄 3칸 구멍).
"""
import math

import config

SOLID, ONEWAY, SPIKE = '#', '=', '^'
DOOR_CHARS = 'LRUD'


def jump_limits():
    """config에서 구한 점프 한계(칸 단위). rise = 올라갈 수 있는 줄 수, 도달 거리는 보수적으로 줄인다."""
    t = config.TILE
    single = config.JUMP_SPEED ** 2 / (2 * config.GRAVITY) / t           # 한 번 뛰었을 때 높이(칸)
    air = 2 * config.JUMP_SPEED / config.GRAVITY                          # 한 번 뛰었을 때 체공(초)
    run = config.RUN_SPEED / t                                            # 초당 칸
    return {
        'rise_single': math.floor(single * 0.9),      # 3.75칸 -> 3 (여유 10%)
        'rise_double': math.floor(single * 2 * 0.8),  # 약 7.5칸 -> 6
        'reach_single': math.floor(run * air * 0.8),  # 한 번 뛰고 가는 가로 거리 약 5칸
        'reach_double': math.floor(run * air * 2 * 0.8),
    }


class RoomGraph:
    def __init__(self, rows):
        self.rows = rows
        self.nrows = len(rows)
        self.ncols = len(rows[0])
        self.limits = jump_limits()

    # ----- 칸 조회 -----
    def ch(self, col, row):
        if col < 0 or col >= self.ncols or row >= self.nrows:
            return SOLID
        if row < 0:
            return '.'
        c = self.rows[row][col]
        return '.' if c in DOOR_CHARS else c      # 출입구는 열린 것으로 본다

    def solid(self, col, row):
        return self.ch(col, row) == SOLID

    def standable(self, col, row):
        """이 칸에 서 있을 수 있는가: 몸이 들어갈 두 줄이 비어 있고(가시 아님) 아래가 단단한 바닥이다."""
        if self.ch(col, row) in (SOLID, SPIKE) or self.solid(col, row - 1) or self.ch(col, row - 1) == SPIKE:
            return False
        return self.ch(col, row + 1) in (SOLID, ONEWAY)

    def stand_cells(self):
        return [(c, r) for r in range(self.nrows) for c in range(self.ncols) if self.standable(c, r)]

    # ----- 간선 -----
    def _line_clear(self, a, b):
        """a에서 b까지 직선 경로에 단단한 벽이 없는가 (양 끝 칸과 머리 높이까지 본다)."""
        (c0, r0), (c1, r1) = a, b
        steps = max(abs(c1 - c0), abs(r1 - r0))
        for i in range(1, steps):
            c = round(c0 + (c1 - c0) * i / steps)
            r = round(r0 + (r1 - r0) * i / steps)
            if self.solid(c, r) or self.solid(c, r - 1):
                return False
        return True

    def neighbours(self, cell):
        col, row = cell
        lim = self.limits
        out = set()
        # 걷기
        for d in (-1, 1):
            if self.standable(col + d, row):
                out.add((col + d, row))
        # 낭떠러지로 걸어 나가 떨어지기: 옆으로 최대 8칸 흘러가며 가장 가까운 바닥에 내린다
        for d in (-1, 1):
            if self.standable(col + d, row):
                continue
            for k in range(1, 9):
                c = col + d * k
                if self.solid(c, row) or self.solid(c, row - 1):
                    break
                for r in range(row, self.nrows):
                    if self.solid(c, r):
                        break
                    if self.standable(c, r) and r > row:
                        if self._line_clear(cell, (c, r)):
                            out.add((c, r))
                        break
        # 점프: 올라가거나 같은 높이로 건너거나 뛰어내리기
        for r2 in range(max(0, row - lim['rise_double']), min(self.nrows, row + 14)):
            rise = row - r2
            for c2 in range(max(0, col - 9), min(self.ncols, col + 10)):
                if (c2, r2) == cell or not self.standable(c2, r2):
                    continue
                dc = abs(c2 - col)
                if rise > lim['rise_double']:
                    continue
                if rise > lim['rise_single']:
                    reach = lim['reach_single']                # 이중 점프가 필요한 높이: 가로는 짧게
                elif rise > 0:
                    reach = lim['reach_double']
                else:
                    reach = lim['reach_double'] + 1            # 같은 높이·내려가기는 더 멀리
                if dc <= reach and self._line_clear(cell, (c2, r2)):
                    out.add((c2, r2))
        return out

    def reachable(self, start):
        seen, stack = {start}, [start]
        while stack:
            cell = stack.pop()
            for n in self.neighbours(cell):
                if n not in seen:
                    seen.add(n)
                    stack.append(n)
        return seen

    # ----- 출입구 -----
    def doors(self):
        """{방향: [(열, 줄)]}"""
        found = {}
        for r, line in enumerate(self.rows):
            for c, ch in enumerate(line):
                if ch in DOOR_CHARS:
                    found.setdefault(ch, []).append((c, r))
        return found

    def entry_cell(self, side, cells):
        """그 문으로 들어온 플레이어가 처음 서는 칸 (없으면 None)."""
        cols = [c for c, _ in cells]
        rows = [r for _, r in cells]
        mid = (min(cols) + max(cols)) // 2
        if side == 'L':
            return (1, max(rows))
        if side == 'R':
            return (self.ncols - 2, max(rows))
        if side == 'U':                        # 천장 구멍으로 떨어져 첫 바닥에 선다
            for r in range(1, self.nrows):
                if self.standable(mid, r):
                    return (mid, r)
            return None
        # D: 바닥 구멍 옆 바닥으로 올라선다
        for c in (max(cols) + 2, min(cols) - 2):
            if 0 < c < self.ncols - 1 and self.standable(c, self.nrows - 3):
                return (c, self.nrows - 3)
        return None

    def exit_ok(self, side, cells, reach):
        """그 문으로 나갈 수 있는가: 문 앞까지 갈 수 있고(위 문은 머리가 천장 구멍에 닿는 높이까지)."""
        cols = [c for c, _ in cells]
        rows = [r for _, r in cells]
        if side == 'L':
            return (1, max(rows)) in reach
        if side == 'R':
            return (self.ncols - 2, max(rows)) in reach
        lo, hi = min(cols), max(cols)
        if side == 'U':
            for (c, r) in reach:
                if lo - 1 <= c <= hi + 1 and r <= 1 + self.limits['rise_double'] and all(
                        not self.solid(cc, rr) for cc in range(lo, hi + 1) for rr in range(1, r)):
                    return True
            return False
        return any(lo - 2 <= c <= hi + 2 and r >= self.nrows - 4 for (c, r) in reach)   # D: 구멍 근처 바닥에 설 수 있다


def spawn_cells(rows):
    """방 텍스트의 적·보스 스폰 칸 [(열, 줄, 표시문자)]."""
    return [(c, r, ch) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch in 'EstB']


def analyze(rows, safe_distance=7, need_doors=True):
    """방 하나를 검사해 문제 목록을 돌려준다. 빈 목록이면 통과."""
    problems = []
    g = RoomGraph(rows)
    if len({len(r) for r in rows}) != 1:
        return ['줄 길이가 서로 다르다']
    doors = g.doors()
    if need_doors and not doors:
        return ['출입구가 하나도 없다']
    entries = {}
    for side, cells in doors.items():
        if side in 'LR' and len(cells) < 2:
            problems.append(f'{side} 출입구는 2칸 이상(권장 3칸)이어야 몸이 지나간다')
        if side in 'UD' and len(cells) < 3:
            problems.append(f'{side} 출입구는 3칸 이상이어야 한다')
        cell = g.entry_cell(side, cells)
        if cell is None or not g.standable(*cell):
            problems.append(f'{side} 출입구로 들어온 플레이어가 설 수 있는 칸이 없다')
        else:
            entries[side] = cell
    if problems:
        return problems
    reach = {side: g.reachable(cell) for side, cell in entries.items()}
    for a in entries:
        for b, cells in doors.items():
            if a == b:
                continue
            if not g.exit_ok(b, cells, reach[a]):
                problems.append(f'{a} 문으로 들어와서 {b} 문으로 나갈 수 없다')
    for col, row, ch in spawn_cells(rows):
        if not g.standable(col, row):
            problems.append(f'스폰 {ch}({col},{row})이 서 있을 수 없는 칸이다')
            continue
        for side, cell in entries.items():
            if (col, row) not in reach[side]:
                problems.append(f'스폰 {ch}({col},{row})에 {side} 문으로 들어온 플레이어가 갈 수 없다')
            if ch != 'B' and math.hypot(col - cell[0], row - cell[1]) < safe_distance:
                problems.append(f'스폰 {ch}({col},{row})이 {side} 입구에서 {safe_distance}칸 안이다 (안전 시작)')
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == 'I' and not g.standable(c, r):
                problems.append(f'진열대 ({c},{r})가 서 있을 수 없는 칸이다')
            if ch == SPIKE:
                for cell in entries.values():
                    if math.hypot(c - cell[0], r - cell[1]) < 3:
                        problems.append(f'입구 근처({c},{r})에 가시가 있다')
    return list(dict.fromkeys(problems))
