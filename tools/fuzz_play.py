"""무작위 입력 난전: 실제 창(pico2d)에 무작위 키·마우스를 넣어 튕김과 멈춤을 찾는다 (v8 6일 차 PR 자체 점검).

보스·문지기·등장씬 경로를 중심으로: 테스트 모드로 보스방을 오가고, 가끔 플레이어·보스를 쓰러뜨린다.
일시정지·설정·키 바꾸기·제작진·엔딩·NPC 창을 여닫는 입력도 섞인다(ESC, Enter, Q, O, H, C, F ...).
예외가 나면 시드·프레임·모드 스택·최근 입력과 함께 출력하고 새 판으로 이어 간다. 저장 파일은 임시 폴더를 쓴다.
등장씬·보스 카드로 게임이 25초 넘게 멈춰 있으면 '멈춤'으로 알린다.

실행 (창이 없는 곳은 xvfb-run -a -s "-screen 0 1920x1080x24" 를 앞에):
  python tools/fuzz_play.py <시드> <프레임 수>
  환경 변수: FOCUS=stage3 (그 구역 보스방에서 시작, 정해진 순간 보스 처치), BOSS_KILL=0.01 (프레임마다 보스에게 큰 피해 확률),
            P_DIE=0.004 (프레임마다 플레이어를 쓰러뜨릴 확률)
  11/26 기능을 일부러 밟는 선택지 (1이면 켠다, docs/project/bug-sweep.md 2026-11-26):
            CURSE=1 저주 카드가 늘 섞이고(curse.OFFER_CHANCE=1), 저주가 없으면 여섯 종을 차례로 건다.
                    가끔 게이지 용량 아이템·헤이즈 샘·판 도중 무기 얻기, 시한폭탄 중 오버로드.
            AWAKEN=1 판마다 '궁극기 각성'을 주고 강화 3단계를 자주 채운다 (컷인 중 무작위 입력·피격·사망)
            ENH=1 강화 1~3단계를 자주 채운다 (강화 교체기)
            ONE_WEAPON=1 무기 하나로 시작하고 가끔 판 도중 둘째 무기를 얻는다
            OFFER=0.004 프레임마다 증강 카드 창을 여는 확률. FEW=1이면 카드가 0~3장(바닥난 경우)
            RESEEN=1 가끔 본 보스 기록을 지워 처음 만난 등장씬(크래셔 착지)을 다시 본다
            SKIP=1 등장씬 동안 Enter·Space·Esc를 자주 넣는다 (넘기기 연타, 등장씬 중 일시정지)
            CUTKILL=1 컷인이 도는 동안 보스를 쓰러뜨리거나 반 넘게 깎는다 (컷인 직전·도중 처치, 막타 줌과 겹침)
  SHOTS=<폴더> 화면을 그 폴더에 PNG로 남긴다: 600프레임마다, 그리고 컷인·등장씬·저주 카드·저주 표시·사망 화면이 처음 보일 때 (판마다)
  늘 검사: 떠돌이 죄수 거래(피의 거래)가 내놓는 카드에 저주가 없어야 한다, 컷인·막타 줌·HUD 숨김이 끝나야 한다.
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
from window_place import place_window
place_window()                                   # HAZE_DISPLAY=2 이면 두 번째 모니터
rng = random.Random(seed)
recent = collections.deque(maxlen=30)

KEYS = [sdl2.SDLK_ESCAPE, sdl2.SDLK_RETURN, sdl2.SDLK_SPACE, sdl2.SDLK_F6, sdl2.SDLK_F7, sdl2.SDLK_F8, sdl2.SDLK_F9,
        sdl2.SDLK_UP, sdl2.SDLK_DOWN, sdl2.SDLK_LEFT, sdl2.SDLK_RIGHT, sdl2.SDLK_q, sdl2.SDLK_o, sdl2.SDLK_h, sdl2.SDLK_c,
        sdl2.SDLK_f, sdl2.SDLK_TAB, sdl2.SDLK_BACKSPACE, sdl2.SDLK_1, sdl2.SDLK_2, sdl2.SDLK_3]
for ks in keybinds.DEFAULTS.values():
    KEYS += [k for k in ks if k]
held = set()
inject = []                    # 시나리오가 넣는 키 (다음 프레임 입력 맨 앞)


def fake_events():
    out = []
    while inject:
        e = p2.Event(sdl2.SDL_KEYDOWN)
        e.key = inject.pop(0)
        out.append(e)
        recent.append((frame, 'inject', e.key, None))
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


shot_wanted = [None]           # 이번 프레임에 남길 그림 이름 (SHOTS)


def shooting_update_canvas():
    name = shot_wanted[0]
    if name:
        import ctypes
        from PIL import Image
        w, h = ctypes.c_int(), ctypes.c_int()
        sdl2.SDL_GetRendererOutputSize(p2.renderer, ctypes.byref(w), ctypes.byref(h))   # 설정에서 해상도를 바꿀 수 있다
        W, H = w.value, h.value
        buf = (ctypes.c_ubyte * (W * H * 4))()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        im = Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB')
        im.resize((W // 2, H // 2), Image.NEAREST).save(os.path.join(os.environ['SHOTS'], name + '.png'))
        shot_wanted[0] = None
    _real_update_canvas()


_real_update_canvas = p2.update_canvas


def patch():
    for name, mod in list(sys.modules.items()):
        if mod is not None and getattr(mod, '__file__', '') and '/src/' in (mod.__file__ or '').replace(os.sep, '/') and getattr(mod, 'get_events', None) is not None:
            if mod.get_events is not fake_events:
                mod.get_events = fake_events
            if os.environ.get('SHOTS') and getattr(mod, 'update_canvas', None) is _real_update_canvas:
                mod.update_canvas = shooting_update_canvas


def start():
    import play_mode
    stats['runs'] += 1
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
    setup_run()


frame = 0
crashes = 0
stats = collections.Counter()
frozen_run = 0
ENV = lambda k, d='0': os.environ.get(k, d)   # noqa: E731
import curse, mutations, events, boss_intro, cut_in, postfx, weapon as weapon_mod
if ENV('CURSE') == '1':
    curse.OFFER_CHANCE = 1.0
CURSE_ORDER = list(curse.CURSES)
WEAPON_IDS = list(weapon_mod.WEAPONS)
problems = collections.Counter()


def problem(key, *info):
    problems[key] += 1
    if problems[key] <= 3:
        print(f'=== 이상 {key} seed={seed} frame={frame}', *info)


_orig_take = events.take


def checked_take(player, card, rng=None):
    out = _orig_take(player, card, rng)
    if out and out[2]:
        if any(str(c).startswith(curse.CARD) for c in out[2]):
            problem('거래에 저주 카드', out[2])
        stats['deal_follow'] += 1
    return out


events.take = checked_take
if ENV('FEW') == '1':
    _orig_offer = mutations.offer
    mutations.offer = lambda player, rng, n=3: _orig_offer(player, rng, n)[:rng.choice((0, 1, 2, 3))]


def setup_run():
    """새 판(play_mode.enter 직후): 선택지에 맞춰 무기·증강을 준다."""
    import play_mode
    p = play_mode.player
    if ENV('ONE_WEAPON') == '1':
        p.set_loadout(rng.choice(WEAPON_IDS))
    elif ENV('CURSE') == '1' or ENV('AWAKEN') == '1' or ENV('ENH') == '1':
        a, b = rng.sample(WEAPON_IDS, 2)
        p.set_loadout(a, b)
    if ENV('CURSE') == '1' or ENV('OFFER', '0') != '0':
        base = [m for m in mutations.MUTATIONS if mutations.tier(m) == 'base' and mutations.available(p, m)]
        for m in rng.sample(base, min(2, len(base))):
            mutations.give(p, m)                              # 증강이 하나는 있어야 저주가 섞인다
    if ENV('AWAKEN') == '1':
        mutations.give(p, 'ult_awaken')
    if ENV('RESEEN') == '1' and rng.random() < 0.5:
        boss_intro.seen.clear()


def scenario():
    """플레이 중 프레임마다: 오늘 기능을 일부러 밟는다."""
    import play_mode, items
    p = play_mode.player
    if p is None or p.state == 'DEAD':
        return
    g = p.gauge
    if ENV('ONE_WEAPON') != '1' and (ENV('CURSE') == '1' or ENV('ENH') == '1') and p.weapons[1] is None:
        p.give_weapon(rng.choice([w for w in WEAPON_IDS if not p.has_weapon(w)]))   # 구역 시작(무기 걸이)이 한 칸으로 되돌린다
    if ENV('AWAKEN') == '1' and not mutations.has(p, 'ult_awaken'):
        mutations.give(p, 'ult_awaken')
    if (ENV('CURSE') == '1' or ENV('OFFER', '0') != '0') and len(mutations.owned(p)) < 2:
        base = [m for m in mutations.MUTATIONS if mutations.tier(m) == 'base' and mutations.available(p, m)]
        mutations.give(p, rng.choice(base))
    if ENV('CURSE') == '1':
        if curse.active(p) is None and rng.random() < 0.01:
            cid = CURSE_ORDER[stats['curse_n'] % len(CURSE_ORDER)]
            if curse._usable(p, cid):
                curse.take(p, curse.CARD + cid)
                stats['curse:' + cid] += 1
            stats['curse_n'] += 1
        cid = curse.active(p)
        if cid == 'lowcap' and rng.random() < 0.004:
            items.apply(p, "cap")
            stats['lowcap_cap'] += 1
        if cid == 'lowcap' and rng.random() < 0.004:
            events.take(p, rng.choice(events.cards('spring')))
            stats['lowcap_spring'] += 1
        if cid == 'lock' and rng.random() < 0.01:
            p.give_weapon(rng.choice(WEAPON_IDS))                # 판 도중 무기 얻기
            stats['lock_give'] += 1
        if cid == 'lock' and rng.random() < 0.02:
            if p.swap_weapon(strike=True):
                problem('굳은 손인데 교체됨')
            stats['lock_swap'] += 1
        if cid == 'doom' and rng.random() < 0.01:
            g.add(g.cap, 'fuzz')                                 # 오버로드 -> 사망
            stats['doom_overload'] += 1
        if cid and rng.random() < 0.002:
            curse.on_room_clear(p, rng)                          # 방을 깬 것으로 (풀리며 보상)
            stats['curse_room'] += 1
        if g.cap < config.ZONE_NORMAL_MAX + config.CRITICAL_MARGIN:
            problem('게이지 한계가 너무 낮음', g.cap, cid)
    if ENV('ONE_WEAPON') == '1' and rng.random() < 0.0015 and p.weapons[1] is None:
        p.give_weapon(rng.choice(WEAPON_IDS))
        stats['give_second'] += 1
    if (ENV('AWAKEN') == '1' or ENV('ENH') == '1') and rng.random() < 0.02 and not g.enhanced:
        g.enhance_level = config.ENHANCE_MAX_LEVEL if ENV('AWAKEN') == '1' and rng.random() < 0.7 else rng.randint(1, 3)
        g.enhance_timer = config.ENHANCE_TIME
        stats['enh%d' % g.enhance_level] += 1
    boss = getattr(play_mode.stage, 'boss', None)
    if ENV('SKIP') == '1' and boss_intro.freezing and rng.random() < 0.12:
        inject.append(rng.choice((sdl2.SDLK_RETURN, sdl2.SDLK_SPACE, sdl2.SDLK_RETURN, sdl2.SDLK_ESCAPE)))
        stats['intro_key'] += 1
    if ENV('CUTKILL') == '1' and boss is not None and boss.alive:
        if cut_in.running() and rng.random() < 0.08:
            boss.take_damage(boss.max_hp * rng.choice((0.3, 2.0)), from_x=p.x)     # 컷인 도중 처치
            stats['cutin_kill'] += 1
        elif not cut_in.running() and not boss_intro.freezing and rng.random() < 0.01:
            boss.take_damage(max(1, boss.hp - boss.max_hp * 0.45), from_x=p.x)     # 페이즈 문턱 바로 아래로 -> 다음 갱신에 컷인
            stats['phase_push'] += 1
    if cut_in.running():
        stats['cutin_frames'] += 1
        if rng.random() < 0.02:                                  # 컷인 중 피격
            p.invuln_left = 0
            p.take_hit(rng.choice((5, 10 ** 6)), source=None)
            stats['cutin_hit'] += 1
    rate = float(ENV('OFFER', '0'))
    if rate and rng.random() < rate:
        choices = mutations.offer(p, rng)
        if choices:
            choices = curse.mix_in(p, choices, rng)
        stats['offer%d' % len(choices)] += 1
        play_mode._on_mutation(choices)                         # 빈 목록이어도 창이 스스로 닫혀야 한다


watch = collections.Counter()


def invariants():
    """끝나야 할 것이 끝나는지 (프레임 수로 잰다)."""
    import play_mode
    watch['cutin'] = watch['cutin'] + 1 if cut_in.running() else 0
    if watch['cutin'] == 120:
        problem('컷인이 2초 넘게 돎', cut_in.current().__dict__.get('word'))
    import time
    if postfx.zoom_scale() == 1.0:                               # 막타 줌은 실제 시간으로 돈다
        watch.pop('zoom_t', None)
    elif 'zoom_t' not in watch:
        watch['zoom_t'] = time.monotonic()
    elif watch['zoom_t'] and time.monotonic() - watch['zoom_t'] > 2.0:
        problem('막타 줌이 2초 넘게 남음', postfx.zoom_scale(), postfx.zoom_requests)
        watch['zoom_t'] = 0
    hidden = boss_intro.hud_hidden() and not boss_intro.freezing
    watch['hud'] = watch['hud'] + 1 if hidden else 0
    if watch['hud'] == 300:
        problem('등장씬 밖에서 HUD가 5초 넘게 숨음')
    held = boss_intro.music_held(play_mode.stage) and not boss_intro.freezing
    watch['music'] = watch['music'] + 1 if held else 0
    if watch['music'] == 300:
        problem('등장씬 밖에서 음악 정적이 5초 넘게')


shot_seen = set()


def want_shot(top):
    import play_mode, mutation_mode
    name = getattr(top, '__name__', '?')
    tags = []
    if top is play_mode:
        if cut_in.running():
            tags.append('cutin')
        if boss_intro.freezing:
            tags.append('intro')
        p = play_mode.player
        if p is not None and curse.active(p):
            tags.append('curse_hud')
        if postfx.zoom_scale() != 1.0:
            tags.append('zoom')
    elif top is mutation_mode and any(str(c).startswith(curse.CARD) for c in (mutation_mode.choices or [])):
        tags.append('curse_card')
    elif name in ('ending_mode', 'npc_mode', 'pause_mode'):
        tags.append(name)
    run_id = stats['runs']
    for t in tags:
        if (run_id, t) not in shot_seen and rng.random() < 0.3:      # 처음 보인 뒤 조금 지나서 (열리는 중간도 섞이게)
            shot_seen.add((run_id, t))
            shot_wanted[0] = f'{seed}_{frame:06d}_{t}'
            return
    if frame % 600 == 0:
        shot_wanted[0] = f'{seed}_{frame:06d}_{name}'


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
        if top is play_mode:
            scenario()
            invariants()
        game_framework._tick_gamepad(top)
        top.handle_events()
        if game_framework.stack:
            game_framework.stack[-1].update()
        if game_framework.stack:
            if os.environ.get('SHOTS'):
                want_shot(game_framework.stack[-1])           # 그릴 화면 기준으로 이름을 붙인다
            game_framework.stack[-1].draw()
    except SystemExit:
        start()
    except Exception:
        crashes += 1
        print(f'=== 튕김 seed={seed} frame={frame} stack={[getattr(m, "__name__", m) for m in game_framework.stack]}')
        traceback.print_exc()
        print('SDL 오류', sdl2.SDL_GetError(), '| 이미지', len(__import__('assets')._images))
        print('최근 입력', list(recent)[-12:])
        if crashes >= 3:
            break
        game_world.clear()
        start()
close_canvas()
print(f'끝: seed={seed} frames={frame} crashes={crashes} problems={dict(problems)}', dict(stats))
