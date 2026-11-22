"""키 설정 (2026-11-21 퀄리티 계획 2-6). 키보드 동작마다 키 두 칸(기본·보조)을 둔다.

- 기본 칸은 비울 수 없고, 보조 칸은 비울 수 있다.
- 이미 다른 동작이 쓰는 키를 넣으면 두 칸이 맞바뀐다 (한 키가 두 동작을 하지 않게).
  맞바꾼 결과 어떤 동작의 기본 칸이 비면 보조 칸 키를 올리고, 올릴 키도 없으면 바꾸지 않는다.
- Esc(일시정지)와 F1~F5(도움말·개발용)는 넣을 수 없다. 마우스(좌클릭 공격·우클릭 대시)는 바꾸지 않는다.
- 값은 설정 파일(options, ~/.haze_options.json)의 'keys'에 함께 저장한다. 이상한 값이면 기본을 쓴다.
키 코드는 SDL 키 코드(정수)다. 화면에는 key_name / label로 짧은 이름을 보인다.
"""
import sdl2

# (동작 id, 화면 이름, 기본 키 두 칸). 이 순서대로 키 설정 화면에 보인다
ACTIONS = (
    ('left', '왼쪽 이동', (sdl2.SDLK_a, None)),
    ('right', '오른쪽 이동', (sdl2.SDLK_d, None)),
    ('down', '아래 (발판 내려가기)', (sdl2.SDLK_s, None)),
    ('jump', '점프', (sdl2.SDLK_SPACE, sdl2.SDLK_w)),
    ('dash', '대시', (sdl2.SDLK_LSHIFT, None)),
    ('enhance', '강화 일격', (sdl2.SDLK_e, None)),
    ('interact', '상호작용 (구매·말 걸기)', (sdl2.SDLK_f, None)),
    ('swap', '무기 바꾸기', (sdl2.SDLK_q, None)),
    ('weapon1', '무기 1번', (sdl2.SDLK_1, None)),
    ('weapon2', '무기 2번', (sdl2.SDLK_2, None)),
)
IDS = tuple(a for a, _n, _k in ACTIONS)
NAMES = {a: n for a, n, _k in ACTIONS}
DEFAULTS = {a: list(k) for a, _n, k in ACTIONS}
RESERVED = {sdl2.SDLK_ESCAPE, sdl2.SDLK_F1, sdl2.SDLK_F2, sdl2.SDLK_F3, sdl2.SDLK_F4, sdl2.SDLK_F5}
SHORT_NAMES = {
    sdl2.SDLK_LSHIFT: 'Shift', sdl2.SDLK_RSHIFT: 'R Shift', sdl2.SDLK_LCTRL: 'Ctrl', sdl2.SDLK_RCTRL: 'R Ctrl',
    sdl2.SDLK_LALT: 'Alt', sdl2.SDLK_RALT: 'R Alt', sdl2.SDLK_SPACE: 'Space', sdl2.SDLK_RETURN: 'Enter',
    sdl2.SDLK_TAB: 'Tab', sdl2.SDLK_BACKSPACE: 'Backspace', sdl2.SDLK_CAPSLOCK: 'Caps',
    sdl2.SDLK_UP: '↑', sdl2.SDLK_DOWN: '↓', sdl2.SDLK_LEFT: '←', sdl2.SDLK_RIGHT: '→',
}

_keys = {a: list(k) for a, k in DEFAULTS.items()}


def reset():
    """기본 키로 되돌린다 (저장하지 않는다, 테스트용)."""
    global _keys
    _keys = {a: list(k) for a, k in DEFAULTS.items()}


def reset_defaults():
    """설정 화면의 '기본값으로': 되돌리고 저장한다."""
    reset()
    _save()


def keys(action):
    return tuple(_keys[action])


def action_for(key):
    """이 키가 하는 동작 id. 아무것도 아니면 None."""
    for a in IDS:
        if key in _keys[a]:
            return a
    return None


def _where(key):
    for a in IDS:
        for slot, k in enumerate(_keys[a]):
            if k == key:
                return a, slot
    return None


def _fix_primary(table):
    """기본 칸이 빈 동작은 보조 칸을 올린다. 그래도 빈 동작이 있으면 False."""
    for a in IDS:
        if table[a][0] is None:
            table[a] = [table[a][1], None]
        if table[a][0] is None:
            return False
    return True


def bind(action, slot, key):
    """action의 slot(0 기본, 1 보조) 칸에 key를 넣는다. 넣었으면 True (바로 저장)."""
    global _keys
    if key is None or key in RESERVED:
        return False
    table = {a: list(k) for a, k in _keys.items()}
    old = table[action][slot]
    other = _where(key)
    table[action][slot] = key
    if other is not None and other != (action, slot):
        table[other[0]][other[1]] = old             # 맞바꾼다
    if not _fix_primary(table):
        return False
    _keys = table
    _save()
    return True


def clear(action, slot):
    """보조 칸을 비운다. 기본 칸은 비우지 않는다."""
    if slot == 1 and _keys[action][1] is not None:
        _keys[action][1] = None
        _save()


def key_name(key):
    """화면에 보일 짧은 키 이름."""
    if key is None:
        return '-'
    if key in SHORT_NAMES:
        return SHORT_NAMES[key]
    try:
        name = sdl2.SDL_GetKeyName(key).decode('utf-8', 'replace')
    except Exception:            # noqa: BLE001 (이름을 못 얻어도 게임은 계속)
        name = ''
    return name.upper() if len(name) == 1 else (name or '?')


def label(action, first=False):
    """안내 글자: 'Space/W'. first면 기본 칸만."""
    ks = [k for k in _keys[action] if k is not None]
    if first:
        ks = ks[:1]
    return '/'.join(key_name(k) for k in ks)


def to_json():
    return {a: list(_keys[a]) for a in IDS}


def load_json(data):
    """설정 파일의 값을 읽는다. 동작마다 검사하고, 겹치는 키가 있으면 모두 기본으로 둔다."""
    global _keys
    if not isinstance(data, dict):
        return
    table = {a: list(k) for a, k in DEFAULTS.items()}
    for a in IDS:
        v = data.get(a)
        if not (isinstance(v, list) and len(v) == 2):
            continue
        if not all(k is None or (type(k) is int and k not in RESERVED) for k in v) or v[0] is None:
            continue
        table[a] = list(v)
    used = [k for a in IDS for k in table[a] if k is not None]
    if len(used) != len(set(used)):
        return
    _keys = table


def _save():
    import options
    options.save()
