"""설정: 화면 흔들림 세기, 번쩍임 줄이기(접근성), 음악·효과음 크기, 해상도, 마우스 가두기, 키 설정(keybinds). pico2d와 무관한 순수 로직이다.
(해상도·마우스 가두기를 실제 창에 적용하는 일은 display.apply가 한다.)

값은 이번 실행 동안 유지되고, 바꿀 때마다 사용자 홈 폴더의 작은 파일(~/.haze_options.json)에 저장해
다음 실행에도 이어진다. 읽기·쓰기는 safe_io(깨지면 .bak에서 되살림). 읽을 수 없으면 기본값으로 동작한다 (게임은 멈추지 않는다).
"""
import os

import keybinds
import safe_io

SHAKE_LEVELS = (('끔', 0.0), ('약하게', 0.45), ('보통', 1.0))   # (이름, 흔들림 배율)
PATH = os.path.join(os.path.expanduser('~'), '.haze_options.json')

shake_level = 2           # SHAKE_LEVELS 번호 (기본: 보통)
reduce_flash = False      # True면 화면 섬광과 큰 폭발의 하얀 중심을 약하게 한다
VOLUME_MAX = 10
VOLUME_DEFAULT = 8         # 이 단계가 config의 기본 음량(MUSIC_VOLUME, SFX_VOLUME)이다
music_level = VOLUME_DEFAULT
sfx_level = VOLUME_DEFAULT
FLASH_SCALE = 0.25        # 번쩍임 줄이기를 켰을 때 화면 섬광 세기 배율
# 해상도 (이름, 창 너비, 높이). 0은 전체 화면(모니터 크기). 게임은 언제나 1920x1080 논리 화면에 그린다 (display.py)
RESOLUTIONS = (('1280x720', 1280, 720), ('1600x900', 1600, 900), ('1920x1080', 1920, 1080), ('전체 화면', 0, 0))
RESOLUTION_DEFAULT = 2
resolution = RESOLUTION_DEFAULT
show_hints = True         # 처음 하는 사람 안내판 (11/21 계획 2-5)
show_damage = True        # 피해 숫자 (11/21 타격감)
test_mode = False         # v7 테스트 모드: 무적, 게이지 유지, F6~F9 바로가기 (발표·점검용)
confine_mouse = False     # True면 마우스가 게임 창 밖으로 나가지 않는다 (조준하다 다른 모니터를 누르는 일 방지)
_loaded = False


def shake_mult():
    return SHAKE_LEVELS[shake_level][1]


def shake_name():
    return SHAKE_LEVELS[shake_level][0]


def flash_mult():
    return FLASH_SCALE if reduce_flash else 1.0


def resolution_name():
    return RESOLUTIONS[resolution][0]


def set_resolution(level):
    global resolution
    resolution = max(0, min(len(RESOLUTIONS) - 1, int(level)))
    save()


def toggle_hints():
    global show_hints
    show_hints = not show_hints
    save()


def toggle_damage():
    global show_damage
    show_damage = not show_damage
    save()


def toggle_test_mode():
    """저장하지 않는다: 켜 둔 채 잊지 않게 게임을 켤 때마다 꺼진 상태로 시작한다."""
    global test_mode
    test_mode = not test_mode


def toggle_confine():
    global confine_mouse
    confine_mouse = not confine_mouse
    save()


def volume(base, level):
    """config의 기본 음량(0~128)을 단계(0~10)에 맞춰 바꾼다. 기본 단계(8)면 그대로다."""
    return max(0, min(128, round(base * level / VOLUME_DEFAULT)))


def set_music(level):
    global music_level
    music_level = max(0, min(VOLUME_MAX, int(level)))
    save()


def set_sfx(level):
    global sfx_level
    sfx_level = max(0, min(VOLUME_MAX, int(level)))
    save()


def set_shake(level):
    global shake_level
    shake_level = max(0, min(len(SHAKE_LEVELS) - 1, int(level)))
    save()


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
    global shake_level, reduce_flash, music_level, sfx_level, resolution, confine_mouse, show_hints, show_damage, test_mode
    shake_level, reduce_flash, show_hints, show_damage, test_mode = 2, False, True, True, False
    music_level = sfx_level = VOLUME_DEFAULT
    resolution, confine_mouse = RESOLUTION_DEFAULT, False
    keybinds.reset()


def load(path=None):
    """저장된 값을 읽는다. 처음 한 번만 읽고, 이상한 값은 무시한다."""
    global shake_level, reduce_flash, music_level, sfx_level, resolution, confine_mouse, show_hints, show_damage, _loaded
    _loaded = True
    data = safe_io.read_json(path or PATH)            # 깨졌으면 .bak, 그것도 없으면 None (기본값)
    if not isinstance(data, dict):
        return
    try:
        level = int(data.get('shake_level', shake_level))
        if 0 <= level < len(SHAKE_LEVELS):
            shake_level = level
        reduce_flash = bool(data.get('reduce_flash', reduce_flash))
        for key in ('music_level', 'sfx_level'):
            v = int(data.get(key, globals()[key]))
            if 0 <= v <= VOLUME_MAX:
                globals()[key] = v
        v = int(data.get('resolution', resolution))
        if 0 <= v < len(RESOLUTIONS):
            resolution = v
        confine_mouse = bool(data.get('confine_mouse', confine_mouse))
        show_hints = bool(data.get('show_hints', show_hints))
        show_damage = bool(data.get('show_damage', show_damage))
        keybinds.load_json(data.get('keys'))
    except (OSError, ValueError, TypeError, AttributeError):
        pass


def save(path=None):
    return safe_io.write_json(path or PATH, {
        'shake_level': shake_level, 'reduce_flash': reduce_flash, 'music_level': music_level, 'sfx_level': sfx_level,
        'resolution': resolution, 'confine_mouse': confine_mouse, 'show_hints': show_hints, 'show_damage': show_damage,
        'keys': keybinds.to_json()})


def ensure_loaded():
    if not _loaded:
        load()
