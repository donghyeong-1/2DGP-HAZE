"""사망 원인 이름 (2026-11-22 v5 빠른 개선 3). 사망 화면에 '무엇에 쓰러졌나'를 보여 준다.

take_hit(..., source=무엇)으로 넘어온 것을 사람이 읽는 이름으로 바꾼다: 적(정예면 수식어를 앞에), 보스, 투사체 종류,
가시. 게이지가 바닥나거나 오버로드로 쓰러지면 그 이유(GAUGE_EMPTY, OVERLOAD)를 쓴다.
"""
ENEMY_NAMES = {'slum': '슬럼 폐인', 'thrower': '고철 투척병', 'hound': '사냥개', 'guard': '간수',
               'crasher': '크래셔', 'ark': '총감시관 아크'}
PROJECTILE_NAMES = {'Scrap': '투척병의 고철', 'Lob': '투척병의 포물선 고철', 'Shockwave': '크래셔의 충격파',
                    'Debris': '떨어지는 고철', 'SteamVent': '크래셔의 증기', 'HazeBullet': '아크의 헤이즈 탄',
                    'GaugeWave': '아크의 게이지 파동', 'PollutionField': '아크의 오염 지대', 'EliteBurst': '폭발 정예의 폭발'}
OTHER = {'spike': '가시', 'debug': '시험 피해'}
GAUGE_EMPTY = '헤이즈 고갈 (게이지 0%)'
OVERLOAD = '오버로드 폭발 (게이지 100%)'


def describe(source):
    """take_hit에 넘어온 원인 -> 이름. 모르면 '알 수 없음'."""
    if source is None:
        return '알 수 없음'
    if isinstance(source, str):
        return OTHER.get(source, source)
    kind = getattr(source, 'kind', None)
    if kind in ENEMY_NAMES:
        name = ENEMY_NAMES[kind]
        label = source.elite_label() if getattr(source, 'elite', None) else ''
        return f'{label} {name}' if label else name
    return PROJECTILE_NAMES.get(type(source).__name__, '알 수 없음')
