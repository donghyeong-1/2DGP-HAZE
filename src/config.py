"""게임 전체 수치 상수. 밸런싱은 이 파일만 고친다. (pico2d에 의존하지 않는다)"""

# 화면
# 2026-11-11: 1280x720/타일 40 -> 1920x1080/타일 60 (모든 크기 1.5배, 방은 그대로 32x18 칸). docs/DECISIONS.md
SCREEN_W = 1920
SCREEN_H = 1080
TILE = 60
ROOM_COLS = SCREEN_W // TILE  # 32
ROOM_ROWS = SCREEN_H // TILE  # 18
# 픽셀 아트는 확대·축소하지 않고 1배(원본 크기)로만 그린다. docs/pixel_rules.md 참고

# 물리
GRAVITY = 3600.0           # px/s^2
MAX_FALL_SPEED = 1650.0    # px/s
RUN_SPEED = 480.0          # px/s
JUMP_SPEED = 1275.0        # px/s (한 번에 약 225px = 3.75타일)
MAX_JUMPS = 2              # 2단 점프
DROP_TIME = 0.2            # S+Space 로 얇은 바닥을 무시하는 시간(초)
COYOTE_TIME = 0.10         # 낭떠러지를 걸어 떨어진 뒤에도 땅 위 점프로 쳐 주는 시간(초)
JUMP_CUT = 0.5             # 점프 키를 일찍 떼면 남은 상승 속도에 곱한다 (짧게 누르면 낮게 뛴다. platformer 지침의 release cut)
JUMP_BUFFER = 0.12         # 착지 직전에 누른 점프를 기억했다가 착지하면 뛰는 시간(초)

# 대시
DASH_SPEED = 2400.0        # px/s (거리 약 360px)
DASH_TIME = 0.15           # 초
DASH_DOWN_AIM = 0.5        # 땅 위에서 조준이 이 값보다 아래(y 성분)면 아래 대시: 얇은 발판은 뚫고, 단단한 바닥은 수평 대시
DASH_INVULN = 0.25         # 초 (무적 시간)
DASH_SLOTS_BASE = 2
DASH_SLOTS_MAX = 5
DASH_RECHARGE = 1.5        # 슬롯 한 칸 충전 시간(초)

# 대시 잔상 (던그리드처럼 지나간 자리에 청록빛 그림자가 남았다가 사라진다)
AFTERIMAGE_INTERVAL = 0.016         # 이 간격(초)마다 잔상 하나를 남긴다
AFTERIMAGE_LIFE = 0.30              # 잔상이 사라지기까지의 시간(초)
AFTERIMAGE_COLOR = (110, 235, 225)  # 헤이즈의 청록빛 (스프라이트 색에 곱해진다)
AFTERIMAGE_ALPHA_STEPS = (0.60, 0.38, 0.18)  # 수명을 3등분해 단계별로 옅어진다 (연속 페이드 대신 계단식)

# 플레이어
PLAYER_HP = 100
# 주인공 프레임 세트: 접두어 -> (프레임 수, 발 기준점 x, 발 기준점 y). 기준점은 프레임 왼쪽 위 기준 px (Codex 마감 도구의 anchor)
PLAYER_FRAMES = {'n09_idle': (4, 21, 124), 'n09_hurt': (2, 41, 124), 'n09_jump': (4, 48, 125), 'n09_walk': (8, 36, 126),
                 'n09_swing_side': (3, 64, 149), 'n09_swing_up': (3, 77, 173), 'n09_swing_down': (3, 45, 149),
                 'n09_swing_upfwd': (3, 69, 145), 'n09_swing_downfwd': (3, 64, 143)}
PLAYER_FRAMES.update({'n09_dash': (2, 40, 79), 'n09_plunge': (2, 58, 142), 'n09_death': (3, 68, 124)})
DASH_FRAME_TIME = 0.07   # 대시 자세 두 프레임이 바뀌는 간격(초)
PLUNGE_POSE_TIME = 0.5   # 내려찍기 자세를 보여 주는 시간(초)
DEATH_FRAME_TIMES = (0.2, 0.45)   # 사망 프레임이 2번, 3번으로 넘어가는 시각(초). 3번(엎어짐)은 계속 유지
DEATH_SCREEN_DELAY = 1.3   # 사망한 뒤 쓰러지는 모습을 보여 주고 사망 화면으로 넘어가기까지의 시간(초)
SWING_LAST_FRAME = 4     # 휘두르기에서 보여 주는 마지막 그림 (1 젖힘, 2 휘두르는 중, 3 타격, 4 마무리에서 끝)
SWING_TIME = 0.30        # 공격 자세(젖힘·휘두르는 중·타격·마무리·회수 5프레임)를 보여 주는 시간(초)
# 타격 판정은 누르는 순간 나간다. 그래서 준비 프레임은 아주 짧게 스치고, 타격 프레임을 길게 보여 준 뒤 마무리로 넘어간다
SWING_PHASES = (0.06, 0.12, 0.45, 0.75)   # 진행률이 이 값들을 넘을 때마다 2번(휘두르는 중), 3번(타격), 4번(마무리), 5번(회수)
# 연타마다 모양이 다르다: 1타 = 젖힘→타격→마무리→회수, 2타 = 젖힘 없이 바로 타격(빠른 되치기),
# 3타 = 젖힘을 길게 끌고 크게 내딛는다. 판정은 누르는 순간이라, 맞혀서 타격 멈춤(히트 스톱)이 걸린 동안은
# 진행률과 상관없이 타격 자세 이상을 보인다(player._body_frame). 헛스윙일 때만 젖힘 -> 휘두르는 중이 다 보인다
SWING_STYLE_TIME = {1: 0.30, 2: 0.24, 3: 0.38}
SWING_STYLE_PHASES = {1: (0.06, 0.12, 0.45, 0.75), 2: (0.0, 0.0, 0.45, 0.75), 3: (0.16, 0.28, 0.6, 0.82)}
SWING_MOVE_MULT = 0.3    # 휘두르는 동안 땅 위 이동 속도 배율 (선 자세로 미끄러지지 않게 거의 멈춘다)
SWING_LUNGE = {1: 230.0, 2: 170.0, 3: 420.0}   # 휘두를 때 조준 쪽으로 한 발 내딛는 속도(px/s). 3타는 크게
SWING_LUNGE_DECAY = 14.0  # 내딛는 속도가 줄어드는 빠르기(1/초)
IDLE_FRAME_TIME = 0.25   # 숨쉬는 대기 프레임 한 장의 시간(초)
JUMP_RISE_VY = 350.0     # 점프 프레임: vy가 이 값보다 크면 상승, 작고 -이 값보다 크면 정점, 그 아래면 하강
# 이동 그림 (Codex T19 달리기). 조준 쪽으로 움직이면 달리기 8장을 앞으로, 조준 반대쪽(뒷걸음)이면 같은 8장을 거꾸로 돌린다.
# 거꾸로 돌리면 디딘 발이 몸 앞쪽으로 밀려 나가므로 뒤로 물러나는 몸과 발이 맞는다 (11/18: 걷기 그림 역재생을 버렸다.
# 걷기 그림은 옷이 대기·달리기보다 밝게 그려져 색이 튀고, 보폭이 이동 거리의 절반이라 발이 미끄러졌다)
RUN_FRAME_PX = 32.0      # 달리기 한 장이 지나가는 거리(px). 그림에서 디딘 발이 한 장에 약 30px 뒤로 가므로 거의 미끄러지지 않는다
BACKPEDAL_SPEED_MULT = 0.75   # 뒷걸음 속도 배율 (조준을 유지한 채 물러날 때는 조금 느리다)
RUN_START_SPEED = 0.55   # 출발 자세 동안 속도가 이 배율에서 최고까지 오른다 (숙인 출발 자세로 최고 속도로 미끄러지지 않게)
RUN_START_TIME = 0.12    # 서 있다가 조준 쪽으로 달리기 시작할 때 출발 자세 두 장을 보여 주는 시간(초)
RUN_STOP_TIME = 0.16     # 멈출 때 제동 자세 두 장을 보여 주는 시간(초). 몸은 이미 멈춰 있다
RUN_STOP_MIN_RUN = 0.25  # 이만큼 넘게 앞으로 달렸을 때만 제동 자세 (짧게 톡 움직이면 그냥 선다)
RUN_TURN_TIME = 0.08     # 달리다가 조준이 뒤로 넘어가 보는 방향이 바뀔 때, 원래 보던 쪽으로 몸을 트는 자세를 보여 주는 시간(초)
SPRITE_FOOT_MARGIN = 1     # hibit 스프라이트의 발 아래 투명 여백(px). 그릴 때 이만큼 내려 바닥에 붙인다
PLAYER_HB_W = 42           # 충돌 박스 너비
PLAYER_HB_H = 108          # 충돌 박스 높이 (스프라이트 키 123px의 약 88%)
HIT_STUN = 0.25            # 피격 경직(초)
HIT_INVULN = 0.8           # 피격 뒤 무적(초). 연속으로 맞아 순식간에 죽는 것을 막는다

# 헤이즈 게이지
GAUGE_START = 30
GAUGE_CAP = 100
GAUGE_CAP_MAX = 160
GAUGE_DECAY_INTERVAL = 3.0  # 초마다
GAUGE_DECAY_AMOUNT = 1
HIGH_HAZE_INTERVAL = 2.0    # 고농도 방: 감소 대신 상승
HIGH_HAZE_AMOUNT = 1
GAIN_HIT = 3
# 타수 증가 (던그리드의 다단히트처럼): 높은 구간과 강화 공격은 한 번 맞을 때 추가 타격이 이어진다
EXTRA_HITS = {'FADE': 0, 'NORMAL': 0, 'AWAKE': 1, 'CRITICAL': 2, 'OVERLOAD': 2, 'DEAD': 0}
ENHANCED_EXTRA_HITS = 3     # 강화 공격은 구간과 상관없이 추가 3타
EXTRA_HIT_INTERVAL = 0.07   # 추가 타격 간격(초)
EXTRA_HIT_RATIO = 0.4       # 추가 타격 한 번의 피해 비율 (첫 타격 대비)
EXTRA_HIT_GAIN = 1          # 추가 타격 한 번에 오르는 게이지
GAIN_KILL = 8
GAIN_BOSS_HIT = 2
LOSS_DAMAGED = -5
ZONE_FADE_MAX = 20          # value < 20 이면 페이드 (1~19)
ZONE_NORMAL_MAX = 50        # value < 50 이면 노멀 (20~49), 각성은 50부터 (절대값)
CRITICAL_MARGIN = 10        # 위험은 cap-10 이상 (한계에 따라 움직임)
ENHANCE_COST = 25
ENHANCE_FLOOR = 5           # 사용 후 최소 이만큼 남아야 한다 (사용 가능 하한 = COST + FLOOR = 30)
ENHANCE_TIME = 12.0         # 강화 일격을 준비해 두는 최대 시간(초). 그 안에 공격하지 않으면 사라진다 (강화는 1회성)
# E 중첩 (11/19): E를 누를 때마다 단계 +1(최대 3), 단계마다 enhance_cost. 다음 공격 한 번에 모두 쓰인다.
# 1단계 = 강화 일격, 2단계 = 더 강한 판, 3단계 = 궁극기 (무기 x 기본·대시·점프, docs/plan_v4.md 1절)
ENHANCE_MAX_LEVEL = 3
ENHANCE_LEVELS = {1: dict(damage=2.5, reach=1.5, extra=3, blast=190, half=115, plunge=1.35),
                  2: dict(damage=4.0, reach=1.9, extra=5, blast=260, half=150, plunge=1.7)}
ENHANCE_STACK_MULT = {1: 1.0, 2: 1.6}
# 강화 2단계 전용 공격 (11/21): 식칼 칼날 폭풍(사방 8자루), 건틀릿 부채꼴(양옆 ±각도), 사슬 귀환 충격(주인공 둘레)
KNIFE_RING = 8
GAUNTLET_FAN_DEG = 22
CHAIN_SHOCK_RADIUS = 260
CHAIN_SHOCK_MULT = 0.8          # 식칼·건틀릿·사슬의 강화 피해에 곱한다 (2단계)
# 철파이프 2단계 (11/20 사용자: 1단계와 다른 동작): 올려베기(피해 x RISE) -> SLAM_DELAY초 뒤 앞 아래로 내려찍기(x SLAM, 바닥 충격)
STAGE2_RISE_MULT = 1.5
STAGE2_SLAM_MULT = 2.8
STAGE2_SLAM_DELAY = 0.16      # 올려베기 3장(웅크림 -> 앞 수평 -> 머리 위)을 이 시간에 고르게 보여 준다
STAGE2_SLAM_FRAMES = (0.05, 0.09)   # 내려찍기 그림: 1번(두 손 들고 뜸) ~0.05초, 2번(45도) ~0.09초, 그 뒤 3번(바닥 타격)
STAGE2_SLAM_POSE = 0.42        # 내려찍기 자세 전체 시간 (3번에서 머문다)
STAGE2_SLAM_REACH = 1.25      # 내려찍기 범위: 강화 일격 범위(2단계) x 이 값, 앞쪽만
STAGE2_RISE_HOP = 260.0       # 올려베기에 맞은 적이 살짝 떠오르는 속도 (공중 적은 그대로)
# 궁극기 (3단계)
ULT_FREEZE = 0.30            # 시전 순간 화면 정지
ULT_BANNER_TIME = 0.9        # 기술 이름 띠를 보여 주는 시간
ULT_HITS = 5                 # 연속 타격 수
ULT_HIT_INTERVAL = 0.09
ULT_HIT_MULT = 1.4           # 한 번 타격 배율 (5번이면 기본 피해 x7)
ULT_BASE_DAMAGE = 20         # 궁극기 기본 피해: 무기와 상관없이 같다 (철파이프 기본 피해와 같은 값)
ULT_BOSS_CAP = 0.15          # 궁극기 한 번이 보스에게 줄 수 있는 피해 = 최대 체력의 15%
# 2026-11-20 사용자: 화면 전체가 아니라 새 이펙트(ult-nova)의 광역 공격. 범위를 약 절반으로 줄였다 (철파이프 평타 150px의 약 3배)
ULT_FORWARD = 480            # 기본 궁극기: 앞쪽 범위(px)
ULT_DASH_LENGTH = 700        # 대시 궁극기: 직선 길이
ULT_DASH_HALF = 150          # 대시 궁극기: 직선 반폭
ULT_SLAM_RADIUS = 420        # 점프 궁극기: 좌우 범위
ULT_HEIGHT = 320             # 궁극기가 닿는 위아래 범위
ULT_DIM = 0.3                # 시전할 때 화면을 어둡게 하는 정도 (화면 전체 기술처럼 보이지 않게 옅게, 전에는 0.6)
ULT_INVULN = 1.3             # 시전하는 동안 플레이어 무적
ULT_COOLDOWN = 0.9
ULT_POSE_TIME = 0.75         # 시전 자세를 보여 주는 시간 (Codex T23): 앞쪽 ULT_POSE_GATHER는 모으기, 나머지는 해방
ULT_POSE_GATHER = 0.12       # 화면 정지(ULT_FREEZE) 동안은 시간이 흐르지 않으니 정지 내내 모으기, 풀리고 0.12초 뒤 해방
OVERLOAD_DAMAGE_RATIO = 0.20
OVERLOAD_STUN = 1.5
OVERLOAD_RESET = 30
OVERLOAD_FLASH = 0.35        # 오버로드 순간 화면 전체가 하얗게 번쩍이는 시간(초)
OVERLOAD_HIT_STOP = 0.16     # 폭발 순간 화면이 멈추는 시간(초)

# 구간별 배율 (공격, 속도)
MULT_FADE = (0.8, 0.8)
# 페이드(약해진 상태)에서는 모든 공격이 똑같이 약해진다: 판정 범위 x FADE_REACH(페이드 궤적 그림 크기와 맞춤),
# 대시·점프·내려찍기의 추가 피해 배율도 사라진다(기본 공격과 같은 x1.0). 대시·점프 공격만 강하게 나가던 버그 수정(11/19)
FADE_REACH = 0.85
MULT_NORMAL = (1.0, 1.0)
MULT_AWAKE = (1.5, 1.25)
MULT_CRITICAL = (1.8, 1.35)

# 건틀릿
GAUNTLET_DRAIN = 10.0       # 초당 감소
GAUNTLET_FLOOR = 25         # 충전으로는 이 아래까지 태우지 않는다. 보스 충격파 한 방(-5-15=-20)에 게이지 0이 되지 않게
                            # 20보다 크게 둔다. 하한에 닿으면 태울 게이지가 없어 충전도 더 차지 않는다(철파이프로 채울 것)

# 무기: 철파이프 (충전형, 3연타. 3타째에 게이지가 더 오른다)
PIPE_DAMAGE = 20
# 투척용 식칼 묶음 (구간 연동형). KNIFE_ZONE: 구간 -> (칼 수, 양옆으로 퍼지는 각도(도), 관통)
KNIFE_DAMAGE = 11
KNIFE_ZONE = {'DEAD': (1, 0, False), 'FADE': (1, 0, False), 'NORMAL': (2, 4, False), 'AWAKE': (3, 14, False),
              'CRITICAL': (3, 7, True), 'OVERLOAD': (3, 7, True)}
KNIFE_ENHANCED_EXTRA = 2     # E 강화: 칼 +2, 모두 관통
KNIFE_SPEED = 1500.0
KNIFE_RANGE = 950.0
KNIFE_HB = 26                # 칼 판정 상자 한 변(px)
KNIFE_COOLDOWN = 0.36
KNIFE_GAIN = 2               # 칼 한 자루 명중 게이지 (여러 자루가 맞으므로 일반 타격보다 작다)
# 헤이즈 건틀릿 (소모형). 충전 시간·크기는 구간별
GAUNTLET_DAMAGE = 42          # 11/21 34 -> 42: 보스전에서 충전 동안 맞기만 하던 약세 보정 (balance-sim)
GAUNTLET_CHARGE_TIME = {'DEAD': 0.9, 'FADE': 0.9, 'NORMAL': 0.9, 'AWAKE': 0.65, 'CRITICAL': 0.65, 'OVERLOAD': 0.65}   # 11/21 1.2·0.8 -> 0.9·0.65 (보스전 약세 보정)
PUNCH_TIME = {'throw': 0.26, 'blast': 0.32, 'blast_down': 0.32}   # 던지기·건틀릿 발사 자세를 보여 주는 시간(초)
GAUNTLET_CHARGE_MOVE = 0.45  # 건틀릿을 충전하는 동안 땅 위 이동 속도 배율
GAUNTLET_SIZE = {'AWAKE': 1.3, 'CRITICAL': 1.6}
GAUNTLET_CRIT_COST = 15      # 위험 구간 즉시 발사가 비우는 게이지(%)
GAUNTLET_ENHANCED_MULT = 1.5
GAUNTLET_MIN_RATIO = 0.25    # 이만큼은 충전해야 나간다
GAUNTLET_RADIUS = 34         # 충격파 반지름(px, 크기 1.0)
GAUNTLET_SPEED = 1050.0
GAUNTLET_LIFE = 0.45
GAUNTLET_COOLDOWN = 0.45
# 정비방 업그레이드 (기획서 3.4 표, 0단계 -> 3단계). 게이지 용량·흡수·결핍 방지·대시는 단계마다 일정하게 늘어 items.py에서 계산한다
ENHANCE_COST_LEVELS = (25, 20, 17, 15)              # E 강화 비용(%)
OVERLOAD_RESIST_LEVELS = (0.20, 0.15, 0.10, 0.05)   # 오버로드 폭발 피해(최대 체력 비율)
GROWTH_ATTACK = 0.20         # 기본 성장(공격력) 한 단계: 공격력 +20%
GROWTH_HP = 25               # 기본 성장(체력) 한 단계: 최대 체력 +25
UPGRADE_PRICE_MULT = (1.0, 1.6, 2.6)   # 정비방 값 = 1단계 값 x 이 배율 (3단계는 크게)
# 균열방 (11/19): 처음 들어갈 때 최대 체력의 이 %를 낸다(올림, 체력이 그 이하면 못 들어감). 안에서 둘 중 하나:
# 업그레이드 두 단계 한꺼번에 / 균열의 분노(이번 판 공격력 +RIFT_FURY_ATTACK)
RIFT_HP_COST = 15
# 영구 성장 (11/19, src/meta.py): 판이 끝날 때 받는 헤이즈 결정과 정비사 강화 한 단계의 값
META_PER_ROOM = 2            # 방 하나당 (11/19 사용자 결정 1 -> 2: 스테이지 1 중간에 죽어도 가장 싼 강화 하나)
META_PER_END = 10            # 보스·관문
META_ESCAPE = 30             # 탈출(마지막 구역 클리어)
META_HP = 10                 # 최대 체력 +10 / 단계 (5단계)
META_ATTACK = 0.05           # 공격력 +5% / 단계 (5단계)
META_GAUGE = 5               # 시작 게이지 +5% / 단계 (3단계)
META_DASH = 0.1              # 대시 충전 -0.1초 / 단계 (3단계)
META_KEEPER_PRICE = 25       # 보관인 보관 칸 열기
RIFT_FURY_ATTACK = 0.30
# 헤이즈 사슬 (중거리 제어형). CHAIN_ZONE: 구간 -> (끌 수 있는 적 수, 사거리 배율, 끌려온 적 기절·충돌)
CHAIN_DAMAGE = 20
CHAIN_RANGE = 420.0          # 노멀 사거리(px). 각성부터 x1.3
CHAIN_ZONE = {'DEAD': (1, 1.0, False), 'FADE': (1, 1.0, False), 'NORMAL': (1, 1.0, False),
              'AWAKE': (2, 1.3, False), 'CRITICAL': (2, 1.3, True), 'OVERLOAD': (2, 1.3, True)}
CHAIN_GAIN = 2               # 끌려온 적 1마리당 게이지(%). 보스는 끌려오지 않아도 맞으면 같은 만큼
CHAIN_SPEED = 1900.0         # 갈고리가 날아가는 속도
CHAIN_RETURN_SPEED = 2600.0  # 빈 갈고리가 돌아오는 속도
CHAIN_PULL_SPEED = 1100.0    # 걸린 적을 끌어오는 속도
CHAIN_PULL_GAP = 40          # 끌려온 적이 멈추는 자리: 플레이어 몸 앞에서 이만큼 떨어진 곳(px)
CHAIN_PULL_MAX_TIME = 0.6    # 이 시간 안에 못 끌어오면(지형에 걸림) 그 자리에서 끝낸다
CHAIN_HOOK_HB = 30           # 갈고리 판정 상자 한 변(px)
CHAIN_STUN = 1.0             # 위험 구간·E 강화: 끌려온 적 기절 시간(초)
CHAIN_CLASH_DAMAGE = 15      # 위험 구간: 함께 끌려온 적끼리 부딪쳐 받는 피해
CHAIN_COOLDOWN = 0.35        # 사슬이 돌아온 뒤 다음 던지기까지
# 무기별 대시·점프 공격 (11/19): 대시 중·직후 = 대시 공격, 공중 = 점프 공격 (철파이프와 같은 규칙)
KNIFE_DASH_EXTRA = 1         # 식칼 대시: 한 자루 더, 거의 일자로 모아 관통
KNIFE_DASH_SPREAD = 2
KNIFE_AIR_EXTRA = 1          # 식칼 점프: 한 자루 더, 부채꼴을 더 넓게
KNIFE_AIR_SPREAD = 14
GAUNTLET_QUICK_COST = 6      # 건틀릿 대시·점프: 충전 없이 바로 쏘는 작은 충격파의 게이지 값(%)
GAUNTLET_QUICK_RATIO = 0.7   # 그 충격파의 세기 (충전 비율로 친다)
GAUNTLET_AIR_RECOIL = 650.0  # 공중에서 아래로 쏘면 반동으로 떠오른다
CHAIN_DASH_REACH = 1.3       # 사슬 대시: 사거리 x1.3, 한 마리 더
CHAIN_DASH_EXTRA = 1
CHAIN_AIR_MULT = 1.3         # 사슬 점프: 피해 x1.3
CHAIN_ANCHOR_MULT = 1.5      # 끌려오지 않는 적(보스)에게는 갈고리가 박혀 피해 x1.5
PIPE_REACH = 150            # 몸 중심에서 닿는 거리(px)
PIPE_ARC_DEG = 65           # 조준 방향 기준 좌우 각도(도). 적 중심이 이 부채꼴 안이면 맞는다
PIPE_COOLDOWN = (0.30, 0.30, 0.55)  # 1·2·3타 뒤 다음 공격까지 (3타 뒤는 길게)
PIPE_COMBO_WINDOW = 0.55    # 이 시간 안에 다시 치면 다음 타로 이어진다
PIPE_FINISHER_MULT = 1.5    # 3타 대미지 배율
PIPE_FINISHER_GAIN = 6      # 3타 명중 시 게이지 (일반 타격은 GAIN_HIT)
HIT_STOP = 0.045            # 명중 시 화면이 잠깐 멈추는 시간(초)
HIT_STOP_DAMAGED = 0.07     # 내가 맞았을 때 멈추는 시간(초)

# 화면 흔들림 (trauma 방식: 충격마다 trauma가 오르고 시간에 따라 줄며, 흔들림 폭은 trauma의 제곱에 비례한다)
SHAKE_MAX_OFFSET = 9        # 최대 흔들림(px, 정수로만 그린다)
SHAKE_DECAY = 2.2           # 초당 줄어드는 trauma
SHAKE_HIT = 0.16            # 일반 타격
SHAKE_FINISHER = 0.38       # 파이프 3타
SHAKE_KILL = 0.30           # 적 처치
SHAKE_DAMAGED = 0.5         # 내가 맞음
SHAKE_OVERLOAD = 1.0        # 오버로드 폭발

# 적 (hb = 충돌 박스 너비·높이, 스프라이트 키에서 위쪽 여유를 뺀 값)
# sight_dy: 이 높이 차(px) 안에 플레이어가 있어야 발견, reach_dy: 이 높이 차 안일 때만 공격(투척병은 같은 층만 노린다)
# leap: 위층의 플레이어를 쫓아 뛰어오르는 속도(0이면 못 뛴다)
# moves: (기술, 가중치) 목록. 첫 기술이 기본기(첫 공격). 기술 정의는 src/enemy.py MOVES
# speed_jitter: 적마다 이동 속도가 이 범위에서 조금씩 다르다, stagger: 가끔 비틀거리며 멈춤, retreat: 공격 뒤 물러나는 시간(초)
# approach: 이보다 멀면 다가오고 가까우면 멈춰 선다(투척병), back_speed: 뒷걸음 속도 배율
# patrol: 플레이어를 보기 전 제자리 좌우로 순찰하는 거리(px), keep_away: 이보다 가까우면 뒤로 뛴다, super_armor: 공격 중 경직 없음
ENEMY_STATS = {
    'slum': dict(hp=90, hb=(42, 102), speed=210.0, sight=700, sight_dy=480, attack_range=95, reach_dy=200, damage=12,
                 windup=0.45, attack_time=0.15, cooldown=1.1, gain_on_hit=0, sprite='enemy_slum_idle',
                 leap=1250.0, moves=[('swing', 3), ('combo', 2), ('lunge', 2)], lunge_speed=560.0,
                 speed_jitter=(0.85, 1.15), stagger=True, retreat=0.25, patrol=110,
                 frames=dict(walk='enemy_slum_walk', attack='enemy_slum_attack', hurt='enemy_slum_hurt')),
    'thrower': dict(hp=45, hb=(48, 108), speed=110.0, sight=900, sight_dy=130, attack_range=820, reach_dy=130, damage=10,
                    windup=0.55, attack_time=0.1, cooldown=2.2, gain_on_hit=0, sprite='enemy_thrower_idle',
                    projectile_speed=620.0, leap=0.0, moves=[('throw', 3), ('volley', 1), ('lob', 2)], keep_away=300,
                    approach=600, back_speed=0.8, walk_px=34.0,      # 11/21 T30: 600px보다 멀면 걸어서 다가오고, 300px 안이면 물러난다
                    frames=dict(walk='enemy_thrower_walk', back='enemy_thrower_back', attack='enemy_thrower_throw', hurt='enemy_thrower_hurt')),
    # 사냥개: 빠르고 약하다. 멀리서 달려와 물고, 위층도 뛰어오른다. walk_px: 달리기 프레임 한 장이 지나가는 거리(보폭이 커서 길게)
    'hound': dict(hp=50, hb=(84, 70), speed=400.0, sight=900, sight_dy=480, attack_range=110, reach_dy=120, damage=9,
                  windup=0.28, attack_time=0.12, cooldown=0.9, gain_on_hit=0, sprite='enemy_hound_idle', leap=1300.0,
                  moves=[('bite', 2), ('pounce', 3)], speed_jitter=(0.9, 1.1), retreat=0.55, patrol=160, walk_px=62.0,
                  frames=dict(walk='enemy_hound_run', attack='enemy_hound_bite', pounce='enemy_hound_pounce',
                              hurt='enemy_hound_hurt')),
    # 간수: 느리고 단단하다. 휘두르기 전 예고가 길고 맞으면 아프다. frames의 기술 이름 키는 그 기술 전용 동작 그림
    'guard': dict(hp=150, hb=(54, 126), speed=120.0, sight=700, sight_dy=300, attack_range=125, reach_dy=200, damage=22,
                  windup=0.8, attack_time=0.2, cooldown=1.8, gain_on_hit=0, sprite='enemy_guard_idle', leap=0.0,
                  moves=[('swing', 3), ('heavy', 2), ('bash', 2)], bash_speed=640.0, wave_damage=8, super_armor=True,
                  patrol=80, walk_px=40.0,
                  frames=dict(walk='enemy_guard_walk', attack='enemy_guard_swing', heavy='enemy_guard_heavy',
                              bash='enemy_guard_bash', hurt='enemy_guard_hurt')),
}
# 적 동작 프레임 세트: 접두어 -> (프레임 수, 발 기준점 x, 발 기준점 y). 파일은 assets/sprites/unified/<접두어>_<번호>.png
ENEMY_FRAMES = {'enemy_slum_walk': (4, 43, 118), 'enemy_slum_attack': (3, 35, 119), 'enemy_slum_hurt': (1, 39, 118),
                'enemy_thrower_throw': (3, 41, 124), 'enemy_thrower_hurt': (1, 32, 124)}
ENEMY_FRAMES.update({'boss_crasher_idle': (2, 96, 205), 'boss_crasher_smash': (3, 94, 246), 'boss_crasher_charge': (2, 100, 174),
                     'boss_crasher_leap': (3, 114, 210), 'boss_crasher_hurt': (1, 96, 196)})
# 그림 안에서 발이 캔버스 바닥보다 떠 있게 그려진 프레임의 뜬 높이(px). 이미 공중에 있는 몸에 또 띄우지 않도록 기준점을 낮춘다
ENEMY_FRAME_LIFT = {('boss_crasher_leap', 2): 41}
BOSS_IDLE_FRAME_TIME = 0.45      # 크래셔 대기 두 프레임이 바뀌는 간격(초)
BOSS_LAND_POSE_TIME = 0.3        # 도약 착지 자세를 보여 주는 시간(초)
# 경직 저항(초): 적이 경직에서 풀린 뒤 이 시간 동안은 맞아도 끊기지 않는다. 연타만으로 적을 묶어 두지 못하게 해서
# 예고(깜빡임)를 보고 피하는 플레이가 이득이 되게 한다. 적마다 ENEMY_STATS의 stagger_guard로 바꿀 수 있다
ENEMY_STAGGER_GUARD = 0.9
ENEMY_WALK_FRAME_PX = 44.0       # 적 걷기 프레임 한 장이 지나가는 이동 거리(px)
BOSS_LEAP_TIME = 0.8             # 보스 도약 체공 시간(초). 기둥·벽 뒤에 숨은 플레이어에게 넘어가 내려찍는다
BOSS_LEAP_SPEED_CAP = 760.0
BOSS_LAND_RADIUS = 210           # 도약 착지 충격 반경(px)
BOSS_LAND_DAMAGE = 20
# 크래셔 헤이즈 증기 분출(기획 3.2): 닿으면 게이지 +12% (피해 없음). 충격파(-20%)와 반대로 게이지를 올려 오버로드 쪽으로 민다.
# 게이지가 낮을 때는 일부러 들어가 채울 수도 있다
STEAM_GAUGE = 12

# 보스 크래셔 (기획 3.2: 충격파 게이지 -20%, 돌진은 변화 없음). 같은 표에 두고 Boss 클래스가 패턴을 쓴다
ENEMY_STATS['crasher'] = dict(
    hp=700, hb=(100, 180), speed=150.0, sight=2600, sight_dy=900, attack_range=190, reach_dy=260, damage=18,
    windup=0.5, attack_time=0.2, cooldown=0.9, gain_on_hit=0, sprite='boss_crasher_idle', leap=0.0,
    charge_speed=950.0, charge_time=0.55, charge_damage=24, wave_speed=520.0, wave_damage=12, wave_gauge=-15)
LEAP_COOLDOWN = 1.4          # 뛰어오른 뒤 다음 도약까지(초)
SPIKE_DAMAGE = 15            # 가시에 닿았을 때 피해 (게이지는 피격과 같이 -5)
SPIKE_BOUNCE = 900.0         # 가시에 닿으면 위로 튕겨 나가는 속도(px/s)
SPIKE_HEIGHT = 30            # 가시 타일에서 실제로 찌르는 높이(px, 타일 아래쪽)
# 헤이즈 조각 (재화). 적을 처치하면 떨어뜨리고, 정비방 업그레이드에 쓴다 (정비방은 3주차)
# 최종 보스 아크 (기획서 3.2, src/ark.py). 3페이즈, 게이지를 위아래로 크게 흔든다. 경직 없음
ENEMY_STATS['ark'] = dict(
    hp=1000, hb=(60, 150), speed=120.0, sight=2600, sight_dy=900, attack_range=170, reach_dy=260, damage=18,
    windup=0.6, attack_time=0.3, cooldown=1.1, gain_on_hit=0, sprite='boss_ark_idle', leap=0.0, walk_px=34.0)
# 게이지 수치는 '맞았을 때 최종 변화'(피격 기본 손실 LOSS_DAMAGED -5까지 합친 값). 코드는 gauge_delta = NET - LOSS_DAMAGED로 넘긴다
ARK_BULLET_NET = 5            # 헤이즈 탄막: 탄환 1발당 +5%
ARK_BULLET_DAMAGE = 6
ARK_BULLET_SPEED = 560.0
ARK_BULLET_COUNT = (5, 7, 9)  # 페이즈별 부채꼴 탄 수
ARK_BULLET_SPREAD = 50.0      # 부채꼴 전체 각도(도)
ARK_SLASH_NET = -10           # 순간이동 베기 (피해는 ENEMY_STATS['ark']['damage'])
ARK_SLASH_RANGE = 190         # 베기 앞쪽 사거리(px)
ARK_VANISH_TIME = 0.3         # 안개로 흩어지는 시간(초) 뒤 플레이어 옆에 나타난다
ARK_APPEAR_TIME = 0.45        # 나타난 뒤 베기 예고(초). 앞쪽 절반은 웅크린 '나타남' 자세, 뒤쪽은 손날을 당긴 자세
ARK_TELEPORT_GAP = 150        # 플레이어 뒤쪽 이 거리에 나타난다(px)
ARK_ABSORB_NET = -25          # 흡수 파동: 방 양끝에서 아크 쪽으로 조여 든다
ARK_OVERCHARGE_NET = 25       # 과충전 파동: 아크에서 바깥으로 퍼진다
ARK_WAVE_DAMAGE = 10
ARK_WAVE_SPEED = 520.0
ARK_WAVE_H = 80               # 파동 높이(px): 점프(약 225px)로 넘을 수 있다
ARK_FIELD_RATE = 5.0          # 오염 장판 위에 서 있으면 초당 +5%
ARK_FIELD_W = (300, 340, 400)  # 페이즈별 장판 폭(px)
ARK_FIELD_TIME = (5.0, 6.0, 7.0)   # 장판이 남는 시간(초)
ARK_PHASES = (0.66, 0.33)     # 체력 비율이 이 아래로 내려가면 2페이즈, 3페이즈
ARK_DEATH_FALL = 0.6          # 쓰러질 때 무릎 꿇은 자세(사망 1)를 보여 주는 시간(초), 그 뒤 엎어짐(사망 2)
SHARDS_PER_KILL = {'slum': 1, 'thrower': 2, 'hound': 1, 'guard': 3, 'crasher': 10, 'ark': 20}
# 정예 적 (11/21 퀄리티 계획 2-4): 일반 적에 수식어. 색 테두리와 이름으로 표시, 조각 2배
ELITE_MODS = {
    'swift': dict(name='질주', color=(90, 235, 220), speed=1.35, windup=0.8),
    'tough': dict(name='강철', color=(150, 180, 230), hp=2.2, weight=1.6),
    'volatile': dict(name='폭발', color=(255, 150, 60)),
}
ELITE_CHANCE = {'stage1': 0.10, 'stage2': 0.18, 'stage3': 0.25}   # 적 하나가 정예일 확률 (은신처·그 밖은 0)
ELITE_SHARD_MULT = 2
ELITE_BURST_DELAY = 0.6        # 폭발 정예가 쓰러진 뒤 터지기까지 (예고 고리가 조여 든다)
ELITE_BURST_RADIUS = 170
ELITE_BURST_DAMAGE = 14
ELITE_BURST_NET = 8            # 폭발에 맞으면 게이지 최종 +8% (헤이즈가 스며든다)

# E 강화 일격 (1회성): 게이지 ENHANCE_COST를 쓰면 **다음 공격 한 번**이 강화 일격이 된다. 쓰고 나면 사라진다.
# 강화 일격은 대미지가 크고 사거리·부채꼴이 넓으며, 맞은 적마다 안개 폭발이 일어나 주변 적에게 피해를 준다.
ENHANCE_DAMAGE_MULT = 2.5
ENHANCE_REACH_MULT = 1.5
ENHANCE_ARC_BONUS_DEG = 25
ENHANCE_BLAST_RADIUS = 190     # 맞은 적 주위로 퍼지는 안개 폭발
ENHANCE_BLAST_DAMAGE = 30
ENHANCE_STRIKE_COOLDOWN = 0.65  # 강화 일격 뒤 다음 공격까지

# 특수 공격 (대시 평타, 점프 평타). 아무 키 없이 상황으로 정해진다: 대시 중·직후 공격 = 대시 평타, 공중 공격 = 점프 평타
DASH_ATTACK_WINDOW = 0.22       # 대시가 끝난 뒤에도 이 시간(초) 안에 공격하면 대시 평타
DASH_STRIKE_MULT = 1.4          # 대미지 배율
DASH_STRIKE_HALF_WIDTH = 70     # 대시로 지나온 경로(직선) 양옆으로 이 반폭(px) 안의 적을 모두 벤다 (관통)
DASH_STRIKE_ENHANCED_HALF_WIDTH = 115   # 강화된 대시 평타는 경로 양옆이 더 넓다
DASH_STRIKE_COOLDOWN = 0.40
AIR_SPIN_MULT = 1.2             # 점프 평타(회전 베기) 대미지 배율
AIR_SPIN_REACH = 170            # 몸 둘레 360도 사거리(px)
AIR_HOP = 380.0                 # 회전 베기를 하면 살짝 떠오른다(px/s)
AIR_COOLDOWN = 0.50
PLUNGE_MULT = 1.6               # 공중에서 아래를 겨누고 치면 내려찍기: 아래로 꿰뚫고 맞으면 튕겨 오른다
PLUNGE_LENGTH = 300
PLUNGE_HALF_WIDTH = 80
PLUNGE_BOUNCE = 950.0
PLUNGE_AIM = -0.65              # 조준 y 성분이 이보다 작으면(아래를 향하면) 내려찍기
PLUNGE_COOLDOWN = 0.55

ENEMY_HIT_FLASH = 0.10       # 맞았을 때 붉게 번쩍이는 시간(초)
ENEMY_KNOCKBACK = 260.0      # 맞았을 때 밀려나는 속도(px/s). 실제로는 x 공격 크기(KNOCK_*) / 적 무게(ENEMY_WEIGHT)
# 손맛 (11/21 퀄리티 계획 1-5): 맞은 순간 흰 번쩍임 -> 붉게, 무게·공격 크기에 따른 밀림, 방 마지막 적에서 슬로 모션
ENEMY_WHITE_FLASH = 0.05     # 맞은 뒤 처음 이만큼은 하얗게 번쩍인다 (ENEMY_HIT_FLASH 안에서)
ENEMY_WEIGHT = {'hound': 0.7, 'slum': 1.0, 'thrower': 1.0, 'guard': 1.8}   # 클수록 덜 밀린다
KNOCK_BIG = 1.8              # 큰 공격(3타·강화·궁극기 마지막 등 big=True)의 밀림 배율
SLOW_CLEAR = (0.45, 0.35)    # 방의 마지막 적을 쓰러뜨렸을 때 슬로 모션 (실제 시간 초, 시간 배율)
SLOW_BOSS = (1.1, 0.25)      # 보스를 쓰러뜨렸을 때
# 쓰러짐 (Codex T25): 쓰러지는 3장 -> 누워 있다가 헤이즈 조각으로 흩어진다
CORPSE_FRAMES = (0.09, 0.22)  # 1번 -> 2번, 2번 -> 3번이 되는 시간(초)
CORPSE_TIME = 0.9             # 누워 있는 데까지 (그 뒤 흩어지며 사라진다)
CORPSE_FADE = 0.35            # 흩어지며 사라지는 시간
HINT_TIME = 6.0               # 처음 안내판을 보여 주는 시간(초) (11/21 계획 2-5, src/tutorial.py)
AMB_GAP = (3.0, 8.0)          # 환경음 사이 간격(초, 무작위) (11/21 계획 2-3, src/ambience.py)
ENEMY_WINDUP_SOUND = {'slum': 'windup_slum', 'thrower': 'windup_thrower', 'hound': 'windup_hound', 'guard': 'windup_guard'}
# 효과음 음량 균형 (11/21 계획 1-7): 소리마다 기본 음량에 곱한다. 자주 나는 소리는 작게, 큰 기술은 그대로나 조금 크게.
# 표에 없는 소리는 1.0
SFX_GAIN = {'land': 0.55, 'jump': 0.65, 'double_jump': 0.7, 'swing': 0.75, 'swing_fade': 0.7, 'swing_awake': 0.8,
            'enemy_hit': 0.7, 'impact_pipe': 0.75, 'impact_knife': 0.7, 'impact_gauntlet': 0.8, 'throw': 0.75,
            'chain_throw': 0.8, 'dash': 0.8, 'ult_hit': 0.8, 'windup_slum': 0.8, 'windup_thrower': 0.75,
            'windup_hound': 0.85, 'windup_guard': 0.9, 'ult_cast': 1.15, 'ark_roar': 1.1,
            'ult_final_pipe': 1.2, 'ult_final_knife': 1.2, 'ult_final_gauntlet': 1.2, 'ult_final_chain': 1.2,
            'throw_fade': 0.7, 'throw_awake': 0.8, 'chain_throw_fade': 0.75, 'chain_throw_awake': 0.8, 'heartbeat': 0.75,
            'zone_awake': 0.85, 'kill_last': 1.1,
            'amb_drip': 0.45, 'amb_steam': 0.35, 'amb_wind': 0.45, 'amb_forge': 0.4}   # 환경음은 작게
ENEMY_SPAWN_ORDER = ('slum', 'thrower')  # 방의 E 칸에 순서대로 배정한다 (스테이지 데이터가 생기기 전 임시)
PROJECTILE_HB = (30, 18)

# 화면 효과·UI 크기. 1920x1080에서는 원본 크기 효과와 14px 글자가 작아서, 정수 배율(최근접)로만 키운다.
# docs/pixel_rules.md "정수 배율 예외" 참고. 월드 스프라이트와 타일은 1배 그대로다.
EFFECT_SCALE = 2           # 타격 불꽃·휘두르기·연기 등 이펙트 시트 배율
FONT_SCALE = 2             # 글자는 14px/11px 원본의 정수 배(28/22px)로만 그린다. 큰 글자는 3배(42px)
DAMAGE_COLOR = (255, 238, 150)
DAMAGE_COLOR_FINISHER = (255, 170, 80)
DAMAGE_COLOR_ENHANCED = (130, 235, 225)

# 게이지 구간별 공격 효과 (docs/기획서.md 5.12). 구간이 높을수록 궤적이 크고 화려하고, 화면 흔들림·멈춤·소리도 세진다.
#   slash: 휘두르기 시트 / spark: 명중 효과 시트 / shake·stop: 화면 흔들림·타격 멈춤 배율 / sound: 휘두르기 소리 / damage_color: 데미지 숫자 색
ZONE_FX = {
    'FADE':     dict(slash='pipe-slash-fade', spark='hit-fade', spark_time=0.22, shake=0.6, stop=0.7, sound='swing_fade',
                     damage_color=(185, 140, 165)),
    'NORMAL':   dict(slash='pipe-slash', spark='hit-normal', spark_time=0.24, shake=1.0, stop=1.0, sound='swing',
                     damage_color=(255, 238, 150)),
    'AWAKE':    dict(slash='pipe-slash-awake', spark='hit-awake', spark_time=0.28, shake=1.3, stop=1.2, sound='swing_awake',
                     damage_color=(160, 255, 210)),
    'CRITICAL': dict(slash='pipe-slash-critical', spark='hit-critical', spark_time=0.32, shake=1.7, stop=1.5, sound='swing_critical',
                     damage_color=(255, 150, 90)),
}
ZONE_FX['OVERLOAD'] = ZONE_FX['CRITICAL']
ZONE_FX['DEAD'] = ZONE_FX['FADE']
ENHANCED_FX = dict(slash='pipe-slash-enhanced', spark='hit-enhanced', spark_time=0.34, shake=1.9, stop=1.6, sound='swing_enhanced',
                   damage_color=(230, 190, 255), enhanced=True)
# 강화 단계별 색 (11/21): 1단계 보라, 2단계 금, 3단계(궁극기 준비) 진홍. 몇 번 강화했는지 색으로 읽힌다.
# 2·3단계 이펙트 시트(<이름>2·3)는 tools/recolor_fx.py가 보라 시트를 다시 칠해 만든다.
ENHANCE_LEVEL_COLOR = {1: (200, 160, 255), 2: (255, 206, 92), 3: (255, 96, 110)}
ENHANCED_FX_BY_LEVEL = {
    1: ENHANCED_FX,
    2: dict(ENHANCED_FX, slash='pipe-slash-enhanced2', spark='hit-enhanced2', damage_color=(255, 214, 120)),
    3: dict(ENHANCED_FX, slash='pipe-slash-enhanced3', spark='hit-enhanced3', damage_color=(255, 140, 140)),
}
# 충격 방사선 개수 (맞은 자리에서 퍼지는 선): 구간이 높을수록, 강화는 가장 많다. 추가 타격은 작게
IMPACT_RAYS = {'FADE': 4, 'NORMAL': 6, 'AWAKE': 8, 'CRITICAL': 10, 'OVERLOAD': 10, 'DEAD': 0, 'enhanced': 12}
IMPACT_RAYS_EXTRA = 3
FINISHER_SLASH = 'pipe-slash-finisher'     # 3타는 구간과 상관없이 금색 큰 궤적
# 주인공 몸 주위 오라 (반복 재생). 노멀(20~49%)은 없다. E 강화 중에는 구간 오라 위에 겹친다
AURA_BY_ZONE = {'FADE': 'aura-fade', 'AWAKE': 'aura-awake', 'CRITICAL': 'aura-critical'}
AURA_ENHANCED = 'aura-enhanced'
AURA_STUN = 'aura-stun'      # 오버로드 기절 중: 몸을 감싸고 튀는 전기 아크와 머리 위를 도는 별

# 소리
SOUND_ENABLED = False      # main이 오디오를 켠 뒤 True로 바꾼다 (테스트·창 없는 실행에서는 꺼져 있다)
SFX_VOLUME = 64            # 0~128
MUSIC_VOLUME = 44          # 0~128 (효과음보다 작게 깔린다)

# 개발용
DEBUG = False
