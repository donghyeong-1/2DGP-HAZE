"""무기. 철파이프(기본), 투척용 식칼 묶음(구간 연동형), 헤이즈 건틀릿(소모형), 헤이즈 사슬(제어형).
장착 2칸(철파이프 + 하나), Q·1·2로 바꾼다. 식칼·건틀릿·사슬은 아래쪽 클래스를 본다.

공격은 이동 상태 머신 밖의 겹침(overlay)이다. 어떤 공격이 나가는지는 상황으로 정해진다:
  대시 평타(대시 중·직후) > 점프 평타(공중: 회전 베기, 아래를 겨누면 내려찍기) > 기본 3연타.
**강화(E)는 공격 종류를 바꾸지 않고 지금 나가는 공격에 얹힌다 (1회성).** 강화된 기본 공격은 X자 일격, 강화된 대시 평타는
지나온 경로를 넓고 크게 베고, 강화된 점프 평타는 더 큰 회전 베기, 강화된 내려찍기는 더 길고 넓다. 모두 대미지가 크고
맞은 적마다 안개 폭발이 퍼지며, 쓰고 나면 강화는 사라진다.

대시 평타는 **대시가 지나온 직선 경로**를 한 번에 벤다(관통): 대시 중에 누르면 대시가 끝나는 순간, 끝난 직후(0.22초)에
누르면 바로 터진다. 모든 근접 판정은 **시야선**을 본다: 벽(#) 너머의 적은 맞지 않는다.
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


class ExtraHits:
    """첫 타격 뒤에 같은 적에게 이어지는 추가 타격 (게이지 구간·강화로 타수가 늘어난다). 짧은 간격으로 작은 불꽃과 숫자가 튄다."""

    def __init__(self, owner, enemy, damage, fx, count, big):
        self.owner, self.enemy, self.damage, self.fx = owner, enemy, damage, fx
        self.left, self.big = count, big
        self.index = 0
        self.timer = config.EXTRA_HIT_INTERVAL

    def update(self, dt):
        self.timer -= dt
        if self.timer > 0:
            return
        self.timer += config.EXTRA_HIT_INTERVAL
        enemy, p = self.enemy, self.owner
        if not enemy.alive or p.state == 'DEAD':
            game_world.remove_object(self)
            return
        killed = enemy.take_damage(self.damage, from_x=p.x)
        p.gauge.add(config.EXTRA_HIT_GAIN, 'hit')
        ex, ey = enemy.center
        jx, jy = ((-1) ** self.index) * (10 + 6 * self.index), (self.index % 2) * 14 - 7      # 불꽃이 조금씩 다른 자리에 튄다
        effects.spawn(self.fx['spark'], ex + jx, ey + jy, duration=self.fx['spark_time'])
        effects.spawn_impact(ex + jx, ey + jy, ex - p.x, ey - p.center[1], config.IMPACT_RAYS_EXTRA, self.fx['damage_color'])
        effects.float_text(ex + jx * 2, ey + enemy.hb_h / 2 + 70 + 22 * (self.index + 1), str(int(round(self.damage))),
                           self.fx['damage_color'], big=False, life=0.5)
        effects.add_trauma(config.SHAKE_HIT * 0.5)
        assets.play_sound('enemy_hit')
        if killed:
            p.gauge.add(config.GAIN_KILL + p.kill_bonus, 'kill')
            effects.add_trauma(config.SHAKE_KILL)
        self.index += 1
        self.left -= 1
        if killed or self.left <= 0:
            game_world.remove_object(self)

    def draw(self):
        pass


class Pipe:
    name = '철파이프'
    weapon_id = 'pipe'
    base_damage = config.PIPE_DAMAGE

    def __init__(self, owner):
        self.owner = owner
        self.cooldown_max = 0.3   # 지금 쿨타임의 처음 길이 (재충전 바 표시용)
        self.combo = 0            # 지금까지 이어 친 횟수 (1~3)
        self.cooldown = 0.0       # 다음 공격까지 남은 시간
        self.combo_left = 0.0     # 이 시간이 지나면 연타가 끊긴다
        self.last_kind = None     # 마지막으로 나간 공격 종류 (pipe / dash / spin / plunge)
        self.last_enhanced = False   # 그 공격이 강화 일격이었는가

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
        enhanced = self.owner.gauge.enhanced
        self.last_kind, self.last_enhanced = kind, enhanced
        getattr(self, '_attack_' + kind)(enhanced)
        return True

    # ----- 공통 -----
    def _fx(self, enhanced):
        p = self.owner
        return config.ENHANCED_FX if enhanced else config.ZONE_FX[p.gauge.zone]

    def _visible(self, enemy, cx, cy):
        """(cx, cy)에서 적의 몸 어느 한 곳이라도 벽에 안 막히고 보이는가."""
        room = self.owner.room
        if room is None:
            return True
        return any(not room.line_blocked(cx, cy, px, py) for px, py in _enemy_points(enemy))

    def _targets(self, test, origin=None):
        p = self.owner
        cx, cy = origin or p.center
        return [e for e in list(game_world.world[game_world.LAYER_ENEMY])
                if e.alive and test(e) and self._visible(e, cx, cy)]

    def _hit(self, enemy, damage, gain, fx, big=False, color=None, shake=1.0, stop=1.0, blast=False, extra=True):
        """적 하나에게 피해와 모든 맞는 반응(게이지, 불꽃, 숫자, 흔들림, 멈춤)을 준다. 죽였으면 True."""
        p = self.owner
        killed = enemy.take_damage(damage, from_x=p.x)
        p.gauge.add(gain, 'hit')
        ex, ey = enemy.center
        effects.spawn(fx['spark'], ex, ey, duration=fx['spark_time'])
        rays = config.IMPACT_RAYS['enhanced' if fx is config.ENHANCED_FX else p.gauge.zone]
        effects.spawn_impact(ex, ey, ex - p.x, ey - p.center[1], rays, fx['damage_color'], big=big)       # 충격 방사선
        effects.float_text(ex, ey + enemy.hb_h / 2 + 70, str(int(round(damage))), color or fx['damage_color'], big=big)
        effects.request_hit_stop(config.HIT_STOP * stop * fx['stop'])
        p.swing_connected = True                         # 이번 휘두르기가 맞았다: 몸은 젖힘으로 되돌아가지 않는다
        effects.add_trauma(config.SHAKE_HIT * shake * fx['shake'])
        if killed:
            p.gauge.add(config.GAIN_KILL + p.kill_bonus, 'kill')
            effects.add_trauma(config.SHAKE_KILL)
        if blast:
            self._blast(enemy)
        if not extra:                                    # 식칼·건틀릿은 구간 효과가 발사 수·크기로 따로 있다
            return killed
        extra = max(config.EXTRA_HITS.get(p.gauge.zone, 0), config.ENHANCED_EXTRA_HITS if fx is config.ENHANCED_FX else 0)
        if extra and not killed:                         # 타수 증가: 첫 타격 뒤에 작은 추가 타격이 이어진다
            game_world.add_object(ExtraHits(p, enemy, damage * config.EXTRA_HIT_RATIO, fx, extra, big), game_world.LAYER_EFFECT)
        return killed

    def _damage(self, mult):
        p = self.owner
        return self.base_damage * p.gauge.zone_multipliers()['attack'] * p.attack_bonus * mult

    def _weak(self):
        """약해진 상태(페이드)인가. 이때는 모든 공격의 범위가 줄고 대시·점프 공격의 추가 배율이 사라진다."""
        return self.owner.gauge.zone in ('FADE', 'DEAD')

    def _reach(self):
        return config.FADE_REACH if self._weak() else 1.0

    def _special(self, mult):
        """대시·점프·내려찍기의 추가 피해 배율. 페이드에서는 기본 공격과 같은 1.0."""
        return 1.0 if self._weak() else mult

    @staticmethod
    def _segment_hit(enemy, x0, y0, dx, dy, length, half_width):
        """(x0, y0)에서 단위 방향 (dx, dy)로 length만큼 뻗은 직선(반폭 half_width)이 적의 충돌 박스에 닿는가 (관통 판정)."""
        left, bottom, right, top = enemy.rect()
        steps = max(2, int(length // 20))
        for i in range(steps + 1):
            x, y = x0 + dx * length * i / steps, y0 + dy * length * i / steps
            if left - half_width <= x <= right + half_width and bottom - half_width <= y <= top + half_width:
                return True
        return False

    def _finish(self, enhanced):
        if enhanced:
            self.owner.gauge.consume_enhance()          # 강화는 한 번뿐: 쓴 순간 준비가 끝난다

    # ----- 기본 공격 (3연타, 강화되면 X자 일격) -----
    def _attack_pipe(self, enhanced):
        p = self.owner
        ax, ay = p.aim_vector()
        cx, cy = p.center
        fx = self._fx(enhanced)                          # 게이지 구간(또는 강화)에 따라 모양·색·반응이 다르다
        p.start_swing(ax, ay)                            # 철파이프를 든 공격 자세
        effects.spawn_smear(('n09_swing_' + p.swing_dir, 2), p.x, p.y, p.face_dir, (ax, ay), enhanced)   # 휘두르는 몸의 잔상
        assets.play_sound(fx['sound'])
        variant, flip = effects.slash_variant(ax, ay)
        if enhanced:
            self.combo = 0
            p.set_swing_style(3, ax)                     # 강화 일격은 3타처럼 크게 끌어 내딛는다
            self.cooldown = config.ENHANCE_STRIKE_COOLDOWN
            effects.spawn(fx['slash'], cx, cy, flip=flip, duration=0.24, variant=variant)
            effects.add_trauma(config.SHAKE_FINISHER)
            damage = self._damage(config.ENHANCE_DAMAGE_MULT)
            for enemy in self._targets(lambda e: self._in_arc(e, cx, cy, ax, ay, enhanced=True, scale=self._reach())):
                self._hit(enemy, damage, config.PIPE_FINISHER_GAIN, fx, big=True, shake=2.0, stop=2, blast=True)
            self._finish(True)
            return
        self.combo = self.combo % 3 + 1
        finisher = self.combo == 3
        p.set_swing_style(self.combo, ax)                # 1타·2타·3타마다 자세 시간과 내딛기가 다르다
        self.cooldown = self.cooldown_max = config.PIPE_COOLDOWN[self.combo - 1]
        self.combo_left = self.cooldown + config.PIPE_COMBO_WINDOW
        effects.spawn(effects.slash_sheet(p.gauge.zone, finisher), cx, cy, flip=flip, duration=0.22, variant=variant)
        damage = self._damage(config.PIPE_FINISHER_MULT if finisher else 1.0)
        gain = config.PIPE_FINISHER_GAIN if finisher else config.GAIN_HIT
        color = config.DAMAGE_COLOR_FINISHER if finisher else None
        for enemy in self._targets(lambda e: self._in_arc(e, cx, cy, ax, ay, scale=self._reach())):
            self._hit(enemy, damage, gain, fx, big=finisher, color=color,
                      shake=config.SHAKE_FINISHER / config.SHAKE_HIT if finisher else 1.0, stop=2 if finisher else 1)

    def _blast(self, hit):
        """강화된 공격에 맞은 적 주위로 안개 폭발이 퍼져 주변 적에게 피해를 준다 (벽 너머에는 닿지 않는다)."""
        p = self.owner
        bx, by = hit.center
        effects.spawn('haze-blast', bx, by, duration=0.45)
        effects.add_trauma(config.SHAKE_FINISHER)
        for other in list(game_world.world[game_world.LAYER_ENEMY]):
            if other.alive and other is not hit:
                ox, oy = other.center
                if math.hypot(ox - bx, oy - by) <= config.ENHANCE_BLAST_RADIUS and (
                        p.room is None or not p.room.line_blocked(bx, by, ox, oy)):
                    if other.take_damage(config.ENHANCE_BLAST_DAMAGE, from_x=bx):
                        p.gauge.add(config.GAIN_KILL + p.kill_bonus, 'kill')

    # ----- 대시 평타: 지나온 경로를 한 줄로 베는 직선 베기 (관통) -----
    def _attack_dash(self, enhanced):
        p = self.owner
        self.cooldown = config.ENHANCE_STRIKE_COOLDOWN if enhanced else config.DASH_STRIKE_COOLDOWN
        assets.play_sound(self._fx(enhanced)['sound'])
        if p.state == 'DASH':                            # 대시 중: 끝나는 순간 지나온 경로를 벤다
            p.dash_strike_queued = True
            p.dash_strike_enhanced = enhanced
            if enhanced:
                p.gauge.consume_enhance()                # 강화는 이 대시 평타에 쓰인다
            return
        self.resolve_dash_strike(enhanced)               # 막 끝난 직후: 바로 벤다

    def resolve_dash_strike(self, enhanced, path=None):
        """대시가 지나온 직선(시작 -> 끝)에 있는 적을 모두 벤다. 시야가 벽에 막힌 적은 제외한다."""
        p = self.owner
        path = path or p.last_dash_path
        if path is None:
            self._finish(enhanced)
            return
        x0, y0, x1, y1 = path
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 8:
            self._finish(enhanced)
            return
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        fx = self._fx(enhanced)
        half = (config.DASH_STRIKE_ENHANCED_HALF_WIDTH if enhanced else config.DASH_STRIKE_HALF_WIDTH) * self._reach()
        effects.spawn_path_slash(x0, y0, x1, y1, enhanced)
        damage = self._damage(config.ENHANCE_DAMAGE_MULT if enhanced else self._special(config.DASH_STRIKE_MULT))
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or not self._segment_hit(enemy, x0, y0, dx, dy, length, half):
                continue
            ex, ey = enemy.center
            t = max(0.0, min(length, (ex - x0) * dx + (ey - y0) * dy))       # 경로에서 이 적에 가장 가까운 지점
            if not self._visible(enemy, x0 + dx * t, y0 + dy * t):
                continue
            self._hit(enemy, damage, config.PIPE_FINISHER_GAIN if enhanced else config.GAIN_HIT, fx, big=enhanced,
                      shake=1.8 if enhanced else 1.2, blast=enhanced)
        if enhanced:
            effects.add_trauma(config.SHAKE_FINISHER)
        self._finish(enhanced)

    # ----- 점프 평타: 회전 베기 / 내려찍기 -----
    def _attack_spin(self, enhanced):
        p = self.owner
        self.cooldown = config.ENHANCE_STRIKE_COOLDOWN if enhanced else config.AIR_COOLDOWN
        cx, cy = p.center
        fx = self._fx(enhanced)
        assets.play_sound(fx['sound'])
        effects.spawn(effects.special_sheet('spin', enhanced)[0], cx, cy, duration=0.26)
        p.vy = max(p.vy, config.AIR_HOP)                                  # 살짝 떠오르며 한 바퀴 돈다
        reach = config.AIR_SPIN_REACH * (config.ENHANCE_REACH_MULT if enhanced else 1.0) * self._reach()
        damage = self._damage(config.ENHANCE_DAMAGE_MULT if enhanced else self._special(config.AIR_SPIN_MULT))
        for enemy in self._targets(lambda e: self._within(e, cx, cy, reach)):
            self._hit(enemy, damage, config.PIPE_FINISHER_GAIN if enhanced else config.GAIN_HIT, fx, big=enhanced,
                      shake=1.8 if enhanced else 1.1, blast=enhanced)
        if enhanced:
            effects.add_trauma(config.SHAKE_FINISHER)
        self._finish(enhanced)

    def _attack_plunge(self, enhanced):
        p = self.owner
        self.cooldown = config.ENHANCE_STRIKE_COOLDOWN if enhanced else config.PLUNGE_COOLDOWN
        cx, cy = p.center
        fx = self._fx(enhanced)
        assets.play_sound(fx['sound'])
        p.start_plunge_pose()
        sheet, _ = effects.special_sheet('plunge', enhanced)
        effects.spawn(sheet, cx, cy, duration=0.26, variant=4)             # 아래 방향 변형
        k = (1.35 if enhanced else 1.0) * self._reach()
        damage = self._damage(config.ENHANCE_DAMAGE_MULT if enhanced else self._special(config.PLUNGE_MULT))
        targets = self._targets(lambda e: self._segment_hit(e, cx, cy, 0.0, -1.0, config.PLUNGE_LENGTH * k,
                                                             config.PLUNGE_HALF_WIDTH * k))
        for enemy in targets:
            self._hit(enemy, damage, config.PIPE_FINISHER_GAIN if enhanced else config.GAIN_HIT, fx, big=enhanced,
                      shake=1.9 if enhanced else 1.5, stop=1.3, blast=enhanced)
        if targets:                                                        # 맞으면 튕겨 올라 다시 뛸 수 있다
            p.vy = config.PLUNGE_BOUNCE
            p.jump_count = min(p.jump_count, 1)
        self._finish(enhanced)

    # ----- 판정 도형 -----
    @staticmethod
    def _within(enemy, cx, cy, reach):
        left, bottom, right, top = enemy.rect()
        nx, ny = min(max(cx, left), right), min(max(cy, bottom), top)
        return math.hypot(nx - cx, ny - cy) <= reach

    @staticmethod
    def _in_arc(enemy, cx, cy, ax, ay, enhanced=False, scale=1.0):
        """적 충돌 박스가 몸 중심에서 사거리 안에 있고, 중심이 조준 부채꼴 안에 있으면 맞는다."""
        left, bottom, right, top = enemy.rect()
        nearest_x = min(max(cx, left), right)
        nearest_y = min(max(cy, bottom), top)
        reach = config.PIPE_REACH * (config.ENHANCE_REACH_MULT if enhanced else 1.0) * scale
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


# =====================================================================================================
# 투척용 식칼 묶음 (원거리, 구간 연동형): 구간이 오를수록 한 번에 던지는 칼이 늘고, 위험 구간에서는 관통한다.
# 노멀 2발(나란히) / 각성 3발 부채꼴 / 위험 3발 관통 / 페이드 1발. E 강화: 발사 수 +2, 모든 칼 관통.
# 칼은 실행 중 회전하지 않고 8방향 그림(proj_knife_0~7) 중 가장 가까운 것을 쓴다.
# =====================================================================================================
class Knife(Pipe):
    name = '식칼'
    weapon_id = 'knife'
    base_damage = config.KNIFE_DAMAGE

    def current_kind(self):
        return 'knife'

    def volley(self, enhanced=None):
        """지금 구간에서 던지는 (칼 수, 퍼지는 각도, 관통)."""
        p = self.owner
        enhanced = p.gauge.enhanced if enhanced is None else enhanced
        count, spread, pierce = config.KNIFE_ZONE[p.gauge.zone]
        if enhanced:
            count, spread, pierce = count + config.KNIFE_ENHANCED_EXTRA, max(spread, 10), True
        return count, spread, pierce

    def try_attack(self):
        if not self.ready:
            return False
        p = self.owner
        enhanced = p.gauge.enhanced
        self.last_kind, self.last_enhanced = 'knife', enhanced
        count, spread, pierce = self.volley(enhanced)
        ax, ay = p.aim_vector()
        base = math.degrees(math.atan2(ay, ax))
        cx, cy = p.center
        fx = self._fx(enhanced)
        damage = self._damage(config.ENHANCE_DAMAGE_MULT * 0.6 if enhanced else 1.0)
        for i in range(count):
            off = 0.0 if count == 1 else -spread + 2 * spread * i / (count - 1)
            a = math.radians(base + off)
            game_world.add_object(ThrownKnife(self, cx, cy + 8, math.cos(a), math.sin(a), damage, pierce, fx, enhanced),
                                  game_world.LAYER_EFFECT)
        assets.play_sound('throw')
        p.start_punch('throw')
        self.cooldown = self.cooldown_max = config.ENHANCE_STRIKE_COOLDOWN if enhanced else config.KNIFE_COOLDOWN
        if enhanced:
            effects.add_trauma(config.SHAKE_FINISHER * 0.6)
        self._finish(enhanced)
        return True


class ThrownKnife:
    """날아가는 칼 한 자루. 벽(#)에 닿거나 사거리를 넘으면 사라지고, 관통이 아니면 첫 적에서 멈춘다."""

    def __init__(self, weapon, x, y, dx, dy, damage, pierce, fx, enhanced):
        self.weapon, self.x, self.y = weapon, x, y
        self.dx, self.dy = dx, dy
        self.damage, self.pierce, self.fx, self.enhanced = damage, pierce, fx, enhanced
        self.travel = 0.0
        self.hit = set()
        self.frame = int(round(math.degrees(math.atan2(dy, dx)) / 45.0)) % 8   # 가장 가까운 8방향 그림

    def rect(self):
        h = config.KNIFE_HB / 2
        return (self.x - h, self.y - h, self.x + h, self.y + h)

    def update(self, dt):
        step = config.KNIFE_SPEED * dt
        self.x += self.dx * step
        self.y += self.dy * step
        self.travel += step
        room = self.weapon.owner.room
        if self.travel > config.KNIFE_RANGE or (room is not None and room.tile_at_world(self.x, self.y) == '#'):
            effects.spawn('puff', self.x, self.y - 20, duration=0.2)
            game_world.remove_object(self)
            return
        left, bottom, right, top = self.rect()
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or id(enemy) in self.hit:
                continue
            el, eb, er, et = enemy.rect()
            if left < er and el < right and bottom < et and eb < top:
                self.hit.add(id(enemy))
                self.weapon._hit(enemy, self.damage, config.KNIFE_GAIN, self.fx, big=self.enhanced,
                                 shake=0.5, stop=0.35, blast=self.enhanced, extra=False)
                if not self.pierce:
                    game_world.remove_object(self)
                    return

    def draw(self):
        img = assets.image(f'sprites/unified/proj_knife_{self.frame}.png')
        assets.draw_image(img, self.x, self.y - img.h // 2)


# =====================================================================================================
# 헤이즈 건틀릿 (특수, 소모형): 좌클릭을 누르는 동안 게이지를 초당 10%씩 태워(5% 아래로는 안 내려감) 충전하고,
# 떼면 조준 방향으로 충격파를 쏜다. 충전이 많을수록 세다. 게이지가 너무 오를 때 일부러 쓰는 "배출" 무기다.
# 노멀: 충전 1.2초 / 각성: 0.8초, 충격파 x1.3 / 위험: 충전 없이 즉시 발사, 게이지 -15% 고정, 충격파 x1.6.
# E 강화: 충전 시간 절반, 충격파 크기·피해 x1.5.
# =====================================================================================================
class Gauntlet(Pipe):
    name = '건틀릿'
    weapon_id = 'gauntlet'
    base_damage = config.GAUNTLET_DAMAGE

    def __init__(self, owner):
        super().__init__(owner)
        self.charging = False
        self.charge = 0.0
        self.warned_empty = False      # 이번 충전에서 '게이지 부족'을 이미 알렸는지

    def current_kind(self):
        if self.charging:
            return 'charge'
        g = self.owner.gauge
        return 'gauntlet_instant' if g.zone == 'CRITICAL' and not g.enhanced else 'gauntlet'

    def charge_need(self):
        p = self.owner
        need = config.GAUNTLET_CHARGE_TIME.get(p.gauge.zone, config.GAUNTLET_CHARGE_TIME['NORMAL'])
        return need * (0.5 if p.gauge.enhanced else 1.0)

    @property
    def charge_ratio(self):
        return min(1.0, self.charge / max(self.charge_need(), 0.01)) if self.charging else 0.0

    def try_attack(self):
        if not self.ready or self.charging:
            return False
        p = self.owner
        if p.gauge.zone == 'CRITICAL' and not p.gauge.enhanced:     # 위험: 충전 없이 즉시, 게이지를 크게 비운다
            p.gauge.add(-config.GAUNTLET_CRIT_COST, 'gauntlet')
            self._fire(1.0, enhanced=False, size=config.GAUNTLET_SIZE['CRITICAL'])
            return True
        self.charging, self.charge, self.warned_empty = True, 0.0, False
        self.last_kind = 'charge'
        assets.play_sound('enhance')
        return True

    def update(self, dt):
        super().update(dt)
        if not self.charging:
            return
        p = self.owner
        if p.state in ('HIT', 'DEAD') or p.stunned:                 # 맞거나 기절하면 충전이 풀린다
            self.charging = False
            return
        if not p.attack_held:
            self.release()
            return
        if self.charge >= self.charge_need():
            return                                                  # 다 찼다: 더 태우지 않고 쥐고 있는다
        # 누르는 동안 게이지를 태운다. 태운 만큼만 찬다: 하한(GAUNTLET_FLOOR)에 닿으면 태울 게이지가 없어 더 차지 않는다
        want = config.GAUNTLET_DRAIN * dt
        before = p.gauge.value
        p.gauge.drain(want)
        burnt = before - p.gauge.value
        self.charge += dt * min(1.0, burnt / want)
        if burnt < want * 0.5 and not self.warned_empty:
            self.warned_empty = True
            effects.float_text(p.x, p.y + config.PLAYER_HB_H + 40, '게이지 부족', (150, 200, 255))

    def release(self):
        if not self.charging:
            return
        ratio = self.charge_ratio
        self.charging = False
        if ratio < config.GAUNTLET_MIN_RATIO:                      # 너무 짧게 누르면 헛손질
            self.cooldown = self.cooldown_max = 0.15
            effects.spawn('puff', *self.owner.center, duration=0.25)
            return
        enhanced = self.owner.gauge.enhanced
        size = config.GAUNTLET_SIZE.get(self.owner.gauge.zone, 1.0) * (config.GAUNTLET_ENHANCED_MULT if enhanced else 1.0)
        self._fire(ratio, enhanced, size)

    def _fire(self, ratio, enhanced, size):
        p = self.owner
        ax, ay = p.aim_vector()
        cx, cy = p.center
        fx = self._fx(enhanced)
        damage = self._damage(0.4 + 0.6 * ratio) * (config.GAUNTLET_ENHANCED_MULT if enhanced else 1.0)
        game_world.add_object(Blast(self, cx + ax * 40, cy + ay * 40, ax, ay, damage, size, fx, enhanced),
                              game_world.LAYER_EFFECT)
        self.last_kind, self.last_enhanced = 'gauntlet', enhanced
        p.start_punch('blast')
        assets.play_sound('overload_zap' if size >= 1.5 else fx['sound'])
        effects.add_trauma(0.25 + 0.25 * size)
        p.lunge_vx = -ax * 260 * size                                 # 반동으로 살짝 밀린다
        self.cooldown = self.cooldown_max = config.GAUNTLET_COOLDOWN
        self._finish(enhanced)


class Blast:
    """건틀릿 충격파. 조준 방향으로 날아가며 닿는 적을 모두 친다(관통). 벽에 닿으면 터진다."""

    def __init__(self, weapon, x, y, dx, dy, damage, size, fx, enhanced):
        self.weapon, self.x, self.y, self.dx, self.dy = weapon, x, y, dx, dy
        self.damage, self.size, self.fx, self.enhanced = damage, size, fx, enhanced
        self.radius = config.GAUNTLET_RADIUS * size
        self.life = config.GAUNTLET_LIFE
        self.time = 0.0
        self.hit = set()
        self.sprite = 's' if size < 1.2 else 'm' if size < 1.5 else 'l'

    def update(self, dt):
        self.time += dt
        self.life -= dt
        step = config.GAUNTLET_SPEED * dt
        self.x += self.dx * step
        self.y += self.dy * step
        room = self.weapon.owner.room
        if self.life <= 0 or (room is not None and room.tile_at_world(self.x, self.y) == '#'):
            effects.spawn('haze-blast', self.x, self.y - 40, duration=0.35)
            game_world.remove_object(self)
            return
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or id(enemy) in self.hit:
                continue
            if Pipe._within(enemy, self.x, self.y, self.radius):
                self.hit.add(id(enemy))
                self.weapon._hit(enemy, self.damage, config.GAIN_HIT, self.fx, big=self.size >= 1.5,
                                 shake=1.0 + 0.5 * self.size, stop=1.2, blast=self.enhanced, extra=False)

    def draw(self):
        img = assets.image(f'sprites/unified/proj_blast_{self.sprite}_{int(self.time * 16) % 2 + 1}.png')
        assets.draw_image(img, self.x, self.y - img.h // 2, 'h' if self.dx < 0 else '')


# =====================================================================================================
# 헤이즈 사슬 (중거리, 제어형): 조준 방향으로 갈고리를 던져 맞은 적을 플레이어 앞까지 끌어온다. 끌려온 적 1마리당 게이지 +2%.
# 노멀: 1마리 / 각성: 사거리 +30%, 2마리 / 위험: 각성 + 끌려온 적 1초 기절, 함께 끌려온 적끼리 부딪쳐 충돌 피해.
# E 강화: 사슬이 닿는 적을 모두 꿰고(관통) 끌려온 적은 1초 기절. 보스는 끌려오지 않는 대신 갈고리가 박혀 피해 x1.5.
# 갈고리가 돌아오기 전에는 다시 던지지 못한다. 사슬 그림은 코드로 그린 고리 칸이다(회전 없음).
# =====================================================================================================
class Chain(Pipe):
    name = '사슬'
    weapon_id = 'chain'
    base_damage = config.CHAIN_DAMAGE

    def __init__(self, owner):
        super().__init__(owner)
        self.hook = None               # 날아가거나 끌어오는 중인 갈고리 (없으면 던질 수 있다)

    @property
    def ready(self):
        return self.cooldown <= 0 and self.hook is None

    def current_kind(self):
        return 'chain'

    def grip(self, enhanced=None):
        """지금 구간에서 (끌 수 있는 적 수, 사거리, 끌려온 적 기절·충돌)."""
        p = self.owner
        enhanced = p.gauge.enhanced if enhanced is None else enhanced
        count, reach_mult, stun = config.CHAIN_ZONE[p.gauge.zone]
        if enhanced:
            count, stun = 99, True                                  # 관통: 닿는 적 모두
        return count, config.CHAIN_RANGE * reach_mult, stun

    def try_attack(self):
        if not self.ready:
            return False
        p = self.owner
        enhanced = p.gauge.enhanced
        self.last_kind, self.last_enhanced = 'chain', enhanced
        count, reach, stun = self.grip(enhanced)
        ax, ay = p.aim_vector()
        damage = self._damage(config.ENHANCE_DAMAGE_MULT * 0.6 if enhanced else 1.0)
        self.hook = ChainHook(self, ax, ay, damage, count, reach, stun, self._fx(enhanced), enhanced)
        game_world.add_object(self.hook, game_world.LAYER_EFFECT)
        assets.play_sound('throw')
        p.start_punch('throw')
        self.cooldown = self.cooldown_max = config.CHAIN_COOLDOWN
        if enhanced:
            effects.add_trauma(config.SHAKE_FINISHER * 0.5)
        self._finish(enhanced)
        return True


class ChainHook:
    """사슬 갈고리 하나. out(날아감) -> pull(걸린 적을 끌어옴) 또는 back(빈 갈고리가 돌아옴) -> 끝."""
    LINK = 12                          # 고리 사이 간격(px)

    def __init__(self, weapon, dx, dy, damage, count, reach, stun, fx, enhanced):
        self.weapon, self.dx, self.dy = weapon, dx, dy
        self.damage, self.count, self.reach, self.stun = damage, count, reach, stun
        self.fx, self.enhanced = fx, enhanced
        self.dist = 0.0                # 손에서 갈고리 끝까지 거리 (out·back)
        self.phase = 'out'
        self.hit = set()
        self.hooked = []               # 갈고리에 맞은 적 (보스 포함)
        self.pulled = []               # 그중 끌려오는 적
        self.pull_time = 0.0
        self.tip = self.origin()

    def origin(self):
        p = self.weapon.owner
        cx, cy = p.center
        return cx + self.dx * 20, cy + 8 + self.dy * 20

    # ----- 갱신 -----
    def update(self, dt):
        getattr(self, '_update_' + self.phase)(dt)

    def _update_out(self, dt):
        p = self.weapon.owner
        self.dist = min(self.reach, self.dist + config.CHAIN_SPEED * dt)
        ox, oy = self.origin()
        self.tip = (ox + self.dx * self.dist, oy + self.dy * self.dist)
        room = p.room
        if room is not None and room.tile_at_world(*self.tip) == '#':
            effects.spawn('puff', self.tip[0], self.tip[1] - 20, duration=0.2)
            self._end_out()
            return
        h = config.CHAIN_HOOK_HB / 2
        tx, ty = self.tip
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or id(enemy) in self.hit:
                continue
            el, eb, er, et = enemy.rect()
            if tx - h < er and el < tx + h and ty - h < et and eb < ty + h:
                self.hit.add(id(enemy))
                self.hooked.append(enemy)
                damage = self.damage * (1.0 if enemy.pullable else config.CHAIN_ANCHOR_MULT)   # 보스에게는 박혀서 더 아프다
                killed = self.weapon._hit(enemy, damage, config.CHAIN_GAIN, self.fx, big=self.enhanced,
                                          shake=0.7, stop=0.5, blast=self.enhanced, extra=False)
                if not killed and enemy.pullable:
                    self.pulled.append(enemy)
                    enemy.hold(0.2)
                if len(self.hooked) >= self.count:
                    self._end_out()
                    return
        if self.dist >= self.reach:
            self._end_out()

    def _end_out(self):
        self.phase = 'pull' if self.pulled else 'back'

    def _stop_x(self, index, enemy):
        """끌려온 index번째 적이 멈추는 x: 플레이어 앞에서부터 차례로 줄 선다."""
        p = self.weapon.owner
        side = 1 if enemy.x >= p.x else -1
        gap = p.hb_w / 2 + config.CHAIN_PULL_GAP
        for e in self.pulled[:index]:
            gap += e.hb_w
        return p.x + side * (gap + enemy.hb_w / 2)

    def _update_pull(self, dt):
        self.pull_time += dt
        alive = [e for e in self.pulled if e.alive]
        done = True
        for i, e in enumerate(alive):
            want = self._stop_x(i, e) - e.x
            if abs(want) <= 1.0:
                continue
            move = max(-config.CHAIN_PULL_SPEED * dt, min(config.CHAIN_PULL_SPEED * dt, want))
            moved = e.pull_step(move)
            e.hold(0.15)
            if abs(moved) >= abs(move) * 0.5 and abs(want - moved) > 1.0:
                done = False                                        # 아직 끌려오는 중 (벽에 막히면 거기서 멈춘다)
        if alive:
            self.tip = alive[0].center
        if done or not alive or self.pull_time >= config.CHAIN_PULL_MAX_TIME:
            self._arrive(alive)

    def _arrive(self, alive):
        """다 끌어왔다: 위험 구간·강화면 기절과 충돌, 아니면 짧은 경직."""
        p = self.weapon.owner
        for e in alive:
            e.hold(config.CHAIN_STUN if self.stun else 0.18)
        if self.stun and len(alive) >= 2:                           # 함께 끌려온 적끼리 부딪친다
            for e in alive:
                killed = e.take_damage(config.CHAIN_CLASH_DAMAGE, from_x=p.x)
                ex, ey = e.center
                effects.spawn(self.fx['spark'], ex, ey, duration=self.fx['spark_time'])
                effects.float_text(ex, ey + e.hb_h / 2 + 70, str(config.CHAIN_CLASH_DAMAGE), (255, 200, 120))
                if killed:
                    p.gauge.add(config.GAIN_KILL + p.kill_bonus, 'kill')
                else:
                    e.hold(config.CHAIN_STUN)                       # 충돌 경직이 기절을 줄이지 않게 다시 건다
            effects.add_trauma(config.SHAKE_FINISHER * 0.6)
            assets.play_sound('enemy_hit')
        self._done()

    def _update_back(self, dt):
        self.dist -= config.CHAIN_RETURN_SPEED * dt
        ox, oy = self.origin()
        self.tip = (ox + self.dx * max(0.0, self.dist), oy + self.dy * max(0.0, self.dist))
        if self.dist <= 0:
            self._done()

    def _done(self):
        w = self.weapon
        if w.hook is self:
            w.hook = None
        w.cooldown = w.cooldown_max = config.CHAIN_COOLDOWN
        game_world.remove_object(self)

    # ----- 그리기: 손에서 갈고리까지 고리 칸을 늘어놓는다 -----
    def draw(self):
        ox, oy = self.origin()
        tx, ty = self.tip
        length = math.hypot(tx - ox, ty - oy)
        glow = self.fx['damage_color'] if self.enhanced or self.stun else (186, 196, 210)
        for i in range(int(length // self.LINK) + 1):
            k = i * self.LINK / max(length, 1.0)
            x, y = int(ox + (tx - ox) * k), int(oy + (ty - oy) * k)
            assets.draw_rect_color(x - 4, y - 4, 8, 8, (12, 14, 22))                     # 외곽선
            if i % 2:
                assets.draw_rect_color(x - 3, y - 1, 6, 2, glow)                        # 눕힌 고리
            else:
                assets.draw_rect_color(x - 1, y - 3, 2, 6, glow)                        # 세운 고리
        x, y = int(tx), int(ty)
        assets.draw_rect_color(x - 8, y - 8, 16, 16, (12, 14, 22))                      # 갈고리 머리
        assets.draw_rect_color(x - 6, y - 6, 12, 12, (186, 196, 210))
        assets.draw_rect_color(x - 3, y - 3, 6, 6, (90, 210, 240))                      # 헤이즈 빛


WEAPONS = {'pipe': Pipe, 'knife': Knife, 'gauntlet': Gauntlet, 'chain': Chain}
