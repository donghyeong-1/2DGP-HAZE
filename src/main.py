"""헤이즈 (Haze) 실행 파일. 실행: python src/main.py"""
import os

from pico2d import close_canvas, open_canvas

import config
import game_framework
import title_mode


def main():
    open_canvas(config.SCREEN_W, config.SCREEN_H)
    try:
        # 개발용: HAZE_MAX_SECONDS 환경 변수가 있으면 그 시간 뒤에 자동 종료한다 (실행 확인용)
        limit = float(os.environ.get('HAZE_MAX_SECONDS', '0')) or None
        game_framework.run(title_mode, limit)
    finally:
        close_canvas()


if __name__ == '__main__':
    main()
