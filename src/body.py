"""타일 충돌을 받는 몸(플레이어·적 공통). 축을 나눠 x -> y 순서로 움직이고 겹친 타일에서 밀어낸다.

쓰는 쪽은 x, y(발 아래 중앙), vx, vy, on_ground, drop_timer, room, hb_w, hb_h 를 가져야 한다.
"""
import config
import room as room_module

EPS = 1.0  # 충돌 판정에서 모서리 접촉을 겹침으로 보지 않기 위한 여유(px)


class TileBody:
    hb_w = config.PLAYER_HB_W
    hb_h = config.PLAYER_HB_H
    drop_timer = 0.0
    stop_on_wall = True  # 벽에 부딪히면 vx를 0으로 만든다 (대시 중인 플레이어는 끈다)

    def move_with_tiles(self, dt):
        dx, dy = self.vx * dt, self.vy * dt
        self.x += dx
        if dx != 0:
            self._resolve_x(dx)
        prev_y = self.y
        self.y += dy
        self.on_ground = False
        if dy != 0:
            self._resolve_y(dy, prev_y)

    def _tile_range_x(self):
        hw = self.hb_w / 2
        return self.room.col_of(self.x - hw + EPS), self.room.col_of(self.x + hw - EPS)

    def _resolve_x(self, dx):
        hw = self.hb_w / 2
        r = self.room
        row_top = r.row_of(self.y + self.hb_h - EPS)
        row_bottom = r.row_of(self.y + EPS)
        for row in range(row_top, row_bottom + 1):
            for col in range(r.col_of(self.x - hw), r.col_of(self.x + hw) + 1):
                if r.tile_at(col, row) != room_module.SOLID:
                    continue
                if dx > 0:
                    self.x = min(self.x, col * config.TILE - hw)
                else:
                    self.x = max(self.x, (col + 1) * config.TILE + hw)
                if self.stop_on_wall:
                    self.vx = 0.0

    def _resolve_y(self, dy, prev_y):
        r = self.room
        col_a, col_b = self._tile_range_x()
        top = self.y + self.hb_h
        row_top = r.row_of(top)
        row_bottom = r.row_of(self.y)
        for row in range(row_top, row_bottom + 1):
            for col in range(col_a, col_b + 1):
                ch = r.tile_at(col, row)
                if ch == room_module.SOLID:
                    if dy < 0 and r.tile_top(row) <= prev_y + EPS:
                        self.y = max(self.y, r.tile_top(row))
                        self.vy = 0.0
                        self.on_ground = True
                    elif dy > 0 and r.tile_bottom(row) >= prev_y + self.hb_h - EPS:
                        self.y = min(self.y, r.tile_bottom(row) - self.hb_h)
                        self.vy = 0.0
                elif ch == room_module.ONEWAY and dy < 0 and self.drop_timer <= 0:
                    tile_top = r.tile_top(row)
                    if prev_y >= tile_top - EPS and self.y < tile_top + EPS:
                        self.y = max(self.y, tile_top)
                        self.vy = 0.0
                        self.on_ground = True
