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


def fresh(enemies=False):
    import game_framework
    import play_mode
    game_framework.running = True
    game_framework.stack = [play_mode]
    play_mode.SPAWN_ENEMIES = enemies
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
    import config, game_world
    [bl] = [o for o in game_world.objects() if getattr(o, 'state', '') == 'FLYING']
    while bl.bounces == 0:         # 프레임 수 대신 상태로 기다려서 총알 속도를 바꿔도 같은 장면이 나온다
        sim.step(1)
    while bl.x > p.x + 70:         # 돌아오는 중간쯤
        sim.step(1)
    save('w1_5_bounced_back')      # 벽에 튕겨 돌아오는 총알 (주황: 누구든 맞음)
    while p.hp == config.PLAYER_HP:
        sim.step(1)
    sim.step(2)
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
    save('w1_8_dry_click')         # 머리 위 'CLICK', 위쪽 실린더 테두리 붉게, 조준점 회색
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


# ---------------------------------------------------------------- 2주차

def flying_or(state):
    import game_world
    from bullet import Bullet
    return [o for o in game_world.objects() if isinstance(o, Bullet) and o.state == state]


@scene
def w2_1_picker_steals():
    # 술집: 내가 쏜 총알이 바닥에 떨어지자 줍줍이들이 주우러 오고, 하나는 줍는 중(막대), 하나는 쏜다
    import random
    random.seed(3)
    pm = fresh(enemies=True)
    p = pm.player
    for tx, ty in ((1000, 520), (1050, 230), (820, 640)):
        sim.mouse_move(tx, ty)
        sim.click()
        sim.step(12)
    sim.mouse_move(900, 360)
    for _ in range(400):
        sim.step(1)
        p.hp = 4
        picking = [e for e in pm.enemies if e.state == 'PICK']
        if picking and any(e.state == 'SHOOT' for e in pm.enemies):
            break
    save('w2_1_picker_steals')
    for _ in range(200):
        sim.step(1)
        p.hp = 4
        if [b for b in flying_or('FLYING') if b.owner != 'player']:
            break
    sim.step(8)
    save('w2_1_enemy_fires')       # 줍줍이가 내 총알로 쏜다 (자주색 총알)
    pm.finish()


@scene
def w2_2_kick():
    from picker import Picker
    pm = fresh()
    p = pm.player
    e = pm.add_enemy(Picker, p.x + 48, p.y + 10)
    e.held = [p.held.pop(), p.held.pop()]
    e.state, e.SPEED = 'FLEE', 0
    b = p.held.pop()
    b.drop(p.x + 40, p.y - 30)
    b.add_to_world()
    sim.mouse_move(p.x + 200, p.y)
    sim.step(1)
    p.kick()
    sim.step(4)
    save('w2_2_kick')              # 발차기: 부채꼴 호, 적 기절 별, 떨어뜨린 총알, 굴러가는 바닥 총알
    pm.finish()


@scene
def w2_3_mine():
    import random
    random.seed(5)
    pm = fresh(enemies=True)
    pm.start_zone(1)
    p = pm.player
    for tx, ty in ((700, 600), (900, 200), (600, 120)):
        sim.mouse_move(tx, ty)
        sim.click()
        sim.step(12)
    p.x, p.y = 420, 300
    sim.mouse_move(800, 360)
    for _ in range(60):
        sim.step(1)
        p.hp = 4
    save('w2_3_mine')              # 광산: 랜턴 빛 안만 바닥 총알이 보인다. 들개·술꾼·줍줍이
    pm.finish()


@scene
def w2_4_door_open():
    from picker import Picker
    pm = fresh()
    p = pm.player
    e = pm.add_enemy(Picker, 1000, 330)   # 테이블에 가리지 않는 자리
    e.held = [p.held.pop()]
    e.state, e.SPEED = 'FLEE', 0
    sim.mouse_move(1000, 330)
    sim.step(1)
    p.fire()
    for _ in range(60):
        sim.step(1)
        if pm.zone.door_open:
            break
    sim.step(20)
    save('w2_4_door_open')         # 마지막 적을 쓰러뜨리면 오른쪽 문이 열리고 EXIT, 현상금 $50
    pm.finish()


@scene
def w2_5_game_over():
    import config
    from drunk import Drunk
    pm = fresh()
    p = pm.player
    p.hp = 1
    pm.add_enemy(Drunk, p.x + 200, p.y)
    for _ in range(200):
        sim.step(1)
        import game_framework
        if game_framework.stack[-1] is not pm:
            break
    sim.step(1)
    save('w2_5_game_over')
    import game_framework
    game_framework.stack = [pm]
    pm.finish()


@scene
def w2_6_drunk_pass():
    # 술꾼 패스: 바닥 총알을 빈손 줍줍이에게 차 준다 ('HEY!'), 굴러간 총알을 줍줍이가 줍는다
    from drunk import Drunk
    from picker import Picker
    pm = fresh()
    p = pm.player
    p.x, p.y = 160, 620
    mate = pm.add_enemy(Picker, 1080, 330)
    mate.state = 'FLEE'
    b = p.held.pop()
    b.drop(700, 330)
    b.add_to_world()
    d = pm.add_enemy(Drunk, 600, 300)
    d.pass_cooldown = 0
    sim.mouse_move(400, 400)
    for _ in range(120):
        sim.step(1)
        if b.state == 'ROLLING':
            break
    sim.step(6)
    save('w2_6_drunk_pass')        # 'HEY!' 와 줍줍이 쪽으로 굴러가는 총알
    for _ in range(120):
        sim.step(1)
        if mate.target is not None:
            break
    sim.step(5)
    save('w2_6_pass_received')     # 줍줍이가 패스 받은 총알을 줍는 중 (막대)
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
