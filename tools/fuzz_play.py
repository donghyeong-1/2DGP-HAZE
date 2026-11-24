"""무작위 입력 난전: 실제 창(pico2d)에 무작위 키·마우스를 넣어 튕김과 멈춤을 찾는다 (v8 6일 차 PR 자체 점검).

보스·문지기·등장씬 경로를 중심으로: 테스트 모드로 보스방을 오가고, 가끔 플레이어·보스를 쓰러뜨린다.
일시정지·설정·키 바꾸기·제작진·엔딩·NPC 창을 여닫는 입력도 섞인다(ESC, Enter, Q, O, H, C, F ...).
예외가 나면 시드·프레임·모드 스택·최근 입력과 함께 출력하고 새 판으로 이어 간다. 저장 파일은 임시 폴더를 쓴다.
등장씬·보스 카드로 게임이 25초 넘게 멈춰 있으면 '멈춤'으로 알린다.

실행 (창이 없는 곳은 xvfb-run -a -s "-screen 0 1920x1080x24" 를 앞에):
  python tools/fuzz_play.py <시드> <프레임 수>
  환경 변수: FOCUS=stage3 (그 구역 보스방에서 시작, 정해진 순간 보스 처치), BOSS_KILL=0.01 (프레임마다 보스에게 큰 피해 확률),
            P_DIE=0.004 (프레임마다 플레이어를 쓰러뜨릴 확률)
"""
import collections, os, random, sys, tempfile, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
os.chdir(ROOT)
seed, total = int(sys.argv[1]), int(sys.argv[2])
import pico2d.pico2d as p2
from pico2d import open_canvas, close_canvas
import sdl2
import config, game_framework, game_world, meta, options, keybinds
meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json'); meta.reset()
options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')
options.test_mode = True
open_canvas(config.SCREEN_W, config.SCREEN_H)
rng = random.Random(seed)
recent = collections.deque(maxlen=30)

KEYS = [sdl2.SDLK_ESCAPE, sdl2.SDLK_RETURN, sdl2.SDLK_SPACE, sdl2.SDLK_F6, sdl2.SDLK_F7, sdl2.SDLK_F8, sdl2.SDLK_F9,
        sdl2.SDLK_UP, sdl2.SDLK_DOWN, sdl2.SDLK_LEFT, sdl2.SDLK_RIGHT, sdl2.SDLK_q, sdl2.SDLK_o, sdl2.SDLK_h, sdl2.SDLK_c,
        sdl2.SDLK_f, sdl2.SDLK_TAB, sdl2.SDLK_BACKSPACE, sdl2.SDLK_1, sdl2.SDLK_2, sdl2.SDLK_3]
for ks in keybinds.DEFAULTS.values():
    KEYS += [k for k in ks if k]
held = set()


def fake_events():
    out = []
    for _ in range(rng.choice((0, 0, 1, 1, 2, 3))):
        r = rng.random()
        if r < 0.55:
            k = rng.choice(KEYS)
            if k in held and rng.random() < 0.6:
                e = p2.Event(sdl2.SDL_KEYUP); held.discard(k)
            else:
                e = p2.Event(sdl2.SDL_KEYDOWN); held.add(k)
            e.key = k
        elif r < 0.75:
            e = p2.Event(sdl2.SDL_MOUSEMOTION)
            e.x, e.y = rng.randrange(config.SCREEN_W), rng.randrange(config.SCREEN_H)
        else:
            e = p2.Event(rng.choice((sdl2.SDL_MOUSEBUTTONDOWN, sdl2.SDL_MOUSEBUTTONUP)))
            e.button = rng.choice((1, 3))
            e.x, e.y = rng.randrange(config.SCREEN_W), rng.randrange(config.SCREEN_H)
        out.append(e)
        recent.append((frame, getattr(e, 'type', None), e.key, e.button))
    return out


def patch():
    for name, mod in list(sys.modules.items()):
        if mod is not None and getattr(mod, '__file__', '') and '/src/' in (mod.__file__ or '') and getattr(mod, 'get_events', None) is not None:
            if mod.get_events is not fake_events:
                mod.get_events = fake_events


def start():
    import play_mode
    game_framework.running = True
    game_framework.stack.clear()
    game_framework.stack.append(play_mode)
    play_mode.enter()
    focus = os.environ.get('FOCUS')
    if focus:
        play_mode._test_jump(focus)
        play_mode._test_jump('boss')
        stats['kill_at'] = frame + rng.randrange(0, 700)
    elif rng.random() < 0.8:
        play_mode._test_jump(rng.choice(['stage1', 'stage2', 'stage3']))
        play_mode._test_jump('boss')


frame = 0
crashes = 0
stats = collections.Counter()
frozen_run = 0
start()
while frame < total:
    frame += 1
    patch()
    game_framework.frame_time = 1 / 60
    try:
        if not game_framework.running or not game_framework.stack:
            start()
        top = game_framework.stack[-1]
        import play_mode, boss_intro
        stats[getattr(top, '__name__', '?')] += 1
        if boss_intro.freezing:
            stats['intro'] += 1
        if top is play_mode and (boss_intro.freezing or __import__('zone_card').freezing):
            frozen_run += 1
            stats['max_frozen'] = max(stats['max_frozen'], frozen_run)
            if frozen_run == 1500:
                print(f'=== 멈춤 25초 seed={seed} frame={frame}', [(type(o).__name__, getattr(o, 'step', None), getattr(o, 't', None)) for o in game_world.world[game_world.LAYER_UI]][-3:])
        elif top is play_mode:
            frozen_run = 0
        if getattr(play_mode, 'stage', None) is not None and getattr(play_mode.stage, 'boss', None) is not None:
            stats['boss:' + play_mode.stage.boss.kind] += 1
        if top is play_mode and rng.random() < float(os.environ.get('P_DIE', '0.004')) and play_mode.player is not None:   # 가끔 플레이어를 쓰러뜨린다
            play_mode.player.invuln_left = 0
            play_mode.player.take_hit(10 ** 6, source=None)
        if top is play_mode and rng.random() < float(os.environ.get('BOSS_KILL', '0.006')) and getattr(play_mode.stage, 'boss', None) is not None:
            b = play_mode.stage.boss
            if b.alive:
                b.take_damage(b.max_hp * rng.choice((0.3, 0.6, 2.0)), from_x=play_mode.player.x)
        if top is play_mode and os.environ.get('FOCUS') and frame == stats['kill_at'] and play_mode.stage.boss is not None:
            play_mode.stage.boss.take_damage(10 ** 7, from_x=play_mode.player.x)     # 등장씬 중이든 아니든 정해진 순간에 쓰러뜨린다
        if top is play_mode and rng.random() < 0.003 and not os.environ.get('FOCUS'):
            play_mode._test_jump(rng.choice(['boss', 'stage1', 'stage2', 'stage3']))
        game_framework._tick_gamepad(top)
        top.handle_events()
        if game_framework.stack:
            game_framework.stack[-1].update()
        if game_framework.stack:
            game_framework.stack[-1].draw()
    except SystemExit:
        start()
    except Exception:
        crashes += 1
        print(f'=== 튕김 seed={seed} frame={frame} stack={[getattr(m, "__name__", m) for m in game_framework.stack]}')
        traceback.print_exc()
        print('최근 입력', list(recent)[-12:])
        if crashes >= 3:
            break
        game_world.clear()
        start()
close_canvas()
print(f'끝: seed={seed} frames={frame} crashes={crashes}', dict(stats))
