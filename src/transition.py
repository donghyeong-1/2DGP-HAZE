"""화면 전환 연출 (2026-11-21 퀄리티 계획 4-3). 새 방·새 화면이 검은 화면에서 점묘로 걷히며 드러난다.

반투명 없이 켜짐·꺼짐 점만 쓴다(픽셀 규칙): assets/ui/wipe_01~15.png(128x128 베이어 타일, 번호가 클수록 촘촘)를
화면에 깔고, LEVELS(16)는 화면 전체를 칠한다. tools/make_atmosphere.py가 타일을 만든다.
- reveal(): 지금부터 DURATION초 동안 걷힌다 (방 입장 stage.enter_room, 타이틀·사망·탈출·크레딧 enter).
- draw(): 각 화면의 draw가 update_canvas 바로 앞에서 부른다 (가장 위에 그린다). reveal부터 흐른 실제 시간으로
  걷힌다(게임 루프 밖의 캡처 도구에서도 멈추지 않게). tick(dt)은 테스트용.
"""
import math
import time

DURATION = 0.3
LEVELS = 16
TILE = 128
INK = (6, 8, 18)

_left = 0.0
_start = 0.0
_duration = DURATION


def reveal(duration=DURATION):
    global _left, _start, _duration
    _left = _duration = duration
    _start = time.perf_counter()


def tick(dt):
    global _left
    _left = max(0.0, _left - dt)


def level():
    """지금 가리는 정도: 0(다 보임) ~ LEVELS(다 가림)."""
    return max(0, min(LEVELS, math.ceil(LEVELS * _left / DURATION - 1e-9)))


def draw():
    global _left
    _left = max(0.0, min(_left, _duration - (time.perf_counter() - _start)))
    lv = level()
    if lv <= 0:
        return
    import assets
    import config
    old = assets.draw_offset
    assets.draw_offset = (0, 0)
    try:
        if lv >= LEVELS:
            assets.draw_rect_color(0, 0, config.SCREEN_W, config.SCREEN_H, INK)
            return
        img = assets.image(f'ui/wipe_{lv:02d}.png')
        for y in range(0, config.SCREEN_H, TILE):
            for x in range(0, config.SCREEN_W, TILE):
                assets.draw_clip(img, 0, 0, TILE, TILE, x, y)
    finally:
        assets.draw_offset = old
