# AI 이미지 요청서 (Gemini 통일판, 복사해서 붙여 넣기)

Gemini 이미지 생성 대화창에 아래 요청을 **순서대로** 하나씩 붙여 넣는다. 코드 블록 하나가 한 번의 요청이고, 공통 스타일 문단이 이미 들어 있다.
정해진 것 (2026-11-25): **한 세트는 Gemini 하나로**, 시점은 **위에서 약 65도 하이앵글**, 얼굴이 모자 아래에 보이는 차분하고 약간 근엄한 표정, 총은 손에 쥐고 있다. 기준 그림은 보안관 정면(Gemini 6번, 콧수염이 작은 것).

## 진행 규칙
1. **캐릭터는 방향 3장을 한 그림(시트)에 뽑는다.** 요청이 3분의 1로 줄고 한 번에 그려서 같은 캐릭터가 되기 쉽다. 받은 시트는 `tools\split_sheet.py` 로 자른다 (아래 '저장과 투명 처리').
2. 시트가 칸이 어긋나거나 잘리면 같은 요청을 다시 뽑는다. 한 장만 보고 정하지 말고 2~3번 뽑아 가장 나은 것을 고른다.
3. 두 번째 캐릭터부터는 **보안관 시트를 같이 첨부**하고 "같은 그림체, 같은 선 굵기와 채도"를 덧붙인다 (첨부가 안 되면 요청만 붙인다).
4. 같은 대화창에서 이어서 뽑으면 스타일이 더 잘 맞는다. 새 대화로 시작하면 스타일 문단이 요청마다 들어 있으니 그대로 붙이면 된다. 단, **새 요청에서 시점이 안 바뀌면 이전 그림이 보이는 대화창이 원인**일 수 있으니 새 대화에서 첨부 없이 뽑는다.
5. 맨 마지막에 확인한다: 세 방향이 같은 캐릭터인가(모자, 옷 색, 비율), 오른쪽 그림이 정확히 오른쪽을 보나, 같은 시점(약 65도)인가, 글자·워터마크 없나. 오른쪽 아래의 Gemini 반짝이 마크는 마젠타와 같이 지워진다.

## 저장과 투명 처리
```powershell
# 1) 시트를 방향별로 자른다 (받은 시트 -> 이름_down/up/right.png)
C:\Python313\python.exe tools\split_sheet.py C:\dev\2dgp\raw_art\sheriff_sheet.png sheriff C:\dev\2dgp\raw_art
# 2) 마젠타를 투명으로 바꾸고 줄여 res/ 에 넣는다 (기본 --tol 90, 올리면 살색이 깎인다)
C:\Python313\python.exe tools\prep_sprites.py C:\dev\2dgp\raw_art res --size 256
```
받은그림 폴더는 저장소 밖(`C:\dev\2dgp\raw_art`)에 둔다. 경로와 파일 이름에 한글·공백을 쓰지 않는다. 자세한 규칙은 `docs/SPRITES.md`.

## 필요한 파일 전체 목록 (체크하며 진행)
파일 이름은 코드가 그대로 읽는다. 저장 위치는 최종적으로 `res/` 이다. 왼쪽 보는 그림은 오른쪽을 코드가 반전하므로 만들지 않는다.

**A. 꼭 필요 (23개)** - 이것만 있어도 4개 구역이 그림으로 돈다
- [ ] 보안관 `sheriff_down` `sheriff_up` `sheriff_right`
- [ ] 줍줍이 `picker_down` `picker_up` `picker_right`
- [ ] 술꾼 `drunk_down` `drunk_up` `drunk_right`
- [ ] 들개 `hound_down` `hound_up` `hound_right`
- [ ] 두목 `boss_down` `boss_up` `boss_right`
- [ ] 배경 `bg_saloon` `bg_mine` `bg_train` `bg_bank`
- [ ] 장애물 `obs_table` `obs_rock` `obs_crate` `obs_pillar`

**B. 있으면 좋음 - 걷기 (30개)** - 움직일 때 두 장이 번갈아 나온다
- [ ] 보안관 `sheriff_{down,up,right}_{walk1,walk2}` (6)
- [ ] 줍줍이 `picker_{down,up,right}_{walk1,walk2}` (6)
- [ ] 술꾼 `drunk_{down,up,right}_{walk1,walk2}` (6)
- [ ] 들개 `hound_{down,up,right}_{walk1,walk2}` (6)
- [ ] 두목 `boss_{down,up,right}_{walk1,walk2}` (6)

**C. 있으면 좋음 - 쏘기 (12개)** - 쏜 직후 0.12초 동안 나온다 (들개는 쏘지 않아 없음)
- [ ] 보안관 `sheriff_{down,up,right}_shoot` (3)
- [ ] 줍줍이 `picker_{down,up,right}_shoot` (3)
- [ ] 술꾼 `drunk_{down,up,right}_shoot` (3)
- [ ] 두목 `boss_{down,up,right}_shoot` (3)

**D. 있으면 좋음 - 보안관 발차기 (3개)**
- [ ] `sheriff_{down,up,right}_kick`

**E. 선택**
- [ ] 장애물 모양 추가 `obs_rock2` `obs_rock3` 처럼 번호를 붙이면 번갈아 쓴다

합계: A 23 + B 30 + C 12 + D 3 = **68개**. 이 중 B~D 45개는 없으면 서 있는 그림으로 나오므로 마지막에 해도 된다.

**이 요청서에 없는 것** (코드가 도형으로 그리거나 다른 작업 담당): 총알·총구 불꽃·UI(체력, 실린더, 조준점)는 코드 도형, 수배 포스터 초상화·타이틀·엔딩은 `flow-screens` 작업 담당. 맞음·쓰러짐 그림은 만들지 않는다(흰 번쩍임과 별을 코드가 그린다).

## 순서 추천
1. 보안관 방향 시트 (정면은 이미 있는 Gemini 6번 기준)
2. 술집 배경 → 테이블 → 줍줍이 → 술꾼 방향 시트 (여기까지 하면 1구역이 그림으로 나온다. 게임을 켜서 크기와 시점을 먼저 확인한다)
3. 광산(배경, 바위, 들개) → 기차(배경, 상자) → 은행(배경, 기둥, 두목)
4. 보안관 걷기 → 보안관 발차기·쏘기 → 적 걷기 → 적 쏘기 (선택)
5. 그림이 모일 때마다 `prep_sprites.py` 로 `res/` 에 넣고 게임에서 확인한다.


## 1. 캐릭터 방향 시트 (3칸: 아래 · 위 · 오른쪽)

### 보안관: `sheriff_sheet.png` -> `sheriff_down/up/right.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body views of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width third of the image, none overlapping or cropped. Left = facing toward the viewer (down the screen), middle = seen from behind, facing away (up the screen), right = facing right in side view. Identical outfit, colors, proportions and size in all three, each with a soft round shadow under the feet. Image ratio 3:1.
The character: a Wild West sheriff with a tan wide-brim hat, blue shirt, dark green vest with a gold star badge, red bandana, holding a revolver.
```

### 줍줍이: `picker_sheet.png` -> `picker_down/up/right.png`
(보안관 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body views of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width third of the image, none overlapping or cropped. Left = facing toward the viewer (down the screen), middle = seen from behind, facing away (up the screen), right = facing right in side view. Identical outfit, colors, proportions and size in all three, each with a soft round shadow under the feet. Image ratio 3:1.
The character: a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture.

Same art style, line thickness and color saturation as the attached sheriff sheet.
```

### 술꾼: `drunk_sheet.png` -> `drunk_down/up/right.png`
(보안관 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body views of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width third of the image, none overlapping or cropped. Left = facing toward the viewer (down the screen), middle = seen from behind, facing away (up the screen), right = facing right in side view. Identical outfit, colors, proportions and size in all three, each with a soft round shadow under the feet. Image ratio 3:1.
The character: a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side.

Same art style, line thickness and color saturation as the attached sheriff sheet.
```

### 들개: `hound_sheet.png` -> `hound_down/up/right.png`
(보안관 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body views of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width third of the image, none overlapping or cropped. Left = facing toward the viewer (down the screen), middle = seen from behind, facing away (up the screen), right = facing right in side view. Identical outfit, colors, proportions and size in all three, each with a soft round shadow under the feet. Image ratio 3:1.
The character: a lean stray hound dog, ears back, tail visible, alert pose.

Same art style, line thickness and color saturation as the attached sheriff sheet.
```

### 두목: `boss_sheet.png` -> `boss_down/up/right.png`
(보안관 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body views of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width third of the image, none overlapping or cropped. Left = facing toward the viewer (down the screen), middle = seen from behind, facing away (up the screen), right = facing right in side view. Identical outfit, colors, proportions and size in all three, each with a soft round shadow under the feet. Image ratio 3:1.
The character: a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders.

Same art style, line thickness and color saturation as the attached sheriff sheet.
```


## 2. 동작 시트 (걷기 2장 + 쏘기 1장, 보안관은 발차기 1장 더, 들개는 쏘기 없음) - 캐릭터 5종 x 방향 3개 = 15개, 들개는 걷기만

방향 시트(1번)가 **확정된 뒤**에 만든다. 요청마다 그 캐릭터의 방향 시트를 같이 첨부한다. 서 있는 그림(1번)과 같은 시점·크기·옷이어야 한다. 이 그림이 없는 동작은 서 있는 그림으로 대신 나오므로 **필수가 아니다.** 우선순위: 보안관 걷기 > 보안관 발차기·쏘기 > 적 걷기 > 적 쏘기.

칸을 자를 때는 `--order walk1,walk2,shoot` (들개는 `walk1,walk2`, 보안관은 `walk1,walk2,shoot,kick`)로 하고 이름을 `캐릭터_방향` 으로 쓰면 `sheriff_down_walk1.png` 처럼 저장된다.

```powershell
C:\Python313\python.exe tools\split_sheet.py C:\dev\2dgp\raw_art\sheriff_down_action.png sheriff_down C:\dev\2dgp\raw_art --order walk1,walk2,shoot,kick
```

### 보안관 down: `sheriff_down_action.png` -> `sheriff_down_walk1/walk2/shoot/kick.png`
(보안관 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 4 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing toward the viewer (down the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil; kick: kicking forward with the leg raised. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 4:1.
The character: a Wild West sheriff with a tan wide-brim hat, blue shirt, dark green vest with a gold star badge, red bandana, holding a revolver.
```

### 보안관 up: `sheriff_up_action.png` -> `sheriff_up_walk1/walk2/shoot/kick.png`
(보안관 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 4 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames seen from behind, facing away (up the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil; kick: kicking forward with the leg raised. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 4:1.
The character: a Wild West sheriff with a tan wide-brim hat, blue shirt, dark green vest with a gold star badge, red bandana, holding a revolver.
```

### 보안관 right: `sheriff_right_action.png` -> `sheriff_right_walk1/walk2/shoot/kick.png`
(보안관 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 4 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing right in side view, in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil; kick: kicking forward with the leg raised. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 4:1.
The character: a Wild West sheriff with a tan wide-brim hat, blue shirt, dark green vest with a gold star badge, red bandana, holding a revolver.
```

### 줍줍이 down: `picker_down_action.png` -> `picker_down_walk1/walk2/shoot.png`
(줍줍이 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing toward the viewer (down the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture.
```

### 줍줍이 up: `picker_up_action.png` -> `picker_up_walk1/walk2/shoot.png`
(줍줍이 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames seen from behind, facing away (up the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture.
```

### 줍줍이 right: `picker_right_action.png` -> `picker_right_walk1/walk2/shoot.png`
(줍줍이 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing right in side view, in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture.
```

### 술꾼 down: `drunk_down_action.png` -> `drunk_down_walk1/walk2/shoot.png`
(술꾼 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing toward the viewer (down the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side.
```

### 술꾼 up: `drunk_up_action.png` -> `drunk_up_walk1/walk2/shoot.png`
(술꾼 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames seen from behind, facing away (up the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side.
```

### 술꾼 right: `drunk_right_action.png` -> `drunk_right_walk1/walk2/shoot.png`
(술꾼 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing right in side view, in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side.
```

### 들개 down: `hound_down_action.png` -> `hound_down_walk1/walk2.png`
(들개 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 2 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing toward the viewer (down the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 2:1.
The character: a lean stray hound dog, ears back, tail visible, alert pose.
```

### 들개 up: `hound_up_action.png` -> `hound_up_walk1/walk2.png`
(들개 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 2 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames seen from behind, facing away (up the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 2:1.
The character: a lean stray hound dog, ears back, tail visible, alert pose.
```

### 들개 right: `hound_right_action.png` -> `hound_right_walk1/walk2.png`
(들개 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 2 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing right in side view, in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 2:1.
The character: a lean stray hound dog, ears back, tail visible, alert pose.
```

### 두목 down: `boss_down_action.png` -> `boss_down_walk1/walk2/shoot.png`
(두목 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing toward the viewer (down the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders.
```

### 두목 up: `boss_up_action.png` -> `boss_up_walk1/walk2/shoot.png`
(두목 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames seen from behind, facing away (up the screen), in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders.
```

### 두목 right: `boss_right_action.png` -> `boss_right_walk1/walk2/shoot.png`
(두목 방향 시트를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
The hat brim must not hide the face: both eyes and a small neat mustache are clearly visible below the brim, with a calm, slightly stern expression, and the hat is only slightly wider than the shoulders.
A character sprite sheet with exactly 3 full-body frames of the same character in one row on a solid pure magenta (#FF00FF) background, evenly spaced, each in its own equal-width part of the image, none overlapping or cropped. All frames facing right in side view, in the same steep high-angle camera, same size and position, each with a soft round shadow under the feet. Frames from left to right: walk1: walking, right leg forward; walk2: walking, left leg forward; shoot: firing pose, arm with the gun extended and a slight recoil. Identical outfit, colors, proportions, line thickness and art style as the attached reference sheet. Image ratio 3:1.
The character: a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders.
```


## 3. 구역 배경 (1280x720, 16:9, 인물과 장애물 없는 빈 방)

가운데 넓은 놀이 공간(약 1180x620)을 비우고 벽과 소품은 가장자리에만 둔다. 캐릭터와 같은 시점이다. 배경은 마젠타가 아니라 방 전체를 그리므로 투명 처리하지 않는다.

### `bg_saloon.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
Empty Wild West saloon interior, same steep high-angle camera as the character sprites, about 65 degrees down, 16:9, 1280x720, large open empty floor in the middle with no furniture and no characters, walls and props only along the edges, dark wood plank floor, barrels and lanterns along the edges, swinging doors in the middle of the top wall.
```

### `bg_mine.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
Empty dark mine tunnel interior, same steep high-angle camera as the character sprites, about 65 degrees down, 16:9, 1280x720, large open empty floor in the middle with no furniture and no characters, walls and props only along the edges, dark rocky floor, wooden support beams and rails along the edges.
```

### `bg_train.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
Empty wooden freight train car interior, same steep high-angle camera as the character sprites, about 65 degrees down, 16:9, 1280x720, large open empty floor in the middle with no furniture and no characters, walls and props only along the edges, wooden plank floor, car walls on both long sides, a long horizontal rectangular room.
```

### `bg_bank.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
Empty bank interior, same steep high-angle camera as the character sprites, about 65 degrees down, 16:9, 1280x720, large open empty floor in the middle with no furniture and no characters, walls and props only along the edges, marble floor, teller cage bars and a vault door along the edges.
```


## 4. 장애물 (그림 한 장씩, 마젠타 배경)

판정은 사각형이라 그림이 정사각형에 가깝게 채워지게 한다. 크기는 게임이 줄이니 비율만 맞으면 된다.

### `obs_table.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
a round wooden saloon table with chairs, same steep high-angle camera as the character sprites (about 65 degrees down), same art style, filling a roughly square area, solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```

### `obs_rock.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
a lump of cave rock, same steep high-angle camera as the character sprites (about 65 degrees down), same art style, filling a roughly square area, solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```

### `obs_crate.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
a wooden freight crate, same steep high-angle camera as the character sprites (about 65 degrees down), same art style, filling a roughly square area, solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```

### `obs_pillar.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle view looking steeply down at about 65 degrees, only slightly tilted from straight overhead.
The top of the hat and head are clearly visible, the body is somewhat foreshortened, and the feet with the round shadow are visible below.
Same camera angle for every image.
No text, no logos, no watermark.
a square marble pillar seen from above, same steep high-angle camera as the character sprites (about 65 degrees down), same art style, filling a roughly square area, solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```
