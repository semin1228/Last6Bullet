# 총알 한 발. 구역을 시작할 때만 만들고, 이후에는 상태만 바뀐다 (PRD 15-4).
#   HELD: 누군가의 손에 있음. 월드에 없고 그리지 않는다.
#   FLYING: 날아가는 중
#   FLOOR: 바닥에 멈춤. 지나가면 주울 수 있다.
import math

from pico2d import draw_circle
from transitions import Machine

import config
import game_framework


class Bullet:
    def __init__(self, zone):
        self.zone = zone
        self.x, self.y = 0.0, 0.0
        self.vx, self.vy = 0.0, 0.0
        self.radius = config.BULLET_RADIUS
        self.owner = None          # 마지막으로 쏜 쪽 ('player' 등)
        self.age = 0.0             # 날아간 시간 (초)
        self.bounces = 0           # 벽이나 장애물에 튕긴 횟수

        self.machine = Machine(
            model=self,
            states=['HELD', 'FLYING', 'FLOOR'],
            transitions=[
                {'trigger': 'fire', 'source': 'HELD', 'dest': 'FLYING', 'before': 'launch'},
                {'trigger': 'land', 'source': 'FLYING', 'dest': 'FLOOR'},
                {'trigger': 'pick_up', 'source': 'FLOOR', 'dest': 'HELD'},
            ],
            initial='HELD',
            auto_transitions=False,
        )

    def launch(self, x, y, angle, owner):
        self.x, self.y = x, y
        self.vx = math.cos(angle) * config.BULLET_SPEED
        self.vy = math.sin(angle) * config.BULLET_SPEED
        self.owner = owner
        self.age = 0.0
        self.bounces = 0

    def on_enter_FLOOR(self):
        self.vx = self.vy = 0.0

    def update(self):
        if self.state != 'FLYING':
            return
        dt = game_framework.frame_time
        self.age += dt
        # 한 프레임 이동을 BULLET_SUBSTEP 이하로 나눠 움직여서 얇은 벽을 뚫고 지나가지 않게 한다
        distance = math.hypot(self.vx, self.vy) * dt
        steps = max(1, math.ceil(distance / config.BULLET_SUBSTEP))
        for _ in range(steps):
            self.x += self.vx * dt / steps
            self.y += self.vy * dt / steps
            if self.zone.bounce(self):
                self.bounces += 1
                if self.bounces > config.MAX_BOUNCES:
                    self.land()
                    return
        if self.age >= config.BULLET_LIFE:
            self.land()

    def draw(self):
        if self.state == 'FLYING':
            color = config.COLOR_BULLET_BOUNCED if self.bounces else config.COLOR_BULLET_PLAYER
            draw_circle(self.x, self.y, self.radius, *color, filled=True)
        elif self.state == 'FLOOR':
            draw_circle(self.x, self.y, self.radius + 2, *config.COLOR_BULLET_EDGE, filled=True)
            draw_circle(self.x, self.y, self.radius, *config.COLOR_BULLET_FLOOR, filled=True)

    def can_hit_anyone(self):
        # 튕긴 총알은 쏜 사람까지 누구든 맞는다 (PRD 3장 규칙 5). 발사 직후는 제외한다.
        return self.state == 'FLYING' and self.bounces > 0 and self.age > config.HIT_GRACE

    def get_bb(self):
        r = self.radius
        return self.x - r, self.y - r, self.x + r, self.y + r

    def handle_collision(self, group, other):
        pass
