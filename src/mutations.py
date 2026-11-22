"""헤이즈 변이 (2026-11-22 v5 계획 3, docs/plan_v5.md). 하데스의 축복처럼 방을 깨면 셋 중 하나를 고른다.

- 12종, 4계열. 계열마다 묶인 게이지 구간에서 힘을 낸다 (게이지를 그 구간에 두고 싶게 만든다).
  각성 bloom(50%부터) / 위험 ember(한계-10% 이상) / 페이드 hollow(20% 아래) / 강화 tide(E 강화)
- 같은 계열 2개면 시너지(계열 보너스)가 켜진다.
- 변이는 이번 판에만 있다 (player.mutations, 죽으면 Player와 함께 사라진다).
- 방 보상(REWARDS): 전투방마다 시드로 정해지고, 그 방으로 가는 문 위에 미리 보인다 (stage.reward_of).
여기는 규칙만 있다. 고르는 창은 mutation_mode, 효과가 걸리는 곳은 player·weapon·haze_gauge의 몇 줄이다.
"""
import assets
import effects
import game_world

FAMILIES = {
    'bloom': {'name': '각성', 'zone': 'AWAKE', 'color': (110, 235, 215), 'icon': 'ui/icon_absorb.png',
              'set': '각성 구간에서 이동 속도 +12%'},
    'ember': {'name': '위험', 'zone': 'CRITICAL', 'color': (255, 120, 80), 'icon': 'ui/icon_fury.png',
              'set': '위험 구간에서 게이지가 25% 덜 오른다'},
    'hollow': {'name': '페이드', 'zone': 'FADE', 'color': (130, 150, 230), 'icon': 'ui/icon_steady.png',
               'set': '페이드 구간의 이동 감속이 사라진다'},
    'tide': {'name': '강화', 'zone': None, 'color': (215, 150, 255), 'icon': 'ui/icon_enhance.png',
             'set': 'E 강화 준비 시간 +50%'},
}

BLOOM_CRIT = 1.2          # 각성 구간 공격 배율
BLOOM_GAIN = 4            # 각성 구간 처치 게이지 추가
BLOOM_DASH = (150, 14)    # 각성 구간 대시 끝 충격파 (반경 px, 피해)
BLOOM_SPEED = 1.12
EMBER_GUARD = 0.7         # 위험 구간 받는 피해 배율
EMBER_BURST = (320, 40)   # 오버로드 폭발이 적에게 (반경 px, 피해)
EMBER_COOL = 0.5          # 오버로드 피해 배율
EMBER_RISE = 0.75         # 시너지: 위험 구간 게이지 상승 배율
HOLLOW_LEECH = 2          # 페이드 구간 적중 회복
HOLLOW_DASH = 0.6         # 대시 충전 시간 배율
HOLLOW_FLOOR = 30.0       # 게이지 0이 되는 순간 한 번 이만큼으로 버틴다
TIDE_COST = 4             # E 강화 비용 감소(%)
TIDE_CHAIN = 6            # 강화 공격 처치 게이지 추가
TIDE_WAVE = (220, 0.5)    # 강화 타격이 번지는 (반경 px, 피해 비율)
TIDE_TIME = 1.5           # 시너지: 강화 준비 시간 배율

MUTATIONS = {
    'bloom_crit': {'family': 'bloom', 'name': '만개', 'desc': f'각성 구간 공격력 +{round((BLOOM_CRIT - 1) * 100)}%'},
    'bloom_gain': {'family': 'bloom', 'name': '꽃가루', 'desc': f'각성 구간 처치 게이지 +{BLOOM_GAIN}%'},
    'bloom_dash': {'family': 'bloom', 'name': '포자 폭발', 'desc': '각성 구간 대시가 끝난 자리에 충격파'},
    'ember_guard': {'family': 'ember', 'name': '그을린 피부', 'desc': f'위험 구간 받는 피해 -{round((1 - EMBER_GUARD) * 100)}%'},
    'ember_burst': {'family': 'ember', 'name': '불씨 폭주', 'desc': f'오버로드 폭발이 주변 적에게 피해 {EMBER_BURST[1]}'},
    'ember_cool': {'family': 'ember', 'name': '방열판', 'desc': f'오버로드 피해 -{round((1 - EMBER_COOL) * 100)}%'},
    'hollow_leech': {'family': 'hollow', 'name': '굶주림', 'desc': f'페이드 구간 적중마다 체력 +{HOLLOW_LEECH}'},
    'hollow_dash': {'family': 'hollow', 'name': '빈 몸', 'desc': f'대시 충전 시간 -{round((1 - HOLLOW_DASH) * 100)}%'},
    'hollow_floor': {'family': 'hollow', 'name': '마지막 숨', 'desc': f'게이지가 바닥나면 한 번 {int(HOLLOW_FLOOR)}%로 버틴다'},
    'tide_cost': {'family': 'tide', 'name': '얕은 물', 'desc': f'E 강화 비용 -{TIDE_COST}%'},
    'tide_chain': {'family': 'tide', 'name': '되밀림', 'desc': f'강화 공격으로 처치하면 게이지 +{TIDE_CHAIN}%'},
    'tide_wave': {'family': 'tide', 'name': '파문', 'desc': f'강화 타격이 주변 적에게 {round(TIDE_WAVE[1] * 100)}% 번진다'},
}

# 방 보상 -> (이름, 아이콘, 글자 색). 무게는 REWARD_WEIGHTS.
REWARDS = {
    'mutation': ('변이', 'ui/icon_absorb.png', (150, 240, 225)),
    'shards': ('조각', 'ui/icon_shard.png', (130, 235, 225)),
    'heal': ('회복', 'ui/icon_heal.png', (255, 150, 150)),
    'crystal': ('결정', 'ui/icon_cap.png', (190, 200, 255)),
}
REWARD_WEIGHTS = {'mutation': 4, 'shards': 3, 'heal': 2, 'crystal': 1}
REWARD_SHARDS = (6, 10)   # 조각 보상 범위
REWARD_HEAL = 25
REWARD_CRYSTALS = 3


# ----- 가진 것 -----
def owned(player):
    return getattr(player, 'mutations', [])


def has(player, mid):
    return mid in owned(player)


def family_count(player, family):
    return sum(1 for m in owned(player) if MUTATIONS[m]['family'] == family)


def synergy(player, family):
    return family_count(player, family) >= 2


def _zone(player):
    return player.gauge.zone


def offer(player, rng, n=3):
    """가지지 않은 변이 n개. 먼저 서로 다른 계열에서 하나씩 뽑고, 모자라면 남은 것에서 채운다."""
    left = [m for m in MUTATIONS if not has(player, m)]
    rng.shuffle(left)
    out, fams = [], set()
    for m in left:
        if MUTATIONS[m]['family'] not in fams and len(out) < n:
            out.append(m)
            fams.add(MUTATIONS[m]['family'])
    for m in left:
        if m not in out and len(out) < n:
            out.append(m)
    return out


def give(player, mid):
    """변이를 얻는다. 한 번만 걸면 되는 효과(대시 충전·강화 비용·버티기)는 여기서 건다."""
    if has(player, mid):
        return
    if not hasattr(player, 'mutations'):
        player.mutations = []
    player.mutations.append(mid)
    g = player.gauge
    if mid == 'hollow_dash':
        player.dash_recharge *= HOLLOW_DASH
    elif mid == 'tide_cost':
        g.cost_cut += TIDE_COST
    elif mid == 'hollow_floor':
        g.rescue = _rescue
    if synergy(player, 'ember') and _ember_filter not in g.filters:
        g.filters.append(_ember_filter)
    if synergy(player, 'tide'):
        g.enhance_time_mult = TIDE_TIME


def _rescue(gauge):
    """마지막 숨: 게이지가 0이 되는 순간 한 번만 HOLLOW_FLOOR로 되돌린다."""
    gauge.rescue = None
    gauge.value = HOLLOW_FLOOR
    effects.request_flash(0.25)
    assets.play_sound('zone_awake')
    return True


def _ember_filter(gauge, delta):
    """위험 시너지: 위험 구간에서 오르는 양을 줄인다."""
    return delta * EMBER_RISE if delta > 0 and gauge.zone == 'CRITICAL' else delta


# ----- 효과 (player·weapon이 부른다) -----
def damage_mult(player):
    return BLOOM_CRIT if has(player, 'bloom_crit') and _zone(player) == 'AWAKE' else 1.0


def overload_mult(player):
    return EMBER_COOL if has(player, 'ember_cool') else 1.0


def taken_mult(player):
    return EMBER_GUARD if has(player, 'ember_guard') and _zone(player) == 'CRITICAL' else 1.0


def kill_extra(player, enhanced=False):
    extra = BLOOM_GAIN if has(player, 'bloom_gain') and _zone(player) == 'AWAKE' else 0
    if enhanced and has(player, 'tide_chain'):
        extra += TIDE_CHAIN
    return extra


def speed_mult(player, base):
    """구간 이동 배율 base에 시너지를 얹는다."""
    zone = _zone(player)
    if zone == 'FADE' and synergy(player, 'hollow'):
        base = max(base, 1.0)
    if zone == 'AWAKE' and synergy(player, 'bloom'):
        base *= BLOOM_SPEED
    return base


def on_hit(player):
    """적을 때렸다: 굶주림(페이드 흡혈)."""
    if has(player, 'hollow_leech') and _zone(player) == 'FADE':
        player.hp = min(player.max_hp, player.hp + HOLLOW_LEECH)


def _blast(player, x, y, radius, damage, skip=None, color=(255, 255, 255)):
    hit = 0
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        if e is skip or not e.alive:
            continue
        ex, ey = e.center
        if (ex - x) ** 2 + (ey - y) ** 2 <= radius * radius:
            import drama
            with drama.hit_style(color=color):
                killed = e.take_damage(damage, from_x=x)
            if killed:
                player.gauge.add(player.kill_gain(), 'kill')
            hit += 1
    return hit


def on_dash_end(player):
    """포자 폭발: 각성 구간 대시가 끝난 자리에 충격파."""
    if has(player, 'bloom_dash') and _zone(player) == 'AWAKE':
        cx, cy = player.center
        effects.spawn_ring(cx, cy, FAMILIES['bloom']['color'])
        _blast(player, cx, cy, BLOOM_DASH[0], BLOOM_DASH[1], color=FAMILIES['bloom']['color'])


def on_overload(player):
    """불씨 폭주: 오버로드 폭발이 주변 적을 친다."""
    if has(player, 'ember_burst'):
        cx, cy = player.center
        _blast(player, cx, cy, EMBER_BURST[0], EMBER_BURST[1], color=FAMILIES['ember']['color'])


def on_enhanced_hit(player, enemy, damage):
    """파문: 강화 타격이 맞은 적 주변으로 번진다."""
    if has(player, 'tide_wave'):
        ex, ey = enemy.center
        effects.spawn_ring(ex, ey, FAMILIES['tide']['color'])
        _blast(player, ex, ey, TIDE_WAVE[0], damage * TIDE_WAVE[1], skip=enemy, color=FAMILIES['tide']['color'])
