# 자동 점검: 기능마다 명세를 테스트로 옮겨 두고, 게임 루프를 고정 프레임으로 돌려 확인한다.
#   C:\Python313\python.exe tools\check.py            창 없이 실행
#   C:\Python313\python.exe tools\check.py --window   창을 띄워 실행
import sys
import traceback

import sim

import play_mode
from pico2d import close_canvas
from checks import c1_basics, c2_enemies, c3_zones, c4_train_boss, c6_sprites   # noqa: F401  불러오면 테스트가 순서대로 등록된다
from checks.common import TESTS


def main():
    sim.open_game('--window' in sys.argv)
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print('  PASS', fn.__name__)
        except Exception:
            failed += 1
            print('  FAIL', fn.__name__)
            traceback.print_exc()
            play_mode.finish()
    close_canvas()
    print('%d/%d passed' % (len(TESTS) - failed, len(TESTS)))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
