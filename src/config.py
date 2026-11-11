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

# 대시
DASH_SPEED = 2400.0        # px/s (거리 약 360px)
DASH_TIME = 0.15           # 초
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
SPRITE_FOOT_MARGIN = 1     # hibit 스프라이트의 발 아래 투명 여백(px). 그릴 때 이만큼 내려 바닥에 붙인다
PLAYER_HB_W = 42           # 충돌 박스 너비
PLAYER_HB_H = 108          # 충돌 박스 높이 (스프라이트 키 123px의 약 88%)
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

# 소리
SOUND_ENABLED = False      # main이 오디오를 켠 뒤 True로 바꾼다 (테스트·창 없는 실행에서는 꺼져 있다)
SFX_VOLUME = 64            # 0~128

# 개발용
DEBUG = False
