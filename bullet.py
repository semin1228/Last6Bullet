# 총알 한 발. 구역을 시작할 때만 만들고, 이후에는 상태만 바뀐다 (PRD 15-4).
#   HELD: 누군가(플레이어 또는 적)의 손에 있음. 월드에 없고 그리지 않는다.
#   FLYING: 날아가는 중
#   FLOOR: 바닥에 멈춤. 플레이어는 지나가면 줍고, 적은 줍기 동작을 시작한다.
#   ROLLING: 발차기로 굴러가는 중. 마찰로 느려지고, 벽에 한 번 튕기면 속도 절반, 두 번째 벽에서 멈춘다.
#   PINNED: 적이 밟고 줍는 중. 줍기가 끝나면 HELD, 발차기로 끊기면 FLOOR.
import math

from pico2d import draw_circle
from transitions import Machine

import config
import effect
import game_framework
import game_world


class Bullet:
    def __init__(self, zone):
        self.zone = zone
        self.x, self.y = 0.0, 0.0
        self.vx, self.vy = 0.0, 0.0
        self.radius = config.BULLET_RADIUS
        self.owner = None          # 마지막으로 쏜 쪽 ('player' 또는 쏜 적 객체)
        self.age = 0.0             # 날아간 시간 (초)
        self.bounces = 0           # 벽이나 장애물에 튕긴 횟수 (날 때, 구를 때 따로 센다)
        self.trail = []            # 이번 프레임에 지나온 점들 (사람 맞히기 판정용, 느린 프레임에도 뚫고 지나가지 않게)

        self.machine = Machine(
            model=self,
            states=['HELD', 'FLYING', 'FLOOR', 'ROLLING', 'PINNED'],
            transitions=[
                {'trigger': 'fire', 'source': 'HELD', 'dest': 'FLYING', 'before': 'launch'},
                {'trigger': 'land', 'source': 'FLYING', 'dest': 'FLOOR'},
                {'trigger': 'pick_up', 'source': ['FLOOR', 'PINNED'], 'dest': 'HELD'},
                {'trigger': 'drop', 'source': 'HELD', 'dest': 'FLOOR', 'before': 'place'},
                {'trigger': 'kick', 'source': 'FLOOR', 'dest': 'ROLLING', 'before': 'roll'},
                {'trigger': 'stop', 'source': 'ROLLING', 'dest': 'FLOOR'},
                {'trigger': 'pin', 'source': 'FLOOR', 'dest': 'PINNED'},
                {'trigger': 'unpin', 'source': 'PINNED', 'dest': 'FLOOR'},
            ],
            initial='HELD',
            auto_transitions=False,
        )

    def launch(self, x, y, angle, owner, speed=None):
        speed = speed or config.BULLET_SPEED
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.owner = owner
        self.age = 0.0
        self.bounces = 0
        self.trail = [(x, y)]

    def place(self, x, y):
        # 손에서 바닥으로 떨어뜨릴 때 (적이 쓰러지거나 발차기에 맞을 때)
        self.x, self.y = self.zone.push_out(x, y, self.radius)

    def roll(self, angle, speed=None):
        # 플레이어 발차기는 ROLL_SPEED, 술꾼 패스는 더 세게 (speed)
        speed = speed or config.ROLL_SPEED
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.bounces = 0

    def add_to_world(self):
        # 손을 떠난 총알을 월드에 넣고, 플레이어·적과의 충돌 검사에 등록한다
        game_world.add_object(self, 1)
        game_world.add_collision_pair('player:bullet', None, self)
        game_world.add_collision_pair('enemy:bullet', None, self)

    def on_enter_FLOOR(self, *args, **kwargs):   # drop(x, y) 처럼 트리거 인자가 같이 넘어온다
        self.vx = self.vy = 0.0

    def is_loose(self):
        # 바닥에 있어서 누군가 주우러 갈 수 있는 총알 (적에게 밟힌 것은 제외)
        return self.state == 'FLOOR'

    def update(self):
        dt = game_framework.frame_time
        if self.state == 'FLYING':
            self.trail = [(self.x, self.y)]
            self.age += dt
            self.advance(dt)
            if self.state == 'FLYING' and self.age >= config.BULLET_LIFE:
                self.land()
        elif self.state == 'ROLLING':
            speed = math.hypot(self.vx, self.vy)
            slower = max(0.0, speed - config.ROLL_FRICTION * dt)
            if slower <= config.ROLL_STOP_SPEED:
                self.stop()
                return
            self.vx, self.vy = self.vx / speed * slower, self.vy / speed * slower
            self.advance(dt)

    def travel(self, distance):
        # 쏜 사람 몸 중심에서 총구까지 처럼, 프레임과 상관없이 정해진 거리만큼 움직인다
        self.advance(distance / math.hypot(self.vx, self.vy))

    def advance(self, dt):
        # dt 초 동안의 이동을 BULLET_SUBSTEP 이하로 나눠 움직여서 얇은 벽을 뚫고 지나가지 않게 한다
        distance = math.hypot(self.vx, self.vy) * dt
        steps = max(1, math.ceil(distance / config.BULLET_SUBSTEP))
        for _ in range(steps):
            self.x += self.vx * dt / steps
            self.y += self.vy * dt / steps
            if self.state == 'FLYING':
                self.trail.append((self.x, self.y))
            if self.zone.bounce(self):
                self.bounces += 1
                if self.state == 'ROLLING':
                    if self.bounces >= 2:      # 두 번째 벽에서 멈춘다 (PRD 6장)
                        self.stop()
                        return
                    self.vx, self.vy = self.vx / 2, self.vy / 2
                    continue
                effect.spawn(effect.Spark(self.x, self.y, self.vx, self.vy))
                if self.bounces > config.MAX_BOUNCES:
                    self.land()
                    return

    def draw(self):
        if self.state == 'FLYING':
            if self.bounces:
                color = config.COLOR_BULLET_BOUNCED
            elif self.owner == 'player':
                color = config.COLOR_BULLET_PLAYER
            else:
                color = config.COLOR_BULLET_ENEMY
            draw_circle(self.x, self.y, self.radius, *color, filled=True)
        elif self.state in ('FLOOR', 'ROLLING', 'PINNED'):
            if not self.zone.shows_floor_bullet(self):
                if self.zone.glints(self):     # 광산: 빛 밖 총알은 안 보이고 가끔 반짝이기만 한다
                    draw_circle(self.x, self.y, 2, *config.COLOR_GLINT, filled=True)
                return
            edge = config.COLOR_BULLET_ENEMY if self.state == 'PINNED' else config.COLOR_BULLET_EDGE
            draw_circle(self.x, self.y, self.radius + 2, *edge, filled=True)
            draw_circle(self.x, self.y, self.radius, *config.COLOR_BULLET_FLOOR, filled=True)

    def can_hit_anyone(self):
        # 튕긴 총알은 쏜 사람까지 누구든 맞는다 (PRD 3장 규칙 5). 발사 직후는 제외한다.
        return self.state == 'FLYING' and self.bounces > 0 and self.age > config.HIT_GRACE

    def get_bb(self):
        # 날아가는 총알은 이번 프레임에 지나온 길 전체를 감싼다. 한 프레임에 40px 까지 움직여도
        # 그 사이에 있던 사람과 충돌 검사가 이뤄지게 하기 위해서다.
        r = self.radius
        pts = self.trail if self.state == 'FLYING' and self.trail else [(self.x, self.y)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r

    def closest_on_path(self, cx, cy):
        # 이번 프레임 경로(trail) 위에서 (cx, cy) 에 가장 가까운 점과 그 거리
        pts = self.trail if self.state == 'FLYING' and len(self.trail) > 1 else [(self.x, self.y)]
        best = (math.hypot(pts[0][0] - cx, pts[0][1] - cy), pts[0])
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            dx, dy = bx - ax, by - ay
            seg = dx * dx + dy * dy
            t = 0.0 if seg == 0 else max(0.0, min(1.0, ((cx - ax) * dx + (cy - ay) * dy) / seg))
            px, py = ax + dx * t, ay + dy * t
            d = math.hypot(px - cx, py - cy)
            if d < best[0]:
                best = (d, (px, py))
        return best

    def hit_at(self, x, y):
        # 사람에게 맞음: 맞은 자리에 떨어진다
        self.x, self.y = x, y
        self.land()

    def handle_collision(self, group, other):
        pass
