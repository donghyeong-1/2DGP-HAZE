"""저주 증강 (2026-11-26 사용자 제안: 하데스의 혼돈처럼).

증강 카드 셋 중 한 장이 가끔 저주 카드로 나온다. 고르면 저주가 바로 걸리고, 전투방을 정해진 수만큼 깨면 풀리면서
등급에 맞는 보상을 받는다. 카드에는 저주의 내용·기간과 보상의 등급(결정 1~3개)만 보이고, 보상이 무엇인지는 '???'다.
센 저주일수록 보상이 크다: 1 기본 증강 둘 / 2 든 무기의 진화 하나 / 3 합성 하나(재료 진화까지).
한 번에 하나만 걸린다. 저주 중에 죽으면 그대로 판이 끝난다.

걸리는 곳: 공격력·받는 피해 = mutations.damage_mult / taken_mult, 게이지 흡수 = haze_gauge.gain_mult,
게이지 한계 = gauge.cap, 무기 교체 = player.swap_weapon, 오버로드 사망 = player._on_gauge_event.
방을 세는 곳과 카드를 섞는 곳은 stage.py (전투방을 깼을 때 on_room_clear, 증강 보상 카드에 mix_in).
"""
import config

CARD = 'curse:'
OFFER_CHANCE = 0.3          # 증강 보상 카드에 저주 카드가 섞일 확률 (0이면 저주 증강이 꺼진다)
COLOR = (236, 58, 72)       # 저주: 진홍
REWARD_COLOR = (255, 214, 120)
WEAK_DAMAGE = 0.8
THIRST_GAIN = 0.6
LOWCAP = 30
FRAIL_TAKEN = 2.0
CURSES = {
    'weak': {'grade': 1, 'rooms': 3, 'name': '무뎌진 손', 'desc': f'공격력 -{round((1 - WEAK_DAMAGE) * 100)}%', 'short': '공격력 감소'},
    'thirst': {'grade': 1, 'rooms': 3, 'name': '메마름', 'desc': f'적중과 처치로 얻는 게이지 -{round((1 - THIRST_GAIN) * 100)}%',
               'short': '게이지 흡수 감소'},
    'lowcap': {'grade': 2, 'rooms': 3, 'name': '좁아진 한계', 'desc': f'게이지 한계 -{LOWCAP}%. 빨리 오버로드합니다',
               'short': '게이지 한계 감소'},
    'lock': {'grade': 2, 'rooms': 3, 'name': '굳은 손', 'desc': '무기를 교체할 수 없습니다', 'short': '무기 교체 잠김'},
    'frail': {'grade': 3, 'rooms': 2, 'name': '유리 몸', 'desc': '받는 피해가 2배가 됩니다', 'short': '받는 피해 2배'},
    'doom': {'grade': 3, 'rooms': 2, 'name': '시한폭탄', 'desc': '오버로드하면 사망합니다', 'short': '오버로드 시 사망'},
}
REWARD_NAMES = {1: '기본 증강 둘', 2: '진화', 3: '합성'}


# ----- 상태 -----
def state(player):
    return getattr(player, 'curse', None)


def active(player):
    """지금 걸린 저주의 id (없으면 None)."""
    st = state(player)
    return st['id'] if st else None


def rooms_left(player):
    st = state(player)
    return st['left'] if st else 0


def _held(player):
    return [w for w in (getattr(player, 'weapons', None) or []) if w is not None]


def _usable(player, cid):
    if cid == 'lock':
        return len(_held(player)) >= 2                     # 무기가 하나면 잠글 것이 없다
    if cid == 'lowcap':
        return player.gauge.cap - LOWCAP >= config.ZONE_NORMAL_MAX + config.CRITICAL_MARGIN
    return True


# ----- 카드 -----
def mix_in(player, cards, rng, chance=None):
    """증강 카드 목록에 저주 카드 한 장을 섞는다(확률 chance, 기본 OFFER_CHANCE). 기본 등급 카드 한 장의 자리를 차지한다
    (진화·합성 카드는 밀어내지 않는다). 첫 보상(증강이 하나도 없을 때)과 저주가 걸려 있는 동안에는 섞지 않는다."""
    import mutations as mu
    chance = OFFER_CHANCE if chance is None else chance
    if active(player) or not mu.owned(player) or chance <= 0:
        return cards
    base = [i for i, c in enumerate(cards) if c in mu.MUTATIONS and mu.tier(c) == 'base']
    pool = [cid for cid in CURSES if _usable(player, cid)]
    if not base or not pool or rng.random() >= chance:
        return cards
    cards = list(cards)
    cards[rng.choice(base)] = CARD + rng.choice(pool)
    return cards


def card_info(player, card):
    """카드 한 장에 쓸 글: 이름, 등급·기간, 저주 설명, 보상('???')."""
    c = CURSES[card[len(CARD):]]
    return {'name': c['name'], 'sub': f'저주 · 전투방 {c["rooms"]}개', 'desc': c['desc'],
            'reward': '보상 ???', 'grade': c['grade'], 'color': COLOR}          # 등급은 카드가 결정 아이콘 수로 그린다


def take(player, card):
    """저주 카드를 고른다: 저주가 바로 걸린다. (화면에 띄울 글, 색)을 돌려준다."""
    cid = card[len(CARD):]
    c = CURSES[cid]
    player.curse = {'id': cid, 'left': c['rooms'], 'grade': c['grade']}
    g = player.gauge
    if cid == 'thirst':
        g.gain_mult = THIRST_GAIN
    elif cid == 'lowcap':
        g.cap -= LOWCAP
        safe = g.cap - config.CRITICAL_MARGIN - 1.0        # 걸리는 순간 바로 터지지 않게 위험 구간 바로 아래로
        if g.value > safe:
            g.set_value(safe, 'curse')
    return f'저주: {c["name"]}', COLOR


def _lift(player):
    st, player.curse = player.curse, None
    g = player.gauge
    if st['id'] == 'thirst':
        g.gain_mult = 1.0
    elif st['id'] == 'lowcap':
        g.cap += LOWCAP
    return st


def on_room_clear(player, rng):
    """전투방 하나를 깼다. 저주가 풀렸으면 받은 증강 id 목록을, 아직이거나 저주가 없으면 None을 돌려준다."""
    st = state(player)
    if st is None:
        return None
    st['left'] -= 1
    if st['left'] > 0:
        return None
    return grant(player, _lift(player)['grade'], rng)


# ----- 효과 (다른 모듈이 부른다) -----
def damage_mult(player):
    return WEAK_DAMAGE if active(player) == 'weak' else 1.0


def taken_mult(player):
    return FRAIL_TAKEN if active(player) == 'frail' else 1.0


def cap_penalty(player):
    """지금 저주로 줄어 있는 게이지 한계 (한계를 다시 계산하는 곳에서 뺀다)."""
    return LOWCAP if active(player) == 'lowcap' else 0


def locks_swap(player):
    return active(player) == 'lock'


def kills_on_overload(player):
    return active(player) == 'doom'


# ----- 보상 -----
def _give_base(player, rng, n):
    import mutations as mu
    got = []
    for _ in range(n):
        pool = [m for m in mu.MUTATIONS if mu.tier(m) == 'base' and mu.available(player, m) and mu.offerable(player, m)]
        mid = mu._pick(player, pool, rng, got)
        if mid is None:
            break
        mu.give(player, mid)
        got.append(mid)
    return got


def _give_evo(player, rng, skip=()):
    """든 무기(또는 공통)의 진화 하나를 기본 카드 없이 바로. 이미 기본 카드를 모은 갈래일수록 잘 걸린다."""
    import mutations as mu
    pool = [m for m, d in mu.MUTATIONS.items() if mu.tier(m) == 'evo' and d.get('ready') and not mu.has(player, m)
            and mu.offerable(player, m) and m not in skip]
    if not pool:
        return None
    weights = [1 + 2 * mu.base_count(player, mu.MUTATIONS[m]['family']) for m in pool]
    r = rng.random() * sum(weights)
    mid = pool[-1]
    for m, w in zip(pool, weights):
        r -= w
        if r <= 0:
            mid = m
            break
    mu.give(player, mid)
    return mid


def grant(player, grade, rng):
    """등급에 맞는 보상을 준다. 받은 증강 id 목록 (순서대로).
    1 = 기본 증강 둘, 2 = 진화 하나, 3 = 짝이 정해진 합성 하나와 모자란 재료 진화 (만들 수 없으면 진화 둘)."""
    import mutations as mu
    if grade >= 3:
        duos = [m for m, d in mu.MUTATIONS.items() if mu.tier(m) == 'duo' and d.get('requires') and d.get('ready')
                and not mu.has(player, m) and mu.offerable(player, m)]
        if duos:
            have = lambda m: sum(mu.has(player, r) for r in mu.MUTATIONS[m]['requires'])   # noqa: E731
            best = max(have(m) for m in duos)
            duo = rng.choice([m for m in duos if have(m) == best])          # 이미 재료를 가진 쪽부터
            got = [r for r in mu.MUTATIONS[duo]['requires'] if not mu.has(player, r)]
            for r in got:
                mu.give(player, r)
            mu.give(player, duo)
            return got + [duo]
        got = [m for m in (_give_evo(player, rng), _give_evo(player, rng)) if m]
        return got or _give_base(player, rng, 2)
    if grade == 2:
        mid = _give_evo(player, rng)
        return [mid] if mid else _give_base(player, rng, 2)
    return _give_base(player, rng, 2)


def reward_text(got):
    """풀렸을 때 화면에 띄울 글: 받은 것 가운데 가장 높은 것의 이름."""
    import mutations as mu
    if not got:
        return '저주 해제'
    return '저주 해제 · ' + mu.MUTATIONS[got[-1]]['name'] + (f' 외 {len(got) - 1}' if len(got) > 1 else '')
