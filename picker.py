# 줍줍이 THE PICKER ($50, 체력 1). 바닥 총알을 주워서 거리를 두고 쏜다. 총알이 없으면 도망친다 (PRD 8장).
#   SEEK -> PICK(바닥 총알에 닿음) -> SHOOT(줍기 완료) -> SEEK(총알 다 씀)
#   SEEK -> FLEE(주울 총알도, 가진 총알도 없음) -> SEEK(바닥 총알 생김)
#   어느 상태든 발차기 -> STUN(0.7초) -> SEEK
#   빈손일 때(SEEK, FLEE) 플레이어에게 닿으면 밀쳐서 플레이어 총알 1발을 발밑에 떨어뜨리게 한다 (1.5초 간격).
#   총알을 쥐고 쫓아가 가까이에서 쏘는 것만 하면 위험이 없던 문제를 막는다 (기획서 리뷰 반영).
import math

from pico2d import draw_circle, draw_line

import config
import effect
import game_framework
from enemy import Enemy


class Picker(Enemy):
    NAME = 'THE PICKER'
    SPEED = config.PICKER_SPEED
    HP = 1
    BOUNTY = 50
    COLOR = config.COLOR_PICKER
    START = 'SEEK'
    STATES = ['SEEK', 'PICK', 'SHOOT', 'FLEE']
    TRANSITIONS = [
        {'trigger': 'reach_bullet', 'source': 'SEEK', 'dest': 'PICK'},
        {'trigger': 'picked', 'source': 'PICK', 'dest': 'SHOOT'},
        {'trigger': 'lost_bullet', 'source': 'PICK', 'dest': 'SEEK'},
        {'trigger': 'out_of_ammo', 'source': 'SHOOT', 'dest': 'SEEK'},
        {'trigger': 'nothing_to_pick', 'source': 'SEEK', 'dest': 'FLEE'},
        {'trigger': 'bullet_appeared', 'source': 'FLEE', 'dest': 'SEEK'},
        {'trigger': 'armed', 'source': 'SEEK', 'dest': 'SHOOT'},
    ]

    def __init__(self, zone, player, x, y):
        super().__init__(zone, player, x, y)
        self.shove_cooldown = 0.0

    def try_shove(self):
        # 빈손이고, 총알을 가진 플레이어가 몸에 닿았으면 밀친다
        p = self.player
        if self.held or not p.held or self.shove_cooldown > 0 or not self.touching(p, config.SHOVE_REACH):
            return False
        angle = math.atan2(p.y - self.y, p.x - self.x)
        self.facing = angle
        p.shoved(angle, self.x, self.y)
        self.shove_cooldown = config.SHOVE_COOLDOWN
        effect.spawn(effect.TextPop(self.x, self.y + self.radius + 4, 'SHOVE', config.COLOR_BULLET_ENEMY))
        return True

    def after_recover(self):
        if self.held:              # 기절에서 깨어났는데 총알이 남아 있으면 바로 쏘러 간다
            self.armed()

    def think(self):
        p = self.player
        self.shove_cooldown = max(0.0, self.shove_cooldown - game_framework.frame_time)
        if self.state in ('SEEK', 'FLEE') and self.try_shove():
            return
        if self.state == 'SEEK':
            b = self.nearest_loose_bullet()
            if b is None:
                if self.held:
                    self.armed()
                else:
                    self.nothing_to_pick()
            elif self.touching(b):
                self.start_pick(b)
                self.reach_bullet()
            else:
                self.move_toward(b.x, b.y)
        elif self.state == 'PICK':
            done = self.pick_done()
            if done:
                self.timer = config.PICKER_FIRST_SHOT   # 줍자마자 쏘지 않고 잠깐 겨눈다
                self.picked()
            elif done is False:
                self.lost_bullet()
        elif self.state == 'SHOOT':
            d = self.distance_to(p)
            if d < config.PICKER_KEEP_NEAR:
                self.move_away(p.x, p.y)
            elif d > config.PICKER_KEEP_FAR:
                self.move_toward(p.x, p.y)
            self.facing = self.aim_at_player(config.ENEMY_BULLET_SPEED)
            self.timer -= game_framework.frame_time
            if self.timer <= 0:
                self.shoot()
                self.timer = config.PICKER_SHOOT_INTERVAL
            if not self.held:
                self.out_of_ammo()
        elif self.state == 'FLEE':
            if self.nearest_loose_bullet() is not None:
                self.bullet_appeared()
            else:
                self.move_away(p.x, p.y)

    def draw_body(self, cx, cy):
        # 줍줍이: 녹색 몸, 붉은 두건, 짧은 총
        gx, gy = self.x + cx * (self.radius + 7), self.y + cy * (self.radius + 7)
        draw_line(self.x, self.y, gx, gy, *config.COLOR_GUN)
        draw_line(self.x + 1, self.y, gx + 1, gy, *config.COLOR_GUN)
        draw_circle(self.x, self.y, self.radius, *self.COLOR, filled=True)
        draw_circle(self.x, self.y, self.radius - 5, *config.COLOR_BANDANA, filled=True)
