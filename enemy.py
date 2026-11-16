# 적 공통 부모 (PRD 15-3 Enemy). 가까운 바닥 총알 찾기, 줍기 동작(PINNED), 기절, 맞기, 쓰러질 때 총알 떨어뜨리기.
# 행동(상태 머신)은 Picker / Drunk / Dog 가 각자 정한다. 모든 적은 STUN 상태를 갖고,
# 'stagger' 트리거로 어느 상태에서든(줍는 중 포함) STUN 에 들어가며 'recover' 로 처음 상태로 돌아간다.
# 발차기에 맞을 때와 몸으로 부딪힌 뒤 튕겨 나갈 때 모두 stagger 를 쓴다.
import math
import random

from pico2d import draw_circle, draw_line
from transitions import Machine

import config
import effect
import game_framework
import game_world
from bullet import Bullet


class Enemy:
    NAME = 'ENEMY'
    RADIUS = 13
    SPEED = 120
    HP = 1
    BOUNTY = 0
    COLOR = (95, 94, 90)
    TOUCH_DAMAGE = False           # 몸으로 부딪히면 플레이어 체력 -1 (술꾼, 들개)
    START = 'SEEK'
    STATES = ['SEEK']
    TRANSITIONS = []

    def __init__(self, zone, player, x, y):
        self.zone, self.player = zone, player
        self.x, self.y = zone.push_out(x, y, self.RADIUS)
        self.radius = self.RADIUS
        self.hp = self.HP
        self.held = []             # 주운 총알 (HELD)
        self.facing = math.pi      # 바라보는 방향 (처음엔 왼쪽: 보통 오른쪽에서 등장)
        self.timer = 0.0           # 상태마다 쓰는 남은 시간 (줍기, 기절, 사격 간격 등)
        self.target = None         # 줍는 중인 총알
        self.push = (0.0, 0.0)     # 발차기로 밀려나는 속도
        self.alive = True
        self.flash = 0.0           # 맞은 직후 몸이 하얗게 번쩍이는 남은 시간 (초)
        self.detour = 0.0          # 장애물에 막혔을 때 옆으로 비켜 걷는 남은 시간
        self.detour_dir = (0.0, 0.0)
        self.detour_side = random.choice((-1, 1))   # 비켜 걷는 쪽 (막힐 때마다 바꾸지 않고 유지)
        self.machine = Machine(
            model=self,
            states=self.STATES + ['STUN'],
            transitions=self.TRANSITIONS + [
                {'trigger': 'stagger', 'source': '*', 'dest': 'STUN'},
                {'trigger': 'recover', 'source': 'STUN', 'dest': self.START, 'after': 'after_recover'},
            ],
            initial=self.START,
            auto_transitions=False,
        )

    # ------------------------------------------------------------ 찾기와 움직이기

    def loose_bullets(self):
        return [o for o in game_world.objects() if isinstance(o, Bullet) and o.is_loose()]

    def nearest_loose_bullet(self):
        bullets = self.loose_bullets()
        if not bullets:
            return None
        return min(bullets, key=lambda b: (b.x - self.x) ** 2 + (b.y - self.y) ** 2)

    def distance_to(self, o):
        return math.hypot(o.x - self.x, o.y - self.y)

    def touching(self, o, reach=2):
        return self.distance_to(o) <= self.radius + o.radius + reach

    def move(self, dx, dy, speed):
        # (dx, dy) 방향으로 speed 만큼 움직인다. 장애물 면에 정면으로 막혀 거의 못 가면
        # 테이블 하나를 돌아갈 만큼(DETOUR_DIST) 옆으로 비켜 걷는다. 비켜 걷다가도 막히면 반대쪽으로.
        dt = game_framework.frame_time
        detouring = self.detour > 0
        if detouring:
            self.detour -= dt
            dx, dy = self.detour_dir
        length = math.hypot(dx, dy)
        if length == 0:
            return
        dx, dy = dx / length, dy / length
        self.facing = math.atan2(dy, dx)
        nx, ny = self.zone.push_out(self.x + dx * speed * dt, self.y + dy * speed * dt, self.radius)
        moved = math.hypot(nx - self.x, ny - self.y)
        self.x, self.y = nx, ny
        if moved >= speed * dt * 0.3:
            return
        if detouring:                                   # 비켜 걷는 쪽도 막힘: 반대쪽으로
            self.detour_side = -self.detour_side
            self.detour_dir = (-dx, -dy)
        else:
            side = self.detour_side
            self.detour_dir = (-dy * side, dx * side)   # 가려던 방향의 옆
        self.detour = config.DETOUR_DIST / speed

    def move_toward(self, x, y, speed=None):
        self.move(x - self.x, y - self.y, speed or self.SPEED)

    def move_away(self, x, y, speed=None):
        self.move(self.x - x, self.y - y, speed or self.SPEED)

    def separate(self):
        # 적끼리, 적과 플레이어가 겹치지 않게 서로 밀어 낸다
        others = [o for o in game_world.objects() if isinstance(o, Enemy) and o is not self]
        for o in others + [self.player]:
            d = self.distance_to(o)
            gap = self.radius + o.radius - d
            if gap > 0 and d > 0:
                self.x -= (o.x - self.x) / d * gap / 2
                self.y -= (o.y - self.y) / d * gap / 2
        self.x, self.y = self.zone.push_out(self.x, self.y, self.radius)

    # ------------------------------------------------------------ 줍기 (PRD 3장 규칙 3: 적은 0.25초 동작)

    def start_pick(self, bullet):
        bullet.pin()
        self.target = bullet
        self.timer = config.ENEMY_PICK_TIME

    def pick_done(self):
        # 줍기 시간이 끝났으면 손으로 옮기고 True. 그 사이 총알을 잃었으면(발차기 등) False.
        b = self.target
        if b is None or b.state != 'PINNED':
            self.target = None
            return False
        self.timer -= game_framework.frame_time
        if self.timer > 0:
            return None
        b.pick_up()
        game_world.remove_object(b)
        self.held.append(b)
        self.target = None
        effect.spawn(effect.Ring(b.x, b.y, config.COLOR_BULLET_ENEMY, 5, 16, 0.25))
        return True

    def cancel_pick(self):
        if self.target is not None and self.target.state == 'PINNED':
            self.target.unpin()
        self.target = None

    # ------------------------------------------------------------ 쏘기

    def aim_at_player(self, speed):
        # 플레이어가 움직이는 방향을 일부 예측해서 겨눈다 (PRD 8장, 보통 난이도 '일부')
        px, py = self.player.x, self.player.y
        vx, vy = self.player.velocity()
        t = math.hypot(px - self.x, py - self.y) / speed * config.ENEMY_AIM_LEAD
        return math.atan2(py + vy * t - self.y, px + vx * t - self.x)

    def shoot(self):
        if not self.held:
            return None
        angle = self.aim_at_player(config.ENEMY_BULLET_SPEED)
        self.facing = angle
        b = self.held.pop()
        b.fire(self.x, self.y, angle, self, speed=config.ENEMY_BULLET_SPEED)
        b.travel(self.radius + 8)
        b.add_to_world()
        effect.spawn(effect.MuzzleFlash(b.x, b.y, angle))
        return b

    # ------------------------------------------------------------ 맞기, 발차기, 쓰러지기

    def drop_bullets(self, count):
        for i in range(min(count, len(self.held))):
            b = self.held.pop()
            a = random.uniform(0, 2 * math.pi)
            b.drop(self.x + math.cos(a) * (self.radius + 6), self.y + math.sin(a) * (self.radius + 6))
            b.add_to_world()

    def on_kicked(self, angle):
        # 발차기: 데미지 없음. 밀려나고 0.7초 기절, 줍기는 끊기고 총알 1발을 떨어뜨린다 (PRD 6장)
        if not self.alive:
            return
        self.knock_back(angle, config.ENEMY_STUN_TIME)
        self.drop_bullets(self.kick_drop_count())

    def knock_back(self, angle, stun_time):
        # angle 쪽으로 밀려나며 stun_time 동안 기절. 줍는 중이었으면 줍기가 끊긴다.
        self.cancel_pick()
        self.stagger()
        self.timer = stun_time
        self.push = (math.cos(angle) * config.KICK_PUSH_SPEED, math.sin(angle) * config.KICK_PUSH_SPEED)

    def kick_drop_count(self):
        return config.KICK_DROPS

    def hit_by(self, bullet, point=None):
        angle = math.atan2(bullet.vy, bullet.vx)
        x, y = point or (bullet.x, bullet.y)
        bullet.hit_at(x, y)        # 맞힌 총알은 그 자리에 떨어진다 (PRD 3장 규칙 2)
        self.hp -= 1
        self.flash = config.HIT_FLASH_TIME
        effect.spawn(effect.Ring(self.x, self.y, self.COLOR, 14, 30, 0.25))
        if self.hp <= 0:
            self.die()
        else:
            self.on_hit_survived(angle)

    def on_hit_survived(self, angle):
        # 맞고 버틴 적 (술꾼, 3주차 두목). 종류마다 반응을 정한다.
        pass

    def die(self):
        self.alive = False
        self.cancel_pick()
        self.drop_bullets(len(self.held))   # 쓰러지면 가진 총알을 모두 떨어뜨린다
        self.player.bounty += self.BOUNTY
        effect.spawn(effect.TextPop(self.x, self.y + self.radius + 4, '$%d' % self.BOUNTY, config.COLOR_BOUNTY, 0.8))
        game_world.remove_object(self)

    def can_be_hit_by(self, bullet):
        # 플레이어 총알은 바로, 적 총알은 튕긴 뒤에만 (쏜 적 자신도 포함)
        if bullet.state != 'FLYING':
            return False
        return bullet.owner == 'player' or bullet.can_hit_anyone()

    def handle_collision(self, group, other):
        if not self.alive:
            return
        if group == 'enemy:bullet':
            if self.can_be_hit_by(other):
                d, point = other.closest_on_path(self.x, self.y)   # 이번 프레임에 지나온 길 전체로 판정
                if d <= self.radius + other.radius:
                    self.hit_by(other, point)
        elif group == 'player:enemy':
            # 서로 밀어 내서 딱 붙은 거리에 있으므로 3px 여유를 둔다
            if self.TOUCH_DAMAGE and self.state != 'STUN' and self.touching(other, 3):
                other.hurt()
                self.on_touch_player()

    def on_touch_player(self):
        # 부딪힌 뒤에는 튕겨 나가 잠깐 멈춘다 (붙어서 계속 때리지 않게)
        p = self.player
        self.knock_back(math.atan2(self.y - p.y, self.x - p.x), config.BUMP_STUN_TIME)

    def after_recover(self):
        # 기절에서 깨어난 직후 (트리거 이름과 같은 메서드를 만들면 transitions 가 트리거를 붙이지 않아서 따로 둔다)
        pass

    # ------------------------------------------------------------ 매 프레임

    def update(self):
        if not self.alive:
            return
        dt = game_framework.frame_time
        self.flash = max(0.0, self.flash - dt)
        if self.state == 'STUN':
            px, py = self.push
            self.x, self.y = self.zone.push_out(self.x + px * dt, self.y + py * dt, self.radius)
            self.push = (px * 0.85, py * 0.85)
            self.timer -= dt
            if self.timer <= 0:
                self.recover()
        else:
            self.think()
        self.separate()

    def think(self):
        pass

    def get_bb(self):
        r = self.radius
        return self.x - r, self.y - r, self.x + r, self.y + r

    def draw(self):
        cx, cy = math.cos(self.facing), math.sin(self.facing)
        self.draw_body(cx, cy)
        if self.flash > 0:                  # 맞은 순간: 몸 전체가 하얗게 번쩍인다
            draw_circle(self.x, self.y, self.radius, *config.COLOR_HIT_FLASH, filled=True)
        for i in range(len(self.held)):     # 가진 총알 수 (머리 위 점)
            draw_circle(self.x - (len(self.held) - 1) * 3 + i * 6, self.y + self.radius + 6, 2,
                        *config.COLOR_BULLET_FLOOR, filled=True)
        if self.state == 'STUN':            # 기절: 머리 위를 도는 별 두 개
            a = self.timer * 12
            for k in (0, math.pi):
                draw_circle(self.x + math.cos(a + k) * 9, self.y + self.radius + 4 + math.sin(a + k) * 3, 2,
                            *config.COLOR_FLASH, filled=True)
        if self.target is not None:         # 줍는 중: 남은 시간 막대
            w = 20 * max(0.0, self.timer) / config.ENEMY_PICK_TIME
            draw_line(self.x - 10, self.y - self.radius - 6, self.x - 10 + w, self.y - self.radius - 6,
                      *config.COLOR_BULLET_ENEMY)

    def draw_body(self, cx, cy):
        draw_circle(self.x, self.y, self.radius, *self.COLOR, filled=True)
