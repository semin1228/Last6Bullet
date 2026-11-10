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


@scene
def w1_4_bounce():
    # 총알이 지나간 자리를 기록해 점으로 찍는다 (스크린샷에서만 쓰는 표시)
    import math
    from pico2d import clear_canvas, draw_circle
    import config
    import game_world
    pm = fresh()
    p = pm.player
    l, b, r, t = config.SALOON_TABLES[0]
    p.x, p.y = (l + r) / 2 - 30, b - 120
    trail = []
    for deg in (80, 20, -35):
        a = math.radians(deg)
        sim.mouse_move(p.x + math.cos(a) * 200, p.y + math.sin(a) * 200)
        sim.click()
        sim.step(12, before=lambda i: trail.extend(
            (o.x, o.y) for o in game_world.objects() if getattr(o, 'state', '') == 'FLYING'))
    sim.step(90, before=lambda i: trail.extend(
        (o.x, o.y) for o in game_world.objects() if getattr(o, 'state', '') == 'FLYING'))
    clear_canvas()
    game_world.render()
    for x, y in trail[::2]:
        draw_circle(x, y, 1, 12, 68, 124, filled=True)
    save('w1_4_bounce')
    pm.finish()


@scene
def w1_5_self_hit():
    pm = fresh()
    p = pm.player
    l, b, r, t = pm.zone.inner
    p.x, p.y = r - 160, (b + t) / 2
    sim.mouse_move(r, p.y)
    sim.click()
    sim.step(21)
    save('w1_5_bounced_back')      # 벽에 튕겨 돌아오는 총알 (주황: 누구든 맞음)
    sim.step(14)
    p.invincible = 0.05            # 스크린샷이 깜빡임에 걸려 캐릭터가 사라지지 않게
    sim.step(1)
    save('w1_5_hurt')              # 맞아서 왼쪽 위 체력이 3칸, 총알은 발밑에서 주워 다시 6발
    pm.finish()


@scene
def w1_6_ledger():
    from pico2d import SDLK_F1
    pm = fresh()
    p = pm.player
    sim.key_down(SDLK_F1)          # 장부 표시 켜기
    for tx, ty in ((p.x - 300, p.y + 250), (p.x + 400, p.y - 200)):
        sim.mouse_move(tx, ty)
        sim.click()
        sim.step(80)
    sim.mouse_move(p.x, p.y + 300)
    sim.click()
    sim.step(6)
    save('w1_6_ledger')            # 오른쪽 위에 손·바닥·공중 총알 수와 합계(항상 6)
    pm.finish()


@scene
def w1_7_hud_and_crosshair():
    pm = fresh()
    for tx, ty in ((1100, 650), (200, 600)):
        sim.mouse_move(tx, ty)
        sim.click()
        sim.step(14)
    sim.mouse_move(820, 280)
    sim.step(2)
    save('w1_7_hud_and_crosshair')  # 위쪽: 체력, 실린더(4발), 구역 이름 / 마우스 자리에 조준점
    pm.finish()


@scene
def w1_8_effects():
    import config
    import game_world
    pm = fresh()
    p = pm.player
    l, b, r, t = pm.zone.inner
    p.x, p.y = r - 200, 300
    sim.mouse_move(r - 60, 300)
    sim.click()
    sim.step(1)
    save('w1_8_muzzle_flash')      # 총구 불꽃
    [bl] = [o for o in game_world.objects() if getattr(o, 'state', '') == 'FLYING']
    while bl.bounces == 0:
        sim.step(1)
    sim.mouse_move(r - 300, 450)   # 조준점이 불똥을 가리지 않게 옮긴다
    sim.step(2)
    save('w1_8_bounce_spark')      # 벽에 튕긴 자리의 불똥, 총알은 주황
    while p.hp == config.PLAYER_HP:   # 돌아온 총알에 맞을 때까지
        sim.step(1)
    sim.step(4)
    p.invincible = 0.05            # 깜빡임에 걸려 캐릭터가 사라지지 않게
    sim.step(1)
    save('w1_8_hit_ring')          # 튕긴 총알에 맞은 붉은 고리 + 발밑에 떨어진 총알을 주운 놋쇠 고리
    pm.finish()


@scene
def w1_8_dry_click():
    import math
    pm = fresh()
    p = pm.player
    deg = 100
    while p.held:                  # 여섯 발을 실제로 다 쏴서 빈 총을 만든다 (돌아와 주운 총알도 다시 쏜다)
        sim.mouse_move(p.x + math.cos(math.radians(deg)) * 200, p.y + math.sin(math.radians(deg)) * 200)
        sim.click()
        sim.step(15)
        deg += 55
        if not p.held:
            sim.step(100)          # 모두 바닥에 떨어질 때까지 기다린다
    sim.mouse_move(p.x + 150, p.y + 60)
    sim.click()
    sim.step(8)
    save('w1_8_dry_click')         # 머리 위 '찰칵', 위쪽 실린더 테두리 붉게, 조준점 회색
    pm.finish()


@scene
def w1_9_thin_wall_fix():
    # 버그 수정 확인: 6px 벽에 붙어 벽 쪽으로 쏴도 총알이 벽 앞면에서 튕겨 나온다
    from pico2d import clear_canvas, draw_circle
    import game_world
    pm = fresh()
    p = pm.player
    wall = (700, 40, 706, 680)
    pm.zone.obstacles = [wall]
    p.x, p.y = pm.zone.push_out(wall[0] - 1, 360, p.radius)
    sim.mouse_move(p.x + 200, p.y + 60)
    sim.click()
    trail = []
    sim.step(30, before=lambda i: trail.extend(
        (o.x, o.y) for o in game_world.objects() if getattr(o, 'state', '') == 'FLYING'))
    clear_canvas()
    game_world.render()
    for x, y in trail:
        draw_circle(x, y, 1, 12, 68, 124, filled=True)
    save('w1_9_thin_wall_fix')
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
