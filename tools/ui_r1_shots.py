"""R1 나머지 손질 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' R1): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. 같은 시드·같은 프레임 수라 고치기 전·후가 같은 순간이다.

  python tools/ui_r1_shots.py <출력 폴더>          이 스크립트만의 장면: r1_<장면>.png
        hub_mech 은신처 정비사 앞(머리 위 안내) / hub_armory 무기 걸이 앞 / credits_ai 크레딧 'AI 도구' 절
  python tools/ui_r1_shots.py --board <전 폴더> <후 폴더> <비교판 폴더>
        <전·후 폴더>는 각각 storm/(title_storm_shots), hud2/(ui_hud2_shots), menu/(ui_menu_shots), pick/(ui_pick_shots),
        r1/(이 스크립트)를 담는다. 비교판 R1_*.png (원래 크기로 자른 전·후, 줄이지 않는다)
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
    import credits_mode
    import effects
    import game_framework
    import game_world
    import npc as npc_mod
    import play_mode
    import transition
    import zone_card
    for mod in (play_mode, credits_mode):
        mod.update_canvas = lambda: None
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(mod, name):
        transition._left = 0.0
        mod.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'r1_{name}.png'))
        p2.update_canvas()

    def run(n):
        p = play_mode.player
        for _ in range(n):
            zone_card.freezing = False
            for o in list(game_world.world[game_world.LAYER_UI]):
                if isinstance(o, zone_card.ZoneCard):
                    game_world.remove_object(o)
            p.hp = max(p.hp, 1)
            game_framework.frame_time = 1 / 60
            play_mode.update()
        transition.reveal(0.0)
        transition.tick(5.0)

    spots = []
    for kind in ('mechanic', 'armory'):
        meta.reset()
        random.seed(21)
        boss_intro.reset_all()
        effects.reset()
        game_framework.stack[:] = [play_mode]
        play_mode.enter()
        run(20)
        p = play_mode.player
        n = next(o for layer in game_world.world for o in layer if isinstance(o, npc_mod.NPC) and o.kind == kind)
        p.x, p.y = n.x + 70, n.y
        run(30)
        spots.append(f'{kind} {int(n.x)} {int(n.y)}')
        grab(play_mode, 'hub_' + kind[:4] if kind == 'mechanic' else 'hub_armory')
    # 크레딧 'AI 도구' 절이 화면 가운데쯤 오게
    credits_mode.enter()
    off = 0
    for kind, text in credits_mode.CREDITS:
        if text == 'AI 도구':
            break
        off += credits_mode.STYLE[kind][0]
    credits_mode.scroll = 760 + 40 + off
    credits_mode._scene = credits_mode.scene_for(credits_mode.scroll)
    grab(credits_mode, 'credits_ai')
    with open(os.path.join(out, 'r1_spots.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(spots))
    close_canvas()
    print('ok', out)


# ----- 비교판 -----
BG = (20, 20, 24)
try:
    FONT = ImageFont.truetype('malgun.ttf', 22)
except OSError:
    FONT = ImageFont.load_default()


def stack(rows, path, pad=10, label_h=34):
    """[(이름표, 그림)]을 세로로 쌓는다 (원래 크기)."""
    w = max(im.width for _l, im in rows)
    board = Image.new('RGB', (w + 2 * pad, sum(im.height + label_h + pad for _l, im in rows) + pad), BG)
    d = ImageDraw.Draw(board)
    y = pad
    for label, im in rows:
        d.text((pad, y + 4), label, fill=(230, 230, 230), font=FONT)
        board.paste(im, (pad, y + label_h))
        y += im.height + label_h + pad
    board.save(path)
    return path


def side(pairs, path, pad=10, label_h=34):
    """[(이름표, 전, 후)]를 줄마다 전 | 후로 나란히 (원래 크기)."""
    w = max(a.width + b.width for _l, a, b in pairs) + 3 * pad
    h = sum(max(a.height, b.height) + label_h + pad for _l, a, b in pairs) + pad
    board = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(board)
    y = pad
    for label, a, b in pairs:
        d.text((pad, y + 4), label + '   (왼쪽: 고치기 전 / 오른쪽: 고친 뒤)', fill=(230, 230, 230), font=FONT)
        board.paste(a, (pad, y + label_h))
        board.paste(b, (2 * pad + a.width, y + label_h))
        y += max(a.height, b.height) + label_h + pad
    board.save(path)
    return path


def board(before, after, dest):
    os.makedirs(dest, exist_ok=True)

    def two(sub, name, box=None):
        a = Image.open(os.path.join(before, sub, name + '.png')).convert('RGB')
        b = Image.open(os.path.join(after, sub, name + '.png')).convert('RGB')
        return (a.crop(box), b.crop(box)) if box else (a, b)

    made = []
    # 묶음 1: 번개
    TOP = (0, 0, W, 620)
    rows = []
    for n in (1, 2, 3):
        a, b = two('storm', f'bolt_{n}', TOP)
        rows += [(f'판 {n} 줄기 단계: 고치기 전', a), (f'판 {n} 줄기 단계: 고친 뒤', b)]
    made.append(stack(rows, os.path.join(dest, 'R1_storm_bolts.png')))
    rows = []
    for n in (1, 2, 3):
        a, b = two('storm', f'flash_{n}', TOP)
        rows += [(f'판 {n} 대비 판: 고치기 전', a), (f'판 {n} 대비 판: 고친 뒤', b)]
    made.append(stack(rows, os.path.join(dest, 'R1_storm_flash.png')))
    LOGO, HEAD = (560, 300, 1360, 560), (0, 0, 800, 140)
    made.append(side([('대비 판 로고 둘레 (원래 크기)',) + two('storm', 'flash_1', LOGO),
                      ('대비 판 머리글 (원래 크기)',) + two('storm', 'flash_1', HEAD),
                      ('평소 화면 머리글 (그대로여야 한다)',) + two('storm', 'normal', HEAD),
                      ('평소 화면 로고 둘레 (그대로여야 한다)',) + two('storm', 'normal', LOGO)],
                     os.path.join(dest, 'R1_storm_logo_head.png')))
    # 묶음 2: NPC 머리 위 안내, 무기 걸이 제목
    sp = {}
    for line in open(os.path.join(after, 'r1', 'r1_spots.txt'), encoding='utf-8'):
        k, x, y = line.split()
        sp[k] = (int(x), int(y))

    def around(k):
        x, y = sp[k]
        return (x - 330, H - y - 320, x + 330, H - y + 40)
    made.append(side([('은신처 정비사 앞 머리 위 안내',) + two('r1', 'r1_hub_mech', around('mechanic')),
                      ('은신처 무기 걸이 앞 머리 위 안내',) + two('r1', 'r1_hub_armory', around('armory')),
                      ('무기 걸이 창 제목 (원래 크기)',) + two('pick', 'pick_npc_armory_first', (380, 200, 1540, 330))],
                     os.path.join(dest, 'R1_npc_text.png')))
    # 묶음 3: 증강 카드 진행 칸
    a, b = two('pick', 'pick_cards_augment')
    made.append(side([('증강 카드 셋 (원래 크기, 아래쪽 진행 칸)', a.crop((340, 560, 1580, 800)), b.crop((340, 560, 1580, 800)))],
                     os.path.join(dest, 'R1_step_cells.png')))
    a2 = a.crop((900, 664, 1020, 704)).resize((480, 160), Image.NEAREST)
    b2 = b.crop((900, 664, 1020, 704)).resize((480, 160), Image.NEAREST)
    made.append(side([('가운데 카드 진행 칸 (4배 확대해 본 것, 게임은 1배)', a2, b2)], os.path.join(dest, 'R1_step_cells_zoom.png')))
    # 묶음 4: 크레딧
    made.append(side([('크레딧 AI 도구 절',) + two('r1', 'r1_credits_ai', (160, 120, 1760, 1000))],
                     os.path.join(dest, 'R1_credits.png')))
    # 묶음 5: HUD
    SLOTS, GAUGE = (1500, 880, 1920, 1080), (520, 0, 1400, 140)
    made.append(side([('어두운 방, 강화 못 씀 (E 칸)',) + two('hud2', 'h2_dark_d_low', SLOTS),
                      ('밝은 벽 방, 강화 못 씀 (E 칸)',) + two('hud2', 'h2_bright_d_low', SLOTS),
                      ('어두운 방, 강화 쓸 수 있음 (그대로)',) + two('hud2', 'h2_dark_a_ready', SLOTS)],
                     os.path.join(dest, 'R1_hud_e_slot.png')))
    made.append(side([('위험 맥박 켜짐 (게이지, 원래 크기)',) + two('hud2', 'h2_crit_on', GAUGE),
                      ('페이드 맥박 켜짐',) + two('hud2', 'h2_fade_on', GAUGE),
                      ('위험 맥박 꺼짐 (그대로)',) + two('hud2', 'h2_crit_off', GAUGE)],
                     os.path.join(dest, 'R1_hud_gauge.png')))
    # 묶음 6: 뒤로 비치는 것, 결과 화면, 효과음 듣기
    for name, sub, scene in (('pause', 'menu', 'menu_pause_bright'), ('npc', 'pick', 'pick_npc_mech_buy'),
                             ('practice', 'pick', 'pick_practice'), ('ending_dead', 'menu', 'menu_ending_dead'),
                             ('ending_clear', 'menu', 'menu_ending_clear')):
        a, b = two(sub, scene)
        made.append(stack([(f'{scene}: 고치기 전', a), (f'{scene}: 고친 뒤', b)], os.path.join(dest, f'R1_{name}.png')))
    made.append(side([('사망 결과 맡길 물건 둘레 (원래 크기)',) + two('menu', 'menu_ending_dead', (420, 600, 1500, 900)),
                      ('NPC 창 돌아가기 둘레',) + two('pick', 'pick_npc_mech_buy', (500, 700, 1420, 920)),
                      ('일시정지 제목·메뉴 둘레',) + two('menu', 'menu_pause_bright', (0, 100, 700, 640)),
                      ('연습 메뉴 위쪽',) + two('pick', 'pick_practice', (420, 100, 1500, 420))],
                     os.path.join(dest, 'R1_backdrop_crops.png')))
    a, b = two('pick', 'pick_sfx', (420, 310, 760, 390))
    made.append(side([('효과음 듣기 고른 줄 (3배 확대해 본 것, 게임은 1배)', a.resize((a.width * 3, a.height * 3), Image.NEAREST),
                       b.resize((b.width * 3, b.height * 3), Image.NEAREST))], os.path.join(dest, 'R1_sfx_row.png')))
    for m in made:
        print(m)


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:5])
    else:
        shoot(sys.argv[1])
