# 게임 전체 설정값. PRD 11장(난이도 설계)의 '보통' 기준 초기값이며 플레이 테스트로 조정한다.

WIDTH, HEIGHT = 1280, 720
WALL = 32                      # 바깥 벽 두께 (px)

PLAYER_RADIUS = 14
PLAYER_SPEED = 200             # px/초
PLAYER_HP = 4
INVINCIBLE_TIME = 1.0          # 맞은 뒤 무적 시간 (초)
PICKUP_REACH = 2               # 몸과 총알이 이만큼 떨어져 있어도 줍는다 (px)

AMMO = 6                       # 구역 안에 존재하는 총알 수 (PRD 3장: 고정)
BULLET_RADIUS = 4
BULLET_SPEED = 520             # px/초
BULLET_LIFE = 1.6              # 이 시간이 지나면 바닥에 떨어진다 (초)
FIRE_COOLDOWN = 0.18           # 연사 간격 (초)
MAX_BOUNCES = 2                # 이만큼 튕긴 뒤 다시 닿으면 바닥에 떨어진다
DRY_FLASH_TIME = 0.3           # 빈 총을 당겼을 때 HUD 실린더가 붉게 깜빡이는 시간 (초)
HIT_GRACE = 0.12              # 발사 직후 이 시간 동안은 사람에게 맞지 않는다 (초)
BULLET_SUBSTEP = 6             # 한 번에 움직이는 최대 거리 (px). 얇은 벽을 뚫고 지나가지 않게 한다

# 술집 테이블 (left, bottom, right, top)
SALOON_TABLES = [
    (360, 470, 500, 540),
    (580, 180, 720, 250),
    (840, 440, 980, 510),
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
COLOR_HP = (226, 75, 74)
COLOR_HP_EMPTY = (99, 56, 6)
COLOR_CYLINDER = (44, 44, 42)          # 위쪽 HUD 리볼버 실린더
COLOR_CHAMBER_EMPTY = (95, 94, 90)
COLOR_HUD_TEXT = (244, 233, 212)
COLOR_FLASH = (250, 199, 117)          # 총구 불꽃
COLOR_FLASH_CORE = (255, 250, 235)
COLOR_CROSSHAIR = (163, 45, 45)
COLOR_CROSSHAIR_EMPTY = (136, 135, 128)
