"""Q1 소품 그림 다시 뽑기 (2026-11-27, docs/opus/TASKS.md '4차' Q1).

은신처 무기 걸이·연습장 표지판, 장치(상자·증기 분출구·감시 레이저), 진열대를 PixelLab 그림으로 바꿨다(tools/apply_pixellab_props.py).
그림이 바뀌어도 서는 자리·누르는 자리·닿는 자리는 그대로이고, 상태 그림(부서짐·달아오름·품절)은 같은 그림에서 나와 모양이 어긋나지 않는다.
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

UI = os.path.join(ROOT, 'assets', 'ui')
PROPS = ('hideout_armory', 'hideout_practice', 'device_crate', 'device_crate_broken', 'device_vent', 'device_vent_hot',
         'device_laser', 'pedestal_gold', 'pedestal_shop', 'pedestal_gone', 'pedestal_gone_shop')


def _a(name):
    return np.array(Image.open(os.path.join(UI, name + '.png')).convert('RGBA'))


def test_props_follow_pixel_rules():
    """알파 0/255, 2px 격자(최근접 2배), 64색 이하."""
    for n in PROPS:
        a = _a(n)
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, n
        h, w = a.shape[:2]
        assert h % 2 == 0 and w % 2 == 0, n
        assert (a[0::2, 0::2] == a[1::2, 1::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), n
        assert len(np.unique(a[a[:, :, 3] == 255][:, :3], axis=0)) <= 64, n


def test_props_stand_on_their_anchor():
    """게임은 그림의 가운데 아래를 기준점으로 그린다: 바닥에 서는 것은 맨 아래 줄이 차 있고, 천장에 달린 레이저는 맨 위 줄이 차 있다.
    가로로는 그림이 기준점 둘레에 고르게 놓인다(좌우 여백 차이 4px 이하)."""
    for n in PROPS:
        a = _a(n)[:, :, 3]
        if n == 'device_laser':
            assert a[0].any(), n
        else:
            assert a[-1].any(), n
        xs = np.nonzero(a.any(axis=0))[0]
        assert abs(int(xs.min()) - (a.shape[1] - 1 - int(xs.max()))) <= 4, n


def test_state_images_share_one_shape():
    """상태 그림은 같은 그림에서: 분출구 달아오름·품절 진열대는 모양(알파)이 똑같고, 부서진 상자는 같은 캔버스·같은 바닥."""
    for a, b in (('device_vent', 'device_vent_hot'), ('pedestal_gold', 'pedestal_gone'), ('pedestal_shop', 'pedestal_gone_shop')):
        assert (_a(a)[:, :, 3] == _a(b)[:, :, 3]).all(), (a, b)
        assert not (_a(a) == _a(b)).all(), (a, b)
    assert _a('device_crate').shape == _a('device_crate_broken').shape
    assert _a('device_crate_broken')[-1, :, 3].any()
    for n in ('pedestal_gold', 'pedestal_shop', 'pedestal_gone', 'pedestal_gone_shop'):
        assert _a(n).shape[:2] == (150, 120), n


def test_interaction_spots_unchanged():
    """그림이 바뀌어도 누르는 자리·닿는 자리는 그대로다 (Q1 전 값)."""
    import config
    import npc
    import pedestal
    import importlib.util
    spec = importlib.util.spec_from_file_location('hideout_stage', os.path.join(ROOT, 'data', 'stages', 'hideout.py'))
    hs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hs)
    assert npc.INTERACT_RANGE == 120
    assert dict((k, c) for k, c in hs.NPCS) == {'mechanic': 9, 'keeper': 17, 'archivist': 25, 'armory': 13, 'practice': 21}
    assert (pedestal.INTERACT_RANGE, pedestal.INTERACT_HEIGHT) == (110, 170)
    assert (config.CRATE_REACH, config.CRATE_REACH_FAR) == (170, 620)
    assert (config.VENT_HALF_WIDTH, config.VENT_HEIGHT) == (40, 260)
    assert config.LASER_HALF_WIDTH == 22


def _npc_draw(kind, first='pipe', second='pistol'):
    import meta
    import npc as npc_mod
    from test_ui_skin import _Img, _Recorder, _with_skin

    class P:
        x, y = 2000, 100                       # 멀리 (안내 글자 없이)
    meta.ensure_loaded()
    meta.state['start_first'], meta.state['start_weapon'] = first, second
    n = npc_mod.NPC(kind, 600, 100)
    n.player = P()

    def go():
        import assets
        old = assets.outline_image
        try:
            assets.outline_image = lambda rel, *a, **k: _Img(rel)
            with _Recorder() as r:
                n.draw()
            return r
        finally:
            assets.outline_image = old
    return _with_skin('mist', go)


def test_armory_and_practice_draw_their_pixellab_art():
    """무기 걸이·연습장 표지판은 PixelLab 그림 한 장을 기준점에 그린다 (사각형으로 그린 틀·과녁·무기 아이콘이 없다)."""
    import meta
    saved = dict(meta.state) if meta.state else None
    try:
        for kind, img in (('armory', 'ui/hideout_armory.png'), ('practice', 'ui/hideout_practice.png')):
            r = _npc_draw(kind)
            rows = [row for row in r.log if row[0] == 'draw_image']
            assert rows and rows[0][1:4] == (img, 600, 100), (kind, rows)
            assert not any(p.startswith('ui/icon_w_') for p in r.paths()), kind
        # 걸이의 표시: 두 칸에 든 무기 아래에 하나씩 (네 무기가 모두 걸려 있다)
        for first, second, n in (('pipe', 'pistol', 2), ('chain', None, 1), ('gauntlet', 'chain', 2)):
            r = _npc_draw('armory', first, second)
            marks = [row for row in r.log if row[0] == 'draw_rect_color']
            assert len(marks) == n, (first, second, marks)
        import npc as npc_mod
        assert set(npc_mod.RACK_SLOTS) == {'pipe', 'pistol', 'gauntlet', 'chain'}
        xs = [npc_mod.RACK_SLOTS[w][0] for w in ('pipe', 'pistol', 'gauntlet', 'chain')]
        assert xs == sorted(xs)                                  # 왼쪽부터 철파이프·쌍권총·건틀릿·사슬
    finally:
        if saved is not None:
            meta.state.clear()
            meta.state.update(saved)


def test_pedestal_icon_sits_on_the_top_surface():
    """진열대 아이콘은 받침 윗면에 놓인다: 아이콘의 그림 아래 끝이 받침 가운데 윗면과 4px 안."""
    import pedestal
    icon = np.array(Image.open(os.path.join(UI, 'icon_cap.png')).convert('RGBA'))[:, :, 3]
    margin = icon.shape[0] - 1 - int(np.nonzero(icon.any(axis=1))[0].max())     # 아이콘 아래 빈 줄
    for kind in ('gold', 'shop'):
        a = _a(f'pedestal_{kind}')[:, :, 3]
        top = a.shape[0] - int(np.nonzero(a[:, a.shape[1] // 2])[0].min())       # 가운데 열 윗면 (발에서 px)
        assert abs(pedestal.ICON_Y[kind] + margin - top) <= 4, (kind, pedestal.ICON_Y[kind], margin, top)


def test_sold_out_shop_uses_its_own_dim_counter():
    """품절 정비방 진열대는 어두운 선반(pedestal_gone_shop), 황금방·균열방에서 가져간 것은 어두운 제단(pedestal_gone)."""
    import pedestal
    from test_ui_skin import _Recorder
    for mode, img in (('shop', 'ui/pedestal_gone_shop.png'), ('gold', 'ui/pedestal_gone.png'), ('rift', 'ui/pedestal_gone.png')):
        ped = pedestal.Pedestal(800, 300, 'cap', mode)
        ped.gone = True
        with _Recorder() as r:
            ped.draw()
        assert r.log[0][1] == img, (mode, r.log[0])


FOOT_X = {'anvil': 56, 'brazier': 50}     # Q1 전(Codex T28) 그림의 발 가운데 x (캔버스 왼쪽에서 px)


def test_hideout_anvil_and_brazier_keep_their_footing():
    """은신처 모루·화로(움직이는 소품 4장): 그림 아래 끝이 기준점보다 2px 아래(옛 Codex 그림과 같다 = 바닥에 서는 자리 그대로),
    발의 가로 가운데는 옛 그림의 발 가운데에서 2px 안. 네 장은 같은 크기이고 몸통(모루 전부, 화로 그릇·다리)은 장마다 똑같다(불똥·불꽃만 움직인다)."""
    import props_anim
    for prop, still_from in (('anvil', None), ('brazier', 70)):      # 화로 그릇 윗줄 = 캔버스 66px (원본 32줄)
        ax, ay = props_anim.ANCHOR[prop]
        w, h = props_anim.SIZE[prop]
        frames = [np.array(Image.open(os.path.join(ROOT, 'assets', 'props', f'hideout_{prop}_{i}.png')).convert('RGBA'))
                  for i in range(1, 5)]
        for f in frames:
            assert f.shape[:2] == (h, w), (prop, f.shape)
            al = f[:, :, 3]
            ys, xs = np.nonzero(al)
            assert int(ys.max()) + 1 - ay == 2, (prop, ys.max(), ay)
            low = ys >= ys.max() - 20                                   # 발 둘레의 가로 가운데
            assert abs((int(xs[low].min()) + int(xs[low].max()) + 1) / 2 - FOOT_X[prop]) <= 2, prop
        if prop == 'brazier':
            for f in frames[1:]:
                assert (f[still_from:] == frames[0][still_from:]).all(), prop
        else:
            body = [f[:, :, 3] > 0 for f in frames]
            common = np.logical_and.reduce(body)
            assert common[ay - 40:].sum() == body[0][ay - 40:].sum(), prop     # 모루 몸통(아래 40px)은 장마다 같다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
