# 모드 스택과 메인 루프. 수업 LEC15 game_framework 에 프레임 시간(frame_time)만 더했다.
import time

running = False
stack = []
frame_time = 0.0               # 직전 프레임에 걸린 시간(초). 이동은 모두 이 값에 비례시킨다.
MAX_FRAME_TIME = 0.05          # 창을 끄는 등으로 멈췄다 돌아올 때 한 번에 너무 많이 움직이지 않게 한다


def change_mode(mode):
    if stack:
        stack.pop().finish()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack.pop().finish()
    if stack:
        stack[-1].resume()
    else:
        quit()


def quit():
    global running
    running = False


def run(start_mode):
    global running, stack, frame_time
    running = True
    stack = [start_mode]
    current = time.time()
    try:
        start_mode.init()
        while running:
            stack[-1].handle_events()
            stack[-1].update()
            stack[-1].render()
            time.sleep(0.01)
            now = time.time()
            frame_time = min(now - current, MAX_FRAME_TIME)
            current = now
    finally:
        while stack:
            stack.pop().finish()
        running = False
