from pico2d import *

import config
import game_framework
import game_world
from ammo_ledger import AmmoLedger
from bullet import Bullet
from crosshair import Crosshair
from hud import Hud
from boss import Boss
from dog import Dog
from drunk import Drunk
from picker import Picker
from player import Player
from train_zone import TrainZone
from zone import ZONES, Zone

ENEMY_KINDS = {'picker': Picker, 'drunk': Drunk, 'dog': Dog, 'boss': Boss}
SPAWN_ENEMIES = True               # 구역 배치(적, 바닥 총알, 결투). 자동 점검에서 플레이어·총알만 볼 때 끈다

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
    if data.get('kind') == 'train':
        zone = TrainZone(data['obstacles'], data['number'], data['name'], data['ammo'])
        zone.on_fall = fell_off_train
    else:
        zone = Zone(data['obstacles'], data['number'], data['name'], data['ammo'], data['dark'], data.get('style'))
    game_world.add_object(zone, 0)
    x, y = data['start']
    player = Player(zone, x, y)
    zone.light = player            # 광산에서는 플레이어가 랜턴을 든다
    if keep is not None:
        player.hp, player.bounty = keep.hp, keep.bounty
        player.mouse = keep.mouse
    game_world.add_object(player, 1)
    # 구역의 총알은 여기서만 만든다. 이후에는 상태만 바뀌므로 총알 수가 늘거나 줄지 않는다.
    # 구역 데이터의 floor 자리에 놓을 만큼은 바닥에, 나머지는 플레이어 손에 쥐고 시작한다.
    bullets = [Bullet(zone) for _ in range(zone.ammo)]
    spots = data.get('floor', []) if SPAWN_ENEMIES else []
    in_hand = len(bullets) - len(spots)
    player.held = bullets[:in_hand]
    game_world.add_collision_pair('player:bullet', player, None)
    for b, (fx, fy) in zip(bullets[in_hand:], spots):
        b.drop(fx, fy)
        b.add_to_world()
    enemies = []
    if SPAWN_ENEMIES:
        for kind, ex, ey in data['enemies']:
            add_enemy(ENEMY_KINDS[kind], ex, ey)
    game_world.add_object(Hud(player, zone), 2)
    ledger = AmmoLedger([player] + enemies, zone.ammo)
    game_world.add_object(ledger, 2)
    game_world.add_object(Crosshair(player), 2)     # UI 중 가장 위에 그린다
    hide_cursor()
    if data.get('duel') and SPAWN_ENEMIES:
        import duel_mode           # duel_mode 도 play_mode 를 불러서, 서로 맨 위에서 부르지 않는다
        game_framework.push_mode(duel_mode)          # 은행: 보스전 전에 정오의 결투 (PRD 9장)


def fell_off_train(o):
    # 기차 뒤 끝으로 밀려 떨어짐 (PRD 7장)
    import effect
    if o is player:
        player.hp -= 1             # 무적 시간과 상관없이 체력 -1, 가진 총알은 그대로
        player.invincible = config.INVINCIBLE_TIME
        player.push = (0.0, 0.0)
        effect.spawn(effect.TextPop(player.x + 40, player.y, 'FELL!', config.COLOR_HP, 0.8))
        player.x, player.y = zone.push_out(config.WIDTH // 2, config.HEIGHT // 2, player.radius)
        effect.spawn(effect.hit_ring(player.x, player.y))
    else:
        # 적은 퇴장하며 가진 총알을 짐받이 턱 앞에 흘린다. 차서 떨어뜨린 것도 쓰러뜨린 것으로 친다
        o.cancel_pick()
        for i, b in enumerate(list(o.held)):
            o.held.remove(b)
            x, y = zone.lip_drop_point(o.y + (i - len(o.held) / 2) * 14)
            b.drop(x, y)
            b.add_to_world()
        effect.spawn(effect.TextPop(o.x + 40, o.y, 'FELL!', config.COLOR_BOUNTY, 0.8))
        o.die()


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
    elif event.type == SDL_KEYDOWN and event.key == SDLK_F2:
        next_zone()                # 디버그: 적을 다 쓰러뜨리지 않고 다음 구역으로 (확인·발표 촬영용)
    else:
        player.handle_event(event)


def update():
    game_world.update()
    game_world.handle_collisions()
    ledger.check()                 # 충돌 처리(줍기 등)까지 끝난 뒤 총알 수를 검사한다
    if enemies and not zone.door_open and all(not e.alive for e in enemies):
        if ZONES[zone_index].get('final'):
            show_result('TOWN SAVED')   # 은행의 두목을 쓰러뜨리면 클리어 (PRD 10장, 엔딩 연출은 4주차)
            return
        zone.door_open = True      # 구역의 적을 모두 쓰러뜨리면 오른쪽 문이 열린다 (PRD 4장)
    if zone.at_door(player.x, player.y, player.radius):
        next_zone()
    elif player.hp <= 0:
        show_result('GAME OVER')


def next_zone():
    if zone_index + 1 < len(ZONES):
        start_zone(zone_index + 1, keep=player)   # 체력과 현상금은 이어진다 (PRD 10장: 구역 사이 회복 없음)
    else:
        show_result('TO BE CONTINUED')            # 마지막 구역(은행)은 문 대신 두목을 쓰러뜨리면 클리어


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
