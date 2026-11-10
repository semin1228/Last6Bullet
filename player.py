# 보안관(플레이어). 위에서 내려다본 모습: 몸통 원, 모자 원, 마우스 쪽으로 향한 총.
import math

from pico2d import (SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN,
                    SDL_MOUSEMOTION, SDLK_a, SDLK_d, SDLK_s, SDLK_w, draw_circle, draw_line)
from transitions import Machine

import config
import game_framework
import game_world

MOVE_KEYS = {SDLK_w: (0, 1), SDLK_s: (0, -1), SDLK_a: (-1, 0), SDLK_d: (1, 0)}


class Player:
    def __init__(self, zone, x, y):
        self.zone = zone
        self.x, self.y = x, y
        self.radius = config.PLAYER_RADIUS
        self.mouse = (x + 1, y)    # 마지막 마우스 위치 (게임 좌표)
        self.aim = 0.0             # 조준 각도 (라디안, 오른쪽이 0)
        self.pressed = set()
        self.held = []             # 손에 든 총알 (HELD 상태의 Bullet)
        self.fire_cooldown = 0.0

        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN'],
            transitions=[
                {'trigger': 'start_run', 'source': 'IDLE', 'dest': 'RUN'},
                {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
        )

    def direction(self):
        dx = sum(MOVE_KEYS[k][0] for k in self.pressed)
        dy = sum(MOVE_KEYS[k][1] for k in self.pressed)
        length = math.hypot(dx, dy)
        if length == 0:
            return 0.0, 0.0
        return dx / length, dy / length  # 대각선도 같은 속도가 되도록 길이를 1로 맞춘다

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN and event.key in MOVE_KEYS:
            self.pressed.add(event.key)
        elif event.type == SDL_KEYUP and event.key in MOVE_KEYS:
            self.pressed.discard(event.key)
        elif event.type == SDL_MOUSEMOTION:
            self.mouse = (event.x, config.HEIGHT - 1 - event.y)  # SDL 은 좌상단 원점이라 뒤집는다
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.fire()
        self.update_run_state()

    def gun_tip(self):
        reach = self.radius + 10
        return self.x + math.cos(self.aim) * reach, self.y + math.sin(self.aim) * reach

    def fire(self):
        if not self.held or self.fire_cooldown > 0:
            return None
        bullet = self.held.pop()
        bullet.fire(*self.gun_tip(), self.aim, 'player')
        game_world.add_object(bullet, 1)
        game_world.add_collision_pair('player:bullet', None, bullet)
        self.fire_cooldown = config.FIRE_COOLDOWN
        return bullet

    def update_run_state(self):
        moving = self.direction() != (0.0, 0.0)
        if moving and self.state == 'IDLE':
            self.start_run()
        elif not moving and self.state == 'RUN':
            self.stop_run()

    def release_all_keys(self):
        # 다른 모드가 위에 올라와 키업을 놓쳤을 때, 모든 키를 뗀 것으로 처리
        self.pressed.clear()
        self.update_run_state()

    def update(self):
        self.fire_cooldown = max(0.0, self.fire_cooldown - game_framework.frame_time)
        if self.state == 'RUN':
            dx, dy = self.direction()
            step = config.PLAYER_SPEED * game_framework.frame_time
            self.x, self.y = self.zone.push_out(self.x + dx * step, self.y + dy * step, self.radius)
        mx, my = self.mouse
        if (mx, my) != (self.x, self.y):
            self.aim = math.atan2(my - self.y, mx - self.x)  # 움직여도 마우스를 계속 바라본다

    def draw(self):
        cx, cy = math.cos(self.aim), math.sin(self.aim)
        gx, gy = self.x + cx * (self.radius + 10), self.y + cy * (self.radius + 10)
        for o in (-1, 0, 1):  # 두께 3px 총신
            draw_line(self.x - cy * o, self.y + cx * o, gx - cy * o, gy + cx * o, *config.COLOR_GUN)
        draw_circle(self.x, self.y, self.radius, *config.COLOR_PLAYER, filled=True)
        draw_circle(self.x, self.y, self.radius - 5, *config.COLOR_HAT, filled=True)
        for i in range(config.AMMO):  # 발밑에 남은 총알 표시 (리볼버 여섯 칸)
            color = config.COLOR_BULLET_FLOOR if i < len(self.held) else config.COLOR_AMMO_EMPTY
            draw_circle(self.x - 15 + i * 6, self.y - self.radius - 8, 2, *color, filled=True)

    def get_bb(self):
        r = self.radius
        return self.x - r, self.y - r, self.x + r, self.y + r

    def handle_collision(self, group, other):
        pass
