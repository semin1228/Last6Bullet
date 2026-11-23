# 게임 전체 설정값. PRD 11장(난이도 설계)의 '보통' 기준 초기값이며 플레이 테스트로 조정한다.

TITLE = 'Last 6 Bullet'        # 창 제목
WIDTH, HEIGHT = 1280, 720
WALL = 32                      # 바깥 벽 두께 (px)

PLAYER_RADIUS = 14
PLAYER_SPEED = 200             # px/초
PLAYER_HP = 4
INVINCIBLE_TIME = 1.0          # 맞은 뒤 무적 시간 (초)
PICKUP_REACH = 2               # 몸과 총알이 이만큼 떨어져 있어도 줍는다 (px)

AMMO = 6                       # 구역 안에 존재하는 총알 수 (PRD 3장: 고정)
BULLET_RADIUS = 4
BULLET_SPEED = 800             # px/초 (체험판 520 은 쏜 뒤 기다리는 느낌이라 올림)
BULLET_LIFE = 1.1              # 이 시간이 지나면 바닥에 떨어진다 (초). 사거리(속도x수명) 약 880px 유지
FIRE_COOLDOWN = 0.18           # 연사 간격 (초)
MAX_BOUNCES = 2                # 이만큼 튕긴 뒤 다시 닿으면 바닥에 떨어진다
DRY_FLASH_TIME = 0.3           # 빈 총을 당겼을 때 HUD 실린더가 붉게 깜빡이는 시간 (초)
HIT_GRACE = 0.12              # 발사 직후 이 시간 동안은 사람에게 맞지 않는다 (초)
ROLL_SPEED = 420               # 발차기로 찬 바닥 총알의 처음 속도 (px/초)
ROLL_FRICTION = 520            # 구르는 총알이 1초에 잃는 속도 (px/초)
ROLL_STOP_SPEED = 20           # 이보다 느려지면 멈춘다 (px/초)
BULLET_SUBSTEP = 6             # 한 번에 움직이는 최대 거리 (px). 얇은 벽을 뚫고 지나가지 않게 한다

# 적 (PRD 8장, 11장 '보통' 기준)
HIT_NO_PICK_TIME = 1.0        # 맞은 사람은 자기를 맞힌 총알을 이 시간 동안 줍지 못한다 (초). 그 사이 근처 적이 먼저 주우러 온다
ENEMY_PICK_TIME = 0.25         # 적이 바닥 총알을 줍는 동작 시간 (초)
ENEMY_STUN_TIME = 0.7          # 발차기에 맞은 적의 기절 시간 (초)
# 총알 속도는 누가 쏘든 BULLET_SPEED 하나다 (같은 여섯 발을 돌려 쓰는 게임이라). 피할 틈은 조준 예고로 준다.
ENEMY_AIM_TIME = 0.3           # 적이 쏘기 직전 멈춰서 총구가 반짝이는 시간 (초). 이때 조준이 고정된다
ENEMY_AIM_LEAD = 0.5           # 플레이어 이동을 얼마나 예측해서 겨누는지 (0: 안 함, 1: 완전)
PICKER_SPEED = 120
PICKER_KEEP_NEAR = 180         # 줍줍이가 쏠 때 유지하는 거리 (이보다 가까우면 물러난다)
PICKER_KEEP_FAR = 340          # (이보다 멀면 다가간다)
PICKER_FIRST_SHOT = 0.35       # 줍고 나서 첫 발까지 (초)
PICKER_SHOOT_INTERVAL = 0.9    # 쏘는 간격 (초)
PICKER_CORNERED = 1.5          # 플레이어가 가까워 물러나느라 못 쏜 지 이만큼 지나면 그 거리에서라도 쏜다 (구석에 몰렸을 때, 초)
COVER_GAP = 36                 # 빈손 줍줍이가 숨을 때와 장애물을 돌아갈 때 장애물에서 떨어지는 거리 (px)
COVER_MIN_DIST = 150           # 숨을 자리가 플레이어와 이보다 가까우면 그 장애물은 쓰지 않는다 (px)
COVER_ARRIVE = 8               # 숨을 자리에 이만큼 가까우면 멈춰서 엿본다 (px)
COVER_REPLAN_TIME = (0.8, 1.4) # 숨을 자리를 다시 고르는 간격 (초, 이 사이 무작위)
COVER_REPLAN_URGENT = 0.25     # 지금 자리가 플레이어에게 보이면 이만큼 뒤에 바로 다시 고른다 (초)
COVER_REPLAN_MIN = 25          # 새 자리가 이보다 가까우면 옮기지 않는다 (잔걸음 방지, px)
COVER_PEEK = 25                # 다시 고를 때 자리를 옆으로 흔드는 최대 거리 (엿보기, px)
COVER_PEEK_MIN = 12            # 엿보기로 옮길 때 지금 자리와 최소한 이만큼은 다르게 (px)
COVER_SHARE_PENALTY = 600      # 다른 줍줍이가 쓰는 엄폐물은 이만큼 멀리 있는 것으로 친다 (px)
COVER_SWITCH_RATIO = 0.6       # 다른 엄폐물이 지금 것보다 이 비율 이하로 가까울 때만 옮긴다
SHOVE_REACH = 6                # 빈손 줍줍이가 플레이어를 밀칠 수 있는 거리 (몸이 닿은 뒤 여유, px)
SHOVE_COOLDOWN = 1.5           # 밀치기 간격 (초)
LUNGE_RANGE = 80               # 빈손 줍줍이가 덤벼드는 거리 (몸 사이, px)
LUNGE_WINDUP = 0.25            # 덤벼들기 전 웅크리는 시간 ('!', 초). 이 사이에 피하거나 차면 막는다
LUNGE_SPEED = 280              # 달려드는 속도 (px/초)
LUNGE_DASH = 0.4               # 달려드는 시간 (초). 약 110px
SHOVE_DAZE_TIME = 0.4          # 밀쳐진 뒤 쏘지 못하는 시간 (초). 줍줍이가 줍고(0.25초) 돌아설 때까지
SHOVE_PUSH_SPEED = 450         # 밀쳐진 플레이어가 밀려나는 처음 속도 (px/초)
DETOUR_DIST = 90               # 적이 장애물에 막혔을 때 옆으로 비켜 걷는 거리 (테이블 반 폭 + 몸)
DRUNK_SPEED = 150
DRUNK_SWAY_SPEED = 3.0         # 비틀거리는 빠르기 (라디안/초)
DRUNK_SWAY_ANGLE = 0.6         # 비틀거리며 벗어나는 각도 (라디안)
DRUNK_PASS_RANGE = 140         # 술꾼이 패스하러 가는 바닥 총알까지의 거리 (px)
DRUNK_PASS_SPEED = 600         # 술꾼이 찬 총알의 처음 속도 (px/초). 마찰 520 이면 약 350px 굴러간다
DRUNK_PASS_COOLDOWN = 3.0      # 패스 간격 (초). 너무 자주 패스하면 돌진 위협이 사라진다
DRUNK_HIT_STUN = 0.4           # 술꾼이 총알에 맞고 버틸 때 휘청이는 시간 (초)
DRUNK_PASS_GIVE_UP = 2.0       # 총알에 이만큼 안에 못 닿으면 포기하고 다시 돌진 (초)
DOG_SPEED = 230                # 들개는 플레이어(200)보다 빠르게 총알로 달려간다
DOG_ROAM_SPEED = 110
DOG_MAX_SWALLOW = 2            # 들개가 삼킬 수 있는 최대 총알 수 (리뷰 반영: 다 삼켜 판이 막히는 것 방지)
DOG_ROAM_TIME = 1.5            # 어슬렁거릴 때 새 목적지를 고르는 간격 (초)
BUMP_STUN_TIME = 0.5           # 몸으로 부딪힌 적이 튕겨 나가 멈추는 시간 (초)
KICK_COOLDOWN = 0.65           # 발차기 쿨타임 (초, PRD 6장)
KICK_TIME = 0.15               # 발차기 동작(KICK 상태) 시간 (초)
KICK_RANGE = 50                # 몸 가장자리에서 발차기가 닿는 거리 (px)
KICK_HALF_ANGLE = 60           # 조준 방향에서 좌우로 이만큼 (도)
KICK_DROPS = 1                 # 발차기에 맞은 적이 떨어뜨리는 총알 수
KICK_PUSH_SPEED = 380          # 발차기에 맞은 적이 밀려나는 처음 속도 (px/초)

# 술집 테이블 (left, bottom, right, top)
SALOON_TABLES = [
    (360, 470, 500, 540),
    (580, 180, 720, 250),
    (840, 440, 980, 510),
]

LIGHT_RADIUS = 110             # 광산 랜턴 빛 반경 (px, PRD 7장)
GLINT_PERIOD = 2.2             # 빛 밖 바닥 총알이 반짝이는 주기 (초)
GLINT_TIME = 0.12              # 한 번 반짝이는 시간 (초)
DOOR_HALF = 44                 # 오른쪽 벽 문 높이의 절반 (px)

# 광산 바위·버팀목 (left, bottom, right, top)
MINE_ROCKS = [
    (300, 430, 370, 600),
    (540, 110, 690, 190),
    (800, 400, 880, 560),
    (960, 200, 1040, 300),
]

# 기차 (PRD 7장). 기차는 오른쪽으로 달리고, 뒤(왼쪽)로 밀린다
LIP_X = 200                    # 짐받이 턱 x. 그 뒤(왼쪽)가 위험 띠
TRAIN_BULLET_SLIDE = 70        # 열차 바닥 위 바닥 총알이 뒤로 밀리는 속도 (px/초)
TRAIN_PLAYER_SLIDE = 28        # 플레이어
TRAIN_ENEMY_SLIDE = 14         # 적
JOLT_INTERVAL = (5.0, 7.0)     # 덜컹 간격 (초)
JOLT_WARN = 1.0                # 덜컹 예고 시간 (초)
JOLT_TIME = 0.25               # 덜컹이 미는 시간 (초)
JOLT_SPEED = 360               # 덜컹 동안 뒤로 미는 속도 (px/초). 0.25초면 약 90px
TRAIN_SCROLL = 600             # 바깥 침목이 흘러가는 속도 (그림만, px/초)
# 두목 (PRD 9장, 보통 난이도)
BOSS_HP = 8
BOSS_SPEED = 130
BOSS_GATHER_LIMIT = 4.0        # 이 시간 안에 다 못 모으면 대체 공격 (초)
BOSS_SPREAD_COUNT = 3          # 이만큼 모으면 흩뿌린다 (1페이즈)
BOSS_SPREAD_HALF = 50          # 흩뿌리기 부채꼴 좌우 각도 (도)
BOSS_CHARGE_SPEED = 240        # 대체 공격 돌진 속도 (px/초)
BOSS_CHARGE_TIME = 2.0         # 돌진 시간 (초)
BOSS_KEEP = 260                # 주울 총알이 없을 때 플레이어와 두는 거리 (px)
# 정오의 결투 (PRD 9장, 보통 난이도)
DUEL_INTRO = 1.4               # 'HIGH NOON' 연출 (초, 클릭 무시)
DUEL_READY = (1.0, 3.0)        # 'READY...' 가 떠 있는 시간 (무작위, 초)
DUEL_BOSS_REACT = (0.3, 0.45)  # 두목 반응 시간 (무작위, 초)
DUEL_RESULT = 1.2              # 결과를 보여 주는 시간 (초)
DUEL_LOSE_SPLIT = 3            # 지면 두목에게 넘어가는 총알 수
DUEL_PLAYER_POS = (440, 360)
DUEL_BOSS_POS = (840, 360)
BANK_PILLARS = [
    (380, 150, 440, 210),
    (380, 510, 440, 570),
    (840, 150, 900, 210),
    (840, 510, 900, 570),
]

TRAIN_CRATES = [
    (480, 140, 560, 220),
    (760, 470, 840, 560),
    (980, 170, 1060, 250),
]

# 글꼴 (Windows 기본 글꼴 맑은 고딕, 저장소에는 넣지 않는다). 없으면 글자 없이 실행된다.
UI_FONT = 'C:/Windows/Fonts/malgun.ttf'
DEBUG_FONT = UI_FONT

# 색 (r, g, b)
COLOR_WALL = (65, 36, 2)
COLOR_FLOOR = (214, 186, 150)
COLOR_FLOOR_LINE = (196, 166, 128)
COLOR_TABLE = (133, 79, 11)
COLOR_TABLE_EDGE = (99, 56, 6)
COLOR_PLAYER = (24, 95, 165)
COLOR_HAT = (186, 117, 23)
COLOR_GUN = (44, 44, 42)
COLOR_BULLET_PLAYER = (12, 68, 124)
COLOR_BULLET_FLOOR = (239, 159, 39)
COLOR_BULLET_EDGE = (99, 56, 6)
COLOR_AMMO_EMPTY = (180, 178, 169)
COLOR_BULLET_BOUNCED = (216, 90, 48)   # 튕긴 총알 (누구든 맞음)
COLOR_BULLET_ENEMY = (153, 53, 86)     # 적이 쏜 총알, 적이 밟고 줍는 총알 테두리
COLOR_HP = (226, 75, 74)
COLOR_HP_EMPTY = (99, 56, 6)
COLOR_MINE_WALL = (30, 26, 22)
COLOR_MINE_FLOOR = (46, 40, 34)
COLOR_MINE_LIGHT = (98, 82, 60)
COLOR_MINE_LIGHT_CORE = (128, 106, 76)
COLOR_ROCK = (88, 84, 78)
COLOR_ROCK_EDGE = (60, 57, 52)
COLOR_GLINT = (255, 244, 210)
COLOR_DOOR = (110, 64, 10)
COLOR_DOOR_OPEN = (150, 130, 100)
COLOR_TRAIN_OUTSIDE = (120, 96, 66)
COLOR_TRAIN_SLEEPER = (74, 54, 34)
COLOR_TRAIN_FLOOR = (168, 124, 80)
COLOR_TRAIN_PLANK = (140, 100, 62)
COLOR_STRIPE_YELLOW = (230, 180, 40)
COLOR_STRIPE_BLACK = (40, 34, 28)
COLOR_JOLT_WARN = (226, 75, 74)
COLOR_BOSS = (46, 40, 36)
COLOR_BOSS_HAT = (20, 18, 16)
COLOR_BANK_FLOOR = (206, 200, 188)
COLOR_BANK_TILE = (186, 180, 168)
COLOR_PILLAR = (150, 146, 138)
COLOR_PILLAR_EDGE = (112, 108, 100)
COLOR_CYLINDER = (44, 44, 42)          # 위쪽 HUD 리볼버 실린더
COLOR_CHAMBER_EMPTY = (95, 94, 90)
COLOR_HUD_TEXT = (244, 233, 212)
COLOR_FLASH = (255, 190, 30)           # 총구 불꽃 (나무 바닥 위에서 보이게 진한 노랑)
COLOR_FLASH_CORE = (255, 250, 235)
COLOR_BOOT = (68, 68, 65)
COLOR_PICKER = (59, 109, 17)
COLOR_BANDANA = (163, 45, 45)
COLOR_BOUNTY = (99, 153, 34)
COLOR_DRUNK = (83, 74, 183)
COLOR_BOTTLE = (15, 110, 86)
COLOR_DOG = (95, 75, 50)
COLOR_DOG_EAR = (60, 45, 30)
COLOR_HIT_FLASH = (255, 250, 240)      # 적이 맞은 순간 몸 색
HIT_FLASH_TIME = 0.1
COLOR_CROSSHAIR = (163, 45, 45)
COLOR_CROSSHAIR_EMPTY = (136, 135, 128)
