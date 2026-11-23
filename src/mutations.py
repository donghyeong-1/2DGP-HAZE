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
    'bloom': {'name': '각성', 'zone': 'AWAKE', 'color': (110, 235, 215), 'icon': 'ui/mut_bloom.png',
              'set': '각성 구간에서 이동 속도 +12%'},
    'ember': {'name': '위험', 'zone': 'CRITICAL', 'color': (255, 120, 80), 'icon': 'ui/mut_ember.png',
              'set': '위험 구간 게이지 상승 -25%'},
    'hollow': {'name': '페이드', 'zone': 'FADE', 'color': (130, 150, 230), 'icon': 'ui/mut_hollow.png',
               'set': '페이드 구간 이동 감속 없음'},
    'tide': {'name': '강화', 'zone': None, 'color': (215, 150, 255), 'icon': 'ui/mut_tide.png',
             'set': 'E 강화 준비 시간 +50%'},
    # v7 무기 갈래 (docs/plan_v7.md 2절). weapon: 그 무기를 들고 있을 때 잘 나온다. set: 같은 갈래 2개면 열리는 진화
    'pipe_combo': {'name': '연타', 'zone': None, 'weapon': 'pipe', 'color': (240, 248, 255), 'icon': 'ui/mut_bloom.png',
                   'set': '진화: 난타 (준비 중)'},
    'pipe_air': {'name': '공중', 'zone': None, 'weapon': 'pipe', 'color': (150, 210, 255), 'icon': 'ui/mut_hollow.png',
                 'set': '진화: 낙뢰 내려찍기 (준비 중)'},
    'pipe_dash': {'name': '이동 베기', 'zone': None, 'weapon': 'pipe', 'color': (120, 240, 230), 'icon': 'ui/mut_tide.png',
                  'set': '진화: 섬광 베기 (준비 중)'},
    'dash': {'name': '대시', 'zone': None, 'weapon': None, 'color': (190, 215, 255), 'icon': 'ui/mut_hollow.png',
             'set': '진화: 잔영 대시 (준비 중)'},
}
GAUGE_FAMILIES = ('bloom', 'ember', 'hollow', 'tide')   # 공통 갈래 '게이지' (v5 변이 12종)
COMBO_SPEED = 0.85        # 연타: 공격 쿨다운 배율 (공속 +15%)
COMBO_THIRD = 1.3         # 3타 피해
COMBO_REACH = 1.15        # 사거리
AIR_POWER = 1.25          # 공중 공격 피해
AIR_HANG = 0.18           # 공중에서 맞히면 이 시간 동안 떨어지지 않는다(초)
DASHCUT_POWER = 1.3       # 대시 공격 피해
DASHCUT_REFUND = 0.3      # 대시 공격이 맞으면 대시 충전이 이만큼(비율) 찬다
DASH_IFRAME = 0.1         # 대시 무적 추가(초)
DASHCUT_WIDE = 1.5        # 대시 공격 판정 폭 배율
LIFT_VY = 620.0           # '띄우기': 위로 친 적이 뜨는 속도
DASH_RECHARGE = 0.75      # 대시 충전 시간 배율
OFFER_WEIGHTS = {'owned': 3.0, 'held': 2.0, 'common': 1.0, 'other': 0.2}

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
    'hollow_floor': {'family': 'hollow', 'name': '마지막 숨', 'desc': f'게이지가 바닥나면 한 번 {int(HOLLOW_FLOOR)}%로 회복 (한 번)'},
    'tide_cost': {'family': 'tide', 'name': '얕은 물', 'desc': f'E 강화 비용 -{TIDE_COST}%'},
    'tide_chain': {'family': 'tide', 'name': '되밀림', 'desc': f'강화 공격으로 처치하면 게이지 +{TIDE_CHAIN}%'},
    'tide_wave': {'family': 'tide', 'name': '파문', 'desc': f'강화 타격이 주변 적에게 {round(TIDE_WAVE[1] * 100)}% 확산'},
    # v7 철파이프 갈래 (기본 3 + 진화 1). 진화는 동작·이펙트가 준비되면 ready=True
    'combo_speed': {'family': 'pipe_combo', 'name': '손목 풀기', 'desc': f'철파이프 공격 속도 +{round((1 / COMBO_SPEED - 1) * 100)}%'},
    'combo_third': {'family': 'pipe_combo', 'name': '마무리', 'desc': f'3타 피해 +{round((COMBO_THIRD - 1) * 100)}%'},
    'combo_reach': {'family': 'pipe_combo', 'name': '긴 손잡이', 'desc': f'철파이프 사거리 +{round((COMBO_REACH - 1) * 100)}%'},
    'combo_evo': {'family': 'pipe_combo', 'tier': 'evo', 'ready': False, 'name': '난타', 'desc': '4·5타가 생기고 마지막은 회전 베기'},
    'air_power': {'family': 'pipe_air', 'name': '낙차', 'desc': f'공중 공격 피해 +{round((AIR_POWER - 1) * 100)}%'},
    'air_hang': {'family': 'pipe_air', 'name': '체공', 'desc': '공중에서 맞히면 잠깐 떨어지지 않는다'},
    'air_lift': {'family': 'pipe_air', 'name': '띄우기', 'desc': '땅에서 위로 친 적이 크게 뜬다'},
    'air_evo': {'family': 'pipe_air', 'tier': 'evo', 'ready': False, 'name': '낙뢰 내려찍기', 'desc': '내려찍기 착지에 번개 기둥과 충격파'},
    'dashcut_power': {'family': 'pipe_dash', 'name': '돌진 베기', 'desc': f'대시 공격 피해 +{round((DASHCUT_POWER - 1) * 100)}%'},
    'dashcut_refund': {'family': 'pipe_dash', 'name': '흐름', 'desc': f'대시 공격이 맞으면 대시 충전 {round(DASHCUT_REFUND * 100)}%'},
    'dashcut_wide': {'family': 'pipe_dash', 'name': '넓은 궤적', 'desc': '대시 공격 판정이 두꺼워진다'},
    'dashcut_evo': {'family': 'pipe_dash', 'tier': 'evo', 'ready': False, 'name': '섬광 베기', 'desc': '지나간 자리에 0.3초 뒤 번쩍이며 다시 벤다'},
    'dash_extra': {'family': 'dash', 'name': '여분의 숨', 'desc': '대시 +1칸'},
    'dash_iframe': {'family': 'dash', 'name': '미끄러짐', 'desc': f'대시 무적 +{DASH_IFRAME}초'},
    'dash_recharge': {'family': 'dash', 'name': '가쁜 숨', 'desc': f'대시 충전 시간 -{round((1 - DASH_RECHARGE) * 100)}%'},
    'dash_evo': {'family': 'dash', 'tier': 'evo', 'ready': False, 'name': '잔영 대시', 'desc': '대시 경로의 분신이 한 번 더 공격'},
}

# 방 보상 -> (이름, 아이콘, 글자 색). 무게는 REWARD_WEIGHTS.
REWARDS = {
    'mutation': ('변이', 'ui/reward_mutation.png', (150, 240, 225)),
    'shards': ('조각', 'ui/reward_shards.png', (130, 235, 225)),
    'heal': ('회복', 'ui/reward_heal.png', (255, 150, 150)),
    'crystal': ('결정', 'ui/reward_crystal.png', (190, 200, 255)),
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


def tier(mid):
    return MUTATIONS[mid].get('tier', 'base')


def base_count(player, family):
    return sum(1 for m in owned(player) if MUTATIONS[m]['family'] == family and tier(m) == 'base')


def available(player, mid):
    """카드에 나올 수 있는가: 아직 없고, 진화는 같은 갈래 기본 2개 + 구현 완료(ready), 합성은 필요한 것 + ready."""
    if has(player, mid):
        return False
    m = MUTATIONS[mid]
    if tier(mid) == 'evo':
        return bool(m.get('ready')) and base_count(player, m['family']) >= 2
    if tier(mid) == 'duo':
        return bool(m.get('ready')) and all(has(player, r) for r in m.get('requires', ()))
    return True


def _held_weapons(player):
    held = {'pipe'}
    for w in getattr(player, 'weapons', []) or []:
        if w is not None:
            held.add(getattr(w, 'weapon_id', None))
    return held


def _weight(player, mid):
    fam = MUTATIONS[mid]['family']
    if any(MUTATIONS[m]['family'] == fam for m in owned(player)):
        return OFFER_WEIGHTS['owned']
    weapon = FAMILIES[fam].get('weapon')
    if weapon is None:
        return OFFER_WEIGHTS['common']
    return OFFER_WEIGHTS['held'] if weapon in _held_weapons(player) else OFFER_WEIGHTS['other']


def _pick(player, cands, rng, taken):
    """갈래를 무게대로 먼저 고르고, 그 갈래의 카드 하나. 이미 고른 갈래는 피한다 (없으면 같은 갈래라도).
    (카드마다 무게를 주면 카드가 많이 남은 갈래가 유리해져, 가진 갈래가 오히려 덜 나온다)"""
    fams_taken = {MUTATIONS[m]['family'] for m in taken}
    left = [m for m in cands if m not in taken and MUTATIONS[m]['family'] not in fams_taken]
    left = left or [m for m in cands if m not in taken]
    if not left:
        return None
    by_fam = {}
    for m in left:
        by_fam.setdefault(MUTATIONS[m]['family'], []).append(m)
    fams = sorted(by_fam)
    weights = [_weight(player, by_fam[f][0]) for f in fams]
    r = rng.random() * sum(weights)
    for f, w in zip(fams, weights):
        r -= w
        if r <= 0:
            return rng.choice(by_fam[f])
    return rng.choice(by_fam[fams[-1]])


def offer(player, rng, n=3):
    """카드 n장 (v7 증강 v2). 진화·합성이 열려 있으면 한 장을 먼저 차지한다. 나머지는 갈래 무게로 뽑되
    서로 다른 갈래에서, 그리고 셋 중 하나는 아직 가지지 않은 갈래에서 (빌드를 바꿀 여지)."""
    pool = [m for m in MUTATIONS if available(player, m)]
    out = []
    special = [m for m in pool if tier(m) != 'base']
    if special:
        out.append(rng.choice(special))
    base = [m for m in pool if tier(m) == 'base']
    owned_fams = {MUTATIONS[m]['family'] for m in owned(player)}
    fresh = [m for m in base if MUTATIONS[m]['family'] not in owned_fams]
    if fresh and not any(MUTATIONS[m]['family'] not in owned_fams for m in out):
        out.append(_pick(player, fresh, rng, out))
    while len(out) < n:
        m = _pick(player, base, rng, out)
        if m is None:
            break
        out.append(m)
    rng.shuffle(out)
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
    elif mid == 'dash_extra':
        player.dash_max += 1
        player.dash_slots = min(player.dash_max, player.dash_slots + 1)
    elif mid == 'dash_recharge':
        player.dash_recharge *= DASH_RECHARGE
    if synergy(player, 'ember') and _ember_filter not in g.filters:
        g.filters.append(_ember_filter)
    if synergy(player, 'tide'):
        g.enhance_time_mult = TIDE_TIME


def remove(player, mid):
    """증강을 뺀다 (연습장). give에서 한 번 건 효과(대시 칸·충전·강화 비용·버티기·시너지)를 되돌린다."""
    if not has(player, mid):
        return
    had_ember, had_tide = synergy(player, 'ember'), synergy(player, 'tide')
    player.mutations.remove(mid)
    g = player.gauge
    if mid == 'hollow_dash':
        player.dash_recharge /= HOLLOW_DASH
    elif mid == 'tide_cost':
        g.cost_cut -= TIDE_COST
    elif mid == 'hollow_floor':
        g.rescue = None
    elif mid == 'dash_extra':
        player.dash_max -= 1
        player.dash_slots = min(player.dash_slots, player.dash_max)
    elif mid == 'dash_recharge':
        player.dash_recharge /= DASH_RECHARGE
    if had_ember and not synergy(player, 'ember') and _ember_filter in g.filters:
        g.filters.remove(_ember_filter)
    if had_tide and not synergy(player, 'tide'):
        g.enhance_time_mult = 1.0


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
def attack_speed_mult(player):
    """철파이프 공격 쿨다운 배율 (연타 '손목 풀기')."""
    return COMBO_SPEED if has(player, 'combo_speed') else 1.0


def reach_mult(player):
    return COMBO_REACH if has(player, 'combo_reach') else 1.0


def pipe_damage_mult(player, finisher=False, air=False, dash=False):
    """철파이프 갈래 피해 배율: 3타 '마무리', 공중 '낙차', 대시 공격 '돌진 베기'."""
    k = 1.0
    if finisher and has(player, 'combo_third'):
        k *= COMBO_THIRD
    if air and has(player, 'air_power'):
        k *= AIR_POWER
    if dash and has(player, 'dashcut_power'):
        k *= DASHCUT_POWER
    return k


def dash_invuln_extra(player):
    return DASH_IFRAME if has(player, 'dash_iframe') else 0.0


def on_air_hit(player):
    """공중에서 맞혔다: '체공'이면 잠깐 떨어지지 않는다."""
    if has(player, 'air_hang') and not player.on_ground:
        player.vy = max(player.vy, 0.0)
        player.hang_left = AIR_HANG


def on_dash_strike_hit(player):
    """대시 공격이 맞았다: '흐름'이면 대시 충전이 찬다."""
    if has(player, 'dashcut_refund') and player.dash_slots < player.dash_max:
        player.dash_charge += player.dash_recharge * DASHCUT_REFUND

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
