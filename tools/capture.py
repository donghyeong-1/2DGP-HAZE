"""게임 화면 캡처: 실제 창(pico2d)을 열고 게임의 draw()를 그대로 그린 뒤 렌더러 픽셀을 PNG로 저장한다.

에셋·연출을 바꾼 뒤 "정말 그렇게 보이는지"를 확인하는 용도다. 테스트(창 없음)로는 그림을 볼 수 없다.
실행하면 잠깐 창이 뜬다. 결과는 --out 폴더에 shot_00.png ... 와 모아 보기 sheet.png(축소 없이 잘라 붙임).

옵션
  --stage 2          0 은신처, 1~3 스테이지 (기본 1)
  --cell 1,0          스테이지 1의 방 좌표 (기본: 시작 방)
  --clear             방에 원래 있던 적을 지운다
  --spawn hound:400 guard:-300   적을 플레이어 기준 x 거리에 세운다 (boss도 가능)
  --weapon knife      두 번째 칸 무기를 주고 든다 (knife, gauntlet, chain)
  --gauge 65          게이지(%) 설정
  --bot stand|dodge   tools/balance_sim.py의 봇이 플레이어를 조작해 싸운다 (없으면 가만히 서 있다)
  --shots 8 --every 10   10프레임마다 8장
  --warmup 20         첫 장 전에 흘려보낼 프레임
  --crop x0,y0,x1,y1  모아 보기에 쓸 화면 영역 (기본: 전체를 절반 크기로)
  --god               플레이어가 죽지 않게 한다
  --hold              공격 버튼을 누른 채로 둔다 (건틀릿 충전 확인)
  --display 2         창을 두 번째 모니터에 띄운다 (환경 변수 HAZE_DISPLAY=2 와 같음)

예: python tools/capture.py --cell 1,0 --clear --spawn hound:500 --bot stand --shots 12 --every 6 --god --out shots/hound
"""
import argparse
import ctypes
import inspect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cell')
    ap.add_argument('--stage', type=int, default=1, help='0 은신처, 1~3 스테이지 (기본 1)')
    ap.add_argument('--clear', action='store_true')
    ap.add_argument('--spawn', nargs='*', default=[])
    ap.add_argument('--weapon')
    ap.add_argument('--gauge', type=float)
    ap.add_argument('--bot', choices=('stand', 'dodge'))
    ap.add_argument('--shots', type=int, default=1)
    ap.add_argument('--every', type=int, default=10)
    ap.add_argument('--warmup', type=int, default=20)
    ap.add_argument('--crop')
    ap.add_argument('--god', action='store_true')
    ap.add_argument('--hold', action='store_true')
    ap.add_argument('--display', type=int, help='창을 띄울 모니터 번호 (1부터, 기본: HAZE_DISPLAY 환경 변수)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, clear_canvas, close_canvas, open_canvas
    import pico2d.pico2d as p2
    from sdl2 import SDL_PIXELFORMAT_RGBA32, SDL_RenderReadPixels
    from PIL import Image

    import camera
    import config
    import game_framework
    import game_world
    import play_mode

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')        # 최근접 필터 (게임과 같게)
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window(a.display)                              # --display 2 또는 HAZE_DISPLAY=2: 두 번째 모니터
    W, H = config.SCREEN_W, config.SCREEN_H
    buf = (ctypes.c_ubyte * (W * H * 4))()
    draw_src = inspect.getsource(play_mode.draw)

    def grab():
        clear_canvas()
        ns = dict(play_mode.__dict__)
        ns['update_canvas'] = lambda: None                 # 화면에 내보내지 않고 렌더러에 그린 채로 읽는다
        ns['clear_canvas'] = lambda: None
        exec(draw_src + '\ndraw()', ns)
        SDL_RenderReadPixels(p2.renderer, None, SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        return Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB')

    def step(n, bot_state):
        for _ in range(n):
            if a.bot:
                import balance_sim
                balance_sim.bot_step(p, a.bot, a.weapon or 'pipe', bot_state)
            if a.god:
                p.hp = p.max_hp
            game_framework.frame_time = 1 / 60
            play_mode.update()

    import meta
    import stage as stage_mod
    import tempfile
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')   # 사용자 저장을 덮어쓰지 않는다 (처음 안내가 '본 것'을 저장한다)
    meta.reset()                                         # 사용자 저장(영구 강화)을 읽지 않고 기본값으로 찍는다
    play_mode.enter()                                    # 판은 은신처에서 시작하므로 스테이지 1로 바꾼다
    p = play_mode.player
    stage = play_mode.stage
    for _ in range(a.stage):                             # --stage: 은신처(0)에서 그 스테이지까지 넘긴다
        stage = stage_mod.next_stage(stage)
    play_mode.stage, play_mode.room = stage, stage.room
    for o in game_world.world[game_world.LAYER_UI]:
        if hasattr(o, 'stage'):
            o.stage = stage
    if a.cell:
        cx, cy = (int(v) for v in a.cell.split(','))
        stage.enter_room((cx, cy), 'L')
    camera.snap(p, stage.room)
    import transition
    transition.reveal(0.0)                               # 방 입장 점묘(계획 4-3)가 캡처를 가리지 않게
    if a.clear:
        for o in list(game_world.world[game_world.LAYER_ENEMY]):
            game_world.remove_object(o)
    if a.weapon:
        p.give_weapon(a.weapon)
    if a.gauge is not None:
        p.gauge.value = a.gauge
        p.gauge.zone = p.gauge._zone_of(a.gauge)
    for spec in a.spawn:
        kind, dx = spec.split(':')
        x = p.x + float(dx)
        if kind == 'boss':
            from boss import Boss
            e = Boss(x, p.y, stage.room, p)
        else:
            import enemy_kinds
            e = enemy_kinds.make(kind, x, p.y, stage.room, p)       # 드론·수레는 자기 클래스
        game_world.add_object(e, game_world.LAYER_ENEMY)
        if not (0 < x < stage.room.width):
            print(f'경고: {spec}는 방 밖(x={x:.0f}, 방 폭 {stage.room.width})')

    bot_state = {}
    if a.hold:
        p.attack_held = True
        p.request_attack()
    step(a.warmup, bot_state)
    shots = []
    for i in range(a.shots):
        if i:
            step(a.every, bot_state)
        img = grab()
        path = os.path.join(a.out, f'shot_{i:02d}.png')
        img.save(path)
        shots.append(img)
        foes = [f'{e.kind}:{e.state}:{int(e.hp)}' for e in game_world.world[game_world.LAYER_ENEMY]]
        print(f'{path}  player {p.state} hp {int(p.hp)} gauge {p.gauge.value:.0f}  적 {foes}')
    close_canvas()

    # 모아 보기: 잘라 낸 영역(없으면 전체를 절반으로)을 세로 4장씩 붙인다
    if a.crop:
        box = tuple(int(v) for v in a.crop.split(','))
        tiles = [s.crop(box) for s in shots]
    else:
        tiles = [s.resize((W // 2, H // 2), Image.NEAREST) for s in shots]
    tw, th = tiles[0].size
    cols = min(len(tiles), 2 if not a.crop else 1)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (tw * cols, th * rows))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    sheet.save(os.path.join(a.out, 'sheet.png'))
    print('모아 보기:', os.path.join(a.out, 'sheet.png'))


if __name__ == '__main__':
    main()
