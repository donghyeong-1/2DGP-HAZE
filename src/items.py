"""아이템과 업그레이드. 황금방(하나를 골라 무료로 얻는다)과 정비방(헤이즈 조각으로 산다)에서 얻는다.

효과는 이번 판 동안만 유지된다 (죽으면 처음부터). 기획서의 업그레이드 7종(게이지 용량, 흡수 효율, 결핍 방지, 강화 효율,
오버로드 내성, 대시 강화, 기본 성장)을 아이템으로 옮겼고, 정비방 전용 회복약이 하나 더 있다. pico2d와 무관한 순수 로직이다.
"""
import config

# id -> 이름, 한 글자 표시, 설명, 가격(정비방, 헤이즈 조각), 색(화면 표시)
ITEMS = {
    'cap':     dict(name='게이지 용량', glyph='용', desc='게이지 한계 +20% (최대 160%)', price=6, color=(90, 210, 240)),
    'absorb':  dict(name='흡수 효율', glyph='흡', desc='처치할 때 게이지 +3% 더', price=5, color=(130, 235, 225)),
    'steady':  dict(name='결핍 방지', glyph='결', desc='게이지가 줄어드는 간격 +1.5초', price=5, color=(110, 150, 220)),
    'enhance': dict(name='강화 효율', glyph='강', desc='E 강화 비용 -5%', price=6, color=(240, 150, 60)),
    'resist':  dict(name='오버로드 내성', glyph='내', desc='오버로드 피해 -40%', price=5, color=(250, 220, 90)),
    'dash':    dict(name='대시 강화', glyph='대', desc='대시 슬롯 +1 (최대 5)', price=7, color=(170, 200, 255)),
    'power':   dict(name='파이프 연마', glyph='공', desc='공격력 +25%', price=6, color=(255, 120, 120)),
    'vigor':   dict(name='강인한 몸', glyph='체', desc='최대 체력 +25, 그만큼 회복', price=6, color=(255, 150, 170)),
    'heal':    dict(name='응급 치료', glyph='약', desc='체력 40 회복 (정비방 전용)', price=3, color=(120, 235, 150)),
    # 무기: 두 번째 칸에 들어가고 바로 든다 (Q·1·2로 철파이프와 바꾼다). 이미 다른 무기가 있으면 바뀐다
    'w_knife':    dict(name='투척용 식칼 묶음', glyph='칼', desc='구간이 오를수록 많이 던진다 (위험 구간 관통)', price=9,
                     color=(220, 228, 240), weapon='knife'),
    'w_gauntlet': dict(name='헤이즈 건틀릿', glyph='권', desc='누르는 동안 게이지를 태워 충전, 떼면 충격파', price=9,
                     color=(120, 220, 245), weapon='gauntlet'),
    'w_chain':    dict(name='헤이즈 사슬', glyph='사', desc='맞은 적을 끌어온다 (끌려온 적마다 게이지 +2%)', price=9,
                     color=(170, 160, 255), weapon='chain'),
}
GOLD_POOL = ['cap', 'absorb', 'steady', 'enhance', 'resist', 'dash', 'power', 'vigor']   # 황금방에서 나오는 것
WEAPON_ITEMS = ['w_knife', 'w_gauntlet', 'w_chain']   # 황금방 진열대 하나는 늘 무기다 (가진 무기는 빼고)
SHOP_POOL = ['cap', 'absorb', 'steady', 'enhance', 'resist', 'dash', 'power', 'vigor', 'heal']


def can_take(player, item_id):
    """더 얻을 수 있는가 (이미 한계면 의미가 없다)."""
    g = player.gauge
    if 'weapon' in ITEMS[item_id]:
        return not player.has_weapon(ITEMS[item_id]['weapon'])
    if item_id == 'cap':
        return g.cap < config.GAUGE_CAP_MAX
    if item_id == 'enhance':
        return g.enhance_cost > 10
    if item_id == 'steady':
        return g.decay_interval < 6.0
    if item_id == 'dash':
        return player.dash_max < config.DASH_SLOTS_MAX
    if item_id == 'heal':
        return player.hp < player.max_hp
    return True


def apply(player, item_id):
    """아이템 효과를 플레이어에게 적용한다."""
    g = player.gauge
    if 'weapon' in ITEMS[item_id]:                 # 무기는 소지 아이템 목록이 아니라 무기 칸에 들어간다
        player.give_weapon(ITEMS[item_id]['weapon'])
        return
    if item_id == 'cap':
        g.cap = min(config.GAUGE_CAP_MAX, g.cap + 20)
    elif item_id == 'absorb':
        player.kill_bonus += 3
    elif item_id == 'steady':
        g.decay_interval = min(6.0, g.decay_interval + 1.5)
    elif item_id == 'enhance':
        g.enhance_cost = max(10, g.enhance_cost - 5)
    elif item_id == 'resist':
        player.overload_mult *= 0.6
    elif item_id == 'dash':
        player.dash_max = min(config.DASH_SLOTS_MAX, player.dash_max + 1)
        player.dash_slots = min(player.dash_max, player.dash_slots + 1)
    elif item_id == 'power':
        player.attack_bonus += 0.25
    elif item_id == 'vigor':
        player.max_hp += 25
        player.hp += 25
    elif item_id == 'heal':
        player.hp = min(player.max_hp, player.hp + 40)
    else:
        raise KeyError(item_id)
    if item_id != 'heal':
        player.items.append(item_id)


def roll(rng, pool, count, player=None):
    """풀에서 겹치지 않게 count개를 뽑는다. player가 있으면 이미 한계인 것은 뺀다."""
    candidates = [i for i in pool if player is None or can_take(player, i)]
    rng.shuffle(candidates)
    return candidates[:count]


def roll_gold(rng, count, player=None):
    """황금방 진열: 하나는 무기(가진 것은 빼고), 나머지는 일반 아이템. 무기를 모두 가졌으면 일반 아이템만."""
    weapons = [w for w in WEAPON_ITEMS if player is None or can_take(player, w)]
    picked = [rng.choice(weapons)] if weapons and count > 0 else []
    picked += roll(rng, GOLD_POOL, count - len(picked), player)
    rng.shuffle(picked)
    return picked
