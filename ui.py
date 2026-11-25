# 타이틀·포스터·엔딩 화면이 함께 쓰는 글자 도우미.
# pico2d 의 Font 에는 글자 너비를 재는 기능이 없어서, 영어 대문자 한 글자가 글자 크기의 약 0.6배라고 보고 가운데 맞춘다.
from pico2d import load_font

import config


def load(size):
    try:
        return load_font(config.UI_FONT, size)
    except Exception:
        return None            # 글꼴 파일이 없으면 글자 없이 도형만 그린다


def draw_center(font, x, y, text, size, color):
    if font:
        font.draw(x - len(text) * size * 0.27, y, text, color)
