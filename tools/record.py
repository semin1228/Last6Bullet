# 발표 데모 영상 녹화: 실제 창을 띄워 장면마다 정해진 조작(이동·조준·발사·발차기)을 자동으로 하고,
# 화면을 초당 30장 캡처해 ffmpeg 로 mp4 를 만든다. 사람이 하는 것과 같은 입력 이벤트로 조작한다.
#   C:\Python313\python.exe tools\record.py            모든 장면 + 이어 붙인 영상
#   C:\Python313\python.exe tools\record.py s2_steal   한 장면만
# 결과: demo_video/ (저장소에 올리지 않는다, .gitignore). 소리는 없다(목소리는 따로 녹음해서 편집).
# 장면 순서와 내용은 docs/Presentation2_Script.md 의 데모 장면을 따른다.
import ctypes
import math
import os
import random
import shutil
import subprocess
import sys

import sim

OUT = os.path.join(sim.ROOT, 'demo_video')
FPS = 30                       # 영상 프레임 (게임은 1/60초씩 돌리고 두 프레임마다 한 장 찍는다)
SCENES = {}


def scene(fn):
    SCENES[fn.__name__] = fn
    return fn


class Recorder:
    # 게임을 한 프레임씩 돌리면서 화면을 ffmpeg 에 넘긴다
    def __init__(self, name):
        import config
        self.w, self.h = config.WIDTH, config.HEIGHT
        self.path = os.path.join(OUT, name + '.mp4')
        self.frame = 0
        self.ff = subprocess.Popen(
            [ffmpeg(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba',
             '-s', '%dx%d' % (self.w, self.h), '-r', str(FPS), '-i', '-',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', self.path],
            stdin=subprocess.PIPE)
        self.buf = (ctypes.c_ubyte * (self.w * self.h * 4))()

    def step(self, frames=1, act=None):
        import pico2d.pico2d as core
        from pico2d import SDL_PIXELFORMAT_ABGR8888, SDL_RenderReadPixels
        for _ in range(frames):
            if act:
                act()
            sim.step(1)
            self.frame += 1
            if self.frame % (60 // FPS) == 0:
                SDL_RenderReadPixels(core.renderer, None, SDL_PIXELFORMAT_ABGR8888, ctypes.byref(self.buf), self.w * 4)
                self.ff.stdin.write(bytes(self.buf))

    def until(self, cond, limit, act=None):
        for _ in range(limit):
            if cond():
                return True
            self.step(1, act)
        return False

    def close(self):
        self.ff.stdin.close()
        self.ff.wait()
        print('  saved %s (%.1f초)' % (os.path.relpath(self.path, sim.ROOT), self.frame / 60))


def ffmpeg():
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


# ---------------------------------------------------------------- 조작 도우미 (키보드·마우스 이벤트)

class Bot:
    def __init__(self, pm):
        self.pm = pm
        self.p = pm.player

    def keys(self, want):
        from pico2d import SDLK_a, SDLK_d, SDLK_s, SDLK_w
        for k in (SDLK_w, SDLK_a, SDLK_s, SDLK_d):
            (sim.key_down if k in want else sim.key_up)(k)

    def walk_to(self, x, y, slack=6):
        from pico2d import SDLK_a, SDLK_d, SDLK_s, SDLK_w
        p, want = self.p, set()
        if x > p.x + slack: want.add(SDLK_d)
        if x < p.x - slack: want.add(SDLK_a)
        if y > p.y + slack: want.add(SDLK_w)
        if y < p.y - slack: want.add(SDLK_s)
        self.keys(want)
        return not want

    def stop(self):
        self.keys(set())

    def aim(self, x, y):
        sim.mouse_move(x, y)

    def shoot(self):
        sim.click(1)

    def kick(self):
        from pico2d import SDLK_SPACE
        sim.key_down(SDLK_SPACE)
        sim.key_up(SDLK_SPACE)


def setup(zone=0):
    import game_framework
    import play_mode
    game_framework.running = True
    game_framework.stack = [play_mode]
    play_mode.SPAWN_ENEMIES = False
    random.seed(11)
    play_mode.init()
    if zone:
        play_mode.start_zone(zone)
    return play_mode, Bot(play_mode)


def keep_alive(pm):
    pm.player.hp = max(pm.player.hp, 2)    # 데모 중 게임 오버가 나지 않게


# ---------------------------------------------------------------- 장면 (스크립트의 데모 ① ~ ⑤)

@scene
def s1_shoot():
    # ① 줍줍이를 쏴서 쓰러뜨린다. 총알이 그 자리에 떨어지고 현상금 +$50. 걸어가서 다시 줍는다.
    from picker import Picker
    pm, bot = setup()
    p = pm.player
    p.x, p.y = 300, 330
    pk = pm.add_enemy(Picker, 1000, 330)
    pk.SPEED = 0                                   # 맞히는 장면을 확실히 보여 주려고 이 장면에서만 세워 둔다
    rec = Recorder('s1_shoot')
    bot.aim(700, 330)
    rec.step(30)
    rec.step(20, lambda: bot.aim(pk.x, pk.y))
    bot.shoot()
    rec.until(lambda: not pk.alive, 90, lambda: keep_alive(pm))
    rec.step(30)
    import game_world
    from bullet import Bullet
    floor = [b for b in game_world.objects() if isinstance(b, Bullet) and b.state == 'FLOOR']
    if floor:
        b = floor[0]
        rec.until(lambda: b.state == 'HELD', 240, lambda: (bot.walk_to(b.x, b.y), bot.aim(b.x + 200, b.y)))
    bot.stop()
    rec.step(45)
    rec.close()
    pm.finish()


@scene
def s2_steal():
    # ② 일부러 빗맞힌다. 줍줍이가 그 총알을 주워(막대) 물러나고, 총구가 반짝이면 옆으로 피한다.
    from picker import Picker
    pm, bot = setup()
    p = pm.player
    p.x, p.y = 260, 330
    pk = pm.add_enemy(Picker, 1150, 330)
    rec = Recorder('s2_steal')
    bot.aim(1240, 620)
    rec.step(30)
    bot.shoot()                                    # 오른쪽 위로 빗맞힌다 (줍줍이 근처에 떨어진다)
    rec.until(lambda: pk.state == 'PICK', 420, lambda: keep_alive(pm))
    rec.until(lambda: pk.state == 'SHOOT', 60)
    dodged = {'t': 0}

    def act():
        keep_alive(pm)
        bot.aim(pk.x, pk.y)
        if pk.aiming() and dodged['t'] == 0:
            dodged['t'] = 40                       # 총구가 반짝이면 위로 피한다
        if dodged['t'] > 0:
            dodged['t'] -= 1
            bot.walk_to(p.x, p.y + 100)
        else:
            bot.stop()
    rec.until(lambda: not pk.held, 300, act)
    rec.step(50, act)
    bot.stop()
    rec.step(20)
    rec.close()
    pm.finish()


@scene
def s3_kick():
    # ③ 총알을 가진 줍줍이에게 달려가 발차기. 기절하며 총알을 떨어뜨리고, 내가 줍는다.
    from picker import Picker
    pm, bot = setup()
    p = pm.player
    p.x, p.y = 300, 330
    pk = pm.add_enemy(Picker, 760, 360)
    pk.held = [p.held.pop(), p.held.pop()]
    pk.state, pk.timer = 'SHOOT', 6.0              # 데모 동안은 쏘지 않게
    rec = Recorder('s3_kick')
    rec.step(20, lambda: bot.aim(pk.x, pk.y))

    def chase():
        keep_alive(pm)
        bot.aim(pk.x, pk.y)
        bot.walk_to(pk.x, pk.y)
        if pk.distance_to(p) < p.radius + pk.radius + 40 and pk.state != 'STUN':
            bot.kick()
    rec.until(lambda: pk.state == 'STUN', 240, chase)
    bot.stop()
    rec.step(10)
    import game_world
    from bullet import Bullet
    floor = [b for b in game_world.objects() if isinstance(b, Bullet) and b.state == 'FLOOR']
    if floor:
        b = min(floor, key=lambda b: math.hypot(b.x - p.x, b.y - p.y))
        rec.until(lambda: b.state == 'HELD', 120, lambda: bot.walk_to(b.x, b.y))
    bot.stop()
    rec.step(50, lambda: bot.aim(pk.x, pk.y))
    rec.close()
    pm.finish()


@scene
def s4_door_to_mine():
    # ④ 마지막 적을 쓰러뜨리면 오른쪽 문이 열리고(EXIT), 문으로 나가 광산에 들어선다.
    from picker import Picker
    pm, bot = setup()
    p = pm.player
    p.x, p.y = 500, 360
    pk = pm.add_enemy(Picker, 1000, 330)
    pk.SPEED = 0                                   # 마지막 적을 쓰러뜨리는 장면 (이 장면에서만 세워 둔다)
    rec = Recorder('s4_door_to_mine')
    rec.step(20, lambda: bot.aim(pk.x, pk.y))
    bot.shoot()
    rec.until(lambda: not pk.alive, 90, lambda: bot.aim(pk.x, pk.y))
    rec.until(lambda: pm.zone.door_open, 10)
    rec.step(30)
    rec.until(lambda: pm.zone.number == 2, 400, lambda: (bot.walk_to(1260, 360, 3), bot.aim(1250, 360)))
    bot.stop()
    p = pm.player
    rec.step(90, lambda: (bot.walk_to(400, 300), bot.aim(700, 300)))
    bot.stop()
    rec.step(30)
    rec.close()
    pm.finish()


@scene
def s5_mine():
    # ⑤ 광산: 랜턴 빛 안의 총알만 보인다. 쏜 총알을 들개가 삼키고, 쫓아가 차면 토해 낸다.
    from dog import Dog
    pm, bot = setup(1)
    p = pm.player
    p.x, p.y = 200, 360
    dog = pm.add_enemy(Dog, 900, 600)
    rec = Recorder('s5_mine')
    bot.aim(700, 250)
    rec.step(30)
    bot.shoot()
    rec.step(20)
    bot.aim(650, 480)
    bot.shoot()
    rec.until(lambda: len(dog.held) >= 1, 300, lambda: (keep_alive(pm), bot.walk_to(420, 360)))

    def chase():
        keep_alive(pm)
        bot.aim(dog.x, dog.y)
        bot.walk_to(dog.x, dog.y)
        if dog.distance_to(p) < p.radius + dog.radius + 40 and dog.state != 'STUN':
            bot.kick()
    rec.until(lambda: dog.state == 'STUN', 360, chase)
    bot.stop()
    rec.step(60, lambda: bot.aim(dog.x, dog.y))
    rec.close()
    pm.finish()


def join(names):
    # 장면들을 순서대로 이어 붙인 영상 (다시 인코딩하지 않는다)
    lst = os.path.join(OUT, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as f:
        for n in names:
            f.write("file '%s.mp4'\n" % n)
    out = os.path.join(OUT, 'demo_all.mp4')
    subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out],
                   check=True)
    os.remove(lst)
    print('  saved', os.path.relpath(out, sim.ROOT))


def main():
    os.makedirs(OUT, exist_ok=True)
    sim.open_game(window=True)
    from pico2d import close_canvas
    names = sys.argv[1:] or list(SCENES)
    for name in names:
        SCENES[name]()
    close_canvas()
    if not sys.argv[1:]:
        join(names)


if __name__ == '__main__':
    main()
