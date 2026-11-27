"""U1-2 (2026-11-27) UI·UX 검토에서 고친 동작 테스트 (창 없이). 실행: python tests/test_u1_ui.py

- 닫기·확인 키: NPC 창·연습 메뉴·효과음 듣기·사망 결과의 'F'는 상호작용 키 설정을 따른다(input-systems: 동작 이름으로 읽는다).
  상호작용을 G로 바꾸면 G로 열고 G로 닫는다. F를 다른 동작에 주면 F로는 닫히지 않는다.
- 메뉴 소리: 설정·키 설정·연습 메뉴·사망 결과에서 줄을 옮기면 이동 소리가 난다(game-feel: 반응 없는 선택 없음).
- 은신처 HUD(mist): 게이지·미니맵·판 안 재화(조각)를 빼고, 은신처에서 쓰는 헤이즈 결정을 보인다.
- 방 클리어 아래 '열린 문으로 이동하세요'는 처음 하는 사람에게만(처음 안내가 켜져 있고, 끝낸 판이 없고, 이 판에서 두 방까지).
- 오버로드로 기절한 동안 짧은 알림은 기절 막대 아래로 내려 겹치지 않는다.
- 일시정지의 판 포기 확인 문구가 어디로 가는지 말한다.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')

import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
import meta  # noqa: E402

meta.PATH = os.path.join(tempfile.mkdtemp(), 'meta.json')

import sdl2  # noqa: E402

import assets  # noqa: E402
import config  # noqa: E402
import game_framework  # noqa: E402
import game_world  # noqa: E402
import keybinds  # noqa: E402


class _Ev:
    def __init__(self, key, kind=sdl2.SDL_KEYDOWN):
        self.type, self.key = kind, key


class _Feed:
    """모드의 get_events·pop_mode·play_sound를 바꿔 끼운다."""

    def __init__(self, mod, keys):
        self.mod, self.keys = mod, keys

    def __enter__(self):
        self.popped, self.sounds = [], []
        self.saved = (self.mod.get_events, game_framework.pop_mode, assets.play_sound)
        self.mod.get_events = lambda: [_Ev(k) for k in self.keys]
        game_framework.pop_mode = lambda *a, **k: self.popped.append(True)
        assets.play_sound = lambda name, *a, **k: self.sounds.append(name)
        return self

    def __exit__(self, *exc):
        self.mod.get_events, game_framework.pop_mode, assets.play_sound = self.saved


def _bind_interact_g():
    keybinds.reset()
    keys = dict(keybinds.to_json())
    keys['interact'] = [sdl2.SDLK_g, None]
    keys['enhance'] = [sdl2.SDLK_f, None]
    keybinds.load_json(keys)


def _player():
    from player import Player
    from room import Room
    game_world.clear()
    p = Player(300, 120, Room.load('test_01'))
    game_world.add_object(p, game_world.LAYER_PLAYER)
    return p


# ----- 닫기 키 -----
def test_npc_window_closes_with_the_interact_key():
    import npc_mode
    npc_mode.kind, npc_mode.player = 'mechanic', _player()
    _bind_interact_g()
    try:
        with _Feed(npc_mode, [sdl2.SDLK_g]) as f:
            npc_mode.handle_events()
        assert f.popped, 'G(상호작용)로 닫혀야 한다'
        with _Feed(npc_mode, [sdl2.SDLK_f]) as f:
            npc_mode.handle_events()
        assert not f.popped, 'F는 이제 강화 키다'
        with _Feed(npc_mode, [sdl2.SDLK_ESCAPE]) as f:
            npc_mode.handle_events()
        assert f.popped
    finally:
        keybinds.reset()


def test_practice_and_sound_menus_close_with_the_interact_key():
    import practice_mode
    import sfx_mode
    _bind_interact_g()
    try:
        for mod in (practice_mode, sfx_mode):
            with _Feed(mod, [sdl2.SDLK_g]) as f:
                mod.handle_events()
            assert f.popped, mod.__name__
            with _Feed(mod, [sdl2.SDLK_f]) as f:
                mod.handle_events()
            assert not f.popped, mod.__name__
    finally:
        keybinds.reset()


def test_practice_footer_names_the_interact_key():
    import practice_mode
    _bind_interact_g()
    try:
        keys = ' '.join(k for k, _ in practice_mode.footer())
        assert 'G' in keys and 'F' not in keys, keys
    finally:
        keybinds.reset()


def test_death_result_takes_the_keepsake_with_the_interact_key():
    import ending_mode
    _bind_interact_g()
    try:
        ending_mode.choosing, ending_mode.choice, ending_mode._ignore_input = True, 0, 0
        ending_mode.choices = ['none']
        with _Feed(ending_mode, [sdl2.SDLK_f]) as f:
            ending_mode.handle_events()
        assert ending_mode.choosing, 'F(강화)로는 맡기지 않는다'
        with _Feed(ending_mode, [sdl2.SDLK_g]) as f:
            ending_mode.handle_events()
        assert not ending_mode.choosing
    finally:
        keybinds.reset()
        ending_mode.choosing = False


# ----- 메뉴 이동 소리 -----
def test_moving_in_menus_makes_the_move_sound():
    import keys_mode
    import options_mode
    import practice_mode
    import ending_mode
    for mod in (options_mode, keys_mode, practice_mode):
        with _Feed(mod, [sdl2.SDLK_s, sdl2.SDLK_w]) as f:
            mod.handle_events()
        assert f.sounds.count('ui_move') == 2, (mod.__name__, f.sounds)
    ending_mode.choosing, ending_mode.choice, ending_mode._ignore_input = True, 0, 0
    ending_mode.choices = ['none', 'cap']
    with _Feed(ending_mode, [sdl2.SDLK_d]) as f:
        ending_mode.handle_events()
    assert 'ui_move' in f.sounds, f.sounds
    ending_mode.choosing = False


# ----- 은신처 HUD -----
def _hud_texts(stage_name):
    import hud_kit
    import ui
    import test_ui_skin as tu
    p = _player()

    class St:
        name = stage_name
        boss = None
        challenge = None
        room = p.room
        coord = (0, 0)
        def minimap_cells(self):
            return [((0, 0), 'current', None, False)]
        def enemy_count(self):
            return 0
    hud = ui.GameUI(p, St())
    meta.ensure_loaded()
    meta.state['crystals'] = 37
    old = config.UI_SKIN
    config.UI_SKIN = 'mist'
    hud_kit.reset_skin() if hasattr(hud_kit, 'reset_skin') else None
    try:
        with tu._Recorder() as r:
            hud.draw()
    finally:
        config.UI_SKIN = old
    return [row[3] for row in r.log if row[0] == 'draw_text'], r.paths()


def test_hideout_hud_drops_gauge_and_map_and_shows_crystals():
    texts, paths = _hud_texts('hideout')
    assert not any('노멀' in t for t in texts), texts                     # 게이지 줄 없음
    assert '37' in texts, texts                                          # 헤이즈 결정
    assert not any('uc_shard' in p for p in paths), paths                # 판 안 조각 칩 없음
    texts, paths = _hud_texts('stage1')
    assert any('노멀' in t for t in texts), texts                         # 전투 구역은 그대로


# ----- 방 클리어 안내 -----
def test_room_clear_door_hint_only_for_new_players():
    import ui
    p = _player()
    meta.ensure_loaded()
    meta.state['runs'] = 0
    options.show_hints = True
    p.run_rooms = 1
    assert ui.clear_hint(p) == '열린 문으로 이동하세요'
    p.run_rooms = 3
    assert ui.clear_hint(p) is None                                      # 세 번째 방부터는 문 빛과 보상 판으로 충분
    p.run_rooms = 1
    meta.state['runs'] = 2
    assert ui.clear_hint(p) is None                                      # 판을 끝내 본 사람
    meta.state['runs'] = 0
    options.show_hints = False
    assert ui.clear_hint(p) is None
    options.show_hints = True


# ----- 기절 중 알림 자리 -----
def test_toast_moves_below_the_stun_bar():
    import ui
    p = _player()
    assert ui.toast_y(p) == ui.TOAST_Y - 40
    p.gauge.stun_timer = 1.0
    if not p.stunned:
        p.stunned_override = True
    y = ui.toast_y(p, stunned=True)
    assert y < ui.TOAST_Y - 10 - 22 - 30, y                              # 기절 글자(막대 아래 22px)보다 30px 이상 아래


# ----- 판 포기 확인 -----
def test_give_up_confirm_says_where_it_goes():
    import pause_mode
    pause_mode.asking = None
    with _Feed(pause_mode, []):
        pause_mode.run('hideout')
    label = pause_mode._button('hideout').label
    assert '은신처' in label and '포기' in label, label
    pause_mode._reset_labels()
    pause_mode.asking = None
    with _Feed(pause_mode, []):
        pause_mode.run('title')
    label = pause_mode._button('title').label
    assert '타이틀' in label and '포기' in label, label
    pause_mode._reset_labels()
    pause_mode.asking = None


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
