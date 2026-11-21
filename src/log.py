"""오류 기록 (2026-11-21 퀄리티 계획 3-2). 사용자 폴더의 ~/.haze_log.txt에 시간과 함께 남긴다.

콘솔이 없는 실행 파일에서도 무슨 일이 있었는지 알 수 있게 한다. 기록하다 실패해도 게임은 멈추지 않는다.
파일이 MAX_BYTES를 넘으면 .old로 넘기고 새로 쓴다(최근 것 두 개만 남는다).
"""
import datetime
import os
import traceback

# HAZE_LOG_PATH: 테스트가 사용자 폴더 대신 임시 폴더에 쓰게 한다 (tests/run_all.py)
PATH = os.environ.get('HAZE_LOG_PATH') or os.path.join(os.path.expanduser('~'), '.haze_log.txt')
MAX_BYTES = 256 * 1024


def write(message):
    """한 줄(또는 여러 줄) 기록. 절대 예외를 내지 않는다."""
    try:
        line = f'[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n'
        if os.path.exists(PATH) and os.path.getsize(PATH) + len(line.encode('utf-8')) > MAX_BYTES:
            os.replace(PATH, PATH + '.old')
        with open(PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:            # noqa: BLE001 (기록 실패로 게임을 멈추지 않는다)
        pass


def error(context, exc=None):
    """예외와 추적 내용(traceback)을 기록한다. exc가 없으면 지금 처리 중인 예외."""
    try:
        if exc is None:
            detail = traceback.format_exc()
        else:
            detail = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    except Exception:            # noqa: BLE001
        detail = repr(exc)
    write(f'{context}\n{detail.rstrip()}')
