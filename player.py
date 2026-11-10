# 보안관(플레이어). 위에서 내려다본 모습: 몸통 원과 모자 원.
import math

from pico2d import SDL_KEYDOWN, SDL_KEYUP, SDLK_a, SDLK_d, SDLK_s, SDLK_w, draw_circle
from transitions import Machine

import config
import game_framework

MOVE_KEYS = {SDLK_w: (0, 1), SDLK_s: (0, -1), SDLK_a: (-1, 0), SDLK_d: (1, 0)}


class Player:
    def __init__(self, zone, x, y):
        self.zone = zone
        self.x, self.y = x, y
        self.radius = config.PLAYER_RADIUS
        self.pressed = set()

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
        self.update_run_state()

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
        if self.state == 'RUN':
            dx, dy = self.direction()
            step = config.PLAYER_SPEED * game_framework.frame_time
            self.x, self.y = self.zone.push_out(self.x + dx * step, self.y + dy * step, self.radius)

    def draw(self):
        draw_circle(self.x, self.y, self.radius, *config.COLOR_PLAYER, filled=True)
        draw_circle(self.x, self.y, self.radius - 5, *config.COLOR_HAT, filled=True)

    def get_bb(self):
        r = self.radius
        return self.x - r, self.y - r, self.x + r, self.y + r

    def handle_collision(self, group, other):
        pass
