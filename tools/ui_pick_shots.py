"""고르는 화면과 남은 화면 확인 촬영 (2026-11-27 S1, docs/opus/TASKS.md '4차'): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. 같은 시드·같은 프레임 수라 고치기 전·후가 같은 순간이다.

  python tools/ui_pick_shots.py <출력 폴더>          장면 찍기: pick_<장면>.png
  python tools/ui_pick_shots.py --board <전 폴더> <후 폴더> <비교판 폴더>
        S1_scene_<장면>.png(전·후 전체), S1_crop_<부분>.png(원래 크기로 자른 전·후), S1_set.png(증강 카드·형태 카드·NPC 창 한 벌)

장면: npc_mech_buy 정비사(살 수 있는 줄) / npc_mech_no 정비사(다 올린 줄, 결정 모자람 문구) / npc_keeper 보관인 / npc_archivist 기록관
      npc_armory_first 무기 걸이 첫 칸 / npc_armory_second 무기 걸이 둘째 칸 / practice 연습장 F 메뉴 / sfx 효과음 듣기
      boss_lines 보스 대사 띠(Enter 키 판) / ped_shop 정비방 진열대 앞 / ped_gold 황금방 진열대 앞
      options_music 설정(음량 줄, 일시정지 위) / options_top 설정(맨 위 줄, 타이틀 위)
      cards_augment·cards_form 증강·형태 카드 (한 벌 비교판용, 이번에 바꾸지 않는다)
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

SCENES = ('npc_mech_buy', 'npc_mech_no', 'npc_keeper', 'npc_archivist', 'npc_armory_first', 'npc_armory_second',
          'practice', 'sfx', 'boss_lines', 'ped_shop', 'ped_gold', 'options_music', 'options_top')
W, H = 1920, 1080
# 원래 크기로 자를 부분: (장면, (왼, 위, 오른, 아래) PIL 좌표: 위가 0)
CROPS = {
    'mech_rows': ('npc_mech_buy', (380, 150, 1540, 560)),        # 줄 이름·설명·값(결정)
    'mech_no': ('npc_mech_no', (380, 150, 1540, 620)),          # 다 올린 줄·살 수 없는 줄
    'mech_head': ('npc_mech_buy', (380, 40, 1540, 200)),        # 이름·역할·결정 수·한마디
    'keeper': ('npc_keeper', (380, 150, 1540, 520)),
    'armory': ('npc_armory_second', (380, 150, 1540, 980)),
    'archivist': ('npc_archivist', (380, 150, 1540, 760)),
    'practice': ('practice', (420, 120, 1500, 560)),
    'sfx': ('sfx', (420, 120, 1500, 560)),
    'boss_lines': ('boss_lines', (360, 940, 1920, 1080)),
    'ped_shop': ('ped_shop', None),                             # 진열대 둘레 (찍을 때 자리를 적어 둔다)
    'ped_gold': ('ped_gold', None),
    'options_rows': ('options_music', (220, 60, 1700, 560)),
    'footer': ('npc_mech_buy', (360, 980, 1560, 1080)),
}


def shoot(out):
    os.makedirs(out, exist_ok=True)
    import pico2d.pico2d as p2
    import sdl2
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

    import config
    import meta
    import options
    if os.environ.get('PICK_SKIN'):                   # 다른 스킨으로: PICK_SKIN=plate
        config.UI_SKIN = os.environ['PICK_SKIN']
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
    import forms
    import game_framework
    import game_world
    import mutation_mode
    import mutations as mu
    import npc_mode
    import options_mode
    import pause_mode
    import play_mode
    import practice_mode
    import sfx_mode
    import title_mode
    import title_storm
    import transition
    import zone_card
    for mod in (play_mode, pause_mode, options_mode, title_mode, npc_mode, practice_mode, sfx_mode, mutation_mode):
        mod.update_canvas = lambda: None              # 화면에 내보내기 전에 읽는다
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()
    spots = {}

    def grab(mod, name):
        transition._left = 0.0
        mod.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'pick_{name}.png'))
        p2.update_canvas()

    def new_run(seed):
        random.seed(seed)
        boss_intro.reset_all()
        effects.reset()
        game_framework.stack[:] = [play_mode]
        play_mode.enter()
        return play_mode.player

    def go(target, cell_kind=None):
        play_mode._test_jump(target)
        st = play_mode.stage
        if cell_kind:
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
            p.hp = max(p.hp, 1)
            game_framework.frame_time = 1 / 60
            play_mode.update()
        transition.reveal(0.0)
        transition.tick(5.0)

    def npc(kind, sel, crystals, prep=None, act_row=None):
        meta.reset()
        p = new_run(21)
        run(20)
        meta.state['crystals'] = crystals
        if prep:
            prep()
        npc_mode.kind, npc_mode.player = kind, p
        game_framework.stack[:] = [play_mode, npc_mode]
        npc_mode.enter()
        if act_row is not None:
            npc_mode.selected = act_row
            npc_mode.act(npc_mode.rows()[act_row][3])
        npc_mode.selected = sel

    # 정비사: 살 수 있는 줄 (결정 넉넉) / 다 올린 줄을 고름 + 다른 줄을 사려다 결정이 모자람
    npc('mechanic', 0, 40)
    grab(npc_mode, 'npc_mech_buy')

    def maxed():
        key = meta.ORDER[1]
        meta.state['levels'][key] = meta.UPGRADES[key]['max']
    npc('mechanic', 1, 3, maxed, act_row=0)
    grab(npc_mode, 'npc_mech_no')

    npc('keeper', 0, 20)
    grab(npc_mode, 'npc_keeper')
    npc('archivist', 1, 14)
    grab(npc_mode, 'npc_archivist')
    npc('armory', 0, 14)
    grab(npc_mode, 'npc_armory_first')
    npc('armory', 5, 14)
    grab(npc_mode, 'npc_armory_second')

    # 연습장 F 메뉴 (무기 받기 줄), 효과음 듣기
    p = new_run(22)
    play_mode._go_stage('practice')
    run(30)
    practice_mode.stage, practice_mode.player = play_mode.stage, p
    game_framework.stack[:] = [play_mode, practice_mode]
    practice_mode.enter()
    practice_mode.selected = 2
    grab(practice_mode, 'practice')
    game_framework.stack[:] = [play_mode, practice_mode, sfx_mode]
    sfx_mode.enter()
    old_path, sfx_mode.PATH = sfx_mode.PATH, os.path.join(tempfile.mkdtemp(), 'sfx_review.json')   # 사용자의 표시 파일을 건드리지 않는다
    sfx_mode.marks = {}
    names = sfx_mode.catalog()[0][1]
    sfx_mode.marks = {names[0]: 'good', names[2]: 'bad'} if len(names) > 2 else {}
    sfx_mode.row = 1
    grab(sfx_mode, 'sfx')
    sfx_mode.PATH = old_path

    # 보스 대사 띠: 구역 1 문지기 등장씬의 대사 단계 (한 줄을 다 친 뒤 = Enter 키 판이 밝다)
    config.BOSS_INTRO = True
    p = new_run(23)
    p.set_loadout('pipe', 'pistol')
    play_mode._test_jump('stage1')
    play_mode._test_jump('boss')
    intro = next(o for o in game_world.world[game_world.LAYER_UI] if isinstance(o, boss_intro.BossIntro))
    for _ in range(1200):
        run(1)
        if intro.step == 'lines' and intro.typed() >= len(intro.line()) and intro.line_t > 1.5:
            break
    grab(play_mode, 'boss_lines')
    config.BOSS_INTRO = False

    # 진열대 앞: 정비방(조각을 내고 사는 선반), 황금방(하나만 무료)
    for scene, kind, seed in (('ped_shop', 'shop', 24), ('ped_gold', 'gold', 25)):
        p = new_run(seed)
        p.set_loadout('pipe', 'pistol')
        p.shards = 80
        play_mode._test_jump('stage1')
        st = play_mode.stage
        st.cleared |= {c for c in st.layout if st.type_of(c) == 'combat'}     # 황금방이 열린 상태
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
        sx, sy = camera.to_screen(ped.x, ped.y)
        spots[scene] = (int(sx), int(sy))
        game_framework.stack[:] = [play_mode]
        grab(play_mode, scene)

    # 설정: 일시정지 위 음량 줄 / 타이틀 위 맨 위 줄
    p = new_run(26)
    go('stage1', 'combat')
    run(40)
    game_framework.stack[:] = [play_mode, pause_mode, options_mode]
    pause_mode.enter()
    options_mode.enter()
    options_mode.selected = 2
    grab(options_mode, 'options_music')
    game_framework.stack[:] = [title_mode]
    title_mode.enter()
    title_mode._storm[0] = title_storm.Storm(seed=1)
    for _ in range(120):
        title_mode.update()
    title_mode._storm[0] = title_storm.Storm(seed=1)
    game_framework.stack.append(options_mode)
    options_mode.enter()
    options_mode.selected = 0
    grab(options_mode, 'options_top')

    # 증강·형태 카드 (한 벌 비교판용)
    p = new_run(27)
    go('stage1', 'combat')
    run(40)
    game_framework.stack[:] = [play_mode, mutation_mode]
    for scene, ids in (('cards_augment', list(mu.MUTATIONS)[:3]), ('cards_form', [forms.CARD + w for w in list(forms.FORMS)[:2]] + [forms.CARD + 'skip'])):
        mutation_mode.setup(p, ids)
        mutation_mode.enter()
        mutation_mode.age = 5.0
        mutation_mode.selected = 1
        grab(mutation_mode, scene)
    with open(os.path.join(out, 'spots.txt'), 'w') as f:
        for k, (x, y) in spots.items():
            f.write(f'{k} {x} {y}\n')
    close_canvas()
    print('ok', out)


def _label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 * len(text) + 16, 22), fill=(0, 0, 0))
    d.text((6, 5), text, fill=(255, 255, 120))
    return im


def _spots(folder):
    out = {}
    path = os.path.join(folder, 'spots.txt')
    if os.path.exists(path):
        for line in open(path):
            k, x, y = line.split()
            out[k] = (int(x), int(y))
    return out


def board(before, after, out):
    os.makedirs(out, exist_ok=True)
    made = []
    for s in SCENES:
        a, b = os.path.join(before, f'pick_{s}.png'), os.path.join(after, f'pick_{s}.png')
        if not (os.path.exists(a) and os.path.exists(b)):
            continue
        im = Image.new('RGB', (W, H * 2 + 20), (20, 20, 24))
        im.paste(_label(Image.open(a), f'BEFORE {s}'), (0, 0))
        im.paste(_label(Image.open(b), f'AFTER {s}'), (0, H + 20))
        name = f'S1_scene_{s}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    spots = _spots(after)
    for part, (s, box) in CROPS.items():               # 원래 크기로 자른 전·후 (왼쪽 전, 오른쪽 후)
        if box is None:
            if s not in spots:
                continue
            x, y = spots[s]
            py = H - 1 - y
            box = (max(0, x - 420), max(0, py - 300), min(W, x + 420), min(H, py + 60))
        cw, ch = box[2] - box[0], box[3] - box[1]
        im = Image.new('RGB', (cw * 2 + 30, ch), (20, 20, 24))
        ok = True
        for c, folder in enumerate((before, after)):
            path = os.path.join(folder, f'pick_{s}.png')
            if not os.path.exists(path):
                ok = False
                break
            src = Image.open(path).crop(box)
            im.paste(_label(src, f'{"BEFORE" if c == 0 else "AFTER"} {part}'), (c * (cw + 30), 0))
        if not ok:
            continue
        name = f'S1_crop_{part}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    # 한 벌: 증강 카드·형태 카드·NPC 창 (정비사)·연습 메뉴 (반 크기 넷) + 아래에 원래 크기로 카드 하나와 NPC 줄 하나
    names = ['cards_augment', 'cards_form', 'npc_mech_buy', 'npc_armory_second']
    hw, hh = W // 2, H // 2
    im = Image.new('RGB', (hw * 2 + 20, hh * 2 + 20 + 560), (20, 20, 24))
    for i, f in enumerate(names):
        src = Image.open(os.path.join(after, f'pick_{f}.png'))
        im.paste(_label(src.resize((hw, hh), Image.NEAREST), f), (i % 2 * (hw + 20), i // 2 * (hh + 20)))
    card = Image.open(os.path.join(after, 'pick_cards_augment.png')).crop((740, 180, 1180, 760))     # 원래 크기: 고른(가운데) 카드
    rows = Image.open(os.path.join(after, 'pick_npc_mech_buy.png')).crop((400, 160, 1520, 720))
    im.paste(card, (0, hh * 2 + 20))
    im.paste(rows, (card.width + 20, hh * 2 + 20))
    im.save(os.path.join(out, 'S1_set.png'))
    made.append('S1_set.png')
    print(len(made), '장:', ', '.join(made))


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:5])
    else:
        shoot(sys.argv[1])
