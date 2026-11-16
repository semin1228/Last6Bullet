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
ENEMY_PICK_TIME = 0.25         # 적이 바닥 총알을 줍는 동작 시간 (초)
ENEMY_STUN_TIME = 0.7          # 발차기에 맞은 적의 기절 시간 (초)
ENEMY_BULLET_SPEED = 560       # 적 총알은 플레이어 총알(800)보다 느리게 해서 피할 틈을 준다 (px/초)
ENEMY_AIM_LEAD = 0.5           # 플레이어 이동을 얼마나 예측해서 겨누는지 (0: 안 함, 1: 완전)
PICKER_SPEED = 120
PICKER_KEEP_NEAR = 180         # 줍줍이가 쏠 때 유지하는 거리 (이보다 가까우면 물러난다)
PICKER_KEEP_FAR = 340          # (이보다 멀면 다가간다)
PICKER_FIRST_SHOT = 0.35       # 줍고 나서 첫 발까지 (초)
PICKER_SHOOT_INTERVAL = 0.9    # 쏘는 간격 (초)
DETOUR_DIST = 90               # 적이 장애물에 막혔을 때 옆으로 비켜 걷는 거리 (테이블 반 폭 + 몸)
DRUNK_SPEED = 150
DRUNK_SWAY_SPEED = 3.0         # 비틀거리는 빠르기 (라디안/초)
DRUNK_SWAY_ANGLE = 0.6         # 비틀거리며 벗어나는 각도 (라디안)
DOG_SPEED = 230                # 들개는 플레이어(200)보다 빠르게 총알로 달려간다
DOG_ROAM_SPEED = 110
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

# 광산 바위·버팀목 (left, bottom, right, top)
MINE_ROCKS = [
    (300, 430, 370, 600),
    (540, 110, 690, 190),
    (800, 400, 880, 560),
    (960, 200, 1040, 300),
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
COLOR_CROSSHAIR = (163, 45, 45)
COLOR_CROSSHAIR_EMPTY = (136, 135, 128)
