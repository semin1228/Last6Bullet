from pico2d import close_canvas, open_canvas

import config
import game_framework
import play_mode

open_canvas(config.WIDTH, config.HEIGHT)
game_framework.run(play_mode)
close_canvas()
