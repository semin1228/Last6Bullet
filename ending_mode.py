# 엔딩 (PRD 10장, 15-1). 은행의 두목을 쓰러뜨리면 play_mode 위에 올라온다(push_mode).
#   Enter / R / 클릭: 타이틀로   ESC: 종료
# 모은 현상금 합계를 보여 준다 (구역 평가는 여유 항목이라 아직 없다). 이미지는 나중에 res/ 로 바꾼다.
from pico2d import (SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_RETURN, SDLK_r,
                    clear_canvas, draw_circle, draw_rectangle, get_events, update_canvas)

import config
import game_framework
import title_mode
import ui

bounty = 0                     # 모은 현상금. play_mode 가 올리기 전에 정해 준다
big = small = None
time = 0.0


def init():
    global big, small, time
    big = ui.load(88)
    small = ui.load(30)
    time = 0.0


def finish():
    pass


def handle_events():
    for event in get_events():
        dispatch(event)


def dispatch(event):
    if event.type == SDL_QUIT or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_r):
        to_title()
    elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT and time > 1.0:
        to_title()             # 두목을 쓰러뜨린 클릭이 엔딩을 바로 넘기지 않게 1초는 무시한다


def to_title():
    game_framework.pop_mode()                  # 엔딩을 닫고 (아래의 play_mode 가 드러난다)
    game_framework.change_mode(title_mode)     # play_mode 도 닫으면서 타이틀로


def update():
    global time
    time += game_framework.frame_time


def render():
    clear_canvas()
    w, h = config.WIDTH, config.HEIGHT
    draw_rectangle(0, 0, w, h, 244, 196, 120, filled=True)            # 해 뜨는 하늘
    draw_circle(w // 2, 250, 150, 250, 226, 150, filled=True)         # 해
    draw_circle(w // 2, 250, 100, 255, 244, 200, filled=True)
    draw_rectangle(0, 0, w, 250, *config.COLOR_FLOOR, filled=True)    # 땅
    draw_rectangle(0, 246, w, 252, *config.COLOR_TABLE_EDGE, filled=True)
    ui.draw_center(big, w // 2, 600, 'TOWN SAVED', 88, config.COLOR_WALL)
    ui.draw_center(small, w // 2, 500, 'THE SUN RISES OVER A QUIET TOWN', 30, config.COLOR_WALL)
    ui.draw_center(small, w // 2, 170, 'TOTAL BOUNTY  $%d' % bounty, 30, config.COLOR_WALL)
    ui.draw_center(small, w // 2, 100, 'ENTER  TITLE      ESC  QUIT', 30, config.COLOR_TABLE_EDGE)
    update_canvas()


def pause():
    pass


def resume():
    pass
