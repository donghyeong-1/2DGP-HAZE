"""이미지·글꼴 로드와 캐시. 같은 파일은 한 번만 읽는다. pico2d는 실제로 그릴 때 불러온다."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets')
DATA_DIR = os.path.join(ROOT, 'data')

_images = {}
_fonts = {}


def image(relative_path):
    """assets/ 아래 이미지를 반환한다. 예: image('sprites/unified/n09_idle.png')"""
    if relative_path not in _images:
        from pico2d import load_image
        _images[relative_path] = load_image(os.path.join(ASSET_DIR, relative_path))
    return _images[relative_path]


def draw_image(img, x, y, flip=''):
    """이미지를 원본 크기(1배)로 정수 좌표에 그린다. x는 가운데, y는 아래 가장자리.

    픽셀 아트 규칙: 확대·축소·회전 없이 그리고, 위치는 항상 정수 픽셀에 맞춘다.
    """
    left = int(round(x)) - img.w // 2
    bottom = int(round(y))
    if flip:
        img.composite_draw(0, flip, left + img.w / 2, bottom + img.h / 2, img.w, img.h)
    else:
        img.draw_to_origin(left, bottom)


def draw_rect_image(img, left, bottom, w, h):
    """단색 사각형(placeholder/px_*.png)을 정수 좌표로 채운다. 무늬 없는 색 칸 전용."""
    img.draw_to_origin(int(round(left)), int(round(bottom)), int(round(w)), int(round(h)))


# 갈무리(Galmuri, SIL OFL 1.1) 픽셀 폰트. 글자는 폰트의 원래 크기로만 그린다(docs/pixel_rules.md 규칙 6).
FONT_SIZES = {'normal': 14, 'small': 11}


def font(small=False):
    """한글 픽셀 폰트를 반환한다. 글꼴 파일이 없으면 None (글자는 그리지 않는다)."""
    key = 'small' if small else 'normal'
    if key not in _fonts:
        size = FONT_SIZES[key]
        path = os.path.join(ASSET_DIR, 'fonts', f'Galmuri{size}.ttf')
        if os.path.exists(path):
            from pico2d import load_font
            _fonts[key] = load_font(path, size)
        else:
            _fonts[key] = None
    return _fonts[key]


def text_width(text, small=False):
    f = font(small)
    if f is None:
        return 0
    import ctypes
    from sdl2.sdlttf import TTF_SizeUTF8
    w, h = ctypes.c_int(0), ctypes.c_int(0)
    TTF_SizeUTF8(f.font, text.encode('utf-8'), ctypes.byref(w), ctypes.byref(h))
    return w.value


def draw_text(x, y, text, color=(255, 255, 255), small=False, center=False):
    """글자를 그린다. center=True면 x가 글자의 가운데. 위치는 정수로 맞춘다."""
    f = font(small)
    if f is None:
        return
    left = int(round(x)) - (text_width(text, small) // 2 if center else 0)
    f.draw(left, int(round(y)), text, color)
