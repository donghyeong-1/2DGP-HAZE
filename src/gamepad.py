"""게임패드 (2026-11-21 퀄리티 계획 2-6). SDL GameController로 첫 번째 패드를 읽는다 (Xbox 배치, 꽂으면 바로 잡는다).

pico2d의 get_events는 패드 이벤트를 넘겨주지 않아서, 매 프레임 패드 상태를 직접 읽는다(tick).
- 플레이 중: 플레이어 함수를 바로 부른다(apply_play). Start만 Esc 키 이벤트를 넣어 일시정지 창을 연다.
- 메뉴: 화살표·Enter·Esc 키 이벤트를 SDL 큐에 넣어 기존 메뉴가 그대로 받게 한다(위아래는 누르고 있으면 반복).
  타이틀에서는 B(Esc = 게임 끄기)를 무시한다.
변환 규칙(Translator)은 SDL과 무관한 순수 로직이라 패드 없이 테스트한다(tests/test_gamepad.py).
"""
import math
from collections import namedtuple

DEADZONE = 0.3            # 왼쪽 스틱 이동 데드존 (-1~1)
AIM_DEADZONE = 0.35       # 오른쪽 스틱 조준 데드존
AIM_DISTANCE = 320        # 조준점: 플레이어에게서 이 거리(px) 앞
REPEAT_DELAY, REPEAT_EVERY = 0.35, 0.12   # 메뉴에서 방향을 누르고 있을 때 반복

PadState = namedtuple('PadState', 'buttons lx ly rx ry')     # 축은 -1~1, SDL처럼 아래·오른쪽이 +
PLAY_BUTTONS = {'a': 'jump', 'b': 'dash', 'x': 'attack', 'rb': 'enhance', 'lb': 'swap', 'y': 'interact', 'start': 'pause'}


def _direction(state, deadzone=DEADZONE):
    """왼쪽 스틱과 D패드를 합친 (x, y) 방향, 각 -1·0·1. y는 화면 기준 위가 +."""
    b = state.buttons
    x = (1 if 'dpright' in b or state.lx > deadzone else 0) - (1 if 'dpleft' in b or state.lx < -deadzone else 0)
    y = (1 if 'dpup' in b or state.ly < -deadzone else 0) - (1 if 'dpdown' in b or state.ly > deadzone else 0)
    return x, y


class Translator:
    """패드 상태 -> 플레이 동작 / 메뉴 키. 직전 상태를 기억해 누른 순간·뗀 순간을 가린다."""

    def __init__(self):
        self.prev = set()
        self.menu_dir = None
        self.repeat_left = 0.0

    def play(self, state, dt):
        held = {PLAY_BUTTONS[b] for b in state.buttons if b in PLAY_BUTTONS}
        before = {PLAY_BUTTONS[b] for b in self.prev if b in PLAY_BUTTONS}
        self.prev = set(state.buttons)
        x, y = _direction(state)
        aim = None
        mag = math.hypot(state.rx, state.ry)
        if mag > AIM_DEADZONE:
            aim = (state.rx / mag, -state.ry / mag)
        return {'move': x, 'down': y < 0, 'press': held - before, 'release': before - held, 'held': held, 'aim': aim}

    def menu(self, state, dt, on_title=False):
        keys = []
        pressed = set(state.buttons) - self.prev
        self.prev = set(state.buttons)
        if 'a' in pressed:
            keys.append('enter')
        if 'b' in pressed and not on_title:
            keys.append('escape')
        x, y = _direction(state, 0.5)
        d = 'up' if y > 0 else 'down' if y < 0 else 'right' if x > 0 else 'left' if x < 0 else None
        if d != self.menu_dir:
            self.menu_dir = d
            self.repeat_left = REPEAT_DELAY
            if d:
                keys.append(d)
        elif d:
            self.repeat_left -= dt
            if self.repeat_left <= 0:
                self.repeat_left += REPEAT_EVERY
                keys.append(d)
        return keys


def apply_play(player, actions, origin):
    """플레이 동작을 플레이어에 건다. origin = 플레이어 몸 중심의 화면 좌표 (조준점 계산)."""
    move, down = actions['move'], actions['down']
    pad_moved = getattr(player, 'pad_moving', False)
    if move != 0 or down or pad_moved:               # 패드가 움직일 때만 덮어쓴다 (키보드 A·D를 매 프레임 지우지 않게)
        player.left, player.right = move < 0, move > 0
        player.down = down
    player.pad_moving = move != 0 or down
    press, release = actions['press'], actions['release']
    if actions['aim'] is not None:
        ax, ay = actions['aim']
        player.mouse_screen = (int(origin[0] + ax * AIM_DISTANCE), int(origin[1] + ay * AIM_DISTANCE))
        player._sync_mouse()
    if 'jump' in press:
        player.request_jump()
    if 'jump' in release:
        player.release_jump()
    if 'dash' in press:
        player.request_dash()
    if 'enhance' in press:
        player.request_enhance()
    if 'swap' in press:
        player.swap_weapon()
    if 'interact' in press:
        player.interact_pressed = True
    if 'attack' in press:
        player.attack_held = True
        player.request_attack()
    if 'attack' in release:
        player.attack_held = False


# ----- SDL (실제 패드) -----
_controller = None
_translator = Translator()
_was_play = False
_BUTTONS = None


def _buttons_table():
    import sdl2
    return {'a': sdl2.SDL_CONTROLLER_BUTTON_A, 'b': sdl2.SDL_CONTROLLER_BUTTON_B, 'x': sdl2.SDL_CONTROLLER_BUTTON_X,
            'y': sdl2.SDL_CONTROLLER_BUTTON_Y, 'lb': sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER,
            'rb': sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, 'start': sdl2.SDL_CONTROLLER_BUTTON_START,
            'dpup': sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP, 'dpdown': sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN,
            'dpleft': sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT, 'dpright': sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT}


def read():
    """첫 번째 패드의 상태. 패드가 없으면 None (꽂으면 다음 프레임에 잡는다)."""
    global _controller, _BUTTONS
    try:
        import sdl2
    except ImportError:
        return None
    if _controller is not None and not sdl2.SDL_GameControllerGetAttached(_controller):
        sdl2.SDL_GameControllerClose(_controller)
        _controller = None
    if _controller is None:
        for i in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(i):
                _controller = sdl2.SDL_GameControllerOpen(i)
                break
        if _controller is None:
            return None
    if _BUTTONS is None:
        _BUTTONS = _buttons_table()
    c = _controller
    buttons = {name for name, code in _BUTTONS.items() if sdl2.SDL_GameControllerGetButton(c, code)}
    if sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT) > 16000:
        buttons.add('rb')                                   # RT도 강화
    if sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT) > 16000:
        buttons.add('b')                                    # LT도 대시

    def axis(code):
        return sdl2.SDL_GameControllerGetAxis(c, code) / 32767.0
    return PadState(buttons, axis(sdl2.SDL_CONTROLLER_AXIS_LEFTX), axis(sdl2.SDL_CONTROLLER_AXIS_LEFTY),
                    axis(sdl2.SDL_CONTROLLER_AXIS_RIGHTX), axis(sdl2.SDL_CONTROLLER_AXIS_RIGHTY))


def _push_key(name):
    import ctypes
    import sdl2
    code = {'up': sdl2.SDLK_UP, 'down': sdl2.SDLK_DOWN, 'left': sdl2.SDLK_LEFT, 'right': sdl2.SDLK_RIGHT,
            'enter': sdl2.SDLK_RETURN, 'escape': sdl2.SDLK_ESCAPE}[name]
    for kind in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
        ev = sdl2.SDL_Event()
        ev.type = kind
        ev.key.keysym.sym = code
        ev.key.repeat = 0
        sdl2.SDL_PushEvent(ctypes.byref(ev))


def tick(mode, dt):
    """game_framework가 매 프레임 부른다. 플레이 모드면 플레이어를, 그 밖의 모드면 메뉴를 움직인다."""
    global _was_play
    state = read()
    if state is None:
        return
    import play_mode
    is_play = mode is play_mode
    if is_play != _was_play:                                # 모드가 바뀌면 누르고 있던 버튼을 새로 누른 것으로 보지 않는다
        _translator.prev = set(state.buttons)
        _was_play = is_play
    if is_play and play_mode.player is not None:
        actions = _translator.play(state, dt)
        if 'pause' in actions['press']:
            _push_key('escape')
        p = play_mode.player
        cx, cy = p.center
        ox, oy = play_mode.camera.offset()
        apply_play(p, actions, (cx + ox, cy + oy))
        return
    import title_mode
    for key in _translator.menu(state, dt, on_title=mode is title_mode):
        _push_key(key)
