# 정오의 결투 (PRD 9장, 15-4 duel_mode). 은행에 들어서면 play_mode 위에 올라온다(push_mode).
#   INTRO(1.4초, 'HIGH NOON 12:00', 클릭 무시) -> READY(무작위 1~3초, 클릭하면 반칙 패배)
#   -> GO('DRAW!', 두목 반응 0.3~0.45초 안에 클릭하면 승리, 늦으면 패배) -> WIN / LOSE(1.2초 결과) -> 보스전
# 결과는 총알 배분으로 이어진다:
#   승리: 두목 체력 -1(7부터), 총알 4발은 플레이어 손에, 2발은 두 사람 사이 바닥에
#   패배: 플레이어 체력 -1, 총알을 3발씩 나눠 쥐고 시작하며 두목이 바로 흩뿌린다
import random

from pico2d import (SDL_BUTTON_LEFT, SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE, clear_canvas,
                    draw_line, draw_rectangle, get_events, load_font, update_canvas)
from transitions import Machine

import config
import game_framework
import game_world
import play_mode
from boss import Boss


class Duel:
    def __init__(self, player, boss):
        self.player, self.boss = player, boss
        self.t = 0.0                                             # 지금 단계에서 지난 시간
        self.ready_time = random.uniform(*config.DUEL_READY)     # READY 가 떠 있는 시간
        self.react = random.uniform(*config.DUEL_BOSS_REACT)     # 두목이 신호에 반응하는 시간
        self.reason = ''                                         # 결과 문구 (YOU WIN, FOUL, TOO SLOW)
        self.machine = Machine(
            model=self,
            states=['INTRO', 'READY', 'GO', 'WIN', 'LOSE'],
            transitions=[
                {'trigger': 'ready', 'source': 'INTRO', 'dest': 'READY'},
                {'trigger': 'signal', 'source': 'READY', 'dest': 'GO'},
                {'trigger': 'foul', 'source': 'READY', 'dest': 'LOSE'},
                {'trigger': 'draw_first', 'source': 'GO', 'dest': 'WIN'},
                {'trigger': 'too_slow', 'source': 'GO', 'dest': 'LOSE'},
            ],
            initial='INTRO',
            auto_transitions=False,
            after_state_change='restart_clock',
        )

    def restart_clock(self):
        self.t = 0.0

    def click(self):
        if self.state == 'READY':
            self.reason = 'FOUL'
            self.foul()
        elif self.state == 'GO':
            self.reason = 'YOU WIN'
            self.draw_first()
        # INTRO 중 클릭은 무시한다 (연출을 보다 무심코 누른 클릭으로 지지 않게, PRD 9장)

    def update(self, dt):
        self.t += dt
        if self.state == 'INTRO' and self.t >= config.DUEL_INTRO:
            self.ready()
        elif self.state == 'READY' and self.t >= self.ready_time:
            self.signal()
        elif self.state == 'GO' and self.t >= self.react:
            self.reason = 'TOO SLOW'
            self.too_slow()

    def finished(self):
        return self.state in ('WIN', 'LOSE') and self.t >= config.DUEL_RESULT

    def apply(self):
        # 결투 결과를 보스전 시작 조건으로 (PRD 9장 표)
        p, b = self.player, self.boss
        if self.state == 'WIN':
            # 비판 점검 반영: 6발을 다 쥐면 두목이 주울 총알이 없어 3.2초 만에 끝났다. 2발은 가운데 바닥에 둔다
            b.hp -= 1
            b.flash = config.HIT_FLASH_TIME
            for x, y in config.DUEL_WIN_FLOOR[:len(p.held)]:
                bullet = p.held.pop()
                bullet.drop(x, y)
                bullet.add_to_world()
        else:
            p.hp -= 1
            p.invincible = config.INVINCIBLE_TIME
            for _ in range(min(config.DUEL_LOSE_SPLIT, len(p.held))):
                b.held.append(p.held.pop())
            b.start_spread()                                     # 두목이 바로 흩뿌린다


duel = None
big = small = None


def find_boss():
    return next(e for e in play_mode.enemies if isinstance(e, Boss) and e.alive)


def init():
    global duel, big, small
    p, b = play_mode.player, find_boss()
    p.x, p.y = config.DUEL_PLAYER_POS
    b.x, b.y = config.DUEL_BOSS_POS
    p.mouse = (b.x, b.y)                                         # 서로 마주 본다
    p.update_aim()
    b.facing = 3.14159
    duel = Duel(p, b)
    try:
        big = load_font(config.UI_FONT, 72)
        small = load_font(config.UI_FONT, 24)
    except Exception:
        big = small = None


def finish():
    pass


def handle_events():
    for event in get_events():
        dispatch(event)


def dispatch(event):
    if event.type == SDL_QUIT or (event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE):
        game_framework.quit()
    elif event.type == SDL_MOUSEBUTTONDOWN and event.button == SDL_BUTTON_LEFT:
        duel.click()


def update():
    duel.update(game_framework.frame_time)
    if duel.finished():
        game_framework.pop_mode()                                # 보스전으로 돌아가서
        duel.apply()                                             # 결과대로 시작한다


def render():
    clear_canvas()
    game_world.render()
    cy = config.HEIGHT // 2 + 190
    draw_rectangle(0, cy - 70, config.WIDTH, cy + 70, *config.COLOR_WALL, filled=True)
    p, b = duel.player, duel.boss
    if duel.state in ('WIN', 'LOSE') and duel.reason != 'FOUL' and duel.t < 0.25:
        a, c = (p, b) if duel.state == 'WIN' else (b, p)         # 먼저 쏜 쪽에서 맞은 쪽으로 총알 자국
        for o in (-1, 0, 1):
            draw_line(a.x, a.y + o, c.x, c.y + o, *config.COLOR_FLASH)
    if big:
        text, color = {
            'INTRO': ('HIGH NOON', config.COLOR_HUD_TEXT),
            'READY': ('READY...', config.COLOR_HUD_TEXT),
            'GO': ('DRAW!', config.COLOR_FLASH),
            'WIN': (duel.reason, config.COLOR_BOUNTY),
            'LOSE': (duel.reason, config.COLOR_HP),
        }[duel.state]
        big.draw(config.WIDTH // 2 - len(text) * 20, cy + 8, text, color)
        sub = {'INTRO': '12:00', 'READY': 'WAIT FOR IT', 'GO': 'CLICK!',
               'WIN': 'BOSS HP -1 · 4 BULLETS YOURS', 'LOSE': 'HP -1 · 3 BULLETS EACH'}[duel.state]
        small.draw(config.WIDTH // 2 - len(sub) * 6, cy - 44, sub, config.COLOR_HUD_TEXT)
    update_canvas()


def pause():
    pass


def resume():
    pass
