"""보스 크래셔. 일반 적과 같은 몸(Enemy)에 패턴 여러 개를 얹었다. 맞아도 경직되지 않는다(슈퍼 아머).

패턴(기획 3.2 표가 바탕): 휘두르기, 세 번 내리치기(한 걸음씩 다가오며), 내려찍기 충격파(맞으면 게이지 -20% = 기본 -5 + 추가 -15), 돌진,
도약 내려찍기, 발 구르기(천장에서 고철이 떨어진다: 떨어질 자리에 노란 표시가 먼저 깜빡인다, HP 피해만),
헤이즈 증기 분출(바닥에 청록 표시 뒤 증기 기둥이 솟는다: 닿으면 게이지 +12%, 피해 없음).
게이지를 내리는 충격파와 올리는 증기가 섞여 게이지 유지를 어렵게 한다(기획의 '교란 패턴').
**2페이즈(체력 절반 이하)**: 포효하며 붉어지고, 공격 간격이 짧아지며 돌진은 되돌아 한 번 더, 충격파는 두 겹,
떨어지는 고철은 더 많아진다.

고르는 법: 거리에 맞는 패턴들 중 가중치로 고르되 **같은 패턴을 연달아 쓰지 않는다.** 모든 공격 직전에는 노랗게 깜빡여 예고한다.
패턴 사이에는 다가오거나, 너무 붙으면 뒤로 뛰어 물러나거나, 잠깐 멈춰 노려본다.
**플레이어가 기둥·벽 뒤에 숨어 보스에게 닿지 않으면(시야선이 막히면) 보스는 위로 도약해 벽을 넘어 내려찍는다.**
숨어서 일방적으로 때리는 전략을 막는다 (플레이어의 근접 공격도 벽 너머에는 닿지 않는다, weapon.py 시야선).
"""
import random

import assets
import config
import effects
import game_world
import projectile
from enemy import Enemy

PATTERNS = ('smash', 'combo', 'slam', 'charge', 'leap', 'rubble', 'steam')
# 거리별 후보와 가중치. 2페이즈에는 PHASE2_BONUS를 더한다
NEAR = {'smash': 3, 'combo': 3, 'slam': 1}
MID = {'slam': 3, 'rubble': 2, 'steam': 2, 'leap': 1, 'combo': 1}
FAR = {'charge': 3, 'rubble': 2, 'steam': 2, 'leap': 2, 'slam': 1}
COMBO_HITS = 3
COMBO_GAP = 0.38          # 세 번 내리치기 간격(초). 매번 한 걸음 다가온다
COMBO_STEP_SPEED = 420.0
QUAKE_DELAY = 0.45        # 2페이즈 충격파 두 번째 겹이 나가는 시각(첫 충격파 뒤 초)
RUBBLE_COUNT = (5, 7)     # 떨어지는 고철 수 (1페이즈, 2페이즈)
RUBBLE_SPACING = 170
RUBBLE_DAMAGE = 14
RUBBLE_GAUGE = 0          # 고철은 HP 피해만 (피격 기본 손실 -5는 그대로). 크래셔의 게이지 패턴은 충격파와 증기뿐
STEAM_COUNT = (2, 3)      # 증기 기둥 수 (1페이즈, 2페이즈)
STEAM_SPACING = 230
BACKSTEP_VX, BACKSTEP_VY = 460.0, 760.0


class Boss(Enemy):
    def __init__(self, x, y, room, player):
        super().__init__('crasher', x, y, room, player)
        self.pattern = 'slam'
        self.last_pattern = None
        self.count = 0              # 지금까지 쓴 패턴 수
        self.phase = 1
        self.charging = False
        self.charge_hit = False
        self.charges_left = 0       # 2페이즈 돌진: 되돌아 한 번 더
        self.leaping = False        # 도약 중인가
        self.air_seen = False       # 도약 뒤 땅에서 떨어진 것을 한 번 봤는가 (착지 판정용)
        self.anim_time = 0.0        # 대기 그림을 번갈아 보여 주는 시계
        self.land_left = 0.0        # 도약 착지 자세가 남은 시간
        self.backstep_cd = 0.0      # 뒤로 뛰기 재사용 대기
        self.stare_left = 0.0       # 패턴 사이 멈춰 노려보는 남은 시간
        self.roar_left = 0.0        # 2페이즈로 넘어가며 포효하는 남은 시간
        self.rng = random.Random(7)

    # ----- 패턴 고르기 -----
    def _choose_pattern(self):
        d = self.distance_x()
        cx, cy = self.center
        px, py = self.player.center
        if self.room.line_blocked(cx, cy, px, py):      # 벽·기둥 뒤에 숨었다: 넘어가서 내려찍는다
            return 'leap'
        table = NEAR if d < self.stats['attack_range'] else MID if d <= 520 else FAR
        options = {k: w for k, w in table.items() if k != self.last_pattern} or dict(table)
        if self.count == 0:                              # 첫 패턴은 늘 충격파: 보스가 무엇을 하는지 먼저 보여 준다
            return 'slam' if d >= self.stats['attack_range'] else 'smash'
        total = sum(options.values())
        r = self.rng.uniform(0, total)
        for name, weight in options.items():
            r -= weight
            if r <= 0:
                return name
        return name

    def _windup(self):
        s = self.stats
        mult = {'smash': 1.0, 'combo': 1.1, 'slam': 1.8, 'charge': 1.6, 'leap': 1.5, 'rubble': 1.4, 'steam': 1.3}[self.pattern]
        return s['windup'] * mult * (0.85 if self.phase == 2 else 1.0)

    def _active(self):
        s = self.stats
        return {'smash': s['attack_time'], 'combo': COMBO_GAP * (COMBO_HITS - 1) + 0.25,
                'slam': 0.35 + (QUAKE_DELAY if self.phase == 2 else 0.0), 'charge': s['charge_time'],
                'leap': 0.0, 'rubble': 0.55, 'steam': 0.55}[self.pattern]

    # 일반 적의 예고·깜빡임 계산이 보스 패턴 시간을 쓰게 한다
    def _windup_time(self):
        return self._windup()

    def _active_time(self):
        return self._active()

    # ----- 상태 -----
    def update(self, dt):
        self.backstep_cd = max(0.0, self.backstep_cd - dt)
        self.roar_left = max(0.0, self.roar_left - dt)
        super().update(dt)
        self.anim_time += dt
        self.land_left = max(0.0, self.land_left - dt)
        if self.phase == 1 and self.alive and self.hp <= self.max_hp / 2:
            self._enter_phase2()

    def _enter_phase2(self):
        """체력 절반: 포효하며 2페이즈로. 잠깐 멈춰 서서 화면이 흔들린다."""
        self.phase = 2
        self.roar_left = 0.9
        self.cooldown = max(self.cooldown, 1.0)
        assets.play_sound('overload')
        effects.add_trauma(0.8)
        effects.spawn('quake-blast', self.x, self.y, duration=0.6)
        effects.float_text(self.x, self.y + self.hb_h + 80, '분노', (255, 110, 90), big=True, life=1.0)

    def _do_chase(self, dt):
        s = self.stats
        if not self._player_alive() or self.roar_left > 0:
            self.vx = 0.0
            return
        if not self.on_ground:                            # 뒤로 뛰는 중: 날아가는 속도 그대로
            return
        if self.cooldown <= 0:
            self.pattern = self._choose_pattern()
            self.count += 1
            self.vx = 0.0
            self.engage()
            return
        d = self.distance_x()
        speed = s['speed'] * (1.3 if self.phase == 2 else 1.0)
        if self.stare_left > 0:                           # 잠깐 멈춰 노려본다
            self.stare_left -= dt
            self.vx = 0.0
            return
        if d < 170 and self.backstep_cd <= 0 and self.cooldown > 0.3 and self._floor_behind(far=True):
            self.vy, self.vx = BACKSTEP_VY, -self.face_dir * BACKSTEP_VX    # 너무 붙으면 뒤로 뛰어 거리를 벌린다
            self.backstep_cd = 3.5
            effects.spawn('puff', self.x, self.y + 10, duration=0.35)
            return
        if self.rng.random() < dt * 0.25:                 # 가끔 걸음을 멈추고 노려본다 (평균 4초에 한 번)
            self.stare_left = self.rng.uniform(0.3, 0.6)
        self.vx = self.face_dir * speed if d > 150 else 0.0

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
        after = self.attack_time - windup
        if not self.struck:
            self.struck = True
            self._begin_active()
        if self.pattern == 'charge':
            self._charge_step()
            if self.attack_time >= windup + active and self.charges_left > 1:
                self._turn_and_charge_again()
                return
        elif self.pattern == 'combo':
            self._combo_step(after)
        elif self.pattern == 'slam' and self.phase == 2 and self.hits_done == 1 and after >= QUAKE_DELAY:
            self.hits_done = 2
            self._shockwaves(speed_mult=1.35)            # 두 번째 겹: 더 빠르다
        else:
            self.vx = 0.0
        if self.attack_time >= windup + active:
            self.charging = False
            self.vx = 0.0
            self.last_pattern = self.pattern
            cd = s['cooldown'] * (1.4 if self.pattern == 'charge' else 1.0)
            self.cooldown = cd * (0.7 if self.phase == 2 else 1.0)
            self.recover()

    def _begin_active(self):
        s = self.stats
        if self.pattern == 'smash':
            self._melee()                      # 앞쪽 휘두르기 (일반 적과 같은 판정)
        elif self.pattern == 'combo':
            self.hits_done = 0
        elif self.pattern == 'slam':
            self.hits_done = 1
            assets.play_sound('overload')
            effects.add_trauma(0.7)
            effects.spawn('quake-blast', self.x, self.y, duration=0.5)
            self._shockwaves()
        elif self.pattern == 'rubble':
            self._stomp_rubble()
        elif self.pattern == 'steam':
            self._vent_steam()
        else:
            self.charging, self.charge_hit = True, False
            if self.charges_left == 0:
                self.charges_left = 2 if self.phase == 2 else 1
            assets.play_sound('dash')

    def _shockwaves(self, speed_mult=1.0):
        s = self.stats
        for d in (-1, 1):                  # 좌우로 바닥 충격파
            game_world.add_object(
                projectile.Shockwave(self.x + d * 70, self.y, d, s['wave_speed'] * speed_mult, s['wave_damage'],
                                     s['wave_gauge'], self.room, self.player), game_world.LAYER_EFFECT)

    def _combo_step(self, after):
        """세 번 내리치기: 매번 한 걸음 다가가 내리친다. 마지막 한 방이 가장 크다."""
        k = min(COMBO_HITS - 1, int(after / COMBO_GAP))
        local = after - k * COMBO_GAP
        if self.hits_done <= k:
            self.vx = self.face_dir * COMBO_STEP_SPEED if local < 0.1 and self._floor_ahead() else 0.0
            if local >= 0.1:
                self.hits_done = k + 1
                self._melee(extra=20 if k == COMBO_HITS - 1 else 0)
                effects.add_trauma(0.25 if k < COMBO_HITS - 1 else 0.5)
                assets.play_sound('hit')
        else:
            self.vx = 0.0

    def _stomp_rubble(self):
        """발 구르기: 플레이어가 선 자리와 그 양옆에 고철이 차례로 떨어진다. 바닥에 표시가 먼저 깜빡인다."""
        assets.play_sound('overload')
        effects.add_trauma(0.5)
        effects.spawn('quake-blast', self.x, self.y, duration=0.4)
        count = RUBBLE_COUNT[self.phase - 1]
        px = self.player.x
        offsets = [0]
        for i in range(1, count):
            offsets.append(((i + 1) // 2) * RUBBLE_SPACING * (1 if i % 2 else -1))
        for i, ox in enumerate(offsets):
            x = px + ox + self.rng.uniform(-25, 25)
            if not (60 <= x <= self.room.width - 60):
                continue
            floor = projectile.floor_below(self.room, x, self.player.y + 30)
            if floor is None:
                continue
            game_world.add_object(projectile.Debris(x, floor, 0.12 * i, RUBBLE_DAMAGE, RUBBLE_GAUGE,
                                                    self.room, self.player), game_world.LAYER_EFFECT)

    def _vent_steam(self):
        """헤이즈 증기 분출: 플레이어 자리와 옆에 증기 기둥이 솟는다 (2페이즈는 양옆까지 세 줄기)."""
        effects.add_trauma(0.3)
        effects.spawn('haze-blast', self.x, self.y + 60, duration=0.5)
        count = STEAM_COUNT[self.phase - 1]
        px = self.player.x
        side = 1 if self.rng.random() < 0.5 else -1
        offsets = [0, side * STEAM_SPACING, -side * STEAM_SPACING][:count]
        for i, ox in enumerate(offsets):
            x = min(max(px + ox, 60), self.room.width - 60)
            floor = projectile.floor_below(self.room, x, self.player.y + 30)
            if floor is None:
                continue
            game_world.add_object(projectile.SteamVent(x, floor, 0.1 * i, config.STEAM_GAUGE, self.room, self.player),
                                  game_world.LAYER_EFFECT)

    def _turn_and_charge_again(self):
        """2페이즈 돌진: 끝에서 돌아서서 짧게 예고하고 한 번 더 달린다."""
        self.charges_left -= 1
        self.charging = False
        self.vx = 0.0
        if self.player.x != self.x:
            self.face_dir = 1 if self.player.x > self.x else -1
        self.attack_time = self._windup() * 0.45         # 두 번째 돌진은 예고가 짧다
        self.struck = False

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
        effects.spawn('quake-blast', self.x, self.y, duration=0.5)
        self._shockwaves()
        px, py = self.player.center
        cx, cy = self.center
        if self._player_alive() and abs(px - cx) <= config.BOSS_LAND_RADIUS and abs(py - cy) <= config.BOSS_LAND_RADIUS:
            self.player.take_hit(config.BOSS_LAND_DAMAGE, gauge_delta=s['wave_gauge'])    # 바로 밑에 있으면 직격
        self.cooldown = s['cooldown'] * 1.3 * (0.7 if self.phase == 2 else 1.0)
        self.land_left = config.BOSS_LAND_POSE_TIME
        self.last_pattern = 'leap'
        self.recover()

    def _charge_step(self):
        s = self.stats
        self.vx = self.face_dir * s['charge_speed']
        if not self.charge_hit and projectile.overlap(self.rect(), self.player.rect()) and self._player_alive():
            self.charge_hit = True
            self.player.take_hit(s['charge_damage'])
        if self.blocked_time_charge():
            self.attack_time = max(self.attack_time, self._windup() + self._active())   # 벽에 부딪히면 이번 돌진 끝
            effects.add_trauma(0.4)

    def blocked_time_charge(self):
        ahead = self.x + self.face_dir * (self.hb_w / 2 + 8)
        return self.room.tile_at_world(ahead, self.y + 40) == '#'

    def on_attack_end(self):
        super().on_attack_end()
        self.charges_left = 0

    # ----- 그리기: 패턴마다 동작 그림이 다르다 -----
    def _body_frame(self):
        if self.state == 'ATTACK':
            t = self.attack_time
            windup, active = self._windup(), self._active()
            if self.pattern == 'combo':                          # 주먹을 들었다 내리치기를 세 번
                if t < windup:
                    return 'boss_crasher_smash', 1
                local = (t - windup) % COMBO_GAP
                return 'boss_crasher_smash', 1 if local < 0.1 else 2 if local < 0.22 else 3
            if self.pattern in ('smash', 'slam', 'rubble', 'steam'):     # 예고: 주먹을 머리 위로 -> 내려찍음 -> 주먹이 박힌 채 마무리
                if t < windup:
                    return 'boss_crasher_smash', 1
                return 'boss_crasher_smash', 2 if t < windup + active * 0.6 else 3
            if self.pattern == 'charge':                        # 예고: 몸을 숙임, 돌진: 두 발이 번갈아
                return 'boss_crasher_charge', 1 if t < windup else int(t * 10) % 2 + 1
            if t < windup:                                      # 도약: 웅크림 -> 공중 -> (착지는 land_left)
                return 'boss_crasher_leap', 1
            return 'boss_crasher_leap', 2
        if self.land_left > 0:
            return 'boss_crasher_leap', 3
        if self.roar_left > 0:                                  # 포효: 주먹을 쳐든다
            return 'boss_crasher_smash', 1
        if not self.on_ground and self.backstep_cd > 2.5:      # 방금 뒤로 뛰어 공중에 있다
            return 'boss_crasher_leap', 2
        if self.flash > 0:                                      # 공격 중이 아닐 때 맞으면 움찔 (경직은 없다)
            return 'boss_crasher_hurt', 1
        if self.vx != 0:                                        # 걸어온다: 숙인 자세의 두 발이 천천히 번갈아
            return 'boss_crasher_charge', int(self.walk_phase * 0.5) % 2 + 1
        return 'boss_crasher_idle', int(self.anim_time / config.BOSS_IDLE_FRAME_TIME) % 2 + 1

    def _pose_offset(self, name):
        return 0, 0                                             # 보스는 패턴마다 그림이 따로 있다

    def _tint(self):
        tint = super()._tint()
        if tint is None and self.phase == 2 and int(self.anim_time * 3) % 2 == 0:
            return (255, 175, 160)                              # 2페이즈: 붉게 달아오른다
        return tint

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
                effects.spawn('haze-blast', self.x + dx, self.y + dy, duration=0.6)
            game_world.remove_object(self)
            return True
        assets.play_sound('enemy_hit')
        return False

    def _draw_hp_bar(self):
        pass                                   # 보스 체력은 화면 위 큰 바(UI)로 보여 준다
