"""최종 거대 보스 '헤이즈 심장' (2026-11-22 v5 계획 2-2, docs/plan_v5.md). 아크의 진짜 모습.

탑 꼭대기 보스방(stage3의 final: heart)에서 아크를 쓰러뜨리면 방 위에서 내려온다. 던그리드 벨리알처럼 화면 위쪽을
차지하는 본체(HeartCore) + 따로 움직이는 기계 손 둘(HeartHand). 수치는 config.HEART.

- 심장은 닫혀 있으면 피해가 closed_mult로 줄어든다. 손 체력이 0이 되면 손이 바닥에 떨어져 기절하고(hand_stun 초),
  두 손이 모두 기절하면 심장이 열려(open_time 초) 내려오고 피해가 open_mult로 커진다 = 약점 노출.
- 패턴(심장이 고른다): 손 내려치기 slam / 손바닥 광선 훑기 laser / 결정 비 rain / 농도 파동 pulse.
- 페이즈(체력 비율 phases): 2페이즈 가운데 양옆에 발판이 솟는다(임시 벽, room.extra_solids 값 'heart'),
  3페이즈 바닥이 헤이즈로 잠기고(고농도 방) 심장이 내려온다.
그림: 본체 Codex T45(900x560), 손 Codex T46(260x260 오른손, 왼손은 반전), 결전 방 원경·등장 카드 Codex T47.
"""
import math
import random

import assets
import config
import effects
import game_world
import projectile
import room as room_module
import sprites
from enemy import Enemy

H = config.HEART
HEART_SETS = ('heart_core', 'heart_core_hurt', 'heart_core_dying',
              'heart_hand_idle', 'heart_hand_fist', 'heart_hand_palm', 'heart_hand_stun')
T = config.TILE
SHELL = (46, 40, 58)
SHELL_HI = (88, 78, 104)
CORE = (90, 240, 220)
CORE_HOT = (220, 255, 250)
IRON = (70, 66, 82)
JOINT = (120, 235, 225)


def floor_under(room, x, y_from):
    """x 아래로 처음 만나는 벽 칸의 윗면 y (없으면 0)."""
    row = max(1, room.row_of(min(y_from, room.height - T - 1)))     # 천장(맨 윗줄)을 바닥으로 잡지 않게
    for r in range(row, room.nrows):
        if room.tile_at(room.col_of(x), r) == room_module.SOLID:
            return room.tile_top(r)
    return 0.0


def spawn(room, player):
    """심장과 두 손을 world에 넣고 심장을 돌려준다 (stage가 보스로 삼는다)."""
    core = HeartCore(room, player)
    room.set_far('backgrounds/far_heart.png')       # 아크의 방이 심장의 기계 공동으로 바뀐다 (T47, 천천히 겹쳐 그린다)
    game_world.add_object(core, game_world.LAYER_ENEMY)
    for h in core.hands:
        game_world.add_object(h, game_world.LAYER_ENEMY)
    return core


class _Part(Enemy):
    pullable = False

    def hold(self, seconds):           # 사슬에 걸려도 묶이지 않는다
        pass

    def pull_step(self, dx):
        return 0.0

    def _draw_hp_bar(self):
        pass

    def _hurt_fx(self, damage, shown):
        self.flash = config.ENEMY_HIT_FLASH
        import drama
        drama.damage_number(self, shown, self.player)


# ----- 심장 -----
class HeartCore(_Part):
    title = '헤이즈 심장'
    MUSIC = 'ark'

    def __init__(self, room, player):
        super().__init__('heart', room.width / 2, 0.0, room, player)
        self.floor_y = floor_under(room, room.width / 2, room.height - T)
        self.home_y = self.floor_y + H['core_height']
        self.y = self.home_y + 700                  # 방 위에서 내려온다
        self.intro_left = H['intro']
        self.warmed = False                         # 테두리 판을 미리 만들었는가 (draw)
        self.phase = 1
        self.open_left = 0.0
        self.opened = False                         # 이번 기절로 이미 열렸는가
        self.cooldown = 1.5
        self.time = 0.0
        self.dead_time = 0.0
        self.last_pattern = None
        self.rng = random.Random(7)
        self.platforms = []
        self.hands = [HeartHand(self, -1), HeartHand(self, 1)]

    # ----- 조회 -----
    @property
    def is_open(self):
        return self.open_left > 0

    def target_y(self):
        if self.is_open:
            return self.floor_y + H['open_height']
        return self.floor_y + (H['low_height'] if self.phase == 3 else H['core_height'])

    def busy(self):
        if any(h.mode not in ('idle', 'stun') for h in self.hands):
            return True
        return any(isinstance(o, (HazePulse, CrystalShard)) for o in game_world.world[game_world.LAYER_EFFECT])

    # ----- 갱신 -----
    def update(self, dt):
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        if not self.alive:
            self.dead_time += dt
            if self.dead_time >= 3.0:
                game_world.remove_object(self)
            return
        self.room.step_far(dt)
        if self.intro_left > 0:
            self.intro_left -= dt
            k = max(0.0, self.intro_left / H['intro'])
            self.y = self.home_y + 700 * k * k
            if self.intro_left <= 0:
                assets.play_sound('ark_roar')
                effects.add_trauma(0.8)
                effects.float_text(self.x, self.y + 320, '헤이즈 심장', (150, 240, 230), big=True, life=1.4)
            return
        self._check_phase()
        self._check_open(dt)
        ty = self.target_y()                       # 목표 높이로 천천히 오르내린다
        step = H['descend_speed'] * dt
        self.y += max(-step, min(step, ty - self.y))
        if self.is_open:
            return
        self.cooldown -= dt
        if self.cooldown <= 0 and not self.busy() and self.player.state != 'DEAD':
            self.start_pattern(self._choose())

    def _check_phase(self):
        a, b = H['phases']
        if self.phase == 1 and self.hp <= self.max_hp * a:
            self.phase = 2
            self._raise_platforms()
            self._announce('맥동', (150, 240, 230))
        elif self.phase == 2 and self.hp <= self.max_hp * b:
            self.phase = 3
            self.room.is_high_haze = True          # 바닥이 헤이즈로 잠긴다: 게이지가 계속 오른다
            self._announce('범람', (255, 150, 120))

    def _announce(self, word, color):
        assets.play_sound('ark_roar')
        effects.add_trauma(0.7)
        effects.float_text(self.x, self.floor_y + 420, word, color, big=True, life=1.2)
        self.cooldown = max(self.cooldown, 1.2)

    def _raise_platforms(self):
        """2페이즈: 심장 양옆에 발판이 솟는다 (심장에 닿을 높이)."""
        row = self.room.row_of(self.floor_y + H['platform_height'])
        mid = self.room.col_of(self.x)
        for c0 in (mid - 9, mid + 6):
            cells = [(c, row) for c in range(c0, c0 + 3) if self.room.tile_at(c, row) != '#']
            for cell in cells:
                self.room.extra_solids[cell] = 'heart'
            if cells:
                self.platforms.append(cells)
                x = (c0 + 1.5) * T
                effects.spawn('puff', x, self.room.height - row * T, duration=0.4)
        assets.play_sound('chain_latch_heavy')

    def _check_open(self, dt):
        if self.open_left > 0:
            self.open_left -= dt
            if self.open_left <= 0:
                assets.play_sound('chain_latch_heavy')
            return
        stunned = all(h.stunned for h in self.hands)
        if not stunned:
            self.opened = False
            return
        if not self.opened:                         # 두 손 모두 기절: 열린다
            self.opened = True
            self.open_left = H['open_time']
            for o in list(game_world.world[game_world.LAYER_EFFECT]):
                if isinstance(o, HazePulse):
                    game_world.remove_object(o)
            assets.play_sound('ark_burst')
            effects.add_trauma(0.6)
            effects.float_text(self.x, self.floor_y + 520, '약점 노출', (255, 230, 140), big=True, life=1.4)

    # ----- 패턴 -----
    def _choose(self):
        table = dict(H['patterns'][self.phase])
        if not any(h.mode == 'idle' for h in self.hands):
            table.pop('slam', None)
            table.pop('laser', None)
        table.pop(self.last_pattern, None)
        if not table:
            return 'rain'
        total = sum(table.values())
        r = self.rng.uniform(0, total)
        for name, w in table.items():
            r -= w
            if r <= 0:
                return name
        return name

    def start_pattern(self, name):
        self.last_pattern = name
        self.cooldown = H['cooldown'][self.phase]
        if name in ('slam', 'laser'):
            free = [h for h in self.hands if h.mode == 'idle']
            if not free:
                return
            hand = min(free, key=lambda h: abs(h.x - self.player.x)) if name == 'slam' else self.rng.choice(free)
            hand.start(name)
        elif name == 'rain':
            self._rain()
        elif name == 'pulse':
            game_world.add_object(HazePulse(self.player, self.room), game_world.LAYER_EFFECT)
            effects.float_text(self.x, self.floor_y + 420, '농도 파동', (150, 240, 230), big=True, life=1.0)
            assets.play_sound('ark_field')

    def _rain(self):
        """결정 비: 하나는 플레이어 자리, 나머지는 방 곳곳 (떨어질 자리에 표시가 먼저)."""
        assets.play_sound('ark_absorb')
        xs = [self.player.x]
        while len(xs) < H['rain_count']:
            x = self.rng.uniform(2 * T, self.room.width - 2 * T)
            if all(abs(x - o) > 150 for o in xs):
                xs.append(x)
        for i, x in enumerate(xs):
            fy = floor_under(self.room, x, self.room.height - 2 * T)
            game_world.add_object(CrystalShard(x, fy, 0.12 * i, H['rain_damage'], 0, self.room, self.player),
                                  game_world.LAYER_EFFECT)

    # ----- 피해 -----
    def take_damage(self, damage, from_x=None, knock=1.0):
        if not self.alive or self.intro_left > 0:
            return False
        dealt = damage * (H['open_mult'] if self.is_open else H['closed_mult'])
        self.hp -= dealt
        self._hurt_fx(damage, dealt)
        assets.play_sound('hit_organic' if self.is_open else 'chain_clash')
        if self.hp <= 0:
            self._die()
            return True
        return False

    def _die(self):
        self.alive = False
        self.die()
        p = self.player
        p.run_kills = getattr(p, 'run_kills', 0) + 1
        p.shards += H['shards']
        for h in self.hands:
            h.alive = False
            game_world.remove_object(h)
            effects.spawn('haze-blast', h.x, h.y + 50, duration=0.6)
        for o in list(game_world.world[game_world.LAYER_EFFECT]):
            if isinstance(o, (HazePulse, CrystalShard)):
                game_world.remove_object(o)
        for cell in [c for c, v in self.room.extra_solids.items() if v == 'heart']:
            del self.room.extra_solids[cell]
        effects.add_trauma(1.0)
        effects.request_flash(0.4)
        assets.play_sound('enemy_die')
        for dx, dy in ((0, 100), (-120, 180), (120, 220), (0, 300)):
            effects.spawn('haze-blast', self.x + dx, self.y + dy, duration=0.7)

    # ----- 그리기 (Codex T45 그림) -----
    def _core_frame(self):
        """(세트 이름, 번호): 쓰러짐 2장 -> 열림 중 피격 -> 열림 -> 닫힘 두 장 느린 맥동."""
        if not self.alive:
            return 'heart_core_dying', 1 if self.dead_time < 1.2 else 2
        if self.is_open:
            return ('heart_core_hurt', 1) if self.flash > 0 else ('heart_core', 3)
        return 'heart_core', 1 + int(self.time * 1.5) % 2

    def draw(self):
        if not self.warmed:                         # 처음 그릴 때(등장 카드로 게임이 멈춘 동안) 본체·손 테두리 판 14장을 한꺼번에 만든다
            self.warmed = True
            sprites.warm_outlines(HEART_SETS)
        x, y = int(self.x), int(self.y)
        alpha = 1.0 if self.alive else max(0.0, 1.0 - self.dead_time / 3.0)
        if alpha <= 0:
            return
        name, n = self._core_frame()
        sprites.draw(name, n, x, y, 1, alpha=alpha)
        if self.flash > 0 and not self.is_open and self.alive:       # 닫힌 채 맞으면 하얗게 번쩍
            sprites.draw_white(name, n, x, y)
        if self.is_open:
            assets.draw_text(x, y - 40, '약점', (255, 230, 140), center=True, small=True)
        for cells in self.platforms:                                 # 2페이즈 발판
            c0, r = cells[0]
            px0, py = c0 * T, self.room.height - (r + 1) * T
            assets.draw_rect_color(px0, py, len(cells) * T, T, IRON)
            assets.draw_rect_color(px0, py + T - 10, len(cells) * T, 10, SHELL_HI)
            assets.draw_rect_color(px0 + 10, py + 20, len(cells) * T - 20, 8, JOINT)
        if self.room.is_high_haze and self.phase == 3:              # 3페이즈 바닥에 고인 헤이즈
            k = 0.18 + 0.06 * math.sin(self.time * 3)
            assets.draw_rect_color(0, int(self.floor_y), int(self.room.width), 60, CORE, k)


# ----- 손 -----
class HeartHand(_Part):
    def __init__(self, core, side):
        super().__init__('heart_hand', core.x + side * H['hand_dx'], core.y - H['hand_dy'], core.room, core.player)
        self.core, self.side = core, side
        self.mode = 'idle'
        self.timer = 0.0
        self.struck = False
        self.dir = 1
        self.time = 0.0
        self.lock_x = None

    @property
    def stunned(self):
        return self.mode == 'stun'

    def home(self):
        c = self.core
        return c.x + self.side * H['hand_dx'], c.y - H['hand_dy'] + math.sin(self.time * 2 + self.side) * 14

    def _toward(self, tx, ty, dt, speed):
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        if d <= speed * dt:
            self.x, self.y = tx, ty
            return True
        self.x += dx / d * speed * dt
        self.y += dy / d * speed * dt
        return False

    def start(self, name):
        self.struck = False
        self.timer = 0.0
        self.lock_x = None
        if name == 'slam':
            self.mode = 'aim'
            assets.play_sound('windup_guard')
        else:
            self.mode = 'go'
            self.dir = -1 if self.side > 0 else 1      # 오른손은 오른쪽 끝에서 왼쪽으로 훑는다
            assets.play_sound('ark_absorb')

    def update(self, dt):
        self.time += dt
        self.flash = max(0.0, self.flash - dt)
        if not self.alive:
            return
        if self.core.intro_left > 0:
            self.x, self.y = self.home()
            return
        self.timer += dt
        getattr(self, '_' + self.mode)(dt)

    def _idle(self, dt):
        self._toward(*self.home(), dt, H['hand_speed'] * 0.5)

    def _return(self, dt):
        if self._toward(*self.home(), dt, H['hand_speed']):
            self.mode = 'idle'

    # 내려치기: 플레이어 위로 -> 그림자 예고 -> 내려찍기 -> 바닥에 박혀 잠시 (때릴 기회) -> 돌아감
    def _aim(self, dt):
        p = self.player
        if self.timer < H['slam_aim'] - 0.25:
            self.lock_x = p.x
        self._toward(self.lock_x, p.y + H['slam_from'], dt, H['hand_speed'])
        if self.timer >= H['slam_aim']:
            self.mode, self.timer = 'fall', 0.0

    def _fall(self, dt):
        fy = floor_under(self.room, self.x, self.y + 1)
        self.y = max(fy, self.y - H['slam_speed'] * dt)
        self._crush()
        if self.y <= fy:
            self.mode, self.timer = 'rest', 0.0
            self._crush()
            effects.add_trauma(0.6)
            effects.spawn('quake-blast', self.x, fy, duration=0.35)
            assets.play_sound('overload')
            for d in (-1, 1):
                game_world.add_object(projectile.Shockwave(self.x + d * self.hb_w / 2, fy, d, H['wave_speed'],
                                                           H['slam_wave'], 0, self.room, self.player, life=1.2),
                                      game_world.LAYER_EFFECT)

    def _crush(self):
        p = self.player
        if not self.struck and p.hit_test(self.rect(), self):
            self.struck = True
            p.take_hit(H['slam_damage'], source=self)

    def _rest(self, dt):
        if self.timer >= H['slam_rest']:
            self.mode = 'return'

    # 광선: 방 끝으로 -> 예고 -> 반대쪽 끝까지 세로 광선으로 훑는다
    def _edge_x(self, d):
        return 3 * T if d < 0 else self.room.width - 3 * T

    def _go(self, dt):
        start = self._edge_x(-self.dir)
        fy = floor_under(self.room, start, self.room.height - 2 * T)
        if self._toward(start, fy + H['laser_height'], dt, H['hand_speed'] * 1.6):
            self.mode, self.timer = 'warn', 0.0

    def _warn(self, dt):
        if self.timer >= H['laser_warn']:
            self.mode, self.timer = 'sweep', 0.0
            assets.play_sound('ark_burst')

    def beam_box(self):
        fy = floor_under(self.room, self.x, self.y)
        w = H['laser_w']
        return (self.x - w / 2, fy, self.x + w / 2, self.y)

    def _sweep(self, dt):
        self.x += self.dir * H['laser_speed'] * dt
        p = self.player
        if not self.struck and p.hit_test(self.beam_box(), self):
            self.struck = True
            p.take_hit(H['laser_damage'], source=self)
        if (self.dir > 0 and self.x >= self._edge_x(1)) or (self.dir < 0 and self.x <= self._edge_x(-1)):
            self.mode = 'return'

    # 기절: 바닥에 떨어져 있다가 체력을 되찾고 돌아간다
    def _stun(self, dt):
        fy = floor_under(self.room, self.x, self.y + 1)
        self.y = max(fy, self.y - 900 * dt)
        if self.timer >= H['hand_stun']:
            self.hp = self.max_hp
            self.mode = 'return'
            effects.spawn('surge', self.x, self.y, duration=0.4)

    def take_damage(self, damage, from_x=None, knock=1.0):
        if not self.alive or self.stunned or self.core.intro_left > 0:
            return False
        self.hp = max(0.0, self.hp - damage)
        self._hurt_fx(damage, damage)
        assets.play_sound('hit_organic')
        if self.hp <= 0:
            self.mode, self.timer = 'stun', 0.0
            effects.add_trauma(0.5)
            effects.spawn('haze-blast', self.x, self.y + 50, duration=0.45)
            assets.play_sound('chain_latch_heavy')
        return False

    # ----- 그리기 (Codex T46 그림) -----
    def draw(self):
        if not self.alive:
            return
        if self.mode == 'aim':                                         # 내려칠 자리 그림자
            fy = int(floor_under(self.room, self.x, self.y))
            if int(self.timer * 12) % 2 == 0 or self.timer > H['slam_aim'] - 0.3:
                assets.draw_rect_color(int(self.x - self.hb_w / 2), fy, int(self.hb_w), 10, (255, 90, 70), 0.8)
        if self.mode == 'warn' and int(self.timer * 14) % 2 == 0:      # 광선 예고: 가는 붉은 선
            x0, y0, x1, y1 = self.beam_box()
            assets.draw_rect_color(int(self.x) - 2, int(y0), 4, int(y1 - y0), (255, 90, 70), 0.9)
        if self.mode == 'sweep':
            x0, y0, x1, y1 = self.beam_box()
            w = int(x1 - x0)
            f = int(self.timer * 30) % 2
            assets.draw_rect_color(int(x0) - 6 + f * 2, int(y0), w + 12 - f * 4, int(y1 - y0), CORE, 0.45)
            assets.draw_rect_color(int(x0) + 8, int(y0), w - 16, int(y1 - y0), CORE_HOT)
            assets.draw_rect_color(int(x0) - 30, int(y0), w + 60, 10, CORE, 0.8)
        x, y = int(self.x), int(self.y)
        h = int(self.hb_h)
        name, n = self._frame()
        sprites.draw(name, n, x, y, self.side)
        if self.flash > 0:
            sprites.draw_white(name, n, x, y, self.side)
        if self.stunned and int(self.timer * 6) % 2 == 0:                                 # 기절: 불똥
            assets.draw_rect_color(x + 30 * self.side, y + 40, 8, 8, (255, 200, 90))
        if self.hp < self.max_hp and not self.stunned:                                    # 손 체력 (작게, 손 위)
            assets.draw_rect_color(x - 50, y + h + 40, 100, 8, (30, 20, 30))
            assets.draw_rect_color(x - 50, y + h + 40, int(100 * self.hp / self.max_hp), 8, (230, 80, 90))
        if self.mode == 'aim':                                                            # '!'
            assets.draw_rect_color(x - 3, y + h + 64, 6, 22, (255, 90, 70))
            assets.draw_rect_color(x - 3, y + h + 90, 6, 6, (255, 90, 70))

    def _frame(self):
        """(세트 이름, 번호): 내려치기 예고 = 들어 올린 주먹 -> 떨어짐·박힘 = 내려친 주먹, 광선 예고 -> 발사, 기절 두 장, 그 밖은 대기 두 장."""
        if self.mode == 'aim':
            return 'heart_hand_fist', 1
        if self.mode in ('fall', 'rest'):
            return 'heart_hand_fist', 2
        if self.mode == 'warn':
            return 'heart_hand_palm', 1
        if self.mode == 'sweep':
            return 'heart_hand_palm', 2
        if self.stunned:
            return 'heart_hand_stun', 1 if self.timer < 0.3 else 2
        return 'heart_hand_idle', 1 + int(self.time * 2 + (self.side > 0)) % 2


class CrystalShard(projectile.Debris):
    """결정 비 한 조각 (떨어질 자리 표시는 Debris와 같다). 청록 결정으로 그린다."""

    def draw(self):
        if self.wait > 0:
            return
        if not self.falling:
            super().draw()
            return
        x, y = int(self.x), int(self.y)
        assets.draw_rect_color(x - 10, y, 20, 60, (40, 150, 150))
        assets.draw_rect_color(x - 5, y + 6, 10, 48, CORE)
        assets.draw_rect_color(x - 2, y + 14, 4, 30, CORE_HOT)


class HazePulse:
    """농도 파동: pulse_time 동안 방 전체 게이지가 사인 파도로 오르내린다 (먼저 오른다). 화면에 색 파도."""

    def __init__(self, player, room):
        self.player, self.room = player, room
        self.time = 0.0

    def rate(self):
        return H['pulse_rate'] * math.sin(2 * math.pi * self.time / H['pulse_period'])

    def update(self, dt):
        self.time += dt
        p = self.player
        if p.state != 'DEAD':
            p.gauge.add(self.rate() * dt, 'pulse')
        if self.time >= H['pulse_time']:
            game_world.remove_object(self)

    def draw(self):
        k = self.rate() / H['pulse_rate']
        color = (60, 220, 200) if k > 0 else (230, 240, 255)
        assets.draw_rect_color(0, 0, int(self.room.width), int(self.room.height), color, 0.10 * abs(k))
        p = self.player
        assets.draw_text(int(p.x), int(p.y + p.hb_h + 70), '농도 상승' if k > 0 else '농도 하강', color, center=True,
                         small=True)
