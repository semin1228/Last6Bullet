# 자동 점검: 기능마다 명세를 테스트로 옮겨 두고, 게임 루프를 고정 프레임으로 돌려 확인한다.
#   C:\Python313\python.exe tools\check.py            창 없이 실행
#   C:\Python313\python.exe tools\check.py --window   창을 띄워 실행
import sys
import traceback

import sim

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def fresh():
    import game_framework
    import play_mode
    game_framework.running = True
    play_mode.init()
    return play_mode


# ---------------------------------------------------------------- 1. 뼈대

@test
def skeleton_runs_and_esc_quits():
    import game_framework
    from pico2d import SDLK_ESCAPE
    pm = fresh()
    sim.step(120)
    assert pm.zone is not None
    sim.key_down(SDLK_ESCAPE)
    assert game_framework.running is False, 'ESC 를 눌러도 종료되지 않음'
    pm.finish()


# ---------------------------------------------------------------- 2. 이동과 조준

def near(a, b, tol=1.0):
    return abs(a - b) <= tol


@test
def move_right_for_one_second():
    import config
    from pico2d import SDLK_d
    pm = fresh()
    p = pm.player
    x0, y0 = p.x, p.y
    sim.key_down(SDLK_d)
    assert p.state == 'RUN'
    sim.step(60)
    assert near(p.x - x0, config.PLAYER_SPEED), '1초에 %.1f px 이동 (기대 %d)' % (p.x - x0, config.PLAYER_SPEED)
    assert near(p.y, y0)
    sim.key_up(SDLK_d)
    assert p.state == 'IDLE'
    x1 = p.x
    sim.step(30)
    assert p.x == x1, '키를 뗐는데 계속 움직임'
    pm.finish()


@test
def diagonal_has_same_speed():
    import config, math
    from pico2d import SDLK_d, SDLK_w
    pm = fresh()
    p = pm.player
    x0, y0 = p.x, p.y
    sim.key_down(SDLK_w)
    sim.key_down(SDLK_d)
    sim.step(60)
    dist = math.hypot(p.x - x0, p.y - y0)
    assert near(dist, config.PLAYER_SPEED), '대각선 1초 이동 거리 %.1f' % dist
    pm.finish()


@test
def opposite_keys_cancel():
    from pico2d import SDLK_a, SDLK_d
    pm = fresh()
    p = pm.player
    x0 = p.x
    sim.key_down(SDLK_a)
    sim.key_down(SDLK_d)
    assert p.state == 'IDLE', '반대 방향 키를 같이 눌렀는데 RUN'
    sim.step(30)
    assert p.x == x0
    pm.finish()


@test
def cannot_leave_the_floor():
    from pico2d import SDLK_a, SDLK_s
    pm = fresh()
    p = pm.player
    l, b, r, t = pm.zone.inner
    sim.key_down(SDLK_a)
    sim.key_down(SDLK_s)
    sim.step(600)
    assert near(p.x, l + p.radius) and near(p.y, b + p.radius), '벽 밖으로 나감: (%.1f, %.1f)' % (p.x, p.y)
    pm.finish()


@test
def aim_follows_mouse_even_while_moving():
    import math
    from pico2d import SDLK_d
    pm = fresh()
    p = pm.player
    sim.mouse_move(p.x + 100, p.y)
    sim.step(1)
    assert near(p.aim, 0.0, 0.02), '오른쪽 조준 %.3f' % p.aim
    sim.mouse_move(p.x, p.y + 100)
    sim.step(1)
    assert near(p.aim, math.pi / 2, 0.02), '위쪽 조준 %.3f' % p.aim
    mx = p.x
    sim.key_down(SDLK_d)           # 마우스는 그대로 두고 오른쪽으로 이동하면 조준이 왼쪽 위로 기운다
    sim.step(30)
    assert p.aim > math.pi / 2 and near(p.aim, math.atan2(100, mx - p.x), 0.02)
    pm.finish()


# ---------------------------------------------------------------- 3. 발사와 총알 상태

def bullets_in_world():
    import game_world
    from bullet import Bullet
    return [o for o in game_world.objects() if isinstance(o, Bullet)]


@test
def start_with_six_bullets_in_hand():
    import config
    pm = fresh()
    assert len(pm.player.held) == config.AMMO
    assert all(b.state == 'HELD' for b in pm.player.held)
    assert bullets_in_world() == []
    pm.finish()


@test
def click_fires_toward_mouse_immediately():
    import config, math
    pm = fresh()
    p = pm.player
    sim.mouse_move(p.x, p.y + 200)  # 마우스를 위로 옮기고 같은 프레임에 바로 쏜다
    sim.click()
    assert len(p.held) == config.AMMO - 1
    [b] = bullets_in_world()
    assert b.state == 'FLYING' and b.owner == 'player'
    assert near(math.atan2(b.vy, b.vx), math.pi / 2, 0.01), '이전 조준 방향으로 나감'
    y0 = b.y
    sim.step(10)
    assert near(b.y - y0, config.BULLET_SPEED * 10 / 60, 1.0)
    pm.finish()


@test
def cooldown_blocks_rapid_double_click():
    import config
    pm = fresh()
    p = pm.player
    sim.click()
    sim.click()
    assert len(p.held) == config.AMMO - 1, '연사 간격 안에 두 발이 나감'
    sim.step(int(config.FIRE_COOLDOWN * 60) + 1)
    sim.click()
    assert len(p.held) == config.AMMO - 2
    pm.finish()


@test
def empty_gun_does_nothing():
    import config
    pm = fresh()
    p = pm.player
    for _ in range(config.AMMO + 2):
        sim.click()
        sim.step(15)
    assert p.held == []
    assert len(bullets_in_world()) == config.AMMO, '총알 수가 변함'
    pm.finish()


@test
def flying_bullet_stops_on_floor():
    import config
    pm = fresh()
    sim.mouse_move(pm.player.x + 300, pm.player.y)
    sim.step(1)
    sim.click()
    [b] = bullets_in_world()
    sim.step(int(config.BULLET_LIFE * 60) + 5)
    assert b.state == 'FLOOR' and (b.vx, b.vy) == (0, 0)
    l, bt, r, t = pm.zone.inner
    assert l <= b.x <= r and bt <= b.y <= t, '총알이 벽 밖에 떨어짐'
    pm.finish()


# ---------------------------------------------------------------- 4. 벽과 장애물 반사

def place(p, x, y):
    p.x, p.y = x, y
    sim.mouse_move(x + 100, y)     # 기본 조준은 오른쪽


def aim(p, angle_deg):
    import math
    a = math.radians(angle_deg)
    sim.mouse_move(p.x + math.cos(a) * 200, p.y + math.sin(a) * 200)


@test
def bullet_bounces_off_right_wall():
    pm = fresh()
    p = pm.player
    aim(p, 0)
    sim.click()
    [b] = bullets_in_world()
    sim.step(80)                   # 벽까지 약 600px, 1.15초
    assert b.state == 'FLYING' and b.bounces == 1 and b.vx < 0, '오른쪽 벽에서 튕기지 않음'
    pm.finish()


@test
def third_hit_lands_the_bullet():
    import config
    pm = fresh()
    life = config.BULLET_LIFE
    config.BULLET_LIFE = 99        # 수명 대신 튕긴 횟수로 떨어지는지만 본다
    try:
        p = pm.player
        aim(p, 0)
        sim.click()
        [b] = bullets_in_world()
        while b.state == 'FLYING':
            sim.step(1)
        assert b.bounces == config.MAX_BOUNCES + 1, '튕긴 횟수 %d' % b.bounces
    finally:
        config.BULLET_LIFE = life
    pm.finish()


@test
def bullet_bounces_off_table():
    import config
    pm = fresh()
    p = pm.player
    l, b, r, t = config.SALOON_TABLES[0]
    place(p, (l + r) / 2, b - 80)  # 첫 번째 테이블 바로 아래에서 위로 쏜다
    aim(p, 90)
    sim.click()
    [bl] = bullets_in_world()
    sim.step(20)
    assert bl.bounces == 1 and bl.vy < 0, '테이블 아랫면에서 튕기지 않음'
    assert bl.y < b, '총알이 테이블을 통과함'
    pm.finish()


@test
def player_cannot_walk_through_table():
    import config
    from pico2d import SDLK_w
    pm = fresh()
    p = pm.player
    l, b, r, t = config.SALOON_TABLES[0]
    place(p, (l + r) / 2, b - 60)
    sim.key_down(SDLK_w)
    sim.step(120)
    assert near(p.y, b - p.radius), '테이블을 뚫고 지나감: y=%.1f' % p.y
    pm.finish()


@test
def no_tunneling_in_500_random_shots():
    shoot_randomly(sim.DT)


@test
def thin_wall_is_not_tunneled_at_slowest_frame_rate():
    # 두께 6px 벽(3주차 기차 짐받이 턱 정도)을 세우고, 가장 느린 프레임(한 프레임 26px 이동)에서
    # 왼쪽에서 오른쪽으로 쏜 총알이 한 발도 벽 너머로 넘어가지 않는지 본다.
    import random, game_world, game_framework
    from bullet import Bullet
    pm = fresh()
    wall = (700, 40, 706, 680)
    pm.zone.obstacles = [wall]
    rng = random.Random(99)
    shots = []
    for _ in range(200):
        bl = Bullet(pm.zone)
        bl.fire(rng.uniform(100, 600), rng.uniform(60, 660), rng.uniform(-1.2, 1.2), 'player')
        game_world.add_object(bl, 1)
        shots.append(bl)
    for frame in range(40):
        sim.step(1, dt=game_framework.MAX_FRAME_TIME)
        crossed = [bl for bl in shots if bl.x > wall[2]]
        assert not crossed, '%d발이 얇은 벽을 뚫고 지나감 (%d 프레임)' % (len(crossed), frame)
    pm.finish()


def shoot_randomly(dt):
    import random, game_world, config
    from bullet import Bullet
    pm = fresh()
    rng = random.Random(1234)
    l, b, r, t = pm.zone.inner
    shots = []
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


def main():
    sim.open_game('--window' in sys.argv)
    from pico2d import close_canvas
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print('  PASS', fn.__name__)
        except Exception:
            failed += 1
            print('  FAIL', fn.__name__)
            traceback.print_exc()
            import play_mode
            play_mode.finish()
    close_canvas()
    print('%d/%d passed' % (len(TESTS) - failed, len(TESTS)))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
