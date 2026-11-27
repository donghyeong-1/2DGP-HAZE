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


# ----- 2026-11-27 M1 메뉴 화면: 일시정지·설정·키 설정·결과·크레딧 (docs/opus/TASKS.md '4차' M1) -----
# 화면마다 draw()를 그리기 호출 기록기로 감싸 부른다. 아래에 깔리는 화면(멈춘 게임·타이틀)은 빼고 그 화면이 그리는 것만.
def _quiet(mod):
    """그 모드의 clear_canvas·update_canvas를 잠시 비운다 (창 없이 draw()를 부르려고)."""
    saved = {n: getattr(mod, n) for n in ('clear_canvas', 'update_canvas') if hasattr(mod, n)}
    for n in saved:
        setattr(mod, n, lambda: None)
    return saved


def _restore(mod, saved):
    for n, f in saved.items():
        setattr(mod, n, f)


def _temp_saves():
    import tempfile
    import meta
    import options
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')
    options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
    meta.reset()
    options.ensure_loaded()


def _draw_log(mod, prepare=None, under=None):
    """mod.draw()의 호출 기록. prepare()로 상태를 맞춘다. under: 아래에 깔리는 화면 (없으면 None)."""
    import transition
    _temp_saves()
    saved = _quiet(mod)
    old_under = getattr(mod, '_under', None)
    try:
        if hasattr(mod, '_under'):
            mod._under = under
        if prepare:
            prepare()
        transition._left = 0.0
        with _Recorder() as r:
            mod.draw()
        return r
    finally:
        _restore(mod, saved)
        if hasattr(mod, '_under'):
            mod._under = old_under


def _pause_log(skin_name, sel=0, build=False, ask=None):
    import pause_mode as pm
    import play_mode

    def go():
        p = st = None
        if build:
            p, st, _pick = dict(_hud_states())['fade_items_curse']()
        old = getattr(play_mode, 'player', None), getattr(play_mode, 'stage', None), pm.draw_frozen
        play_mode.player, play_mode.stage = p, st
        pm.draw_frozen = lambda: None                              # 멈춘 게임 화면은 빼고
        try:
            def prep():
                pm.enter()
                pm.selected = sel
                if ask:
                    pm.run(ask)                                    # '포기하려면 한 번 더 누르세요'
            return _draw_log(pm, prep)
        finally:
            play_mode.player, play_mode.stage, pm.draw_frozen = old
    return _with_skin(skin_name, go)


def _options_log(skin_name, sel=0):
    import options_mode as om

    def prep():
        om.selected = sel
    return _with_skin(skin_name, lambda: _draw_log(om, prep))


def _keys_log(skin_name, row=0, col=0, listen=False, message=''):
    import keybinds
    import keys_mode as km

    def prep():
        km.row, km.col, km.message = row, col, message
        km.listening = (keybinds.IDS[row], col) if listen else None
    return _with_skin(skin_name, lambda: _draw_log(km, prep))


def _ending_log(skin_name, result='dead', choosing=False, kept=None, line='', hint=''):
    import ending_mode as em

    def prep():
        em.result = result
        em.reward = 12
        em.summary = [('도달한 구역', '구역 2 · 공장'), ('걸린 시간', '12:34'), ('클리어한 방', '9'), ('처치한 적', '41'),
                      ('처치한 보스·관문', '1'), ('받은 헤이즈 결정', '+12')] + ([('사망 원인', '크래셔의 강타')] if result == 'dead' else [])
        em.choices = ['absorb', 'power', None] if choosing else []
        em.choice = 1 if choosing else 0
        em.choosing = choosing
        em.kept = kept
        em.ending_line = line
        em.easy_hint = hint
    return _with_skin(skin_name, lambda: _draw_log(em, prep))


def _credits_log(skin_name, scroll=0.0):
    import credits_mode as cm

    def prep():
        cm.scroll = scroll
        cm._scene = cm.scene_for(scroll)
    return _with_skin(skin_name, lambda: _draw_log(cm, prep))


class _FakeStorm:
    """타이틀 번개를 원하는 단계에 세워 둔다."""
    def __init__(self, phase):
        self._phase = phase

    def phase(self):
        return self._phase

    def flash_plate(self):
        return 1 if self._phase == 'flash' else None

    def bolt_plate(self):
        return 2 if self._phase in ('bolt', 'dark') else None

    def glow_alpha(self):
        return 0.5 if self._phase == 'glow' else 0.0

    def update(self, dt):
        pass


def _title_log(skin_name, sel=0, phase=None):
    import title_mode as tm

    def go():
        import sprites
        old = tm._storm[0], tm._rain[0], tm.selected, tm.age, sprites.draw
        tm._storm[0], tm._rain[0], tm.selected, tm.age = _FakeStorm(phase), None, sel, 1.25
        try:
            with _Recorder() as r:
                sprites.draw = lambda *a, **k: r.log.append(('sprite',) + a)      # 철판 타이틀의 주인공 (창 없이는 외곽선을 못 굽는다)
                tm.draw_frozen()
            return r
        finally:
            tm._storm[0], tm._rain[0], tm.selected, tm.age, sprites.draw = old
    return _with_skin(skin_name, go)


def _menu_logs(skin_name):
    """네 화면(+키 설정)의 장면별 기록 {장면: 기록}."""
    import keybinds
    return {
        'pause_0': _pause_log(skin_name, 0), 'pause_build_2': _pause_log(skin_name, 2, build=True),
        'pause_ask': _pause_log(skin_name, 3, ask='title'),
        'options_0': _options_log(skin_name, 0), 'options_music': _options_log(skin_name, 2),
        'options_keys': _options_log(skin_name, 10), 'options_back': _options_log(skin_name, 11),
        'keys_0': _keys_log(skin_name), 'keys_listen': _keys_log(skin_name, 3, 1, listen=True),
        'keys_buttons': _keys_log(skin_name, len(keybinds.IDS), 1, message='기본 키로 되돌렸습니다'),
        'ending_dead_choose': _ending_log(skin_name, 'dead', choosing=True, hint='초보자 모드 안내'),
        'ending_dead': _ending_log(skin_name, 'dead', kept='absorb', hint='초보자 모드 안내'),
        'ending_clear': _ending_log(skin_name, 'clear', line='탈출 뒤 한 줄'),
        'credits_0': _credits_log(skin_name, 0.0), 'credits_mid': _credits_log(skin_name, 1400.0),
    }


def _other_logs(skin_name):
    """이번에 바꾸지 않는 화면: 은신처 NPC 넷, 연습 메뉴, 효과음 듣기, 증강·형태·저주 카드."""
    import curse
    import forms
    import mutation_mode as mm
    import mutations as mu
    import npc_mode
    import practice_mode
    import sfx_mode
    out = {}
    for kind in ('mechanic', 'keeper', 'armory', 'archivist'):
        def prep(kind=kind):
            npc_mode.kind, npc_mode.selected, npc_mode.note, npc_mode.result = kind, 1, '', None
        out['npc_' + kind] = _with_skin(skin_name, lambda: _draw_log(npc_mode, prep))

    p = dict(_hud_states())['normal']()[0]

    def prac():
        practice_mode.selected, practice_mode.player = 2, p
    out['practice'] = _with_skin(skin_name, lambda: _draw_log(practice_mode, prac))

    def sfx():
        sfx_mode.cat, sfx_mode.row, sfx_mode.marks = 0, 1, {}
    out['sfx'] = _with_skin(skin_name, lambda: _draw_log(sfx_mode, sfx))
    ids_sets = {'augment': list(mu.MUTATIONS)[:3],
                'form': [forms.CARD + w for w in list(forms.FORMS)[:2]],
                'curse': list(mu.MUTATIONS)[3:5] + [curse.CARD + next(iter(curse.CURSES))]}
    for name, ids in ids_sets.items():
        def mut(ids=ids):
            mm.setup(p, ids)
            mm.age = 5.0
            mm.selected = 1
        out['cards_' + name] = _with_skin(skin_name, lambda: _draw_log(mm, mut))
    return out


# 고치기 전(2026-11-27, 712637e)의 기록 (위 _menu_logs·_other_logs·_title_log). M1 뒤에도 이 값 그대로여야 한다
MENU_DIGEST = {
    'plate': {'pause_0': 'b19ee9dc864b0a01', 'pause_build_2': '6ae6f7ab6ef0d0b7', 'pause_ask': '66ee9d32b8a33b9f', 'options_0': '8cbd7f0df2cfc6fc', 'options_music': 'a419f76afd494218', 'options_keys': '9f7173efe3492c98', 'options_back': '8a5eee2d0a367c12', 'keys_0': 'ef308dbcb9260879', 'keys_listen': 'd295e3923ad3762e', 'keys_buttons': '752615646c0755d4', 'ending_dead_choose': 'af721d2263e1944c', 'ending_dead': '4f2ce782d823d96f', 'ending_clear': '457569a5e2438d30', 'credits_0': '172500abe524364a', 'credits_mid': '7896f4a09436720a'},
    'plate_code': {'pause_0': '8df4193d19bdfbf2', 'pause_build_2': '34455f35d14d2f5a', 'pause_ask': '5082a77b5ab0160b', 'options_0': 'ab08bd79454e75cb', 'options_music': 'ef857f40dc5b69ea', 'options_keys': '4cb748417456d6c2', 'options_back': '24a49e43e2c2a66d', 'keys_0': 'fed31c421bb366af', 'keys_listen': '2a3a765ce28e8d3a', 'keys_buttons': '05357bebb0facb1d', 'ending_dead_choose': 'a47a3ae8591d9019', 'ending_dead': '15808d816142bca1', 'ending_clear': 'e1b2c56e58772ddf', 'credits_0': '172500abe524364a', 'credits_mid': '7896f4a09436720a'},
    'crystal': {'pause_0': '79c408f0d295d530', 'pause_build_2': '9987c6242ccd28c0', 'pause_ask': '333c32d83894f2d4', 'options_0': 'a0c7365cc9e7ffbb', 'options_music': '5634f126abf58c51', 'options_keys': 'c21e3299723bf298', 'options_back': 'bc0eff4b8c851f33', 'keys_0': '6dd4d230b55172a7', 'keys_listen': '59e8301e6d732c38', 'keys_buttons': 'f002538b74e0e07a', 'ending_dead_choose': 'e86e9f0d8a7d9b22', 'ending_dead': 'bf3a7d649011bd3b', 'ending_clear': 'd88bb8f7622d7c31', 'credits_0': '172500abe524364a', 'credits_mid': '7896f4a09436720a'},
}
OTHER_DIGEST = {
    'mist': {'npc_mechanic': '28af8461a02c3229', 'npc_keeper': 'cfa0ab2b66838723', 'npc_armory': '968fa2c2210cb7c4', 'npc_archivist': '21e97898001e6a97', 'practice': 'e9559cc8d678474f', 'sfx': '9a9457b7fddf7a23', 'cards_augment': 'c56ed617c57c2389', 'cards_form': 'c34bc28ac9fe489b', 'cards_curse': 'f791b2981770fab9'},
    'plate': {'npc_mechanic': '28af8461a02c3229', 'npc_keeper': 'cfa0ab2b66838723', 'npc_armory': '968fa2c2210cb7c4', 'npc_archivist': '21e97898001e6a97', 'practice': 'e9559cc8d678474f', 'sfx': '9a9457b7fddf7a23', 'cards_augment': '66dde66425db532b', 'cards_form': 'ae0723bb82b4dcb0', 'cards_curse': '555cccc3b76312d3'},
    'plate_code': {'npc_mechanic': '716d1cbb76959899', 'npc_keeper': '9bd792190691bf5d', 'npc_armory': '6c2ed9b37c52f713', 'npc_archivist': 'e1b19db44dcbd2fd', 'practice': '00d90b22a3d76598', 'sfx': 'eadf10acbcbf4be4', 'cards_augment': '56c1d0b20659a32a', 'cards_form': '5a00a1cd20b36e53', 'cards_curse': 'a6935aa1ce7013cb'},
    'crystal': {'npc_mechanic': '96e7246516e9d3e3', 'npc_keeper': '31561871fca6e4e8', 'npc_armory': '85f7f3ec6f0c1355', 'npc_archivist': '14ba1e5f05411fc7', 'practice': '65851386c8f25102', 'sfx': '0275367891d27066', 'cards_augment': '290c43e803d5ea39', 'cards_form': 'f159e81d34c0a9f9', 'cards_curse': 'f89e823a62aa03ca'},
}
TITLE_DIGEST = {
    'mist': {'0_None': '96332275734e9873', '0_bolt': 'a3d2af5695e9fdb6', '0_flash': 'c11c65208d8510e7', '0_glow': 'bb61df4537c82835', '0_dark': 'a3d2af5695e9fdb6', '2_None': 'fa00c5dac1455141', '2_bolt': '76a420dda14b725f', '2_flash': '683ccfdbc9a80c9c', '2_glow': 'e4aac5e20e64b8b0', '2_dark': '76a420dda14b725f'},
    'plate': {'0_None': '7953c8af79829697', '2_None': '07ca9bb3cb141af2'},
    'plate_code': {'0_None': '7a88abf1168794ce', '2_None': 'ee4dabfe94a926ac'},
    'crystal': {'0_None': 'cd03ff02e3c5e164', '2_None': '50542a0ca7b7705d'},
}
MENU_PLATE_OK = ('up_mut_',)                     # mist 메뉴 화면에서도 쓰는 철판 쪽 그림: 증강 갈래 아이콘(일시정지 '이번 판')


def test_m1_mist_menus_call_no_plate_parts():
    """(1) mist일 때 일시정지·설정·키 설정·결과·크레딧이 철판 판·띠·키캡·커서(upx_*, up_*)와 노란 꺾쇠(경고 노랑)를 부르지 않는다.
    타이틀과 같은 틀(네 귀퉁이 꺾쇠 um_bracket)과 글자 뒤 어둠(light/menu_shade_*)을 쓴다."""
    for scene, r in _menu_logs('mist').items():
        paths = r.paths()
        for path in paths:
            name = os.path.basename(path)
            assert not name.startswith(('upx_', 'uc_')), (scene, path)
            assert not name.startswith('up_') or name.startswith(MENU_PLATE_OK), (scene, path)
        for row in r.log:
            assert hud_kit.YELLOW not in row and hud_kit.YELLOW_LO not in row, (scene, row)
        assert 'ui/um_bracket.png' in paths, scene
        assert any(p.startswith('light/menu_shade_') for p in paths), scene


def _inverted_blocks(r):
    """기록에서 색 뒤집힌 블록(인광색 사각형)과 바로 뒤에 그 위에 쓴 어두운 글자: [(블록 폭, 글자 폭)]."""
    import mist_menu as mm
    out = []
    for i, row in enumerate(r.log):
        if row[0] != 'draw_rect_color' or row[5:6] != (mm.PH,) or row[4] < 20:       # 2px 밑줄·선은 뒤집힘이 아니다
            continue
        nxt = next(x for x in r.log[i + 1:] if x[0] == 'draw_text')
        assert nxt[4] == mm.PH_BG, (row, nxt)
        small = ('small', True) in nxt
        out.append((row[3], len(nxt[3]) * (14 if small else 20)))       # _Recorder의 글자 폭 어림과 같은 식
    return out


def test_m1_selected_item_is_inverted_only_as_wide_as_its_text():
    """(2) 고른 항목은 글자 폭 + 양옆 8px만 색을 뒤집는다 (길게 뻗는 띠 금지). 키 칸은 키캡 최소 폭 34px까지."""
    logs = _menu_logs('mist')
    for scene in ('pause_0', 'pause_build_2', 'pause_ask', 'options_0', 'options_music', 'options_keys', 'options_back',
                  'keys_0', 'keys_listen', 'keys_buttons', 'ending_dead_choose'):
        blocks = _inverted_blocks(logs[scene])
        assert blocks, scene
        for bw, tw in blocks:
            assert bw <= max(34, tw + 16), (scene, bw, tw)


def test_m1_old_skins_draw_the_same_menus():
    """(3) 'plate'·'plate_code'·'crystal'에서 네 화면(+키 설정)의 그리기 기록이 고치기 전과 같다."""
    for skin_name, want in MENU_DIGEST.items():
        got = {k: v.digest() for k, v in _menu_logs(skin_name).items()}
        assert got == want, (skin_name, [k for k in want if got.get(k) != want[k]])


def test_m1_unchanged_screens_draw_the_same_in_every_skin():
    """(4) 이번에 바꾸지 않는 화면(은신처 NPC 넷, 연습 메뉴, 효과음 듣기, 증강·형태·저주 카드)은 네 스킨 모두 고치기 전과 같다.
    HUD·문 위 보상 판·처음 안내 카드·메뉴 공통 hud_kit 함수(대화 창의 키캡·글자 포함)는 위 H1 테스트가 본다."""
    for skin_name, want in OTHER_DIGEST.items():
        got = {k: v.digest() for k, v in _other_logs(skin_name).items()}
        if skin_name == 'mist':                            # S1(11/27)이 mist의 NPC 창·연습·효과음을 바꿨다: 카드만 그대로
            want = {k: v for k, v in want.items() if k.startswith('cards_')}
            got = {k: v for k, v in got.items() if k in want}
        assert got == want, (skin_name, [k for k in want if got.get(k) != want[k]])


def test_m1_title_draws_the_same():
    """(5) 타이틀은 공통 부품을 꺼낸 뒤에도 고치기 전과 같다 (네 스킨, mist는 번개 단계마다, 고른 메뉴 둘)."""
    for skin_name, want in TITLE_DIGEST.items():
        got = {}
        for key in want:
            sel, ph = key.split('_', 1)
            got[key] = _title_log(skin_name, int(sel), None if ph == 'None' else ph).digest()
        assert got == want, (skin_name, [k for k in want if got[k] != want[k]])


def test_m1_menu_parts_follow_pixel_rules_and_shade_is_soft():
    """(6) 새 그림: 인광 테두리·막대 속(um_hud_frame_ph*, um_fill_phos_*)은 픽셀 규칙(알파 0/255, 2px 격자, 64색 이하),
    테두리는 한 줄·한 색·속 투명. 글자 뒤 어둠 조각 시트(빛 층 예외)는 가운데가 가장 진하고(k) 가장자리는 0, 체크무늬 없이 부드럽다."""
    import mist_menu as mm
    for n in ['um_hud_frame_ph', 'um_hud_frame_ph_dim'] + [f'um_fill_phos_{h}' for h in hud_kit.FILL_HEIGHTS]:
        a = np.array(Image.open(os.path.join(UI, n + '.png')).convert('RGBA'))
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, n
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), n
        assert len({tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}) <= 64, n
        if 'frame' in n:
            h, w = a.shape[:2]
            assert len(np.nonzero(a[h // 2, :, 3])[0]) == 4 and not a[2:h - 2, 2:w - 2, 3].any(), n
            assert len({tuple(c) for c in a[a[:, :, 3] > 0][:, :3]}) == 1, n
        else:
            assert Image.open(os.path.join(UI, f'um_fill_cyan_{n.rsplit("_", 1)[1]}.png')).size == (a.shape[1], a.shape[0]), n
    for kind, k in mm.SHADE_K.items():
        a = np.array(Image.open(os.path.join(ROOT, 'assets', 'light', f'menu_shade_{kind}.png')).convert('RGBA'))
        n = a.shape[0]
        assert a.shape[:2] == (n, n) and (n - mm.SHADE_MID) % 2 == 0, kind
        al = a[:, :, 3].astype(int)
        c = n // 2
        assert abs(al[c, c] - round(k * 255)) <= 1, kind                     # 가운데 = k (실행 중 사각형 한 장과 같다)
        assert al[0, :].max() == 0 and al[:, 0].max() == 0 and al[-1, :].max() == 0, kind
        row = al[c, :c]
        assert (np.diff(row) >= 0).all(), kind                              # 가장자리에서 가운데로 점점 진해진다 (디더 없음)
        assert len(np.unique(al)) > 40, kind                                # 계단 몇 개가 아니라 부드러운 알파
        assert (a[al > 0][:, :3] == mm.SHADE_COLOR).all(), kind
        r = (n - mm.SHADE_MID) // 2                                          # 변 조각은 길이 방향으로 같은 값 (이어 붙여도 이음매 없음)
        assert (al[:r, r:r + mm.SHADE_MID] == al[:r, r:r + 1]).all(), kind


def test_m1_menu_shade_tiles_without_gaps():
    """글자 뒤 어둠을 큰 상자로 깔아도 9칸 조각이 빈틈·겹침 없이 맞물린다 (그린 칸들 = 상자 + 둘레 번짐, 한 번씩)."""
    import mist_menu as mm

    def go():
        with _Recorder() as r:
            mm.shade(101, 203, 1377, 911)
        return r
    r = _with_skin('mist', go)
    R = Image.open(os.path.join(ROOT, 'assets', 'light', 'menu_shade_soft.png')).size[0] - mm.SHADE_MID   # 둘레 번짐 (화면 px)
    cover = np.zeros((1400, 1900), int)
    for row in r.log:
        if row[0] == 'draw_rect_color':
            x, y, w, h = row[1:5]
        else:
            x, y, w, h = row[6], row[7], row[4] * 2, row[5] * 2
        cover[y + 200:y + 200 + h, x + 200:x + 200 + w] += 1
    x0, y0, x1, y1 = 100, 202, 1378, 912
    want = np.zeros_like(cover)
    want[y0 - R + 200:y1 + R + 200, x0 - R + 200:x1 + R + 200] = 1
    assert (cover == want).all()



# ----- 2026-11-27 S1 고르는 화면과 남은 화면 (docs/opus/TASKS.md '4차' S1) -----
def _npc_log(skin_name, kind, sel=1, crystals=0, levels=None, note='', result=None, keeper=False, keepsake=None):
    """은신처 NPC 창 한 장면의 기록 (멈춘 은신처 화면은 빼고)."""
    import meta
    import npc_mode

    def prep():
        meta.state['crystals'] = crystals
        meta.state['keeper'], meta.state['keepsake'] = keeper, keepsake
        for k, v in (levels or {}).items():
            meta.state['levels'][k] = v
        npc_mode.kind, npc_mode.selected, npc_mode.note, npc_mode.result = kind, sel, note, result
    return _with_skin(skin_name, lambda: _draw_log(npc_mode, prep))


def _practice_log(skin_name, sel=2):
    import practice_mode
    p = dict(_hud_states())['normal']()[0]

    def prep():
        practice_mode.selected, practice_mode.player = sel, p
    return _with_skin(skin_name, lambda: _draw_log(practice_mode, prep))


def _sfx_log(skin_name, row=1, marks=None):
    import sfx_mode

    def prep():
        sfx_mode.cat, sfx_mode.row = 0, row
        sfx_mode.marks = dict(marks or {})
    return _with_skin(skin_name, lambda: _draw_log(sfx_mode, prep))


class _FakeBoss:
    kind = 'gatekeeper'


def _boss_lines_log(skin_name, done=True):
    """보스 등장씬 대사 단계 (위아래 검은 띠 + 이름·대사 + Enter 키 판)."""
    import boss_intro

    def go():
        b = boss_intro.BossIntro.__new__(boss_intro.BossIntro)
        b.step, b.t, b.age, b.landed = 'lines', 0.4, 3.0, True
        b.boss = _FakeBoss()
        b.lines = list(boss_intro.LINES['gatekeeper']['intro'])
        b.line_index = 0
        b.line_t = 99.0 if done else 0.3
        with _Recorder() as r:
            b.draw()
        return r
    return _with_skin(skin_name, go)


def _pedestal_log(skin_name, mode='shop', item='cap', gone=False):
    """진열대 하나 (가까이 선 주인공에게 이름·설명·안내가 뜬다)."""
    import camera
    import pedestal

    def go():
        p = dict(_hud_states())['normal']()[0]
        camera.x = camera.y = 0.0
        ped = pedestal.Pedestal(800, 300, item, mode, price=6 if mode == 'shop' else 0)
        ped.gone = gone
        p.x, p.y = 810, 310
        ped.player = p
        with _Recorder() as r:
            ped.draw()
        return r
    return _with_skin(skin_name, go)


def _s1_logs(skin_name):
    """S1에서 바꾸는 화면의 장면별 기록 {장면: 기록}."""
    import meta
    full = {k: meta.UPGRADES[k]['max'] for k in meta.ORDER[:1]}
    return {
        'npc_mech_buy': _npc_log(skin_name, 'mechanic', 0, crystals=40),
        'npc_mech_no': _npc_log(skin_name, 'mechanic', 0, crystals=3, levels=full, note='헤이즈 결정이 부족합니다', result='fail'),
        'npc_keeper_shut': _npc_log(skin_name, 'keeper', 0, crystals=3),
        'npc_keeper_open': _npc_log(skin_name, 'keeper', 0, crystals=30, keeper=True, keepsake='absorb'),
        'npc_archivist': _npc_log(skin_name, 'archivist', 1, crystals=14),
        'npc_archivist_last': _npc_log(skin_name, 'archivist', 3, crystals=14),
        'npc_armory_first': _npc_log(skin_name, 'armory', 0),
        'npc_armory_second': _npc_log(skin_name, 'armory', 5, note='시작 무기 변경: 철파이프 + 쌍권총', result='ok'),
        'npc_back': _npc_log(skin_name, 'mechanic', 4, crystals=40),
        'practice': _practice_log(skin_name, 2), 'practice_gauge': _practice_log(skin_name, 3),
        'sfx': _sfx_log(skin_name, 1, {}), 'sfx_marked': _sfx_log(skin_name, 12, {'swing_1': 'good', 'swing_2': 'bad'}),
        'boss_lines': _boss_lines_log(skin_name, True), 'boss_typing': _boss_lines_log(skin_name, False),
        'ped_shop': _pedestal_log(skin_name, 'shop', 'cap'), 'ped_gold': _pedestal_log(skin_name, 'gold', 'fury'),
        'ped_rift': _pedestal_log(skin_name, 'rift', 'power'), 'ped_gone': _pedestal_log(skin_name, 'shop', 'cap', gone=True),
    }


# 고치기 전(2026-11-27, 50fe67f)의 기록. 옛 스킨 셋은 S1 뒤에도 그대로 (진열대는 스킨과 상관없이 같았다)
S1_DIGEST = {
    'plate': {'npc_mech_buy': '4f5314f76e2a7077', 'npc_mech_no': '314c821562203ae9', 'npc_keeper_shut': 'cd5b7b541c40af84', 'npc_keeper_open': 'da7ac678eccaed13', 'npc_archivist': '47e437d979fc63a6', 'npc_archivist_last': '62942550f5f69262', 'npc_armory_first': '439dbba3040724d4', 'npc_armory_second': '3a5475ae22ca8613', 'npc_back': '690d068c83a433aa', 'practice': 'e9559cc8d678474f', 'practice_gauge': 'e911e4a65c1f79b8', 'sfx': '9a9457b7fddf7a23', 'sfx_marked': '39f7bcd9fda783a2', 'boss_lines': '9445d045dbf72914', 'boss_typing': '4df1020eed768fb9', 'ped_shop': '5394f43bf2ddc69a', 'ped_gold': 'b9ccfd9ddf62aaf9', 'ped_rift': 'f8879eb6c068b907', 'ped_gone': 'b0aa35ea40c8f3da'},
    'plate_code': {'npc_mech_buy': 'a16b6f9acf87dba7', 'npc_mech_no': 'cdfce17098319efb', 'npc_keeper_shut': 'fa73aa9e2755d0a6', 'npc_keeper_open': '04ef54d251b5c3f6', 'npc_archivist': '8892a3890506d8dd', 'npc_archivist_last': 'ff610a6c0a2a804d', 'npc_armory_first': 'b51e81b3684ed7f8', 'npc_armory_second': '1f4d63b47d9ee1df', 'npc_back': '34c1c9b2a44f09a7', 'practice': '00d90b22a3d76598', 'practice_gauge': '0be357627f8b97ad', 'sfx': 'eadf10acbcbf4be4', 'sfx_marked': '2788a1090e92b50e', 'boss_lines': 'fcbf4a962eb2cf83', 'boss_typing': '7e3e0e9e9beaf4ee', 'ped_shop': '5394f43bf2ddc69a', 'ped_gold': 'b9ccfd9ddf62aaf9', 'ped_rift': 'f8879eb6c068b907', 'ped_gone': 'b0aa35ea40c8f3da'},
    'crystal': {'npc_mech_buy': 'ec2ce8adf2918287', 'npc_mech_no': 'c518c1d107af02f3', 'npc_keeper_shut': '2dac496e4cfbcc38', 'npc_keeper_open': '10d3aa716277ef56', 'npc_archivist': '45b6a919d4ae55c9', 'npc_archivist_last': '674a9500a6e90d8a', 'npc_armory_first': 'db08a46a8785814f', 'npc_armory_second': '78c1966cca357d0c', 'npc_back': 'b89dc61c26fc6a37', 'practice': '65851386c8f25102', 'practice_gauge': '9a55970123f3455d', 'sfx': '0275367891d27066', 'sfx_marked': '86df89ba8866a045', 'boss_lines': '483a93bf8c0527e7', 'boss_typing': '076b56e29120a179', 'ped_shop': '5394f43bf2ddc69a', 'ped_gold': 'b9ccfd9ddf62aaf9', 'ped_rift': 'f8879eb6c068b907', 'ped_gone': 'b0aa35ea40c8f3da'},
}
# 이미 끝난 화면의 mist 기록 (S1 전, 50fe67f). 설정(options_*)은 묶음 5로 바뀌므로 뺀다
MIST_DONE_DIGEST = {
    'pause_0': '7c2a8885d1b28a99', 'pause_build_2': 'f9913e8d78a0b16a', 'pause_ask': '78b44769b58dffa7',
    'keys_0': '89e6b6949d456e3d', 'keys_listen': 'e52db5bf5ec26c81', 'keys_buttons': '793b1540dbcb3f05',
    'ending_dead_choose': 'b9e6f5c9ad866e37', 'ending_dead': '52682eb733096be5', 'ending_clear': '11eef79b43905daf',
    'credits_0': '9806d3b1e8a2a935', 'credits_mid': '0b0823fe314bdbc0',
    'hud_normal': '8efe4fcd6336eccb', 'hud_critical': 'b31072f9b278ac7c', 'hud_fade_items_curse': '3bb41f6c79aa52a0',
    'hud_enhanced': '865db9d39038e5d6', 'hud_boss': '00693a953f9a52ad', 'room_reward': 'a24a0f1ce3f66cfd', 'hint': 'dbe7a284f9ac069a',
}
# mist에서도 쓰는 철판 쪽 작은 그림 (판·틀·띠·키·노란 표시가 아니다). up_step_off는 증강 카드의 진행 칸(이미 끝난 화면이라 그대로 둔다)
MIST_PLATE_ICONS_OK = PLATE_ICONS_OK + ('up_step_off',)
PICK_PARTS = ('um_pick_cursor', 'um_pick_cursor_off')


def _mist_done_logs():
    out = {k: v for k, v in _menu_logs('mist').items() if not k.startswith('options_')}
    for name, st in _hud_states():
        out['hud_' + name] = _hud_log('mist', st)
    out['room_reward'] = _room_reward_log('mist')
    out['hint'] = _hint_log('mist')
    return out


def _assert_no_plate(scene, r, ok=('up_mut_',)):
    for path in r.paths():
        name = os.path.basename(path)
        assert not name.startswith(('upx_', 'uc_')), (scene, path)
        assert not name.startswith('up_') or name.startswith(ok), (scene, path)
    for row in r.log:
        assert hud_kit.YELLOW not in row and hud_kit.YELLOW_LO not in row, (scene, row)


def test_s1_mist_pick_screens_call_no_plate_parts():
    """(1) mist일 때 은신처 NPC 창 넷·연습 메뉴·효과음 듣기·보스 대사 띠·진열대 표시가 철판 판·틀·띠·키캡·커서(upx_*, up_*, uc_*)와
    경고 노랑을 부르지 않는다. NPC 창과 진열대는 가는 테두리 판(um_hud_frame_*), 연습·효과음은 감시 단말 틀(um_bracket)을 쓴다."""
    logs = _s1_logs('mist')
    for scene, r in logs.items():
        _assert_no_plate(scene, r)
        paths = r.paths()
        if scene.startswith('npc_'):
            assert any(p.startswith('ui/um_hud_frame_') for p in paths), scene
        if scene.startswith(('practice', 'sfx')):
            assert 'ui/um_bracket.png' in paths and any(p.startswith('light/menu_shade_') for p in paths), scene
        if scene.startswith('ped_') and scene != 'ped_gone':
            assert any(p.startswith('ui/um_hud_frame_') for p in paths), scene
    assert 'ui/um_hud_frame_gold.png' in logs['ped_gold'].paths()                 # 황금방 = 특별 보상 = 금 테두리
    assert any(p.startswith('ui/um_hud_frame_') for p in logs['boss_lines'].paths())   # Enter 키 판 = 가는 테두리


def test_s1_no_mist_screen_calls_plate_parts():
    """(2) mist에서 철판 판·틀·띠·키캡·노란 표시를 부르는 화면이 없다: 지금 그려 볼 수 있는 화면 전부
    (타이틀·번개 단계, 일시정지·설정·키 설정·결과·크레딧, HUD 다섯 장면, 문 위 보상 판, 안내 카드, 증강·형태·저주 카드, 이번 S1 화면)."""
    logs = dict(_s1_logs('mist'))
    logs.update(_menu_logs('mist'))
    logs.update(_mist_done_logs())
    logs.update({'other_' + k: v for k, v in _other_logs('mist').items()})
    for key in TITLE_DIGEST['mist']:
        sel, ph = key.split('_', 1)
        logs['title_' + key] = _title_log('mist', int(sel), None if ph == 'None' else ph)
    assert len(logs) >= 55, len(logs)
    for scene, r in logs.items():
        _assert_no_plate(scene, r, MIST_PLATE_ICONS_OK)


def test_s1_old_skins_draw_the_same():
    """(3) 'plate'·'plate_code'·'crystal'에서 S1 화면(NPC 넷·연습·효과음·보스 대사 띠·진열대)의 그리기 기록이 고치기 전과 같다."""
    for skin_name, want in S1_DIGEST.items():
        got = {k: v.digest() for k, v in _s1_logs(skin_name).items()}
        assert got == want, (skin_name, [k for k in want if got.get(k) != want[k]])


def test_s1_finished_mist_screens_draw_the_same():
    """(4) 이미 끝난 화면(일시정지·키 설정·결과·크레딧·HUD·문 위 보상 판·안내 카드)은 mist에서도 S1 전과 같다.
    타이틀과 증강·형태·저주 카드는 test_m1_title_draws_the_same·test_m1_unchanged_screens_draw_the_same_in_every_skin이 본다."""
    got = {k: v.digest() for k, v in _mist_done_logs().items()}
    assert got == MIST_DONE_DIGEST, [k for k in MIST_DONE_DIGEST if got.get(k) != MIST_DONE_DIGEST[k]]


def test_s1_pick_parts_follow_pixel_rules():
    """(5) 새 그림(고르는 화면의 커서)은 픽셀 규칙(알파 0/255, 2px 격자, 64색 이하)을 지키고 경고 노랑·청록을 쓰지 않는다."""
    for n in PICK_PARTS:
        a = np.array(Image.open(os.path.join(UI, n + '.png')).convert('RGBA'))
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, n
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), n
        rgb = a[a[:, :, 3] > 0][:, :3].astype(int)
        assert 0 < len({tuple(c) for c in rgb}) <= 64, n
        assert not (rgb == hud_kit.YELLOW).all(axis=1).any(), n
        assert not ((rgb[:, 1] > 150) & (rgb[:, 2] > 150) & (rgb[:, 0] < 120)).any(), n


def _pick_blocks(r):
    """고르는 화면의 색 뒤집힌 블록과 그 위 글자: [(블록 폭, 글자 폭)]."""
    import mist_pick as mp
    out = []
    for i, row in enumerate(r.log):
        if row[0] != 'draw_rect_color' or row[5:6] not in ((mp.HOT_BG,), (mp.HOT_OFF,)) or row[4] < 20:
            continue
        nxt = next(x for x in r.log[i + 1:] if x[0] == 'draw_text')
        assert nxt[4] == mp.HOT_FG, (row, nxt)
        small = ('small', True) in nxt
        out.append((row[3], len(nxt[3]) * (14 if small else 20)))
    return out


def test_s1_selected_row_is_inverted_only_as_wide_as_its_text():
    """고른 줄은 글자 폭 + 양옆 8px만 색을 뒤집는다 (긴 띠 금지): NPC 창은 카드 색, 연습·효과음은 감시 단말 색(M1과 같은 식)."""
    logs = _s1_logs('mist')
    for scene, r in logs.items():
        if not scene.startswith('npc_'):
            continue
        blocks = _pick_blocks(r)
        assert blocks, scene
        for bw, tw in blocks:
            assert bw <= tw + 16, (scene, bw, tw)
    for scene in ('practice', 'practice_gauge', 'sfx', 'sfx_marked'):
        blocks = _inverted_blocks(logs[scene])
        assert blocks, scene
        for bw, tw in blocks:
            assert bw <= tw + 16, (scene, bw, tw)


def test_s1_unbuyable_row_looks_different_from_buyable():
    """정비사: 고른 줄이 살 수 있으면 밝은 뒤집힘, 살 수 없으면(다 올림·결정 모자람) 흐린 뒤집힘. 값 글자도 다른 색."""
    import mist_pick as mp
    buy, no = _s1_logs('mist')['npc_mech_buy'], _s1_logs('mist')['npc_mech_no']
    hot = lambda r: [row[5] for row in r.log if row[0] == 'draw_rect_color' and row[5:6] in ((mp.HOT_BG,), (mp.HOT_OFF,)) and row[4] >= 20]  # noqa: E731
    assert hot(buy) == [mp.HOT_BG] and hot(no) == [mp.HOT_OFF]
    value = lambda r, s: [row[4] for row in r.log if row[0] == 'draw_text' and row[3] == s][-1]  # noqa: E731  (앞은 그림자)
    assert value(buy, '10 결정') != value(no, '10 결정')


def test_s1_mist_options_rows_group_name_and_description():
    """묶음 5: mist 설정에서 한 항목의 이름과 설명은 붙어 있고(사이가 좁다), 항목과 항목 사이는 그보다 넓다.
    이름·설명은 누르는 자리(ROW_Y 줄 가운데 ±30px) 안에 있다."""
    import options_mode as om
    r = _options_log('mist', 0)
    texts = [row for row in r.log if row[0] == 'draw_text']
    gaps_in, gaps_out = [], []
    for i, item in enumerate(om.ROWS):
        name = next(t for t in texts if t[3] == om.NAMES[item])
        desc = next(t for t in texts if t[3] == om.DESCS[item])
        name_y, desc_y = name[2], desc[2]
        gaps_in.append((name_y - 14) - (desc_y + 11))                 # 이름 글자 아래 ~ 설명 글자 위
        if i + 1 < len(om.ROWS):
            nxt = next(t for t in texts if t[3] == om.NAMES[om.ROWS[i + 1]])
            gaps_out.append((desc_y - 11) - (nxt[2] + 14))           # 설명 아래 ~ 다음 이름 위
        assert abs(name_y - om.ROW_Y[i]) <= 30 and abs(desc_y - om.ROW_Y[i]) <= 30, item
    assert max(gaps_in) + 8 <= min(gaps_out), (gaps_in, gaps_out)
    import mist_menu as mm
    for sel in range(len(om.ROWS)):                                   # 고른 이름의 뒤집힌 블록이 설명 글자를 덮지 않는다
        r = _options_log('mist', sel)
        block = next(row for row in r.log if row[0] == 'draw_rect_color' and row[5:6] == (mm.PH,) and row[4] >= 20)
        desc = [t for t in r.log if t[0] == 'draw_text' and t[3] == om.DESCS[om.ROWS[sel]]][-1]
        assert block[2] >= desc[2] + 11 - 2, (sel, block, desc)

def _glyph_span(text, small=False, big=False):
    """그 글자를 y에 그렸을 때 실제 글자 픽셀의 세로 범위 (y 기준 아래·위, 아래쪽이 0인 화면 좌표).
    assets.draw_text와 같은 글꼴·크기를 창 없이 SDL_ttf로 그려 알파가 있는 줄을 잰다 (pico2d는 글자 그림을 y에 세로 가운데로 놓는다)."""
    import ctypes
    import sdl2
    import sdl2.sdlttf as ttf
    import assets
    if not ttf.TTF_WasInit():
        ttf.TTF_Init()
    key = 'big' if big else ('small' if small else 'normal')
    base = assets.FONT_SIZES['normal' if key == 'big' else key]
    f = ttf.TTF_OpenFont(os.path.join(ROOT, 'assets', 'fonts', f'Galmuri{base}.ttf').encode(), assets._font_px(key))
    s = ttf.TTF_RenderUTF8_Blended(f, text.encode('utf-8'), sdl2.SDL_Color(255, 255, 255))
    try:
        surf = s.contents
        h, w, pitch, amask = surf.h, surf.w, surf.pitch, surf.format.contents.Amask
        buf = ctypes.string_at(surf.pixels, pitch * h)
        rows = [r for r in range(h)
                if any(int.from_bytes(buf[r * pitch + 4 * c:r * pitch + 4 * c + 4], 'little') & amask for c in range(w))]
    finally:
        sdl2.SDL_FreeSurface(s)
        ttf.TTF_CloseFont(f)
    return h / 2 - rows[-1] - 1, h / 2 - rows[0]


def _inverted_text_fits(r, block_colors, text_colors, scene, margin=2):
    """색 뒤집힌 블록 위의 어두운 글자가 블록 안에 위아래 margin px 이상 여유로 들어간다. 블록 수를 돌려준다."""
    n = 0
    for i, row in enumerate(r.log):
        if row[0] != 'draw_rect_color' or row[5:6] not in tuple((c,) for c in block_colors) or row[4] < 20:
            continue
        nxt = next(x for x in r.log[i + 1:] if x[0] == 'draw_text')
        if nxt[4] not in text_colors:
            continue
        lo, hi = _glyph_span(nxt[3], ('small', True) in nxt, ('big', True) in nxt)
        y = nxt[2]
        assert row[2] <= y + lo - margin and row[2] + row[4] >= y + hi + margin, (scene, nxt[3], row[2:5], y + lo, y + hi)
        n += 1
    return n


def test_s1fix_inverted_block_holds_its_whole_text():
    """S1-fix: 고른 항목의 뒤집힌 블록이 그 글자(실제 글자 픽셀)를 위아래 2px 이상 여유로 감싼다. 설정 화면의 모든 줄,
    뒤집기를 쓰는 다른 mist 화면(일시정지·키 설정·결과·연습·효과음·NPC 창·타이틀)은 글자가 블록 밖으로 나가지 않는다(1px 이상).
    (11/27: S1에서 설정의 블록을 위아래 14로 줄여 큰 글자 윗줄이 잘렸다)"""
    import mist_menu as mm
    import mist_pick as mp
    import options_mode as om
    for sel in range(len(om.ITEMS)):
        assert _inverted_text_fits(_options_log('mist', sel), (mm.PH,), (mm.PH_BG,), f'options_{sel}') >= 1, sel
    logs = dict(_menu_logs('mist'))
    logs.update(_s1_logs('mist'))
    logs['title'] = _title_log('mist', 0)
    logs['title_2'] = _title_log('mist', 2)
    n = 0
    for scene, r in logs.items():                       # 다른 화면은 고치지 않는다: 잘리지 않는지(1px 이상)만. 효과음 듣기의 영문 소문자
        n += _inverted_text_fits(r, (mm.PH, mp.HOT_BG, mp.HOT_OFF), (mm.PH_BG, mp.HOT_FG), scene, margin=1)   # g 아래가 1px 여유
    assert n > 20, n

if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
