# 봇 측정: 봇 플레이어로 구역마다 여러 판을 돌려 난이도 수치를 모은다 (4주차 비판 점검에서 만듦).
# 게임 코드는 바꾸지 않고 함수를 감싸 기록만 한다. 결과는 docs/DEVLOG.md 4주차 표와 비교한다.
#   실행: C:\Python313\python.exe tools\bot_measure.py          (구역마다 8판, 은행 6판. 몇 분 걸린다)
#         C:\Python313\python.exe tools\bot_measure.py 2        (구역마다 2판, 빠른 확인)
#         C:\Python313\python.exe tools\bot_measure.py 8 2      (기차만 8판. 두 번째 수는 구역 번호 0~3)
# 봇은 단순하다: 조준 예고를 보면 옆으로 피하고, 총알이 있으면 가까운 적을 쏘고, 없으면 바닥 총알을 주우러 간다.
import math
import os
import random
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim

sim.open_game(False)
import config
import game_framework
import game_world
import play_mode
from bullet import Bullet
from enemy import Enemy
from player import Player
from pico2d import SDLK_a, SDLK_d, SDLK_s, SDLK_w
from zone import ZONES

# ------------------------------------------------------------ 기록 (함수 감싸기)
LOG = Counter()
ctx = {'cause': None, 'bullet': None}
frame = {'n': 0}
recent_hit_bullets = {}            # 플레이어를 맞힌 총알 id -> 맞은 프레임

_p_coll = Player.handle_collision
def p_coll(self, group, other):
    if group == 'player:bullet' and other.state == 'FLYING':
        if other.owner == 'player':
            ctx['cause'] = '내 튕긴 총알'
        elif other.bounces:
            ctx['cause'] = '적의 튕긴 총알'
        else:
            ctx['cause'] = '적 총알 직격'
        ctx['bullet'] = other
    _p_coll(self, group, other)
    ctx['cause'] = ctx['bullet'] = None
Player.handle_collision = p_coll

_e_coll = Enemy.handle_collision
def e_coll(self, group, other):
    if group == 'player:enemy':
        ctx['cause'] = '몸통 박치기(%s)' % type(self).__name__
    _e_coll(self, group, other)
    ctx['cause'] = None
Enemy.handle_collision = e_coll

_hurt = Player.hurt
def hurt(self):
    hp = self.hp
    _hurt(self)
    if self.hp < hp:
        LOG['피해:' + (ctx['cause'] or '기타')] += 1
        if ctx['bullet'] is not None:
            recent_hit_bullets[id(ctx['bullet'])] = frame['n']
Player.hurt = hurt

_pick = Player.pick_up
def pick_up(self, b):
    LOG['줍기:플레이어'] += 1
    f = recent_hit_bullets.pop(id(b), None)
    if f is not None and frame['n'] - f <= 6:
        LOG['맞은 총알을 0.1초 안에 그대로 주움'] += 1
    _pick(self, b)
Player.pick_up = pick_up

_pick_done = Enemy.pick_done
def pick_done(self):
    r = _pick_done(self)
    if r:
        LOG['줍기:적(%s)' % type(self).__name__] += 1
    return r
Enemy.pick_done = pick_done

_hit_by = Enemy.hit_by
def hit_by(self, bullet, point=None):
    if bullet.owner == 'player':
        LOG['적 피격:플레이어 ' + ('튕긴 총알' if bullet.bounces else '직격')] += 1
    elif bullet.owner is self:
        LOG['적 피격:자기 튕긴 총알(자멸)'] += 1
    else:
        LOG['적 피격:다른 적의 튕긴 총알'] += 1
    _hit_by(self, bullet, point)
Enemy.hit_by = hit_by

_shoved = Player.shoved
def shoved(self, angle, x, y):
    r = _shoved(self, angle, x, y)
    if r:
        LOG['밀쳐져 총알 뺏김'] += 1
    return r
Player.shoved = shoved

_fell = play_mode.fell_off_train
def fell(o):
    LOG['추락:' + ('플레이어' if o is play_mode.player else type(o).__name__)] += 1
    if o is play_mode.player:
        LOG['피해:추락'] += 1
    _fell(o)
play_mode.fell_off_train = fell


# ------------------------------------------------------------ 봇
class Bot:
    def __init__(self, pm, rng):
        self.pm, self.rng = pm, rng
        self.dodge = 0
        self.dodge_dir = (0, 0)
        self.shot_gap = 0

    def keys(self, dx, dy):
        want = set()
        if dx > 4: want.add(SDLK_d)
        if dx < -4: want.add(SDLK_a)
        if dy > 4: want.add(SDLK_w)
        if dy < -4: want.add(SDLK_s)
        for k in (SDLK_w, SDLK_a, SDLK_s, SDLK_d):
            (sim.key_down if k in want else sim.key_up)(k)

    def act(self):
        pm = self.pm
        p = pm.player
        alive = [e for e in pm.enemies if e.alive]
        if not alive:
            self.keys(0, 0)
            return
        dist = lambda o: math.hypot(o.x - p.x, o.y - p.y)
        target = min(alive, key=dist)
        self.shot_gap = max(0, self.shot_gap - 1)
        threat = [e for e in alive if getattr(e, 'aiming', None) and e.aiming()]
        if self.dodge > 0:
            self.dodge -= 1
            self.keys(*self.dodge_dir)
        elif threat:
            t = threat[0]
            ax, ay = t.x - p.x, t.y - p.y
            side = self.rng.choice((-1, 1))
            self.dodge_dir = (-ay * side, ax * side)           # 조준선의 옆으로
            self.dodge = 18
            self.keys(*self.dodge_dir)
        elif p.held:
            d = dist(target)
            if d < 200:
                self.keys(p.x - target.x, p.y - target.y)
            elif d > 360:
                self.keys(target.x - p.x, target.y - p.y)
            else:
                self.keys(0, 0)
        else:
            floor = [o for o in game_world.objects() if isinstance(o, Bullet) and o.state == 'FLOOR']
            if floor:
                b = min(floor, key=dist)
                self.keys(b.x - p.x, b.y - p.y)
            else:
                holder = [e for e in alive if e.held] or alive
                e = min(holder, key=dist)
                self.keys(e.x - p.x, e.y - p.y)
        sim.mouse_move(target.x, target.y)
        if p.held and self.shot_gap == 0 and dist(target) < 520:
            sim.click()
            self.shot_gap = 18
        close = [e for e in alive if dist(e) < p.radius + e.radius + 40]
        if close and p.kick_cooldown <= 0:
            sim.mouse_move(close[0].x, close[0].y)
            p.kick()


def run(index, trials, limit_s=90):
    results = []
    for k in range(trials):
        game_framework.running = True
        game_framework.stack = [play_mode]
        play_mode.SPAWN_ENEMIES = True
        random.seed(1000 + k)
        play_mode.init()
        if index:
            play_mode.start_zone(index)
        game_framework.stack = [play_mode]
        if ZONES[index].get('duel'):
            boss = [e for e in play_mode.enemies if type(e).__name__ == 'Boss'][0]
            boss.hp -= 1                                    # 결투에서 이겼다고 치고 시작 (체력 7, 손 4 + 바닥 2)
            for x, y in config.DUEL_WIN_FLOOR:
                b = play_mode.player.held.pop()
                b.drop(x, y)
                b.add_to_world()
            LOG['_boss'] = boss
        bot = Bot(play_mode, random.Random(k))
        hp0 = play_mode.player.hp
        outcome, t = '시간초과', limit_s
        for i in range(limit_s * 60):
            frame['n'] += 1
            sim.step(1, before=lambda _: bot.act())
            if play_mode.player.hp <= 0:
                outcome, t = '패배', i / 60
                break
            if not any(e.alive for e in play_mode.enemies):
                outcome, t = '클리어', i / 60
                break
        results.append((outcome, t, hp0 - max(play_mode.player.hp, 0)))
        bo = LOG.pop('_boss', None)
        if bo is not None and bo.phase == 2:
            LOG['두목 2페이즈 도달'] += 1
        game_framework.stack = [play_mode]
        play_mode.finish()
    return results


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    plan = [(0, n), (1, n), (2, n), (3, max(1, n * 3 // 4))]
    if len(sys.argv) > 2:
        plan = [(int(sys.argv[2]), n)]
    for index, n in plan:
        LOG.clear()
        res = run(index, n)
        outs = Counter(r[0] for r in res)
        clear_t = [r[1] for r in res if r[0] == '클리어']
        print('=== %s (%d판) ===' % (ZONES[index]['name'], n))
        print('  결과:', dict(outs))
        print('  클리어 시간 평균: %s초' % (round(sum(clear_t) / len(clear_t), 1) if clear_t else '-'))
        print('  잃은 체력 평균: %.2f / 판' % (sum(r[2] for r in res) / n))
        for key in sorted(k for k in LOG if not k.startswith('_')):
            print('  %s: %d (판당 %.1f)' % (key, LOG[key], LOG[key] / n))
        sys.stdout.flush()
