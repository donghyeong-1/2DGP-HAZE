"""투사체. 지금은 고철 투척병이 던지는 고철 조각 하나뿐이다.

실행 중 회전하지 않으므로(docs/pixel_rules.md 규칙 5) 가로로만 날고, 왼쪽은 좌우 반전으로 그린다.
"""
import assets
import config
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

    def rect(self):
        return (self.x - 36, self.y, self.x + 36, self.y + 56)

    def update(self, dt):
        self.x += self.dir * self.speed * dt
        self.life -= dt
        if self.life <= 0 or self.room.tile_at_world(self.x + self.dir * 36, self.y + 20) == room_module.SOLID:
            game_world.remove_object(self)
            return
        p = self.player
        if p.state != 'DEAD' and p.invuln_left <= 0 and overlap(self.rect(), p.rect()):
            p.take_hit(self.damage, gauge_delta=self.gauge_delta)
            game_world.remove_object(self)

    def draw(self):
        left, bottom, right, top = self.rect()
        for name, inset, h in (('px_orange', 0, 56), ('px_yellow', 10, 40), ('px_white', 22, 22)):
            assets.draw_rect_image(assets.image('placeholder/' + name + '.png'), left + inset, bottom, (right - left) - 2 * inset, h)
