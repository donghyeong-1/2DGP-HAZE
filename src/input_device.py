"""마지막으로 쓴 입력 장치 (N1-3, 2026-11-27). 키 안내가 이 장치를 따른다: 키보드·마우스면 키 이름, 게임패드면 패드 버튼 이름.

- 패드: 버튼을 새로 누르거나 스틱을 PAD_STICK보다 크게 기울이면. 이동 데드존(gamepad.DEADZONE 0.3)보다 크게 잡아
  손을 얹은 스틱의 흔들림으로는 바뀌지 않는다.
- 키보드: 키를 누르거나 마우스 버튼을 누르거나 마우스를 한 번에 MOUSE_MOVE px 이상 움직이면.
  패드가 메뉴에 넣는 가짜 키 이벤트(gamepad._push_key)는 창 번호가 0이라 키보드로 치지 않는다.
패드 버튼 이름은 지금 패드 배치를 따른다: 플레이 gamepad.PLAY_BUTTONS(A 점프, B·LT 대시, X 공격, RB·RT 강화, LB 교체, Y 상호작용,
Start 일시정지, 왼쪽 스틱·십자 이동, 오른쪽 스틱 조준), 메뉴 A 확인·B 뒤로·십자·스틱 이동. pico2d와 무관한 순수 로직 + SDL 엿보기(scan).
"""
import math

KEYBOARD, PAD = 'keyboard', 'pad'
current = KEYBOARD
PAD_STICK = 0.6          # 패드로 보는 스틱 기울기
MOUSE_MOVE = 6           # 키보드·마우스로 보는 마우스 한 번 이동 (px, 가로+세로)
_pad_prev = set()

# 동작 -> 패드 버튼 이름 (keybinds.label이 패드일 때 쓴다). 물약은 패드 버튼이 없다
PAD_LABELS = {'left': '←', 'right': '→', 'down': '↓', 'jump': 'A', 'dash': 'B', 'attack': 'X', 'enhance': 'RB',
              'swap': 'LB', 'weapon1': 'LB', 'weapon2': 'LB', 'interact': 'Y', 'potion': '-'}
# 메뉴 아래 키 안내: 키보드 글자 -> 패드 버튼. 여기에 없는 키(O·H·Q·G·Backspace 등 키보드 전용)는 패드일 때 안내에서 뺀다
MENU_KEYS = {'W S': '↑↓', 'A D': '←→', 'Enter': 'A', 'Space': 'A', 'Esc': 'B', '아무 키': 'A'}


def reset():
    """처음 상태 (키보드, 누른 패드 버튼 없음). 테스트용."""
    global current, _pad_prev
    current, _pad_prev = KEYBOARD, set()


def is_pad():
    return current == PAD


def use(device):
    global current
    current = device


def note_pad(state):
    """패드 상태(gamepad.PadState) 한 프레임. 새로 누른 버튼이나 크게 기울인 스틱이 있으면 패드."""
    global _pad_prev
    pressed = set(state.buttons) - _pad_prev
    _pad_prev = set(state.buttons)
    if pressed or math.hypot(state.lx, state.ly) > PAD_STICK or math.hypot(state.rx, state.ry) > PAD_STICK:
        use(PAD)


def note_event(kind, window_id=1, xrel=0, yrel=0):
    """SDL 이벤트 하나 (종류, 창 번호, 마우스 이동량). 진짜 키보드·마우스면 키보드."""
    import sdl2
    if kind == sdl2.SDL_KEYDOWN and window_id:
        use(KEYBOARD)
    elif kind == sdl2.SDL_MOUSEBUTTONDOWN:
        use(KEYBOARD)
    elif kind == sdl2.SDL_MOUSEMOTION and abs(xrel) + abs(yrel) >= MOUSE_MOVE:
        use(KEYBOARD)


def scan():
    """game_framework가 모드의 handle_events 전에 부른다: 큐의 이벤트를 꺼내지 않고 엿본다."""
    try:
        import ctypes
        import sdl2
    except ImportError:
        return
    sdl2.SDL_PumpEvents()
    buf = (sdl2.SDL_Event * 64)()
    n = sdl2.SDL_PeepEvents(buf, 64, sdl2.SDL_PEEKEVENT, sdl2.SDL_FIRSTEVENT, sdl2.SDL_LASTEVENT)
    for i in range(max(0, n)):
        ev = buf[i]
        if ev.type == sdl2.SDL_KEYDOWN:
            note_event(ev.type, ev.key.windowID)
        elif ev.type == sdl2.SDL_MOUSEBUTTONDOWN:
            note_event(ev.type)
        elif ev.type == sdl2.SDL_MOUSEMOTION:
            note_event(ev.type, xrel=ev.motion.xrel, yrel=ev.motion.yrel)
    del ctypes


def key(label):
    """키보드 글자 하나 -> 지금 장치의 이름 (패드인데 대응이 없으면 None)."""
    if not is_pad():
        return label
    return MENU_KEYS.get(label)


def footer(pairs):
    """[(키, 설명)] -> 지금 장치에 맞춘 목록. 패드면 패드 버튼으로 바꾸고 키보드 전용 키는 뺀다."""
    if not is_pad():
        return list(pairs)
    return [(MENU_KEYS[k], d) for k, d in pairs if k in MENU_KEYS]
