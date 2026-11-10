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

    def on_enter_FLOOR(self):
        self.vx = self.vy = 0.0

    def update(self):
        if self.state != 'FLYING':
            return
        dt = game_framework.frame_time
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        x, y = self.zone.push_out(self.x, self.y, self.radius)
        if (x, y) != (self.x, self.y):  # 벽에 닿으면 그 자리에 떨어진다 (반사는 다음 단계)
            self.x, self.y = x, y
            self.land()
        elif self.age >= config.BULLET_LIFE:
            self.land()

    def draw(self):
        if self.state == 'FLYING':
            draw_circle(self.x, self.y, self.radius, *config.COLOR_BULLET_PLAYER, filled=True)
        elif self.state == 'FLOOR':
            draw_circle(self.x, self.y, self.radius + 2, *config.COLOR_BULLET_EDGE, filled=True)
            draw_circle(self.x, self.y, self.radius, *config.COLOR_BULLET_FLOOR, filled=True)

    def get_bb(self):
        r = self.radius
        return self.x - r, self.y - r, self.x + r, self.y + r

    def handle_collision(self, group, other):
        pass
