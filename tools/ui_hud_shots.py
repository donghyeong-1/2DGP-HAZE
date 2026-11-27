"""플레이 중 HUD 확인 촬영 (2026-11-27 H1 HUD, docs/opus/TASKS.md '4차'): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. 같은 시드·같은 프레임 수라 고치기 전·후가 같은 순간이다.

  python tools/ui_hud_shots.py <출력 폴더>                     장면 여덟 개(+ 덤) 찍기: hud_<장면>.png
      HUD_SKIN=plate 를 주면 그 스킨으로 찍는다 (H1 전 mist HUD는 plate와 그리기 호출까지 같았다: tests/test_ui_skin.py)
  python tools/ui_hud_shots.py --board <전 폴더> <후 폴더> <비교판 폴더> [타이틀·카드 폴더]
        H1_scene_<장면>.png(전·후 전체), H1_crop_<부분>.png(원래 크기로 자른 전·후), H1_set.png(타이틀·증강 카드·HUD 한 벌)

장면: a_dark 어두운 방 전투(노멀) / b_bright 밝은 벽이 HUD 뒤 / c_boss 보스전(이름·체력바·페이즈 눈금, 깎인 자국)
      d_critical 위험 구간 + E 강화 준비 / e_fade 페이드 / f_curse 저주(게이지 아래) / g_items 아이템·증강 여럿 + 무기 교체 직후 + 아이템 띠
      h_shop 상점 진열대 앞 상호작용 안내 + 문 위 보상 판 / i_enhanced 강화 2단계 중 + 방 클리어 알림
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

SCENES = ('a_dark', 'b_bright', 'c_boss', 'd_critical', 'e_fade', 'f_curse', 'g_items', 'h_shop', 'i_enhanced')
W, H = 1920, 1080
# 원래 크기로 자를 부분 (PIL 좌표: 위가 0)
CROPS = {'top_left': (0, 0, 620, 300), 'top_center': (540, 0, 1380, 170), 'top_right': (1480, 0, 1920, 420),
         'boss_bar': (440, 120, 1480, 230), 'bottom_right': (1340, 820, 1920, 1080), 'bottom_center': (560, 880, 1360, 1080)}


def shoot(out):
    os.makedirs(out, exist_ok=True)
    import pico2d.pico2d as p2
    import sdl2
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

    import config
    import meta
    import options
    if os.environ.get('HUD_SKIN'):                    # 고치기 전과 비교: HUD_SKIN=plate (H1 전 mist HUD는 plate와 같았다)
        config.UI_SKIN = os.environ['HUD_SKIN']
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')
    meta.reset()
    options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window(2)
    import boss_intro
    import camera
    import curse
    import effects
    import game_framework
    import game_world
    import items
    import mutations as mu
    import play_mode
    import stage as stage_mod
    import transition
    import zone_card
    play_mode.update_canvas = lambda: None            # 화면에 내보내기 전에 읽는다
    config.BOSS_INTRO = False                         # 등장씬 없이 바로 싸우는 장면 (HUD가 숨지 않게)
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(name):
        play_mode.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'hud_{name}.png'))
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

    def run(n, god=True):
        p = play_mode.player
        for _ in range(n):
            zone_card.freezing = False
            for o in list(game_world.world[game_world.LAYER_UI]):
                if isinstance(o, zone_card.ZoneCard):
                    game_world.remove_object(o)
            if god:
                p.hp = max(p.hp, 1)
            game_framework.frame_time = 1 / 60
            play_mode.update()
        transition.reveal(0.0)
        transition.tick(5.0)

    def gauge(p, v):
        p.gauge.value = v
        p.gauge.zone = p.gauge._zone_of(v)

    def aim(p, x=1180, y=520):
        p.mouse_screen = (x, y)

    # (가) 어두운 방 전투: 구역 1 첫 전투방, 노멀
    p = new_run(11)
    p.set_loadout('pipe', 'pistol')
    go('stage1', 'combat')
    run(50)
    gauge(p, 38)
    p.hp = int(p.max_hp * 0.7)
    aim(p)
    run(2)
    grab('a_dark')
    boss_intro._hud_hidden[0] = True                  # 같은 순간 HUD 없이 (HUD가 가리는 넓이를 잰다)
    grab('a_dark_nohud')
    boss_intro._hud_hidden[0] = False

    # (나) 밝은 벽이 HUD 뒤: 구역 3(탑) 시작 방
    p = new_run(12)
    p.set_loadout('gauntlet', 'chain')
    go('stage3', 'combat')
    run(50)
    gauge(p, 62)
    aim(p)
    run(2)
    grab('b_bright')

    # (다) 보스전: 구역 3 아크 (페이즈 눈금 여럿), 체력을 깎아 깎인 자국까지
    p = new_run(13)
    p.set_loadout('pipe', 'gauntlet')
    play_mode._test_jump('stage3')
    play_mode._test_jump('boss')
    run(90)
    b = play_mode.stage.boss
    if b is not None:
        b.hp = b.max_hp * 0.78                    # 첫 페이즈 경계 위 (페이즈 전환 컷인 없이 깎인 자국만)
        run(6)
    gauge(p, 55)
    aim(p)
    run(1)
    effects.flash_left = 0.0
    import cut_in
    if hasattr(cut_in, 'reset'):
        cut_in.reset()
    grab('c_boss')

    # (라) 위험 구간 + E 강화 준비
    p = new_run(14)
    p.set_loadout('pistol', 'chain')
    go('stage2', 'combat')
    run(50)
    gauge(p, p.gauge.cap - config.CRITICAL_MARGIN + 3)
    aim(p)
    run(1)
    grab('d_critical')

    # (마) 페이드
    p = new_run(15)
    p.set_loadout('pipe', 'pistol')
    go('stage1', 'combat')
    run(50)
    gauge(p, 9)
    p.hp = int(p.max_hp * 0.25)
    aim(p)
    run(1)
    grab('e_fade')

    # (바) 저주가 걸린 상태
    p = new_run(16)
    p.set_loadout('pipe', 'chain')
    mu.give(p, 'tide_cost')
    go('stage2', 'combat')
    run(50)
    curse.take(p, curse.CARD + 'frail')
    gauge(p, 44)
    aim(p)
    run(1)
    grab('f_curse')

    # (사) 아이템·증강 여럿 + 무기 교체 직후 + 아이템 띠
    p = new_run(17)
    p.set_loadout('pipe', 'pistol')
    for it in ('cap', 'absorb', 'steady', 'enhance', 'resist', 'dash', 'power', 'vigor', 'power'):
        items.apply(p, it)
    for m in ('tide_cost', 'bloom_crit'):
        mu.give(p, m)
    p.shards = 137
    go('stage1', 'combat')
    run(50)
    p.swap_weapon(0)                              # 쌍권총 -> 철파이프 (교체 쿨다운 막대가 쌍권총 칸에)
    run(3)
    ui = next(o for o in game_world.world[game_world.LAYER_UI] if type(o).__name__ == 'GameUI')
    ui.show_pickup('absorb', items.describe(p, 'absorb'))
    run(12)
    gauge(p, 47)
    aim(p)
    run(1)
    grab('g_items')
    boss_intro._hud_hidden[0] = True
    grab('g_items_nohud')
    boss_intro._hud_hidden[0] = False

    # (아) 상점 진열대 앞 상호작용 안내 (+ 문 위 보상 판은 전투방 문에 뜬다)
    p = new_run(18)
    p.set_loadout('pipe', 'pistol')
    p.shards = 80
    go('stage1', 'shop')
    run(20)
    st = play_mode.stage
    if st.pedestals:
        ped = st.pedestals[1 if len(st.pedestals) > 1 else 0]
        p.x, p.y = ped.x + 10, ped.y + 10
        p.vx = p.vy = 0
        camera.snap(p, st.room)
    run(30)
    aim(p)
    run(1)
    grab('h_shop')

    # (덤) 강화 2단계 중 + 방 클리어 알림 + 깬 방 문 위 보상 판
    p = new_run(19)
    p.set_loadout('gauntlet', 'pipe')
    go('stage1', 'combat')
    run(30)
    for o in list(game_world.world[game_world.LAYER_ENEMY]):
        game_world.remove_object(o)
    run(40)
    gauge(p, 80)
    for _ in range(2):
        p.gauge.use_enhance()
    play_mode.clear_notice = 2.6
    aim(p)
    run(1)
    play_mode.clear_notice = 2.6
    grab('i_enhanced')
    close_canvas()
    print('ok', out)


def _label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 * len(text) + 16, 22), fill=(0, 0, 0))
    d.text((6, 5), text, fill=(255, 255, 120))
    return im


def board(before, after, out, extra=None):
    os.makedirs(out, exist_ok=True)
    made = []
    for s in SCENES:
        a, b = os.path.join(before, f'hud_{s}.png'), os.path.join(after, f'hud_{s}.png')
        if not (os.path.exists(a) and os.path.exists(b)):
            continue
        im = Image.new('RGB', (W, H * 2 + 20), (20, 20, 24))
        im.paste(_label(Image.open(a), f'BEFORE {s}'), (0, 0))
        im.paste(_label(Image.open(b), f'AFTER {s}'), (0, H + 20))
        name = f'H1_scene_{s}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    for part, box in CROPS.items():                    # 원래 크기로 자른 전·후: 장면마다 한 줄(왼쪽 전, 오른쪽 후)
        cw, ch = box[2] - box[0], box[3] - box[1]
        rows = [s for s in SCENES if os.path.exists(os.path.join(after, f'hud_{s}.png'))]
        im = Image.new('RGB', (cw * 2 + 30, (ch + 10) * len(rows)), (20, 20, 24))
        for r, s in enumerate(rows):
            for c, folder in enumerate((before, after)):
                src = Image.open(os.path.join(folder, f'hud_{s}.png')).crop(box)
                im.paste(_label(src, f'{"BEFORE" if c == 0 else "AFTER"} {s}'), (c * (cw + 30), r * (ch + 10)))
        name = f'H1_crop_{part}.png'
        im.save(os.path.join(out, name))
        made.append(name)
    if extra:                                          # 타이틀·증강 카드·HUD를 한 벌로
        t = os.path.join(extra, 'title_0.png')
        c = os.path.join(extra, 'cards_slum_base.png')
        h = os.path.join(after, 'hud_a_dark.png')
        if all(os.path.exists(x) for x in (t, c, h)):
            hw, hh = W // 2, H // 2
            im = Image.new("RGB", (hw * 3 + 40, hh * 2 + 20), (20, 20, 24))
            for i, x in enumerate((t, c, h)):
                im.paste(Image.open(x).resize((hw, hh), Image.NEAREST), (i * (hw + 20), 0))
            # 아래: 원래 크기로 가운데 위 부분을 셋 나란히 (로고 / 카드 위쪽 / 게이지)
            crops = [(Image.open(t), (W // 2 - 480, 140, W // 2 + 160, 140 + H // 2)),
                     (Image.open(c), (W // 2 - 640, 200, W // 2, 200 + H // 2)),
                     (Image.open(h), (0, 0, 640, H // 2))]
            for i, (src, box) in enumerate(crops):
                im.paste(src.crop(box), (i * (hw + 20), hh + 20))
            im.save(os.path.join(out, 'H1_set.png'))
            made.append('H1_set.png')
    import numpy as np                                # HUD가 가리는 넓이: 같은 순간 HUD 없는 화면과 다른 픽셀 수
    for s in ('a_dark', 'g_items'):
        for label, folder in (('전', before), ('후', after)):
            a = np.array(Image.open(os.path.join(folder, f'hud_{s}.png'))).astype(int)
            b = np.array(Image.open(os.path.join(folder, f'hud_{s}_nohud.png'))).astype(int)
            print(f'{s} {label}: HUD가 바꾼 픽셀 {(np.abs(a - b).sum(axis=2) > 24).mean() * 100:.2f}%')
    print(len(made), '장:', ', '.join(made))


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:6])
    else:
        shoot(sys.argv[1])
