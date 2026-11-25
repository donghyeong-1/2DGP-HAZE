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


def effect_files():
    return sorted(glob.glob(os.path.join(ROOT, 'assets', 'effects', '*.png')))


def tile_files():
    return sorted(glob.glob(os.path.join(ROOT, 'assets', 'placeholder', 'tile_*.png')) +
                  glob.glob(os.path.join(ROOT, 'assets', 'tiles', 'tile_*.png')))


def prop_files():
    return sorted(glob.glob(os.path.join(ROOT, 'assets', 'props', '*.png')) +      # 움직이는 배경 소품 (Codex T28)
                  glob.glob(os.path.join(ROOT, 'assets', 'decor', '*.png')) +      # 멈춘 장식 (T31)
                  glob.glob(os.path.join(ROOT, 'assets', 'portraits', '*.png')))   # 대화 초상화 (T32)


def ui_files():
    return sorted(glob.glob(os.path.join(ROOT, 'assets', 'ui', '*.png')))


def test_v6_sprite_sets_are_on_the_two_pixel_grid():
    """v6 규격(docs/plan_v6.md): 캐릭터는 도트 하나가 화면 2px다. skin_*.json에 등록된 세트(PixelLab으로 만든 것)는
    모든 2x2 칸이 한 색이어야 한다. 2026-11-25: 1px 단위로 그린 문지기 그림(Codex T50)이 섞여 들어가 그림체가 달라졌다."""
    import json

    import numpy as np
    uni = os.path.join(ROOT, 'assets', 'sprites', 'unified')
    checked = 0
    for path in sorted(glob.glob(os.path.join(uni, 'skin_*.json'))):
        for name, (count, _x, _y) in json.load(open(path, encoding='utf-8'))['frames'].items():
            for n in range(1, count + 1):
                a = np.asarray(Image.open(os.path.join(uni, f'{name}_{n}.png')).convert('RGBA'))
                assert a.shape[0] % 2 == 0 and a.shape[1] % 2 == 0, (name, n, a.shape)
                b = a.reshape(a.shape[0] // 2, 2, a.shape[1] // 2, 2, 4)
                assert (b == b[:, :1, :, :1]).all(), f'{name}_{n}: 2px 격자가 아니다 (1px 단위 그림)'
                checked += 1
    assert checked > 100


def test_sprites_have_binary_alpha():
    assert sprite_files(), '검사할 스프라이트가 없다'
    for path in sprite_files() + tile_files() + effect_files() + ui_files() + prop_files():
        alpha = Image.open(path).convert('RGBA').getchannel('A').histogram()
        assert sum(alpha[1:255]) == 0, f'반투명 픽셀이 있다: {os.path.basename(path)}'


def test_sprites_within_palette_limit():
    assert prop_files(), '배경 소품이 없다'
    for path in sprite_files() + prop_files():
        img = Image.open(path).convert('RGBA')
        colors = {p for p in img.get_flattened_data() if p[3] == 255} if hasattr(img, 'get_flattened_data') \
            else {p for p in img.getdata() if p[3] == 255}
        assert len(colors) <= MAX_COLORS, f'{os.path.basename(path)}: {len(colors)}색'


def test_code_art_within_palette_limit():
    """코드 아트(타일, 로고)는 색이 적다: 64색 이하."""
    assert ui_files() and tile_files()
    for path in tile_files() + ui_files():
        img = Image.open(path).convert('RGBA')
        colors = {p for p in img.getdata() if p[3] == 255}
        assert len(colors) <= MAX_COLORS, f'{os.path.basename(path)}: {len(colors)}색'


def test_effects_within_palette_limit():
    """이펙트는 시트마다 64색 이하, 프레임 수는 60 이하(용량). 모두 자체 제작이다 (외부 이펙트 파일이 없어야 한다)."""
    import json
    for path in effect_files():
        img = Image.open(path).convert('RGBA')
        colors = {p for p in img.getdata() if p[3] == 255}
        assert len(colors) <= MAX_COLORS, f'{os.path.basename(path)}: {len(colors)}색'
        meta = json.load(open(path[:-4] + '.json', encoding='utf-8'))
        per = meta['frames'] // meta.get('variants', 1)          # 방향 변형이 있으면 한 변형의 길이 (11/24 fxkit 두 겹 시트)
        assert per <= 60, f"{os.path.basename(path)}: {per}프레임"
    for name in os.listdir(os.path.join(ROOT, 'assets', 'effects')):
        assert 'pixelfx' not in name.lower(), f'외부 이펙트 파일이 남아 있다: {name}'


def test_tiles_are_multiples_of_tile_size():
    for path in tile_files():
        w, h = Image.open(path).size
        assert w % config.TILE == 0 and h % config.TILE == 0, f'{os.path.basename(path)}: {w}x{h}'


def test_no_scaling_or_rotation_in_game_code():
    """코드에서 배율·회전 그리기를 쓰지 않는다 (draw_rect_image는 단색 칸 전용으로 예외)."""
    banned = [r'rotate_draw', r'composite_draw\(\s*[^0\s)]',
              r'clip_composite_draw\(\s*[^,]+,[^,]+,[^,]+,[^,]+,\s*[^0\s,]']  # 각도 인자는 항상 0
    for path in glob.glob(os.path.join(ROOT, 'src', '*.py')):
        text = open(path, encoding='utf-8').read()
        for pattern in banned:
            assert not re.search(pattern, text), f'{os.path.basename(path)}: {pattern}'


def test_pixel_font_native_sizes_only():
    """픽셀 폰트는 원래 크기(14, 11)의 정수 배로만 쓴다. draw_text에 크기 숫자를 넘기지 않는다."""
    import assets
    import config
    assert set(assets.FONT_SIZES.values()) == {14, 11}
    assert isinstance(config.FONT_SCALE, int) and isinstance(config.EFFECT_SCALE, int)
    assert all(isinstance(v, int) and v >= 1 for v in assets.FONT_MULTIPLES.values())
    for size in assets.FONT_SIZES.values():
        assert os.path.exists(os.path.join(ROOT, 'assets', 'fonts', f'Galmuri{size}.ttf'))
    assert os.path.exists(os.path.join(ROOT, 'assets', 'fonts', 'OFL.txt'))  # 라이선스 문구 동봉
    for path in glob.glob(os.path.join(ROOT, 'src', '*.py')):
        text = open(path, encoding='utf-8').read()
        assert not re.search(r"draw_text\([^)]*['\"],\s*\d{2,3}\s*,", text), os.path.basename(path)


def test_nearest_filter_is_requested():
    text = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert 'SDL_HINT_RENDER_SCALE_QUALITY' in text and "b'0'" in text


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
