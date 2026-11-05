"""이미지·글꼴 로드와 캐시. 같은 파일은 한 번만 읽는다. pico2d는 실제로 그릴 때 불러온다."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets')
DATA_DIR = os.path.join(ROOT, 'data')
FONT_PATH = 'C:/Windows/Fonts/malgun.ttf'

_images = {}
_fonts = {}


def image(relative_path):
    """assets/ 아래 이미지를 반환한다. 예: image('sprites/unified/n09_idle.png')"""
    if relative_path not in _images:
        from pico2d import load_image
        _images[relative_path] = load_image(os.path.join(ASSET_DIR, relative_path))
    return _images[relative_path]


def font(size):
    """한글 글꼴을 반환한다. 글꼴 파일이 없으면 None (글자는 그리지 않는다)."""
    if size not in _fonts:
        if os.path.exists(FONT_PATH):
            from pico2d import load_font
            _fonts[size] = load_font(FONT_PATH, size)
        else:
            _fonts[size] = None
    return _fonts[size]


def draw_text(x, y, text, size=24, color=(255, 255, 255)):
    f = font(size)
    if f is not None:
        f.draw(x, y, text, color)
