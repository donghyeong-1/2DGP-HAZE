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
    # 공장 새 적 (Codex T36·T37, 11/22). 드론 캔버스 160x136, 몸통 중심 (73,65): 히트박스 가운데(발 위 32)에 맞춰 기준점 y=97.
    # 잔해 2장째는 바닥에 누운 그림(맨 아래 불투명 줄 112)이라 기준점을 따로 (FRAME_ANCHOR). 수레 캔버스 160x122, 바닥 (76,104)
    'enemy_drone_fly': (4, 73, 97), 'enemy_drone_aim': (2, 73, 97), 'enemy_drone_fire': (3, 73, 97),
    'enemy_drone_hurt': (2, 73, 97), 'enemy_drone_wreck': (2, 73, 97),
    'enemy_cart_roll': (4, 76, 104), 'enemy_cart_arm': (3, 76, 104), 'enemy_cart_hurt': (2, 76, 104),
    'enemy_cart_wreck': (2, 76, 104),
    # 탑·슬럼 새 적 (Codex T38~T42, 11/22). 눈: 캔버스 150x140, 몸통 중심 (78,70)을 히트박스(높이 96) 가운데에 맞춰 y=118.
    # 기사: 250x176, 골반 x 바닥 (107,155). 망령: 192x156, 몸통 (82,63)을 히트박스(높이 100) 가운데에 맞춰 y=113.
    # 쥐: 124x68, (68,53). 무당: 192x188, (73,162)
    'enemy_eye_idle': (2, 78, 118), 'enemy_eye_charge': (3, 78, 118), 'enemy_eye_fire': (1, 78, 118),
    'enemy_eye_hurt': (2, 78, 118), 'enemy_eye_death': (2, 78, 118),
    'enemy_knight_idle': (2, 107, 155), 'enemy_knight_walk': (4, 107, 155), 'enemy_knight_vanish': (2, 107, 155),
    'enemy_knight_appear': (2, 107, 155), 'enemy_knight_slash': (3, 107, 155), 'enemy_knight_hurt': (1, 107, 155),
    'enemy_wraith_float': (4, 82, 113), 'enemy_wraith_grab': (3, 82, 113), 'enemy_wraith_hurt': (1, 82, 113),
    'enemy_wraith_death': (2, 82, 113),
    'enemy_rat_run': (4, 68, 53), 'enemy_rat_bite': (2, 68, 53), 'enemy_rat_hurt': (1, 68, 53), 'enemy_rat_death': (2, 68, 53),
    'enemy_shaman_idle': (2, 73, 162), 'enemy_shaman_walk': (4, 73, 162), 'enemy_shaman_cast': (3, 73, 162),
    'enemy_shaman_hurt': (2, 73, 162),
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
    # 최종 보스 헤이즈 심장 본체 (Codex T45, 캔버스 900x560). 기준점 y=462는 열린 핵 중심(행 312)이 히트박스 가운데(발 위 150)에 오게 한 값
    'heart_core': (3, 450, 462), 'heart_core_hurt': (1, 450, 462), 'heart_core_dying': (2, 450, 462),
    # 헤이즈 심장 기계 손 (Codex T46, 캔버스 260x260, 손 중심 (130,130), 오른손 그림 -> 왼손은 좌우 반전).
    # 떠 있는 자세는 손 중심이 히트박스(높이 110) 가운데에 오게 (130,185). 손바닥은 결정(광선 시작점)이 히트박스 아래에 (130,130).
    # 바닥에 닿는 컷(내려친 주먹·기절)은 FRAME_ANCHOR에서 그림 맨 아래가 바닥에 오게 따로 잡는다
    'heart_hand_idle': (2, 130, 185), 'heart_hand_fist': (2, 130, 185), 'heart_hand_palm': (2, 130, 130),
    'heart_hand_stun': (2, 130, 250),
}
# 그림 안에서 발이 캔버스 바닥보다 떠 있게 그려진 프레임의 뜬 높이(px).
# 몸이 이미 공중에 있으므로 그림에서 또 띄우지 않도록 그만큼 기준점을 올려 잡는다.
LIFT = {('boss_crasher_leap', 2): 41, ('enemy_rat_bite', 2): 5}
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
FRAME_ANCHOR[('enemy_drone_wreck', 2)] = (73, 113)
FRAME_ANCHOR[('heart_hand_fist', 2)] = (130, 208)      # 내려친 주먹: 아래 끝(78px)이 바닥에
FRAME_ANCHOR[('heart_hand_stun', 2)] = (130, 234)      # 기절 2: 아래 끝(104px)이 바닥에 (1은 120px -> 기본 250)

SHIFT = {
    # 맨손 자세는 프레임마다 발 위치가 다르게 그려져 있어 발을 같은 자리에 맞춘다 (발 가운데 x: 43.5, 36, 25, 36.5)
    ('n09_punch', 1): (-7, 0), ('n09_punch', 3): (11, 0),
    ('enemy_slum_walk', 1): (1, 0), ('enemy_slum_walk', 2): (-2, 1), ('enemy_slum_walk', 3): (1, 2), ('enemy_slum_walk', 4): (0, 0),
}


# v6 새 주인공 (PixelLab 62px를 2배, tools/apply_pixellab_hero.py가 hero6.json에 세트를 쓴다, docs/plan_v6.md).
# 플레이어 코드는 그대로 n09_* 이름을 고르고, 새 그림이 있는 동작만 여기서 hero6_*로 바꿔 그린다(SKIN).
# 새 그림은 PixelLab이 1px(화면 2px) 검은 테두리를 이미 그려 두어, 실행 중 테두리는 밝은 선만 화면 2px로 두른다.
def _load_hero6():
    import json
    import os
    p = os.path.join(assets.ASSET_DIR, 'sprites', 'unified', 'hero6.json')
    if not os.path.exists(p):
        return {}
    with open(p, encoding='utf-8') as fp:
        return {k: tuple(v) for k, v in json.load(fp).items()}


HERO6 = _load_hero6()
FRAMES.update(HERO6)
# 기존 동작 이름 -> 새 세트. 위 대각·아래 대각 휘두르기는 올려치기·내려찍기 그림을 같이 쓴다.
# 아직 새 그림이 없는 것(식칼·건틀릿·사슬 자세, 맨손, 궁극기)은 기존 그림 그대로.
SKIN_PAIRS = (
    ('n09_idle', 'hero6_idle'), ('n09_run', 'hero6_run'), ('n09_run_trans', 'hero6_run_trans'),
    ('n09_jump', 'hero6_jump'), ('n09_dash', 'hero6_dash'),
    ('n09_swing_side', 'hero6_swing_side'), ('n09_swing_up', 'hero6_swing_up'), ('n09_swing_upfwd', 'hero6_swing_up'),
    ('n09_swing_down', 'hero6_swing_down'), ('n09_swing_downfwd', 'hero6_swing_down'),
    ('n09_s2rise', 'hero6_s2rise'), ('n09_s2slam', 'hero6_s2slam'), ('n09_plunge', 'hero6_plunge'),
    ('n09_hurt', 'hero6_hurt'), ('n09_death', 'hero6_death'),
    # 공격 v3 (2026-11-24): 기존 그림이 없던 새 동작. 플레이어가 swing_anim으로 고른다 (그림이 없으면 n09_swing_<방향>)
    ('n09_swing_side2', 'hero6_swing_side2'), ('n09_swing_side3', 'hero6_swing_side3'),
    ('n09_air1', 'hero6_air1'), ('n09_air2', 'hero6_air2'), ('n09_airup', 'hero6_airup'),
    ('n09_dashcut', 'hero6_dashcut'), ('n09_e1', 'hero6_e1'),
    ('n09_pistol', 'hero6_pistol'),                       # v7 쌍권총 겨눔 (PixelLab base_pistols)
)
SKIN = {old: new for old, new in SKIN_PAIRS if new in HERO6}


def _load_skins():
    """v6 다른 캐릭터(적·보스): tools/apply_pixellab_char.py가 쓰는 skin_<캐릭터>.json.
    {"frames": {새 세트: [장수, 기준점 x, y]}, "skin": {기존 이름: 새 세트}}. 기존 이름 그대로 고르면 새 그림이 그려진다."""
    import glob
    import json
    import os
    frames, skin = {}, {}
    for p in sorted(glob.glob(os.path.join(assets.ASSET_DIR, 'sprites', 'unified', 'skin_*.json'))):
        with open(p, encoding='utf-8') as fp:
            data = json.load(fp)
        frames.update({k: tuple(v) for k, v in data['frames'].items()})
        skin.update({old: new for old, new in data['skin'].items() if new in data['frames']})
    return frames, skin


SKIN_FRAMES, _skin_more = _load_skins()
FRAMES.update(SKIN_FRAMES)
SKIN.update(_skin_more)
OWN_OUTLINE = set(HERO6) | set(SKIN_FRAMES)   # 테두리를 그림에 이미 가진 세트 (PixelLab 그림)
OWN_RIM = 2                       # 그런 세트에 두를 밝은 선 두께 (화면 px = 원본 1px)


def resolve(name, n):
    """새 주인공 그림이 있는 동작이면 (hero6 세트, 번호)로 바꾼다. 정지 그림(0)은 1번으로."""
    new = SKIN.get(name)
    if new is None:
        return name, n
    return new, (n - 1) % FRAMES[new][0] + 1 if n else 1


def count(name):
    return FRAMES[SKIN.get(name, name)][0]


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


def draw_glow(name, n, x, y, face_dir, color, width=3, alpha=0.85):
    """그림의 흰 실루엣을 색으로 물들여 상하좌우 width px씩 비켜 네 번 그린다 = 색 테두리 (정예 3px, 모든 적 얇게 2px).
    본 그림은 그 위에."""
    name, n = resolve(name, n)
    img = assets.silhouette(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    flip = 'h' if face_dir < 0 else ''
    width += OUTLINE_WIDTH + RIM_WIDTH         # 검은·밝은 테두리 바깥에 색이 보이게
    for ox, oy in ((width, 0), (-width, 0), (0, width), (0, -width)):
        assets.draw_image_tinted(img, x + dx + ox, y - foot + oy, flip, color, alpha)


def draw_silhouette(name, n, x, y, face_dir, color, alpha):
    """그림 모양의 흰 실루엣을 color로 물들여 한 번 그린다 (잔상용). v7 새 주인공은 옷이 어두워서
    그림 색에 곱하면(tint) 검은 덩어리가 되므로, 실루엣에 색을 입힌다."""
    name, n = resolve(name, n)
    img = assets.silhouette(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    assets.draw_image_tinted(img, x + dx, y - foot, 'h' if face_dir < 0 else '', color, alpha)


def draw_white(name, n, x, y, face_dir=1):
    """같은 그림을 '더하기' 섞기로 한 번 더 그려 하얗게 번쩍이게 한다 (맞은 순간)."""
    name, n = resolve(name, n)
    img = assets.image(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    assets.draw_image_added(img, x + dx, y - foot, 'h' if face_dir < 0 else '')


OUTLINE_COLOR = (6, 8, 14)       # 캐릭터 검은 테두리 (던그리드식, 순수 검정보다 살짝 푸른 검정)
OUTLINE_WIDTH = 2                # 검은 테두리 두께 (px)
RIM_WIDTH = 1                    # 그 바깥 밝은 선 (어두운 방에서 윤곽이 보이게)
RIM_COLOR = (110, 140, 185)


def warm_outlines(names):
    """세트들의 모든 그림의 테두리 판을 미리 만든다 (큰 보스가 처음 그려질 때 멈칫하지 않게)."""
    for name in names:
        for n in range(1, count(name) + 1):
            assets.outline_image(path(name, n), OUTLINE_WIDTH, OUTLINE_COLOR, RIM_WIDTH, RIM_COLOR)


def draw_outline(name, n, x, y, face_dir, alpha=1.0):
    """그림 모양을 OUTLINE_WIDTH px 부풀린 검은 판을 본 그림 아래에 깐다 (판은 사방 여백이 붙어 있어 y를 그만큼 내린다)."""
    black, rim = (0, OWN_RIM) if name in OWN_OUTLINE else (OUTLINE_WIDTH, RIM_WIDTH)
    img = assets.outline_image(path(name, n), black, OUTLINE_COLOR, rim, RIM_COLOR)
    orig = assets.image(path(name, n))
    dx, foot = place(name, n, orig.w, orig.h, face_dir)
    assets.draw_image_tinted(img, x + dx, y - foot - black - rim, 'h' if face_dir < 0 else '', (255, 255, 255), alpha)


def draw(name, n, x, y, face_dir=1, tint=None, alpha=1.0, outline=True):
    """세트 name의 n번 그림을 발 위치 (x, y)에 그린다. tint(색 곱)와 alpha는 잔상·번쩍임용.
    outline: 검은 테두리와 밝은 선을 먼저 깐다 (잔상은 끈다)."""
    name, n = resolve(name, n)
    img = assets.image(path(name, n))
    dx, foot = place(name, n, img.w, img.h, face_dir)
    flip = 'h' if face_dir < 0 else ''
    if outline:
        draw_outline(name, n, x, y, face_dir, alpha)
    if tint is None and alpha >= 1.0:
        assets.draw_image(img, x + dx, y - foot, flip)
    else:
        assets.draw_image_tinted(img, x + dx, y - foot, flip, tint or (255, 255, 255), alpha)
