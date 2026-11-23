# 보안관(플레이어). 위에서 내려다본 모습: 몸통 원, 모자 원, 마우스 쪽으로 향한 총.
import math

from pico2d import (SDL_BUTTON_LEFT, SDL_BUTTON_RIGHT, SDL_KEYDOWN, SDL_KEYUP, SDL_MOUSEBUTTONDOWN,
                    SDL_MOUSEMOTION, SDLK_SPACE, SDLK_a, SDLK_d, SDLK_s, SDLK_w, draw_circle, draw_line)
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
        self.bounty = 0            # 쓰러뜨린 수배자 현상금 합계 (점수)
        self.kick_cooldown = 0.0   # 다음 발차기까지 남은 시간 (초)
        self.kick_time = 0.0       # 발차기 동작(KICK 상태) 남은 시간 (초)
        self.push = (0.0, 0.0)     # 밀쳐져서 밀려나는 속도 (px/초)
        self.dazed = 0.0           # 밀쳐진 뒤 쏘지 못하는 남은 시간 (초). 이동과 발차기는 된다

        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN', 'KICK'],
            transitions=[
                {'trigger': 'start_run', 'source': 'IDLE', 'dest': 'RUN'},
                {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'start_kick', 'source': ['IDLE', 'RUN'], 'dest': 'KICK'},
                # 발차기가 끝나면 이동 키를 누르고 있는지에 따라 RUN 또는 IDLE 로 (PRD 15-4: Kick -> Idle 0.15초)
                {'trigger': 'end_kick', 'source': 'KICK', 'dest': 'RUN', 'conditions': 'is_moving'},
                {'trigger': 'end_kick', 'source': 'KICK', 'dest': 'IDLE'},
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
        if event.type == SDL_MOUSEBUTTONDOWN and event.x is not None:
            # 클릭한 자리로 조준부터 맞춘다. 시작 직후 마우스를 움직이기 전 첫 클릭이
            # 기본 조준(오른쪽)으로 나가던 버그 (비판 점검에서 발견)
            self.mouse = (event.x, config.HEIGHT - 1 - event.y)
            self.update_aim()
        if event.type == SDL_KEYDOWN and event.key in MOVE_KEYS:
            self.pressed.add(event.key)
        elif event.type == SDL_KEYUP and event.key in MOVE_KEYS:
            self.pressed.discard(event.key)
        elif event.type == SDL_MOUSEMOTION:
            self.mouse = (event.x, config.HEIGHT - 1 - event.y)  # SDL 은 좌상단 원점이라 뒤집는다
        elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
            self.fire()
        elif (event.type == SDL_KEYDOWN and event.key == SDLK_SPACE) or                 (event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_RIGHT):
            self.kick()
        self.update_run_state()

    def gun_reach(self):
        return self.radius + 10    # 몸 중심에서 총구까지 거리

    def fire(self):
        if self.fire_cooldown > 0:
            return None
        if self.dazed > 0:
            # 밀쳐진 직후: 바로 쏘면 총알을 줍는 줍줍이를 코앞에서 쏴 빼앗기가 의미 없어진다 (사용자 제안)
            self.fire_cooldown = config.FIRE_COOLDOWN
            effect.spawn(effect.TextPop(self.x, self.y + self.radius + 6, 'DAZED', config.COLOR_BULLET_ENEMY,
                                        self.dazed))
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
        effect.spawn(effect.MuzzleFlash(bullet.x, bullet.y, self.aim))
        bullet.add_to_world()
        self.fire_cooldown = config.FIRE_COOLDOWN
        return bullet

    def dry_fire(self):
        # 빈 총: 아무것도 안 나가면 클릭이 씹힌 건지 총알이 없는 건지 알 수 없어서 알려 준다
        self.dry_flash = config.DRY_FLASH_TIME
        self.fire_cooldown = config.FIRE_COOLDOWN   # 연타해도 글자가 겹겹이 쌓이지 않게
        effect.spawn(effect.TextPop(self.x, self.y + self.radius + 6, 'CLICK', config.COLOR_CROSSHAIR))

    def kick(self):
        # 발차기 (PRD 6장): 데미지 없음. 조준 방향 앞 부채꼴 안의 적을 밀치고 기절시키며,
        # 줍기를 끊고 1발을 떨어뜨리게 한다. 부채꼴 안의 바닥 총알은 조준 방향으로 굴린다.
        if self.kick_cooldown > 0 or self.state == 'KICK':
            return False
        self.update_aim()
        self.kick_cooldown = config.KICK_COOLDOWN
        self.kick_time = config.KICK_TIME
        self.start_kick()
        from bullet import Bullet
        from enemy import Enemy
        # 찰 수 있는 것은 적과 총알뿐이다 (연출 Ring 처럼 x, radius 를 가진 다른 오브젝트는 제외)
        targets = [o for o in game_world.objects() if isinstance(o, (Enemy, Bullet)) and self.in_kick_fan(o)]
        floor = [o for o in targets if isinstance(o, Bullet) and o.state == 'FLOOR']
        for o in targets:
            if isinstance(o, Enemy):
                o.on_kicked(self.aim)
        for b in floor:            # 적이 떨어뜨린 총알은 굴리지 않고, 원래 바닥에 있던 것만 굴린다
            b.kick(self.aim)
        effect.spawn(effect.KickArc(self.x, self.y, self.aim))
        return True

    def in_kick_fan(self, o):
        dx, dy = o.x - self.x, o.y - self.y
        d = math.hypot(dx, dy)
        if d > self.radius + config.KICK_RANGE + o.radius:
            return False
        if d <= self.radius + o.radius:
            return True            # 몸에 붙어 있으면 방향과 상관없이 찬다
        diff = (math.atan2(dy, dx) - self.aim + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) <= math.radians(config.KICK_HALF_ANGLE)

    def is_moving(self):
        return self.direction() != (0.0, 0.0)

    def update_run_state(self):
        if self.state == 'KICK':
            return                 # 발차기 중에는 끝날 때 end_kick 이 정한다
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
        self.kick_cooldown = max(0.0, self.kick_cooldown - game_framework.frame_time)
        self.dazed = max(0.0, self.dazed - game_framework.frame_time)
        if self.state == 'KICK':
            self.kick_time -= game_framework.frame_time
            if self.kick_time <= 0:
                self.end_kick()
        px, py = self.push
        if (px, py) != (0.0, 0.0):          # 밀쳐져서 밀려나는 중 (점점 줄어든다)
            dt = game_framework.frame_time
            self.x, self.y = self.zone.push_out(self.x + px * dt, self.y + py * dt, self.radius)
            self.push = (px * 0.85, py * 0.85) if math.hypot(px, py) > 10 else (0.0, 0.0)
        if self.state in ('RUN', 'KICK'):   # 발차기 중에도 걷던 방향으로는 계속 움직인다
            dx, dy = self.direction()
            step = config.PLAYER_SPEED * game_framework.frame_time
            self.x, self.y = self.zone.push_out(self.x + dx * step, self.y + dy * step, self.radius)
        self.update_aim()          # 움직여도 마우스를 계속 바라본다

    def velocity(self):
        # 지금 움직이는 속도 (px/초). 적이 조준을 예측할 때 쓴다.
        if self.state == 'IDLE':
            return 0.0, 0.0
        dx, dy = self.direction()
        return dx * config.PLAYER_SPEED, dy * config.PLAYER_SPEED

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
        if self.state == 'KICK':  # 차는 발: 몸에서 조준 방향으로 뻗는 굵은 선
            reach = self.radius + config.KICK_RANGE * 0.6
            for o in (-2, -1, 0, 1, 2):
                draw_line(self.x - cy * o, self.y + cx * o, self.x + cx * reach - cy * o,
                          self.y + cy * reach + cx * o, *config.COLOR_BOOT)
        draw_circle(self.x, self.y, self.radius, *config.COLOR_PLAYER, filled=True)
        draw_circle(self.x, self.y, self.radius - 5, *config.COLOR_HAT, filled=True)
        if self.dazed > 0:        # 밀쳐져 경직: 머리 위를 도는 별 두 개 (적 기절 표시와 같은 모양)
            a = self.dazed * 14
            for k in (0, math.pi):
                draw_circle(self.x + math.cos(a + k) * 10, self.y + self.radius + 5 + math.sin(a + k) * 3, 2,
                            *config.COLOR_FLASH, filled=True)
        for i in range(self.zone.ammo):  # 발밑에 남은 총알 표시 (구역 총알 수만큼)
            color = config.COLOR_BULLET_FLOOR if i < len(self.held) else config.COLOR_AMMO_EMPTY
            draw_circle(self.x - 15 + i * 6, self.y - self.radius - 8, 2, *color, filled=True)

    def get_bb(self):
        r = self.radius
        return self.x - r, self.y - r, self.x + r, self.y + r

    def handle_collision(self, group, other):
        if group != 'player:bullet':
            return
        if other.state == 'FLYING':
            # 튕긴 총알은 누구 것이든, 적이 쏜 총알은 튕기지 않아도 맞는다 (PRD 15-5).
            # 이번 프레임에 지나온 길 중 가장 가까운 점으로 판정해서 느린 프레임에도 뚫고 지나가지 않는다.
            if not (other.can_hit_anyone() or other.owner != 'player'):
                return
            d, (hx, hy) = other.closest_on_path(self.x, self.y)
            if d <= self.radius + other.radius:
                self.hurt()
                other.hit_at(hx, hy, self)   # 맞힌 총알은 그 자리에 떨어지고, 나는 1초 동안 못 줍는다
            return
        if math.hypot(other.x - self.x, other.y - self.y) > self.radius + other.radius + config.PICKUP_REACH:
            return                 # 사각형은 겹쳐도 원끼리는 닿지 않음 (대각선 모서리)
        if other.can_be_picked_by(self):
            self.pick_up(other)

    def shoved(self, angle, x, y):
        # 빈손 줍줍이에게 밀침: angle 쪽으로 밀려나고, 손의 총알 1발이 (x, y)(줍줍이 발밑)에 떨어진다.
        # 플레이어는 밀려나서 바로 다시 줍지 못하고, 줍줍이가 줍는 0.25초 사이에 발차기로 끊을 수 있다.
        if not self.held:
            return False
        b = self.held.pop()
        b.drop(x, y)
        b.add_to_world()
        self.push = (math.cos(angle) * config.SHOVE_PUSH_SPEED, math.sin(angle) * config.SHOVE_PUSH_SPEED)
        self.dazed = config.SHOVE_DAZE_TIME
        effect.spawn(effect.Ring(b.x, b.y, config.COLOR_BULLET_ENEMY, 5, 16, 0.25))
        return True

    def pick_up(self, bullet):
        bullet.pick_up()
        game_world.remove_object(bullet)
        self.held.append(bullet)
        effect.spawn(effect.pickup_ring(bullet.x, bullet.y))

    def hurt(self):
        if self.invincible > 0 or self.hp <= 0:
            return
        self.hp -= 1
        self.invincible = config.INVINCIBLE_TIME
        effect.spawn(effect.hit_ring(self.x, self.y))
