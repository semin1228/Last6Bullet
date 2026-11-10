# 화면 위쪽 벽에 표시하는 정보: 체력
from pico2d import draw_circle

import config


class Hud:
    def __init__(self, player):
        self.player = player

    def update(self):
        pass

    def draw(self):
        y = config.HEIGHT - config.WALL // 2
        for i in range(config.PLAYER_HP):
            color = config.COLOR_HP if i < self.player.hp else config.COLOR_HP_EMPTY
            draw_circle(48 + i * 26, y, 9, *color, filled=True)
