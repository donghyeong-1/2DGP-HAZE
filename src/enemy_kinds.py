"""공장 새 적 (2026-11-22 v5 계획 1, docs/plan_v5.md, 그림 Codex T36·T37). 공장(스테이지 2)에만 나온다.

- 용접 드론(Drone): 중력 없이 날아 플레이어 머리 위(hover px)에 머문다. 가로로 가까워지면 예고(토치를 아래로,
  렌즈가 밝아짐, 바닥에 붉은 표시) 뒤 아래로 곧은 불꽃을 뿜는다. 불꽃은 벽 칸에서 멈춘다(얇은 발판은 뚫는다).
  옆으로 비키면 맞지 않는다. 마우스 조준을 위로 쓰게 만든다. 쓰러지면 잔해가 바닥으로 떨어진다.
- 자폭 수레(Cart): 굴러와 가까이서 예고(경고등·통이 부풂) 뒤 터진다. 맞으면 맞은 쪽 반대로 되밀려 굴러가다
  적이나 벽에 닿으면 그 자리에서 터진다(받아치기: 적에게 큰 피해). 부수면 잠깐 뒤 터진다(가까이서 부수면 휘말린다).
make(kind, ...)가 종류에 맞는 클래스를 만든다(stage가 쓴다).

구역 새 적 (2026-11-22 v5 계획 1, 그림 Codex T38~T42). 탑(스테이지 3), 슬럼(스테이지 1)에만 나온다.
- 감시 눈(Eye): 벽에 붙은 포탑. 보이면 예고(렌즈가 밝아짐, 조준선) 뒤 레이저로 바닥을 훑는다. 맞으면 끊기고 부술 수 있다.
- 결정 기사(Knight): 멀리 있으면 헤이즈로 사라졌다 플레이어 바로 옆에 나타나 벤다(사라진 동안 맞지 않는다). 가까우면 그냥 벤다.
- 헤이즈 망령(Wraith): 중력도 벽도 무시하고 느리게 다가와 팔을 뻗어 빨아들인다(게이지를 더 뺏는다). 맞으면 오래 흐트러진다.
- 헤이즈 쥐(일반 Enemy): 작고 빠르며 한 대에 죽는다. make_pack이 한 칸에 여러 마리로 만든다.
- 누더기 무당(Shaman): 뒤에서 거리를 두고 다른 적에게 보호막을 건다(Enemy.shield). 먼저 잡아야 할 대상.
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
MOVES['laser'] = dict(range=None, gap=0, windup=1.0, active=None)
MOVES['slash'] = dict(range=None, gap=0, windup=1.0, active=None)
MOVES['blink'] = dict(range=None, gap=0, windup=1.0, active=None)     # 순간이동 뒤 베기 (windup·active는 베기의 것)
MOVES['grab'] = dict(range=None, gap=0, windup=1.0, active=None)
MOVES['cast'] = dict(range=None, gap=0, windup=1.0, active=0.45)

DRONE_RISE = 120            # 바닥 스폰 칸에서 이만큼 띄워 시작한다
DRONE_ACCEL = 900.0         # 목표점으로 가는 가속(px/s^2)
FLAME_MAX = 640             # 불꽃 최대 길이(px)
CART_DEATH_DELAY = 0.45     # 부순 수레가 터지기까지(초)
CART_RETURN_TIME = 1.2      # 되밀린 수레가 굴러가는 최대 시간(초)
EYE_RISE = 110              # 감시 눈: 바닥 스폰 칸에서 이만큼 띄워 벽에 붙인다
EYE_PLATE = 66              # 눈 몸통 중심에서 벽 고정판 끝까지(px, 그림 기준)
EYE_LOCK = 0.25             # 발사 이만큼 전에 조준선이 고정된다 (그 뒤에는 피할 수 있다)
BEAM_STEP = 12              # 레이저를 이 간격으로 훑어 벽을 찾고 맞았는지 본다
BEAM_MAX = 1500
KNIGHT_VANISH = 0.3         # 결정 기사 순간이동: 사라지는 중 -> 안 보임(맞지 않음) -> 나타나는 중 -> 베기
KNIGHT_HIDDEN = 0.3
KNIGHT_APPEAR = 0.3
KNIGHT_SIDE = 115           # 플레이어 옆 이만큼 떨어진 곳에 나타난다
WRAITH_RISE = 90            # 망령: 바닥 스폰 칸에서 이만큼 띄워 시작한다


def make(kind, x, y, room, player):
    if kind == 'drone':
        return Drone(kind, x, y + DRONE_RISE, room, player)
    if kind == 'cart':
        return Cart(kind, x, y, room, player)
    if kind == 'eye':
        return Eye(kind, x, y, room, player)
    if kind == 'knight':
        return Knight(kind, x, y, room, player)
    if kind == 'wraith':
        return Wraith(kind, x, y + WRAITH_RISE, room, player)
    if kind == 'shaman':
        return Shaman(kind, x, y, room, player)
    return Enemy(kind, x, y, room, player)


def make_pack(kind, x, y, room, player):
    """스폰 칸 하나에서 나오는 적들: 무리 종류(config.PACK_SIZE)는 여러 마리가 나란히, 그 밖은 한 마리."""
    n = config.PACK_SIZE.get(kind, 1)
    spacing = config.ENEMY_STATS[kind]['hb'][0] + 8
    return [make(kind, x + (i - (n - 1) / 2) * spacing, y, room, player) for i in range(n)]


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


# ----- 감시 눈 (탑) -----
class Eye(Enemy):
    """벽에 붙은 둥근 눈. 가까운 옆 벽에 달라붙어 방 안쪽을 본다. 중력·이동 없음."""

    def __init__(self, kind, x, y, room, player):
        super().__init__(kind, x, y + EYE_RISE, room, player)
        self.move = 'laser'
        self.time = self.rng.uniform(0, 3)
        self.sweep_dir = self.rng.choice((-1, 1))
        self.aim = 0.0
        self._mount()

    def _mount(self):
        """스폰 칸에서 가장 가까운 옆 벽에 고정판을 붙인다 (벽이 없으면 제자리, 방 쪽을 본다)."""
        cy = self.y + self.hb_h / 2
        self.face_dir = 1
        for d in range(0, 1300, 10):
            for side in (-1, 1):
                if self.room.tile_at_world(self.x + side * d, cy) == room_module.SOLID:
                    col = self.room.col_of(self.x + side * d)
                    edge = (col + 1) * config.TILE if side < 0 else col * config.TILE
                    self.x = edge - side * EYE_PLATE
                    self.face_dir = -side
                    return

    def muzzle(self):
        return self.x + self.face_dir * 34, self.y + self.hb_h / 2

    def _sees_player(self):
        if not self._player_alive():
            return False
        mx, my = self.muzzle()
        px, py = self.player.center
        return math.hypot(px - mx, py - my) <= self.stats['attack_range'] and not self.room.line_blocked(mx, my, px, py)

    def beam_path(self, angle):
        """레이저가 지나는 점들: 눈 렌즈에서 angle(라디안) 방향으로 처음 만나는 벽 앞까지."""
        mx, my = self.muzzle()
        dx, dy = math.cos(angle), math.sin(angle)
        pts = []
        d = BEAM_STEP
        while d <= BEAM_MAX:
            x, y = mx + dx * d, my + dy * d
            if self.room.tile_at_world(x, y) == room_module.SOLID:
                break
            pts.append((x, y))
            d += BEAM_STEP
        return pts

    def beam_end(self, angle):
        pts = self.beam_path(angle)
        return pts[-1] if pts else self.muzzle()

    def update(self, dt):
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.state != 'HIT':
            self.stagger_guard = max(0.0, self.stagger_guard - dt)
        self.vx = self.vy = 0.0
        getattr(self, '_do_' + self.state.lower())(dt)

    def _do_idle(self, dt):
        if self._sees_player() and self.distance_x() <= self.stats['sight']:
            self.see()

    def _do_chase(self, dt):
        if self.cooldown <= 0 and self._sees_player():
            self.engage()

    def on_attack_start(self):
        face = self.face_dir
        super().on_attack_start()
        self.face_dir = face                               # 벽에 붙어 있어 돌지 않는다
        mx, my = self.muzzle()
        px, py = self.player.center
        self.aim = math.atan2(py - my, px - mx)
        self.sweep_dir = -self.sweep_dir                   # 쏠 때마다 훑는 방향이 바뀐다

    def _do_attack(self, dt):
        self.attack_time += dt
        windup, active = self._windup_time(), self._active_time()
        t = self.attack_time
        if t < windup - EYE_LOCK and self._player_alive():     # 예고 앞부분은 플레이어를 따라가고, 마지막 EYE_LOCK 동안은 고정
            mx, my = self.muzzle()
            px, py = self.player.center
            self.aim = math.atan2(py - my, px - mx)
        if t >= windup:
            if self.hits_done == 0:
                self.hits_done = 1
                assets.play_sound('drone_torch')
                effects.add_trauma(0.15)
            if not self.struck and self._player_alive():
                pr = self.player.rect()
                grow = self.stats['beam_w'] / 2
                box = (pr[0] - grow, pr[1] - grow, pr[2] + grow, pr[3] + grow)
                for x, y in self.beam_path(self._beam_angle()):
                    if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                        self.struck = True
                        self.player.take_hit(self.stats['damage'], gauge_delta=self.stats['gain_on_hit'], source=self)
                        break
        if t >= windup + active:
            self.cooldown = self.stats['cooldown'] * self.rng.uniform(0.85, 1.2)
            self.recover()

    def _beam_angle(self):
        """발사 중 레이저 방향: 고정한 조준선에서 시작해 바닥을 훑는다."""
        k = min(1.0, max(0.0, (self.attack_time - self._windup_time()) / max(0.05, self._active_time())))
        return self.aim + self.sweep_dir * self.stats['sweep'] * k

    def _do_hit(self, dt):
        self.hit_left -= dt
        if self.hit_left <= 0:
            self.stagger_guard = self.stats.get('stagger_guard', config.ENEMY_STAGGER_GUARD)
            self.recover_hit()

    # ----- 그리기 -----
    def _body_frame(self):
        if self.state == 'HIT':
            return 'enemy_eye_hurt', 1 if self.hit_left > 0.09 else 2
        if self.state == 'ATTACK':
            windup = self._windup_time()
            if self.attack_time < windup:
                return 'enemy_eye_charge', min(3, 1 + int(self.attack_time / windup * 3))
            return 'enemy_eye_fire', 1
        return 'enemy_eye_idle', int(self.time * 1.2) % 2 + 1

    def _pose_offset(self, name):
        return 0, 0

    def draw(self):
        if self.state == 'ATTACK':
            if self.attack_time < self._windup_time():
                self._draw_aim()
            else:
                self._draw_beam()
        super().draw()

    def _draw_aim(self):
        """예고: 렌즈에서 조준선 (점점 진하게, 고정되면 또렷하게)."""
        windup = self._windup_time()
        k = self.attack_time / windup
        locked = self.attack_time >= windup - EYE_LOCK
        for i, (x, y) in enumerate(self.beam_path(self.aim)):
            if i % 3 == 0 and (locked or (i // 3 + int(self.attack_time * 10)) % 2 == 0):
                assets.draw_rect_color(int(x) - 3, int(y) - 3, 6, 6, (255, 90, 70) if locked else (255, 200, 120), 0.35 + 0.55 * k)

    def _draw_beam(self):
        """발사: 청록 레이저 (정수 좌표 사각형 세 겹)."""
        flick = int(self.attack_time * 30) % 2
        for x, y in self.beam_path(self._beam_angle()):
            x, y = int(x), int(y)
            assets.draw_rect_color(x - 10 + flick, y - 10 + flick, 20 - 2 * flick, 20 - 2 * flick, (60, 220, 200), 0.7)
            assets.draw_rect_color(x - 6, y - 6, 12, 12, (170, 255, 235))
            assets.draw_rect_color(x - 2, y - 2, 4, 4, (245, 255, 250))


# ----- 결정 기사 (탑) -----
class Knight(Enemy):
    def __init__(self, kind, x, y, room, player):
        super().__init__(kind, x, y, room, player)
        self.blink_cooldown = 0.0
        self.blinked = False

    @property
    def hidden(self):
        """순간이동 중 사라져 있는 동안 (맞지 않는다)."""
        return (self.state == 'ATTACK' and self.move == 'blink'
                and KNIGHT_VANISH <= self.attack_time < KNIGHT_VANISH + KNIGHT_HIDDEN)

    def update(self, dt):
        self.blink_cooldown = max(0.0, self.blink_cooldown - dt)
        super().update(dt)

    def _blink_spot(self):
        """플레이어 옆에 설 수 있는 x (발밑에 바닥이 있고 몸이 벽에 박히지 않는 곳). 없으면 None."""
        p = self.player
        first = 1 if self.x > p.x else -1                       # 기사가 있던 쪽을 먼저
        for side in (first, -first):
            x = p.x + side * KNIGHT_SIDE
            room = self.room
            if (room.tile_at_world(x, self.y - 4) in (room_module.SOLID, room_module.ONEWAY)
                    and room.tile_at_world(x, self.y + 30) != room_module.SOLID
                    and room.tile_at_world(x, self.y + 100) != room_module.SOLID):
                return x
        return None

    def _pick_move(self, d, dy):
        s = self.stats
        if abs(dy) >= s['reach_dy']:
            return None
        if self.blink_cooldown <= 0 and s['blink_min'] < d <= s['blink_max'] and self._blink_spot() is not None:
            return 'blink'
        if d <= s['attack_range']:
            return 'slash'
        return None

    def on_attack_start(self):
        super().on_attack_start()
        if self.move == 'blink':
            self.blinked = False
            self.blink_cooldown = self.stats['blink_cd']

    def take_damage(self, damage, from_x=None, knock=1.0):
        if self.hidden:
            return False                                        # 사라진 동안은 맞지 않는다
        return super().take_damage(damage, from_x, knock)

    _move_slash = Enemy._move_swing                           # 베기: 앞쪽 박스 한 번

    def _slash_start(self):
        return KNIGHT_VANISH + KNIGHT_HIDDEN + KNIGHT_APPEAR

    def _do_attack(self, dt):
        if self.move != 'blink':
            super()._do_attack(dt)
            return
        self.attack_time += dt
        self.vx = 0.0
        t = self.attack_time
        if t >= KNIGHT_VANISH and not self.blinked:
            self.blinked = True
            self._teleport()
        rel = t - self._slash_start()
        if rel >= self._windup_time():
            if not self.struck:
                self.struck = True
                self._melee()
            if rel >= self._windup_time() + self._active_time():
                self.cooldown = self.stats['cooldown'] * self.rng.uniform(0.85, 1.2)
                self.recover()

    def _teleport(self):
        effects.spawn('death-burst', self.x, self.y + 60, duration=0.4)
        x = self._blink_spot()
        if x is not None:
            self.x = x
        if self.player.x != self.x:
            self.face_dir = 1 if self.player.x > self.x else -1
        effects.spawn('puff', self.x, self.y + 20, duration=0.35)

    def telegraph(self):
        if self.state == 'ATTACK' and self.move == 'blink':
            rel = self.attack_time - self._slash_start()
            return 'blink' if 0 <= rel < self._windup_time() else None
        return super().telegraph()

    def _tint(self):
        if self.state == 'ATTACK' and self.move == 'blink':
            if self.flash > 0:
                return (255, 90, 90)
            rel = self.attack_time - self._slash_start()
            if 0 <= rel < self._windup_time() and int(self.attack_time * 20) % 2 == 0:
                return (255, 225, 120)
            return None
        return super()._tint()

    def _body_frame(self):
        if self.state == 'ATTACK' and self.move == 'blink':
            t = self.attack_time
            if t < KNIGHT_VANISH:
                return 'enemy_knight_vanish', 1 if t < KNIGHT_VANISH / 2 else 2
            t -= KNIGHT_VANISH + KNIGHT_HIDDEN
            if t < KNIGHT_APPEAR:
                return 'enemy_knight_appear', 1 if t < KNIGHT_APPEAR / 2 else 2
            rel = t - KNIGHT_APPEAR
            windup = self._windup_time()
            if rel < windup:
                return 'enemy_knight_slash', 1
            return 'enemy_knight_slash', 2 if rel - windup < self._active_time() * 0.6 else 3
        return super()._body_frame()

    def _pose_offset(self, name):
        if self.state == 'ATTACK' and self.move == 'blink':
            return 0, 0
        return super()._pose_offset(name)

    def draw(self):
        if self.hidden:
            return
        super().draw()


# ----- 헤이즈 망령 (탑) -----
class Wraith(Enemy):
    """중력도 벽도 무시하고 떠다닌다 (방 밖으로만 나가지 않는다)."""

    def __init__(self, kind, x, y, room, player):
        super().__init__(kind, x, y, room, player)
        self.move = 'grab'
        self.time = self.rng.uniform(0, 3)
        self.side = self.rng.choice((-1, 1))                    # 플레이어 옆에서 이쪽으로 비껴 선다

    def update(self, dt):
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.state != 'HIT':
            self.stagger_guard = max(0.0, self.stagger_guard - dt)
        getattr(self, '_do_' + self.state.lower())(dt)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x = max(self.hb_w / 2, min(self.room.width - self.hb_w / 2, self.x))
        self.y = max(0.0, min(self.room.height - self.hb_h, self.y))

    def _steer(self, tx, ty, dt, speed):
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        want = min(speed, d * 2.0)
        wx, wy = (dx / d * want, dy / d * want) if d > 1 else (0.0, 0.0)
        k = min(1.0, DRONE_ACCEL * dt / max(1.0, math.hypot(wx - self.vx, wy - self.vy)))
        self.vx += (wx - self.vx) * k
        self.vy += (wy - self.vy) * k

    def _do_idle(self, dt):
        self.vx *= 0.9
        self.vy = math.sin(self.time * 2.0) * 14.0
        if self._player_alive() and self.distance_x() <= self.stats['sight'] and abs(self.player.y - self.y) < self.stats['sight_dy']:
            self.see()

    def _do_chase(self, dt):
        if not self._player_alive():
            self.vx = self.vy = 0.0
            return
        p = self.player
        if p.x != self.x:
            self.face_dir = 1 if p.x > self.x else -1
        pcx, pcy = p.center
        self._steer(p.x + self.side * self.stats['hover_side'], pcy - self.hb_h / 2 + math.sin(self.time * 2.0) * 10,
                    dt, self._speed())
        cx, cy = self.center
        if self.cooldown <= 0 and math.hypot(pcx - cx, pcy - cy) <= self.stats['attack_range']:
            self.engage()

    def _do_attack(self, dt):
        self.attack_time += dt
        self.vx *= 0.85
        self.vy *= 0.85
        windup, active = self._windup_time(), self._active_time()
        if self.attack_time >= windup and not self.struck:
            self.struck = True
            cx, cy = self.center
            x1 = self.x + self.face_dir * (self.stats['attack_range'] + 30)
            box = (min(self.x, x1), cy - 70, max(self.x, x1), cy + 70)
            effects.spawn('hit-normal', (self.x + x1) / 2, cy, flip=self.face_dir < 0, duration=0.2)
            if self._player_alive() and projectile.overlap(box, self.player.rect()):
                self.player.take_hit(self.stats['damage'], gauge_delta=self.stats['gain_on_hit'], source=self)
        if self.attack_time >= windup + active:
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

    def take_damage(self, damage, from_x=None, knock=1.0):
        killed = super().take_damage(damage, from_x, knock)
        if not killed and self.state == 'HIT':
            self.hit_left = max(self.hit_left, self.stats['stun'])      # 맞으면 한참 흐트러진다
        return killed

    def _body_frame(self):
        if self.state == 'HIT':
            return 'enemy_wraith_hurt', 1
        if self.state == 'ATTACK':
            windup = self._windup_time()
            if self.attack_time < windup:
                return 'enemy_wraith_grab', 1 if self.attack_time < windup * 0.5 else 2
            return 'enemy_wraith_grab', 3
        return 'enemy_wraith_float', int(self.time * 6) % 4 + 1

    def _pose_offset(self, name):
        return 0, 0


# ----- 누더기 무당 (슬럼) -----
class Shaman(Enemy):
    def __init__(self, kind, x, y, room, player):
        super().__init__(kind, x, y, room, player)
        self.move = 'cast'
        self.shield_target = None

    def _shield_target(self):
        """보호막을 걸 적: 사거리 안의 다른 적 중 보호막이 없는 것, 플레이어에 가장 가까운(앞줄) 것. 보스·다른 무당은 제외."""
        s = self.stats
        best, best_d = None, 1e9
        for o in game_world.world[game_world.LAYER_ENEMY]:
            if (o is self or not isinstance(o, Enemy) or isinstance(o, Shaman) or not o.alive or o.shield > 0
                    or not o.pullable):
                continue
            if abs(o.x - self.x) > s['shield_range'] or abs(o.y - self.y) > 250:
                continue
            d = abs(o.x - self.player.x)
            if d < best_d:
                best, best_d = o, d
        return best

    def _do_chase(self, dt):
        s = self.stats
        if not self._player_alive():
            self.vx = 0.0
            return
        if self.cooldown <= 0 and self.on_ground:
            target = self._shield_target()
            if target is not None:
                self.shield_target = target
                self.move = 'cast'
                self.vx = 0.0
                self.engage()
                return
        d = self.distance_x()
        if d < s['keep_away'] and abs(self.player.y - self.y) < 200 and self.on_ground:     # 가까우면 물러난다
            self.vx = -self.face_dir * s['back_speed'] * self._speed() if self._floor_behind() else 0.0
        elif d > s['approach'] and self.on_ground and self._floor_ahead():
            self.vx = self.face_dir * self._speed()
        else:
            self.vx = 0.0

    def _move_cast(self, after):
        self.vx = 0.0
        if self.struck:
            return
        self.struck = True
        t = self.shield_target
        if t is not None and t.alive and t.shield <= 0:
            t.shield = float(self.stats['shield_hp'])
            effects.spawn('puff', t.x, t.y + t.hb_h / 2, duration=0.35)
            assets.play_sound('enemy_hit')

    def draw(self):
        t = self.shield_target
        if self.state == 'ATTACK' and self.move == 'cast' and t is not None and t.alive and self.attack_time < self._windup_time():
            k = self.attack_time / self._windup_time()
            sx, sy = self.x + self.face_dir * 30, self.y + self.hb_h
            tx, ty = t.x, t.y + t.hb_h / 2
            for i in range(1, 9):                               # 지팡이 끝에서 대상으로 가는 점선 (점점 진하게)
                f = i / 9
                if int(f * 9 + self.attack_time * 12) % 2 == 0:
                    assets.draw_rect_color(int(sx + (tx - sx) * f) - 3, int(sy + (ty - sy) * f) - 3, 6, 6,
                                           config.SHIELD_COLOR, 0.3 + 0.6 * k)
        super().draw()
