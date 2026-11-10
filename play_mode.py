from pico2d import *

import config
import game_framework
import game_world
from player import Player
from zone import Zone

zone = None
player = None


def init():
    global zone, player
    zone = Zone()
    game_world.add_object(zone, 0)
    player = Player(zone, config.WIDTH // 2, config.HEIGHT // 2)
    game_world.add_object(player, 1)


def handle_events():
    for event in get_events():
        dispatch(event)


def dispatch(event):
    # 이벤트 하나를 처리한다. 자동 점검(tools/check.py)도 같은 경로로 입력을 넣는다.
    if event.type == SDL_QUIT:
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
        game_framework.quit()
    else:
        player.handle_event(event)


def update():
    game_world.update()
    game_world.handle_collisions()


def render():
    clear_canvas()
    game_world.render()
    update_canvas()


def finish():
    game_world.clear()


def pause():
    player.release_all_keys()


def resume():
    pass
