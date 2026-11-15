"""적. 상태 머신(IDLE -> CHASE -> ATTACK -> HIT/DEAD)을 transitions로 돌린다.

종류는 config.ENEMY_STATS의 수치로 갈린다. 슬럼 폐인은 쫓아와서 휘두르는 근접형,
고철 투척병은 제자리에서 고철을 던지는 원거리형이다.
"""
from transitions import Machine

import assets
import config
import effects
import game_world
import projectile
import room as room_module
from body import TileBody


class Enemy(TileBody):
    def __init__(self, kind, x, y, room, player):
        self.kind = kind
        self.stats = config.ENEMY_STATS[kind]
        self.hb_w, self.hb_h = self.stats['hb']
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.room, self.player = room, player
        self.hp = self.max_hp = self.stats['hp']
        self.face_dir = -1
        self.alive = True
        self.flash = 0.0           # 맞은 뒤 붉게 번쩍이는 남은 시간
        self.attack_time = 0.0     # ATTACK 상태에 들어온 뒤 지난 시간
        self.struck = False        # 이번 공격의 타격을 이미 냈는가
        self.cooldown = 0.0
        self.hit_left = 0.0
        self.leap_cooldown = 0.0   # 도약 재사용 대기
        self.blocked_time = 0.0    # 가려는데 앞이 막혀 있던 시간 (벽·기둥에 막힘 감지)
        self.machine = Machine(
            model=self,
            states=['IDLE', 'CHASE', 'ATTACK', 'HIT', 'DEAD'],
            transitions=[
                {'trigger': 'see', 'source': 'IDLE', 'dest': 'CHASE'},
                {'trigger': 'engage', 'source': ['IDLE', 'CHASE'], 'dest': 'ATTACK', 'after': 'on_attack_start'},
                {'trigger': 'recover', 'source': 'ATTACK', 'dest': 'CHASE'},
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
            effects.spawn('poof', self.x, self.y + 8, duration=0.5)
            game_world.remove_object(self)
            return True
        assets.play_sound('enemy_hit')
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
        if self.player.x != self.x and self.state not in ('ATTACK', 'HIT'):
            self.face_dir = 1 if self.player.x > self.x else -1

        before_x = self.x
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

    def _do_idle(self, dt):
        self.vx = 0.0
        s = self.stats
        if self._player_alive() and self.distance_x() <= s['sight'] and abs(self.player.y - self.y) < s['sight_dy']:
            self.see()

    def _do_chase(self, dt):
        s = self.stats
        if not self._player_alive():
            self.vx = 0.0
            return
        dy = self.player.y - self.y
        in_range = self.distance_x() <= s['attack_range'] and abs(dy) < s['reach_dy']
        if in_range and self.cooldown <= 0 and self.on_ground:
            self.vx = 0.0
            self.engage()
            return
        if s['speed'] <= 0:                          # 고정형(투척병)은 제자리에서 기다린다
            self.vx = 0.0
            return
        if in_range:                                 # 사거리 안이면 멈춰서 공격 차례를 기다린다
            self.vx = 0.0
            return
        # 위층의 플레이어를 쫓거나 기둥에 막히면 뛰어오른다
        if self.on_ground and self.leap_cooldown <= 0 and s['leap'] > 0 and (
                (dy > 90 and self.distance_x() < 360) or (self.blocked_time > 0.2 and dy > -40)):
            self.vy = s['leap']
            self.leap_cooldown = config.LEAP_COOLDOWN
        # 아래층의 플레이어를 쫓을 때는 낭떠러지도 걸어서 내려간다
        if not self.on_ground:
            self.vx = self.face_dir * s['speed'] * 1.4          # 공중에서는 조금 더 멀리 날아가 발판에 닿는다
        elif self._floor_ahead() or dy < -100:
            self.vx = self.face_dir * s['speed']
        else:
            self.vx = 0.0

    def _floor_ahead(self):
        ahead_x = self.x + self.face_dir * (self.hb_w / 2 + 6)
        if self.room.tile_at_world(ahead_x, self.y + 6) == room_module.SPIKE:  # 가시로는 걸어 들어가지 않는다
            return False
        below = self.room.tile_at_world(ahead_x, self.y - 4)
        return below in (room_module.SOLID, room_module.ONEWAY)

    def on_attack_start(self):
        self.attack_time = 0.0
        self.struck = False
        self.vx = 0.0

    def _do_attack(self, dt):
        s = self.stats
        self.vx = 0.0
        self.attack_time += dt
        if not self.struck and self.attack_time >= s['windup']:
            self.struck = True
            self._strike()
        if self.attack_time >= s['windup'] + s['attack_time']:
            self.cooldown = s['cooldown']
            self.recover()

    def _strike(self):
        """윈드업이 끝난 순간의 타격. 종류별로 다르다."""
        s = self.stats
        if self.kind == 'thrower':
            assets.play_sound('throw')
            game_world.add_object(
                projectile.Scrap(self.x + self.face_dir * 30, self.y + self.hb_h * 0.62, self.face_dir,
                                 s['projectile_speed'], s['damage'], self.room, self.player),
                game_world.LAYER_EFFECT)
            return
        # 근접: 앞쪽 박스가 플레이어와 겹치면 맞는다
        reach_x0 = self.x + self.face_dir * self.hb_w / 2
        reach_x1 = reach_x0 + self.face_dir * (s['attack_range'] - self.hb_w / 2 + 25)
        box = (min(reach_x0, reach_x1), self.y, max(reach_x0, reach_x1), self.y + self.hb_h)
        effects.spawn('hit-spark', (reach_x0 + reach_x1) / 2, self.y + self.hb_h * 0.55,
                      flip=self.face_dir < 0, duration=0.2)
        if self._player_alive() and projectile.overlap(box, self.player.rect()):
            self.player.take_hit(s['damage'], gauge_delta=s['gain_on_hit'])

    def _do_hit(self, dt):
        self.hit_left -= dt
        self.vx *= max(0.0, 1.0 - 9.0 * dt)  # 밀려나다 멈춘다
        if self.hit_left <= 0:
            self.vx = 0.0
            self.recover_hit()

    def _do_dead(self, dt):
        self.vx = 0.0

    # ----- 그리기 -----
    def draw(self):
        img = assets.image('sprites/unified/' + self.stats['sprite'])
        flip = 'h' if self.face_dir < 0 else ''
        y = self.y - config.SPRITE_FOOT_MARGIN
        if self.flash > 0:
            assets.draw_image_tinted(img, self.x, y, flip, (255, 90, 90), 1.0)
        elif self.state == 'ATTACK' and not self.struck and int(self.attack_time * 20) % 2 == 0:
            assets.draw_image_tinted(img, self.x, y, flip, (255, 225, 120), 1.0)  # 공격 직전 깜빡임(예고)
        else:
            assets.draw_image(img, self.x, y, flip)
        if self.hp < self.max_hp:
            self._draw_hp_bar()
        if config.DEBUG:
            from pico2d import draw_rectangle
            left, bottom, right, top = self.rect()
            draw_rectangle(left, bottom, right, top, 255, 160, 0)
            assets.draw_text(self.x, top + 27, f'{self.kind} {self.state} {int(self.hp)}', (255, 200, 120),
                             small=True, center=True)

    def _draw_hp_bar(self):
        w, h = 96, 12
        left = self.x - w / 2
        bottom = self.y + self.hb_h + 14
        assets.draw_rect_image(assets.image('placeholder/px_black.png'), left - 3, bottom - 3, w + 6, h + 6)
        assets.draw_rect_image(assets.image('placeholder/px_gray.png'), left, bottom, w, h)
        assets.draw_rect_image(assets.image('placeholder/px_red.png'), left, bottom, w * max(0.0, self.hp) / self.max_hp, h)
