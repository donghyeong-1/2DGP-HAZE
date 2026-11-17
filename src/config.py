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
PLAYER_FRAMES = {'n09_idle': (4, 21, 124), 'n09_hurt': (2, 41, 124), 'n09_jump': (4, 48, 125), 'n09_walk': (4, 37, 124),
                 'n09_swing_side': (3, 53, 136), 'n09_swing_up': (3, 64, 165), 'n09_swing_down': (3, 30, 140),
                 'n09_swing_upfwd': (3, 51, 128), 'n09_swing_downfwd': (3, 47, 127)}
PLAYER_FRAMES.update({'n09_dash': (2, 40, 79), 'n09_plunge': (2, 58, 142), 'n09_death': (3, 68, 124)})
DASH_FRAME_TIME = 0.07   # 대시 자세 두 프레임이 바뀌는 간격(초)
PLUNGE_POSE_TIME = 0.5   # 내려찍기 자세를 보여 주는 시간(초)
DEATH_FRAME_TIMES = (0.2, 0.45)   # 사망 프레임이 2번, 3번으로 넘어가는 시각(초). 3번(엎어짐)은 계속 유지
DEATH_SCREEN_DELAY = 1.3   # 사망한 뒤 쓰러지는 모습을 보여 주고 사망 화면으로 넘어가기까지의 시간(초)
SWING_TIME = 0.27        # 공격 자세(준비·타격·마무리 3프레임)를 보여 주는 시간(초)
IDLE_FRAME_TIME = 0.25   # 숨쉬는 대기 프레임 한 장의 시간(초)
JUMP_RISE_VY = 350.0     # 점프 프레임: vy가 이 값보다 크면 상승, 작고 -이 값보다 크면 정점, 그 아래면 하강
WALK_FRAMES = 4          # 걷기 프레임 수 (assets/sprites/unified/n09_walk_1~4.png, 발 기준점 x=37)
WALK_PIVOT_X = 37        # 걷기 프레임에서 발 중앙의 x (캔버스 86px 기준)
WALK_FRAME_PX = 56.0     # 걷기 프레임 한 장이 지나가는 이동 거리(px). 달리는 속도에 맞춰 발이 바닥을 미끄러지지 않게 한다
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
OVERLOAD_DAMAGE_RATIO = 0.20
OVERLOAD_STUN = 1.5
OVERLOAD_RESET = 30
OVERLOAD_FLASH = 0.35        # 오버로드 순간 화면 전체가 하얗게 번쩍이는 시간(초)
OVERLOAD_HIT_STOP = 0.16     # 폭발 순간 화면이 멈추는 시간(초)

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
# sight_dy: 이 높이 차(px) 안에 플레이어가 있어야 발견, reach_dy: 이 높이 차 안일 때만 공격(투척병은 같은 층만 노린다)
# leap: 위층의 플레이어를 쫓아 뛰어오르는 속도(0이면 못 뛴다)
ENEMY_STATS = {
    'slum': dict(hp=60, hb=(42, 102), speed=210.0, sight=700, sight_dy=480, attack_range=95, reach_dy=200, damage=12,
                 windup=0.45, attack_time=0.15, cooldown=1.1, gain_on_hit=0, sprite='enemy_slum_idle',
                 leap=1250.0,
                 frames=dict(walk='enemy_slum_walk', attack='enemy_slum_attack', hurt='enemy_slum_hurt')),
    'thrower': dict(hp=45, hb=(48, 108), speed=0.0, sight=900, sight_dy=130, attack_range=820, reach_dy=130, damage=10,
                    windup=0.55, attack_time=0.1, cooldown=2.2, gain_on_hit=0, sprite='enemy_thrower_idle',
                    projectile_speed=620.0, leap=0.0,
                    frames=dict(attack='enemy_thrower_throw', hurt='enemy_thrower_hurt')),
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
ENEMY_WALK_FRAME_PX = 44.0       # 적 걷기 프레임 한 장이 지나가는 이동 거리(px)
BOSS_LEAP_TIME = 0.8             # 보스 도약 체공 시간(초). 기둥·벽 뒤에 숨은 플레이어에게 넘어가 내려찍는다
BOSS_LEAP_SPEED_CAP = 760.0
BOSS_LAND_RADIUS = 210           # 도약 착지 충격 반경(px)
BOSS_LAND_DAMAGE = 20

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
SHARDS_PER_KILL = {'slum': 1, 'thrower': 2, 'crasher': 10}

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
                   damage_color=(230, 190, 255))
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

# 개발용
DEBUG = False
