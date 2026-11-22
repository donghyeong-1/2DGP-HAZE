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
        """메뉴 줄 모양(11/22 메뉴 v2): 고르면 밝은 속 + 왼쪽 강조 띠 + 화살표, 아니면 어두운 속 + 얇은 테두리."""
        row(self.x, self.y, self.w, self.h, hot)
        color = (240, 248, 255) if hot else (150, 165, 192)
        s = label or self.label
        if left:
            text(self.x + 34, self.y + self.h // 2, s, color)
        else:
            text(self.x + self.w // 2, self.y + self.h // 2, s, color, center=True)


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


def heading(x, y, title, sub=None, color=(240, 246, 255)):
    """큰 제목(왼쪽 정렬, 글자 가운데 y) + 아래 강조선 + 작은 부제."""
    text(x, y, title, color, big=True)
    assets.draw_rect_color(int(x), int(y) - 40, 120, 4, ACCENT)
    assets.draw_rect_color(int(x) + 124, int(y) - 40, 40, 4, EDGE)
    if sub:
        text(x + 180, y - 38, sub, FAINT, small=True)


def row(x, y, w, h, hot):
    """메뉴 줄 바탕 (불투명). 고른 줄은 밝은 속·테두리·왼쪽 강조 띠·화살표."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    assets.draw_rect_color(x, y, w, h, ACCENT if hot else EDGE)
    assets.draw_rect_color(x + 2, y + 2, w - 4, h - 4, ROW_HOT if hot else ROW_BG)
    if hot:
        assets.draw_rect_color(x + 2, y + 2, 8, h - 4, ACCENT)
        ax, ay = x - 22, y + h // 2
        for i in range(8):
            assets.draw_rect_color(ax + i, ay - 8 + i, 2, 16 - 2 * i, ACCENT)


def keycap(x, y, label, hot=True):
    """키 글자 판 (왼쪽 아래 x, y, 높이 30). 폭은 글자에 맞춘다. 돌려주는 값은 폭."""
    w = max(34, assets.text_width(label, True) + 16)
    assets.draw_rect_color(int(x), int(y), w, 30, EDGE)
    assets.draw_rect_color(int(x) + 2, int(y) + 4, w - 4, 24, (26, 34, 54) if hot else (18, 22, 34))
    text(int(x) + w // 2, int(y) + 16, label, (235, 245, 255) if hot else FAINT, small=True, center=True)
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
    """값 고르기 칸: 고른 값은 청록으로 채우고 어두운 글자, 아니면 테두리만."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    assets.draw_rect_color(x, y, w, h, ACCENT if on else (EDGE if not focus else (70, 86, 120)))
    assets.draw_rect_color(x + 2, y + 2, w - 4, h - 4, (110, 215, 205) if on else ROW_BG)
    text(x + w // 2, y + h // 2, label, (10, 22, 30) if on else (150, 165, 192), small=True, center=True)


def card(x, y, w, h, title=None):
    """정보 카드 (불투명): 테두리 + 속, 제목이 있으면 왼쪽 위에 청록 글자와 짧은 선."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    assets.draw_rect_color(x, y, w, h, EDGE)
    assets.draw_rect_color(x + 2, y + 2, w - 4, h - 4, (12, 17, 30))
    if title:
        text(x + 28, y + h - 34, title, ACCENT)
        assets.draw_rect_color(x + 28, y + h - 60, 60, 3, ACCENT)
