"""화면 후처리 (2026-11-24 사용자 요청: 오버로드 때 기운이 모이며 어두워졌다가 터지고, 블러와 함께 공간이 왜곡되는 느낌).

pico2d에는 흐림·왜곡 효과가 없어서, 연출하는 짧은 동안만 세계 층을 화면 대신 그림판(렌더 타깃 텍스처)에 그린 뒤 그 그림판을
화면에 다시 그린다:
  - 당김·밀림(zoom): 그림판을 연출 중심으로 조금 키워 그린다 (기운이 모일 때 빨려드는 느낌, 터질 때 튕겨 나오는 느낌)
  - 블러(blur): 같은 그림판을 조금씩 더 키워 옅게 여러 번 겹친다 = 중심에서 퍼지는 방사 블러
  - 왜곡(wobble): 가로 띠마다 좌우로 조금씩 밀어 그린다 (중심 높이에서 가장 크다) = 공간이 일렁이는 느낌
UI 층은 그림판 밖(화면)에 그대로 그린다. 연출이 없으면 아무것도 하지 않는다 (평소 그리기 경로 그대로).
픽셀 규칙의 '확대 금지'는 평소 그림에 대한 것이고, 이것은 0.8초 안팎의 화면 연출이다. 설정의 '번쩍임 줄이기'면 켜지 않는다.
"""
import math
import time

import config

_tex = None
_keys = []            # [(시각, zoom, blur, wobble)] 실제 시간 기준
_start = 0.0
_center = (config.SCREEN_W // 2, config.SCREEN_H // 2)     # 화면 좌표 (왼쪽 아래 기준)
_drawing = False


def play(keys, cx, cy):
    """연출을 시작한다. keys: [(t초, zoom, blur 0~1, wobble px)] (사이는 곧게 잇는다). (cx, cy)는 화면 좌표의 중심."""
    global _keys, _start, _center
    import options
    if options.reduce_flash:
        return
    _keys, _start, _center = list(keys), time.monotonic(), (cx, cy)


def stop():
    global _keys
    _keys = []


def state():
    """지금의 (zoom, blur, wobble, 지난 시간). 연출 중이 아니면 None."""
    if not _keys:
        return None
    t = time.monotonic() - _start
    if t >= _keys[-1][0]:
        stop()
        return None
    for (t0, *a), (t1, *b) in zip(_keys, _keys[1:]):
        if t0 <= t < t1:
            k = (t - t0) / max(1e-6, t1 - t0)
            return tuple(x + (y - x) * k for x, y in zip(a, b)) + (t,)
    return tuple(_keys[0][1:]) + (t,)


def begin():
    """세계 층을 그리기 직전에 부른다: 연출 중이면 그림판에 그리게 돌린다."""
    global _tex, _drawing
    _drawing = False
    if state() is None:
        return
    import pico2d.pico2d as p2
    from sdl2 import (SDL_BLENDMODE_BLEND, SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_TARGET, SDL_CreateTexture, SDL_RenderClear,
                      SDL_SetRenderDrawColor, SDL_SetRenderTarget, SDL_SetTextureBlendMode)
    if _tex is None:
        _tex = SDL_CreateTexture(p2.renderer, SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_TARGET, config.SCREEN_W, config.SCREEN_H)
        if not _tex:
            stop()
            return
        SDL_SetTextureBlendMode(_tex, SDL_BLENDMODE_BLEND)
    if SDL_SetRenderTarget(p2.renderer, _tex) != 0:
        stop()
        return
    SDL_SetRenderDrawColor(p2.renderer, 0, 0, 0, 255)
    SDL_RenderClear(p2.renderer)
    _drawing = True


def end():
    """세계 층을 다 그린 뒤(UI 전에) 부른다: 그림판을 화면에 당김·블러·왜곡을 걸어 그린다."""
    global _drawing
    if not _drawing:
        return
    _drawing = False
    import pico2d.pico2d as p2
    from sdl2 import SDL_Rect, SDL_RenderCopy, SDL_SetRenderTarget, SDL_SetTextureAlphaMod
    SDL_SetRenderTarget(p2.renderer, None)
    zoom, blur, wobble, t = state() or (1.0, 0.0, 0.0, 0.0)
    w, h = config.SCREEN_W, config.SCREEN_H
    cx, sy = _center[0], h - _center[1]                       # SDL은 y가 아래로

    def copy(scale, alpha):
        SDL_SetTextureAlphaMod(_tex, max(0, min(255, int(alpha * 255))))
        SDL_RenderCopy(p2.renderer, _tex, None, SDL_Rect(int(cx - cx * scale), int(sy - sy * scale), int(w * scale) + 1, int(h * scale) + 1))

    zoom = max(1.0, zoom)                                     # 1보다 작으면 가장자리가 빈다
    copy(zoom, 1.0)
    if wobble >= 1.0:                                         # 왜곡: 가로 띠를 좌우로 민다 (중심 높이에서 가장 크다)
        strip = 8
        SDL_SetTextureAlphaMod(_tex, 255)
        for y0 in range(0, h, strip):
            fall = math.exp(-((y0 - sy) / 300.0) ** 2)
            dx = wobble * fall * math.sin(y0 * 0.05 + t * 46.0)
            if abs(dx) < 1.0:
                continue
            src = SDL_Rect(0, y0, w, strip)
            dst = SDL_Rect(int(cx - cx * zoom + dx), int(sy + (y0 - sy) * zoom), int(w * zoom) + 1, int(strip * zoom) + 1)
            SDL_RenderCopy(p2.renderer, _tex, src, dst)
    if blur > 0.02:                                           # 방사 블러: 조금씩 더 키워 옅게 겹친다
        for i in range(1, 6):
            copy(zoom * (1.0 + blur * 0.022 * i), 0.24)
    SDL_SetTextureAlphaMod(_tex, 255)
