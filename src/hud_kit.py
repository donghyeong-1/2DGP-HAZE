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

    def draw(self, hot, label=None):
        panel('button_hot' if hot else 'button', self.x, self.y, self.w, self.h)
        color = (235, 245, 255) if hot else (160, 176, 205)
        text(self.x + self.w // 2, self.y + self.h // 2, label or self.label, color, center=True)
        if hot:                                            # 고른 버튼 앞의 화살표
            ax, ay = self.x - 26, self.y + self.h // 2
            for i in range(8):
                assets.draw_rect_color(ax + i, ay - 8 + i, 2, 16 - 2 * i, (130, 235, 225))


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
