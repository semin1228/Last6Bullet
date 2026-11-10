# 게임 전체 설정값. PRD 11장(난이도 설계)의 '보통' 기준 초기값이며 플레이 테스트로 조정한다.

WIDTH, HEIGHT = 1280, 720
WALL = 32                      # 바깥 벽 두께 (px)

PLAYER_RADIUS = 14
PLAYER_SPEED = 200             # px/초

AMMO = 6                       # 구역 안에 존재하는 총알 수 (PRD 3장: 고정)
BULLET_RADIUS = 4
BULLET_SPEED = 520             # px/초
BULLET_LIFE = 1.6              # 이 시간이 지나면 바닥에 떨어진다 (초)
FIRE_COOLDOWN = 0.18           # 연사 간격 (초)

# 색 (r, g, b)
COLOR_WALL = (65, 36, 2)
COLOR_FLOOR = (214, 186, 150)
COLOR_FLOOR_LINE = (196, 166, 128)
COLOR_PLAYER = (24, 95, 165)
COLOR_HAT = (186, 117, 23)
COLOR_GUN = (44, 44, 42)
COLOR_BULLET_PLAYER = (12, 68, 124)
COLOR_BULLET_FLOOR = (239, 159, 39)
COLOR_BULLET_EDGE = (99, 56, 6)
COLOR_AMMO_EMPTY = (180, 178, 169)
