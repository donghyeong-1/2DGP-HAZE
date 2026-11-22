"""UI 부품 그리기: 9칸 판, 막대, 그림자 글자, 버튼. HUD(ui.py)와 메뉴(타이틀·일시정지·설정)가 함께 쓴다.

판은 tools/make_ui.py가 만든 assets/ui/ui_kit_<종류>.png를 9칸으로 나눠 그린다: 네 모서리는 그대로,
네 변은 같은 무늬 조각을 길이만큼 이어 붙이고(늘이지 않는다), 가운데는 그 판의 속 색으로 채운다.
막대 속은 ui_fill_<색>_<높이>.png에서 필요한 너비만큼 잘라 쓴다. 모든 위치는 정수 픽셀이다.
"""
import assets

# 판 종류 -> (그림 한 변 크기, 모서리 크기, 속 색)
KITS = {
    'panel': (48, 16, (13, 18, 31)),
    'plate': (24, 8, (17, 24, 40)),
    'frame': (16, 5, (13, 18, 31)),
    'button': (36, 12, (24, 32, 52)),
    'button_hot': (36, 12, (30, 66, 86)),
    'slot': (36, 12, (16, 22, 36)),
    'slot_hot': (36, 12, (20, 40, 54)),
    'banner': (32, 12, (16, 22, 36)),
}
FILL_HEIGHTS = (8, 12, 16, 20, 24)
SHADOW = (8, 11, 20)


def panel(kind, x, y, w, h):
    """왼쪽 아래 (x, y)부터 w x h 판을 그린다."""
    size, c, well = KITS[kind]
    img = assets.image(f'ui/ui_kit_{kind}.png')
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


def fill(color, x, y, w, h):
    """막대 속 무늬를 (x, y)부터 너비 w만큼. h는 FILL_HEIGHTS 중 하나."""
    w = int(w)
    if w <= 0:
        return
    img = assets.image(f'ui/ui_fill_{color}_{h}.png')
    assets.draw_clip(img, 0, 0, min(w, img.w), h, int(x), int(y))


def bar(color, x, y, w, h, ratio, empty='empty'):
    """틀이 있는 막대: 틀(frame 판) 안에 빈 칸 무늬를 깔고 ratio만큼 색 무늬를 채운다."""
    panel('frame', x - 3, y - 3, w + 6, h + 6)
    fill(empty, x, y, w, h)
    fill(color, x, y, round(w * max(0.0, min(1.0, ratio))), h)


def icon(name, x, y):
    """assets/ui/<name>.png를 왼쪽 아래 (x, y)에 1배로 그린다."""
    img = assets.image(f'ui/{name}.png')
    assets.draw_image(img, int(x) + img.w // 2, int(y))
    return img.w, img.h


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
        color = (244, 236, 214) if hot else (128, 140, 166)
        cy = self.y + self.h // 2
        if left:
            tx = self.x + 40
            text(tx, cy, s, color)
            if hot:
                marker(self.x + 4, cy)
        else:
            text(self.x + self.w // 2, cy, s, color, center=True)
            if hot:
                tw = assets.text_width(s, False)
                marker(self.x + self.w // 2 - tw // 2 - 40, cy)


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
    """고른 항목 앞 표시: 헤이즈 조각 아이콘(ui_shard_s, 24px)을 글자 가운데 y에 맞춘다."""
    img = assets.image('ui/ui_shard_s.png')
    assets.draw_image(img, int(x) + img.w // 2, int(y) - img.h // 2)


def keycap(x, y, label, hot=True):
    """키 글자 판 (왼쪽 아래 x, y, 높이 30): 아래가 두꺼운 키보드 키 모양. 폭은 글자에 맞춘다. 돌려주는 값은 폭."""
    w = max(34, assets.text_width(label, True) + 16)
    x, y = int(x), int(y)
    assets.draw_rect_color(x, y, w, 30, (20, 24, 36))                         # 키 옆면(아래)
    assets.draw_rect_color(x, y + 4, w, 26, (92, 100, 122) if hot else (52, 58, 76))
    assets.draw_rect_color(x + 2, y + 6, w - 4, 22, (54, 60, 80) if hot else (30, 34, 48))
    assets.draw_text(x + w // 2, y + 18, label, (236, 238, 244) if hot else FAINT, small=True, center=True)
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
        assets.draw_rect_color(x, y, w, h, (38, 50, 74))
        assets.draw_rect_color(x, y, w, 4, (232, 200, 120))
    assets.draw_text(x + w // 2, y + h // 2 + 2, label,
                     (250, 244, 226) if on else ((150, 162, 188) if focus else (104, 116, 142)), small=True, center=True)


def card(x, y, w, h, title=None):
    """정보 카드 (불투명): 테두리 + 속, 제목이 있으면 왼쪽 위에 청록 글자와 짧은 선."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    assets.draw_rect_color(x, y, w, h, EDGE)
    assets.draw_rect_color(x + 2, y + 2, w - 4, h - 4, (12, 17, 30))
    if title:
        text(x + 28, y + h - 34, title, (232, 200, 120))
