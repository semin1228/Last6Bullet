from pico2d import *

import config
import game_framework
import game_world
from ammo_ledger import AmmoLedger
from bullet import Bullet
from crosshair import Crosshair
from hud import Hud
from dog import Dog
from drunk import Drunk
from picker import Picker
from player import Player
from zone import ZONES, Zone

ENEMY_KINDS = {'picker': Picker, 'drunk': Drunk, 'dog': Dog}
SPAWN_ENEMIES = True               # 자동 점검에서 플레이어·총알만 볼 때 끈다

zone = None
player = None
ledger = None
enemies = []
zone_index = 0


def init():
    start_zone(0)


def restart():
    # 게임 오버 뒤 다시 하기: 체력과 현상금도 처음으로
    start_zone(0)


def start_zone(index, keep=None):
    # 구역 하나를 만든다. keep 은 다음 구역으로 넘어갈 때 이어받는 플레이어 (체력, 현상금)
    global zone, player, ledger, enemies, zone_index
    zone_index = index
    data = ZONES[index]
    game_world.clear()
    zone = Zone(data['obstacles'], data['number'], data['name'], data['ammo'], data['dark'])
    game_world.add_object(zone, 0)
    x, y = data['start']
    player = Player(zone, x, y)
    zone.light = player            # 광산에서는 플레이어가 랜턴을 든다
    if keep is not None:
        player.hp, player.bounty = keep.hp, keep.bounty
        player.mouse = keep.mouse
    game_world.add_object(player, 1)
    # 구역의 총알은 여기서만 만든다. 이후에는 상태만 바뀌므로 총알 수가 늘거나 줄지 않는다.
    player.held = [Bullet(zone) for _ in range(zone.ammo)]
    game_world.add_collision_pair('player:bullet', player, None)
    enemies = []
    if SPAWN_ENEMIES:
        for kind, ex, ey in data['enemies']:
            add_enemy(ENEMY_KINDS[kind], ex, ey)
    game_world.add_object(Hud(player, zone), 2)
    ledger = AmmoLedger([player] + enemies, zone.ammo)
    game_world.add_object(ledger, 2)
    game_world.add_object(Crosshair(player), 2)     # UI 중 가장 위에 그린다
    hide_cursor()


def add_enemy(cls, x, y):
    e = cls(zone, player, x, y)
    enemies.append(e)
    if ledger is not None:
        ledger.holders.append(e)
    game_world.add_object(e, 1)
    game_world.add_collision_pair('enemy:bullet', e, None)
    game_world.add_collision_pair('player:enemy', player, e)
    return e


def handle_events():
    for event in get_events():
        dispatch(event)


def dispatch(event):
    # 이벤트 하나를 처리한다. 자동 점검(tools/check.py)도 같은 경로로 입력을 넣는다.
    if event.type == SDL_QUIT:
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
        game_framework.quit()
    elif event.type == SDL_KEYDOWN and event.key == SDLK_F1:
        ledger.visible = not ledger.visible
    else:
        player.handle_event(event)


def update():
    game_world.update()
    game_world.handle_collisions()
    ledger.check()                 # 충돌 처리(줍기 등)까지 끝난 뒤 총알 수를 검사한다
    if enemies and not zone.door_open and all(not e.alive for e in enemies):
        zone.door_open = True      # 구역의 적을 모두 쓰러뜨리면 오른쪽 문이 열린다 (PRD 4장)
    if zone.at_door(player.x, player.y, player.radius):
        next_zone()
    elif player.hp <= 0:
        show_result('GAME OVER')


def next_zone():
    if zone_index + 1 < len(ZONES):
        start_zone(zone_index + 1, keep=player)   # 체력과 현상금은 이어진다 (PRD 10장: 구역 사이 회복 없음)
    else:
        show_result('TO BE CONTINUED')            # 기차와 은행은 3주차


def show_result(title):
    import gameover_mode           # gameover_mode 도 play_mode 를 불러서, 서로 맨 위에서 부르지 않는다
    gameover_mode.title = title
    game_framework.push_mode(gameover_mode)


def render():
    clear_canvas()
    game_world.render()
    update_canvas()


def finish():
    game_world.clear()
    show_cursor()


def pause():
    player.release_all_keys()


def resume():
    pass
