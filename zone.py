# 구역: 바깥 벽, 바닥, 장애물(테이블, 바위). 움직이는 것들이 벽과 장애물을 통과하지 못하게 하고,
# 총알이 벽과 장애물에 닿으면 튕겨 낸다. 적을 모두 쓰러뜨리면 오른쪽 벽의 문이 열린다.
# 어두운 구역(광산)은 랜턴(플레이어) 빛 반경 안의 바닥 총알만 보이고, 바깥 총알은 가끔 반짝인다 (PRD 7장).
import math

from pico2d import draw_circle, draw_line, draw_rectangle

import config
import game_framework


class Zone:
    def __init__(self, obstacles=(), number=1, name='SALOON', ammo=config.AMMO, dark=False, style=None):
        w, h, t = config.WIDTH, config.HEIGHT, config.WALL
        self.number, self.name, self.ammo = number, name, ammo
        self.title = 'ZONE %d · %s' % (number, name)  # 위쪽 HUD 에 표시 (PRD 15-2 play_mode). 화면 글자는 영어 (PRD 14장)
        self.inner = (t, t, w - t, h - t)      # 벽 안쪽 바닥 영역 (left, bottom, right, top)
        self.obstacles = list(obstacles)       # 장애물 사각형 목록 (left, bottom, right, top)
        self.dark = dark
        self.style = style                     # 'bank': 대리석 바닥과 돌기둥
        self.light = None                      # 랜턴을 든 쪽 (play_mode 가 플레이어로 정한다)
        self.door_open = False
        self.clock = 0.0                       # 반짝임 주기용 시간

    def door_span(self):
        cy = config.HEIGHT // 2
        return cy - config.DOOR_HALF, cy + config.DOOR_HALF

    def at_door(self, x, y, radius):
        # 문이 열렸고, 몸이 오른쪽 벽 문 앞에 닿았는지
        l, b, r, t = self.inner
        lo, hi = self.door_span()
        return self.door_open and x >= r - radius - 1 and lo + radius <= y <= hi - radius

    def update(self):
        self.clock += game_framework.frame_time

    def draw(self):
        wall = config.COLOR_MINE_WALL if self.dark else config.COLOR_WALL
        draw_rectangle(0, 0, config.WIDTH, config.HEIGHT, *wall, filled=True)
        l, b, r, t = self.inner
        if self.dark:
            draw_rectangle(l, b, r, t, *config.COLOR_MINE_FLOOR, filled=True)
            if self.light is not None:     # 랜턴 빛: 바깥 고리와 안쪽 밝은 원
                lx, ly = self.light.x, self.light.y
                draw_circle(lx, ly, config.LIGHT_RADIUS, *config.COLOR_MINE_LIGHT, filled=True)
                draw_circle(lx, ly, int(config.LIGHT_RADIUS * 0.6), *config.COLOR_MINE_LIGHT_CORE, filled=True)
        elif self.style == 'bank':
            draw_rectangle(l, b, r, t, *config.COLOR_BANK_FLOOR, filled=True)
            for y in range(b + 64, t, 64):  # 대리석 타일 줄
                draw_line(l, y, r, y, *config.COLOR_BANK_TILE)
            for x in range(l + 64, r, 64):
                draw_line(x, b, x, t, *config.COLOR_BANK_TILE)
        else:
            draw_rectangle(l, b, r, t, *config.COLOR_FLOOR, filled=True)
            for y in range(b + 40, t, 40):  # 나무 바닥 결
                draw_line(l, y, r, y, *config.COLOR_FLOOR_LINE)
        if self.dark:
            top, edge = config.COLOR_ROCK, config.COLOR_ROCK_EDGE
        elif self.style == 'bank':
            top, edge = config.COLOR_PILLAR, config.COLOR_PILLAR_EDGE
        else:
            top, edge = config.COLOR_TABLE, config.COLOR_TABLE_EDGE
        for ol, ob, o_r, ot in self.obstacles:
            draw_rectangle(ol, ob, o_r, ot, *top, filled=True)
            draw_rectangle(ol, ob, o_r, ob + 8, *edge, filled=True)  # 앞면 (3/4 느낌)
        lo, hi = self.door_span()          # 오른쪽 벽의 문: 닫히면 판자, 열리면 바닥이 이어진다
        if self.door_open:
            draw_rectangle(r, lo, config.WIDTH, hi, *config.COLOR_DOOR_OPEN, filled=True)
        else:
            draw_rectangle(r, lo, config.WIDTH - 6, hi, *config.COLOR_DOOR, filled=True)
            for y in range(lo + 10, hi, 14):
                draw_line(r, y, config.WIDTH - 6, y, *config.COLOR_TABLE_EDGE)

    def shows_floor_bullet(self, bullet):
        # 바닥 총알을 그릴지. 밝은 구역은 항상, 어두운 구역은 랜턴 빛 안에서만 보인다.
        if not self.dark or self.light is None:
            return True
        return math.hypot(bullet.x - self.light.x, bullet.y - self.light.y) <= config.LIGHT_RADIUS

    def glints(self, bullet):
        # 빛 밖 바닥 총알이 잠깐 반짝일 차례인지 (총알마다 주기를 어긋나게)
        phase = (id(bullet) // 16) % 97 / 97 * config.GLINT_PERIOD
        return (self.clock + phase) % config.GLINT_PERIOD < config.GLINT_TIME

    def push_out(self, x, y, radius):
        # 반지름 radius 인 원이 벽 안쪽에 머물고 장애물과 겹치지 않도록 위치를 고쳐 돌려준다
        for ol, ob, o_r, ot in self.obstacles:
            cx, cy = min(max(x, ol), o_r), min(max(y, ob), ot)   # 사각형에서 원 중심과 가장 가까운 점
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if dist == 0:                                         # 중심이 사각형 안: 가장 가까운 변으로 꺼낸다
                gaps = {x - ol: (ol - radius, y), o_r - x: (o_r + radius, y),
                        y - ob: (x, ob - radius), ot - y: (x, ot + radius)}
                x, y = gaps[min(gaps)]
            elif dist < radius:
                x, y = cx + dx / dist * radius, cy + dy / dist * radius
        l, b, r, t = self.inner
        return min(max(x, l + radius), r - radius), min(max(y, b + radius), t - radius)

    def bounce(self, bullet):
        # 총알이 벽이나 장애물에 닿았으면 속도를 뒤집고 밖으로 꺼낸 뒤 True 를 돌려준다
        x, y, rad = bullet.x, bullet.y, bullet.radius
        l, b, r, t = self.inner
        hit = False
        if x - rad < l or x + rad > r:
            bullet.x = min(max(x, l + rad), r - rad)
            bullet.vx = -bullet.vx
            hit = True
        if y - rad < b or y + rad > t:
            bullet.y = min(max(y, b + rad), t - rad)
            bullet.vy = -bullet.vy
            hit = True
        for ol, ob, o_r, ot in self.obstacles:
            x, y = bullet.x, bullet.y
            if x + rad <= ol or x - rad >= o_r or y + rad <= ob or y - rad >= ot:
                continue
            # 날아온 방향의 면으로 들어온 깊이를 축마다 재고, 얕은 축의 속도를 뒤집는다 (PRD 15-5).
            # 꺼낼 쪽도 위치가 아니라 날아온 방향으로 정한다. 얇은 벽에서 중심이 벽 가운데를
            # 넘어가도 반대편으로 꺼내지지 않게 하기 위해서다.
            vx, vy = bullet.vx, bullet.vy
            pen_x = (x + rad - ol) if vx > 0 else (o_r - (x - rad)) if vx < 0 else math.inf
            pen_y = (y + rad - ob) if vy > 0 else (ot - (y - rad)) if vy < 0 else math.inf
            if pen_x < pen_y:
                bullet.x = ol - rad if vx > 0 else o_r + rad
                bullet.vx = -vx
            else:
                bullet.y = ob - rad if vy > 0 else ot + rad
                bullet.vy = -vy
            hit = True
        return hit


# 구역 데이터 (PRD 7장). 적은 (종류, x, y). 플레이어는 start 에서 시작하고, 적을 모두 쓰러뜨리면 오른쪽 문이 열린다.
# floor: 구역 시작 때 바닥에 놓여 있는 총알 자리. 나머지는 플레이어 손에 쥐고 시작한다.
#   손의 3발로는 적 체력 합(4~5)을 다 깎지 못해서, 시작부터 바닥 총알 쟁탈이 벌어진다 (비판 점검 반영:
#   6발을 다 쥐고 시작하면 술집이 2.8초 만에 끝나고 적이 총알을 한 발도 줍지 않았다).
#   은행은 정오의 결투 결과가 배분을 정하므로 floor 가 없다.
ZONES = [
    {'number': 1, 'name': 'SALOON', 'ammo': 6, 'obstacles': config.SALOON_TABLES, 'dark': False,
     'start': (config.WIDTH // 2, config.HEIGHT // 2),
     'floor': [(880, 620), (900, 330), (860, 110)],
     'enemies': [('picker', 1120, 600), ('picker', 1120, 130), ('drunk', 1180, 360)]},
    {'number': 2, 'name': 'MINE', 'ammo': 6, 'obstacles': config.MINE_ROCKS, 'dark': True,
     'start': (110, config.HEIGHT // 2),
     'floor': [(620, 560), (700, 300), (600, 70)],
     'enemies': [('picker', 1100, 610), ('picker', 760, 640), ('dog', 1100, 110), ('drunk', 1180, 360)]},
    {'number': 3, 'name': 'TRAIN', 'ammo': 6, 'obstacles': config.TRAIN_CRATES, 'dark': False, 'kind': 'train',
     'start': (320, config.HEIGHT // 2),
     'floor': [(1040, 600), (1060, 330), (1040, 110)],
     'enemies': [('picker', 1100, 610), ('picker', 1100, 110), ('dog', 1100, 360), ('drunk', 1180, 360)]},
    {'number': 4, 'name': 'BANK', 'ammo': 6, 'obstacles': config.BANK_PILLARS, 'dark': False, 'style': 'bank',
     'start': (240, config.HEIGHT // 2), 'duel': True, 'final': True,
     'enemies': [('boss', 1040, config.HEIGHT // 2)]},
]
