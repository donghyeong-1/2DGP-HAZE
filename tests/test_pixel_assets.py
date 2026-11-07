"""픽셀 아트 규칙 자동 검사 (docs/pixel_rules.md). 실행: python tests/test_pixel_assets.py 또는 pytest"""
import glob
import os
import re
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import config  # noqa: E402

MAX_COLORS = 64


def sprite_files():
    return sorted(glob.glob(os.path.join(ROOT, 'assets', 'sprites', 'unified', '*.png')))


def tile_files():
    return sorted(glob.glob(os.path.join(ROOT, 'assets', 'placeholder', 'tile_*.png')))


def test_sprites_have_binary_alpha():
    assert sprite_files(), '검사할 스프라이트가 없다'
    for path in sprite_files() + tile_files():
        alpha = Image.open(path).convert('RGBA').getchannel('A').histogram()
        assert sum(alpha[1:255]) == 0, f'반투명 픽셀이 있다: {os.path.basename(path)}'


def test_sprites_within_palette_limit():
    for path in sprite_files():
        img = Image.open(path).convert('RGBA')
        colors = {p for p in img.get_flattened_data() if p[3] == 255} if hasattr(img, 'get_flattened_data') \
            else {p for p in img.getdata() if p[3] == 255}
        assert len(colors) <= MAX_COLORS, f'{os.path.basename(path)}: {len(colors)}색'


def test_tiles_are_multiples_of_tile_size():
    for path in tile_files():
        w, h = Image.open(path).size
        assert w % config.TILE == 0 and h % config.TILE == 0, f'{os.path.basename(path)}: {w}x{h}'


def test_no_scaling_or_rotation_in_game_code():
    """코드에서 배율·회전 그리기를 쓰지 않는다 (draw_rect_image는 단색 칸 전용으로 예외)."""
    banned = [r'rotate_draw', r'composite_draw\(\s*[^0\s)]']
    for path in glob.glob(os.path.join(ROOT, 'src', '*.py')):
        text = open(path, encoding='utf-8').read()
        for pattern in banned:
            assert not re.search(pattern, text), f'{os.path.basename(path)}: {pattern}'


def test_nearest_filter_is_requested():
    text = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert 'SDL_HINT_RENDER_SCALE_QUALITY' in text and "b'0'" in text


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
