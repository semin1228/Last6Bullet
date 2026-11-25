# 자동 점검: 2주차 적: 총알 새 상태, 적 공통, 줍줍이, 술꾼, 들개
import math
import random as rnd

import sim                       # 먼저 불러야 게임 폴더가 import 경로에 들어간다

import config
import game_framework
from dog import Dog
from drunk import Drunk
from picker import Picker
from pico2d import SDLK_a
from checks.common import (Picker_cls, aim, blocked_by_obstacle, bullets_in_world, floor_bullet, fresh, lunge_setup,
                           math_atan, pass_setup, run_until, still_picker, test)


# ---------------------------------------------------------------- 8. 2주차: 총알 새 상태 (구름, 밟힘, 떨굼)


@test
def kicked_bullet_rolls_slows_and_stops():
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


@test
def rolling_and_pinned_bullets_hurt_nobody_and_player_cannot_take_pinned():
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


@test
def picker_walks_to_floor_bullet_picks_it_slowly_and_shoots_at_player():
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
    for seed in range(4):
        for l, b, r, t in config.SALOON_TABLES:
            for cls in (Picker, Dog):
                for below in (True, False):
                    pm = fresh()
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


@test
def empty_picker_winds_up_then_pounces_and_steals():
    # 사용자 플레이 테스트: 바로 옆(몸 사이 약 55px)에 있어도 빼앗지 않았다. 닿아야만 빼앗고 스스로 오지 않아서.
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
def shoved_player_cannot_fire_for_a_moment_but_can_move_and_kick():
    # 사용자 제안: 밀쳐진 직후 바로 쏘면 줍줍이가 줍는 0.25초 사이에 코앞에서 쏴서 빼앗기가 의미 없어진다.
    # 0.4초 동안 사격만 막는다. 이동과 발차기는 된다 (발차기로 줍기를 끊는 대응은 남긴다).
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker_cls(), p.x + 32, p.y)
    pk.state = 'FLEE'
    sim.step(1)
    assert len(p.held) == config.AMMO - 1 and p.dazed > 0, '밀쳐졌는데 경직이 없음'
    aim(p, 0)
    p.fire_cooldown = 0
    assert p.fire() is None and len(p.held) == config.AMMO - 1, '경직 중에 쏨'
    x0 = p.x
    sim.key_down(SDLK_a)
    sim.step(5)
    assert p.x < x0 - 5, '경직 중에 움직이지 못함'
    sim.key_up(SDLK_a)
    p.kick_cooldown = 0
    assert p.kick() is True, '경직 중에 발차기를 못함'
    sim.step(int(config.SHOVE_DAZE_TIME * 60))
    p.fire_cooldown = 0
    assert p.dazed == 0 and p.fire() is not None, '경직이 끝났는데 못 쏨'
    pm.finish()


@test
def kicked_picker_does_not_fire_the_moment_it_wakes_up():
    # 데모 녹화에서 찾은 버그: 총알을 가진 줍줍이를 차면, 깨어나는 순간 timer(기절 시간을 세던 값)가 0 이라
    # 조준 예고 없이 바로 쐈고, '가까우면 물러난다' 도 SHOOT 에 있던 시간이 쌓여 있어 건너뛰었다.
    pm = fresh()
    p = pm.player
    pk = pm.add_enemy(Picker, p.x + 60, p.y)
    pk.held = [p.held.pop(), p.held.pop()]
    pk.state, pk.timer, pk.shoot_wait = 'SHOOT', 5.0, 3.0
    aim(p, 0)
    p.kick()
    assert pk.state == 'STUN'
    run_until(lambda: pk.state != 'STUN', 60)
    held = len(pk.held)
    for _ in range(int((config.PICKER_FIRST_SHOT - 0.02) * 60)):
        sim.step(1)
        assert len(pk.held) == held, '깨어나자마자(조준 예고 없이) 쏨'
    pm.finish()


@test
def shove_needs_empty_picker_loaded_player_and_cooldown():
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


@test
def picker_does_not_shoot_through_obstacle_and_sidesteps_until_clear():
    # 적 시야: 줍줍이는 플레이어와의 직선 사이에 장애물이 있으면 쏘지 않고, 멈춰 있지 않고 옆으로 비켜 걷다가
    # 시야가 트이면 쏜다 (PRD 위험표: 모서리에 걸려 영영 못 쏘면 안 됨).
    pm = fresh()
    p = pm.player
    l, b, r, t = config.SALOON_TABLES[0]
    cy = (b + t) / 2
    p.x, p.y = l - 160, cy
    pk = pm.add_enemy(Picker, r + 160, cy)
    pk.held = [p.held.pop()]
    pk.state, pk.timer = 'SHOOT', 0.2                # 곧 쏠 차례인데 테이블이 가로막음
    assert blocked_by_obstacle(pm.zone, p, pk)
    x0, y0 = pk.x, pk.y
    fired_blocked = []
    for i in range(300):
        sim.step(1)
        if not pk.held:
            fired_blocked.append(blocked_by_obstacle(pm.zone, p, pk))
            break
        if i == 20:
            assert (pk.x, pk.y) != (x0, y0), '막힌 채 멈춰 서 있음'
    assert not pk.held, '5초가 지나도 못 쏨 (모서리에 걸림)'
    assert fired_blocked == [False], '장애물 너머로 쏨'
    pm.finish()


@test
def picker_cancels_locked_aim_when_player_hides_behind_cover():
    # 조준 예고 중에 플레이어가 장애물 뒤로 숨으면 쏘지 않고 예고를 취소한다 (그 뒤엔 다시 비켜 걷는다).
    pm = fresh()
    p = pm.player
    l, b, r, t = config.SALOON_TABLES[0]
    cy = (b + t) / 2
    p.x, p.y = l - 160, cy + 200
    pk = pm.add_enemy(Picker, r + 160, cy + 200)
    pk.SPEED = 0
    pk.held = [p.held.pop()]
    pk.state, pk.timer = 'SHOOT', 0.6
    run_until(lambda: pk.aiming() and pk.locked_aim is not None, 60)
    p.x, p.y = l - 160, cy
    pk.y = cy
    sim.step(1)
    assert pk.locked_aim is None, '시야가 막혔는데 조준 예고가 유지됨'
    sim.step(60)
    assert pk.held, '시야가 막혔는데 쏨'
    pm.finish()


@test
def empty_picker_hides_behind_cover_instead_of_rubbing_the_wall():
    # 사용자 플레이 테스트: 빈손 줍줍이가 플레이어 반대쪽으로만 가서 맵 끝 벽에 붙어 비볐다
    # (측정: 서 있는 플레이어 기준 시간의 51% 를 벽 근처에서 보냄). 이제 장애물 뒤에 숨는다.
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


@test
def drunk_kicks_a_nearby_bullet_to_an_empty_picker():
    # 사용자 제안: 총알을 쓰지 않는 술꾼도 쟁탈전에 끼도록, 바닥 총알을 빈손 줍줍이에게 차서 넘긴다
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
