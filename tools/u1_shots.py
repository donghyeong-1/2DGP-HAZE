"""U1(2026-11-27) 글 반영·UI 검토 확인 촬영: 실제 창(모니터 2)에서 게임의 그리기 코드 그대로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. 같은 시드·같은 프레임 수라 고치기 전·후가 같은 순간이다.
  python tools/u1_shots.py <출력 폴더> [장면 이름 ...]      장면마다 <장면>.png (이름을 주면 그것만)
  python tools/u1_shots.py --list                          장면 이름 목록
장면은 아래 SCENES 순서. 다른 촬영 도구(ui_menu_shots·ui_pick_shots·ui_hud_shots·ui_mist_shots)가 찍는 화면은 다시 찍지 않는다.
"""
import ctypes
import os
import random
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
W, H = 1920, 1080
SCENES = []


def scene(fn):
    SCENES.append(fn.__name__)
    return fn


class Shooter:
    """게임 한 번 띄워 두고 장면을 차례로 찍는다."""

    def __init__(self, out):
        import pico2d.pico2d as p2
        import sdl2
        from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, open_canvas
        import config
        import meta
        import options
        self.p2, self.sdl2, self.out = p2, sdl2, out
        os.makedirs(out, exist_ok=True)
        meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')
        meta.reset()
        options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
        import keybinds
        keybinds.reset()
        SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
        open_canvas(config.SCREEN_W, config.SCREEN_H)
        from window_place import place_window
        place_window(2)
        import game_framework
        for name in ('play_mode', 'pause_mode', 'options_mode', 'title_mode', 'npc_mode', 'practice_mode', 'sfx_mode',
                     'mutation_mode', 'keys_mode', 'ending_mode', 'credits_mode'):
            __import__(name).update_canvas = lambda: None          # 화면에 내보내기 전에 읽는다
        config.BOSS_INTRO = False
        self.buf = (ctypes.c_ubyte * (W * H * 4))()
        self.gf = game_framework

    def grab(self, name, mod=None):
        import play_mode
        import transition
        transition._left = 0.0
        (mod or play_mode).draw()
        self.sdl2.SDL_RenderReadPixels(self.p2.renderer, None, self.sdl2.SDL_PIXELFORMAT_RGBA32, self.buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(self.buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(
            os.path.join(self.out, f'{name}.png'))
        self.p2.update_canvas()

    def new_run(self, seed, weapons=('pipe', 'pistol')):
        import boss_intro
        import effects
        import play_mode
        random.seed(seed)
        boss_intro.reset_all()
        effects.reset()
        self.gf.stack[:] = [play_mode]
        play_mode.enter()
        p = play_mode.player
        if weapons:
            p.set_loadout(*weapons)
        return p

    def go(self, target, cell_kind=None):
        import camera
        import play_mode
        play_mode._test_jump(target)
        st = play_mode.stage
        if cell_kind:
            coord = next(c for c in st.layout if st.type_of(c) == cell_kind)
            st.enter_room(coord, 'L')
            play_mode.room = st.room
            camera.snap(play_mode.player, st.room)
        return st

    def run(self, n, hints=False):
        import game_world
        import play_mode
        import transition
        import tutorial
        import zone_card
        p = play_mode.player
        for _ in range(n):
            zone_card.freezing = False
            for o in list(game_world.world[game_world.LAYER_UI]):
                if isinstance(o, zone_card.ZoneCard) or (not hints and isinstance(o, tutorial.Tutorial)):
                    if isinstance(o, tutorial.Tutorial):
                        o.current = None
                    else:
                        game_world.remove_object(o)
            p.hp = max(p.hp, 1)
            self.gf.frame_time = 1 / 60
            play_mode.update()
        transition.reveal(0.0)
        transition.tick(5.0)

    def cards(self, name, ids, selected=1, seed=27):
        import mutation_mode
        import play_mode
        p = self.new_run(seed)
        self.go('stage1', 'combat')
        self.run(40)
        prep = getattr(self, 'card_prep', None)
        if prep:
            prep(p)
        self.gf.stack[:] = [play_mode, mutation_mode]
        mutation_mode.setup(p, ids)
        mutation_mode.enter()
        mutation_mode.age = 5.0
        mutation_mode.selected = selected
        self.grab(name, mutation_mode)


# ----- 1부: 글이 바뀐 화면 -----
@scene
def cards_text_1(s):
    s.cards('cards_text_1', ['ult_awaken', 'link_bind', 'dshot_load'])


@scene
def cards_text_2(s):
    s.cards('cards_text_2', ['link_share', 'link_burst', 'crash_wall'])


@scene
def cards_text_3(s):
    s.cards('cards_text_3', ['ric_evo', 'duo_swap_mist', 'ember_burst'])


@scene
def cards_text_4(s):
    s.cards('cards_text_4', ['gather_clash', 'counter_guard', 'tide_cost'])


@scene
def cards_text_5(s):
    s.cards('cards_text_5', ['dashcut_wide', 'charge_parry', 'ric_more'])


@scene
def cards_curse(s):
    import curse
    s.cards('cards_curse', ['bloom_crit', curse.CARD + 'lowcap', 'air_hang'])


@scene
def cards_drifter(s):
    import events
    s.cards('cards_drifter', events.cards('drifter'))


@scene
def cards_spring(s):
    import events
    s.cards('cards_spring', events.cards('spring'))


def _hint(s, hid, seed, gauge=None, weapons=('pipe', 'pistol')):
    import game_world
    import play_mode
    import tutorial
    p = s.new_run(seed, weapons)
    s.go('stage1', 'combat')
    s.run(30)
    if gauge is not None:
        p.gauge.value = gauge
        p.gauge.zone = p.gauge._zone_of(gauge)
    t = next(o for o in game_world.world[game_world.LAYER_UI] if isinstance(o, tutorial.Tutorial))
    t.current, t.left = hid, 2.0
    s.grab(f'hint_{hid}')


@scene
def hint_fade(s):
    _hint(s, 'fade', 31, 12)


@scene
def hint_critical(s):
    _hint(s, 'critical', 32, 94)


@scene
def hint_enhance(s):
    _hint(s, 'enhance', 33, 60)


@scene
def hint_weapon(s):
    _hint(s, 'weapon', 34, 40)


@scene
def hint_move(s):
    _hint(s, 'move', 35, 40)


def _room(s, seed, zone, kind, weapons=('pipe', 'pistol')):
    p = s.new_run(seed, weapons)
    st = s.go(zone, kind)
    s.run(30)
    return p, st


@scene
def ped_rift(s):
    """균열방 진열대 앞: 'N~N+1단계' 설명."""
    import camera
    import play_mode
    p, st = _room(s, 41, 'stage1', 'rift')
    ped = next(d for d in st.pedestals if d.item_id != 'fury')
    p.x, p.y = ped.x, ped.y
    camera.snap(p, st.room)
    s.run(2)
    s.grab('ped_rift')
    st.interact()                                       # 얻은 뒤 화면 아래 띠
    s.run(10)
    s.grab('pickup_rift')
    play_mode.player = p


@scene
def shop_full(s):
    """정비방에서 물약이 가득할 때 물약을 사려 함."""
    import camera
    import config
    p, st = _room(s, 42, 'stage1', 'shop')
    ped = next(d for d in st.pedestals if d.item_id == 'heal')
    p.potions = config.POTION_MAX
    p.shards = 30
    p.x, p.y = ped.x, ped.y
    camera.snap(p, st.room)
    s.run(2)
    st.interact()
    s.run(6)
    s.grab('shop_full')


@scene
def keys_swap(s):
    import keybinds
    import keys_mode
    import options_mode
    import sdl2
    import title_mode
    keybinds.reset()
    s.gf.stack[:] = [title_mode]
    title_mode.enter()
    s.gf.stack.append(options_mode)
    options_mode.enter()
    options_mode.selected = options_mode.ITEMS.index('keys')
    s.gf.stack.append(keys_mode)
    keys_mode.enter()
    keys_mode.row, keys_mode.col = 5, 0
    keys_mode.listening = ('enhance', 0)
    keys_mode.press_key(sdl2.SDLK_f)
    s.grab('keys_swap', keys_mode)
    keys_mode.listening = ('enhance', 0)
    keys_mode.press_key(sdl2.SDLK_F1)
    s.grab('keys_reserved', keys_mode)
    keys_mode.listening = ('jump', 0)
    s.grab('keys_listen', keys_mode)
    keys_mode.listening = None
    keybinds.reset()


def main():
    if '--list' in sys.argv:
        print('\n'.join(SCENES))
        return
    out = sys.argv[1]
    want = sys.argv[2:] or SCENES
    s = Shooter(out)
    g = globals()
    for name in want:
        g[name](s)
        print('찍음', name)
    from pico2d import close_canvas
    close_canvas()


if __name__ == '__main__':
    main()
