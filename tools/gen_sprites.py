# AI 이미지 API 로 게임 그림 원본을 뽑는다 (결과는 art_raw/<provider>/ 에 저장, 저장소에는 올리지 않는다).
#   set GEMINI_API_KEY=...   (또는 OPENAI_API_KEY)   키는 환경변수로만 넣는다. 채팅이나 코드에 적지 않는다.
#   C:\Python313\python.exe tools\gen_sprites.py --dry-run                 프롬프트만 출력 (API 호출 없음)
#   C:\Python313\python.exe tools\gen_sprites.py --provider gemini --only sheriff
#   C:\Python313\python.exe tools\gen_sprites.py --provider openai --only sheriff
#   C:\Python313\python.exe tools\gen_sprites.py --compare sheriff_down    provider 별 결과를 한 장에 나란히 (art_raw/compare_*.png)
# 이미 있는 파일은 건너뛴다. 마음에 안 들면 그 파일을 지우고 다시 실행하면 새로 뽑는다.
# 받은 그림은 tools\prep_sprites.py 로 투명 처리·크기 조정해서 res/ 에 넣는다 (docs/SPRITES.md).
# 이 스크립트는 API 문서(2026-11-25 확인)대로 썼고 실제 키로는 아직 돌려 보지 못했다. 응답 모양이 다르면 find_image 를 고친다.
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
RAW = os.path.join(ROOT, 'art_raw')

# docs/GEMINI_IMAGE_PROMPTS.md 의 공통 스타일 문단 (한 글자도 바꾸지 않는다)
STYLE = """Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark."""

CHARACTERS = {
    'sheriff': 'a Wild West sheriff with a tan wide-brim hat, blue shirt, dark green vest with a gold star badge, red bandana, holding a revolver',
    'picker': 'a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture',
    'drunk': 'a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side',
    'hound': 'a lean stray hound dog, ears back, tail visible, alert pose',
    'boss': 'a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders',
}
DIRECTIONS = {
    'down': 'facing toward the viewer (down the screen)',
    'up': 'seen from behind, facing away (up the screen)',
    'right': 'facing to the right in side view',
}
BACKGROUNDS = {
    'bg_saloon': ('Wild West saloon', 'dark wood plank floor, barrels and lanterns along the edges, swinging doors in the middle of the top wall'),
    'bg_mine': ('dark mine tunnel', 'dark rocky floor, wooden support beams and rails along the edges'),
    'bg_train': ('wooden freight train car', 'wooden plank floor, car walls on both long sides, a long horizontal rectangular room'),
    'bg_bank': ('bank', 'marble floor, teller cage bars and a vault door along the edges'),
}
OBSTACLES = {
    'obs_table': 'a round wooden saloon table with chairs',
    'obs_rock': 'a lump of cave rock',
    'obs_crate': 'a wooden freight crate',
    'obs_pillar': 'a square marble pillar seen from above',
}


def jobs(only=None):
    # (파일 이름, 프롬프트, 종횡비, 먼저 뽑아야 하는 기준 그림 이름) 목록
    out = []
    for name, desc in CHARACTERS.items():
        for d, text in DIRECTIONS.items():
            prompt = ('%s\nFull-body game character sprite of %s, %s, standing, with a soft round shadow under the feet,\n'
                      'centered, solid pure magenta (#FF00FF) background, 512x512.' % (STYLE, desc, text))
            ref = None if d == 'down' else name + '_down'      # 같은 캐릭터로 맞추려고 _down 을 참고 그림으로 준다
            if ref:
                prompt += '\nUse the attached image as the exact character design reference: same outfit, colors, proportions and art style.'
            out.append((name + '_' + d, prompt, '1:1', ref))
    for name, (place, details) in BACKGROUNDS.items():
        out.append((name, '%s\nEmpty %s interior, same steep high-angle camera (about 65 degrees down), 16:9, 1280x720,\n'
                    'large open empty floor in the middle with no furniture and no characters, walls and props only along the edges,\n%s.'
                    % (STYLE, place, details), '16:9', None))
    for name, obj in OBSTACLES.items():
        out.append((name, '%s\n%s, same steep high-angle camera (about 65 degrees down), same art style, filling a roughly square area,\n'
                    'solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.' % (STYLE, obj), '1:1', None))
    if only:
        out = [j for j in out if any(j[0].startswith(o) for o in only)]
    return out


def post(url, headers, body):
    req = urllib.request.Request(url, json.dumps(body).encode('utf-8'), headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit('API 오류 %s: %s' % (e.code, e.read()[:500].decode('utf-8', 'replace')))


def find_image(node):
    # 응답 JSON 어디에 있든 base64 이미지(긴 문자열 'data' 또는 'b64_json')를 찾아 바이트로 돌려준다
    if isinstance(node, dict):
        for key in ('b64_json', 'data'):
            v = node.get(key)
            if isinstance(v, str) and len(v) > 1000:
                return base64.b64decode(v)
        for v in node.values():
            found = find_image(v)
            if found:
                return found
    elif isinstance(node, list):
        for v in node:
            found = find_image(v)
            if found:
                return found
    return None


def gemini(prompt, aspect, ref_path, model, size):
    key = os.environ.get('GEMINI_API_KEY') or sys.exit('GEMINI_API_KEY 환경변수가 없습니다')
    content = [{'type': 'text', 'text': prompt}]
    if ref_path:
        content.append({'type': 'image', 'mime_type': 'image/png', 'data': base64.b64encode(open(ref_path, 'rb').read()).decode()})
    body = {'model': model, 'input': content, 'response_format': {'type': 'image', 'aspect_ratio': aspect, 'image_size': size}}
    return find_image(post('https://generativelanguage.googleapis.com/v1beta/interactions',
                           {'x-goog-api-key': key, 'Content-Type': 'application/json'}, body))


def openai(prompt, aspect, ref_path, model, size):
    # gpt-image 계열: 투명 배경을 직접 지원한다 (마젠타가 필요 없지만 같은 프롬프트로 비교하려고 그대로 둔다)
    key = os.environ.get('OPENAI_API_KEY') or sys.exit('OPENAI_API_KEY 환경변수가 없습니다')
    if ref_path:
        sys.exit('openai 참고 그림 입력은 아직 구현하지 않았습니다 (--only 로 _down 만 뽑아 비교하세요)')
    px = '1536x1024' if aspect == '16:9' else '1024x1024'
    body = {'model': model, 'prompt': prompt, 'size': px, 'n': 1}
    return find_image(post('https://api.openai.com/v1/images/generations',
                           {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, body))


def compare(stem):
    from PIL import Image
    shots = []
    for prov in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, prov, stem + '.png')
        if os.path.isfile(p):
            shots.append((prov, Image.open(p).convert('RGB').resize((512, 512))))
    if not shots:
        sys.exit('비교할 그림이 없습니다: art_raw/*/%s.png' % stem)
    sheet = Image.new('RGB', (512 * len(shots), 512), (255, 255, 255))
    for i, (prov, im) in enumerate(shots):
        sheet.paste(im, (512 * i, 0))
    path = os.path.join(RAW, 'compare_%s.png' % stem)
    sheet.save(path)
    print('왼쪽부터', [p for p, _ in shots], '->', path)


def main():
    ap = argparse.ArgumentParser(description='AI 이미지 API 로 게임 그림 원본 뽑기')
    ap.add_argument('--provider', choices=['gemini', 'openai'], default='gemini')
    ap.add_argument('--model', help='기본: gemini=gemini-3-pro-image (Nano Banana Pro, 고품질), openai=gpt-image-1')
    ap.add_argument('--size', default='2K', help='gemini 그림 크기 1K/2K/4K (기본 2K)')
    ap.add_argument('--only', nargs='*', help='이름이 이 글자로 시작하는 것만 (예: sheriff bg_saloon)')
    ap.add_argument('--dry-run', action='store_true', help='프롬프트만 출력하고 API 는 부르지 않는다')
    ap.add_argument('--compare', metavar='NAME', help='provider 별 NAME.png 를 나란히 붙인 비교 그림을 만든다')
    args = ap.parse_args()
    if args.compare:
        return compare(args.compare)
    model = args.model or ('gemini-3-pro-image' if args.provider == 'gemini' else 'gpt-image-1')
    out_dir = os.path.join(RAW, args.provider)
    for name, prompt, aspect, ref in jobs(args.only):
        path = os.path.join(out_dir, name + '.png')
        if args.dry_run:
            print('--- %s (%s, 참고: %s)\n%s\n' % (name, aspect, ref, prompt))
            continue
        if os.path.isfile(path):
            print('건너뜀 (이미 있음):', name)
            continue
        ref_path = os.path.join(out_dir, ref + '.png') if ref else None
        if ref_path and not os.path.isfile(ref_path):
            print('건너뜀 (참고 그림 %s 먼저 필요):' % ref, name)
            continue
        print('만드는 중:', name)
        data = (gemini if args.provider == 'gemini' else openai)(prompt, aspect, ref_path, model, args.size)
        if not data:
            print('  응답에서 그림을 못 찾음 (find_image 를 확인)')
            continue
        os.makedirs(out_dir, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)
        print('  저장', os.path.relpath(path, ROOT))


if __name__ == '__main__':
    main()
