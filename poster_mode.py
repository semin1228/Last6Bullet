# 현상수배 포스터 (PRD 15-1). 구역이 시작될 때 그 구역에 처음 나오는 적을 play_mode 위에 겹쳐 보여 준다(push_mode).
#   클릭 / Enter / Space 또는 1.5초 뒤에 닫힌다. 새로 나오는 적이 없는 구역(기차)은 띄우지 않는다.
# 얼굴은 도형으로 그렸고, 이미지가 생기면 res/ 의 그림으로 바꾼다.
from pico2d import (SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_RETURN,
                    SDLK_SPACE, clear_canvas, draw_circle, draw_rectangle, get_events, update_canvas)

import config
import game_framework
import game_world
import ui
from boss import Boss
from dog import Dog
from drunk import Drunk
from picker import Picker
from zone import ZONES

SHOW_TIME = 1.5
PAPER = (233, 214, 172)
INK = (65, 36, 2)
# 적 종류 -> (포스터 이름, 현상금, 얼굴색, 모자색). 이름은 PRD 14장 대응표
WANTED = {
    'picker': ('THE PICKER', Picker.BOUNTY, config.COLOR_PICKER, config.COLOR_HAT),
    'drunk': ('THE DRUNK', Drunk.BOUNTY, config.COLOR_DRUNK, config.COLOR_HAT),
    'dog': ('THE HOUND', Dog.BOUNTY, config.COLOR_DOG, config.COLOR_DOG_EAR),
    'boss': ('THE BOSS', Boss.BOUNTY, config.COLOR_BOSS, config.COLOR_BOSS_HAT),
}

kinds = []                     # 지금 보여 주는 적 종류
time = 0.0
big = small = None


def new_kinds(index):
    # index 구역에서 앞 구역들에 없던 적 종류 (구역 데이터 순서 그대로)
    seen = {kind for z in ZONES[:index] for kind, x, y in z['enemies']}
    result = []
    for kind, x, y in ZONES[index]['enemies']:
        if kind not in seen and kind not in result:
            result.append(kind)
    return result


def prepare(index):
    # index 구역에서 보여 줄 적을 정해 두고, 포스터를 띄울지(True) 말지(False) 알려 준다.
    # 띄우는 쪽(play_mode)이 game_framework.push_mode(poster_mode) 를 부른다.
    global kinds
    kinds = new_kinds(index)
    return bool(kinds)


def init():
    global time, big, small
    time = 0.0
    big = ui.load(40)
    small = ui.load(22)


def finish():
    pass


def handle_events():
    for event in get_events():
        dispatch(event)


def dispatch(event):
    if event.type == SDL_QUIT or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key in (SDLK_RETURN, SDLK_SPACE):
        game_framework.pop_mode()
    elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
        game_framework.pop_mode()


def update():
    global time
    time += game_framework.frame_time
    if time >= SHOW_TIME:
        game_framework.pop_mode()


def draw_poster(cx, kind):
    name, reward, face, hat = WANTED[kind]
    w, h = 260, 400
    b = 160
    draw_rectangle(cx - w // 2, b, cx + w // 2, b + h, *PAPER, filled=True)
    draw_rectangle(cx - w // 2, b, cx + w // 2, b + h, *INK)
    draw_rectangle(cx - w // 2 + 8, b + 8, cx + w // 2 - 8, b + h - 8, *INK)
    ui.draw_center(big, cx, b + h - 50, 'WANTED', 40, INK)
    draw_circle(cx, b + 215, 62, *face, filled=True)                       # 얼굴
    draw_rectangle(cx - 80, b + 258, cx + 80, b + 270, *hat, filled=True)  # 모자 챙
    draw_rectangle(cx - 44, b + 268, cx + 44, b + 312, *hat, filled=True)  # 모자 윗부분
    draw_circle(cx - 22, b + 215, 6, *PAPER, filled=True)                  # 눈
    draw_circle(cx + 22, b + 215, 6, *PAPER, filled=True)
    ui.draw_center(small, cx, b + 100, name, 22, INK)
    ui.draw_center(small, cx, b + 60, 'REWARD $%d' % reward, 22, config.COLOR_HP)


def render():
    clear_canvas()
    game_world.render()                               # 아래의 전투 화면은 멈춘 채로 보인다
    w = config.WIDTH
    n = len(kinds)
    for i, kind in enumerate(kinds):
        draw_poster(w // 2 + int((i - (n - 1) / 2) * 300), kind)
    ui.draw_center(small, w // 2, 110, 'CLICK TO CONTINUE', 22, config.COLOR_WALL)
    update_canvas()


def pause():
    pass


def resume():
    pass
