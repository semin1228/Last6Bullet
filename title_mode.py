# 타이틀 화면 (PRD 15-1). 게임을 켜면 가장 먼저 나온다.
#   클릭 / Enter / Space: 1구역 시작   ESC: 종료
# 이미지는 나중에 res/ 에 넣어 바꾼다. 지금은 도형과 글자만 쓴다.
import math

from pico2d import (SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_RETURN,
                    SDLK_SPACE, clear_canvas, draw_circle, draw_rectangle, get_events, update_canvas)

import config
import game_framework
import play_mode
import ui

big = small = None
time = 0.0                     # 안내 글자 깜빡임용


def init():
    global big, small, time
    big = ui.load(96)
    small = ui.load(28)
    time = 0.0


def finish():
    pass


def handle_events():
    for event in get_events():
        dispatch(event)


def dispatch(event):
    if event.type == SDL_QUIT or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_SPACE):
        start()
    elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
        start()


def start():
    game_framework.change_mode(play_mode)      # 타이틀을 닫고 1구역부터


def update():
    global time
    time += game_framework.frame_time


def draw_cylinder(cx, cy, r):
    # 리볼버 실린더: 총알 여섯 개가 둥글게 (제목의 '6'을 그림으로)
    draw_circle(cx, cy, r, *config.COLOR_GUN, filled=True)
    for i in range(6):
        a = math.radians(90 + i * 60)
        draw_circle(int(cx + math.cos(a) * r * 0.62), int(cy + math.sin(a) * r * 0.62), int(r * 0.22),
                    *config.COLOR_BULLET_FLOOR, filled=True)
    draw_circle(cx, cy, int(r * 0.14), *config.COLOR_FLOOR, filled=True)


def render():
    clear_canvas()
    w, h = config.WIDTH, config.HEIGHT
    draw_rectangle(0, 0, w, h, *config.COLOR_WALL, filled=True)
    draw_rectangle(0, 0, w, 150, *config.COLOR_FLOOR, filled=True)         # 바닥 띠
    draw_rectangle(0, 146, w, 154, *config.COLOR_TABLE_EDGE, filled=True)
    draw_cylinder(w // 2, 360, 120)
    ui.draw_center(big, w // 2, 560, 'LAST 6 BULLET', 96, config.COLOR_HUD_TEXT)
    ui.draw_center(small, w // 2, 190, 'SIX BULLETS. ONE ROOM. NO SPARES.', 28, config.COLOR_WALL)
    if int(time * 2) % 2 == 0:                                            # 0.5초마다 깜빡
        ui.draw_center(small, w // 2, 90, 'CLICK OR PRESS ENTER TO START', 28, config.COLOR_BULLET_FLOOR)
    update_canvas()


def pause():
    pass


def resume():
    pass
