"""캐릭터 동작 그림: 파일 규칙, 프레임 수, 발 기준점, 그리기.

동작마다 캔버스 크기가 달라서(공격 자세는 파이프 때문에 넓고, 사망은 누워서 길다) 그림마다 '발 기준점'을 따로 둔다.
기준점은 프레임 왼쪽 위에서 잰 (x, y)이며, 그릴 때 이 점을 캐릭터의 발 위치(x, y)에 맞춘다.
좌우 반전하면 기준점도 반대편으로 옮겨진다. 수치는 Codex 마감 도구(finish.json의 anchor)가 준 값이다.

파일 규칙: assets/sprites/unified/<세트 이름>_<번호>.png (번호는 1부터).
번호 0은 '정지 그림' 한 장(<이름>.png)이고 기준점은 가로 가운데, 발 아래 여백 1px이다.
"""
import assets

# 세트 이름 -> (프레임 수, 기준점 x, 기준점 y)
FRAMES = {
    # 주인공 N-09
    # 걷기 8장(Codex T17 v4b). 기준점 x는 피벗 33보다 3 앞(36): 머리가 대기 그림보다 3px 앞이라 걷기 시작할 때 튀지 않게
    # 달리기 8장·전환 5장(Codex T19: 출발 1·2, 멈춤 3·4, 방향 전환 5). 기준점 x는 Codex 피벗(벨트)보다 4 뒤: 대기 그림의 벨트가
    # 발 기준점보다 4px 앞이라, 대기 -> 출발 -> 달리기 -> 멈춤 -> 대기에서 벨트(허리)가 같은 자리에 있게 한다
    'n09_run': (8, 55, 128), 'n09_run_trans': (5, 51, 124),
    'n09_idle': (4, 21, 124), 'n09_walk': (8, 36, 126), 'n09_jump': (4, 48, 125), 'n09_hurt': (2, 41, 124),
    'n09_dash': (2, 40, 79), 'n09_plunge': (2, 58, 142), 'n09_death': (3, 68, 124),
    # 휘두르기 5장(Codex T18): 1 젖힘, 2 휘두르는 중(새), 3 최대 신장(타격), 4 마무리, 5 회수(새). 1·3·4는 T15 그림 그대로
    'n09_swing_side': (5, 72, 149), 'n09_swing_up': (5, 82, 173), 'n09_swing_down': (5, 78, 149),
    'n09_swing_upfwd': (5, 76, 159), 'n09_swing_downfwd': (5, 75, 152),
    'n09_punch': (4, 36, 124),     # 맨손 자세 (Codex T05): 식칼 던지기·건틀릿 충전·발사 공용
    # 슬럼 폐인, 고철 투척병
    'enemy_slum_walk': (4, 43, 118), 'enemy_slum_attack': (3, 35, 119), 'enemy_slum_hurt': (1, 39, 118),
    'enemy_thrower_throw': (3, 41, 124), 'enemy_thrower_hurt': (1, 32, 124),
    # 사냥개, 간수 (Codex T12). 간수 걷기는 머리가 대기 그림보다 4px 앞에 있어 기준점을 3px 앞(43->46)으로 잡아 걷기 시작할 때 튀지 않게 한다
    'enemy_hound_run': (4, 60, 83), 'enemy_hound_bite': (3, 50, 82), 'enemy_hound_pounce': (2, 69, 84), 'enemy_hound_hurt': (1, 46, 82),
    'enemy_guard_walk': (4, 46, 136), 'enemy_guard_swing': (3, 57, 136), 'enemy_guard_heavy': (3, 68, 155),
    'enemy_guard_bash': (2, 65, 118), 'enemy_guard_hurt': (1, 58, 136),
    # 보스 크래셔
    'boss_crasher_idle': (2, 96, 205), 'boss_crasher_smash': (3, 94, 246), 'boss_crasher_charge': (2, 100, 174),
    'boss_crasher_leap': (3, 114, 210), 'boss_crasher_hurt': (1, 96, 196),
}
# 그림 안에서 발이 캔버스 바닥보다 떠 있게 그려진 프레임의 뜬 높이(px).
# 몸이 이미 공중에 있으므로 그림에서 또 띄우지 않도록 그만큼 기준점을 올려 잡는다.
LIFT = {('boss_crasher_leap', 2): 41}
STILL_FOOT_MARGIN = 1          # 정지 그림(번호 0)의 발 아래 투명 여백(px)

# 프레임마다 그리는 위치를 조금 옮기는 보정 (dx: 앞쪽 +, dy: 위쪽 +), 단위 px.
# AI가 장마다 따로 그린 그림은 몸통이 프레임마다 앞뒤로 흔들릴 수 있어, 재서 같은 자리에 맞춘다.
# (주인공 걷기는 T17 v4b에서 머리 흔들림이 1.4px 안이라 보정이 필요 없어졌다.)
SHIFT = {
    # 맨손 자세는 프레임마다 발 위치가 다르게 그려져 있어 발을 같은 자리에 맞춘다 (발 가운데 x: 43.5, 36, 25, 36.5)
    ('n09_punch', 1): (-7, 0), ('n09_punch', 3): (11, 0),
    ('enemy_slum_walk', 1): (1, 0), ('enemy_slum_walk', 2): (-2, 1), ('enemy_slum_walk', 3): (1, 2), ('enemy_slum_walk', 4): (0, 0),
}


def count(name):
    return FRAMES[name][0]


def path(name, n):
    """그림 파일 경로 (assets/ 기준). n이 0이면 정지 그림 한 장."""
    return f'sprites/unified/{name}_{n}.png' if n else f'sprites/unified/{name}.png'


def place(name, n, width, height, face_dir):
    """그림(width x height)을 발 위치에 맞추는 보정: (가운데 기준 가로 이동 dx, 발 아래로 내릴 높이 foot)."""
    if n == 0:
        return 0, STILL_FOOT_MARGIN
    _, px, py = FRAMES[name]
    py -= LIFT.get((name, n), 0)
    if face_dir < 0:                      # 좌우 반전하면 기준점이 반대편으로 간다
        px = width - 1 - px
    sdx, sdy = SHIFT.get((name, n), (0, 0))
    return width // 2 - px + (sdx if face_dir >= 0 else -sdx), height - py - sdy


def draw(name, n, x, y, face_dir=1, tint=None, alpha=1.0):
    """세트 name의 n번 그림을 발 위치 (x, y)에 그린다. tint(색 곱)와 alpha는 잔상·번쩍임용."""
    img = assets.image(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    flip = 'h' if face_dir < 0 else ''
    if tint is None and alpha >= 1.0:
        assets.draw_image(img, x + dx, y - foot, flip)
    else:
        assets.draw_image_tinted(img, x + dx, y - foot, flip, tint or (255, 255, 255), alpha)
