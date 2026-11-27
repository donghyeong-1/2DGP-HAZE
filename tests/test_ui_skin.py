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
# U1-1(11/27, 글 검토 A·B 반영): 화면 글자가 바뀐 장면의 기록을 네 스킨 모두 새 값으로 바꿨다(글은 스킨과 상관없이 같다).
#   이 파일의 모든 기록 표 가운데 바뀐 것: HUD boss(아크 별칭), MENU pause·options·keys·ending_clear·credits(조작·설정 설명·키 안내·탈출 문구·크레딧),
#   OTHER cards_form·cards_curse·npc_mechanic·practice·sfx, S1 진열대·NPC·연습·효과음, MIST_DONE 같은 화면, W1·D·DA on3(궁극기 · 이름).
#   그림·자리·색은 그대로다. 전 값은 1f2f2e1의 이 파일에 있다.
# U1-2(11/27, UI·UX 검토): pause_ask(판 포기 확인이 어디로 가는지 말한다, 네 스킨 같은 글), mist hud_boss·hud_fade_items_curse
#   (보스 별칭·'강화 30%+'의 흐린 글자를 명암비 4.5:1 넘는 hud_kit.FAINT로), on3 장면('궁극기 준비!' -> '궁극기 준비'). 옛 스킨 HUD 기록은 그대로. 전 값은 10da4d6.
#   mist ending_dead·ending_dead_choose·ending_clear: 결과의 '받은 헤이즈 결정' 값은 청록(보유 결정·NPC 창과 같게), 권하는 글은 본문색.
# N1(11/27, 이름·대사 변경): 네 스킨 같은 글이라 함께 바뀜. pause_build_2·ending_dead_choose('기본 성장: 공격력' -> '공격력 강화'), npc_keeper·npc_archivist(대사),
#   ped_rift(진열대 이름), two_on3(쌍권총 궁극기 '록온 난사' -> '일제 사격'). 그림·자리·색은 그대로. 전 값은 1b3106f.
HUD_DIGEST = {('plate', 'normal'): '26f48c155b548dbc', ('plate', 'critical'): 'c7c9e8dc8033946b',
              ('plate', 'fade_items_curse'): '507c647ff1e06ab9', ('plate', 'enhanced'): '9f3eb5f4c7a35eea', ('plate', 'boss'): '0689f767b9a0460d',
              ('plate_code', 'normal'): '3c4cf4184ede1ad8', ('plate_code', 'critical'): '6803fdc3f439077d',
              ('plate_code', 'fade_items_curse'): '408168d06e0487fc', ('plate_code', 'enhanced'): '742090c564486360',
              ('plate_code', 'boss'): 'c4fcee6dcf012589',
              ('crystal', 'normal'): 'dc045e05fd3d1a8a', ('crystal', 'critical'): 'e2066d47b48a3578',
              ('crystal', 'fade_items_curse'): '7a3f2c7088ea11c0', ('crystal', 'enhanced'): 'fdec8aa4c167bf16',
              ('crystal', 'boss'): '67e621c204cec2ee'}
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
    assert 'ui/um_hud_frame_line.png' in paths
    flat = _with_style('flat', lambda: _hud_log('mist', _hud_states()[0][1]))     # 든 무기 칸의 밝은 테두리는 'flat' 패널의 것 (W3부터 기본값 'da'는 무기 색 테두리)
    assert 'ui/um_hud_frame_hot.png' in flat.paths()
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
# R2(11/27): credits_mid(세 옛 스킨) = 크레딧 '아이템 아이콘'·PixelLab 셋째 줄·'그래픽' 캐릭터 줄 (R2 전 f8b78f59f4fceb53)
# Q1(11/27): credits_mid(세 옛 스킨) = 크레딧 PixelLab 첫 줄 끝에 ', 소품' (Q1 전 e40b84a73a1f011c)
# R1(11/27)이 바꾼 값: credits_mid(세 옛 스킨 같은 값) = 크레딧 'AI 도구'·'그래픽' 절 문구(묶음 4, 스킨과 상관없는 글. 전 7896f4a09436720a),
# mist cards_augment·cards_curse = 증강 카드 진행 칸 up_step_off -> um_step_off/on(묶음 3. 전 c56ed617c57c2389·f791b2981770fab9),
# mist 0_flash·2_flash = 번쩍이는 프레임에 머리글 첫 줄을 그리지 않음(묶음 1. 전 c11c65208d8510e7·683ccfdbc9a80c9c).
# 평소·줄기·잔광 프레임(0_None·0_bolt·0_glow·0_dark 등)과 옛 스킨의 타이틀은 그대로
MENU_DIGEST = {
    'plate': {'pause_0': '3a7adcc2cb177ae0', 'pause_build_2': '706591185f320235', 'pause_ask': 'ac3d7b2aca3ef322', 'options_0': 'baed5c4e11369fac', 'options_music': '1382968b63b6b9e3', 'options_keys': '690d89f14401eccc', 'options_back': '88322c21baa5b7f1', 'keys_0': '85f5508d571bc559', 'keys_listen': 'bca825bb1d9f4747', 'keys_buttons': '8bda51343f1afe66', 'ending_dead_choose': 'a985340e9be7c1eb', 'ending_dead': '4f2ce782d823d96f', 'ending_clear': '3407f630c87e6cce', 'credits_0': '172500abe524364a', 'credits_mid': 'd19ea4512e2eaa47'},
    'plate_code': {'pause_0': '1ea14262c6f07cfd', 'pause_build_2': '56fb50d25fed5cee', 'pause_ask': '89feb0a901922810', 'options_0': '6f7c97363f0fecdb', 'options_music': 'ea31a03ee2067e98', 'options_keys': '27837dded66ff392', 'options_back': '17cb8512e37de282', 'keys_0': 'c2666fbf7292c6e5', 'keys_listen': '2da226e898213d44', 'keys_buttons': 'b5c9cbd7001ffda5', 'ending_dead_choose': 'e3eda8690d84a844', 'ending_dead': '15808d816142bca1', 'ending_clear': '99816a0bf313922e', 'credits_0': '172500abe524364a', 'credits_mid': 'd19ea4512e2eaa47'},
    'crystal': {'pause_0': 'd1a97bcf8fbaee1d', 'pause_build_2': '39793beeefa30d40', 'pause_ask': '7db77125d2deef6c', 'options_0': '40ec2e254f4cb802', 'options_music': 'b29f84307aa857d1', 'options_keys': '3b2506b0fcf156dd', 'options_back': 'c0cdf902cc0b60eb', 'keys_0': '43aed813c19294b1', 'keys_listen': 'c0bb98803a8d37db', 'keys_buttons': '0f60bc50a509ea9c', 'ending_dead_choose': '0fcf2c183f4d832b', 'ending_dead': 'bf3a7d649011bd3b', 'ending_clear': '98f3426d37b328fd', 'credits_0': '172500abe524364a', 'credits_mid': 'd19ea4512e2eaa47'},
}
OTHER_DIGEST = {
    'mist': {'npc_mechanic': '36c64caa73dd7b01', 'npc_keeper': '4403ee234fef16ee', 'npc_armory': '968fa2c2210cb7c4', 'npc_archivist': '58361502e50533c1', 'practice': '0959cb55ced9d876', 'sfx': '28653647e3ffb732', 'cards_augment': '3da451f159297ebc', 'cards_form': '5d1f396d9b756037', 'cards_curse': 'e3f25c236caf0183'},
    'plate': {'npc_mechanic': '36c64caa73dd7b01', 'npc_keeper': '4403ee234fef16ee', 'npc_armory': '968fa2c2210cb7c4', 'npc_archivist': '58361502e50533c1', 'practice': '0959cb55ced9d876', 'sfx': '28653647e3ffb732', 'cards_augment': '66dde66425db532b', 'cards_form': 'caf3d6e618f401b5', 'cards_curse': 'dddfb9245c9ee76e'},
    'plate_code': {'npc_mechanic': '53e9731cdb6d0d1a', 'npc_keeper': 'bd7e82e19215afbf', 'npc_armory': '6c2ed9b37c52f713', 'npc_archivist': 'c5334c3aa349e111', 'practice': '94076e03390392f9', 'sfx': 'dbff211c37372fa2', 'cards_augment': '56c1d0b20659a32a', 'cards_form': 'f8c3003f42ce5da6', 'cards_curse': 'f4e04ff275846b59'},
    'crystal': {'npc_mechanic': '2296d9ff50c42621', 'npc_keeper': '6867bc0e99f46b59', 'npc_armory': '85f7f3ec6f0c1355', 'npc_archivist': '6dd7762ea9f4e3d5', 'practice': 'ee791d71529e7aaa', 'sfx': 'd0e2801e95720bf9', 'cards_augment': '290c43e803d5ea39', 'cards_form': 'f946d90561f820f0', 'cards_curse': 'd69cba64404e7582'},
}
TITLE_DIGEST = {
    'mist': {'0_None': '96332275734e9873', '0_bolt': 'a3d2af5695e9fdb6', '0_flash': '79b7ac365eda8ccc', '0_glow': 'bb61df4537c82835', '0_dark': 'a3d2af5695e9fdb6', '2_None': 'fa00c5dac1455141', '2_bolt': '76a420dda14b725f', '2_flash': 'ca21b8b008e2359b', '2_glow': 'e4aac5e20e64b8b0', '2_dark': '76a420dda14b725f'},
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
# Q1(11/27): 진열대 넷(ped_*)은 PixelLab 진열대로 아이콘 높이가 66 -> 제단 44·선반 56, 품절 선반은 pedestal_gone_shop
# (Q1 전: ped_shop 5394f43bf2ddc69a, ped_gold b9ccfd9ddf62aaf9, ped_rift f8879eb6c068b907, ped_gone b0aa35ea40c8f3da)
S1_DIGEST = {
    'plate': {'npc_mech_buy': '9f2a0beb9a28c23d', 'npc_mech_no': 'd6b1e44d1a1630af', 'npc_keeper_shut': 'd94fad20fd6f0a30', 'npc_keeper_open': 'dd7653c58cb14d66', 'npc_archivist': '192932e287c59c58', 'npc_archivist_last': '83e7be628cfa5994', 'npc_armory_first': '439dbba3040724d4', 'npc_armory_second': '3a5475ae22ca8613', 'npc_back': '53cf95233a15450a', 'practice': '0959cb55ced9d876', 'practice_gauge': '6df9f28cbc2a54f7', 'sfx': '28653647e3ffb732', 'sfx_marked': 'fc7666d2d11bd6f9', 'boss_lines': '9445d045dbf72914', 'boss_typing': '4df1020eed768fb9', 'ped_shop': 'a194a09ca4051aba', 'ped_gold': '7dfed109d9900764', 'ped_rift': '5519909755419551', 'ped_gone': 'b549e69d11b10558'},
    'plate_code': {'npc_mech_buy': 'f05fd4acc01204b4', 'npc_mech_no': 'dfc48bf52842def1', 'npc_keeper_shut': '289d7c3c976712ab', 'npc_keeper_open': 'de8d321cf357cbc7', 'npc_archivist': '26d76cd41a59e35f', 'npc_archivist_last': '7a94cb8d0ec0d6b0', 'npc_armory_first': 'b51e81b3684ed7f8', 'npc_armory_second': '1f4d63b47d9ee1df', 'npc_back': '04475ad9a407af87', 'practice': '94076e03390392f9', 'practice_gauge': '39df7af502d628f4', 'sfx': 'dbff211c37372fa2', 'sfx_marked': '17c7fe5c6584f2d3', 'boss_lines': 'fcbf4a962eb2cf83', 'boss_typing': '7e3e0e9e9beaf4ee', 'ped_shop': 'a194a09ca4051aba', 'ped_gold': '7dfed109d9900764', 'ped_rift': '5519909755419551', 'ped_gone': 'b549e69d11b10558'},
    'crystal': {'npc_mech_buy': '900e6781baf62817', 'npc_mech_no': '4c760b5cc9629a7a', 'npc_keeper_shut': 'e0198921b8567125', 'npc_keeper_open': '82dc1320094aa4f0', 'npc_archivist': 'd9a62504c21bbba7', 'npc_archivist_last': 'a6561641232f9dcc', 'npc_armory_first': 'db08a46a8785814f', 'npc_armory_second': '78c1966cca357d0c', 'npc_back': 'c786854c9b5207e0', 'practice': 'ee791d71529e7aaa', 'practice_gauge': '1c9f9aa90505585d', 'sfx': 'd0e2801e95720bf9', 'sfx_marked': '059e12e7ce668bb3', 'boss_lines': '483a93bf8c0527e7', 'boss_typing': '076b56e29120a179', 'ped_shop': 'a194a09ca4051aba', 'ped_gold': '7dfed109d9900764', 'ped_rift': '5519909755419551', 'ped_gone': 'b549e69d11b10558'},
}
# 이미 끝난 화면의 mist 기록 (S1 전, 50fe67f). 설정(options_*)은 묶음 5로 바뀌므로 뺀다
MIST_DONE_DIGEST = {
    'pause_0': 'c909b5ac2529364b', 'pause_build_2': '589f69d74ed45a67', 'pause_ask': '2655e1c8ff2c502a',
    'keys_0': 'b44b597ad20c63dc', 'keys_listen': '42a3e9d4960cc1df', 'keys_buttons': 'f8a8e1e10811752c',
    'ending_dead_choose': '9b644f1cc7af2a1a', 'ending_dead': '12ef159e411d165d', 'ending_clear': 'f10f4ce355a6fb13',
    'credits_0': 'c7ea34876ff69204', 'credits_mid': 'e877d54422d17aa2',   # Q1(11/27): 크레딧 PixelLab 첫 줄에 ', 소품' (Q1 전 67cc436ab00bde72)
    # H2(11/27)이 mist HUD 다섯 장면을 바꿨다: 위험·페이드 맥박이 바깥 띠 대신 게이지 테두리(critical·fade_items_curse),
    # 들지 않은 무기 칸 테두리 dim -> line·아이콘·숫자 밝게(모든 장면), 켜지 않았지만 쓸 수 있는 E 칸 테두리 e1 -> line(enhanced 밖의 장면).
    # S1 전 값: normal 8efe4fcd6336eccb, critical b31072f9b278ac7c, fade_items_curse 3bb41f6c79aa52a0, enhanced 865db9d39038e5d6, boss 00693a953f9a52ad
    # R1(11/27): ending_dead_choose = 맡길 물건 이름을 칸 위로·칸 간격 88(묶음 6, 전 b9e6f5c9ad866e37), credits_mid = 크레딧 문구(묶음 4, 전 0b0823fe314bdbc0),
    # hud_critical·hud_fade_items_curse = 맥박이 켜진 프레임의 구간 눈금을 테두리 안쪽까지만(묶음 5, 전 c4f647940e7a08a6·bdaf7e221ef01150)
    # W4(11/27): 무기·E 패널 기본값이 'da' -> 'row'(한 줄 1·2·E)라 HUD 다섯 장면이 다시 바뀌었다. 'flat' 값은 FLAT_MIST_HUD_DIGEST, 'da'는 DA_DIGEST가 본다
    # (W4 전 = da: normal 0983bb8e8fb070bd, critical 45af07c556566555, fade_items_curse 0b3e5f39d920eddc, enhanced b2965326972bc329, boss 6ef6c177c0925d67)
    # W5(11/27): row의 공격 설명 줄은 잠깐만(첫 프레임에는 보인다)·콤보 칸은 든 칸 안이라 다시 바뀌었다 (W5 전 = W4 row: normal 0cee15bba614f447, critical d91b8f349ea0d637, fade_items_curse c93403d845b463d6, enhanced beba88515de4feb2, boss 0efed2a7de8aeab8)
    # W6(11/27): 기본 그림 'mix'(결정·무기 칸 틀 PixelLab)와 이름 자리 손질로 다시 바뀌었다 (W6 전: normal f0f62e71a80383f5, critical 401cad53cd7ce33a, fade_items_curse 545badf1b23d2033, enhanced 09fc099fa437c13e, boss 7d9bbe677ca8d9b1)
    # R2(11/27): 기본 그림 'mix'의 E 마름모 테두리를 세로로 긴 마름모(um_wp_row_socket_mix_*, 가운데 x = cx-1, 결정과 같은 축)로, credits_mid = 크레딧 문구
    # (R2 전: normal 4686e809587db610, critical 834c88ae5ec2a70f, fade_items_curse 218265a74db90ef2, enhanced 922fbb1129555a59, boss 29c828bbbb8a8b77, credits_mid 0079b3bc44f0a3ff)
    'hud_normal': '022318b8b83d2c43', 'hud_critical': '46d9fe4d9a5cbf88', 'hud_fade_items_curse': '9394e6cf546291be',
    'hud_enhanced': '63a75d99890e63b6', 'hud_boss': 'a98ffc002a626cd6', 'room_reward': 'a24a0f1ce3f66cfd', 'hint': 'dbe7a284f9ac069a',
}
# 무기·E 패널 'flat'일 때의 mist HUD 다섯 장면 (W3 전 기본값. W3부터 기본값 'da'라 MIST_DONE_DIGEST의 hud_*는 da 값)
FLAT_MIST_HUD_DIGEST = {
    'hud_normal': '23b4e49a3fc1f2c2',
    'hud_critical': '9fb9d92670150de6',
    'hud_fade_items_curse': '8023ff4fe9813426',
    'hud_enhanced': '9d1b7738804e202b',
    'hud_boss': 'b0b9071e0886ca2b',
}
# mist에서도 쓰는 철판 쪽 작은 그림 (판·틀·띠·키·노란 표시가 아니다). up_step_off는 증강 카드의 진행 칸(이미 끝난 화면이라 그대로 둔다)
MIST_PLATE_ICONS_OK = PLATE_ICONS_OK          # R1(11/27): 증강 카드의 진행 칸도 mist 부품 um_step_*으로 (전에는 up_step_off를 여기서 허용했다)
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


# ----- 2026-11-27 H2 HUD 손질 셋 (지휘 쪽 검토 셋, 사용자 "HUD 세 가지 다 고쳐줘". docs/opus/TASKS.md '4차' H2) -----
def _h2_log(state, aura=None, prep=None, style='flat'):
    """mist에서 _hud_states의 한 장면을 aura_time·준비를 바꿔 그린 기록. style: 무기·E 패널 (H2·R1 검사는 'flat'을 본다. W3부터 기본값은 'da')."""
    import ui

    def go():
        p, st, _pick = state()
        if prep:
            prep(p)
        if aura is not None:
            p.aura_time = aura
        with _Recorder() as r:
            ui.GameUI(p, st).draw()
        return r, p
    return _with_skin('mist', lambda: _with_style(style, go))


def _frame_at(r, x, y):
    """(x, y)에 왼쪽 아래 모서리를 그린 테두리 그림 경로 (hud_panel의 9칸 중 왼쪽 아래 조각)."""
    got = [row[1] for row in r.log if row[0] == 'draw_clip' and row[1].startswith('ui/um_hud_frame_')
           and row[6] == x and row[7] == y]
    return got[0] if got else None


def _h2_state(name):
    return dict(_hud_states())[name]


def _gauge_frame(r):
    import ui
    for d in (4, 6):                                     # 기본 2px 테두리는 바깥 4px 자리, 굵어진 테두리는 6px 자리
        f = _frame_at(r, ui.BAR_X - d, ui.BAR_Y - d)
        if f:
            return f
    return None


def test_h2_gauge_pulse_tints_the_frame_without_an_outer_band():
    """(1) mist 위험·페이드: 게이지 판 바깥에 색 띠(사각형)를 그리지 않는다. 맥박이 켜진 프레임에는 게이지 테두리가 구간 색 부품으로,
    꺼진 프레임에는 기본 테두리. 노멀·각성은 늘 기본 테두리."""
    import math
    import ui
    from haze_gauge import AWAKE, CRITICAL, FADE, NORMAL
    cases = [('critical', CRITICAL, math.pi / 18, 3 * math.pi / 18), ('fade_items_curse', FADE, math.pi / 12, 3 * math.pi / 12)]
    for name, zone, on, off in cases:
        for aura, lit in ((on, True), (off, False)):
            r, p = _h2_log(_h2_state(name), aura)
            assert p.gauge.zone == zone, (name, p.gauge.zone)
            for row in r.log:                            # 구간 색 사각형(옛 띠: 판 위아래 6px 바깥)을 그리지 않는다
                assert not (row[0] == 'draw_rect_color' and row[5] == ui.ZONE_COLOR[zone]), (name, row)
            frame = _gauge_frame(r)
            want = 'ui/um_hud_frame_' + ui.PULSE_TONE[zone]
            assert frame is not None, name
            if lit:
                assert frame.startswith(want), (name, frame)
            else:
                assert frame == 'ui/um_hud_frame_line.png', (name, frame)

    def awake(p):
        p.gauge.value = 70
        p.gauge.zone = p.gauge._zone_of(70)
    for prep, zone in ((None, NORMAL), (awake, AWAKE)):
        for aura in (math.pi / 18, math.pi / 12, 0.1):
            r, p = _h2_log(_h2_state('normal'), aura, prep)
            assert p.gauge.zone == zone
            assert _gauge_frame(r) == 'ui/um_hud_frame_line.png', (zone, aura)


def _e_slot_x():
    import ui
    return ui.ACT_RIGHT - 2 * ui.SLOT - 14 - ui.SLOT - 26


def test_h2_e_slot_is_plain_until_enhance_is_on():
    """(2) mist E 칸 테두리: 쓸 수 있지만 켜지 않음 = 기본 테두리(line), 켬 = 강화 단계 색(e1~e3), 게이지가 모자라 못 씀 = 흐린 테두리(dim)."""
    import ui

    def gauge_to(v):
        def f(p):
            p.gauge.value = v
            p.gauge.zone = p.gauge._zone_of(v)
        return f

    def enhance(n):
        def f(p):
            gauge_to(90)(p)
            for _ in range(n):
                assert p.gauge.use_enhance()
        return f
    r, p = _h2_log(_h2_state('normal'), 0.1, gauge_to(62))
    assert p.gauge.can_enhance() and not p.gauge.enhanced
    assert _frame_at(r, _e_slot_x(), ui.ACT_Y) == 'ui/um_hud_frame_line.png'
    for n in (1, 2, 3):
        r, p = _h2_log(_h2_state('normal'), 0.1, enhance(n))
        assert p.gauge.enhanced and p.gauge.enhance_level == n
        assert _frame_at(r, _e_slot_x(), ui.ACT_Y) == f'ui/um_hud_frame_e{n}.png', n
    r, p = _h2_log(_h2_state('normal'), 0.1, gauge_to(22))
    assert not p.gauge.can_enhance() and not p.gauge.enhanced
    # R1(11/27): 못 쓰는 E 칸도 테두리는 들지 않은 무기 칸과 같은 기본 회백 (dim은 어두운 방에서 거의 안 보였다). 못 씀은 흐린 아이콘·글자·빈 점으로
    assert _frame_at(r, _e_slot_x(), ui.ACT_Y) == 'ui/um_hud_frame_line.png'


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _frame_color(path):
    a = np.array(Image.open(os.path.join(ROOT, 'assets', path)).convert('RGBA'))
    return tuple(int(v) for v in a[a[:, :, 3] > 0][0][:3])


IDLE_MIN_LUMA = 120          # 들지 않은 칸 테두리: 어두운 방에서도 칸으로 읽히는 밝기 (11/27 H1의 dim은 약 78)
IDLE_GAP_LUMA = 60           # 든 칸(밝은 회백, 약 227)과 이만큼 이상 차이


def test_h2_idle_weapon_slot_reads_as_a_slot_but_stays_below_the_held_one():
    """(3) mist에서 들지 않은 무기 칸(빈 칸 포함)의 테두리 밝기가 IDLE_MIN_LUMA 이상이고, 든 칸 테두리보다 IDLE_GAP_LUMA 이상 어둡다.
    들지 않은 칸의 아이콘·숫자, '빈 칸' 글자도 예전(H1)보다 밝다."""
    import ui
    xs = [ui.ACT_RIGHT - 2 * ui.SLOT - 14, ui.ACT_RIGHT - ui.SLOT]

    def empty(p):
        p.set_loadout('pipe')
    for prep, idle in ((None, 0), (empty, 1)):
        r, p = _h2_log(_h2_state('normal'), 0.1, prep)
        held = p.slot
        assert held != idle
        idle_c = _frame_color(_frame_at(r, xs[idle], ui.ACT_Y))
        held_c = _frame_color(_frame_at(r, xs[held], ui.ACT_Y))
        assert _luma(idle_c) >= IDLE_MIN_LUMA, idle_c
        assert _luma(held_c) - _luma(idle_c) >= IDLE_GAP_LUMA, (held_c, idle_c)
        texts = [row for row in r.log if row[0] == 'draw_text' and xs[idle] <= row[1] <= xs[idle] + ui.SLOT and row[2] <= ui.ACT_Y + ui.SLOT
                 and row[4] != hud_kit.SHADOW]                # 글자 그림자는 뺀다
        assert texts, idle
        for row in texts:                                  # 칸 안 숫자 / '빈 칸'
            assert _luma(row[4]) >= 145, row
        if idle == 0:
            tint = [row for row in r.log if row[0] == 'draw_image_tinted' and row[1].startswith('ui/icon_w_')]
            assert tint and _luma(tint[0][5]) >= 145 and tint[0][6] >= 0.8, tint


H2_NEW_TONES = ('crit', 'fade')


def test_h2_new_frame_parts_follow_pixel_rules():
    """(4) 새 테두리 부품(위험·페이드 구간 색)이 픽셀 규칙(알파 0/255, 2px 격자, 한 색)을 지키고 속이 비었으며 색이 구간 색과 같다."""
    import ui
    from haze_gauge import CRITICAL, FADE
    for zone in (CRITICAL, FADE):
        tone = ui.PULSE_TONE[zone]
        for path in glob.glob(os.path.join(UI, f'um_hud_frame_{tone}*.png')):
            a = np.array(Image.open(path).convert('RGBA'))
            assert set(np.unique(a[:, :, 3])) <= {0, 255}, path
            assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), path
            assert {tuple(c) for c in a[a[:, :, 3] > 0][:, :3]} == {tuple(ui.ZONE_COLOR[zone])}, path
            h, w = a.shape[:2]
            assert not a[4:h - 4, 4:w - 4, 3].any(), path
        assert os.path.exists(os.path.join(UI, f'um_hud_frame_{tone}.png')), tone


# ----- 2026-11-27 W1 무기·E 패널 시안 셋 (사용자 "무기, E 나오는 UI창이 너무 밋밋하게 변경이 되었는데 조금의 특색이 들어가면 좋겠다".
# docs/opus/TASKS.md '4차' W1). config.HUD_WEAPON_STYLE = 'flat'(기본, 지금 모습) / 'a' 결정 소켓 / 'b' 감시 단말 / 'c' 문장 -----
W1_STYLES = ('a', 'b', 'c')


def _with_style(style, fn):
    old = getattr(config, 'HUD_WEAPON_STYLE', 'flat')
    try:
        config.HUD_WEAPON_STYLE = style
        return fn()
    finally:
        config.HUD_WEAPON_STYLE = old


def _w1_preps():
    """무기 칸 상태(1번 듦·2번 듦·둘째 칸 빈 칸) x E 상태(못 씀·쓸 수 있음·켬 1~3단계) = 15가지 준비 함수."""
    def gauge_to(p, v):
        p.gauge.value = v
        p.gauge.zone = p.gauge._zone_of(v)

    def make(slot, e):
        def f(p):
            if slot == 'empty':
                p.set_loadout('pipe')
            else:
                p.set_loadout('pipe', 'pistol')
                p.swap_weapon(0 if slot == 'one' else 1)
                p.swap_cool = 0.3
            if e == 'low':
                gauge_to(p, 22)
            elif e == 'ready':
                gauge_to(p, 62)
            else:
                gauge_to(p, 95)
                for _ in range(int(e[2])):
                    assert p.gauge.use_enhance()
        return f
    return {(slot, e): make(slot, e) for slot in ('one', 'two', 'empty') for e in ('low', 'ready', 'on1', 'on2', 'on3')}


def _w1_log(style, prep):
    return _h2_log(_h2_state('normal'), 0.1, prep, style=style)


def test_w1_default_style_is_flat_and_flat_draws_the_same_hud():
    """(1) 'flat'이면 mist HUD 다섯 장면의 그리기 기록이 W1 전과 같다(R1 손질 포함). 다른 스킨에서는 시안 값이 무엇이든 'flat'.
    (기본값은 W3부터 'da': test_w3_default_is_da_and_other_values_still_work)"""
    for name, st in _hud_states():
        got = _with_style('flat', lambda: _hud_log('mist', st)).digest()
        assert got == FLAT_MIST_HUD_DIGEST['hud_' + name], name
    for skin_name in ('plate', 'plate_code', 'crystal'):
        for style in W1_STYLES:
            assert _with_skin(skin_name, lambda: _with_style(style, hud_kit.weapon_style)) == 'flat'
    for style in W1_STYLES:
        assert _with_skin('mist', lambda: _with_style(style, hud_kit.weapon_style)) == style


def test_w1_styles_draw_every_state_without_plate_parts():
    """(2) 'a'·'b'·'c'에서 무기 칸 세 상태 x E 다섯 상태가 오류 없이 그려지고, 그 시안의 부품(um_wp_<시안>_)을 쓰며
    철판 판·틀(upx_*, up_ 판, uc_*)과 경고 노랑, 다른 시안의 부품을 부르지 않는다. 든 무기 칸은 밝은(hot) 부품이다.
    무기 이름, 빈 칸 글자, '강화 -25%'(쓸 수 있음·켬) / '강화 30%+'(못 씀)가 그대로 나온다."""
    preps = _w1_preps()
    for style in W1_STYLES:
        for key, prep in preps.items():
            r, p = _w1_log(style, prep)
            _assert_no_plate((style, key), r, PLATE_ICONS_OK)
            wp = {os.path.basename(x) for x in r.paths() if 'um_wp_' in x}
            assert wp and all(x.startswith(f'um_wp_{style}_') for x in wp), (style, key, wp)
            if style in ('a', 'c'):
                assert any('_big_hot' in x for x in wp) and not any('_big_line' in x or '_small_hot' in x for x in wp), (style, key, wp)
            else:
                assert 'um_wp_b_bracket_hot.png' in wp and 'um_wp_b_bracket_line.png' in wp, (style, key, wp)
            texts = [row[3] for row in r.log if row[0] == 'draw_text']
            assert p.weapon.name in texts, (style, key)
            if key[0] == 'empty':
                assert '빈 칸' in texts, (style, key)
            if key[1] == 'low':
                assert any(t.startswith('강화 ') and t.endswith('%+') for t in texts), (style, key, texts)
            else:
                assert any(t.startswith('강화 -') for t in texts), (style, key, texts)


def _e_part(style, wp):
    """그 장면에서 E 칸 판으로 쓴 부품 이름."""
    head = {'a': 'um_wp_a_socket_', 'b': 'um_wp_b_dial_', 'c': 'um_wp_c_crest_'}[style]
    got = [x for x in wp if x.startswith(head)]
    assert len(got) == 1, (style, got)
    return got[0]


def test_w1_e_states_differ_by_shape_and_low_e_outline_stays_visible():
    """(3) E 칸: 켬 1~3단계는 그 단계 색 부품이고, 못 씀은 단계 색·청록이 없는 빈 모양이다(a는 빈 소켓 = 빈 결정).
    못 씀일 때 E의 겉 윤곽 밝기(0.299R+0.587G+0.114B)가 IDLE_MIN_LUMA 이상이라 어두운 방에서도 윤곽이 보인다(H2의 dim은 약 78)."""
    preps = _w1_preps()
    tiers = {tuple(c) for c in config.ENHANCE_LEVEL_COLOR.values()}
    for style in W1_STYLES:
        seen = {}
        for e in ('low', 'ready', 'on1', 'on2', 'on3'):
            r, _p = _w1_log(style, preps[('one', e)])
            wp = {os.path.basename(x) for x in r.paths() if 'um_wp_' in x}
            part = _e_part(style, wp)
            seen[e] = part
            if e.startswith('on'):
                assert part.endswith(f'_e{e[2]}.png'), (style, e, part)
            if e == 'low':
                a = np.array(Image.open(os.path.join(UI, part)).convert('RGBA'))
                mid = a.shape[0] // 2
                row = np.nonzero(a[mid, :, 3])[0]
                outer = tuple(int(v) for v in a[mid, row[0], :3])
                assert _luma(outer) >= IDLE_MIN_LUMA, (style, part, outer)
                cols = {tuple(int(v) for v in c) for c in a[a[:, :, 3] > 0][:, :3]}
                assert not cols & tiers and CYAN not in cols, (style, part)
                if style == 'a':                                   # 빈 소켓: 결정이 차 있지 않다
                    assert 'um_wp_a_crystal_empty.png' in wp and 'um_wp_a_crystal_haze.png' not in wp, wp
        if style == 'a':                                           # a는 못 씀·쓸 수 있음이 같은 소켓, 결정(빈 / 참)으로 가른다
            assert seen['low'] == seen['ready'] and len(set(seen.values())) == 4, seen
        else:
            assert len(set(seen.values())) == 5, (style, seen)


def test_w1_old_skins_ignore_the_style():
    """(4) 'plate'·'plate_code'·'crystal'은 HUD_WEAPON_STYLE이 무엇이든 HUD를 고치기 전과 똑같이 그린다."""
    for style in W1_STYLES:
        for name, st in _hud_states():
            for skin_name in ('plate', 'plate_code', 'crystal'):
                got = _with_style(style, lambda: _hud_log(skin_name, st)).digest()
                assert got == HUD_DIGEST[(skin_name, name)], (style, skin_name, name)


def test_w1_new_parts_follow_pixel_rules():
    """(5) 새 부품 um_wp_*: 알파 0/255, 2px 격자, 64색 이하, 경고 노랑 없음. 청록은 a의 헤이즈 결정에만."""
    files = sorted(glob.glob(os.path.join(UI, 'um_wp_*.png')))
    assert len(files) >= 40, len(files)
    for f in files:
        a = np.array(Image.open(f).convert('RGBA'))
        name = os.path.basename(f)
        assert a.shape[0] % 2 == 0 and a.shape[1] % 2 == 0, name
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name
        cols = {tuple(int(v) for v in c) for c in a[a[:, :, 3] > 0][:, :3]}
        assert len(cols) <= 64, name
        assert hud_kit.YELLOW not in cols, name
        if not name.startswith('um_wp_a_crystal_haze'):
            assert CYAN not in cols, name


# ----- R1 나머지 손질 (11/27, docs/opus/TASKS.md '4차' R1) -----
def _yellowish(c):
    """경고 노랑 계열: 빨강·초록이 밝고 파랑이 그보다 한참 낮다 ((255,240,150), (230,210,150) 등)."""
    r, g, b = c[:3]
    return r >= 200 and g >= 190 and b <= min(r, g) - 50


def _texts(r):
    """기록에서 (글, 색) 줄: kit.text는 그림자 + 글자 두 줄로 남는다."""
    return [(row[3], tuple(row[4])) for row in r.log if row[0] == 'draw_text']


def test_r1_armory_title_is_not_yellow_in_mist():
    """(묶음 2) mist 무기 걸이 창 제목 '무기 걸이'는 밝은 회백(사람이 아니라 인물 색이 없다). 사람 NPC 이름 색은 그대로. 옛 스킨은 그대로."""
    import npc as npc_mod
    r = _npc_log('mist', 'armory', 0)
    cols = [c for t, c in _texts(r) if t == '무기 걸이' and c != hud_kit.SHADOW]
    assert cols and not any(_yellowish(c) for c in cols), cols
    assert all(min(c) >= 200 for c in cols), cols                       # 밝은 회백
    for kind in ('mechanic', 'keeper', 'archivist'):
        cols = [c for t, c in _texts(_npc_log('mist', kind, 0)) if t == npc_mod.NAMES[kind] and c != hud_kit.SHADOW]
        assert cols == [npc_mod.COLORS[kind]], (kind, cols)


def _hub_npc_log(skin_name, kind):
    import npc as npc_mod

    class P:
        x, y = 600, 100
    n = npc_mod.NPC(kind, 600, 100)
    n.player = P()

    def go():
        import assets
        old = assets.outline_image
        try:
            assets.outline_image = lambda rel, *a, **k: _Img(rel)          # 창 없이는 외곽선을 못 굽는다
            with _Recorder() as r:
                n.draw()
            return r
        finally:
            assets.outline_image = old
    return _with_skin(skin_name, go)


def test_r1_hub_npc_prompt_is_light_grey_not_warning_yellow_in_mist():
    """(묶음 2) 은신처 NPC 머리 위 상호작용 안내('F 기본 능력 영구 강화' 등): mist에서는 진열대 'F 획득'(S1)과 같은 밝은 회백 그림자 글자.
    다른 스킨은 예전 경고 노랑 (255,240,150) 그대로."""
    import npc as npc_mod
    for kind in ('mechanic', 'keeper', 'archivist', 'armory', 'practice'):
        prompt = f'F {npc_mod.ROLES[kind]}'
        cols = [c for t, c in _texts(_hub_npc_log('mist', kind)) if t == prompt]
        assert cols == [hud_kit.SHADOW, (236, 240, 248)], (kind, cols)
        for skin_name in ('plate', 'plate_code', 'crystal'):
            cols = [c for t, c in _texts(_hub_npc_log(skin_name, kind)) if t == prompt]
            assert cols == [(255, 240, 150)], (skin_name, kind, cols)


def _augment_log(skin_name, have=1):
    """증강 카드 셋 (기본 증강: 진행 칸 두 개). have: 이미 가진 같은 갈래 수 (0이면 칸 하나만 찬다)."""
    import mutation_mode as mm
    import mutations as mu
    p = dict(_hud_states())['normal']()[0]
    ids = list(mu.MUTATIONS)[:3]

    def mut():
        mm.setup(p, ids)
        mm.age = 5.0
        mm.selected = 1
    return _with_skin(skin_name, lambda: _draw_log(mm, mut))


def test_r1_augment_step_cells_are_thin_frames_in_mist():
    """(묶음 3) mist 증강 카드의 진행 칸은 철판 칸(up_step_*)이 아니라 가는 테두리(2px)의 작은 칸 um_step_off/on.
    찬 칸은 갈래 색 그대로(뜻이 같다). 칸 크기·자리는 예전과 같다."""
    r = _augment_log('mist')
    paths = r.paths()
    assert not any('up_step' in p or 'uc_step' in p for p in paths), paths
    assert 'ui/um_step_off.png' in paths or 'ui/um_step_on.png' in paths, paths
    for name in ('um_step_off', 'um_step_on'):
        a = np.array(Image.open(os.path.join(UI, name + '.png')).convert('RGBA'))
        old = np.array(Image.open(os.path.join(UI, 'up_step_off.png')).convert('RGBA'))
        assert a.shape == old.shape, (name, a.shape)
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name
        edge = np.ones(a.shape[:2], bool)
        edge[2:-2, 2:-2] = False
        ring = {tuple(int(v) for v in c) for c in a[edge][:, :3]}
        assert len(ring) == 1, (name, ring)                                 # 테두리는 한 줄 한 색 (도트 1칸 = 2px)
        inner = {tuple(int(v) for v in c) for c in a[~edge][:, :3]}
        assert len(inner) == 1 and max(next(iter(inner))) < 40, (name, inner)   # 속은 어두운 한 색 (찬 칸 색은 코드가 깐다)
        assert hud_kit.YELLOW not in ring | inner, name
    # 찬 칸은 갈래 색 사각형으로 속을 채운다
    import mutations as mu
    colors = {tuple(mu.FAMILIES[f]['color']) for f in mu.FAMILIES}
    fills = [row for row in r.log if row[0] == 'draw_rect_color' and len(row) > 5 and tuple(row[5]) in colors]
    assert fills, '찬 칸이 없다'


def test_r1_flat_low_e_slot_outline_matches_the_idle_weapon_slot():
    """(묶음 5-1) HUD_WEAPON_STYLE 'flat'(기본): 게이지가 모자라 강화를 못 쓰는 E 칸의 테두리 = 들지 않은 무기 칸 테두리(같은 부품, 같은 밝기).
    못 쓴다는 것은 흐린 아이콘(색 곱)·흐린 키 글자·'강화 N%+' 흐린 글자·빈 단계 점으로 알린다."""
    import ui

    def low(p):                                                            # _h2_log는 'flat'을 그린다 (W3부터 기본값은 'da')
        p.gauge.value = 22
        p.gauge.zone = p.gauge._zone_of(22)
    r, p = _h2_log(_h2_state('normal'), 0.1, low)
    assert not p.gauge.can_enhance() and not p.gauge.enhanced
    e = _frame_at(r, _e_slot_x(), ui.ACT_Y)
    xs = [ui.ACT_RIGHT - 2 * ui.SLOT - 14 + i * (ui.SLOT + 14) for i in range(2)]
    frames = [_frame_at(r, x, ui.ACT_Y) for x in xs]
    idle = [f for f in frames if f != 'ui/um_hud_frame_hot.png']
    assert idle, frames
    assert e == idle[0], (e, idle)
    assert abs(_luma(_frame_color(e)) - _luma(_frame_color(idle[0]))) < 1
    assert _luma(_frame_color(e)) >= IDLE_MIN_LUMA
    tinted = [row for row in r.log if row[0] == 'draw_image_tinted' and row[1] == 'ui/icon_enhance.png']
    assert tinted, '못 쓰는 E 아이콘이 흐리지 않다'
    dots = [row for row in r.log if row[0] == 'draw_rect_color' and len(row) > 5 and tuple(row[5]) in
            {tuple(c) for c in config.ENHANCE_LEVEL_COLOR.values()}]
    assert not dots, dots                                                  # 빈 단계 점


def test_r1_gauge_ticks_stay_inside_the_pulsing_frame():
    """(묶음 5-2) 위험·페이드 맥박이 켜진 프레임: 구간 경계 흰 눈금이 굵어진 색 테두리(바깥 6px ~ 안쪽 2px)를 가로지르지 않는다 —
    눈금은 테두리 안쪽(막대 위아래 2px 틈까지)에만. 꺼진 프레임과 다른 구간은 예전 그대로."""
    import math
    import ui
    white = (242, 246, 250)
    for name, on, off in (('critical', math.pi / 18, 3 * math.pi / 18), ('fade_items_curse', math.pi / 12, 3 * math.pi / 12)):
        r, _p = _h2_log(_h2_state(name), on)
        ticks = [row for row in r.log if row[0] == 'draw_rect_color' and tuple(row[5]) == white and row[3] == 4 and row[4] > ui.BAR_H // 2]
        assert ticks, name
        for row in ticks:
            y, h = row[2], row[4]
            assert y >= ui.BAR_Y - 2 and y + h <= ui.BAR_Y + ui.BAR_H + 2, (name, row)
        r, _p = _h2_log(_h2_state(name), off)
        ticks = [row for row in r.log if row[0] == 'draw_rect_color' and tuple(row[5]) == white and row[3] == 4 and row[4] > ui.BAR_H // 2]
        assert ticks and all(row[2] == ui.BAR_Y - 6 and row[4] == ui.BAR_H + 12 for row in ticks), (name, ticks)


def _backdrop_flag_during(mod, prep=None):
    """mod.draw()가 아래 멈춘 게임(play_mode.draw_frozen = game_world.render)을 그리는 동안의 game_world.quiet 값들."""
    import game_world
    seen = []
    old = game_world.render

    class Under:
        __name__ = 'play_mode'

        @staticmethod
        def draw_frozen():
            seen.append(getattr(game_world, 'quiet', False))
    try:
        game_world.render = lambda *a, **k: seen.append(getattr(game_world, 'quiet', False))
        _draw_log(mod, prep, under=Under)
    finally:
        game_world.render = old
    return seen


def test_r1_menus_draw_the_frozen_game_without_its_text_overlays_in_mist():
    """(묶음 6-1) mist에서 일시정지·NPC 창·연습 메뉴·효과음 듣기가 뒤에 멈춘 게임을 깔 때는 게임의 글자 덮개(처음 안내 카드,
    연습장 '초당 피해'·안내 줄, NPC 이름표·머리 위 안내, 이벤트 방 이름)를 빼고 그린다(game_world.quiet). 방·캐릭터·HUD는 그대로 비친다.
    다른 스킨과 증강 카드 화면은 예전처럼 다 그린다."""
    import game_world
    import mutation_mode
    import npc_mode
    import pause_mode
    import practice_mode
    import sfx_mode

    def pause_prep():
        pause_mode.enter()
    p = dict(_hud_states())['normal']()[0]

    def prac_prep():
        practice_mode.selected, practice_mode.player = 2, p
    for mod, prep in ((npc_mode, None), (practice_mode, prac_prep), (sfx_mode, None), (pause_mode, pause_prep)):
        seen = _with_skin('mist', lambda: _backdrop_flag_during(mod, prep))
        assert seen and all(seen), (mod.__name__, seen)
        seen = _with_skin('plate', lambda: _backdrop_flag_during(mod, prep))
        assert seen and not any(seen), (mod.__name__, seen)
    assert not getattr(game_world, 'quiet', False)
    seen = _with_skin('mist', lambda: _backdrop_flag_during(mutation_mode))
    assert not any(seen), seen                                               # 증강 카드는 이번에 바꾸지 않는다


def test_r1_text_overlays_hide_while_quiet():
    """(묶음 6-1) game_world.quiet이면 처음 안내 카드·연습장 글자·NPC 이름표·머리 위 안내가 글자를 그리지 않는다 (그림은 그린다)."""
    import game_world
    import npc as npc_mod
    import practice
    import tutorial

    class St:
        name = 'practice'

    class P:
        x, y = 600, 100
    t = tutorial.Tutorial.__new__(tutorial.Tutorial)
    t.__dict__.update(tutorial.Tutorial.__new__(tutorial.Tutorial).__dict__)
    n = npc_mod.NPC('mechanic', 600, 100)
    n.player = P()
    hud = practice.PracticeHud(St())

    def go():
        import assets
        old = assets.outline_image
        try:
            assets.outline_image = lambda rel, *a, **k: _Img(rel)
            with _Recorder() as r:
                n.draw()
                hud.draw()
            return r
        finally:
            assets.outline_image = old
    try:
        game_world.quiet = True
        r = _with_skin('mist', go)
        assert not [row for row in r.log if row[0] == 'draw_text'], r.log
        assert any(row[0] == 'draw_image' for row in r.log)                 # NPC 그림은 그린다
    finally:
        game_world.quiet = False
    r = _with_skin('mist', go)
    assert [row for row in r.log if row[0] == 'draw_text']
    import inspect
    assert 'quiet' in inspect.getsource(tutorial.Tutorial.draw)


def test_r1_npc_back_button_has_its_own_shade_in_mist():
    """(묶음 6-1) NPC 창 '돌아가기' 뒤에 글자 뒤 어둠을 한 번 더 깐다 (은신처 무기 걸이 그림이 비쳐 겹쳤다)."""
    import npc_mode
    r = _npc_log('mist', 'mechanic', 0, crystals=40)
    back = npc_mode._buttons()[-1]
    shades = [row for row in r.log if row[0] == 'draw_rect_color' and len(row) > 6 and row[5] == (4, 6, 12)]
    cy = back.y + back.h // 2
    assert any(row[1] <= back.x + back.w // 2 - 60 and row[1] + row[3] >= back.x + back.w // 2 + 60
               and row[2] <= cy - 14 and row[2] + row[4] >= cy + 14 for row in shades), shades


# 사망 결과 일러스트(screen_death.png)의 쓰러진 주인공 머리 상자 (화면 좌표, 아래가 0): 원래 크기 그림에서 잰 값 (x 605~765, 위에서 745~855)
DEAD_HEAD = (605, 1080 - 855, 765, 1080 - 745)
DEAD_CLEAR = 16                                    # 머리와 떨어뜨릴 거리 (px)


def _boxes_apart(a, b, gap):
    return a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1]


def test_r1_dead_result_item_group_clears_the_fallen_hero():
    """(묶음 6-2) 사망 결과(mist): 고른 물건 이름의 뒤집힌 블록·커서·물건 칸이 일러스트의 쓰러진 주인공 머리에서 DEAD_CLEAR px 이상 떨어진다.
    물건이 셋·넷일 때, 어느 것을 골라도. 이 화면은 키(A D·Enter)로만 고른다(마우스로 누르는 자리가 없다: 보이는 자리만 옮기면 된다)."""
    import inspect
    import ending_mode as em
    import items
    assert 'MOUSE' not in inspect.getsource(em.handle_events)
    ids = [i for i in items.ITEMS][:3]
    for choices in ([ids[0], ids[1], None], [ids[0], ids[1], ids[2], None]):
        for choice in range(len(choices)):
            def prep():
                em.result, em.reward = 'dead', 12
                em.summary = [('도달한 구역', '구역 2 · 공장'), ('걸린 시간', '12:34'), ('클리어한 방', '9'), ('처치한 적', '41'),
                              ('처치한 보스·관문', '1'), ('받은 헤이즈 결정', '+12'), ('사망 원인', '크래셔의 강타')]
                em.choices, em.choice, em.choosing, em.kept = list(choices), choice, True, None
                em.ending_line, em.easy_hint = '', ''
            r = _with_skin('mist', lambda: _draw_log(em, prep))
            boxes = []
            for row in r.log:
                if row[0] == 'draw_rect_color' and len(row) > 5 and row[5] == mm_ph() and row[4] >= 20:
                    boxes.append((row[1], row[2], row[1] + row[3], row[2] + row[4]))              # 뒤집힌 블록
                if row[0] == 'draw_image' and row[1] == 'ui/um_cursor.png':
                    boxes.append((row[2] - 13, row[3], row[2] + 13, row[3] + 42))                  # 커서 (26x42)
                if row[0] == 'draw_clip' and row[1].startswith('ui/um_hud_frame_ph'):
                    boxes.append((row[6], row[7], row[6] + 8, row[7] + 8))                         # 물건 칸 테두리 조각
            assert len(boxes) > 4, boxes
            for b in boxes:
                assert _boxes_apart(b, DEAD_HEAD, DEAD_CLEAR), (choices, choice, b)


def mm_ph():
    import mist_menu as mm
    return mm.PH


def test_r1_sfx_inverted_block_has_two_px_under_every_name():
    """(묶음 6-3) 효과음 듣기: 모든 종류·모든 줄에서 고른 이름의 뒤집힌 블록이 실제 글자 픽셀을 위아래 2px 이상 여유로 감싼다
    (소문자 g 등이 있는 줄도. S1-fix의 재는 방법: SDL_ttf로 글자 픽셀을 잰다)."""
    import mist_menu as mm
    import sfx_mode
    n = 0
    for cat, (_label, names) in enumerate(sfx_mode.catalog()):
        for row in range(len(names)):
            def prep(cat=cat, row=row):
                sfx_mode.cat, sfx_mode.row, sfx_mode.marks = cat, row, {}
            r = _with_skin('mist', lambda: _draw_log(sfx_mode, prep))
            n += _inverted_text_fits(r, (mm.PH,), (mm.PH_BG,), f'sfx_{cat}_{row}', margin=2)
    assert n > 50, n



# ----- 2026-11-27 W2 무기·E 패널 시안 D (사용자가 A·B·C를 본 뒤 참고 그림과 함께 "이런 느낌 안되나?". docs/opus/TASKS.md '4차' W2) -----
# 'd' 떠 있는 칸: 칸이 하나씩 따로 떠 있고(반투명 바탕), 무기 두 칸은 어긋나게 세로로 쌓이고 E 칸은 따로 떨어져 있다.
# 든 칸만 그 무기 색으로 밝고, 칸 바깥에 반쯤 걸친 동그란 키 배지(1·2·E), E 칸 모서리에 강화 단계 숫자 배지.
# W1 뒤(3eccbd5)의 시안 a·b·c 그리기 기록. D를 더해도 그대로여야 한다 (_w1_preps의 열다섯 상태)
W1_DIGEST = {
    'a': {'one_low': '575a2568228c8d3f', 'one_ready': 'cbe06e3e973d2244', 'one_on1': '753f0b860479f938', 'one_on2': '09ed9121359490e0', 'one_on3': '94a9392444a266dd', 'two_low': 'a4a6e6363197a925', 'two_ready': '2de3d1069c05cb6f', 'two_on1': '4d9b88ff50bcb7d1', 'two_on2': '696e6b7f2ab1bac1', 'two_on3': 'e44a886cbde9f6a7', 'empty_low': '01ca5531c2a393c5', 'empty_ready': '79397b8cdda97cd9', 'empty_on1': '5e36eb491d6d709f', 'empty_on2': '33a8fe0255db268a', 'empty_on3': '26bd0964226ccf59'},
    'b': {'one_low': '8beda36e772d14c7', 'one_ready': '5d54f1a260560dca', 'one_on1': '0e215b42fa0818a4', 'one_on2': '0eb85465443cd057', 'one_on3': 'e86fd2320e611eeb', 'two_low': '1af57f80f3d51c34', 'two_ready': '73c699e980542268', 'two_on1': '7c1a800032182465', 'two_on2': 'cb14145c87be9f9c', 'two_on3': '1e1a8c935e900584', 'empty_low': '388011f7ca0eac53', 'empty_ready': 'af9067898a443c47', 'empty_on1': '0b9a844183baf8e5', 'empty_on2': '2587f3659ff94dc1', 'empty_on3': 'dde675c31acf18d5'},
    'c': {'one_low': 'c5ef5e612ce26ed1', 'one_ready': 'f126fe8b0531f261', 'one_on1': 'a2e06b17b396bdbd', 'one_on2': 'ee45898155a1ad85', 'one_on3': '5a7ccea43ca5f0cb', 'two_low': 'c9d82a4cd8b5c420', 'two_ready': '2e7c6866c108d8bf', 'two_on1': 'fcf9f3fb427cfbe5', 'two_on2': 'f54eb6babe2f3a22', 'two_on3': 'a983ef0adbc96187', 'empty_low': 'c08c4c6a3e92f93f', 'empty_ready': '38b0207eb697f21e', 'empty_on1': '0f4688f1ff5597b9', 'empty_on2': '9ad743c131fed7d0', 'empty_on3': '1c1034a373df4a4c'},
}


def test_w2_d_is_a_style_and_other_styles_draw_the_same():
    """(1) 'd'는 고를 수 있는 시안이다(mist에서만, 다른 스킨은 'flat'). 기본값은 W3부터 'da'이고,
    'a'·'b'·'c'는 열다섯 상태의 그리기 기록이 D를 더하기 전과 같다('flat'과 옛 스킨은 test_w1_*가 본다)."""
    assert _with_skin('mist', lambda: _with_style('d', hud_kit.weapon_style)) == 'd'
    for skin_name in ('plate', 'plate_code', 'crystal'):
        assert _with_skin(skin_name, lambda: _with_style('d', hud_kit.weapon_style)) == 'flat'
    for style, want in W1_DIGEST.items():
        got = {'_'.join(k): _w1_log(style, prep)[0].digest() for k, prep in _w1_preps().items()}
        assert got == want, (style, [k for k in want if got.get(k) != want[k]])
    for name, st in _hud_states():                                      # 옛 스킨은 'd'여도 그대로
        for skin_name in ('plate', 'plate_code', 'crystal'):
            assert _with_style('d', lambda: _hud_log(skin_name, st)).digest() == HUD_DIGEST[(skin_name, name)], (skin_name, name)


def test_w2_d_draws_every_state_without_plate_parts():
    """(2) 'd'에서 무기 칸 세 상태 x E 다섯 상태가 오류 없이 그려지고, D 부품(um_wp_d_*)만 쓰며 철판 판·틀과 경고 노랑,
    다른 시안의 부품을 부르지 않는다. 무기 이름·빈 칸·'강화 -25%'/'강화 30%+'·키 글자(1·2·E)가 그대로 나온다."""
    for key, prep in _w1_preps().items():
        r, p = _w1_log('d', prep)
        _assert_no_plate(('d', key), r, PLATE_ICONS_OK)
        wp = {os.path.basename(x) for x in r.paths() if 'um_wp_' in x}
        assert wp and all(x.startswith('um_wp_d_') for x in wp), (key, wp)
        texts = [row[3] for row in r.log if row[0] == 'draw_text']
        assert p.weapon.name in texts, key
        assert '1' in texts and '2' in texts and 'E' in texts, (key, texts)          # 키 배지는 빈 칸에도 붙는다
        assert ('빈 칸' in texts) == (key[0] == 'empty'), key
        if key[1] == 'low':
            assert any(t.startswith('강화 ') and t.endswith('%+') for t in texts), (key, texts)
        else:
            assert any(t.startswith('강화 -') for t in texts), (key, texts)


def _d_slot_frames(r):
    """D 무기 칸 테두리 부품 이름 (그린 차례대로: 1번 칸, 2번 칸)."""
    return [os.path.basename(row[1]) for row in r.log
            if row[0] == 'draw_image' and os.path.basename(row[1]).startswith('um_wp_d_slot_')]


def _outer_color(name):
    a = np.array(Image.open(os.path.join(UI, name)).convert('RGBA'))
    mid = a.shape[0] // 2
    row = np.nonzero(a[mid, :, 3])[0]
    return tuple(int(v) for v in a[mid, row[0], :3])


def test_w2_held_slot_is_lit_in_its_weapon_color_and_idle_slot_still_reads():
    """(3) 든 칸 테두리 = 그 무기의 색 부품(um_wp_d_slot_<무기>), 들지 않은 칸(빈 칸 포함) = 회백 부품(um_wp_d_slot_line).
    든 칸 테두리 밝기는 들지 않은 칸보다 IDLE_GAP_LUMA 이상 높고, 들지 않은 칸은 IDLE_MIN_LUMA 이상(H2 기준: 어두운 방에서도 칸으로 보인다).
    든 칸 아이콘은 원래 색, 들지 않은 칸 아이콘은 회백 곱."""
    preps = _w1_preps()
    for slot in ('one', 'two', 'empty'):
        r, p = _w1_log('d', preps[(slot, 'ready')])
        frames = _d_slot_frames(r)
        assert len(frames) == 2, frames
        held, idle = frames[p.slot], frames[1 - p.slot]
        assert held == f'um_wp_d_slot_{p.weapon.weapon_id}.png', (slot, held)
        assert idle == 'um_wp_d_slot_line.png', (slot, idle)
        hc, ic = _outer_color(held), _outer_color(idle)
        assert _luma(ic) >= IDLE_MIN_LUMA, ic
        assert _luma(hc) - _luma(ic) >= IDLE_GAP_LUMA, (hc, ic)
        icons = [row for row in r.log if row[0] in ('draw_image', 'draw_image_tinted') and row[1].startswith('ui/icon_w_')]
        assert any(row[0] == 'draw_image' and row[1] == f'ui/icon_w_{p.weapon.weapon_id}.png' for row in icons), icons
        if slot != 'empty':
            assert any(row[0] == 'draw_image_tinted' for row in icons), icons
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):          # 무기 넷 모두 든 칸 테두리가 회백보다 분명히 밝다
        assert _luma(_outer_color(f'um_wp_d_slot_{wid}.png')) - _luma(_outer_color('um_wp_d_slot_line.png')) >= IDLE_GAP_LUMA, wid


def test_w2_e_slot_and_level_badge_follow_the_enhance_state():
    """(4) E 칸: 켬 1~3단계 = 단계 색 테두리(um_wp_d_e_e<n>) + 단계 배지(um_wp_d_lv_e<n>)와 그 숫자, 쓸 수 있음 = 회백 테두리 + 빈 배지(um_wp_d_lv_off),
    못 씀 = 회백 테두리(겉 윤곽 밝기 ≥ IDLE_MIN_LUMA) + 배지 없음 + 흐린 아이콘. 배지 색은 config.ENHANCE_LEVEL_COLOR의 그 단계 색."""
    preps = _w1_preps()
    for e in ('low', 'ready', 'on1', 'on2', 'on3'):
        r, p = _w1_log('d', preps[('one', e)])
        wp = {os.path.basename(x) for x in r.paths() if 'um_wp_d_' in x}
        frames = [x for x in wp if x.startswith('um_wp_d_e_') and x != 'um_wp_d_e_well.png']
        badges = [x for x in wp if x.startswith('um_wp_d_lv_')]
        texts = [row for row in r.log if row[0] == 'draw_text']
        if e.startswith('on'):
            n = int(e[2])
            assert frames == [f'um_wp_d_e_e{n}.png'], (e, frames)
            assert badges == [f'um_wp_d_lv_e{n}.png'], (e, badges)
            a = np.array(Image.open(os.path.join(UI, badges[0])).convert('RGBA'))
            cols = {tuple(int(v) for v in c) for c in a[a[:, :, 3] > 0][:, :3]}
            assert tuple(config.ENHANCE_LEVEL_COLOR[n]) in cols, (n, cols)
            assert any(row[3] == str(n) for row in texts), (e, [row[3] for row in texts])
        else:
            assert frames == ['um_wp_d_e_line.png'], (e, frames)
            assert badges == (['um_wp_d_lv_off.png'] if e == 'ready' else []), (e, badges)
            tinted = [row for row in r.log if row[0] == 'draw_image_tinted' and row[1] == 'ui/icon_enhance.png']
            assert bool(tinted) == (e == 'low'), e
    assert _luma(_outer_color('um_wp_d_e_line.png')) >= IDLE_MIN_LUMA


def test_w2_d_parts_follow_pixel_rules():
    """(5) 새 부품 um_wp_d_*: 알파 0/255, 2px 격자, 64색 이하, 경고 노랑·헤이즈 청록 없음.
    칸 바탕(_well)은 한 색 불투명 그림이고 실행 중 불투명도를 낮춰 그린다(반투명 바탕)."""
    files = sorted(glob.glob(os.path.join(UI, 'um_wp_d_*.png')))
    names = {os.path.basename(f) for f in files}
    want = ({'um_wp_d_well.png', 'um_wp_d_slot_line.png', 'um_wp_d_e_well.png', 'um_wp_d_e_line.png', 'um_wp_d_lv_off.png',
             'um_wp_d_key_hot.png', 'um_wp_d_key_line.png'} |
            {f'um_wp_d_slot_{w}.png' for w in ('pipe', 'pistol', 'gauntlet', 'chain')} |
            {f'um_wp_d_e_e{n}.png' for n in (1, 2, 3)} | {f'um_wp_d_lv_e{n}.png' for n in (1, 2, 3)})
    assert want <= names, want - names
    for f in files:
        a = np.array(Image.open(f).convert('RGBA'))
        name = os.path.basename(f)
        assert a.shape[0] % 2 == 0 and a.shape[1] % 2 == 0, name
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name
        cols = {tuple(int(v) for v in c) for c in a[a[:, :, 3] > 0][:, :3]}
        assert len(cols) <= 64, name
        assert hud_kit.YELLOW not in cols and CYAN not in cols, name
        if name.endswith('_well.png'):
            assert len(cols) == 1, name
    r, _p = _w1_log('d', _w1_preps()[('one', 'ready')])
    wells = [row for row in r.log if row[0] == 'draw_image_tinted' and row[1].endswith('_well.png')]
    assert len(wells) == 3 and all(0.6 <= row[6] < 1.0 for row in wells), wells



# ----- 2026-11-27 W3 무기·E 패널 확정: D 배치 + A 결정 소켓 = 'da' (사용자 "D 배치에 A 결정 소켓으로 합쳐줘". docs/opus/TASKS.md '4차' W3) -----
# W2 뒤(fb1d342)의 시안 d 그리기 기록 (열다섯 상태). 'da'를 더하고 기본값으로 바꿔도 그대로여야 한다
D_DIGEST = {
    'one_low': '80713cc2a813d3ec',
    'one_ready': 'a71726d6bc8ca591',
    'one_on1': '2d2ef4c46684a249',
    'one_on2': '26e4344a413d9cae',
    'one_on3': '1b6ce7896336874a',
    'two_low': '983b11deba282cef',
    'two_ready': '1fe3c46b70d6e283',
    'two_on1': '4a695b84e30f7724',
    'two_on2': '2832779d5a0f2cd4',
    'two_on3': '1a048cf95c93eef6',
    'empty_low': 'f650fc61d2a79bc7',
    'empty_ready': '9f7638518fb3e1e6',
    'empty_on1': '2fdfdcc21b4104c9',
    'empty_on2': 'f7f08d220cb92da4',
    'empty_on3': 'f0870752aa0d9cb9',
}
DA_OK = ('um_wp_da_', 'um_wp_d_', 'um_wp_a_crystal_')      # da가 쓰는 부품: 제 것 + D의 칸·키 배지·단계 배지 + A의 헤이즈 결정


def test_w3_default_is_da_and_other_values_still_work():
    """(1) 'da'는 고를 수 있는 값이다(mist에서만, 다른 스킨은 'flat'. W3에서 기본값이었고 W4부터 기본값은 'row'). 'flat'·'a'·'b'·'c'·'d'는 남아 있고 그리기 기록이 그대로다."""
    assert _with_skin('mist', lambda: _with_style('da', hud_kit.weapon_style)) == 'da'      # W4부터 기본값은 'row'
    for skin_name in ('plate', 'plate_code', 'crystal'):
        assert _with_skin(skin_name, hud_kit.weapon_style) == 'flat'
    for name, st in _hud_states():
        assert _with_style('flat', lambda: _hud_log('mist', st)).digest() == FLAT_MIST_HUD_DIGEST['hud_' + name], name
    for style, want in list(W1_DIGEST.items()) + [('d', D_DIGEST)]:
        got = {'_'.join(k): _w1_log(style, prep)[0].digest() for k, prep in _w1_preps().items()}
        assert got == want, (style, [k for k in want if got.get(k) != want[k]])


def test_w3_da_draws_every_state_without_plate_parts():
    """(2) 'da'에서 무기 칸 세 상태 x E 다섯 상태가 오류 없이 그려지고, da·D·A 결정 부품만 쓰며 철판 판·틀과 경고 노랑을 부르지 않는다.
    무기 이름·빈 칸·'강화 -25%'/'강화 30%+'·키 글자(1·2·E)가 그대로 나온다. A의 결정 조각(단계)과 A의 E 글자 자리는 쓰지 않는다."""
    for key, prep in _w1_preps().items():
        r, p = _w1_log('da', prep)
        _assert_no_plate(('da', key), r, PLATE_ICONS_OK)
        wp = {os.path.basename(x) for x in r.paths() if 'um_wp_' in x}
        assert wp and all(x.startswith(DA_OK) for x in wp), (key, wp)
        assert not any(x.startswith('um_wp_a_shard') or x.startswith('um_wp_a_socket') for x in wp), (key, wp)
        texts = [row[3] for row in r.log if row[0] == 'draw_text']
        assert p.weapon.name in texts, key
        assert '1' in texts and '2' in texts and 'E' in texts, (key, texts)
        assert ('빈 칸' in texts) == (key[0] == 'empty'), key
        if key[1] == 'low':
            assert any(t.startswith('강화 ') and t.endswith('%+') for t in texts), (key, texts)
        else:
            assert any(t.startswith('강화 -') for t in texts), (key, texts)


def test_w3_e_socket_crystal_and_level_badge_follow_the_state():
    """(3) E = 결정 소켓: 못 씀 = 빈 결정 윤곽(청록 결정 없음), 쓸 수 있음 = 청록 결정(A보다 한 단 어두운 um_wp_da_crystal_haze), 켬 n단계 = 단계 색 소켓 테두리 + 단계 색 결정(남은 시간만큼).
    단계 배지는 켰을 때만 그 단계의 배지와 숫자, 켜지 않았을 때는 그리지 않는다. 못 쓸 때 소켓 겉 윤곽 밝기 ≥ IDLE_MIN_LUMA."""
    preps = _w1_preps()
    for e in ('low', 'ready', 'on1', 'on2', 'on3'):
        r, p = _w1_log('da', preps[('one', e)])
        wp = {os.path.basename(x) for x in r.paths() if 'um_wp_' in x}
        sockets = [x for x in wp if x.startswith('um_wp_da_socket_') and x != 'um_wp_da_socket_well.png']
        badges = [x for x in wp if x.startswith('um_wp_d_lv_')]
        import weapon_panel as wpn
        _s1, _s2, (cx, cy) = wpn.da_layout()
        nums = [row[3] for row in r.log if row[0] == 'draw_text' and row[3] in ('1', '2', '3') and cx + 20 <= row[1] <= cx + 56
                and cy + 20 <= row[2] <= cy + 56]                     # 소켓 오른쪽 위 단계 배지 자리의 숫자
        if e.startswith('on'):
            n = int(e[2])
            assert sockets == [f'um_wp_da_socket_e{n}.png'], (e, sockets)
            assert f'um_wp_a_crystal_e{n}.png' in wp and 'um_wp_da_crystal_haze.png' not in wp, (e, wp)
            assert badges == [f'um_wp_d_lv_e{n}.png'] and nums == [str(n)], (e, badges, nums)
        else:
            assert sockets == ['um_wp_da_socket_line.png'], (e, sockets)
            assert not badges and not nums, (e, badges, nums)
            want, other = ('um_wp_a_crystal_empty.png', 'um_wp_da_crystal_haze.png') if e == 'low' else ('um_wp_da_crystal_haze.png', 'um_wp_a_crystal_empty.png')
            assert want in wp and other not in wp, (e, wp)
    assert _luma(_outer_color('um_wp_da_socket_line.png')) >= IDLE_MIN_LUMA


def test_w3_cost_text_sits_on_a_backing():
    """(4) '강화 -25%'/'강화 30%+' 글자 뒤에 반투명 꼬리표 바탕(um_wp_da_tag_well)이 먼저 그려지고, 글자는 그 안에 있다(긴 띠가 아니다: 폭 ≤ 160)."""
    preps = _w1_preps()
    for e in ('low', 'ready', 'on2'):
        r, _p = _w1_log('da', preps[('one', e)])
        tag = [i for i, row in enumerate(r.log) if row[0] == 'draw_image_tinted' and row[1] == 'ui/um_wp_da_tag_well.png']
        cost = [i for i, row in enumerate(r.log) if row[0] == 'draw_text' and row[3].startswith('강화 ') and '단계' not in row[3]]
        assert len(tag) == 1 and cost, (e, tag, cost)
        assert tag[0] < cost[0], (e, tag, cost)
        img = Image.open(os.path.join(UI, 'um_wp_da_tag_well.png'))
        assert img.width <= 160, img.size
        row = r.log[tag[0]]
        cx, bottom = row[2], row[3]
        for i in cost:
            tx, ty = r.log[i][1], r.log[i][2]
            assert cx - img.width // 2 - 4 <= tx <= cx + img.width // 2 and bottom <= ty <= bottom + img.height, (e, r.log[i], row)


def test_w3_name_line_sits_over_the_weapon_slots():
    """(5) 무기 이름 줄은 무기 칸 묶음 위에 칸과 왼쪽을 맞춰 놓인다(소켓 위 오른쪽 끝에 떨어져 있지 않다)."""
    import weapon_panel as wpn
    (x1, y1), _s2, _e = wpn.da_layout()
    r, p = _w1_log('da', _w1_preps()[('one', 'ready')])
    names = [row for row in r.log if row[0] == 'draw_text' and row[3] == p.weapon.name and row[4] != hud_kit.SHADOW]
    assert names, p.weapon.name
    x, y = names[0][1], names[0][2]
    assert abs(x - (x1 - 16)) <= 4 and y > y1 + wpn.D_SLOT_H, (x, y, x1, y1)


def test_w3_da_parts_follow_pixel_rules():
    """(6) 새 부품 um_wp_da_*: 알파 0/255, 2px 격자, 64색 이하, 경고 노랑 없음, 청록은 헤이즈 결정(da_crystal_haze)에만 — 카드 청록 (46,230,214) 자체는 없음. 바탕(_well)은 한 색이고 실행 중 반투명으로 그린다."""
    files = sorted(glob.glob(os.path.join(UI, 'um_wp_da_*.png')))
    names = {os.path.basename(f) for f in files}
    want = {'um_wp_da_socket_well.png', 'um_wp_da_socket_line.png', 'um_wp_da_tag_well.png'} | {f'um_wp_da_socket_e{n}.png' for n in (1, 2, 3)}
    assert want <= names, want - names
    for f in files:
        a = np.array(Image.open(f).convert('RGBA'))
        name = os.path.basename(f)
        assert a.shape[0] % 2 == 0 and a.shape[1] % 2 == 0, name
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name
        cols = {tuple(int(v) for v in c) for c in a[a[:, :, 3] > 0][:, :3]}
        assert len(cols) <= 64 and hud_kit.YELLOW not in cols and CYAN not in cols, name
        if name.endswith('_well.png'):
            assert len(cols) == 1, name
    r, _p = _w1_log('da', _w1_preps()[('one', 'ready')])
    wells = [row for row in r.log if row[0] == 'draw_image_tinted' and row[1].endswith('_well.png')]
    assert len(wells) == 4 and all(0.6 <= row[6] < 1.0 for row in wells), wells



# ----- 2026-11-27 W4 무기·E 패널 배치 다시 짜기 = 'row' (사용자 "배치를 새로 짜는 것으로 현재 비슷한 장르 게임들의 ui 배치나, 색, 반투명도, 크기 등을
# 조사해서 세팅을 해줘". docs/opus/TASKS.md '4차' W4, 조사는 docs/REFERENCES.md) -----
# 한 줄, 아랫변 맞춤, 왼쪽부터 1·2·E. 자리 고정, 든 칸은 그 자리에서 커지고(크기·바탕 불투명도·아이콘 밝기·밝은 겉 테두리로 동시에 구분),
# 무기 색은 안쪽 줄과 재충전 줄에만. E는 W3의 결정 소켓을 줄였다. 글은 줄였다(이름은 든 칸 위 작게).
# W3 뒤(824eb15)의 'da' 그리기 기록 (열다섯 상태). 'row'를 더하고 기본값으로 바꿔도 그대로여야 한다
DA_DIGEST = {
    'one_low': '1b64cb7e5aa09769',
    'one_ready': 'f67e3a36655b269f',
    'one_on1': '43489531beb17133',
    'one_on2': 'd1b285bea5dac023',
    'one_on3': '20f444911e57f8fe',
    'two_low': '4a5362c7392e3095',
    'two_ready': 'ec77b174955ca544',
    'two_on1': '9b4d0eda19ce5933',
    'two_on2': '85725af50b4235cf',
    'two_on3': '669d156f680c259c',
    'empty_low': '7d9403f9ebf40807',
    'empty_ready': '71a635c840b1f2fd',
    'empty_on1': '60af987fd4fbe162',
    'empty_on2': 'b844ba93299ca7c2',
    'empty_on3': '5e8e88a527147c1b',
}
ROW_OK = ('um_wp_row_', 'um_wp_d_key_', 'um_wp_d_lv_', 'um_wp_da_crystal_', 'um_wp_a_crystal_')
ROW_MARGIN_RIGHT = 28        # 오른쪽 여백 = 미니맵(오른쪽 위)과 같은 ui.MARGIN
ROW_MARGIN_BOTTOM = 40       # 아래 여백 (키 배지·소켓 꼭짓점까지 포함)


def _row_panel_log(prep, style='row', art='code'):
    """mist에서 오른쪽 아래 무기·E 패널만 그린 기록 (GameUI._draw_actions). W4 검사는 코드 그림(art='code')을 본다 (W6부터 기본값은 'mix')."""
    import ui

    def go():
        p, st, _pick = _h2_state('normal')()
        prep(p)
        p.aura_time = 0.1
        with _Recorder() as r:
            ui.GameUI(p, st)._draw_actions()
        return r, p
    return _with_skin('mist', lambda: _with_style(style, lambda: _with_art(art, go)))


def _img_size(path):
    full = os.path.join(ROOT, 'assets', path)
    return Image.open(full).size


def _row_boxes(r):
    """그리기 기록 한 줄마다 화면 상자 (왼쪽, 아래, 오른쪽, 위). 글자는 기록기의 글자 폭 어림(작은 글자 14px/자)과 높이 ±12."""
    out = []
    for row in r.log:
        kind = row[0]
        if kind in ('draw_image', 'draw_image_tinted'):
            w, h = _img_size(row[1])
            left = int(round(row[2])) - w // 2
            out.append((row, (left, row[3], left + w, row[3] + h)))
        elif kind == 'draw_clip':
            out.append((row, (row[6], row[7], row[6] + row[4], row[7] + row[5])))
        elif kind == 'draw_rect_color':
            out.append((row, (row[1], row[2], row[1] + row[3], row[2] + row[4])))
        elif kind == 'draw_text':
            kw = dict(x for x in row if isinstance(x, tuple) and len(x) == 2 and isinstance(x[0], str))
            tw = len(row[3]) * (14 if kw.get('small') else 20)
            left = row[1] - tw // 2 if kw.get('center') else row[1]
            out.append((row, (left, row[2] - 12, left + tw, row[2] + 12)))
    return out


def _row_frames(r):
    """무기 칸 테두리 기록 [(부품 이름, 왼쪽, 아래, 폭, 높이)], 그린 차례(1번, 2번)."""
    out = []
    for row in r.log:
        if row[0] == 'draw_image' and os.path.basename(row[1]).startswith('um_wp_row_slot_'):
            w, h = _img_size(row[1])
            out.append((os.path.basename(row[1]), int(row[2]) - w // 2, row[3], w, h))
    return out


def _row_socket(r):
    got = [(int(row[2]), row[3]) for row in r.log if row[0] == 'draw_image' and os.path.basename(row[1]).startswith('um_wp_row_socket_')
           and not row[1].endswith('_well.png')]
    assert len(got) == 1, got
    return got[0]


def test_w4_default_is_row_and_other_values_still_work():
    """(1) 기본값은 'row'(mist에서만, 다른 스킨은 'flat'). 'flat'·'a'·'b'·'c'·'d'·'da'는 남아 있고 그리기 기록이 그대로다."""
    assert config.HUD_WEAPON_STYLE == 'row'
    assert _with_skin('mist', hud_kit.weapon_style) == 'row'
    for skin_name in ('plate', 'plate_code', 'crystal'):
        assert _with_skin(skin_name, hud_kit.weapon_style) == 'flat'
    for name, st in _hud_states():
        assert _with_style('flat', lambda: _hud_log('mist', st)).digest() == FLAT_MIST_HUD_DIGEST['hud_' + name], name
    for style, want in list(W1_DIGEST.items()) + [('d', D_DIGEST), ('da', DA_DIGEST)]:
        got = {'_'.join(k): _w1_log(style, prep)[0].digest() for k, prep in _w1_preps().items()}
        assert got == want, (style, [k for k in want if got.get(k) != want[k]])
    for name, st in _hud_states():                                      # 옛 스킨은 'row'여도 그대로
        for skin_name in ('plate', 'plate_code', 'crystal'):
            assert _with_style('row', lambda: _hud_log(skin_name, st)).digest() == HUD_DIGEST[(skin_name, name)], (skin_name, name)


def test_w4_row_draws_every_state_without_plate_parts():
    """(2) 'row'에서 무기 칸 세 상태 x E 다섯 상태가 오류 없이 그려지고 row 부품(과 D 키·단계 배지, W3 꼬리표·결정)만 쓰며 철판·경고 노랑이 없다.
    무기 이름·빈 칸·'강화 -25%'/'강화 30%+'·키 글자(1·2·E)가 그대로 나오고, E 상태는 결정으로 갈린다(못 씀 = 빈 윤곽, 쓸 수 있음 = 청록, 켬 = 단계 색 + 숫자 배지)."""
    for key, prep in _w1_preps().items():
        r, p = _with_art('code', lambda: _w1_log('row', prep))          # 코드 그림 (W6부터 기본값은 'mix')
        _assert_no_plate(('row', key), r, PLATE_ICONS_OK)
        wp = {os.path.basename(x) for x in r.paths() if 'um_wp_' in x}
        assert wp and all(x.startswith(ROW_OK) for x in wp), (key, wp)
        texts = [row[3] for row in r.log if row[0] == 'draw_text']
        assert p.weapon.name in texts and '1' in texts and '2' in texts and 'E' in texts, (key, texts)
        assert ('빈 칸' in texts) == (key[0] == 'empty'), key
        if key[1] == 'low':
            assert any(t.startswith('강화 ') and t.endswith('%+') for t in texts), (key, texts)
            assert 'um_wp_a_crystal_empty.png' in wp and 'um_wp_da_crystal_haze.png' not in wp, wp
        else:
            assert any(t.startswith('강화 -') for t in texts), (key, texts)
        if key[1] == 'ready':
            assert 'um_wp_da_crystal_haze.png' in wp, wp
        if key[1].startswith('on'):
            n = int(key[1][2])
            assert f'um_wp_row_socket_e{n}.png' in wp and f'um_wp_a_crystal_e{n}.png' in wp and f'um_wp_d_lv_e{n}.png' in wp, (key, wp)
        else:
            assert not any(x.startswith('um_wp_d_lv_') for x in wp), (key, wp)


def test_w4_slots_keep_their_order_and_the_socket_stays_put_when_swapping():
    """(3) 1번을 들든 2번을 들든 칸은 왼쪽부터 1·2·E 순서이고, E 소켓의 자리는 그대로다. 줄의 왼쪽 끝도 그대로다(든 칸이 그 자리에서 커진다)."""
    preps = _w1_preps()
    seen = []
    for slot in ('one', 'two', 'empty'):
        r, p = _row_panel_log(preps[(slot, 'ready')])
        frames = _row_frames(r)
        assert len(frames) == 2, frames
        (n1, x1, y1, w1, h1), (n2, x2, y2, w2, h2) = frames
        sx, sy = _row_socket(r)
        assert x1 + w1 <= x2 and x2 + w2 <= sx, (frames, sx)
        assert y1 == y2, frames                                        # 아랫변 맞춤
        seen.append((x1, sx, sy))
    assert len({s[0] for s in seen}) == 1 and len({s[1:] for s in seen}) == 1, seen


def test_w4_held_slot_is_bigger_more_opaque_and_brighter_with_one_light_outer_frame():
    """(4) 든 칸은 들지 않은 칸보다 가로·세로 모두 크고, 바탕 불투명도와 아이콘 밝기도 높다. 든 칸의 겉 테두리 색은 무기와 상관없이 같은 밝은 회백이고
    (색만으로 알리지 않는다), 무기 색은 안쪽 줄에만 있다. 들지 않은 칸 테두리는 IDLE_MIN_LUMA 이상(어두운 방에서도 칸으로 보인다)."""
    import combo
    preps = _w1_preps()
    for slot in ('one', 'two'):
        r, p = _row_panel_log(preps[(slot, 'ready')])
        frames = _row_frames(r)
        held, idle = frames[p.slot], frames[1 - p.slot]
        assert held[0] == f'um_wp_row_slot_{p.weapon.weapon_id}.png' and idle[0] == 'um_wp_row_slot_line.png', frames
        assert held[3] > idle[3] and held[4] > idle[4], frames
        wells = [row for row in r.log if row[0] == 'draw_image_tinted' and row[1].startswith('ui/um_wp_row_well_')]
        big = [row[6] for row in wells if 'big' in row[1]]
        small = [row[6] for row in wells if 'small' in row[1]]
        assert big and small and big[0] > small[0] and all(0.5 <= a < 1.0 for a in big + small), wells
        icons = [row for row in r.log if row[0] in ('draw_image', 'draw_image_tinted') and row[1].startswith('ui/icon_w_')]
        held_icon = [row for row in icons if row[1] == f'ui/icon_w_{p.weapon.weapon_id}.png' and row[0] == 'draw_image']
        idle_icon = [row for row in icons if row[0] == 'draw_image_tinted']
        assert held_icon and idle_icon and idle_icon[0][6] < 1.0, icons
    outers = set()
    for wid, c in combo.COLORS.items():
        a = np.array(Image.open(os.path.join(UI, f'um_wp_row_slot_{wid}.png')).convert('RGBA'))
        mid = a.shape[0] // 2
        row = np.nonzero(a[mid, :, 3])[0]
        outer = tuple(int(v) for v in a[mid, row[0], :3])
        inner = tuple(int(v) for v in a[mid, row[0] + 2, :3])
        outers.add(outer)
        assert inner != outer, wid
        cols = {tuple(int(v) for v in x) for x in a[a[:, :, 3] > 0][:, :3]}
        assert any(abs(x[0] - c[0]) + abs(x[1] - c[1]) + abs(x[2] - c[2]) < 120 for x in cols - {outer}), (wid, cols)
    assert len(outers) == 1 and _luma(next(iter(outers))) >= 200, outers
    assert _luma(_outer_color('um_wp_row_slot_line.png')) >= IDLE_MIN_LUMA
    assert _luma(next(iter(outers))) - _luma(_outer_color('um_wp_row_slot_line.png')) >= IDLE_GAP_LUMA


def test_w4_panel_stays_inside_the_screen_margins():
    """(5) 패널의 모든 그리기(키 배지·소켓 꼭짓점·글자 포함)가 화면 오른쪽 끝에서 ROW_MARGIN_RIGHT, 아래 끝에서 ROW_MARGIN_BOTTOM 안쪽에 있다.
    바깥 상자는 W3(da)보다 낮고 flat보다 좁다."""
    import ui
    for key, prep in _w1_preps().items():
        r, _p = _row_panel_log(prep)
        boxes = _row_boxes(r)
        assert boxes, key
        for row, (l, b, rt, t) in boxes:
            assert rt <= ui.W - ROW_MARGIN_RIGHT and b >= ROW_MARGIN_BOTTOM, (key, row, (l, b, rt, t))
    r, _p = _row_panel_log(_w1_preps()[('one', 'on2')])
    boxes = [bx for _row, bx in _row_boxes(r)]
    top = max(bx[3] for bx in boxes)
    r2, _p = _row_panel_log(_w1_preps()[('one', 'on2')], style='da')
    top_da = max(bx[3] for _row, bx in _row_boxes(r2))
    assert top < top_da, (top, top_da)


def test_w4_row_parts_follow_pixel_rules():
    """(6) 새 부품 um_wp_row_*: 알파 0/255, 2px 격자, 64색 이하, 경고 노랑·카드 청록 없음. 바탕(_well)은 한 색이고 실행 중 반투명으로 그린다."""
    files = sorted(glob.glob(os.path.join(UI, 'um_wp_row_*.png')))
    names = {os.path.basename(f) for f in files}
    want = ({'um_wp_row_well_big.png', 'um_wp_row_well_small.png', 'um_wp_row_slot_line.png', 'um_wp_row_tag_well.png', 'um_wp_row_socket_well.png', 'um_wp_row_socket_line.png'} |
            {f'um_wp_row_slot_{w}.png' for w in ('pipe', 'pistol', 'gauntlet', 'chain')} | {f'um_wp_row_socket_e{n}.png' for n in (1, 2, 3)})
    assert want <= names, want - names
    for f in files:
        a = np.array(Image.open(f).convert('RGBA'))
        name = os.path.basename(f)
        assert a.shape[0] % 2 == 0 and a.shape[1] % 2 == 0, name
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name
        cols = {tuple(int(v) for v in c) for c in a[a[:, :, 3] > 0][:, :3]}
        assert len(cols) <= 64 and hud_kit.YELLOW not in cols and CYAN not in cols, name
        if name.endswith(('_well.png', '_well_big.png', '_well_small.png')):
            assert len(cols) == 1, name



# ----- 2026-11-27 W5 글·콤보 칸 손질 (사용자 "한 줄 배치로 가고 제안대로 글이랑 콤보 칸 고쳐줘". docs/opus/TASKS.md '4차' W5) -----
# 공격 설명 줄은 평소에 감추고 무기를 바꾸거나 강화를 켜거나(단계가 바뀌거나) 형태가 바뀌거나 방에 들어선 직후 WEAPON_HINT_TIME초만 보인다.
# 콤보 칸·충전 막대는 든 칸 안쪽(오른쪽 세로 줄)으로.
LONGEST_HINT = '대시 공격: 관통 베기 · 표식 3개 처형'


def _w5_ui(prep):
    """mist·'row'에서 장면 하나를 준비한 GameUI와 플레이어 (그리기는 _w5_draw)."""
    import ui
    p, st, _pick = _h2_state('normal')()
    prep(p)
    p.aura_time = 0.1
    return ui.GameUI(p, st), p


def _w5_draw(u):
    def go():
        with _Recorder() as r:
            u._draw_actions()
        return r
    return _with_skin('mist', lambda: _with_style('row', go))


W5_SETTLE = 0.06             # W6: 바뀐 직후 이름이 한 단계 올라가는 동안(0.05초)은 설명 줄을 아직 그리지 않는다


def _w5_shown(u):
    """바뀜을 알아채는 한 프레임을 그린 뒤 W5_SETTLE만큼 지나 다시 그린 기록 (설명 줄이 뜬 프레임)."""
    _w5_draw(u)
    u.update(W5_SETTLE)
    return _w5_draw(u)


def _w5_texts(r):
    return [row[3] for row in r.log if row[0] == 'draw_text' and row[4] != hud_kit.SHADOW]


def _w5_hint(u, p):
    import weapon_panel as wpn
    return wpn._attack_line(u)[0]


def test_w5_hint_shows_after_swap_and_enhance_then_hides():
    """(1) 공격 설명 줄: 처음(방에 들어선 직후)·무기를 바꾼 직후·강화를 켠 직후·단계가 바뀐 직후에는 그려지고, WEAPON_HINT_TIME이 지나면 그려지지 않는다."""
    u, p = _w5_ui(_w1_preps()[('one', 'ready')])
    hint = _w5_hint(u, p)
    assert hint in _w5_texts(_w5_shown(u))                             # 첫 프레임 = 방에 들어선 직후
    u.update(config.WEAPON_HINT_TIME + 0.1)
    assert hint not in _w5_texts(_w5_draw(u))
    p.swap_weapon(1)                                                     # 무기를 바꾼 직후
    hint = _w5_hint(u, p)
    assert hint in _w5_texts(_w5_shown(u)), hint
    u.update(config.WEAPON_HINT_TIME + 0.1)
    assert hint not in _w5_texts(_w5_draw(u))
    p.gauge.value = 95
    p.gauge.zone = p.gauge._zone_of(95)
    assert p.gauge.use_enhance()                                         # 강화를 켠 직후
    hint = _w5_hint(u, p)
    assert hint.startswith('강화 1단계') and hint in _w5_texts(_w5_shown(u)), hint
    u.update(config.WEAPON_HINT_TIME + 0.1)
    assert hint not in _w5_texts(_w5_draw(u))
    assert p.gauge.use_enhance()                                         # 단계가 바뀐 직후
    hint = _w5_hint(u, p)
    assert hint.startswith('강화 2단계') and hint in _w5_texts(_w5_shown(u)), hint
    u.update(config.WEAPON_HINT_TIME - 0.05 - W5_SETTLE)                           # 사라지기 직전 (단계 페이드: 글자 색이 어두워진다)
    r = _w5_draw(u)
    rows = [row for row in r.log if row[0] == 'draw_text' and row[3] == hint and row[4] != hud_kit.SHADOW]
    assert rows and _luma(rows[0][4]) < _luma(config.ENHANCE_LEVEL_COLOR[2]) - 20, rows


def test_w5_only_the_name_and_the_cost_tag_stay_on_screen():
    """(2) 설명 줄이 사라진 평소 프레임에 패널이 그리는 글은 무기 이름과 '강화' 꼬리표뿐이다(키 배지 1·2·E, 빈 칸 글자, 켰을 때의 단계 숫자는 표시).
    무기 넷, 1번·2번 듦, 못 씀·쓸 수 있음·켬."""
    preps = _w1_preps()
    for key, prep in preps.items():
        u, p = _w5_ui(prep)
        _w5_draw(u)
        u.update(config.WEAPON_HINT_TIME + 0.1)
        texts = set(_w5_texts(_w5_draw(u)))
        marks = {'1', '2', 'E', '빈 칸', '3'}
        rest = texts - marks
        cost = [t for t in rest if t.startswith('강화 ') and ('%' in t)]
        assert rest == {p.weapon.name} | set(cost) and len(cost) == 1, (key, texts)


def _w5_slot_rect(p):
    import weapon_panel as wpn
    spots, _c = wpn.row_layout(p.slot)
    return spots[p.slot]


def test_w5_combo_marks_sit_inside_the_held_slot():
    """(3) 콤보 칸(철파이프)·개수 칸(쌍권총·사슬)·충전 막대(건틀릿)는 든 칸의 사각형 안쪽에 그려진다(무기 넷, 1번·2번 듦). 칸 윗변에 걸치지 않는다."""
    for wid in ('pipe', 'pistol', 'gauntlet', 'chain'):
        for held in (0, 1):
            def prep(p, wid=wid, held=held):
                other = 'chain' if wid != 'chain' else 'pipe'
                p.set_loadout(*((wid, other) if held == 0 else (other, wid)))
                p.swap_weapon(held)
                p.gauge.value = 62
                p.gauge.zone = p.gauge._zone_of(62)
            u, p = _w5_ui(prep)
            assert p.weapon.weapon_id == wid, (wid, p.weapon.weapon_id)
            if wid == 'pipe':
                p.weapon.combo = 2
            x, y, w, h = _w5_slot_rect(p)
            r = _w5_draw(u)
            marks = [bx for row, bx in _row_boxes(r) if (row[0] == 'draw_image' and 'um_wp_row_combo_' in row[1])
                     or (row[0] == 'draw_rect_color' and row[1] >= x + w // 2 and row[4] > 6)]
            assert marks, (wid, held)
            for (l, b, rt, t) in marks:
                assert x + 2 <= l and rt <= x + w - 2 and y + 2 <= b and t <= y + h - 2, (wid, held, (l, b, rt, t), (x, y, w, h))
            assert not any('um_combo_' in pth or 'up_combo_' in pth for pth in r.paths()), (wid, r.paths())


def _rect_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def test_w5_hint_line_does_not_overlap_the_tag_socket_or_slots():
    """(4) 가장 긴 설명 줄이 떠 있을 때(1번·2번 듦, 강화 켬 포함) 그 사각형이 '강화' 꼬리표·소켓·무기 칸 둘과 겹치지 않고, 무기 이름 아래에 있다(이름 위가 아니다)."""
    import weapon_panel as wpn
    for slot in ('one', 'two'):
        for e in ('ready', 'on2'):
            u, p = _w5_ui(_w1_preps()[(slot, e)])
            u._attack_text = lambda w, g: (LONGEST_HINT, (150, 165, 190))
            hint = _w5_hint(u, p)
            r = _w5_shown(u)
            boxes = _row_boxes(r)
            hint_box = [bx for row, bx in boxes if row[0] == 'draw_text' and row[3] == hint and row[4] != hud_kit.SHADOW]
            name_box = [bx for row, bx in boxes if row[0] == 'draw_text' and row[3] == p.weapon.name and row[4] != hud_kit.SHADOW]
            assert hint_box and name_box, (slot, e)
            hb, nb = hint_box[0], name_box[0]
            assert hb[3] <= nb[1] + 4, (hb, nb)                                # 이름 아래 줄
            spots, (cx, cy) = wpn.row_layout(p.slot)
            solid = [(x, y, x + w, y + h) for x, y, w, h in spots]
            solid.append((cx - 44, cy - 44, cx + 44, cy + 44))
            tag = [bx for row, bx in boxes if row[0] == 'draw_image_tinted' and 'row_tag_well' in row[1]]
            assert tag, slot
            solid += tag
            for s in solid:
                assert not _rect_overlap(hb, s), (slot, e, hb, s)



# ----- 2026-11-27 P1 무기·E 패널 그림 PixelLab 시험 (사용자 "여기에서 pixelLab을 이용해서 에셋을 뽑는건 어떤가?". docs/opus/TASKS.md '4차' P1) -----
# config.HUD_WEAPON_ART = 'code'(기본, 코드로 구운 그림) / 'px'(PixelLab 부품 um_wpx_*, 없는 것은 코드 그림). 배치·크기·동작은 같다.
# W5 뒤(3e5b528)의 'row' 그리기 기록 (열다섯 상태). 'code'이면 그대로여야 한다
# W6(11/27): 이름이 평소 칸 바로 위·설명 줄이 뜰 때만 올라가도록 row 배치를 손봐 'code' 기록도 바뀌었다 (W5 끝 값은 git 3e5b528의 이 줄)
ROW_DIGEST = {
    'one_low': '04dc6074ef387329',
    'one_ready': '6ff47bf18bb4caab',
    'one_on1': '9f3c6e0a1285dcf9',
    'one_on2': '1cfefbee87bacb9d',
    'one_on3': '8dc11d1e5a734bd1',
    'two_low': '7cb0228b3b8356a6',
    'two_ready': '999e19ff2b6c3adc',
    'two_on1': 'dab716669d6e3be6',
    'two_on2': '20272f6e7c83c91f',
    'two_on3': 'fee0cfb5fe0c0dbd',
    'empty_low': '4004778e1f5b2a74',
    'empty_ready': 'adde10a173eaeb68',
    'empty_on1': '6017decf7eefed81',
    'empty_on2': 'c52f7aae2f1bb5e8',
    'empty_on3': '2c1a2a5f2121b3c2',
}
PX_OK = ROW_OK + ('um_wpx_',)


def _with_art(art, fn):
    old = getattr(config, 'HUD_WEAPON_ART', 'code')
    try:
        config.HUD_WEAPON_ART = art
        return fn()
    finally:
        config.HUD_WEAPON_ART = old


def test_p1_code_art_is_default_and_draws_the_same():
    """(1) 'code'이면 'row' 열다섯 상태의 그리기 기록이 ROW_DIGEST와 같다(PixelLab 부품을 부르지 않는다). W6부터 기본값은 'mix'."""
    got = {'_'.join(k): _with_art('code', lambda: _w1_log('row', prep))[0].digest() for k, prep in _w1_preps().items()}
    assert got == ROW_DIGEST, [k for k in ROW_DIGEST if got.get(k) != ROW_DIGEST[k]]


def test_p1_px_art_draws_every_state_without_plate_parts():
    """(2) 'px'이면 열다섯 상태가 오류 없이 그려지고 PixelLab 부품(um_wpx_*)을 쓰며 철판 판·틀과 경고 노랑을 부르지 않는다.
    소켓·결정·무기 칸 틀이 PixelLab 것이고(키 배지는 코드 그림), E 상태(못 씀 = 빈 결정, 쓸 수 있음 = 청록, 켬 = 단계 색)가 갈린다."""
    for key, prep in _w1_preps().items():
        r, p = _with_art('px', lambda: _w1_log('row', prep))
        _assert_no_plate(('px', key), r, PLATE_ICONS_OK)
        wp = {os.path.basename(x) for x in r.paths() if 'um_wp' in x}
        assert all(x.startswith(PX_OK) for x in wp), (key, wp)
        assert any(x.startswith('um_wpx_socket_') for x in wp) and any(x.startswith('um_wpx_slot_') for x in wp), (key, wp)
        assert 'um_wp_d_key_hot.png' in wp or 'um_wp_d_key_line.png' in wp, (key, wp)        # 키 배지는 코드 그림 (PixelLab 것은 버림)
        e = key[1]
        if e == 'low':
            assert 'um_wpx_crystal_empty.png' in wp and 'um_wpx_crystal_haze.png' not in wp, wp
        elif e == 'ready':
            assert 'um_wpx_crystal_haze.png' in wp, wp
        else:
            assert f'um_wpx_crystal_e{e[2]}.png' in wp and f'um_wpx_socket_e{e[2]}.png' in wp, wp
        texts = [row[3] for row in r.log if row[0] == 'draw_text']
        assert p.weapon.name in texts and '1' in texts and '2' in texts and 'E' in texts, (key, texts)


def test_p1_px_parts_follow_pixel_rules_and_crystals_share_one_silhouette():
    """(3) PixelLab 부품 um_wpx_*: 알파 0/255, 2px 격자, 64색 이하, 경고 노랑 없음. 결정의 색 변형(청록·단계 셋·빈 결정)은 알파 모양이 같다.
    부품 크기는 코드 그림과 같은 자리에 맞는다(칸 96x72 / 72x56, 소켓 96)."""
    files = sorted(glob.glob(os.path.join(UI, 'um_wpx_*.png')))
    names = {os.path.basename(f) for f in files}
    want = ({f'um_wpx_crystal_{k}.png' for k in ('haze', 'empty', 'e1', 'e2', 'e3')} | {f'um_wpx_socket_{k}.png' for k in ('line', 'e1', 'e2', 'e3')} |
            {f'um_wpx_slot_{k}.png' for k in ('line', 'pipe', 'pistol', 'gauntlet', 'chain')})
    assert want <= names, want - names
    for f in files:
        a = np.array(Image.open(f).convert('RGBA'))
        name = os.path.basename(f)
        assert a.shape[0] % 2 == 0 and a.shape[1] % 2 == 0, name
        assert set(np.unique(a[:, :, 3])) <= {0, 255}, name
        assert (a[0::2, 0::2] == a[1::2, 0::2]).all() and (a[0::2, 0::2] == a[0::2, 1::2]).all(), name
        cols = {tuple(int(v) for v in c) for c in a[a[:, :, 3] > 0][:, :3]}
        assert len(cols) <= 64 and hud_kit.YELLOW not in cols, name
    masks = [np.array(Image.open(os.path.join(UI, f'um_wpx_crystal_{k}.png')).convert('RGBA'))[:, :, 3] > 0 for k in ('haze', 'empty', 'e1', 'e2', 'e3')]
    assert all((m == masks[0]).all() for m in masks), '결정 실루엣이 다르다'
    size = lambda n: Image.open(os.path.join(UI, n)).size
    assert size('um_wpx_slot_pipe.png') == (96, 72) and size('um_wpx_slot_line.png') == (72, 56), (size('um_wpx_slot_pipe.png'), size('um_wpx_slot_line.png'))
    assert size('um_wpx_socket_line.png') == (96, 96)



# ----- 2026-11-27 W6 무기·E 패널 그림 확정과 빈 틈 줄이기 (사용자 "결정·소켓(결정 소켓은 원래 것을 사용하자.)만 PixelLab으로 하고 빈 틈도 줄여줘,"
# / "결정을 둘러싼 테두리(소켓)은 기본(코드), 나머지 다른 소켓은 pixelLab". docs/opus/TASKS.md '4차' W6) -----
# HUD_WEAPON_ART 기본값 'mix': 결정·무기 칸 틀 = PixelLab(um_wpx_), 마름모 테두리·키 배지·단계 배지·꼬리표·콤보 칸 = 코드.
# 이름은 평소 든 칸 바로 위(ROW_NAME_DY), 설명 줄이 뜨는 동안만 한 줄 위(ROW_NAME_UP)로 두 단계에 걸쳐 올라간다.
W6_NAME_GAP = 12             # 평소 프레임: 이름 글자 상자 아랫변과 든 칸 윗변 사이 (이하)


def test_w6_default_art_is_mix_with_the_agreed_parts():
    """(1) 기본값 'mix': 결정은 PixelLab, 마름모 테두리는 코드, 무기 칸 틀(든 칸·들지 않은 칸·빈 칸)은 PixelLab, 키 배지·단계 배지는 코드 (열다섯 상태)."""
    assert config.HUD_WEAPON_ART == 'mix'
    for key, prep in _w1_preps().items():
        r, p = _w1_log('row', prep)
        _assert_no_plate(('mix', key), r, PLATE_ICONS_OK)
        wp = {os.path.basename(x) for x in r.paths() if 'um_wp' in x}
        assert any(x.startswith('um_wpx_crystal_') for x in wp) and not any(x.startswith(('um_wp_a_crystal_', 'um_wp_da_crystal_')) for x in wp), (key, wp)
        assert any(x.startswith('um_wp_row_socket_') for x in wp) and not any(x.startswith('um_wpx_socket_') for x in wp), (key, wp)
        assert any(x.startswith('um_wpx_slot_') for x in wp) and not any(x.startswith('um_wp_row_slot_') for x in wp), (key, wp)
        assert any(x.startswith('um_wp_d_key_') for x in wp) and not any(x.startswith('um_wpx_key_') for x in wp), (key, wp)
        if key[1].startswith('on'):
            assert f'um_wp_d_lv_e{key[1][2]}.png' in wp and f'um_wpx_crystal_e{key[1][2]}.png' in wp, (key, wp)


def _dots(name):
    return np.array(Image.open(os.path.join(UI, name)).convert('RGBA'))[::2, ::2]


def test_w6_held_frame_shows_its_weapon_colour_on_all_four_sides():
    """(2) PixelLab 든 칸 틀(um_wpx_slot_<무기>): 무기 색이 네 변(모서리 8도트를 뺀 가운데)에 모두 있다(위·오른쪽에만 보이던 것을 고쳤다)."""
    import combo
    for wid, c in combo.COLORS.items():
        a = _dots(f'um_wpx_slot_{wid}.png')
        h, w = a.shape[:2]
        hit = (a[:, :, 3] > 0) & (a[:, :, :3] == c).all(axis=2)
        sides = {'top': hit[:4, 8:w - 8], 'bottom': hit[h - 4:, 8:w - 8], 'left': hit[8:h - 8, :4], 'right': hit[8:h - 8, w - 4:]}
        for side, band in sides.items():
            n = int(band.sum())
            assert n >= band.shape[0] * band.shape[1] // 4 // 2, (wid, side, n)


def test_w6_idle_frame_keeps_the_held_frame_corners():
    """(3) 들지 않은 칸 틀(um_wpx_slot_line, 72x56)의 네 모서리(6x6도트) 알파 모양이 든 칸 틀과 같다(깎인 모서리·사선 표시가 남는다). 밝기는 든 칸보다 낮다."""
    held, idle = _dots('um_wpx_slot_pipe.png'), _dots('um_wpx_slot_line.png')
    H, W = held.shape[:2]
    h, w = idle.shape[:2]
    c = 6
    for (hs, ws), (is_, iw) in (((slice(0, c), slice(0, c)), (slice(0, c), slice(0, c))),
                                 ((slice(0, c), slice(W - c, W)), (slice(0, c), slice(w - c, w))),
                                 ((slice(H - c, H), slice(0, c)), (slice(h - c, h), slice(0, c))),
                                 ((slice(H - c, H), slice(W - c, W)), (slice(h - c, h), slice(w - c, w)))):
        assert ((held[hs, ws, 3] > 0) == (idle[is_, iw, 3] > 0)).all(), (hs, ws)
    lum = lambda a: max(_luma(tuple(int(v) for v in px[:3])) for px in a[a[:, :, 3] > 0])
    assert lum(idle) < lum(held), (lum(idle), lum(held))
    assert _luma(_outer_color('um_wpx_slot_line.png')) >= IDLE_MIN_LUMA


def test_w6_tier_crystals_are_as_clear_as_the_haze_crystal():
    """(4) PixelLab 단계 색 결정(보라·금·빨강)은 청록 결정과 실루엣이 같고, 밝기 폭(가장 밝은 - 가장 어두운)이 청록의 0.8배 이상이다(탁하지 않다)."""
    base = _dots('um_wpx_crystal_haze.png')
    def span(a):
        ls = [_luma(tuple(int(v) for v in px[:3])) for px in a[a[:, :, 3] > 0]]
        return max(ls) - min(ls)
    for lv in (1, 2, 3):
        a = _dots(f'um_wpx_crystal_e{lv}.png')
        assert ((a[:, :, 3] > 0) == (base[:, :, 3] > 0)).all(), lv
        assert span(a) >= 0.8 * span(base), (lv, span(a), span(base))


def test_w6_name_sits_on_the_slot_and_rises_only_for_the_hint():
    """(5) 평소 프레임(설명 줄 없음): 무기 이름 글자 상자의 아랫변이 든 칸 윗변에서 W6_NAME_GAP 이하로 붙어 있다(1번·2번 듦).
    설명 줄이 뜬 프레임: 이름이 설명 줄보다 위에 있고 둘이 겹치지 않으며, 설명 줄이 든 칸과도 겹치지 않는다."""
    for slot in ('one', 'two'):
        u, p = _w5_ui(_w1_preps()[(slot, 'ready')])
        x, y, w, h = _w5_slot_rect(p)
        r = _w5_shown(u)
        boxes = _row_boxes(r)
        name = [bx for row, bx in boxes if row[0] == 'draw_text' and row[3] == p.weapon.name and row[4] != hud_kit.SHADOW]
        hint = [bx for row, bx in boxes if row[0] == 'draw_text' and row[3] == _w5_hint(u, p) and row[4] != hud_kit.SHADOW]
        assert name and hint, slot
        assert name[0][1] >= hint[0][3] and not _rect_overlap(name[0], hint[0]) and hint[0][1] >= y + h, (slot, name, hint)
        u.update(config.WEAPON_HINT_TIME + 0.5)
        r = _w5_draw(u)
        name = [bx for row, bx in _row_boxes(r) if row[0] == 'draw_text' and row[3] == p.weapon.name and row[4] != hud_kit.SHADOW]
        assert name and 0 <= name[0][1] - (y + h) <= W6_NAME_GAP, (slot, name, y + h)


# ----- R2 나머지 손질 2 (11/27, docs/opus/TASKS.md '4차' R2) -----
R2_GAP_DIFF = 4              # 결정과 소켓 안쪽 선 사이: 좌우 틈과 위아래 틈의 차이 (px)


def _r2_socket_scene(prep):
    """기본 그림(row + mix)으로 HUD를 그려 소켓 테두리·결정의 (그림 경로, 왼쪽, 아래) 를 돌려준다."""
    import ui
    assert config.HUD_WEAPON_STYLE == 'row' and config.HUD_WEAPON_ART == 'mix'

    def go():
        p, st, _pick = dict(_hud_states())['normal']()
        prep(p)
        with _Recorder() as r:
            ui.GameUI(p, st).draw()
        return r
    r = _with_skin('mist', go)
    out = {}
    for row in r.log:
        if row[0] in ('draw_image', 'draw_clip') and isinstance(row[1], str) and 'socket' in row[1] and 'well' not in row[1]:
            img = Image.open(os.path.join(ROOT, 'assets', row[1]))
            out['socket'] = (row[1], row[2] - img.width // 2, row[3])
        if row[0] == 'draw_image' and isinstance(row[1], str) and 'crystal' in row[1]:
            img = Image.open(os.path.join(ROOT, 'assets', row[1]))
            out['crystal'] = (row[1], row[2] - img.width // 2, row[3])
    return out


def _r2_masks(found, H=200, W=200):
    """소켓 선(가장 안쪽 선까지)·결정 픽셀을 같은 좌표(화면, 위가 0)의 마스크로."""
    sp, sl, sb = found['socket']
    cp, cl, cb = found['crystal']
    s = np.array(Image.open(os.path.join(ROOT, 'assets', sp)).convert('RGBA'))[:, :, 3] > 0
    c = np.array(Image.open(os.path.join(ROOT, 'assets', cp)).convert('RGBA'))[:, :, 3] > 0
    ox, oy = sl - 50, sb + s.shape[0] + 50            # 그림 좌표 원점
    S = np.zeros((H, W), bool)
    C = np.zeros((H, W), bool)
    S[oy - sb - s.shape[0]:oy - sb, sl - ox:sl - ox + s.shape[1]] = s
    C[oy - cb - c.shape[0]:oy - cb, cl - ox:cl - ox + c.shape[1]] = c
    return S, C


def _r2_gaps(S, C):
    """결정에서 소켓 선까지 가로(왼·오)·세로(위·아래) 가장 가까운 틈 (px)."""
    gaps = {'left': 999, 'right': 999, 'top': 999, 'bottom': 999}
    for y in np.nonzero(C.any(axis=1))[0]:
        xs = np.nonzero(C[y])[0]
        sx = np.nonzero(S[y])[0]
        lo, hi = sx[sx < xs.min()], sx[sx > xs.max()]
        if len(lo):
            gaps['left'] = min(gaps['left'], xs.min() - lo.max() - 1)
        if len(hi):
            gaps['right'] = min(gaps['right'], hi.min() - xs.max() - 1)
    for x in np.nonzero(C.any(axis=0))[0]:
        ys = np.nonzero(C[:, x])[0]
        sy = np.nonzero(S[:, x])[0]
        lo, hi = sy[sy < ys.min()], sy[sy > ys.max()]
        if len(lo):
            gaps['top'] = min(gaps['top'], ys.min() - lo.max() - 1)
        if len(hi):
            gaps['bottom'] = min(gaps['bottom'], hi.min() - ys.max() - 1)
    return gaps


def test_r2_crystal_sits_in_the_middle_of_the_socket():
    """(묶음 1) 기본 그림(row + mix): PixelLab 결정의 가로 가운데 = 마름모 테두리의 가로 가운데, 세로도 같다.
    결정과 테두리(가장 안쪽 선) 사이의 좌우 틈과 위아래 틈의 차이가 R2_GAP_DIFF px 이하, 왼쪽 = 오른쪽, 위 = 아래. 상태 넷(쓸 수 있음·못 씀·켬·줄어든 결정)."""
    def gauge(v):
        def f(p):
            p.gauge.value = v
            p.gauge.zone = p.gauge._zone_of(v)
        return f

    def on(p):
        gauge(90)(p)
        assert p.gauge.use_enhance()
    for name, prep in (('ready', gauge(62)), ('low', gauge(22)), ('on', on)):
        f = _r2_socket_scene(prep)
        assert 'socket' in f and 'crystal' in f, (name, f)
        S, C = _r2_masks(f)
        sx = np.nonzero(S.any(axis=0))[0]
        cx = np.nonzero(C.any(axis=0))[0]
        assert (sx.min() + sx.max()) == (cx.min() + cx.max()), (name, sx.min(), sx.max(), cx.min(), cx.max())
        sy = np.nonzero(S.any(axis=1))[0]
        cy = np.nonzero(C.any(axis=1))[0]
        assert (sy.min() + sy.max()) == (cy.min() + cy.max()), (name, sy.min(), sy.max(), cy.min(), cy.max())
        g = _r2_gaps(S, C)                                   # 가장 가까운 틈: 좌우·위아래 대칭이고 어디서도 선에 붙지 않는다
        assert g['left'] == g['right'] and g['top'] == g['bottom'], (name, g)
        assert min(g.values()) >= 4, (name, g)
        m = _r2_mid_gaps(S, C)                               # 눈에 보이는 틈: 결정 허리 옆(좌우)과 끝(위아래)
        assert m['left'] == m['right'] and m['top'] == m['bottom'], (name, m)
        assert abs(m['left'] - m['top']) <= R2_GAP_DIFF, (name, m)


def _r2_mid_gaps(S, C):
    """결정 가운데 줄에서 좌우 선까지, 가운데 열에서 위아래 선까지의 틈 (px). W6에서는 좌우 약 22, 위아래 약 6이었다."""
    ys, xs = np.nonzero(C.any(axis=1))[0], np.nonzero(C.any(axis=0))[0]
    r, c = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
    cx, sx = np.nonzero(C[r])[0], np.nonzero(S[r])[0]
    cy, sy = np.nonzero(C[:, c])[0], np.nonzero(S[:, c])[0]
    return {'left': cx.min() - sx[sx < cx.min()].max() - 1, 'right': sx[sx > cx.max()].min() - cx.max() - 1,
            'top': cy.min() - sy[sy < cy.min()].max() - 1, 'bottom': sy[sy > cy.max()].min() - cy.max() - 1}



def test_r2_hub_nameplates_of_things_are_light_grey_in_mist():
    """(묶음 3) 은신처 이름표: 사람이 아닌 것('무기 걸이'·'연습장')은 mist에서 밝은 회백, 사람 NPC 이름표는 인물 색 그대로.
    무기 걸이의 지금 건 무기 밑줄도 옅은 노랑 대신 회백. 다른 스킨은 예전 그대로."""
    import npc as npc_mod
    for kind in ('armory', 'practice'):
        cols = [c for t, c in _texts(_hub_npc_log('mist', kind)) if t == npc_mod.NAMES[kind]]
        assert cols and all(not _yellowish(c) and min(c) >= 200 for c in cols), (kind, cols)
        for skin_name in ('plate', 'plate_code', 'crystal'):
            cols = [c for t, c in _texts(_hub_npc_log(skin_name, kind)) if t == npc_mod.NAMES[kind]]
            assert cols == [npc_mod.COLORS[kind]], (skin_name, kind, cols)
    for kind in ('mechanic', 'keeper', 'archivist'):
        cols = [c for t, c in _texts(_hub_npc_log('mist', kind)) if t == npc_mod.NAMES[kind]]
        assert cols == [npc_mod.COLORS[kind]], (kind, cols)
    import meta
    _temp_saves()
    meta.state['start_weapon'] = meta.START_WEAPONS[0]
    try:
        for skin_name, want in (('mist', npc_mod.PROMPT_MIST), ('plate', npc_mod.COLORS['armory'])):
            r = _hub_npc_log(skin_name, 'armory')
            # Q1(11/27): 걸이 그림이 PixelLab 한 장이 되어 표시 줄은 걸린 무기마다 폭이 다르고, 두 칸(철파이프 + 고른 무기) 모두에 켜진다
            marks = [tuple(row[5]) for row in r.log if row[0] == 'draw_rect_color' and row[4] == 4]
            assert marks == [want, want], (skin_name, marks)
    finally:
        meta.reset()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
