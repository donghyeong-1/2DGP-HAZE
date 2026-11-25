"""구역별 장치 (v8 계획 5-5, 2026-11-25): 구역마다 한 가지, 전투방에 놓인다.

- 슬럼(stage1) 상자: 공격하거나 대시로 지나가면 부서지고 조각이 나온다. 부서진 것은 다시 들어와도 그대로다.
- 공장(stage2) 증기 분출구: 쉼 -> 예고(틈이 달아오르고 작은 김) -> 분출. 분출에 닿으면 주인공은 다치고,
  적은 떠오른다(띄우기와 같다: 공중 연타로 이어진다).
- 탑(stage3) 감시 레이저: 천장에 매달린 머리에서 내려온 빛줄기가 좌우로 천천히 오간다. 닿으면 다치고 게이지가 오른다.

자리는 판의 시드로 방의 바닥 칸에서 고른다(문과 적 자리에서 떨어진 평평한 곳). 방 템플릿은 건드리지 않는다.
움직이는 발판·부서지는 발판(계획 5-5)은 타일 충돌을 바꿔야 해서 넣지 않았다(docs/changes_from_plan.md).
"""
import math
import random

import assets
import config
import effects
import game_world

ZONE = {'stage1': 'crate', 'stage2': 'vent', 'stage3': 'laser'}
OPEN = set('.EsthgPIB')          # 지나다닐 수 있는 칸 (빈 칸과 표식 칸)
DOOR_MARGIN = 6                  # 문에서 이만큼(칸) 안에는 놓지 않는다
SPREAD = 4                       # 장치끼리 떨어지는 거리(칸)


def floor_cells(room):
    """장치를 놓을 수 있는 바닥 칸 [(열, 줄)]: 아래가 벽이고 위로 세 칸이 비었으며, 양옆 칸도 같은 높이의 바닥인 곳."""
    out = []
    for row in range(3, room.nrows - 1):
        for col in range(DOOR_MARGIN, room.cols - DOOR_MARGIN):
            if room.tile_at(col, row + 1) != '#':
                continue
            if any(room.tile_at(col, row - k) not in OPEN for k in range(3)):
                continue
            if any(room.tile_at(col + d, row + 1) != '#' or room.tile_at(col + d, row) not in OPEN for d in (-1, 1)):
                continue
            out.append((col, row))
    return out


def cell_pos(room, col, row):
    """칸의 가운데 x와 바닥 윗면 y."""
    t = config.TILE
    return col * t + t / 2, room.height - (row + 1) * t


def place(stage):
    """지금 방에 이 구역의 장치를 놓는다 (전투방만, 판의 시드로). 놓은 장치 목록을 돌려준다."""
    kind = ZONE.get(stage.name)
    room = stage.room
    if kind is None or stage.type_of(stage.coord) != 'combat':
        return []
    rng = random.Random(f'{stage.seed}:{stage.coord}:device')
    if rng.random() >= config.DEVICE_ROOM_CHANCE:
        return []
    cells = floor_cells(room)
    spawn_cols = {int(x // config.TILE) for x, _y, _k in room.enemy_spawns}
    cells = [c for c in cells if all(abs(c[0] - s) > 1 for s in spawn_cols)]
    rng.shuffle(cells)
    want = rng.randint(*config.DEVICE_COUNT[kind])
    picks = []
    for c in cells:
        if all(abs(c[0] - q[0]) >= SPREAD or c[1] != q[1] for q in picks):
            picks.append(c)
        if len(picks) >= want:
            break
    saved = stage.state.setdefault(stage.coord, {}).setdefault('broken', set())
    out = []
    for i, (col, row) in enumerate(picks):
        x, y = cell_pos(room, col, row)
        if kind == 'crate':
            d = Crate(x, y, stage.player, saved, i, rng.randint(*config.CRATE_SHARDS))
        elif kind == 'vent':
            d = Vent(x, y, stage.player, rng.uniform(0, config.VENT_IDLE))
        else:
            d = Laser(x, y, stage.player, room, col, row, rng.uniform(0, math.tau))
        out.append(d)
        game_world.add_object(d, game_world.LAYER_TILES)
    return out


class Crate:
    """슬럼의 상자. 공격이 나간 순간 닿는 거리에 있거나, 대시로 지나가면 부서진다."""
    kind = 'crate'

    def __init__(self, x, y, player, broken, key, shards):
        self.x, self.y, self.player = x, y, player
        self.broken, self.key, self.shards = broken, key, shards
        self._ready = True

    @property
    def gone(self):
        return self.key in self.broken

    def update(self, dt):
        p = self.player
        if self.gone or p is None:
            return
        ready = bool(getattr(p.weapon, 'ready', True))
        struck, self._ready = self._ready and not ready, ready           # 이번 프레임에 공격이 나갔다
        dx, dy = self.x - p.x, (self.y + 30) - p.center[1]
        ranged = type(p.weapon).__name__ == 'Pistols'
        reach = config.CRATE_REACH_FAR if ranged else config.CRATE_REACH
        aim = p.aim_vector()[0] if hasattr(p, 'aim_vector') else 1
        if struck and abs(dx) <= reach and abs(dy) <= 120 and (dx * aim >= 0 or abs(dx) < 50):
            self.smash()
        elif getattr(p, 'dash_left', 0) > 0 and abs(dx) < 56 and abs(dy) < 90:
            self.smash()

    def smash(self):
        if self.gone:
            return
        self.broken.add(self.key)
        p = self.player
        p.shards += self.shards
        effects.spawn('puff', self.x, self.y + 30, duration=0.34)
        effects.spawn('dust-land', self.x, self.y, duration=0.28)
        effects.float_text(self.x, self.y + 80, f'조각 +{self.shards}', (130, 235, 225))
        effects.add_kick(0, 1, 4)
        assets.play_sound('hit_armor')

    def draw(self):
        assets.draw_image(assets.image('ui/device_crate_broken.png' if self.gone else 'ui/device_crate.png'), self.x, self.y)


class Vent:
    """공장의 증기 분출구. idle -> warn -> jet 을 되풀이한다."""
    kind = 'vent'

    def __init__(self, x, y, player, offset=0.0):
        self.x, self.y, self.player = x, y, player
        self.phase, self.left = 'idle', config.VENT_IDLE - offset
        self.tick = 0.0
        self.hit = set()                 # 이번 분출에 이미 맞은 것 (한 번만)
        self.puffs = 0                   # 띄운 김 시트 수: 시트의 세 줄(시드가 다른 변형)을 차례로 쓴다

    def column(self, x, y):
        """(x, y)가 분출 기둥 안인가."""
        return abs(x - self.x) <= config.VENT_HALF_WIDTH and self.y - 10 <= y <= self.y + config.VENT_HEIGHT

    def update(self, dt):
        self.left -= dt
        self.tick -= dt
        if self.left <= 0:
            self.phase = {'idle': 'warn', 'warn': 'jet', 'jet': 'idle'}[self.phase]
            self.left = {'idle': config.VENT_IDLE, 'warn': config.VENT_WARN, 'jet': config.VENT_JET}[self.phase]
            self.tick = 0.0
            self.hit = set()
            if self.phase == 'jet':
                assets.play_sound('drone_torch')
        if self.phase == 'warn' and self.tick <= 0:
            self.tick = 0.16
            effects.spawn('dust-land', self.x, self.y + 4, duration=0.22)
        if self.phase != 'jet':
            return
        if self.tick <= 0:                                   # 분출 기둥을 이어 붙인다
            self.tick = 0.2
            effects.spawn('steam-jet', self.x, self.y + 6, duration=0.46, variant=self.puffs % 3)
            self.puffs += 1
        p = self.player
        if p is not None and 'player' not in self.hit and self.column(p.x, p.y) and p.invuln_left <= 0:
            self.hit.add('player')
            p.take_hit(config.VENT_DAMAGE, 0, source=self)
        import combo
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            if e.alive and id(e) not in self.hit and self.column(e.x, e.y):
                self.hit.add(id(e))
                combo.launch(e, config.VENT_LAUNCH)          # 적은 떠오른다 (보스는 뜨지 않는다)

    def draw(self):
        hot = self.phase != 'idle'
        assets.draw_image(assets.image('ui/device_vent_hot.png' if hot else 'ui/device_vent.png'), self.x, self.y - 4)


class Laser:
    """탑의 감시 레이저. 천장의 머리가 좌우로 오가며 아래로 빛줄기를 쏜다. 닿으면 다치고 게이지가 오른다."""
    kind = 'laser'

    def __init__(self, x, y, player, room, col, row, phase=0.0):
        self.player, self.room = player, room
        t = config.TILE
        top = row                                            # 천장(벽)까지 올라간다. 통과 발판은 빛이 지나간다
        while top > 1 and room.tile_at(col, top - 1) != '#':
            top -= 1
        self.top_row, self.row = top, row
        left = right = col                                   # 같은 바닥·같은 천장이 이어지는 만큼 오간다 (최대 LASER_SPAN칸씩)
        while col - left < config.LASER_SPAN and self._open(left - 1):
            left -= 1
        while right - col < config.LASER_SPAN and self._open(right + 1):
            right += 1
        self.x0, self.x1 = left * t + t / 2, right * t + t / 2
        self.floor = y
        self.top = room.height - top * t                     # 천장 아랫면 (머리가 매달리는 곳)
        self.glow = 0.0
        self.time = phase / config.LASER_SPEED
        self.x = self._x()
        self.y = self.floor
        self.cool = 0.0

    def _open(self, col):
        """이 열로도 오갈 수 있는가: 바닥과 천장 높이가 같고 그 사이에 벽이 없다."""
        room = self.room
        return (room.tile_at(col, self.row + 1) == '#' and room.tile_at(col, self.top_row - 1) == '#'
                and all(room.tile_at(col, r) != '#' for r in range(self.top_row, self.row + 1)))

    def _x(self):
        k = (math.sin(self.time * config.LASER_SPEED) + 1) / 2
        return self.x0 + (self.x1 - self.x0) * k

    def touches(self, x, y):
        return abs(x - self.x) <= config.LASER_HALF_WIDTH and self.floor - 10 <= y <= self.top

    def update(self, dt):
        self.time += dt
        self.cool = max(0.0, self.cool - dt)
        self.x = self._x()
        self.glow -= dt
        if self.glow <= 0:                                   # 바닥에 닿은 자리와 머리의 붉은 빛
            self.glow = 0.12
            effects.spawn_bloom(self.x, self.floor + 6, (255, 90, 90), big=False, life=0.2, strength=0.7)
            effects.spawn_bloom(self.x, self.top - 26, (255, 90, 90), big=False, life=0.2, strength=0.5)
        p = self.player
        if p is not None and self.cool <= 0 and p.invuln_left <= 0 and self.touches(p.x, p.center[1]):
            self.cool = config.LASER_COOL
            p.take_hit(config.LASER_DAMAGE, config.LASER_GAUGE, source=self)
            effects.spawn_bloom(p.x, p.center[1], (255, 110, 110), big=True, life=0.2, strength=1.0)
            assets.play_sound('overload_zap')

    def draw(self):
        head = assets.image('ui/device_laser.png')
        x = int(self.x) // 2 * 2
        assets.draw_image(head, x, self.top - head.h)
        bottom, top = int(self.floor), int(self.top - head.h)
        flick = int(self.time * 30) % 4                      # 빛줄기: 붉은 바깥 8px + 밝은 붉은 4px + 흰 심 2px (심은 흐르듯 끊긴다)
        assets.draw_rect_color(x - 4, bottom, 8, top - bottom, (200, 44, 60), 0.35)
        assets.draw_rect_color(x - 2, bottom, 4, top - bottom, (255, 110, 110))
        for y in range(bottom + flick * 4, top, 16):
            assets.draw_rect_color(x - 1, y, 2, 12, (255, 236, 226))
        assets.draw_rect_color(x - 8, bottom, 16, 2, (255, 110, 110))     # 바닥에 닿은 자리
        assets.draw_rect_color(x - 4, bottom + 2, 8, 2, (255, 226, 214))
