"""사망 원인 이름 (2026-11-22 v5 빠른 개선 3). 사망 화면에 '무엇에 쓰러졌나'를 보여 준다.

take_hit(..., source=무엇)으로 넘어온 것을 사람이 읽는 이름으로 바꾼다: 적(정예면 수식어를 앞에), 보스, 투사체 종류,
가시. 게이지가 바닥나거나 오버로드로 쓰러지면 그 이유(GAUGE_EMPTY, OVERLOAD)를 쓴다.
"""
ENEMY_NAMES = {'slum': '슬럼 폐인', 'thrower': '고철 투척병', 'hound': '사냥개', 'guard': '간수',
               'drone': '용접 드론', 'cart': '자폭 수레', 'eye': '감시 눈', 'knight': '결정 기사',
               'wraith': '헤이즈 망령', 'rat': '헤이즈 쥐', 'shaman': '누더기 무당', 'heart': '헤이즈 심장', 'heart_hand': '헤이즈 심장의 손',
               'crasher': '크래셔', 'ark': '총감시관 아크', 'gatekeeper': '문지기'}
PROJECTILE_NAMES = {'Scrap': '투척병의 고철', 'Lob': '투척병의 포물선 고철', 'Shockwave': '충격파',
                    'Debris': '떨어지는 고철', 'SteamVent': '크래셔의 증기', 'HazeBullet': '아크의 헤이즈 탄',
                    'GaugeWave': '아크의 게이지 파동', 'PollutionField': '아크의 오염 지대', 'EliteBurst': '폭발 정예의 자폭',
                    'CartBlast': '자폭 수레의 폭발', 'CrystalShard': '헤이즈 심장의 결정 비',
                    'ScrapPillar': '무너지는 고철 기둥'}
# 쏜 주체가 따로 있는 것(owner): '<주체 이름>의 <이름>'. 충격파는 크래셔·간수·문지기·헤이즈 심장이 모두 쓴다 (U1 2026-11-27,
# 전에는 늘 '크래셔의 충격파'로 적혀 간수에게 쓰러져도 은신처에서 크래셔 대사가 나왔다)
OWNED = ('Shockwave',)
OTHER = {'spike': '가시', 'debug': '시험 피해'}
DEVICE_NAMES = {'vent': '증기 분출구', 'laser': '감시 레이저'}   # v8 구역별 장치 (devices.py)
GAUGE_EMPTY = '헤이즈 고갈 (게이지 0%)'
OVERLOAD = '오버로드 폭발 (게이지 한계)'       # 한계는 게이지 용량 업그레이드로 100~160%
OLD_OVERLOAD = ('오버로드 폭발 (게이지 100%)',)   # U1 전 저장의 기록 (talk.cause_kind가 함께 읽는다)


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
    if kind in DEVICE_NAMES:
        return DEVICE_NAMES[kind]
    cls = type(source).__name__
    owner = getattr(source, 'owner', None)
    if cls in OWNED and owner is not None and owner is not source:
        return f'{describe(owner)}의 {PROJECTILE_NAMES[cls]}'
    return PROJECTILE_NAMES.get(cls, '알 수 없음')
