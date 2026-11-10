# 자동 점검과 스크린샷 도구가 함께 쓰는 시뮬레이션 도우미.
# 사람 대신 이벤트를 만들어 넣고, 게임 루프를 고정 프레임(1/60초)으로 돌린다.
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

DT = 1.0 / 60.0


def open_game(window):
    if not window:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'   # 창 없이 실행 (그리기는 하지만 화면에 안 보임)
    from pico2d import open_canvas
    import config
    open_canvas(config.WIDTH, config.HEIGHT)


class FakeEvent:
    def __init__(self, type, key=None, x=0, y=0, button=0):
        self.type, self.key, self.x, self.y, self.button = type, key, x, y, button


def key_down(key):
    from pico2d import SDL_KEYDOWN
    send(FakeEvent(SDL_KEYDOWN, key))


def key_up(key):
    from pico2d import SDL_KEYUP
    send(FakeEvent(SDL_KEYUP, key))


def mouse_move(x, y):
    # x, y 는 게임 좌표(좌하단 원점). SDL 이벤트는 좌상단 원점이라 뒤집어서 넣는다.
    from pico2d import SDL_MOUSEMOTION
    import config
    send(FakeEvent(SDL_MOUSEMOTION, x=int(x), y=config.HEIGHT - 1 - int(y)))


def click(button=1):
    from pico2d import SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP
    send(FakeEvent(SDL_MOUSEBUTTONDOWN, button=button))
    send(FakeEvent(SDL_MOUSEBUTTONUP, button=button))


def send(event):
    import play_mode
    play_mode.dispatch(event)


def step(frames=1, before=None, dt=DT):
    import game_framework
    import play_mode
    for i in range(frames):
        if before:
            before(i)
        game_framework.frame_time = dt
        play_mode.update()
        play_mode.render()
