# 총알 장부: 매 프레임 구역 총알 수가 그대로인지 검사한다 (PRD 15-3, 18장 위험 요소).
# 버그로 총알이 늘거나 사라지면 화면에 경고를 띄운다. F1 로 집계와 FPS 표시를 켜고 끈다.
from pico2d import load_font

import config
import game_framework
import game_world
from bullet import Bullet


class AmmoLedger:
    def __init__(self, holders, expected):
        self.holders = holders     # 총알을 손에 드는 쪽 목록 (지금은 플레이어, 2주차부터 적도 추가)
        self.expected = expected
        self.visible = False
        self.counts = {'hand': 0, 'floor': 0, 'air': 0}
        self.problem = None        # 마지막으로 찾은 문제 (없으면 None)
        self.reported = False
        self.fps = 0.0             # 최근 프레임 속도 (부드럽게 평균 낸 값)
        try:
            self.font = load_font(config.DEBUG_FONT, 16)
        except Exception:
            self.font = None

    def check(self):
        hand = [b for h in self.holders for b in h.held]
        loose = [o for o in game_world.objects() if isinstance(o, Bullet)]
        self.counts = {
            'hand': len(hand),
            'floor': sum(1 for b in loose if b.state == 'FLOOR'),
            'air': sum(1 for b in loose if b.state == 'FLYING'),
        }
        total = len(hand) + len(loose)
        if total != self.expected:
            self.problem = 'AMMO %d (expected %d)' % (total, self.expected)
        elif any(b.state != 'HELD' for b in hand) or any(b.state == 'HELD' for b in loose):
            self.problem = 'bullet state does not match its place'
        elif len(set(map(id, hand + loose))) != total:
            self.problem = 'same bullet in two places'
        else:
            self.problem = None
        if self.problem and not self.reported:
            print('[AmmoLedger]', self.problem)
            self.reported = True
        return self.problem is None

    def update(self):
        # 프레임마다 값이 튀어 숫자를 읽기 어려우므로 최근 값 쪽으로 조금씩 옮겨 간다
        if game_framework.frame_time > 0:
            now = 1.0 / game_framework.frame_time
            self.fps = now if self.fps == 0 else self.fps * 0.9 + now * 0.1

    def text(self):
        c = self.counts
        text = 'HAND %d · FLOOR %d · AIR %d = %d' % (c['hand'], c['floor'], c['air'], sum(c.values()))
        if self.visible:
            text = 'FPS %3d    ' % round(self.fps) + text
        if self.problem:
            text += '   ' + self.problem
        return text

    def draw(self):
        if not self.font or not (self.visible or self.problem):
            return
        color = (240, 149, 149) if self.problem else (244, 233, 212)
        self.font.draw(config.WIDTH - 500, config.HEIGHT - config.WALL // 2, self.text(), color)
