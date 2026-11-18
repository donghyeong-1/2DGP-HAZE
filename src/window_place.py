"""게임 창을 원하는 모니터로 옮긴다. pico2d.open_canvas는 창을 기본 위치에 열기 때문에, 연 직후에 옮긴다.

모니터 번호는 1부터 센다 (1 = 주 모니터, 2 = 두 번째 모니터). 정하는 방법(앞이 우선):
  1) place_window(2)처럼 직접 넘긴다 (tools/capture.py --display 2)
  2) 환경 변수 HAZE_DISPLAY=2
없거나 그런 모니터가 없으면 옮기지 않는다(기본 위치 그대로). 창은 그 모니터 한가운데에 놓인다.
"""
import os


def wanted_display(display=None):
    """옮길 모니터 번호(1부터) 또는 None."""
    if display is None:
        value = os.environ.get('HAZE_DISPLAY', '').strip()
        if not value:
            return None
        try:
            display = int(value)
        except ValueError:
            return None
    return display if display >= 1 else None


def place_window(display=None):
    """open_canvas 다음에 부른다. 옮겼으면 그 모니터 번호, 아니면 None."""
    display = wanted_display(display)
    if display is None:
        return None
    import sdl2
    import pico2d.pico2d as p2
    if p2.window is None or display > sdl2.SDL_GetNumVideoDisplays():
        return None
    pos = sdl2.SDL_WINDOWPOS_CENTERED_DISPLAY(display - 1)
    sdl2.SDL_SetWindowPosition(p2.window, pos, pos)
    return display
