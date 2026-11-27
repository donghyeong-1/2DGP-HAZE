"""R2 나머지 손질 2 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' R2): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. 같은 시드·같은 프레임 수라 고치기 전·후가 같은 순간이다.

  python tools/ui_r2_shots.py <출력 폴더>        E 결정 소켓 장면: r2_<방>_<상태>.png
        상태: low 게이지 모자람(빈 윤곽) / ready 쓸 수 있음(청록) / on2 강화 2단계 켬(단계 색) / half 2단계 켬, 남은 시간 45%(줄어든 결정)
  python tools/ui_r2_shots.py --board <전 폴더> <후 폴더> <비교판 폴더>
        <전·후 폴더>는 각각 r2/(이 스크립트), w1/(ui_w1_shots rowmix), storm/(title_storm_shots), r1/(ui_r1_shots)를 담는다.
        R2_socket.png(소켓 원래 크기와 4배, 상태 넷), R2_panel.png(패널 전체, 어두운 방·밝은 벽 방), R2_storm.png(판 셋 줄기 단계·번쩍이는 순간, 머리글 둘레),
        R2_nameplates.png(은신처 이름표), R2_credits.png(크레딧 AI 도구·그래픽 절, 전체 폭)
"""
import ctypes
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1920, 1080
ROOMS = {'dark': (11, 'stage1'), 'bright': (12, 'stage3')}
STATES = ('low', 'ready', 'on2', 'half')
SOCKET_BOX = (1790, 900, 1920, 1062)            # 소켓 둘레 (PIL 좌표: 위가 0)
PANEL_BOX = (1500, 790, 1920, 1080)


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
    import play_mode
    import transition
    import zone_card
    play_mode.update_canvas = lambda: None
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(name):
        play_mode.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'r2_{name}.png'))
        p2.update_canvas()

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

    for room, (seed, target) in ROOMS.items():
        for state in STATES:
            random.seed(seed)
            boss_intro.reset_all()
            effects.reset()
            game_framework.stack[:] = [play_mode]
            play_mode.enter()
            p = play_mode.player
            p.set_loadout('pipe', 'pistol')
            play_mode._test_jump(target)
            st = play_mode.stage
            coord = next(c for c in st.layout if st.type_of(c) == 'combat')
            st.enter_room(coord, 'L')
            play_mode.room = st.room
            camera.snap(p, st.room)
            p.swap_weapon(0)
            run(150)                                   # 교체 쿨다운·설명 줄이 다 지나도록
            v = 22 if state == 'low' else 62
            p.gauge.value = v
            p.gauge.zone = p.gauge._zone_of(v)
            if state in ('on2', 'half'):
                p.gauge.use_enhance()
                p.gauge.use_enhance()
            p.mouse_screen = (1180, 520)
            run(1)
            if state == 'half':
                p.gauge.enhance_timer = config.ENHANCE_TIME * 0.45
            p.aura_time = 0.1
            grab(f'{room}_{state}')
    import credits_mode                                # 크레딧 '그래픽' 절이 화면 가운데쯤 (r1의 credits_ai는 'AI 도구' 절)
    credits_mode.update_canvas = lambda: None
    credits_mode.enter()
    off = 0
    for kind, text in credits_mode.CREDITS:
        if text == '그래픽':
            break
        off += credits_mode.STYLE[kind][0]
    credits_mode.scroll = 600 + 40 + off
    credits_mode._scene = credits_mode.scene_for(credits_mode.scroll)
    import transition as tr
    tr._left = 0.0
    credits_mode.draw()
    sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
    Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, 'r2_credits_gfx.png'))
    p2.update_canvas()
    close_canvas()
    print('ok', out)


# ----- 비교판 (원래 크기로 자른다. 4배는 따로 적는다) -----
BG = (20, 20, 24)
try:
    FONT = ImageFont.truetype('malgun.ttf', 20)
except OSError:
    FONT = ImageFont.load_default()


def grid(cells, cols, path, pad=10, label_h=30):
    """[(이름표, 그림)]을 cols 열 격자로."""
    cw = max(im.width for _l, im in cells)
    ch = max(im.height for _l, im in cells)
    rows = (len(cells) + cols - 1) // cols
    board = Image.new('RGB', (cols * (cw + pad) + pad, rows * (ch + label_h + pad) + pad), BG)
    d = ImageDraw.Draw(board)
    for k, (label, im) in enumerate(cells):
        x, y = pad + (k % cols) * (cw + pad), pad + (k // cols) * (ch + label_h + pad)
        d.text((x, y + 4), label, fill=(230, 230, 230), font=FONT)
        board.paste(im, (x, y + label_h))
    board.save(path)
    return path


def board(before, after, dest):
    os.makedirs(dest, exist_ok=True)

    def img(folder, sub, name):
        return Image.open(os.path.join(folder, sub, name + '.png')).convert('RGB')

    made = []
    # 소켓: 원래 크기 + 4배, 상태 넷, 어두운 방
    cells = []
    for room in ROOMS:
        for state in STATES:
            for tag, folder in (('전', before), ('후', after)):
                im = img(folder, 'r2', f'r2_{room}_{state}').crop(SOCKET_BOX)
                cells.append((f'{tag} {room} {state} (1배)', im))
    made.append(grid(cells, 8, os.path.join(dest, 'R2_socket_1x.png')))
    cells = []
    for state in STATES:
        for tag, folder in (('전', before), ('후', after)):
            im = img(folder, 'r2', f'r2_dark_{state}').crop(SOCKET_BOX)
            cells.append((f'{tag} {state} (4배로 본 것)', im.resize((im.width * 4, im.height * 4), Image.NEAREST)))
    made.append(grid(cells, 4, os.path.join(dest, 'R2_socket.png')))
    # 패널 전체
    cells = []
    for room in ('dark', 'bright'):
        for s in ('a_ready_off', 'c_on2_off', 'd_low_off', 'e_slot2_off'):
            for tag, folder in (('전', before), ('후', after)):
                cells.append((f'{tag} {room} {s}', img(folder, 'w1', f'w1_rowmix_{room}_{s}').crop(PANEL_BOX)))
    made.append(grid(cells, 4, os.path.join(dest, 'R2_panel.png')))
    # 번개
    TOP = (0, 0, W, 620)
    cells = []
    for n in (1, 2, 3):
        for tag, folder in (('전', before), ('후', after)):
            cells.append((f'{tag} 판 {n} 줄기 단계', img(folder, 'storm', f'bolt_{n}').crop(TOP)))
    for tag, folder in (('전', before), ('후', after)):
        cells.append((f'{tag} 판 3 번쩍이는 순간', img(folder, 'storm', 'flash_3').crop(TOP)))
    made.append(grid(cells, 2, os.path.join(dest, 'R2_storm.png')))
    HEAD = (0, 0, 800, 220)
    cells = []
    for n in (1, 2, 3):
        for tag, folder in (('전', before), ('후', after)):
            cells.append((f'{tag} 판 {n} 줄기 단계: 머리글 둘레 (원래 크기)', img(folder, 'storm', f'bolt_{n}').crop(HEAD)))
    made.append(grid(cells, 2, os.path.join(dest, 'R2_storm_head.png')))
    # 이름표
    sp = {}
    for line in open(os.path.join(after, 'r1', 'r1_spots.txt'), encoding='utf-8'):
        k, x, y = line.split()
        sp[k] = (int(x), int(y))
    cells = []
    for scene, k in (('r1_hub_mech', 'mechanic'), ('r1_hub_armory', 'armory')):
        x, y = sp[k]
        box = (x - 420, H - y - 320, x + 420, H - y + 40)
        for tag, folder in (('전', before), ('후', after)):
            cells.append((f'{tag} {scene}', img(folder, 'r1', scene).crop(box)))
    made.append(grid(cells, 2, os.path.join(dest, 'R2_nameplates.png')))
    # 크레딧 (전체 폭)
    cells = [(f'{tag} 크레딧 AI 도구 절', img(folder, 'r1', 'r1_credits_ai').crop((0, 100, W, 1040))) for tag, folder in (('전', before), ('후', after))]
    cells += [(f'{tag} 크레딧 그래픽 절', img(folder, 'r2', 'r2_credits_gfx').crop((0, 300, W, 800))) for tag, folder in (('전', before), ('후', after))]
    made.append(grid(cells, 1, os.path.join(dest, 'R2_credits.png')))
    for m in made:
        print(m)


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:5])
    else:
        shoot(sys.argv[1])
