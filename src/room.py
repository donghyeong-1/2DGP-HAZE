"""방(Room): 텍스트 타일 맵 로드, 충돌용 타일 조회, 그리기. 방 크기는 파일마다 다르고 화면보다 커도 된다(카메라가 따라간다).

타일 문자: # 벽·바닥 / = 얇은 바닥 / ^ 가시 / P 시작 위치 / E·s·t 적 스폰(s 슬럼, t 투척병) /
           L R 좌우 출입구(벽 3칸) / U 위 출입구(맨 윗줄 3칸) / D 아래 출입구(바닥 두 줄 3칸 구멍) /
           I 아이템 진열대 / B 보스 스폰 / . 빈 칸
좌표: 원점은 방의 왼쪽 아래, y는 위로 증가. 맨 윗줄이 0줄이다 (줄 r의 아래 모서리 y = (줄 수 - r - 1) x TILE).
"""
import os

import assets
import camera
import config

SOLID = '#'
ONEWAY = '='
SPIKE = '^'
EMPTY = '.'
SPAWN_KINDS = {'s': 'slum', 't': 'thrower'}  # 방 텍스트의 적 스폰 표시
DOOR_CHARS = 'LRUD'
DOOR_TINT = {'gold': (255, 215, 90), 'boss': (255, 90, 100), 'shop': (120, 215, 255)}   # 문 너머 방 종류 표시 색
DOOR_LABEL = {'gold': '황금방', 'boss': '보스', 'shop': '정비방'}


class Room:
    def __init__(self, rows, links=None, high_haze=False):
        assert rows and all(len(r) == len(rows[0]) for r in rows), '방은 직사각형이어야 한다'
        assert len(rows) >= 12 and len(rows[0]) >= 16, f'방이 너무 작다: {len(rows[0])}x{len(rows)}'
        self.rows = rows
        self.cols, self.nrows = len(rows[0]), len(rows)
        self.width, self.height = self.cols * config.TILE, self.nrows * config.TILE
        self.is_high_haze = high_haze
        self.links = set(links or ())   # 이웃 방(또는 탈출구)이 있어서 열릴 수 있는 출입구 방향. 나머지 출입구는 벽이다
        self.locked = False             # 전투 중에는 출입구가 잠긴다
        self.door_hints = {}            # 방향 -> 문 너머 방 종류('gold', 'boss', 'shop'): 문 색과 이름으로 알려 준다
        self.spawn = (self.width / 2, config.TILE)
        self.enemy_spawns = []          # (x, y, 종류 또는 None)
        self.pedestals = []             # 진열대 칸 (x, y): 발 위치
        self.boss_spawn = None
        self.exits = {}                 # 방향 -> [(열, 줄)]
        for row, line in enumerate(rows):
            for col, ch in enumerate(line):
                x = col * config.TILE + config.TILE / 2
                y = self.height - (row + 1) * config.TILE  # 타일 아래 모서리(발 위치)
                if ch == 'P':
                    self.spawn = (x, y)
                elif ch == 'E':
                    self.enemy_spawns.append((x, y, None))          # 종류는 스테이지 데이터가 정한다
                elif ch in SPAWN_KINDS:
                    self.enemy_spawns.append((x, y, SPAWN_KINDS[ch]))  # 종류가 칸에 적혀 있다
                elif ch == 'I':
                    self.pedestals.append((x, y))
                elif ch == 'B':
                    self.boss_spawn = (x, y)
                elif ch in DOOR_CHARS:
                    self.exits.setdefault(ch, []).append((col, row))

    @classmethod
    def load(cls, name, links=None, high_haze=False):
        path = os.path.join(assets.DATA_DIR, 'rooms', name + '.txt')
        with open(path, encoding='utf-8') as f:
            rows = [line.rstrip('\r') for line in f.read().split('\n') if line.strip('\r') != '']
        return cls(rows, links, high_haze)

    def spike_rects(self):
        """가시 타일마다 실제로 찌르는 사각형 (left, bottom, right, top). 타일 아래쪽 SPIKE_HEIGHT만 위험하다."""
        rects = []
        for row, line in enumerate(self.rows):
            for col, ch in enumerate(line):
                if ch == SPIKE:
                    bottom = self.height - (row + 1) * config.TILE
                    rects.append((col * config.TILE, bottom, (col + 1) * config.TILE, bottom + config.SPIKE_HEIGHT))
        return rects

    def door_open(self, direction):
        return direction in self.links and not self.locked

    def door_center(self, direction):
        """출입구 칸들의 가운데 (x, 가장 아래 칸의 아래 모서리 y). 없으면 None."""
        cells = self.exits.get(direction)
        if not cells:
            return None
        cols = [c for c, _ in cells]
        rows = [r for _, r in cells]
        x = (min(cols) + max(cols) + 1) * config.TILE / 2
        y = self.height - (max(rows) + 1) * config.TILE
        return (x, y)

    # ----- 충돌용 조회 -----
    def tile_at(self, col, row):
        """격자 좌표의 타일 문자. 좌우 바깥은 벽, 위쪽 바깥은 빈 칸, 아래 바깥은 열린 아래 출입구 구멍만 빈 칸이다."""
        if row < 0:
            return EMPTY
        if col < 0 or col >= self.cols:
            return SOLID
        if row >= self.nrows:
            return EMPTY if self._hole_below(col) else SOLID
        ch = self.rows[row][col]
        if ch in DOOR_CHARS and not self.door_open(ch):
            return SOLID  # 잠겼거나 이어진 방이 없는 출입구는 벽
        return ch

    def _hole_below(self, col):
        return self.door_open('D') and any(c == col for c, _ in self.exits.get('D', []))

    @staticmethod
    def col_of(x):
        return int(x // config.TILE)

    def row_of(self, y):
        """세계 좌표 y(위로 증가)가 속한 줄 번호(맨 윗줄이 0)."""
        return int((self.height - y) // config.TILE)

    def tile_top(self, row):
        return self.height - row * config.TILE

    def tile_bottom(self, row):
        return self.height - (row + 1) * config.TILE

    def tile_at_world(self, x, y):
        return self.tile_at(self.col_of(x), self.row_of(y))

    # ----- 객체 인터페이스 -----
    def update(self, dt):
        pass

    def draw(self):
        screen_offset = assets.draw_offset
        assets.draw_offset = (0, 0)  # 배경은 화면에 고정 (카메라를 따라 움직이지 않는다)
        assets.draw_image(assets.image('placeholder/bg.png'), config.SCREEN_W // 2, 0)
        assets.draw_offset = screen_offset
        solids = [assets.image(f'tiles/tile_solid_{v}.png') for v in 'abc']  # 벽은 3변형을 칸 위치로 골라 단조로움을 줄인다
        oneway = assets.image('tiles/tile_oneway.png')
        spike = assets.image('tiles/tile_spike.png')
        half = config.TILE // 2
        # 화면에 보이는 칸만 그린다
        c0 = max(0, int(camera.x // config.TILE) - 1)
        c1 = min(self.cols - 1, int((camera.x + config.SCREEN_W) // config.TILE) + 1)
        r0 = max(0, self.row_of(camera.y + config.SCREEN_H) - 1)
        r1 = min(self.nrows - 1, self.row_of(camera.y) + 1)
        for row in range(r0, r1 + 1):
            line = self.rows[row]
            bottom = self.height - (row + 1) * config.TILE
            for col in range(c0, c1 + 1):
                ch = line[col]
                cx = col * config.TILE + half
                if ch in DOOR_CHARS:
                    self._draw_door(ch, col, row, cx, bottom, solids[(col * 7 + row * 13) % 3])
                elif ch == SOLID:
                    assets.draw_image(solids[(col * 7 + row * 13) % 3], cx, bottom)
                elif ch == ONEWAY:
                    assets.draw_image(oneway, cx, bottom)  # 이미지의 위쪽 10px만 판으로 칠해져 있다
                elif ch == SPIKE:
                    assets.draw_image(spike, cx, bottom)
        if self.is_high_haze:
            haze = assets.image('placeholder/px_cyan.png')  # 고농도 방: 화면 전체에 옅은 청록빛 안개
            haze.opacify(0.10)
            screen_offset = assets.draw_offset
            assets.draw_offset = (0, 0)
            assets.draw_rect_image(haze, 0, 0, config.SCREEN_W, config.SCREEN_H)
            assets.draw_offset = screen_offset
            haze.opacify(1.0)

    def _draw_door(self, ch, col, row, cx, bottom, wall_tile):
        """출입구 그리기. 이어진 방이 없으면 벽, 잠겼으면 붉은 문, 열렸으면 문 너머 방 종류 색의 빛이 새어 들어온다."""
        if ch not in self.links:
            assets.draw_image(wall_tile, cx, bottom)
            return
        if self.locked:
            assets.draw_image_tinted(wall_tile, cx, bottom, '', (255, 110, 120), 1.0)
            return
        hint = self.door_hints.get(ch)
        name = 'px_yellow' if hint == 'gold' else 'px_red' if hint == 'boss' else 'px_blue' if hint == 'shop' else 'px_cyan'
        edge = assets.image('placeholder/' + name + '.png')
        edge.opacify(0.7 if hint else 0.5)
        t = config.TILE
        if ch == 'L':
            assets.draw_rect_image(edge, col * t, bottom, 10, t)
        elif ch == 'R':
            assets.draw_rect_image(edge, (col + 1) * t - 10, bottom, 10, t)
        elif ch == 'U':
            assets.draw_rect_image(edge, col * t, bottom + t - 10, t, 10)
        else:
            assets.draw_rect_image(edge, col * t, bottom + t - 10 if row == self.nrows - 2 else bottom, t, 10)
        edge.opacify(1.0)
        cells = self.exits.get(ch, [])
        if hint in DOOR_LABEL and cells and (col, row) == cells[len(cells) // 2]:
            tint = DOOR_TINT[hint]
            dx = 70 if ch == 'L' else -70 if ch == 'R' else 0
            dy = 0 if ch in 'LR' else (-50 if ch == 'U' else 70)
            assets.draw_text(cx + dx, bottom + t // 2 + dy, DOOR_LABEL[hint], tint, small=True, center=True)
