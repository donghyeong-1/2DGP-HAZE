"""보스방 지형·헤이즈 농도 패턴 (2026-11-22 v5 계획 2-1, docs/plan_v5.md). 보스가 페이즈를 올리면 방을 쓴다.

- ScrapPillar (크래셔 2페이즈 '고철 기둥'): 바닥에 그림자 예고 -> 천장에서 떨어져 박힌다. 박힌 기둥은 방의 임시 벽 칸
  (room.extra_solids)이라 올라설 수 있고, PILLAR_LIFE 뒤 무너진다. 떨어질 때 밑에 있으면 맞고 옆으로 밀려난다.
- Valve (크래셔 2페이즈 '배기 펌프'): 방이 고농도(room.is_high_haze)가 되어 게이지가 계속 오른다. 밸브 앞에서 F를 누르면
  멈추고, 안 누르면 PUMP_TIME 뒤 저절로 멈춘다.
- HazeBands (아크 2·3페이즈 '농도 띠'): 짙은 띠(게이지 상승)와 맑은 띠(하강)가 방을 가로질러 천천히 움직인다.
- CrystalWall (아크 3페이즈 '결정 벽'): 솟아올라 길을 막는다(임시 벽). 대시로 부딪치면 깨지며 헤이즈를 흡수(게이지 상승).
그림은 Codex T43(assets/props/boss/, 11/22 적용): 고철 기둥 120x240(낙하·박힘·붕괴), 밸브 90x110(열림·피격·닫힘,
기준점 x=37), 결정 기둥 100x260(솟음·직립·파괴), 용광로 배기구 180x60(크래셔 증기 분출 자리). 농도 띠만 코드로 그린다.
"""


def _img(name, n):
    return assets.image(f'props/boss/{name}_{n}.png')
import assets
import config
import effects
import game_world

T = config.TILE
PILLAR_WARN, PILLAR_FALL, PILLAR_LIFE, PILLAR_CRUMBLE = 0.7, 0.25, 7.0, 0.4
PILLAR_ROWS = 4
PILLAR_DAMAGE = 16
PUMP_TIME = 10.0
VALVE_REACH = (90, 140)
BAND_W, BAND_SPEED, BAND_RATE, BANDS_LIFE = 240, 110.0, 6.0, 9.0
CRYSTAL_RISE, CRYSTAL_LIFE, CRYSTAL_ROWS, CRYSTAL_ABSORB = 0.35, 6.0, 3, 8


def _landing_row(room, cols):
    """천장에서 떨어진 것이 처음 닿는 바닥 바로 위 줄 (두 칸 모두 아래가 벽인 가장 위의 빈 줄)."""
    for r in range(1, room.nrows - 1):
        if all(room.tile_at(c, r) != '#' for c in cols) and any(room.tile_at(c, r + 1) == '#' for c in cols):
            return r
    return room.nrows - 3


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class _Solid:
    """방의 임시 벽 칸을 가진 지형 조각 (등록·해제)."""

    def _claim(self):
        for cell in self.cells:
            if self.room.tile_at(*cell) != '#':              # 빈 칸·얇은 발판·스폰 표시 칸 모두 덮는다
                self.room.extra_solids[cell] = self

    def _release(self):
        for cell in self.cells:
            if self.room.extra_solids.get(cell) is self:
                del self.room.extra_solids[cell]

    def rect(self):
        cs = [c for c, _r in self.cells]
        rs = [r for _c, r in self.cells]
        return (min(cs) * T, self.room.height - (max(rs) + 1) * T, (max(cs) + 1) * T, self.room.height - min(rs) * T)


class ScrapPillar(_Solid):
    def __init__(self, x, room, player):
        self.room, self.player = room, player
        c0 = max(1, min(room.cols - 3, room.col_of(x) - 1 if x % T < T / 2 else room.col_of(x)))
        self.cols = (c0, c0 + 1)
        base = _landing_row(room, self.cols)
        self.cells = [(c, r) for c in self.cols for r in range(base - PILLAR_ROWS + 1, base + 1)]
        self.x = (c0 + 1) * T
        self.floor_y = room.height - (base + 1) * T
        self.top_y = self.floor_y + PILLAR_ROWS * T
        self.time, self.state = 0.0, 'warn'

    def update(self, dt):
        self.time += dt
        if self.state == 'warn' and self.time >= PILLAR_WARN:
            self.state, self.time = 'fall', 0.0
        elif self.state == 'fall' and self.time >= PILLAR_FALL:
            self.state, self.time = 'stand', 0.0
            self._land()
        elif self.state == 'stand' and self.time >= PILLAR_LIFE:
            self.state, self.time = 'crumble', 0.0
        elif self.state == 'crumble' and self.time >= PILLAR_CRUMBLE:
            self._release()
            effects.spawn('puff', self.x, self.floor_y + 40, duration=0.4)
            game_world.remove_object(self)

    def _land(self):
        p = self.player
        box = self.rect()
        if p.state != 'DEAD' and _overlap(box, p.rect()):           # 밑에 있었다: 맞고 옆으로 밀려난다
            p.take_hit(PILLAR_DAMAGE, source=self)
            side = -1 if p.x < self.x else 1
            p.x = (box[0] - config.PLAYER_HB_W / 2 - 2) if side < 0 else (box[2] + config.PLAYER_HB_W / 2 + 2)
        self._claim()
        effects.add_trauma(0.5)
        effects.spawn('quake-blast', self.x, self.floor_y, duration=0.35)
        assets.play_sound('overload')

    def draw(self):
        x0 = int(self.x - T)
        if self.state == 'warn':                                     # 바닥에 깜빡이는 그림자
            if int(self.time * 10) % 2 == 0:
                assets.draw_rect_color(x0, int(self.floor_y), 2 * T, 8, (255, 120, 60))
            return
        if self.state == 'fall':
            k = self.time / PILLAR_FALL
            bottom = int(self.floor_y + (1 - k) * 700)
        else:
            bottom = int(self.floor_y)
        n = {'fall': 1, 'stand': 2, 'crumble': 3}[self.state]
        assets.draw_image(_img('scrap_pillar', n), int(self.x), bottom)              # 두 칸 x 네 칸 (Codex T43)


class Valve:
    def __init__(self, room, player, x):
        self.room, self.player = room, player
        col = room.col_of(x)
        base = _landing_row(room, (col,))
        self.x = (col + 0.5) * T
        self.y_floor = room.height - (base + 1) * T
        self.base_high = getattr(room, 'base_high_haze', room.is_high_haze)
        room.base_high_haze = self.base_high
        room.is_high_haze = True
        self.left = PUMP_TIME
        self.time = 0.0

    def near(self):
        p = self.player
        return abs(p.x - self.x) <= VALVE_REACH[0] and abs(p.y - self.y_floor) <= VALVE_REACH[1]

    def update(self, dt):
        self.time += dt
        self.left -= dt
        p = self.player
        closed = p.interact_pressed and self.near()
        if closed:
            p.interact_pressed = False
            effects.float_text(self.x, self.y_floor + 170, '배기 정지', (150, 230, 255))
            assets.play_sound('chain_latch_heavy')
        if closed or self.left <= 0:
            self.room.is_high_haze = self.base_high
            game_world.remove_object(self)

    def draw(self):
        x, y = int(self.x), int(self.y_floor)
        n = 1 if int(self.time * 5) % 4 else 2                                          # 증기가 새다 가끔 덜컹 (Codex T43)
        assets.draw_image(_img('steam_valve', n), x + 8, y)                            # 기준점 x=37 (캔버스 가운데 45)
        if self.near():
            assets.draw_text(x, y + 160, 'F 밸브 잠그기', (255, 230, 140), center=True, small=True)


class HazeBands:
    def __init__(self, room, player, start_x=None, life=BANDS_LIFE):
        self.room, self.player = room, player
        self.origin = (start_x if start_x is not None else player.x) - BAND_W / 2
        self.direction = 1 if player.x < room.width / 2 else -1
        self.left, self.time = life, 0.0

    def band_at(self, x):
        return 'dense' if ((x - self.origin) % (2 * BAND_W)) < BAND_W else 'clear'

    def update(self, dt):
        p = self.player
        if p.state != 'DEAD':
            p.gauge.add(BAND_RATE * dt if self.band_at(p.x) == 'dense' else -BAND_RATE * dt, 'band')
        self.origin += self.direction * BAND_SPEED * dt
        self.time += dt
        self.left -= dt
        if self.left <= 0:
            game_world.remove_object(self)

    def draw(self):
        k = min(1.0, self.time / 0.4, self.left / 0.4)
        start = self.origin - ((self.origin // (2 * BAND_W)) + 1) * 2 * BAND_W
        x = start
        while x < self.room.width + 2 * BAND_W:
            assets.draw_rect_color(int(x), 0, BAND_W, self.room.height, (60, 220, 200), 0.16 * k)      # 짙은 띠
            assets.draw_rect_color(int(x + BAND_W), 0, BAND_W, self.room.height, (230, 240, 255), 0.06 * k)  # 맑은 띠
            x += 2 * BAND_W


class CrystalWall(_Solid):
    def __init__(self, x, room, player):
        self.room, self.player = room, player
        col = max(1, min(room.cols - 2, room.col_of(x)))
        base = _landing_row(room, (col,))
        self.cells = [(col, r) for r in range(base - CRYSTAL_ROWS + 1, base + 1)]
        self.x = (col + 0.5) * T
        self.floor_y = room.height - (base + 1) * T
        self.time, self.state = 0.0, 'rise'

    def update(self, dt):
        self.time += dt
        p = self.player
        if self.state == 'rise' and self.time >= CRYSTAL_RISE:
            self.state, self.time = 'stand', 0.0
            self._claim()
            effects.spawn('hit-enhanced', self.x, self.floor_y + 90, duration=0.3)
        elif self.state == 'stand':
            x0, y0, x1, y1 = self.rect()
            touching = _overlap((x0 - 24, y0, x1 + 24, y1), p.rect())
            if (p.state == 'DASH' and touching) or self.time >= CRYSTAL_LIFE:
                if p.state == 'DASH' and touching:                              # 대시로 깼다: 헤이즈를 흡수
                    p.gauge.add(CRYSTAL_ABSORB, 'absorb')
                    effects.float_text(self.x, self.floor_y + 220, f'+{CRYSTAL_ABSORB}%', (130, 235, 225))
                self._release()
                effects.spawn('hit-enhanced', self.x, self.floor_y + 90, duration=0.35)
                assets.play_sound('chain_clash')
                game_world.add_object(_Shatter(self.x, self.floor_y), game_world.LAYER_EFFECT)
                game_world.remove_object(self)

    def draw(self):
        n = 2 if self.state == 'stand' else 1                                          # 솟음 -> 직립 (Codex T43)
        assets.draw_image(_img('crystal_pillar', n), int(self.x), int(self.floor_y))


class _Shatter:
    """깨진 결정 기둥 (판정 없음): 파괴 그림을 잠깐 보여 준다."""
    TIME = 0.3

    def __init__(self, x, floor_y):
        self.x, self.floor_y, self.time = x, floor_y, 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.TIME:
            game_world.remove_object(self)

    def draw(self):
        assets.draw_image(_img('crystal_pillar', 3), int(self.x), int(self.floor_y))
