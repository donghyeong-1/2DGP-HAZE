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


# 타일 세트(assets/tiles/tile_set_<테마>.png)의 칸 위치. 16열 x 5줄, 칸 60x60, 줄 0이 맨 위
ATLAS_H = 300
ATLAS_ONEWAY, ATLAS_SPIKE, ATLAS_BACK, ATLAS_DECOR = 0, 4, 6, 0     # 줄 3: 얇은 바닥 0~3, 가시 4~5, 뒷벽 6~9 / 줄 4: 소품
DECOR_CHAIN_TOP, DECOR_CHAIN, DECOR_LAMP, DECOR_PIPE, DECOR_BANNER, DECOR_WINDOW, DECOR_CRATE, DECOR_BARREL, DECOR_VENT = range(9)
THEMES = ('cell', 'foundry', 'haze', 'gold', 'shop', 'boss')


def _hash(a, b=0, c=0):
    return ((a * 73856093) ^ (b * 19349663) ^ (c * 83492791)) & 0xFFFF


class Room:
    def __init__(self, rows, links=None, high_haze=False, theme='cell', name=''):
        assert rows and all(len(r) == len(rows[0]) for r in rows), '방은 직사각형이어야 한다'
        assert len(rows) >= 12 and len(rows[0]) >= 16, f'방이 너무 작다: {len(rows[0])}x{len(rows)}'
        self.rows = rows
        self.cols, self.nrows = len(rows[0]), len(rows)
        self.width, self.height = self.cols * config.TILE, self.nrows * config.TILE
        self.is_high_haze = high_haze
        self.theme = theme if theme in THEMES else 'cell'
        self.name = name
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
        self._build_look()

    # ----- 겉모습 계산 (방을 읽을 때 한 번) -----
    def _wallish(self, col, row):
        """자동 타일링에서 이웃이 벽처럼 이어지는가. 방 바깥과 출입구도 벽으로 본다."""
        if col < 0 or col >= self.cols or row < 0 or row >= self.nrows:
            return True
        ch = self.rows[row][col]
        return ch == SOLID or ch in DOOR_CHARS

    def _build_look(self):
        """벽 타일의 이웃 마스크, 뒷벽이 보일 칸, 장식 소품 위치를 정한다. 방 이름과 칸 좌표로만 정해지는 고정 배치다."""
        seed = sum(ord(c) for c in self.name) + self.cols
        self.masks = {}
        self.back = {}
        self.decor = []            # (소품 번호, 열, 줄)
        near_marker = set()        # 문·스폰·진열대 근처는 소품을 두지 않는다
        for row in range(self.nrows):
            for col in range(self.cols):
                ch = self.rows[row][col]
                if ch in DOOR_CHARS or ch in 'PEstIB':
                    for dc in range(-3, 4):
                        for dr in range(-3, 4):
                            near_marker.add((col + dc, row + dr))
        for row in range(self.nrows):
            for col in range(self.cols):
                ch = self.rows[row][col]
                if ch == SOLID or ch in DOOR_CHARS:
                    m = 0
                    if not self._wallish(col, row - 1):
                        m |= 1
                    if not self._wallish(col + 1, row):
                        m |= 2
                    if not self._wallish(col, row + 1):
                        m |= 4
                    if not self._wallish(col - 1, row):
                        m |= 8
                    self.masks[(col, row)] = m
                    continue
                near_wall = any(self._wallish(col + dc, row + dr) for dc in range(-2, 3) for dr in range(-2, 3))
                if near_wall:                                    # 벽 가까이에만 뒷벽을 깐다 (나머지는 먼 배경이 보인다)
                    pick = _hash(col, row, seed) % 20                # 판넬 55%, 리벳 25%, 파이프 10%, 환기구 10%
                    self.back[(col, row)] = 0 if pick < 11 else 2 if pick < 16 else 1 if pick < 18 else 3
        for row in range(1, self.nrows - 2):
            for col in range(1, self.cols - 1):
                if (col, row) in near_marker or self.rows[row][col] != EMPTY:
                    continue
                h = _hash(col, row, seed) % 100
                above, below = self._wallish(col, row - 1), self._wallish(col, row + 1) or self.rows[row + 1][col] == ONEWAY
                if above and self.rows[row - 1][col] == SOLID:
                    if h < 7:
                        self.decor.append((DECOR_CHAIN_TOP, col, row))
                        k = 1
                        while k < 3 and row + k < self.nrows - 3 and self.rows[row + k][col] == EMPTY and _hash(col, row, k) % 3:
                            self.decor.append((DECOR_CHAIN, col, row + k))
                            k += 1
                    elif h < 11:
                        self.decor.append((DECOR_LAMP, col, row))
                    elif h < 15:
                        self.decor.append((DECOR_BANNER, col, row))
                    elif row == 1 and h < 55:
                        self.decor.append((DECOR_PIPE, col, row))
                elif below and self.rows[row + 1][col] == SOLID and not above:
                    if h < 5:
                        self.decor.append((DECOR_CRATE, col, row))
                    elif h < 9:
                        self.decor.append((DECOR_BARREL, col, row))
                    elif h < (16 if self.theme == 'haze' else 11):
                        self.decor.append((DECOR_VENT, col, row))
                elif (col, row) in self.back and h < 3 and 3 <= row < self.nrows - 5:
                    self.decor.append((DECOR_WINDOW, col, row))

    @classmethod
    def load(cls, name, links=None, high_haze=False, theme='cell'):
        path = os.path.join(assets.DATA_DIR, 'rooms', name + '.txt')
        with open(path, encoding='utf-8') as f:
            rows = [line.rstrip('\r') for line in f.read().split('\n') if line.strip('\r') != '']
        return cls(rows, links, high_haze, theme, name)

    def spike_rects(self):
        """가시 타일마다 실제로 찌르는 사각형 (left, bottom, right, top). 타일 아래쪽 SPIKE_HEIGHT만 위험하다."""
        rects = []
        for row, line in enumerate(self.rows):
            for col, ch in enumerate(line):
                if ch == SPIKE:
                    bottom = self.height - (row + 1) * config.TILE
                    rects.append((col * config.TILE, bottom, (col + 1) * config.TILE, bottom + config.SPIKE_HEIGHT))
        return rects

    def line_blocked(self, x0, y0, x1, y1, step=18):
        """두 점 사이의 직선이 단단한 벽(#, 잠긴 문)에 막히는가. 근접 공격이 벽을 뚫고 맞지 않게 하는 시야 검사."""
        dist = max(abs(x1 - x0), abs(y1 - y0))
        n = max(1, int(dist // step))
        for i in range(1, n):
            t = i / n
            if self.tile_at_world(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) == SOLID:
                return True
        return False

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

    def _cell(self, atlas, acol, arow, col, bottom, tint=None):
        """타일 세트에서 한 칸을 잘라 (col, 아래 모서리 bottom)에 그린다."""
        t = config.TILE
        if tint:
            from sdl2 import SDL_SetTextureColorMod
            SDL_SetTextureColorMod(atlas.texture, *tint)
        assets.draw_clip(atlas, acol * t, ATLAS_H - (arow + 1) * t, t, t, col * t, bottom)
        if tint:
            SDL_SetTextureColorMod(atlas.texture, 255, 255, 255)

    def _wall(self, atlas, col, row, bottom, tint=None):
        variant = _hash(col, row, 5) % 3
        self._cell(atlas, self.masks.get((col, row), 0), variant, col, bottom, tint)

    def draw(self):
        screen_offset = assets.draw_offset
        assets.draw_offset = (0, 0)  # 배경은 화면에 고정 (카메라를 따라 움직이지 않는다)
        assets.draw_image(assets.image(f'backgrounds/bg_{self.theme}.png'), config.SCREEN_W // 2, 0)
        assets.draw_offset = screen_offset
        atlas = assets.image(f'tiles/tile_set_{self.theme}.png')
        t = config.TILE
        # 화면에 보이는 칸만 그린다
        c0 = max(0, int(camera.x // t) - 1)
        c1 = min(self.cols - 1, int((camera.x + config.SCREEN_W) // t) + 1)
        r0 = max(0, self.row_of(camera.y + config.SCREEN_H) - 1)
        r1 = min(self.nrows - 1, self.row_of(camera.y) + 1)
        # 1) 뒷벽과 뒤쪽 소품
        for row in range(r0, r1 + 1):
            bottom = self.height - (row + 1) * t
            for col in range(c0, c1 + 1):
                kind = self.back.get((col, row))
                if kind is not None:
                    self._cell(atlas, ATLAS_BACK + kind, 3, col, bottom)
        for kind, col, row in self.decor:
            if c0 <= col <= c1 and r0 <= row <= r1:
                self._cell(atlas, ATLAS_DECOR + kind, 4, col, self.height - (row + 1) * t)
        # 2) 벽·바닥·가시
        for row in range(r0, r1 + 1):
            line = self.rows[row]
            bottom = self.height - (row + 1) * t
            for col in range(c0, c1 + 1):
                ch = line[col]
                if ch in DOOR_CHARS:
                    self._draw_door(ch, col, row, col * t + t // 2, bottom, atlas)
                elif ch == SOLID:
                    self._wall(atlas, col, row, bottom)
                elif ch == ONEWAY:                                   # 얇은 바닥: 이웃 얇은 바닥에 따라 끝 모양이 달라진다
                    left = col > 0 and line[col - 1] == ONEWAY
                    right = col < self.cols - 1 and line[col + 1] == ONEWAY
                    kind = 2 if left and right else 3 if left else 1 if right else 0
                    self._cell(atlas, ATLAS_ONEWAY + kind, 3, col, bottom)
                elif ch == SPIKE:
                    self._cell(atlas, ATLAS_SPIKE + _hash(col, row) % 2, 3, col, bottom)
        if self.is_high_haze:
            haze = assets.image('placeholder/px_cyan.png')  # 고농도 방: 화면 전체에 옅은 청록빛 안개
            haze.opacify(0.10)
            screen_offset = assets.draw_offset
            assets.draw_offset = (0, 0)
            assets.draw_rect_image(haze, 0, 0, config.SCREEN_W, config.SCREEN_H)
            assets.draw_offset = screen_offset
            haze.opacify(1.0)

    def _draw_door(self, ch, col, row, cx, bottom, atlas):
        """출입구 그리기. 이어진 방이 없으면 벽, 잠겼으면 붉은 문, 열렸으면 문 너머 방 종류 색의 빛이 새어 들어온다."""
        if ch not in self.links:
            self._wall(atlas, col, row, bottom)
            return
        if self.locked:
            self._wall(atlas, col, row, bottom, tint=(255, 110, 120))
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
