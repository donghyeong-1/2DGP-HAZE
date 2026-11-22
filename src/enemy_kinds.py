"""공장 새 적 (2026-11-22 v5 계획 1, docs/plan_v5.md, 그림 Codex T36·T37). 공장(스테이지 2)에만 나온다.

- 용접 드론(Drone): 중력 없이 날아 플레이어 머리 위(hover px)에 머문다. 가로로 가까워지면 예고(토치를 아래로,
  렌즈가 밝아짐, 바닥에 붉은 표시) 뒤 아래로 곧은 불꽃을 뿜는다. 불꽃은 벽 칸에서 멈춘다(얇은 발판은 뚫는다).
  옆으로 비키면 맞지 않는다. 마우스 조준을 위로 쓰게 만든다. 쓰러지면 잔해가 바닥으로 떨어진다.
- 자폭 수레(Cart): 굴러와 가까이서 예고(경고등·통이 부풂) 뒤 터진다. 맞으면 맞은 쪽 반대로 되밀려 굴러가다
  적이나 벽에 닿으면 그 자리에서 터진다(받아치기: 적에게 큰 피해). 부수면 잠깐 뒤 터진다(가까이서 부수면 휘말린다).
make(kind, ...)가 종류에 맞는 클래스를 만든다(stage가 쓴다).
"""
import math

import assets
import config
import effects
import game_world
import projectile
import room as room_module
import sprites
from body import TileBody
from enemy import MOVES, Corpse, Enemy

MOVES['torch'] = dict(range=None, gap=0, windup=1.0, active=None)
MOVES['arm'] = dict(range=None, gap=0, windup=1.0, active=None)

DRONE_RISE = 120            # 바닥 스폰 칸에서 이만큼 띄워 시작한다
DRONE_ACCEL = 900.0         # 목표점으로 가는 가속(px/s^2)
FLAME_MAX = 640             # 불꽃 최대 길이(px)
CART_DEATH_DELAY = 0.45     # 부순 수레가 터지기까지(초)
CART_RETURN_TIME = 1.2      # 되밀린 수레가 굴러가는 최대 시간(초)


def make(kind, x, y, room, player):
    if kind == 'drone':
        return Drone(kind, x, y + DRONE_RISE, room, player)
    if kind == 'cart':
        return Cart(kind, x, y, room, player)
    return Enemy(kind, x, y, room, player)


def blast(x, y, radius, player, player_damage, enemy_damage, source, skip=None, gauge_delta=0):
    """반경 안의 플레이어(벽 너머 제외)와 적에게 피해. 맞힌 적 수를 돌려준다."""
    effects.spawn('haze-blast', x, y, duration=0.45)
    effects.add_trauma(0.45)
    assets.play_sound('overload')
    room = getattr(player, 'room', None)
    px, py = player.center
    if player_damage and player.state != 'DEAD' and math.hypot(px - x, py - y) <= radius and (
            room is None or not room.line_blocked(x, y, px, py)):
        player.take_hit(player_damage, gauge_delta=gauge_delta, source=source)
    hit = 0
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        if e is skip or e is source or not getattr(e, 'alive', False):
            continue
        ex, ey = e.center
        if math.hypot(ex - x, ey - y) <= radius:
            e.take_damage(enemy_damage, from_x=x, knock=1.6)
            hit += 1
    return hit


# ----- 용접 드론 -----
class Drone(Enemy):
    def __init__(self, kind, x, y, room, player):
        super().__init__(kind, x, y, room, player)
        self.move = 'torch'
        self.time = self.rng.uniform(0, 3)
        self.side = self.rng.choice((-1, 1))      # 머리 위에서 조금 비켜 서는 쪽 (여럿이 한 점에 겹치지 않게)

    def update(self, dt):
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.state != 'HIT':
            self.stagger_guard = max(0.0, self.stagger_guard - dt)
        getattr(self, '_do_' + self.state.lower())(dt)
        self.move_with_tiles(dt)                  # 중력 없음

    def _target(self):
        p = self.player
        return p.x + self.side * 24, p.y + self.stats['hover']

    def _steer(self, tx, ty, dt, speed):
        """목표점으로 부드럽게 다가간다 (가까우면 느려진다)."""
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        want = min(speed, d * 3.0)
        wx, wy = (dx / d * want, dy / d * want) if d > 1 else (0.0, 0.0)
        k = min(1.0, DRONE_ACCEL * dt / max(1.0, math.hypot(wx - self.vx, wy - self.vy)))
        self.vx += (wx - self.vx) * k
        self.vy += (wy - self.vy) * k

    def _do_idle(self, dt):
        s = self.stats
        self.vx *= 0.9
        self.vy = math.sin(self.time * 2.4) * 18.0                # 제자리에서 둥실
        if self._player_alive() and self.distance_x() <= s['sight'] and abs(self.player.y - self.y) < s['sight_dy']:
            self.see()

    def _do_chase(self, dt):
        if not self._player_alive():
            self.vx = self.vy = 0.0
            return
        if self.player.x != self.x:
            self.face_dir = 1 if self.player.x > self.x else -1
        tx, ty = self._target()
        self._steer(tx, ty + math.sin(self.time * 2.4) * 12, dt, self._speed())
        for o in game_world.world[game_world.LAYER_ENEMY]:      # 다른 드론과 겹치지 않게
            if o is not self and isinstance(o, Drone) and o.alive and abs(o.x - self.x) < 90 and abs(o.y - self.y) < 70:
                self.vx += (1 if self.x >= o.x else -1) * 160.0 * dt * 10
        above = self.y - self.player.y
        if (self.cooldown <= 0 and abs(self.player.x - self.x) <= self.stats['attack_range']
                and 80 < above < self.stats['hover'] + 200):
            self.vx = self.vy = 0.0
            self.engage()

    def _do_attack(self, dt):
        self.attack_time += dt
        self.vx *= 0.8
        self.vy = math.sin(self.time * 2.4) * 6.0
        windup, active = self._windup_time(), self._active_time()
        t = self.attack_time
        if t >= windup:
            if not self.struck and self.hits_done == 0:
                self.hits_done = 1
                assets.play_sound('drone_torch')
                effects.add_trauma(0.12)
            if not self.struck and self._player_alive() and projectile.overlap(self.flame_box(), self.player.rect()):
                self.struck = True
                self.player.take_hit(self.stats['damage'], gauge_delta=self.stats['gain_on_hit'], source=self)
        if t >= windup + active:
            self.cooldown = self.stats['cooldown'] * self.rng.uniform(0.85, 1.2)
            self.side = -self.side
            self.recover()

    def _do_hit(self, dt):
        self.hit_left -= dt
        self.vx *= max(0.0, 1.0 - 6.0 * dt)
        self.vy *= max(0.0, 1.0 - 6.0 * dt)
        if self.hit_left <= 0:
            self.stagger_guard = self.stats.get('stagger_guard', config.ENEMY_STAGGER_GUARD)
            self.recover_hit()

    def flame_box(self):
        """불꽃 판정 (x0, y0, x1, y1): 노즐(몸 아래)에서 아래로, 처음 만나는 벽 칸 윗면까지."""
        w = self.stats['flame_w']
        top = self.y + 6
        bottom = max(0.0, top - FLAME_MAX)
        y = top
        while y > bottom:
            if self.room.tile_at_world(self.x, y) == room_module.SOLID:
                bottom = self.room.tile_top(self.room.row_of(y))
                break
            y -= config.TILE / 2
        return (self.x - w / 2, bottom, self.x + w / 2, top)

    def take_damage(self, damage, from_x=None, knock=1.0):
        killed = super().take_damage(damage, from_x, knock)
        if killed:                                      # 잔해가 바닥으로 떨어진다 (불똥)
            game_world.add_object(FallingWreck(self.x, self.y, self.face_dir, self.vx * 0.4, self.room),
                                  game_world.LAYER_EFFECT)
        elif from_x is not None and self.state == 'HIT':
            self.vy = 120.0                             # 맞으면 살짝 튀어 오른다
        return killed

    # ----- 그리기 -----
    def _body_frame(self):
        if self.state == 'HIT':
            return 'enemy_drone_hurt', 1 if self.hit_left > 0.09 else 2
        if self.state == 'ATTACK':
            windup = self._windup_time()
            if self.attack_time < windup:
                return 'enemy_drone_aim', 1 if self.attack_time < windup * 0.5 else 2
            return 'enemy_drone_fire', int((self.attack_time - windup) * 18) % 3 + 1
        return 'enemy_drone_fly', int(self.time * 14) % 4 + 1

    def _pose_offset(self, name):
        return 0, 0

    def draw(self):
        if self.state == 'ATTACK':
            x0, y0, x1, y1 = self.flame_box()
            windup = self._windup_time()
            if self.attack_time < windup:                       # 예고: 바닥에 붉은 표시 (점점 진하게)
                k = self.attack_time / windup
                if int(self.attack_time * 14) % 2 == 0 or k > 0.7:
                    assets.draw_rect_color(int(x0), int(y0), int(x1 - x0), 6, (255, 90, 70), 0.4 + 0.5 * k)
            else:
                self._draw_flame(x0, y0, x1, y1)
        super().draw()

    def _draw_flame(self, x0, y0, x1, y1):
        """아래로 뿜는 불꽃 (정수 좌표 사각형 세 겹 + 깜빡이는 가장자리)."""
        w = int(x1 - x0)
        h = int(y1 - y0)
        flick = int(self.attack_time * 30) % 2
        assets.draw_rect_color(int(x0) - 4 + flick * 2, int(y0), w + 8 - flick * 4, h, (255, 110, 40), 0.75)
        assets.draw_rect_color(int(x0) + 10, int(y0), w - 20, h, (255, 200, 90))
        assets.draw_rect_color(int(x0) + 20, int(y0), w - 40, h, (255, 250, 220))
        assets.draw_rect_color(int(x0) - 18, int(y0), w + 36, 10, (255, 140, 60), 0.8)     # 바닥에 튀는 불꽃


class FallingWreck(TileBody):
    """쓰러진 드론의 잔해: 떨어지는 동안 1장, 바닥에 닿으면 누운 2장 -> 잠시 뒤 흩어진다 (판정 없음)."""
    hb_w, hb_h = 40, 20

    def __init__(self, x, y, face_dir, vx, room):
        self.x, self.y, self.face_dir, self.room = x, y, face_dir, room
        self.vx, self.vy = vx, 0.0
        self.on_ground = False
        self.time = 0.0
        self.landed = None

    def update(self, dt):
        self.time += dt
        if self.landed is None:
            self.vy = max(self.vy - config.GRAVITY * dt, -config.MAX_FALL_SPEED)
            self.vx *= max(0.0, 1.0 - 2.0 * dt)
            self.move_with_tiles(dt)
            if self.on_ground:
                self.landed = self.time
                self.vx = 0.0
                effects.spawn('puff', self.x, self.y + 10, duration=0.35)
                assets.play_sound('land')
            elif self.time > 3.0:                               # 바닥이 없는 곳(구덩이)으로 떨어졌다
                game_world.remove_object(self)
            return
        if self.time - self.landed >= config.CORPSE_TIME + config.CORPSE_FADE:
            effects.spawn('death-burst', self.x, self.y + 20, duration=0.45)
            game_world.remove_object(self)

    def draw(self):
        n = 1 if self.landed is None else 2
        alpha = 1.0
        if self.landed is not None:
            alpha = max(0.0, 1.0 - max(0.0, self.time - self.landed - config.CORPSE_TIME) / config.CORPSE_FADE)
        sprites.draw('enemy_drone_wreck', n, int(self.x), int(self.y), self.face_dir, alpha=alpha)


# ----- 자폭 수레 -----
class Cart(Enemy):
    def __init__(self, kind, x, y, room, player):
        super().__init__(kind, x, y, room, player)
        self.move = 'arm'
        self.returned = False       # 받아쳐져 되밀려 굴러가는 중
        self.return_dir = 1
        self.return_left = 0.0
        self.last_x = x

    def _move_arm(self, after):
        if not self.struck:
            self.struck = True
            self.explode(self.stats['damage'], self.stats['blast_enemy'] // 2)

    def explode(self, player_damage, enemy_damage):
        """그 자리에서 터진다: 반경 안의 플레이어·적에게 피해, 잔해를 남기고 사라진다."""
        if not self.alive:
            return
        self.alive = False
        self.die()
        x, y = self.center
        blast(x, y, self.stats['blast_r'], self.player, player_damage, enemy_damage, self,
              gauge_delta=self.stats['gain_on_hit'])
        game_world.add_object(Corpse('enemy_cart_wreck', self.x, self.y, self.face_dir, self.vx * 0.2),
                              game_world.LAYER_EFFECT)
        game_world.remove_object(self)

    def take_damage(self, damage, from_x=None, knock=1.0):
        was_alive = self.alive
        killed = super().take_damage(damage, from_x, knock)
        if killed and was_alive:                        # 부쉈다: 잠깐 뒤 터진다 (가까이서 부수면 휘말린다)
            game_world.add_object(CartBlast(self.x, self.y + self.hb_h / 2, self.player, self.stats),
                                  game_world.LAYER_EFFECT)
            game_world.add_object(Corpse('enemy_cart_wreck', self.x, self.y, self.face_dir, self.vx * 0.3),
                                  game_world.LAYER_EFFECT)
        elif not killed and from_x is not None:         # 받아쳤다: 맞은 쪽 반대로 되밀려 굴러간다
            self.returned = True
            self.return_dir = 1 if self.x >= from_x else -1
            self.return_left = CART_RETURN_TIME
            self.face_dir = self.return_dir
            self.hit_left = CART_RETURN_TIME
            self.last_x = self.x
            if self.state != 'HIT':
                self.hurt()
        return killed

    def _do_hit(self, dt):
        if not self.returned:
            super()._do_hit(dt)
            return
        self.return_left -= dt
        moved = abs(self.x - self.last_x)
        self.last_x = self.x
        self.vx = self.return_dir * self.stats['return_speed']
        bumped = None
        for o in game_world.world[game_world.LAYER_ENEMY]:
            if o is not self and getattr(o, 'alive', False) and projectile.overlap(self.rect(), o.rect()):
                bumped = o
                break
        wall = self.return_left < CART_RETURN_TIME - 0.05 and moved < 0.5
        if bumped is not None or wall or self.return_left <= 0:
            self.player.shards += config.SHARDS_PER_KILL.get('cart', 1)      # 받아쳐 터뜨렸다: 처치로 친다
            self.player.run_kills = getattr(self.player, 'run_kills', 0) + 1
            self.explode(self.stats['damage'], self.stats['blast_enemy'])

    def _attack_frame(self):
        k = self.attack_time / max(0.05, self._windup_time())
        return min(3, 1 + int(k * 3))

    def _body_frame(self):
        if self.state == 'HIT':
            return 'enemy_cart_hurt', 1 if int(self.return_left * 8) % 2 == 0 or not self.returned else 2
        if self.state == 'ATTACK':
            return 'enemy_cart_arm', self._attack_frame()
        if self.on_ground and self.vx != 0:
            return 'enemy_cart_roll', int(self.walk_phase) % 4 + 1
        return 'enemy_cart_roll', 1

    def _pose_offset(self, name):
        return 0, 0


class CartBlast:
    """부서진 수레가 남긴 폭발: 예고 고리가 조여 든 뒤 터진다 (EliteBurst와 같은 모양, 수레 반경)."""

    def __init__(self, x, y, player, stats):
        self.x, self.y, self.player, self.stats = x, y, player, stats
        self.time = 0.0
        assets.play_sound('windup_cart')

    def update(self, dt):
        self.time += dt
        if self.time >= CART_DEATH_DELAY:
            blast(self.x, self.y, self.stats['blast_r'], self.player, self.stats['damage'], self.stats['blast_enemy'], self,
                  gauge_delta=self.stats['gain_on_hit'])
            game_world.remove_object(self)

    def draw(self):
        k = self.time / CART_DEATH_DELAY
        r = int(self.stats['blast_r'] * (1.0 - 0.7 * k))
        for i in range(16):
            a = i / 16 * math.tau + k * 2
            x, y = int(self.x + math.cos(a) * r), int(self.y + math.sin(a) * r)
            assets.draw_rect_color(x - 4, y - 4, 8, 8, (255, 110, 60), 0.5 + 0.5 * k)
