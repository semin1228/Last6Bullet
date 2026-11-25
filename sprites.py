# 그림 불러오기와 그리기 도우미. res/ 폴더의 PNG 를 이름으로 한 번만 불러와 캐시한다.
# 그림이 없으면 아무것도 그리지 않고 False/None 을 돌려주므로, 부른 쪽이 기존 도형 그리기로 넘어간다 (폴백).
#
# 캐릭터 그림 규칙 (docs/GEMINI_IMAGE_PROMPTS.md):
#   NAME_down.png, NAME_up.png, NAME_right.png 세 장이 모두 있으면 조준 각도에 가까운 방향을 고르고
#   왼쪽은 오른쪽을 좌우 반전한다. 그것이 없고 NAME.png 한 장이 있으면 오른쪽을 보는 그림으로 보고 회전한다.
#   그림은 보이기만 한다. 판정과 총알 방향은 그림과 상관없이 각도로 계산한다.
import math
import os

import config

RES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res')
_cache = {}          # 이름 -> Image 또는 None (없는 것도 기억해 매 프레임 디스크를 뒤지지 않는다)


def set_dir(path):
    # 그림 폴더를 바꾸고 캐시를 비운다 (점검과 스크린샷이 임시 폴더의 더미 그림을 쓸 때)
    global RES_DIR
    RES_DIR = path
    _cache.clear()


def _load(path):
    from pico2d import load_image
    return load_image(path)


def get(name):
    # res/NAME.png 를 불러온다. 파일이 없거나 불러오지 못하면 None (없는 것도 기억해 매 프레임 디스크를 뒤지지 않는다).
    if name in _cache:
        return _cache[name]
    image = None
    path = os.path.join(RES_DIR, name + '.png')
    if os.path.isfile(path):
        try:
            image = _load(path)
        except Exception:        # 창 없는 점검 환경(렌더러 없음)이나 깨진 파일: 도형으로 그린다
            image = None
    _cache[name] = image
    return image


def pick_direction(angle):
    # 조준 각도(라디안) -> ('right'|'up'|'down', 좌우 반전 여부). 90도씩 네 구역으로 나눈다.
    a = math.degrees(angle) % 360
    if a < 45 or a >= 315:
        return 'right', False
    if a < 135:
        return 'up', False
    if a < 225:
        return 'right', True        # 왼쪽: 오른쪽 그림을 반전
    return 'down', False


def has_directions(name):
    return all(get('%s_%s' % (name, d)) is not None for d in ('down', 'up', 'right'))


def draw_character(name, x, y, angle, variant=None):
    # 캐릭터 그림을 (x, y) 가운데로 그린다. 그렸으면 True, 그림이 없어 못 그렸으면 False.
    # variant: 'run1' 처럼 오른쪽 동작 그림 (sheriff_right_run1.png). 위·아래를 볼 때는 쓰지 않는다.
    size = config.SPRITE_SIZE.get(name, 64)
    if has_directions(name):
        direction, flip = pick_direction(angle)
        image = None
        if variant and direction == 'right':
            image = get('%s_right_%s' % (name, variant))
        if image is None:
            image = get('%s_%s' % (name, direction))
        image.composite_draw(0, 'h' if flip else '', x, y, size, size)
        return True
    image = get(name)
    if image is not None:
        image.composite_draw(angle, '', x, y, size, size)     # 오른쪽을 보는 한 장을 각도만큼 회전
        return True
    return False


OBSTACLE_FILES = {'table': 'obs_table', 'rock': 'obs_rock', 'crate': 'obs_crate', 'pillar': 'obs_pillar'}


def draw_obstacle(kind, index, rect):
    # 장애물 사각형(판정) 위에 그림을 사각형 크기로 맞춰 그린다. 모양이 여러 장(obs_rock2.png ...)이면 번갈아 쓴다.
    base = OBSTACLE_FILES[kind]
    images = [get(base)] + [get('%s%d' % (base, n)) for n in (2, 3, 4)]
    images = [im for im in images if im is not None]
    if not images:
        return False
    ol, ob, o_r, ot = rect
    images[index % len(images)].draw((ol + o_r) / 2, (ob + ot) / 2, o_r - ol, ot - ob)
    return True


def draw_background(name):
    # 1280x720 배경을 화면 전체에 그린다. 없으면 False.
    image = get(name)
    if image is None:
        return False
    image.draw(config.WIDTH / 2, config.HEIGHT / 2, config.WIDTH, config.HEIGHT)
    return True


def draw_dark_background(name, light):
    # 어두운 구역: 배경을 어둡게 깔고, 빛 반경 안만 원래 밝기로 다시 그린다 (가로줄 띠로 원을 만든다).
    image = get(name)
    if image is None:
        return False
    texture = image.texture
    try:
        from pico2d import SDL_SetTextureColorMod
        SDL_SetTextureColorMod(texture, *config.MINE_DIM)
    except Exception:
        pass
    image.draw(config.WIDTH / 2, config.HEIGHT / 2, config.WIDTH, config.HEIGHT)
    try:
        SDL_SetTextureColorMod(texture, 255, 255, 255)
    except Exception:
        pass
    if light is not None:
        r, step = config.LIGHT_RADIUS, 4
        sx, sy = image.w / config.WIDTH, image.h / config.HEIGHT      # 화면 좌표 -> 그림 좌표
        for k in range(-r, r, step):
            half = math.sqrt(max(0, r * r - (k + step / 2) ** 2))
            left, right, bottom = max(0.0, light.x - half), min(float(config.WIDTH), light.x + half), light.y + k
            w = right - left
            if w < 1 or not (0 <= bottom <= config.HEIGHT - step):
                continue
            image.clip_draw(int(left * sx), int(bottom * sy), max(1, int(w * sx)), max(1, int(step * sy)),
                            left + w / 2, bottom + step / 2, w, step)
    return True
