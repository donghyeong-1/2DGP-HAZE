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


# I1-fix(11/27): HUD 무기 칸에서 아이콘과 칸 바탕의 명암 차이. 칸 바탕은 실제 창에서 잰 값(어두운 방·밝은 벽 방 모두 약 (12, 16, 27),
# 칸 바탕 판이 불투명도 0.72~0.9라 방 색이 거의 비치지 않는다). 들지 않은 칸은 weapon_panel.ROW_ICON_IDLE(회백 곱 + 불투명도 0.6)을 적용한 뒤.
SLOT_BG = np.array([12, 16, 27], float)
LUM = np.array([0.3, 0.6, 0.1])
# I1 전(71b2bac) 코드 그림 무기 아이콘의 값: 든 칸, 들지 않은 칸 (평균 |아이콘 밝기 - 칸 바탕 밝기|, 불투명 픽셀 전부)
OLD_CONTRAST = {'pipe': (103.9, 43.1), 'pistol': (121.5, 50.0), 'gauntlet': (141.4, 57.8), 'chain': (82.2, 34.8)}


def slot_contrast(a):
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import weapon_panel
    tint, alpha = weapon_panel.ROW_ICON_IDLE
    px = a[a[:, :, 3] == 255][:, :3].astype(float)
    lb = SLOT_BG @ LUM
    held = np.abs(px @ LUM - lb).mean()
    idle_px = alpha * (px * np.array(tint, float) / 255) + (1 - alpha) * SLOT_BG
    idle = np.abs(idle_px @ LUM - lb).mean()
    return held, idle


def test_weapon_icons_read_on_the_dark_hud():
    """I1-fix: 무기 아이콘은 어두운 HUD 칸에서 곁눈으로 읽혀야 한다. 든 칸에서 칸 바탕과의 명암 차이가 I1 전 아이콘 이상,
    들지 않은 칸에서는 I1 전의 0.8배 이상 (I1 첫 적용은 든 칸 54~79로 I1 전의 0.56~0.65배였다)."""
    for w in WEAPONS:
        held, idle = slot_contrast(_a(f'icon_w_{w}'))
        old_held, old_idle = OLD_CONTRAST[w]
        assert held >= old_held, (w, round(held, 1), old_held)
        assert idle >= 0.8 * old_idle, (w, round(idle, 1), old_idle)


def test_weapon_icons_keep_their_shading():
    """밝혀도 평평한 흰색이 되지 않는다: 몸통(바깥 외곽선 안쪽)에 밝기 단계가 넷 이상 남고, 바깥 외곽선은 어둡다."""
    from scipy import ndimage
    for w in WEAPONS:
        a = _a(f'icon_w_{w}')[::2, ::2]
        op = a[:, :, 3] == 255
        inner = ndimage.binary_erosion(op)
        edge = op & ~inner
        lum = a[:, :, :3].astype(float) @ LUM
        assert np.median(lum[edge]) < 60, (w, np.median(lum[edge]))
        levels = np.unique(np.round(lum[inner] / 16))
        assert len(levels) >= 4, (w, levels)


def test_form_icons_follow_the_new_art():
    """형태 아이콘 = 새 무기 아이콘 + 금별 (금별 자리 밖은 무기 아이콘과 같다)."""
    for w in WEAPONS:
        f, base = _a(f'icon_f_{w}'), _a(f'icon_w_{w}')
        assert (f[20:] == base[20:]).all(), w                     # 금별은 왼쪽 위 9x9 도트(18px) 안


def test_power_and_fury_are_different_pictures():
    """I1-fix: 공격력(영구 +20%)과 균열의 분노(이번 판 +30%)는 효과가 다르니 모양부터 다르다 (I1에서는 분노가 공격력의 색만 바꾼 같은 그림이었다).
    두 실루엣이 겹치는 칸이 합친 칸의 80% 아래(둘 다 칸을 채운 덩어리라 0.65쯤, I1의 색만 바꾼 그림은 1.0), 분노는 보라가 주된 강조색, 공격력은 주황·빨강."""
    import colorsys
    p, f = _a('icon_power')[:, :, 3] > 0, _a('icon_fury')[:, :, 3] > 0
    assert (p & f).sum() / (p | f).sum() < 0.8, (p & f).sum() / (p | f).sum()

    def hues(n):
        a = _a(n)
        out = []
        for r, g, b in a[a[:, :, 3] == 255][:, :3] / 255:
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            if s > 0.45 and 0.2 < l < 0.9:
                out.append(h)
        return np.array(out)
    hp, hf = hues('icon_power'), hues('icon_fury')
    assert ((hf > 0.68) & (hf < 0.88)).mean() > 0.6, 'fury not violet'
    assert ((hp < 0.14) | (hp > 0.95)).mean() > 0.6, 'power not orange-red'


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
