# 구역: 바깥 벽과 바닥을 그리고, 움직이는 것들이 벽 밖으로 나가지 않게 한다.
from pico2d import draw_line, draw_rectangle

import config


class Zone:
    def __init__(self):
        w, h, t = config.WIDTH, config.HEIGHT, config.WALL
        self.inner = (t, t, w - t, h - t)  # 벽 안쪽 바닥 영역 (left, bottom, right, top)

    def update(self):
        pass

    def draw(self):
        draw_rectangle(0, 0, config.WIDTH, config.HEIGHT, *config.COLOR_WALL, filled=True)
        l, b, r, t = self.inner
        draw_rectangle(l, b, r, t, *config.COLOR_FLOOR, filled=True)
        for y in range(b + 40, t, 40):  # 나무 바닥 결
            draw_line(l, y, r, y, *config.COLOR_FLOOR_LINE)
