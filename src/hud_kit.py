"""UI 부품 그리기: 9칸 판, 막대, 그림자 글자, 버튼. HUD(ui.py)와 메뉴(타이틀·일시정지·설정)가 함께 쓴다.

2026-11-25 UI 개편(C안 결정형): 그림은 Gemini G06 부품 시트를 tools/apply_ui_parts.py가 구운 assets/ui/uc_*.png.
판은 uc_kit_<종류>.png를 9칸으로 나눠 그린다: 네 모서리는 그대로,
네 변은 같은 무늬 조각을 길이만큼 이어 붙이고(늘이지 않는다), 가운데는 그 판의 속 색으로 채운다.
막대 속은 uc_fill_<색>_<높이>.png에서 필요한 너비만큼 잘라 쓴다. 모든 위치는 정수 픽셀(도트 2px 격자에 맞게 짝수)이다.
"""
import assets
import config

ART = 'ui/uc_'                 # 예전(결정형) 부품 그림 접두 (assets/ui/uc_*.png). 지금 스킨의 접두는 prefix()
# 2026-11-26 UI 3차 '교도소 철판': config.UI_SKIN
#   'plate'      PixelLab 철판 (assets/ui/upx_*.png, tools/apply_ui_plate.py). PixelLab 판이 없는 부품은 코드 철판(up_*)을 쓴다
#   'plate_code' 코드로 그린 철판 (assets/ui/up_*.png, tools/make_ui_plate.py)
#   'crystal'    예전 결정형 (uc_*, Gemini G06)
# 2026-11-27 UI 컨셉 확정 'mist': 타이틀 = B 감시 단말, 증강 선택 = A 안개 미니멀 (um_*, tools/make_ui_mist.py).
#   플레이 중 HUD는 11/27 H1부터 '가는 선 + 어두운 바탕'(아래 hud_* 함수). 그 밖의 화면(일시정지·설정·상점·결과)은 아직 'plate'와 같다 (upx_*, 없으면 up_)
# 이름·크기가 같아 접두만 바꿔 끼운다. 예전 그림은 지우지 않는다.
SKIN_PREFIX = {'mist': 'upx_', 'plate': 'upx_', 'plate_code': 'up_', 'crystal': 'uc_'}
FALLBACK = {'mist': 'up_', 'plate': 'up_'}                  # 이 스킨에 없는 부품은 이 접두로
_exists = {}


def skin():
    s = getattr(config, 'UI_SKIN', 'mist')
    return s if s in SKIN_PREFIX else 'mist'


def is_plate():
    """철판 계열 스킨인가 (PixelLab·코드 둘 다: 노란 꺾쇠, 청록은 헤이즈에만, 결정 장식 없음). 'mist'도 타이틀·증강·HUD 밖은 철판."""
    return skin() in ('mist', 'plate', 'plate_code')


def is_pixellab_plate():
    """PixelLab 철판 부품(upx_*)을 쓰는 스킨인가."""
    return skin() in ('mist', 'plate')


def is_mist():
    """2026-11-27 확정 컨셉: 타이틀은 감시 단말, 증강 선택은 안개 미니멀 (um_*)."""
    return skin() == 'mist'


WEAPON_STYLES = ('flat', 'a', 'b', 'c')


def weapon_style():
    """HUD 오른쪽 아래 무기·E 패널 시안 (2026-11-27 W1). mist 스킨에서만 config.HUD_WEAPON_STYLE을 따르고, 다른 스킨은 늘 'flat'."""
    style = getattr(config, 'HUD_WEAPON_STYLE', 'flat')
    return style if is_mist() and style in WEAPON_STYLES else 'flat'


def prefix():
    return SKIN_PREFIX[skin()]


def _has(rel):
    if rel not in _exists:
        import os
        _exists[rel] = os.path.exists(os.path.join(assets.ASSET_DIR, rel))
    return _exists[rel]


def art(rest):
    """지금 스킨의 부품 경로: art('kit_panel.png') -> 'ui/upx_kit_panel.png' (plate, 없으면 up_) / 'ui/up_...' (plate_code) /
    'ui/uc_...' (crystal)."""
    rel = f'ui/{prefix()}{rest}'
    fb = FALLBACK.get(skin())
    if fb and not _has(rel):
        return f'ui/{fb}{rest}'
    return rel


def part_name(name):
    """'uc_<부품>' 이름을 지금 스킨의 이름으로 (그 밖의 이름은 그대로)."""
    return art(name[3:] + '.png')[3:-4] if name.startswith('uc_') else name


# 판 종류 -> (그림 한 변 크기, 모서리 크기, 속 색). 크기는 스킨이 같고, 속 색만 스킨마다 다르다
KITS = {
    'panel': (96, 24, (13, 18, 31)),          # 큰 판: 사선 모서리, 흰 1점 선
    'plate': (48, 12, (13, 18, 31)),          # 작은 HUD 틀: 미니맵·칩·아이템 칸
    'frame': (16, 6, (13, 18, 31)),           # 얇은 막대 틀
    'slot': (80, 16, (13, 18, 31)),           # 무기 칸
    'slot_hot': (80, 16, (13, 18, 31)),       # 든 무기 칸: 흰·청록 이중 선 + 모서리 결정
    'key': (24, 8, (22, 30, 49)),             # 키캡
    'key_dim': (24, 8, (13, 18, 31)),
}
PLATE_WELL = {'key': (42, 48, 59)}                      # 철판 스킨의 속 색 (나머지는 면 색 #1d222b)
PLATE_FACE = (29, 34, 43)


def kit(kind):
    """(그림 한 변 크기, 모서리 크기, 속 색) — 지금 스킨 기준."""
    size, c, well = KITS[kind]
    if is_plate():
        well = PLATE_WELL.get(kind, PLATE_FACE)
    return size, c, well
FILL_HEIGHTS = (8, 12, 16, 20, 24)
SHADOW = (8, 11, 20)


def panel(kind, x, y, w, h):
    """왼쪽 아래 (x, y)부터 w x h 판을 그린다."""
    size, c, well = kit(kind)
    img = assets.image(art(f'kit_{kind}.png'))
    x, y, w, h = int(x), int(y), max(int(w), 2 * c), max(int(h), 2 * c)
    m = size - 2 * c                                       # 가운데 무늬 조각 길이
    assets.draw_rect_color(x + c, y + c, w - 2 * c, h - 2 * c, well)
    # 네 변: 무늬 조각을 이어 붙인다 (마지막 조각은 남은 길이만큼 잘라서)
    for along in range(0, w - 2 * c, m):
        seg = min(m, w - 2 * c - along)
        assets.draw_clip(img, c, size - c, seg, c, x + c + along, y + h - c)    # 위
        assets.draw_clip(img, c, 0, seg, c, x + c + along, y)                    # 아래
    for along in range(0, h - 2 * c, m):
        seg = min(m, h - 2 * c - along)
        assets.draw_clip(img, 0, c, c, seg, x, y + c + along)                    # 왼쪽
        assets.draw_clip(img, size - c, c, c, seg, x + w - c, y + c + along)     # 오른쪽
    # 네 모서리
    assets.draw_clip(img, 0, size - c, c, c, x, y + h - c)
    assets.draw_clip(img, size - c, size - c, c, c, x + w - c, y + h - c)
    assets.draw_clip(img, 0, 0, c, c, x, y)
    assets.draw_clip(img, size - c, 0, c, c, x + w - c, y)


def family_icon(fid, fam):
    """증강 갈래 아이콘 경로. 철판: 갈래마다 다른 그림 ui/up_mut_<갈래>.png (18개 + 저주) / 결정형: 예전 넷을 돌려쓴 fam['icon']."""
    return f'ui/up_mut_{fid}.png' if is_plate() else fam['icon']


EVENT_ICONS = {'ui/mut_tide.png': 'tide', 'ui/mut_bloom.png': 'bloom', 'ui/mut_ember.png': 'ember'}   # 헤이즈 샘 카드 (구간 갈래와 같은 뜻)


def event_icon(path):
    """이벤트 카드 아이콘: 철판이면 같은 뜻의 갈래 아이콘으로 (샘의 노멀 = 강화가 아니라 '가라앉히기'라 tide 그대로 둔다)."""
    if is_plate() and path in EVENT_ICONS:
        return f'ui/up_mut_{EVENT_ICONS[path]}.png'
    return path


def card_well():
    """카드·정보판 속 색 (철판 스킨은 면 색)."""
    return PLATE_FACE if is_plate() else (13, 18, 31)


YELLOW = (226, 178, 58)        # 경고 노랑: 철판 스킨에서 '지금 고른 것'
YELLOW_LO = (138, 102, 26)


def select_mark(x, y, w, h, color, L=44, t=6, o=10):
    """고른 카드·칸 표시. 결정형: 둘레를 color로 채운 테 / 철판: 네 귀퉁이 노란 꺾쇠(바깥 o px, 굵기 t px, 길이 L px)."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    if not is_plate():
        assets.draw_rect_color(x - 6, y - 6, w + 12, h + 12, color)
        return
    for cx, cy, sx, sy in ((x - o, y - o, 1, 1), (x + w + o, y - o, -1, 1), (x - o, y + h + o, 1, -1), (x + w + o, y + h + o, -1, -1)):
        hx = cx if sx > 0 else cx - L
        vy = cy if sy > 0 else cy - L
        bx = cx if sx > 0 else cx - t
        by = cy if sy > 0 else cy - t
        for (rx, ry, rw, rh) in ((hx, by, L, t), (bx, vy, t, L)):
            assets.draw_rect_color(rx - 2, ry - 2, rw + 4, rh + 4, (6, 7, 10))        # 어두운 윤곽
        for (rx, ry, rw, rh) in ((hx, by, L, t), (bx, vy, t, L)):
            assets.draw_rect_color(rx, ry, rw, rh, YELLOW)
            assets.draw_rect_color(rx, ry, rw, 2, YELLOW_LO)


def fill(color, x, y, w, h):
    """막대 속 무늬를 (x, y)부터 너비 w만큼. h는 FILL_HEIGHTS 중 하나."""
    w = int(w)
    if w <= 0:
        return
    img = assets.image(art(f'fill_{color}_{h}.png'))
    assets.draw_clip(img, 0, 0, min(w, img.w), h, int(x), int(y))


def bar(color, x, y, w, h, ratio, empty='empty'):
    """틀이 있는 막대: 틀(frame 판) 안에 빈 칸 무늬를 깔고 ratio만큼 색 무늬를 채운다."""
    panel('frame', x - 4, y - 4, w + 8, h + 8)
    fill(empty, x, y, w, h)
    fill(color, x, y, round(w * max(0.0, min(1.0, ratio))), h)


def icon(name, x, y):
    """assets/ui/<name>.png를 왼쪽 아래 (x, y)에 1배로 그린다. 'uc_' 부품은 지금 스킨의 것으로."""
    img = assets.image(f'ui/{part_name(name)}.png')
    assets.draw_image(img, int(x) + img.w // 2, int(y))
    return img.w, img.h


def tag(x, y, w):
    """이름표 띠(양끝이 육각으로 깎인 판, 높이 40)를 왼쪽 아래 (x, y)에 너비 w로. 양끝 16px은 그대로, 가운데는 이어 붙인다."""
    img = assets.image(art('tag.png'))
    cap, x, y, w = 16, int(x) // 2 * 2, int(y), max(int(w) // 2 * 2, 32)
    mid = img.w - 2 * cap
    for along in range(0, w - 2 * cap, mid):
        assets.draw_clip(img, cap, 0, min(mid, w - 2 * cap - along), img.h, x + cap + along, y)
    assets.draw_clip(img, 0, 0, cap, img.h, x, y)
    assets.draw_clip(img, img.w - cap, 0, cap, img.h, x + w - cap, y)


def strip(x, y, w):
    """고른 메뉴 띠(높이 44): 흰 윗선·청록 밑선, 오른쪽 아래 청록 모서리, 왼쪽에 결정 덩어리. 왼쪽 아래 (x, y), 너비 w."""
    img = assets.image(art('strip_hot.png'))
    left = 16 if is_pixellab_plate() else 2                   # PixelLab 띠는 왼쪽 끝에도 잘린 모서리가 있다
    right, x, y, w = 16, int(x) // 2 * 2, int(y) // 2 * 2, max(int(w) // 2 * 2, 40)
    mid = 64
    for along in range(0, w - left - right, mid):
        assets.draw_clip(img, left, 0, min(mid, w - left - right - along), img.h, x + left + along, y)
    assets.draw_clip(img, 0, 0, left, img.h, x, y)
    assets.draw_clip(img, img.w - right, 0, right, img.h, x + w - right, y)
    if not is_plate():                                    # 철판 띠는 결정 장식 없이 (경고 줄무늬가 끝에 있다)
        icon('uc_crystal', x - 22, y - 6)


def text(x, y, s, color, small=False, center=False, big=False, right=False):
    """그림자(오른쪽 아래 2px)가 있는 글자. 밝은 배경 위에서도 읽힌다. right면 x가 글자의 오른쪽 끝."""
    if right:
        x -= assets.text_width(s, small, big)
    assets.draw_text(x + 2, y - 2, s, SHADOW, small=small, center=center, big=big)
    assets.draw_text(x, y, s, color, small=small, center=center, big=big)


class Button:
    """메뉴 버튼: 판(평소 / 고름) + 가운데 글자. rect = (x, y, w, h)는 왼쪽 아래 기준."""

    def __init__(self, key, label, x, y, w=420, h=64):
        self.key, self.label = key, label
        self.x, self.y, self.w, self.h = x, y, w, h

    def contains(self, mx, my):
        return self.x <= mx < self.x + self.w and self.y <= my < self.y + self.h

    def draw(self, hot, label=None, left=False):
        """메뉴 항목 (11/22 메뉴 v3): 상자 없이 글자만. 고른 항목은 밝은 글자 + 앞에 헤이즈 조각 표시
        (게임 안 재화 아이콘을 그대로 써서, 흔한 화살표·테두리 대신 이 게임의 표시로)."""
        s = label or self.label
        color = (242, 246, 250) if hot else (128, 140, 166)
        cy = self.y + self.h // 2
        tw = assets.text_width(s, False)
        if left:
            tx = self.x + 40
            if hot:                                          # 고른 항목: 결정 띠 (2026-11-25 C안)
                strip(tx - 24, cy - 22, max(tw + 96, 300))
            text(tx, cy, s, color)
        else:
            if hot:
                sw = max(tw + 120, 300)
                strip(self.x + self.w // 2 - sw // 2, cy - 22, sw)
            text(self.x + self.w // 2, cy, s, color, center=True)


def menu_pick(buttons, selected, event, height):
    """메뉴 입력 공통: 마우스로 올리면 고르고, 누르면 그 버튼을 고른 채 'click'을 돌려준다.
    W·S·위·아래로 고르고 Enter·Space면 'click'. (새로 고른 번호, 'click' 또는 None)."""
    from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_MOUSEMOTION, SDLK_DOWN, SDLK_RETURN, SDLK_SPACE, SDLK_UP,
                        SDLK_s, SDLK_w)
    import assets
    if event.type in (SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN):
        mx, my = event.x, height - 1 - event.y
        for i, b in enumerate(buttons):
            if b.contains(mx, my):
                if event.type == SDL_MOUSEBUTTONDOWN:
                    assets.play_sound('ui_select')
                    return i, 'click'
                if i != selected:
                    assets.play_sound('ui_move')            # 메뉴 전용 소리 (11/22)
                return i, None
        return selected, None
    if event.type == SDL_KEYDOWN:
        if event.key in (SDLK_w, SDLK_UP):
            assets.play_sound('ui_move')
            return (selected - 1) % len(buttons), None
        if event.key in (SDLK_s, SDLK_DOWN):
            assets.play_sound('ui_move')
            return (selected + 1) % len(buttons), None
        if event.key in (SDLK_RETURN, SDLK_SPACE):
            assets.play_sound('ui_select')
            return selected, 'click'
    return selected, None


# ----- 메뉴 공통 모양 (2026-11-22 메뉴 v2: 일시정지·설정·키·NPC·사망 화면이 같이 쓴다) -----
ACCENT = (130, 235, 225)
EDGE = (46, 56, 82)
ROW_BG = (16, 22, 38)
ROW_HOT = (30, 46, 72)
FAINT = (120, 134, 160)


def backdrop(alpha=0.8):
    """멈춘 화면 위를 어둡게 덮는다. 위아래 가장자리는 더 진하게(글자가 놓이는 곳)."""
    import config
    w, h = config.SCREEN_W, config.SCREEN_H
    assets.draw_rect_color(0, 0, w, h, (5, 8, 15), alpha)
    for i in range(4):                                     # 위·아래 띠 (계단식으로 옅어진다)
        a = 0.5 * (1 - i / 4)
        assets.draw_rect_color(0, h - 60 - i * 30, w, 30, (5, 8, 15), a)
        assets.draw_rect_color(0, 30 + i * 30, w, 30, (5, 8, 15), a)
    assets.draw_rect_color(0, 0, w, 30, (5, 8, 15), 0.6)
    assets.draw_rect_color(0, h - 30, w, 30, (5, 8, 15), 0.6)


def heading(x, y, title, sub=None, color=(244, 236, 214)):
    """큰 제목(왼쪽 정렬, 글자 가운데 y). 부제가 있으면 그 아래 작게 (장식 선 없이)."""
    text(x, y, title, color, big=True)
    if sub:
        text(x + 2, y - 42, sub, FAINT, small=True)


def row(x, y, w, h, hot):
    """목록 한 줄 (메뉴 v3): 평소에는 바탕 없이 아래 구분선만, 고른 줄은 밝은 바탕 + 앞에 헤이즈 조각 표시."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    if hot:
        assets.draw_rect_color(x, y, w, h, (30, 38, 58))
        marker(x - 34, y + h // 2)
    assets.draw_rect_color(x, y, w, 2, (34, 42, 62))


def marker(x, y):
    """고른 항목 앞 표시: 떠 있는 청록 결정(uc_cursor, 8x24)을 글자 가운데 y에 맞춘다. x는 예전 24px 표시의 왼쪽."""
    img = assets.image(art('cursor.png'))
    assets.draw_image(img, int(x) + 12, int(y) - img.h // 2)


def keycap(x, y, label, hot=True):
    """키 글자 판 (왼쪽 아래 x, y, 높이 30): 아래가 두꺼운 키보드 키 모양. 폭은 글자에 맞춘다. 돌려주는 값은 폭."""
    w = max(34, assets.text_width(label, True) + 16) // 2 * 2
    x, y = int(x), int(y)
    panel('key' if hot else 'key_dim', x, y, w, 30)
    assets.draw_text(x + w // 2, y + 16, label, (242, 246, 250) if hot else FAINT, small=True, center=True)
    return w


def footer(pairs, y=34):
    """화면 아래 가운데 키 안내: [(키, 설명)] -> 키 글자 판 + 설명, 사이 간격."""
    import config
    widths = [max(34, assets.text_width(k, True) + 16) + 10 + assets.text_width(d, True) for k, d in pairs]
    total = sum(widths) + 44 * (len(pairs) - 1)
    x = (config.SCREEN_W - total) // 2
    for (k, d), w in zip(pairs, widths):
        kw = keycap(x, y, k)
        text(x + kw + 10, y + 15, d, (175, 188, 212), small=True)
        x += w + 44


def pill(x, y, w, h, label, on, focus=False):
    """값 고르기 칸 (메뉴 v3): 고른 값은 밝은 글자 + 아래 두꺼운 선, 아니면 흐린 글자. 글자 뒤에 효과를 넣지 않는다
    (밝은 칸 위 어두운 글자 + 그림자가 오히려 읽기 어렵다는 사용자 의견, 11/22)."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    if on:
        assets.draw_rect_color(x, y, w, h, (34, 44, 69))
        assets.draw_rect_color(x, y, w, 4, YELLOW if is_plate() else (46, 230, 214))   # 밑줄: 철판은 경고 노랑, 결정형은 청록
    assets.draw_text(x + w // 2, y + h // 2 + 2, label,
                     (242, 246, 250) if on else ((150, 162, 188) if focus else (104, 116, 142)), small=True, center=True)


def card(x, y, w, h, title=None):
    """정보 카드 (불투명): 사선 모서리 큰 판 + 오른쪽 위 모서리의 결정. 제목이 있으면 왼쪽 위에 청록 글자."""
    x, y, w, h = int(x) // 2 * 2, int(y) // 2 * 2, int(w) // 2 * 2, int(h) // 2 * 2
    panel('panel', x, y, w, h)
    if not is_plate():                                    # 철판: 결정 장식 없음, 제목은 스텐실 흰색
        icon('uc_crystal', x + w - 24, y + h - 20)
    if title:
        text(x + 28, y + h - 34, title, (216, 221, 230) if is_plate() else (159, 247, 238))


# ----- 2026-11-27 H1: 플레이 중 HUD (docs/opus/TASKS.md '4차' H1 HUD) -----
# 'mist'에서 HUD는 철판을 걷고 '가는 선 + 어두운 바탕'(증강 카드 A 안개 미니멀과 같은 말투). 부품 um_hud_*·um_fill_*·작은 표시
# (tools/make_ui_mist.py --hud). HUD(ui.GameUI·문 위 보상 판·처음 안내 카드)만 아래 hud_* 함수를 부른다.
# 메뉴·고르는 화면이 쓰는 panel()·bar()·fill()·tag()·keycap() 등은 그대로라 그 화면들은 모양이 변하지 않는다.
# 다른 스킨에서 hud_*는 예전 함수를 그대로 부른다 (픽셀 단위로 같은 화면).
HUD_WELL, HUD_WELL_ALPHA = (9, 12, 21), 0.94      # 안쪽 바탕: 증강 카드 바탕과 같은 색·불투명도 (mutation_mode.MIST_WELL)
HUD_EDGE = 4                                       # 9칸 테두리 그림의 모서리 (화면 px). 선은 2px
MIST_MARKS = ('uc_dash_on', 'uc_dash_off', 'uc_combo_on', 'uc_combo_off', 'uc_combo_fin', 'uc_dot_off')


def frozen_backdrop(draw_fn):
    """메뉴 창 뒤에 멈춘 게임을 깐다 (draw_fn). mist면 그동안 game_world.quiet: 게임의 글자 덮개를 빼고 방·캐릭터·HUD만 (R1, 11/27)."""
    import game_world
    old = game_world.quiet
    game_world.quiet = is_mist()
    try:
        draw_fn()
    finally:
        game_world.quiet = old


def hud_panel(kind, x, y, w, h, tone='line', alpha=HUD_WELL_ALPHA):
    """HUD 판. mist: 바탕 한 장 + 테두리 한 줄(um_hud_frame_<tone>: line 회백 / dim / hot 지금 것 / red / cyan / gold / e1~e3).
    alpha는 바탕 불투명도 (미니맵은 1.0: 뒤 벽이 비치면 방 칸처럼 보인다). 다른 스킨: panel(kind, ...) 그대로."""
    if not is_mist():
        panel(kind, x, y, w, h)
        return
    x, y, w, h = int(x), int(y), max(int(w), 8), max(int(h), 8)
    assets.draw_rect_color(x + 2, y + 2, w - 4, h - 4, HUD_WELL, alpha)
    img = assets.image(f'ui/um_hud_frame_{tone}.png')
    size, c = img.w, HUD_EDGE
    m = size - 2 * c
    for along in range(0, w - 2 * c, m):
        seg = min(m, w - 2 * c - along)
        assets.draw_clip(img, c, size - c, seg, c, x + c + along, y + h - c)
        assets.draw_clip(img, c, 0, seg, c, x + c + along, y)
    for along in range(0, h - 2 * c, m):
        seg = min(m, h - 2 * c - along)
        assets.draw_clip(img, 0, c, c, seg, x, y + c + along)
        assets.draw_clip(img, size - c, c, c, seg, x + w - c, y + c + along)
    for (l, b, dx, dy) in ((0, size - c, 0, h - c), (size - c, size - c, w - c, h - c), (0, 0, 0, 0), (size - c, 0, w - c, 0)):
        assets.draw_clip(img, l, b, c, c, x + dx, y + dy)


def hud_fill(color, x, y, w, h):
    """HUD 막대 속. mist: 한 색 + 위 밝은 줄 (um_fill_<색>_<높이>). 다른 스킨: fill()."""
    if not is_mist():
        fill(color, x, y, w, h)
        return
    w = int(w)
    if w <= 0:
        return
    img = assets.image(f'ui/um_fill_{color}_{h}.png')
    assets.draw_clip(img, 0, 0, min(w, img.w), h, int(x), int(y))


def hud_bar(color, x, y, w, h, ratio, empty='empty', tone='line'):
    """HUD 막대: mist는 가는 테두리 판 안에 빈 칸과 채움 / 다른 스킨은 bar()."""
    if not is_mist():
        bar(color, x, y, w, h, ratio, empty)
        return
    hud_panel('frame', x - 4, y - 4, w + 8, h + 8, tone)
    hud_fill(empty, x, y, w, h)
    hud_fill(color, x, y, round(w * max(0.0, min(1.0, ratio))), h)


def hud_icon(name, x, y):
    """HUD 작은 표시: mist에서 대시·콤보·단계 점은 가는 선 그림(um_*), 그 밖(하트·물약·조준점 등)은 icon()과 같다."""
    if is_mist() and name in MIST_MARKS:
        img = assets.image(f'ui/um_{name[3:]}.png')
        assets.draw_image(img, int(x) + img.w // 2, int(y))
        return img.w, img.h
    return icon(name, x, y)


def hud_tag(x, y, w, tone='line'):
    """HUD 이름표 띠 (높이 40, 게이지 아래 구간 이름·저주): mist는 가는 테두리 판 / 다른 스킨은 tag()."""
    if not is_mist():
        tag(x, y, w)
        return
    hud_panel('plate', int(x) // 2 * 2, int(y), max(int(w) // 2 * 2, 32), 40, tone)


def hud_keycap(x, y, label, hot=True, framed=False, dim_color=None):
    """HUD 칸 안의 키 글자: mist는 판 없이 글자만(칸이 이미 어둡다. 판 안에 판을 겹치지 않는다) / 다른 스킨은 keycap().
    framed: 칸 밖에 홀로 놓이는 키 판(보스 대사 띠의 Enter, 11/27 S1). mist는 가는 테두리 한 줄 + 어두운 바탕(누를 수 있으면 회백,
    아직이면 흐린 테두리). 폭·자리는 keycap()과 같다. dim_color: mist에서 hot이 아닐 때 글자 색(H2: 들지 않은 무기 칸 숫자. 없으면 FAINT)."""
    if not is_mist():
        return keycap(x, y, label, hot)
    w = max(34, assets.text_width(label, True) + 16) // 2 * 2
    if framed:
        hud_panel('key', int(x), int(y), w, 30, 'line' if hot else 'dim')
        assets.draw_text(int(x) + w // 2, int(y) + 16, label, (242, 246, 250) if hot else FAINT, small=True, center=True)
        return w
    text(int(x) + w // 2, int(y) + 16, label, (242, 246, 250) if hot else (dim_color or FAINT), small=True, center=True)
    return w
