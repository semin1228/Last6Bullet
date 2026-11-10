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
