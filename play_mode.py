from pico2d import *

import config
import game_framework
import game_world
from bullet import Bullet
from hud import Hud
from player import Player
from zone import Zone

zone = None
player = None


def init():
    global zone, player
    zone = Zone(config.SALOON_TABLES)
    game_world.add_object(zone, 0)
    player = Player(zone, config.WIDTH // 2, config.HEIGHT // 2)
    game_world.add_object(player, 1)
    # 구역의 총알은 여기서만 만든다. 이후에는 상태만 바뀌므로 총알 수가 늘거나 줄지 않는다.
    player.held = [Bullet(zone) for _ in range(config.AMMO)]
    game_world.add_collision_pair('player:bullet', player, None)
    game_world.add_object(Hud(player), 2)


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
