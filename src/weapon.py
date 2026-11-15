"""무기. 지금은 철파이프 하나다. 식칼·건틀릿·사슬은 이후 주차에 같은 모양으로 추가한다.

공격은 이동 상태 머신 밖의 겹침(overlay)이다. 누른 순간 판정이 바로 일어난다. 어떤 공격이 나가는지는 상황으로 정해진다:
  강화 일격(E로 준비, 1회성) > 대시 평타(대시 중·직후) > 점프 평타(공중: 회전 베기, 아래를 겨누면 내려찍기) > 기본 3연타.
모든 근접 판정은 **시야선**을 본다: 벽(#) 너머의 적은 맞지 않는다 (벽 뒤에 숨어서 일방적으로 때리지 못한다).
대미지는 항상 기본 x 게이지 구간 배율 x 공격력 보너스 x 공격 종류 배율이다.
"""
import math

import assets
import config
import effects
import game_world


def _enemy_points(enemy):
    """적에게 닿는 시야선을 확인할 몸의 세 지점 (아래, 가운데, 위)."""
    left, bottom, right, top = enemy.rect()
    x = (left + right) / 2
    return [(x, bottom + 12), (x, (bottom + top) / 2), (x, top - 12)]


class Pipe:
    def __init__(self, owner):
        self.owner = owner
        self.combo = 0            # 지금까지 이어 친 횟수 (1~3)
        self.cooldown = 0.0       # 다음 공격까지 남은 시간
        self.combo_left = 0.0     # 이 시간이 지나면 연타가 끊긴다
        self.last_kind = None     # 마지막으로 나간 공격 종류 (테스트·UI용)

    def update(self, dt):
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.combo_left > 0:
            self.combo_left = max(0.0, self.combo_left - dt)
            if self.combo_left == 0:
                self.combo = 0

    @property
    def ready(self):
        return self.cooldown <= 0

    # ----- 어떤 공격인가 -----
    def current_kind(self):
        p = self.owner
        if p.gauge.enhanced:
            return 'enhanced'
        if p.dash_window > 0:
            return 'dash'
        if not p.on_ground and p.state in ('JUMP', 'FALL'):
            return 'plunge' if p.aim_vector()[1] < config.PLUNGE_AIM else 'spin'
        return 'pipe'

    def try_attack(self):
        """공격을 시도한다. 공격했으면 True."""
        if not self.ready:
            return False
        kind = self.current_kind()
        self.last_kind = kind
        getattr(self, '_attack_' + kind)()
        return True

    # ----- 공통 -----
    def _visible(self, enemy, cx, cy):
        """플레이어 몸 중심에서 적의 몸 어느 한 곳이라도 벽에 안 막히고 보이는가."""
        room = self.owner.room
        if room is None:
            return True
        return any(not room.line_blocked(cx, cy, px, py) for px, py in _enemy_points(enemy))

    def _targets(self, test):
        p = self.owner
        cx, cy = p.center
        out = []
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if enemy.alive and test(enemy) and self._visible(enemy, cx, cy):
                out.append(enemy)
        return out

    def _hit(self, enemy, damage, gain, fx, big=False, color=None, shake=1.0, stop=1.0, blast=False):
        """적 하나에게 피해와 모든 맞는 반응(게이지, 불꽃, 숫자, 흔들림, 멈춤)을 준다. 죽였으면 True."""
        p = self.owner
        killed = enemy.take_damage(damage, from_x=p.x)
        p.gauge.add(gain, 'hit')
        ex, ey = enemy.center
        effects.spawn(fx['spark'], ex, ey, duration=fx['spark_time'])
        effects.float_text(ex, ey + enemy.hb_h / 2 + 70, str(int(round(damage))), color or fx['damage_color'], big=big)
        effects.request_hit_stop(config.HIT_STOP * stop * fx['stop'])
        effects.add_trauma(config.SHAKE_HIT * shake * fx['shake'])
        if killed:
            p.gauge.add(config.GAIN_KILL + p.kill_bonus, 'kill')
            effects.add_trauma(config.SHAKE_KILL)
        if blast:
            self._blast(enemy)
        return killed

    def _damage(self, mult):
        p = self.owner
        return config.PIPE_DAMAGE * p.gauge.zone_multipliers()['attack'] * p.attack_bonus * mult

    @staticmethod
    def _segment_hit(enemy, cx, cy, dx, dy, length, half_width):
        """중심에서 (dx, dy) 방향으로 length만큼 뻗은 줄(반폭 half_width)이 적의 충돌 박스에 닿는가 (관통 판정)."""
        left, bottom, right, top = enemy.rect()
        steps = max(2, int(length // 20))
        for i in range(steps + 1):
            x, y = cx + dx * length * i / steps, cy + dy * length * i / steps
            if left - half_width <= x <= right + half_width and bottom - half_width <= y <= top + half_width:
                return True
        return False

    # ----- 기본 3연타 -----
    def _attack_pipe(self):
        p = self.owner
        self.combo = self.combo % 3 + 1
        finisher = self.combo == 3
        self.cooldown = config.PIPE_COOLDOWN[self.combo - 1]
        self.combo_left = self.cooldown + config.PIPE_COMBO_WINDOW
        ax, ay = p.aim_vector()
        cx, cy = p.center
        fx = config.ZONE_FX[p.gauge.zone]               # 게이지 구간에 따라 모양·색·반응이 다르다
        assets.play_sound(fx['sound'])
        variant, flip = effects.slash_variant(ax, ay)
        effects.spawn(effects.slash_sheet(p.gauge.zone, finisher), cx, cy, flip=flip, duration=0.22, variant=variant)
        damage = self._damage(config.PIPE_FINISHER_MULT if finisher else 1.0)
        gain = config.PIPE_FINISHER_GAIN if finisher else config.GAIN_HIT
        color = config.DAMAGE_COLOR_FINISHER if finisher else None
        for enemy in self._targets(lambda e: self._in_arc(e, cx, cy, ax, ay)):
            self._hit(enemy, damage, gain, fx, big=finisher, color=color, shake=1.0 if not finisher else config.SHAKE_FINISHER / config.SHAKE_HIT,
                      stop=2 if finisher else 1)

    # ----- 강화 일격 (E로 준비, 1회성) -----
    def _attack_enhanced(self):
        p = self.owner
        self.combo = 0
        self.cooldown = config.ENHANCE_STRIKE_COOLDOWN
        ax, ay = p.aim_vector()
        cx, cy = p.center
        fx = config.ENHANCED_FX
        assets.play_sound(fx['sound'])
        variant, flip = effects.slash_variant(ax, ay)
        effects.spawn(fx['slash'], cx, cy, flip=flip, duration=0.24, variant=variant)
        effects.add_trauma(config.SHAKE_FINISHER)
        damage = self._damage(config.ENHANCE_DAMAGE_MULT)
        for enemy in self._targets(lambda e: self._in_arc(e, cx, cy, ax, ay, enhanced=True)):
            self._hit(enemy, damage, config.PIPE_FINISHER_GAIN, fx, big=True, shake=2.0, stop=2, blast=True)
        p.gauge.consume_enhance()                        # 강화는 한 번뿐: 휘두른 순간 준비가 끝난다

    def _blast(self, hit):
        """강화 일격에 맞은 적 주위로 안개 폭발이 퍼져 주변 적에게 피해를 준다 (벽 너머에는 닿지 않는다)."""
        p = self.owner
        bx, by = hit.center
        effects.spawn('plasma-explosion', bx, by, duration=0.5)
        effects.add_trauma(config.SHAKE_FINISHER)
        for other in list(game_world.world[game_world.LAYER_ENEMY]):
            if other.alive and other is not hit:
                ox, oy = other.center
                if math.hypot(ox - bx, oy - by) <= config.ENHANCE_BLAST_RADIUS and (
                        p.room is None or not p.room.line_blocked(bx, by, ox, oy)):
                    if other.take_damage(config.ENHANCE_BLAST_DAMAGE, from_x=bx):
                        p.gauge.add(config.GAIN_KILL + p.kill_bonus, 'kill')

    # ----- 대시 평타: 돌진 베기 (관통) -----
    def _attack_dash(self):
        p = self.owner
        self.cooldown = config.DASH_STRIKE_COOLDOWN
        dx, dy = p.dash_vec
        cx, cy = p.center
        fx = config.ZONE_FX[p.gauge.zone]
        assets.play_sound(fx['sound'])
        sheet, _ = effects.special_sheet('dash')
        variant, flip = effects.slash_variant(dx, dy)
        effects.spawn(sheet, cx, cy, flip=flip, duration=0.24, variant=variant)
        if p.state == 'DASH':
            p.dash_left = max(p.dash_left, config.DASH_STRIKE_EXTEND)   # 돌진하며 벤다: 대시가 조금 더 이어진다
        damage = self._damage(config.DASH_STRIKE_MULT)
        targets = self._targets(lambda e: self._segment_hit(e, cx, cy, dx, dy, config.DASH_STRIKE_LENGTH,
                                                             config.DASH_STRIKE_HALF_WIDTH))
        for enemy in targets:                                            # 줄에 선 적을 모두 벤다
            self._hit(enemy, damage, config.GAIN_HIT, fx, shake=1.2, stop=1.0)

    # ----- 점프 평타: 회전 베기 / 내려찍기 -----
    def _attack_spin(self):
        p = self.owner
        self.cooldown = config.AIR_COOLDOWN
        cx, cy = p.center
        fx = config.ZONE_FX[p.gauge.zone]
        assets.play_sound(fx['sound'])
        effects.spawn(effects.special_sheet('spin')[0], cx, cy, duration=0.24)
        p.vy = max(p.vy, config.AIR_HOP)                                  # 살짝 떠오르며 한 바퀴 돈다
        damage = self._damage(config.AIR_SPIN_MULT)
        for enemy in self._targets(lambda e: self._within(e, cx, cy, config.AIR_SPIN_REACH)):
            self._hit(enemy, damage, config.GAIN_HIT, fx, shake=1.1)

    def _attack_plunge(self):
        p = self.owner
        self.cooldown = config.PLUNGE_COOLDOWN
        cx, cy = p.center
        fx = config.ZONE_FX[p.gauge.zone]
        assets.play_sound(fx['sound'])
        sheet, _ = effects.special_sheet('plunge')
        effects.spawn(sheet, cx, cy, duration=0.24, variant=4)             # 아래 방향 변형
        damage = self._damage(config.PLUNGE_MULT)
        targets = self._targets(lambda e: self._segment_hit(e, cx, cy, 0.0, -1.0, config.PLUNGE_LENGTH, config.PLUNGE_HALF_WIDTH))
        for enemy in targets:
            self._hit(enemy, damage, config.GAIN_HIT, fx, shake=1.5, stop=1.3)
        if targets:                                                        # 맞으면 튕겨 올라 다시 뛸 수 있다
            p.vy = config.PLUNGE_BOUNCE
            p.jump_count = min(p.jump_count, 1)

    # ----- 판정 도형 -----
    @staticmethod
    def _within(enemy, cx, cy, reach):
        left, bottom, right, top = enemy.rect()
        nx, ny = min(max(cx, left), right), min(max(cy, bottom), top)
        return math.hypot(nx - cx, ny - cy) <= reach

    @staticmethod
    def _in_arc(enemy, cx, cy, ax, ay, enhanced=False):
        """적 충돌 박스가 몸 중심에서 사거리 안에 있고, 중심이 조준 부채꼴 안에 있으면 맞는다."""
        left, bottom, right, top = enemy.rect()
        nearest_x = min(max(cx, left), right)
        nearest_y = min(max(cy, bottom), top)
        reach = config.PIPE_REACH * (config.ENHANCE_REACH_MULT if enhanced else 1.0)
        if math.hypot(nearest_x - cx, nearest_y - cy) > reach:
            return False
        ex, ey = enemy.center
        dx, dy = ex - cx, ey - cy
        dist = math.hypot(dx, dy)
        if dist < 1.0 or (left <= cx <= right and bottom <= cy <= top):
            return True
        cos_angle = (dx * ax + dy * ay) / dist
        arc = config.PIPE_ARC_DEG + (config.ENHANCE_ARC_BONUS_DEG if enhanced else 0)
        return cos_angle >= math.cos(math.radians(arc))
