"""무기 형태 (v8 계획 2절, 2026-11-25): 형태 카드를 얻으면 그 무기의 **기본 공격 자체**가 달라진다.

증강(수치·추가 효과)과 달리 누르는 방식과 쓰임이 바뀐다. 무기마다 새 형태 하나, 판 동안 유지된다(무기를 다시 주워도).
대시 공격·공중 공격·E 강화·궁극기는 그대로다: 땅에서 치는 기본 공격만 바뀐다.

| 무기 | 기본 | 새 형태 |
| 철파이프 | 빠른 3연타 | 중량 타격: 누르고 있으면 힘을 모아 크게 한 번(멀리 닿고 띄운다), 짧게 누르면 느리고 센 베기 |
| 쌍권총 | 좌우 연사 | 산탄: 가까이 5발 부채꼴, 쏠 때마다 반동 (공중에서 아래로 쏘면 뜬다) |
| 건틀릿 | 충전 돌진 강타 | 연타: 빠른 잽(게이지 소모 없음), 세 번째 잽 뒤 누르고 있으면 돌진 강타 |
| 사슬 | 적을 끌어옴 | 갈고리 이동: 적에게 걸면 내가 날아가 걷어찬다 (지나가며 스친 적도 맞는다) |

무기의 try_attack이 active()를 보고 여기의 *_attack을 부르고, Pipe.update가 update()를 불러 누르고 있는 동안의 일을 처리한다.
진행 중인 동작은 weapon.form_state(없으면 None)에 둔다.
"""
import math

import assets
import config
import effects
import game_world

FORMS = {
    'pipe': dict(name='중량 타격', desc='길게 누르면 힘을 모아 크게 칩니다. 짧게 누르면 느리고 세게 벱니다'),
    'pistol': dict(name='산탄', desc='가까이 5발을 부채꼴로 쏩니다. 쏠 때마다 반동으로 밀립니다'),
    'gauntlet': dict(name='연타', desc='빠른 잽을 연달아 칩니다. 세 번째 잽 뒤에도 누르고 있으면 돌진합니다'),
    'chain': dict(name='갈고리 이동', desc='적에게 걸면 끌어오는 대신 내가 날아가 걷어찹니다'),
}
COLOR = (255, 214, 120)            # 형태 카드·안내의 색 (금색)
# 형태와 잘 맞는 증강 갈래: 형태를 얻으면 이 갈래의 카드가 MATCH_WEIGHT배 자주 나온다 (판 초반에 싸움 방식이 정해진다)
MATCH = {'pipe': ('pipe_air', 'pipe_dash'), 'pistol': ('pistol_dash',), 'gauntlet': ('gauntlet_counter',),
         'chain': ('chain_pierce', 'chain_link')}
MATCH_WEIGHT = 2.0
SKIP_SHARDS = 8                    # 형태 카드를 넘기면 받는 조각
CARD = 'form:'                     # 카드 창에서 형태 카드의 id 머리말 ('form:pipe', 'form:skip')


def active(weapon):
    return weapon.weapon_id in getattr(weapon.owner, 'forms', ())


def give(player, wid):
    """그 무기의 새 형태를 얻는다 (판 동안 유지). 이미 있거나 없는 무기면 False."""
    if wid not in FORMS or wid in player.forms:
        return False
    player.forms.add(wid)
    return True


def offer(player):
    """지금 형태 카드로 내놓을 수 있는 무기: 들고 있는 무기 가운데 아직 형태가 없는 것."""
    return [w.weapon_id for w in player.weapons if w is not None and w.weapon_id not in player.forms]


def cards(player):
    """형태 카드 창에 내놓을 것: 들고 있는 무기의 새 형태들 + 넘기기. 내놓을 형태가 없으면 빈 목록."""
    wids = offer(player)
    return [CARD + w for w in wids] + [CARD + 'skip'] if wids else []


def take_card(player, card):
    """형태 카드를 골랐다. 넘기기면 조각을 조금 준다. 화면에 띄울 (이름, 색)을 돌려준다."""
    wid = card[len(CARD):]
    if wid == 'skip':
        player.shards += SKIP_SHARDS
        return f'조각 +{SKIP_SHARDS}', (130, 235, 225)
    give(player, wid)
    return FORMS[wid]['name'], COLOR


def weight_mult(player, family):
    """증강 카드 무게에 곱하는 값: 얻은 형태와 잘 맞는 갈래면 MATCH_WEIGHT."""
    return MATCH_WEIGHT if any(family in MATCH[w] for w in getattr(player, 'forms', ())) else 1.0


def busy(weapon):
    """형태의 동작이 진행 중인가 (모으는 중·잽 뒤 이어치기 대기·날아가는 중). 그동안은 새 공격을 받지 않는다."""
    return getattr(weapon, 'form_state', None) is not None


def update(weapon, dt):
    st = getattr(weapon, 'form_state', None)
    if st is not None:
        _TICKS[st['kind']](weapon, st, dt)


def cancel(weapon):
    weapon.form_state = None
    weapon.heavy = False


def _launch(e, speed):
    if e.alive and getattr(e, 'pullable', True):
        e.vy = max(e.vy, speed)
        e.hold(config.DETONATE_LAUNCH_HOLD)


# ----- 철파이프: 중량 타격 -----
def pipe_attack(w):
    w.form_state = dict(kind='heavy', t=0.0, ping=False)
    w.heavy = True
    w.last_kind, w.last_enhanced = 'pipe', False
    assets.play_sound('enhance')
    return True


def _tick_heavy(w, st, dt):
    p = w.owner
    if p.state in ('HIT', 'DEAD') or p.stunned:
        cancel(w)
        return
    st['t'] += dt
    if st['t'] >= config.FORM_HEAVY_CHARGE and not st['ping']:        # 다 모였다: 한 번 번쩍
        st['ping'] = True
        effects.spawn_bloom(*p.center, (255, 255, 255), big=True, life=0.18, strength=0.8)
        assets.play_sound('pickup')
    if p.attack_held and st['t'] < config.FORM_HEAVY_CHARGE + config.FORM_HEAVY_HOLD:
        if int(st['t'] * 20) != int((st['t'] - dt) * 20):             # 모으는 동안 발밑에서 기운이 솟는다
            effects.spawn_bloom(p.x, p.y + 30, effects.zone_glow(p), life=0.14, strength=0.35 + 0.4 * min(1.0, st['t'] / config.FORM_HEAVY_CHARGE))
        return
    ratio = min(1.0, st['t'] / config.FORM_HEAVY_CHARGE)
    cancel(w)
    if ratio >= config.FORM_HEAVY_MIN:
        _heavy_blow(w, ratio)
    else:
        _heavy_light(w)


def _heavy_blow(w, ratio):
    """모아서 크게 한 번: 멀리 닿고(FORM_HEAVY_REACH), 크게 밀고 띄운다."""
    p = w.owner
    ax, ay = p.aim_vector()
    cx, cy = p.center
    fx = w._fx(False)
    p.set_swing_style(3, ax)
    variant, flip = effects.slash_variant(ax, ay)
    effects.spawn(config.FINISHER_SLASH, cx, cy, flip=flip, duration=0.26, variant=variant)
    w._swing_sound('swing_3', False)
    effects.add_trauma(config.SHAKE_FINISHER)
    damage = w._damage(config.FORM_HEAVY_MULT * (0.75 + 0.25 * ratio))
    for e in w._targets(lambda e: w._in_arc(e, cx, cy, ax, ay, scale=config.FORM_HEAVY_REACH)):
        w._hit(e, damage, config.PIPE_FINISHER_GAIN, fx, big=True, shake=1.8, stop=1.8)
        _launch(e, config.FORM_HEAVY_LAUNCH)
    w.cooldown = w.cooldown_max = config.FORM_HEAVY_COOLDOWN


def _heavy_light(w):
    """짧게 눌렀다: 느리고 센 베기 (두 번이 번갈아 나간다)."""
    p = w.owner
    ax, ay = p.aim_vector()
    cx, cy = p.center
    fx = w._fx(False)
    w.combo = w.combo % 2 + 1
    p.set_swing_style(w.combo, ax)
    variant, flip = effects.slash_variant(ax, ay)
    effects.spawn(fx['slash'], cx, cy, flip=flip, duration=0.24, variant=variant)
    w._swing_sound(f'swing_{w.combo}', False)
    damage = w._damage(config.FORM_HEAVY_LIGHT)
    for e in w._targets(lambda e: w._in_arc(e, cx, cy, ax, ay, scale=1.1)):
        w._hit(e, damage, config.GAIN_HIT, fx, big=w.combo == 2)
    w.cooldown = w.cooldown_max = config.PIPE_COOLDOWN[0] * config.FORM_HEAVY_SLOW
    w.combo_left = w.cooldown + config.PIPE_COMBO_WINDOW


# ----- 쌍권총: 산탄 -----
def pistol_attack(w):
    import weapon as wp
    p = w.owner
    ax, ay = p.aim_vector()
    mx, my = p.pistol_muzzle()
    base = math.atan2(ay, ax)
    n = config.FORM_SHOTGUN_PELLETS
    damage = w._damage(config.FORM_SHOTGUN_MULT)
    for i in range(n):
        a = base + (i - (n - 1) / 2) * config.FORM_SHOTGUN_SPREAD
        game_world.add_object(wp.Bullet(w, mx, my, math.cos(a), math.sin(a), damage, False, w._fx(False), 1 if i % 2 else -1,
                                        reach=config.FORM_SHOTGUN_REACH), game_world.LAYER_EFFECT)
    game_world.add_object(wp.MuzzleFlash(mx, my, ax, ay), game_world.LAYER_EFFECT)
    assets.play_sound('shot')
    effects.add_trauma(config.SHAKE_HIT * 1.2)
    if p.on_ground:                                                   # 반동: 쏜 반대쪽으로 밀린다
        p.lunge_vx = (-1 if ax >= 0 else 1) * config.FORM_SHOTGUN_RECOIL
    elif ay < -0.3:                                                   # 공중에서 아래로 쏘면 뜬다
        p.vy = max(p.vy, config.FORM_SHOTGUN_HOP)
    w.side = -w.side
    w.last_kind, w.last_enhanced = 'pistol', False
    w.cooldown = w.cooldown_max = config.FORM_SHOTGUN_COOLDOWN
    return True


# ----- 건틀릿: 연타 -----
def gauntlet_attack(w):
    p = w.owner
    ax, ay = p.aim_vector()
    cx, cy = p.center
    fx = w._fx(False)
    w.jab = (getattr(w, 'jab', 0) % 3 + 1) if getattr(w, 'jab_left', 0.0) > 0 else 1
    w.jab_left = config.FORM_JAB_WINDOW
    third = w.jab == 3
    p.start_punch('blast')
    if p.on_ground:
        p.lunge_vx = (1 if ax >= 0 else -1) * config.FORM_JAB_STEP
    w._swing_sound('swing_3' if third else f'swing_{w.jab}', False)
    damage = w._damage(config.FORM_JAB_MULT * (config.FORM_JAB_THIRD if third else 1.0))
    for e in w._targets(lambda e: w._in_arc(e, cx, cy, ax, ay, scale=config.FORM_JAB_REACH)):
        w._hit(e, damage, config.GAIN_HIT, fx, big=third, extra=False)
    w.last_kind, w.last_enhanced = 'gauntlet', False
    w.cooldown = w.cooldown_max = config.FORM_JAB_COOLDOWN
    if third:                                                         # 세 번째 잽: 누르고 있으면 돌진 강타로 이어진다
        w.form_state = dict(kind='jab_end', t=config.FORM_JAB_FOLLOW)
        w.jab_left = 0.0
    return True


def _tick_jab_end(w, st, dt):
    p = w.owner
    st['t'] -= dt
    if st['t'] > 0:
        return
    cancel(w)
    if not p.attack_held or p.state in ('HIT', 'DEAD') or p.stunned:
        return
    p.gauge.add(-min(config.GAUNTLET_QUICK_COST, max(0.0, p.gauge.value - config.GAUNTLET_FLOOR)), 'gauntlet')
    w._start_rush(config.FORM_JAB_RUSH_RATIO, False, w._size(False), config.FORM_JAB_RUSH_DIST)


def tick_combo(w, dt):
    """잽 콤보 창 (Pipe.update가 늘 부른다)."""
    if getattr(w, 'jab_left', 0.0) > 0:
        w.jab_left = max(0.0, w.jab_left - dt)


# ----- 사슬: 갈고리 이동 -----
def chain_attack(w):
    p = w.owner
    ax, ay = p.aim_vector()
    cx, cy = p.center

    def in_cone(e):
        ex, ey = e.center
        d = math.hypot(ex - cx, ey - cy)
        return 40 < d <= config.FORM_ZIP_REACH and ((ex - cx) * ax + (ey - cy) * ay) / d >= config.FORM_ZIP_CONE
    found = w._targets(in_cone)
    p.start_punch('throw')
    import drama
    assets.play_sound(drama.chain_sound(p.gauge.zone, False))
    w.last_kind, w.last_enhanced = 'chain', False
    w.cooldown = w.cooldown_max = config.CHAIN_COOLDOWN
    if found:
        target = min(found, key=lambda e: math.hypot(e.center[0] - cx, e.center[1] - cy))
        w.form_state = dict(kind='zip', target=target, t=0.0, hit=set(), v=None)
        game_world.add_object(ZipLine(w), game_world.LAYER_EFFECT)
    return True


def start_wall_zip(w, point):
    """증강 '벽 걸기' (v8): 벽에 박힌 사슬을 타고 그 점으로 날아간다. 형태와 상관없이 쓴다."""
    w.form_state = dict(kind='zip', target=None, point=point, t=0.0, hit=set(), v=None)


def _tick_zip(w, st, dt):
    p, e = w.owner, st['target']
    st['t'] += dt
    cx, cy = p.center
    if e is None:                                                     # 벽으로: 가까워지면(또는 막히면) 멈춘다
        ex, ey = st['point']
        d = math.hypot(ex - cx, ey - cy)
        fx = w._fx(False)
        for o in w._targets(lambda o: id(o) not in st['hit'] and math.hypot(o.center[0] - cx, o.center[1] - cy) < 80):
            st['hit'].add(id(o))                                      # 날아가며 스친 적
            w._hit(o, w._damage(config.FORM_ZIP_MULT * 0.6), config.GAIN_HIT, fx, extra=False)
        stuck = st.get('last') is not None and math.hypot(cx - st['last'][0], cy - st['last'][1]) < 2.0 and st['t'] > 0.08
        st['last'] = (cx, cy)
        if d <= config.CHAIN_WALL_STOP or stuck or st['t'] >= config.FORM_ZIP_TIME or p.state in ('HIT', 'DEAD') or p.stunned:
            cancel(w)
            p.vx = 0.0
            p.vy = max(p.vy, 220.0)                                   # 벽 앞에서 살짝 떠오른다 (이어서 뛰거나 칠 수 있다)
            return
        flat = abs(ey - cy) < 40 and p.on_ground
        st['v'] = ((ex - cx) / d * config.FORM_ZIP_SPEED, None if flat else (ey - cy) / d * config.FORM_ZIP_SPEED)
        st['line'] = (cx, cy, ex, ey)
        return
    ex, ey = e.center
    d = math.hypot(ex - cx, ey - cy)
    fx = w._fx(False)
    for o in w._targets(lambda o: o is not e and id(o) not in st['hit'] and math.hypot(o.center[0] - cx, o.center[1] - cy) < 80):
        st['hit'].add(id(o))                                          # 날아가며 스친 적
        w._hit(o, w._damage(config.FORM_ZIP_MULT * 0.6), config.GAIN_HIT, fx, extra=False)
    done = (not e.alive) or st['t'] >= config.FORM_ZIP_TIME or d <= config.FORM_ZIP_STOP or p.state in ('HIT', 'DEAD') or p.stunned
    if done:
        cancel(w)
        p.vx = 0.0
        if e.alive and d <= config.FORM_ZIP_STOP + 70 and p.state not in ('HIT', 'DEAD'):
            w._hit(e, w._damage(config.FORM_ZIP_MULT), config.GAIN_HIT, fx, extra=False)   # 걷어찬다
            p.vy = max(p.vy, 300.0)                                   # 차고 살짝 떠오른다
            effects.add_trauma(config.SHAKE_HIT * 1.4)
        return
    flat = abs(ey - cy) < 50 and p.on_ground                          # 같은 높이의 적: 바닥을 따라 달려간다
    st['v'] = ((ex - cx) / d * config.FORM_ZIP_SPEED, None if flat else (ey - cy) / d * config.FORM_ZIP_SPEED)
    st['line'] = (cx, cy, ex, ey)


def zip_velocity(w):
    """갈고리 이동 중 주인공 속도 (Player._apply_swing_motion이 쓴다). 아니면 None."""
    st = getattr(w, 'form_state', None)
    return st['v'] if st is not None and st['kind'] == 'zip' else None


def draw_zip(w):
    """갈고리 이동 중의 사슬 (주인공 -> 걸린 적): 4px 칸을 12px마다."""
    st = getattr(w, 'form_state', None)
    if st is None or st['kind'] != 'zip' or 'line' not in st:
        return
    x0, y0, x1, y1 = st['line']
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 12))
    for i in range(n + 1):
        x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        assets.draw_rect_color(int(x) // 2 * 2 - 2, int(y) // 2 * 2 - 2, 4, 4, (160, 90, 255) if i % 2 else (235, 225, 255))


class ZipLine:
    """갈고리 이동 중 주인공과 걸린 적을 잇는 사슬. 이동이 끝나면 사라진다."""

    def __init__(self, weapon):
        self.w = weapon

    def update(self, dt):
        st = getattr(self.w, 'form_state', None)
        if st is None or st['kind'] != 'zip':
            game_world.remove_object(self)

    def draw(self):
        draw_zip(self.w)


_TICKS = {'heavy': _tick_heavy, 'jab_end': _tick_jab_end, 'zip': _tick_zip}
