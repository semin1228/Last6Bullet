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
#   SEEK/FLEE -> LUNGE: 빈손인데 총알을 가진 플레이어가 몸 사이 80px 안에 오면, 0.25초 '!' 를 띄우고 웅크렸다가
#   그 순간 방향으로 280px/s 로 0.4초 달려든다. 닿으면 밀쳐서 빼앗고, 빗나가면 1.5초 쉰다. -> SEEK
#   (붙어야만 빼앗아서 숨기만 하는 줍줍이에게 빼앗길 일이 거의 없었다: 사용자 플레이 테스트)
import math
import random

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
    STATES = ['SEEK', 'PICK', 'SHOOT', 'FLEE', 'LUNGE']
    TRANSITIONS = [
        {'trigger': 'reach_bullet', 'source': 'SEEK', 'dest': 'PICK'},
        {'trigger': 'picked', 'source': 'PICK', 'dest': 'SHOOT'},
        {'trigger': 'lost_bullet', 'source': 'PICK', 'dest': 'SEEK'},
        {'trigger': 'out_of_ammo', 'source': 'SHOOT', 'dest': 'SEEK'},
        {'trigger': 'nothing_to_pick', 'source': 'SEEK', 'dest': 'FLEE'},
        {'trigger': 'bullet_appeared', 'source': 'FLEE', 'dest': 'SEEK'},
        {'trigger': 'armed', 'source': 'SEEK', 'dest': 'SHOOT'},
        {'trigger': 'pounce', 'source': ['SEEK', 'FLEE'], 'dest': 'LUNGE'},
        {'trigger': 'pounce_end', 'source': 'LUNGE', 'dest': 'SEEK'},
    ]

    def __init__(self, zone, player, x, y):
        super().__init__(zone, player, x, y)
        self.shove_cooldown = 0.0
        self.locked_aim = None     # 조준 예고 중 고정한 방향 (라디안)
        self.shoot_wait = 0.0      # 쏠 준비가 된 뒤 너무 가까워 쏘지 못하고 기다린 시간 (초)
        self.cover = None          # 빈손일 때 숨어 있는 장애물 (left, bottom, right, top)
        self.passed_corners = set()  # 엄폐물을 돌아갈 때 이미 지나온 모서리 번호
        self.hide_target = None    # 지금 숨으러 가는 자리 (가끔만 다시 고른다)
        self.replan = 0.0          # 숨을 자리를 다시 고를 때까지 남은 시간 (초)
        self.since_plan = 0.0      # 마지막으로 고른 뒤 지난 시간 (초)
        self.lunge_time = 0.0      # 덤벼들기 시작 뒤 지난 시간 (초)
        self.lunge_dir = None      # 달려드는 방향 (준비 동작이 끝나는 순간 고정)

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

    def wants_to_pounce(self):
        p = self.player
        if self.held or not p.held or self.shove_cooldown > 0:
            return False
        return self.distance_to(p) - self.radius - p.radius <= config.LUNGE_RANGE

    def start_pounce(self):
        self.lunge_time = 0.0
        self.lunge_dir = None
        self.cover = self.hide_target = None
        self.pounce()
        effect.spawn(effect.TextPop(self.x, self.y + self.radius + 4, '!', config.COLOR_BULLET_ENEMY,
                                    config.LUNGE_WINDUP))

    def lunge(self):
        # 준비(웅크림) -> 고정한 방향으로 달려들기 -> 닿으면 밀치기
        p = self.player
        self.lunge_time += game_framework.frame_time
        if self.lunge_time < config.LUNGE_WINDUP:
            self.facing = math.atan2(p.y - self.y, p.x - self.x)
            return
        if self.lunge_dir is None:
            self.lunge_dir = math.atan2(p.y - self.y, p.x - self.x)
            self.facing = self.lunge_dir
        if self.try_shove():
            self.pounce_end()
            return
        self.detour = 0.0          # 달려드는 동안은 장애물을 돌아가지 않고 곧게 간다
        self.move(math.cos(self.lunge_dir), math.sin(self.lunge_dir), config.LUNGE_SPEED)
        self.detour = 0.0
        if self.try_shove():
            self.pounce_end()
        elif self.lunge_time >= config.LUNGE_WINDUP + config.LUNGE_DASH:
            self.shove_cooldown = config.SHOVE_COOLDOWN    # 빗나감: 잠깐 쉰다
            self.pounce_end()

    def after_recover(self):
        if self.held:              # 기절에서 깨어났는데 총알이 남아 있으면 바로 쏘러 간다
            self.armed()

    def think(self):
        p = self.player
        self.shove_cooldown = max(0.0, self.shove_cooldown - game_framework.frame_time)
        if self.state == 'LUNGE':
            self.lunge()
            return
        if self.state in ('SEEK', 'FLEE') and self.try_shove():
            return
        if self.state in ('SEEK', 'FLEE') and self.wants_to_pounce():
            self.start_pounce()
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
                self.shoot_wait = 0.0
                self.picked()
            elif done is False:
                self.lost_bullet()
        elif self.state == 'SHOOT':
            dt = game_framework.frame_time
            self.timer -= dt
            self.shoot_wait += dt
            d = self.distance_to(p)
            # 너무 가까우면 쏘지 않고 먼저 물러난다. 안 그러면 밀쳐서 빼앗은 총알을 바로 코앞에서 쏘고,
            # 맞은 총알이 내 발밑에 떨어져 곧바로 되돌아와서 '안 빼앗는다' 처럼 보였다 (사용자 플레이 테스트).
            # 구석에 몰려 물러날 수 없으면 PICKER_CORNERED 초 뒤에는 쏜다.
            if (d < config.PICKER_KEEP_NEAR and self.timer < config.ENEMY_AIM_TIME + 0.05
                    and self.locked_aim is None and self.shoot_wait < config.PICKER_CORNERED):
                self.timer = config.ENEMY_AIM_TIME + 0.05
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
                self.shoot_wait = 0.0
            if not self.held:
                self.out_of_ammo()
        elif self.state == 'FLEE':
            if self.nearest_loose_bullet() is not None:
                self.cover = None
                self.hide_target = None
                self.bullet_appeared()
                return
            self.plan_hiding()
            target = self.hide_target
            if target is None:
                self.move_away(p.x, p.y)
            elif math.hypot(target[0] - self.x, target[1] - self.y) > config.COVER_ARRIVE:
                self.move_toward(*self.route_to(target))
            else:
                self.facing = math.atan2(p.y - self.y, p.x - self.x)   # 숨어서 플레이어 쪽을 엿본다

    def plan_hiding(self):
        # 숨을 자리를 매 프레임 다시 계산하면, 플레이어가 조금만 움직여도 목표가 따라 움직여서
        # 섰다 걸었다를 초당 20~40번 반복하며 떨었다 (사용자 플레이 테스트: '지진').
        # 그래서 0.8~1.4초마다만 다시 고르고, 지금 자리가 플레이어에게 보이게 됐을 때만 바로(0.25초 뒤) 고른다.
        # 다시 고를 때 자리를 옆으로 조금(±25px) 흔들어 가만히 서 있을 때도 가끔 자리를 옮기며 엿본다.
        dt = game_framework.frame_time
        self.replan -= dt
        self.since_plan += dt
        exposed = self.hide_target is not None and not self.is_covered(self.hide_target)
        due = self.replan <= 0 or (exposed and self.since_plan >= config.COVER_REPLAN_URGENT)
        if self.hide_target is not None and not due:
            return
        self.replan = random.uniform(*config.COVER_REPLAN_TIME)
        self.since_plan = 0.0
        spot = self.cover_spot()
        if spot is None:
            self.hide_target = None
            return
        cur = self.hide_target
        moved_far = cur is None or math.hypot(spot[0] - cur[0], spot[1] - cur[1]) >= config.COVER_REPLAN_MIN
        # 엿보기 후보: 옆으로 흔든 자리 중 여전히 가려지고, 지금 자리와 조금이라도(12px) 다른 곳
        peeks = [q for q in (self.peek_shift(spot) for _ in range(4)) if self.is_covered(q)
                 and (cur is None or math.hypot(q[0] - cur[0], q[1] - cur[1]) >= config.COVER_PEEK_MIN)]
        if exposed or moved_far:
            self.hide_target = peeks[0] if peeks else spot     # 플레이어가 많이 움직였다: 새 자리로
        elif peeks:
            self.hide_target = peeks[0]                        # 플레이어가 그대로다: 옆으로 살짝 옮겨 엿본다

    def peek_shift(self, spot):
        # 플레이어-자리 방향의 옆으로 무작위로 조금 옮긴 자리
        p = self.player
        dx, dy = spot[0] - p.x, spot[1] - p.y
        d = math.hypot(dx, dy) or 1.0
        side = random.uniform(-config.COVER_PEEK, config.COVER_PEEK)
        return self.zone.push_out(spot[0] - dy / d * side, spot[1] + dx / d * side, self.radius)

    def is_covered(self, point):
        # 플레이어에서 point 까지 선이 지금 엄폐물을 지나면 숨은 것
        if self.cover is None:
            return False
        l, b, r, t = self.cover
        return self.segment_hits_rect((self.player.x, self.player.y), point, (l, b, r, t))

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

    def zone_pickers(self):
        import game_world
        return [o for o in game_world.objects() if isinstance(o, Picker) and o.alive]

    def cover_spot(self):
        # 숨을 장애물을 고른다. 지금 쓰는 엄폐물은 쓸 수 없게 되거나 훨씬 가까운 곳이 생길 때만 바꾼다
        # (매 프레임 가장 가까운 것으로 바꾸면 두 테이블 사이를 오가며 떨린다)
        # 다른 줍줍이가 이미 숨어 있는 엄폐물은 멀리 있는 것으로 쳐서, 다른 엄폐물이 있으면 그쪽으로 흩어진다
        # (안 그러면 술집에서 둘이 같은 테이블 뒤에 몰렸다: 사용자 플레이 테스트, 시간의 75%)
        taken = {o.cover for o in self.zone_pickers() if o is not self and o.cover is not None}
        spots = []
        for rect in self.zone.obstacles:
            spot = self.hide_spot(rect)
            if spot:
                cost = math.hypot(spot[0] - self.x, spot[1] - self.y)
                if rect in taken:
                    cost += config.COVER_SHARE_PENALTY
                spots.append((cost, rect, spot))
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
        if self.state == 'LUNGE' and self.lunge_time < config.LUNGE_WINDUP:   # 웅크림: 몸 테두리가 붉게
            draw_circle(self.x, self.y, self.radius + 3, *config.COLOR_BULLET_ENEMY)
            draw_circle(self.x, self.y, self.radius + 4, *config.COLOR_BULLET_ENEMY)
        if self.aiming():                  # 조준 예고: 총구가 커지며 반짝인다
            r = 3 + int(5 * (1 - max(0.0, self.timer) / config.ENEMY_AIM_TIME))
            draw_circle(gx, gy, r + 2, *config.COLOR_BULLET_ENEMY, filled=True)
            draw_circle(gx, gy, r, *config.COLOR_FLASH, filled=True)
