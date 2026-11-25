# 18. 4주차: 화면 전환 (타이틀, 수배 포스터, 엔딩). 규칙이 아니라 모드 스택이 맞게 쌓이고 풀리는지만 본다.
import sim                       # 먼저 불러야 게임 폴더가 import 경로에 들어간다

import config
import duel_mode
import ending_mode
import game_framework
import gameover_mode
import play_mode
import poster_mode
import title_mode
from pico2d import SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDLK_RETURN, SDLK_t
from zone import ZONES
from checks.common import fresh, test, still_picker


def start_from_title():
    # main.py 와 같게: 타이틀 모드 하나만 쌓고 시작한다 (포스터와 적 배치를 켠다)
    game_framework.running = True
    game_framework.stack = [title_mode]
    play_mode.SPAWN_ENEMIES = True
    play_mode.SHOW_POSTERS = True
    title_mode.init()


def click(mode):
    mode.dispatch(sim.FakeEvent(SDL_MOUSEBUTTONDOWN, button=1))


def finish_flow():
    # 쌓인 모드를 모두 닫고 다음 테스트를 위해 포스터를 다시 끈다
    while game_framework.stack:
        game_framework.stack.pop().finish()
    play_mode.SHOW_POSTERS = False


@test
def title_click_starts_zone_1_with_a_poster():
    start_from_title()
    click(title_mode)
    assert game_framework.stack == [play_mode, poster_mode], '타이틀 뒤 스택 %s' % game_framework.stack
    assert play_mode.zone.number == 1
    assert poster_mode.kinds == ['picker', 'drunk'], poster_mode.kinds
    click(poster_mode)
    assert game_framework.stack == [play_mode], '포스터 클릭 뒤 스택 %s' % game_framework.stack
    finish_flow()


@test
def title_enter_also_starts():
    start_from_title()
    title_mode.dispatch(sim.FakeEvent(SDL_KEYDOWN, SDLK_RETURN))
    assert game_framework.stack[0] is play_mode
    finish_flow()


@test
def poster_closes_by_itself_after_1_5_seconds():
    start_from_title()
    click(title_mode)
    sim.step(int(poster_mode.SHOW_TIME * 60) - 5)
    assert game_framework.stack[-1] is poster_mode, '1.5초 전에 닫힘'
    sim.step(10)
    assert game_framework.stack == [play_mode]
    finish_flow()


@test
def poster_only_shows_enemies_new_to_the_zone():
    assert poster_mode.new_kinds(0) == ['picker', 'drunk']
    assert poster_mode.new_kinds(1) == ['dog']
    assert poster_mode.new_kinds(2) == []
    assert poster_mode.new_kinds(3) == ['boss']
    assert not poster_mode.prepare(2), '새 적이 없는 기차에서 포스터를 띄움'
    assert poster_mode.WANTED['picker'][1] == 50 and poster_mode.WANTED['boss'][1] == 500


@test
def bank_poster_sits_above_the_duel():
    pm = fresh()
    play_mode.SPAWN_ENEMIES = True
    play_mode.SHOW_POSTERS = True
    pm.start_zone(len(ZONES) - 1)
    assert game_framework.stack == [pm, duel_mode, poster_mode], game_framework.stack
    click(poster_mode)
    assert game_framework.stack[-1] is duel_mode, '포스터를 닫으면 결투가 나와야 함'
    finish_flow()


@test
def ending_returns_to_title_and_ignores_the_first_click():
    pm = fresh()
    pm.start_zone(len(ZONES) - 1)
    pm.player.bounty = 640
    still_picker(pm, 900, 600).die()
    sim.step(1)
    assert game_framework.stack[-1] is ending_mode and ending_mode.bounty == pm.player.bounty >= 640
    sim.step(10)
    click(ending_mode)
    assert game_framework.stack[-1] is ending_mode, '엔딩이 1초 안에 클릭으로 넘어감'
    sim.step(60)
    click(ending_mode)
    assert game_framework.stack == [title_mode], '엔딩 뒤 스택 %s' % game_framework.stack
    finish_flow()


@test
def game_over_t_goes_to_title_and_r_still_restarts_zone_1():
    pm = fresh()
    pm.player.hp = 0
    pm.start_zone(1, keep=pm.player)
    pm.player.hp = 0
    sim.step(1)
    assert game_framework.stack[-1] is gameover_mode
    gameover_mode.dispatch(sim.FakeEvent(SDL_KEYDOWN, SDLK_t))
    assert game_framework.stack == [title_mode]
    finish_flow()
    pm = fresh()
    pm.start_zone(2)
    pm.player.hp = 0
    sim.step(1)
    gameover_mode.dispatch(sim.FakeEvent(SDL_KEYDOWN, SDLK_RETURN))
    assert game_framework.stack == [pm] and pm.zone.number == 1
    finish_flow()
