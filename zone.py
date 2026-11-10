# 구역: 바깥 벽, 바닥, 장애물(테이블). 움직이는 것들이 벽과 장애물을 통과하지 못하게 하고,
# 총알이 벽과 장애물에 닿으면 튕겨 낸다.
import math

from pico2d import draw_line, draw_rectangle

import config


class Zone:
    def __init__(self, obstacles=()):
        w, h, t = config.WIDTH, config.HEIGHT, config.WALL
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

