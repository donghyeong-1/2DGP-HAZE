"""W1 무기·E 패널 시안 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' W1): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
config.HUD_WEAPON_STYLE을 'flat'·'a'·'b'·'c'로 바꿔 가며 같은 시드·같은 프레임 수로 찍어 같은 순간을 비교한다.
설정·저장 파일은 임시 폴더로 돌린다(사용자 파일을 건드리지 않는다). tools/ui_hud2_shots.py의 방식을 잇는다.

  python tools/ui_w1_shots.py <출력 폴더>                 장면 찍기: w1_<시안>_<방>_<상태>.png, w1_<시안>_cards.png
  W1_ONLY=da,row W1_EXTRA=da,row python tools/ui_w1_shots.py <출력 폴더>  후
  W1_ONLY=row W1_EXTRA=row W5_OFF=row python tools/ui_w1_shots.py <출력 폴더>  후
  python tools/ui_w1_shots.py --board5 <출력 폴더> <W4 촬영 폴더(전)> <비교판 폴더>
        W5: W5_hint.png(설명 줄 뜬 순간 / 2초 뒤), W5_combo.png(무기 넷 콤보 칸 W4 전·후), W5_full.png
  python tools/ui_w1_shots.py --board4 <출력 폴더> <비교판 폴더>
        W4(row): W4_compare_dark/bright.png(가로 da·row), W4_weapons.png, W4_swap.png, W4_full.png, W4_corners.png
  W1_ONLY=d,a,da W1_EXTRA=da python tools/ui_w1_shots.py <출력 폴더>  후
  python tools/ui_w1_shots.py --board3 <출력 폴더> <비교판 폴더>
        W3(확정 da): W3_compare_dark.png·W3_compare_bright.png(가로 D·A·da, 세로 상태 여섯 + 강화 3단계), W3_weapons.png, W3_full.png, W3_set.png
  python tools/ui_w1_shots.py --board2 <출력 폴더> <비교판 폴더>
        W2(시안 D): W2_compare_dark.png·W2_compare_bright.png(가로 flat·A·D), W2_full_d.png, W2_set_d.png
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
STYLES = ('flat', 'a', 'b', 'c', 'd', 'da', 'row')
W4_STYLES = ('da', 'row')
W5_HINT_STATES = ('a_ready', 'e_slot2', 'b_on1', 'g_on3')   # W5: 설명 줄이 뜬 순간과 2초 뒤를 같이 찍는 상태 (W5_OFF에 적은 시안만)                    # W4 비교판의 가로 (da·새 배치)
W3_STYLES = ('d', 'a', 'da')                 # W3 비교판의 가로 (D·A·합친 것)
EXTRA_STATES = ('g_on3', 'w_pipe', 'w_pistol', 'w_gauntlet', 'w_chain')   # W3·W4: 강화 3단계 켬, 무기 넷을 각각 든 모습 (W1_EXTRA에 적은 시안만)
W2_STYLES = ('flat', 'a', 'd')               # W2 비교판의 가로 (flat·A·D)
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

    default_style = config.HUD_WEAPON_STYLE
    extra = os.environ.get('W1_EXTRA', '').split(',')
    w5_off = os.environ.get('W5_OFF', '').split(',')
    for style in os.environ.get('W1_ONLY', ','.join(STYLES)).split(','):   # W1_ONLY=flat,a,d 로 일부만
        config.HUD_WEAPON_STYLE = style
        for room, (seed, target) in ROOMS.items():
            for state in SLOT_STATES + (EXTRA_STATES if style in extra else ()):
                p = new_run(seed)
                if state.startswith('w_'):                # 무기 넷을 각각 들고, 다른 칸에는 사슬(사슬을 들 때는 철파이프)
                    p.set_loadout(state[2:], 'chain' if state != 'w_chain' else 'pipe')
                else:
                    p.set_loadout('pipe') if state == 'f_empty' else p.set_loadout('pipe', 'pistol')
                go(target)
                if state != 'e_slot2':
                    p.swap_weapon(0)                      # 1번 무기 (set_loadout은 둘째 칸을 든다)
                run(80)                                    # 교체 쿨다운이 다 차도록
                gauge(p, 22 if state == 'd_low' else (95 if state == 'g_on3' else 62))
                if state in ('b_on1', 'c_on2', 'g_on3'):
                    p.gauge.use_enhance()
                if state in ('c_on2', 'g_on3'):
                    p.gauge.use_enhance()
                if state == 'g_on3':
                    p.gauge.use_enhance()
                p.mouse_screen = (1180, 520)
                run(1)
                p.aura_time = 0.1
                grab(play_mode, f'{style}_{room}_{state}')
                if style in w5_off and (state in W5_HINT_STATES or state.startswith('w_')):
                    run(150)                                   # 설명 줄이 사라진 뒤 (WEAPON_HINT_TIME 2초 + 여유)
                    p.aura_time = 0.1
                    grab(play_mode, f'{style}_{room}_{state}_off')
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
    config.HUD_WEAPON_STYLE = default_style
    close_canvas()
    print('ok', out)


def _label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 7 * len(text) + 12, 16), fill=(0, 0, 0))
    d.text((5, 3), text, fill=(255, 255, 120))
    return im


def _compare(src, out, styles, prefix):
    made = []
    cw, ch = PANEL_BOX[2] - PANEL_BOX[0], PANEL_BOX[3] - PANEL_BOX[1]
    for room in ROOMS:
        im = Image.new('RGB', ((cw + 20) * len(styles) - 20, (ch + 10) * len(SLOT_STATES)), (20, 20, 24))
        for r, s in enumerate(SLOT_STATES):
            for c, style in enumerate(styles):
                crop = Image.open(os.path.join(src, f'w1_{style}_{room}_{s}.png')).crop(PANEL_BOX)
                im.paste(_label(crop, f'{style.upper()} {s}'), (c * (cw + 20), r * (ch + 10)))
        name = f'{prefix}_compare_{room}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    return made


def _full_and_set(src, out, style, prefix):
    full = _label(Image.open(os.path.join(src, f'w1_{style}_dark_a_ready.png')), f'{style.upper()} dark a_ready')
    full.save(os.path.join(out, f'{prefix}_full_{style}.png'))
    im = Image.new('RGB', (W * 2 + 20, H), (20, 20, 24))
    im.paste(_label(Image.open(os.path.join(src, f'w1_{style}_bright_a_ready.png')), f'{style.upper()} HUD'), (0, 0))
    im.paste(_label(Image.open(os.path.join(src, f'w1_{style}_cards.png')), f'{style.upper()} cards'), (W + 20, 0))
    im.save(os.path.join(out, f'{prefix}_set_{style}.png'))
    return [f'{prefix}_full_{style}.png', f'{prefix}_set_{style}.png']


def board5(src, before, out):
    """W5: 설명 줄이 뜬 순간 / 사라진 뒤(1번 듦·2번 듦·강화 1단계·궁극기, 두 방, 원래 크기), 무기 넷의 콤보 칸 W4 전·후, 평소 전체 화면."""
    os.makedirs(out, exist_ok=True)
    made = []
    cw, ch = PANEL_BOX[2] - PANEL_BOX[0], PANEL_BOX[3] - PANEL_BOX[1]
    rows = [(room, s) for room in ROOMS for s in W5_HINT_STATES]
    im = Image.new('RGB', ((cw + 20) * 2 - 20, (ch + 10) * len(rows)), (20, 20, 24))
    for r, (room, s) in enumerate(rows):
        for c, tail in enumerate(('', '_off')):
            path = os.path.join(src, f'w1_row_{room}_{s}{tail}.png')
            im.paste(_label(Image.open(path).crop(PANEL_BOX), f'{room} {s} {"shown" if not tail else "after 2s"}'), (c * (cw + 20), r * (ch + 10)))
    im.save(os.path.join(out, 'W5_hint.png'))
    made.append('W5_hint.png')
    weapons = EXTRA_STATES[1:]
    im = Image.new('RGB', ((cw + 20) * 2 - 20, (ch + 10) * len(weapons)), (20, 20, 24))
    for r, s in enumerate(weapons):
        for c, folder in enumerate((before, src)):
            tail = '' if c == 0 else '_off'
            path = os.path.join(folder, f'w1_row_dark_{s}{tail}.png')
            if not os.path.exists(path):
                path = os.path.join(folder, f'w1_row_dark_{s}.png')
            im.paste(_label(Image.open(path).crop(PANEL_BOX), f'{"W4" if c == 0 else "W5"} {s}'), (c * (cw + 20), r * (ch + 10)))
    im.save(os.path.join(out, 'W5_combo.png'))
    made.append('W5_combo.png')
    _label(Image.open(os.path.join(src, 'w1_row_dark_a_ready_off.png')), 'ROW W5 dark a_ready (no hint)').save(os.path.join(out, 'W5_full.png'))
    made.append('W5_full.png')
    print(len(made), '장:', ', '.join(made))


def board4(src, out):
    """W4: 가로 da·row x 세로 상태(평소·강화 1~3단계·게이지 모자람·2번 듦·빈 칸, 원래 크기), 무기 넷, 1번 듦/2번 듦(자리), 전체 화면 두 장, 네 귀퉁이 여백."""
    from PIL import ImageFont
    os.makedirs(out, exist_ok=True)
    made = []
    cw, ch = PANEL_BOX[2] - PANEL_BOX[0], PANEL_BOX[3] - PANEL_BOX[1]
    states = ('a_ready', 'b_on1', 'c_on2', 'g_on3', 'd_low', 'e_slot2', 'f_empty')
    for room in ROOMS:
        im = Image.new('RGB', ((cw + 20) * len(W4_STYLES) - 20, (ch + 10) * len(states)), (20, 20, 24))
        for r, s in enumerate(states):
            for c, style in enumerate(W4_STYLES):
                im.paste(_label(Image.open(os.path.join(src, f'w1_{style}_{room}_{s}.png')).crop(PANEL_BOX), f'{style.upper()} {s}'),
                         (c * (cw + 20), r * (ch + 10)))
        im.save(os.path.join(out, f'W4_compare_{room}.png'))
        made.append(f'W4_compare_{room}.png')
    weapons = EXTRA_STATES[1:]
    im = Image.new('RGB', ((cw + 20) * len(weapons) - 20, (ch + 10) * len(ROOMS)), (20, 20, 24))
    for r, room in enumerate(ROOMS):
        for c, s in enumerate(weapons):
            im.paste(_label(Image.open(os.path.join(src, f'w1_row_{room}_{s}.png')).crop(PANEL_BOX), f'ROW {room} {s}'), (c * (cw + 20), r * (ch + 10)))
    im.save(os.path.join(out, 'W4_weapons.png'))
    made.append('W4_weapons.png')
    # 1번 듦 / 2번 듦: 같은 자리에 세로로 (칸 왼쪽 끝·E 소켓이 그대로인지 세로선으로 짚는다)
    box = (1560, 900, 1920, 1080)
    bw, bh = box[2] - box[0], box[3] - box[1]
    im = Image.new('RGB', (bw * 2 + 20, bh * 2 + 10), (20, 20, 24))
    for c, room in enumerate(ROOMS):
        for r, s in enumerate(('a_ready', 'e_slot2')):
            im.paste(_label(Image.open(os.path.join(src, f'w1_row_{room}_{s}.png')).crop(box), f'ROW {room} {s}'), (c * (bw + 20), r * (bh + 10)))
    d = ImageDraw.Draw(im)
    for c in range(2):
        for x in (1604, 1800, 1888):                     # 줄 왼쪽 끝, 소켓 왼쪽·오른쪽 꼭짓점 (화면 x)
            px = c * (bw + 20) + x - box[0]
            d.line((px, 0, px, im.height), fill=(255, 236, 120), width=1)
    im.save(os.path.join(out, 'W4_swap.png'))
    made.append('W4_swap.png')
    im = Image.new('RGB', (W, H * 2 + 20), (20, 20, 24))
    im.paste(_label(Image.open(os.path.join(src, 'w1_row_dark_a_ready.png')), 'ROW dark a_ready'), (0, 0))
    im.paste(_label(Image.open(os.path.join(src, 'w1_row_dark_c_on2.png')), 'ROW dark c_on2'), (0, H + 20))
    im.save(os.path.join(out, 'W4_full.png'))
    made.append('W4_full.png')
    # 네 귀퉁이 여백: 화면 끝에서 HUD 가장자리까지 (왼쪽 위 체력 28·36, 오른쪽 위 미니맵 28·28, 오른쪽 아래 패널 28·40)
    im = Image.open(os.path.join(src, 'w1_row_bright_a_ready.png')).convert('RGB')
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(os.path.join(ROOT, 'assets', 'fonts', 'Galmuri11.ttf'), 22)
    Y = (255, 236, 120)
    marks = [  # (선 x0, y0, x1, y1, 글자, 글자 x, y)  PIL 좌표 (위가 0)
        (0, 36, 140, 36, '위 36 (체력 판)', 150, 24), (28, 0, 28, 120, '왼 28', 36, 120),
        (W - 28, 0, W - 28, 200, '오른 28 (미니맵)', W - 230, 200), (W - 200, 28, W, 28, '위 28', W - 270, 16),
        (W - 28, H - 320, W - 28, H, '오른 28 (무기·E 패널 그림 끝)', W - 380, H - 340), (1100, H - 40, W, H - 40, '아래 40 (키 배지·소켓 꼭짓점 포함)', 1110, H - 72),
    ]
    for x0, y0, x1, y1, t, tx, ty in marks:
        d.line((x0, y0, x1, y1), fill=Y, width=2)
        d.text((tx + 1, ty + 1), t, fill=(0, 0, 0), font=font)
        d.text((tx, ty), t, fill=Y, font=font)
    im.save(os.path.join(out, 'W4_corners.png'))
    made.append('W4_corners.png')
    print(len(made), '장:', ', '.join(made))


def board3(src, out):
    """W3: 가로 D·A·da x 세로 상태 여섯 + 강화 3단계(원래 크기), 무기 넷을 든 모습, 전체 화면 두 장(평소·강화 켬), HUD | 증강 카드."""
    os.makedirs(out, exist_ok=True)
    made = []
    cw, ch = PANEL_BOX[2] - PANEL_BOX[0], PANEL_BOX[3] - PANEL_BOX[1]
    states = SLOT_STATES + ('g_on3',)
    for room in ROOMS:
        im = Image.new('RGB', ((cw + 20) * len(W3_STYLES) - 20, (ch + 10) * len(states)), (20, 20, 24))
        for r, s in enumerate(states):
            for c, style in enumerate(W3_STYLES):
                path = os.path.join(src, f'w1_{style}_{room}_{s}.png')
                if os.path.exists(path):
                    im.paste(_label(Image.open(path).crop(PANEL_BOX), f'{style.upper()} {s}'), (c * (cw + 20), r * (ch + 10)))
        im.save(os.path.join(out, f'W3_compare_{room}.png'))
        made.append(f'W3_compare_{room}.png')
    weapons = EXTRA_STATES[1:]
    im = Image.new('RGB', ((cw + 20) * len(weapons) - 20, (ch + 10) * len(ROOMS)), (20, 20, 24))
    for r, room in enumerate(ROOMS):
        for c, s in enumerate(weapons):
            im.paste(_label(Image.open(os.path.join(src, f'w1_da_{room}_{s}.png')).crop(PANEL_BOX), f'DA {room} {s}'), (c * (cw + 20), r * (ch + 10)))
    im.save(os.path.join(out, 'W3_weapons.png'))
    made.append('W3_weapons.png')
    im = Image.new('RGB', (W, H * 2 + 20), (20, 20, 24))
    im.paste(_label(Image.open(os.path.join(src, 'w1_da_dark_a_ready.png')), 'DA dark a_ready'), (0, 0))
    im.paste(_label(Image.open(os.path.join(src, 'w1_da_dark_c_on2.png')), 'DA dark c_on2'), (0, H + 20))
    im.save(os.path.join(out, 'W3_full.png'))
    made.append('W3_full.png')
    im = Image.new('RGB', (W * 2 + 20, H), (20, 20, 24))
    im.paste(_label(Image.open(os.path.join(src, 'w1_da_bright_a_ready.png')), 'DA HUD'), (0, 0))
    im.paste(_label(Image.open(os.path.join(src, 'w1_da_cards.png')), 'DA cards'), (W + 20, 0))
    im.save(os.path.join(out, 'W3_set.png'))
    made.append('W3_set.png')
    print(len(made), '장:', ', '.join(made))


def board2(src, out):
    os.makedirs(out, exist_ok=True)
    made = _compare(src, out, W2_STYLES, 'W2') + _full_and_set(src, out, 'd', 'W2')
    print(len(made), '장:', ', '.join(made))


def board(src, out):
    os.makedirs(out, exist_ok=True)
    made = _compare(src, out, STYLES[:4], 'W1')
    for style in STYLES[1:4]:
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
    if sys.argv[1] == '--board5':
        board5(*sys.argv[2:5])
    elif sys.argv[1] == '--board4':
        board4(*sys.argv[2:4])
    elif sys.argv[1] == '--board3':
        board3(*sys.argv[2:4])
    elif sys.argv[1] == '--board2':
        board2(*sys.argv[2:4])
    elif sys.argv[1] == '--board':
        board(*sys.argv[2:4])
    else:
        shoot(sys.argv[1])
