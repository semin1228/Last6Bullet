# 줍줍이 THE PICKER ($50, 체력 1). 바닥 총알을 주워서 거리를 두고 쏜다. 총알이 없으면 도망친다 (PRD 8장).
#   SEEK -> PICK(바닥 총알에 닿음) -> SHOOT(줍기 완료) -> SEEK(총알 다 씀)
#   SEEK -> FLEE(주울 총알도, 가진 총알도 없음) -> SEEK(바닥 총알 생김)
#   FLEE 에서는 플레이어 반대편의 테이블·바위 뒤로 숨는다. 플레이어가 움직이면 숨을 자리도 돌아가서
#   장애물을 사이에 두고 술래잡기하듯 맴돈다. 숨을 곳이 없을 때만 그냥 멀어진다.
#   (처음엔 그냥 멀어지기만 해서 벽에 붙어 비볐다: 사용자 플레이 테스트, 벽 근처에 있던 시간 약 50%)
#   어느 상태든 발차기 -> STUN(0.7초) -> SEEK
#   SHOOT 에서 쏘기 0.3초 전에는 멈춰 서서 총구가 반짝이고 조준을 고정한다(조준 예고).
#   총알 속도는 플레이어와 같으므로, 플레이어는 총알 대신 이 예고를 보고 피한다.
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
        self.locked_aim = None     # 조준 예고 중 고정한 방향 (라디안)
        self.cover = None          # 빈손일 때 숨어 있는 장애물 (left, bottom, right, top)
        self.passed_corners = set()  # 엄폐물을 돌아갈 때 이미 지나온 모서리 번호

    def aiming(self):
        return self.state == 'SHOOT' and self.held and self.timer <= config.ENEMY_AIM_TIME

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
            self.timer -= game_framework.frame_time
            if self.timer > config.ENEMY_AIM_TIME:
                self.locked_aim = None
                d = self.distance_to(p)
                if d < config.PICKER_KEEP_NEAR:
                    self.move_away(p.x, p.y)
                elif d > config.PICKER_KEEP_FAR:
                    self.move_toward(p.x, p.y)
                self.facing = self.aim_at_player(config.BULLET_SPEED)
            else:
                if self.locked_aim is None:        # 조준 예고 시작: 이 순간의 방향으로 고정
                    self.locked_aim = self.aim_at_player(config.BULLET_SPEED)
                self.facing = self.locked_aim
            if self.timer <= 0:
                self.shoot(self.locked_aim)
                self.locked_aim = None
                self.timer = config.PICKER_SHOOT_INTERVAL
            if not self.held:
                self.out_of_ammo()
        elif self.state == 'FLEE':
            if self.nearest_loose_bullet() is not None:
                self.cover = None
                self.bullet_appeared()
                return
            spot = self.cover_spot()
            if spot is None:
                self.move_away(p.x, p.y)
            elif math.hypot(spot[0] - self.x, spot[1] - self.y) > config.COVER_ARRIVE:
                self.move_toward(*self.route_to(spot))
            else:
                self.facing = math.atan2(p.y - self.y, p.x - self.x)   # 숨어서 플레이어 쪽을 엿본다

    def hide_spot(self, rect):
        # 장애물 rect 를 사이에 두고 플레이어 반대편 자리. 플레이어에게 너무 가까우면 None
        p = self.player
        l, b, r, t = rect
        cx, cy = (l + r) / 2, (b + t) / 2
        dx, dy = cx - p.x, cy - p.y
        d = math.hypot(dx, dy)
        if d == 0:
            return None
        ux, uy = dx / d, dy / d
        hw, hh = (r - l) / 2, (t - b) / 2
        edge = min(hw / abs(ux) if ux else math.inf, hh / abs(uy) if uy else math.inf)
        away = edge + self.radius + config.COVER_GAP
        sx, sy = self.zone.push_out(cx + ux * away, cy + uy * away, self.radius)
        if math.hypot(sx - p.x, sy - p.y) < config.COVER_MIN_DIST:
            return None
        return sx, sy

    def route_to(self, spot):
        # 숨을 자리로 가는 길이 엄폐물을 가로지르면, 엄폐물에서 COVER_GAP 만큼 떨어진 모서리를 거쳐 돌아간다.
        # 곧장 가면 엄폐물 가장자리에 몸을 비비며 미끄러진다 (사용자 플레이 테스트).
        # 지나온 모서리는 기억해서 다시 고르지 않는다 (안 그러면 두 모서리 사이를 오가며 제자리걸음한다).
        if self.cover is None:
            return spot
        l, b, r, t = self.cover
        body = (l - self.radius, b - self.radius, r + self.radius, t + self.radius)
        if not self.segment_hits_rect((self.x, self.y), spot, body):
            self.passed_corners.clear()
            return spot
        m = self.radius + config.COVER_GAP - 2
        corners = [self.zone.push_out(cx, cy, self.radius)
                   for cx, cy in ((l - m, b - m), (l - m, t + m), (r + m, b - m), (r + m, t + m))]
        for i, (cx, cy) in enumerate(corners):
            if math.hypot(cx - self.x, cy - self.y) <= config.COVER_ARRIVE * 2:
                self.passed_corners.add(i)
        options = [i for i in range(4) if i not in self.passed_corners
                   and not self.segment_hits_rect((self.x, self.y), corners[i], body)]
        if not options:
            self.passed_corners.clear()
            return spot
        best = min(options, key=lambda i: math.hypot(corners[i][0] - self.x, corners[i][1] - self.y)
                   + math.hypot(spot[0] - corners[i][0], spot[1] - corners[i][1]))
        return corners[best]

    @staticmethod
    def segment_hits_rect(a, b, rect):
        # 선분 a-b 가 사각형 안을 지나는지 (24등분 점으로 본다)
        l, bt, r, t = rect
        for k in range(1, 24):
            x, y = a[0] + (b[0] - a[0]) * k / 24, a[1] + (b[1] - a[1]) * k / 24
            if l < x < r and bt < y < t:
                return True
        return False

    def cover_spot(self):
        # 숨을 장애물을 고른다. 지금 쓰는 엄폐물은 쓸 수 없게 되거나 훨씬 가까운 곳이 생길 때만 바꾼다
        # (매 프레임 가장 가까운 것으로 바꾸면 두 테이블 사이를 오가며 떨린다)
        spots = []
        for rect in self.zone.obstacles:
            spot = self.hide_spot(rect)
            if spot:
                spots.append((math.hypot(spot[0] - self.x, spot[1] - self.y), rect, spot))
        if not spots:
            self.cover = None
            return None
        best = min(spots, key=lambda s: s[0])
        current = [s for s in spots if s[1] == self.cover]
        if current and current[0][0] <= best[0] / config.COVER_SWITCH_RATIO:
            return current[0][2]
        if best[1] != self.cover:
            self.passed_corners.clear()
        self.cover = best[1]
        return best[2]

    def draw_body(self, cx, cy):
        # 줍줍이: 녹색 몸, 붉은 두건, 짧은 총
        gx, gy = self.x + cx * (self.radius + 7), self.y + cy * (self.radius + 7)
        draw_line(self.x, self.y, gx, gy, *config.COLOR_GUN)
        draw_line(self.x + 1, self.y, gx + 1, gy, *config.COLOR_GUN)
        draw_circle(self.x, self.y, self.radius, *self.COLOR, filled=True)
        draw_circle(self.x, self.y, self.radius - 5, *config.COLOR_BANDANA, filled=True)
        if self.aiming():                  # 조준 예고: 총구가 커지며 반짝인다
            r = 3 + int(5 * (1 - max(0.0, self.timer) / config.ENEMY_AIM_TIME))
            draw_circle(gx, gy, r + 2, *config.COLOR_BULLET_ENEMY, filled=True)
            draw_circle(gx, gy, r, *config.COLOR_FLASH, filled=True)
