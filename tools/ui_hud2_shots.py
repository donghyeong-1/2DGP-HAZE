"""H2 HUD 손질 셋 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' H2): 실제 창(모니터 2)에서 실제 그리기 코드로 찍는다.
설정·저장 파일은 임시 폴더로 돌린다. 같은 시드·같은 프레임 수라 고치기 전·후가 같은 순간이다.

  python tools/ui_hud2_shots.py <출력 폴더>                     장면 찍기: h2_<장면>.png
  python tools/ui_hud2_shots.py --board <전 폴더> <후 폴더> <비교판 폴더>
        H2_gauge_pulse.png(게이지 둘레 원래 크기 전·후, 맥박 켜짐·꺼짐), H2_slots_<dark|bright>.png(오른쪽 아래 세 칸 원래 크기 전·후),
        H2_full_critical.png·H2_full_normal.png(전체 화면 전·후)

장면: crit_on·crit_off 위험 구간 맥박 켜진/꺼진 프레임, fade_on·fade_off 페이드 맥박 켜진/꺼진 프레임,
      <dark|bright>_<상태> 무기 칸: a_ready 강화 쓸 수 있음 + 1번 무기 듦 / b_on1 강화 켬 1단계 / c_on2 강화 켬 2단계 /
      d_low 게이지 모자라 강화 못 씀 / e_slot2 2번 무기 듦 / f_empty 둘째 칸이 빈 칸
"""
import ctypes
import math
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
from PIL import Image, ImageDraw  # noqa: E402

W, H = 1920, 1080
PULSE = ('crit_on', 'crit_off', 'fade_on', 'fade_off')
SLOT_STATES = ('a_ready', 'b_on1', 'c_on2', 'd_low', 'e_slot2', 'f_empty')
ROOMS = {'dark': (11, 'stage1'), 'bright': (12, 'stage3')}
# 원래 크기로 자를 부분 (PIL 좌표: 위가 0)
GAUGE_BOX = (560, 0, 1360, 130)
SLOT_BOX = (1340, 820, 1920, 1080)
# 맥박 sin(aura_time * k) > 0 이면 켜진 프레임 (ui._draw_gauge: 위험 k = 9, 페이드 k = 6)
AURA = {'crit_on': math.pi / 18, 'crit_off': 3 * math.pi / 18, 'fade_on': math.pi / 12, 'fade_off': 3 * math.pi / 12}


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
    play_mode.update_canvas = lambda: None            # 화면에 내보내기 전에 읽는다
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()

    def grab(name):
        play_mode.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'h2_{name}.png'))
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

    # 위험·페이드: 같은 순간에서 aura_time만 바꿔 맥박 켜짐·꺼짐 두 장
    for prefix, seed, target, value in (('crit', 14, 'stage2', None), ('fade', 15, 'stage1', 9)):
        p = new_run(seed)
        p.set_loadout('pistol', 'chain') if prefix == 'crit' else p.set_loadout('pipe', 'pistol')
        go(target)
        run(50)
        gauge(p, p.gauge.cap - config.CRITICAL_MARGIN + 3 if value is None else value)
        p.mouse_screen = (1180, 520)
        run(1)
        gauge(p, p.gauge.cap - config.CRITICAL_MARGIN + 3 if value is None else value)
        for k in ('on', 'off'):
            p.aura_time = AURA[f'{prefix}_{k}']
            grab(f'{prefix}_{k}')

    # 무기 칸 여섯 상태 x 어두운 방·밝은 벽 방
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
            grab(f'{room}_{state}')
    close_canvas()
    print('ok', out)


def _label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 7 * len(text) + 12, 16), fill=(0, 0, 0))
    d.text((5, 3), text, fill=(255, 255, 120))
    return im


def _crops(before, after, names, box, out_name, out):
    cw, ch = box[2] - box[0], box[3] - box[1]
    im = Image.new('RGB', (cw * 2 + 30, (ch + 10) * len(names)), (20, 20, 24))
    for r, s in enumerate(names):
        for c, folder in enumerate((before, after)):
            src = Image.open(os.path.join(folder, f'h2_{s}.png')).crop(box)
            im.paste(_label(src, f'{"BEFORE" if c == 0 else "AFTER"} {s}'), (c * (cw + 30), r * (ch + 10)))
    im.save(os.path.join(out, out_name))
    return out_name


def board(before, after, out):
    os.makedirs(out, exist_ok=True)
    made = [_crops(before, after, PULSE, GAUGE_BOX, 'H2_gauge_pulse.png', out)]
    for room in ROOMS:
        made.append(_crops(before, after, [f'{room}_{s}' for s in SLOT_STATES], SLOT_BOX, f'H2_slots_{room}.png', out))
    for scene, name in (('crit_on', 'H2_full_critical.png'), ('dark_a_ready', 'H2_full_normal.png')):
        im = Image.new('RGB', (W, H * 2 + 20), (20, 20, 24))
        im.paste(_label(Image.open(os.path.join(before, f'h2_{scene}.png')), f'BEFORE {scene}'), (0, 0))
        im.paste(_label(Image.open(os.path.join(after, f'h2_{scene}.png')), f'AFTER {scene}'), (0, H + 20))
        im.save(os.path.join(out, name))
        made.append(name)
    print(len(made), '장:', ', '.join(made))


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:5])
    else:
        shoot(sys.argv[1])
