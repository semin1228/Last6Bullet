# 마젠타(#FF00FF) 단색 배경 그림을 투명 PNG 로 바꾸고 크기를 줄인다. Gemini 는 투명 PNG 를 못 내는 경우가 많아서 쓴다.
#   C:\Python313\python.exe tools\prep_sprites.py 받은그림폴더 res [--size 128] [--tol 90]
# - 받은그림폴더의 PNG/JPG 를 읽어 같은 이름의 .png 를 출력 폴더에 저장한다. 원본은 지우거나 고치지 않는다.
# - 마젠타와 가까운 색은 투명, 경계는 반투명으로 부드럽게 하고 분홍 번짐은 줄인다 (--tol 이 클수록 많이 지운다).
# - bg_, poster_ 로 시작하는 파일은 배경과 포스터라 투명 처리하지 않고 크기만 맞춘다 (배경 1280x720).
# - Pillow 가 필요하다 (이 도구만. 게임 본체는 Pillow 없이 돈다).
import argparse
import os
import sys

from PIL import Image

KEY = (255, 0, 255)
NO_KEY_PREFIXES = ('bg_', 'poster_')


def magenta_to_alpha(img, tol=90):
    # RGBA 로 바꿔 돌려준다. 마젠타와의 거리가 tol 이하면 완전 투명, tol~2*tol 이면 반투명(경계), 그 밖은 불투명.
    img = img.convert('RGBA')
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            dist = ((r - KEY[0]) ** 2 + (g - KEY[1]) ** 2 + (b - KEY[2]) ** 2) ** 0.5
            if dist <= tol:
                px[x, y] = (0, 0, 0, 0)
            elif dist < tol * 2:                      # 경계: 반투명으로 하고 분홍 번짐(빨강·파랑이 초록보다 센 만큼)을 뺀다
                spill = max(0, min(r, b) - g)
                alpha = int(255 * (dist - tol) / tol)
                px[x, y] = (r - spill, g, b - spill, alpha)
    return img


def convert_file(src, dst, size=None, tol=90):
    img = Image.open(src)
    name = os.path.basename(src).lower()
    if name.startswith(NO_KEY_PREFIXES):
        img = img.convert('RGB')
        if name.startswith('bg_'):
            size = (1280, 720)
    else:
        img = magenta_to_alpha(img, tol)
    if size is not None and img.size != size:
        img = img.resize(size, Image.LANCZOS)
    img.save(dst)


def main():
    ap = argparse.ArgumentParser(description='마젠타 배경 그림을 투명 PNG 로 바꾸고 줄인다')
    ap.add_argument('src', help='받은 그림이 있는 폴더 (원본은 그대로 둔다)')
    ap.add_argument('dst', help='결과를 저장할 폴더 (보통 res)')
    ap.add_argument('--size', type=int, default=0, help='캐릭터·장애물을 이 크기의 정사각형으로 줄인다 (0 이면 그대로)')
    ap.add_argument('--tol', type=int, default=90, help='마젠타로 보는 색 거리 (기본 90)')
    args = ap.parse_args()
    src, dst = os.path.abspath(args.src), os.path.abspath(args.dst)
    if src == dst:
        sys.exit('입력과 출력 폴더가 같으면 원본을 덮어쓰므로 다른 폴더를 지정하세요')
    os.makedirs(dst, exist_ok=True)
    size = (args.size, args.size) if args.size else None
    count = 0
    for fn in sorted(os.listdir(src)):
        stem, ext = os.path.splitext(fn)
        if ext.lower() not in ('.png', '.jpg', '.jpeg'):
            continue
        convert_file(os.path.join(src, fn), os.path.join(dst, stem + '.png'), size, args.tol)
        print('  ', fn, '->', stem + '.png')
        count += 1
    print('%d개 변환' % count)


if __name__ == '__main__':
    main()
