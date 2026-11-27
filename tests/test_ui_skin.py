"""UI 스킨 바꿔 끼우기 (2026-11-26 UI 3차 '교도소 철판', docs/opus/TASKS.md). 창 없이: python tests/test_ui_skin.py

- config.UI_SKIN = 'plate'(새 철판, assets/ui/up_*) / 'crystal'(예전 결정형, uc_*). 이름·크기가 같아 접두만 바꾼다.
- 두 스킨 모두 hud_kit이 찾는 부품이 다 있고 치수가 KITS와 맞는다. 코드가 부르는 'uc_' 부품은 철판 쪽에도 있다.
- 새 그림은 픽셀 규칙(2px 격자, 64색 이하, 알파 0/255)을 지킨다.
- 철판 스킨의 판 테두리·장식에는 청록을 쓰지 않는다(청록은 헤이즈에만).
"""
import glob
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import config  # noqa: E402
import hud_kit  # noqa: E402

UI = os.path.join(ROOT, 'assets', 'ui')
CYAN = (46, 230, 214)
HAZE_PARTS = ('shard', 'crystal', 'diamond', 'map_haze', 'fill_cyan', 'mut_bloom')     # 헤이즈를 나타내는 부품 (청록 허용. 각성 = 헤이즈 구간)


def _with_skin(name, fn):
    old = config.UI_SKIN
    try:
        config.UI_SKIN = name
        return fn()
    finally:
        config.UI_SKIN = old


def test_default_skin_is_plate_and_paths_switch():
    assert config.UI_SKIN == 'mist'                                          # 2026-11-27 확정 (타이틀 감시 단말 + 증강 안개 미니멀)
    assert _with_skin('mist', lambda: hud_kit.art('kit_panel.png')) == 'ui/upx_kit_panel.png'   # 나머지 화면은 plate와 같다
    assert _with_skin('mist', hud_kit.is_plate) and _with_skin('mist', hud_kit.is_pixellab_plate)
    assert _with_skin('mist', hud_kit.is_mist) and not _with_skin('plate', hud_kit.is_mist)
    assert _with_skin('nonsense', hud_kit.skin) == 'mist'
    assert _with_skin('plate_code', lambda: hud_kit.art('kit_panel.png')) == 'ui/up_kit_panel.png'
    assert _with_skin('crystal', lambda: hud_kit.art('kit_panel.png')) == 'ui/uc_kit_panel.png'
    assert _with_skin('plate_code', lambda: hud_kit.part_name('uc_heart')) == 'up_heart'
    assert _with_skin('crystal', lambda: hud_kit.part_name('uc_heart')) == 'uc_heart'
    assert _with_skin('plate', lambda: hud_kit.part_name('icon_shard')) == 'icon_shard'
    assert _with_skin('plate_code', hud_kit.is_plate) and _with_skin('plate', hud_kit.is_plate)
    assert not _with_skin('crystal', hud_kit.is_plate)


def test_pixellab_skin_uses_its_own_parts_and_falls_back_to_code_plates():
    for f in glob.glob(os.path.join(UI, 'uc_*.png')):
        rest = os.path.basename(f)[3:]
        rel = _with_skin('plate', lambda: hud_kit.art(rest))
        assert rel in (f'ui/upx_{rest}', f'ui/up_{rest}'), rel
        assert os.path.exists(os.path.join(ROOT, 'assets', rel)), rel
        if rel.startswith('ui/upx_'):                                         # PixelLab 부품도 크기가 같다
            assert Image.open(os.path.join(ROOT, 'assets', rel)).size == Image.open(f).size, rest


def test_every_old_part_has_a_plate_twin_of_the_same_size():
    olds = sorted(glob.glob(os.path.join(UI, 'uc_*.png')))
    assert len(olds) > 90
    for f in olds:
        twin = os.path.join(UI, 'up_' + os.path.basename(f)[3:])
        assert os.path.exists(twin), twin
        assert Image.open(twin).size == Image.open(f).size, os.path.basename(twin)


def test_kit_sizes_match_in_both_skins():
    for prefix in ('uc_', 'up_'):
        for kind, (size, corner, _well) in hud_kit.KITS.items():
            im = Image.open(os.path.join(UI, f'{prefix}kit_{kind}.png'))
            assert im.size == (size, size), (prefix, kind)
            assert 2 * corner < size


def test_parts_named_in_code_exist_for_the_plate_skin():
    names = set()
    for f in glob.glob(os.path.join(ROOT, 'src', '*.py')):
        src = open(f, encoding='utf-8').read()
        names |= set(re.findall(r"'uc_([a-z_]+)'", src))
    names = {n for n in names if n and not n.endswith('_')}       # 'uc_map_' + 종류처럼 이어 붙이는 접두는 뺀다
    assert names
    for n in names:
        assert os.path.exists(os.path.join(UI, f'up_{n}.png')), n
    assert os.path.exists(os.path.join(UI, 'up_card_curse.png'))                 # 철판 스킨에만 있는 저주 카드 틀


def test_plate_parts_follow_pixel_rules():
    for f in sorted(glob.glob(os.path.join(UI, 'up_*.png')) + glob.glob(os.path.join(UI, 'upx_*.png'))):
        a = np.array(Image.open(f).convert('RGBA'))
        name = os.path.basename(f)
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name   # 2px 격자
        colors = {tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}
        assert len(colors) <= 64, (name, len(colors))


def test_no_cyan_on_plate_frames_and_decor():
    for f in sorted(glob.glob(os.path.join(UI, 'up_*.png')) + glob.glob(os.path.join(UI, 'upx_*.png'))):
        name = os.path.basename(f).split('_', 1)[1][:-4]
        if name.startswith(HAZE_PARTS):
            continue
        a = np.array(Image.open(f).convert('RGBA'))
        rgb = a[a[:, :, 3] > 0][:, :3].astype(int)
        cyanish = ((rgb[:, 1] > 150) & (rgb[:, 2] > 150) & (rgb[:, 0] < 120)).sum() if len(rgb) else 0
        assert cyanish == 0, name


def test_every_family_has_its_own_icon_in_the_plate_skin():
    import hashlib
    import mutations as mu
    seen = {}
    for fid, fam in mu.FAMILIES.items():
        path = _with_skin('plate', lambda: hud_kit.family_icon(fid, fam))
        data = open(os.path.join(ROOT, 'assets', path), 'rb').read()
        h = hashlib.md5(np.array(Image.open(os.path.join(ROOT, 'assets', path)).convert('RGBA')).tobytes()).hexdigest()
        assert h not in seen, (fid, seen.get(h))
        seen[h] = fid
        assert Image.open(os.path.join(ROOT, 'assets', path)).size == (64, 64)
        del data
    assert len(seen) == len(mu.FAMILIES) == 18
    assert _with_skin('crystal', lambda: hud_kit.family_icon('bloom', mu.FAMILIES['bloom'])) == mu.FAMILIES['bloom']['icon']


# ----- 2026-11-27 'mist' 스킨 (docs/opus/TASKS.md '3차 변경 2', tools/make_ui_mist.py) -----
MIST_PARTS = (['um_card_' + k + h for k in ('common', 'rare', 'legendary', 'curse') for h in ('', '_hot')] +
              ['um_divider_' + c for c in ('white', 'cyan', 'gold', 'red')] +
              ['um_mist_pool', 'um_logo_title', 'um_cursor', 'um_bracket', 'um_bolt_1', 'um_bolt_2', 'um_bolt_3'])


def test_mist_parts_exist_and_follow_pixel_rules():
    for n in MIST_PARTS:
        a = np.array(Image.open(os.path.join(UI, n + '.png')).convert('RGBA'))
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, n
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), n
        assert len({tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}) <= 64, n


def test_mist_card_border_is_one_thin_line_around_an_empty_inside():
    """증강 카드 테두리: 카드 크기 그대로, 변은 도트 1칸(화면 2px) 한 줄, 속은 비어 있다(바탕은 코드가 깐다). 등급마다 색이 다르다."""
    import mutation_mode as mm
    seen = set()
    for k in ('common', 'rare', 'legendary', 'curse'):
        a = np.array(Image.open(os.path.join(UI, f'um_card_{k}.png')).convert('RGBA'))
        assert a.shape[:2] == (mm.CARD_H, mm.CARD_W), k
        h, w = a.shape[:2]
        for line in (a[h // 3, :, 3], a[:, w // 3, 3]):                    # 왼쪽 변·오른쪽 변 / 위 변·아래 변을 가로지르는 한 줄
            on = np.nonzero(line)[0]
            assert len(on) == 4, (k, on)                                   # 양쪽 변이 각각 2px
        assert not a[40:h - 40, 40:w - 40, 3].any(), k                     # 속은 투명
        hot = np.array(Image.open(os.path.join(UI, f'um_card_{k}_hot.png')).convert('RGBA'))
        assert hot[hot[:, :, 3] > 0][:, :3].astype(int).sum() > a[a[:, :, 3] > 0][:, :3].astype(int).sum(), k   # 고른 카드는 밝게
        seen.add(tuple(a[h // 3, np.nonzero(a[h // 3, :, 3])[0][0], :3]))
    assert len(seen) == 4


def test_mist_card_dividers_sit_in_the_middle():
    """증강 카드 위아래 장식선의 가운데 장식(가장 키 큰 세로 줄들)이 그림 가운데에 있다 (11/27: 흰색만 왼쪽으로 13px 치우쳤다)."""
    for c in ('white', 'cyan', 'gold', 'red'):
        a = np.array(Image.open(os.path.join(UI, f'um_divider_{c}.png')).convert('RGBA'))
        col = (a[:, :, 3] > 0).sum(axis=0)
        mid = np.nonzero(col == col.max())[0].mean()
        assert abs(mid - (a.shape[1] - 1) / 2) <= 2, (c, mid, a.shape[1])


def test_title_shade_is_soft_light_layer_dark_behind_text_and_clear_at_the_sides():
    """타이틀 글자 뒤 어둠: 빛 층(assets/light, 부드러운 알파 허용)에 절반 크기로. 로고·메뉴 뒤가 가장 진하고, 화면 양옆과
    주인공 자리는 비어 있다(배경이 그대로 보인다). 화면 전체를 덮는 판이 아니다."""
    import title_mode as tm
    a = np.array(Image.open(os.path.join(ROOT, 'assets', 'light', 'title_shade.png')).convert('RGBA'))[:, :, 3]
    W, H = config.SCREEN_W, config.SCREEN_H
    assert a.shape == (H // 2, W // 2)
    at = lambda x, y: int(a[(H - 1 - y) // 2, x // 2])  # noqa: E731
    assert at(W // 2, tm.LOGO_Y + 40) > 170                                   # 로고 뒤
    for b in tm.MENU:
        assert at(W // 2, b.y + b.h // 2) > 150, b.label                    # 메뉴 줄 뒤
    assert at(W // 2 + 520, tm.LOGO_Y) < 40                                   # 로고에서 멀어지면 옅어진다
    mid = slice(H // 2 // 2 - 100, H // 2 // 2 + 100)
    assert a[mid, 0].max() == 0 and a[mid, -1].max() == 0                     # 양옆 가장자리
    assert at(tm.HERO_X, tm.HERO_Y + 60) == 0                                 # 주인공
    assert 0 < (a > 0).mean() < 0.6                                           # 화면 전체 판이 아니다
    assert len(np.unique(a)) > 60                                             # 계단 몇 개가 아니라 부드러운 알파


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
