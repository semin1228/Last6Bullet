# 술꾼 THE DRUNK ($30, 체력 2). 비틀거리며 플레이어에게 돌진해 몸으로 부딪힌다. 총알은 줍지 않는다 (PRD 8장).
#   CHARGE <-> STUN : 부딪히거나 발차기에 맞으면 STUN, 깨어나면 다시 CHARGE
import math

from pico2d import draw_circle, draw_line

import config
import game_framework
from enemy import Enemy


class Drunk(Enemy):
    NAME = 'THE DRUNK'
    RADIUS = 15
    SPEED = config.DRUNK_SPEED
    HP = 2
    BOUNTY = 30
    COLOR = config.COLOR_DRUNK
    TOUCH_DAMAGE = True
    START = 'CHARGE'
    STATES = ['CHARGE']
    TRANSITIONS = [
        {'trigger': 'bump', 'source': 'CHARGE', 'dest': 'STUN'},
    ]

    def __init__(self, zone, player, x, y):
        super().__init__(zone, player, x, y)
        self.sway = 0.0            # 비틀거림 위상

    def think(self):
        self.sway += game_framework.frame_time * config.DRUNK_SWAY_SPEED
        p = self.player
        a = math.atan2(p.y - self.y, p.x - self.x) + math.sin(self.sway) * config.DRUNK_SWAY_ANGLE
        self.move(math.cos(a), math.sin(a), self.SPEED)

    def on_touch_player(self):
        # 부딪힌 뒤에는 튕겨 나가 잠깐 멈춘다 (붙어서 계속 때리지 않게)
        p = self.player
        a = math.atan2(self.y - p.y, self.x - p.x)
        self.bump()
        self.timer = config.BUMP_STUN_TIME
        self.push = (math.cos(a) * config.KICK_PUSH_SPEED, math.sin(a) * config.KICK_PUSH_SPEED)

    def draw_body(self, cx, cy):
        # 술꾼: 보라색 큰 몸, 손에 든 술병
        bx, by = self.x + cx * (self.radius + 6) - cy * 6, self.y + cy * (self.radius + 6) + cx * 6
        draw_line(self.x - cy * 6, self.y + cx * 6, bx, by, *config.COLOR_BOTTLE)
        draw_circle(bx, by, 3, *config.COLOR_BOTTLE, filled=True)
        draw_circle(self.x, self.y, self.radius, *self.COLOR, filled=True)
        draw_circle(self.x, self.y, self.radius - 6, *config.COLOR_HAT, filled=True)
        for i in range(self.HP):   # 체력 2칸 (맞으면 하나 빈다)
            color = config.COLOR_HP if i < self.hp else config.COLOR_HP_EMPTY
            draw_circle(self.x - 4 + i * 8, self.y - self.radius - 6, 2, *color, filled=True)
