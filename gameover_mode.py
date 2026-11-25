# 게임 오버 (PRD 15-1). 체력이 0 이 되면 play_mode 위에 겹쳐 올린다(push_mode).
# 아래의 전투 화면은 멈춘 채로 그대로 그리고, 가운데 띠에 결과를 쓴다.
#   R 또는 Enter: 1구역부터 다시   T: 타이틀로   ESC: 종료
from pico2d import (SDL_KEYDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_RETURN, SDLK_r, SDLK_t, clear_canvas,
                    draw_rectangle, get_events, load_font, update_canvas)

import config
import game_framework
import game_world
import play_mode
import title_mode

title = 'GAME OVER'
big = small = None


def init():
    global big, small
    try:
        big = load_font(config.UI_FONT, 56)
        small = load_font(config.UI_FONT, 20)
    except Exception:
        big = small = None


def finish():
    pass


def handle_events():
    for event in get_events():
        dispatch(event)


def dispatch(event):
    if event.type == SDL_QUIT or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key in (SDLK_r, SDLK_RETURN):
        game_framework.pop_mode()  # play_mode 로 돌아가서
        play_mode.restart()        # 1구역부터 새로 시작
    elif event.type == SDL_KEYDOWN and event.key == SDLK_t:
        game_framework.pop_mode()
        game_framework.change_mode(title_mode)   # play_mode 도 닫으면서 타이틀로


def update():
    pass


def render():
    clear_canvas()
    game_world.render()            # 멈춘 전투 화면
    cy = config.HEIGHT // 2
    draw_rectangle(0, cy - 80, config.WIDTH, cy + 80, *config.COLOR_WALL, filled=True)
    if big:
        big.draw(config.WIDTH // 2 - len(title) * 17, cy + 28, title, config.COLOR_HUD_TEXT)
        info = 'BOUNTY $%d' % play_mode.player.bounty
        small.draw(config.WIDTH // 2 - len(info) * 6, cy - 22, info, config.COLOR_BULLET_FLOOR)
        keys = 'R  TRY AGAIN      T  TITLE      ESC  QUIT'
        small.draw(config.WIDTH // 2 - len(keys) * 6, cy - 54, keys, config.COLOR_HUD_TEXT)
    update_canvas()


def pause():
    pass


def resume():
    pass
