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
JUMP_BUFFER = 0.12         # 착지 직전에 누른 점프를 기억했다가 착지하면 뛰는 시간(초)

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

# 무기: 철파이프 (충전형, 3연타. 3타째에 게이지가 더 오른다)
PIPE_DAMAGE = 20
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
ENEMY_STATS = {
    'slum': dict(hp=60, hb=(42, 102), speed=210.0, sight=620, attack_range=95, damage=12,
                 windup=0.45, attack_time=0.15, cooldown=1.1, gain_on_hit=0, sprite='enemy_slum_idle.png'),
    'thrower': dict(hp=45, hb=(48, 108), speed=0.0, sight=900, attack_range=820, damage=10,
                    windup=0.55, attack_time=0.1, cooldown=2.2, gain_on_hit=0, sprite='enemy_thrower_idle.png',
                    projectile_speed=620.0),
}
# 헤이즈 조각 (재화). 적을 처치하면 떨어뜨리고, 정비방 업그레이드에 쓴다 (정비방은 3주차)
SHARDS_PER_KILL = {'slum': 1, 'thrower': 2}

# E 무기 강화: 게이지 ENHANCE_COST를 쓰고 ENHANCE_TIME초 동안 파이프가 강해진다
ENHANCE_DAMAGE_MULT = 1.5
ENHANCE_REACH_MULT = 1.35
ENHANCE_ARC_BONUS_DEG = 15
ENHANCE_BLAST_RADIUS = 170     # 강화 무기로 처치한 적은 작은 안개 폭발을 일으킨다
ENHANCE_BLAST_DAMAGE = 25

ENEMY_HIT_FLASH = 0.10       # 맞았을 때 붉게 번쩍이는 시간(초)
ENEMY_KNOCKBACK = 260.0      # 맞았을 때 밀려나는 속도(px/s)
ENEMY_SPAWN_ORDER = ('slum', 'thrower')  # 방의 E 칸에 순서대로 배정한다 (스테이지 데이터가 생기기 전 임시)
PROJECTILE_HB = (30, 18)

# 화면 효과·UI 크기. 1920x1080에서는 원본 크기 효과와 14px 글자가 작아서, 정수 배율(최근접)로만 키운다.
# docs/pixel_rules.md "정수 배율 예외" 참고. 월드 스프라이트와 타일은 1배 그대로다.
EFFECT_SCALE = 2           # 타격 불꽃·휘두르기·연기 등 이펙트 시트 배율
FONT_SCALE = 2             # 글자는 14px/11px 원본의 정수 배(28/22px)로만 그린다. 큰 글자는 3배(42px)
DAMAGE_COLOR = (255, 238, 150)
DAMAGE_COLOR_FINISHER = (255, 170, 80)
DAMAGE_COLOR_ENHANCED = (130, 235, 225)

# 소리
SOUND_ENABLED = False      # main이 오디오를 켠 뒤 True로 바꾼다 (테스트·창 없는 실행에서는 꺼져 있다)
SFX_VOLUME = 64            # 0~128

# 개발용
DEBUG = False
