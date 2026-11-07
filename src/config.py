"""게임 전체 수치 상수. 밸런싱은 이 파일만 고친다. (pico2d에 의존하지 않는다)"""

# 화면
SCREEN_W = 1280
SCREEN_H = 720
TILE = 40
ROOM_COLS = SCREEN_W // TILE  # 32
ROOM_ROWS = SCREEN_H // TILE  # 18
# 픽셀 아트는 확대·축소하지 않고 1배(원본 크기)로만 그린다. docs/pixel_rules.md 참고

# 물리
GRAVITY = 2400.0           # px/s^2
MAX_FALL_SPEED = 1100.0    # px/s
RUN_SPEED = 320.0          # px/s
JUMP_SPEED = 850.0         # px/s (한 번에 약 150px)
MAX_JUMPS = 2              # 2단 점프
DROP_TIME = 0.2            # S+Space 로 얇은 바닥을 무시하는 시간(초)

# 대시
DASH_SPEED = 1600.0        # px/s
DASH_TIME = 0.15           # 초
DASH_INVULN = 0.25         # 초 (무적 시간)
DASH_SLOTS_BASE = 2
DASH_SLOTS_MAX = 5
DASH_RECHARGE = 1.5        # 슬롯 한 칸 충전 시간(초)

# 플레이어
PLAYER_HP = 100
PLAYER_HB_W = 28           # 충돌 박스 너비
PLAYER_HB_H = 72           # 충돌 박스 높이
HIT_STUN = 0.25            # 피격 경직(초)

# 헤이즈 게이지
GAUGE_START = 30
GAUGE_CAP = 100
GAUGE_CAP_MAX = 160
GAUGE_DECAY_INTERVAL = 3.0  # 초마다
GAUGE_DECAY_AMOUNT = 1
HIGH_HAZE_INTERVAL = 2.0    # 고농도 방: 감소 대신 상승
HIGH_HAZE_AMOUNT = 1
GAIN_HIT = 3
GAIN_KILL = 8
GAIN_BOSS_HIT = 2
LOSS_DAMAGED = -5
ZONE_FADE_MAX = 20          # value < 20 이면 페이드 (1~19)
ZONE_NORMAL_MAX = 50        # value < 50 이면 노멀 (20~49), 각성은 50부터 (절대값)
CRITICAL_MARGIN = 10        # 위험은 cap-10 이상 (한계에 따라 움직임)
ENHANCE_COST = 25
ENHANCE_FLOOR = 5           # 사용 후 최소 이만큼 남아야 한다 (사용 가능 하한 = COST + FLOOR = 30)
ENHANCE_TIME = 8.0
OVERLOAD_DAMAGE_RATIO = 0.20
OVERLOAD_STUN = 1.5
OVERLOAD_RESET = 30

# 구간별 배율 (공격, 속도)
MULT_FADE = (0.8, 0.8)
MULT_NORMAL = (1.0, 1.0)
MULT_AWAKE = (1.5, 1.25)
MULT_CRITICAL = (1.8, 1.35)

# 건틀릿
GAUNTLET_DRAIN = 10.0       # 초당 감소
GAUNTLET_FLOOR = 5          # 이 아래로는 내려가지 않음

# 개발용
DEBUG = False
