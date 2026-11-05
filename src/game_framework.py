"""모드(씬) 스택과 프레임 시간. 수업의 game_framework 구조를 따른다."""
import time

running = False
stack = []
frame_time = 0.0  # 직전 프레임 길이(초). 모든 이동·타이머에 곱한다.

MAX_FRAME_TIME = 0.05  # 창을 끌 때 등 큰 값이 들어오는 것을 막는다
TARGET_FRAME = 1 / 60  # 목표 프레임 길이(초)


def change_mode(mode):
    """현재 모드를 끝내고 새 모드로 바꾼다."""
    if stack:
        stack.pop().exit()
    stack.append(mode)
    mode.enter()


def push_mode(mode):
    """현재 모드를 멈추고(pause) 위에 새 모드를 쌓는다."""
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.enter()


def pop_mode():
    """맨 위 모드를 끝내고 아래 모드를 이어서(resume) 실행한다."""
    if stack:
        stack.pop().exit()
    if stack:
        stack[-1].resume()


def quit():
    global running
    running = False


def run(start_mode, max_seconds=None):
    """max_seconds가 있으면 그 시간이 지난 뒤 자동으로 끝낸다 (개발용 실행 확인)."""
    global running, frame_time
    running = True
    stack.clear()
    stack.append(start_mode)
    start_mode.enter()

    current = time.perf_counter()
    deadline = current + max_seconds if max_seconds else None
    while running and stack:
        if deadline and time.perf_counter() > deadline:
            break
        top = stack[-1]
        top.handle_events()
        top.update()
        top.draw()

        spare = TARGET_FRAME - (time.perf_counter() - current)
        if spare > 0:
            time.sleep(spare)  # 약 60fps로 제한해 CPU를 아낀다
        now = time.perf_counter()
        frame_time = min(now - current, MAX_FRAME_TIME)
        current = now

    while stack:
        stack.pop().exit()
