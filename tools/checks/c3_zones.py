# 자동 점검: 2주차 구역: 발차기, 게임 오버, 구역 클리어, 광산
import math
import random

import sim                       # 먼저 불러야 게임 폴더가 import 경로에 들어간다

import config
import game_framework
import game_world
import ending_mode
import gameover_mode
from bullet import Bullet
from effect import Ring
from enemy import Enemy
from pico2d import SDLK_F2, SDLK_SPACE, SDLK_a, SDLK_d, SDLK_r, SDLK_s, SDLK_w, SDL_KEYDOWN
from zone import ZONES
from checks.common import (aim, bullets_in_world, effects, floor_bullet, flying_bullet, fresh, near, run_until,
                           still_picker, test)


# ---------------------------------------------------------------- 10. 2주차: 발차기


@test
def kick_pushes_and_stuns_enemy_in_front_without_damage():
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
    assert effects(Ring), '고리 연출이 없음 (검사 전제)'
    aim(p, 0)
    assert p.kick() is True
    pm.finish()


@test
def can_move_while_kicking_and_returns_to_run():
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
def zone_starts_with_three_in_hand_and_three_on_the_floor():
    # 비판 점검 반영: 6발을 다 쥐고 시작하면 술집이 2.8초 만에 끝나고 적이 총알을 줍지 않았다.
    # 술집·광산·기차는 손 3 + 바닥 3 (floor 자리), 은행은 결투가 배분을 정하므로 손 6. 구역 총알은 늘 6발.
    for i, data in enumerate(ZONES):
        pm = fresh(enemies=True)
        pm.start_zone(i)
        floor = [b for b in bullets_in_world() if b.state == 'FLOOR']
        spots = data.get('floor', [])
        assert len(pm.player.held) + len(floor) == 6 and pm.ledger.expected == 6, data['name']
        assert len(floor) == len(spots), '%s 바닥 총알 %d발' % (data['name'], len(floor))
        assert sorted((round(b.x), round(b.y)) for b in floor) == sorted(spots), data['name']
        if not data.get('duel'):
            assert len(pm.player.held) == 3, data['name']
        game_framework.stack = [pm]
        pm.finish()


@test
def every_zone_has_exactly_six_bullets():
    # 제목이 Last 6 Bullet 이다. 어느 구역이든 총알은 여섯 발 (사용자 결정으로 광산 5발을 없앰)
    for i, data in enumerate(ZONES):
        assert data['ammo'] == 6, '%s 구역 총알이 %d발' % (data['name'], data['ammo'])
        pm = fresh()
        pm.start_zone(i)
        assert len(pm.player.held) == 6 and pm.ledger.expected == 6
        pm.finish()


@test
def f2_skips_to_the_next_zone_keeping_hp_and_bounty():
    pm = fresh()
    pm.player.hp, pm.player.bounty = 2, 80
    sim.key_down(SDLK_F2)
    assert pm.zone.number == 2 and pm.player.hp == 2 and pm.player.bounty == 80
    pm.finish()


@test
def closed_door_is_just_a_wall():
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
    pm = fresh()
    pm.start_zone(1)
    p = pm.player
    near = floor_bullet(pm, p.x + 60, p.y + 40)
    far = floor_bullet(pm, 900, 600)
    assert pm.zone.shows_floor_bullet(near) and not pm.zone.shows_floor_bullet(far)
    # 한 주기보다 조금 길게 지켜보면서, 반짝임이 한 번 이상 있고 한 번의 반짝임이 GLINT_TIME 쯤인지 본다.
    # (처음엔 반짝인 프레임 수의 합으로 봤는데, 지켜보는 구간이 주기보다 길어 처음과 끝에서 두 번 걸리면
    #  합이 넘쳐 드물게 실패했다. 총알 주기의 위상이 id() 에 따라 달라서 실행마다 달랐다.)
    runs, run = [], 0
    for _ in range(int(config.GLINT_PERIOD * 60) + 2):
        sim.step(1)
        if pm.zone.glints(far):
            run += 1
        elif run:
            runs.append(run)
            run = 0
    if run:
        runs.append(run)
    assert runs, '빛 밖 총알이 한 주기 동안 한 번도 반짝이지 않음'
    assert max(runs) <= int(config.GLINT_TIME * 60) + 2, '한 번에 %d 프레임 반짝임' % max(runs)
    p.x, p.y = 860, 560                # 다가가면 보인다
    assert pm.zone.shows_floor_bullet(far)
    pm.finish()


@test
def beating_every_enemy_in_the_bank_shows_town_saved():
    # 마지막 구역(은행)은 문이 열리는 대신, 두목(과 남은 적)을 모두 쓰러뜨리면 클리어 화면 (PRD 10장)
    pm = fresh()
    pm.start_zone(len(ZONES) - 1)
    assert ZONES[pm.zone_index].get('final') and pm.zone.name == 'BANK'
    still_picker(pm, 900, 600).die()
    sim.step(1)
    assert game_framework.stack[-1] is ending_mode
    assert not pm.zone.door_open
    game_framework.stack = [pm]
    pm.finish()


@test
def random_battle_for_50_seconds_keeps_ammo_in_both_zones():
    # 적 3~4명과 함께 무작위로 움직이고, 쏘고, 차는 3000프레임(50초)을 구역마다 돌린다.
    # 매 프레임: 장부(손 + 적 + 바닥 + 공중 = 구역 총알 수), 모두 벽 안·장애물 밖, 게임이 멈추지 않음.
    # 적이 다 쓰러지면 다시 세운다. 체력 0 처리는 따로 검사하므로 여기서는 유지한다.
    for index in range(len(ZONES)):
        pm = fresh(enemies=True)
        if index:
            pm.start_zone(index)
        game_framework.stack = [pm]                 # 은행: 결투는 따로 검사하므로 건너뛰고 바로 보스전
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

        hits = 0
        for i in range(3000):
            before = sum(1 for e in pm.enemies if e.alive)
            hp_before = sum(max(e.hp, 0) for e in pm.enemies)
            sim.step(1, before=lambda _, i=i: act(i))
            kills += before - sum(1 for e in pm.enemies if e.alive)
            hits += max(0, hp_before - sum(max(e.hp, 0) for e in pm.enemies))
            enemy_shots += sum(1 for o in game_world.objects()
                               if isinstance(o, Bullet) and o.state == 'FLYING' and o.owner != 'player' and o.age == 1 / 60)
            assert pm.ledger.problem is None, '%s %d 프레임: %s' % (pm.zone.name, i, pm.ledger.problem)
            for o in game_world.objects():
                if isinstance(o, (Bullet, Enemy)) or o is p:
                    assert l <= o.x <= r and b <= o.y <= t, '%s 가 벽 밖 (%d 프레임)' % (type(o).__name__, i)
                    for ol, ob, o_r, ot in pm.zone.obstacles:
                        assert not (ol < o.x < o_r and ob < o.y < ot), '%s 가 장애물 안 (%d 프레임)' % (type(o).__name__, i)
            if game_framework.stack[-1] is not pm:  # 은행 클리어 화면이 올라오면 내리고 계속 싸운다
                game_framework.stack = [pm]
            if not any(e.alive for e in pm.enemies):
                for kind, ex, ey in ZONES[index]['enemies']:
                    pm.add_enemy(pm.ENEMY_KINDS[kind], ex, ey)
        # 두목(체력 8)은 50초 무작위 전투로는 잘 안 쓰러지므로, 적을 한 번이라도 맞혔는지로 본다
        assert hits > 0 and kicks > 0, '검사가 의미 없음 (맞힘 %d, 발차기 %d)' % (hits, kicks)
        print('       (%s: 맞힘 %d, 쓰러뜨림 %d, 발차기 %d, 적 발사 %d)' % (pm.zone.name, hits, kills, kicks, enemy_shots))
        pm.finish()
