"""아이템과 업그레이드. 황금방(하나를 골라 무료로 얻는다)과 정비방(헤이즈 조각으로 산다)에서 얻는다.

기획서 3.4의 정비방 업그레이드 7종은 **각 3단계**다 (게이지 용량, 흡수 효율, 결핍 방지, 강화 효율, 오버로드 내성,
대시 강화, 기본 성장). 기본 성장은 공격력(power) / 최대 체력(vigor) 중 택1이라 둘이 3단계를 함께 쓴다.
황금방에서 얻어도 같은 단계가 하나 오른다(합쳐서 최대 3단계). 정비방 값은 단계마다 오르고 3단계는 크게 오른다.
정비방 전용 응급 치료(체력 40)는 단계가 없다. 효과는 이번 판 동안만 유지된다 (죽으면 처음부터).
단계는 player.items에 얻은 횟수로 남는다. pico2d와 무관한 순수 로직이다.
"""
import config

# id -> 이름, 한 글자 표시, 설명(단계 없는 것), 1단계 값(정비방, 헤이즈 조각), 색(화면 표시)
ITEMS = {
    'cap':     dict(name='게이지 용량', glyph='용', desc='게이지 한계 +20% (최대 160%)', price=6, color=(90, 210, 240)),
    'absorb':  dict(name='흡수 효율', glyph='흡', desc='처치할 때 게이지 +2% 더', price=5, color=(130, 235, 225)),
    'steady':  dict(name='결핍 방지', glyph='결', desc='게이지가 줄어드는 간격 +1초', price=5, color=(110, 150, 220)),
    'enhance': dict(name='강화 효율', glyph='강', desc='E 강화 비용이 줄어든다', price=6, color=(240, 150, 60)),
    'resist':  dict(name='오버로드 내성', glyph='내', desc='오버로드 피해 -5%p', price=5, color=(250, 220, 90)),
    'dash':    dict(name='대시 강화', glyph='대', desc='대시 슬롯 +1 (최대 5)', price=7, color=(170, 200, 255)),
    'power':   dict(name='기본 성장: 공격력', glyph='공', desc='공격력 +20%', price=6, color=(255, 120, 120)),
    'vigor':   dict(name='기본 성장: 체력', glyph='체', desc='최대 체력 +25, 그만큼 회복', price=6, color=(255, 150, 170)),
    'heal':    dict(name='응급 치료', glyph='약', desc='체력 40 회복 (정비방 전용)', price=3, color=(120, 235, 150)),
    # 무기: 두 번째 칸에 들어가고 바로 든다 (Q·1·2로 철파이프와 바꾼다). 이미 다른 무기가 있으면 바뀐다
    'w_knife':    dict(name='투척용 식칼 묶음', glyph='칼', desc='구간이 오를수록 많이 던진다 (위험 구간 관통)', price=9,
                     color=(220, 228, 240), weapon='knife'),
    'w_gauntlet': dict(name='헤이즈 건틀릿', glyph='권', desc='누르는 동안 게이지를 태워 충전, 떼면 충격파', price=9,
                     color=(120, 220, 245), weapon='gauntlet'),
    'w_chain':    dict(name='헤이즈 사슬', glyph='사', desc='맞은 적을 끌어온다 (끌려온 적마다 게이지 +2%)', price=9,
                     color=(170, 160, 255), weapon='chain'),
}
UPGRADES = ['cap', 'absorb', 'steady', 'enhance', 'resist', 'dash', 'power', 'vigor']   # 단계가 있는 것 (7종, 기본 성장은 둘)
TRACK = {'power': 'growth', 'vigor': 'growth'}   # 같은 단계를 함께 쓰는 것 (기본 성장 택1)
MAX_LEVEL = 3
GOLD_POOL = list(UPGRADES)                 # 황금방에서 나오는 것 (+ 무기 하나)
WEAPON_ITEMS = ['w_knife', 'w_gauntlet', 'w_chain']   # 황금방 진열대 하나는 늘 무기다 (가진 무기는 빼고)
SHOP_UPGRADES = 3                          # 정비방 진열대 4개 = 업그레이드 3개 + 응급 치료


# ----- 단계 -----
def level(player, item_id):
    """지금 몇 단계인가 (0 = 아직 없음). 기본 성장은 공격력·체력을 합쳐 센다."""
    track = TRACK.get(item_id, item_id)
    return sum(1 for i in player.items if TRACK.get(i, i) == track)


def price_at(item_id, lv):
    """lv단계를 정비방에서 살 때 값. 3단계는 크게 오른다(눈덩이 효과 방지)."""
    return int(round(ITEMS[item_id]['price'] * config.UPGRADE_PRICE_MULT[lv - 1]))


def price(player, item_id):
    """정비방에서 지금 사면 내는 값 (다음 단계 값)."""
    if item_id not in UPGRADES:
        return ITEMS[item_id]['price']
    return price_at(item_id, min(MAX_LEVEL, level(player, item_id) + 1))


def describe(player, item_id):
    """진열대 설명: 업그레이드는 '다음 단계: 지금 -> 다음' 수치로."""
    if item_id not in UPGRADES:
        return ITEMS[item_id]['desc']
    lv = level(player, item_id)
    if lv >= MAX_LEVEL:
        return '최대 단계'
    a, b = lv, lv + 1
    text = {
        'cap': lambda: f'게이지 한계 {config.GAUGE_CAP + 20 * a}% -> {config.GAUGE_CAP + 20 * b}%',
        'absorb': lambda: f'처치 게이지 +{config.GAIN_KILL + 2 * a}% -> +{config.GAIN_KILL + 2 * b}%',
        'steady': lambda: f'게이지 감소 간격 {config.GAUGE_DECAY_INTERVAL + a:g}초 -> {config.GAUGE_DECAY_INTERVAL + b:g}초',
        'enhance': lambda: f'E 강화 비용 {config.ENHANCE_COST_LEVELS[a]}% -> {config.ENHANCE_COST_LEVELS[b]}%',
        'resist': lambda: (f'오버로드 피해 {int(config.OVERLOAD_RESIST_LEVELS[a] * 100)}% -> '
                           f'{int(config.OVERLOAD_RESIST_LEVELS[b] * 100)}%'),
        'dash': lambda: f'대시 슬롯 {config.DASH_SLOTS_BASE + a} -> {config.DASH_SLOTS_BASE + b}',
        'power': lambda: f'공격력 +{int(config.GROWTH_ATTACK * 100)}% (체력과 단계 공유)',
        'vigor': lambda: f'최대 체력 +{config.GROWTH_HP}, 그만큼 회복 (공격력과 단계 공유)',
    }[item_id]()
    return f'{b}단계: {text}'


def can_take(player, item_id):
    """더 얻을 수 있는가 (이미 3단계거나 의미가 없으면 못 얻는다)."""
    if 'weapon' in ITEMS[item_id]:
        return not player.has_weapon(ITEMS[item_id]['weapon'])
    if item_id == 'heal':
        return player.hp < player.max_hp
    return level(player, item_id) < MAX_LEVEL


def apply(player, item_id):
    """아이템 효과를 플레이어에게 적용한다. 업그레이드는 한 단계 오르고 그 단계의 값(기획서 표)이 된다."""
    g = player.gauge
    if 'weapon' in ITEMS[item_id]:                 # 무기는 소지 아이템 목록이 아니라 무기 칸에 들어간다
        player.give_weapon(ITEMS[item_id]['weapon'])
        return
    if item_id == 'heal':
        player.hp = min(player.max_hp, player.hp + 40)
        return
    if item_id not in UPGRADES:
        raise KeyError(item_id)
    player.items.append(item_id)
    lv = level(player, item_id)
    if item_id == 'cap':
        g.cap = min(config.GAUGE_CAP_MAX, config.GAUGE_CAP + 20 * lv)
    elif item_id == 'absorb':
        player.kill_bonus = 2 * lv
    elif item_id == 'steady':
        g.decay_interval = config.GAUGE_DECAY_INTERVAL + lv
    elif item_id == 'enhance':
        g.enhance_cost = config.ENHANCE_COST_LEVELS[lv]
    elif item_id == 'resist':
        player.overload_mult = config.OVERLOAD_RESIST_LEVELS[lv] / config.OVERLOAD_DAMAGE_RATIO
    elif item_id == 'dash':
        player.dash_max = config.DASH_SLOTS_BASE + lv
        player.dash_slots = min(player.dash_max, player.dash_slots + 1)
    elif item_id == 'power':
        player.attack_bonus += config.GROWTH_ATTACK
    elif item_id == 'vigor':
        player.max_hp += config.GROWTH_HP
        player.hp += config.GROWTH_HP


# ----- 진열 -----
def roll(rng, pool, count, player=None):
    """풀에서 겹치지 않게 count개를 뽑는다. player가 있으면 이미 한계인 것은 뺀다."""
    candidates = [i for i in pool if player is None or can_take(player, i)]
    rng.shuffle(candidates)
    return candidates[:count]


def roll_gold(rng, count, player=None):
    """황금방 진열: 하나는 무기(가진 것은 빼고), 나머지는 업그레이드. 무기를 모두 가졌으면 업그레이드만."""
    weapons = [w for w in WEAPON_ITEMS if player is None or can_take(player, w)]
    picked = [rng.choice(weapons)] if weapons and count > 0 else []
    picked += roll(rng, GOLD_POOL, count - len(picked), player)
    rng.shuffle(picked)
    return picked


def roll_shop(rng, count, player=None):
    """정비방 진열: 업그레이드 3개(3단계인 것은 빼고) + 응급 치료 하나 (구역 사이 회복이 없어서 늘 둔다)."""
    return roll(rng, UPGRADES, min(SHOP_UPGRADES, count - 1), player) + ['heal']
