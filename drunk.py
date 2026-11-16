# 술꾼 THE DRUNK ($30, 체력 2). 비틀거리며 플레이어에게 돌진해 몸으로 부딪힌다. 총알은 줍지 않는다 (PRD 8장).
# 대신 가까운 바닥 총알을 빈손 줍줍이에게 차서 넘겨 준다 (패스). 총알을 쓰지 않는 적도 쟁탈전에 끼게 한다.
#   CHARGE -> PASS : 3초 쿨타임이 끝났고, 140px 안에 바닥 총알이 있고, 빈손 줍줍이가 있을 때
#   PASS   -> CHARGE : 총알에 닿아 줍줍이 쪽으로 찼을 때('HEY!'), 또는 총알이 사라지거나 2초가 지났을 때
#   어느 상태든 발차기나 부딪힘 -> STUN -> CHARGE (Enemy 공통)
import math

from pico2d import draw_circle, draw_line

import config
import effect
import game_framework
import game_world
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
    STATES = ['CHARGE', 'PASS']
    TRANSITIONS = [
        {'trigger': 'see_pass', 'source': 'CHARGE', 'dest': 'PASS'},
        {'trigger': 'passed', 'source': 'PASS', 'dest': 'CHARGE'},
        {'trigger': 'give_up', 'source': 'PASS', 'dest': 'CHARGE'},
    ]

    def __init__(self, zone, player, x, y):
        super().__init__(zone, player, x, y)
        self.sway = 0.0            # 비틀거림 위상
        self.pass_cooldown = config.DRUNK_PASS_COOLDOWN
        self.ball = None           # 차려는 바닥 총알

    def empty_pickers(self):
        from picker import Picker  # picker 도 enemy 를 불러서, 함수 안에서 불러 순환을 피한다
        return [o for o in game_world.objects()
                if isinstance(o, Picker) and o.alive and not o.held and o.target is None]

    def pass_plan(self):
        # 패스할 (총알, 받을 줍줍이). 없으면 None
        pickers = self.empty_pickers()
        if not pickers:
            return None
        near = [b for b in self.loose_bullets() if self.distance_to(b) <= config.DRUNK_PASS_RANGE]
        if not near:
            return None
        ball = min(near, key=self.distance_to)
        mate = min(pickers, key=lambda pk: math.hypot(pk.x - ball.x, pk.y - ball.y))
        return ball, mate

    def think(self):
        dt = game_framework.frame_time
        self.pass_cooldown = max(0.0, self.pass_cooldown - dt)
        if self.state == 'CHARGE':
            plan = self.pass_plan() if self.pass_cooldown <= 0 else None
            if plan:
                self.ball = plan[0]
                self.timer = config.DRUNK_PASS_GIVE_UP
                self.see_pass()
                return
            self.sway += dt * config.DRUNK_SWAY_SPEED
            p = self.player
            a = math.atan2(p.y - self.y, p.x - self.x) + math.sin(self.sway) * config.DRUNK_SWAY_ANGLE
            self.move(math.cos(a), math.sin(a), self.SPEED)
        elif self.state == 'PASS':
            self.timer -= dt
            pickers = self.empty_pickers()
            if self.ball is None or not self.ball.is_loose() or not pickers or self.timer <= 0:
                self.stop_passing(passed=False)
            elif self.touching(self.ball, 4):
                mate = min(pickers, key=lambda pk: math.hypot(pk.x - self.ball.x, pk.y - self.ball.y))
                angle = math.atan2(mate.y - self.ball.y, mate.x - self.ball.x)
                self.facing = angle
                self.ball.kick(angle, config.DRUNK_PASS_SPEED)
                effect.spawn(effect.TextPop(self.x, self.y + self.radius + 4, 'HEY!', config.COLOR_DRUNK, 0.6))
                self.stop_passing(passed=True)
            else:
                self.move_toward(self.ball.x, self.ball.y)

    def stop_passing(self, passed):
        self.ball = None
        self.pass_cooldown = config.DRUNK_PASS_COOLDOWN
        if passed:
            self.passed()
        else:
            self.give_up()

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
