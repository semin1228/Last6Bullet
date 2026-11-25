# 자동 점검: 3주차: 기차, 두목, 정오의 결투, 한 판 끝까지
import math
import random

import sim                       # 먼저 불러야 게임 폴더가 import 경로에 들어간다

import config
import duel_mode
import game_framework
import ending_mode
from picker import Picker
from pico2d import SDL_MOUSEBUTTONDOWN
from zone import ZONES
from checks.common import (aim, bank_with_boss, bullets_in_world, click_left, duel_setup, floor_bullet, fresh,
                           run_until, still_picker, test, train)


# ---------------------------------------------------------------- 15. 3주차: 달리는 기차


@test
def train_floor_slides_bullets_to_the_lip_and_people_backward():
    pm = fresh()
    z = train(pm)
    p = pm.player
    p.x, p.y = 900, 360
    b = floor_bullet(pm, 700, 300)
    strip = floor_bullet(pm, 120, 500)              # 위험 띠 위 총알은 평소에 안 밀린다
    x0, px0 = b.x, p.x
    sim.step(60)
    assert abs((x0 - b.x) - config.TRAIN_BULLET_SLIDE) < 2, '바닥 총알 1초 %.0fpx (기대 70)' % (x0 - b.x)
    assert abs((px0 - p.x) - config.TRAIN_PLAYER_SLIDE) < 2, '플레이어 1초 %.0fpx (기대 28)' % (px0 - p.x)
    assert strip.x == 120, '위험 띠 위 총알이 밀림'
    sim.step(60 * 10)
    assert abs(b.x - (config.LIP_X + b.radius)) < 0.5, '바닥 총알이 짐받이 턱에서 멈추지 않음 (x=%.1f)' % b.x
    p.x = 150                                       # 위험 띠 위 사람도 평소에는 안 밀린다
    sim.step(30)
    assert p.x == 150
    pm.finish()


@test
def enemies_slide_slower_and_pinned_bullets_stay_put():
    pm = fresh()
    train(pm)
    e = still_picker(pm, 900, 600)
    x0 = e.x
    sim.step(60)
    assert abs((x0 - e.x) - config.TRAIN_ENEMY_SLIDE) < 2, '적 1초 %.0fpx (기대 14)' % (x0 - e.x)
    b = floor_bullet(pm, 700, 300)
    b.pin()
    sim.step(30)
    assert b.x == 700, '적이 줍는 중인 총알이 미끄러짐 (PRD 15-6)'
    pm.finish()


@test
def jolt_warns_a_second_ahead_then_throws_everyone_back():
    pm = fresh()
    z = train(pm)
    p = pm.player
    p.x, p.y = 900, 360
    b = floor_bullet(pm, 800, 300)
    z.jolt_in = config.JOLT_WARN + 0.5
    sim.step(20)
    assert not z.warning()
    sim.step(20)
    assert z.warning(), '덜컹 1초 전인데 예고가 없음'
    run_until(lambda: z.jolting(), 80)
    px0, bx0 = p.x, b.x
    sim.step(int(config.JOLT_TIME * 60) + 1)
    pushed = px0 - p.x
    assert 80 < pushed < 110, '덜컹에 플레이어가 %.0fpx 밀림 (기대 약 90 + 미끄럼)' % pushed
    assert bx0 - b.x > 80, '덜컹에 바닥 총알이 밀리지 않음'
    assert not z.jolting() and not z.warning(), '덜컹이 끝나지 않음'
    pm.finish()


@test
def jolt_throws_player_off_the_back_hp_minus_one_back_in_the_middle():
    pm = fresh()
    z = train(pm)
    p = pm.player
    p.x, p.y = 90, 300                              # 위험 띠 뒤쪽 끝 가까이
    held = len(p.held)
    z.jolt_in = 0.01
    run_until(lambda: p.hp < config.PLAYER_HP, 40)
    assert abs(p.x - config.WIDTH // 2) < 2 and abs(p.y - config.HEIGHT // 2) < 2, '떨어진 뒤 열차 가운데로 오지 않음'
    assert len(p.held) == held and pm.ledger.problem is None, '떨어졌는데 총알 수가 바뀜'
    pm.finish()


@test
def kicking_an_enemy_off_the_back_drops_its_bullets_at_the_lip():
    pm = fresh()
    train(pm)
    p = pm.player
    e = still_picker(pm, 70, 300)                   # 뒤쪽 끝 바로 앞
    e.held = [p.held.pop(), p.held.pop(), p.held.pop()]
    p.x, p.y = 140, 300
    aim(p, 180)
    p.kick()                                        # 발차기로 1발은 그 자리에 떨어뜨리고 (PRD 6장)
    run_until(lambda: not e.alive, 30)              # 밀려나 뒤 끝에서 떨어진다
    assert p.bounty == e.BOUNTY, '차서 떨어뜨렸는데 현상금이 없음'
    sim.step(1)
    floor = [b for b in bullets_in_world() if b.state == 'FLOOR']
    at_lip = [b for b in floor if config.LIP_X < b.x < config.LIP_X + 30]   # 놓인 뒤 턱 쪽으로 미끄러진다
    assert len(floor) == 3 and len(at_lip) == 2,         '남은 2발이 턱 앞에 놓이지 않음 %s' % [(round(b.x), round(b.y)) for b in floor]
    assert pm.ledger.problem is None
    pm.finish()


@test
def bullets_never_leave_the_train():
    # 옆·뒤 가장자리는 총알에게 난간이다. 덜컹이 와도 총알은 열차 밖으로 나가지 않는다.
    pm = fresh()
    z = train(pm)
    p = pm.player
    l, b, r, t = z.inner
    rng = random.Random(3)
    for k in range(120):
        p.x, p.y = rng.uniform(250, 1200), rng.uniform(60, 660)
        sim.mouse_move(rng.uniform(l, r), rng.uniform(b, t))
        p.fire_cooldown = 0
        p.fire()
        if k % 30 == 0:
            z.jolt_in = 0.01
        sim.step(4)
        p.hp = 4
        for bl in bullets_in_world():
            assert l <= bl.x <= r and b <= bl.y <= t, '총알이 열차 밖으로 나감'
        assert pm.ledger.problem is None
    pm.finish()
# ---------------------------------------------------------------- 16. 3주차: 두목


@test
def boss_gathers_three_then_telegraphs_and_fires_a_fan():
    pm = fresh()
    boss = bank_with_boss(pm)                       # 구역을 바꾸면 플레이어도 새로 만들어지므로 그 뒤에 잡는다
    p = pm.player
    p.x, p.y = 260, 360
    bullets = [floor_bullet(pm, 980, 300), floor_bullet(pm, 1000, 420), floor_bullet(pm, 1100, 360)]
    run_until(lambda: boss.state == 'SPREAD', 600)
    assert len(boss.held) == config.BOSS_SPREAD_COUNT, '3발을 모으기 전에 흩뿌림 (%d발)' % len(boss.held)
    x0 = boss.x
    for _ in range(int(config.ENEMY_AIM_TIME * 60) - 1):
        sim.step(1)
        assert len(boss.held) == 3 and boss.x == x0, '조준 예고 중에 쏘거나 움직임'
    run_until(lambda: not boss.held, 5)
    flying = [b for b in bullets if b.state == 'FLYING' and b.owner is boss]
    assert len(flying) == 3, '모은 총알을 모두 쏘지 않음'
    angles = sorted(math.degrees(math.atan2(b.vy, b.vx)) % 360 for b in flying)
    assert abs((angles[-1] - angles[0]) - 2 * config.BOSS_SPREAD_STEP) < 2, '부채꼴 폭 %.0f도' % (angles[-1] - angles[0])
    assert abs(angles[1] - 180) < 15, '플레이어(왼쪽) 쪽으로 쏘지 않음 (가운데 %.0f도)' % angles[1]
    assert boss.state == 'GATHER'
    pm.finish()


@test
def boss_fallback_fires_what_it_has_or_charges():
    # 4초 동안 다 못 모으면: 가진 총알이 있으면 그것만이라도 흩뿌리고, 없으면 돌진 (교착 방지)
    pm = fresh()
    boss = bank_with_boss(pm)
    p = pm.player
    p.x, p.y = 300, 360
    boss.held = [p.held.pop()]                      # 1발만 있고 바닥 총알은 없다 (나머지는 플레이어 손)
    run_until(lambda: boss.state == 'SPREAD', int(config.BOSS_GATHER_LIMIT * 60) + 5)
    run_until(lambda: not boss.held, 30)
    pm.finish()
    pm = fresh()
    boss = bank_with_boss(pm, 900, 360)             # 총알 0발, 바닥 총알도 없음
    p = pm.player
    p.x, p.y = 600, 360
    run_until(lambda: boss.state == 'CHARGE', int(config.BOSS_GATHER_LIMIT * 60) + 5)
    run_until(lambda: p.hp < config.PLAYER_HP, 120)
    assert boss.state == 'STUN', '부딪힌 뒤 튕겨 나가지 않음'
    pm.finish()


@test
def kicking_the_boss_stuns_it_and_knocks_one_bullet_loose():
    pm = fresh()
    boss = bank_with_boss(pm, 240 + 55, 360)        # 은행 시작 위치 (240, 360) 바로 오른쪽
    p = pm.player
    boss.held = [p.held.pop(), p.held.pop()]
    aim(p, 0)
    p.kick()
    assert boss.state == 'STUN' and len(boss.held) == 1
    assert pm.ledger.check()
    pm.finish()


@test
def boss_phase_two_summons_two_minions_once_and_spreads_at_two():
    # 체력 절반(4) 이하: 부하 줍줍이 2명이 한 번만 나타나고, 2발만 모여도 흩뿌린다 (PRD 9장 2페이즈)
    pm = fresh()
    boss = bank_with_boss(pm)
    p = pm.player
    p.x, p.y = 260, 360
    sim.step(2)
    assert boss.phase == 1 and len(pm.enemies) == 1
    boss.hp = config.BOSS_PHASE2_HP
    sim.step(2)
    minions = [e for e in pm.enemies if isinstance(e, Picker)]
    assert boss.phase == 2 and len(minions) == 2, '2페이즈 부하 수 %d' % len(minions)
    assert all(m.x > 1000 for m in minions), '부하가 오른쪽 구석에서 나오지 않음'
    boss.hp -= 1
    sim.step(2)
    assert len([e for e in pm.enemies if isinstance(e, Picker)]) == 2, '부하를 또 불렀음'
    for m in minions:                                  # 두목만 보려고 부하는 쓰러뜨린다
        m.die(reward=False)
    floor_bullet(pm, boss.x + 40, boss.y + 30)
    floor_bullet(pm, boss.x + 40, boss.y - 30)
    p.held.clear()                                     # 플레이어가 끼어들지 않게 (장부 검사는 하지 않는다)
    run_until(lambda: boss.state == 'SPREAD', 600)
    assert len(boss.held) == config.BOSS_SPREAD_COUNT_2, '2페이즈인데 %d발에 흩뿌림' % len(boss.held)
    pm.finish()


@test
def spread_always_sends_one_bullet_straight_at_the_player():
    # 사용자 피드백: 좌우 50° 는 피하기 쉬웠다. 18° 간격이고, 2발이어도 한 발은 정조준 (가만히 서 있으면 맞는다)
    pm = fresh()
    boss = bank_with_boss(pm)
    for n in (1, 2, 3, 4):
        angles = boss.spread_angles(0.0, n)
        assert len(angles) == n and any(abs(a) < 1e-9 for a in angles), (n, angles)
        gaps = [math.degrees(b - a) for a, b in zip(angles, angles[1:])]
        assert all(abs(g - config.BOSS_SPREAD_STEP) < 1e-6 for g in gaps), (n, gaps)
    pm.finish()


@test
def minions_fall_with_the_boss_without_bounty():
    pm = fresh()
    boss = bank_with_boss(pm)
    boss.hp = config.BOSS_PHASE2_HP
    sim.step(2)
    assert len(boss.minions) == 2
    bounty = pm.player.bounty
    boss.die()
    assert not any(m.alive for m in boss.minions), '두목이 쓰러졌는데 부하가 남음'
    assert pm.player.bounty == bounty + boss.BOUNTY, '부하 현상금까지 붙음'
    sim.step(1)
    assert game_framework.stack[-1] is ending_mode
    assert pm.ledger.check()
    game_framework.stack = [pm]
    pm.finish()


@test
def boss_takes_a_hit_per_bullet_and_beating_it_saves_the_town():
    pm = fresh()
    boss = bank_with_boss(pm, 700, 360)
    p = pm.player
    p.x, p.y = 300, 360
    boss.SPEED = 0
    aim(p, 0)
    p.fire()
    run_until(lambda: boss.hp < config.BOSS_HP, 60)
    assert boss.hp == config.BOSS_HP - 1 and boss.alive
    boss.hp = 1
    sim.step(12)
    p.fire_cooldown = 0
    aim(p, 0)
    p.fire()
    run_until(lambda: not boss.alive, 60)
    assert p.bounty == 500
    sim.step(1)
    assert game_framework.stack[-1] is ending_mode
    game_framework.stack = [pm]
    pm.finish()
# ---------------------------------------------------------------- 17. 3주차: 정오의 결투


@test
def duel_ignores_clicks_in_intro_and_fouls_on_ready():
    pm, dm = duel_setup()
    p, boss = pm.player, dm.duel.boss
    assert (p.x, p.y) == config.DUEL_PLAYER_POS and (boss.x, boss.y) == config.DUEL_BOSS_POS
    click_left()
    assert dm.duel.state == 'INTRO', '시계탑 연출 중 클릭으로 결투가 끝남'
    run_until(lambda: dm.duel.state == 'READY', 120)
    click_left()
    assert dm.duel.state == 'LOSE' and dm.duel.reason == 'FOUL'
    run_until(lambda: game_framework.stack[-1] is pm, 120)
    assert p.hp == config.PLAYER_HP - 1 and len(p.held) == 3 and len(boss.held) == 3, '패배: 체력 -1, 총알 3:3 이 아님'
    assert boss.state == 'SPREAD', '패배했는데 두목이 바로 흩뿌리지 않음'
    assert pm.ledger.check()
    pm.finish()


@test
def drawing_first_wins_the_duel():
    pm, dm = duel_setup()
    p, boss = pm.player, dm.duel.boss
    run_until(lambda: dm.duel.state == 'GO', 400)
    sim.step(int(config.DUEL_BOSS_REACT[0] * 60) - 3)   # 두목보다 먼저
    click_left()
    assert dm.duel.state == 'WIN' and dm.duel.reason == 'YOU WIN'
    run_until(lambda: game_framework.stack[-1] is pm, 120)
    assert boss.hp == config.BOSS_HP - 1 and len(p.held) == 4 and p.hp == config.PLAYER_HP
    floor = sorted((round(b.x), round(b.y)) for b in bullets_in_world() if b.state == 'FLOOR')
    assert floor == sorted(config.DUEL_WIN_FLOOR), '승리: 바닥 2발이 가운데에 없음 %s' % floor
    assert pm.ledger.check()
    pm.finish()


@test
def waiting_after_draw_loses_too_slow():
    pm, dm = duel_setup()
    run_until(lambda: dm.duel.state == 'GO', 400)
    run_until(lambda: dm.duel.state == 'LOSE', int(config.DUEL_BOSS_REACT[1] * 60) + 3)
    assert dm.duel.reason == 'TOO SLOW'
    click_left()                                    # 늦게 눌러도 바뀌지 않는다
    assert dm.duel.state == 'LOSE'
    run_until(lambda: game_framework.stack[-1] is pm, 120)
    pm.finish()
# ---------------------------------------------------------------- 18. 3주차: 한 판 끝까지


@test
def a_full_run_goes_from_saloon_to_town_saved():
    # 3주차 최소 완성 기준 (PRD 17장): 술집 -> 광산 -> 기차 -> 결투 -> 두목까지 한 판이 끝까지 이어진다.
    # 각 구역의 적을 쓰러뜨리고 문으로 나가며, 체력·현상금이 이어지고 구역마다 총알 6발인지 본다.
    pm = fresh(enemies=True)
    names = []
    for index in range(len(ZONES) - 1):
        in_hand = 6 - len(ZONES[index].get('floor', []))     # 손 3 + 바닥 3 으로 시작 (은행은 결투가 정함)
        assert pm.zone_index == index and len(pm.player.held) == in_hand and pm.ledger.expected == 6
        names.append(pm.zone.name)
        pm.player.hp = config.PLAYER_HP - index % 2           # 체력이 이어지는지 보려고 바꿔 둔다
        for e in list(pm.enemies):
            if e.alive:
                e.die()
        sim.step(1)
        hp, bounty = pm.player.hp, pm.player.bounty           # 쓰러뜨린 현상금까지 받은 뒤의 값
        assert pm.zone.door_open, '%s: 적을 모두 쓰러뜨렸는데 문이 안 열림' % pm.zone.name
        l, b, r, t = pm.zone.inner
        pm.player.x, pm.player.y = r - pm.player.radius, config.HEIGHT // 2
        sim.step(1)
        assert pm.player.hp == hp and pm.player.bounty == bounty, '다음 구역으로 체력·현상금이 이어지지 않음'
    names.append(pm.zone.name)
    assert names == ['SALOON', 'MINE', 'TRAIN', 'BANK'], names
    assert game_framework.stack[-1] is duel_mode, '은행에 들어섰는데 결투가 없음'
    run_until(lambda: duel_mode.duel.state == 'GO', 400)
    duel_mode.dispatch(sim.FakeEvent(SDL_MOUSEBUTTONDOWN, button=1))
    run_until(lambda: game_framework.stack[-1] is pm, 120)
    boss = duel_mode.duel.boss
    assert boss.hp == config.BOSS_HP - 1
    boss.hp = 1
    p = pm.player
    p.x, p.y = boss.x - 120, boss.y              # 결투 뒤 두목이 바닥 총알을 주우러 움직이므로 가까이서 쏜다
    p.mouse = (boss.x, boss.y)
    p.fire_cooldown = 0
    p.fire()
    run_until(lambda: game_framework.stack[-1] is not pm, 120)
    assert game_framework.stack[-1] is ending_mode
    assert p.bounty >= 500
    game_framework.stack = [pm]
    pm.finish()
