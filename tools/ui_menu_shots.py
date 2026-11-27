"""메뉴 화면 확인 촬영 (2026-11-27 M1 메뉴 화면, docs/opus/TASKS.md '4차'): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. 같은 시드·같은 프레임 수라 고치기 전·후가 같은 순간이다.

  python tools/ui_menu_shots.py <출력 폴더>                    장면 열하나 찍기: menu_<장면>.png (+ 타이틀 title_0.png)
      MENU_SKIN=plate 를 주면 그 스킨으로 찍는다 (M1 전 mist 메뉴 화면은 plate와 그리기 호출까지 같았다: tests/test_ui_skin.py)
  python tools/ui_menu_shots.py --board <전 폴더> <후 폴더> <비교판 폴더>
        M1_scene_<장면>.png(전·후 전체), M1_crop_<부분>.png(원래 크기로 자른 전·후), M1_set.png(타이틀·일시정지·설정·결과 한 벌)

장면: pause_dark 어두운 방 위 일시정지(계속하기) / pause_bright 밝은 벽 방 위 일시정지(판 포기하고 은신처로, 이번 판 카드 채움)
      options_top 설정 맨 위 줄 / options_music 음량 막대 줄 / options_bottom 맨 아래 줄(돌아가기) / keys 키 설정
      ending_dead 사망 결과(맡길 물건 고르기) / ending_clear 탈출 결과 / credits_0 크레딧 처음 / credits_mid 크레딧 중간
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

SCENES = ('pause_dark', 'pause_bright', 'options_top', 'options_music', 'options_bottom', 'keys',
          'ending_dead', 'ending_clear', 'credits_0', 'credits_mid')
W, H = 1920, 1080
# 원래 크기로 자를 부분: (장면, (왼, 위, 오른, 아래) PIL 좌표: 위가 0, 이름)
CROPS = {
    'pause_menu': ('pause_bright', (100, 120, 760, 620)),           # 밝은 벽 위 메뉴 줄
    'pause_controls': ('pause_bright', (640, 180, 1360, 760)),      # 조작 안내 (작은 글자 + 키)
    'pause_build': ('pause_bright', (1360, 180, 1820, 760)),        # 이번 판 (작은 회색 글자)
    'pause_header': ('pause_dark', (0, 0, 760, 200)),               # 머리글·제목
    'options_rows': ('options_music', (220, 140, 1700, 520)),       # 값 칸·음량 막대
    'options_desc': ('options_top', (220, 60, 1000, 360)),          # 작은 회색 설명
    'keys_rows': ('keys', (340, 80, 1580, 560)),
    'ending_dead': ('ending_dead', (520, 160, 1400, 760)),
    'ending_clear': ('ending_clear', (520, 160, 1400, 760)),
    'credits_mid': ('credits_mid', (360, 300, 1560, 780)),
    'footer': ('options_top', (360, 980, 1560, 1080)),
}


def shoot(out):
    os.makedirs(out, exist_ok=True)
    import pico2d.pico2d as p2
    import sdl2
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

    import config
    import meta
    import options
    if os.environ.get('MENU_SKIN'):                   # 고치기 전과 비교: MENU_SKIN=plate
        config.UI_SKIN = os.environ['MENU_SKIN']
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')
    meta.reset()
    options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window(2)
    import boss_intro
    import camera
    import credits_mode
    import effects
    import ending_mode
    import game_framework
    import game_world
    import items
    import keys_mode
    import mutations as mu
    import options_mode
    import pause_mode
    import play_mode
    import title_mode
    import title_storm
    import transition
    import zone_card
    for mod in (play_mode, pause_mode, options_mode, keys_mode, ending_mode, credits_mode, title_mode):
        mod.update_canvas = lambda: None              # 화면에 내보내기 전에 읽는다
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(mod, name):
        transition._left = 0.0
        mod.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'{name}.png'))
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

    def title_under():
        game_framework.stack[:] = [title_mode]
        title_mode.enter()
        title_mode._storm[0] = title_storm.Storm(seed=1)            # 평소 (번개 없음)
        for _ in range(120):
            title_mode.update()
        title_mode._storm[0] = title_storm.Storm(seed=1)

    # 타이틀 (한 벌 비교판용)
    title_under()
    grab(title_mode, 'title_0')

    # 일시정지: 어두운 방 (구역 1 첫 전투방), 계속하기
    p = new_run(11)
    p.set_loadout('pipe', 'pistol')
    go('stage1', 'combat')
    run(50)
    game_framework.stack[:] = [play_mode, pause_mode]
    pause_mode.enter()
    grab(pause_mode, 'menu_pause_dark')

    # 일시정지: 밝은 벽 방 (구역 3 탑), 판 포기하고 은신처로, 이번 판 카드 채움
    p = new_run(12)
    p.set_loadout('gauntlet', 'chain')
    for it in ('cap', 'absorb', 'steady', 'power', 'power'):
        items.apply(p, it)
    for m in ('tide_cost', 'bloom_crit'):
        mu.give(p, m)
    go('stage3', 'combat')
    run(50)
    game_framework.stack[:] = [play_mode, pause_mode]
    pause_mode.enter()
    pause_mode.selected = 2
    grab(pause_mode, 'menu_pause_bright')

    # 설정: 타이틀 위 (맨 위 줄), 일시정지 위 (음량 막대), 타이틀 위 (맨 아래 줄)
    title_under()
    game_framework.stack.append(options_mode)
    options_mode.enter()
    grab(options_mode, 'menu_options_top')
    game_framework.stack[:] = [play_mode, pause_mode, options_mode]
    options_mode.enter()
    options_mode.selected = 2
    grab(options_mode, 'menu_options_music')
    title_under()
    game_framework.stack.append(options_mode)
    options_mode.enter()
    options_mode.selected = len(options_mode.ROWS)
    grab(options_mode, 'menu_options_bottom')

    # 키 설정 (타이틀 > 설정 > 키 설정), 점프 줄의 보조 칸
    game_framework.stack.append(keys_mode)
    options_mode.selected = options_mode.ITEMS.index('keys')
    keys_mode.enter()
    keys_mode.row, keys_mode.col = 2, 1
    grab(keys_mode, 'menu_keys')

    # 사망 결과: 보관 칸이 열려 있어 맡길 물건을 고른다
    p = new_run(13)
    p.set_loadout('pipe', 'pistol')
    for it in ('absorb', 'power'):
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
    grab(ending_mode, 'menu_ending_dead')

    # 탈출 결과
    p = new_run(14)
    go('stage3', 'combat')
    run(40)
    p.run_rooms, p.run_kills, p.run_ends, p.run_clock = 23, 118, 3, 1932.0
    meta.state['keeper'] = False
    ending_mode.result = 'clear'
    game_framework.stack[:] = [ending_mode]
    ending_mode.enter()
    grab(ending_mode, 'menu_ending_clear')

    # 크레딧: 처음(제목이 화면 가운데쯤), 중간
    game_framework.stack[:] = [credits_mode]
    credits_mode.enter()
    for name, sc in (('credits_0', 560.0), ('credits_mid', 1500.0)):
        credits_mode.scroll = sc
        credits_mode._scene = credits_mode.scene_for(sc)
        grab(credits_mode, f'menu_{name}')
    close_canvas()
    print('ok', out)


def _label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 * len(text) + 16, 22), fill=(0, 0, 0))
    d.text((6, 5), text, fill=(255, 255, 120))
    return im


def board(before, after, out):
    os.makedirs(out, exist_ok=True)
    made = []
    for s in SCENES:
        a, b = os.path.join(before, f'menu_{s}.png'), os.path.join(after, f'menu_{s}.png')
        if not (os.path.exists(a) and os.path.exists(b)):
            continue
        im = Image.new('RGB', (W, H * 2 + 20), (20, 20, 24))
        im.paste(_label(Image.open(a), f'BEFORE {s}'), (0, 0))
        im.paste(_label(Image.open(b), f'AFTER {s}'), (0, H + 20))
        name = f'M1_scene_{s}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    for part, (s, box) in CROPS.items():               # 원래 크기로 자른 전·후 (왼쪽 전, 오른쪽 후)
        cw, ch = box[2] - box[0], box[3] - box[1]
        im = Image.new('RGB', (cw * 2 + 30, ch), (20, 20, 24))
        for c, folder in enumerate((before, after)):
            src = Image.open(os.path.join(folder, f'menu_{s}.png')).crop(box)
            im.paste(_label(src, f'{"BEFORE" if c == 0 else "AFTER"} {part}'), (c * (cw + 30), 0))
        name = f'M1_crop_{part}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    # 한 벌: 타이틀·일시정지·설정·결과 (반 크기 넷 + 아래에 원래 크기로 자른 왼쪽 위 머리글 넷)
    names = [('title_0', 'title_0'), ('pause', 'menu_pause_dark'), ('options', 'menu_options_top'), ('ending', 'menu_ending_dead')]
    hw, hh = W // 2, H // 2
    im = Image.new('RGB', (hw * 2 + 20, hh * 2 + 20 + 240), (20, 20, 24))
    for i, (_n, f) in enumerate(names):
        src = Image.open(os.path.join(after, f + '.png'))
        im.paste(src.resize((hw, hh), Image.NEAREST), (i % 2 * (hw + 20), i // 2 * (hh + 20)))
    for i, (_n, f) in enumerate(names):
        src = Image.open(os.path.join(after, f + '.png')).crop((0, 0, 480, 240))      # 원래 크기: 왼쪽 위 꺾쇠·머리글
        im.paste(src, (i * 485, hh * 2 + 20))
    im.save(os.path.join(out, 'M1_set.png'))
    made.append('M1_set.png')
    print(len(made), '장:', ', '.join(made))


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:5])
    else:
        shoot(sys.argv[1])
