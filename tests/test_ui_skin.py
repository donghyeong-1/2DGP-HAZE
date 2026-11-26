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
    assert config.UI_SKIN == 'plate'
    assert _with_skin('plate', lambda: hud_kit.art('kit_panel.png')) == 'ui/up_kit_panel.png'
    assert _with_skin('crystal', lambda: hud_kit.art('kit_panel.png')) == 'ui/uc_kit_panel.png'
    assert _with_skin('plate', lambda: hud_kit.part_name('uc_heart')) == 'up_heart'
    assert _with_skin('crystal', lambda: hud_kit.part_name('uc_heart')) == 'uc_heart'
    assert _with_skin('plate', lambda: hud_kit.part_name('icon_shard')) == 'icon_shard'
    assert _with_skin('nonsense', hud_kit.skin) == 'plate'


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
    for f in sorted(glob.glob(os.path.join(UI, 'up_*.png'))):
        a = np.array(Image.open(f).convert('RGBA'))
        name = os.path.basename(f)
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name   # 2px 격자
        colors = {tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}
        assert len(colors) <= 64, (name, len(colors))


def test_no_cyan_on_plate_frames_and_decor():
    for f in sorted(glob.glob(os.path.join(UI, 'up_*.png'))):
        name = os.path.basename(f)[3:-4]
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


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
