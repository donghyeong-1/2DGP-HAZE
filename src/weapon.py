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
import random
import time

import sprites

import assets
import config
import effects
import game_world


def _enemy_points(enemy):
    """적에게 닿는 시야선을 확인할 몸의 세 지점 (아래, 가운데, 위)."""
    left, bottom, right, top = enemy.rect()
    x = (left + right) / 2
    return [(x, bottom + 12), (x, (bottom + top) / 2), (x, top - 12)]


# ----- v7 증강 v2 진화·합성의 색과 장면 물체 (판정은 무기 메서드가 한다) -----
FRENZY_COLOR = (240, 248, 255)     # 난타: 흰 회전 궤적
BOLT_COLOR = (110, 240, 230)       # 낙뢰 내려찍기: 청록 번개
FLASH_COLOR = (150, 255, 245)      # 섬광 베기
ECHO_COLOR = (170, 205, 255)       # 잔영 대시 분신
VORTEX_COLOR = (190, 140, 255)     # 소용돌이 (보라)
NET_COLOR = (235, 150, 235)        # 사슬 묶기·헤이즈 그물


class DelayedFlash:
    """섬광 베기: 대시 공격이 지난 직선에 가는 빛줄이 남았다가, delay 뒤 번쩍이며 다시 벤다."""

    def __init__(self, weapon, path, half, damage, delay, net):
        self.weapon, self.path, self.half, self.damage, self.net = weapon, path, half, damage, net
        self.delay = self.left = delay

    def update(self, dt):
        self.left -= dt
        if self.left <= 0:
            game_world.remove_object(self)
            self.weapon.flash_strike(self.path, self.half, self.damage, self.net)

    def draw(self):
        x0, y0, x1, y1 = self.path
        k = 1.0 - max(0.0, self.left) / self.delay      # 터질 때가 가까울수록 진해진다
        length = math.hypot(x1 - x0, y1 - y0)
        for i in range(int(length // 10) + 1):
            t = i * 10 / max(length, 1.0)
            x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
            assets.draw_rect_color(x - 3, y - 1, 6, 2, FLASH_COLOR, 0.25 + 0.6 * k)


class BoltPillar:
    """낙뢰 내려찍기: 착지 지점에 화면 위에서 내리꽂는 청록 번개 기둥 (지그재그 사각형, 회전 없음)."""
    LIFE = 0.32
    HEIGHT = 520

    def __init__(self, x, y):
        self.x, self.y = int(x), int(y)
        self.life = self.LIFE
        rng = random.Random(int(x) * 31 + int(y))
        self.offsets = [rng.randint(-14, 14) for _ in range(self.HEIGHT // 26 + 1)]

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            game_world.remove_object(self)

    def draw(self):
        k = max(0.0, self.life / self.LIFE)
        width = int(10 + 14 * k)
        for i, ox in enumerate(self.offsets):
            y = self.y + i * 26
            assets.draw_rect_color(self.x + ox - width // 2 - 4, y, width + 8, 26, BOLT_COLOR, 0.35 * k)    # 번짐
            assets.draw_rect_color(self.x + ox - width // 2, y, width, 26, BOLT_COLOR, 0.85 * k)
            assets.draw_rect_color(self.x + ox - 3, y, 6, 26, (250, 255, 255), k)                           # 흰 심


class DashEcho:
    """잔영 대시: 대시를 시작한 자리에 분신이 남아, 잠시 뒤 대시 방향으로 기본 공격을 한 번 휘두른다.
    합성 '분신 연타'면 대신 난타 회전 베기 (몸 둘레)."""

    def __init__(self, player, path, spin):
        import mutations
        x0, y0, x1, y1 = path
        length = math.hypot(x1 - x0, y1 - y0)
        self.aim = ((x1 - x0) / length, (y1 - y0) / length) if length > 1 else (float(player.face_dir), 0.0)
        self.player, self.spin = player, spin
        self.cx, self.cy = x0, y0
        self.foot_y = y0 - (player.center[1] - player.y)
        self.face = 1 if self.aim[0] >= 0 else -1
        self.left = mutations.ECHO[0]
        game_world.add_object(effects.BodyGhost(('n09_dash', 1), x0, self.foot_y, self.face, ECHO_COLOR, 0.55, life=0.22),
                              game_world.LAYER_EFFECT)

    def update(self, dt):
        self.left -= dt
        if self.left <= 0:
            game_world.remove_object(self)
            self._swing()

    def _swing(self):
        import mutations
        p = self.player
        w = p.weapons[0] if getattr(p, 'weapons', None) else p.weapon        # 분신은 늘 철파이프를 휘두른다
        cx, cy = self.cx, self.cy
        ax, ay = self.aim
        fx = w._fx(False)
        game_world.add_object(effects.BodyGhost(('n09_swing_side', 2), cx, self.foot_y, self.face, ECHO_COLOR, 0.6, life=0.24),
                              game_world.LAYER_EFFECT)
        assets.play_sound('swing_2')
        if self.spin:
            reach = config.PIPE_REACH * mutations.FRENZY_REACH
            effects.spawn(effects.special_sheet('spin', False)[0], cx, cy, duration=0.26)
            effects.spawn_ring(cx, cy, FRENZY_COLOR, radius_max=int(reach), life=0.24)
            damage = w._damage(mutations.FRENZY_MULT[1] * mutations.ECHO[1])

            def test(e):
                return Pipe._within(e, cx, cy, reach)
        else:
            variant, flip = effects.slash_variant(ax, ay)
            effects.spawn(effects.slash_sheet(p.gauge.zone, False), cx, cy, flip=flip, duration=0.22, variant=variant)
            damage = w._damage(mutations.ECHO[1])

            def test(e):
                return Pipe._in_arc(e, cx, cy, ax, ay)
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if enemy.alive and test(enemy) and w._visible(enemy, cx, cy):
                w._hit(enemy, damage, config.GAIN_HIT, fx, big=self.spin, color=ECHO_COLOR, extra=False)

    def draw(self):
        pass


class SwordWave:
    """v8 연타 '검기': 3타의 베기가 조준 방향으로 날아간다. 지나가며 닿은 적을 한 번씩 베고(휘두르기에 이미 맞은 적은 빼고),
    벽에 닿거나 COMBO_WAVE[2]만큼 날면 사라진다. 그림은 3타 베기 시트를 지나간 자리에 짧게 남긴다."""

    def __init__(self, weapon, x, y, ax, ay, damage, skip=()):
        import mutations
        self.weapon, self.x, self.y = weapon, x, y
        n = math.hypot(ax, ay) or 1.0
        self.dx, self.dy = ax / n, ay / n
        self.damage = damage
        _mult, self.speed, self.reach, self.half = mutations.COMBO_WAVE
        self.travel = 0.0
        self.trail = 0.0
        self.hit = set(id(e) for e in skip)
        self.variant, self.flip = effects.slash_variant(ax, ay)

    def update(self, dt):
        step = self.speed * dt
        self.x += self.dx * step
        self.y += self.dy * step
        self.travel += step
        self.trail -= dt
        p = self.weapon.owner
        if self.trail <= 0:
            self.trail = 0.035
            effects.spawn(effects.slash_sheet(p.gauge.zone, True), self.x, self.y, flip=self.flip, duration=0.12,
                          variant=self.variant)
        room = p.room
        if self.travel > self.reach or (room is not None and room.tile_at_world(self.x, self.y) == '#'):
            effects.spawn_bloom(self.x, self.y, FRENZY_COLOR, life=0.1, strength=0.5)
            game_world.remove_object(self)
            return
        fx = self.weapon._fx(False)
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or id(enemy) in self.hit:
                continue
            left, bottom, right, top = enemy.rect()
            if left - self.half < self.x < right + self.half and bottom - self.half < self.y < top + self.half:
                self.hit.add(id(enemy))
                self.weapon._hit(enemy, self.damage, config.GAIN_HIT, fx, color=FRENZY_COLOR, shake=0.5, stop=0.5, extra=False)

    def draw(self):
        pass


class Vortex:
    """소용돌이 (사슬 진화): 끌어온 자리(플레이어 둘레)에 보라 소용돌이. 둘레 적을 pull초 동안 빨아들이고,
    끝나는 순간 작은 피해와 함께 hold_time초 묶는다. 보스는 끌려오지 않는다."""

    def __init__(self, weapon, damage):
        import mutations
        self.weapon = weapon
        self.radius, self.pull, self.hold_time, mult = mutations.VORTEX
        self.base_damage = damage
        self.damage = damage * mult
        self.age = 0.0
        self.fired = False                               # 다 빨아들여 묶었다. 그 뒤 hold_time 동안 남아 '묶인 적'을 알려 준다 (합성 '집중 탄막')
        self.caught = []
        p = weapon.owner
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            ex, ey = e.center
            if e.alive and getattr(e, 'pullable', True) and math.hypot(ex - p.x, ey - p.center[1]) <= self.radius:
                self.caught.append(e)
                e.hold(self.pull + 0.1)
        assets.play_sound('chain_clash')

    def update(self, dt):
        import mutations
        p = self.weapon.owner
        self.age += dt
        if self.fired:
            if self.age >= self.pull + self.hold_time:
                game_world.remove_object(self)
            return
        for e in self.caught:
            if not e.alive:
                continue
            want = p.x + (60 if e.x >= p.x else -60) - e.x
            if abs(want) > 1.0:
                e.pull_step(max(-700.0 * dt, min(700.0 * dt, want)))
        if self.age >= self.pull:
            self.fired = True
            for e in self.caught:
                if e.alive:
                    self.weapon._hit(e, self.damage, config.CHAIN_GAIN * 0.5, self.weapon._fx(False), color=VORTEX_COLOR,
                                     shake=0.6, stop=0.4, extra=False)
                    e.hold(self.hold_time)
            effects.spawn_ring(p.x, p.center[1], VORTEX_COLOR, radius_max=self.radius, life=0.3)
            effects.add_trauma(config.SHAKE_FINISHER * 0.5)
            if mutations.has(p, 'duo_vortex_collapse'):          # v8 합성 '끌어모아 한 방': 모인 자리에서 붕괴가 터진다
                _collapse_burst(self.weapon, (p.x, p.center[1]), self.base_damage * mutations.DUO_PULL_BLAST,
                                self.weapon._fx(False))

    def bound(self):
        """소용돌이에 묶여 있는 (살아 있는) 적들. 빨아들이는 동안은 아직 없다."""
        return [e for e in self.caught if e.alive] if self.fired else []

    def draw(self):
        if self.fired:
            return
        p = self.weapon.owner
        cx, cy = p.x, p.center[1]
        k = min(1.0, self.age / self.pull)
        for ring in range(3):
            r = self.radius * (1.0 - k) * (1.0 - ring * 0.28) + 24
            size = 8 - ring * 2
            for i in range(14):
                a = self.age * (9 + ring * 3) + i * math.tau / 14 + ring
                x, y = int(cx + math.cos(a) * r), int(cy + math.sin(a) * r * 0.55)
                assets.draw_rect_color(x - size // 2, y - size // 2, size, size, VORTEX_COLOR, 0.8 - ring * 0.2)


class LinkNet:
    """사슬 묶기 / 헤이즈 그물: 묶인 적들 사이에 사슬이 이어진다. 하나를 치면 나머지가 피해를 나눠 받는다
    (mutations.on_linked_hit). LINK_TIME이 지나거나 묶인 적이 하나만 남으면 풀린다."""

    def __init__(self, members):
        import mutations
        self.members = list(members)
        self.life = mutations.LINK_TIME
        self.active = True
        for e in self.members:
            old = getattr(e, 'haze_link', None)
            if old is not None and old is not self:
                old.release(e)
            e.haze_link = self

    def release(self, enemy):
        if enemy in self.members:
            self.members.remove(enemy)
        if getattr(enemy, 'haze_link', None) is self:
            enemy.haze_link = None

    def alive_members(self):
        return [e for e in self.members if e.alive]

    def update(self, dt):
        self.life -= dt
        if self.life <= 0 or len(self.alive_members()) < 2:
            self.active = False
            for e in list(self.members):
                self.release(e)
            game_world.remove_object(self)

    def draw(self):
        alive = self.alive_members()
        if self.life < 1.0 and int(self.life * 10) % 2:      # 풀리기 직전 깜빡인다
            return
        for a, b in zip(alive, alive[1:]):
            (ax, ay), (bx, by) = a.center, b.center
            length = math.hypot(bx - ax, by - ay)
            for i in range(int(length // 6) + 1):                  # 적 몸 위에서도 보이게 옅은 빛 띠를 먼저 깐다
                t = i * 6 / max(length, 1.0)
                x, y = int(ax + (bx - ax) * t), int(ay + (by - ay) * t)
                assets.draw_rect_color(x - 4, y - 4, 8, 8, NET_COLOR, 0.35)
            draw_chain_line(int(ax), int(ay), int(bx), int(by), (255, 210, 255), link=14)
        for e in alive:                                            # 묶인 적 머리 위 고리 표시 (붙어 서 있어도 보이게)
            left, _bottom, right, top = e.rect()
            mx, my = int((left + right) / 2), int(top) + 50          # 체력 바 위
            assets.draw_rect_color(mx - 9, my - 9, 18, 18, (12, 14, 22))
            assets.draw_rect_color(mx - 7, my - 7, 14, 14, NET_COLOR)
            assets.draw_rect_color(mx - 3, my - 3, 6, 6, (12, 14, 22))


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
        import drama
        with drama.hit_style(color=self.fx['damage_color']):
            killed = enemy.take_damage(self.damage, from_x=p.x)
        p.gauge.add(config.EXTRA_HIT_GAIN, 'hit')
        ex, ey = enemy.center
        jx, jy = ((-1) ** self.index) * (10 + 6 * self.index), (self.index % 2) * 14 - 7      # 불꽃이 조금씩 다른 자리에 튄다
        effects.spawn(self.fx['spark'], ex + jx, ey + jy, duration=self.fx['spark_time'])
        effects.spawn_impact(ex + jx, ey + jy, ex - p.x, ey - p.center[1], config.IMPACT_RAYS_EXTRA, self.fx['damage_color'])
        effects.spawn_slash_marks(ex + jx, ey + jy, ex - p.x, ey - p.center[1], self.fx['damage_color'])   # 다단 히트 자국
        effects.add_trauma(config.SHAKE_HIT * 0.5)       # 소리는 적이 재질 소리를 낸다 (v7)
        if killed:
            p.gauge.add(p.kill_gain(), 'kill')
            effects.add_trauma(config.SHAKE_KILL)
        self.index += 1
        self.left -= 1
        if killed or self.left <= 0:
            game_world.remove_object(self)

    def draw(self):
        pass


# ----- 대시 공격 v2 (2026-11-24 사용자 요청 "이나리 같은 대시 공격"): 표식 3개 -> 처형, 맞히면 대시 회복, 붉은 궤적 -----
EXEC_COLOR = (255, 64, 78)           # 표식·처형·대시 궤적 (진홍)
MARK_INK = (14, 6, 10)
X_SHAPE = [(i, i) for i in range(5)] + [(i, 4 - i) for i in range(5) if i != 2]   # 2px 칸 5x5 X


def dash_mark(weapon, enemy, killed):
    """대시 공격이 적을 맞혔다 (Pipe._hit이 부른다): 이 대시의 첫 적중이면 대시 한 칸 회복, 적마다 표식 하나(같은 대시로는 하나),
    표식이 DASH_MARKS개면 처형. 대시 공격이 아니면 아무것도 안 한다."""
    p = weapon.owner
    if getattr(p, 'dash_attack_left', 0.0) <= 0 or id(enemy) in p.dash_marked:
        return
    p.dash_marked.add(id(enemy))
    if not p.dash_refunded:
        p.dash_refunded = True
        if p.dash_slots < p.dash_max:
            p.dash_slots += 1                                        # 대시 -> 베기 -> 대시
        effects.spawn_bloom(*p.center, (150, 230, 255), life=0.12, strength=0.5)
    if killed or not enemy.alive:
        return
    import mutations
    add = 2 if mutations.has(p, 'dashcut_refund') else 1          # v7 '깊은 낙인' (11/24 '흐름'을 바꿈)
    enemy.dash_marks = min(config.DASH_MARKS, getattr(enemy, 'dash_marks', 0) + add)
    enemy.dash_mark_left = config.DASH_MARK_TIME
    tag = getattr(enemy, 'mark_tag', None)
    if tag is None or tag.gone:
        enemy.mark_tag = MarkTag(enemy)
        game_world.add_object(enemy.mark_tag, game_world.LAYER_EFFECT)
    enemy.mark_tag.pop = 0.12
    if enemy.dash_marks >= config.DASH_MARKS:
        enemy.dash_marks = 0
        game_world.add_object(DashExecution(weapon, enemy), game_world.LAYER_EFFECT)


class MarkTag:
    """적 머리 위 표식(붉은 X 1~3개). 쌓일 때 잠깐 크게 번쩍인다. 시간이 다 되거나 적이 죽으면 사라진다."""

    def __init__(self, enemy):
        self.enemy = enemy
        self.pop = 0.0
        self.gone = False

    def update(self, dt):
        e = self.enemy
        self.pop = max(0.0, self.pop - dt)
        e.dash_mark_left = getattr(e, 'dash_mark_left', 0.0) - dt
        if e.dash_mark_left <= 0:
            e.dash_marks = 0
        if not e.alive or getattr(e, 'dash_marks', 0) <= 0:
            self.gone = True
            game_world.remove_object(self)

    def draw(self):
        e = self.enemy
        n = e.dash_marks
        left, bottom, right, top = e.rect()
        cx = _snap((left + right) / 2)
        y0 = _snap(top + 44)                                          # 체력 막대보다 위
        for k in range(n):
            x0 = cx - (n * 26 - 6) // 2 + k * 26
            big = self.pop > 0 and k == n - 1
            u = 5 if big else 4                                       # 막 쌓인 표식은 칸이 크다 (정수 칸 크기만 바꾼다)
            for (a, b) in X_SHAPE:
                assets.draw_rect_color(x0 + a * u - 2, y0 + b * u - 2, u + 4, u + 4, MARK_INK)
            img = assets.image('light/dot_48.png')                    # 표식 뒤 붉은 빛
            img.opacify(0.5)
            assets.draw_image_added(img, x0 + 2 * u, y0 + 2 * u - img.h // 2, color=EXEC_COLOR, times=1)
            img.opacify(1.0)
            for (a, b) in X_SHAPE:
                assets.draw_rect_color(x0 + a * u, y0 + b * u, u, u, (255, 255, 255) if big else EXEC_COLOR)
        if n >= config.DASH_MARKS - 1:                                # 하나만 더: 몸에 금빛 마름모 (처형 예고)
            mx, my = cx, _snap((bottom + top) / 2)
            for r in (10, 8):
                c = MARK_INK if r == 10 else (255, 214, 110)
                for i in range(-r, r + 1, 2):
                    h = r - abs(i)
                    assets.draw_rect_color(mx + i, my + h, 2, 2, c)
                    assets.draw_rect_color(mx + i, my - h, 2, 2, c)


class Shatter:
    """조각나는 처치 (v8 4-3): 큰 공격으로 죽은 적의 그림을 몇 칸으로 잘라 공격 방향으로 흩뿌린다 (새 그림 없이 그 자리의 그림을 자른다).
    조각은 돌지 않고(픽셀 규칙: 회전 없음) 포물선으로 날아가다 깜빡이며 사라진다."""

    def __init__(self, frame, x, y, face, side):
        self.frame, self.x, self.y, self.face, self.side = frame, x, y, face, side
        self.t = 0.0
        cols, rows = config.SHATTER_PIECES
        rng = random.Random(int(x) * 31 + int(y))
        self.pieces = []                      # (칸 x, 칸 y, 속도 x, 속도 y)
        for r in range(rows):
            for c in range(cols):
                up = 200 + 300 * (r + 1) / rows + rng.uniform(-90, 90)       # 위쪽 조각일수록 높이 튄다
                out = (c - (cols - 1) / 2) * 260                             # 가운데에서 바깥으로 벌어진다
                self.pieces.append((c, r, side * rng.uniform(140, 380) + out + rng.uniform(-60, 60), up))

    def update(self, dt):
        self.t += dt
        if self.t >= config.SHATTER_LIFE:
            game_world.remove_object(self)

    def draw(self):
        name, n = sprites.resolve(*self.frame)
        img = assets.image(sprites.path(name, n))
        dx, foot = sprites.place(name, n, img.w, img.h, self.face)
        flip = 'h' if self.face < 0 else ''
        k = self.t / config.SHATTER_LIFE
        if k > 0.6 and int(self.t * 30) % 2 == 0:                       # 끝에는 깜빡이며 사라진다
            return
        cols, rows = config.SHATTER_PIECES
        pw, ph = img.w // cols, img.h // rows
        bx, by = self.x + dx, self.y - foot
        for c, r, vx, vy in self.pieces:
            ox = vx * self.t
            oy = vy * self.t - 0.5 * config.GRAVITY * 0.55 * self.t * self.t
            src_c = (cols - 1 - c) if self.face < 0 else c              # 좌우 반전된 그림은 칸도 뒤집힌 자리에 놓인다
            assets.draw_clip(img, src_c * pw, r * ph, pw, ph, int(bx + c * pw + ox), int(max(self.y - 4, by + r * ph + oy)), flip)
        if k < 0.18:                                                    # 갈라지는 순간의 흰 금
            a = 1.0 - k / 0.18
            assets.draw_rect_color(int(bx), int(by + img.h // 2) - 2, img.w, 4, (255, 255, 255), a)
            assets.draw_rect_color(int(bx + img.w // 2) - 2, int(by), 4, img.h, (255, 255, 255), a)


class CutHalves:
    """처형으로 쓰러진 적이 두 동강 난다: 그림을 위아래로 잘라 위쪽은 베인 방향으로 미끄러져 올라가고 아래쪽은 주저앉으며 사라진다."""
    LIFE = 0.7

    def __init__(self, frame, x, y, face, side):
        self.frame, self.x, self.y, self.face, self.side = frame, x, y, face, side
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        if self.t >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        name, n = sprites.resolve(*self.frame)
        img = assets.image(sprites.path(name, n))
        dx, foot = sprites.place(name, n, img.w, img.h, self.face)
        flip = 'h' if self.face < 0 else ''
        k = self.t / self.LIFE
        if k > 0.6 and int(self.t * 30) % 2 == 0:                       # 끝에는 깜빡이며 사라진다
            return
        half = img.h // 2
        slide = 1 - (1 - min(1.0, k * 1.6)) ** 2
        bx, by = self.x + dx, self.y - foot
        assets.draw_clip(img, 0, 0, img.w, half, bx - self.side * 6 * slide, by - 10 * slide, flip)                  # 아래쪽
        assets.draw_clip(img, 0, half, img.w, img.h - half, bx + self.side * 46 * slide, by + half + 26 * slide - 60 * k * k, flip)   # 위쪽
        if k < 0.25:                                                    # 잘린 자리의 흰 선
            assets.draw_rect_color(int(bx), int(by + half) - 2, img.w, 4, (255, 255, 255), 1.0 - k / 0.25)


def _deep(color, k=1.6):
    """그 색의 진한 면 색: 가장 밝은 성분은 두고 나머지를 더 낮춰 채도를 올린다 (옅은 색이 원반에서 뿌옇게 보이지 않게)."""
    top = max(color)
    return tuple(max(0, int(top - (top - c) * k)) for c in color)


def _enemy_snap(e):
    """적의 지금 모습 (그림, 발 x, 발 y, 보는 쪽). 그림을 알 수 없으면 None."""
    frame = enemy_frame(e)
    return (frame, e.x, e.y, e.face_dir) if frame else None


def enemy_frame(e):
    """적이 지금 그리는 그림 (세트, 번호). 동작 그림이 없는 순간((None, 0))은 Enemy.draw처럼 정지 그림 한 장으로 바꾼다.
    그림을 알 수 없으면 None (실루엣·두 동강을 건너뛴다)."""
    if e is None or not hasattr(e, '_body_frame'):
        return None
    name, n = e._body_frame()
    if name is None:
        name = (getattr(e, 'stats', None) or {}).get('sprite')
    return (name, n) if name else None


class FinisherCut:
    """큰 마무리 연출 (v3, 2026-11-24 사용자가 준 INARI 영상을 프레임별로 분석해 같은 순서로). 처형과 궁극기 마무리가 쓴다.
      0.00  예고 초승달이 적을 감싼다: 회색 -> 흰색 -> 진한 색 -> 가늘어진다. 배경이 어두워지고 시간이 느려진다
      0.14  첫 일격: 화면을 가르는 흰 빛줄기 + 위아래로 긴 색 가시. 주인공은 흰 실루엣, 적은 검은 실루엣
      0.17  작은 진한 원반 -> 0.20 빛줄기 자리에 **검은 띠** (잔상)
      0.24  둘째 일격(on_hit): 흰 빛줄기 + 큰 색 네 갈래 별
      0.27  색 빛줄기 + **크고 진한 원반**(흰 부분은 가운데 작은 별과 불티뿐) -> 0.34 원반이 고리로 비워지고 검은 선
      0.40  가는 흰 선과 고리가 스러지고 조각이 흩어진다 -> 0.45 가로로 번지는 블러. 주인공은 0.5초쯤 색이 돌아온다
    색은 부르는 쪽이 준다 (처형 = 게이지 구간·강화 단계 색, 궁극기 = 무기 색). 시간은 실제 시간으로 흐른다
    (느려진 dt를 시간 배율로 나눈다). 화면을 완전히 멈추지 않는다. start를 주면 그 시점부터(궁극기는 예고 없이 0.14부터)."""
    T1, T2, END = 0.14, 0.24, 0.68
    MAX_VICTIMS = 6
    CLEAR = ('TintFx', 'Bloom', 'SheetEffect', 'SlashMark', 'ImpactBurst', 'ImpactRing', 'DashStreak', 'PathSlash', 'BlurSmear',
             'ExtraHits', 'BodyGhost', 'LightPillar')

    def __init__(self, x, y, color, player, enemy=None, start=0.0, slow=(0.42, 0.12), clear=True, victims=()):
        self.ex, self.ey, self.color, self.player, self.enemy = x, y, color, player, enemy
        # 맞은 적 {id: [적, (그림, 발 x, 발 y, 보는 쪽), (가운데 x, y)]}: 폭발이 적마다 터지고, 끝의 블러가 이들도 번지게 한다
        self.victims = {}
        near = sorted(victims, key=lambda v: abs(v.x - x))[:self.MAX_VICTIMS]      # 많으면 가운데에서 가까운 적부터
        for v in ([enemy] if enemy is not None else []) + list(near):
            snap = _enemy_snap(v)
            if snap:
                self.victims[id(v)] = [v, snap, v.center]
        self.deep = _deep(color)
        self.rt = start
        self.fresh = True
        self.clear = clear
        self.step = 0 if start < self.T1 else 1
        self.frame = enemy_frame(enemy)
        self.efoot, self.eface = ((enemy.x, enemy.y), enemy.face_dir) if enemy is not None else ((x, y), 1)
        effects.request_slow_motion(*slow)
        game_world.add_object(ExecDim(color=(8, 4, 12), strength=0.72, life=0.14), game_world.LAYER_TILES)

    def update(self, dt):
        if self.fresh:                                                 # 만든 프레임의 dt는 느려지기 전 값이라 건너뛴다
            self.fresh = False
        else:
            self.rt += dt / max(0.05, effects.time_scale())
        if self.clear and self.rt < 0.45:                              # 연출 동안은 다른 타격 이펙트를 걷어 낸다 (느려진 시간에 남아 그림을 덮는다)
            layer = game_world.world[game_world.LAYER_EFFECT]
            for o in list(layer):
                if type(o).__name__ in self.CLEAR:
                    game_world.remove_object(o)
            if layer and layer[-1] is not self and self in layer:      # 늘 맨 위에 그린다
                layer.remove(self)
                layer.append(self)
        e = self.enemy
        if e is not None and e.alive:
            self.ex, self.ey = e.center
            self.frame = enemy_frame(e) or self.frame
            self.efoot, self.eface = (e.x, e.y), e.face_dir
        for pair in self.victims.values():                             # 살아 있는 동안은 지금 자리·그림을 따라간다 (죽으면 마지막 모습)
            if pair[0].alive:
                pair[1] = _enemy_snap(pair[0]) or pair[1]
                pair[2] = pair[0].center
        if self.step == 0 and self.rt >= self.T1:
            self.step = 1
            effects.add_trauma(config.SHAKE_FINISHER)
            assets.play_sound('ult_hit')
            self._warp(0.6)                                             # 첫 일격: 화면이 살짝 휜다
        if self.step == 1 and self.rt >= self.T2:
            self.step = 2
            self.on_hit()
            self._warp(1.0)                                             # 둘째 일격: 배경까지 크게 휘고 색이 갈라진다
            effects.add_trauma(config.SHAKE_FINISHER * 1.6)
        if self.step == 2 and self.rt >= 0.45:                         # 원반이 사라진 뒤에 가로로 번지는 블러 (영상의 순서)
            self.step = 3
            effects.spawn_blur(self.ex, self.ey, self.deep, self.player, victims=[v[1] for v in self.victims.values()],
                               centers=[v[2] for v in self.victims.values()])
        if self.rt >= self.END:
            game_world.remove_object(self)

    def _warp(self, strength):
        import camera
        import postfx
        postfx.pulse(*camera.to_screen(self.ex, self.ey), strength=strength, life=0.5)

    def on_hit(self):
        """둘째 일격 순간에 할 일 (처형은 여기서 피해를 준다)."""

    # ----- 그리기 -----
    def _band(self, y, h, color, alpha=1.0):
        import camera
        left, _ = camera.to_world(0, 0)
        assets.draw_rect_color(left - 16, int(y - h / 2) // 2 * 2, config.SCREEN_W + 32, max(2, int(h) // 2 * 2), color, alpha)

    def _glow_row(self, y, color, alpha):
        """빛줄기를 따라 화면 끝까지 번지는 빛 (빛 층)."""
        import camera
        import options
        left, _ = camera.to_world(0, 0)
        img = assets.image('light/bloom_256.png')
        img.opacify(alpha * (0.5 if options.reduce_flash else 1.0))
        for off in range(0, config.SCREEN_W + 1, 96):
            assets.draw_image_added(img, int(left + off), int(y - img.h // 2), color=color, times=1)
        img.opacify(1.0)

    def _stamp(self, name, i, color):
        n = effects.sheet_info(name)['columns']
        effects.draw_tint_sheet(name, self.ex, self.ey, (i + 0.5) / n, color)

    def _spots(self):
        """폭발이 터지는 자리들: 맞은 적이 있으면 그 적들의 가운데(처형은 그 적 하나, 궁극기는 맞은 적마다), 없으면 연출의 중심."""
        return [v[2] for v in self.victims.values()] or [(self.ex, self.ey)]

    def _rows(self):
        """빛줄기가 지나는 높이들: 폭발 자리의 높이를 가까운 것끼리 묶는다 (같은 바닥의 적들은 한 줄)."""
        rows = []
        for _, y in sorted(self._spots(), key=lambda s: s[1]):
            if not rows or y - rows[-1] > 60:
                rows.append(y)
        return rows[:3]

    def draw(self):
        rt, ex, ey = self.rt, self.ex, self.ey
        p, e = self.player, self.enemy
        white, deep = (255, 255, 255), self.deep
        if rt < self.T1:                                               # 예고 초승달
            i = min(4, int(rt / (self.T1 / 5)))
            self._stamp('exec-crescent', i, (150, 150, 162) if i == 0 else white if i == 1 else self.color)
            return
        if rt < 0.34:                                                  # 맞은 적은 검은 실루엣 (처형의 적, 궁극기에 맞은 적들)
            for v, (frame, vx, vy, face), _ in self.victims.values():
                if v.alive:
                    sprites.draw_silhouette(*frame, vx, vy, face, (10, 6, 12), 0.9)
        if rt < 0.52:                                                  # 주인공은 흰 실루엣 (끝에서 색이 돌아온다). 별·원반보다 아래에
            a = 1.0 if rt < 0.42 else 1.0 - (rt - 0.42) / 0.1
            sprites.draw_silhouette(*p._body_frame(), p.x, p.y, p.draw_face(), white, a)
        # 가운데 폭발은 구운 시트 fin-burst 한 장이 흐른다 (haze-fx 스킬로 제작: 가시 -> 작은 원반 -> 큰 별 -> 진한 원반 -> 고리 -> 토막)
        # 화면 전체를 가르는 빛줄기와 검은 띠만 여기서 그린다
        for ey in self._rows():
            if rt < 0.173:                                             # 첫 일격의 흰 빛줄기 (위아래 색 가장자리)
                self._glow_row(ey, self.color, 0.5)
                self._band(ey, 22, self.color)
                self._band(ey - 12, 4, (90, 130, 255))
                self._band(ey, 14, white)
            elif 0.207 <= rt < self.T2:                                # 검은 띠 (빛줄기의 잔상)
                self._band(ey, 16, (2, 0, 2), 0.9)
            elif self.T2 <= rt < 0.273:                                # 둘째 일격의 흰 빛줄기
                self._glow_row(ey, self.color, 0.6)
                self._band(ey, 24, self.color)
                self._band(ey - 13, 4, (90, 130, 255))
                self._band(ey, 16, white)
            elif 0.273 <= rt < 0.373:                                  # 진한 원반 동안: 색 빛줄기
                self._glow_row(ey, deep, 0.4)
                self._band(ey, 10, deep)
                self._band(ey, 2, white, 0.6)
            elif 0.373 <= rt < 0.43:                                   # 고리로 비워질 때: 검은 선
                self._band(ey, 6, (2, 0, 2), 0.85)
            elif rt >= 0.43:                                           # 가는 흰 선이 스러진다
                k = max(0.0, 1.0 - (rt - 0.43) / (self.END - 0.43))
                self._band(ey, 4 if k > 0.5 else 2, white, k)
        for sx, sy in self._spots():                                   # 폭발은 자리마다 (2026-11-24 사용자: 궁극기도 적마다 대시 마무리처럼)
            if 0.207 <= rt < self.T2:
                assets.draw_rect_color(int(sx) - 2, int(sy) - 150, 4, 300, (2, 0, 2), 0.8)
            effects.draw_tint_sheet('fin-burst', sx, sy, min(0.999, (rt - self.T1) / 0.54), deep)


class DashExecution(FinisherCut):
    """표식 3개 처형: FinisherCut 연출을 처음(예고 초승달)부터. 둘째 일격에서 피해가 들어가고, 쓰러지면 두 동강.
    색은 그 순간 주인공의 게이지 구간·강화 단계 색 (11/24 사용자: 색만 게이지에 맞게)."""

    def __init__(self, weapon, enemy):
        p = weapon.owner
        super().__init__(*enemy.center, effects.zone_glow(p), p, enemy)
        self.weapon = weapon
        assets.play_sound('swing_critical')

    def on_hit(self):
        e, w = self.enemy, self.weapon
        if not e.alive:
            return
        p = w.owner
        import drama
        import mutations
        damage = (config.DASH_EXEC_DAMAGE * p.gauge.zone_multipliers()['attack'] * p.attack_bonus * mutations.damage_mult(p)
                  * (config.DASH_EXEC_BOSS if getattr(e, 'BOSS', False) else 1.0))
        side = 1 if p.x <= e.x else -1
        before = set(id(o) for o in game_world.world[game_world.LAYER_EFFECT])
        with drama.hit_style(big=True, color=self.color):
            killed = e.take_damage(damage, from_x=p.x, knock=config.KNOCK_BIG)
        p.gauge.add(config.GAIN_HIT * 2, 'hit')
        if killed:
            p.gauge.add(p.kill_gain(False), 'kill')
            if self.frame is not None and not getattr(e, 'BOSS', False):       # 쓰러지는 그림 대신 두 동강
                for o in list(game_world.world[game_world.LAYER_EFFECT]):
                    if id(o) not in before and type(o).__name__ == 'Corpse':
                        game_world.remove_object(o)
                game_world.add_object(CutHalves(self.frame, *self.efoot, self.eface, side), game_world.LAYER_EFFECT)
        effects.float_text(self.ex, self.ey + 150, '처형!', self.color, big=True, life=0.7)
        assets.play_sound('impact_enh2')


class ExecDim:
    """처형 순간 배경을 어둡고 붉게 (타일 층에 그려서 적·주인공·이펙트는 밝게 남는다)."""
    LIFE = 0.45

    def __init__(self, color=(34, 0, 8), strength=0.8, life=None):
        self.t = 0.0
        self.color, self.strength, self.life = color, strength, life or self.LIFE     # 궁극기는 푸른 어둠으로 옅게

    def update(self, dt):
        self.t += dt
        if self.t >= self.life:
            game_world.remove_object(self)

    def draw(self):
        import camera
        k = self.t / self.life
        a = self.strength * (min(1.0, k * 6) if k < 0.2 else 1.0 - (k - 0.2) / 0.8)
        left, bottom = camera.to_world(0, 0)
        assets.draw_rect_color(left - 16, bottom - 16, config.SCREEN_W + 32, config.SCREEN_H + 32, self.color, a)


class DashStreak:
    """대시가 지나간 자리에 남는 붉은 궤적: 굵은 빛줄기 + 흰 심, 시간이 지나며 가늘어진다 (2px 칸, 회전 없음)."""

    def __init__(self, path, life=0.6, width=26, color=EXEC_COLOR):
        self.path, self.life, self.width, self.color = path, life, width, color
        self.t = 0.0
        self.seed = random.randint(0, 999)

    def update(self, dt):
        self.t += dt
        if self.t >= self.life:
            game_world.remove_object(self)

    def draw(self):
        """v8 (사용자가 준 INARI 그림): 굵은 흰 속도 줄기 몇 가닥 + 아래로 불꽃처럼 일렁이는 색 띠 + 길을 따라 번지는 빛."""
        x0, y0, x1, y1 = self.path
        k = 1.0 - self.t / self.life
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 4:
            return
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        nx, ny = -dy, dx
        img = assets.image('light/bloom_256.png')                      # 번지는 빛 (빛 층)
        img.opacify(0.5 * k)
        for s_ in range(0, int(length) + 1, 110):
            assets.draw_image_added(img, int(x0 + dx * s_), int(y0 + dy * s_) - img.h // 2, color=self.color, times=1)
        img.opacify(1.0)
        w = self.width * (k ** 0.6)
        steps = max(1, int(length // 4))
        for i in range(steps + 1):                                      # 색 띠: 뒤쪽일수록 낮고, 가장자리가 일렁인다
            t = i / steps
            x, y = _snap(x0 + dx * length * t), _snap(y0 + dy * length * t)
            wob = 0.55 + 0.45 * math.sin(i * 0.9 + self.seed + self.t * 26) * math.sin(i * 0.37 + self.seed)
            hh = max(2, int(w * (0.35 + 0.65 * t) * (0.7 + 0.5 * wob)) // 2 * 2)
            lift = int(hh * 0.35 * wob) // 2 * 2
            assets.draw_rect_color(x - 2 + int(nx * lift), y - hh // 2 + int(ny * lift), 4, hh, self.color, 0.9 * k)
        for band, (off, a0, a1, th) in enumerate(((0, 0.0, 1.0, 0.34), (-0.42, 0.25, 0.95, 0.16), (0.4, 0.1, 0.8, 0.14),
                                                  (-0.8, 0.45, 1.0, 0.08), (0.78, 0.4, 0.9, 0.08))):   # 흰 속도 줄기
            grow = min(1.0, self.t / 0.05 + 0.3)
            s0, s1 = length * (a0 + (1 - k) * 0.5 * (a1 - a0)), length * a1 * grow
            if s1 - s0 < 6:
                continue
            ww = max(2, int(w * th * 2) // 2 * 2)
            ox, oy = nx * off * w * 0.6, ny * off * w * 0.6
            n = max(1, int((s1 - s0) // 6))
            for q in range(n + 1):
                u = q / n
                taper = math.sin(math.pi * u) ** 0.5
                hw = max(2, int(ww * taper) // 2 * 2)
                x, y = _snap(x0 + dx * (s0 + (s1 - s0) * u) + ox), _snap(y0 + dy * (s0 + (s1 - s0) * u) + oy)
                assets.draw_rect_color(x - 3, y - hw // 2, 6, hw, (255, 255, 255), min(1.0, 1.2 * k))


class Pipe:
    IMPACT = 'impact_pipe'          # 명중할 때 적 피격음 위에 겹치는 무기 소리 (11/21 계획 1-7). 사슬은 갈고리 소리가 따로 있다
    # v7 효과음 v3: 철파이프는 공격 종류마다 다른 타격음 (hit_kind)
    PIPE_IMPACTS = {'finisher': 'impact_pipe_heavy', 'dash': 'impact_pipe_dash', 'air': 'impact_pipe_air',
                    'plunge': 'impact_pipe_plunge'}
    hit_kind = 'normal'
    name = '철파이프'
    weapon_id = 'pipe'
    form_state = None            # v8 무기 형태의 진행 중인 동작 (src/forms.py). 없으면 None
    heavy = False                # 철파이프 '중량 타격'을 모으는 중
    jab, jab_left = 0, 0.0       # 건틀릿 '연타'의 잽 번호와 이어지는 시간
    base_damage = config.PIPE_DAMAGE

    def __init__(self, owner):
        self.owner = owner
        self.cooldown_max = 0.3   # 지금 쿨타임의 처음 길이 (재충전 바 표시용)
        self.combo = 0            # 지금까지 이어 친 횟수 (1~3)
        self.cooldown = 0.0       # 다음 공격까지 남은 시간
        self.combo_left = 0.0     # 이 시간이 지나면 연타가 끊긴다
        self.last_kind = None     # 마지막으로 나간 공격 종류 (pipe / dash / spin / plunge)
        self.last_enhanced = False   # 그 공격이 강화 일격이었는가
        self.level = 0               # 지금 나가는 공격에 쓰인 강화 단계 (0 = 강화 없음, 1~2, 3은 궁극기)
        self.followup = None         # (남은 시간, 할 일): 이어지는 둘째 타 (철파이프 2단계 내려찍기)
        self.pass_hit = set()        # 대시 v2: 이번 대시 베기로 지나가며 이미 벤 적

    def update(self, dt):
        self.cooldown = max(0.0, self.cooldown - dt)
        import forms
        forms.tick_combo(self, dt)
        forms.update(self, dt)                               # v8 무기 형태: 모으는 중·이어치기·갈고리 이동
        p = self.owner
        if p.state == 'DASH' and p.dash_strike_queued:      # 대시 v2: 대시 중 눌렀으면 지나가는 순간 벤다
            self._dash_pass()
        if self.followup is not None:
            left, action = self.followup
            left -= dt
            if left <= 0:
                self.followup = None
                action()
            else:
                self.followup = (left, action)
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
        if not self.ready or getattr(self, 'form_state', None) is not None:    # 형태의 동작(모으는 중 등)이 진행 중이면 받지 않는다
            return False
        if self._try_ultimate():
            return True
        kind = self.current_kind()
        import forms
        if kind == 'pipe' and forms.active(self) and not self.owner.gauge.enhanced:    # v8 형태 '중량 타격'
            return forms.pipe_attack(self)
        enhanced = self._take_level()
        self.last_kind, self.last_enhanced = kind, enhanced
        getattr(self, '_attack_' + kind)(enhanced)
        return True

    # ----- 강화 단계 (E 중첩) -----
    def _take_level(self):
        """이번 공격에 쓰는 강화 단계를 정한다. 강화됐으면 True."""
        g = self.owner.gauge
        self.level = g.enhance_level if g.enhanced else 0
        effects.enh_level = max(1, self.level)          # 이번 공격의 강화 이펙트 색 (1 보라·2 금·3 진홍)
        return self.level > 0

    def _enh(self, key):
        """지금 강화 단계(1~2)의 값: 피해 배율·범위·추가 타격·폭발 반지름 (config.ENHANCE_LEVELS)."""
        return config.ENHANCE_LEVELS[max(1, min(self.level, 2))][key]

    def _stack(self):
        """식칼·건틀릿·사슬의 강화 피해에 곱하는 단계 배율."""
        return config.ENHANCE_STACK_MULT.get(max(1, min(self.level, 2)), 1.0)

    def ult_kind(self):
        """궁극기 종류: 대시 중·직후 = dash, 공중 = jump, 그 밖 = basic (철파이프의 공격 종류 규칙과 같다)."""
        p = self.owner
        if p.dash_window > 0:
            return 'dash'
        if not p.on_ground and p.state in ('JUMP', 'FALL'):
            return 'jump'
        return 'basic'

    def _try_ultimate(self):
        """강화 3단계로 공격하면 궁극기가 나간다. 나갔으면 True."""
        g = self.owner.gauge
        if not (g.enhanced and g.enhance_level >= config.ENHANCE_MAX_LEVEL):
            return False
        p = self.owner
        kind = self.ult_kind()
        ax, ay = p.aim_vector()
        self.level = config.ENHANCE_MAX_LEVEL
        effects.enh_level = self.level
        self.last_kind, self.last_enhanced = 'ult_' + kind, True
        game_world.add_object(ULTIMATES[self.weapon_id](self, kind, ax, ay), game_world.LAYER_EFFECT)
        g.consume_enhance()
        p.ult_pose_left = config.ULT_POSE_TIME             # 시전 자세: 모으기 -> 해방 (사슬만 끝까지 쓴다, 나머지는 자기 동작)
        p.swing_left = p.punch_left = 0.0
        self.cooldown = self.cooldown_max = config.ULT_COOLDOWN
        return True

    # ----- 공통 -----
    def _fx(self, enhanced):
        p = self.owner
        return config.ENHANCED_FX_BY_LEVEL[max(1, min(3, self.level))] if enhanced else config.ZONE_FX[p.gauge.zone]

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
        import combo
        import drama
        snap = _enemy_snap(enemy) if big else None                  # v8 조각 처치: 죽기 직전의 모습
        before = set(id(o) for o in game_world.world[game_world.LAYER_EFFECT]) if big else ()
        with drama.hit_style(big=big or None, color=color or fx['damage_color']):   # 피해 숫자 모양 (픽셀 글꼴, 하나만)
            killed = enemy.take_damage(damage, from_x=p.x, knock=(config.KNOCK_BIG if big else 1.0) * self.knock_mult())
        combo.juggle(enemy)                                          # v8 공중 연타: 떠 있는 적은 맞으면 조금 다시 뜬다
        import impact_frame
        if fx.get('enhanced') or (killed and impact_frame.is_boss(enemy)):   # v8 4-2 임팩트 프레임: 강화 일격·보스 막타
            impact_frame.trigger(p, enemy, p.x, snap)
        if big:
            ecx, ecy = enemy.center
            effects.add_kick(ecx - p.x, ecy - p.center[1], config.KICK_BIG)     # v8 카메라 킥: 공격 방향으로 한 번 밀린다
            if killed and snap is not None and not getattr(enemy, 'BOSS', False):   # v8 조각 처치: 쓰러지는 그림 대신 흩어진다
                for o in list(game_world.world[game_world.LAYER_EFFECT]):
                    if id(o) not in before and type(o).__name__ == 'Corpse':
                        game_world.remove_object(o)
                frame, fx_, fy_, face = snap
                game_world.add_object(Shatter(frame, fx_, fy_, face, 1 if ecx >= p.x else -1), game_world.LAYER_EFFECT)
        if self.IMPACT:
            assets.play_sound(self._impact_sound(fx))
        p.gauge.add(gain, 'hit')
        ex, ey = enemy.center
        effects.spawn(fx['spark'], ex, ey, duration=fx['spark_time'])
        rays = config.IMPACT_RAYS['enhanced' if fx.get('enhanced') else p.gauge.zone]
        effects.spawn_impact(ex, ey, ex - p.x, ey - p.center[1], rays, fx['damage_color'], big=big)       # 충격 방사선
        if big:                                          # 강한 공격: X자 베기 자국 두 개 + 퍼지는 고리 + 별 섬광(v8)
            effects.spawn_slash_marks(ex, ey, ex - p.x, ey - p.center[1], fx['damage_color'], big=True, count=2)
            effects.spawn_ring(ex, ey, fx['damage_color'])
            effects.spawn_flare(ex, ey, color or effects.zone_glow(p))
        else:                                            # 맞을 때마다 적을 가로지르는 베기 자국 (다단 히트가 하나하나 보이게)
            effects.spawn_slash_marks(ex, ey, ex - p.x, ey - p.center[1], fx['damage_color'])
            effects.spawn_flare(ex, ey, color or effects.zone_glow(p), small=True)      # v8: 작은 별 섬광 (대시 화풍)
        effects.request_hit_stop(config.HIT_STOP * stop * fx['stop'])
        effects.spawn_bloom(ex, ey, fx['damage_color'], big=big, strength=0.9 if big else 0.6)   # v7 빛 번짐
        p.swing_connected = True                         # 이번 휘두르기가 맞았다: 몸은 젖힘으로 되돌아가지 않는다
        effects.add_trauma(config.SHAKE_HIT * shake * fx['shake'])
        if killed:
            p.gauge.add(p.kill_gain(bool(fx.get('enhanced'))), 'kill')
            effects.add_trauma(config.SHAKE_KILL)
            effects.spawn_kill(ex, ey, ex - p.x, ey - p.center[1], fx['damage_color'])   # v7 처치 연출
        import mutations
        mutations.on_linked_hit(p, enemy, damage, killed)   # v7 연결 갈래: 묶인 적이 나눠 받고, 죽으면 터진다
        mutations.on_hit(p)                              # 변이 '굶주림'
        dash_mark(self, enemy, killed)                   # 대시 v2: 대시 공격이면 표식·대시 회복
        import combo
        combo.on_hit(self, enemy, killed)                # v8 두 무기 조합: 각인을 남기거나, 다른 무기의 각인을 격발
        if fx.get('enhanced'):
            mutations.on_enhanced_hit(p, enemy, damage)  # 변이 '파문'
        if blast:
            self._blast(enemy)
        if not extra:                                    # 식칼·건틀릿은 구간 효과가 발사 수·크기로 따로 있다
            return killed
        extra = max(config.EXTRA_HITS.get(p.gauge.zone, 0), self._enh('extra') if fx.get('enhanced') else 0)
        if extra and not killed:                         # 타수 증가: 첫 타격 뒤에 작은 추가 타격이 이어진다
            game_world.add_object(ExtraHits(p, enemy, damage * config.EXTRA_HIT_RATIO, fx, extra, big), game_world.LAYER_EFFECT)
        return killed

    def knock_mult(self):
        """적을 미는 힘 배율 (v7 건틀릿 '밀어내기')."""
        return 1.0

    def _impact_sound(self, fx):
        """무기 쪽 타격음: 강화면 단계 소리, 철파이프는 공격 종류(1·2타·마무리·이동·공중·찍기)마다, 그 밖은 무기 소리."""
        if fx.get('enhanced'):
            return f'impact_enh{max(1, min(3, self.level))}'
        if self.IMPACT == 'impact_pipe':
            return self.PIPE_IMPACTS.get(self.hit_kind, self.IMPACT)
        return self.IMPACT

    def _swing_sound(self, kind, enhanced):
        """휘두르는 소리 (v7 효과음 v3): 강화는 단계 소리, 페이드는 힘 빠진 소리, 각성·위험은 공격 소리 위에 색 소리를 겹친다."""
        if enhanced:
            assets.play_sound(f'swing_enh{max(1, min(3, self.level))}')
            return
        zone = self.owner.gauge.zone
        if zone == 'FADE':
            assets.play_sound('swing_fade')
            return
        assets.play_sound(kind)
        if zone in ('AWAKE', 'CRITICAL'):
            assets.play_sound('accent_' + zone.lower())

    def _damage(self, mult):
        p = self.owner
        import mutations
        return self.base_damage * p.gauge.zone_multipliers()['attack'] * p.attack_bonus * mult * mutations.damage_mult(p)

    def _weak(self):
        """약해진 상태(페이드)인가. 이때는 모든 공격의 범위가 줄고 대시·점프 공격의 추가 배율이 사라진다."""
        return self.owner.gauge.zone in ('FADE', 'DEAD')

    def _reach(self):
        return config.FADE_REACH if self._weak() else 1.0      # v8: 연타 '긴 손잡이'(사거리)는 '검기'로 바뀌었다

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
        variant, flip = effects.slash_variant(ax, ay)
        if enhanced and self.level >= 2:
            self._stage2_rise(ax, ay)
            return
        if enhanced:
            self.combo = 0
            self._swing_sound('swing_3', True)
            p.set_swing_style(3, ax)                     # 강화 일격은 3타처럼 크게 끌어 내딛는다
            p.swing_anim = 'n09_e1'                      # 공격 v3: X베기
            self.cooldown = config.ENHANCE_STRIKE_COOLDOWN
            effects.spawn(fx['slash'], cx, cy, flip=flip, duration=0.24, variant=variant)
            effects.add_trauma(config.SHAKE_FINISHER)
            damage = self._damage(self._enh('damage'))
            scale = self._reach() * self._enh('reach') / config.ENHANCE_REACH_MULT
            for enemy in self._targets(lambda e: self._in_arc(e, cx, cy, ax, ay, enhanced=True, scale=scale)):
                self._hit(enemy, damage, config.PIPE_FINISHER_GAIN, fx, big=True, shake=2.0, stop=2, blast=True)
            self._finish(True)
            return
        import mutations
        frenzy = mutations.has(p, 'combo_evo') and self.weapon_id == 'pipe'    # v7 진화 '난타': 4·5타가 생긴다
        self.combo = self.combo % (5 if frenzy else 3) + 1
        if self.combo == 5:
            self._frenzy_spin(fx)
            return
        finisher = self.combo == 3
        style = 2 if self.combo == 4 else self.combo     # 4타는 2타처럼 빠른 사선
        self.hit_kind = 'finisher' if finisher else 'normal'
        self._swing_sound(f'swing_{style}', False)
        p.set_swing_style(style, ax)                     # 1타·2타·3타마다 자세 시간과 내딛기가 다르다
        self.cooldown = self.cooldown_max = config.PIPE_COOLDOWN[style - 1] * mutations.attack_speed_mult(p)   # v7 '손목 풀기'
        self.combo_left = self.cooldown + config.PIPE_COMBO_WINDOW
        shape = None                                     # 공격 v3: 그림에 맞춘 모양 (1타 가로 = 납작한 호, 3타 올려베기 = 올라가는 호)
        if p.swing_dir == 'side' and self.combo == 1:
            shape = 'flat'
        elif finisher and p.swing_dir in ('side', 'up', 'upfwd'):
            shape = 'rise'
        lift_y = config.FLAT_SLASH_LIFT if shape == 'flat' else 0     # 납작한 호는 아래 반쪽이라 허리 높이로 올린다
        effects.spawn(effects.slash_sheet(p.gauge.zone, finisher, shape=shape), cx, cy + lift_y, flip=flip, duration=0.22,
                      variant=variant)
        mult = config.PIPE_FINISHER_MULT if finisher else (mutations.FRENZY_MULT[0] if self.combo == 4 else 1.0)
        damage = self._damage(mult) * mutations.pipe_damage_mult(p, finisher=finisher, air=not p.on_ground)   # v7 '마무리'·'낙차'
        gain = config.PIPE_FINISHER_GAIN if finisher else config.GAIN_HIT
        lift = p.on_ground and p.swing_dir in ('up', 'upfwd') and mutations.has(p, 'air_lift')
        color = config.DAMAGE_COLOR_FINISHER if finisher else None
        struck = self._targets(lambda e: self._in_arc(e, cx, cy, ax, ay, scale=self._reach()))
        if finisher and self.weapon_id == 'pipe' and mutations.has(p, 'combo_wave'):     # v8 연타 '검기': 3타가 앞으로 날아간다
            game_world.add_object(SwordWave(self, cx, cy, ax, ay, damage * mutations.COMBO_WAVE[0], struck),
                                  game_world.LAYER_EFFECT)
        for enemy in struck:
            self._hit(enemy, damage, gain, fx, big=finisher, color=color,
                      shake=config.SHAKE_FINISHER / config.SHAKE_HIT if finisher else 1.0, stop=2 if finisher else 1)
            if lift and getattr(enemy, 'alive', False) and not getattr(enemy, 'BOSS', False):
                import combo
                combo.launch(enemy, mutations.LIFT_VY)                               # v7 '띄우기': 높이
            elif finisher and shape == 'rise' and p.on_ground:
                import combo
                combo.launch(enemy, config.JUGGLE_RISE)                              # v8: 3타 올려베기는 적을 띄운다 (공중 연타의 시작)
            if not p.on_ground:
                mutations.on_air_hit(p)                                              # v7 '체공'

    # ----- v7 진화 '난타' 5타: 몸 둘레를 한 바퀴 도는 회전 베기 (흰 원형 궤적) -----
    def _frenzy_spin(self, fx):
        import mutations
        p = self.owner
        cx, cy = p.center
        ax, _ay = p.aim_vector()
        self.hit_kind = 'finisher'
        self._swing_sound('swing_3', False)
        p.set_swing_style(3, ax)
        p.swing_anim = 'n09_air2'                        # 반원 휘두르기 그림을 땅에서도 쓴다
        p.lunge_vx = 0.0                                 # 제자리에서 돈다
        self.cooldown = self.cooldown_max = config.PIPE_COOLDOWN[2] * mutations.attack_speed_mult(p)
        self.combo_left = self.cooldown + config.PIPE_COMBO_WINDOW
        reach = config.PIPE_REACH * mutations.FRENZY_REACH * self._reach()
        effects.spawn(effects.special_sheet('spin', False)[0], cx, cy, duration=0.26)
        effects.spawn_ring(cx, cy, FRENZY_COLOR, radius_max=int(reach), life=0.24)
        effects.add_trauma(config.SHAKE_FINISHER)
        damage = self._damage(mutations.FRENZY_MULT[1])
        for enemy in self._targets(lambda e: self._within(e, cx, cy, reach)):
            self._hit(enemy, damage, config.PIPE_FINISHER_GAIN, fx, big=True, color=FRENZY_COLOR,
                      shake=config.SHAKE_FINISHER / config.SHAKE_HIT, stop=2)

    # ----- v7 진화 '낙뢰 내려찍기': 내려찍고 땅에 닿는 순간 번개 기둥과 충격파 -----
    def bolt_strike(self):
        import mutations
        p = self.owner
        radius, mult, lift = mutations.BOLT
        cx, cy = p.center
        fx = self._fx(False)
        game_world.add_object(BoltPillar(p.x, p.y), game_world.LAYER_EFFECT)
        effects.ground_slam(p.x, p.y, power=1.1, color=BOLT_COLOR)
        effects.spawn_ring(p.x, p.y + 20, BOLT_COLOR, radius_max=radius, life=0.3)
        effects.add_trauma(config.SHAKE_FINISHER)
        assets.play_sound('impact_pipe_plunge')
        damage = self._damage(mult) * mutations.pipe_damage_mult(p, air=True)
        bowl = mutations.has(p, 'duo_bolt_bowl')          # v8 합성 '볼링 내려찍기': 띄우는 대신 옆으로 날려 다른 적을 들이받게
        for enemy in self._targets(lambda e: self._within(e, p.x, cy, radius)):
            self._hit(enemy, damage, config.GAIN_HIT, fx, big=True, color=BOLT_COLOR, shake=1.2, extra=False)
            if not getattr(enemy, 'alive', False) or getattr(enemy, 'BOSS', False):
                continue
            if bowl:
                side = 1 if enemy.x >= p.x else -1
                weight = config.ENEMY_WEIGHT.get(getattr(enemy, 'kind', ''), 1.0)
                game_world.add_object(Fling(self, enemy, damage, side * mutations.DUO_BOWL / weight), game_world.LAYER_EFFECT)
            else:
                enemy.vy = max(getattr(enemy, 'vy', 0.0), lift)

    # ----- v7 진화 '섬광 베기': 대시 공격이 지난 직선을 잠시 뒤 번쩍이며 다시 벤다 -----
    def flash_strike(self, path, half, damage, net=False):
        import mutations
        x0, y0, x1, y1 = path
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 8:
            return
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        fx = self._fx(False)
        effects.spawn_path_slash(x0, y0, x1, y1, True)
        effects.spawn_bloom((x0 + x1) / 2, (y0 + y1) / 2, FLASH_COLOR, big=True)
        effects.add_trauma(config.SHAKE_FINISHER * 0.6)
        assets.play_sound('swing_dash')
        hit = []
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or not self._segment_hit(enemy, x0, y0, dx, dy, length, half):
                continue
            ex, ey = enemy.center
            t = max(0.0, min(length, (ex - x0) * dx + (ey - y0) * dy))
            if not self._visible(enemy, x0 + dx * t, y0 + dy * t):
                continue
            self._hit(enemy, damage, config.GAIN_HIT, fx, big=True, color=FLASH_COLOR, shake=1.0, extra=False)
            hit.append(enemy)
        if net and len(hit) >= 2:                        # 합성 '그물 베기': 벤 적을 모두 그물로 묶는다
            mutations.bind(self.owner, hit, mutations.NET_SIZE)

    # ----- 철파이프 2단계: 올려베기 -> 내려찍기 (11/20) -----
    def _stage2_rise(self, ax, ay):
        """첫 타: 앞을 위로 쳐올린다. 맞은 땅 위 적은 살짝 뜬다. 이어서 내려찍기를 예약한다."""
        p = self.owner
        cx, cy = p.center
        fx = config.ENHANCED_FX_BY_LEVEL[2]             # 2단계: 금색
        side = 1 if ax >= 0 else -1
        self.combo = 0
        p.start_swing(side * 0.45, 0.9)
        p.set_swing_style(2, side)
        p.swing_dir = 's2rise'                           # 전용 그림 (Codex T24): 웅크림 -> 앞 수평 -> 머리 위
        p.swing_total = p.swing_left = config.STAGE2_SLAM_DELAY + 0.01   # 세 장이 내려찍기 전에 모두 보이게
        self.cooldown = config.ENHANCE_STRIKE_COOLDOWN + config.STAGE2_SLAM_DELAY
        variant, flip = effects.slash_variant(side * 0.45, 0.9)
        effects.spawn(fx['slash'], cx, cy + 30, flip=flip, duration=0.2, variant=variant)
        damage = self._damage(config.STAGE2_RISE_MULT)
        scale = self._enh('reach') / config.ENHANCE_REACH_MULT
        for enemy in self._targets(lambda e: self._in_arc(e, cx, cy, side, 0.35, enhanced=True, scale=scale)):
            self._hit(enemy, damage, config.GAIN_HIT, fx, shake=1.2, extra=False)
            if enemy.alive and getattr(enemy, 'pullable', True) and getattr(enemy, 'on_ground', False):
                enemy.vy = max(getattr(enemy, 'vy', 0.0), config.STAGE2_RISE_HOP)
        self.followup = (config.STAGE2_SLAM_DELAY, lambda: self._stage2_slam(side))
        self._finish(True)                               # 강화 단계는 지금 쓴다 (둘째 타 사이에 E를 눌러도 쌓이지 않게)

    def _stage2_slam(self, side):
        """둘째 타의 시작: 두 손으로 들고 뛰어올라 내리친다 (그림 1·2번). 피해는 파이프가 바닥에 닿는 3번에서."""
        p = self.owner
        if p.state == 'DEAD':
            return
        p.start_swing(side * 0.7, -0.6)
        p.set_swing_style(3, side)
        p.swing_dir = 's2slam'                           # 전용 그림 (Codex T24): 두 손 들고 뜸 -> 45도 -> 바닥 타격
        p.swing_total = p.swing_left = config.STAGE2_SLAM_POSE
        assets.play_sound('swing_enh2')
        self.followup = (config.STAGE2_SLAM_FRAMES[1], lambda: self._stage2_impact(side))

    def _stage2_impact(self, side):
        """파이프가 바닥에 닿는 순간: 바닥 충격과 큰 피해."""
        p = self.owner
        if p.state == 'DEAD':
            return
        cx, cy = p.center
        fx = config.ENHANCED_FX_BY_LEVEL[2]             # 2단계: 금색
        assets.play_sound('swing_critical')
        effects.spawn('quake-blast', p.x + side * 150, p.y, duration=0.4)
        effects.add_trauma(config.SHAKE_FINISHER * 1.3)
        effects.ground_slam(p.x + side * 150, p.y, power=1.2, color=fx['damage_color'])   # v7 땅 강타
        self.level = 2
        damage = self._damage(config.STAGE2_SLAM_MULT)
        scale = self._enh('reach') / config.ENHANCE_REACH_MULT * config.STAGE2_SLAM_REACH
        for enemy in self._targets(lambda e: self._in_arc(e, cx, cy, side, -0.3, enhanced=True, scale=scale)):
            self._hit(enemy, damage, config.PIPE_FINISHER_GAIN, fx, big=True, shake=2.0, stop=2, blast=True)

    def _blast(self, hit):
        """강화된 공격에 맞은 적 주위로 안개 폭발이 퍼져 주변 적에게 피해를 준다 (벽 너머에는 닿지 않는다)."""
        p = self.owner
        bx, by = hit.center
        effects.spawn('haze-blast', bx, by, duration=0.45)
        effects.add_trauma(config.SHAKE_FINISHER)
        for other in list(game_world.world[game_world.LAYER_ENEMY]):
            if other.alive and other is not hit:
                ox, oy = other.center
                if math.hypot(ox - bx, oy - by) <= self._enh('blast') and (
                        p.room is None or not p.room.line_blocked(bx, by, ox, oy)):
                    if other.take_damage(config.ENHANCE_BLAST_DAMAGE, from_x=bx):
                        p.gauge.add(p.kill_gain(), 'kill')

    # ----- 대시 평타: 지나온 경로를 한 줄로 베는 직선 베기 (관통) -----
    def _attack_dash(self, enhanced):
        p = self.owner
        self.cooldown = config.ENHANCE_STRIKE_COOLDOWN if enhanced else config.DASH_STRIKE_COOLDOWN
        self.hit_kind = 'dash'
        self._swing_sound('swing_dash', enhanced)
        if p.state == 'DASH':                            # 대시 중: 지금부터 지나가는 적을 그 순간 벤다 (대시 v2)
            p.dash_strike_queued = True
            p.dash_strike_enhanced = enhanced
            self.pass_hit = set()
            p.start_dash_cut()
            self._dash_pass()
            if enhanced:
                p.gauge.consume_enhance()                # 강화는 이 대시 평타에 쓰인다
            return
        self.pass_hit = set()
        self.resolve_dash_strike(enhanced)               # 막 끝난 직후: 지나온 길을 한 번에 벤다

    @property
    def dash_color(self):
        """이번 대시 공격의 색: 강화 일격이면 강화 단계 색, 아니면 게이지 구간 색."""
        if self.owner.dash_strike_enhanced or self.owner.gauge.enhanced:
            return config.ENHANCE_LEVEL_COLOR[max(1, min(3, self.level or self.owner.gauge.enhance_level))]
        return config.ZONE_GLOW.get(self.owner.gauge.zone, config.ZONE_GLOW['NORMAL'])

    def _dash_strike_stats(self, enhanced):
        """대시 평타의 (반폭, 피해, 이펙트)."""
        import mutations
        half = (self._enh('half') if enhanced else config.DASH_STRIKE_HALF_WIDTH) * self._reach()
        if mutations.has(self.owner, 'dashcut_wide'):
            half *= mutations.DASHCUT_WIDE                                       # v7 '넓은 궤적'
        damage = self._damage(self._enh('damage') if enhanced else self._special(config.DASH_STRIKE_MULT))
        damage *= mutations.pipe_damage_mult(self.owner, dash=True)               # v7 '돌진 베기'
        return half, damage, self._fx(enhanced)

    def _dash_cut_one(self, enemy, x0, y0, dx, dy, length, damage, fx, enhanced):
        """대시 경로 위 적 하나를 벤다 (벽 너머는 제외). 벴으면 True."""
        ex, ey = enemy.center
        t = max(0.0, min(length, (ex - x0) * dx + (ey - y0) * dy))       # 경로에서 이 적에 가장 가까운 지점
        if not self._visible(enemy, x0 + dx * t, y0 + dy * t):
            return False
        self.pass_hit.add(id(enemy))
        self._hit(enemy, damage, config.PIPE_FINISHER_GAIN if enhanced else config.GAIN_HIT, fx, big=enhanced,
                  shake=1.8 if enhanced else 1.2, blast=enhanced)
        effects.spawn_slash_marks(ex, ey, dx, dy, (255, 255, 255), big=True)   # 지나가며 긋는 큰 베기 자국
        variant, flip = effects.slash_variant(dx, dy)
        sheet = (('pipe-slash-enhanced' + effects.enh_suffix()) if enhanced else
                 {'NORMAL': 'pipe-slash-awake', 'DEAD': 'pipe-slash-fade', 'OVERLOAD': 'pipe-slash-critical'}.get(
                     self.owner.gauge.zone, config.ZONE_FX[self.owner.gauge.zone]['slash']))
        effects.spawn(sheet, ex - dx * 40, ey - dy * 40, flip=flip, duration=0.26, variant=variant)   # 적을 감싸는 큰 초승달 (구간·강화 색)
        effects.spawn_flare(ex, ey, self.dash_color)                           # 별 섬광 + 큰 빛 (구간·강화 색, 위험은 레드)
        return True

    def _dash_pass(self):
        """대시하는 동안: 출발점에서 지금까지 지나온 길에 들어온 적을 그 순간 벤다 (한 적에 한 번)."""
        p = self.owner
        x0, y0 = p.dash_origin
        x1, y1 = p.center
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 8:
            return
        dx, dy = (x1 - x0) / length, (y1 - y0) / length
        half, damage, fx = self._dash_strike_stats(p.dash_strike_enhanced)
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if enemy.alive and id(enemy) not in self.pass_hit and self._segment_hit(enemy, x0, y0, dx, dy, length, half):
                self._dash_cut_one(enemy, x0, y0, dx, dy, length, damage, fx, p.dash_strike_enhanced)

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
        if self.owner.state != 'DASH':
            self.owner.start_dash_cut()                                   # 공격 v3: 낮은 돌진 가로 베기 자세
        import mutations
        half, damage, fx = self._dash_strike_stats(enhanced)
        if enhanced:                                                      # 강화만 단계 색 궤적 (보통은 붉은 DashStreak, 대시 v2)
            effects.spawn_path_slash(x0, y0, x1, y1, enhanced)
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):       # 지나가며 아직 못 벤 적 (대시 v2)
            if (enemy.alive and id(enemy) not in self.pass_hit and
                    self._segment_hit(enemy, x0, y0, dx, dy, length, half)):
                self._dash_cut_one(enemy, x0, y0, dx, dy, length, damage, fx, enhanced)
        self.pass_hit = set()
        if enhanced:
            effects.add_trauma(config.SHAKE_FINISHER)
        if mutations.has(self.owner, 'dashcut_evo') and self.weapon_id == 'pipe':    # v7 진화 '섬광 베기'
            delay, mult, wide = mutations.FLASH
            game_world.add_object(DelayedFlash(self, (x0, y0, x1, y1), half * wide, damage * mult, delay,
                                               mutations.has(self.owner, 'duo_flash_net')), game_world.LAYER_EFFECT)
        self._finish(enhanced)

    # ----- 점프 평타: 회전 베기 / 내려찍기 -----
    def _attack_spin(self, enhanced):
        p = self.owner
        self.cooldown = config.ENHANCE_STRIKE_COOLDOWN if enhanced else config.AIR_COOLDOWN
        cx, cy = p.center
        fx = self._fx(enhanced)
        self.hit_kind = 'air'
        self._swing_sound('swing_air', enhanced)
        p.vy = max(p.vy, config.AIR_HOP)                                  # 살짝 떠오르며 한 바퀴 돈다
        ax, ay = p.aim_vector()
        anim = p.start_air_swing(ax, ay)                                  # 공격 v3: 가로 베기 -> 반원, 위로 겨누면 올려베기
        damage = self._damage(self._enh('damage') if enhanced else self._special(config.AIR_SPIN_MULT))
        if self._weak() and not enhanced:
            # 페이드: 한 바퀴 돌 힘이 없다. 기본 공격처럼 조준 앞쪽만 작게 벤다 (2026-11-20 사용자 요청)
            variant, flip = effects.slash_variant(ax, ay)
            effects.spawn(effects.slash_sheet(p.gauge.zone, False), cx, cy, flip=flip, duration=0.22, variant=variant)
            in_range = lambda e: self._in_arc(e, cx, cy, ax, ay, scale=self._reach())
        else:
            if enhanced:
                effects.spawn(effects.special_sheet('spin', enhanced)[0], cx, cy, duration=0.26)
            else:                                                         # 공격 v3: 동작과 같은 모양의 호 (판정은 그대로 몸 둘레)
                variant, flip = effects.slash_variant(ax, ay)
                shape = 'flat' if anim == 'n09_air1' else None
                lift_y = config.FLAT_SLASH_LIFT if shape == 'flat' else 0
                effects.spawn(effects.slash_sheet(p.gauge.zone, shape=shape), cx, cy + lift_y, flip=flip, duration=0.24,
                              variant=variant)
            reach = config.AIR_SPIN_REACH * (self._enh('reach') if enhanced else 1.0)
            in_range = lambda e: self._within(e, cx, cy, reach)
        for enemy in self._targets(in_range):
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
        self.hit_kind = 'plunge'
        self._swing_sound('swing_plunge', enhanced)
        p.start_plunge_pose()
        sheet, _ = effects.special_sheet('plunge', enhanced)
        effects.spawn(sheet, cx, cy, duration=0.26, variant=4)             # 아래 방향 변형
        k = (self._enh('plunge') if enhanced else 1.0) * self._reach()
        damage = self._damage(self._enh('damage') if enhanced else self._special(config.PLUNGE_MULT))
        targets = self._targets(lambda e: self._segment_hit(e, cx, cy, 0.0, -1.0, config.PLUNGE_LENGTH * k,
                                                             config.PLUNGE_HALF_WIDTH * k))
        for enemy in targets:
            self._hit(enemy, damage, config.PIPE_FINISHER_GAIN if enhanced else config.GAIN_HIT, fx, big=enhanced,
                      shake=1.9 if enhanced else 1.5, stop=1.3, blast=enhanced)
        if targets:                                                        # 맞으면 튕겨 올라 다시 뛸 수 있다
            p.vy = config.PLUNGE_BOUNCE
            p.jump_count = min(p.jump_count, 1)
        import mutations
        if mutations.has(p, 'air_evo') and self.weapon_id == 'pipe':
            p.bolt_armed = True                                            # v7 진화 '낙뢰 내려찍기': 착지할 때 터진다
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
# 쌍권총 (v7, 2026-11-24, 식칼 대체, docs/plan_v7.md 1절): 좌우 총을 번갈아 쏜다. 쏘면서 움직이고 뛸 수 있다.
# 구간: 노멀 1발 / 각성 2발 / 위험 3발 부채꼴 / 페이드 느리게 1발. 대시 중·직후: 일자로 모은 3발 관통.
# E 강화: 두 총을 모아 큰 한 발(관통)과 반동. 2단계는 큰 한 발이 처음 맞힌 자리에서 사방 8발 파편.
# 총알·총구 섬광은 코드로 그린다 (정수 좌표, 2배 픽셀 격자).
# =====================================================================================================
BULLET_COLORS = {False: [(255, 255, 255), (150, 250, 238), (46, 230, 214), (11, 106, 116)],      # 흰 머리 -> 청록 꼬리
                 True: [(255, 255, 255), (230, 204, 255), (164, 107, 255), (90, 47, 184)]}      # 강화: 보라


class Pistols(Pipe):
    IMPACT = 'impact_pistol'
    name = '쌍권총'
    weapon_id = 'pistol'
    base_damage = config.PISTOL_DAMAGE

    def __init__(self, owner):
        super().__init__(owner)
        self.side = 1                                    # 다음에 쏠 총 (+1 앞손, -1 뒷손). 쏠 때마다 바뀐다
        self.loaded = False                              # v7 '장전 회피': 다음 한 발이 강화탄
        self.after_dash = 0.0                            # v7 '여세': 대시가 끝나고 남은 빠른 연사 시간
        self.auto_left = 0.0                             # v7 '질주 사격': 다음 자동 사격까지

    def update(self, dt):
        super().update(dt)
        import mutations
        p = self.owner
        if p.state == 'DASH':
            self.after_dash = mutations.DSHOT_AFTER[0]
            if mutations.has(p, 'dshot_auto'):          # 대시하는 동안 저절로 쏜다
                self.auto_left -= dt
                if self.auto_left <= 0:
                    self.auto_left = mutations.DSHOT_AUTO[0]
                    self._auto_shot()
        else:
            self.after_dash = max(0.0, self.after_dash - dt)

    def _auto_shot(self):
        import mutations
        p = self.owner
        ax, ay = p.aim_vector()
        cx, cy = p.center
        self.side = -self.side
        mx, my = p.pistol_muzzle()
        my += self.side * 3
        dmg = self._damage(mutations.DSHOT_AUTO[1])
        game_world.add_object(Bullet(self, mx, my, ax, ay, dmg, False, self._fx(False), self.side), game_world.LAYER_EFFECT)
        game_world.add_object(MuzzleFlash(mx, my, ax, ay), game_world.LAYER_EFFECT)
        assets.play_sound('shot')

    def ring_burst(self):
        """v7 진화 '탄막 회피': 대시가 끝난 자리에서 사방으로 총알."""
        import mutations
        p = self.owner
        cx, cy = p.center
        n, mult = mutations.DSHOT_RING
        dmg = self._damage(mult)
        for i in range(n):
            a = math.tau * i / n
            game_world.add_object(Bullet(self, cx, cy, math.cos(a), math.sin(a), dmg, False, self._fx(False), 1 if i % 2 else -1),
                                  game_world.LAYER_EFFECT)
        effects.spawn_ring(cx, cy, mutations.FAMILIES['pistol_dash']['color'], radius_max=160, life=0.22)
        effects.spawn_bloom(cx, cy, mutations.FAMILIES['pistol_dash']['color'], big=True, life=0.18, strength=0.6)
        assets.play_sound('shot_critical')

    def _cooldown(self, slow):
        """이번 발 뒤 다음 발까지 (v7 연사·대시 사격 갈래가 줄인다)."""
        import mutations
        p = self.owner
        cd = config.PISTOL_FADE_COOLDOWN if slow else config.PISTOL_COOLDOWN
        if mutations.has(p, 'rapid_speed'):
            cd *= mutations.RAPID_SPEED
        if mutations.has(p, 'rapid_still') and p.on_ground and abs(p.vx) < mutations.RAPID_STILL_VX:
            cd *= mutations.RAPID_STILL
        if mutations.has(p, 'dshot_after') and self.after_dash > 0:
            cd *= mutations.DSHOT_AFTER[1]
        if mutations.has(p, 'rapid_evo') and p.attack_held:
            cd *= mutations.RAPID_EVO[0]
        return cd

    def current_kind(self):
        """대시 중·직후 = 대시 사격, 공중 = 공중 사격, 그 밖 = 기본 사격."""
        return {'dash': 'pistol_dash', 'jump': 'pistol_air'}.get(self.ult_kind(), 'pistol')

    def volley(self, enhanced=None, kind=None):
        """지금 구간·공격 종류에서 쏘는 (총알 수, 퍼지는 각도, 관통)."""
        p = self.owner
        enhanced = p.gauge.enhanced if enhanced is None else enhanced
        kind = kind or self.current_kind()
        if enhanced:
            return 1, 0, True
        if kind == 'pistol_dash':
            return config.PISTOL_DASH_COUNT, config.PISTOL_DASH_SPREAD, True
        count, spread = config.PISTOL_ZONE[p.gauge.zone]
        import mutations
        if mutations.has(p, 'rapid_extra'):              # v7 '덧탄': 한 발 더 (부채꼴)
            count, spread = count + 1, spread + mutations.RAPID_EXTRA_SPREAD
        return count, spread, False

    def try_attack(self):
        if not self.ready:
            return False
        if self._try_ultimate():
            return True
        p = self.owner
        kind = self.current_kind()
        import forms
        if kind == 'pistol' and forms.active(self) and not p.gauge.enhanced and not self.loaded:    # v8 형태 '산탄'
            return forms.pistol_attack(self)
        enhanced = self._take_level()
        loaded = self.loaded and not enhanced            # v7 '장전 회피': 강화 비용 없이 큰 한 발
        if loaded:
            self.loaded = False
            self.level = 1
        self.last_kind, self.last_enhanced = kind, enhanced or loaded
        count, spread, pierce = self.volley(enhanced or loaded, kind)
        import mutations
        barrage = mutations.has(p, 'rapid_evo') and p.attack_held and not (enhanced or loaded)
        ax, ay = p.aim_vector()
        base = math.degrees(math.atan2(ay, ax))
        if barrage:                                      # v7 진화 '난사': 끊김 없는 탄막은 조금씩 흩어진다
            import random
            base += random.uniform(-mutations.RAPID_EVO[1], mutations.RAPID_EVO[1])
        cx, cy = p.center
        self.side = -self.side
        mx, my = p.pistol_muzzle()                       # 겨눔 그림의 총구 (2026-11-24)
        my += self.side * 3                              # 두 총이 살짝 위아래로 엇갈린다
        fx = self._fx(enhanced or loaded)
        if enhanced or loaded:                           # 두 총을 모아 큰 한 발
            damage = self._damage(config.PISTOL_BIG_MULT * self._stack())
            game_world.add_object(Bullet(self, mx, my, ax, ay, damage, True, fx, self.side, big=True,
                                         burst=self.level >= 2), game_world.LAYER_EFFECT)
            back = -(1 if ax >= 0 else -1)
            p.lunge_vx = back * config.PISTOL_RECOIL     # 반동: 쏜 반대쪽으로 밀린다
            effects.add_trauma(config.SHAKE_FINISHER * 0.8)
            effects.spawn_bloom(mx, my, BULLET_COLORS[True][2], big=True, life=0.2, strength=0.9)
            p.start_punch('shoot_big')
        else:
            damage = self._damage(1.0)
            for i in range(count):
                off = 0.0 if count == 1 else -spread + 2 * spread * i / (count - 1)
                a = math.radians(base + off)
                game_world.add_object(Bullet(self, mx, my, math.cos(a), math.sin(a), damage, pierce, fx, self.side),
                                      game_world.LAYER_EFFECT)
            p.start_punch('shoot')
        game_world.add_object(MuzzleFlash(mx, my, ax, ay, enhanced or loaded), game_world.LAYER_EFFECT)
        if barrage:                                      # 탄피가 뒤로 튄다
            game_world.add_object(ShellCasing(cx - ax * 10, cy + 10, -(1 if ax >= 0 else -1)), game_world.LAYER_EFFECT)
        import drama
        assets.play_sound(drama.pistol_sound(p.gauge.zone, enhanced or loaded))
        slow = p.gauge.zone in ('FADE', 'DEAD')
        self.cooldown = self.cooldown_max = (config.ENHANCE_STRIKE_COOLDOWN if enhanced or loaded else self._cooldown(slow))
        self._finish(enhanced)
        return True


class Bullet:
    """날아가는 총알 한 발 (코드로 그린 빛줄기). 벽(#)에 닿거나 사거리를 넘으면 사라지고, 관통이 아니면 첫 적에서 멈춘다.
    big(강화 큰 한 발)은 굵고 보라. burst(강화 2단계)면 처음 맞힌 자리에서 사방으로 파편(shrapnel)이 튄다."""

    def __init__(self, weapon, x, y, dx, dy, damage, pierce, fx, side, big=False, burst=False, shrapnel=False,
                 reach=None, skip=()):
        self.weapon, self.x, self.y = weapon, x, y
        n = math.hypot(dx, dy) or 1.0
        self.dx, self.dy = dx / n, dy / n
        self.damage, self.pierce, self.fx, self.side = damage, pierce, fx, side
        self.big, self.burst, self.shrapnel = big, burst, shrapnel
        self.reach = reach or (config.PISTOL_SHRAPNEL_RANGE if shrapnel else config.PISTOL_RANGE)
        self.travel = 0.0
        self.hit = set(id(e) for e in skip)
        import mutations
        p = weapon.owner
        self.bounces = 0 if shrapnel else int(mutations.has(p, 'ric_bounce')) + int(mutations.has(p, 'ric_more'))   # v7 도탄
        self.bounced = 0
        self.ric_power = mutations.has(p, 'ric_power')
        self.chains = 0 if shrapnel else (mutations.RIC_CHAIN[0] if mutations.has(p, 'ric_evo') else 0)          # v7 도탄 사슬
        self.homing = not shrapnel and mutations.has(p, 'duo_focus_barrage')                                    # v8 합성 집중 탄막

    def rect(self):
        h = config.PISTOL_HB * (2.0 if self.big else 0.5 if self.shrapnel else 1.0) / 2
        return (self.x - h, self.y - h, self.x + h, self.y + h)

    def update(self, dt):
        if self.homing:
            self._home(dt)
        step = config.PISTOL_SPEED * dt * (0.7 if self.shrapnel else 1.0)
        self.x += self.dx * step
        self.y += self.dy * step
        self.travel += step
        room = self.weapon.owner.room
        wall = room is not None and room.tile_at_world(self.x, self.y) == '#'
        if wall and self.bounces > 0 and self.travel <= self.reach:     # v7 도탄: 벽에서 튕긴다
            self._bounce(room, step)
        elif self.travel > self.reach or wall:
            effects.spawn_bloom(self.x, self.y, BULLET_COLORS[self.big][2], life=0.08, strength=0.4)
            game_world.remove_object(self)
            return
        left, bottom, right, top = self.rect()
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or id(enemy) in self.hit:
                continue
            el, eb, er, et = enemy.rect()
            if left < er and el < right and bottom < et and eb < top:
                self.hit.add(id(enemy))
                self.weapon._hit(enemy, self.damage, config.PISTOL_GAIN, self.fx, big=self.big,
                                 shake=0.9 if self.big else 0.3, stop=1.2 if self.big else 0.25, blast=self.big, extra=False)
                if self.burst:
                    self._shrapnel(enemy)
                if self.chains > 0 and self._chain_to_next(enemy):    # v7 도탄 사슬: 가까운 적으로 튕긴다
                    return
                if not self.pierce:
                    game_world.remove_object(self)
                    return

    def _bounce(self, room, step):
        """벽에 닿았다: 한 걸음 물러나 가로·세로 중 막힌 쪽 방향을 뒤집는다."""
        px, py = self.x - self.dx * step, self.y - self.dy * step
        if room.tile_at_world(self.x, py) == '#':       # 가로로만 움직여도 막힌다 = 옆벽
            self.dx = -self.dx
        if room.tile_at_world(px, self.y) == '#':       # 세로로만 움직여도 막힌다 = 바닥·천장
            self.dy = -self.dy
        if room.tile_at_world(self.x, py) != '#' and room.tile_at_world(px, self.y) != '#':
            self.dx, self.dy = -self.dx, -self.dy       # 모서리
        self.x, self.y = px, py
        self.bounces -= 1
        self.bounced += 1
        if self.ric_power and self.bounced == 1:
            import mutations
            self.damage *= mutations.RIC_POWER
        effects.spawn_bloom(self.x, self.y, (255, 230, 140), life=0.1, strength=0.5)
        assets.play_sound('impact_pistol')

    def _home(self, dt):
        """v8 합성 '집중 탄막': 소용돌이에 묶인 적 가운데 가장 가까운 쪽으로 방향을 조금씩 꺾는다."""
        import mutations
        turn, reach = mutations.DUO_FOCUS
        best, best_d = None, reach
        for o in game_world.world[game_world.LAYER_EFFECT]:
            if type(o) is not Vortex or o.weapon.owner is not self.weapon.owner:
                continue
            for e in o.bound():
                if id(e) in self.hit:
                    continue
                ex, ey = e.center
                d = math.hypot(ex - self.x, ey - self.y)
                if d < best_d:
                    best, best_d = e, d
        if best is None or best_d < 1.0:
            return
        ex, ey = best.center
        want = math.atan2(ey - self.y, ex - self.x)
        now = math.atan2(self.dy, self.dx)
        diff = (want - now + math.pi) % math.tau - math.pi
        turn = max(turn, min(60.0, 2.0 * config.PISTOL_SPEED / best_d))   # 가까운 적: 돌아 드는 반지름이 거리의 절반이 되게 (소용돌이는 적을 바로 옆에 모은다)
        now += max(-turn * dt, min(turn * dt, diff))
        self.dx, self.dy = math.cos(now), math.sin(now)

    def _chain_to_next(self, enemy):
        """맞힌 적 둘레에서 아직 안 맞힌 가장 가까운 적으로 날아간다. 찾으면 True."""
        import mutations
        ex, ey = enemy.center
        best, best_d = None, mutations.RIC_CHAIN[1]
        for other in game_world.world[game_world.LAYER_ENEMY]:
            if other is enemy or not other.alive or id(other) in self.hit:
                continue
            ox, oy = other.center
            d = math.hypot(ox - ex, oy - ey)
            if d < best_d:
                best, best_d = other, d
        if best is None:
            return False
        ox, oy = best.center
        self.dx, self.dy = (ox - ex) / best_d, (oy - ey) / best_d
        self.x, self.y = ex, ey
        self.travel = 0.0
        self.reach = best_d + 120
        self.chains -= 1
        game_world.add_object(ChainTrail(ex, ey, ox, oy), game_world.LAYER_EFFECT)
        return True

    def _shrapnel(self, enemy):
        """강화 2단계: 처음 맞힌 자리에서 사방으로 파편 (맞힌 적은 다시 맞지 않는다)."""
        self.burst = False
        ex, ey = enemy.center
        for i in range(config.PISTOL_SHRAPNEL):
            a = math.tau * i / config.PISTOL_SHRAPNEL + 0.2
            game_world.add_object(Bullet(self.weapon, ex, ey, math.cos(a), math.sin(a), self.damage * config.PISTOL_SHRAPNEL_MULT,
                                         False, self.fx, self.side, shrapnel=True, skip=(enemy,)), game_world.LAYER_EFFECT)
        effects.spawn('hit-enhanced2', ex, ey, duration=0.3)

    def draw(self):
        cols = BULLET_COLORS[self.big]
        length = 80 if self.big else 26 if self.shrapnel else 52
        thick = 12 if self.big else 6
        for k in range(0, length, 2):                   # 머리(흰)에서 꼬리(짙은 청록)로, 꼬리 쪽이 가늘다
            t = k / length
            c = cols[min(3, int(t * 4))]
            w = max(2, int(thick * (1.0 - 0.6 * t)) // 2 * 2)
            x = int(round(self.x - self.dx * k)) // 2 * 2
            y = int(round(self.y - self.dy * k)) // 2 * 2
            assets.draw_rect_color(x - w // 2, y - w // 2, w, w, c)


class ChainTrail:
    """도탄 사슬: 튕긴 두 적 사이에 잠깐 남는 빛줄기 잔상."""
    LIFE = 0.18

    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        k = 1.0 - self.time / self.LIFE
        length = math.hypot(self.x1 - self.x0, self.y1 - self.y0) or 1.0
        w = max(2, int(6 * k) // 2 * 2)
        for s in range(0, int(length), 4):
            t = s / length
            x = int(self.x0 + (self.x1 - self.x0) * t) // 2 * 2
            y = int(self.y0 + (self.y1 - self.y0) * t) // 2 * 2
            assets.draw_rect_color(x - w // 2, y - w // 2, w, w, (255, 240, 170) if s % 8 else (255, 255, 255))


class ShellCasing:
    """난사의 탄피: 작은 놋쇠 조각이 뒤로 튀었다가 떨어진다."""
    GRAVITY = -1900.0

    def __init__(self, x, y, back):
        import random
        self.x, self.y = x, y
        self.vx, self.vy = back * random.uniform(160, 300), random.uniform(260, 420)
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        self.vy += self.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.time >= 0.45:
            game_world.remove_object(self)

    def draw(self):
        x, y = int(self.x) // 2 * 2, int(self.y) // 2 * 2
        flip = int(self.time * 30) % 2
        assets.draw_rect_color(x, y, 4 if flip else 2, 2 if flip else 4, (235, 200, 110))


class MuzzleFlash:
    """총구 섬광: 흰 사각 심 + 앞쪽으로 뻗는 짧은 빛살 세 줄, 0.06초. 작은 빛 번짐."""
    LIFE = 0.06

    def __init__(self, x, y, dx, dy, big=False):
        n = math.hypot(dx, dy) or 1.0
        self.x, self.y, self.dx, self.dy, self.big = x, y, dx / n, dy / n, big
        self.time = 0.0
        effects.spawn_bloom(x, y, BULLET_COLORS[big][1], big=big, life=0.08, strength=0.5)

    def update(self, dt):
        self.time += dt
        if self.time >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        cols = BULLET_COLORS[self.big]
        k = 1.0 - self.time / self.LIFE
        core = (14 if self.big else 8)
        x, y = int(self.x) // 2 * 2, int(self.y) // 2 * 2
        assets.draw_rect_color(x - core // 2, y - core // 2, core, core, cols[0])
        for ang in (-28, 0, 28):                         # 앞쪽 부채꼴 빛살
            a = math.atan2(self.dy, self.dx) + math.radians(ang)
            ln = int((34 if ang == 0 else 18) * (1.6 if self.big else 1.0) * k)
            for s in range(0, ln, 2):
                px = int(round(self.x + math.cos(a) * s)) // 2 * 2
                py = int(round(self.y + math.sin(a) * s)) // 2 * 2
                assets.draw_rect_color(px - 1, py - 1, 2 if s > ln // 2 else 4, 2 if s > ln // 2 else 4,
                                       cols[0] if s < ln // 2 else cols[1])


class Tracer:
    """궁극기 연출용 날아가는 총알 줄기 (판정 없음)."""

    def __init__(self, x, y, vx, vy, life, big=False):
        self.x, self.y, self.vx, self.vy, self.life, self.big = x, y, vx, vy, life, big
        n = math.hypot(vx, vy) or 1.0
        self.dx, self.dy = vx / n, vy / n
        self.shrapnel = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.life <= 0:
            game_world.remove_object(self)

    def draw(self):
        Bullet.draw(self)


# =====================================================================================================
# 헤이즈 건틀릿 (특수, 소모형): 좌클릭을 누르는 동안 게이지를 초당 10%씩 태워(5% 아래로는 안 내려감) 충전하고,
# 떼면 조준 방향으로 몸째 돌진해 처음 닿은 적에 주먹을 박는다 (2026-11-24 충격파 발사 -> 돌진 강타). 충전이 많을수록
# 멀리·세게. 게이지가 너무 오를 때 일부러 쓰는 "배출" 무기다.
# 노멀: 충전 0.9초 / 각성: 0.65초, 크기 x1.3 / 위험: 충전 없이 즉시 끝까지 돌진, 게이지 -15% 고정, 크기 x1.6.
# E 강화: 충전 시간 절반, 크기·피해 x1.5, 둘레 충격 x2. 2단계는 부딪힌 자리에서 양옆 충격파.
# =====================================================================================================
class Gauntlet(Pipe):
    """헤이즈 건틀릿 (2026-11-24 돌진 강타로 개편): 누르는 동안 게이지를 태워 충전하고, 떼면 조준 쪽으로 몸째 돌진해
    처음 닿은 적에게 주먹을 박는다. 충전할수록 멀리·세게. 맞은 적은 크게 날아가고 둘레 적은 충격으로 조금 맞는다.
    공격 간격은 느리다. 대시·공중은 충전 없이 짧은 돌진, 공중에서 아래로는 내리꽂기(땅에 닿으면 둘레를 친다)."""
    IMPACT = 'impact_gauntlet'
    name = '건틀릿'
    weapon_id = 'gauntlet'
    base_damage = config.GAUNTLET_DAMAGE

    def __init__(self, owner):
        super().__init__(owner)
        self.charging = False
        self.charge = 0.0
        self.warned_empty = False      # 이번 충전에서 '게이지 부족'을 이미 알렸는지
        self.rush = None               # 돌진 중이면 그 정보 (dict), 아니면 None

    @property
    def rushing(self):
        return self.rush is not None

    @property
    def ready(self):
        return self.cooldown <= 0 and self.rush is None

    def current_kind(self):
        if self.charging:
            return 'charge'
        kind = self.ult_kind()
        if kind in ('dash', 'jump'):                 # 대시·점프: 충전 없이 바로 짧은 돌진
            return 'gauntlet_dash' if kind == 'dash' else 'gauntlet_air'
        g = self.owner.gauge
        return 'gauntlet_instant' if g.zone == 'CRITICAL' and not g.enhanced else 'gauntlet'

    def charge_need(self):
        import mutations
        p = self.owner
        need = config.GAUNTLET_CHARGE_TIME.get(p.gauge.zone, config.GAUNTLET_CHARGE_TIME['NORMAL'])
        if mutations.has(p, 'charge_fast'):              # v7 '빠른 장전'
            need *= mutations.CHARGE_FAST
        return need * (0.5 if p.gauge.enhanced else 1.0)

    def knock_mult(self):
        import mutations
        return mutations.CRASH_KNOCK if mutations.has(self.owner, 'crash_knock') else 1.0

    @property
    def charge_ratio(self):
        return min(1.0, self.charge / max(self.charge_need(), 0.01)) if self.charging else 0.0

    def _size(self, enhanced):
        return config.GAUNTLET_SIZE.get(self.owner.gauge.zone, 1.0) * (config.GAUNTLET_ENHANCED_MULT if enhanced else 1.0)

    def try_attack(self):
        if not self.ready or self.charging or getattr(self, 'form_state', None) is not None:
            return False
        if self._try_ultimate():
            return True
        p = self.owner
        kind = self.current_kind()
        if kind in ('gauntlet_dash', 'gauntlet_air'):               # 대시·점프: 게이지 조금 내고 바로 짧게 돌진
            p.gauge.add(-min(config.GAUNTLET_QUICK_COST, max(0.0, p.gauge.value - config.GAUNTLET_FLOOR)), 'gauntlet')
            enhanced = self._take_level()
            ax, ay = p.aim_vector()
            dive = kind == 'gauntlet_air' and ay < -0.5              # 공중에서 아래로: 내리꽂기
            self._start_rush(config.GAUNTLET_QUICK_RATIO, enhanced, self._size(enhanced), config.GAUNTLET_RUSH_QUICK, dive)
            self.last_kind = kind
            return True
        import forms
        if forms.active(self) and not p.gauge.enhanced:             # v8 형태 '연타': 충전 대신 빠른 잽
            return forms.gauntlet_attack(self)
        if p.gauge.zone == 'CRITICAL' and not p.gauge.enhanced:     # 위험: 충전 없이 바로 끝까지, 게이지를 크게 비운다
            p.gauge.add(-config.GAUNTLET_CRIT_COST, 'gauntlet')
            self._start_rush(1.0, False, config.GAUNTLET_SIZE['CRITICAL'], config.GAUNTLET_RUSH_MAX)
            return True
        self.charging, self.charge, self.warned_empty = True, 0.0, False
        self.last_kind = 'charge'
        assets.play_sound('enhance')
        return True

    def update(self, dt):
        super().update(dt)
        if self.rush is not None:
            self._update_rush(dt)
            return
        if not self.charging:
            return
        p = self.owner
        if p.state in ('HIT', 'DEAD') or p.stunned:                 # 맞거나 기절하면 충전이 풀린다
            self.charging = False
            return
        if not p.attack_held:
            self.release()
            return
        import mutations
        if mutations.has(p, 'charge_parry'):                        # v8 충전 '쳐 내기': 가까이 온 적 투사체를 지운다
            _parry_shots(p, mutations.CHARGE_PARRY)
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
        enhanced = self._take_level()
        k = (ratio - config.GAUNTLET_MIN_RATIO) / (1.0 - config.GAUNTLET_MIN_RATIO)
        dist = config.GAUNTLET_RUSH_MIN + (config.GAUNTLET_RUSH_MAX - config.GAUNTLET_RUSH_MIN) * k
        self._start_rush(ratio, enhanced, self._size(enhanced), dist)

    # ----- 돌진 -----
    def _start_rush(self, ratio, enhanced, size, dist, dive=False):
        import mutations
        p = self.owner
        ax, ay = p.aim_vector()
        if dive:
            ay = min(ay, -0.5)
            p.vy = 0.0
        elif p.on_ground and ay < 0.2:                               # 땅 위: 바닥으로는 못 파고드니 수평으로
            ax, ay = (math.copysign(1.0, ax) if abs(ax) > 0.05 else float(p.face_dir)), 0.0
        n = math.hypot(ax, ay) or 1.0
        dx, dy = ax / n, ay / n
        fx = self._fx(enhanced)
        damage = self._damage(0.4 + 0.6 * ratio) * (config.GAUNTLET_ENHANCED_MULT * self._stack() if enhanced else 1.0)
        full = ratio >= 1.0
        if full and mutations.has(p, 'charge_power'):    # v7 '꽉 쥔 주먹'
            damage *= mutations.CHARGE_POWER
        speed = config.GAUNTLET_RUSH_SPEED * (1.15 if dive else 1.0)
        self.rush = dict(dx=dx, dy=dy, speed=speed, left=(config.GAUNTLET_DIVE_TIME if dive else dist / speed),
                         damage=damage, size=size, enhanced=enhanced, full=full, fx=fx, dive=dive,
                         collapse=full and mutations.has(p, 'charge_evo'),            # v7 진화 '헤이즈 붕괴'
                         px=None, py=None, last_dt=0.0, trail=0.0)
        self.last_kind, self.last_enhanced = 'gauntlet', enhanced
        p.start_punch('blast_down' if dive else 'blast')
        if dy != 0.0:
            p.vy = 0.0
        assets.play_sound('dash')
        assets.play_sound('overload_zap' if size >= 1.5 else fx['sound'])
        effects.add_trauma(0.15 + 0.12 * size)
        cx, cy = p.center
        effects.spawn_bloom(cx + dx * 30, cy + dy * 30, fx['damage_color'], life=0.12, strength=0.7)
        if p.on_ground:
            effects.spawn('dust-land', p.x, p.y, duration=0.3)                  # 박차고 나간 발밑 먼지
        game_world.add_object(RushTrail(self, fx['damage_color'], size), game_world.LAYER_EFFECT)
        self.cooldown = self.cooldown_max = config.GAUNTLET_COOLDOWN
        self._finish(enhanced)

    def rush_velocity(self):
        """돌진하는 동안 주인공 속도 (Player._apply_swing_motion이 쓴다). 돌진 중이 아니면 None.
        땅 위 수평 돌진은 vy가 None: 중력을 그대로 받아 바닥을 따라간다 (발판 끝에서는 떨어진다)."""
        r = self.rush
        if r is None:
            return None
        return r['dx'] * r['speed'], (None if r['dy'] == 0.0 else r['dy'] * r['speed'])

    def on_put_away(self):
        """다른 무기로 바꿨다: 충전·돌진을 끊는다 (돌진 정보가 남으면 다시 들 때 멈추지 않는다)."""
        self.charging = False
        self.rush = None

    def _update_rush(self, dt):
        r, p = self.rush, self.owner
        if r.get('ult') is not None:                                 # 궁극기 '유성 돌진': 이동만 여기 것, 판정은 GauntletUlt
            return
        if p.state in ('HIT', 'DEAD') or p.stunned:
            self.rush = None
            return
        if r['px'] is not None:                                      # 지난 프레임에 얼마나 갔나 (벽·바닥에 막혔나)
            if r['dive'] and p.on_ground:
                self._dive_land()
                return
            went = math.hypot(p.x - r['px'], p.y - r['py'])
            if went < r['speed'] * r['last_dt'] * 0.3:
                self._end_rush(wall=True)
                return
        r['px'], r['py'], r['last_dt'] = p.x, p.y, dt
        cx, cy = p.center
        hx, hy = cx + r['dx'] * config.GAUNTLET_RUSH_REACH, cy + r['dy'] * config.GAUNTLET_RUSH_REACH
        reach = config.GAUNTLET_RUSH_HIT * min(1.4, r['size'])
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if enemy.alive and Pipe._within(enemy, hx, hy, reach):
                self._impact(enemy)
                return
        r['left'] -= dt
        if r['left'] <= 0:
            self._end_rush()
            return
        p.punch_left = max(p.punch_left, p.punch_total * 0.7)          # 주먹을 뻗은 자세로 날아간다
        p.invuln_left = max(p.invuln_left, dt * 2)                     # 돌진 중에는 맞지 않는다 (짧다)
        p.steady_left = max(p.steady_left, dt * 2)
        r['trail'] -= dt
        if r['trail'] <= 0:                                            # 잔상
            r['trail'] = 0.022
            p.afterimages.append([p.x, p.y, p.face_dir, config.AFTERIMAGE_LIFE, p._body_frame()])

    def _end_rush(self, wall=False):
        """아무도 못 맞히고 끝났다 (끝까지 갔거나 벽에 막혔다)."""
        r, p = self.rush, self.owner
        self.rush = None
        p.lunge_vx = r['dx'] * 260 if p.on_ground else 0.0              # 조금 미끄러지며 선다
        p.punch_left = min(p.punch_left, p.punch_total * 0.5)            # 회수 자세로
        cx, cy = p.center
        if wall:
            effects.spawn_impact(cx + r['dx'] * 30, cy + r['dy'] * 30, -r['dx'], -r['dy'], 6, (220, 220, 230))
            effects.add_trauma(config.SHAKE_HIT)
            assets.play_sound('land')
        else:
            effects.spawn('puff', cx + r['dx'] * 30, cy, duration=0.25)

    def _impact(self, enemy):
        """처음 닿은 적에 주먹이 박혔다: 큰 일격 + 날려 보내기 + 둘레 충격."""
        import mutations
        r, p = self.rush, self.owner
        self.rush = None
        damage = r['damage']
        counter = _in_windup(enemy) and any(mutations.has(p, m) for m in
                                            ('counter_power', 'counter_guard', 'counter_gain', 'counter_evo'))
        if counter:                                      # v7 반격: 예고 중인 적을 쳤다
            damage *= mutations.COUNTER_POWER if mutations.has(p, 'counter_power') else 1.0
            _counter_success(p, enemy, self)
        size = r['size']
        killed = self._hit(enemy, damage, config.GAIN_HIT, r['fx'], big=True, shake=1.4 + 0.5 * size,
                           stop=1.6 + 0.4 * size, blast=r['enhanced'], extra=False)
        ex, ey = enemy.center
        side = (1 if r['dx'] > 0 else -1) if abs(r['dx']) > 0.2 else (1 if ex >= p.x else -1)
        if not killed and enemy.alive and not getattr(enemy, 'BOSS', False):   # 크게 날아간다 (충돌 갈래는 Fling이 벽·기절·연쇄)
            weight = config.ENEMY_WEIGHT.get(getattr(enemy, 'kind', ''), 1.0)
            speed = config.GAUNTLET_KNOCK * min(1.3, size) * self.knock_mult() / weight
            game_world.add_object(Fling(self, enemy, damage, side * speed), game_world.LAYER_EFFECT)
        self._impact_burst(ex, ey, damage, r, exclude={id(enemy)})
        if r['collapse']:
            _collapse_burst(self, (ex, ey), damage, r['fx'])
        p.vx = 0.0
        p.lunge_vx = -side * 220 if p.on_ground else 0.0                 # 반동으로 살짝 튕겨 선다
        if not p.on_ground:
            p.vy = max(p.vy, 320.0)
        p.punch_left = p.punch_total * 0.5

    def _dive_land(self):
        """내리꽂기가 땅에 닿았다: 발밑 둘레를 친다."""
        r, p = self.rush, self.owner
        self.rush = None
        effects.ground_slam(p.x, p.y, power=0.9 + 0.3 * r['size'], color=r['fx']['damage_color'])
        self._impact_burst(p.x, p.y + config.PLAYER_HB_H / 2, r['damage'], r, exclude=set(), mult=1.0)
        p.punch_left = p.punch_total * 0.5

    def _impact_burst(self, x, y, damage, r, exclude, mult=None):
        """부딪힌 자리의 충격: 둘레 적에게 약한 피해, 빛·고리·방사선·흔들림. 강화 2단계면 양옆으로 충격파가 퍼진다."""
        p = self.owner
        size, enhanced, fx = r['size'], r['enhanced'], r['fx']
        color = fx['damage_color']
        radius = config.GAUNTLET_IMPACT_RADIUS * size * (1.4 if enhanced else 1.0)
        if mult is None:
            mult = config.GAUNTLET_SPLASH * (2.0 if enhanced else 1.0)
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            if e.alive and id(e) not in exclude and Pipe._within(e, x, y, radius):
                self._hit(e, damage * mult, config.GAIN_HIT, fx, big=mult >= 1.0, shake=0.5, stop=0.4, extra=False)
        effects.spawn('haze-blast', x, y - 40, duration=0.35)
        effects.spawn_ring(x, y, color, radius_max=int(radius * 1.3), life=0.22)
        effects.spawn_ring(x, y, (255, 255, 255), radius_max=int(radius * 0.7), life=0.14)
        effects.spawn_bloom(x, y, color, big=True, life=0.22, strength=1.0)
        effects.spawn_impact(x, y, r['dx'], r['dy'], 14, color, big=True)
        effects.add_trauma(0.3 + 0.2 * size)
        if r['full'] or size >= 1.5:
            effects.request_flash(0.035)
        if p.on_ground:
            effects.ground_slam(x, p.y, power=0.5 + 0.3 * size, color=color)
        if enhanced and self.level >= 2:                 # 2단계: 부딪힌 자리에서 양옆으로 땅을 타는 충격파
            for side in (-1, 1):
                game_world.add_object(Blast(self, x + side * 30, y, side, 0.0, damage * 0.6, 0.9, fx, enhanced),
                                      game_world.LAYER_EFFECT)


class RushTrail:
    """돌진 강타 궤적: 지나온 자리에 굵은 빛줄기(앞이 굵고 밝다) + 위아래 속도선 + 주먹 앞 빛. 돌진이 끝나면 짧게 옅어진다.
    모두 정수 좌표의 사각형과 빛 층(light/dot_48)으로 그린다 (회전 없음)."""
    FADE = 0.18

    def __init__(self, weapon, color, size):
        self.weapon, self.color, self.size = weapon, color, size
        self.points = []
        self.fade = 0.0
        self.age = 0.0
        self.dir = (1.0, 0.0)

    def update(self, dt):
        self.age += dt
        w = self.weapon
        if w.rush is not None and self.fade == 0.0:
            self.points.append(w.owner.center)
            del self.points[:-9]
            self.dir = (w.rush['dx'], w.rush['dy'])
        else:
            self.fade += dt
            if self.fade >= self.FADE:
                game_world.remove_object(self)

    def draw(self):
        if len(self.points) < 2:
            return
        a = 1.0 - self.fade / self.FADE
        dx, dy = self.dir
        nx, ny = -dy, dx
        n = len(self.points)
        for i, ((x0, y0), (x1, y1)) in enumerate(zip(self.points, self.points[1:])):
            k = (i + 1) / n                               # 앞(최근)일수록 굵고 밝다
            thick = 2 + 2 * int(k * 5 * min(1.4, self.size))
            length = math.hypot(x1 - x0, y1 - y0)
            s = 0.0
            while s <= length:
                t = s / max(length, 1.0)
                x, y = _snap(x0 + (x1 - x0) * t), _snap(y0 + (y1 - y0) * t)
                assets.draw_rect_color(x - thick // 2, y - thick // 2, thick, thick, self.color, alpha=0.35 * a * k)
                assets.draw_rect_color(x - 2, y - 2, 4, 4, (255, 255, 255), alpha=0.8 * a * k)
                if i % 2 == 0:                            # 위아래 속도선
                    for off in (-22, 22):
                        assets.draw_rect_color(_snap(x + nx * off), _snap(y + ny * off), 6, 2, (230, 240, 255), alpha=0.5 * a * k)
                s += 4
        if self.fade == 0.0:                              # 주먹 앞 빛 (빛 층)
            x, y = self.points[-1]
            img = assets.image('light/dot_48.png')
            img.opacify(0.8)
            assets.draw_image_added(img, int(x + dx * 34), int(y + dy * 34) - img.h // 2, color=self.color, times=1)
            img.opacify(1.0)


class Blast:
    """건틀릿 충격파 (11/24부터 기본 공격은 돌진 강타): 강화 2단계 양옆 충격파·'역류'가 되돌린 투사체.
    날아가며 닿는 적을 모두 친다(관통). 벽에 닿으면 터진다."""

    def __init__(self, weapon, x, y, dx, dy, damage, size, fx, enhanced):
        self.weapon, self.x, self.y, self.dx, self.dy = weapon, x, y, dx, dy
        self.damage, self.size, self.fx, self.enhanced = damage, size, fx, enhanced
        self.radius = config.GAUNTLET_RADIUS * size
        self.life = config.GAUNTLET_LIFE
        self.time = 0.0
        self.hit = set()
        self.sprite = 's' if size < 1.2 else 'm' if size < 1.5 else 'l'
        self.collapse = False                            # v7 '헤이즈 붕괴': 처음 맞힌 자리에서 폭발
        self.reflected = False                           # v7 '역류': 적 투사체를 되돌린 충격파

    def update(self, dt):
        self.time += dt
        self.life -= dt
        step = config.GAUNTLET_SPEED * dt
        self.x += self.dx * step
        self.y += self.dy * step
        room = self.weapon.owner.room
        if self.life <= 0 or (room is not None and room.tile_at_world(self.x, self.y) == '#'):
            effects.spawn('haze-blast', self.x, self.y - 40, duration=0.35)
            if self.collapse:                            # 아무도 못 맞혀도 끝난 자리에서 터진다
                self.collapse = False
                _collapse_burst(self.weapon, (self.x, self.y), self.damage, self.fx)
            game_world.remove_object(self)
            return
        for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
            if not enemy.alive or id(enemy) in self.hit:
                continue
            if Pipe._within(enemy, self.x, self.y, self.radius):
                self.hit.add(id(enemy))
                import mutations
                p = self.weapon.owner
                damage = self.damage
                counter = _in_windup(enemy) and any(mutations.has(p, m) for m in
                                                    ('counter_power', 'counter_guard', 'counter_gain', 'counter_evo'))
                if counter:                              # v7 반격: 예고 중인 적을 쳤다
                    damage *= mutations.COUNTER_POWER if mutations.has(p, 'counter_power') else 1.0
                    _counter_success(p, enemy, self.weapon)
                killed = self.weapon._hit(enemy, damage, config.GAIN_HIT, self.fx, big=self.size >= 1.5 or counter,
                                          shake=1.0 + 0.5 * self.size, stop=1.2, blast=self.enhanced, extra=False)
                if (not killed and not getattr(enemy, 'BOSS', False) and
                        any(mutations.has(p, m) for m in ('crash_wall', 'crash_stun', 'crash_evo'))):   # v7 충돌 갈래: 날아간다
                    side = 1 if self.dx >= 0 else -1
                    speed = config.GAUNTLET_KNOCK * 0.7 * min(1.0, self.size) * self.weapon.knock_mult()
                    game_world.add_object(Fling(self.weapon, enemy, damage, side * speed), game_world.LAYER_EFFECT)
                if self.collapse:
                    self.collapse = False
                    _collapse_burst(self.weapon, enemy.center, damage, self.fx)

    def draw(self):
        img = assets.image(f'sprites/unified/proj_blast_{self.sprite}_{int(self.time * 16) % 2 + 1}.png')
        assets.draw_image(img, self.x, self.y - img.h // 2, 'h' if self.dx < 0 else '')


def _in_windup(enemy):
    """적이 공격 예고 중인가 (반격 갈래). 기술을 시작했고 아직 판정이 나오기 전."""
    stats = getattr(enemy, 'stats', {}) or {}
    return (getattr(enemy, 'state', None) == 'ATTACK' and
            getattr(enemy, 'attack_time', 99.0) < stats.get('windup', 0.0))


def _counter_success(p, enemy, weapon):
    """반격 성공: 무적·게이지·역류(진화), 흰 번쩍임과 글자."""
    import mutations
    cx, cy = p.center
    effects.float_text(cx, cy + 130, '반격!', mutations.FAMILIES['gauntlet_counter']['color'], big=True, life=0.7)
    effects.spawn_bloom(*enemy.center, (255, 255, 255), big=True, life=0.2, strength=0.9)
    if mutations.has(p, 'counter_guard'):
        p.invuln_left = max(p.invuln_left, mutations.COUNTER_GUARD)
        p.steady_left = max(getattr(p, 'steady_left', 0.0), mutations.COUNTER_GUARD)   # 무적이어도 깜빡이지 않는다
    if mutations.has(p, 'counter_gain'):
        p.gauge.add(mutations.COUNTER_GAIN, 'hit')
    if mutations.has(p, 'counter_evo'):
        _backflow(p, weapon)
    if mutations.has(p, 'duo_counter_ring'):           # v8 합성 '반격 탄막': 다른 칸의 쌍권총이 사방으로 쏜다
        for w in getattr(p, 'weapons', None) or ():
            if w is not None and w.weapon_id == 'pistol':
                w.ring_burst()
                break


def _backflow(p, weapon):
    """v7 진화 '역류': 흰 고리 충격파가 둘레의 적 투사체를 되돌린다 (투사체 -> 주인공 반대쪽으로 나는 충격파)."""
    import mutations
    radius, mult = mutations.BACKFLOW
    cx, cy = p.center
    effects.spawn_ring(cx, cy, (255, 255, 255), radius_max=radius, life=0.25)
    effects.request_flash(0.04)
    for o in list(game_world.world[game_world.LAYER_EFFECT]):
        if getattr(o, 'player', None) is not p or not hasattr(o, 'damage') or not hasattr(o, 'x'):
            continue                                     # 적 투사체만 (주인공을 노리는 것)
        dx, dy = o.x - cx, o.y - cy
        d = math.hypot(dx, dy)
        if d > radius:
            continue
        game_world.remove_object(o)
        ux, uy = (dx / d, dy / d) if d > 1 else (p.face_dir, 0.0)
        back = Blast(weapon, o.x, o.y, ux, uy, max(8.0, o.damage * mult), 0.9, weapon._fx(False), False)
        back.reflected = True
        game_world.add_object(back, game_world.LAYER_EFFECT)


PARRY_KINDS = ('Scrap', 'Lob', 'Debris', 'HazeBullet', 'CrystalShard')   # 쳐 낼 수 있는 날아오는 것 (충격파·장판·증기는 못 쳐 낸다)


def _parry_shots(p, radius):
    """주인공을 노리는 적 투사체 가운데 radius 안에 온 것을 쳐 낸다 (불꽃 + 소리). 쳐 낸 수를 돌려준다."""
    cx, cy = p.center
    n = 0
    for o in list(game_world.world[game_world.LAYER_EFFECT]):
        if type(o).__name__ not in PARRY_KINDS or getattr(o, 'player', None) is not p or getattr(o, 'y', None) is None:
            continue
        if math.hypot(o.x - cx, o.y - cy) > radius:
            continue
        game_world.remove_object(o)
        effects.spawn_impact(o.x, o.y, o.x - cx, o.y - cy, 8, (255, 220, 160), big=True)
        effects.spawn_bloom(o.x, o.y, (255, 220, 160), life=0.14, strength=0.8)
        effects.spawn_flare(o.x, o.y, (255, 210, 140))
        effects.spawn_ring(o.x, o.y, (255, 200, 120), radius_max=70, life=0.16)
        n += 1
    if n:
        assets.play_sound('impact_gauntlet')
        effects.add_trauma(config.SHAKE_HIT)
    return n


def _collapse_burst(weapon, center, damage, fx):
    """v7 진화 '헤이즈 붕괴': 폭발 원 + 화면 번쩍 + 큰 빛. 둘레 적 모두에게 피해."""
    import mutations
    radius, mult = mutations.COLLAPSE
    x, y = center
    effects.spawn('haze-blast', x, y - 40, duration=0.5)
    effects.spawn_ring(x, y, (255, 200, 120), radius_max=radius, life=0.3)
    effects.spawn_bloom(x, y, (255, 230, 180), big=True, life=0.3, strength=1.0)
    effects.request_flash(0.06)
    effects.add_trauma(config.SHAKE_FINISHER * 1.2)
    assets.play_sound('impact_enh2')
    for enemy in list(game_world.world[game_world.LAYER_ENEMY]):
        if enemy.alive and Pipe._within(enemy, x, y, radius):
            weapon._hit(enemy, damage * mult, config.GAIN_HIT, fx, big=True, shake=1.0, extra=False)


class Fling:
    """v7 충돌 갈래: 강타로 날아가는 적을 잠깐 지켜본다. 벽에 막히면 '벽꽝' 피해, 멈추면 '뇌진탕' 기절,
    날아가다 다른 적에 닿으면 '연쇄 충돌'(그 적도 같은 쪽으로 날아간다)."""

    def __init__(self, weapon, enemy, damage, speed, chained=()):
        self.weapon, self.enemy, self.damage = weapon, enemy, damage
        self.time = 0.0
        self.speed = speed                               # 날아가는 속도 (부호 = 방향). 적의 원래 감속보다 천천히 줄인다
        self.prev_vx = enemy.vx = speed
        self.done = set(id(e) for e in chained) | {id(enemy)}

    def update(self, dt):
        import mutations
        e, p = self.enemy, self.weapon.owner
        self.time += dt
        if not e.alive:
            game_world.remove_object(self)
            return
        fast = abs(self.prev_vx) > 150
        if e.state == 'HIT':
            e.hit_left = max(e.hit_left, 0.05)
        if fast and abs(e.vx) < 1.0:                      # 벽에 막혔다 (stop_on_wall)
            if mutations.has(p, 'crash_wall'):
                effects.spawn_impact(*e.center, -self.prev_vx, 0, 10, (255, 200, 140), big=True)
                effects.add_trauma(config.SHAKE_HIT * 2)
                assets.play_sound('impact_gauntlet')
                self.weapon._hit(e, self.damage * mutations.CRASH_WALL, config.GAIN_HIT, self.weapon._fx(False), big=True, extra=False)
            self._end()
            return
        if mutations.has(p, 'crash_evo') and fast:      # 날아가다 다른 적에 닿았다: 볼링
            for other in list(game_world.world[game_world.LAYER_ENEMY]):
                if not other.alive or id(other) in self.done or not _overlap(e.rect(), other.rect()):
                    continue
                self.done.add(id(other))
                self.weapon._hit(other, self.damage * mutations.CRASH_CHAIN, config.GAIN_HIT, self.weapon._fx(False),
                                 big=True, extra=False)
                if other.alive and not getattr(other, 'BOSS', False):
                    game_world.add_object(Fling(self.weapon, other, self.damage, self.speed * 0.9, self.done),
                                          game_world.LAYER_EFFECT)
        self.speed *= max(0.0, 1.0 - mutations.CRASH_FLING[1] * dt)
        if self.time > mutations.CRASH_FLY or abs(self.speed) < 80:
            self._end()
            return
        e.vx = self.speed                                # 다음 프레임에도 날아간다
        if e.state == 'HIT':
            e.hit_left = max(e.hit_left, 0.05)           # 날아가는 동안은 경직이 풀리지 않는다 (날면서 공격하지 않게)
        self.prev_vx = e.vx

    def _end(self):
        import mutations
        e, p = self.enemy, self.weapon.owner
        if mutations.has(p, 'crash_stun') and e.alive:
            e.hold(mutations.CRASH_STUN)
        game_world.remove_object(self)

    def draw(self):
        pass


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


# =====================================================================================================
# 헤이즈 사슬 (중거리, 제어형): 조준 방향으로 갈고리를 던져 맞은 적을 플레이어 앞까지 끌어온다. 끌려온 적 1마리당 게이지 +2%.
# 노멀: 1마리 / 각성: 사거리 +30%, 2마리 / 위험: 각성 + 끌려온 적 1초 기절, 함께 끌려온 적끼리 부딪쳐 충돌 피해.
# E 강화: 사슬이 닿는 적을 모두 꿰고(관통) 끌려온 적은 1초 기절. 보스는 끌려오지 않는 대신 갈고리가 박혀 피해 x1.5.
# 갈고리가 돌아오기 전에는 다시 던지지 못한다. 사슬 그림은 코드로 그린 고리 칸이다(회전 없음).
# =====================================================================================================
class Chain(Pipe):
    IMPACT = None
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
        """대시 중·직후 = 멀리 던지기, 공중 = 강하게 낚기, 그 밖 = 기본."""
        kind = self.ult_kind()
        return {'dash': 'chain_dash', 'jump': 'chain_air'}.get(kind, 'chain')

    def grip(self, enhanced=None, kind=None):
        """지금 구간·공격 종류에서 (끌 수 있는 적 수, 사거리, 끌려온 적 기절·충돌)."""
        p = self.owner
        enhanced = p.gauge.enhanced if enhanced is None else enhanced
        kind = kind or self.current_kind()
        count, reach_mult, stun = config.CHAIN_ZONE[p.gauge.zone]
        if kind == 'chain_dash':                                    # 대시: 더 멀리, 한 마리 더
            count, reach_mult = count + config.CHAIN_DASH_EXTRA, reach_mult * config.CHAIN_DASH_REACH
        if enhanced:
            count, stun = 99, True                                  # 관통: 닿는 적 모두
        import mutations
        if mutations.has(p, 'gather_more'):                         # v7 '한 마리 더'
            count += 1
        if mutations.has(p, 'pierce_reach'):                        # v7 '긴 사슬'
            reach_mult *= mutations.PIERCE_REACH
        return count, config.CHAIN_RANGE * reach_mult, stun

    def rush_velocity(self):
        """v8 형태 '갈고리 이동': 걸린 적에게 날아가는 동안의 속도 (Player._apply_swing_motion이 쓴다). 아니면 None."""
        import forms
        return forms.zip_velocity(self)

    def on_put_away(self):
        import forms
        forms.cancel(self)

    def try_attack(self):
        if not self.ready:
            return False
        if self._try_ultimate():
            return True
        p = self.owner
        kind = self.current_kind()
        import forms
        if forms.busy(self):
            return False
        if kind == 'chain' and forms.active(self) and not p.gauge.enhanced:    # v8 형태 '갈고리 이동'
            return forms.chain_attack(self)
        enhanced = self._take_level()
        self.last_kind, self.last_enhanced = kind, enhanced
        count, reach, stun = self.grip(enhanced, kind)
        ax, ay = p.aim_vector()
        damage = self._damage(config.ENHANCE_DAMAGE_MULT * 0.6 * self._stack() if enhanced else 1.0)
        if kind == 'chain_air':                                     # 공중: 내리꽂듯 강하게
            damage *= config.CHAIN_AIR_MULT
        self.hook = ChainHook(self, ax, ay, damage, count, reach, stun, self._fx(enhanced), enhanced)
        game_world.add_object(self.hook, game_world.LAYER_EFFECT)
        import drama
        assets.play_sound(drama.chain_sound(p.gauge.zone, enhanced))   # 구간·강화마다 다른 사슬 소리 (11/21)
        p.start_punch('throw')
        self.cooldown = self.cooldown_max = config.CHAIN_COOLDOWN
        if enhanced:
            effects.add_trauma(config.SHAKE_FINISHER * 0.5)
        self._finish(enhanced)
        return True


class ChainHook:
    """사슬 갈고리 하나. out(날아감) -> pull(걸린 적을 끌어옴) 또는 back(빈 갈고리가 돌아옴) -> 끝."""
    LINK = 10                          # 고리 사이 간격(px)

    def __init__(self, weapon, dx, dy, damage, count, reach, stun, fx, enhanced):
        self.weapon, self.dx, self.dy = weapon, dx, dy
        self.damage, self.count, self.reach, self.stun = damage, count, reach, stun
        self.fx, self.enhanced = fx, enhanced
        self.level = weapon.level if enhanced else 0     # 2단계면 돌아올 때 주인공 둘레에 충격
        self.dist = 0.0                # 손에서 갈고리 끝까지 거리 (out·back)
        self.phase = 'out'
        self.hit = set()
        self.hooked = []               # 갈고리에 맞은 적 (보스 포함)
        self.pulled = []               # 그중 끌려오는 적
        self.pull_time = 0.0
        self.tip = self.origin()
        import mutations
        p = weapon.owner
        self.pulls = enhanced or mutations.chain_pulls(p)           # v8: 기본은 타격. 끌어오기는 모으기 갈래 증강이나 E 강화일 때만
        if not self.pulls:
            self.damage *= config.CHAIN_LASH_MULT                  # 끌어오지 않는 타격은 그만큼 세다
        self.wall_zip = mutations.has(p, 'gather_wall')             # v8 증강 '벽 걸기'
        self.pierce = mutations.has(p, 'pierce_through')            # v7 '꿰뚫기': 끌어오는 수를 넘어도 계속 날아가며 맞힌다
        self.ramp = mutations.PIERCE_RAMP if mutations.has(p, 'pierce_ramp') else 0.0
        self.bounces = mutations.PIERCE_BOUNCES if mutations.has(p, 'pierce_evo') else 0   # v7 진화 '반사 사슬'
        self.bends = []                # 벽에 꺾인 점들 (반사 사슬)
        self.seg_dist = 0.0            # 마지막 꺾인 점(없으면 손)에서 갈고리 끝까지
        self.age = 0.0                 # v7 이펙트: 흐르는 빛 마디·떨림 시계
        self.trail = []                # v7 이펙트: 날아가는 갈고리 뒤 잔상 (최근 위치)

    def origin(self):
        p = self.weapon.owner
        cx, cy = p.center
        return cx + self.dx * 20, cy + 8 + self.dy * 20

    # ----- 갱신 -----
    def update(self, dt):
        self.age += dt
        if self.phase == 'out':
            self.trail.append(self.tip)
            del self.trail[:-6]
        else:
            self.trail = []
        getattr(self, '_update_' + self.phase)(dt)

    def _seg_origin(self):
        return self.bends[-1] if self.bends else self.origin()

    def _update_out(self, dt):
        p = self.weapon.owner
        step = min(self.reach, self.dist + config.CHAIN_SPEED * dt) - self.dist
        self.dist += step
        self.seg_dist += step
        ox, oy = self._seg_origin()
        prev = self.tip
        self.tip = (ox + self.dx * self.seg_dist, oy + self.dy * self.seg_dist)
        room = p.room
        if room is not None and room.tile_at_world(*self.tip) == '#':
            effects.spawn('puff', self.tip[0], self.tip[1] - 20, duration=0.2)
            if self.bounces > 0 and self.dist < self.reach:
                self._bounce(room, prev)
                return
            if self.wall_zip and not self.hooked:                   # v8 '벽 걸기': 빈 사슬이 벽에 닿았다 -> 그 벽으로 날아간다
                import forms
                self.tip = prev
                forms.start_wall_zip(self.weapon, prev)
                self.phase = 'anchor'
                assets.play_sound('chain_clash')
                return
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
                ramp = 1.0 + self.ramp * len(self.hooked)                       # v7 '가속 고리': 관통할수록 세진다
                self.hooked.append(enemy)
                import drama
                assets.play_sound(drama.latch_sound(self.weapon.owner.gauge.zone, self.enhanced))   # 위험·강화는 묵직하게
                damage = self.damage * ramp * (1.0 if enemy.pullable else config.CHAIN_ANCHOR_MULT)   # 보스에게는 박혀서 더 아프다
                ex, ey = enemy.center                                              # v7 이펙트: 박히는 순간 빛·고리·방사선
                glow = self.fx['damage_color'] if self.enhanced or self.stun else CHAIN_CORE
                effects.spawn_bloom(ex, ey, glow, big=True, life=0.16, strength=0.8)
                effects.spawn_ring(ex, ey, glow, radius_max=70, life=0.18)
                effects.spawn_impact(ex, ey, self.dx, self.dy, 8, CHAIN_HI)
                killed = self.weapon._hit(enemy, damage, config.CHAIN_GAIN, self.fx, big=self.enhanced,
                                          shake=0.7, stop=0.5, blast=self.enhanced, extra=False)
                if self.pulls and not killed and enemy.pullable and len(self.pulled) < self.count:
                    self.pulled.append(enemy)
                    enemy.hold(0.2)
                elif not self.pulls and not killed and self.stun:           # 끌어오지 않는 타격: 위험 구간의 기절은 맞은 자리에서
                    enemy.hold(config.CHAIN_STUN)
                if len(self.hooked) >= self.count and not self.pierce:
                    self._end_out()
                    return
        if self.dist >= self.reach:
            self._end_out()

    def _update_anchor(self, dt):
        """벽에 박힌 채 주인공이 날아오기를 기다린다 (v8 '벽 걸기'). 이동이 끝나면 사라진다."""
        st = getattr(self.weapon, 'form_state', None)
        if st is None or st.get('kind') != 'zip':
            self._done()

    def _bounce(self, room, prev):
        """반사 사슬: 벽에 닿기 직전 점에서 방향을 꺾는다. 가로로 막혔으면 dx, 세로로 막혔으면 dy를 뒤집는다."""
        px, py = prev
        tx, ty = self.tip
        flip_x = room.tile_at_world(tx, py) == '#'
        flip_y = room.tile_at_world(px, ty) == '#'
        if not flip_x and not flip_y:                               # 모서리: 둘 다 뒤집는다
            flip_x = flip_y = True
        if flip_x:
            self.dx = -self.dx
        if flip_y:
            self.dy = -self.dy
        self.bounces -= 1
        self.bends.append(prev)
        self.seg_dist = 0.0
        self.tip = prev
        assets.play_sound('chain_clash')
        effects.spawn_ring(px, py, NET_COLOR, radius_max=60, life=0.18)

    def _end_out(self):
        import mutations
        p = self.weapon.owner
        if mutations.family_count(p, 'chain_link') >= 1:            # v7 연결 갈래: 함께 걸린 적을 묶는다
            alive = [e for e in self.hooked if e.alive]
            if len(alive) >= 2:
                mutations.bind(p, alive, mutations.NET_SIZE if mutations.has(p, 'link_evo') else 2)
        if self.pulled:
            self.bends = []                                         # 끌어올 때는 손에서 적까지 곧게
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
        for e in alive:                                             # v7 이펙트: 끌려와 멈추는 순간 쾅
            ex, ey = e.center
            effects.spawn_bloom(ex, ey, CHAIN_PULSE, life=0.14, strength=0.6)
            effects.spawn_impact(ex, ey, p.x - ex, 0.0, 6, CHAIN_CORE)
        if alive:
            effects.add_trauma(config.SHAKE_HIT)
        import mutations
        stun_time = config.CHAIN_STUN if self.stun else 0.18
        if mutations.has(p, 'gather_stun'):                         # v7 '목줄'
            stun_time = max(stun_time, mutations.GATHER_STUN)
        for e in alive:
            e.hold(stun_time)
        if mutations.has(p, 'gather_evo'):                          # v7 진화 '소용돌이'
            game_world.add_object(Vortex(self.weapon, self.damage), game_world.LAYER_EFFECT)
        clash = self.stun or mutations.has(p, 'gather_clash')       # v7 '박치기': 어느 구간이든 부딪친다
        if clash and len(alive) >= 2:                               # 함께 끌려온 적끼리 부딪친다
            for e in alive:
                killed = e.take_damage(config.CHAIN_CLASH_DAMAGE, from_x=p.x)
                ex, ey = e.center
                effects.spawn(self.fx['spark'], ex, ey, duration=self.fx['spark_time'])
                effects.spawn_slash_marks(ex, ey, ex - p.x, ey - p.center[1], (255, 200, 120), big=True)
                if killed:
                    p.gauge.add(p.kill_gain(), 'kill')
                else:
                    e.hold(max(stun_time, config.CHAIN_STUN if self.stun else 0.0))   # 충돌 경직이 기절을 줄이지 않게 다시 건다
            effects.add_trauma(config.SHAKE_FINISHER * 0.6)
            assets.play_sound('chain_clash')
        self._done()

    def _update_back(self, dt):
        """빈 갈고리가 돌아온다: 꺾인 점을 거꾸로 따라 손까지."""
        move = config.CHAIN_RETURN_SPEED * dt
        while move > 0:
            gx, gy = self.bends[-1] if self.bends else self.origin()
            tx, ty = self.tip
            gap = math.hypot(gx - tx, gy - ty)
            if gap > move:
                self.tip = (tx + (gx - tx) * move / gap, ty + (gy - ty) * move / gap)
                return
            self.tip = (gx, gy)
            move -= gap
            if not self.bends:
                self._done()
                return
            self.bends.pop()

    def _done(self):
        w = self.weapon
        hx, hy = self.origin()                                      # v7 이펙트: 손에 감기는 작은 빛
        effects.spawn_bloom(hx, hy, CHAIN_CORE, life=0.12, strength=0.45)
        if self.level >= 2:
            self._shock()
        if w.hook is self:
            w.hook = None
        w.cooldown = w.cooldown_max = config.CHAIN_COOLDOWN
        game_world.remove_object(self)

    def _shock(self):
        """강화 2단계: 사슬이 돌아오는 순간 주인공 둘레(CHAIN_SHOCK_RADIUS)에 충격. 갈고리에 안 걸린 적도 맞는다."""
        w, p = self.weapon, self.weapon.owner
        cx, cy = p.center
        effects.spawn('quake-blast', p.x, p.y, duration=0.4)
        effects.ground_slam(p.x, p.y, power=0.9)                                          # v7 땅 강타
        effects.spawn('hit-enhanced2', cx, cy, duration=0.35)
        effects.add_trauma(config.SHAKE_FINISHER)
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            ex, ey = e.center
            if e.alive and math.hypot(ex - cx, ey - cy) <= config.CHAIN_SHOCK_RADIUS:
                w._hit(e, self.damage * config.CHAIN_SHOCK_MULT, config.CHAIN_GAIN, self.fx, big=True, shake=0.5,
                       stop=0.4, extra=False)

    # ----- 그리기 (v7 이펙트 개편): 빛나는 심줄 위 고리 + 작살 갈고리 + 던질 때 잔상, 당길 때 팽팽한 떨림 -----
    def draw(self):
        tx, ty = self.tip
        glow = self.fx['damage_color'] if self.enhanced or self.stun else CHAIN_CORE
        points = [self.origin()] + list(self.bends) + [self.tip]        # 반사 사슬이면 꺾인 점마다 한 토막
        pulling = self.phase == 'pull'
        for i, (px, py) in enumerate(self.trail[:-1]):                  # 날아가는 갈고리 뒤 잔상
            s = 2 + 2 * (i * 3 // max(1, len(self.trail)))
            assets.draw_rect_color(_snap(px) - s // 2, _snap(py) - s // 2, s, s, glow, alpha=0.3 + 0.1 * i)
        draw_chain(points, glow, age=self.age, flow=-1 if pulling else 1, shake=2.5 if pulling else 0.0, link=self.LINK)
        ox, oy = points[-2]
        draw_hook(tx, ty, tx - ox, ty - oy, glow)


# =====================================================================================================
# 궁극기 (E 3단계로 공격, 11/19): 무기 x 공격 종류(기본·대시·점프)마다 이름이 있다. 시전하는 순간 화면이 멈추고
# 어두워지며 기술 이름 띠가 지나간 뒤, 범위 안의 적을 여러 번(ULT_HITS) 크게 친다. 플레이어는 그동안 무적.
# 범위: 기본 = 앞쪽 화면 절반 / 대시 = 조준 방향 긴 직선 / 점프 = 좌우 넓게 내려찍기. 궁극기는 **벽·기둥 너머도 맞는다**
# (게이지 75%를 쓰는 화면 기술이라 일반 공격의 시야선 규칙에서 뺐다. 보스는 피해 상한이 있다).
# 보스에게는 한 번에 최대 체력의 ULT_BOSS_CAP까지만. 궁극기 타격은 게이지를 올리지 않는다(처치 보너스만).
# 무기마다 범위 모양이 다르다 (ULT_AREAS): 식칼 = 조준한 곳 일대 칼비, 건틀릿 = 멀리 뻗는 광선,
# 사슬 = 주위 적을 끌어모아 터뜨림. 철파이프는 앞쪽 화면 절반·긴 직선·좌우 내려찍기.
# 컷인 그림은 Codex T23이 오면 이름 띠 자리에 넣는다.
# =====================================================================================================
# 궁극기 v2 (2026-11-24): 무기마다 기술 하나, 구성이 서로 다르다 (아래 Ultimate와 무기별 클래스)
ULT_NAMES = {'pipe': '안개 난무', 'pistol': '록온 난사', 'gauntlet': '유성 돌진', 'chain': '사슬 감옥'}
ULT_COLORS = {'pipe': (150, 235, 255), 'pistol': (180, 250, 240), 'gauntlet': (255, 176, 110), 'chain': (200, 160, 255)}   # 11/25 색 정리: 건틀릿은 주황 (각인 빛·폭발 시트와 같은 계열. 전에는 청록이었다)
ULT_DEEP = {'pipe': (40, 190, 255), 'pistol': (40, 235, 180), 'gauntlet': (255, 130, 40), 'chain': (160, 90, 255)}   # 마무리 연출의 진한 면 색


class Decor:
    """궁극기 연출용 날아가는 그림 (판정 없음): 떨어지는 칼 같은 것."""

    def __init__(self, path, x, y, vx, vy, life):
        self.path, self.x, self.y, self.vx, self.vy, self.life = path, x, y, vx, vy, life

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.life <= 0:
            game_world.remove_object(self)

    def draw(self):
        img = assets.image(self.path)
        assets.draw_image(img, self.x, self.y - img.h // 2)


# ----- v7 사슬 그리기 (2026-11-24 이펙트 개편): 빛나는 헤이즈 심줄 위에 쇠고리, 끝에 작살 갈고리 -----
CHAIN_INK = (10, 12, 20)
CHAIN_METAL = (128, 142, 164)
CHAIN_HI = (236, 244, 252)
CHAIN_CORE = (46, 230, 214)          # 고리 사이를 잇는 헤이즈 심줄
CHAIN_PULSE = (210, 255, 248)        # 심줄을 따라 흐르는 밝은 마디


def _snap(v):
    return int(round(v)) // 2 * 2


def draw_chain(points, glow=CHAIN_CORE, age=0.0, flow=1, shake=0.0, link=10, light=True):
    """점들(손 -> 꺾인 점 -> 끝)을 잇는 사슬. 아래에 빛나는 심줄(흐르는 밝은 마디), 위에 눕힌 고리·세운 고리를 번갈아.
    flow: 밝은 마디가 흐르는 쪽 (+1 끝으로 = 던질 때, -1 손으로 = 당길 때). shake: 팽팽할 때 옆으로 떨리는 정도(px).
    모두 정수 좌표의 2px 사각형으로 그린다 (회전 없음)."""
    segs = list(zip(points, points[1:]))
    total = 0.0
    for (ox, oy), (ex, ey) in segs:
        length = math.hypot(ex - ox, ey - oy) or 1.0
        nx, ny = -(ey - oy) / length, (ex - ox) / length          # 옆 방향 (떨림)
        steep = abs(ey - oy) > abs(ex - ox)
        s = 0.0
        while s <= length:                                        # 심줄
            k = s / length
            wob = shake * math.sin(age * 55 + (total + s) * 0.12)
            x, y = _snap(ox + (ex - ox) * k + nx * wob), _snap(oy + (ey - oy) * k + ny * wob)
            hot = ((total + s) - flow * age * 700) % 70 < 14
            assets.draw_rect_color(x - 1, y - 1, 2, 2, CHAIN_PULSE if hot else glow)
            s += 2
        i = 0
        s = link * 0.5
        while s < length:                                         # 고리
            k = s / length
            wob = shake * math.sin(age * 55 + (total + s) * 0.12)
            x, y = _snap(ox + (ex - ox) * k + nx * wob), _snap(oy + (ey - oy) * k + ny * wob)
            flat = (i % 2 == 0) != steep
            w, h = (10, 6) if flat else (4, 8)
            assets.draw_rect_color(x - w // 2 - 2, y - h // 2 - 2, w + 4, h + 4, CHAIN_INK)
            assets.draw_rect_color(x - w // 2, y - h // 2, w, h, CHAIN_METAL)
            if flat:
                assets.draw_rect_color(x - w // 2 + 2, y - 1, w - 4, 2, CHAIN_INK)        # 고리 구멍
                assets.draw_rect_color(x - w // 2, y - h // 2, 4, 2, CHAIN_HI)             # 빛 받은 윗변
            else:
                assets.draw_rect_color(x - w // 2, y - h // 2, 2, 4, CHAIN_HI)
            if light and i % 4 == 0:                              # 고리 몇 개마다 부드러운 빛 (빛 층)
                img = assets.image('light/dot_48.png')
                img.opacify(0.35)
                assets.draw_image_added(img, x, y - img.h // 2, color=glow, times=1)
                img.opacify(1.0)
            i += 1
            s += link
        total += length


# 작살 갈고리 모양 (2px 칸 단위, 앞 = +x). 가운데 날 + 뒤로 휜 미늘 둘
HOOK_SHAPE = ([(x, 0) for x in range(-3, 8)] + [(x, y) for x in range(-3, 5) for y in (-1, 1)] +
              [(3, 2), (2, 3), (1, 4), (0, 4), (3, -2), (2, -3), (1, -4), (0, -4)])
HOOK_EDGE = {(7, 0), (6, 0), (5, 0)}                             # 날 끝 (흰색)


def draw_hook(x, y, dx, dy, glow=CHAIN_CORE):
    """작살 갈고리 머리: 진행 방향 (dx, dy)으로 돌린 칸 모양을 정수 좌표로 찍는다. 검은 테두리 -> 쇠 -> 날 끝 흰색 -> 헤이즈 심."""
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    pts = []
    for (a, b) in HOOK_SHAPE:                                     # 칸 하나 = 3px (빈틈 없게 4px 사각으로 찍는다)
        px = x + (a * ux - b * uy) * 3
        py = y + (a * uy + b * ux) * 3
        pts.append((_snap(px), _snap(py), (a, b)))
    img = assets.image('light/dot_48.png')
    img.opacify(0.7)
    assets.draw_image_added(img, int(x), int(y) - img.h // 2, color=glow, times=1)
    img.opacify(1.0)
    for px, py, _ in pts:
        assets.draw_rect_color(px - 4, py - 4, 8, 8, CHAIN_INK)
    for px, py, key in pts:
        color = CHAIN_HI if key in HOOK_EDGE else glow if key[1] == 0 and key[0] < 3 else CHAIN_METAL
        assets.draw_rect_color(px - 2, py - 2, 4, 4, color)


def draw_chain_line(x0, y0, x1, y1, glow, link=12):
    """(x0, y0)에서 (x1, y1)까지 사슬 (헤이즈 그물·궁극기 사슬 줄). 갈고리 사슬과 같은 그림."""
    draw_chain([(x0, y0), (x1, y1)], glow, link=link, light=False)


class Ultimate:
    """궁극기 공통 (v2, 2026-11-24 사용자: 무기별로 다르게 구성, 화면 멈춤·컷인 띠는 없앤다 - 흐름을 끊지 않는다).
    무기마다 아래 클래스 하나. 적 하나가 받는 피해 합은 무기와 상관없이 같다(ULT_BASE_DAMAGE x ULT_HIT_MULT x ULT_HITS),
    보스는 한 번에 최대 체력의 ULT_BOSS_CAP까지. 타격은 게이지를 올리지 않는다. 시전하는 동안 무적."""
    is_ultimate = True

    def __init__(self, weapon, kind, ax, ay):
        p = weapon.owner
        wid = weapon.weapon_id
        self.weapon, self.kind = weapon, kind
        self.name = ULT_NAMES[wid]
        self.color = ULT_COLORS[wid]
        self.x0, self.y0 = p.center
        self.floor_y = p.y
        self.side = 1 if ax >= 0 else -1
        length = math.hypot(ax, ay) or 1.0
        self.dx, self.dy = ax / length, ay / length
        self.nova_count = 0                                           # 광역 폭발 이펙트를 터뜨린 횟수 (테스트)
        self.nova_name = 'ult-nova-' + wid                            # 무기마다 색·모양이 다른 폭발
        self.time = 0.0
        self.hits_done = 0
        self.dealt = {}
        self.struck = {}
        self.targets = []
        self.started = False
        effects.add_trauma(0.6)
        p.invuln_left = max(p.invuln_left, config.ULT_INVULN)
        p.steady_left = max(p.steady_left, config.ULT_INVULN)   # 무적이지만 깜빡이지 않는다
        assets.play_sound('ult_cast')
        effects.spawn_blur(*p.center, self.color, p)                            # 시전 순간에도 블러
        effects.float_text(p.x, p.y + config.PLAYER_HB_H + 70, self.name, self.color, big=True, life=0.9)
        game_world.add_object(ExecDim(color=(6, 8, 26), strength=config.ULT_DIM * 2, life=0.7), game_world.LAYER_TILES)
        self._nova(*p.center, duration=0.4)

    # ----- 공통 도구 -----
    def _nova(self, x, y, duration=0.55):
        effects.spawn(self.nova_name, x, y, duration=duration)
        self.nova_count += 1

    def _deal(self, e, share, last=False):
        """적 하나에게 궁극기 피해 합의 share만큼. 보스는 상한까지만. 죽였으면 True."""
        p = self.weapon.owner
        damage = (config.ULT_BASE_DAMAGE * p.gauge.zone_multipliers()['attack'] * p.attack_bonus *
                  config.ULT_HIT_MULT * config.ULT_HITS * share)
        if not getattr(e, 'pullable', True):              # 보스: 한 번의 궁극기로 최대 체력의 ULT_BOSS_CAP까지만
            damage = min(damage, e.max_hp * config.ULT_BOSS_CAP - self.dealt.get(id(e), 0.0))
        if damage <= 0 or not e.alive:
            return False
        fx = config.ENHANCED_FX_BY_LEVEL[3]             # 궁극기(3단계): 진홍
        import drama
        with drama.hit_style(big=last, color=self.color):
            killed = e.take_damage(damage, from_x=p.x)
        self.dealt[id(e)] = self.dealt.get(id(e), 0.0) + damage
        self.struck[id(e)] = e                         # 마무리의 블러가 맞은 적들도 번지게 한다
        ex, ey = e.center
        effects.spawn(fx['spark'], ex, ey, duration=fx['spark_time'])
        effects.spawn_impact(ex, ey, ex - p.x, ey - p.center[1], config.IMPACT_RAYS['enhanced'], self.color, big=last)
        effects.spawn_slash_marks(ex, ey, ex - p.x, ey - p.center[1], self.color, big=True, count=2 if last else 1)
        effects.spawn_bloom(ex, ey, self.color, big=last, strength=0.9)
        if killed:
            p.gauge.add(p.kill_gain(), 'kill')
        if last:
            effects.spawn('haze-blast', ex, ey - 40, duration=0.45)
            effects.spawn_flare(ex, ey, self.color)
        return killed

    def _finale(self, cx, cy):
        """마지막 일격: 광역 폭발 + 큰 마무리 연출(FinisherCut) + 무기별 마무리 소리 (화면은 멈추지 않고 잠깐 느려진다)."""
        effects.add_trauma(0.8)
        self._nova(cx, cy)
        # 11/24 사용자: 처형과 같은 마무리 연출 (예고 초승달 없이 첫 일격부터). 빛기둥·큰 고리·별 섬광은 이것으로 대신한다
        game_world.add_object(FinisherCut(cx, cy, ULT_DEEP[self.weapon.weapon_id], self.weapon.owner, start=FinisherCut.T1, slow=(0.36, 0.2),
                                          victims=list(self.struck.values())), game_world.LAYER_EFFECT)
        assets.play_sound(f'ult_final_{self.weapon.weapon_id}')

    def _in_reach(self, radius, sight=True):
        """시전 자리에서 radius 안의 살아 있는 적 (sight면 벽에 가린 적은 뺀다), 가까운 순."""
        found = []
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            if not e.alive:
                continue
            ex, ey = e.center
            d = math.hypot(ex - self.x0, ey - self.y0)
            if d <= radius and (not sight or self.weapon._visible(e, self.x0, self.y0)):
                found.append((d, id(e), e))
        return [e for _, _, e in sorted(found)]

    def _end(self):
        game_world.remove_object(self)

    def update(self, dt):
        if not self.started:
            self.started = True
            self._start()
        self.time += dt
        self._step(dt)

    def _start(self):
        pass

    def _step(self, dt):
        self._end()

    def draw(self):
        pass


class PipeUlt(Ultimate):
    """철파이프 '안개 난무': 둘레 적들 사이를 순간이동하며 벤다. 한 번 벨 때마다 걸린 적 모두에게 베기가 들어가고,
    마지막에 제자리로 돌아오며 한꺼번에 터진다."""
    BLINK = 0.085

    def _start(self):
        p = self.weapon.owner
        p.ult_pose_left = 0.0
        self.targets = self._in_reach(config.ULT_FLURRY_RADIUS)[:config.ULT_FLURRY_TARGETS]
        self.home = (p.x, p.y)
        self.prev = p.center

    def _free(self, x, y):
        """그 자리에 주인공 몸이 벽에 끼지 않고 설 수 있나."""
        room = self.weapon.owner.room
        if room is None:
            return True
        hw = config.PLAYER_HB_W / 2 - 2
        for px in (x - hw, x, x + hw):
            for py in (y + 4, y + config.PLAYER_HB_H / 2, y + config.PLAYER_HB_H - 4):
                if room.tile_at_world(px, py) == '#':
                    return False
        return True

    def _step(self, dt):
        p = self.weapon.owner
        p.motion_lock = max(p.motion_lock, dt * 2)                    # 난무하는 동안은 입력·중력으로 움직이지 않는다
        while self.hits_done < config.ULT_HITS and self.time >= 0.06 + self.hits_done * self.BLINK:
            self._blink()
        if self.hits_done >= config.ULT_HITS and self.time >= 0.06 + config.ULT_HITS * self.BLINK + 0.08:
            sx, sy = p.center
            p.x, p.y = self.home                                       # 제자리로
            game_world.add_object(DashStreak((sx, sy, *p.center), life=0.35, width=14, color=self.color),
                                  game_world.LAYER_EFFECT)
            p.vx = p.vy = 0.0
            self._end()

    def _blink(self):
        p = self.weapon.owner
        i = self.hits_done
        last = i == config.ULT_HITS - 1
        alive = [e for e in self.targets if e.alive]
        if alive:
            e = alive[i % len(alive)]
            side = 1 if self.prev[0] <= e.x else -1                    # 적을 꿰뚫고 반대편에 선다
            for s in (side, -side):
                tx = e.x + s * 80
                if self._free(tx, e.y):
                    p.afterimages.append([p.x, p.y, p.face_dir, config.AFTERIMAGE_LIFE, p._body_frame()])
                    p.x, p.y = tx, e.y
                    break
            cx, cy = p.center
            game_world.add_object(DashStreak((*self.prev, cx, cy), life=0.4, width=18, color=self.color),
                                  game_world.LAYER_EFFECT)
            self.prev = (cx, cy)
            p.start_dash_cut()
        for e in alive:
            ex, ey = e.center
            self._deal(e, 1.0 / config.ULT_HITS, last)
            effects.spawn_slash_marks(ex, ey, random.uniform(-1, 1), random.uniform(-0.6, 0.6), (255, 255, 255), big=True)
        effects.add_trauma(0.3)
        if last:
            if alive:
                cx = sum(e.x for e in alive) / len(alive)
                cy = sum(e.center[1] for e in alive) / len(alive)
            else:
                cx, cy = self.x0, self.y0
            self._finale(cx, cy)
        else:
            assets.play_sound('ult_hit')
        self.hits_done += 1


class PistolUlt(Ultimate):
    """쌍권총 '록온 난사': 보이는 적 모두에 조준 표시가 걸리고, 주인공은 자유롭게 움직이며 다섯 번 일제 사격한다."""
    VOLLEY = 0.11
    LEAD = 0.18                    # 조준 표시가 조여드는 시간

    def _start(self):
        p = self.weapon.owner
        p.ult_pose_left = 0.0
        self.targets = self._in_reach(config.ULT_LOCKON_RANGE)

    def _step(self, dt):
        while self.hits_done < config.ULT_HITS and self.time >= self.LEAD + self.hits_done * self.VOLLEY:
            self._volley()
        if self.hits_done >= config.ULT_HITS and self.time >= self.LEAD + config.ULT_HITS * self.VOLLEY + 0.12:
            self._end()

    def _volley(self):
        p = self.weapon.owner
        last = self.hits_done == config.ULT_HITS - 1
        cx, cy = p.center
        alive = [e for e in self.targets if e.alive]
        for e in alive:
            ex, ey = e.center
            d = math.hypot(ex - cx, ey - cy) or 1.0
            speed = 3000.0
            game_world.add_object(Tracer(cx, cy, (ex - cx) / d * speed, (ey - cy) / d * speed, d / speed, big=last),
                                  game_world.LAYER_EFFECT)
            self._deal(e, 1.0 / config.ULT_HITS, last)
        p.start_punch('shoot_big' if last else 'shoot')
        effects.spawn_bloom(cx + p.face_dir * 40, cy + 10, self.color, life=0.08, strength=0.8)
        effects.add_trauma(0.25)
        if last:
            if alive:
                fx = sum(e.x for e in alive) / len(alive)
                fy = sum(e.center[1] for e in alive) / len(alive)
            else:
                fx, fy = cx, cy
            self._finale(fx, fy)
        else:
            assets.play_sound('shot_big')
        self.hits_done += 1

    def draw(self):
        k = min(1.0, self.time / self.LEAD)                            # 조준 표시: 바깥에서 조여든다
        gap = int(84 - 40 * k) // 2 * 2
        blink = int(self.time * 20) % 2 == 0
        for e in self.targets:
            if not e.alive:
                continue
            x, y = _snap(e.center[0]), _snap(e.center[1])
            for ink in (True, False):                                  # 검은 테두리 -> 밝은 꺾쇠
                c = MARK_INK if ink else ((255, 255, 255) if blink else self.color)
                g = 2 if ink else 0
                for sx in (-1, 1):
                    for sy in (-1, 1):                                 # 네 귀퉁이 꺾쇠
                        bx, by = x + sx * gap, y + sy * gap
                        assets.draw_rect_color(min(bx, bx - sx * 20) - g, by - 3 - g, 20 + g * 2, 6 + g * 2, c)
                        assets.draw_rect_color(bx - 3 - g, min(by, by - sy * 20) - g, 6 + g * 2, 20 + g * 2, c)
            assets.draw_rect_color(x - 5, y - 5, 10, 10, MARK_INK)
            assets.draw_rect_color(x - 3, y - 3, 6, 6, EXEC_COLOR)                 # 가운데 붉은 점
            img = assets.image('light/dot_48.png')
            img.opacify(0.5)
            assets.draw_image_added(img, x, y - img.h // 2, color=self.color, times=1)
            img.opacify(1.0)


class GauntletUlt(Ultimate):
    """건틀릿 '유성 돌진': 조준 쪽으로 길게 돌진하며 닿는 적을 모두 주먹 앞에 끌고 가, 끝에서 한꺼번에 터뜨려 날린다."""

    def _start(self):
        p, w = self.weapon.owner, self.weapon
        p.ult_pose_left = 0.0
        dx, dy = self.dx, self.dy
        if p.on_ground and dy < 0.2:                                   # 땅 위: 수평으로
            dx, dy = float(self.side), 0.0
        self.dx, self.dy = dx, dy
        speed = config.ULT_METEOR_SPEED
        w.charging = False
        w.rush = dict(dx=dx, dy=dy, speed=speed, ult=self)             # 이동은 Gauntlet.rush_velocity, 판정은 여기서
        self.left = config.ULT_METEOR_LENGTH / speed
        self.carried, self.touched = [], set()
        self.prev = None
        self.ghost = 0.0
        p.start_punch('blast')
        if dy != 0.0:
            p.vy = 0.0
        game_world.add_object(RushTrail(w, self.color, 1.6), game_world.LAYER_EFFECT)
        assets.play_sound('dash')
        if p.on_ground:
            effects.spawn('dust-land', p.x, p.y, duration=0.3)

    def _step(self, dt):
        p, w = self.weapon.owner, self.weapon
        if w.rush is None or w.rush.get('ult') is not self:
            self._burst()
            return
        if self.prev is not None and math.hypot(p.x - self.prev[0], p.y - self.prev[1]) < config.ULT_METEOR_SPEED * dt * 0.3:
            self._burst()                                               # 벽에 막혔다: 거기서 터진다
            return
        self.prev = (p.x, p.y)
        p.punch_left = max(p.punch_left, p.punch_total * 0.7)
        self.ghost -= dt
        if self.ghost <= 0:
            self.ghost = 0.02
            p.afterimages.append([p.x, p.y, p.face_dir, config.AFTERIMAGE_LIFE, p._body_frame()])
        cx, cy = p.center
        hx, hy = cx + self.dx * config.GAUNTLET_RUSH_REACH, cy + self.dy * config.GAUNTLET_RUSH_REACH
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            if e.alive and id(e) not in self.touched and Pipe._within(e, hx, hy, config.GAUNTLET_RUSH_HIT * 1.6):
                self.touched.add(id(e))
                self._deal(e, 0.4)
                effects.request_hit_stop(config.HIT_STOP)
                assets.play_sound('impact_gauntlet')
                if e.alive and getattr(e, 'pullable', True):
                    self.carried.append(e)
        for k, e in enumerate(self.carried):                            # 주먹 앞에 얹혀 끌려간다
            if e.alive:
                e.pull_step(p.x + self.dx * (70 + 14 * k) - e.x)
                e.hold(0.3)
        self.left -= dt
        if self.left <= 0:
            self._burst()

    def _burst(self):
        p, w = self.weapon.owner, self.weapon
        if w.rush is not None and w.rush.get('ult') is self:
            w.rush = None
        cx, cy = p.center
        bx, by = cx + self.dx * 60, cy + self.dy * 60
        side = self.side if abs(self.dx) > 0.2 else (1 if p.face_dir >= 0 else -1)
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            if not e.alive or not (e in self.carried or Pipe._within(e, bx, by, config.ULT_METEOR_RADIUS)):
                continue
            self._deal(e, 0.6 if id(e) in self.touched else 1.0, last=True)
            if e.alive and getattr(e, 'pullable', True):                # 터지며 날아간다
                weight = config.ENEMY_WEIGHT.get(getattr(e, 'kind', ''), 1.0)
                away = side if e in self.carried else (1 if e.x >= bx else -1)
                game_world.add_object(Fling(w, e, 0.0, away * config.GAUNTLET_KNOCK / weight), game_world.LAYER_EFFECT)
        effects.ground_slam(bx, p.y, power=1.4, color=self.color)
        effects.spawn('haze-blast', bx, by - 40, duration=0.5)
        self._finale(bx, by)
        p.vx = 0.0
        p.lunge_vx = -side * 220 if p.on_ground else 0.0
        p.punch_left = p.punch_total * 0.5
        self._end()


class ChainUlt(Ultimate):
    """사슬 '사슬 감옥': 둘레 적 모두에 사슬을 걸어 한곳으로 끌어모으고, 마지막에 묶어 둔다(ULT_PRISON_HOLD초).
    묶인 적은 서로 이어져(LinkNet) 하나를 치면 나머지도 피해를 나눠 받는다 - 다음 공격을 위한 판 깔기."""

    def _start(self):
        self.targets = self._in_reach(config.ULT_PRISON_RADIUS, sight=False)
        self.gather_x = self.x0 + self.side * 110

    def _step(self, dt):
        while self.hits_done < config.ULT_HITS and self.time >= 0.12 + self.hits_done * config.ULT_HIT_INTERVAL:
            self._tug()
        if self.hits_done >= config.ULT_HITS and self.time >= 0.12 + config.ULT_HITS * config.ULT_HIT_INTERVAL + 0.2:
            self._end()

    def _tug(self):
        last = self.hits_done == config.ULT_HITS - 1
        left = config.ULT_HITS - self.hits_done
        alive = [e for e in self.targets if e.alive]
        for k, e in enumerate(alive):
            if getattr(e, 'pullable', True):                            # 보스는 끌려오지 않는다
                stop = self.gather_x + ((k % 3) - 1) * 26
                e.pull_step((stop - e.x) / max(1, left))
                e.hold(0.3)
            self._deal(e, 1.0 / config.ULT_HITS, last)
        effects.add_trauma(0.3)
        if last:
            held = [e for e in alive if e.alive and getattr(e, 'pullable', True)]
            for e in held:
                e.hold(config.ULT_PRISON_HOLD)
            if len(held) >= 2:
                net = LinkNet(held)
                net.life = config.ULT_PRISON_HOLD
                game_world.add_object(net, game_world.LAYER_EFFECT)
            if held:
                game_world.add_object(PrisonBind(held, self.color, config.ULT_PRISON_HOLD), game_world.LAYER_EFFECT)
            self._finale(self.gather_x, self.y0)
        else:
            assets.play_sound('ult_hit')
        self.hits_done += 1

    def draw(self):
        p = self.weapon.owner
        hx, hy = p.center
        for e in self.targets:
            if e.alive:
                draw_chain([(hx, hy), e.center], self.color, age=self.time, flow=-1, shake=2.0, light=False)


class PrisonBind:
    """사슬 감옥에 묶인 적: 몸을 가로지르는 사슬 두 줄이 묶인 시간 동안 남는다."""

    def __init__(self, enemies, color, life):
        self.enemies, self.color, self.life = list(enemies), color, life
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.life or not any(e.alive for e in self.enemies):
            game_world.remove_object(self)

    def draw(self):
        for e in self.enemies:
            if not e.alive:
                continue
            left, bottom, right, top = e.rect()
            mid = (bottom + top) / 2
            draw_chain([(left - 10, mid + 14), (right + 10, mid - 6)], self.color, age=self.time, link=10, light=False)
            draw_chain([(left - 10, mid - 12), (right + 10, mid + 10)], self.color, age=self.time, link=10, light=False)


ULTIMATES = {'pipe': PipeUlt, 'pistol': PistolUlt, 'gauntlet': GauntletUlt, 'chain': ChainUlt}


WEAPONS = {'pipe': Pipe, 'pistol': Pistols, 'gauntlet': Gauntlet, 'chain': Chain}
