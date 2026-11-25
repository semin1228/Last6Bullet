# 자동 점검: 4주차 그림 교체 (sprites.py, tools/prep_sprites.py). 그림은 코드로 만든 더미를 임시 폴더에 두고 쓴다.
import contextlib
import math
import os
import shutil
import tempfile

import sim                       # 먼저 불러야 게임 폴더가 import 경로에 들어간다

import config
import sprites
from checks.common import fresh, test

REAL_DIR = sprites.RES_DIR
DRAWS = {'n': 0}


class FakeImage:
    # 창 없는 점검에서는 실제 그림을 불러올 수 없어서(렌더러 없음), 그리기 호출만 세는 가짜 그림을 쓴다.
    # 실제 그림이 화면에 나오는지는 tools/shot.py 로 눈으로 확인한다.
    w, h, texture = 1280, 720, None
    calls = None

    def draw(self, *a):
        DRAWS['n'] += 1

    def clip_draw(self, *a):
        DRAWS['n'] += 1

    def composite_draw(self, rad, flip, x, y, w=None, h=None):
        DRAWS['n'] += 1
        if FakeImage.calls is not None:
            FakeImage.calls.append((rad, flip, w, h))


def make_png(folder, name, color=(200, 40, 40, 255), size=(64, 64)):
    from PIL import Image as PilImage
    PilImage.new('RGBA', size, color).save(os.path.join(folder, name + '.png'))


@contextlib.contextmanager
def dummy_res(names=()):
    # 임시 폴더에 더미 그림을 만들어 sprites 가 거기서 읽게 한다. 끝나면 원래 폴더로 되돌린다.
    folder = tempfile.mkdtemp(prefix='l6b_sprites_')
    for name in names:
        make_png(folder, name, size=(1280, 720) if name.startswith('bg_') else (64, 64))
    sprites.set_dir(folder)
    real_load = sprites._load
    sprites._load = lambda path: FakeImage()
    try:
        yield folder
    finally:
        sprites._load = real_load
        sprites.set_dir(REAL_DIR)
        shutil.rmtree(folder, ignore_errors=True)


@contextlib.contextmanager
def count_image_draws():
    DRAWS['n'] = 0
    yield DRAWS


CHARACTERS = ('sheriff', 'picker', 'drunk', 'hound', 'boss')


def all_direction_names():
    return ['%s_%s' % (c, d) for c in CHARACTERS for d in ('down', 'up', 'right')]


# ---------------------------------------------------------------- 17. 4주차: 그림 교체


@test
def sprites_without_files_draw_shapes_and_return_none():
    with dummy_res():
        assert sprites.get('sheriff_down') is None and sprites.get('bg_saloon') is None
        assert not sprites.draw_character('sheriff', 100, 100, 0.0), '그림이 없는데 그렸다고 답함'
        assert not sprites.draw_background('bg_saloon')
        pm = fresh(enemies=True)
        with count_image_draws() as c:
            sim.step(10)
        assert c['n'] == 0, '그림이 없는데 이미지 그리기가 불림 (%d)' % c['n']
        pm.finish()


@test
def sprites_missing_folder_is_safe():
    sprites.set_dir(os.path.join(REAL_DIR, 'no_such_folder'))
    try:
        assert sprites.get('anything') is None
        pm = fresh(enemies=True)
        sim.step(5)
        pm.finish()
    finally:
        sprites.set_dir(REAL_DIR)


@test
def direction_choice_follows_aim_angle():
    cases = [(0, ('right', False)), (30, ('right', False)), (60, ('up', False)), (90, ('up', False)),
             (120, ('up', False)), (150, ('right', True)), (180, ('right', True)), (-150, ('right', True)),
             (-120, ('down', False)), (-90, ('down', False)), (-60, ('down', False)), (-30, ('right', False))]
    for deg, want in cases:
        got = sprites.pick_direction(math.radians(deg))
        assert got == want, '%d도: %s 가 아니라 %s' % (deg, want, got)


@test
def three_direction_sprites_are_drawn_for_every_character():
    with dummy_res(all_direction_names()):
        assert sprites.has_directions('sheriff')
        with count_image_draws() as c:
            for name in CHARACTERS:
                for deg in (0, 90, 180, -90):
                    assert sprites.draw_character(name, 300, 300, math.radians(deg)), name
        assert c['n'] == 20
        pm = fresh(enemies=True)         # 게임 화면에서도 보안관과 적이 모두 그림으로 그려진다
        with count_image_draws() as c:
            sim.step(5)
        assert c['n'] >= 5 * (1 + len(pm.enemies)), '게임 안에서 그림이 안 그려짐 (%d)' % c['n']
        pm.finish()


@test
def partial_direction_set_falls_back_to_shape():
    with dummy_res(['picker_down', 'picker_up']):      # 오른쪽이 없다
        assert not sprites.has_directions('picker')
        assert not sprites.draw_character('picker', 100, 100, 0.0), '세 장이 안 모였는데 그림을 씀'


@test
def single_sprite_is_rotated_by_aim_angle():
    with dummy_res(['hound']):
        assert not sprites.has_directions('hound')
        FakeImage.calls = calls = []
        try:
            assert sprites.draw_character('hound', 200, 200, 1.25)
        finally:
            FakeImage.calls = None
        assert calls == [(1.25, '', config.SPRITE_SIZE['hound'], config.SPRITE_SIZE['hound'])], calls


@test
def left_aim_flips_the_right_sprite():
    with dummy_res(all_direction_names()):
        FakeImage.calls = calls = []
        try:
            sprites.draw_character('sheriff', 200, 200, math.pi)
            sprites.draw_character('sheriff', 200, 200, 0.0)
        finally:
            FakeImage.calls = None
        size = config.SPRITE_SIZE['sheriff']
        assert calls == [(0, 'h', size, size), (0, '', size, size)], calls


@test
def sheriff_run_and_kick_sprites_are_used_when_present():
    with dummy_res(all_direction_names() + ['sheriff_right_run1', 'sheriff_right_run2', 'sheriff_right_kick']):
        used = []
        orig = sprites.get
        sprites.get = lambda name: (used.append(name), orig(name))[1]
        try:
            sprites.draw_character('sheriff', 100, 100, 0.0, 'kick')
            sprites.draw_character('sheriff', 100, 100, 0.0, 'run2')
            used.append('--')
            sprites.draw_character('sheriff', 100, 100, math.pi / 2, 'run1')    # 위를 볼 때는 위 그림
        finally:
            sprites.get = orig
        assert 'sheriff_right_kick' in used and 'sheriff_right_run2' in used, used
        after = used[used.index('--'):]
        assert 'sheriff_right_run1' not in after and after[-1] == 'sheriff_up', used


@test
def backgrounds_and_obstacles_draw_in_every_zone_with_pictures():
    names = ['bg_saloon', 'bg_mine', 'bg_train', 'bg_bank', 'obs_table', 'obs_rock', 'obs_crate', 'obs_pillar']
    with dummy_res(names):
        pm = fresh(enemies=True)
        for i in range(4):
            pm.start_zone(i)
            with count_image_draws() as c:
                sim.step(3)
            per_frame = 1 + len(pm.zone.obstacles)       # 배경 한 장 + 장애물마다 한 장
            assert c['n'] >= 3 * per_frame, '구역 %d: 그림 그리기 %d 번' % (i + 1, c['n'])
        pm.finish()


@test
def mine_background_is_dim_with_a_lit_circle_around_the_lantern():
    with dummy_res(['bg_mine']):
        pm = fresh()
        pm.start_zone(1)
        with count_image_draws() as c:
            sim.step(1)
        assert c['n'] > 1 + config.LIGHT_RADIUS // 4, c['n']      # 어둡게 한 장 + 빛 반경 안 가로줄 여러 개
        pm.player.x, pm.player.y = 5, 5                           # 모서리에서도 예외 없이
        sim.step(2)
        pm.finish()


@test
def train_background_keeps_jolt_warning_and_lip_line():
    with dummy_res(['bg_train']):
        pm = fresh()
        pm.start_zone(2)
        pm.zone.jolt_in = config.JOLT_WARN / 2           # 덜컹 예고 중
        sim.step(8)
        assert pm.zone.warning() or pm.zone.jolting()
        pm.finish()


@test
def obstacle_pictures_do_not_change_collision():
    with dummy_res(['obs_table', 'obs_rock']):
        pm = fresh()
        z = pm.zone
        for rect in z.obstacles:
            cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
            x, y = z.push_out(cx, cy, config.PLAYER_RADIUS)
            assert (x, y) != (cx, cy), '사각형 안에 있던 몸이 밀려나지 않음'
        pm.finish()


@test
def prep_tool_makes_magenta_transparent_and_keeps_subject():
    from PIL import Image as PilImage
    import prep_sprites
    img = PilImage.new('RGB', (40, 40), (255, 0, 255))
    for y in range(10, 30):
        for x in range(10, 30):
            img.putpixel((x, y), (30, 90, 160))
    img.putpixel((9, 20), (255, 90, 255))           # 가장자리 분홍 번짐 한 점
    out = prep_sprites.magenta_to_alpha(img, 90)
    assert out.getpixel((0, 0))[3] == 0, '모서리 배경이 투명하지 않음'
    assert out.getpixel((20, 20)) == (30, 90, 160, 255), '본체가 바뀜'
    fringe = out.getpixel((9, 20))
    assert fringe[3] < 255, '번진 점이 투명해지지 않음 (%s)' % (fringe,)


@test
def prep_tool_resizes_and_never_touches_the_original():
    from PIL import Image as PilImage
    import prep_sprites
    src = tempfile.mkdtemp(prefix='l6b_in_')
    dst = tempfile.mkdtemp(prefix='l6b_out_')
    try:
        PilImage.new('RGB', (200, 200), (255, 0, 255)).save(os.path.join(src, 'sheriff_down.png'))
        PilImage.new('RGB', (1920, 1080), (90, 60, 30)).save(os.path.join(src, 'bg_saloon.jpg'))
        before = open(os.path.join(src, 'sheriff_down.png'), 'rb').read()
        prep_sprites.convert_file(os.path.join(src, 'sheriff_down.png'), os.path.join(dst, 'sheriff_down.png'), (64, 64))
        prep_sprites.convert_file(os.path.join(src, 'bg_saloon.jpg'), os.path.join(dst, 'bg_saloon.png'))
        a = PilImage.open(os.path.join(dst, 'sheriff_down.png'))
        b = PilImage.open(os.path.join(dst, 'bg_saloon.png'))
        assert a.size == (64, 64) and a.mode == 'RGBA' and a.getpixel((5, 5))[3] == 0
        assert b.size == (1280, 720) and b.mode == 'RGB', '배경은 투명 처리하지 않고 1280x720 으로'
        assert open(os.path.join(src, 'sheriff_down.png'), 'rb').read() == before, '원본이 바뀜'
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)
