# 3구역 달리는 기차 (PRD 7장). 기차는 오른쪽으로 달리므로 '뒤' 는 왼쪽이다.
#   - 열차 바닥(짐받이 턱 앞)에서는 바닥 총알이 70px/s, 플레이어가 28px/s, 적이 14px/s 로 뒤로 밀린다.
#   - 바닥 총알은 짐받이 턱(LIP_X)에서 멈춰 모인다. 사람은 턱을 넘어 다닐 수 있다.
#   - 턱 뒤의 위험 띠(노랑·검정 줄무늬)는 평소에 밀리지 않는다 (체험판에서 사용자가 정함).
#   - 덜컹(5~7초 간격, 1초 전 예고 'JOLT!'): 0.25초 동안 모두가 크게(약 90px) 뒤로 밀린다.
#     열차 뒤 끝으로 밀려나면 사람은 떨어진다. 플레이어는 체력 -1 하고 열차 가운데로 돌아오며 총알은 그대로,
#     적은 퇴장하며 가진 총알을 턱 앞에 흘린다. 발차기로 뒤 끝까지 밀려나도 떨어진다.
#   - 옆과 뒤 가장자리는 총알에게는 낮은 난간(벽)이라 튕긴다. 총알 수는 유지된다.
# 적이 줍는 중인 총알(PINNED)은 미끄러지지 않는다 (PRD 15-6).
import random

from pico2d import draw_line, draw_rectangle

import config
import game_framework
import game_world
from bullet import Bullet
from zone import Zone


class TrainZone(Zone):
    def __init__(self, obstacles=(), number=3, name='TRAIN', ammo=config.AMMO):
        super().__init__(obstacles, number, name, ammo)
        self.jolt_in = random.uniform(*config.JOLT_INTERVAL)   # 다음 덜컹까지 남은 시간 (초)
        self.jolt_left = 0.0                                   # 지금 덜컹이 남은 시간 (초)
        self.on_fall = None                                    # 사람이 떨어졌을 때 부를 함수 (play_mode 가 정한다)

    # ------------------------------------------------------------ 덜컹

    def warning(self):
        # 덜컹 1초 전부터 예고 (HUD 'JOLT!', 위험 띠 깜빡임)
        return self.jolt_left <= 0 and self.jolt_in <= config.JOLT_WARN

    def jolting(self):
        return self.jolt_left > 0

    def tick_jolt(self, dt):
        if self.jolt_left > 0:
            self.jolt_left -= dt
            return
        self.jolt_in -= dt
        if self.jolt_in <= 0:
            self.jolt_left = config.JOLT_TIME
            self.jolt_in = random.uniform(*config.JOLT_INTERVAL)

    # ------------------------------------------------------------ 밀림과 추락

    def on_main_floor(self, x):
        return x > config.LIP_X

    def update(self):
        super().update()
        dt = game_framework.frame_time
        self.tick_jolt(dt)
        jolt = config.JOLT_SPEED if self.jolting() else 0.0
        from enemy import Enemy
        from player import Player
        for o in list(game_world.objects()):
            if isinstance(o, Bullet):
                if o.state == 'FLOOR':
                    self.slide_bullet(o, jolt, dt)
            elif isinstance(o, Player) or (isinstance(o, Enemy) and o.alive):
                base = config.TRAIN_PLAYER_SLIDE if isinstance(o, Player) else config.TRAIN_ENEMY_SLIDE
                v = (base if self.on_main_floor(o.x) else 0.0) + jolt
                self.slide_person(o, v, dt)

    def slide_bullet(self, b, jolt, dt):
        if self.on_main_floor(b.x):
            v = config.TRAIN_BULLET_SLIDE + jolt
            nx = max(config.LIP_X + b.radius, b.x - v * dt)     # 짐받이 턱에서 멈춘다
        elif jolt:
            nx = b.x - jolt * dt                                 # 위험 띠 위의 총알은 덜컹 때만 (뒤 난간에서 멈춤)
        else:
            return
        b.x, b.y = self.push_out(nx, b.y, b.radius)

    def slide_person(self, o, v, dt):
        l = self.inner[0]
        shoved_back = getattr(o, 'push', (0.0, 0.0))[0] < 0       # 발차기·밀치기로 뒤쪽으로 밀리는 중
        at_edge = o.x - o.radius <= l + 0.5
        if at_edge and (v > 0 and self.jolting() or shoved_back):
            self.fall(o)
            return
        if v <= 0:
            return
        nx = o.x - v * dt
        if nx - o.radius < l and self.jolting():
            self.fall(o)
            return
        o.x, o.y = self.push_out(nx, o.y, o.radius)

    def fall(self, o):
        if self.on_fall:
            self.on_fall(o)

    def lip_drop_point(self, y):
        # 떨어진 적이 흘린 총알이 놓일 자리: 턱 바로 앞
        l, b, r, t = self.inner
        return config.LIP_X + config.BULLET_RADIUS + 14, min(max(y, b + 20), t - 20)

    # ------------------------------------------------------------ 그리기

    def draw(self):
        l, b, r, t = self.inner
        draw_rectangle(0, 0, config.WIDTH, config.HEIGHT, *config.COLOR_TRAIN_OUTSIDE, filled=True)
        # 지나가는 침목: 위아래 벽 자리에서 왼쪽으로 흘러간다 (달리는 느낌)
        shift = (self.clock * config.TRAIN_SCROLL) % 48
        for x in range(-48, config.WIDTH + 48, 48):
            sx = x - shift
            draw_rectangle(sx, 0, sx + 16, b - 4, *config.COLOR_TRAIN_SLEEPER, filled=True)
            draw_rectangle(sx, t + 4, sx + 16, config.HEIGHT, *config.COLOR_TRAIN_SLEEPER, filled=True)
        draw_rectangle(l, b, r, t, *config.COLOR_TRAIN_FLOOR, filled=True)
        for x in range(config.LIP_X + 40, r, 40):                # 세로 널판
            draw_line(x, b, x, t, *config.COLOR_TRAIN_PLANK)
        stripe = config.COLOR_JOLT_WARN if self.warning() and int(self.clock * 8) % 2 else config.COLOR_STRIPE_YELLOW
        for i, x in enumerate(range(l, config.LIP_X, 16)):     # 위험 띠: 노랑·검정 줄무늬
            color = stripe if i % 2 == 0 else config.COLOR_STRIPE_BLACK
            draw_rectangle(x, b, min(x + 16, config.LIP_X), t, *color, filled=True)
        draw_rectangle(config.LIP_X - 4, b, config.LIP_X + 4, t, *config.COLOR_TABLE_EDGE, filled=True)   # 짐받이 턱
        for ol, ob, o_r, ot in self.obstacles:                  # 짐 상자
            draw_rectangle(ol, ob, o_r, ot, *config.COLOR_TABLE, filled=True)
            draw_rectangle(ol, ob, o_r, ob + 8, *config.COLOR_TABLE_EDGE, filled=True)
            draw_line(ol, ob, o_r, ot, *config.COLOR_TABLE_EDGE)
            draw_line(ol, ot, o_r, ob, *config.COLOR_TABLE_EDGE)
        lo, hi = self.door_span()
        if self.door_open:
            draw_rectangle(r, lo, config.WIDTH, hi, *config.COLOR_DOOR_OPEN, filled=True)
        else:
            draw_rectangle(r, lo, config.WIDTH - 6, hi, *config.COLOR_DOOR, filled=True)
