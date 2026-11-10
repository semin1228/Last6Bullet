# 화면 위쪽 벽에 표시하는 정보 (PRD 15-2 hud.py): 체력, 손에 든 총알(리볼버 실린더), 구역 이름
import math

from pico2d import draw_circle, load_font

import config

CYLINDER_X = 172               # 실린더 중심 x (체력 표시 오른쪽)
CYLINDER_R = 13                # 실린더 반지름
CHAMBER_R = 3                  # 약실(총알 칸) 반지름
CHAMBER_DIST = 8               # 실린더 중심에서 약실까지 거리


class Hud:
    def __init__(self, player, zone):
        self.player = player
        self.zone = zone
        try:
            self.font = load_font(config.UI_FONT, 18)
        except Exception:
            self.font = None

    def update(self):
        pass

    def chambers(self):
        # 약실 6칸의 (x, y, 장전 여부). 맨 위 칸부터 시계 방향으로, 남은 총알 수만큼 채운다.
        y = config.HEIGHT - config.WALL // 2
        loaded = len(self.player.held)
        result = []
        for i in range(config.AMMO):
            a = math.pi / 2 - i * 2 * math.pi / config.AMMO
            result.append((CYLINDER_X + math.cos(a) * CHAMBER_DIST, y + math.sin(a) * CHAMBER_DIST, i < loaded))
        return result

    def rim_color(self):
        # 빈 총을 당긴 직후에는 실린더 테두리를 붉게 해서 '총알 없음' 을 알린다
        return config.COLOR_CROSSHAIR if self.player.dry_flash > 0 else config.COLOR_CROSSHAIR_EMPTY

    def draw(self):
        y = config.HEIGHT - config.WALL // 2
        for i in range(config.PLAYER_HP):
            color = config.COLOR_HP if i < self.player.hp else config.COLOR_HP_EMPTY
            draw_circle(48 + i * 26, y, 9, *color, filled=True)

        draw_circle(CYLINDER_X, y, CYLINDER_R, *config.COLOR_CYLINDER, filled=True)
        draw_circle(CYLINDER_X, y, CYLINDER_R, *self.rim_color())   # 어두운 벽 위에서 보이게 테두리
        for cx, cy, loaded in self.chambers():
            color = config.COLOR_BULLET_FLOOR if loaded else config.COLOR_CHAMBER_EMPTY
            draw_circle(cx, cy, CHAMBER_R, *color, filled=True)

        if self.font:
            self.font.draw(config.WIDTH // 2 - 50, y, self.zone.title, config.COLOR_HUD_TEXT)
