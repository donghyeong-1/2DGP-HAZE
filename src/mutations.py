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
                   'set': '진화: 난타'},
    'pipe_air': {'name': '공중', 'zone': None, 'weapon': 'pipe', 'color': (150, 210, 255), 'icon': 'ui/mut_hollow.png',
                 'set': '진화: 낙뢰 내려찍기'},
    'pipe_dash': {'name': '이동 베기', 'zone': None, 'weapon': 'pipe', 'color': (120, 240, 230), 'icon': 'ui/mut_tide.png',
                  'set': '진화: 섬광 베기'},
    'dash': {'name': '대시', 'zone': None, 'weapon': None, 'color': (190, 215, 255), 'icon': 'ui/mut_hollow.png',
             'set': '진화: 잔영 대시'},
    # v7 사슬 갈래 (두 번째 무기: 사슬을 들고 있을 때만 효과가 있다)
    'chain_gather': {'name': '모으기', 'zone': None, 'weapon': 'chain', 'color': (200, 160, 255), 'icon': 'ui/mut_tide.png',
                     'set': '진화: 소용돌이'},
    'chain_pierce': {'name': '관통', 'zone': None, 'weapon': 'chain', 'color': (170, 190, 255), 'icon': 'ui/mut_hollow.png',
                     'set': '진화: 반사 사슬'},
    'chain_link': {'name': '연결', 'zone': None, 'weapon': 'chain', 'color': (235, 150, 235), 'icon': 'ui/mut_bloom.png',
                   'set': '진화: 헤이즈 그물'},
    # v7 쌍권총 갈래 (2026-11-24, 쌍권총을 들고 있을 때만 효과가 있다)
    'pistol_rapid': {'name': '연사', 'zone': None, 'weapon': 'pistol', 'color': (150, 250, 238), 'icon': 'ui/mut_bloom.png',
                     'set': '진화: 난사'},
    'pistol_ricochet': {'name': '도탄', 'zone': None, 'weapon': 'pistol', 'color': (255, 230, 140), 'icon': 'ui/mut_ember.png',
                        'set': '진화: 도탄 사슬'},
    'pistol_dash': {'name': '대시 사격', 'zone': None, 'weapon': 'pistol', 'color': (190, 215, 255), 'icon': 'ui/mut_hollow.png',
                    'set': '진화: 탄막 회피'},
    # v7 건틀릿 갈래 (2026-11-24, 건틀릿을 들고 있을 때만 효과가 있다)
    'gauntlet_charge': {'name': '충전', 'zone': None, 'weapon': 'gauntlet', 'color': (255, 200, 120), 'icon': 'ui/mut_ember.png',
                        'set': '진화: 헤이즈 붕괴'},
    'gauntlet_crash': {'name': '충돌', 'zone': None, 'weapon': 'gauntlet', 'color': (255, 150, 110), 'icon': 'ui/mut_bloom.png',
                       'set': '진화: 연쇄 충돌'},
    'gauntlet_counter': {'name': '반격', 'zone': None, 'weapon': 'gauntlet', 'color': (235, 245, 255), 'icon': 'ui/mut_tide.png',
                         'set': '진화: 역류'},
    # 합성: 서로 다른 진화 둘이 만나면 나온다 (전설 카드)
    'duo': {'name': '합성', 'zone': None, 'weapon': None, 'color': (255, 214, 120), 'icon': 'ui/mut_ember.png',
            'set': '진화 둘이 합쳐진 기술'},
}
GAUGE_FAMILIES = ('bloom', 'ember', 'hollow', 'tide')   # 공통 갈래 '게이지' (v5 변이 12종)
COMBO_SPEED = 0.85        # 연타: 공격 쿨다운 배율 (공속 +15%)
COMBO_THIRD = 1.3         # 3타 피해
COMBO_WAVE = (0.6, 1300.0, 460.0, 46)   # 검기 (v8 '긴 손잡이' 대신): (3타 피해 배율, 속도 px/s, 날아가는 거리 px, 판정 반높이 px)
AIR_POWER = 1.25          # 공중 공격 피해
AIR_HANG = 0.18           # 공중에서 맞히면 이 시간 동안 떨어지지 않는다(초)
DASHCUT_POWER = 1.3       # 대시 공격 피해
DASH_IFRAME = 0.1         # 대시 무적 추가(초)
DASHCUT_WIDE = 1.5        # 대시 공격 판정 폭 배율
LIFT_VY = 620.0           # '띄우기': 위로 친 적이 뜨는 속도
DASH_RECHARGE = 0.75      # 대시 충전 시간 배율
# 진화
FRENZY_REACH = 1.2        # 난타 5타 회전 베기 반경 (철파이프 사거리 배율)
FRENZY_MULT = (1.0, 1.8)  # 난타 4타 / 5타 피해 배율
BOLT = (190, 1.4, 640.0)  # 낙뢰 내려찍기 착지: (반경 px, 피해 배율, 띄우는 속도)
FLASH = (0.3, 0.6, 1.6)   # 섬광 베기: (지연 초, 피해 배율, 판정 폭 배율)
ECHO = (0.1, 0.6)         # 잔영 대시 분신: (나타나서 휘두르기까지 초, 피해 배율)
# 사슬 갈래
GATHER_STUN = 0.6         # 끌려온 적 기절(초)
VORTEX = (260, 0.5, 1.5, 0.5)   # 소용돌이: (반경, 끌어오는 시간, 묶는 시간, 피해 배율)
PIERCE_RAMP = 0.15        # 관통할 때마다 피해 +
PIERCE_REACH = 1.3        # 사거리 배율
PIERCE_BOUNCES = 2        # 반사 사슬: 벽에 꺾이는 횟수
LINK_SHARE = (0.25, 0.5)  # 묶인 적 하나를 치면 다른 쪽에 (묶기만 / '공명') 비율
LINK_TIME = 6.0           # 묶이는 시간(초)
LINK_BURST = (170, 30)    # 묶인 적이 죽으면 폭발 (반경, 피해)
NET_SIZE = 6              # 헤이즈 그물: 한 번에 묶는 수 (기본은 2)
# v7 쌍권총 갈래 수치 (초안, balance-sim으로 맞춘다)
RAPID_SPEED = 1 / 1.2     # 연사 +20% (쿨다운 배율)
RAPID_STILL = 1 / 1.3     # 멈춰 서서 쏘면 연사 +30%
RAPID_STILL_VX = 40.0     # 이 속도보다 느리면 '멈춰 섬'
RAPID_EXTRA_SPREAD = 6    # 탄 +1의 부채꼴 각도(도)
RAPID_EVO = (0.5, 4.0)    # 난사: 누르고 있을 때 (쿨다운 배율, 흩어짐 각도)
RIC_POWER = 1.3           # 반사한 총알 피해
RIC_CHAIN = (3, 460.0)    # 도탄 사슬: (튕기는 수, 다음 적을 찾는 거리)
DSHOT_AUTO = (0.06, 0.7)  # 대시 중 자동 사격: (간격 초, 피해 배율)
DSHOT_AFTER = (0.5, 0.5)  # 대시 직후 (시간, 쿨다운 배율 = 연사 2배)
DSHOT_RING = (8, 0.8)     # 탄막 회피: (총알 수, 피해 배율)
# v7 건틀릿 갈래 수치 (초안)
CHARGE_FAST = 0.75        # 충전 시간 배율
CHARGE_POWER = 1.3        # 완충 피해
CHARGE_PARRY = 120        # 쳐 내기 (v8 '버팀 자세' 대신): 충전하는 동안 이 거리(px) 안에 온 적 투사체를 지운다
COLLAPSE = (220, 0.8)     # 헤이즈 붕괴: (폭발 반지름 px, 피해 배율)
CRASH_KNOCK = 1.4         # 넉백 배율
CRASH_WALL = 0.5          # 벽에 부딪힌 적이 받는 피해 (그 강타 피해에 곱한다)
CRASH_STUN = 0.5          # 날아간 적이 멈추면 기절(초)
CRASH_FLY = 0.6           # 날아가는 상태를 지켜보는 시간(초)
CRASH_FLING = (650.0, 2.5)   # 충돌 갈래가 있으면 강타 맞은 적이 날아간다: (처음 속도 px/s, 초당 줄어드는 비율)
CRASH_CHAIN = 0.6         # 연쇄 충돌: 부딪힌 적이 받는 피해(강타 피해 배율)
COUNTER_POWER = 2.0       # 예고 중인 적에게 강타 피해 배율
COUNTER_GUARD = 0.3       # 반격 무적(초)
COUNTER_GAIN = 5          # 반격 게이지 +%
BACKFLOW = (300, 2.0)     # 역류: (투사체를 되돌리는 반지름, 되돌린 충격파 피해 = 투사체 피해 x)
# v8 합성 6종 (2026-11-25, docs/plan_v8.md 1-4). 수치는 초안 (balance-sim·플레이로 맞춘다)
DUO_PULL_BLAST = 1.6      # 끌어모아 한 방: 소용돌이 끝 붕괴 폭발 피해 (사슬 한 번 피해 배율, 여기에 COLLAPSE[1]이 곱해진다)
DUO_BOWL = 760.0          # 볼링 내려찍기: 낙뢰에 맞은 적이 옆으로 날아가는 처음 속도(px/s)
DUO_FOCUS = (9.0, 640.0)  # 집중 탄막: (총알이 꺾이는 빠르기 rad/s, 묶인 적을 찾는 거리 px)
DUO_STORM = (300, 0.6)    # 각인 폭풍: (번지는 거리 px, 번진 격발의 피해 비율)
DUO_MIST = (0.5, 3.0, 8.0)   # 교체 연무: (교체기 쿨다운 초, 쓸 때마다 게이지 -%, 이 게이지 아래면 보통 쿨다운)
OFFER_WEIGHTS = {'owned': 3.0, 'held': 2.0, 'common': 1.0}     # 2026-11-26: 안 든 무기의 갈래('other' 0.2)는 아예 나오지 않는다
OFFER_PARTNER = 3.0       # 진화 하나를 가졌을 때, 그 진화와 짝인 합성의 다른 갈래가 나오는 무게 (가진 갈래 무게에 곱한다)

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
    'bloom_dash': {'family': 'bloom', 'name': '포자 폭발', 'desc': '각성 구간에서 대시가 끝난 자리에 충격파가 일어납니다'},
    'ember_guard': {'family': 'ember', 'name': '그을린 피부', 'desc': f'위험 구간 받는 피해 -{round((1 - EMBER_GUARD) * 100)}%'},
    'ember_burst': {'family': 'ember', 'name': '불씨 폭주', 'desc': f'오버로드 폭발이 주변 적에게도 피해를 줍니다 (피해 {EMBER_BURST[1]})'},
    'ember_cool': {'family': 'ember', 'name': '방열판', 'desc': f'오버로드 피해 -{round((1 - EMBER_COOL) * 100)}%'},
    'hollow_leech': {'family': 'hollow', 'name': '굶주림', 'desc': f'페이드 구간 적중마다 체력 +{HOLLOW_LEECH}'},
    'hollow_dash': {'family': 'hollow', 'name': '빈 몸', 'desc': f'페이드 구간 대시 충전 시간 -{round((1 - HOLLOW_DASH) * 100)}%'},   # v8: '가쁜 숨'과 겹쳐 페이드에서만
    'hollow_floor': {'family': 'hollow', 'name': '마지막 숨', 'desc': f'게이지가 0%가 되면 {int(HOLLOW_FLOOR)}%로 회복합니다 (판마다 한 번)'},
    'tide_cost': {'family': 'tide', 'name': '얕은 물', 'desc': f'E 강화 비용 -{TIDE_COST}%'},
    'tide_chain': {'family': 'tide', 'name': '되밀림', 'desc': f'강화 공격으로 처치하면 게이지 +{TIDE_CHAIN}%'},
    'tide_wave': {'family': 'tide', 'name': '파문', 'desc': f'강화 공격 피해의 {round(TIDE_WAVE[1] * 100)}%가 주변 적에게 퍼집니다'},
    # v7 철파이프 갈래 (기본 3 + 진화 1). 진화는 동작·이펙트가 준비되면 ready=True
    'combo_speed': {'family': 'pipe_combo', 'name': '손목 풀기', 'desc': f'철파이프 공격 속도 +{round((1 / COMBO_SPEED - 1) * 100)}%'},
    'combo_third': {'family': 'pipe_combo', 'name': '마무리', 'desc': f'3타 피해 +{round((COMBO_THIRD - 1) * 100)}%'},
    'combo_wave': {'family': 'pipe_combo', 'name': '검기', 'desc': '3타가 앞으로 검기를 날립니다'},   # v8: '긴 손잡이'(사거리 +15%) 대신
    'combo_evo': {'family': 'pipe_combo', 'tier': 'evo', 'ready': True, 'name': '난타', 'desc': '4타와 5타가 추가됩니다. 5타는 회전 베기입니다'},
    'air_power': {'family': 'pipe_air', 'name': '낙차', 'desc': f'공중 공격 피해 +{round((AIR_POWER - 1) * 100)}%'},
    'air_hang': {'family': 'pipe_air', 'name': '체공', 'desc': '공중에서 적을 맞히면 잠깐 떨어지지 않습니다'},
    'air_lift': {'family': 'pipe_air', 'name': '띄우기', 'desc': '땅에서 위로 친 적이 높이 뜹니다'},
    'air_evo': {'family': 'pipe_air', 'tier': 'evo', 'ready': True, 'name': '낙뢰 내려찍기', 'desc': '내려찍기로 착지하면 번개 기둥과 충격파가 일어납니다'},
    'dashcut_power': {'family': 'pipe_dash', 'name': '돌진 베기', 'desc': f'대시 공격 피해 +{round((DASHCUT_POWER - 1) * 100)}%'},
    'dashcut_refund': {'family': 'pipe_dash', 'name': '깊은 낙인', 'desc': '대시 공격의 표식이 한 번에 2개 쌓입니다'},   # 11/24 '흐름'(대시 충전)은 기본이 됐다
    'dashcut_wide': {'family': 'pipe_dash', 'name': '넓은 궤적', 'desc': '대시 공격의 범위가 넓어집니다'},
    'dashcut_evo': {'family': 'pipe_dash', 'tier': 'evo', 'ready': True, 'name': '섬광 베기', 'desc': '지나간 자리를 0.3초 뒤에 한 번 더 벱니다'},
    'dash_extra': {'family': 'dash', 'name': '여분의 숨', 'desc': '대시 +1칸'},
    'dash_iframe': {'family': 'dash', 'name': '미끄러짐', 'desc': f'대시 무적 +{DASH_IFRAME}초'},
    'dash_recharge': {'family': 'dash', 'name': '가쁜 숨', 'desc': f'대시 충전 시간 -{round((1 - DASH_RECHARGE) * 100)}%'},
    'dash_evo': {'family': 'dash', 'tier': 'evo', 'ready': True, 'name': '잔영 대시', 'desc': '대시한 자리에 남은 분신이 한 번 더 공격합니다'},
    # v7 사슬 갈래
    'gather_more': {'family': 'chain_gather', 'name': '한 마리 더', 'desc': '사슬로 끌어오는 적 +1'},
    'gather_stun': {'family': 'chain_gather', 'name': '목줄', 'desc': f'끌려온 적 {GATHER_STUN}초 기절'},
    'gather_wall': {'family': 'chain_gather', 'name': '벽 걸기', 'desc': '아무도 걸리지 않은 사슬이 벽에 닿으면 그 벽으로 날아갑니다'},   # v8 (2026-11-25 사용자 요청)
    'gather_clash': {'family': 'chain_gather', 'name': '박치기', 'desc': '끌려온 적끼리 부딪혀 피해를 입습니다 (모든 구간)'},
    'gather_evo': {'family': 'chain_gather', 'tier': 'evo', 'ready': True, 'name': '소용돌이',
                   'desc': f'끌어온 자리에 소용돌이가 생겨 주변 적을 {VORTEX[2]}초 동안 묶습니다'},
    'pierce_through': {'family': 'chain_pierce', 'name': '꿰뚫기', 'desc': '사슬이 적을 관통해 모두 맞힙니다'},
    'pierce_ramp': {'family': 'chain_pierce', 'name': '가속 고리', 'desc': f'관통할 때마다 피해 +{round(PIERCE_RAMP * 100)}%'},
    'pierce_reach': {'family': 'chain_pierce', 'name': '긴 사슬', 'desc': f'사슬 사거리 +{round((PIERCE_REACH - 1) * 100)}%'},
    'pierce_evo': {'family': 'chain_pierce', 'tier': 'evo', 'ready': True, 'name': '반사 사슬',
                   'desc': f'사슬이 벽에서 {PIERCE_BOUNCES}번 튕깁니다'},
    'link_bind': {'family': 'chain_link', 'name': '사슬 묶기', 'desc': f'함께 걸린 적 둘을 묶습니다. 한쪽이 맞으면 다른 쪽도 {round(LINK_SHARE[0] * 100)}% 피해'},
    'link_share': {'family': 'chain_link', 'name': '공명', 'desc': f'묶인 적이 나눠 받는 피해 {round(LINK_SHARE[1] * 100)}% (사슬 묶기 포함)'},
    'link_burst': {'family': 'chain_link', 'name': '연쇄 폭발', 'desc': f'묶인 적이 죽으면 폭발합니다 (피해 {LINK_BURST[1]}, 사슬 묶기 포함)'},
    'link_evo': {'family': 'chain_link', 'tier': 'evo', 'ready': True, 'name': '헤이즈 그물',
                 'desc': f'걸린 적을 모두 그물로 묶습니다. 피해의 {round(LINK_SHARE[1] * 100)}%를 나눠 받습니다'},
    # v7 쌍권총 갈래
    'rapid_speed': {'family': 'pistol_rapid', 'name': '방아쇠', 'desc': f'쌍권총 연사 +{round((1 / RAPID_SPEED - 1) * 100)}%'},
    'rapid_extra': {'family': 'pistol_rapid', 'name': '덧탄', 'desc': '한 번에 나가는 총알 +1 (부채꼴)'},
    'rapid_still': {'family': 'pistol_rapid', 'name': '거치 사격', 'desc': f'멈춰 서서 쏘면 연사 +{round((1 / RAPID_STILL - 1) * 100)}%'},
    'rapid_evo': {'family': 'pistol_rapid', 'tier': 'evo', 'ready': True, 'name': '난사',
                  'desc': '누르고 있으면 끊기지 않는 탄막을 쏩니다'},
    'ric_bounce': {'family': 'pistol_ricochet', 'name': '도탄', 'desc': '총알이 벽에서 한 번 튕깁니다'},
    'ric_power': {'family': 'pistol_ricochet', 'name': '튕긴 탄', 'desc': f'튕긴 총알 피해 +{round((RIC_POWER - 1) * 100)}%'},
    'ric_more': {'family': 'pistol_ricochet', 'name': '이중 도탄', 'desc': '총알이 벽에서 한 번 더 튕깁니다'},
    'ric_evo': {'family': 'pistol_ricochet', 'tier': 'evo', 'ready': True, 'name': '도탄 사슬',
                'desc': f'적을 맞힌 총알이 가까운 적에게 튕깁니다 (최대 {RIC_CHAIN[0]}번)'},
    'dshot_auto': {'family': 'pistol_dash', 'name': '질주 사격', 'desc': '대시하는 동안 자동으로 쏩니다'},
    'dshot_after': {'family': 'pistol_dash', 'name': '여세', 'desc': f'대시 직후 {DSHOT_AFTER[0]}초 동안 연사 속도 2배'},
    'dshot_load': {'family': 'pistol_dash', 'name': '장전 회피', 'desc': '저스트 대시에 성공하면 다음 한 발이 강화탄이 됩니다'},
    'dshot_evo': {'family': 'pistol_dash', 'tier': 'evo', 'ready': True, 'name': '탄막 회피',
                  'desc': f'대시가 끝난 자리에서 {DSHOT_RING[0]}방향으로 탄막을 쏩니다'},
    # v7 건틀릿 갈래
    'charge_fast': {'family': 'gauntlet_charge', 'name': '빠른 장전', 'desc': f'건틀릿 충전 시간 -{round((1 - CHARGE_FAST) * 100)}%'},
    'charge_power': {'family': 'gauntlet_charge', 'name': '꽉 쥔 주먹', 'desc': f'끝까지 충전한 강타 피해 +{round((CHARGE_POWER - 1) * 100)}%'},
    'charge_parry': {'family': 'gauntlet_charge', 'name': '쳐 내기', 'desc': '충전하는 동안 가까이 온 적 투사체를 쳐 냅니다'},   # v8: '버팀 자세'(받는 피해 -30%) 대신
    'charge_evo': {'family': 'gauntlet_charge', 'tier': 'evo', 'ready': True, 'name': '헤이즈 붕괴',
                   'desc': '끝까지 충전한 강타가 처음 맞힌 자리에서 폭발합니다'},
    'crash_knock': {'family': 'gauntlet_crash', 'name': '밀어내기', 'desc': f'건틀릿 넉백 +{round((CRASH_KNOCK - 1) * 100)}%'},
    'crash_wall': {'family': 'gauntlet_crash', 'name': '벽꽝', 'desc': '날아간 적이 벽에 부딪히면 피해를 입습니다'},
    'crash_stun': {'family': 'gauntlet_crash', 'name': '뇌진탕', 'desc': f'날아간 적이 멈추면 {CRASH_STUN}초 기절'},
    'crash_evo': {'family': 'gauntlet_crash', 'tier': 'evo', 'ready': True, 'name': '연쇄 충돌',
                  'desc': '날아간 적에게 부딪힌 적도 함께 날아갑니다'},
    'counter_power': {'family': 'gauntlet_counter', 'name': '맞받아치기', 'desc': '공격을 준비 중인 적에게 강타 피해 2배'},
    'counter_guard': {'family': 'gauntlet_counter', 'name': '흘려 받기', 'desc': f'반격하면 {COUNTER_GUARD}초 무적'},
    'counter_gain': {'family': 'gauntlet_counter', 'name': '역습의 숨', 'desc': f'반격하면 게이지 +{COUNTER_GAIN}%'},
    'counter_evo': {'family': 'gauntlet_counter', 'tier': 'evo', 'ready': True, 'name': '역류',
                    'desc': '반격하는 순간 충격파가 적의 투사체를 되돌려 보냅니다'},
    # v7 합성 (진화 둘)
    'duo_echo_combo': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': ('combo_evo', 'dash_evo'),
                       'name': '분신 연타', 'desc': '잔영 대시의 분신이 회전 베기를 합니다'},
    'duo_flash_net': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': ('dashcut_evo', 'link_evo'),
                      'name': '그물 베기', 'desc': '섬광 베기에 맞은 적이 모두 그물로 묶입니다'},
    # v8 합성 6종 (docs/plan_v8.md 1-4). 'any_evos': 정한 짝 대신 서로 다른 무기의 진화가 그만큼 있으면 열린다
    'duo_vortex_collapse': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': ('gather_evo', 'charge_evo'),
                            'name': '끌어모아 한 방', 'desc': '소용돌이가 끝나는 순간 그 자리에서 헤이즈 붕괴가 터집니다'},
    'duo_bolt_bowl': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': ('air_evo', 'crash_evo'),
                      'name': '볼링 내려찍기', 'desc': '낙뢰 내려찍기에 맞은 적이 옆으로 날아가 다른 적을 들이받습니다'},
    'duo_focus_barrage': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': ('rapid_evo', 'gather_evo'),
                          'name': '집중 탄막', 'desc': '쌍권총 총알이 소용돌이에 묶인 적에게 휘어 들어갑니다'},
    'duo_counter_ring': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': ('counter_evo', 'dshot_evo'),
                         'name': '반격 탄막', 'desc': '반격하는 순간 쌍권총이 사방으로 탄막을 쏩니다'},
    'duo_imprint_storm': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': (), 'any_evos': 2,
                          'name': '각인 폭풍', 'desc': '격발이 가장 가까운 다른 적에게 한 번 더 번집니다'},
    'duo_swap_mist': {'family': 'duo', 'tier': 'duo', 'ready': True, 'requires': (), 'any_evos': 2,
                      'name': '교체 연무',
                      'desc': f'교체기 쿨다운 {DUO_MIST[0]}초. 쓸 때마다 게이지 {int(DUO_MIST[1])}%를 냅니다'},
}

# 방 보상 -> (이름, 아이콘, 글자 색). 무게는 REWARD_WEIGHTS.
REWARDS = {
    'mutation': ('증강', 'ui/reward_mutation.png', (150, 240, 225)),
    'shards': ('조각', 'ui/reward_shards.png', (130, 235, 225)),
    'heal': ('회복', 'ui/reward_heal.png', (255, 150, 150)),
    'crystal': ('결정', 'ui/reward_crystal.png', (190, 200, 255)),
    'form': ('형태', 'ui/reward_mutation.png', (255, 214, 120)),      # v8 무기 형태: 구역의 첫 전투방 (무작위로는 안 나온다)
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
        if m.get('any_evos') and len(evolved_weapons(player)) < m['any_evos']:
            return False
        return bool(m.get('ready')) and all(has(player, r) for r in m.get('requires', ()))
    return True


def evolved_weapons(player):
    """진화를 가진 무기들 (v8 합성 '각인 폭풍'·'교체 연무'의 조건). 대시·게이지 갈래는 무기가 아니라 세지 않는다."""
    out = set()
    for mid in owned(player):
        if tier(mid) == 'evo':
            weapon = FAMILIES[MUTATIONS[mid]['family']].get('weapon')
            if weapon:
                out.add(weapon)
    return out


def _held_weapons(player):
    held = {'pipe'}
    for w in getattr(player, 'weapons', []) or []:
        if w is not None:
            held.add(getattr(w, 'weapon_id', None))
    return held


def _offer_weapons(player):
    """카드를 낼 때 보는 '든 무기' (실제 두 칸. _held_weapons와 달리 철파이프를 늘 넣지 않는다)."""
    held = {getattr(w, 'weapon_id', None) for w in (getattr(player, 'weapons', None) or []) if w is not None}
    return held or {'pipe'}


def offerable(player, mid):
    """든 무기로 쓸 수 있는 카드인가: 공통 갈래이거나 그 무기를 들고 있다. 합성은 재료 진화가 모두 그래야 한다.
    (2026-11-26 사용자 결정: 안 든 무기의 증강은 카드에 나오지 않는다)"""
    held = _offer_weapons(player)
    mids = MUTATIONS[mid].get('requires') or (mid,)
    return all(FAMILIES[MUTATIONS[m]['family']].get('weapon') in (None, *held) for m in mids)


def duo_partner(player, family):
    """(합성 id, 짝 진화 id): 이 갈래의 진화가 재료인 '짝이 정해진 합성' 가운데 짝 갈래도 든 무기로 쓸 수 있는 것.
    짝 진화를 이미 가진 것이 먼저다. 없으면 None."""
    evo = evolution_of(family)
    found = None
    for did, d in MUTATIONS.items():
        req = d.get('requires') or ()
        if len(req) != 2 or evo not in req or not offerable(player, did):
            continue
        other = req[1 - req.index(evo)]
        if has(player, other):
            return did, other
        found = found or (did, other)
    return found


def _weight(player, mid):
    fam = MUTATIONS[mid]['family']
    pair = duo_partner(player, fam)
    if pair and has(player, pair[1]) and not has(player, evolution_of(fam)):
        return OFFER_WEIGHTS['owned'] * OFFER_PARTNER      # 합성까지 진화 하나: 그 갈래를 밀어 준다
    if any(MUTATIONS[m]['family'] == fam for m in owned(player)):
        return OFFER_WEIGHTS['owned']
    weapon = FAMILIES[fam].get('weapon')
    if weapon is None:
        return OFFER_WEIGHTS['common']
    import forms
    return OFFER_WEIGHTS['held'] * forms.weight_mult(player, fam)       # v8: 얻은 무기 형태와 잘 맞는 갈래는 더 자주


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
    """카드 n장 (v7 증강 v2). 진화·합성이 열려 있으면 한 장을 먼저 차지한다 (짝이 정해진 합성이 가장 먼저). 나머지는 갈래 무게로
    뽑되 서로 다른 갈래에서, 그리고 셋 중 하나는 아직 가지지 않은 갈래에서 (빌드를 바꿀 여지). 안 든 무기의 카드는 나오지 않는다."""
    pool = [m for m in MUTATIONS if available(player, m) and offerable(player, m)]
    out = []
    special = [m for m in pool if tier(m) != 'base']
    paired = [m for m in special if tier(m) == 'duo' and MUTATIONS[m].get('requires')]
    if special:
        out.append(rng.choice(paired or special))
    base = [m for m in pool if tier(m) == 'base']
    owned_fams = {MUTATIONS[m]['family'] for m in owned(player)}
    while len(out) < n:
        m = _pick(player, base, rng, out)
        if m is None:
            break
        out.append(m)
    # 갈래 무게로 먼저 뽑고, 새 갈래가 하나도 없을 때만 마지막 기본 카드를 새 갈래로 바꾼다
    # (새 갈래 카드를 먼저 뽑으면 가진 갈래가 나올 자리가 줄어든다)
    fresh = [m for m in base if MUTATIONS[m]['family'] not in owned_fams and m not in out]
    if fresh and not any(MUTATIONS[m]['family'] not in owned_fams for m in out):
        last = max(i for i, m in enumerate(out) if tier(m) == 'base') if any(tier(m) == 'base' for m in out) else None
        pick = _pick(player, fresh, rng, [m for i, m in enumerate(out) if i != last])
        if last is None:
            out.append(pick)
        else:
            out[last] = pick
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
    if mid == 'tide_cost':
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
    if mid == 'tide_cost':
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


def dash_recharge_time(player):
    """대시 한 칸 충전 시간. '빈 몸'은 페이드 구간에서만 줄인다 (v8: 늘 줄이던 것이 '가쁜 숨'과 겹쳤다)."""
    t = player.dash_recharge
    if has(player, 'hollow_dash') and _zone(player) == 'FADE':
        t *= HOLLOW_DASH
    return t


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


def damage_mult(player):
    import curse
    return (BLOOM_CRIT if has(player, 'bloom_crit') and _zone(player) == 'AWAKE' else 1.0) * curse.damage_mult(player)


def overload_mult(player):
    return EMBER_COOL if has(player, 'ember_cool') else 1.0


def taken_mult(player):
    import curse
    return (EMBER_GUARD if has(player, 'ember_guard') and _zone(player) == 'CRITICAL' else 1.0) * curse.taken_mult(player)


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
    """포자 폭발: 각성 구간 대시가 끝난 자리에 충격파. 잔영 대시: 시작 자리에 분신이 남아 한 번 휘두른다."""
    if has(player, 'bloom_dash') and _zone(player) == 'AWAKE':
        cx, cy = player.center
        effects.spawn_ring(cx, cy, FAMILIES['bloom']['color'])
        _blast(player, cx, cy, BLOOM_DASH[0], BLOOM_DASH[1], color=FAMILIES['bloom']['color'])
    w = getattr(player, 'weapon', None)
    if has(player, 'dshot_evo') and getattr(w, 'weapon_id', None) == 'pistol':   # v7 진화 '탄막 회피'
        w.ring_burst()
    path = getattr(player, 'last_dash_path', None)
    if has(player, 'dash_evo') and path is not None:
        import weapon
        game_world.add_object(weapon.DashEcho(player, path, has(player, 'duo_echo_combo')), game_world.LAYER_EFFECT)


def on_just_dash(player):
    """저스트 대시: '장전 회피'면 쌍권총의 다음 한 발이 강화탄."""
    w = getattr(player, 'weapon', None)
    if has(player, 'dshot_load') and getattr(w, 'weapon_id', None) == 'pistol':
        w.loaded = True
        effects.float_text(player.center[0], player.center[1] + 130, '장전!', FAMILIES['pistol_dash']['color'], life=0.7)


def on_plunge_land(player):
    """낙뢰 내려찍기: 내려찍기 뒤 땅에 닿았다 (player.on_landing이 부른다)."""
    for w in (getattr(player, 'weapons', None) or [player.weapon]):     # 철파이프 갈래: 철파이프를 들고 있지 않으면 아무 일도 없다 (v8 두 칸 자유)
        if w is not None and w.weapon_id == 'pipe':
            w.bolt_strike()
            return


# ----- 연결 갈래: 묶인 적 -----
def bind(player, enemies, size=2):
    """적 여럿(앞에서부터 size마리)을 사슬로 묶는다."""
    members = [e for e in enemies if e.alive][:size]
    if len(members) < 2:
        return None
    import weapon
    net = weapon.LinkNet(members)
    game_world.add_object(net, game_world.LAYER_EFFECT)
    return net


def linked(enemy):
    """이 적과 함께 묶인 (살아 있는) 적들."""
    net = getattr(enemy, 'haze_link', None)
    if net is None or not net.active:
        return []
    return [e for e in net.members if e is not enemy and e.alive]


def on_linked_hit(player, enemy, damage, killed):
    """묶인 적을 쳤다: 나머지가 피해를 나눠 받는다 ('공명'·'헤이즈 그물'은 더 많이). 죽었으면 '연쇄 폭발'."""
    others = linked(enemy)
    if not others:
        return
    import drama
    share = LINK_SHARE[1] if has(player, 'link_share') or has(player, 'link_evo') else LINK_SHARE[0]
    color = FAMILIES['chain_link']['color']
    for other in others:
        with drama.hit_style(color=color):
            if other.take_damage(damage * share):
                player.gauge.add(player.kill_gain(), 'kill')
        ox, oy = other.center
        effects.spawn_slash_marks(ox, oy, 1, 0, color)
    if killed and has(player, 'link_burst'):
        ex, ey = enemy.center
        effects.spawn_ring(ex, ey, color, radius_max=LINK_BURST[0])
        effects.spawn_bloom(ex, ey, color, big=True)
        _blast(player, ex, ey, LINK_BURST[0], LINK_BURST[1], skip=enemy, color=color)


# ----- 카드·일시정지 화면에 보일 정보 -----
WEAPON_NAMES = {'pipe': '철파이프', 'pistol': '쌍권총', 'gauntlet': '건틀릿', 'chain': '사슬'}
RARITY = {'base': 'common', 'evo': 'rare', 'duo': 'legendary'}


def chain_pulls(player):
    """사슬이 맞은 적을 끌어오는가 (v8): 모으기 갈래의 증강을 하나라도 가졌을 때. E 강화 일격은 이것과 상관없이 끌어온다."""
    return family_count(player, 'chain_gather') >= 1


def evolution_of(family):
    for mid, m in MUTATIONS.items():
        if m['family'] == family and tier(mid) == 'evo':
            return mid
    return None


def active(player, mid):
    """지금 효과가 있는가: 두 번째 무기 갈래는 그 무기를 들고 있을 때만."""
    weapon = FAMILIES[MUTATIONS[mid]['family']].get('weapon')
    return weapon is None or weapon in _held_weapons(player)


def card_info(player, mid):
    """카드 한 장: 테두리 등급(rarity), 아래 안내(note), 안내가 금색인가(hot)."""
    m = MUTATIONS[mid]
    t = tier(mid)
    fam_id = m['family']
    fam = FAMILIES[fam_id]
    hot = False
    if t == 'duo' and m.get('any_evos'):
        note, hot = '다른 무기의 진화 둘', True          # 카드 위에 '합성' 띠가 있다: 조건만 한 줄로 (16자 안)
    elif t == 'duo':
        note, hot = ' + '.join(MUTATIONS[r]['name'] for r in m['requires']), True
    elif t == 'evo':
        pair = duo_partner(player, fam_id)                 # 합성의 짝을 카드에서 알 수 있게 (2026-11-26)
        note, hot = (f'합성 짝: {MUTATIONS[pair[1]]["name"]}' if pair else f'{fam["name"]} 갈래 진화'), True
    elif fam_id in GAUGE_FAMILIES:
        hot = family_count(player, fam_id) + 1 >= 2
        note = ('계열 효과 켜짐: ' if hot else '같은 계열 2개면: ') + fam['set']
    else:
        evo = evolution_of(fam_id)
        left = 2 - (base_count(player, fam_id) + 1)
        name = MUTATIONS[evo]['name'] if evo else ''
        if evo is None or has(player, evo):
            note = f'{fam["name"]} 갈래'
        elif left <= 0:
            note, hot = f'진화 열림: {name}', True
        else:
            note = f'진화까지 {left}개: {name}'
            pair = duo_partner(player, fam_id)
            hot = bool(pair and has(player, pair[1]))      # 가진 진화의 합성 짝 갈래: 금색으로 눈에 띄게
    if fam_id == 'chain_gather' and t == 'base' and family_count(player, 'chain_gather') == 0:
        note = '모으기 갈래를 얻으면 사슬이 적을 끌어옵니다'      # v8: 사슬의 기본은 타격, 당기기는 이 갈래부터
    weapon = fam.get('weapon')
    if weapon and weapon not in _held_weapons(player):
        note = f'{WEAPON_NAMES.get(weapon, weapon)} 장착 시 적용 · ' + note
    return {'rarity': RARITY[t], 'note': note, 'hot': hot}


def grouped(player):
    """가진 증강을 갈래별로 [(갈래, [증강...]), ...] (처음 얻은 순서)."""
    out, index = [], {}
    for mid in owned(player):
        fam = MUTATIONS[mid]['family']
        if fam not in index:
            index[fam] = len(out)
            out.append((fam, []))
        out[index[fam]][1].append(mid)
    return out


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
