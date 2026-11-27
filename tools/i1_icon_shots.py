"""I1 무기·아이템 아이콘 다시 뽑기 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' I1).

실제 창(모니터 2)에서 게임의 그리기 코드 그대로 찍는다. 설정·저장 파일은 임시 폴더로 돌린다.
같은 시드·같은 프레임 수라 아이콘을 바꾸기 전·후가 같은 순간이다.

  python tools/i1_icon_shots.py <출력 폴더>
      i1_hud_<방>_<두 칸>_<든 칸>.png  HUD (방: dark 구역 1 / bright 구역 3, 두 칸: pp 철파이프+쌍권총 / gc 건틀릿+사슬)
      i1_rack_window.png, i1_rack_hideout.png  무기 걸이 창, 은신처 걸이 옆
      i1_ped_shop.png, i1_ped_gold.png  진열대 앞
      i1_cards_form.png, i1_pause.png, i1_ending.png  형태 카드, 일시정지 '이번 판', 사망 결과(맡길 물건)
  python tools/i1_icon_shots.py --board <전 폴더> <후 폴더> <비교판 폴더> <전 아이콘 폴더>
      I1_sheet.png, I1_hud.png, I1_rack.png, I1_pedestal.png, I1_cards.png
"""
import ctypes
import glob
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1920, 1080
ITEMS_HELD = ('cap', 'absorb', 'steady', 'enhance', 'resist', 'dash', 'power', 'vigor')


def shoot(out):
    os.makedirs(out, exist_ok=True)
    import pico2d.pico2d as p2
    import sdl2
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

    import config
    import meta
    import options
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')     # 사용자 저장을 건드리지 않는다
    meta.reset()
    options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')   # 사용자 설정을 건드리지 않는다
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window(2)
    import boss_intro
    import camera
    import effects
    import ending_mode
    import forms
    import game_framework
    import game_world
    import items
    import mutation_mode
    import npc_mode
    import pause_mode
    import play_mode
    import transition
    import zone_card
    for mod in (play_mode, pause_mode, npc_mode, mutation_mode, ending_mode):
        mod.update_canvas = lambda: None
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(mod, name):
        transition._left = 0.0
        mod.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'i1_{name}.png'))
        p2.update_canvas()

    def new_run(seed):
        random.seed(seed)
        boss_intro.reset_all()
        effects.reset()
        game_framework.stack[:] = [play_mode]
        play_mode.enter()
        return play_mode.player

    def go(target, kind):
        play_mode._test_jump(target)
        st = play_mode.stage
        coord = next(c for c in st.layout if st.type_of(c) == kind)
        st.enter_room(coord, 'L')
        play_mode.room = st.room
        camera.snap(play_mode.player, st.room)

    def run(n):
        p = play_mode.player
        for _ in range(n):
            zone_card.freezing = False
            for o in list(game_world.world[game_world.LAYER_UI]):
                if isinstance(o, zone_card.ZoneCard):
                    game_world.remove_object(o)
            p.hp = max(p.hp, p.max_hp * 0.7)
            game_framework.frame_time = 1 / 60
            play_mode.update()
        transition.reveal(0.0)
        transition.tick(5.0)

    # HUD: 어두운 방·밝은 벽 방 x 두 칸 둘 x 든 칸 둘 (무기 넷을 각각 든 모습과 들지 않은 모습), 아이템 줄
    for room, seed, target in (('dark', 11, 'stage1'), ('bright', 12, 'stage3')):
        for pair, (a, b) in (('pp', ('pipe', 'pistol')), ('gc', ('gauntlet', 'chain'))):
            for held in (0, 1):
                p = new_run(seed)
                p.set_loadout(a, b)
                for it in ITEMS_HELD:
                    items.apply(p, it)
                go(target, 'combat')
                p.swap_weapon(held)
                run(150)
                p.mouse_screen = (1180, 520)
                run(1)
                grab(play_mode, f'hud_{room}_{pair}_{held}')

    # 무기 걸이 창 (첫 칸 줄 고름), 은신처 걸이 옆
    meta.reset()
    p = new_run(21)
    run(20)
    npc_mode.kind, npc_mode.player = 'armory', p
    game_framework.stack[:] = [play_mode, npc_mode]
    npc_mode.enter()
    npc_mode.selected = 1
    grab(npc_mode, 'rack_window')
    p = new_run(21)
    rack = next(n for n in play_mode.stage.npcs if n.kind == 'armory')
    p.x = rack.x - 150
    camera.snap(p, play_mode.stage.room)
    run(60)
    game_framework.stack[:] = [play_mode]
    grab(play_mode, 'rack_hideout')

    # 진열대 앞: 정비방·황금방 (가운데 진열대 옆)
    for scene, kind, seed in (('ped_shop', 'shop', 24), ('ped_gold', 'gold', 25)):
        p = new_run(seed)
        p.set_loadout('pipe', 'pistol')
        p.shards = 80
        play_mode._test_jump('stage1')
        st = play_mode.stage
        st.cleared |= {c for c in st.layout if st.type_of(c) == 'combat'}
        coord = next(c for c in st.layout if st.type_of(c) == kind)
        st.enter_room(coord, 'L')
        play_mode.room = st.room
        ped = st.pedestals[1 if len(st.pedestals) > 1 else 0]
        p.x, p.y = ped.x + 10, ped.y + 10
        p.vx = p.vy = 0
        camera.snap(p, st.room)
        run(30)
        p.mouse_screen = (1180, 520)
        run(1)
        game_framework.stack[:] = [play_mode]
        grab(play_mode, scene)

    # 형태 카드
    p = new_run(27)
    go('stage1', 'combat')
    run(40)
    game_framework.stack[:] = [play_mode, mutation_mode]
    mutation_mode.setup(p, [forms.CARD + w for w in list(forms.FORMS)[:2]] + [forms.CARD + 'skip'])
    mutation_mode.enter()
    mutation_mode.age = 5.0
    mutation_mode.selected = 1
    grab(mutation_mode, 'cards_form')

    # 일시정지 '이번 판' (아이템 여럿)
    p = new_run(12)
    p.set_loadout('gauntlet', 'chain')
    for it in ITEMS_HELD:
        items.apply(p, it)
    go('stage3', 'combat')
    run(50)
    game_framework.stack[:] = [play_mode, pause_mode]
    pause_mode.enter()
    grab(pause_mode, 'pause')

    # 사망 결과: 맡길 물건 칸
    p = new_run(13)
    p.set_loadout('pipe', 'pistol')
    for it in ('absorb', 'power', 'vigor'):
        items.apply(p, it)
    go('stage2', 'combat')
    run(40)
    p.run_rooms, p.run_kills, p.run_ends, p.run_clock = 9, 41, 1, 754.0
    p.death_cause = '크래셔의 강타'
    meta.state['keeper'] = True
    ending_mode.result = 'dead'
    game_framework.stack[:] = [ending_mode]
    ending_mode.enter()
    ending_mode.choice = 1
    grab(ending_mode, 'ending')
    close_canvas()
    print('ok', out)


# ----- 비교판 -----
BG = (20, 20, 24)
try:
    FONT = ImageFont.truetype('malgun.ttf', 18)
except OSError:
    FONT = ImageFont.load_default()


def row_board(rows, path, label_w=200):
    pad = 10
    w = label_w + max(sum(im.width + pad for im in ims) for _l, ims in rows) + pad
    h = sum(max(im.height for im in ims) + pad for _l, ims in rows) + pad
    board = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(board)
    y = pad
    for label, ims in rows:
        d.text((pad, y + 4), label, fill=(230, 230, 230), font=FONT)
        x = label_w
        for im in ims:
            board.paste(im, (x, y))
            x += im.width + pad
        y += max(im.height for im in ims) + pad
    board.save(path)
    print('saved', path, board.size)


NAMES = ['icon_w_pipe', 'icon_w_pistol', 'icon_w_gauntlet', 'icon_w_chain', 'icon_f_pipe', 'icon_f_pistol', 'icon_f_gauntlet',
         'icon_f_chain', 'icon_cap', 'icon_absorb', 'icon_steady', 'icon_enhance', 'icon_resist', 'icon_dash', 'icon_power',
         'icon_vigor', 'icon_heal', 'icon_fury', 'icon_shard']


def _strip(folder, names, k, bg=(30, 34, 48)):
    ims = [Image.open(os.path.join(folder, n + '.png')).convert('RGBA') for n in names]
    s = Image.new('RGBA', (len(ims) * 56, 56), bg + (255,))
    for i, im in enumerate(ims):
        s.alpha_composite(im, (i * 56 + 4, 4))
    s = s.convert('RGB')
    return s.resize((s.width * k, s.height * k), Image.NEAREST) if k > 1 else s


def board(before, after, out, old_icons):
    os.makedirs(out, exist_ok=True)
    new_icons = os.path.join(ROOT, 'assets', 'ui')
    rows = []
    for title, names in (('무기·형태', NAMES[:8]), ('아이템', NAMES[8:])):
        rows += [(f'{title} 전 1배', [_strip(old_icons, names, 1)]), (f'{title} 후 1배', [_strip(new_icons, names, 1)]),
                 (f'{title} 전 4배', [_strip(old_icons, names[:6], 4)]), (f'{title} 후 4배', [_strip(new_icons, names[:6], 4)])]
        if len(names) > 6:
            rows += [(f'{title} 전 4배 (뒤)', [_strip(old_icons, names[6:], 4)]), (f'{title} 후 4배 (뒤)', [_strip(new_icons, names[6:], 4)])]
    row_board(rows, os.path.join(out, 'I1_sheet.png'))

    def pair(name, box, k=1):
        ims = [Image.open(os.path.join(f, f'i1_{name}.png')).crop(box) for f in (before, after)]
        if k > 1:
            ims = [im.resize((im.width * k, im.height * k), Image.NEAREST) for im in ims]
        return ims

    panel = (1480, 800, 1920, 1080)
    rows = []
    for room in ('dark', 'bright'):
        for pair_name in ('pp', 'gc'):
            for held in (0, 1):
                a, z = pair(f'hud_{room}_{pair_name}_{held}', panel)
                rows.append((f'{room} {pair_name} 든 칸 {held + 1}', [a, z]))
    a, z = pair('hud_dark_pp_0', (0, 0, 620, 200))
    rows.append(('아이템 줄 (전, 후)', [a, z]))
    a, z = pair('hud_dark_pp_0', (1560, 900, 1920, 1080), 3)
    rows.append(('무기 칸 3배', [a, z]))
    row_board(rows, os.path.join(out, 'I1_hud.png'))

    a, z = pair('rack_window', (360, 240, 1560, 900))
    b, y = pair('rack_hideout', (500, 700, 1100, 920))
    row_board([('걸이 창 전', [a]), ('걸이 창 후', [z]), ('은신처 걸이 전·후', [b, y])], os.path.join(out, 'I1_rack.png'))

    rows = []
    for label, scene, box in (('정비방 선반 넷', 'ped_shop', (1000, 580, 1760, 920)), ('황금방 형태(쌍권총)', 'ped_gold', (290, 650, 490, 810)),
                              ('황금방 무기(건틀릿)', 'ped_gold', (1500, 650, 1700, 810))):
        a, z = pair(scene, box)
        rows.append((f'{label} 전·후 1배', [a, z]))
        if box[2] - box[0] <= 200:
            a, z = pair(scene, box, 3)
            rows.append((f'{label} 전·후 3배', [a, z]))
    row_board(rows, os.path.join(out, 'I1_pedestal.png'))

    rows = []
    for scene in ('cards_form', 'pause', 'ending'):
        a, z = pair(scene, (0, 0, W, H))
        rows.append((f'{scene} 전·후 (절반)', [a.resize((960, 540), Image.NEAREST), z.resize((960, 540), Image.NEAREST)]))
    row_board(rows, os.path.join(out, 'I1_cards.png'))


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:6])
    else:
        shoot(sys.argv[1])
