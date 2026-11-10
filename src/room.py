"""방(Room): 텍스트 타일 맵 로드, 충돌용 타일 조회, 그리기.

타일 문자: # 벽·바닥 / = 얇은 바닥 / ^ 가시 / P 시작 위치 / E 적 스폰 / L R U D 출입구 / S 진열대 / . 빈 칸
"""
import os

import assets
import config
import game_world

SOLID = '#'
ONEWAY = '='
SPIKE = '^'
EMPTY = '.'


class Room:
    def __init__(self, rows):
        assert len(rows) == config.ROOM_ROWS, f'방은 {config.ROOM_ROWS}줄이어야 한다: {len(rows)}'
        for r in rows:
            assert len(r) == config.ROOM_COLS, f'방은 {config.ROOM_COLS}글자여야 한다: {len(r)}'
        self.rows = rows
        self.is_high_haze = False
        self.spawn = (config.SCREEN_W / 2, config.TILE)
        self.enemy_spawns = []
        self.exits = {}
        for row, line in enumerate(rows):
            for col, ch in enumerate(line):
                x = col * config.TILE + config.TILE / 2
                y = config.SCREEN_H - (row + 1) * config.TILE  # 타일 아래 모서리(발 위치)
                if ch == 'P':
                    self.spawn = (x, y)
                elif ch == 'E':
                    self.enemy_spawns.append((x, y))
                elif ch in 'LRUD':
                    self.exits.setdefault(ch, []).append((col, row))

    @classmethod
    def load(cls, name):
        path = os.path.join(assets.DATA_DIR, 'rooms', name + '.txt')
        with open(path, encoding='utf-8') as f:
            rows = [line.rstrip('\r') for line in f.read().split('\n')][:config.ROOM_ROWS]
        return cls(rows)

    # ----- 충돌용 조회 -----
    def tile_at(self, col, row):
        """격자 좌표의 타일 문자. 좌우·아래 바깥은 벽, 위쪽 바깥은 빈 칸으로 본다."""
        if row < 0:
            return EMPTY
        if col < 0 or col >= config.ROOM_COLS or row >= config.ROOM_ROWS:
            return SOLID
        return self.rows[row][col]

    @staticmethod
    def col_of(x):
        return int(x // config.TILE)

    @staticmethod
    def row_of(y):
        """세계 좌표 y(위로 증가)가 속한 줄 번호(맨 윗줄이 0)."""
        return int((config.SCREEN_H - y) // config.TILE)

    @staticmethod
    def tile_top(row):
        return config.SCREEN_H - row * config.TILE

    @staticmethod
    def tile_bottom(row):
        return config.SCREEN_H - (row + 1) * config.TILE

    def tile_at_world(self, x, y):
        return self.tile_at(self.col_of(x), self.row_of(y))

    # ----- 객체 인터페이스 -----
    def update(self, dt):
        pass

    def draw(self):
        assets.draw_image(assets.image('placeholder/bg.png'), config.SCREEN_W // 2, 0)
        solids = [assets.image(f'tiles/tile_solid_{v}.png') for v in 'abc']  # 벽은 3변형을 칸 위치로 골라 단조로움을 줄인다
        oneway = assets.image('tiles/tile_oneway.png')
        spike = assets.image('tiles/tile_spike.png')
        half = config.TILE // 2
        for row, line in enumerate(self.rows):
            bottom = config.SCREEN_H - (row + 1) * config.TILE
            for col, ch in enumerate(line):
                cx = col * config.TILE + half
                if ch == SOLID:
                    assets.draw_image(solids[(col * 7 + row * 13) % 3], cx, bottom)
                elif ch == ONEWAY:
                    assets.draw_image(oneway, cx, bottom)  # 이미지의 위쪽 10px만 판으로 칠해져 있다
                elif ch == SPIKE:
                    assets.draw_image(spike, cx, bottom)
