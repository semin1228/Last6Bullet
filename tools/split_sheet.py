# 가로로 나란히 그려진 방향 그림 한 장(시트)을 잘라 NAME_down/up/right.png 로 저장한다.
#   C:\Python313\python.exe tools\split_sheet.py 시트.png sheriff 출력폴더
# 기본은 왼쪽부터 아래·위·오른쪽 3칸 (--order 로 바꾼다). 각 칸을 정사각형으로 잘라 저장하고 원본은 건드리지 않는다.
# 저장된 그림은 마젠타 배경 그대로이니 tools\prep_sprites.py 로 투명 처리한다.
import argparse
import os
import sys

from PIL import Image


def split(img, order):
    # 가로를 len(order) 칸으로 똑같이 나누고, 각 칸 가운데에서 정사각형으로 자른다. {방향: 그림} 을 돌려준다.
    w, h = img.size
    cell = w / len(order)
    side = int(min(cell, h))
    out = {}
    for i, name in enumerate(order):
        cx = cell * (i + 0.5)
        left = int(round(cx - side / 2))
        top = int(round((h - side) / 2))
        out[name] = img.crop((left, top, left + side, top + side))
    return out


def main():
    ap = argparse.ArgumentParser(description='방향 그림 시트를 칸별로 잘라 저장')
    ap.add_argument('sheet', help='나란히 그려진 시트 이미지')
    ap.add_argument('name', help='캐릭터 이름 (예: sheriff). 결과는 NAME_down.png 같은 이름')
    ap.add_argument('out', help='저장할 폴더')
    ap.add_argument('--order', default='down,up,right', help='왼쪽부터 칸 순서 (기본 down,up,right)')
    args = ap.parse_args()
    order = args.order.split(',')
    if not os.path.isfile(args.sheet):
        sys.exit('시트 파일이 없습니다: %s' % args.sheet)
    os.makedirs(args.out, exist_ok=True)
    img = Image.open(args.sheet).convert('RGB')
    for d, part in split(img, order).items():
        path = os.path.join(args.out, '%s_%s.png' % (args.name, d))
        part.save(path)
        print('  저장', path, part.size)


if __name__ == '__main__':
    main()
