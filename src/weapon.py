"""무기. 지금은 철파이프(충전형 3연타)만 있다. 식칼·건틀릿·사슬은 이후 주차에 같은 모양으로 추가한다.

공격은 이동 상태 머신 밖의 겹침(overlay)이다. 누른 순간 조준 방향 부채꼴 안의 적에게 바로 피해를 준다.
대미지는 항상 기본 x 게이지 구간 배율(x 강화 배율)이다.
"""
import math

import assets
import config
import effects
import game_world


class Pipe:
    def __init__(self, owner):
        self.owner = owner
        self.combo = 0            # 지금까지 이어 친 횟수 (1~3)
        self.cooldown = 0.0       # 다음 공격까지 남은 시간
        self.combo_left = 0.0     # 이 시간이 지나면 연타가 끊긴다

    def update(self, dt):
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.combo_left > 0:
            self.combo_left = max(0.0, self.combo_left - dt)
            if self.combo_left == 0:
                self.combo = 0

    @property
    def ready(self):
        return self.cooldown <= 0

    def try_attack(self):
        """공격을 시도한다. 공격했으면 True."""
        if not self.ready:
            return False
        p = self.owner
        self.combo = self.combo % 3 + 1
        finisher = self.combo == 3
        self.cooldown = config.PIPE_COOLDOWN[self.combo - 1]
        self.combo_left = self.cooldown + config.PIPE_COMBO_WINDOW

        ax, ay = p.aim_vector()
        cx, cy = p.center
        assets.play_sound('swing')
        effects.spawn('heavy-cleave', cx + ax * 70, cy + ay * 70, flip=ax < 0, duration=0.24)

        enhanced = p.gauge.enhanced
        mult = p.gauge.zone_multipliers()['attack'] * (config.PIPE_FINISHER_MULT if finisher else 1.0)
        if enhanced:
            mult *= config.ENHANCE_DAMAGE_MULT
        damage = config.PIPE_DAMAGE * mult
        gain = config.PIPE_FINISHER_GAIN if finisher else config.GAIN_HIT
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if enemy.alive and self._in_arc(enemy, cx, cy, ax, ay, enhanced):
                killed = enemy.take_damage(damage, from_x=p.x)
                p.gauge.add(gain, 'hit')
                effects.spawn('crit-hit' if enhanced else 'hit-spark', *enemy.center, duration=0.3 if enhanced else 0.22)
                effects.request_hit_stop(config.HIT_STOP * (2 if finisher else 1))
                effects.add_trauma(config.SHAKE_FINISHER if finisher else config.SHAKE_HIT)
                if killed:
                    p.gauge.add(config.GAIN_KILL, 'kill')
                    effects.add_trauma(config.SHAKE_KILL)
                    if enhanced:
                        self._blast(enemy)
        return True

    def _blast(self, dead):
        """강화 무기로 처치한 적은 작은 안개 폭발을 일으켜 주변 적에게 피해를 준다."""
        p = self.owner
        bx, by = dead.center
        effects.spawn('plasma-explosion', bx, by, duration=0.5)
        effects.add_trauma(config.SHAKE_FINISHER)
        for other in list(game_world.world[game_world.LAYER_ENEMY]):
            if other.alive and other is not dead:
                ox, oy = other.center
                if math.hypot(ox - bx, oy - by) <= config.ENHANCE_BLAST_RADIUS:
                    if other.take_damage(config.ENHANCE_BLAST_DAMAGE, from_x=bx):
                        p.gauge.add(config.GAIN_KILL, 'kill')

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
