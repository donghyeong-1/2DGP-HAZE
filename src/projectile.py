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


class SteamVent:
    """보스의 헤이즈 증기 분출. 바닥에 청록 표시가 먼저 깜빡이고(예고), 그다음 증기 기둥이 솟는다.
    닿으면 게이지가 오른다(한 번만, HP 피해 없음). 대시 무적 중에는 닿지 않는다."""
    WARN = 0.6           # 표시가 깜빡이는 시간(초)
    ERUPT = 0.8          # 기둥이 솟아 있는 시간(초)
    W, H = 70, 260       # 기둥 크기(px)

    def __init__(self, x, floor_y, delay, gauge_delta, room, player):
        self.x, self.floor_y = x, floor_y
        self.wait = delay
        self.warn = self.WARN
        self.left = self.ERUPT
        self.erupting = False
        self.used = False
        self.gauge_delta = gauge_delta
        self.room, self.player = room, player
        self.time = 0.0

    def rect(self):
        return (self.x - self.W / 2, self.floor_y, self.x + self.W / 2, self.floor_y + self.H)

    def update(self, dt):
        self.time += dt
        if self.wait > 0:
            self.wait -= dt
            return
        if self.warn > 0:
            self.warn -= dt
            return
        if not self.erupting:
            self.erupting = True
            effects.spawn('puff', self.x, self.floor_y + 20, duration=0.35)    # 작은 분출 (큰 폭발은 플레이어를 가린다)
            assets.play_sound('enhance')
        self.left -= dt
        p = self.player
        if (not self.used and p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect())):
            self.used = True
            p.gauge.add(self.gauge_delta, 'steam')
        if self.left <= 0:
            game_world.remove_object(self)

    def draw(self):
        if self.wait > 0:
            return
        x, y = int(self.x), int(self.floor_y)
        if not self.erupting:                                # 솟을 자리 표시: 점점 빨리 깜빡인다 (고철의 노란 표시와 구분되는 청록)
            rate = 8 if self.warn > self.WARN / 2 else 16
            assets.draw_rect_color(x - self.W // 2, y, self.W, 40, (90, 230, 230), 0.35)     # 솟을 자리의 옅은 김
            assets.draw_rect_color(x - 3, y, 6, self.H, (110, 235, 230), 0.15)                # 솟을 높이를 보여 주는 가는 기둥
            if int(self.time * rate) % 2 == 0:
                assets.draw_rect_color(x - 40, y, 80, 8, (140, 255, 245))
            return
        k = self.left / self.ERUPT                           # 솟았다가 옅어진다
        h = int(self.H * min(1.0, (1.0 - k) * 4 + 0.3))
        for i, (w, a) in enumerate(((self.W, 0.22), (self.W - 24, 0.3), (self.W - 48, 0.4))):
            sway = int(4 * ((self.time * 9 + i) % 2 > 1)) - 2   # 증기가 좌우로 흔들린다 (정수 좌표)
            assets.draw_rect_color(x - w // 2 + sway, y, w, h, (110, 235, 230), a * (0.4 + 0.6 * k))


# ----- 최종 보스 아크의 패턴 (src/ark.py). 그림은 모두 코드로 그린 정수 좌표 사각형 -----
def _gauge_delta(net):
    """'맞았을 때 최종 게이지 변화'(net)를 take_hit의 gauge_delta로: 피격 기본 손실(LOSS_DAMAGED)을 빼 준다."""
    return net - config.LOSS_DAMAGED


class HazeBullet:
    """헤이즈 탄막의 탄환 한 발. 맞으면 게이지가 오른다(최종 +5%). 벽에 닿으면 사라진다."""
    R = 7                # 판정 반지름(px)

    def __init__(self, x, y, dx, dy, room, player):
        n = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        self.x, self.y = x, y
        self.vx, self.vy = dx / n * config.ARK_BULLET_SPEED, dy / n * config.ARK_BULLET_SPEED
        self.room, self.player = room, player
        self.life = 2.5
        self.time = 0.0

    def rect(self):
        return (self.x - self.R, self.y - self.R, self.x + self.R, self.y + self.R)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.time += dt
        if self.life <= 0 or self.room.tile_at_world(self.x, self.y) == room_module.SOLID:
            game_world.remove_object(self)
            return
        p = self.player
        if p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect()):
            p.take_hit(config.ARK_BULLET_DAMAGE, gauge_delta=_gauge_delta(config.ARK_BULLET_NET))
            game_world.remove_object(self)

    def draw(self):
        x, y = int(self.x), int(self.y)
        pulse = 2 if int(self.time * 12) % 2 else 0
        assets.draw_rect_color(x - 9 - pulse, y - 9 - pulse, 18 + pulse * 2, 18 + pulse * 2, (60, 200, 190), 0.35)   # 번짐
        assets.draw_rect_color(x - 6, y - 6, 12, 12, (150, 250, 235), 0.9)
        assets.draw_rect_color(x - 2, y - 2, 4, 4, (255, 255, 255))                                         # 심


WAVE_COLORS = {'absorb': ((120, 80, 210), (200, 170, 255)),       # 흡수: 어두운 보라 (게이지를 빨아들인다)
               'overcharge': ((90, 235, 220), (255, 250, 200))}   # 과충전: 밝은 청록·흰빛 (게이지를 밀어 넣는다)


class GaugeWave:
    """아크의 게이지 파동. 바닥을 따라 움직이는 낮은 벽이라 점프·대시로 피한다.
    absorb(흡수)는 맞으면 최종 -25%, overcharge(과충전)는 +25%. stop_x에 닿으면(흡수는 아크 자리) 사라진다."""

    def __init__(self, x, y, direction, speed, kind, room, player, stop_x=None, life=3.0):
        self.x, self.y = x, y              # y는 바닥 윗면
        self.dir = direction
        self.speed = speed
        self.kind = kind
        self.room, self.player = room, player
        self.stop_x = stop_x
        self.life = life
        self.time = 0.0

    def rect(self):
        return (self.x - 26, self.y, self.x + 26, self.y + config.ARK_WAVE_H)

    def update(self, dt):
        self.x += self.dir * self.speed * dt
        self.life -= dt
        self.time += dt
        reached = self.stop_x is not None and (self.x - self.stop_x) * self.dir >= 0
        if self.life <= 0 or reached or self.room.tile_at_world(self.x + self.dir * 26, self.y + 20) == room_module.SOLID:
            game_world.remove_object(self)
            return
        p = self.player
        if p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect()):
            net = config.ARK_ABSORB_NET if self.kind == 'absorb' else config.ARK_OVERCHARGE_NET
            p.take_hit(config.ARK_WAVE_DAMAGE, gauge_delta=_gauge_delta(net))
            game_world.remove_object(self)

    def draw(self):
        dark, light = WAVE_COLORS[self.kind]
        x, y, h = int(self.x), int(self.y), config.ARK_WAVE_H
        flicker = int(self.time * 16) % 2
        assets.draw_rect_color(x - 26, y, 52, h, dark, 0.35)
        assets.draw_rect_color(x - 14 + flicker * 2, y, 28, h - 10, light, 0.55)
        assets.draw_rect_color(x - 4, y, 8, h - 4, (255, 255, 255), 0.7)
        for i in range(3):                                   # 나아가는 쪽을 가리키는 꺾쇠 (흡수는 안쪽, 과충전은 바깥쪽)
            cx = x + self.dir * (18 + i * 10)
            cy = y + 20 + i * 18
            assets.draw_rect_color(cx - 3, cy, 6, 6, light, 0.8)


class PollutionField:
    """아크의 오염 장판. 바닥에 깔리고, 위에 서 있으면 초당 +5% 게이지가 오른다(피해 없음). 시간이 지나면 걷힌다."""

    def __init__(self, x, floor_y, width, duration, room, player):
        self.x, self.floor_y = x, floor_y
        self.w = width
        self.left = self.total = duration
        self.room, self.player = room, player
        self.acc = 0.0                        # 1%씩 모아서 올린다 (게이지 변화 횟수를 줄인다)
        self.time = 0.0

    def contains(self, p):
        return (abs(p.x - self.x) <= self.w / 2 and abs(p.y - self.floor_y) < 30 and p.on_ground)

    def update(self, dt):
        self.left -= dt
        self.time += dt
        if self.left <= 0:
            game_world.remove_object(self)
            return
        p = self.player
        if p.state != 'DEAD' and self.contains(p):
            self.acc += config.ARK_FIELD_RATE * dt
            while self.acc >= 1.0:
                self.acc -= 1.0
                p.gauge.add(1.0, 'field')

    def draw(self):
        fade = min(1.0, self.left / 0.5, self.time / 0.25)   # 깔릴 때와 걷힐 때 옅게
        x0, y = int(self.x - self.w / 2), int(self.floor_y)
        assets.draw_rect_color(x0, y, int(self.w), 16, (70, 210, 160), 0.38 * fade)
        assets.draw_rect_color(x0, y, int(self.w), 4, (170, 255, 210), 0.7 * fade)
        for i in range(int(self.w // 40)):                   # 거품이 올라온다
            bx = x0 + 14 + i * 40 + (i * 13) % 17
            rise = int((self.time * 40 + i * 23) % 46)
            assets.draw_rect_color(bx, y + 8 + rise, 6, 6, (150, 255, 210), 0.6 * fade * (1 - rise / 46))
