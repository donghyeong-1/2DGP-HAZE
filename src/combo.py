"""두 무기 조합 (v8 계획 1절, 2026-11-24): 각인과 격발.

한 무기가 묻히고 다른 무기가 터뜨린다. 무기 둘을 들고 있을 때만 일한다(섞을 것이 있어야 한다).
- 무기로 맞힌 적에게 그 무기의 **각인**이 IMPRINT_TIME 동안 남는다 (적마다 하나, 발밑에 그 무기 색 빛).
- **다른 무기**로 각인된 적을 치면 **격발**: 추가 피해 + 터뜨린 무기에 따른 효과. 각인은 사라지고 IMPRINT_LOCK 동안 다시 묻지 않는다.
- 격발하면 게이지 +DETONATE_GAUGE, 교체기 쿨다운 -DETONATE_SWAP_REFUND (바꿔 가며 싸울수록 빨라진다).
대시 표식(붉은 X, 3개 처형)과는 따로 간다: 표식은 대시 공격, 각인은 무기 섞어 쓰기.
Pipe._hit이 on_hit을 부른다(무기 넷 모두 그 함수를 거친다). 궁극기의 피해는 거치지 않으므로 각인·격발과 무관하다.
"""
import math

import assets
import config
import effects
import game_world

COLORS = {'pipe': (40, 190, 255), 'pistol': (40, 235, 180), 'gauntlet': (255, 130, 40), 'chain': (160, 90, 255)}   # 무기의 색 (각인 빛)
NAMES = {'pipe': '연쇄 타격', 'pistol': '폭발탄', 'gauntlet': '분쇄', 'chain': '일망타진'}                        # 터뜨리는 무기별 격발
_busy = False          # 격발이 주는 피해가 다시 각인·격발을 부르지 않게


def imprint_of(enemy):
    """그 적에게 남아 있는 각인의 무기 이름. 없으면 None."""
    return getattr(enemy, 'imprint', None) if getattr(enemy, 'imprint_left', 0.0) > 0 else None


def detonate_damage(player):
    """격발의 기본 추가 피해 (게이지 구간·공격 보너스·변이를 따른다)."""
    import mutations
    return config.DETONATE_DAMAGE * player.gauge.zone_multipliers()['attack'] * player.attack_bonus * mutations.damage_mult(player)


def active(player):
    return sum(1 for w in player.weapons if w is not None) >= 2


def on_hit(weapon, enemy, killed):
    """무기가 적을 맞혔다: 다른 무기의 각인이 있으면 격발, 없으면 이 무기의 각인을 남긴다."""
    p = weapon.owner
    if _busy or not active(p):
        return
    wid = weapon.weapon_id
    if _spread_window(p, wid):                            # O5 강화 교체기: 둘레에 각인이 묻는다
        _spread(enemy, wid)
    mark = imprint_of(enemy)
    if mark is not None and mark != wid:
        _detonate(weapon, enemy)
        return
    if killed or not enemy.alive or getattr(enemy, 'imprint_lock', 0.0) > 0:
        return
    imprint(enemy, wid)


def imprint(enemy, wid):
    enemy.imprint = wid
    enemy.imprint_left = config.IMPRINT_TIME
    _tag(enemy).pop = 0.14


def _tag(enemy):
    tag = getattr(enemy, 'imprint_tag', None)
    if tag is None or tag.gone:
        tag = enemy.imprint_tag = ImprintTag(enemy)
        game_world.add_object(tag, game_world.LAYER_EFFECT)
    return tag


def launch(enemy, speed):
    """적을 띄운다 (v8 4-1). 떠 있는 동안 움직이지 못하고, 맞으면 조금씩 다시 뜬다(juggle). 보스는 뜨지 않는다."""
    if not enemy.alive or not getattr(enemy, 'pullable', True):
        return False
    enemy.vy = max(enemy.vy, speed)
    enemy.on_ground = False
    enemy.launched = True
    enemy.air_hits = 0
    enemy.blown = enemy.wall_bounced = False
    enemy.hold(config.JUGGLE_HOLD)
    return True


def juggle(enemy):
    """떠 있는 적이 맞았다: JUGGLE_MAX번까지 조금 다시 뜬다 (Pipe._hit이 부른다)."""
    if (not enemy.alive or not getattr(enemy, 'launched', False) or enemy.on_ground
            or getattr(enemy, 'air_hits', 0) >= config.JUGGLE_MAX):
        return False
    enemy.air_hits += 1
    enemy.vy = max(enemy.vy, config.JUGGLE_POP)
    flying = enemy.vx
    enemy.hold(config.JUGGLE_HOLD)
    if getattr(enemy, 'blown', False):                 # 큰 공격으로 날아가는 중이면 그 속도는 그대로 (hold가 멈춰 세운다)
        enemy.vx = flying
    return True


def _enemies():
    return [e for e in list(game_world.world[game_world.LAYER_ENEMY]) if e.alive]


def _strike(player, enemy, damage, color, knock=1.0):
    """격발이 주는 피해 한 번 (각인·격발을 다시 부르지 않는다). 죽였으면 처치 게이지와 연출까지."""
    global _busy
    import drama
    _busy = True
    try:
        with drama.hit_style(big=True, color=color):
            killed = enemy.take_damage(damage, from_x=player.x, knock=knock)
    finally:
        _busy = False
    if killed:
        ex, ey = enemy.center
        player.gauge.add(player.kill_gain(False), 'kill')
        effects.spawn_kill(ex, ey, ex - player.x, ey - player.center[1], color)
    return killed


def _detonate(weapon, enemy, echo=False):
    """격발. echo=True는 합성 '각인 폭풍'이 번진 격발: 피해가 DUO_STORM[1]배이고 게이지·쿨다운 환급·다시 번지기는 없다."""
    import mutations
    p = weapon.owner
    wid = weapon.weapon_id
    color = COLORS[wid]
    ex, ey = enemy.center
    enemy.imprint, enemy.imprint_left = None, 0.0
    enemy.imprint_lock = config.IMPRINT_LOCK
    _tag(enemy)                                           # 잠금 시간을 세어 줄 것이 있어야 한다
    damage = detonate_damage(p) * (mutations.DUO_STORM[1] if echo else 1.0)
    if not echo:
        p.gauge.add(config.DETONATE_GAUGE, 'hit')
        p.swap_cool = max(0.0, getattr(p, 'swap_cool', 0.0) - config.DETONATE_SWAP_REFUND)
        assets.play_sound('ult_hit')
    effects.add_trauma(config.SHAKE_HIT * (1.0 if echo else 1.6))
    if echo:                                              # 번진 격발: 짧게, 아래쪽에 (가까운 원래 격발 글자와 겹치지 않게)
        effects.float_text(ex, ey + 90, '번짐', color, life=0.6)
    else:
        effects.float_text(ex, ey + 150, '격발 · ' + NAMES[wid], color, big=True, life=0.7)
    effects.spawn('haze-blast', ex, ey, duration=0.5)
    effects.spawn_flare(ex, ey, color)
    _effect(p, wid, enemy, damage, color)
    if not echo and mutations.has(p, 'duo_imprint_storm'):   # v8 합성 '각인 폭풍': 가장 가까운 다른 적에게 한 번 더
        near = _nearest(enemy, mutations.DUO_STORM[0])
        if near is not None:
            game_world.add_object(StormArc(enemy.center, near, color), game_world.LAYER_EFFECT)
            _detonate(weapon, near, echo=True)


def _nearest(enemy, radius):
    ex, ey = enemy.center
    best, best_d = None, radius
    for o in _enemies():
        if o is enemy:
            continue
        ox, oy = o.center
        d = math.hypot(ox - ex, oy - ey)
        if d <= best_d:
            best, best_d = o, d
    return best


def _effect(p, wid, enemy, damage, color):
    """터뜨린 무기에 따른 격발 효과 (피해 damage)."""
    ex, ey = enemy.center
    if wid == 'gauntlet':                                 # 분쇄: 피해 큼 + 띄움
        _strike(p, enemy, damage * config.DETONATE_CRUSH, color, knock=config.KNOCK_BIG)
        launch(enemy, config.DETONATE_LAUNCH)
        return
    _strike(p, enemy, damage, color)
    if wid == 'pipe':                                     # 번지는 베기: 다른 각인 적 모두에게 베기가 튄다 (그 각인은 남는다)
        for o in _enemies():
            if o is not enemy and imprint_of(o) is not None:
                ox, oy = o.center
                effects.spawn_slash_marks(ox, oy, ox - ex, oy - ey or 0.1, color, big=True, count=2)
                effects.spawn_flare(ox, oy, color, small=True)
                _strike(p, o, damage, color)
    elif wid == 'pistol':                                 # 폭발탄: 둘레의 적에게 폭발 피해, 각인을 옮긴다
        effects.spawn_ring(ex, ey, color, radius_max=config.DETONATE_BURST_RADIUS, life=0.24)
        for o in _enemies():
            ox, oy = o.center
            if o is not enemy and math.hypot(ox - ex, oy - ey) <= config.DETONATE_BURST_RADIUS:
                if not _strike(p, o, damage * config.DETONATE_BURST_RATIO, color) and getattr(o, 'imprint_lock', 0.0) <= 0:
                    imprint(o, 'pistol')
    elif wid == 'chain':                                  # 일망타진: 각인된 적 모두를 터뜨린 적 쪽으로 끌어모은다
        pulled = [o for o in _enemies() if o is not enemy and imprint_of(o) is not None and getattr(o, 'pullable', True)]
        if pulled:
            game_world.add_object(Gather(enemy, pulled, color), game_world.LAYER_EFFECT)


class StormArc:
    """각인 폭풍: 격발한 적에서 번진 적으로 짧게 이어지는 빛 (헤이즈 빛 점을 줄지어 더한다)."""
    LIFE = 0.22

    def __init__(self, start, target, color):
        self.x0, self.y0 = start
        self.target, self.color = target, color
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        x1, y1 = self.target.center
        k = max(0.0, 1.0 - self.time / self.LIFE)
        img = assets.image('light/dot_48.png')
        img.opacify(0.8 * k)
        n = max(2, int(math.hypot(x1 - self.x0, y1 - self.y0) / 26))
        for i in range(n + 1):
            t = i / n
            x = int(self.x0 + (x1 - self.x0) * t) // 2 * 2
            y = int(self.y0 + (y1 - self.y0) * t + math.sin(t * math.pi) * 30) // 2 * 2    # 살짝 휘어 건너간다
            assets.draw_image_added(img, x, y - img.h // 2, color=self.color, times=1)
        img.opacify(1.0)


# =====================================================================================================
# 교체기 (v8 1-2): 무기를 바꾸는 순간 들어오는 무기의 기술이 나간다. 조준 방향을 따르고, 직전 공격의 후딜을 끊는다.
# 맞히는 것은 Pipe._hit을 거치므로, 나가는 무기가 남긴 각인을 바로 격발한다 (묻히고 -> 바꾸며 터뜨린다).
# =====================================================================================================
STRIKE_NAMES = {'pipe': '기습 강타', 'pistol': '물러나 쏘기', 'gauntlet': '올려치기', 'chain': '낚아채기'}


_boost = [1.0]          # 지금 나가는 교체기의 강화 배율 (교체기 함수들이 피해·범위에 곱한다)


def swap_strike(player):
    """방금 든 무기의 교체기. 나갔으면 True (쿨 중·무기 하나·기절 중이면 False).
    O5 강화 교체기: 강화 1~2단계가 준비돼 있으면 피해·범위 x SWAP_ENHANCE_MULT, 쌓인 단계를 모두 쓴다,
    SWAP_ENHANCE_WINDOW 동안 그 무기의 타격이 맞은 적 둘레에 각인을 퍼뜨린다. 3단계(궁극기 준비)면 강화를 쓰지 않는다."""
    p = player
    if p.state in ('DEAD', 'HIT') or p.stunned or p.swap_cool > 0 or not active(p):
        return False
    w = p.weapon
    p.swap_cool = p.swap_cool_max = swap_cooldown(p)
    p.swing_left = 0.0                                    # 직전 공격의 남은 자세를 끊는다
    w.cooldown = min(getattr(w, 'cooldown', 0.0), config.SWAP_FOLLOW)
    cx, cy = p.center
    g = p.gauge
    level = g.enhance_level if g.enhanced and g.enhance_level in config.SWAP_ENHANCE_MULT else 0
    name, color = STRIKE_NAMES[w.weapon_id], COLORS[w.weapon_id]
    p.swap_boost = w.weapon_id if level else None
    if level:
        name, color = '강화 ' + name, config.ENHANCE_LEVEL_COLOR[level]
        g.consume_enhance()                               # 강화 공격과 같다: 쌓인 단계를 모두 쓴다
        effects.spawn_ring(cx, cy, color, radius_max=150 + 60 * level)
        effects.spawn_bloom(cx, cy, color, big=True, life=0.2, strength=0.8)
    effects.float_text(cx, cy - 70, name, color, life=0.5 + 0.2 * bool(level))     # 발밑 쪽에 (피해 숫자·격발 글자와 겹치지 않게)
    _boost[0] = config.SWAP_ENHANCE_MULT.get(level, 1.0)
    try:
        _STRIKES[w.weapon_id](p, w)
    finally:
        _boost[0] = 1.0
    return True


def _spread_window(p, wid):
    """강화 교체기 뒤 SWAP_ENHANCE_WINDOW 안의 그 무기 타격인가 (교체기 쿨다운이 흐른 만큼으로 잰다)."""
    return (getattr(p, 'swap_boost', None) == wid and
            getattr(p, 'swap_cool_max', 0.0) - getattr(p, 'swap_cool', 0.0) <= config.SWAP_ENHANCE_WINDOW)


def _spread(enemy, wid):
    """맞은 적 둘레 SWAP_ENHANCE_SPREAD 안의 적에게 들어오는 무기의 각인을 묻힌다."""
    ex, ey = enemy.center
    for o in list(game_world.world[game_world.LAYER_ENEMY]):
        if o is enemy or not getattr(o, 'alive', False) or getattr(o, 'imprint_lock', 0.0) > 0:
            continue
        ox, oy = o.center
        if math.hypot(ox - ex, oy - ey) <= config.SWAP_ENHANCE_SPREAD:
            imprint(o, wid)


def swap_cooldown(p):
    """이번 교체기의 쿨다운. 합성 '교체 연무'면 짧고 대신 게이지를 쓴다 (게이지가 모자라면 보통 쿨다운, 게이지는 그대로)."""
    import mutations
    cool, cost, floor = mutations.DUO_MIST
    if mutations.has(p, 'duo_swap_mist') and p.gauge.value >= floor:
        p.gauge.add(-cost, 'swap')
        cx, cy = p.center
        effects.spawn_bloom(cx, cy, mutations.FAMILIES['duo']['color'], life=0.16, strength=0.5)
        return cool
    return config.SWAP_COOLDOWN


def _strike_pipe(p, w):
    """발도 베기: 한 발 내디디며 넓은 가로 베기."""
    ax, ay = p.aim_vector()
    cx, cy = p.center
    fx = w._fx(False)
    p.set_swing_style(1, ax)
    if p.on_ground:
        p.lunge_vx = (1 if ax >= 0 else -1) * config.SWAP_PIPE_LUNGE
    variant, flip = effects.slash_variant(ax, ay)
    effects.spawn(fx['slash'], cx, cy, flip=flip, duration=0.24, variant=variant)
    w._swing_sound('swing_3', False)
    effects.add_trauma(config.SHAKE_HIT)
    damage = w._damage(config.SWAP_PIPE_MULT) * _boost[0]
    for e in w._targets(lambda e: w._in_arc(e, cx, cy, ax, ay, scale=config.SWAP_PIPE_REACH * _boost[0])):
        w._hit(e, damage, config.GAIN_HIT, fx, big=True)


def _strike_pistol(p, w):
    """물러나 쏘기: 조준 반대쪽으로 물러나며 3발."""
    import weapon as wp
    ax, ay = p.aim_vector()
    p.lunge_vx = (-1 if ax >= 0 else 1) * config.SWAP_PISTOL_HOP
    mx, my = p.pistol_muzzle()
    base = math.atan2(ay, ax)
    damage = w._damage(config.SWAP_PISTOL_MULT) * _boost[0]
    for k in (-1, 0, 1):
        a = base + k * 0.06
        game_world.add_object(wp.Bullet(w, mx, my + k * 3, math.cos(a), math.sin(a), damage, False, w._fx(False), k or 1),
                              game_world.LAYER_EFFECT)
    game_world.add_object(wp.MuzzleFlash(mx, my, ax, ay), game_world.LAYER_EFFECT)
    assets.play_sound('shot')


def _strike_gauntlet(p, w):
    """올려치기: 앞의 적을 띄운다."""
    ax, ay = p.aim_vector()
    cx, cy = p.center
    fx = w._fx(False)
    p.start_punch('blast')
    w._swing_sound('swing_3', False)
    effects.spawn('surge', cx + (1 if ax >= 0 else -1) * 70, p.y, duration=0.36)
    damage = w._damage(config.SWAP_GAUNTLET_MULT) * _boost[0]
    for e in w._targets(lambda e: w._in_arc(e, cx, cy, ax, ay, scale=config.SWAP_GAUNTLET_REACH * _boost[0])):
        w._hit(e, damage, config.GAIN_HIT, fx, big=True, extra=False)
        launch(e, config.SWAP_LAUNCH)


def _strike_chain(p, w):
    """낚아채기: 가장 가까운 적 하나를 바로 끌어온다."""
    cx, cy = p.center

    def reach(e):
        ex, ey = e.center
        return getattr(e, 'pullable', True) and math.hypot(ex - cx, ey - cy) <= config.SWAP_CHAIN_RANGE * _boost[0]
    found = w._targets(reach)
    p.start_punch('throw')
    assets.play_sound('pickup')
    if not found:
        return
    target = min(found, key=lambda e: math.hypot(e.center[0] - cx, e.center[1] - cy))
    game_world.add_object(Yank(p, w, target), game_world.LAYER_EFFECT)


_STRIKES = {'pipe': _strike_pipe, 'pistol': _strike_pistol, 'gauntlet': _strike_gauntlet, 'chain': _strike_chain}


class Yank:
    """사슬 교체기: 적 하나가 주인공 앞으로 끌려와(SWAP_CHAIN_TIME) 맞는다."""

    def __init__(self, player, weapon, enemy):
        self.p, self.w, self.e = player, weapon, enemy
        self.time = 0.0
        self.mult = _boost[0]                             # O5 강화 교체기 배율 (끌려온 뒤에 맞는다)
        enemy.hold(config.SWAP_CHAIN_TIME + 0.45)

    def update(self, dt):
        p, e = self.p, self.e
        self.time += dt
        if not e.alive:
            game_world.remove_object(self)
            return
        left = max(dt, config.SWAP_CHAIN_TIME - self.time + dt)
        stop = p.x + (1 if e.x >= p.x else -1) * 84
        e.pull_step((stop - e.x) * min(1.0, dt / left))
        if self.time >= config.SWAP_CHAIN_TIME:
            self.w._hit(e, self.w._damage(config.SWAP_CHAIN_MULT) * self.mult, config.GAIN_HIT, self.w._fx(False), extra=False)
            game_world.remove_object(self)

    def draw(self):
        (x0, y0), (x1, y1) = self.p.center, self.e.center
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 12))
        for i in range(n + 1):                              # 사슬 고리: 4px 칸을 12px마다
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            assets.draw_rect_color(int(x) // 2 * 2 - 2, int(y) // 2 * 2 - 2, 4, 4, COLORS['chain'] if i % 2 else (235, 225, 255))


class Gather:
    """사슬 격발: 각인된 적들이 한 점으로 끌려온다 (GATHER_TIME 동안, 벽에 막히면 거기까지)."""
    TIME = 0.28

    def __init__(self, anchor, enemies, color):
        self.x = anchor.x
        self.enemies, self.color = enemies, color
        self.time = 0.0
        for e in enemies:
            e.hold(self.TIME + 0.25)

    def update(self, dt):
        self.time += dt
        left = max(dt, self.TIME - self.time + dt)
        for k, e in enumerate(self.enemies):
            if not e.alive:
                continue
            stop = self.x + (1 if e.x >= self.x else -1) * (44 + 22 * (k % 3))   # 한 점에 겹치지 않게 조금씩 벌려 세운다
            e.pull_step((stop - e.x) * min(1.0, dt / left))
        if self.time >= self.TIME:
            game_world.remove_object(self)

    def draw(self):
        k = max(0.0, 1.0 - self.time / self.TIME)
        for e in self.enemies:                              # 끌려오는 적과 모이는 자리를 잇는 빛 (2px 선)
            if e.alive:
                ex, ey = e.center
                x0, x1 = sorted((int(self.x), int(ex)))
                assets.draw_rect_color(x0 // 2 * 2, int(ey) // 2 * 2, max(2, (x1 - x0) // 2 * 2), 2, self.color, 0.7 * k)


class ImprintTag:
    """적 발밑의 각인 빛 (무기 색). 시간을 세고, 각인도 잠금도 끝났거나 적이 죽으면 사라진다."""

    def __init__(self, enemy):
        self.enemy = enemy
        self.pop = 0.0
        self.time = 0.0
        self.gone = False

    def update(self, dt):
        e = self.enemy
        self.time += dt
        self.pop = max(0.0, self.pop - dt)
        e.imprint_left = max(0.0, getattr(e, 'imprint_left', 0.0) - dt)
        e.imprint_lock = max(0.0, getattr(e, 'imprint_lock', 0.0) - dt)
        if e.imprint_left <= 0:
            e.imprint = None
        if not e.alive or (e.imprint_left <= 0 and e.imprint_lock <= 0):
            self.gone = True
            game_world.remove_object(self)

    def draw(self):
        e = self.enemy
        wid = imprint_of(e)
        if wid is None:
            return
        color = COLORS[wid]
        img = assets.image('light/dot_48.png')
        beat = 0.5 + 0.5 * math.sin(self.time * 9.0)
        fading = min(1.0, e.imprint_left / 0.8)                 # 사라지기 직전에는 옅어진다
        img.opacify((0.55 + 0.25 * beat + (0.3 if self.pop > 0 else 0.0)) * fading)
        x, y = int(e.x) // 2 * 2, int(e.y) // 2 * 2
        for dx in (-22, 0, 22):                                 # 발밑에 가로로 깔린 빛
            assets.draw_image_added(img, x + dx, y - img.h // 2 + 6, color=color, times=1)
        img.opacify(1.0)
        left, bottom, right, top = e.rect()
        w = 6 if self.pop > 0 else 4                            # 머리 위의 작은 마름모 (어느 무기의 각인인지 색으로)
        cx, cy = int((left + right) / 2) // 2 * 2, int(top + 24) // 2 * 2
        assets.draw_rect_color(cx - w - 2, cy - 2, 2 * w + 4, 4, (10, 12, 20))
        assets.draw_rect_color(cx - 2, cy - w - 2, 4, 2 * w + 4, (10, 12, 20))
        assets.draw_rect_color(cx - w, cy - 1, 2 * w, 2, color)
        assets.draw_rect_color(cx - 1, cy - w, 2, 2 * w, color)
