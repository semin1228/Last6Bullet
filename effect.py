# 잠깐 보였다 사라지는 연출. 정해진 시간이 지나면 스스로 월드에서 빠진다.
# 충돌 검사나 총알 장부와는 관계없다 (Bullet 이 아니므로 장부가 세지 않는다).
import math

from pico2d import draw_circle, draw_line, load_font

import config
import game_framework
import game_world

_font = None


def font():
    # 글꼴은 캔버스가 열린 뒤에만 불러올 수 있어서 처음 쓸 때 한 번만 연다
    global _font
    if _font is None:
        try:
            _font = load_font(config.UI_FONT, 16)
        except Exception:
            _font = False
    return _font


def spawn(effect):
    game_world.add_object(effect, 1)   # 캐릭터·총알 위, UI 아래
    return effect


class Effect:
    def __init__(self, x, y, life):
        self.x, self.y = x, y
        self.life = life
        self.age = 0.0

    def progress(self):
        return min(1.0, self.age / self.life)  # 0 에서 시작해 1 이 되면 사라진다

    def update(self):
        self.age += game_framework.frame_time
        if self.age >= self.life:
            game_world.remove_object(self)

    def draw(self):
        pass


class TextPop(Effect):
    # 글자가 위로 떠오르며 사라진다 (예: 빈 총 '찰칵')
    def __init__(self, x, y, text, color, life=0.5):
        super().__init__(x, y, life)
        self.text, self.color = text, color

    def draw(self):
        f = font()
        if f:
            f.draw(self.x - 14, self.y + 22 * self.progress(), self.text, self.color)


class MuzzleFlash(Effect):
    # 총구 불꽃: 발사 순간 총알이 나온 자리에서 노랗게 번쩍이고 줄어든다
    def __init__(self, x, y, angle, life=0.07):
        super().__init__(x, y, life)
        self.dx, self.dy = math.cos(angle), math.sin(angle)

    def draw(self):
        r = int(8 * (1 - self.progress())) + 2
        draw_circle(self.x + self.dx * 3, self.y + self.dy * 3, r, *config.COLOR_FLASH, filled=True)
        draw_circle(self.x, self.y, max(1, r // 2), *config.COLOR_FLASH_CORE, filled=True)


class Spark(Effect):
    # 튕김 불똥: 총알이 벽·장애물에 닿은 자리에서 튕겨 나가는 쪽으로 짧은 선이 퍼진다.
    # 튕긴 총알은 누구든 맞으므로(주황), '이제 위험해졌다' 는 순간을 보여 준다.
    SPREAD = (-0.9, -0.35, 0.35, 0.9)  # 튕겨 나가는 방향에서 벌어지는 각도 (라디안)

    def __init__(self, x, y, vx, vy, life=0.15):
        super().__init__(x, y, life)
        self.angle = math.atan2(vy, vx)

    def draw(self):
        p = self.progress()
        near, far = 3 + 6 * p, 6 + 8 * p
        for s in self.SPREAD:
            c, d = math.cos(self.angle + s), math.sin(self.angle + s)
            draw_line(self.x + c * near, self.y + d * near, self.x + c * far, self.y + d * far,
                      *config.COLOR_BULLET_BOUNCED)


class Ring(Effect):
    # 퍼지는 고리: 줍기(놋쇠색, 작게)와 피격(붉은색, 크게)에 쓴다
    def __init__(self, x, y, color, start, end, life):
        super().__init__(x, y, life)
        self.color, self.start, self.end = color, start, end

    def radius(self):
        return int(self.start + (self.end - self.start) * self.progress())

    def draw(self):
        r = self.radius()
        draw_circle(self.x, self.y, r, *self.color)
        draw_circle(self.x, self.y, r + 1, *self.color)


def pickup_ring(x, y):
    return Ring(x, y, config.COLOR_BULLET_FLOOR, 5, 16, 0.25)


def hit_ring(x, y):
    return Ring(x, y, config.COLOR_HP, 16, 36, 0.3)
