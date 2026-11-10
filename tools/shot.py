# 화면 확인용: 실제 창을 띄워 장면을 재현하고 스크린샷을 docs/shots/ 에 PNG 로 저장한다.
#   C:\Python313\python.exe tools\shot.py            모든 장면
#   C:\Python313\python.exe tools\shot.py 장면이름     한 장면만
# 스크린샷 저장에만 Pillow 를 쓴다. 게임 본체는 Pillow 없이 돌아간다.
import ctypes
import os
import sys

import sim

OUT = os.path.join(sim.ROOT, 'docs', 'shots')
SCENES = {}


def scene(fn):
    SCENES[fn.__name__] = fn
    return fn


def save(name):
    import pico2d.pico2d as core
    from pico2d import SDL_PIXELFORMAT_ABGR8888, SDL_RenderReadPixels
    from PIL import Image
    import config
    w, h = config.WIDTH, config.HEIGHT
    buf = (ctypes.c_ubyte * (w * h * 4))()
    SDL_RenderReadPixels(core.renderer, None, SDL_PIXELFORMAT_ABGR8888, ctypes.byref(buf), w * 4)
    path = os.path.join(OUT, name + '.png')
    Image.frombuffer('RGBA', (w, h), bytes(buf), 'raw', 'RGBA', 0, 1).convert('RGB').save(path)
    print('  saved', os.path.relpath(path, sim.ROOT))


def fresh():
    import game_framework
    import play_mode
    game_framework.running = True
    play_mode.init()
    return play_mode


@scene
def w1_1_skeleton():
    pm = fresh()
    sim.step(10)
    save('w1_1_skeleton')
    pm.finish()


@scene
def w1_2_move_and_aim():
    from pico2d import SDLK_a, SDLK_w
    pm = fresh()
    sim.mouse_move(1000, 600)
    sim.key_down(SDLK_w)
    sim.key_down(SDLK_a)
    sim.step(40)                   # 왼쪽 위로 이동하면서도 마우스(오른쪽 위)를 바라본다
    save('w1_2_move_and_aim')
    pm.finish()


@scene
def w1_3_fire():
    pm = fresh()
    p = pm.player
    for tx, ty in ((1100, 650), (200, 600), (900, 100)):
        sim.mouse_move(tx, ty)
        sim.click()
        sim.step(14)
    save('w1_3_fire_flying')       # 세 발이 날아가는 중, 발밑 총알 표시는 3칸 남음
    sim.step(120)
    save('w1_3_fire_floor')        # 벽에 닿거나 1.6초가 지나 바닥에 떨어진 총알
    pm.finish()


def main():
    os.makedirs(OUT, exist_ok=True)
    sim.open_game(window=True)
    from pico2d import close_canvas
    names = sys.argv[1:] or list(SCENES)
    for name in names:
        SCENES[name]()
    close_canvas()


if __name__ == '__main__':
    main()
