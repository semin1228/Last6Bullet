# 구역: 바깥 벽, 바닥, 장애물(테이블). 움직이는 것들이 벽과 장애물을 통과하지 못하게 하고,
# 총알이 벽과 장애물에 닿으면 튕겨 낸다.
import math

from pico2d import draw_line, draw_rectangle

import config


class Zone:
    def __init__(self, obstacles=(), number=1, name='술집'):
        w, h, t = config.WIDTH, config.HEIGHT, config.WALL
        self.title = '%d구역 · %s' % (number, name)   # 위쪽 HUD 에 표시 (PRD 15-2 play_mode)
        self.inner = (t, t, w - t, h - t)      # 벽 안쪽 바닥 영역 (left, bottom, right, top)
        self.obstacles = list(obstacles)       # 장애물 사각형 목록 (left, bottom, right, top)

    def update(self):
        pass

    def draw(self):
        draw_rectangle(0, 0, config.WIDTH, config.HEIGHT, *config.COLOR_WALL, filled=True)
        l, b, r, t = self.inner
        draw_rectangle(l, b, r, t, *config.COLOR_FLOOR, filled=True)
        for y in range(b + 40, t, 40):  # 나무 바닥 결
            draw_line(l, y, r, y, *config.COLOR_FLOOR_LINE)
        for ol, ob, o_r, ot in self.obstacles:
            draw_rectangle(ol, ob, o_r, ot, *config.COLOR_TABLE, filled=True)
            draw_rectangle(ol, ob, o_r, ob + 8, *config.COLOR_TABLE_EDGE, filled=True)  # 앞면 (3/4 느낌)

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
