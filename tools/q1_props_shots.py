"""Q1 소품 그림 다시 뽑기 확인 촬영 (2026-11-27, docs/opus/TASKS.md '4차' Q1).

실제 창(모니터 2)에서 게임의 그리기 코드 그대로 찍는다. 설정·저장 파일은 임시 폴더로 돌린다.
같은 시드·같은 프레임 수라 그림을 바꾸기 전·후가 같은 순간이다.

  python tools/q1_props_shots.py <출력 폴더>
      장면마다 q1_<장면>.png(전체 화면)와 boxes.json(물건마다 화면 위 둘레: 왼쪽, 위, 오른쪽, 아래. PIL 좌표)
  python tools/q1_props_shots.py --board <전 폴더> <후 폴더> <비교판 폴더>
      Q1_<물건>.png(전·후, 원래 크기 + 4배), Q1_hideout.png, Q1_rooms.png
  python tools/q1_props_shots.py --audit <폴더> <비교판 경로>
      Q1_audit.png: 물건마다 둘레를 잘라 이름을 단다 (원래 크기)
"""
import ctypes
import json
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
os.chdir(ROOT)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1920, 1080
SEED = 7

# 장면: (이름, 구역, 방 종류, 주인공을 세울 물건 종류 또는 열 번호)
SCENES = [
    ('hideout_armory', 'hideout', 'hideout', 'armory'),
    ('hideout_practice', 'hideout', 'hideout', 'practice'),
    ('hideout_left', 'hideout', 'hideout', 4),
    ('slum_crate', 'stage1', 'combat', 'crate'),
    ('foundry_vent', 'stage2', 'combat', 'vent'),
    ('tower_laser', 'stage3', 'combat', 'laser'),
    ('slum_gold', 'stage1', 'gold', 'pedestal'),
    ('slum_shop', 'stage1', 'shop', 'pedestal'),
    ('slum_event', 'stage1', 'event', 'event'),
    ('foundry_boss', 'stage2', 'boss', 8),
]


def _box(obj, img_w, img_h, dy=0):
    import camera
    sx, sy = camera.to_screen(obj.x, obj.y)
    return [int(sx - img_w // 2), int(H - (sy + dy + img_h)), int(sx + img_w // 2), int(H - (sy + dy))]


def shoot(out):
    os.makedirs(out, exist_ok=True)
    import pico2d.pico2d as p2
    import sdl2
    from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

    import config
    import meta
    import options
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')   # 사용자 저장을 건드리지 않는다
    meta.reset()
    options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')  # 사용자 설정을 건드리지 않는다
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    from window_place import place_window
    place_window(2)
    import assets
    import boss_intro
    import camera
    import effects
    import game_framework
    import game_world
    import play_mode
    import stage as stage_mod
    import transition
    import zone_card
    play_mode.update_canvas = lambda: None
    config.BOSS_INTRO = False
    buf = (ctypes.c_ubyte * (W * H * 4))()
    boxes = {}

    def grab(name):
        play_mode.draw()
        sdl2.SDL_RenderReadPixels(p2.renderer, None, sdl2.SDL_PIXELFORMAT_RGBA32, buf, W * 4)
        Image.frombuffer('RGBA', (W, H), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(os.path.join(out, f'q1_{name}.png'))
        p2.update_canvas()

    def run(n, hold_x=None):
        p = play_mode.player
        for _ in range(n):
            zone_card.freezing = False
            for o in list(game_world.world[game_world.LAYER_UI]):
                if isinstance(o, zone_card.ZoneCard):
                    game_world.remove_object(o)
            p.hp = max(p.hp, p.max_hp * 0.7)
            if hold_x is not None:
                p.x = hold_x
            game_framework.frame_time = 1 / 60
            play_mode.update()
        transition.reveal(0.0)
        transition.tick(5.0)

    for name, zone, kind, where in SCENES:
        random.seed(SEED)
        boss_intro.reset_all()
        effects.reset()
        game_framework.stack[:] = [play_mode]
        play_mode.enter()
        p = play_mode.player
        p.set_loadout('pipe', 'pistol')
        if zone != 'hideout':
            play_mode._test_jump(zone)
        st = play_mode.stage
        if kind != 'hideout':
            coords = [c for c in st.layout if st.type_of(c) == kind]
            if kind == 'combat':                                   # 장치가 놓이는 첫 방을 찾는다
                for c in coords:
                    st.enter_room(c, 'L')
                    if any(d.kind == where for d in st.devices):
                        break
            else:
                st.enter_room(coords[0], 'L')
            play_mode.room = st.room
        room = st.room
        objs = []                                                  # (이름, 물건, 그림 폭, 높이, dy)
        if kind == 'hideout':
            for n in st.npcs:
                if n.kind in ('armory', 'practice'):
                    objs.append((n.kind, n, 200, 130, 0))
                else:
                    objs.append((n.kind, n, 130, 130, 0))
        for d in getattr(st, 'devices', []) or []:
            if d.kind == 'crate':
                objs.append(('crate', d, 60, 60, 0))
            elif d.kind == 'vent':
                objs.append(('vent', d, 72, 20, -4))
            elif d.kind == 'laser':
                objs.append(('laser', d, 64, 76, d.top - d.floor - 68))
            elif d.kind == 'crumble':
                objs.append(('crumble', d, (d.x1 - d.x0), 16, -12))
        for pd in getattr(st, 'pedestals', []) or []:
            objs.append(('pedestal_' + ('gone' if pd.gone else 'gold' if pd.mode == 'rift' else pd.mode), pd, 120, 150, 0))
        if getattr(st, 'event', None) is not None:
            objs.append(('event_' + st.event.kind, st.event, 140, 110, 0))
        # 주인공을 물건 옆(왼쪽 70px)에 세운다
        if isinstance(where, int):
            x = where * config.TILE + config.TILE / 2
        else:
            hit = [o for o in objs if o[0] == where or o[0].startswith(where) or (where == 'event' and o[0].startswith('event'))]
            x = (hit[0][1].x - (150 if where == 'armory' else 90)) if hit else room.width / 2
            if where == 'laser' and hit:
                x = hit[0][1].x - 160
        p.x = x
        camera.snap(p, room)
        p.swap_weapon(0)
        run(90, hold_x=x)
        camera.snap(p, room)
        p.mouse_screen = (1500, 560)
        run(1, hold_x=x)
        if where == 'laser' and hit:                                  # 천장의 레이저 머리가 화면 안에 오게 카메라만 올린다
            camera.y = max(camera.y, hit[0][1].top - (H - 160))
        grab(name)
        boxes[name] = {'player': _box(p, 130, 130)}
        for label, o, w, h, dy in objs:
            k, i = label, 2
            while k in boxes[name]:
                k, i = f'{label}#{i}', i + 1
            boxes[name][k] = _box(o, w, h, dy)
    with open(os.path.join(out, 'boxes.json'), 'w', encoding='utf-8') as f:
        json.dump(boxes, f, ensure_ascii=False, indent=1)
    close_canvas()
    print('ok', out)


# ----- 비교판 (원래 크기로 자른다) -----
BG = (20, 20, 24)
try:
    FONT = ImageFont.truetype('malgun.ttf', 18)
except OSError:
    FONT = ImageFont.load_default()


def _crop(folder, scene, box, pad=40, with_player=True):
    im = Image.open(os.path.join(folder, f'q1_{scene}.png'))
    b = json.load(open(os.path.join(folder, 'boxes.json'), encoding='utf-8'))[scene]
    if box not in b and any(k.startswith(box) for k in b):
        box = next(k for k in b if k.startswith(box))
    if with_player and box.startswith('pedestal'):                 # 진열대가 여럿이면 주인공에 가장 가까운 것
        px = (b['player'][0] + b['player'][2]) / 2
        box = min((k for k in b if k.startswith(box.split('#')[0])), key=lambda k: abs((b[k][0] + b[k][2]) / 2 - px) + abs(b[k][3] - b['player'][3]))   # 가로 + 발 높이 차
    l, t, r, btm = b[box]
    if with_player:
        pl = b['player']
        l, t, r, btm = min(l, pl[0]), min(t, pl[1]), max(r, pl[2]), max(btm, pl[3])
    return im.crop((max(0, l - pad), max(0, t - pad), min(W, r + pad), min(H, btm + pad // 2)))


def _crop_obj(folder, scene, box):
    """물건 둘레만 (진열대는 주인공에 가장 가까운 것)."""
    b = json.load(open(os.path.join(folder, 'boxes.json'), encoding='utf-8'))[scene]
    if box.startswith('pedestal'):
        px = (b['player'][0] + b['player'][2]) / 2
        box = min((k for k in b if k.startswith(box)), key=lambda k: abs((b[k][0] + b[k][2]) / 2 - px) + abs(b[k][3] - b['player'][3]))   # 가로 + 발 높이 차
    return _crop(folder, scene, box, 12, False)


def row_board(rows, path, label_w=210):
    """[(이름표, [그림...])] -> 한 줄에 하나씩."""
    pad = 10
    w = label_w + max(sum(im.width + pad for im in ims) for _l, ims in rows) + pad
    h = sum(max(im.height for im in ims) + pad for _l, ims in rows) + pad
    board = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(board)
    y = pad
    for label, ims in rows:
        d.text((pad, y + 4), label, fill=(230, 230, 230), font=FONT)
        x = label_w
        for im in ims:
            board.paste(im, (x, y))
            x += im.width + pad
        y += max(im.height for im in ims) + pad
    board.save(path)
    print('saved', path, board.size)


AUDIT = [   # (이름표, 장면, 둘레 이름)
    ('무기 걸이 (코드 그림)', 'hideout_armory', 'armory'),
    ('연습장 표지판 (코드 그림)', 'hideout_practice', 'practice'),
    ('상자 (코드 그림)', 'slum_crate', 'crate'),
    ('부서지는 발판 금 (코드)', 'slum_crate', 'crumble'),
    ('증기 분출구 (코드 그림)', 'foundry_vent', 'vent'),
    ('감시 레이저 머리 (코드)', 'tower_laser', 'laser'),
    ('진열대 황금 (Codex)', 'slum_gold', 'pedestal_gold'),
    ('진열대 정비 (Codex)', 'slum_shop', 'pedestal_shop'),
    ('이벤트 방 (PixelLab)', 'slum_event', 'event_spring'),
]


def audit(folder, path):
    b = json.load(open(os.path.join(folder, 'boxes.json'), encoding='utf-8'))
    rows = []
    for label, scene, box in AUDIT:
        keys = [k for k in b.get(scene, {}) if k == box or k.startswith(box)]
        if not keys:
            continue
        rows.append((label, [_crop(folder, scene, keys[0])]))
    full = [Image.open(os.path.join(folder, f'q1_{s}.png')) for s in ('hideout_armory', 'hideout_left', 'foundry_boss')]
    rows.append(('은신처 (무기 걸이 쪽)', [full[0].crop((0, 380, 1920, 1080))]))
    rows.append(('은신처 (왼쪽, 움직이는 소품)', [full[1].crop((0, 380, 1920, 1080))]))
    rows.append(('공장 보스방 (지형 소품)', [full[2].crop((0, 380, 1920, 1080))]))
    row_board(rows, path)


def board(before, after, out):
    os.makedirs(out, exist_ok=True)
    pairs = [('armory', 'hideout_armory', 'armory'), ('practice', 'hideout_practice', 'practice'),
             ('crate', 'slum_crate', 'crate'), ('vent', 'foundry_vent', 'vent'), ('laser', 'tower_laser', 'laser'),
             ('pedestal_gold', 'slum_gold', 'pedestal_gold'), ('pedestal_shop', 'slum_shop', 'pedestal_shop')]
    for name, scene, box in pairs:
        try:
            a, z = _crop(before, scene, box), _crop(after, scene, box)
        except (KeyError, FileNotFoundError):
            continue
        if name == 'laser':                                         # 레이저는 천장에 달려 주인공과 멀다: 원래 크기도 머리 둘레만
            a, z = _crop(before, scene, box, 60, False), _crop(after, scene, box, 60, False)
        obj = [_crop_obj(f, scene, box) for f in (before, after)]   # 4배는 물건 둘레만
        big = [im.resize((im.width * 4, im.height * 4), Image.NEAREST) for im in obj]
        row_board([('전 (원래 크기)', [a]), ('후 (원래 크기)', [z]), ('전 4배', [big[0]]), ('후 4배', [big[1]])],
                  os.path.join(out, f'Q1_{name}.png'), label_w=150)
    anv = [Image.open(os.path.join(f, 'q1_hideout_left.png')).crop((380, 740, 700, 910)) for f in (before, after)]   # 모루 + 정비사
    row_board([('전 (원래 크기)', [anv[0]]), ('후 (원래 크기)', [anv[1]]),
               ('전 4배', [anv[0].crop((0, 40, 160, 170)).resize((640, 520), Image.NEAREST)]),
               ('후 4배', [anv[1].crop((0, 40, 160, 170)).resize((640, 520), Image.NEAREST)])],
              os.path.join(out, 'Q1_anvil.png'), label_w=150)
    brz = [Image.open(os.path.join(f, 'q1_hideout_armory.png')).crop((1460, 740, 1860, 910)) for f in (before, after)]   # 기록관 + 화로
    row_board([('전 (원래 크기)', [brz[0]]), ('후 (원래 크기)', [brz[1]]),
               ('전 4배', [brz[0].crop((240, 20, 400, 170)).resize((640, 600), Image.NEAREST)]),
               ('후 4배', [brz[1].crop((240, 20, 400, 170)).resize((640, 600), Image.NEAREST)])],
              os.path.join(out, 'Q1_brazier.png'), label_w=150)
    hide = [Image.open(os.path.join(f, 'q1_hideout_armory.png')) for f in (before, after)]
    row_board([('전', [hide[0]]), ('후', [hide[1]])], os.path.join(out, 'Q1_hideout.png'), label_w=60)
    rows = []
    for scene in ('slum_crate', 'foundry_vent', 'tower_laser', 'slum_shop'):
        ims = [Image.open(os.path.join(f, f'q1_{scene}.png')) for f in (before, after)]
        rows += [(f'{scene} 전', [ims[0]]), (f'{scene} 후', [ims[1]])]
    row_board(rows, os.path.join(out, 'Q1_rooms.png'), label_w=160)


if __name__ == '__main__':
    if sys.argv[1] == '--board':
        board(*sys.argv[2:5])
    elif sys.argv[1] == '--audit':
        audit(*sys.argv[2:4])
    else:
        shoot(sys.argv[1])
