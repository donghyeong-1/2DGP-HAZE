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


# ----- 2부: 다른 도구가 찍지 않는 화면 -----
def _gauge(p, v):
    p.gauge.value = v
    p.gauge.zone = p.gauge._zone_of(v)


def _clear_enemies():
    import game_world
    for o in list(game_world.world[game_world.LAYER_ENEMY]):
        game_world.remove_object(o)


@scene
def title_menus(s):
    import title_mode
    s.gf.stack[:] = [title_mode]
    title_mode.enter()
    for i in range(4):
        title_mode.selected = i
        s.grab(f'title_sel{i}', title_mode)


@scene
def hud_enhance_levels(s):
    """강화 1단계·3단계(궁극기 준비)."""
    p, st = _room(s, 51, 'stage1', 'combat', ('pipe', 'gauntlet'))
    _clear_enemies()
    p.mouse_screen = (1180, 520)
    for lv in (1, 3):
        _gauge(p, 95)
        p.gauge.enhance_level = 0
        for _ in range(lv):
            p.gauge.use_enhance()
        s.run(1)
        s.grab(f'hud_enh{lv}')


@scene
def hud_overload(s):
    """오버로드 기절 순간."""
    p, st = _room(s, 52, 'stage1', 'combat')
    _clear_enemies()
    _gauge(p, p.gauge.cap - 1)
    p.gauge.add(10, 'hit')
    s.run(30)
    s.grab('hud_overload')


@scene
def hud_overload_toast(s):
    """오버로드 기절 중에 짧은 알림이 뜬 순간 (자리가 겹치는지)."""
    import play_mode
    p, st = _room(s, 52, 'stage1', 'combat')
    play_mode.message_time = 0.0
    _clear_enemies()
    _gauge(p, p.gauge.cap - 1)
    p.gauge.add(10, 'hit')
    s.run(30)
    play_mode._show_message('조각이 부족합니다 (3/6)')
    s.grab('hud_overload_toast')


@scene
def pause_ask(s):
    """일시정지: '판 포기하고 은신처로'를 한 번 누른 확인 상태."""
    import pause_mode
    import play_mode
    s.new_run(63)
    s.go('stage1', 'combat')
    s.run(30)
    play_mode.message_time = 0.0
    s.gf.stack[:] = [play_mode, pause_mode]
    pause_mode.enter()
    pause_mode.selected = 2
    pause_mode.run('hideout')
    s.grab('pause_ask', pause_mode)
    pause_mode._reset_labels()
    pause_mode.asking = None


@scene
def hideout(s):
    """은신처 첫 화면 (결정 40)."""
    import meta
    import play_mode
    s.new_run(62)
    meta.state['crystals'] = 40
    s.run(200)
    play_mode.message_time = 0.0
    s.grab('hideout')


@scene
def hud_awake(s):
    p, st = _room(s, 53, 'stage2', 'combat', ('chain', 'pistol'))
    _gauge(p, 70)
    p.mouse_screen = (1180, 520)
    s.run(2)
    s.grab('hud_awake')


@scene
def room_clear(s):
    import play_mode
    p, st = _room(s, 54, 'stage1', 'combat')
    _clear_enemies()
    s.run(5)
    play_mode.clear_notice = 2.0
    s.grab('room_clear')
    s.run(150)
    s.grab('room_after_clear')


@scene
def event_rooms(s):
    import camera
    for kind_seed, name in ((55, 'event_room_a'), (56, 'event_room_b')):
        p, st = _room(s, kind_seed, 'stage1', 'event')
        ev = st.event
        if ev is not None:
            p.x, p.y = ev.x - 60, ev.y
            camera.snap(p, st.room)
        s.run(10)
        s.grab(name)


@scene
def challenge(s):
    import play_mode
    p = s.new_run(57)
    st = s.go('stage1')
    c = next(iter(getattr(st, 'challenges', []) or []), None)
    if c is None:
        return
    import camera
    st.enter_room(c, 'L')
    play_mode.room = st.room
    camera.snap(p, st.room)
    s.run(120)
    s.grab('challenge')


@scene
def big_room(s):
    import camera
    import play_mode
    p = s.new_run(58)
    st = s.go('stage1')
    c = next((c for c in st.layout if st.is_big(c)), None)
    if c is None:
        return
    st.enter_room(c, 'L')
    play_mode.room = st.room
    camera.snap(p, st.room)
    s.run(60)
    s.grab('big_room')


@scene
def boss_intro_steps(s):
    """보스 등장씬 (이름 카드·대사 띠)과 페이즈 컷인."""
    import config
    import cut_in
    import play_mode
    config.BOSS_INTRO = True
    try:
        s.new_run(59)
        play_mode._test_jump('stage2')
        play_mode._test_jump('boss')
        for t, name in ((90, 'boss_intro_a'), (90, 'boss_intro_b'), (90, 'boss_intro_c'), (90, 'boss_intro_d'), (120, 'boss_intro_e')):
            for _ in range(t):
                s.gf.frame_time = 1 / 60
                play_mode.update()
            s.grab(name)
    finally:
        config.BOSS_INTRO = False
    b = play_mode.stage.boss
    if b is not None:
        cut_in.boss_phase(b, 2, '분노')
        for _ in range(20):
            cut_in.update(1 / 60)
        s.grab('boss_phase_cutin')
        cut_in.reset()


@scene
def ult_cutin(s):
    import cut_in
    import mutations as mu
    import weapon
    p, st = _room(s, 60, 'stage1', 'combat', ('pipe', 'pistol'))
    mu.give(p, 'ult_awaken')
    _gauge(p, 95)
    for _ in range(3):
        p.gauge.use_enhance()
    p.mouse_screen = (1180, 520)
    s.run(1)
    p.weapon.attack() if hasattr(p.weapon, 'attack') else None
    for _ in range(18):
        cut_in.update(1 / 60)
    s.grab('ult_cutin')
    cut_in.reset()


@scene
def easy_flash(s):
    """초보자 모드·번쩍임 줄이기 켬: 오버로드 순간."""
    import options
    options.easy_mode, options.reduce_flash = True, True
    try:
        p, st = _room(s, 52, 'stage1', 'combat')
        _clear_enemies()
        _gauge(p, p.gauge.cap - 1)
        p.gauge.add(10, 'hit')
        s.run(8)
        s.grab('easy_flash_overload')
    finally:
        options.easy_mode, options.reduce_flash = False, False


# ----- N1: 바뀐 이름·대사 -----
@scene
def n1_cards(s):
    import curse
    import forms
    for name, ids in (('n1_cards_a', ['dashcut_refund', 'ric_evo', 'ric_more']),
                      ('n1_cards_b', ['charge_fast', 'dashcut_power', 'gather_more']),
                      ('n1_cards_c', ['rapid_speed', 'rapid_extra', 'dshot_load']),
                      ('n1_cards_d', ['duo_vortex_collapse', 'duo_bolt_bowl', curse.CARD + 'lock']),
                      ('n1_cards_e', [curse.CARD + 'doom', forms.CARD + 'gauntlet', 'dashcut_wide'])):
        s.cards(name, ids)


@scene
def n1_pedestal(s):
    """정비방 진열대 앞: '공격력 강화'."""
    import camera
    p, st = _room(s, 64, 'stage1', 'shop')
    ped = st.pedestals[0]
    ped.item_id = 'power'
    p.x, p.y = ped.x, ped.y
    camera.snap(p, st.room)
    s.run(3)
    s.grab('n1_pedestal')


@scene
def n1_floats(s):
    """궁극기 이름(쌍권총), 완벽 회피, 격발·교체기 글자."""
    import combo
    import effects
    p, st = _room(s, 65, 'stage1', 'combat', ('pistol', 'pipe'))
    _clear_enemies()
    _gauge(p, 95)
    for _ in range(3):
        p.gauge.use_enhance()
    p.mouse_screen = (1180, 520)
    cx, cy = p.center
    effects.float_text(cx + 300, cy + 90, '완벽 회피!', (150, 245, 255), big=True, life=3.0)
    effects.float_text(cx + 650, cy + 150, '격발 · ' + combo.NAMES['pipe'], (240, 248, 255), big=True, life=3.0)
    effects.float_text(cx + 650, cy + 60, '강화 ' + combo.STRIKE_NAMES['pipe'], (240, 248, 255), life=3.0)
    s.run(2)
    s.grab('n1_floats')


@scene
def n1_barks(s):
    """보스 대사 띠: 바뀐 줄을 한 줄씩."""
    import boss_intro
    lines = [('gatekeeper', boss_intro.LINES['gatekeeper']['intro'][1]), ('ark', boss_intro.LINES['ark']['phase2']),
             ('heart', boss_intro.LINES['heart']['intro'][0]), ('heart', boss_intro.LINES['heart']['intro'][2]),
             ('heart', boss_intro.LINES['heart']['phase2'])]
    p, st = _room(s, 66, 'stage3', 'combat')
    for i, (kind, text) in enumerate(lines):
        info = boss_intro.LINES[kind]
        boss_intro._bark[0] = [info['speaker'], text, info['color'], 9.0]
        s.run(2)
        s.grab(f'n1_bark_{i}')
    boss_intro._bark[0] = None


def _grab_window(s, name, mod):
    """창 크기 그대로 읽는다 (해상도 장면: 논리 화면 1920x1080을 SDL이 창에 맞춰 줄인 결과)."""
    import play_mode
    import transition
    w, h = ctypes.c_int(), ctypes.c_int()
    s.sdl2.SDL_GetRendererOutputSize(s.p2.renderer, ctypes.byref(w), ctypes.byref(h))
    buf = (ctypes.c_ubyte * (w.value * h.value * 4))()
    transition._left = 0.0
    (mod or play_mode).draw()
    s.sdl2.SDL_RenderReadPixels(s.p2.renderer, None, s.sdl2.SDL_PIXELFORMAT_RGBA32, buf, w.value * 4)
    Image.frombuffer('RGBA', (w.value, h.value), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(
        os.path.join(s.out, f'{name}.png'))
    s.p2.update_canvas()


@scene
def resolutions(s):
    """해상도 1280x720·1600x900·1920x1080에서 타이틀·HUD·설정."""
    import display
    import options
    import options_mode
    import play_mode
    import title_mode
    names = [n for n, _w, _h in options.RESOLUTIONS]
    for name, tag in (('960x540', '960'), ('1280x720', '1280'), ('1600x900', '1600'), ('1920x1080', '1920')):
        if name not in names:                           # N1 전 코드 (960x540 없음)
            continue
        level = names.index(name)
        options.set_resolution(level)
        display.apply()
        s.gf.stack[:] = [title_mode]
        title_mode.enter()
        title_mode.selected = 0
        _grab_window(s, f'res_{tag}_title', title_mode)
        s.gf.stack.append(options_mode)
        options_mode.enter()
        options_mode.selected = 4
        _grab_window(s, f'res_{tag}_options', options_mode)
        p, st = _room(s, 61, 'stage1', 'combat')
        _gauge(p, 62)
        p.mouse_screen = (1180, 520)
        s.run(2)
        _grab_window(s, f'res_{tag}_hud', play_mode)
        import mutation_mode
        s.gf.stack[:] = [play_mode, mutation_mode]
        mutation_mode.setup(p, ['ult_awaken', 'link_bind', 'dshot_load'])
        mutation_mode.enter()
        mutation_mode.age, mutation_mode.selected = 5.0, 1
        _grab_window(s, f'res_{tag}_cards', mutation_mode)
    options.set_resolution(names.index('1920x1080'))
    display.apply()


# ----- N1: 설정 설명·패드 안내 -----
@scene
def n1_options(s):
    """설정(타이틀 위): 맨 위·가운데·맨 아래 줄을 골랐을 때."""
    import options_mode
    import title_mode
    for sel, tag in ((0, 'top'), (5, 'mid'), (len(options_mode.ROWS) - 1, 'bottom')):
        s.gf.stack[:] = [title_mode]
        title_mode.enter()
        s.gf.stack.append(options_mode)
        options_mode.enter()
        options_mode.selected = sel
        s.grab(f'n1_options_{tag}', options_mode)


@scene
def n1_pad(s):
    """같은 장면을 키보드 안내와 패드 안내로: 일시정지, 진열대 상호작용, 처음 안내, 증강 카드, NPC 창, 설정, 보스 대사 넘기기."""
    import camera
    try:
        import input_device
    except ImportError:                                 # N1 전 코드: 키보드 안내만
        input_device = None
    import npc_mode
    import options_mode
    import pause_mode
    import play_mode
    import mutation_mode
    import tutorial
    import game_world
    for dev in ('kb', 'pad'):
        if input_device is not None:
            input_device.use(input_device.PAD if dev == 'pad' else input_device.KEYBOARD)
        elif dev == 'pad':
            continue
        p, st = _room(s, 67, 'stage1', 'shop')
        ped = next(d for d in st.pedestals if d.item_id != 'heal')
        p.x, p.y = ped.x, ped.y
        camera.snap(p, st.room)
        t = next(o for o in game_world.world[game_world.LAYER_UI] if isinstance(o, tutorial.Tutorial))
        t.current, t.left = 'move', 2.0
        s.run(2, hints=True)
        t.current, t.left = 'move', 2.0
        s.grab(f'n1_pad_hud_{dev}')
        s.gf.stack[:] = [play_mode, pause_mode]
        pause_mode.enter()
        s.grab(f'n1_pad_pause_{dev}', pause_mode)
        s.gf.stack[:] = [play_mode, mutation_mode]
        mutation_mode.setup(p, ['combo_speed', 'link_bind', 'dshot_load'])
        mutation_mode.enter()
        mutation_mode.age, mutation_mode.selected = 5.0, 1
        s.grab(f'n1_pad_cards_{dev}', mutation_mode)
        npc_mode.kind, npc_mode.player = 'mechanic', p
        s.gf.stack[:] = [play_mode, npc_mode]
        npc_mode.enter()
        s.grab(f'n1_pad_npc_{dev}', npc_mode)
        s.gf.stack[:] = [play_mode, pause_mode, options_mode]
        options_mode.enter()
        s.grab(f'n1_pad_options_{dev}', options_mode)
    if input_device is not None:
        input_device.use(input_device.KEYBOARD)


def main():
    if '--list' in sys.argv:
        print('\n'.join(SCENES))
        return
    out = sys.argv[1]
    want = sys.argv[2:] or SCENES
    s = Shooter(out)
    g = globals()
    import postfx
    for name in want:
        postfx.stop()                                   # U1-3: 앞 장면의 화면 연출(실제 시간 약 1초)이 다음 장면에 남지 않게
        postfx._zoom = None
        g[name](s)
        print('찍음', name)
    from pico2d import close_canvas
    close_canvas()


if __name__ == '__main__':
    main()
