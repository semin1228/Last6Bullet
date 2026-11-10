import pico2d.pico2d as canvas
from pico2d import SDL_SetWindowTitle, close_canvas, open_canvas

import config
import game_framework
import play_mode

open_canvas(config.WIDTH, config.HEIGHT)
# pico2d 의 get_events() 는 매 프레임 print_fps() 로 창 제목을 'Pico2D Canvas ... FPS' 로 덮어쓴다.
# 제목은 게임 이름으로 한 번만 정하고, FPS 는 F1 디버그 표시에서 본다.
canvas.print_fps = lambda: None
SDL_SetWindowTitle(canvas.window, config.TITLE.encode('utf-8'))
game_framework.run(play_mode)
close_canvas()
