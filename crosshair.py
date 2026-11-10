# 조준점: 시스템 마우스 커서 대신 마우스 위치에 그린다.
# 손에 총알이 있으면 붉은색, 없으면 회색이라 화면 가운데를 보면서도 빈 총인지 알 수 있다.
from pico2d import draw_circle, draw_line

import config

GAP, ARM = 5, 7                # 가운데 빈 칸, 눈금 길이 (px)


class Crosshair:
    def __init__(self, player):
        self.player = player

    def update(self):
        pass

    def color(self):
        return config.COLOR_CROSSHAIR if self.player.held else config.COLOR_CROSSHAIR_EMPTY

    def draw(self):
        x, y = self.player.mouse
        color = self.color()
        draw_circle(x, y, 10, *color)
        draw_circle(x, y, 11, *color)          # 두께 2px 테두리
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            draw_line(x + dx * GAP, y + dy * GAP, x + dx * (GAP + ARM), y + dy * (GAP + ARM), *color)
        draw_circle(x, y, 1, *color, filled=True)
