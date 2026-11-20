"""창 크기(해상도)·전체 화면·마우스 가두기를 실제 SDL 창에 적용한다. (2026-11-20 사용자 요청)

게임은 언제나 1920x1080 '논리 화면'에 그린다(config.SCREEN_W/H). SDL_RenderSetLogicalSize가 이것을 창 크기에 맞춰
늘이거나 줄이고, 마우스 좌표도 논리 화면 좌표로 바꿔 준다. 그래서 해상도를 바꿔도 게임 코드는 그대로다.
1920x1080이 아닌 크기는 정수 배가 아니라서 픽셀 크기가 조금 고르지 않다(최근접 필터). 기본값은 1920x1080.
"""
import config
import options

SIZES = ((1920, 1080), (1600, 900), (1280, 720), (960, 540))   # 모니터에 들어가는 가장 큰 16:9를 고를 때 쓰는 목록


def window_size(name, desktop_w, desktop_h):
    """고른 해상도 이름과 모니터 크기로 (창 너비, 높이, 전체 화면인가)를 정한다. 순수 함수 (테스트)."""
    for label, w, h in options.RESOLUTIONS:
        if label != name:
            continue
        if w == 0:                                                   # 전체 화면: 모니터 크기 그대로
            return desktop_w, desktop_h, True
        if w <= desktop_w and h <= desktop_h:
            return w, h, False
        break
    for w, h in SIZES:                                               # 모니터보다 크면 들어가는 가장 큰 16:9
        if w <= desktop_w and h <= desktop_h:
            return w, h, False
    return SIZES[-1][0], SIZES[-1][1], False


def apply():
    """지금 설정(options.resolution, options.confine_mouse)을 창에 적용한다. 창이 없으면(테스트) 아무것도 하지 않는다."""
    import ctypes
    import sdl2
    import pico2d.pico2d as p2
    if getattr(p2, 'window', None) is None or getattr(p2, 'renderer', None) is None:
        return
    index = max(0, sdl2.SDL_GetWindowDisplayIndex(p2.window))
    mode = sdl2.SDL_DisplayMode()
    if sdl2.SDL_GetDesktopDisplayMode(index, ctypes.byref(mode)) != 0:
        mode.w, mode.h = config.SCREEN_W, config.SCREEN_H
    w, h, full = window_size(options.resolution_name(), mode.w, mode.h)
    sdl2.SDL_RenderSetLogicalSize(p2.renderer, config.SCREEN_W, config.SCREEN_H)
    if full:
        sdl2.SDL_SetWindowFullscreen(p2.window, sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
    else:
        sdl2.SDL_SetWindowFullscreen(p2.window, 0)
        sdl2.SDL_SetWindowSize(p2.window, w, h)
        pos = sdl2.SDL_WINDOWPOS_CENTERED_DISPLAY(index)
        sdl2.SDL_SetWindowPosition(p2.window, pos, pos)
    sdl2.SDL_SetWindowGrab(p2.window, sdl2.SDL_TRUE if options.confine_mouse else sdl2.SDL_FALSE)
