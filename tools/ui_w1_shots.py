"""W1 무기·E 패널 시안 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' W1): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
config.HUD_WEAPON_STYLE을 'flat'·'a'·'b'·'c'로 바꿔 가며 같은 시드·같은 프레임 수로 찍어 같은 순간을 비교한다.
설정·저장 파일은 임시 폴더로 돌린다(사용자 파일을 건드리지 않는다). tools/ui_hud2_shots.py의 방식을 잇는다.

  python tools/ui_w1_shots.py <출력 폴더>                 장면 찍기: w1_<시안>_<방>_<상태>.png, w1_<시안>_cards.png
  python tools/ui_w1_shots.py --board <출력 폴더> <비교판 폴더>
        W1_compare_dark.png·W1_compare_bright.png(가로 flat·A·B·C, 세로 상태 여섯, 패널 둘레를 원래 크기로),
        W1_full_<a|b|c>.png(시안별 전체 화면, 평소 상태, 전투 방), W1_set_<a|b|c>.png(HUD 전체 화면 | 증강 카드 화면)

상태(H2와 같다): a_ready 평소(강화 쓸 수 있음, 1번 듦) / b_on1 강화 1단계 켬 / c_on2 강화 2단계 켬 / d_low 게이지 모자람 /
      e_slot2 2번 듦 / f_empty 둘째 칸 빈 칸.  방: dark 어두운 방, bright 밝은 벽 방.
"""
import ctypes
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
from PIL import Image, ImageDraw  # noqa: E402

W, H = 1920, 1080
STYLES = ('flat', 'a', 'b', 'c')
SLOT_STATES = ('a_ready', 'b_on1', 'c_on2', 'd_low', 'e_slot2', 'f_empty')
ROOMS = {'dark': (11, 'stage1'), 'bright': (12, 'stage3')}
PANEL_BOX = (1500, 790, 1920, 1080)          # 원래 크기로 자를 부분 (PIL 좌표: 위가 0)


def shoot(out):
    os.makedirs(out, exist_ok=True)
    import pico2d.pico2d as p2
    import sdl2
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

    import config
    import meta
    import options
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')
    meta.reset()
    options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window(2)
    import boss_intro
    import camera
    import effects
    import game_framework
    import game_world
    import mutation_mode
    import mutations as mu
    import play_mode
    import transition
    import zone_card
    for mod in (play_mode, mutation_mode):
        mod.update_canvas = lambda: None              # 화면에 내보내기 전에 읽는다
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(mod, name):
        transition._left = 0.0
        mod.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'w1_{name}.png'))
        p2.update_canvas()

    def new_run(seed):
        random.seed(seed)
        boss_intro.reset_all()
        effects.reset()
        game_framework.stack[:] = [play_mode]
        play_mode.enter()
        return play_mode.player

    def go(target, cell_kind='combat'):
        play_mode._test_jump(target)
        st = play_mode.stage
        coord = next(c for c in st.layout if st.type_of(c) == cell_kind)
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

    def gauge(p, v):
        p.gauge.value = v
        p.gauge.zone = p.gauge._zone_of(v)

    for style in STYLES:
        config.HUD_WEAPON_STYLE = style
        for room, (seed, target) in ROOMS.items():
            for state in SLOT_STATES:
                p = new_run(seed)
                p.set_loadout('pipe') if state == 'f_empty' else p.set_loadout('pipe', 'pistol')
                go(target)
                if state != 'e_slot2':
                    p.swap_weapon(0)                      # 1번 무기 (set_loadout은 둘째 칸을 든다)
                run(80)                                    # 교체 쿨다운이 다 차도록
                gauge(p, 22 if state == 'd_low' else 62)
                if state in ('b_on1', 'c_on2'):
                    p.gauge.use_enhance()
                if state == 'c_on2':
                    p.gauge.use_enhance()
                p.mouse_screen = (1180, 520)
                run(1)
                p.aura_time = 0.1
                grab(play_mode, f'{style}_{room}_{state}')
        # 증강 카드 화면 (그 시안의 HUD가 뒤에 깔린다)
        p = new_run(27)
        go('stage1')
        p.swap_weapon(0)
        run(40)
        gauge(p, 62)
        game_framework.stack[:] = [play_mode, mutation_mode]
        mutation_mode.setup(p, list(mu.MUTATIONS)[:3])
        mutation_mode.enter()
        mutation_mode.age = 5.0
        mutation_mode.selected = 1
        grab(mutation_mode, f'{style}_cards')
    config.HUD_WEAPON_STYLE = 'flat'
    close_canvas()
    print('ok', out)


def _label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 7 * len(text) + 12, 16), fill=(0, 0, 0))
    d.text((5, 3), text, fill=(255, 255, 120))
    return im


def board(src, out):
    os.makedirs(out, exist_ok=True)
    made = []
    cw, ch = PANEL_BOX[2] - PANEL_BOX[0], PANEL_BOX[3] - PANEL_BOX[1]
    for room in ROOMS:
        im = Image.new('RGB', ((cw + 20) * len(STYLES) - 20, (ch + 10) * len(SLOT_STATES)), (20, 20, 24))
        for r, s in enumerate(SLOT_STATES):
            for c, style in enumerate(STYLES):
                crop = Image.open(os.path.join(src, f'w1_{style}_{room}_{s}.png')).crop(PANEL_BOX)
                im.paste(_label(crop, f'{style.upper()} {s}'), (c * (cw + 20), r * (ch + 10)))
        name = f'W1_compare_{room}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    for style in STYLES[1:]:
        full = _label(Image.open(os.path.join(src, f'w1_{style}_dark_a_ready.png')), f'{style.upper()} dark a_ready')
        full.save(os.path.join(out, f'W1_full_{style}.png'))
        made.append(f'W1_full_{style}.png')
        im = Image.new('RGB', (W * 2 + 20, H), (20, 20, 24))
        im.paste(_label(Image.open(os.path.join(src, f'w1_{style}_bright_a_ready.png')), f'{style.upper()} HUD'), (0, 0))
        im.paste(_label(Image.open(os.path.join(src, f'w1_{style}_cards.png')), f'{style.upper()} cards'), (W + 20, 0))
        im.save(os.path.join(out, f'W1_set_{style}.png'))
        made.append(f'W1_set_{style}.png')
    print(len(made), '장:', ', '.join(made))


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:4])
    else:
        shoot(sys.argv[1])
