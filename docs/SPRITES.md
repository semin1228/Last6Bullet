# 그림 넣는 법 (그림 교체 코드, 4주차)

`res/` 에 PNG 를 넣으면 게임이 이름으로 읽어 쓰고, 없는 그림은 지금의 도형으로 그린다 (`sprites.py`). 코드를 고칠 필요가 없다.
어떤 그림을 어떤 프롬프트로 만드는지는 `GEMINI_IMAGE_PROMPTS.md` 를 본다. 여기는 코드가 그림을 쓰는 규칙만 적는다.

## 파일 이름 규칙
| 그림 | 파일 | 규칙 |
|---|---|---|
| 캐릭터 5종 (`sheriff` `picker` `drunk` `hound` `boss`) | `NAME_down.png` `NAME_up.png` `NAME_right.png` | 세 장이 **모두** 있어야 쓴다. 조준(바라보는) 방향에 가까운 그림을 고르고, 왼쪽은 오른쪽을 좌우 반전한다. |
| 같은 캐릭터 | `NAME.png` (한 장) | 세 장이 없으면 이것을 오른쪽을 보는 그림으로 보고 각도만큼 회전해서 그린다. |
| 보안관 동작 (선택) | `sheriff_right_run1.png` `sheriff_right_run2.png` `sheriff_right_kick.png` | 오른쪽·왼쪽을 볼 때만 쓴다. 달리기는 두 장을 0.15초마다 번갈아, 발차기 중에는 kick. 발차기 그림이 없으면 기존 차는 발 선이 나온다. |
| 장애물 | `obs_table.png` (술집) `obs_rock.png` (광산) `obs_crate.png` (기차) `obs_pillar.png` (은행) | 장애물 사각형(판정)과 같은 크기로 늘여서 그린다. 모양이 여러 개면 `obs_rock2.png`, `obs_rock3.png` 처럼 번호를 붙이면 번갈아 쓴다. |
| 배경 | `bg_saloon.png` `bg_mine.png` `bg_train.png` `bg_bank.png` | 1280x720 으로 그린다. 광산은 그림을 어둡게 깔고 랜턴 빛 반경 안만 밝게 보인다. 기차는 덜컹 예고 때 왼쪽 위험 띠가 깜빡이고 짐받이 턱 선이 그림 위에 늘 그려진다. |

- 위·아래·오른쪽 그림이 모두 있어도 파일이 하나라도 빠진 캐릭터는 한 장 `NAME.png`, 그것도 없으면 도형으로 그려진다.
- 그림이 화면에 그려지는 크기는 판정(반지름)과 별개이고 `config.py` 의 `SPRITE_SIZE` 에서 캐릭터별로 조절한다 (보안관 64, 줍줍이 56, 술꾼 60, 들개 56, 두목 96).
- 그림은 보이기만 한다. 판정, 총구 불꽃, 총알 방향은 지금처럼 각도로 계산한다.
- 경로와 파일 이름에 한글·공백을 쓰지 않는다.

## 마젠타 배경을 투명으로 바꾸기
Gemini 그림은 마젠타(#FF00FF) 단색 배경이라 투명 PNG 로 바꿔서 `res/` 에 넣는다. 원본은 그대로 둔다.

```powershell
C:\Python313\python.exe tools\prep_sprites.py 받은그림폴더 res --size 128
```

- 마젠타와 가까운 색은 투명으로, 경계는 반투명으로 하고 분홍 번짐을 줄인다. 가장자리가 지저분하면 `--tol 110` 처럼 올려 본다.
- `--size 128` 은 캐릭터와 장애물을 128x128 로 줄인다 (생략하면 그대로). `bg_`·`poster_` 로 시작하는 파일은 투명 처리하지 않고, 배경은 1280x720 으로 맞춘다.
- Pillow 가 필요하다 (`pip install pillow`). 게임 본체는 Pillow 없이 돈다.
- JPG 로 받았어도 PNG 로 저장된다.

## 확인
- 게임을 켜서 본다: `C:\Python313\python.exe main.py`.
- 그림 위치나 크기가 어색하면 `config.py` 의 `SPRITE_SIZE` 만 바꾼다.
