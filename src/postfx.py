"""화면 후처리 (2026-11-24 사용자 요청): 큰 폭발의 순간 **배경까지 화면 전체가 렌즈처럼 휘고**, 가장자리에서 빨강·초록·파랑이
갈라지는 색 번짐(사용자가 준 INARI 화면처럼).

pico2d에는 이런 효과가 없어서, 연출하는 짧은 동안만 세계 층을 화면 대신 그림판(렌더 타깃 텍스처)에 그린 뒤 그 그림판을
**그물망(삼각형)으로 나눠** 화면에 다시 그린다 (SDL_RenderGeometry). 그물의 꼭짓점마다 그림판의 어느 자리를 가져올지를 옮겨서:
  - 볼록 렌즈(bulge): 중심 둘레가 부풀어 보인다 (기운이 모일 때 빨려드는 느낌, 터질 때 튕겨 나오는 느낌)
  - 굴절 고리(ring): 중심에서 퍼져 나가는 고리가 지나가는 자리의 배경이 밀렸다 돌아온다 (충격파가 공간을 일그러뜨리는 느낌)
  - 색 번짐(chroma): 빨강·초록·파랑을 따로 세 번, 조금씩 다르게 휘어 더한다 -> 가장자리와 고리에서 색이 갈라진다
UI 층은 그림판 밖(화면)에 그대로 그린다. 연출이 없으면 아무것도 하지 않는다 (평소 그리기 경로 그대로).
픽셀 규칙의 '확대·회전 금지'는 평소 그림에 대한 것이고, 이것은 1초 안팎의 화면 연출이다. 설정의 '번쩍임 줄이기'면 켜지 않는다.
"""
import math
import time

import config

COLS, ROWS = 32, 18                 # 그물 칸 수 (60px 칸)
_tex = None
_keys = []            # [(시각, bulge, chroma px, ring px)] 실제 시간 기준
_start = 0.0
_center = (config.SCREEN_W // 2, config.SCREEN_H // 2)     # 화면 좌표 (왼쪽 아래 기준)
_ring = None          # (시작 시각, 속도 px/s, 두께 px): 퍼져 나가는 굴절 고리
_drawing = False
_mesh = None          # (꼭짓점 배열 셋, 색인 배열)
_zoom = None          # O6 보스 막타 줌: (시작 시각, 화면 x, 화면 y). 볼록 렌즈와 달리 화면 전체를 같은 비율로 당긴다
zoom_requests = 0     # 받아들인 줌 요청 수 (테스트·확인용)


def reset_zoom():
    global _zoom, zoom_requests
    _zoom, zoom_requests = None, 0


def zoom(cx, cy, now=None):
    """화면(세계 층)을 (cx, cy) 쪽으로 고르게 당겼다가 돌아온다 (config.BOSS_KILL_ZOOM). 번쩍임 줄이기와 상관없이
    config.BOSS_KILL_ZOOM_ON으로만 끈다. 실제 시간으로 잰다 (타격 멈춤·슬로모션과 상관없이)."""
    global _zoom, zoom_requests
    if not getattr(config, 'BOSS_KILL_ZOOM_ON', False):
        return
    _zoom = (time.monotonic() if now is None else now, cx, cy)
    zoom_requests += 1


def zoom_scale(now=None):
    """지금 당긴 배율 (1 = 그대로). 빠르게 당기고(t_in) 부드럽게 돌아온다(t_out)."""
    global _zoom
    if _zoom is None:
        return 1.0
    a, t_in, t_out = config.BOSS_KILL_ZOOM
    t = (time.monotonic() if now is None else now) - _zoom[0]
    if t < 0:
        return 1.0
    if t < t_in:
        k = t / t_in
        return 1.0 + a * (1.0 - (1.0 - k) ** 2)
    if t < t_in + t_out:
        k = (t - t_in) / t_out
        return 1.0 + a * (1.0 - k * k * (3 - 2 * k))
    _zoom = None
    return 1.0


def boss_kill(boss):
    """보스를 쓰러뜨렸다: 그 보스 쪽으로 줌 (보스마다 한 번). 일반 적은 부르지 않는다."""
    if getattr(boss, '_kill_zoomed', False):
        return
    boss._kill_zoomed = True
    import camera
    cx, cy = getattr(boss, 'center', (boss.x, boss.y))
    zoom(*camera.to_screen(cx, cy))


def play(keys, cx, cy, ring=None):
    """연출을 시작한다. keys: [(t초, bulge 0~0.5, chroma px, ring px)] (사이는 곧게 잇는다). (cx, cy)는 화면 좌표의 중심.
    ring=(t0, 속도, 두께)를 주면 t0부터 고리가 퍼져 나가며 지나가는 자리를 ring px만큼 굴절시킨다."""
    global _keys, _start, _center, _ring
    import options
    if options.reduce_flash:
        return
    _keys, _start, _center, _ring = list(keys), time.monotonic(), (cx, cy), ring


def pulse(cx, cy, strength=1.0, life=0.5):
    """한 번 터지는 굴절: 볼록하게 부풀었다 꺼지고, 색이 갈라지고, 고리가 퍼진다 (처형·궁극기 마무리)."""
    s = strength
    play([(0.0, 0.0, 0.0, 0.0), (0.04, 0.16 * s, 14 * s, 26 * s), (life * 0.5, 0.04 * s, 7 * s, 16 * s), (life, 0.0, 0.0, 0.0)],
         cx, cy, ring=(0.0, 2600.0, 220.0))


def stop():
    global _keys
    _keys = []


def state():
    """지금의 (bulge, chroma, ring, 지난 시간). 연출 중이 아니면 None."""
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
    if state() is None and zoom_scale() == 1.0:
        return
    import pico2d.pico2d as p2
    import sdl2
    if not hasattr(sdl2, 'SDL_RenderGeometry'):
        stop()
        return
    if _tex is None:
        _tex = sdl2.SDL_CreateTexture(p2.renderer, sdl2.SDL_PIXELFORMAT_RGBA8888, sdl2.SDL_TEXTUREACCESS_TARGET,
                                      config.SCREEN_W, config.SCREEN_H)
        if not _tex:
            stop()
            return
    if sdl2.SDL_SetRenderTarget(p2.renderer, _tex) != 0:
        stop()
        return
    sdl2.SDL_SetRenderDrawColor(p2.renderer, 0, 0, 0, 255)
    sdl2.SDL_RenderClear(p2.renderer)
    _drawing = True


def _build_mesh():
    """그물의 꼭짓점 배열(빨강·초록·파랑용 셋)과 삼각형 색인. 자리는 고정이고, 가져올 그림판 자리(tex_coord)만 프레임마다 바꾼다."""
    import ctypes

    import sdl2
    n = (COLS + 1) * (ROWS + 1)
    sets = []
    for color in ((255, 0, 0), (0, 255, 0), (0, 0, 255)):
        verts = (sdl2.SDL_Vertex * n)()
        for j in range(ROWS + 1):
            for i in range(COLS + 1):
                v = verts[j * (COLS + 1) + i]
                v.position.x = i * config.SCREEN_W / COLS
                v.position.y = j * config.SCREEN_H / ROWS
                v.color.r, v.color.g, v.color.b, v.color.a = (*color, 255)
        sets.append(verts)
    idx = []
    for j in range(ROWS):
        for i in range(COLS):
            a = j * (COLS + 1) + i
            idx += [a, a + 1, a + COLS + 1, a + 1, a + COLS + 2, a + COLS + 1]
    return sets, (ctypes.c_int * len(idx))(*idx), len(idx), n


def end():
    """세계 층을 다 그린 뒤(UI 전에) 부른다: 그림판을 그물로 휘고 색을 갈라 화면에 그린다."""
    global _drawing, _mesh
    if not _drawing:
        return
    _drawing = False
    import pico2d.pico2d as p2
    import sdl2
    sdl2.SDL_SetRenderTarget(p2.renderer, None)
    bulge, chroma, ring_amp, t = state() or (0.0, 0.0, 0.0, 0.0)
    if _mesh is None:
        _mesh = _build_mesh()
    sets, idx, n_idx, n = _mesh
    w, h = config.SCREEN_W, config.SCREEN_H
    zs = zoom_scale()                                         # O6 보스 막타 줌: 그림판의 가운데 쪽 자리를 가져와 고르게 커 보인다
    zx, zy = (_zoom[1], h - _zoom[2]) if _zoom is not None else (w / 2, h / 2)
    cx, cy = _center[0], h - _center[1]                       # SDL은 y가 아래로
    ring_r = ring_w = None
    if _ring is not None and t >= _ring[0] and ring_amp > 0.5:
        ring_r, ring_w = (t - _ring[0]) * _ring[1], _ring[2]
    # 꼭짓점마다 그림판에서 가져올 자리: 중심 방향으로 d만큼 당겨 온다 (당겨 오면 그 자리가 부풀어 보인다)
    base = []
    for j in range(ROWS + 1):
        y = j * h / ROWS
        for i in range(COLS + 1):
            x = i * w / COLS
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy) or 1.0
            ux, uy = dx / r, dy / r
            d = bulge * r * math.exp(-(r / 520.0) ** 2)       # 볼록 렌즈
            if ring_r is not None:
                q = (r - ring_r) / ring_w
                if -1.0 < q < 1.0:
                    d += ring_amp * math.cos(q * math.pi / 2) ** 2 * (1.0 if q < 0 else -0.6)   # 굴절 고리 (앞은 밀고 뒤는 당긴다)
            base.append((x, y, ux, uy, d, r))
    sdl2.SDL_SetTextureBlendMode(_tex, sdl2.SDL_BLENDMODE_ADD)   # 세 색을 더해 원래 그림이 된다
    sdl2.SDL_SetRenderDrawColor(p2.renderer, 0, 0, 0, 255)
    sdl2.SDL_RenderClear(p2.renderer)
    for verts, k in zip(sets, (1.0, 0.0, -1.0)):              # 빨강은 더, 파랑은 덜 휜다 = 색 번짐
        for v, (x, y, ux, uy, d, r) in zip(verts, base):
            e = d + k * chroma * (0.12 + min(1.6, r / 600.0)) + k * abs(d) * 0.1   # 중심(주인공)은 덜, 가장자리는 크게 갈라진다
            tx, ty = x - ux * e, y - uy * e
            if zs != 1.0:
                tx, ty = zx + (tx - zx) / zs, zy + (ty - zy) / zs
            v.tex_coord.x = min(1.0, max(0.0, tx / w))
            v.tex_coord.y = min(1.0, max(0.0, ty / h))
        sdl2.SDL_RenderGeometry(p2.renderer, _tex, verts, n, idx, n_idx)
    sdl2.SDL_SetTextureBlendMode(_tex, sdl2.SDL_BLENDMODE_BLEND)
