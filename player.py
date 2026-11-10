# 보안관(플레이어). 위에서 내려다본 모습: 몸통 원, 모자 원, 마우스 쪽으로 향한 총.
import math

from pico2d import (SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN,
                    SDL_MOUSEMOTION, SDLK_a, SDLK_d, SDLK_s, SDLK_w, draw_circle, draw_line)
from transitions import Machine

import config
import effect
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
        self.hp = config.PLAYER_HP
        self.invincible = 0.0      # 남은 무적 시간 (초)
        self.dry_flash = 0.0       # 빈 총을 당긴 뒤 HUD 실린더가 붉게 보이는 남은 시간 (초)

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

    def gun_reach(self):
        return self.radius + 10    # 몸 중심에서 총구까지 거리

    def fire(self):
        if self.fire_cooldown > 0:
            return None
        if not self.held:
            self.dry_fire()
            return None
        self.update_aim()          # 같은 프레임에 마우스를 움직이고 바로 쏴도 새 방향으로 나가게
        bullet = self.held.pop()
        # 총구에서 바로 만들면 벽에 붙어 쏠 때 총구가 벽 너머에 있어 총알이 벽을 건너뛴다.
        # 몸 중심(항상 빈 공간)에서 만들고 총구까지 벽 검사를 하며 옮긴다.
        bullet.fire(self.x, self.y, self.aim, 'player')
        bullet.travel(self.gun_reach())
        game_world.add_object(bullet, 1)
        game_world.add_collision_pair('player:bullet', None, bullet)
        self.fire_cooldown = config.FIRE_COOLDOWN
        return bullet

    def dry_fire(self):
        # 빈 총: 아무것도 안 나가면 클릭이 씹힌 건지 총알이 없는 건지 알 수 없어서 알려 준다
        self.dry_flash = config.DRY_FLASH_TIME
        self.fire_cooldown = config.FIRE_COOLDOWN   # 연타해도 글자가 겹겹이 쌓이지 않게
        effect.spawn(effect.TextPop(self.x, self.y + self.radius + 6, '찰칵', config.COLOR_CROSSHAIR))

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
        self.invincible = max(0.0, self.invincible - game_framework.frame_time)
        self.dry_flash = max(0.0, self.dry_flash - game_framework.frame_time)
        if self.state == 'RUN':
            dx, dy = self.direction()
            step = config.PLAYER_SPEED * game_framework.frame_time
            self.x, self.y = self.zone.push_out(self.x + dx * step, self.y + dy * step, self.radius)
        self.update_aim()          # 움직여도 마우스를 계속 바라본다

    def update_aim(self):
        mx, my = self.mouse
        if (mx, my) != (self.x, self.y):
            self.aim = math.atan2(my - self.y, mx - self.x)

    def draw(self):
        if self.invincible > 0 and int(self.invincible * 10) % 2:
            return                 # 무적 중에는 깜빡인다
        cx, cy = math.cos(self.aim), math.sin(self.aim)
        gx, gy = self.x + cx * self.gun_reach(), self.y + cy * self.gun_reach()
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
        if group != 'player:bullet':
            return
        if math.hypot(other.x - self.x, other.y - self.y) > self.radius + other.radius + config.PICKUP_REACH:
            return                 # 사각형은 겹쳐도 원끼리는 닿지 않음 (대각선 모서리)
        if other.state == 'FLOOR':
            self.pick_up(other)
        elif other.can_hit_anyone():
            self.hurt()
            other.land()           # 맞힌 총알은 그 자리에 떨어진다

    def pick_up(self, bullet):
        bullet.pick_up()
        game_world.remove_object(bullet)
        self.held.append(bullet)

    def hurt(self):
        if self.invincible > 0 or self.hp <= 0:
            return
        self.hp -= 1
        self.invincible = config.INVINCIBLE_TIME
