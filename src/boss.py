"""보스 크래셔. 일반 적과 같은 몸(Enemy)에 패턴 세 개를 얹었다. 맞아도 경직되지 않는다(슈퍼 아머).

패턴(기획 3.2 표): 내려찍기 충격파(맞으면 게이지 -20%), 돌진(게이지 변화 없음), 가까이 오면 휘두르기, 도약 내려찍기.
순서는 거리와 횟수로 정해 예측할 수 있다: 멀면 돌진, 보통은 충격파, 가까우면 휘두르기, 4번째마다 도약. 공격 직전에는 노랗게 깜빡여 예고한다.
**플레이어가 기둥·벽 뒤에 숨어 보스에게 닿지 않으면(시야선이 막히면) 보스는 위로 도약해 벽을 넘어 내려찍는다.**
숨어서 일방적으로 때리는 전략을 막는다 (플레이어의 근접 공격도 벽 너머에는 닿지 않는다, weapon.py 시야선).
"""
import assets
import config
import effects
import game_world
import projectile
from enemy import Enemy

# 패턴 -> (예고 시간, 공격이 이어지는 시간) 의 키. 수치는 config.ENEMY_STATS['crasher']
PATTERNS = ('smash', 'slam', 'charge', 'leap')


class Boss(Enemy):
    def __init__(self, x, y, room, player):
        super().__init__('crasher', x, y, room, player)
        self.pattern = 'slam'
        self.count = 0              # 지금까지 쓴 패턴 수
        self.charging = False
        self.charge_hit = False
        self.leaping = False        # 도약 중인가
        self.air_seen = False       # 도약 뒤 땅에서 떨어진 것을 한 번 봤는가 (착지 판정용)

    # ----- 패턴 고르기 -----
    def _choose_pattern(self):
        d = self.distance_x()
        cx, cy = self.center
        px, py = self.player.center
        if self.room.line_blocked(cx, cy, px, py):      # 벽·기둥 뒤에 숨었다: 넘어가서 내려찍는다
            return 'leap'
        if d < self.stats['attack_range']:
            return 'smash'
        if d > 520 and self.count % 2 == 0:
            return 'charge'
        if self.count % 4 == 3:
            return 'leap'
        return 'slam'

    def _windup(self):
        s = self.stats
        return {'smash': s['windup'], 'slam': s['windup'] * 1.8, 'charge': s['windup'] * 1.6, 'leap': s['windup'] * 1.5}[self.pattern]

    def _active(self):
        s = self.stats
        return {'smash': s['attack_time'], 'slam': 0.35, 'charge': s['charge_time'], 'leap': 0.0}[self.pattern]

    # ----- 상태 -----
    def _do_chase(self, dt):
        s = self.stats
        if not self._player_alive():
            self.vx = 0.0
            return
        if self.cooldown <= 0 and self.on_ground:
            self.pattern = self._choose_pattern()
            self.count += 1
            self.vx = 0.0
            self.engage()
            return
        # 패턴 사이에는 천천히 다가간다
        self.vx = self.face_dir * s['speed'] if self.distance_x() > 140 else 0.0

    def _do_attack(self, dt):
        s = self.stats
        self.attack_time += dt
        windup, active = self._windup(), self._active()
        if self.attack_time < windup:
            self.vx = 0.0                      # 예고 중에는 선 채로 노란 깜빡임
            return
        if self.pattern == 'leap':
            self._leap_step()
            return
        if not self.struck:
            self.struck = True
            self._begin_active()
        if self.pattern == 'charge':
            self._charge_step()
        else:
            self.vx = 0.0
        if self.attack_time >= windup + active:
            self.charging = False
            self.vx = 0.0
            self.cooldown = s['cooldown'] * (1.4 if self.pattern == 'charge' else 1.0)
            self.recover()

    def _begin_active(self):
        s = self.stats
        if self.pattern == 'smash':
            Enemy._strike(self)                # 앞쪽 휘두르기 (일반 적과 같은 판정)
        elif self.pattern == 'slam':
            assets.play_sound('overload')
            effects.add_trauma(0.7)
            effects.spawn('plasma-explosion', self.x, self.y + 20, duration=0.5)
            for d in (-1, 1):                  # 좌우로 바닥 충격파
                game_world.add_object(
                    projectile.Shockwave(self.x + d * 70, self.y, d, s['wave_speed'], s['wave_damage'], s['wave_gauge'],
                                         self.room, self.player), game_world.LAYER_EFFECT)
        else:
            self.charging, self.charge_hit = True, False
            assets.play_sound('dash')

    def _leap_step(self):
        """도약 내려찍기: 예고 뒤 플레이어 쪽으로 높이 뛰어올라 벽·기둥을 넘고, 착지하면 충격이 퍼진다."""
        if not self.struck:
            self.struck = True
            self.leaping, self.air_seen = True, False
            t = config.BOSS_LEAP_TIME
            self.vy = config.GRAVITY * t / 2                     # 체공 시간 t에 맞는 위로 던지는 속도
            dx = self.player.x - self.x
            self.vx = max(-config.BOSS_LEAP_SPEED_CAP, min(config.BOSS_LEAP_SPEED_CAP, dx / t))
            assets.play_sound('dash')
            return
        if not self.on_ground:
            self.air_seen = True                               # 공중: 날아가는 속도를 그대로 둔다
            return
        if self.air_seen or self.attack_time > self._windup() + config.BOSS_LEAP_TIME + 0.4:
            self._land()

    def _land(self):
        s = self.stats
        self.vx = 0.0
        self.leaping = False
        assets.play_sound('overload')
        effects.add_trauma(0.8)
        effects.spawn('plasma-explosion', self.x, self.y + 20, duration=0.5)
        for d in (-1, 1):
            game_world.add_object(
                projectile.Shockwave(self.x + d * 70, self.y, d, s['wave_speed'], s['wave_damage'], s['wave_gauge'],
                                     self.room, self.player), game_world.LAYER_EFFECT)
        px, py = self.player.center
        cx, cy = self.center
        if self._player_alive() and abs(px - cx) <= config.BOSS_LAND_RADIUS and abs(py - cy) <= config.BOSS_LAND_RADIUS:
            self.player.take_hit(config.BOSS_LAND_DAMAGE, gauge_delta=s['wave_gauge'])    # 바로 밑에 있으면 직격
        self.cooldown = s['cooldown'] * 1.3
        self.recover()

    def _charge_step(self):
        s = self.stats
        self.vx = self.face_dir * s['charge_speed']
        if not self.charge_hit and projectile.overlap(self.rect(), self.player.rect()) and self._player_alive():
            self.charge_hit = True
            self.player.take_hit(s['charge_damage'])
        if self.blocked_time_charge():
            self.attack_time = 99.0            # 벽에 부딪히면 돌진 끝

    def blocked_time_charge(self):
        ahead = self.x + self.face_dir * (self.hb_w / 2 + 8)
        return self.room.tile_at_world(ahead, self.y + 40) == '#'

    # ----- 피해: 경직 없음 -----
    def take_damage(self, damage, from_x=None):
        if not self.alive:
            return False
        self.hp -= damage
        self.flash = config.ENEMY_HIT_FLASH
        if self.hp <= 0:
            self.alive = False
            self.die()
            assets.play_sound('enemy_die')
            self.player.shards += config.SHARDS_PER_KILL.get(self.kind, 1)
            effects.add_trauma(1.0)
            for dx, dy in ((0, 40), (-50, 100), (50, 150)):
                effects.spawn('plasma-explosion', self.x + dx, self.y + dy, duration=0.6)
            game_world.remove_object(self)
            return True
        assets.play_sound('enemy_hit')
        return False

    def _draw_hp_bar(self):
        pass                                   # 보스 체력은 화면 위 큰 바(UI)로 보여 준다
