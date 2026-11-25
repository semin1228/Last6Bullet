# 자동 점검 공용 도우미: 테스트 등록(test), 새 게임 시작(fresh), 각 장이 함께 쓰는 보조 함수.
import math
import random

import sim                       # 먼저 불러야 게임 폴더가 import 경로에 들어간다

import config
import duel_mode
import game_framework
import game_world
import play_mode
from boss import Boss
from bullet import Bullet
from drunk import Drunk
from picker import Picker
from pico2d import SDL_MOUSEBUTTONDOWN
from zone import ZONES

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def fresh(enemies=False):
    # 기본은 적 없이 시작한다 (1주차 테스트는 플레이어와 총알만 본다). 적 테스트는 enemies=True 나 add_enemy 로.
    game_framework.running = True
    game_framework.stack = [play_mode]
    play_mode.SPAWN_ENEMIES = enemies
    random.seed(7)                 # 적이 비켜 걷는 방향 등 무작위 값을 매번 같게 (결과가 실행마다 달라지지 않게)
    play_mode.init()
    return play_mode


def near(a, b, tol=1.0):
    return abs(a - b) <= tol


def bullets_in_world():
    return [o for o in game_world.objects() if isinstance(o, Bullet)]


def place(p, x, y):
    p.x, p.y = x, y
    sim.mouse_move(x + 100, y)     # 기본 조준은 오른쪽


def aim(p, angle_deg):
    a = math.radians(angle_deg)
    sim.mouse_move(p.x + math.cos(a) * 200, p.y + math.sin(a) * 200)


def shoot_randomly(dt):
    pm = fresh()
    rng = random.Random(1234)
    l, b, r, t = pm.zone.inner
    shots = []
    pm.ledger.expected += 500      # 검사용으로 총알을 직접 더 만든다
    for _ in range(500):
        bl = Bullet(pm.zone)
        x, y = pm.zone.push_out(rng.uniform(l, r), rng.uniform(b, t), bl.radius)
        bl.fire(x, y, rng.uniform(0, 6.283), 'player')
        game_world.add_object(bl, 1)
        shots.append(bl)
    for frame in range(int(config.BULLET_LIFE / dt) + 2):
        sim.step(1, dt=dt)
        for bl in shots:
            assert l <= bl.x <= r and b <= bl.y <= t, '벽 밖으로 나감 (%d 프레임)' % frame
            for ol, ob, o_r, ot in pm.zone.obstacles:
                inside = ol < bl.x < o_r and ob < bl.y < ot
                assert not inside, '테이블 안으로 뚫고 들어감 (%d 프레임)' % frame
    assert all(bl.state == 'FLOOR' for bl in shots)
    pm.finish()


def flying_bullet(pm, x, y, vx, vy, bounces, age=None):
    # age 를 주지 않으면 '발사 직후 맞지 않는 시간'이 막 지난 총알로 만든다 (수명은 거의 그대로 남는다)
    if age is None:
        age = config.HIT_GRACE + 0.01
    b = pm.player.held.pop()
    b.fire(x, y, 0.0, 'player')
    b.vx, b.vy, b.bounces, b.age = vx, vy, bounces, age
    b.add_to_world()
    return b


def effects(kind):
    return [o for o in game_world.objects() if isinstance(o, kind)]


def floor_bullet(pm, x, y):
    # 손의 총알 하나를 (x, y) 바닥에 내려놓는다
    b = pm.player.held.pop()
    b.drop(x, y)
    b.add_to_world()
    return b


def math_atan(y, x):
    return math.atan2(y, x)


def run_until(cond, limit=600):
    # cond() 가 참이 될 때까지 프레임을 돌린다. 걸린 프레임 수를 돌려주고, 넘치면 실패
    for i in range(limit):
        if cond():
            return i
        sim.step(1)
    raise AssertionError('%d 프레임 안에 조건이 이뤄지지 않음' % limit)


def lunge_setup(pm, gap=60):
    # 빈손 줍줍이 오른쪽 gap px 옆에 총알 6발을 든 플레이어 (장애물 없는 곳)
    p = pm.player
    p.x, p.y = 640, 360
    pk = pm.add_enemy(Picker, p.x + p.radius + 13 + gap, p.y)
    pk.state = 'FLEE'
    return pk


def Picker_cls():
    return Picker


def blocked_by_obstacle(zone, a, b):
    # a 와 b 사이 선분이 장애물을 지나는지 (20등분 점으로 본다)
    for ol, ob, o_r, ot in zone.obstacles:
        for k in range(1, 20):
            x, y = a.x + (b.x - a.x) * k / 20, a.y + (b.y - a.y) * k / 20
            if ol < x < o_r and ob < y < ot:
                return True
    return False


def pass_setup(pm, picker_at=(1050, 200), bullet_at=(760, 200), drunk_at=(700, 200)):
    # 술꾼 옆에 바닥 총알, 멀리 빈손 줍줍이(움직이지 않음), 플레이어는 구석
    p = pm.player
    p.x, p.y = 100, 650
    mate = still_picker(pm, *picker_at)
    ball = floor_bullet(pm, *bullet_at)
    d = pm.add_enemy(Drunk, *drunk_at)
    d.pass_cooldown = 0
    return d, ball, mate


def still_picker(pm, x, y):
    e = pm.add_enemy(Picker, x, y)
    e.state, e.SPEED = 'FLEE', 0           # 스스로 움직이지 않게 (발차기 효과만 본다)
    return e


def train(pm):
    # 3구역 기차로 가서, 덜컹이 저절로 오지 않게 멀리 미뤄 둔다 (덜컹 테스트는 직접 일으킨다)
    pm.start_zone(2)
    pm.zone.jolt_in = 999.0
    return pm.zone


def bank_with_boss(pm, x=900, y=360):
    pm.start_zone(len(ZONES) - 1)                   # 적 자동 배치를 끈 상태라 결투도 올라오지 않는다
    return pm.add_enemy(Boss, x, y)


def duel_setup():
    # 3구역 기차에서 문을 지나 은행으로 들어간다 (적 자동 배치를 켜야 두목과 결투가 나온다)
    pm = fresh()
    play_mode.SPAWN_ENEMIES = True
    pm.start_zone(len(ZONES) - 2, keep=None)
    pm.zone_index = len(ZONES) - 2
    for e in pm.enemies:
        e.alive = False
    pm.next_zone()                                  # 은행으로 (결투가 위에 올라온다)
    assert game_framework.stack[-1] is duel_mode, '은행에 들어갔는데 결투가 없음'
    return pm, duel_mode


def click_left():
    duel_mode.dispatch(sim.FakeEvent(SDL_MOUSEBUTTONDOWN, button=1))
