"""접근성 옵션: 화면 흔들림 세기, 번쩍임 줄이기. pico2d와 무관한 순수 로직이다.

값은 이번 실행 동안 유지되고, 바꿀 때마다 사용자 홈 폴더의 작은 파일(~/.haze_options.json)에 저장해
다음 실행에도 이어진다. 파일을 읽거나 쓸 수 없으면 조용히 기본값으로 동작한다 (게임은 멈추지 않는다).
"""
import json
import os

SHAKE_LEVELS = (('끔', 0.0), ('약하게', 0.45), ('보통', 1.0))   # (이름, 흔들림 배율)
PATH = os.path.join(os.path.expanduser('~'), '.haze_options.json')

shake_level = 2           # SHAKE_LEVELS 번호 (기본: 보통)
reduce_flash = False      # True면 화면 섬광과 큰 폭발의 하얀 중심을 약하게 한다
FLASH_SCALE = 0.25        # 번쩍임 줄이기를 켰을 때 화면 섬광 세기 배율
_loaded = False


def shake_mult():
    return SHAKE_LEVELS[shake_level][1]


def shake_name():
    return SHAKE_LEVELS[shake_level][0]


def flash_mult():
    return FLASH_SCALE if reduce_flash else 1.0


def cycle_shake(step=1):
    global shake_level
    shake_level = (shake_level + step) % len(SHAKE_LEVELS)
    save()


def toggle_flash():
    global reduce_flash
    reduce_flash = not reduce_flash
    save()


def reset():
    """기본값으로 되돌린다 (테스트용, 파일은 건드리지 않는다)."""
    global shake_level, reduce_flash
    shake_level, reduce_flash = 2, False


def load(path=None):
    """저장된 값을 읽는다. 처음 한 번만 읽고, 이상한 값은 무시한다."""
    global shake_level, reduce_flash, _loaded
    _loaded = True
    try:
        with open(path or PATH, encoding='utf-8') as f:
            data = json.load(f)
        level = int(data.get('shake_level', shake_level))
        if 0 <= level < len(SHAKE_LEVELS):
            shake_level = level
        reduce_flash = bool(data.get('reduce_flash', reduce_flash))
    except (OSError, ValueError, TypeError, AttributeError):
        pass


def save(path=None):
    try:
        with open(path or PATH, 'w', encoding='utf-8') as f:
            json.dump({'shake_level': shake_level, 'reduce_flash': reduce_flash}, f)
    except OSError:
        pass


def ensure_loaded():
    if not _loaded:
        load()
