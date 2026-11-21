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
    'n09_punch': (4, 36, 124),     # 맨손 자세 (Codex T05): 무기 전용 자세가 없을 때만 (T26 이후 거의 안 씀)
    # 무기 전용 자세 (Codex T26): 식칼 당김 -> 뿌림 -> 흘림, 건틀릿 충전 -> 발사 -> 회수 -> 공중 하향, 사슬 돌림 -> 던짐 -> 당김
    'n09_knife': (3, 39, 121), 'n09_gauntlet': (4, 44, 117), 'n09_chain': (3, 59, 128),
    'n09_ult': (2, 64, 130),       # 궁극기 시전 (Codex T23): 모으기 -> 해방
    # 철파이프 2단계 강화 (Codex T24, 캔버스 171x168, 발 기준점 (70,161)): 올려베기 3장 -> 내려찍기 3장
    'n09_s2rise': (3, 70, 161), 'n09_s2slam': (3, 70, 161),
    # 슬럼 폐인, 고철 투척병
    'enemy_slum_walk': (4, 43, 118), 'enemy_slum_attack': (3, 35, 119), 'enemy_slum_hurt': (2, 39, 118),
    'enemy_thrower_throw': (3, 41, 124), 'enemy_thrower_hurt': (2, 32, 124),
    # Codex T30 (캔버스 105x131, 발 기준점 (62,127)): 걷기 4장(가까운 발 -> 먼 발), 플레이어를 본 채 뒷걸음 2장
    'enemy_thrower_walk': (4, 62, 127), 'enemy_thrower_back': (2, 62, 127),
    # 사냥개, 간수 (Codex T12). 간수 걷기는 머리가 대기 그림보다 4px 앞에 있어 기준점을 3px 앞(43->46)으로 잡아 걷기 시작할 때 튀지 않게 한다
    'enemy_hound_run': (4, 60, 83), 'enemy_hound_bite': (3, 50, 82), 'enemy_hound_pounce': (2, 69, 84), 'enemy_hound_hurt': (2, 46, 82),
    'enemy_guard_walk': (4, 46, 136), 'enemy_guard_swing': (3, 57, 136), 'enemy_guard_heavy': (3, 68, 155),
    'enemy_guard_bash': (2, 65, 118), 'enemy_guard_hurt': (2, 58, 136),
    # 보스 크래셔
    'boss_crasher_idle': (2, 96, 205), 'boss_crasher_smash': (3, 94, 246), 'boss_crasher_charge': (2, 100, 174),
    'boss_crasher_leap': (3, 114, 210), 'boss_crasher_hurt': (1, 96, 196),
    'boss_crasher_walk': (4, 107, 197), 'boss_crasher_death': (2, 82, 148),   # Codex T27: 무거운 걸음 4장(발 교대), 무릎 -> 엎어짐
    # 최종 보스 아크 (Codex T20). 기준점은 Codex 보고서 값(허리 기준 x, 밑창 아래 줄 y). 보스 코드는 아직 없다(스테이지 3은 임시로 크래셔)
    'boss_ark_idle': (2, 57, 160), 'boss_ark_walk': (4, 67, 160), 'boss_ark_hurt': (1, 57, 156),
    'boss_ark_barrage': (2, 71, 161), 'boss_ark_slash': (3, 77, 161), 'boss_ark_absorb': (2, 79, 164),
    'boss_ark_overcharge': (2, 74, 164), 'boss_ark_field': (2, 67, 156),
    'boss_ark_vanish': (1, 40, 160), 'boss_ark_appear': (1, 60, 142),
    'boss_ark_phase': (1, 64, 177), 'boss_ark_death': (2, 76, 110),
}
# 그림 안에서 발이 캔버스 바닥보다 떠 있게 그려진 프레임의 뜬 높이(px).
# 몸이 이미 공중에 있으므로 그림에서 또 띄우지 않도록 그만큼 기준점을 올려 잡는다.
LIFT = {('boss_crasher_leap', 2): 41}
STILL_FOOT_MARGIN = 1          # 정지 그림(번호 0)의 발 아래 투명 여백(px)

# 프레임마다 그리는 위치를 조금 옮기는 보정 (dx: 앞쪽 +, dy: 위쪽 +), 단위 px.
# AI가 장마다 따로 그린 그림은 몸통이 프레임마다 앞뒤로 흔들릴 수 있어, 재서 같은 자리에 맞춘다.
# (주인공 걷기는 T17 v4b에서 머리 흔들림이 1.4px 안이라 보정이 필요 없어졌다.)
# 일반 적 피격 2장째·쓰러짐 3장 (Codex T25): 캔버스가 피격 1장째와 달라 그림마다 기준점을 따로 둔다
ENEMY_T25_ANCHOR = {'slum': (68, 109), 'thrower': (64, 109), 'guard': (69, 135), 'hound': (65, 87)}
for _k, (_x, _y) in ENEMY_T25_ANCHOR.items():
    FRAMES[f'enemy_{_k}_death'] = (3, _x, _y)
# (이름, 번호) -> 이 그림만의 기준점 (FRAMES의 세트 기준점 대신)
FRAME_ANCHOR = {(f'enemy_{_k}_hurt', 2): _a for _k, _a in ENEMY_T25_ANCHOR.items()}

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
    px, py = FRAME_ANCHOR.get((name, n), (px, py))
    py -= LIFT.get((name, n), 0)
    if face_dir < 0:                      # 좌우 반전하면 기준점이 반대편으로 간다
        px = width - 1 - px
    sdx, sdy = SHIFT.get((name, n), (0, 0))
    return width // 2 - px + (sdx if face_dir >= 0 else -sdx), height - py - sdy


def draw_glow(name, n, x, y, face_dir, color):
    """그림의 흰 실루엣을 색으로 물들여 상하좌우 3px씩 비켜 네 번 그린다 = 색 테두리 (정예 표시). 본 그림은 그 위에."""
    img = assets.silhouette(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    flip = 'h' if face_dir < 0 else ''
    for ox, oy in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        assets.draw_image_tinted(img, x + dx + ox, y - foot + oy, flip, color, 0.85)


def draw_white(name, n, x, y, face_dir=1):
    """같은 그림을 '더하기' 섞기로 한 번 더 그려 하얗게 번쩍이게 한다 (맞은 순간)."""
    img = assets.image(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    assets.draw_image_added(img, x + dx, y - foot, 'h' if face_dir < 0 else '')


def draw(name, n, x, y, face_dir=1, tint=None, alpha=1.0):
    """세트 name의 n번 그림을 발 위치 (x, y)에 그린다. tint(색 곱)와 alpha는 잔상·번쩍임용."""
    img = assets.image(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    flip = 'h' if face_dir < 0 else ''
    if tint is None and alpha >= 1.0:
        assets.draw_image(img, x + dx, y - foot, flip)
    else:
        assets.draw_image_tinted(img, x + dx, y - foot, flip, tint or (255, 255, 255), alpha)
