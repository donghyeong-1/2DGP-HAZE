"""구역 1 중간 보스 '문지기' (v8 6일 차, docs/plan_v8.md 6절).

제9구역(슬럼) 끝 관문을 지키는 간수장. 관문 방(gate)에 들어서면 stage가 보스로 세운다(config.GATEKEEPER).
일반 적과 같은 몸(Enemy)에 패턴 셋을 얹었다. 그림은 간수 그림을 1.5배로 구운 것(tools/make_gatekeeper.py).

패턴 (모두 노랗게 깜빡이고 머리 위 '!'로 예고한다):
- 방패 돌진(charge): 멀면. 바닥 표시 뒤 방패를 앞세워 방을 가로지른다(몸통 박치기 한 번). 벽에 부딪히면 잠깐 비틀거린다(빈틈).
- 내려찍기(slam): 가까우면. 큰 한 방(맞으면 게이지 +15, 간수 규칙) + 양옆으로 바닥 충격파(점프로 넘는다).
- 증원 호출(call): 슬럼 폐인·사냥개를 방 끝 스폰 칸에 부른다. 살아 있는 증원은 최대 GATEKEEPER_CALL['max_adds'].
같은 패턴을 연달아 쓰지 않는다. 첫 공격은 거리에 따라 내려찍기나 돌진(무엇을 하는 보스인지 먼저 보여 준다).
**2페이즈(체력 절반)**: 한 줄 대사와 함께 바로 증원을 부르고, 예고가 짧아지며(x0.8) 돌진은 되돌아 한 번 더, 내려찍기는 충격파 두 겹.
보스라서 경직되지 않고 사슬에 묶이거나 끌리지 않는다. 쓰러지면 증원도 흩어지고 관문이 열린다.
"""
import assets
import config
import effects
import enemy
import game_world
import projectile
import room as room_module
import sprites
from enemy import Corpse, Enemy

# 기술 표 등록 (enemy.MOVES의 형식: range/gap은 고르는 거리, windup은 예고 배율, active는 예고 뒤 시간)
enemy.MOVES.setdefault('slam', dict(range=None, gap=0, windup=1.35, active=0.45))
enemy.MOVES.setdefault('charge', dict(range=1100, gap=220, windup=1.15, active=1.1))
enemy.MOVES.setdefault('call', dict(range=3000, gap=0, windup=1.0, active=0.55))
SLAM_SECOND = 0.35        # 2페이즈 내려찍기 두 번째 충격파(첫 충격파 뒤 초)
PHASE2_MULT = 0.8         # 2페이즈 예고 배율


class Gatekeeper(Enemy):
    BOSS, SPREAD = True, False      # 보스 표시 (weapon.py가 조각 처치·날려 보내기·처형 배율에서 거른다), 비켜 서지 않는다
    title = '문지기'
    pullable = False               # 사슬에 맞아도 끌려오지 않는다
    MUSIC = 'boss'

    def __init__(self, x, y, room, player):
        super().__init__('gatekeeper', x, y, room, player)
        self.phase = 1
        self.last_move = None
        self.adds = []              # 부른 증원
        self.since_call = 0.0       # 마지막 증원 뒤 지난 시간
        self.called_p2 = False      # 2페이즈에 들어서며 증원을 불렀는가
        self.charges_left = 0
        self.stunned_left = 0.0     # 벽에 부딪혀 비틀거리는 남은 시간 (빈틈)
        self.roar_left = 0.0
        self.anim_time = 0.0
        self.wave2 = False          # 2페이즈 내려찍기 두 번째 충격파를 냈는가

    # ----- 조회 -----
    def alive_adds(self):
        self.adds = [a for a in self.adds if a.alive]
        return self.adds

    def _windup_time(self):
        return super()._windup_time() * (PHASE2_MULT if self.phase == 2 else 1.0)

    def _active_time(self):
        if self.move == 'slam' and self.phase == 2:
            return enemy.MOVES['slam']['active'] + SLAM_SECOND
        return super()._active_time()

    # ----- 패턴 고르기 -----
    def _pick_move(self, d, dy):
        s = self.stats
        call = config.GATEKEEPER_CALL
        if self.phase == 2 and not self.called_p2:
            return 'call'                                    # 2페이즈에 들어서면 바로 증원
        near = d <= s['attack_range'] + 20 and abs(dy) < 200
        if self.attacks == 0:
            return 'slam' if near else 'charge'
        options = {}
        if near:
            options['slam'] = 3
        if 220 < d <= enemy.MOVES['charge']['range'] and abs(dy) < 120:
            options['charge'] = 3
        if len(self.alive_adds()) < call['max_adds'] and self.since_call >= call['every']:
            options['call'] = 2 if d > s['attack_range'] else 1
        options = {k: w for k, w in options.items() if k != self.last_move} or (
            {'slam': 1} if near and self.last_move == 'slam' else {})
        if not options:
            return None
        total = sum(options.values())
        r = self.rng.uniform(0, total)
        for name, weight in options.items():
            r -= weight
            if r <= 0:
                return name
        return name

    # ----- 갱신 -----
    def update(self, dt):
        self.anim_time += dt
        self.since_call += dt
        self.roar_left = max(0.0, self.roar_left - dt)
        super().update(dt)
        if self.phase == 1 and self.alive and self.hp <= self.max_hp / 2:
            self._enter_phase2()

    def _enter_phase2(self):
        self.phase = 2
        self.roar_left = 0.8
        self.cooldown = min(self.cooldown, 0.6)
        assets.play_sound('overload')
        effects.add_trauma(0.6)
        effects.ground_slam(self.x, self.y, power=1.2)
        effects.float_text(self.x, self.y + self.hb_h + 80, '비상', (255, 110, 90), big=True, life=1.0)
        import boss_intro
        boss_intro.bark(self, 'phase2')

    def _do_chase(self, dt):
        if self.stunned_left > 0:                           # 벽에 부딪혀 비틀거린다 (빈틈)
            self.stunned_left = max(0.0, self.stunned_left - dt)
            self.vx = 0.0
            return
        if self.roar_left > 0:
            self.vx = 0.0
            return
        super()._do_chase(dt)

    def on_attack_start(self):
        super().on_attack_start()
        self.wave2 = False
        if self.move == 'charge':
            self.charges_left = 2 if self.phase == 2 else 1

    def _do_attack(self, dt):
        self.attack_time += dt
        windup, active = self._windup_time(), self._active_time()
        if self.attack_time < windup:
            if self.on_ground:
                self.vx = 0.0
            return
        getattr(self, '_move_' + self.move)(self.attack_time - windup)
        if self.state != 'ATTACK':
            return
        if self.attack_time >= windup + active:
            if self.move == 'charge' and self.charges_left > 1 and self.stunned_left <= 0:
                self._turn_and_charge_again()
                return
            self._end_attack()

    def _end_attack(self):
        self.vx = 0.0
        self.last_move = self.move
        cd = self.stats['cooldown'] * (1.3 if self.move == 'charge' else 1.0)
        self.cooldown = cd * (0.75 if self.phase == 2 else 1.0)
        self.recover()

    def on_attack_end(self):
        self.attacks += 1
        self.charges_left = 0

    # ----- 패턴 -----
    def _move_slam(self, after):
        """내려찍기: 큰 한 방 + 양옆 충격파. 2페이즈는 조금 뒤 한 겹 더 (더 빠르게)."""
        self.vx = 0.0
        if not self.struck:
            self.struck = True
            self._melee(extra=self.stats['slam_reach'])
            assets.play_sound('overload')
            effects.add_trauma(0.55)
            effects.spawn('quake-blast', self.x + self.face_dir * 70, self.y, duration=0.45)
            effects.ground_slam(self.x + self.face_dir * 70, self.y, power=1.2)
            self._shockwaves()
        elif self.phase == 2 and not self.wave2 and after >= SLAM_SECOND:
            self.wave2 = True
            self._shockwaves(speed_mult=1.3)

    def _shockwaves(self, speed_mult=1.0):
        s = self.stats
        for d in (-1, 1):
            game_world.add_object(
                projectile.Shockwave(self.x + d * 60, self.y, d, s['wave_speed'] * speed_mult, s['wave_damage'], 0,
                                     self.room, self.player, life=1.1), game_world.LAYER_EFFECT)

    def _move_charge(self, after):
        """방패 돌진: 앞으로 달린다. 벽에 막히면 멈추고 비틀거린다, 낭떠러지·가시 앞에서는 그냥 멈춘다."""
        s = self.stats
        if not self.struck:
            self.struck = True
            self.contact_hit = False
            assets.play_sound('dash')
        wall = self._wall_ahead()
        if wall or not self._floor_ahead():
            self.vx = 0.0
            if wall and self.stunned_left <= 0:
                self.stunned_left = s['wall_stun']
                effects.add_trauma(0.45)
                effects.spawn('puff', self.x + self.face_dir * self.hb_w / 2, self.y + 60, duration=0.4)
                assets.play_sound('chain_clash')
            self.attack_time = max(self.attack_time, self._windup_time() + self._active_time())
            return
        self.vx = self.face_dir * s['charge_speed']
        if not self.contact_hit and self._player_alive() and projectile.overlap(self.rect(), self.player.rect()):
            self.contact_hit = True
            self.player.take_hit(s['charge_damage'], source=self)

    def _wall_ahead(self):
        ahead = self.x + self.face_dir * (self.hb_w / 2 + 8)
        return self.room.tile_at_world(ahead, self.y + 40) == room_module.SOLID

    def _turn_and_charge_again(self):
        """2페이즈: 끝에서 돌아서서 짧게 예고하고 한 번 더."""
        self.charges_left -= 1
        self.vx = 0.0
        if self.player.x != self.x:
            self.face_dir = 1 if self.player.x > self.x else -1
        self.attack_time = self._windup_time() * 0.45
        self.struck = False
        self.contact_hit = False

    def _move_call(self, after):
        self.vx = 0.0
        if not self.struck:
            self.struck = True
            self.call_adds()

    def call_adds(self):
        """증원을 부른다: 플레이어에게서 먼 스폰 칸(없으면 방 양끝)에 count마리, 살아 있는 증원은 max_adds까지."""
        call = config.GATEKEEPER_CALL
        self.since_call = 0.0
        if self.phase == 2:
            self.called_p2 = True
        room_ = self.room
        spots = [(x, y) for x, y, _k in getattr(room_, 'enemy_spawns', [])]
        floor = self.y
        spots += [(3 * config.TILE, floor), (room_.width - 3 * config.TILE, floor)]
        spots.sort(key=lambda s: -abs(s[0] - self.player.x))
        room_left = call['max_adds'] - len(self.alive_adds())
        n = min(call['count'], max(0, room_left))
        if n <= 0:
            return 0
        import enemy_kinds
        made = 0
        for i in range(n):
            kind = call['kinds'][(len(self.adds) + i) % len(call['kinds'])]
            x, y = spots[i % len(spots)]
            e = enemy_kinds.make(kind, x, y, room_, self.player)
            e.see()                                           # 부르자마자 쫓아온다
            game_world.add_object(e, game_world.LAYER_ENEMY)
            self.adds.append(e)
            effects.spawn('puff', x, y + 20, duration=0.4)
            made += 1
        effects.float_text(self.x, self.y + self.hb_h + 80, '증원', (255, 200, 120), big=True, life=0.9)
        assets.play_sound('warn_high')
        return made

    # ----- 피해: 경직 없음, 사슬에 묶이지 않는다 -----
    def hold(self, seconds):
        pass

    def pull_step(self, dx):
        return 0.0

    def take_damage(self, damage, from_x=None, knock=1.0):
        if not self.alive:
            return False
        self.hp -= damage
        self.flash = config.ENEMY_HIT_FLASH
        import drama
        drama.damage_number(self, damage, self.player)
        if self.hp <= 0:
            self._die()
            return True
        assets.play_sound(drama.hit_sound(self.kind))
        return False

    def _die(self):
        self.alive = False
        self.die()
        self.vx = 0.0
        assets.play_sound('enemy_die')
        import boss_intro
        boss_intro.bark(self, 'death')
        p = self.player
        p.run_kills = getattr(p, 'run_kills', 0) + 1
        p.shards += config.SHARDS_PER_KILL.get(self.kind, 1)
        effects.add_trauma(0.9)
        for a in self.alive_adds():                          # 증원은 흩어진다 (관문이 열린다)
            a.alive = False
            a.die()
            effects.spawn('death-burst', *a.center, duration=0.45)
            game_world.remove_object(a)
        self.adds = []
        for dx, dy in ((0, 40), (-40, 110), (40, 160)):
            effects.spawn('haze-blast', self.x + dx, self.y + dy, duration=0.6)
        if 'boss_gatekeeper_death' in sprites.FRAMES:
            game_world.add_object(Corpse('boss_gatekeeper_death', self.x, self.y, self.face_dir, 0.0, stay=2.2),
                                  game_world.LAYER_EFFECT)
        game_world.remove_object(self)

    # ----- 그리기 -----
    def _body_frame(self):
        name, n = super()._body_frame()
        if self.stunned_left > 0:
            return 'boss_gatekeeper_hurt', 2                  # 벽에 부딪혀 비틀 (한 무릎을 꿇는다)
        if self.roar_left > 0:
            return 'boss_gatekeeper_call', 2                  # 호루라기를 불며 몸을 젖힌다 (비상 호출)
        if self.state == 'HIT' or (name is None and self.flash > 0):
            return 'boss_gatekeeper_hurt', 1
        if name is None:
            return 'boss_gatekeeper_idle', 1 + int(self.anim_time / 0.6) % 2    # 대기: 방패를 세운 채 숨쉬기 2장
        return name, n

    def _tint(self):
        tint = super()._tint()
        if tint is None and self.phase == 2 and int(self.anim_time * 3) % 2 == 0:
            return (255, 190, 170)                            # 2페이즈: 달아오른다
        return tint

    def _draw_hp_bar(self):
        pass                                                  # 체력은 화면 위 보스 막대(UI)
