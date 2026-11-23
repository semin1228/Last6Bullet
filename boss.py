# 두목 THE BOSS ($500, 체력 8). 은행 보스 (PRD 9장, 15-4). 3주차는 1페이즈 + 대체 공격.
#   GATHER -> PICK(바닥 총알에 닿음, 0.25초) -> GATHER(모은 총알 부족) / SPREAD(3발 모음)
#   SPREAD: 0.3초 조준 예고(멈춤, 총구 반짝임, 방향 고정) 뒤 모은 총알을 모두 플레이어 쪽 좌우 50° 부채꼴로 쏜다
#   대체 공격: GATHER 로 4초 동안 다 못 모으면, 가진 총알이 있으면 그것만이라도 SPREAD, 없으면 CHARGE
#   CHARGE: 플레이어에게 2초 동안 돌진. 몸으로 부딪히면 체력 -1 하고 튕겨 나간다 (Enemy 공통)
#   발차기: 기절, 줍기 취소, 1발 떨어뜨림 (Enemy 공통 STUN)
# 쏜 총알은 일반 총알과 같아서 튕기고, 떨어지면 누구든 다시 줍는다. 6발로 체력 8을 깎는 재사용 전투가 의도다.
import math

from pico2d import draw_circle, draw_line, draw_rectangle

import config
import effect
import game_framework
from enemy import Enemy


class Boss(Enemy):
    NAME = 'THE BOSS'
    RADIUS = 18
    SPEED = config.BOSS_SPEED
    HP = config.BOSS_HP
    BOUNTY = 500
    COLOR = config.COLOR_BOSS
    TOUCH_DAMAGE = True
    START = 'GATHER'
    STATES = ['GATHER', 'PICK', 'SPREAD', 'CHARGE']
    TRANSITIONS = [
        {'trigger': 'reach_bullet', 'source': 'GATHER', 'dest': 'PICK'},
        {'trigger': 'picked_more', 'source': 'PICK', 'dest': 'GATHER'},
        {'trigger': 'lost_bullet', 'source': 'PICK', 'dest': 'GATHER'},
        {'trigger': 'ready_spread', 'source': ['GATHER', 'PICK'], 'dest': 'SPREAD'},
        {'trigger': 'spread_done', 'source': 'SPREAD', 'dest': 'GATHER'},
        {'trigger': 'charge', 'source': 'GATHER', 'dest': 'CHARGE'},
        {'trigger': 'charge_end', 'source': 'CHARGE', 'dest': 'GATHER'},
    ]

    def __init__(self, zone, player, x, y):
        super().__init__(zone, player, x, y)
        self.gather_time = 0.0     # GATHER 로 모으기 시작한 뒤 지난 시간 (대체 공격 판단)
        self.spread_time = 0.0     # 조준 예고가 시작된 뒤 지난 시간
        self.locked_aim = None     # 흩뿌릴 가운데 방향 (예고 시작 때 고정)
        self.charge_time = 0.0

    # ------------------------------------------------------------ 상태 전환 도우미

    def start_spread(self):
        self.spread_time = 0.0
        self.locked_aim = None
        self.ready_spread()

    def start_charge(self):
        self.charge_time = 0.0
        self.charge()

    def after_recover(self):
        self.gather_time = 0.0     # 기절에서 깨면 모으기 시간을 처음부터 센다

    def aiming(self):
        return self.state == 'SPREAD'

    # ------------------------------------------------------------ 행동

    def think(self):
        p = self.player
        dt = game_framework.frame_time
        if self.state == 'GATHER':
            self.gather_time += dt
            if self.gather_time >= config.BOSS_GATHER_LIMIT:
                self.gather_time = 0.0
                if self.held:
                    self.start_spread()          # 대체 공격 1: 가진 것만이라도 흩뿌린다
                else:
                    self.start_charge()          # 대체 공격 2: 돌진
                return
            b = self.nearest_loose_bullet()
            if b is None:
                self.facing = math.atan2(p.y - self.y, p.x - self.x)
                if self.distance_to(p) > config.BOSS_KEEP:
                    self.move_toward(p.x, p.y, self.SPEED * 0.5)
            elif self.touching(b):
                self.start_pick(b)
                self.reach_bullet()
            else:
                self.move_toward(b.x, b.y)
        elif self.state == 'PICK':
            done = self.pick_done()
            if done:
                if len(self.held) >= config.BOSS_SPREAD_COUNT:
                    self.start_spread()
                else:
                    self.picked_more()
            elif done is False:
                self.lost_bullet()
        elif self.state == 'SPREAD':
            self.spread_time += dt
            if self.locked_aim is None:
                self.locked_aim = self.aim_at_player(config.BULLET_SPEED)
            self.facing = self.locked_aim
            if self.spread_time >= config.ENEMY_AIM_TIME:
                self.fire_spread(self.locked_aim)
                self.gather_time = 0.0
                self.spread_done()
        elif self.state == 'CHARGE':
            self.charge_time += dt
            self.move_toward(p.x, p.y, config.BOSS_CHARGE_SPEED)
            if self.charge_time >= config.BOSS_CHARGE_TIME:
                self.gather_time = 0.0
                self.charge_end()

    def spread_angles(self, center, n):
        # 가운데 방향을 기준으로 좌우 BOSS_SPREAD_HALF 도 부채꼴에 같은 간격
        if n <= 1:
            return [center]
        half = math.radians(config.BOSS_SPREAD_HALF)
        return [center - half + 2 * half * i / (n - 1) for i in range(n)]

    def fire_spread(self, center):
        angles = self.spread_angles(center, len(self.held))
        for a in angles:
            self.shoot(a)

    # ------------------------------------------------------------ 그리기

    def draw_body(self, cx, cy):
        # 두목: 큰 검은 몸, 넓은 모자 챙, 금색 배지, 머리 위 체력 막대
        gx, gy = self.x + cx * (self.radius + 10), self.y + cy * (self.radius + 10)
        for o in (-1, 0, 1):
            draw_line(self.x - cy * o, self.y + cx * o, gx - cy * o, gy + cx * o, *config.COLOR_GUN)
        draw_circle(self.x, self.y, self.radius + 4, *config.COLOR_BOSS_HAT, filled=True)
        draw_circle(self.x, self.y, self.radius, *self.COLOR, filled=True)
        draw_circle(self.x, self.y, 6, *config.COLOR_BULLET_FLOOR, filled=True)
        if self.aiming():                  # 조준 예고: 총구가 커지며 반짝인다
            r = 4 + int(6 * min(1.0, self.spread_time / config.ENEMY_AIM_TIME))
            draw_circle(gx, gy, r + 2, *config.COLOR_BULLET_ENEMY, filled=True)
            draw_circle(gx, gy, r, *config.COLOR_FLASH, filled=True)
        w = 64
        left = self.x - w / 2
        top = self.y + self.radius + 18
        draw_rectangle(left, top, left + w, top + 6, *config.COLOR_HP_EMPTY, filled=True)
        draw_rectangle(left, top, left + w * max(0, self.hp) / self.HP, top + 6, *config.COLOR_HP, filled=True)
