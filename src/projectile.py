"""투사체. 지금은 고철 투척병이 던지는 고철 조각 하나뿐이다.

실행 중 회전하지 않으므로(docs/pixel_rules.md 규칙 5) 가로로만 날고, 왼쪽은 좌우 반전으로 그린다.
"""
import assets
import config
import effects
import game_world
import room as room_module


def overlap(a, b):
    """두 사각형 (left, bottom, right, top)이 겹치는가."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class Scrap:
    def __init__(self, x, y, direction, speed, damage, room, player):
        self.x, self.y = x, y            # 투사체 중심
        self.dir = direction
        self.speed = speed
        self.damage = damage
        self.room = room
        self.player = player

    def rect(self):
        w, h = config.PROJECTILE_HB
        return (self.x - w / 2, self.y - h / 2, self.x + w / 2, self.y + h / 2)

    def update(self, dt):
        self.x += self.dir * self.speed * dt
        if self.room.tile_at_world(self.x, self.y) == room_module.SOLID or not (0 <= self.x <= self.room.width):
            game_world.remove_object(self)
            return
        p = self.player
        # 대시 무적 중에는 그대로 통과한다 (맞지 않고 사라지지도 않는다)
        if p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect()):
            p.take_hit(self.damage)
            game_world.remove_object(self)

    def draw(self):
        img = assets.image('sprites/unified/proj_scrap.png')
        assets.draw_image(img, self.x, self.y - img.h / 2, 'h' if self.dir < 0 else '')


class Shockwave:
    """보스의 바닥 충격파. 바닥을 따라 퍼져 가고 점프나 대시로 피한다. 맞으면 게이지가 크게 내려간다(기획 3.2)."""

    def __init__(self, x, y, direction, speed, damage, gauge_delta, room, player, life=1.5):
        self.x, self.y = x, y              # y는 바닥 윗면
        self.dir = direction
        self.speed = speed
        self.damage = damage
        self.gauge_delta = gauge_delta
        self.room = room
        self.player = player
        self.life = life
        self.time = 0.0

    def rect(self):
        return (self.x - 36, self.y, self.x + 36, self.y + 56)

    def update(self, dt):
        self.x += self.dir * self.speed * dt
        self.life -= dt
        self.time += dt
        if self.life <= 0 or self.room.tile_at_world(self.x + self.dir * 36, self.y + 20) == room_module.SOLID:
            game_world.remove_object(self)
            return
        p = self.player
        if p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect()):
            p.take_hit(self.damage, gauge_delta=self.gauge_delta)
            game_world.remove_object(self)

    def draw(self):
        effects.draw_loop('shockwave', self.x, self.y, self.time, flip=self.dir < 0)   # 바닥을 달리는 불기둥 물결


LOB_TIME = 0.85          # 포물선 고철이 플레이어 자리에 닿기까지 걸리는 시간(초)
LOB_GRAVITY = 1800.0     # 포물선 고철에 걸리는 중력(px/s^2). 게임 중력보다 약해 높이 떠서 날아간다


class Lob:
    """고철 투척병이 높이 던지는 고철. 포물선으로 날아가 낮은 엄폐물을 넘어온다. 바닥이나 벽에 닿으면 사라진다."""

    def __init__(self, x, y, vx, vy, damage, room, player):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.room = room
        self.player = player
        self.life = 3.0

    def rect(self):
        w, h = config.PROJECTILE_HB
        return (self.x - w / 2, self.y - h / 2, self.x + w / 2, self.y + h / 2)

    def update(self, dt):
        self.vy -= LOB_GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if (self.life <= 0 or self.room.tile_at_world(self.x, self.y) == room_module.SOLID
                or not (0 <= self.x <= self.room.width) or self.y < 0):
            effects.spawn('puff', self.x, self.y, duration=0.3)
            game_world.remove_object(self)
            return
        p = self.player
        if p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect()):
            p.take_hit(self.damage)
            game_world.remove_object(self)

    def draw(self):
        img = assets.image('sprites/unified/proj_scrap.png')
        assets.draw_image(img, self.x, self.y - img.h / 2, 'h' if self.vx < 0 else '')


def floor_below(room, x, y):
    """(x, y)에서 아래로 내려가며 처음 만나는 바닥(벽·발판) 윗면의 y. 없으면 None."""
    row = room.row_of(y)
    col = room.col_of(x)
    for r in range(max(row, 0), room.nrows):
        if room.tile_at(col, r) in (room_module.SOLID, room_module.ONEWAY):
            return room.tile_top(r)
    return None


class Debris:
    """보스가 발을 구르면 천장에서 떨어지는 고철 더미. 떨어질 자리 바닥에 먼저 붉은 표시가 깜빡이고(예고), 그다음 떨어진다."""
    WARN = 0.75          # 표시가 깜빡이는 시간(초)
    FALL_FROM = 760      # 바닥 위 이 높이에서 떨어지기 시작한다(px)
    FALL_SPEED = 1500.0

    def __init__(self, x, floor_y, delay, damage, gauge_delta, room, player):
        self.x, self.floor_y = x, floor_y
        self.wait = delay
        self.warn = self.WARN
        self.y = floor_y + self.FALL_FROM
        self.falling = False
        self.damage, self.gauge_delta = damage, gauge_delta
        self.room, self.player = room, player
        self.time = 0.0

    def rect(self):
        return (self.x - 30, self.y, self.x + 30, self.y + 50)

    def update(self, dt):
        self.time += dt
        if self.wait > 0:
            self.wait -= dt
            return
        if self.warn > 0:
            self.warn -= dt
            return
        if not self.falling:
            self.falling = True
        self.y -= self.FALL_SPEED * dt
        p = self.player
        if p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect()):
            p.take_hit(self.damage, gauge_delta=self.gauge_delta)
            self._land()
            return
        if self.y <= self.floor_y:
            self._land()

    def _land(self):
        effects.spawn('puff', self.x, self.floor_y + 10, duration=0.4)
        effects.add_trauma(0.15)
        game_world.remove_object(self)

    def draw(self):
        if self.wait > 0:
            return
        if not self.falling:                                # 떨어질 자리 표시: 점점 빨리 깜빡인다
            rate = 8 if self.warn > self.WARN / 2 else 16
            # 노란 표시: 붉은 테마 바닥에서도 보이게. 떨어질 길도 옅은 기둥으로 보여 준다
            assets.draw_rect_color(int(self.x) - 3, int(self.floor_y), 6, self.FALL_FROM - 60, (250, 220, 90), 0.18)
            if int(self.time * rate) % 2 == 0:
                assets.draw_rect_image(assets.image('placeholder/px_yellow.png'), int(self.x) - 36, int(self.floor_y), 72, 6)
                assets.draw_rect_image(assets.image('placeholder/px_white.png'), int(self.x) - 6, int(self.floor_y) + 10, 12, 12)
            return
        img = assets.image('sprites/unified/proj_scrap.png')
        for ox, oy in ((-14, 0), (12, 16), (0, 30)):        # 고철 세 조각이 뭉쳐 떨어진다
            assets.draw_image(img, self.x + ox, self.y + oy, '')
