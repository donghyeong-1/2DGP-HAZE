"""헤이즈 (Haze) 실행 파일. 실행: python src/main.py

게임 도중 예외가 나면 기록 파일(log.PATH)에 추적 내용을 남기고 안내 창을 띄운 뒤 끝낸다(run_safely, 계획 3-2).
"""
import os
import sys

from pico2d import SDL_HINT_RENDER_SCALE_QUALITY, SDL_SetHint, close_canvas, open_canvas

import config
import display
import options
import game_framework
import log
import title_mode
from window_place import place_window


WINDOW_TITLE = '헤이즈 (HAZE)'


def _set_title():
    """창 제목을 게임 이름으로. pico2d는 get_events마다 제목을 'Pico2D Canvas ... FPS'로 덮어써서 그 함수를 끈다."""
    import pico2d.pico2d as p2
    from sdl2 import SDL_SetWindowTitle
    p2.print_fps = lambda: None
    SDL_SetWindowTitle(p2.window, WINDOW_TITLE.encode('utf-8'))


def main():
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, b'0')  # 최근접(nearest) 필터: 이미지를 뭉개지 않는다
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    place_window()                 # HAZE_DISPLAY=2 이면 두 번째 모니터에 띄운다
    _set_title()
    config.SOUND_ENABLED = True
    options.load()                 # 접근성 설정(흔들림·번쩍임)을 지난 실행에서 이어 받는다
    display.apply()                # 해상도·마우스 가두기 (창이 놓인 모니터 기준)
    import assets
    from pico2d import clear_canvas, update_canvas
    clear_canvas()                 # 미리 읽는 동안 빈 창 대신 '불러오는 중'
    assets.draw_rect_color(0, 0, config.SCREEN_W, config.SCREEN_H, (6, 9, 18))
    assets.draw_text(config.SCREEN_W // 2, config.SCREEN_H // 2, '불러오는 중', (130, 145, 175), center=True)
    update_canvas()
    assets.preload()               # 그림·효과음을 미리 읽어 첫 방·첫 이펙트에서 끊기지 않게 (약 0.7초)
    try:
        # 개발용: HAZE_MAX_SECONDS 환경 변수가 있으면 그 시간 뒤에 자동 종료한다 (실행 확인용)
        limit = float(os.environ.get('HAZE_MAX_SECONDS', '0')) or None
        # 개발용: HAZE_START=play 이면 타이틀을 건너뛰고 바로 은신처에서 시작한다 (실행 파일 점검용)
        first = title_mode
        if os.environ.get('HAZE_START') == 'play':
            import play_mode
            first = play_mode
        game_framework.run(first, limit)
    finally:
        close_canvas()


def _message_box(text):
    """오류 안내 창 (콘솔이 없는 실행 파일에서도 보인다). 창을 못 띄워도 조용히 넘어간다."""
    try:
        from sdl2 import SDL_MESSAGEBOX_ERROR, SDL_ShowSimpleMessageBox
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, WINDOW_TITLE.encode('utf-8'), text.encode('utf-8'), None)
    except Exception:            # noqa: BLE001
        pass


def run_safely(fn, report=_message_box):
    """fn을 실행한다. 예외가 나면 기록하고 안내한 뒤 1을 돌려준다(정상이면 0)."""
    try:
        fn()
        return 0
    except Exception as e:       # noqa: BLE001 (어떤 오류든 기록을 남기고 끝낸다)
        log.error('오류가 발생해 게임을 종료했습니다', e)
        report('오류가 발생해 게임을 종료했습니다.\n'
               '진행 내용은 마지막으로 저장한 시점까지 남아 있습니다.\n\n'
               f'오류 기록: {log.PATH}')
        return 1


if __name__ == '__main__':
    sys.exit(run_safely(main))
