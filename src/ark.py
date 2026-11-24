"""최종 보스 총감시관 아크 (기획서 3.2, 스테이지 3). 일반 적과 같은 몸(Enemy)에 패턴 다섯 개를 얹었다. 경직 없음.

패턴 (게이지 수치는 맞았을 때 최종 변화):
- 헤이즈 탄막(barrage): 손바닥에서 청록 탄환을 부채꼴로 뿌린다. 탄환당 +5%.  예고: 손바닥을 가슴 앞에 모음
- 순간이동 베기(slash): 안개로 흩어졌다가 플레이어 등 뒤에 나타나 손날로 벤다. -10%.  예고: 낮게 웅크림 -> 손날을 당김
- 흡수 파동(absorb): 방 양끝에서 아크 쪽으로 낮은 파동이 조여 든다(점프로 넘는다). -25%.  예고: 팔을 활짝 벌림
- 과충전 파동(overcharge): 아크에서 바깥으로 파동이 퍼진다. +25%.  예고: 웅크려 팔을 교차
- 오염 장판(field): 플레이어 발밑에 장판이 깔린다. 위에 서 있으면 초당 +5%.  예고: 무릎 꿇고 손을 듦
흡수와 과충전은 **번갈아** 쓴다(게이지를 위아래로 크게 흔든다). 첫 파동은 플레이어 게이지가 높으면 과충전(오버로드로 민다), 낮으면 흡수.

페이즈: 1(체력 100~66%) 탄막·베기·장판 / 2(66~33%) 파동 추가 / 3(33% 아래) 예고 x0.8, 탄 더 많이, 베기 두 번, 과충전 두 겹, 장판 둘.
페이즈가 바뀌면 주먹을 들고 멈춰 선다(페이즈 자세). 패턴 사이에는 중간 거리를 유지하며 천천히 걷는다.
그림은 Codex T20(`boss_ark_*`), 탄환·파동·장판·손 빛은 projectile.py와 이 파일에서 코드로 그린다.
"""
import math
import random

import assets
import config
import effects
import game_world
import projectile
from enemy import Enemy

WINDUP = {'barrage': 0.6, 'absorb': 0.9, 'overcharge': 0.9, 'field': 0.7, 'bands': 0.8, 'crystals': 0.7}   # 베기는 사라짐 + 나타남 시간
ACTIVE = {'barrage': 0.35, 'slash': 0.35, 'absorb': 0.5, 'overcharge': 0.5, 'field': 0.4, 'bands': 0.4, 'crystals': 0.4}
OVERCHARGE_SECOND = 0.4       # 3페이즈 과충전 두 번째 겹이 나가는 시각(첫 겹 뒤 초)
# 페이즈별 패턴 가중치. 'wave'는 흡수·과충전 중 이번 차례인 쪽으로 바뀐다
TABLES = {1: {'barrage': 3, 'slash': 2, 'field': 2},
          2: {'barrage': 2, 'slash': 2, 'field': 1, 'wave': 3, 'bands': 2},
          3: {'barrage': 2, 'slash': 2, 'field': 1, 'wave': 3, 'bands': 2, 'crystals': 2}}
# 2·3페이즈 방 쓰기 (11/22 v5): bands = 짙은·맑은 농도 띠가 방을 가로지름, crystals = 플레이어 양옆에 결정 벽
GLOW = {'barrage': (90, 240, 230), 'slash': (220, 240, 255), 'absorb': (150, 100, 235),
        'overcharge': (255, 240, 150), 'field': (110, 235, 150),
        'bands': (190, 150, 250), 'crystals': (170, 230, 255)}      # 예고 중 손에 맺히는 빛 (패턴마다 색이 다르다)
# 전용 그림이 없는 패턴은 비슷한 자세를 빌린다 (2026-11-25 버그 훑기: 그림이 없어 2페이즈에 게임이 꺼졌다)
POSE = {'bands': 'field', 'crystals': 'overcharge'}
KEEP_FAR, KEEP_NEAR = 480, 220   # 패턴 사이 이 거리 사이를 유지한다(px)


class Ark(Enemy):
    title = '총감시관 아크'
    pullable = False               # 사슬에 맞아도 끌려오지 않는다
    MUSIC = 'ark'                      # 최종 보스 전용 곡 (play_mode.music_for)

    def __init__(self, x, y, room, player):
        super().__init__('ark', x, y, room, player)
        self.pattern = 'barrage'
        self.last_pattern = None
        self.last_wave = None        # 지난번 게이지 파동 (흡수·과충전을 번갈아 쓰려고)
        self.count = 0
        self.phase = 1
        self.roar_left = 0.0         # 페이즈 전환 자세가 남은 시간
        self.anim_time = 0.0
        self.dead_time = 0.0
        self.teleported = False
        self.slashes_left = 0        # 3페이즈: 베기를 한 번 더
        self.stare_left = 0.0
        self.rng = random.Random(11)

    # ----- 패턴 고르기 -----
    def _wave_turn(self):
        """이번 차례의 게이지 파동: 지난번과 반대. 처음이면 플레이어 게이지가 높을 때 과충전, 낮을 때 흡수."""
        if self.last_wave == 'absorb':
            return 'overcharge'
        if self.last_wave == 'overcharge':
            return 'absorb'
        return 'overcharge' if self.player.gauge.value >= 50 else 'absorb'

    def _choose_pattern(self):
        if self.count == 0:                              # 첫 패턴은 탄막: 무엇을 하는 보스인지 먼저 보여 준다
            return 'barrage'
        cx, cy = self.center
        px, py = self.player.center
        if self.room.line_blocked(cx, cy, px, py):      # 벽 뒤에 숨었다: 순간이동해서 벤다
            return 'slash'
        options = {}
        for name, weight in TABLES[self.phase].items():
            name = self._wave_turn() if name == 'wave' else name
            if name != self.last_pattern:
                options[name] = weight
        total = sum(options.values())
        r = self.rng.uniform(0, total)
        for name, weight in options.items():
            r -= weight
            if r <= 0:
                return name
        return name

    def _mult(self):
        return 0.8 if self.phase == 3 else 1.0

    def _vanish_time(self):
        return config.ARK_VANISH_TIME * self._mult()

    def _windup(self):
        if self.pattern == 'slash':
            return (config.ARK_VANISH_TIME + config.ARK_APPEAR_TIME) * self._mult()
        return WINDUP[self.pattern] * self._mult()

    def _active(self):
        extra = OVERCHARGE_SECOND if self.pattern == 'overcharge' and self.phase == 3 else 0.0
        return ACTIVE[self.pattern] + extra

    def _windup_time(self):            # 일반 적의 예고 깜빡임 계산이 패턴 시간을 쓰게 한다
        return self._windup()

    def _active_time(self):
        return self._active()

    # ----- 상태 -----
    def update(self, dt):
        self.roar_left = max(0.0, self.roar_left - dt)
        super().update(dt)
        self.anim_time += dt
        if not self.alive:
            self.dead_time += dt
            return
        if self.phase == 1 and self.hp <= self.max_hp * config.ARK_PHASES[0]:
            self._enter_phase(2, '각성')
        elif self.phase == 2 and self.hp <= self.max_hp * config.ARK_PHASES[1]:
            self._enter_phase(3, '폭주')

    def _enter_phase(self, phase, word):
        """주먹을 들고 멈춰 서서 페이즈를 바꾼다."""
        self.phase = phase
        self.roar_left = 1.0
        self.cooldown = max(self.cooldown, 1.0)
        assets.play_sound('ark_roar')
        effects.add_trauma(0.7)
        effects.spawn('puff', self.x, self.y + 20, duration=0.45)       # 큰 폭발은 페이즈 자세를 가린다
        effects.float_text(self.x, self.y + self.hb_h + 80, word, (150, 240, 230), big=True, life=1.0)

    def on_attack_start(self):
        super().on_attack_start()
        self.teleported = False
        if self.pattern == 'slash':
            self.slashes_left = 1 if self.phase == 3 else 0
        if self.pattern != 'slash':
            effects.spawn('puff', self.x + self.face_dir * 30, self.y + 100, duration=0.3)

    def _do_chase(self, dt):
        if not self._player_alive() or self.roar_left > 0:
            self.vx = 0.0
            return
        if not self.on_ground:
            return
        if self.cooldown <= 0:
            self.pattern = self._choose_pattern()
            self.count += 1
            self.vx = 0.0
            self.engage()
            return
        if self.stare_left > 0:
            self.stare_left -= dt
            self.vx = 0.0
            return
        if self.rng.random() < dt * 0.3:                  # 가끔 멈춰 내려다본다
            self.stare_left = self.rng.uniform(0.3, 0.7)
        d = self.distance_x()
        speed = self.stats['speed'] * (1.25 if self.phase == 3 else 1.0)
        if d > KEEP_FAR and self._floor_ahead():
            self.vx = self.face_dir * speed
        elif d < KEEP_NEAR and self._floor_behind():
            self.vx = -self.face_dir * speed               # 너무 붙으면 천천히 물러난다
        else:
            self.vx = 0.0

    def _do_attack(self, dt):
        self.attack_time += dt
        self.vx = 0.0
        windup, active = self._windup(), self._active()
        if self.pattern == 'slash' and not self.teleported and self.attack_time >= self._vanish_time():
            self._teleport_beside_player()
        if self.attack_time < windup:
            return
        after = self.attack_time - windup
        if not self.struck:
            self.struck = True
            self._begin_active()
        if self.pattern == 'overcharge' and self.phase == 3 and self.hits_done == 1 and after >= OVERCHARGE_SECOND:
            self.hits_done = 2
            self._overcharge_ring(speed_mult=1.3)          # 두 번째 겹: 더 빠르다
        if self.attack_time >= windup + active:
            if self.pattern == 'slash' and self.slashes_left > 0:
                self.slashes_left -= 1                     # 3페이즈: 다시 흩어져 한 번 더
                self.attack_time = 0.0
                self.struck = False
                self.teleported = False
                return
            self.last_pattern = self.pattern
            if self.pattern in ('absorb', 'overcharge'):
                self.last_wave = self.pattern
            self.cooldown = self.stats['cooldown'] * {1: 1.0, 2: 0.85, 3: 0.7}[self.phase]
            self.recover()

    # ----- 패턴 실행 -----
    def _hand(self):
        return self.x + self.face_dir * 40, self.y + 108

    def _begin_active(self):
        if self.pattern == 'barrage':
            self._fire_barrage()
        elif self.pattern == 'slash':
            self._slash()
        elif self.pattern == 'absorb':
            self._absorb_waves()
        elif self.pattern == 'overcharge':
            self.hits_done = 1
            self._overcharge_ring()
        elif self.pattern == 'bands':
            self._lay_bands()
        elif self.pattern == 'crystals':
            self._raise_crystals()
        else:
            self._lay_fields()

    def _lay_bands(self):
        """농도 띠: 짙은 띠(게이지 상승)와 맑은 띠(하강)가 방을 천천히 가로지른다. 서 있는 자리로 게이지를 지킨다."""
        import boss_terrain
        for o in list(game_world.world[game_world.LAYER_EFFECT]):
            if isinstance(o, boss_terrain.HazeBands):
                game_world.remove_object(o)
        game_world.add_object(boss_terrain.HazeBands(self.room, self.player), game_world.LAYER_EFFECT)
        effects.float_text(self.x, self.y + self.hb_h + 80, '농도 조작', (150, 240, 230), big=True, life=1.0)
        assets.play_sound('ark_field')

    def _raise_crystals(self):
        """결정 벽: 플레이어 양옆에 벽이 솟아 길을 막는다. 대시로 부딪쳐 깨면 헤이즈를 흡수한다."""
        import boss_terrain
        for ox in (-3 * config.TILE, 3 * config.TILE):
            x = self.player.x + ox
            if 2 * config.TILE <= x <= self.room.width - 2 * config.TILE:
                game_world.add_object(boss_terrain.CrystalWall(x, self.room, self.player), game_world.LAYER_EFFECT)
        assets.play_sound('ark_absorb')

    def _fire_barrage(self):
        hx, hy = self._hand()
        px, py = self.player.center
        base = math.atan2(py - hy, px - hx)
        n = config.ARK_BULLET_COUNT[self.phase - 1]
        spread = math.radians(config.ARK_BULLET_SPREAD)
        for i in range(n):
            a = base + (spread * (i / (n - 1) - 0.5) if n > 1 else 0.0)
            game_world.add_object(projectile.HazeBullet(hx, hy, math.cos(a), math.sin(a), self.room, self.player),
                                  game_world.LAYER_EFFECT)
        assets.play_sound('ark_bullet')
        effects.add_trauma(0.2)

    def _teleport_beside_player(self):
        """플레이어 등 뒤(바라보는 반대쪽)에 나타난다. 그쪽에 바닥이 없으면 앞쪽."""
        self.teleported = True
        effects.spawn('puff', self.x, self.y + 40, duration=0.35)        # 흩어진 자리
        p = self.player
        for side in (-p.face_dir, p.face_dir):
            x = p.x + side * config.ARK_TELEPORT_GAP
            if not (config.TILE * 1.5 <= x <= self.room.width - config.TILE * 1.5):
                continue
            floor = projectile.floor_below(self.room, x, p.y + 40)
            if floor is not None:
                self.x, self.y, self.vy = x, floor, 0.0
                break
        self.face_dir = 1 if p.x > self.x else -1
        effects.spawn('puff', self.x, self.y + 40, duration=0.35)        # 나타난 자리 (큰 폭발은 플레이어와 아크를 가린다)
        assets.play_sound('ark_teleport')

    def _slash(self):
        reach = config.ARK_SLASH_RANGE
        x0 = self.x - self.hb_w / 2 if self.face_dir < 0 else self.x
        box = (min(x0, x0 + self.face_dir * reach), self.y, max(x0 + self.hb_w / 2, x0 + self.face_dir * reach),
               self.y + self.hb_h)
        effects.spawn('hit-normal', self.x + self.face_dir * reach * 0.6, self.y + self.hb_h * 0.55,
                      flip=self.face_dir < 0, duration=0.25)
        effects.add_trauma(0.35)
        assets.play_sound('swing')
        if self._player_alive() and projectile.overlap(box, self.player.rect()):
            self.player.take_hit(self.stats['damage'], gauge_delta=projectile._gauge_delta(config.ARK_SLASH_NET), source=self)

    def _absorb_waves(self):
        """방 양끝에서 아크 쪽으로 조여 드는 파동 두 개."""
        effects.add_trauma(0.5)
        edge = config.TILE * 1.5
        for x, d in ((edge, 1), (self.room.width - edge, -1)):
            game_world.add_object(projectile.GaugeWave(x, self.y, d, config.ARK_WAVE_SPEED, 'absorb', self.room,
                                                       self.player, stop_x=self.x), game_world.LAYER_EFFECT)
        assets.play_sound('ark_absorb')

    def _overcharge_ring(self, speed_mult=1.0):
        """아크에서 바깥으로 퍼지는 파동 두 개 (좌우)."""
        effects.add_trauma(0.6)
        effects.spawn('puff', self.x, self.y + 30, duration=0.4)
        for d in (-1, 1):
            game_world.add_object(projectile.GaugeWave(self.x + d * 50, self.y, d, config.ARK_WAVE_SPEED * speed_mult,
                                                       'overcharge', self.room, self.player), game_world.LAYER_EFFECT)
        assets.play_sound('ark_burst')

    def _lay_fields(self):
        """플레이어 발밑에 오염 장판 (3페이즈는 하나 더, 옆에)."""
        w = config.ARK_FIELD_W[self.phase - 1]
        t = config.ARK_FIELD_TIME[self.phase - 1]
        xs = [self.player.x]
        if self.phase == 3:
            xs.append(self.player.x + self.rng.choice((-1, 1)) * (w + 120))
        for x in xs:
            x = min(max(x, w / 2 + config.TILE), self.room.width - w / 2 - config.TILE)
            floor = projectile.floor_below(self.room, x, self.player.y + 40)
            if floor is not None:
                game_world.add_object(projectile.PollutionField(x, floor, w, t, self.room, self.player),
                                      game_world.LAYER_EFFECT)
        effects.add_trauma(0.3)
        assets.play_sound('ark_field')

    # ----- 그리기 -----
    def _body_frame(self):
        if self.state == 'DEAD':
            return 'boss_ark_death', 1 if self.dead_time < config.ARK_DEATH_FALL else 2
        if self.state == 'ATTACK':
            t = self.attack_time
            windup = self._windup()
            if self.pattern == 'slash':
                if not self.teleported:
                    return 'boss_ark_vanish', 1                   # 안개로 흩어진다
                if t < windup:                                    # 나타나 웅크림 -> 손날을 당김
                    appear_end = self._vanish_time() + (windup - self._vanish_time()) * 0.5
                    return ('boss_ark_appear', 1) if t < appear_end else ('boss_ark_slash', 1)
                return 'boss_ark_slash', 2 if t < windup + self._active() * 0.5 else 3
            name = 'boss_ark_' + POSE.get(self.pattern, self.pattern)
            return name, 1 if t < windup else 2
        if self.roar_left > 0:
            return 'boss_ark_phase', 1
        if self.flash > 0:                                        # 맞으면 상체가 젖혀진다 (경직은 없다)
            return 'boss_ark_hurt', 1
        if self.vx != 0 and self.on_ground:
            return 'boss_ark_walk', int(self.walk_phase) % 4 + 1
        return 'boss_ark_idle', int(self.anim_time / 0.5) % 2 + 1

    def _pose_offset(self, name):
        return 0, 0

    def _tint(self):
        tint = super()._tint()
        if tint is None and self.phase == 3 and int(self.anim_time * 3) % 2 == 0:
            return (190, 255, 245)                                # 3페이즈: 청록으로 달아오른다
        return tint

    def draw(self):
        super().draw()
        if self.state == 'ATTACK' and self.attack_time < self._windup() and (self.pattern != 'slash' or self.teleported):
            k = min(1.0, self.attack_time / max(self._windup(), 0.01))   # 예고가 끝날수록 커진다
            size = int(6 + 10 * k) // 2 * 2
            hx, hy = int(self._hand()[0]), int(self._hand()[1])
            color = GLOW[self.pattern]
            assets.draw_rect_color(hx - size, hy - size, size * 2, size * 2, color, 0.3)
            assets.draw_rect_color(hx - size // 2, hy - size // 2, size, size, color, 0.85)

    def _draw_hp_bar(self):
        pass                                                      # 보스 체력은 화면 위 큰 바(UI)

    # ----- 피해: 경직 없음, 쓰러지는 자세를 보여 준다 -----
    def take_damage(self, damage, from_x=None, knock=1.0):
        if not self.alive:
            return False
        self.hp -= damage
        self.flash = config.ENEMY_HIT_FLASH
        import drama
        drama.damage_number(self, damage, self.player)    # 피해 숫자 (11/21 타격감)
        if self.hp <= 0:
            self.alive = False
            self.die()
            self.vx = 0.0
            assets.play_sound('enemy_die')
            self.player.run_kills = getattr(self.player, 'run_kills', 0) + 1     # 판 기록 (계획 4-2)
            self.player.shards += config.SHARDS_PER_KILL.get(self.kind, 1)
            effects.add_trauma(1.0)
            for dx, dy in ((0, 40), (-50, 100), (50, 150)):
                effects.spawn('haze-blast', self.x + dx, self.y + dy, duration=0.6)
            return True                                           # 몸은 남아 쓰러진다 (방 클리어는 alive로 판정)
        assets.play_sound('hit_boss_crystal')
        return False
