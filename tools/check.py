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
    game_world.add_object(b, 1)
    game_world.add_collision_pair('player:bullet', None, b)
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
    assert pm.ledger.counts == {'hand': 4, 'floor': 0, 'air': 2}, pm.ledger.counts
    p.x -= 200                     # 돌아오는 총알에 맞지 않게 비켜선다
    sim.step(120)
    assert pm.ledger.counts == {'hand': 4, 'floor': 2, 'air': 0}, pm.ledger.counts
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
