# 자동 점검: 기능마다 명세를 테스트로 옮겨 두고, 게임 루프를 고정 프레임으로 돌려 확인한다.
#   C:\Python313\python.exe tools\check.py            창 없이 실행
#   C:\Python313\python.exe tools\check.py --window   창을 띄워 실행
import random
import sys
import traceback

import sim

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def fresh(enemies=False):
    # 기본은 적 없이 시작한다 (1주차 테스트는 플레이어와 총알만 본다). 적 테스트는 enemies=True 나 add_enemy 로.
    import game_framework
    import play_mode
    game_framework.running = True
    game_framework.stack = [play_mode]
    play_mode.SPAWN_ENEMIES = enemies
    random.seed(7)                 # 적이 비켜 걷는 방향 등 무작위 값을 매번 같게 (결과가 실행마다 달라지지 않게)
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


@test
def crosshair_sits_on_mouse_and_greys_out_when_empty():
    import config, game_world
    from crosshair import Crosshair
    pm = fresh()
    p = pm.player
    [ch] = [o for o in game_world.objects() if isinstance(o, Crosshair)]
    sim.mouse_move(900, 200)
    assert p.mouse == (900, 200), '조준점 위치가 마우스와 다름: %s' % (p.mouse,)
    assert ch.color() == config.COLOR_CROSSHAIR
    p.held.clear()                 # 빈 총 흉내 (총알 수 검사는 이 테스트에서 보지 않는다)
    assert ch.color() == config.COLOR_CROSSHAIR_EMPTY, '빈 총인데 조준점 색이 그대로'
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
def empty_click_says_click_and_flashes_cylinder():
    import config, game_world
    from effect import TextPop
    from hud import Hud
    pm = fresh()
    p = pm.player
    [hud] = [o for o in game_world.objects() if isinstance(o, Hud)]
    pops = lambda: [o for o in game_world.objects() if isinstance(o, TextPop)]
    sim.click()                    # 총알이 있을 때는 'CLICK' 이 나오지 않는다
    assert pops() == [] and p.dry_flash == 0
    p.x -= 300                     # 첫 발이 돌아와 내게 맞고 주워지지 않게 비켜선다
    for _ in range(config.AMMO):
        sim.step(15)
        sim.click()
    assert p.held == [] and len(pops()) == 1, '빈 총 클릭에 CLICK 이 %d개' % len(pops())
    assert hud.rim_color() == config.COLOR_CROSSHAIR, '실린더 테두리가 붉어지지 않음'
    sim.click()                    # 바로 또 눌러도 연사 간격 동안은 글자가 쌓이지 않는다
    assert len(pops()) == 1
    sim.step(int(max(config.DRY_FLASH_TIME, 0.5) * 60) + 2)
    assert pops() == [], 'CLICK 글자가 사라지지 않음'
    assert hud.rim_color() == config.COLOR_CROSSHAIR_EMPTY
    assert pm.ledger.problem is None
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


@test
def hud_cylinder_matches_bullets_in_hand():
    import config, game_world
    from hud import Hud
    pm = fresh()
    p = pm.player
    [hud] = [o for o in game_world.objects() if isinstance(o, Hud)]
    assert sum(loaded for _, _, loaded in hud.chambers()) == config.AMMO
    for shot in range(1, 4):
        aim(p, 90 * shot)
        p.fire_cooldown = 0
        p.fire()
        loaded = [l for _, _, l in hud.chambers()]
        assert sum(loaded) == config.AMMO - shot, '실린더 %d칸 (기대 %d)' % (sum(loaded), config.AMMO - shot)
        assert loaded == sorted(loaded, reverse=True), '채워진 칸이 앞쪽부터 이어지지 않음: %s' % loaded
    for x, y, _ in hud.chambers():
        assert config.HEIGHT - config.WALL <= y <= config.HEIGHT, '실린더가 위쪽 벽 밖으로 나감'
    assert hud.zone.title == 'ZONE 1 · SALOON'
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
    import config, math
    l, bt, r, t = pm.zone.inner
    distance = (r - b.radius) - b.x  # 총구에서 오른쪽 벽 면까지
    sim.step(math.ceil(distance / config.BULLET_SPEED * 60) + 3)   # 속도를 바꿔도 벽에 닿은 직후를 본다
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
        p.y += 200                 # 튕겨 돌아오는 총알에 맞지 않게 비켜선다 (반사만 확인)
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
    p.x += 100                     # 튕겨 돌아오는 총알에 맞지 않게 비켜선다 (반사만 확인)
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
    pm.ledger.expected += 200      # 검사용으로 총알을 직접 더 만든다
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


@test
def hugging_a_thin_wall_does_not_shoot_through_it():
    # 6px 벽에 몸을 붙이고 벽 쪽으로 쏘면 총구(몸 중심에서 24px)가 벽 너머에 있다.
    # 총알이 총구에서 바로 생기면 벽 반대편에서 나오므로, 몸에서 총구까지도 벽 검사를 해야 한다.
    import game_world
    from bullet import Bullet
    pm = fresh()
    p = pm.player
    wall = (700, 40, 706, 680)
    pm.zone.obstacles = [wall]
    for deg in (0, 30, -30, 60):
        p.x, p.y = pm.zone.push_out(wall[0] - 1, 360, p.radius)   # 벽 왼쪽 면에 붙인다
        aim(p, deg)
        p.fire_cooldown = 0
        bl = p.fire()
        assert bl.x <= wall[0], '%d도: 총알이 벽 너머(x=%.1f)에서 생김' % (deg, bl.x)
        sim.step(10)
        assert bl.x <= wall[0], '%d도: 총알이 벽을 뚫고 지나감 (x=%.1f)' % (deg, bl.x)
        game_world.remove_object(bl)                 # 다음 각도 검사를 위해 치운다
        bl.state = 'HELD'
        p.held.append(bl)
    pm.finish()


@test
def hugging_a_table_bounces_off_its_near_face():
    # 테이블 아랫면에 붙어 위로 쏘면 총알은 테이블 안이나 윗쪽이 아니라 아랫면에서 튕겨 내려와야 한다
    import config
    pm = fresh()
    p = pm.player
    l, b, r, t = config.SALOON_TABLES[0]
    p.x, p.y = pm.zone.push_out((l + r) / 2, b - 1, p.radius)
    aim(p, 90)
    bl = p.fire()
    assert bl.y <= b and bl.vy < 0 and bl.bounces == 1, '아랫면에서 튕기지 않음 (y=%.1f, vy=%.1f)' % (bl.y, bl.vy)
    pm.finish()


def shoot_randomly(dt):
    import random, game_world, config
    from bullet import Bullet
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


# ---------------------------------------------------------------- 5. 줍기와 튕긴 총알 자해

def flying_bullet(pm, x, y, vx, vy, bounces, age=None):
    # age 를 주지 않으면 '발사 직후 맞지 않는 시간'이 막 지난 총알로 만든다 (수명은 거의 그대로 남는다)
    import config, game_world
    if age is None:
        age = config.HIT_GRACE + 0.01
    from bullet import Bullet
    b = pm.player.held.pop()
    b.fire(x, y, 0.0, 'player')
    b.vx, b.vy, b.bounces, b.age = vx, vy, bounces, age
    b.add_to_world()
    return b


@test
def walking_over_floor_bullet_picks_it_up():
    import config
    from pico2d import SDLK_d
    pm = fresh()
    p = pm.player
    aim(p, 0)
    sim.click()
    [b] = bullets_in_world()
    while b.state != 'FLOOR':
        sim.step(1)
    p.x, p.y = b.x - 60, b.y       # 총알 왼쪽 60px 에서 걸어간다
    sim.key_down(SDLK_d)
    sim.step(30)
    assert b.state == 'HELD' and b in p.held, '바닥 총알을 줍지 못함'
    assert len(p.held) == config.AMMO and bullets_in_world() == []
    pm.finish()


@test
def own_unbounced_bullet_passes_through():
    import config
    pm = fresh()
    p = pm.player
    b = flying_bullet(pm, p.x - 60, p.y, config.BULLET_SPEED, 0, bounces=0)
    sim.step(20)
    assert p.hp == config.PLAYER_HP, '튕기지 않은 내 총알에 맞음'
    assert b.state == 'FLYING' and b.x > p.x + p.radius
    pm.finish()


@test
def bounced_bullet_hurts_and_drops():
    import config
    pm = fresh()
    p = pm.player
    b = flying_bullet(pm, p.x - 60, p.y, config.BULLET_SPEED, 0, bounces=1)
    sim.step(20)
    assert p.hp == config.PLAYER_HP - 1 and p.invincible > 0
    # 맞힌 총알은 맞은 자리(내 발밑)에 떨어지고, 그 위에 서 있으니 곧바로 주워진다
    assert b.state == 'HELD' and b in p.held, '맞힌 총알이 발밑에 떨어져 주워지지 않음'
    pm.finish()


@test
def bullet_that_hit_you_drops_at_your_feet():
    import config
    pm = fresh()
    p = pm.player
    b = flying_bullet(pm, p.x - 60, p.y, config.BULLET_SPEED, 0, bounces=1)
    while b.state == 'FLYING':
        sim.step(1)
    assert b.state == 'FLOOR', '맞힌 총알이 바닥에 떨어지지 않음'
    assert abs(b.x - p.x) <= p.radius + b.radius, '맞은 자리에 떨어지지 않음'
    pm.finish()


@test
def invincibility_blocks_second_hit():
    import config
    pm = fresh()
    p = pm.player
    flying_bullet(pm, p.x - 60, p.y, config.BULLET_SPEED, 0, bounces=1)
    flying_bullet(pm, p.x + 60, p.y, -config.BULLET_SPEED, 0, bounces=1)
    sim.step(20)
    assert p.hp == config.PLAYER_HP - 1, '무적 시간에 또 맞음 (체력 %d)' % p.hp
    sim.step(int(config.INVINCIBLE_TIME * 60) + 1)
    flying_bullet(pm, p.x - 60, p.y, config.BULLET_SPEED, 0, bounces=1)
    sim.step(20)
    assert p.hp == config.PLAYER_HP - 2, '무적이 끝났는데 맞지 않음'
    pm.finish()


@test
def shooting_a_wall_up_close_hurts_yourself():
    # 실제 상황 재현: 오른쪽 벽 바로 앞에서 벽을 쏘면 튕겨 나온 총알에 내가 맞는다
    import config
    pm = fresh()
    p = pm.player
    l, b, r, t = pm.zone.inner
    place(p, r - 80, (b + t) / 2)
    aim(p, 0)
    sim.click()
    sim.step(30)
    assert p.hp == config.PLAYER_HP - 1, '벽에 튕긴 내 총알에 맞지 않음'
    pm.finish()


# ---------------------------------------------------------------- 5-2. 연출

def effects(kind):
    import game_world
    return [o for o in game_world.objects() if isinstance(o, kind)]


@test
def firing_shows_a_short_muzzle_flash_at_the_bullet():
    from effect import MuzzleFlash
    pm = fresh()
    p = pm.player
    aim(p, 45)
    bl = p.fire()
    [fl] = effects(MuzzleFlash)
    assert (fl.x, fl.y) == (bl.x, bl.y), '불꽃이 총알이 나온 자리에 없음'
    sim.step(6)                    # 0.1초 뒤에는 사라진다
    assert effects(MuzzleFlash) == [], '총구 불꽃이 남아 있음'
    pm.finish()


@test
def bounce_throws_sparks_away_from_the_wall():
    import math
    from effect import Spark
    pm = fresh()
    p = pm.player
    l, b, r, t = pm.zone.inner
    aim(p, 0)
    bl = p.fire()
    p.y += 200                     # 돌아오는 총알에 맞지 않게 비켜선다
    while bl.bounces == 0:
        sim.step(1)
    [sp] = effects(Spark)
    assert abs(sp.x - (r - bl.radius)) < 1, '불똥이 오른쪽 벽에 없음 (x=%.1f)' % sp.x
    assert math.cos(sp.angle) < 0, '불똥이 벽 안쪽(오른쪽)으로 퍼짐'
    sim.step(10)
    assert effects(Spark) == []
    pm.finish()


@test
def picking_up_shows_a_small_brass_ring():
    import config
    from effect import Ring
    pm = fresh()
    p = pm.player
    aim(p, 0)
    bl = p.fire()
    while bl.state != 'FLOOR':
        sim.step(1)
    assert effects(Ring) == []
    p.x, p.y = bl.x, bl.y
    sim.step(1)
    [ring] = effects(Ring)
    assert ring.color == config.COLOR_BULLET_FLOOR and (ring.x, ring.y) == (bl.x, bl.y)
    sim.step(20)
    assert effects(Ring) == []
    pm.finish()


@test
def getting_hit_shows_a_red_ring_once():
    import config
    from effect import Ring
    pm = fresh()
    p = pm.player
    flying_bullet(pm, p.x - 60, p.y, config.BULLET_SPEED, 0, bounces=1)
    flying_bullet(pm, p.x + 60, p.y, -config.BULLET_SPEED, 0, bounces=1)
    sim.step(8)
    hits = [r for r in effects(Ring) if r.color == config.COLOR_HP]
    assert len(hits) == 1, '피격 고리 %d개 (무적 중 두 번째 총알은 연출도 없어야 함)' % len(hits)
    assert (hits[0].x, hits[0].y) == (p.x, p.y)
    pm.finish()


# ---------------------------------------------------------------- 6. 총알 장부

@test
def ledger_counts_hand_floor_and_air():
    pm = fresh()
    p = pm.player
    aim(p, 90)
    sim.click()
    sim.step(12)
    aim(p, -90)
    sim.click()
    sim.step(2)
    assert pm.ledger.counts == {'hand': 4, 'foes': 0, 'floor': 0, 'air': 2}, pm.ledger.counts
    p.x -= 200                     # 돌아오는 총알에 맞지 않게 비켜선다
    sim.step(120)
    assert pm.ledger.counts == {'hand': 4, 'foes': 0, 'floor': 2, 'air': 0}, pm.ledger.counts
    assert pm.ledger.problem is None
    pm.finish()


@test
def ledger_catches_a_lost_bullet():
    # 버그 흉내: 바닥 총알을 줍지도 않고 월드에서 지워 버리면 장부가 잡아내야 한다
    import game_world
    pm = fresh()
    aim(pm.player, 90)
    sim.click()
    [b] = bullets_in_world()
    game_world.remove_object(b)
    sim.step(1)
    assert pm.ledger.problem and '5' in pm.ledger.problem, '사라진 총알을 잡지 못함'
    pm.finish()


@test
def ledger_catches_a_wrong_state():
    # 버그 흉내: 손에 있는데 상태가 FLOOR 인 총알
    pm = fresh()
    pm.player.held[0].state = 'FLOOR'
    sim.step(1)
    assert pm.ledger.problem, '상태가 틀린 총알을 잡지 못함'
    pm.finish()


@test
def f1_shows_fps_near_frame_rate():
    from pico2d import SDLK_F1
    pm = fresh()
    sim.key_down(SDLK_F1)
    assert pm.ledger.visible
    sim.step(120)                  # 1/60초 프레임
    assert near(pm.ledger.fps, 60, 1), 'FPS %.1f' % pm.ledger.fps
    sim.step(120, dt=1 / 30)
    assert near(pm.ledger.fps, 30, 1), '느려진 뒤 FPS %.1f' % pm.ledger.fps
    sim.key_down(SDLK_F1)
    assert not pm.ledger.visible
    pm.finish()


@test
def screen_text_is_english():
    # 게임 화면 글자는 영어로 쓴다 (PRD 14장). 한글이 다시 섞이면 잡아낸다.
    import re, game_world
    from effect import TextPop
    from pico2d import SDLK_F1
    hangul = re.compile('[가-힣ㄱ-ㆎ]')
    pm = fresh()
    p = pm.player
    texts = [pm.zone.title]
    sim.key_down(SDLK_F1)
    sim.step(1)
    texts.append(pm.ledger.text())
    p.held[0].state = 'FLOOR'      # 장부 경고 문구도 화면에 나온다
    sim.step(1)
    texts.append(pm.ledger.text())
    p.held[0].state = 'HELD'
    for b in p.held:
        b.state = 'FLOOR'
    p.held.clear()
    p.dry_fire()
    texts += [o.text for o in game_world.objects() if isinstance(o, TextPop)]
    assert 'CLICK' in texts and 'SALOON' in pm.zone.title, texts
    bad = [t for t in texts if hangul.search(t)]
    assert not bad, '화면 글자에 한글: %s' % bad
    pm.finish()


@test
def random_play_for_50_seconds_keeps_six_bullets():
    # 무작위로 이동·조준·발사를 3000프레임 하면서 매 프레임 총알 수와 위치를 검사한다
    import random, config
    from pico2d import SDLK_a, SDLK_d, SDLK_s, SDLK_w
    pm = fresh()
    p = pm.player
    rng = random.Random(2026)
    keys = [SDLK_w, SDLK_a, SDLK_s, SDLK_d]
    l, b, r, t = pm.zone.inner
    picked = 0

    def walk_toward(tx, ty):
        want = set()
        if tx > p.x + 4: want.add(SDLK_d)
        if tx < p.x - 4: want.add(SDLK_a)
        if ty > p.y + 4: want.add(SDLK_w)
        if ty < p.y - 4: want.add(SDLK_s)
        for k in keys:
            (sim.key_down if k in want else sim.key_up)(k)

    detour = {'frames': 0, 'target': None, 'last': (p.x, p.y)}

    def act(i):
        floor = [bl for bl in bullets_in_world() if bl.state == 'FLOOR']
        if (i // 150) % 2 == 1 and floor:
            # 줍기 구간: 실제 플레이처럼 가장 가까운 바닥 총알로 걸어간다.
            # 테이블에 막혀 제자리면 잠깐 무작위 방향으로 비켜 걷는다.
            if detour['frames'] > 0:
                detour['frames'] -= 1
                walk_toward(*detour['target'])
            else:
                near_b = min(floor, key=lambda bl: (bl.x - p.x) ** 2 + (bl.y - p.y) ** 2)
                walk_toward(near_b.x, near_b.y)
                lx, ly = detour['last']
                if abs(p.x - lx) + abs(p.y - ly) < 0.5 and p.state == 'RUN':
                    detour['frames'] = 40
                    detour['target'] = (rng.uniform(l, r), rng.uniform(b, t))
            detour['last'] = (p.x, p.y)
        elif i % 20 == 0:
            for k in keys:
                (sim.key_down if rng.random() < 0.4 else sim.key_up)(k)
        if i % 7 == 0:
            sim.mouse_move(rng.uniform(l, r), rng.uniform(b, t))
        if rng.random() < 0.08:
            sim.click()
        p.hp = config.PLAYER_HP    # 체력 0 처리는 2주차라 검사 동안 유지한다

    for i in range(3000):
        held_before = len(p.held)
        sim.step(1, before=lambda _, i=i: act(i))   # step 안의 번호는 항상 0이라 전체 프레임 번호를 넘긴다
        picked += max(0, len(p.held) - held_before)
        assert pm.ledger.problem is None, '%d 프레임: %s' % (i, pm.ledger.problem)
        assert l <= p.x <= r and b <= p.y <= t
        for ol, ob, o_r, ot in pm.zone.obstacles:
            assert not (ol < p.x < o_r and ob < p.y < ot), '플레이어가 테이블 안에 있음'
        for bl in bullets_in_world():
            assert l <= bl.x <= r and b <= bl.y <= t, '총알이 벽 밖에 있음'
    assert picked > 0, '50초 동안 한 번도 줍지 않음 (검사가 의미 없음)'
    print('       (50초 동안 주운 총알 %d발)' % picked)
    pm.finish()


# ---------------------------------------------------------------- 8. 2주차: 총알 새 상태 (구름, 밟힘, 떨굼)

def floor_bullet(pm, x, y):
    # 손의 총알 하나를 (x, y) 바닥에 내려놓는다
    import game_world
    b = pm.player.held.pop()
    b.drop(x, y)
    b.add_to_world()
    return b


@test
def kicked_bullet_rolls_slows_and_stops():
    import config
    pm = fresh()
    b = floor_bullet(pm, 300, 200)
    pm.player.x, pm.player.y = 900, 500     # 굴러가는 길에서 비켜 둔다
    b.kick(0.0)
    assert b.state == 'ROLLING' and b.vx == config.ROLL_SPEED
    sim.step(10)
    assert 0 < b.vx < config.ROLL_SPEED, '마찰로 느려지지 않음 (vx=%.1f)' % b.vx
    frames = 0
    while b.state == 'ROLLING':
        sim.step(1)
        frames += 1
        assert frames < 300, '멈추지 않음'
    # 처음 속도 v, 마찰 a 이면 약 v^2/(2a) 만큼 간다
    expect = config.ROLL_SPEED ** 2 / (2 * config.ROLL_FRICTION)
    assert abs((b.x - 300) - expect) < 25, '굴러간 거리 %.0f (기대 약 %.0f)' % (b.x - 300, expect)
    assert b.state == 'FLOOR' and (b.vx, b.vy) == (0, 0)
    pm.finish()


@test
def rolling_bullet_halves_at_first_wall_and_stops_at_second():
    import config
    pm = fresh()
    l, bt, r, t = pm.zone.inner
    b = floor_bullet(pm, r - 30, 600)       # 오른쪽 벽 바로 앞 (벽에 붙은 총알 꺼내기)
    pm.player.x, pm.player.y = 200, 100
    b.kick(0.0)
    while b.bounces == 0:
        sim.step(1)
    assert b.vx < 0 and abs(b.vx) <= config.ROLL_SPEED / 2 + 1, '첫 벽에서 속도 절반으로 튕기지 않음 (vx=%.1f)' % b.vx
    pm.finish()
    pm = fresh()
    b = floor_bullet(pm, (l + r) / 2, t - 40)
    pm.player.x, pm.player.y = 200, 100
    b.vx = 0
    b.kick(math_atan(1, 0.02))              # 위쪽 벽에 거의 수직으로
    b.vx, b.vy = 0.0, 3000.0                # 두 번 튕길 만큼 세게 (테스트용)
    for _ in range(60):
        sim.step(1)
        if b.state != 'ROLLING':
            break
    assert b.state == 'FLOOR' and b.bounces == 2, '두 번째 벽에서 멈추지 않음 (%s, %d)' % (b.state, b.bounces)
    pm.finish()


def math_atan(y, x):
    import math
    return math.atan2(y, x)


@test
def rolling_and_pinned_bullets_hurt_nobody_and_player_cannot_take_pinned():
    import config
    pm = fresh()
    p = pm.player
    b = floor_bullet(pm, p.x - 80, p.y)
    b.kick(0.0)                             # 플레이어 쪽으로 굴린다
    sim.step(20)
    assert p.hp == config.PLAYER_HP, '구르는 총알에 맞음'
    pm.finish()
    pm = fresh()
    p = pm.player
    b = floor_bullet(pm, p.x + 200, p.y)
    b.pin()
    p.x = b.x                               # 적이 밟고 있는 총알 위에 선다
    sim.step(2)
    assert b.state == 'PINNED' and b not in p.held, '적이 줍는 중인 총알을 플레이어가 가져감'
    b.unpin()
    sim.step(1)
    assert b in p.held, '줍기가 끊긴 뒤에는 주울 수 있어야 함'
    pm.finish()


@test
def dropped_bullet_lands_inside_the_floor():
    pm = fresh()
    l, bt, r, t = pm.zone.inner
    b = floor_bullet(pm, r + 50, t + 50)    # 벽 밖 좌표를 줘도 바닥 안으로 꺼낸다
    assert l <= b.x <= r and bt <= b.y <= t and b.state == 'FLOOR'
    assert pm.ledger.check()
    pm.finish()


# ---------------------------------------------------------------- 9. 2주차: 적 공통과 줍줍이

def run_until(cond, limit=600):
    # cond() 가 참이 될 때까지 프레임을 돌린다. 걸린 프레임 수를 돌려주고, 넘치면 실패
    for i in range(limit):
        if cond():
            return i
        sim.step(1)
    raise AssertionError('%d 프레임 안에 조건이 이뤄지지 않음' % limit)


@test
def picker_walks_to_floor_bullet_picks_it_slowly_and_shoots_at_player():
    import config, math
    from picker import Picker
    pm = fresh()
    p = pm.player
    p.x, p.y = 300, 360
    b = floor_bullet(pm, 800, 360)
    pk = pm.add_enemy(Picker, 950, 360)
    run_until(lambda: pk.state == 'PICK')
    assert b.state == 'PINNED' and pk.target is b, '줍기 시작 때 총알이 밟히지 않음'
    frames = run_until(lambda: pk.state != 'PICK')
    assert pk.state == 'SHOOT' and b in pk.held, '줍기 뒤 SHOOT 가 아님 (%s)' % pk.state
    assert abs(frames - config.ENEMY_PICK_TIME * 60) <= 2, '줍기 동작 %d 프레임 (기대 약 %d)' % (frames, config.ENEMY_PICK_TIME * 60)
    run_until(lambda: b.state == 'FLYING')
    assert b.owner is pk
    angle = math.atan2(b.vy, b.vx)
    to_player = math.atan2(p.y - b.y, p.x - b.x)
    assert abs(angle - to_player) < 0.1, '플레이어 쪽으로 쏘지 않음'
    assert abs(math.hypot(b.vx, b.vy) - config.BULLET_SPEED) < 1, '적 총알 속도가 플레이어 총알과 다름'
    assert pm.ledger.problem is None and pm.ledger.counts['foes'] == 0
    pm.finish()


@test
def enemies_get_around_every_table_to_a_bullet_behind_it():
    # 실제로 찾은 문제: 테이블 바로 뒤의 총알로 곧장 가다 테이블에 막히면, 매번 무작위 방향으로 0.4초만
    # 비켜 걸어 좌우를 오가며 갇혔다 (들개 테스트가 5번 중 1번 실패).
    import config
    from picker import Picker
    from dog import Dog
    for seed in range(4):
        for l, b, r, t in config.SALOON_TABLES:
            for cls in (Picker, Dog):
                for below in (True, False):
                    pm = fresh()
                    import random as rnd
                    rnd.seed(seed)
                    pm.player.x, pm.player.y = 60, 60
                    cx = (l + r) / 2
                    by, ey = (b - 10, t + 30) if below else (t + 10, b - 30)
                    bl = floor_bullet(pm, cx, by)
                    e = pm.add_enemy(cls, cx, ey)
                    for f in range(360):
                        sim.step(1)
                        if bl in e.held:
                            break
                    assert bl in e.held, '%s 가 테이블 %s 너머 총알을 6초 안에 못 주움 (seed %d)' % (
                        cls.__name__, (l, b, r, t), seed)
                    pm.finish()


@test
def empty_picker_shoves_player_and_takes_one_bullet():
    # 리뷰 반영: 총알을 쥐고 쫓아가 가까이에서 쏘기만 하면 위험이 없었다. 빈손 줍줍이는 밀쳐서 1발을 빼앗는다.
    import config
    from picker import Picker
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker, p.x + 30, p.y)
    pk.state = 'FLEE'
    x0 = p.x
    sim.step(1)
    assert len(p.held) == config.AMMO - 1, '밀쳤는데 총알을 떨어뜨리지 않음'
    sim.step(5)
    assert p.x < x0 - 15, '밀쳐졌는데 밀려나지 않음 (%.1f px)' % (x0 - p.x)
    run_until(lambda: len(pk.held) == 1, 60)
    assert len(p.held) == config.AMMO - 1, '밀려난 플레이어가 떨어진 총알을 바로 다시 주움'
    assert pm.ledger.problem is None
    pm.finish()


@test
def shoving_picker_runs_off_with_the_bullet_before_firing():
    # 사용자 플레이 테스트: '바로 옆에 있는데 안 뺏는다'. 실제로는 밀쳐서 빼앗았지만, 0.35초 뒤 코앞에서
    # 쏴서 맞힌 총알이 내 발밑에 떨어져 0.7초 만에 되돌아왔다. 이제 빼앗은 총알을 들고 물러난 뒤 쏜다.
    import config, math
    from picker import Picker
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker, p.x + 32, p.y)
    pk.state = 'FLEE'
    sim.step(1)
    assert len(p.held) == config.AMMO - 1, '밀치지 않음'
    run_until(lambda: pk.held, 60)
    gap_at_shot = None
    for i in range(int(config.PICKER_CORNERED * 60) + 60):
        before = len(pk.held)
        sim.step(1)
        if before and not pk.held:
            gap_at_shot = pk.distance_to(p)
            break
        if i < 60:
            assert len(p.held) == config.AMMO - 1, '빼앗긴 총알이 1초 안에 되돌아옴'
    assert gap_at_shot is not None, '빼앗은 총알을 끝내 쏘지 않음'
    assert gap_at_shot > 120, '빼앗고 코앞(%.0fpx)에서 쏨' % gap_at_shot
    pm.finish()


def lunge_setup(pm, gap=60):
    # 빈손 줍줍이 오른쪽 gap px 옆에 총알 6발을 든 플레이어 (장애물 없는 곳)
    from picker import Picker
    p = pm.player
    p.x, p.y = 640, 360
    pk = pm.add_enemy(Picker, p.x + p.radius + 13 + gap, p.y)
    pk.state = 'FLEE'
    return pk


@test
def empty_picker_winds_up_then_pounces_and_steals():
    # 사용자 플레이 테스트: 바로 옆(몸 사이 약 55px)에 있어도 빼앗지 않았다. 닿아야만 빼앗고 스스로 오지 않아서.
    import config
    pm = fresh()
    p = pm.player
    pk = lunge_setup(pm, 60)
    sim.step(1)
    assert pk.state == 'LUNGE', '80px 안인데 덤벼들지 않음 (%s)' % pk.state
    x0 = pk.x
    sim.step(int(config.LUNGE_WINDUP * 60) - 2)
    assert abs(pk.x - x0) < 1, '준비 동작(웅크림) 중에 움직임'
    run_until(lambda: len(p.held) < config.AMMO, 40)
    assert pk.state == 'SEEK', '밀친 뒤 SEEK 로 돌아가지 않음'
    pm.finish()


@test
def stepping_aside_during_windup_dodges_the_pounce():
    import config
    pm = fresh()
    p = pm.player
    pk = lunge_setup(pm, 60)
    run_until(lambda: pk.lunge_dir is not None, 30)   # 방향이 고정된 직후 (1/60 을 더해 가므로 프레임 수로 세지 않는다)
    p.y += 90                                        # 옆으로 피한다
    sim.step(int(config.LUNGE_DASH * 60) + 5)
    assert len(p.held) == config.AMMO, '피했는데 빼앗김'
    assert pk.state in ('SEEK', 'FLEE') and pk.shove_cooldown > 0, '빗나간 뒤 쉬지 않음'
    sim.step(30)
    assert pk.state != 'LUNGE', '빗나가고 0.5초 만에 또 덤빔'
    pm.finish()


@test
def kicking_during_windup_stops_the_pounce():
    import config
    pm = fresh()
    p = pm.player
    pk = lunge_setup(pm, 40)
    sim.step(5)
    assert pk.state == 'LUNGE'
    aim(p, 0)
    p.kick()
    assert pk.state == 'STUN'
    sim.step(int(config.ENEMY_STUN_TIME * 60) - 5)
    assert len(p.held) == config.AMMO, '차서 막았는데 빼앗김'
    pm.finish()


@test
def empty_picker_does_not_pounce_on_empty_handed_player():
    pm = fresh()
    p = pm.player
    pk = lunge_setup(pm, 40)
    for b in p.held:
        b.state = 'FLOOR'
    p.held_backup, p.held = p.held, []
    pk.state, pk.SPEED = 'FLEE', 0
    sim.step(1)
    assert pk.state != 'LUNGE', '빼앗을 총알이 없는데 덤빔'
    p.held = p.held_backup
    for b in p.held:
        b.state = 'HELD'
    pm.finish()


@test
def shove_needs_empty_picker_loaded_player_and_cooldown():
    import config
    from picker import Picker
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker, p.x + 30, p.y)
    pk.state, pk.SPEED = 'FLEE', 0
    p.held_backup, p.held = p.held, []
    sim.step(2)
    assert p.push == (0.0, 0.0), '빈손 플레이어를 밀침'
    p.held = p.held_backup
    pk.shove_cooldown = 0
    assert pk.try_shove() is True
    p.x, p.y = pk.x - 30, pk.y
    assert pk.try_shove() is False, '쿨타임 중에 또 밀침'
    loaded = still_picker(pm, 200, 600)
    loaded.held = [p.held.pop()]
    p.x, p.y = loaded.x + 28, loaded.y
    assert loaded.try_shove() is False, '총알을 가진 줍줍이가 밀침'
    pm.finish()


@test
def picker_telegraphs_and_locks_aim_before_firing():
    # 총알 속도를 하나로 통일한 대신, 줍줍이는 쏘기 0.3초 전에 멈춰 서서 총구가 반짝이고 조준을 고정한다.
    # 예고를 보고 옆으로 움직이면 피할 수 있어야 한다.
    import config, math
    pm = fresh()
    p = pm.player
    p.x, p.y = 300, 360
    pk = still_picker(pm, 700, 360)
    pk.SPEED = config.PICKER_SPEED
    pk.held = [p.held.pop()]
    pk.state, pk.timer = 'SHOOT', 0.6
    run_until(lambda: pk.aiming(), 60)
    x0, y0 = pk.x, pk.y
    p.y += 90                                      # 예고를 보고 옆으로 피한다
    run_until(lambda: not pk.held, 60)
    assert (pk.x, pk.y) == (x0, y0), '조준 예고 중에 움직임'
    [b] = [o for o in bullets_in_world() if o.state == 'FLYING']
    angle = math.atan2(b.vy, b.vx)
    assert abs(angle - math.pi) < 0.05, '고정한 방향이 아니라 피한 자리를 겨눔'
    run_until(lambda: b.state != 'FLYING', 120)
    assert p.hp == config.PLAYER_HP, '예고를 보고 피했는데 맞음'
    pm.finish()


def blocked_by_obstacle(zone, a, b):
    # a 와 b 사이 선분이 장애물을 지나는지 (20등분 점으로 본다)
    for ol, ob, o_r, ot in zone.obstacles:
        for k in range(1, 20):
            x, y = a.x + (b.x - a.x) * k / 20, a.y + (b.y - a.y) * k / 20
            if ol < x < o_r and ob < y < ot:
                return True
    return False


@test
def empty_picker_hides_behind_cover_instead_of_rubbing_the_wall():
    # 사용자 플레이 테스트: 빈손 줍줍이가 플레이어 반대쪽으로만 가서 맵 끝 벽에 붙어 비볐다
    # (측정: 서 있는 플레이어 기준 시간의 51% 를 벽 근처에서 보냄). 이제 장애물 뒤에 숨는다.
    import math
    from picker import Picker
    pm = fresh()
    p = pm.player
    p.x, p.y = 200, 360
    pk = pm.add_enemy(Picker, 700, 620)
    pk.state = 'FLEE'
    p.held = []                                    # 밀치기 없이 숨기만 본다
    l, b, r, t = pm.zone.inner
    near_wall = 0
    for i in range(240):
        sim.step(1)
        near_wall += min(pk.x - l, r - pk.x, pk.y - b, t - pk.y) < pk.radius + 12
    assert near_wall < 24, '4초 중 %d 프레임을 벽에 붙어 있음' % near_wall
    assert blocked_by_obstacle(pm.zone, p, pk), '4초 뒤에도 장애물 뒤에 숨지 않음 (%.0f, %.0f)' % (pk.x, pk.y)
    x0, y0 = pk.x, pk.y
    sim.step(30)
    assert math.hypot(pk.x - x0, pk.y - y0) < 3, '숨은 뒤에도 계속 움직임'
    pm.finish()


@test
def hiding_picker_moves_around_cover_as_player_moves():
    from picker import Picker
    pm = fresh()
    p = pm.player
    p.x, p.y = 200, 360
    pk = pm.add_enemy(Picker, 700, 620)
    pk.state = 'FLEE'
    p.held = []
    sim.step(240)
    cover = pk.cover
    l, b, r, t = cover
    p.x, p.y = (l + r) / 2, t + 160                 # 숨은 장애물 반대편(위쪽)으로 플레이어가 돈다
    sim.step(180)
    assert blocked_by_obstacle(pm.zone, p, pk), '플레이어가 돌아갔는데 다시 숨지 않음'
    pm.finish()


@test
def hiding_picker_keeps_distance_from_cover_while_circling():
    # 사용자 플레이 테스트: 숨을 때 장애물에 몸을 붙이고, 돌아갈 때 가장자리에 비볐다
    # (측정: 플레이어가 테이블을 한 바퀴 도는 동안 17% 프레임을 장애물에 닿아 있음).
    # 숨을 자리는 36px 떨어지고, 돌아갈 때는 모서리를 거친다.
    import config, math
    from picker import Picker
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker, 700, 620)
    pk.state = 'FLEE'
    l, b, r, t = config.SALOON_TABLES[0]
    cx, cy = (l + r) / 2, (b + t) / 2

    def gap(rect):
        ol, ob, o_r, ot = rect
        return math.hypot(max(ol - pk.x, 0, pk.x - o_r), max(ob - pk.y, 0, pk.y - ot)) - pk.radius

    touch = hidden = 0
    N = 900
    for i in range(N):
        a = math.pi + 2 * math.pi * i / N           # 테이블에서 220px 떨어져 15초에 한 바퀴
        p.x, p.y = pm.zone.push_out(cx + math.cos(a) * 220, cy + math.sin(a) * 220, p.radius)
        sim.step(1)
        touch += min(gap(o) for o in pm.zone.obstacles) < 4
        hidden += blocked_by_obstacle(pm.zone, p, pk)
    assert touch < N * 0.03, '장애물에 %d%% 프레임 닿음' % (touch * 100 // N)
    assert hidden > N * 0.9, '장애물 뒤에 있던 시간이 %d%%' % (hidden * 100 // N)
    pm.finish()


@test
def hiding_picker_does_not_shake_and_peeks_when_player_is_still():
    # 사용자 플레이 테스트: 숨을 자리를 매 프레임 플레이어 위치로 다시 계산해서, 플레이어가 움직이면
    # 섰다 걸었다를 초당 21~42번 반복하며 떨었고('지진'), 플레이어가 서 있으면 완전히 굳어 있었다.
    # 이제 0.8~1.4초마다만 다시 고르고(보이면 0.25초 뒤 바로), 다시 고를 때 옆으로 살짝 옮겨 엿본다.
    import config, math
    from picker import Picker
    l, b, r, t = config.SALOON_TABLES[0]
    cx, cy = (l + r) / 2, (b + t) / 2
    for case in ('still', 'sway', 'circle'):
        pm = fresh()
        p = pm.player
        p.x, p.y = 200, 360
        pk = pm.add_enemy(Picker, 700, 620)
        pk.state = 'FLEE'
        sim.step(240)
        N = 600
        toggles = moving = hidden = 0
        was = None
        for i in range(N):
            if case == 'sway':
                p.x, p.y = 200, 360 + math.sin(i / 60 * 2.0) * 120
            elif case == 'circle':
                a = math.pi + 2 * math.pi * i / 900
                p.x, p.y = pm.zone.push_out(cx + math.cos(a) * 220, cy + math.sin(a) * 220, p.radius)
            x0, y0 = pk.x, pk.y
            sim.step(1)
            now = (pk.x, pk.y) != (x0, y0)
            toggles += was is not None and now != was
            was = now
            moving += now
            hidden += blocked_by_obstacle(pm.zone, p, pk)
        rate = toggles / (N / 60)
        assert rate < 4, '%s: 섰다 걸었다 초당 %.1f번 (떨림)' % (case, rate)
        assert hidden > N * 0.9, '%s: 장애물 뒤에 있던 시간 %d%%' % (case, hidden * 100 // N)
        if case == 'still':
            assert moving > 0, '플레이어가 서 있을 때 10초 동안 한 번도 움직이지 않음 (굳어 있음)'
        pm.finish()


@test
def two_empty_pickers_hide_behind_different_cover():
    # 사용자 플레이 테스트: 빈손 줍줍이 둘이 같은 테이블 뒤로 몰렸다 (술집에서 시간의 75%)
    from picker import Picker
    for px, py in ((200, 360), (640, 120), (1100, 360), (640, 620)):
        pm = fresh()
        p = pm.player
        p.x, p.y = px, py
        a = pm.add_enemy(Picker, 1100, 620)
        b = pm.add_enemy(Picker, 1100, 100)
        a.state = b.state = 'FLEE'
        sim.step(180)
        same = 0
        for _ in range(300):
            sim.step(1)
            same += a.cover is not None and a.cover == b.cover
        assert same < 30, '플레이어 %s: 둘이 같은 엄폐물에 %d%% 몰림' % ((px, py), same * 100 // 300)
        pm.finish()


@test
def picker_without_any_cover_just_runs_away():
    from picker import Picker
    pm = fresh()
    pm.zone.obstacles = []
    p = pm.player
    pk = pm.add_enemy(Picker, p.x + 150, p.y + 40)
    pk.state = 'FLEE'
    p.held = []
    d0 = pk.distance_to(p)
    sim.step(30)
    assert pk.distance_to(p) > d0 + 30, '숨을 곳이 없을 때 멀어지지 않음'
    pm.finish()


@test
def picker_flees_when_there_is_nothing_to_pick():
    from picker import Picker
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker, p.x + 150, p.y + 40)
    d0 = pk.distance_to(p)
    sim.step(30)
    assert pk.state == 'FLEE' and pk.distance_to(p) > d0 + 30, '총알이 없는데 도망가지 않음'
    floor_bullet(pm, 200, 200)
    sim.step(2)
    assert pk.state in ('SEEK', 'PICK'), '바닥 총알이 생겼는데 주우러 가지 않음'
    pm.finish()


@test
def shooting_a_picker_kills_it_drops_its_bullets_and_pays_bounty():
    import config
    from picker import Picker
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker, p.x + 250, p.y)
    pk.held = [p.held.pop(), p.held.pop()]   # 줍줍이가 두 발을 가진 상태
    pk.state = 'FLEE'                        # 움직임 대신 맞는 것만 본다
    pk.SPEED = 0
    aim(p, 0)
    p.fire()
    run_until(lambda: not pk.alive, 60)
    assert p.bounty == 50, '현상금 %d' % p.bounty
    sim.step(1)
    floor = [b for b in bullets_in_world() if b.state == 'FLOOR']
    assert len(floor) == 3, '바닥 총알 %d발 (맞힌 1발 + 떨어뜨린 2발)' % len(floor)
    assert pm.ledger.problem is None and sum(pm.ledger.counts.values()) == config.AMMO
    pm.finish()


@test
def enemy_bullet_hurts_player_but_passes_other_enemies_until_it_bounces():
    import config, math
    from picker import Picker
    pm = fresh()
    p = pm.player
    shooter = pm.add_enemy(Picker, p.x + 300, p.y)
    middle = pm.add_enemy(Picker, p.x + 150, p.y)
    for e in (shooter, middle):
        e.state, e.SPEED = 'FLEE', 0
    shooter.held = [p.held.pop()]
    shooter.shoot()
    run_until(lambda: p.hp < config.PLAYER_HP, 60)
    assert middle.alive and middle.hp == 1, '튕기지 않은 적 총알에 다른 적이 맞음'
    pm.finish()
    pm = fresh()
    p = pm.player
    p.x, p.y = 200, 600
    l, b, r, t = pm.zone.inner
    e = pm.add_enemy(Picker, r - 120, 360)
    e.state, e.SPEED = 'FLEE', 0
    bl = p.held.pop()
    bl.fire(e.x, e.y, 0.0, e)      # 벽 쪽으로 쏘게 한다
    bl.add_to_world()
    run_until(lambda: not e.alive, 60)
    assert bl.bounces == 1, '자기 총알에 튕기기 전에 맞음'
    pm.finish()


@test
def drunk_charges_body_hits_once_and_bounces_off():
    import config
    from drunk import Drunk
    pm = fresh()
    p = pm.player
    d = pm.add_enemy(Drunk, p.x + 250, p.y)
    run_until(lambda: p.hp < config.PLAYER_HP, 180)
    assert d.state == 'STUN', '부딪힌 뒤 튕겨 나가지 않음'
    gap = d.distance_to(p)
    sim.step(10)
    assert d.distance_to(p) > gap + 20, '부딪힌 뒤 떨어지지 않음'
    assert p.hp == config.PLAYER_HP - 1, '한 번 부딪혔는데 체력이 %d 줄어듦' % (config.PLAYER_HP - p.hp)
    pm.finish()


@test
def drunk_takes_two_bullets():
    from drunk import Drunk
    pm = fresh()
    p = pm.player
    d = pm.add_enemy(Drunk, p.x + 300, p.y)
    d.SPEED = 0
    aim(p, 0)
    p.fire()
    run_until(lambda: d.hp == 1, 60)
    assert d.alive
    sim.step(12)
    p.fire()
    run_until(lambda: not d.alive, 60)
    assert p.bounty == 30
    pm.finish()


def pass_setup(pm, picker_at=(1050, 200), bullet_at=(760, 200), drunk_at=(700, 200)):
    # 술꾼 옆에 바닥 총알, 멀리 빈손 줍줍이(움직이지 않음), 플레이어는 구석
    from drunk import Drunk
    p = pm.player
    p.x, p.y = 100, 650
    mate = still_picker(pm, *picker_at)
    ball = floor_bullet(pm, *bullet_at)
    d = pm.add_enemy(Drunk, *drunk_at)
    d.pass_cooldown = 0
    return d, ball, mate


@test
def drunk_kicks_a_nearby_bullet_to_an_empty_picker():
    # 사용자 제안: 총알을 쓰지 않는 술꾼도 쟁탈전에 끼도록, 바닥 총알을 빈손 줍줍이에게 차서 넘긴다
    import config, math
    pm = fresh()
    d, ball, mate = pass_setup(pm)
    sim.step(1)
    assert d.state == 'PASS', '패스할 상황인데 돌진만 함 (%s)' % d.state
    run_until(lambda: ball.state == 'ROLLING', 120)
    angle = math.atan2(ball.vy, ball.vx)
    to_mate = math.atan2(mate.y - ball.y, mate.x - ball.x)
    assert abs(angle - to_mate) < 0.05, '줍줍이 쪽으로 차지 않음'
    assert abs(math.hypot(ball.vx, ball.vy) - config.DRUNK_PASS_SPEED) < 15
    d0 = math.hypot(mate.x - ball.x, mate.y - ball.y)
    assert d.state == 'CHARGE', '찬 뒤 다시 돌진하지 않음'
    run_until(lambda: ball.state != 'ROLLING', 120)
    d1 = math.hypot(mate.x - ball.x, mate.y - ball.y)
    assert d1 < 80, '총알이 줍줍이 근처까지 가지 않음 (%.0f -> %.0f px)' % (d0, d1)
    assert pm.ledger.problem is None
    pm.finish()


@test
def drunk_does_not_pass_without_empty_picker_and_waits_cooldown():
    import config
    pm = fresh()
    d, ball, mate = pass_setup(pm)
    mate.held = [pm.player.held.pop()]       # 줍줍이가 총알을 가졌으면 패스하지 않는다
    sim.step(5)
    assert d.state == 'CHARGE' and ball.state == 'FLOOR', '총알 가진 줍줍이에게 패스함'
    pm.finish()
    pm = fresh()
    d, ball, mate = pass_setup(pm)
    run_until(lambda: ball.state == 'ROLLING', 120)
    second = floor_bullet(pm, d.x + 40, d.y + 40)
    sim.step(int(config.DRUNK_PASS_COOLDOWN * 60) - 20)
    assert second.state == 'FLOOR', '쿨타임 3초 안에 또 패스함'
    pm.finish()


@test
def drunk_gives_up_the_pass_when_the_bullet_is_taken():
    pm = fresh()
    d, ball, mate = pass_setup(pm, bullet_at=(900, 200), drunk_at=(780, 200))
    sim.step(1)
    assert d.state == 'PASS'
    pm.player.x, pm.player.y = ball.x, ball.y   # 플레이어가 먼저 줍는다
    sim.step(2)
    assert ball in pm.player.held and d.state == 'CHARGE', '총알이 사라졌는데 패스를 포기하지 않음 (%s)' % d.state
    pm.finish()


@test
def fast_bullet_does_not_pass_through_people_at_slowest_frame_rate():
    # 사용자 플레이 테스트에서 찾은 문제: 맞히기 판정을 프레임 끝 위치로만 해서, 느린 프레임(0.05초,
    # 한 프레임 40px)에는 정면으로 쏜 총알 60발 중 15발이 반지름 13px 적을 건너뛰었다.
    import config, game_framework
    for start in range(0, 40, 2):
        for off in (0, 6, 12):
            pm = fresh()
            p = pm.player
            p.x, p.y = 300 + start, 360
            e = still_picker(pm, 700, 360 + off)
            aim(p, 0)
            p.fire()
            for _ in range(40):
                sim.step(1, dt=game_framework.MAX_FRAME_TIME)
                if not e.alive:
                    break
            assert not e.alive, '느린 프레임에 총알이 적을 지나침 (출발 +%d, 비켜 %d)' % (start, off)
            pm.finish()
    for start in range(0, 40, 4):          # 적 총알이 플레이어를 건너뛰지 않는지도
        pm = fresh()
        p = pm.player
        e = still_picker(pm, 900, 360)
        e.held = [p.held.pop()]
        p.x = 400 + start
        e.shoot()
        for _ in range(40):
            sim.step(1, dt=game_framework.MAX_FRAME_TIME)
            if p.hp < config.PLAYER_HP:
                break
        assert p.hp == config.PLAYER_HP - 1, '느린 프레임에 적 총알이 플레이어를 지나침 (+%d)' % start
        pm.finish()


@test
def shot_drunk_staggers_and_does_not_pass_the_bullet_that_hit_it():
    # 사용자 플레이 테스트: '술꾼을 쐈는데 안 맞고 바로 찬다'. 실제로는 맞았는데(체력 2 -> 1),
    # 발밑에 떨어진 그 총알을 다음 프레임에 줍줍이에게 차 넘겨서 안 맞은 것처럼 보였다.
    import config
    from drunk import Drunk
    pm = fresh()
    p = pm.player
    still_picker(pm, 1100, 600)                    # 패스 받을 빈손 줍줍이
    d = pm.add_enemy(Drunk, p.x + 250, p.y)
    d.pass_cooldown = 0
    aim(p, 0)
    p.fire()
    run_until(lambda: d.hp == 1, 60)
    hit_bullet = [b for b in bullets_in_world() if b.state == 'FLOOR'][0]
    assert d.state == 'STUN' and d.flash > 0, '맞았는데 휘청이거나 번쩍이지 않음 (%s)' % d.state
    assert d.pass_cooldown > config.DRUNK_PASS_COOLDOWN - 0.1, '맞았는데 패스 쿨타임이 다시 시작되지 않음'
    for _ in range(60):
        sim.step(1)
        assert hit_bullet.state != 'ROLLING', '자기를 맞힌 총알을 1초 안에 차 넘김'
    pm.finish()


@test
def hound_swallows_bullets_and_kick_makes_it_spit_all():
    from dog import Dog
    pm = fresh()
    p = pm.player
    p.x, p.y = 150, 600
    b1, b2 = floor_bullet(pm, 700, 200), floor_bullet(pm, 820, 220)
    dog = pm.add_enemy(Dog, 1000, 200)
    run_until(lambda: len(dog.held) == 2, 300)   # 들개 최대(DOG_MAX_SWALLOW)도 2발
    sim.step(1)                    # 삼킨 그 프레임은 SEEK, 주울 게 없음을 다음 프레임에 알고 ROAM
    assert b1.state == b2.state == 'HELD' and dog.state == 'ROAM', '두 발을 삼킨 뒤 어슬렁거리지 않음 (%s)' % dog.state
    assert pm.ledger.counts['foes'] == 2
    dog.SPEED = 0
    dog.state = 'ROAM'
    p.x, p.y = dog.x - 40, dog.y
    import config
    config_speed = config.DOG_ROAM_SPEED
    config.DOG_ROAM_SPEED = 0
    try:
        aim(p, 0)
        p.kick()
        assert dog.held == [] and dog.state == 'STUN', '차도 삼킨 총알을 토하지 않음'
        assert pm.ledger.check()
    finally:
        config.DOG_ROAM_SPEED = config_speed
    pm.finish()


@test
def hound_swallows_at_most_two_and_then_roams_slowly():
    # 리뷰 반영: 무작위 전투에서 들개가 광산 총알 5발을 모두 삼켜 판이 막혔다. 2발이면 배가 찬다.
    import config
    from dog import Dog
    pm = fresh()
    p = pm.player
    p.x, p.y = 150, 600
    bullets = [floor_bullet(pm, 700 + i * 60, 200) for i in range(3)]
    dog = pm.add_enemy(Dog, 1000, 200)
    run_until(lambda: len(dog.held) == config.DOG_MAX_SWALLOW, 400)
    sim.step(120)
    assert len(dog.held) == config.DOG_MAX_SWALLOW, '배가 찼는데 더 삼킴 (%d발)' % len(dog.held)
    assert dog.state == 'ROAM' and sum(b.state == 'FLOOR' for b in bullets) == 1
    pm.finish()


@test
def hound_bumping_player_while_picking_does_not_crash():
    # 실제로 찾은 버그(무작위 전투 검사): 들개가 줍는 중(PICK)에 플레이어와 부딪히면
    # PICK -> STUN 전이가 없어 MachineError 로 게임이 멈췄다.
    import config
    from dog import Dog
    pm = fresh()
    p = pm.player
    b = floor_bullet(pm, p.x + 30, p.y)
    b.pin()                        # 플레이어가 먼저 줍지 않게 (들개가 밟은 상태로)
    dog = pm.add_enemy(Dog, p.x + 20, p.y)   # 몸이 겹친 상태 (부딪힘)
    dog.target, dog.timer, dog.state = b, config.ENEMY_PICK_TIME, 'PICK'
    sim.step(2)
    assert dog.state == 'STUN' and p.hp == config.PLAYER_HP - 1
    assert b.state == 'FLOOR', '부딪혀 끊긴 줍기의 총알이 바닥으로 돌아가지 않음'
    pm.finish()


# ---------------------------------------------------------------- 10. 2주차: 발차기

def still_picker(pm, x, y):
    from picker import Picker
    e = pm.add_enemy(Picker, x, y)
    e.state, e.SPEED = 'FLEE', 0           # 스스로 움직이지 않게 (발차기 효과만 본다)
    return e


@test
def kick_pushes_and_stuns_enemy_in_front_without_damage():
    import config
    from pico2d import SDLK_SPACE
    pm = fresh()
    p = pm.player
    e = still_picker(pm, p.x + 45, p.y)
    aim(p, 0)
    sim.key_down(SDLK_SPACE)
    assert p.state == 'KICK' and e.state == 'STUN', '앞의 적이 기절하지 않음 (%s)' % e.state
    assert e.hp == 1 and e.alive, '발차기에 데미지가 있음'
    x0 = e.x
    sim.step(10)
    assert e.x > x0 + 30, '밀려나지 않음 (%.1f px)' % (e.x - x0)
    assert p.state == 'IDLE', '0.15초 뒤 발차기 상태가 끝나지 않음'
    sim.step(int(config.ENEMY_STUN_TIME * 60))
    assert e.state != 'STUN', '0.7초 뒤 깨어나지 않음'
    pm.finish()


@test
def kick_misses_enemy_behind_and_has_cooldown():
    import config
    from pico2d import SDLK_SPACE
    pm = fresh()
    p = pm.player
    behind = still_picker(pm, p.x - 45, p.y)
    aim(p, 0)
    assert p.kick() is True
    assert behind.state != 'STUN', '등 뒤의 적이 차임'
    sim.step(12)
    front = still_picker(pm, p.x + 45, p.y)
    assert p.kick() is False and front.state != 'STUN', '쿨타임 중에 또 참'
    sim.step(int(config.KICK_COOLDOWN * 60))
    assert p.kick() is True and front.state == 'STUN'
    pm.finish()


@test
def kick_knocks_one_bullet_loose_and_breaks_a_pickup():
    import config
    pm = fresh()
    p = pm.player
    e = still_picker(pm, p.x + 45, p.y)
    e.held = [p.held.pop(), p.held.pop()]
    aim(p, 0)
    p.kick()
    assert len(e.held) == 2 - config.KICK_DROPS, '떨어뜨린 총알 수가 다름'
    assert pm.ledger.check()
    pm.finish()
    pm = fresh()
    p = pm.player
    b = floor_bullet(pm, p.x + 120, p.y)
    e = still_picker(pm, p.x + 140, p.y)
    e.start_pick(b)
    e.state = 'PICK'
    p.x = e.x - 45
    aim(p, 0)
    p.kick()
    assert b.state == 'FLOOR' and e.target is None and e.state == 'STUN', '줍기가 끊기지 않음'
    sim.step(int(config.ENEMY_PICK_TIME * 60) + 5)
    assert b not in e.held, '끊긴 뒤에도 주움'
    pm.finish()


@test
def kick_rolls_floor_bullet_in_aim_direction():
    import math
    pm = fresh()
    p = pm.player
    b = floor_bullet(pm, p.x + 30, p.y + 30)   # 45도 방향, 줍는 거리 밖
    aim(p, 90)                                   # 위를 보고 찬다 (총알은 부채꼴 안)
    p.kick()
    assert b.state == 'ROLLING', '바닥 총알이 굴러가지 않음'
    assert abs(math.atan2(b.vy, b.vx) - math.pi / 2) < 0.01, '조준 방향으로 굴러가지 않음'
    pm.finish()


@test
def kicking_right_after_a_pickup_ring_does_not_crash():
    # 실제로 찾은 버그: 줍기·피격 고리(Ring)는 radius() 메서드를 가져서, 발차기 판정이 이것을
    # 찰 대상으로 보고 '정수 + 메서드' 로 계산하다 게임이 멈췄다.
    pm = fresh()
    p = pm.player
    b = floor_bullet(pm, p.x + 10, p.y)
    sim.step(1)                    # 주우면서 고리 연출이 생긴다
    from effect import Ring
    assert effects(Ring), '고리 연출이 없음 (검사 전제)'
    aim(p, 0)
    assert p.kick() is True
    pm.finish()


@test
def can_move_while_kicking_and_returns_to_run():
    import config
    from pico2d import SDLK_d
    pm = fresh()
    p = pm.player
    sim.key_down(SDLK_d)
    p.kick()
    x0 = p.x
    sim.step(5)
    assert p.state == 'KICK' and p.x > x0, '발차기 중에 움직이지 않음'
    sim.step(10)
    assert p.state == 'RUN', '키를 누른 채 발차기가 끝나면 RUN 이어야 함 (%s)' % p.state
    pm.finish()


# ---------------------------------------------------------------- 11. 2주차: 체력 0 과 게임 오버

@test
def hp_zero_shows_game_over_and_r_restarts():
    import config, game_framework, gameover_mode
    from pico2d import SDL_KEYDOWN, SDLK_r
    pm = fresh()
    p = pm.player
    p.hp = 1
    p.bounty = 120
    flying_bullet(pm, p.x - 60, p.y, config.BULLET_SPEED, 0, bounces=1)
    sim.step(10)
    assert p.hp == 0 and game_framework.stack[-1] is gameover_mode, '체력 0 인데 게임 오버가 아님'
    assert p.pressed == set(), '게임 오버로 넘어갈 때 누르던 키를 놓지 않음'
    gameover_mode.dispatch(sim.FakeEvent(SDL_KEYDOWN, SDLK_r))
    assert game_framework.stack == [pm], '다시 하기 뒤 모드 스택 %s' % game_framework.stack
    assert pm.player is not p and pm.player.hp == config.PLAYER_HP and pm.player.bounty == 0
    assert len(pm.player.held) == pm.zone.ammo and pm.zone.number == 1
    pm.finish()


# ---------------------------------------------------------------- 12. 2주차: 구역 클리어, 문, 광산

@test
def door_opens_only_when_every_enemy_is_down_and_leads_to_the_mine():
    import config
    from pico2d import SDLK_d
    from picker import Picker
    pm = fresh()
    p = pm.player
    a, b = still_picker(pm, 900, 600), still_picker(pm, 900, 150)
    a.die()
    sim.step(1)
    assert not pm.zone.door_open, '적이 남았는데 문이 열림'
    b.die()
    sim.step(1)
    assert pm.zone.door_open, '적을 모두 쓰러뜨렸는데 문이 닫혀 있음'
    p.hp = 3
    p.y = config.HEIGHT // 2
    sim.key_down(SDLK_d)
    run_until(lambda: pm.zone.number == 2, 400)
    q = pm.player
    assert pm.zone.name == 'MINE' and pm.zone.dark and pm.zone.ammo == config.AMMO
    assert q.hp == 3 and q.bounty == 100, '체력·현상금이 이어지지 않음 (%d, %d)' % (q.hp, q.bounty)
    assert len(q.held) == config.AMMO and pm.ledger.expected == config.AMMO
    assert q.x < 200, '광산은 왼쪽에서 시작해야 함'
    pm.finish()


@test
def every_zone_has_exactly_six_bullets():
    # 제목이 Last 6 Bullet 이다. 어느 구역이든 총알은 여섯 발 (사용자 결정으로 광산 5발을 없앰)
    from zone import ZONES
    for i, data in enumerate(ZONES):
        assert data['ammo'] == 6, '%s 구역 총알이 %d발' % (data['name'], data['ammo'])
        pm = fresh()
        pm.start_zone(i)
        assert len(pm.player.held) == 6 and pm.ledger.expected == 6
        pm.finish()


@test
def f2_skips_to_the_next_zone_keeping_hp_and_bounty():
    from pico2d import SDLK_F2
    pm = fresh()
    pm.player.hp, pm.player.bounty = 2, 80
    sim.key_down(SDLK_F2)
    assert pm.zone.number == 2 and pm.player.hp == 2 and pm.player.bounty == 80
    pm.finish()


@test
def closed_door_is_just_a_wall():
    from pico2d import SDLK_d
    import config
    pm = fresh()
    p = pm.player
    still_picker(pm, 300, 600)
    p.y = config.HEIGHT // 2
    sim.key_down(SDLK_d)
    sim.step(300)
    assert pm.zone.number == 1, '문이 닫혔는데 다음 구역으로 감'
    pm.finish()


@test
def mine_shows_floor_bullets_only_in_lantern_light_and_glints_outside():
    import config, game_world
    pm = fresh()
    pm.start_zone(1)
    p = pm.player
    near = floor_bullet(pm, p.x + 60, p.y + 40)
    far = floor_bullet(pm, 900, 600)
    assert pm.zone.shows_floor_bullet(near) and not pm.zone.shows_floor_bullet(far)
    seen = 0
    for _ in range(int(config.GLINT_PERIOD * 60) + 2):
        sim.step(1)
        seen += pm.zone.glints(far)
    assert 0 < seen <= int(config.GLINT_TIME * 60) + 2, '빛 밖 총알이 한 주기에 %d 프레임 반짝임' % seen
    p.x, p.y = 860, 560                # 다가가면 보인다
    assert pm.zone.shows_floor_bullet(far)
    pm.finish()


@test
def leaving_the_last_zone_shows_to_be_continued():
    import game_framework, gameover_mode
    pm = fresh()
    pm.start_zone(1)
    still_picker(pm, 900, 600).die()
    sim.step(1)
    p = pm.player
    l, b, r, t = pm.zone.inner
    p.x, p.y = r - p.radius, 360
    sim.step(1)
    assert game_framework.stack[-1] is gameover_mode and gameover_mode.title == 'TO BE CONTINUED'
    game_framework.stack = [pm]
    pm.finish()


# ---------------------------------------------------------------- 13. 2주차: 적과 함께 무작위 플레이

@test
def random_battle_for_50_seconds_keeps_ammo_in_both_zones():
    # 적 3~4명과 함께 무작위로 움직이고, 쏘고, 차는 3000프레임(50초)을 구역마다 돌린다.
    # 매 프레임: 장부(손 + 적 + 바닥 + 공중 = 구역 총알 수), 모두 벽 안·장애물 밖, 게임이 멈추지 않음.
    # 적이 다 쓰러지면 다시 세운다. 체력 0 처리는 따로 검사하므로 여기서는 유지한다.
    import random, config, game_world
    from pico2d import SDLK_a, SDLK_d, SDLK_s, SDLK_w
    from bullet import Bullet
    from enemy import Enemy
    from zone import ZONES
    for index in (0, 1):
        pm = fresh(enemies=True)
        if index:
            pm.start_zone(1)
        p = pm.player
        rng = random.Random(100 + index)
        keys = [SDLK_w, SDLK_a, SDLK_s, SDLK_d]
        l, b, r, t = pm.zone.inner
        kills = kicks = enemy_shots = 0

        def walk_toward(tx, ty):
            want = set()
            if tx > p.x + 4: want.add(SDLK_d)
            if tx < p.x - 4: want.add(SDLK_a)
            if ty > p.y + 4: want.add(SDLK_w)
            if ty < p.y - 4: want.add(SDLK_s)
            for k in keys:
                (sim.key_down if k in want else sim.key_up)(k)

        def act(i):
            nonlocal kicks
            hoarder = [e for e in pm.enemies if e.alive and e.held]
            if not p.held and hoarder and (i // 120) % 2 == 0:
                # 실제 공략처럼: 빈 총이면 총알을 가진 적(들개 등)을 쫓아가 찬다
                e = min(hoarder, key=lambda e: e.distance_to(p))
                walk_toward(e.x, e.y)
                sim.mouse_move(e.x, e.y)
                if e.distance_to(p) < p.radius + e.radius + config.KICK_RANGE and p.kick():
                    kicks += 1
                p.hp = config.PLAYER_HP
                p.invincible = 0.0
                pm.zone.door_open = False
                return
            if i % 20 == 0:
                for k in keys:
                    (sim.key_down if rng.random() < 0.4 else sim.key_up)(k)
            if i % 7 == 0:
                alive = [e for e in pm.enemies if e.alive]
                if alive and rng.random() < 0.5:   # 절반은 실제 적을 겨눈다 (아무 데나 쏘면 거의 안 맞음)
                    e = rng.choice(alive)
                    sim.mouse_move(e.x, e.y)
                else:
                    sim.mouse_move(rng.uniform(l, r), rng.uniform(b, t))
            if rng.random() < 0.06:
                sim.click()
            if rng.random() < 0.03 and p.kick():
                kicks += 1
            p.hp = config.PLAYER_HP
            p.invincible = 0.0
            pm.zone.door_open = False          # 문으로 나가지 않게 (구역 전환은 따로 검사)

        for i in range(3000):
            before = sum(1 for e in pm.enemies if e.alive)
            sim.step(1, before=lambda _, i=i: act(i))
            kills += before - sum(1 for e in pm.enemies if e.alive)
            enemy_shots += sum(1 for o in game_world.objects()
                               if isinstance(o, Bullet) and o.state == 'FLYING' and o.owner != 'player' and o.age == 1 / 60)
            assert pm.ledger.problem is None, '%s %d 프레임: %s' % (pm.zone.name, i, pm.ledger.problem)
            for o in game_world.objects():
                if isinstance(o, (Bullet, Enemy)) or o is p:
                    assert l <= o.x <= r and b <= o.y <= t, '%s 가 벽 밖 (%d 프레임)' % (type(o).__name__, i)
                    for ol, ob, o_r, ot in pm.zone.obstacles:
                        assert not (ol < o.x < o_r and ob < o.y < ot), '%s 가 장애물 안 (%d 프레임)' % (type(o).__name__, i)
            if not any(e.alive for e in pm.enemies):
                for kind, ex, ey in ZONES[index]['enemies']:
                    pm.add_enemy(pm.ENEMY_KINDS[kind], ex, ey)
        assert kills > 0 and kicks > 0, '검사가 의미 없음 (쓰러뜨림 %d, 발차기 %d)' % (kills, kicks)
        print('       (%s: 쓰러뜨림 %d, 발차기 %d, 적 발사 %d)' % (pm.zone.name, kills, kicks, enemy_shots))
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
