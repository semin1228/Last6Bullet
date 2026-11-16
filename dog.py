# 들개 THE HOUND ($20, 체력 1). 빠르게 달려가 바닥 총알을 삼킨다. 쏘지는 않는다 (PRD 8장).
#   SEEK -> PICK -> SEEK (삼킨 총알은 몸 안에 보관), 주울 총알이 없거나 배가 차면(DOG_MAX_SWALLOW) ROAM(어슬렁거림)
#   배가 찬 들개는 느리게 어슬렁거리므로 쫓아가 차기 쉽다 (혼자 구역 총알을 다 가져가 판이 막히지 않게)
#   발차기에 맞으면 STUN, 삼킨 총알을 모두 토해 낸다. 몸으로 부딪히면 플레이어 체력 -1.
import math
import random

from pico2d import draw_circle

import config
import game_framework
from enemy import Enemy


class Dog(Enemy):
    NAME = 'THE HOUND'
    RADIUS = 11
    SPEED = config.DOG_SPEED
    HP = 1
    BOUNTY = 20
    COLOR = config.COLOR_DOG
    TOUCH_DAMAGE = True
    START = 'SEEK'
    STATES = ['SEEK', 'PICK', 'ROAM']
    TRANSITIONS = [
        {'trigger': 'reach_bullet', 'source': 'SEEK', 'dest': 'PICK'},
        {'trigger': 'swallowed', 'source': 'PICK', 'dest': 'SEEK'},
        {'trigger': 'lost_bullet', 'source': 'PICK', 'dest': 'SEEK'},
        {'trigger': 'nothing_to_pick', 'source': 'SEEK', 'dest': 'ROAM'},
        {'trigger': 'bullet_appeared', 'source': 'ROAM', 'dest': 'SEEK'},
    ]

    def __init__(self, zone, player, x, y):
        super().__init__(zone, player, x, y)
        self.roam_to = (x, y)

    def full(self):
        return len(self.held) >= config.DOG_MAX_SWALLOW

    def kick_drop_count(self):
        return len(self.held)      # 차면 삼킨 총알을 모두 토해 낸다

    def think(self):
        if self.state == 'SEEK':
            b = None if self.full() else self.nearest_loose_bullet()
            if b is None:
                self.nothing_to_pick()
            elif self.touching(b):
                self.start_pick(b)
                self.reach_bullet()
            else:
                self.move_toward(b.x, b.y)
        elif self.state == 'PICK':
            done = self.pick_done()
            if done:
                self.swallowed()
            elif done is False:
                self.lost_bullet()
        elif self.state == 'ROAM':
            if not self.full() and self.nearest_loose_bullet() is not None:
                self.bullet_appeared()
                return
            self.timer -= game_framework.frame_time
            tx, ty = self.roam_to
            if self.timer <= 0 or math.hypot(tx - self.x, ty - self.y) < 10:
                l, b, r, t = self.zone.inner
                self.roam_to = (random.uniform(l + 40, r - 40), random.uniform(b + 40, t - 40))
                self.timer = config.DOG_ROAM_TIME
            self.move_toward(*self.roam_to, config.DOG_ROAM_SPEED)

    def draw_body(self, cx, cy):
        # 들개: 몸통 원 + 바라보는 쪽 머리 원 + 귀
        hx, hy = self.x + cx * (self.radius + 3), self.y + cy * (self.radius + 3)
        draw_circle(self.x, self.y, self.radius, *self.COLOR, filled=True)
        draw_circle(hx, hy, 7, *self.COLOR, filled=True)
        draw_circle(hx - cy * 5, hy + cx * 5, 2, *config.COLOR_DOG_EAR, filled=True)
        draw_circle(hx + cy * 5, hy - cx * 5, 2, *config.COLOR_DOG_EAR, filled=True)
