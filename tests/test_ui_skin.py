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



# ----- 2026-11-27 H1 HUD: 그리기 호출 기록 (창 없이). docs/opus/TASKS.md '4차' H1 -----
class _Img:
    """assets.image 대신: 경로와 실제 크기만 가진 가짜 그림."""
    texture = None

    def __init__(self, path):
        self.path = path
        full = os.path.join(ROOT, 'assets', path)
        self.w, self.h = Image.open(full).size if os.path.exists(full) else (0, 0)

    def opacify(self, a):
        pass


class _Recorder:
    """assets의 그리기 함수를 가로채 (함수, 그림 경로, 인자) 줄을 모은다. text_width는 글자 수로 어림한다."""
    FNS = ('draw_image', 'draw_image_tinted', 'draw_image_added', 'draw_clip', 'draw_clip_added', 'draw_clip_tinted',
           'draw_rect_color', 'draw_rect_image', 'draw_text')

    def __enter__(self):
        import assets
        self.assets, self.log, self.saved = assets, [], {}
        for name in self.FNS + ('image', 'text_width'):
            self.saved[name] = getattr(assets, name)
        assets.image = lambda path: _Img(path)
        assets.text_width = lambda s, small=False, big=False: len(s) * (14 if small else 34 if big else 20)
        for name in self.FNS:
            setattr(assets, name, self._rec(name))
        return self

    def _rec(self, name):
        def f(*args, **kw):
            args = tuple(a.path if isinstance(a, _Img) else (tuple(int(v) for v in a) if isinstance(a, tuple) else a)
                         for a in args)
            self.log.append((name,) + tuple(round(a, 3) if isinstance(a, float) else a for a in args) + tuple(sorted(kw.items())))
        return f

    def __exit__(self, *exc):
        for name, fn in self.saved.items():
            setattr(self.assets, name, fn)

    def paths(self):
        return {a for row in self.log for a in row if isinstance(a, str) and a.endswith('.png')}

    def digest(self):
        import hashlib
        return hashlib.sha1(repr(self.log).encode('utf-8')).hexdigest()[:16]


def _hud_states():
    """HUD 장면 다섯: (이름, 준비 함수). 같은 시드·같은 값이라 늘 같은 호출이 나온다."""
    import curse
    import effects
    import game_world
    import items
    import mutations as mu
    import stage as stage_mod
    from player import Player
    from stage import Stage

    def make(seed, name='stage1', boss=False):
        game_world.clear()
        effects.reset()
        p = Player(0, 0, None)
        game_world.add_object(p, game_world.LAYER_PLAYER)
        st = Stage(p, seed=seed, name=name)
        st.start()
        if boss:
            st.enter_room(stage_mod.boss_room(st), 'L')
        p.set_loadout('pipe', 'pistol')
        p.mouse_screen = (900, 500)
        p.aura_time = 0.1
        return p, st

    def gauge(p, v):
        p.gauge.value = v
        p.gauge.zone = p.gauge._zone_of(v)

    def normal():
        p, st = make(3)
        gauge(p, 38)
        p.hp = p.max_hp * 0.7
        return p, st, None

    def critical():
        p, st = make(4, 'stage2')
        gauge(p, p.gauge.cap - config.CRITICAL_MARGIN + 3)
        p.hp = p.max_hp * 0.2
        return p, st, None

    def fade_items_curse():
        p, st = make(5)
        for it in ('cap', 'absorb', 'steady', 'power', 'power'):
            items.apply(p, it)
        mu.give(p, 'tide_cost')
        curse.take(p, curse.CARD + 'frail')
        gauge(p, 9)
        p.swap_weapon(0)
        p.swap_cool = 0.3
        return p, st, ('absorb', '흡수 효율')

    def enhanced():
        p, st = make(6)
        p.set_loadout('gauntlet', 'chain')
        gauge(p, 90)
        p.gauge.use_enhance()
        p.gauge.use_enhance()
        p.dash_slots = 0
        return p, st, None

    def boss():
        p, st = make(7, 'stage3', boss=True)
        gauge(p, 55)
        if st.boss is not None:
            st.boss.hp = st.boss.max_hp * 0.6
        return p, st, None

    return [('normal', normal), ('critical', critical), ('fade_items_curse', fade_items_curse), ('enhanced', enhanced), ('boss', boss)]


def _hud_log(skin_name, state):
    """그 스킨으로 GameUI 한 장면을 그린 호출 기록."""
    import ui

    def go():
        p, st, pick = state()
        hud = ui.GameUI(p, st)
        if pick:
            hud.show_pickup(*pick)
            hud.update(0.5)
        with _Recorder() as r:
            hud.draw()
        return r
    return _with_skin(skin_name, go)



def _kit_log(skin_name):
    """메뉴·고르는 화면이 쓰는 hud_kit 함수를 모두 한 번씩 그린 기록 (이번에 바꾸지 않는 화면의 몫)."""
    def go():
        with _Recorder() as r:
            for kind in hud_kit.KITS:
                hud_kit.panel(kind, 100, 100, 300, 120)
            hud_kit.bar('red', 10, 10, 200, 12, 0.4)
            hud_kit.fill('cyan', 10, 40, 150, 16)
            hud_kit.tag(50, 50, 220)
            hud_kit.strip(60, 60, 400)
            hud_kit.select_mark(70, 70, 360, 500, (200, 100, 50))
            hud_kit.keycap(80, 80, 'Esc', hot=True)
            hud_kit.keycap(80, 120, 'Q', hot=False)
            hud_kit.footer([('Enter', '확인'), ('Esc', '뒤로')])
            hud_kit.card(200, 200, 400, 300, '제목')
            hud_kit.pill(300, 300, 120, 40, '켜기', True, focus=True)
            hud_kit.pill(300, 340, 120, 40, '끄기', False)
            hud_kit.row(400, 400, 600, 50, True)
            hud_kit.row(400, 460, 600, 50, False)
            hud_kit.marker(500, 500)
            hud_kit.icon('uc_heart', 10, 10)
            hud_kit.backdrop()
            hud_kit.heading(100, 900, '일시정지', '부제')
            b = hud_kit.Button('go', '계속하기', 700, 500)
            b.draw(True)
            b.draw(False, left=True)
            b.draw(True, left=True)
            hud_kit.text(10, 10, '글자', (255, 255, 255), small=True, right=True)
        return r
    return _with_skin(skin_name, go)


def _room_reward_log(skin_name):
    """문 위 보상 판 (room.Room._draw_reward)."""
    import room as room_mod

    def go():
        with _Recorder() as r:
            room_mod.Room._draw_reward(None, 'L', 'mutation', 600, 300)
            room_mod.Room._draw_reward(None, 'U', 'shards', 900, 300)
        return r
    return _with_skin(skin_name, go)


def _hint_log(skin_name):
    """왼쪽 위 처음 안내 카드 (tutorial.Tutorial.draw)."""
    import tutorial

    def go():
        t = tutorial.Tutorial.__new__(tutorial.Tutorial)
        t.current, t.left = 'gauge', config.HINT_TIME * 0.5
        with _Recorder() as r:
            t.draw()
        return r
    return _with_skin(skin_name, go)

# 고치기 전(2026-11-27, d9ad0d7)의 기록. 옛 스킨 셋은 H1 뒤에도 이 값 그대로여야 한다 (픽셀 단위로 같은 화면)
HUD_DIGEST = {('plate', 'normal'): '26f48c155b548dbc', ('plate', 'critical'): 'c7c9e8dc8033946b',
              ('plate', 'fade_items_curse'): '507c647ff1e06ab9', ('plate', 'enhanced'): '9f3eb5f4c7a35eea', ('plate', 'boss'): 'e48cdfba75514510',
              ('plate_code', 'normal'): '3c4cf4184ede1ad8', ('plate_code', 'critical'): '6803fdc3f439077d',
              ('plate_code', 'fade_items_curse'): '408168d06e0487fc', ('plate_code', 'enhanced'): '742090c564486360',
              ('plate_code', 'boss'): '9df63654f52b21eb',
              ('crystal', 'normal'): 'dc045e05fd3d1a8a', ('crystal', 'critical'): 'e2066d47b48a3578',
              ('crystal', 'fade_items_curse'): '7a3f2c7088ea11c0', ('crystal', 'enhanced'): 'fdec8aa4c167bf16',
              ('crystal', 'boss'): '633923b39603851e'}
KIT_DIGEST = {'mist': 'c72452ec0c9efa8d', 'plate': 'c72452ec0c9efa8d', 'plate_code': 'c78add1ee756ab8f', 'crystal': 'c418f00f62897b83'}
ROOM_DIGEST = {'plate': '06c962c248b65ac5', 'plate_code': '6456ff80e5f3747d', 'crystal': 'de35a11ee146a771'}
HINT_DIGEST = 'e4d287488ee5b79c'                 # 처음 안내 카드: 옛 스킨 셋 모두 같다

MIST_HUD_TONES = ('line', 'dim', 'hot', 'red', 'cyan', 'gold', 'e1', 'e2', 'e3')
MIST_HUD_PARTS = (['um_hud_frame_' + t for t in MIST_HUD_TONES] +
                  [f'um_fill_{c}_{h}' for c in ('red', 'orange', 'gray', 'cyan', 'white', 'boss', 'blue', 'violet', 'empty')
                   for h in hud_kit.FILL_HEIGHTS] +
                  ['um_dash_on', 'um_dash_off', 'um_combo_on', 'um_combo_off', 'um_combo_fin', 'um_dot_off'])
# 판·틀이 아닌 작은 그림: mist HUD에서도 철판 것을 그대로 쓴다 (하트·물약·조준점·미니맵 방 표시·조각·고농도·바늘)
PLATE_ICONS_OK = ('up_mut_', 'up_heart', 'up_potion_', 'up_reticle_', 'up_map_', 'up_shard', 'up_diamond', 'up_needle')


def test_h1_mist_hud_parts_exist_and_follow_pixel_rules():
    """(1) mist HUD 부품(um_hud_*, um_fill_*, 작은 표시)이 있고 픽셀 규칙(알파 0/255, 2px 격자, 64색 이하)을 지킨다.
    철판 것과 이름이 겹치지 않고, 작은 표시는 철판 것과 크기가 같다(자리가 그대로)."""
    for n in MIST_HUD_PARTS:
        a = np.array(Image.open(os.path.join(UI, n + '.png')).convert('RGBA'))
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, n
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), n
        assert len({tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}) <= 64, n
        assert n not in MIST_PARTS, n
        plate = os.path.join(UI, 'up_' + n[3:] + '.png')
        if n.startswith(('um_dash', 'um_combo', 'um_dot', 'um_fill')):
            assert Image.open(plate).size == (a.shape[1], a.shape[0]), n
        rgb = a[a[:, :, 3] > 0][:, :3]
        assert not (rgb == hud_kit.YELLOW).all(axis=1).any(), n            # 경고 노랑은 mist HUD에서 쓰지 않는다


def test_h1_mist_hud_frame_is_one_thin_line_one_color_and_empty_inside():
    """(2) mist 판 테두리: 변은 도트 1칸(화면 2px) 한 줄, 한 색, 속은 비어 있다(바탕은 hud_panel이 한 장으로 깐다).
    판 하나를 그리면 바탕 사각형은 딱 한 번, 한 색이다."""
    for t in MIST_HUD_TONES:
        a = np.array(Image.open(os.path.join(UI, f'um_hud_frame_{t}.png')).convert('RGBA'))
        h, w = a.shape[:2]
        for line in (a[h // 2, :, 3], a[:, w // 2, 3]):
            assert len(np.nonzero(line)[0]) == 4, (t, np.nonzero(line)[0])     # 양쪽 변이 각각 2px
        assert not a[2:h - 2, 2:w - 2, 3].any(), t
        assert len({tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}) == 1, t
    r = _with_skin('mist', lambda: _draw_with_recorder(lambda: hud_kit.hud_panel('slot', 100, 100, 92, 92, tone='hot')))
    rects = [row for row in r.log if row[0] == 'draw_rect_color']
    assert len(rects) == 1, rects
    assert rects[0][1:5] == (102, 102, 88, 88), rects                   # 테두리 2px 안쪽 전체
    assert all(row[1] == 'ui/um_hud_frame_hot.png' for row in r.log if row[0] == 'draw_clip')


def _draw_with_recorder(fn):
    with _Recorder() as r:
        fn()
    return r


def test_h1_mist_hud_calls_no_plate_frames():
    """(3) mist일 때 HUD(GameUI)·문 위 보상 판·처음 안내 카드가 철판 판·틀(upx_*, up_ 판·막대·띠)을 부르지 않는다.
    갈래 아이콘(up_mut_*)과 판이 아닌 작은 그림은 예외. 경고 노랑도 쓰지 않는다."""
    logs = [_hud_log('mist', st) for _name, st in _hud_states()] + [_room_reward_log('mist'), _hint_log('mist')]
    for r in logs:
        for path in r.paths():
            name = os.path.basename(path)
            assert not name.startswith('upx_'), path
            assert not name.startswith('up_') or name.startswith(PLATE_ICONS_OK), path
        for row in r.log:
            assert hud_kit.YELLOW not in row, row
    paths = set().union(*(r.paths() for r in logs))
    assert 'ui/um_hud_frame_line.png' in paths and 'ui/um_hud_frame_hot.png' in paths
    assert any(p.startswith('ui/um_fill_') for p in paths)


def test_h1_old_skins_draw_the_same_hud():
    """(4) 'plate'·'plate_code'·'crystal'은 HUD를 고치기 전과 똑같이 그린다 (그리기 호출 기록이 같다 = 픽셀 단위로 같은 화면)."""
    for name, st in _hud_states():
        for skin_name in ('plate', 'plate_code', 'crystal'):
            assert _hud_log(skin_name, st).digest() == HUD_DIGEST[(skin_name, name)], (skin_name, name)
    for skin_name in ('plate', 'plate_code', 'crystal'):
        assert _room_reward_log(skin_name).digest() == ROOM_DIGEST[skin_name], skin_name
        assert _hint_log(skin_name).digest() == HINT_DIGEST, skin_name


def test_h1_menus_and_pickers_keep_their_parts_in_every_skin():
    """이번에 바꾸지 않는 화면(일시정지·설정·상점·형태 선택·결과·크레딧·은신처 메뉴·대화)이 쓰는 hud_kit 함수는
    mist를 포함한 네 스킨 모두에서 고치기 전과 같은 것을 그린다."""
    for skin_name, want in KIT_DIGEST.items():
        assert _kit_log(skin_name).digest() == want, skin_name

if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
