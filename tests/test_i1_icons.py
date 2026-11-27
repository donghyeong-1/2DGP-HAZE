"""I1 무기·아이템 아이콘 다시 뽑기 (2026-11-27, docs/opus/TASKS.md '4차' I1).

무기 아이콘 넷·아이템 아이콘 10종을 PixelLab 그림으로 바꿨다(tools/apply_pixellab_icons.py). 형태 아이콘 넷(make_form_icons)과
분노 아이콘(make_fury_icon)은 새 그림에서 코드로 다시 만들었다. 크기(48x48)와 쓰는 코드의 자리는 그대로다.
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
UI = os.path.join(ROOT, 'assets', 'ui')
WEAPONS = ('pipe', 'pistol', 'gauntlet', 'chain')
ITEMS = ('cap', 'absorb', 'steady', 'enhance', 'resist', 'dash', 'power', 'vigor', 'heal', 'shard', 'fury')
ALL = [f'icon_w_{w}' for w in WEAPONS] + [f'icon_f_{w}' for w in WEAPONS] + [f'icon_{i}' for i in ITEMS]


def _a(name):
    return np.array(Image.open(os.path.join(UI, name + '.png')).convert('RGBA'))


def test_icons_follow_pixel_rules():
    """48x48, 알파 0/255, 도트 2px(최근접 2배), 64색 이하. 그 전 무기·아이템 아이콘은 1px 도트였다(2px 격자 일치 0.79~0.87)."""
    for n in ALL:
        a = _a(n)
        assert a.shape[:2] == (48, 48), n
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, n
        assert (a[0::2, 0::2] == a[1::2, 1::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), n
        assert len(np.unique(a[a[:, :, 3] == 255][:, :3], axis=0)) <= 64, n


def test_no_floating_specks_and_centered():
    """떠 있는 조각이 없다(무기·아이템은 한 덩어리, 형태 아이콘은 무기 + 금별 둘까지), 그림은 칸 가운데(좌우·위아래 여백 차이 2도트 이하)."""
    from scipy import ndimage
    for n in ALL:
        al = _a(n)[::2, ::2, 3] == 255
        _lab, k = ndimage.label(al, structure=np.ones((3, 3)))
        assert k <= (2 if n.startswith('icon_f_') else 1), (n, k)
        if n.startswith('icon_f_'):
            continue
        ys, xs = np.nonzero(al)
        assert abs(int(xs.min()) - (23 - int(xs.max()))) <= 2 and abs(int(ys.min()) - (23 - int(ys.max()))) <= 2, n


def test_weapon_icons_read_on_the_dark_hud():
    """무기 아이콘은 어두운 HUD 칸 위에 놓인다: 외곽선을 뺀 몸통의 평균 밝기가 충분하다(어두운 강철색 그대로는 칸에 묻혔다)."""
    for w in WEAPONS:
        a = _a(f'icon_w_{w}')
        rgb = a[a[:, :, 3] == 255][:, :3].astype(float)
        lum = rgb @ np.array([0.3, 0.6, 0.1])
        body = lum[lum >= 34]
        assert body.mean() >= 95, (w, body.mean())


def test_form_and_fury_icons_follow_the_new_art():
    """형태 아이콘 = 새 무기 아이콘 + 금별 (금별 자리 밖은 무기 아이콘과 같다), 분노 = 새 공격력 아이콘의 색만 보라로 (모양이 같다)."""
    for w in WEAPONS:
        f, base = _a(f'icon_f_{w}'), _a(f'icon_w_{w}')
        assert (f[20:] == base[20:]).all(), w                     # 금별은 왼쪽 위 9x9 도트(18px) 안
    assert (_a('icon_fury')[:, :, 3] == _a('icon_power')[:, :, 3]).all()
    assert not (_a('icon_fury') == _a('icon_power')).all()


def test_icon_paths_unchanged():
    """쓰는 코드는 같은 파일 이름을 부른다 (자리·크기 그대로)."""
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import items
    for item_id in items.ITEMS:
        path = os.path.join(ROOT, 'assets', items.icon_path(item_id))
        assert os.path.exists(path) and Image.open(path).size == (48, 48), item_id


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
