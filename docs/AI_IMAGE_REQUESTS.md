# AI 이미지 요청서 (복사해서 붙여 넣기)

Gemini, ChatGPT 같은 이미지 생성 AI 대화창에 아래 요청을 **위에서부터 순서대로** 하나씩 붙여 넣는다. 각 칸의 코드 블록 전체가 한 번의 요청이다 (스타일 문단이 이미 들어 있다).
같은 대화창에서 이어서 만들면 스타일이 더 잘 맞는다. 새 대화로 시작하면 스타일 문단이 이미 요청마다 들어 있으니 그대로 붙이면 된다.

## 규칙
- 받은 그림은 **칸 제목의 파일 이름**으로 저장한다 (예: `sheriff_down.png`). 파일 이름과 경로에 한글·공백을 쓰지 않는다.
- 배경이 마젠타(#FF00FF) 단색인 그림은 `tools\prep_sprites.py` 가 투명으로 바꾼다. 배경 그림(`bg_*`)은 그대로 쓴다. 자세한 것은 `docs/SPRITES.md`.
- 캐릭터는 `_down` 을 **먼저** 마음에 들 때까지 만든다. 그다음 `_up`, `_right` 를 요청할 때 **`_down` 그림을 같이 첨부**한다 (첨부할 수 없는 대화창이면 요청만 붙이고, 여러 번 뽑아 가장 비슷한 것을 고른다).
- 마지막에 세 방향이 같은 캐릭터로 보이는지(모자, 옷 색, 몸 비율) 나란히 놓고 본다. 오른쪽 그림이 정확히 오른쪽을 보는지, 배경에 장애물·사람이 없는지, 글자·워터마크가 없는지도 본다.
- 크기가 달라도(AI가 512x512 를 못 지키는 경우가 많다) 비율만 맞으면 된다. 크기는 `prep_sprites.py --size` 로 줄인다.
- 순서 추천: 보안관 3장 → 술집 배경 → 테이블 → 줍줍이 → 나머지. 일부만 있어도 게임이 돈다 (없는 그림은 도형으로 나온다).


## 캐릭터 (방향별)

### `sheriff_down.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a Wild West sheriff with a tan wide-brim hat, blue shirt, brown vest with a star badge, holding a revolver, facing toward the viewer (down the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
```

### `sheriff_up.png`
(`sheriff_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a Wild West sheriff with a tan wide-brim hat, blue shirt, brown vest with a star badge, holding a revolver, seen from behind, facing away (up the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `sheriff_right.png`
(`sheriff_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a Wild West sheriff with a tan wide-brim hat, blue shirt, brown vest with a star badge, holding a revolver, facing to the right in side view, standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `picker_down.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture, facing toward the viewer (down the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
```

### `picker_up.png`
(`picker_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture, seen from behind, facing away (up the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `picker_right.png`
(`picker_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a small scrappy bandit with a flat cap and a sack over the shoulder, crouched posture, facing to the right in side view, standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `drunk_down.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side, facing toward the viewer (down the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
```

### `drunk_up.png`
(`drunk_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side, seen from behind, facing away (up the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `drunk_right.png`
(`drunk_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a drunk cowboy in a stained green vest holding a whiskey bottle, leaning to one side, facing to the right in side view, standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `hound_down.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a lean stray hound dog, ears back, tail visible, alert pose, facing toward the viewer (down the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
```

### `hound_up.png`
(`hound_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a lean stray hound dog, ears back, tail visible, alert pose, seen from behind, facing away (up the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `hound_right.png`
(`hound_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a lean stray hound dog, ears back, tail visible, alert pose, facing to the right in side view, standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `boss_down.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders, facing toward the viewer (down the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
```

### `boss_up.png`
(`boss_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders, seen from behind, facing away (up the screen), standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```

### `boss_right.png`
(`boss_down.png` 를 같이 첨부)

```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Full-body game character sprite of a large outlaw boss in a long dark red coat and black wide-brim hat, two revolvers at the belt, broad shoulders, facing to the right in side view, standing, with a soft round shadow under the feet,
centered, solid pure magenta (#FF00FF) background, 512x512.
Use the attached image as the exact character design reference: same outfit, colors, proportions and art style.
```


## 구역 배경 (1280x720, 16:9)

### `bg_saloon.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Empty Wild West saloon interior, high-angle top-down view almost straight down, 16:9, 1280x720,
large open empty floor in the middle with no furniture and no characters, walls and props only along the edges,
dark wood plank floor, barrels and lanterns along the edges, swinging doors in the middle of the top wall.
```

### `bg_mine.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Empty dark mine tunnel interior, high-angle top-down view almost straight down, 16:9, 1280x720,
large open empty floor in the middle with no furniture and no characters, walls and props only along the edges,
dark rocky floor, wooden support beams and rails along the edges.
```

### `bg_train.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Empty wooden freight train car interior, high-angle top-down view almost straight down, 16:9, 1280x720,
large open empty floor in the middle with no furniture and no characters, walls and props only along the edges,
wooden plank floor, car walls on both long sides, a long horizontal rectangular room.
```

### `bg_bank.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
Empty bank interior, high-angle top-down view almost straight down, 16:9, 1280x720,
large open empty floor in the middle with no furniture and no characters, walls and props only along the edges,
marble floor, teller cage bars and a vault door along the edges.
```


## 장애물

### `obs_table.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
a round wooden saloon table with chairs, high-angle top-down view almost straight down, same art style, filling a roughly square area,
solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```

### `obs_rock.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
a lump of cave rock, high-angle top-down view almost straight down, same art style, filling a roughly square area,
solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```

### `obs_crate.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
a wooden freight crate, high-angle top-down view almost straight down, same art style, filling a roughly square area,
solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```

### `obs_pillar.png`
```
Style: clean 2D cartoon game art, like a polished indie mobile game. Thick, smooth, dark brown-black outlines
around every object. Flat colors with simple soft shading and a small highlight, no realistic texture, no painterly
brush strokes, no gritty noise. Warm cozy lantern lighting. Wild West saloon theme.
Camera: high-angle top-down, looking down from above with only a slight tilt, almost straight down.
Characters are chibi-proportioned (big head and hat, small body), with a soft round dark shadow under the feet.
Palette: dark wood plank brown (#5a3a22 to #8a5a35), warm beige walls, lantern orange glow, tan hat, dusty blue shirt,
dark green vest, red bandana, dark charcoal trousers. Consistent look across every image.
No text, no logos, no watermark.
a square marble pillar seen from above, high-angle top-down view almost straight down, same art style, filling a roughly square area,
solid pure magenta (#FF00FF) background, soft shadow underneath, 512x512.
```
