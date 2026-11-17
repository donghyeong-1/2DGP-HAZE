"""적. 상태 머신(IDLE -> CHASE -> ATTACK -> HIT/DEAD)을 transitions로 돌린다.

종류는 config.ENEMY_STATS의 수치와 **기술 목록(moves)**으로 갈린다. 공격에 들어갈 때 거리에 맞는 기술 중 하나를
가중치로 고른다(첫 공격은 늘 기본기라 처음 보는 적도 읽을 수 있다). 기술마다 예고 시간과 움직임이 다르다.

  슬럼 폐인  : 휘두르기 / 두 번 치기 / 달려들며 치기. 비틀거리며 쫓아오고, 친 뒤에는 반걸음 물러난다.
  고철 투척병: 곧게 던지기 / 세 개 연달아 / 포물선으로 던지기(엄폐물 너머). 가까이 오면 뒤로 뛰어 거리를 벌린다.
  사냥개     : 물기 / 덮치기(멀리서 뛰어들어 닿으면 피해). 치고 빠진다(공격 뒤 크게 물러났다 다시 온다).
  간수       : 휘두르기 / 내려찍기(짧은 충격파) / 방패 돌진. 느리지만 한 방이 크다.

공통 이동: 처음에는 제자리 주변을 순찰하다 플레이어를 보면 쫓는다. 같은 자리에 겹쳐 서지 않도록 서로 밀어낸다.
"""
import math
import random

from transitions import Machine

import assets
import config
import effects
import game_world
import projectile
import room as room_module
import sprites
from body import TileBody

# 기술 표. range: 이 거리 안에서만 고른다 (None = 종류의 attack_range 안). gap: 이 거리보다 멀어야 고른다 (달려드는 기술).
# windup: 예고 시간 배율 (종류의 windup에 곱한다), active: 예고 뒤 기술이 이어지는 시간(초)
MOVES = {
    'swing':  dict(range=None, gap=0, windup=1.0, active=None),
    'combo':  dict(range=None, gap=0, windup=1.0, active=0.5),
    'lunge':  dict(range=300, gap=110, windup=1.15, active=0.4),
    'bite':   dict(range=None, gap=0, windup=1.0, active=None),
    'pounce': dict(range=430, gap=150, windup=1.3, active=0.9),
    'heavy':  dict(range=None, gap=0, windup=1.45, active=0.35),
    'bash':   dict(range=440, gap=150, windup=1.0, active=0.45),
    'throw':  dict(range=None, gap=0, windup=1.0, active=None),
    'volley': dict(range=None, gap=200, windup=1.2, active=0.5),
    'lob':    dict(range=None, gap=160, windup=1.1, active=None),
}
COMBO_GAP = 0.3          # 두 번 치기의 두 번째 타격 시각(첫 타격 뒤 초)
VOLLEY_GAP = 0.16        # 세 개 연달아 던지기 간격(초)
POUNCE_VY = 700.0        # 덮치기로 뛰어오르는 속도(px/s). 낮게 날아 플레이어가 서 있던 자리에 떨어진다
POUNCE_MAX_VX = 1000.0


class Enemy(TileBody):
    def __init__(self, kind, x, y, room, player):
        self.kind = kind
        self.stats = config.ENEMY_STATS[kind]
        self.hb_w, self.hb_h = self.stats['hb']
        self.x, self.y = x, y
        self.home_x = x            # 순찰 중심
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.room, self.player = room, player
        self.hp = self.max_hp = self.stats['hp']
        self.face_dir = -1
        self.alive = True
        self.flash = 0.0           # 맞은 뒤 붉게 번쩍이는 남은 시간
        self.attack_time = 0.0     # ATTACK 상태에 들어온 뒤 지난 시간
        self.struck = False        # 이번 공격의 (첫) 타격을 이미 냈는가
        self.hits_done = 0         # 이번 공격에서 낸 타격 수 (두 번 치기·연달아 던지기)
        self.contact_hit = False   # 몸으로 부딪치는 기술(덮치기·돌진)이 이미 맞혔는가
        self.move = 'swing'        # 지금 쓰는 기술
        self.attacks = 0           # 지금까지 쓴 공격 수 (첫 공격은 기본기)
        self.cooldown = 0.0
        self.hit_left = 0.0
        self.leap_cooldown = 0.0   # 도약 재사용 대기
        self.blocked_time = 0.0    # 가려는데 앞이 막혀 있던 시간 (벽·기둥에 막힘 감지)
        self.walk_phase = 0.0      # 걷기 프레임 위상 (이동한 거리에 비례)
        self.retreat_left = 0.0    # 공격 뒤 물러나는 남은 시간
        self.hop_cooldown = 0.0    # 뒤로 뛰기 재사용 대기 (투척병)
        self.pause_left = 0.0      # 비틀거리며 잠깐 멈춘 남은 시간 (슬럼)
        self.patrol_dir = 1
        self.patrol_wait = 0.0
        # 적마다 조금씩 다르게: 같은 자리·종류면 늘 같은 값이라 테스트와 재현이 된다
        self.rng = random.Random(f'{kind}:{int(x)}:{int(y)}')
        self.speed_scale = self.rng.uniform(*self.stats.get('speed_jitter', (1.0, 1.0)))
        self.stagger_timer = self.rng.uniform(2.0, 4.0)
        self.machine = Machine(
            model=self,
            states=['IDLE', 'CHASE', 'ATTACK', 'HIT', 'DEAD'],
            transitions=[
                {'trigger': 'see', 'source': 'IDLE', 'dest': 'CHASE'},
                {'trigger': 'engage', 'source': ['IDLE', 'CHASE'], 'dest': 'ATTACK', 'after': 'on_attack_start'},
                {'trigger': 'recover', 'source': 'ATTACK', 'dest': 'CHASE', 'after': 'on_attack_end'},
                {'trigger': 'hurt', 'source': ['IDLE', 'CHASE', 'ATTACK', 'HIT'], 'dest': 'HIT'},
                {'trigger': 'recover_hit', 'source': 'HIT', 'dest': 'CHASE'},
                {'trigger': 'die', 'source': '*', 'dest': 'DEAD'},
            ],
            initial='IDLE',
            ignore_invalid_triggers=True,
        )

    # ----- 조회 -----
    @property
    def center(self):
        return (self.x, self.y + self.hb_h / 2)

    def rect(self):
        hw = self.hb_w / 2
        return (self.x - hw, self.y, self.x + hw, self.y + self.hb_h)

    def distance_x(self):
        return abs(self.player.x - self.x)

    def _windup_time(self):
        return self.stats['windup'] * MOVES[self.move]['windup']

    def _active_time(self):
        a = MOVES[self.move]['active']
        return self.stats['attack_time'] if a is None else a

    # ----- 피해 -----
    def take_damage(self, damage, from_x=None):
        """피해를 받는다. 죽었으면 True."""
        if not self.alive:
            return False
        self.hp -= damage
        self.flash = config.ENEMY_HIT_FLASH
        if self.hp <= 0:
            self.alive = False
            self.die()
            self.player.shards += config.SHARDS_PER_KILL.get(self.kind, 1)
            assets.play_sound('enemy_die')
            effects.spawn('death-burst', *self.center, duration=0.45)   # 헤이즈 조각으로 흩어진다
            game_world.remove_object(self)
            return True
        assets.play_sound('enemy_hit')
        if self.stats.get('super_armor') and self.state == 'ATTACK':
            return False                                  # 간수는 공격 중에 맞아도 기술이 끊기지 않는다
        if from_x is not None:
            self.vx = config.ENEMY_KNOCKBACK * (1 if self.x >= from_x else -1)
        self.hit_left = 0.18
        self.hurt()
        return False

    # ----- 갱신 -----
    def update(self, dt):
        self.flash = max(0.0, self.flash - dt)
        self.cooldown = max(0.0, self.cooldown - dt)
        self.leap_cooldown = max(0.0, self.leap_cooldown - dt)
        self.hop_cooldown = max(0.0, self.hop_cooldown - dt)
        self.retreat_left = max(0.0, self.retreat_left - dt)
        if self.player.x != self.x and self.state in ('CHASE',):
            self.face_dir = 1 if self.player.x > self.x else -1

        before_x = self.x
        if self.state in ('CHASE', 'IDLE') and self.on_ground and self.vx != 0:
            self.walk_phase += abs(self.vx) * dt / self.stats.get('walk_px', config.ENEMY_WALK_FRAME_PX)
        elif self.state not in ('CHASE', 'IDLE'):
            self.walk_phase = 0.0
        getattr(self, '_do_' + self.state.lower())(dt)
        self.vy = max(self.vy - config.GRAVITY * dt, -config.MAX_FALL_SPEED)
        self.move_with_tiles(dt)
        # 걸어가려는데 거의 못 움직였으면 막힌 것이다 (기둥, 벽)
        if self.state == 'CHASE' and self.vx != 0 and abs(self.x - before_x) < 0.5 and self.on_ground:
            self.blocked_time += dt
        else:
            self.blocked_time = 0.0

    def _player_alive(self):
        return self.player.state != 'DEAD'

    def _speed(self):
        return self.stats['speed'] * self.speed_scale

    # ----- 대기: 제자리 주변 순찰 -----
    def _do_idle(self, dt):
        s = self.stats
        self.vx = 0.0
        if self._player_alive() and self.distance_x() <= s['sight'] and abs(self.player.y - self.y) < s['sight_dy']:
            self.see()
            return
        patrol = s.get('patrol', 0)
        if patrol <= 0 or not self.on_ground:
            return
        if self.patrol_wait > 0:                          # 끝에 닿으면 잠깐 서서 두리번거린다
            self.patrol_wait -= dt
            return
        self.face_dir = self.patrol_dir
        out = (self.x - self.home_x) * self.patrol_dir > patrol
        wall = self.room.tile_at_world(self.x + self.patrol_dir * (self.hb_w / 2 + 6), self.y + 20) == room_module.SOLID
        if out or wall or not self._floor_ahead():
            self.patrol_dir *= -1
            self.patrol_wait = self.rng.uniform(0.5, 1.2)
            return
        self.vx = self.patrol_dir * self._speed() * 0.35

    # ----- 추적: 종류마다 다르게 움직인다 -----
    def _do_chase(self, dt):
        s = self.stats
        if not self._player_alive():
            self.vx = 0.0
            return
        dy = self.player.y - self.y
        d = self.distance_x()
        if self.cooldown <= 0 and self.on_ground and self.retreat_left <= 0:
            move = self._pick_move(d, dy)
            if move:
                self.move = move
                self.vx = 0.0
                self.engage()
                return
        if self.retreat_left > 0 and self.on_ground:      # 치고 빠지기: 등 뒤로 물러난다 (낭떠러지면 멈춘다)
            self.vx = -self.face_dir * self._speed() * 0.75 if self._floor_behind() else 0.0
            return
        if s.get('keep_away') and d < s['keep_away'] and abs(dy) < 120:   # 투척병: 너무 가까우면 뒤로 뛴다
            if self.on_ground and self.hop_cooldown <= 0 and self._floor_behind(far=True):
                self.vy, self.vx = 560.0, -self.face_dir * 330.0
                self.hop_cooldown = 1.6
                effects.spawn('puff', self.x, self.y + 10, duration=0.3)
            elif self.on_ground:
                self.vx = 0.0
            return
        if self._speed() <= 0:                            # 고정형(투척병)은 제자리에서 기다린다
            self.vx = 0.0 if self.on_ground else self.vx
            return
        in_range = d <= s['attack_range'] and abs(dy) < s['reach_dy']
        if in_range:                                      # 사거리 안이면 멈춰서 공격 차례를 기다린다
            self.vx = 0.0
            return
        if s.get('stagger') and self.on_ground:           # 슬럼: 가끔 비틀거리며 멈춘다
            if self.pause_left > 0:
                self.pause_left -= dt
                self.vx = 0.0
                return
            self.stagger_timer -= dt
            if self.stagger_timer <= 0:
                self.stagger_timer = self.rng.uniform(2.2, 4.5)
                self.pause_left = self.rng.uniform(0.25, 0.5)
        # 위층의 플레이어를 쫓거나 기둥에 막히면 뛰어오른다
        if self.on_ground and self.leap_cooldown <= 0 and s['leap'] > 0 and (
                (dy > 90 and d < 360) or (self.blocked_time > 0.2 and dy > -40)):
            self.vy = s['leap']
            self.leap_cooldown = config.LEAP_COOLDOWN
        speed = self._speed()
        if not self.on_ground:
            self.vx = self.face_dir * speed * 1.4          # 공중에서는 조금 더 멀리 날아가 발판에 닿는다
        elif self._floor_ahead() or dy < -100:
            self.vx = self.face_dir * speed
        else:
            self.vx = 0.0
        self.vx += self._separation()

    def _pick_move(self, d, dy):
        """거리에 맞는 기술 하나를 가중치로 고른다. 첫 공격은 기본기(목록의 첫 기술)."""
        s = self.stats
        if abs(dy) >= s['reach_dy']:
            return None
        moves = s.get('moves', [('swing', 1)])
        ok = []
        for name, weight in moves:
            m = MOVES[name]
            reach = s['attack_range'] if m['range'] is None else m['range']
            if m['gap'] < d <= reach or (m['gap'] == 0 and d <= reach):
                ok.append((name, weight))
        if self.attacks == 0:                             # 첫 공격은 기본기만: 처음 보는 적도 읽을 수 있다
            ok = [(n, w) for n, w in ok if n == moves[0][0]]
        if not ok:
            return None
        total = sum(w for _, w in ok)
        r = self.rng.uniform(0, total)
        for name, weight in ok:
            r -= weight
            if r <= 0:
                return name
        return ok[-1][0]

    def _separation(self):
        """같은 층에서 바로 옆에 붙은 다른 적에게서 조금 떨어진다 (한 자리에 겹쳐 서지 않게)."""
        push = 0.0
        for o in game_world.world[game_world.LAYER_ENEMY]:
            if o is self or not getattr(o, 'alive', False) or not isinstance(o, Enemy):
                continue
            dx = self.x - o.x
            if abs(dx) < 50 and abs(o.y - self.y) < 40:
                push += (1 if dx >= 0 else -1) * 70.0
        return push

    def _floor_ahead(self, direction=None):
        direction = direction or self.face_dir
        ahead_x = self.x + direction * (self.hb_w / 2 + 6)
        if self.room.tile_at_world(ahead_x, self.y + 6) == room_module.SPIKE:  # 가시로는 걸어 들어가지 않는다
            return False
        below = self.room.tile_at_world(ahead_x, self.y - 4)
        return below in (room_module.SOLID, room_module.ONEWAY)

    def _floor_behind(self, far=False):
        if not far:
            return self._floor_ahead(-self.face_dir)
        x = self.x - self.face_dir * (self.hb_w / 2 + 100)
        return (self.room.tile_at_world(x, self.y - 4) in (room_module.SOLID, room_module.ONEWAY)
                and self.room.tile_at_world(x, self.y + 30) != room_module.SOLID)

    # ----- 공격 -----
    def on_attack_start(self):
        self.attack_time = 0.0
        self.struck = False
        self.hits_done = 0
        self.contact_hit = False
        self.vx = 0.0
        if self.player.x != self.x:
            self.face_dir = 1 if self.player.x > self.x else -1

    def on_attack_end(self):
        self.attacks += 1
        self.retreat_left = self.stats.get('retreat', 0.0)

    def _do_attack(self, dt):
        s = self.stats
        self.attack_time += dt
        windup, active = self._windup_time(), self._active_time()
        t = self.attack_time
        if t < windup:
            if self.on_ground:
                self.vx = 0.0
            return
        getattr(self, '_move_' + self.move)(t - windup)
        if self.attack_time >= windup + active and (self.on_ground or self.attack_time > windup + active + 1.0):
            self.vx = 0.0
            self.cooldown = s['cooldown'] * self.rng.uniform(0.85, 1.2)
            self.recover()

    # 기술마다 예고가 끝난 뒤 시간(after)으로 움직인다
    def _move_swing(self, after):
        self.vx = 0.0
        if not self.struck:
            self.struck = True
            self._melee()

    _move_bite = _move_swing

    def _move_combo(self, after):
        self.vx = 0.0
        if self.hits_done == 0:
            self.struck = True
            self.hits_done = 1
            self._melee()
        elif self.hits_done == 1 and after >= COMBO_GAP:
            self.hits_done = 2
            self._melee()

    def _move_lunge(self, after):
        """달려들며 치기: 한 걸음 크게 내딛고 그 끝에서 친다."""
        if after < 0.18:
            self.vx = self.face_dir * self.stats.get('lunge_speed', 520.0)
        else:
            self.vx *= 0.8
            if not self.struck:
                self.struck = True
                self._melee()

    def _move_pounce(self, after):
        """덮치기: 플레이어 쪽으로 낮게 뛰어들고, 날아가는 동안 몸이 닿으면 피해."""
        if not self.struck:
            self.struck = True
            dx = self.player.x - self.x
            self.vy = POUNCE_VY
            air = 2 * POUNCE_VY / config.GRAVITY               # 같은 높이에 떨어질 때까지의 체공 시간
            self.vx = max(-POUNCE_MAX_VX, min(POUNCE_MAX_VX, dx / air))
            assets.play_sound('dash')
            return
        if not self.on_ground:
            self._contact(self.stats['damage'])
        elif after > 0.1:
            self.vx = 0.0

    def _move_heavy(self, after):
        """내려찍기: 큰 한 방과 양옆으로 짧게 퍼지는 충격파."""
        self.vx = 0.0
        if not self.struck:
            self.struck = True
            self._melee(extra=35)
            effects.add_trauma(0.35)
            effects.spawn('quake-blast', self.x + self.face_dir * 60, self.y, duration=0.4)
            for d in (-1, 1):
                game_world.add_object(
                    projectile.Shockwave(self.x + d * 50, self.y, d, 430.0, self.stats.get('wave_damage', 8), 0,
                                         self.room, self.player, life=0.55), game_world.LAYER_EFFECT)

    def _move_bash(self, after):
        """방패 돌진: 앞으로 짧게 달려 부딪친다. 벽이나 낭떠러지에서 멈춘다."""
        if not self.struck:
            self.struck = True
            assets.play_sound('dash')
        if after < self._active_time() - 0.1 and self._floor_ahead():
            self.vx = self.face_dir * self.stats.get('bash_speed', 640.0)
            self._contact(self.stats['damage'])
        else:
            self.vx = 0.0

    def _move_throw(self, after):
        self.vx = 0.0
        if not self.struck:
            self.struck = True
            self._throw_scrap()

    def _move_volley(self, after):
        self.vx = 0.0
        while self.hits_done < 3 and after >= self.hits_done * VOLLEY_GAP:
            self.struck = True
            self.hits_done += 1
            self._throw_scrap()

    def _move_lob(self, after):
        """포물선으로 던지기: 플레이어가 서 있는 자리에 떨어지도록 높이 던진다 (낮은 엄폐물 너머로 넘어온다)."""
        self.vx = 0.0
        if self.struck:
            return
        self.struck = True
        assets.play_sound('throw')
        sx, sy = self.x + self.face_dir * 30, self.y + self.hb_h * 0.8
        px, py = self.player.center
        t = projectile.LOB_TIME
        g = projectile.LOB_GRAVITY
        game_world.add_object(projectile.Lob(sx, sy, (px - sx) / t, (py - sy + 0.5 * g * t * t) / t,
                                             self.stats['damage'], self.room, self.player), game_world.LAYER_EFFECT)

    def _throw_scrap(self):
        s = self.stats
        assets.play_sound('throw')
        game_world.add_object(
            projectile.Scrap(self.x + self.face_dir * 30, self.y + self.hb_h * 0.62, self.face_dir,
                             s['projectile_speed'], s['damage'], self.room, self.player),
            game_world.LAYER_EFFECT)

    def _melee(self, extra=0):
        """앞쪽 박스가 플레이어와 겹치면 맞는다."""
        s = self.stats
        reach_x0 = self.x + self.face_dir * self.hb_w / 2
        reach_x1 = reach_x0 + self.face_dir * (s['attack_range'] - self.hb_w / 2 + 25 + extra)
        box = (min(reach_x0, reach_x1), self.y, max(reach_x0, reach_x1), self.y + self.hb_h)
        effects.spawn('hit-normal', (reach_x0 + reach_x1) / 2, self.y + self.hb_h * 0.55,
                      flip=self.face_dir < 0, duration=0.2)
        if self._player_alive() and projectile.overlap(box, self.player.rect()):
            self.player.take_hit(s['damage'], gauge_delta=s['gain_on_hit'])

    def _contact(self, damage):
        """몸통 박치기: 이번 기술에서 한 번만 맞힌다."""
        if self.contact_hit or not self._player_alive():
            return
        if projectile.overlap(self.rect(), self.player.rect()):
            self.contact_hit = True
            self.player.take_hit(damage, gauge_delta=self.stats['gain_on_hit'])

    def _strike(self):
        """기본 타격 (보스의 휘두르기도 이것을 쓴다)."""
        self._melee()

    def _do_hit(self, dt):
        self.hit_left -= dt
        self.vx *= max(0.0, 1.0 - 9.0 * dt)  # 밀려나다 멈춘다
        if self.hit_left <= 0:
            self.vx = 0.0
            self.recover_hit()

    def _do_dead(self, dt):
        self.vx = 0.0

    # ----- 그리기 -----
    def _body_frame(self):
        """지금 상태에 맞는 동작 프레임 (접두어, 번호). 해당 동작 그림이 없는 적이나 상태는 (None, 0) = 대기 그림 한 장."""
        frames = self.stats.get('frames', {})
        if self.state == 'HIT' and 'hurt' in frames:
            return frames['hurt'], 1
        if self.state == 'ATTACK' and 'attack' in frames:
            name = frames.get(self.move, frames['attack'])     # 기술 전용 그림이 있으면 그것 (간수 내려찍기·방패 돌진, 사냥개 덮치기)
            return name, min(self._attack_frame(), sprites.count(name))
        moving = self.state in ('CHASE', 'IDLE') and self.on_ground and self.vx != 0
        if moving and 'walk' in frames:
            count = sprites.count(frames['walk'])
            return frames['walk'], int(self.walk_phase) % count + 1
        return None, 0

    def _attack_frame(self):
        """공격 동작의 프레임 번호. 1 예고(당김), 2 타격, 3 회수. 두 장짜리(덮치기·돌진)는 1 웅크림, 2 뛰어듦."""
        t = self.attack_time
        windup = self._windup_time()
        if t < windup:
            return 1                                            # 예고: 팔을 뒤로 뺀다
        after = t - windup
        if self.move == 'pounce':
            return 2 if not self.on_ground else 1               # 나는 동안 앞발을 뻗고, 내려앉으면 다시 웅크린다
        if self.move == 'bash':
            return 2
        if self.move == 'combo':                                # 두 번 치기: 타격 -> 다시 당김 -> 타격
            if after < COMBO_GAP * 0.55:
                return 2
            if after < COMBO_GAP:
                return 1
            return 2 if after < COMBO_GAP + 0.12 else 3
        if self.move == 'volley':
            k = after % VOLLEY_GAP
            return 2 if k < VOLLEY_GAP * 0.6 and after < VOLLEY_GAP * 3 else 3
        if self.move == 'lunge' and after < 0.18:
            return 1                                            # 내딛는 동안은 당긴 채로
        return 2 if after < self._active_time() * 0.6 else 3

    def _pose_offset(self, name):
        """그림 한 장으로 움직이는 적(걷기 그림 없음)에게 주는 몸짓: 걸을 때 출렁임, 예고 때 몸을 뒤로 젖힘, 타격 때 앞으로."""
        dx = dy = 0
        if self.state == 'ATTACK':
            windup = self._windup_time()
            if self.attack_time < windup:
                k = min(1.0, self.attack_time / max(windup, 0.01))
                dx = -int(round(5 * k))                         # 예고: 점점 뒤로 젖힌다
                if name is None:
                    dy = int(round(2 * k))
            elif self.attack_time < windup + 0.1:
                dx = 6                                           # 타격 순간 앞으로
        elif name is None and self.state in ('CHASE', 'IDLE') and self.on_ground and self.vx != 0:
            dy = int(round(abs(math.sin(self.walk_phase * math.pi)) * 4))   # 걸음마다 몸이 출렁인다
        return dx * self.face_dir, dy

    def _tint(self):
        if self.flash > 0:
            return (255, 90, 90)                          # 맞은 순간 붉게
        if self.state == 'ATTACK' and self.attack_time < self._windup_time() and int(self.attack_time * 20) % 2 == 0:
            return (255, 225, 120)                        # 공격 직전 깜빡임(예고)
        return None

    def draw(self):
        name, n = self._body_frame()
        dx, dy = self._pose_offset(name)
        if name is None:                                  # 동작 그림이 없으면 정지 그림 한 장
            name = self.stats['sprite']
        sprites.draw(name, n, self.x + dx, self.y + dy, self.face_dir, self._tint())
        if self.hp < self.max_hp:
            self._draw_hp_bar()
        if config.DEBUG:
            from pico2d import draw_rectangle
            left, bottom, right, top = self.rect()
            draw_rectangle(left, bottom, right, top, 255, 160, 0)
            assets.draw_text(self.x, top + 27, f'{self.kind} {self.state} {self.move} {int(self.hp)}', (255, 200, 120),
                             small=True, center=True)

    def _draw_hp_bar(self):
        w, h = 96, 12
        left = self.x - w / 2
        bottom = self.y + self.hb_h + 14
        assets.draw_rect_image(assets.image('placeholder/px_black.png'), left - 3, bottom - 3, w + 6, h + 6)
        assets.draw_rect_image(assets.image('placeholder/px_gray.png'), left, bottom, w, h)
        assets.draw_rect_image(assets.image('placeholder/px_red.png'), left, bottom, w * max(0.0, self.hp) / self.max_hp, h)
