# 코드 구조 정리 설계안 (2026-11-25, 안 A 승인·구현 완료)

CLAUDE.md 남은 일 2번. 동작(규칙·수치·난이도)은 바꾸지 않는 구조 변경만 다룬다. 아래 수치는 모두 이 브랜치(main 302d5e1 기준)에서 Grep과 `wc -l`로 센 값이다. 실행 시간(check.py 약 40초)도 쟀다.

## 1. 측정 결과

| 문제 | 실제 규모 | 판단 |
|---|---|---|
| `tools/check.py` 길다 | 2483줄, 테스트 110개, 구역 머리글 17개(1~18장 번호). 테스트가 아닌 도우미(`fresh`, `place`, `aim`, `run_until` 등)가 중간중간 섞여 있다 | **나눌 가치 있음**: 그래픽 주차에 테스트가 더 붙고, 읽을 때마다 큰 파일을 훑는 비용이 든다 |
| 함수 안 import | 게임 코드 10줄(줄 번호는 `grep` 결과: `drunk` 1, `duel_mode` 1, `picker` 1, `play_mode` 3, `player` 2, `train_zone` 2). `tools/check.py` 187개, `sim.py` 10, `shot.py` 44, `record.py` 19 | 진짜 순환은 **`play_mode`↔`duel_mode`, `play_mode`↔`gameover_mode` 두 쌍뿐**(2줄). 나머지 게임 코드 8줄은 맨 위로 올려도 순환이 없다(import 목록을 읽어 확인, 올린 뒤 실행으로 최종 확인 필요). `check.py`의 187개는 창 없이 도는 환경변수(`SDL_VIDEODRIVER`)를 `open_game` 안에서 설정해서 생긴 습관일 가능성이 높다(추측) |
| `play_mode` 전역 변수 | `zone, player, ledger, enemies, zone_index` 5개가 모듈 전역. 쓰는 곳: `duel_mode` 2곳, `gameover_mode` 2곳, `tools/bot_measure.py` 8곳, `check.py` 222곳(`pm.player` 등) | **하지 않는 편이 낫다**: 수업(LEC) 모드 패턴이 모듈 전역이고 과제 맥락에 맞다. 클래스로 바꾸면 테스트 약 230곳을 고쳐야 하는데 얻는 것은 없다(상태가 하나뿐). 그래픽 작업과도 충돌한다 |

## 2. 안

### 안 A (추천): check.py 분리 + import 정리, 전역은 그대로
1. **import 정리** (먼저, 작은 커밋): 게임 코드 함수 안 import 8줄을 맨 위로. `play_mode`↔`duel_mode`/`gameover_mode` 순환 2쌍은 그대로 두되 "왜 안에 있는지" 주석이 이미 있으므로 유지. `sim.py`가 import 시점에 `SDL_VIDEODRIVER`를 설정하게 해서 `check.py`의 함수 안 import(`play_mode`, `config`, `game_framework`, `pico2d` 등)도 맨 위로.
2. **check.py 분리**: `tools/check.py`는 실행기(통과·실패 출력, `--window`)로 남기고, 테스트를 `tools/checks/` 아래로 장 단위로 옮긴다. 후보: 기본(1~6장, 약 790줄) / 2주차 적(8~9장, 약 880줄) / 2주차 구역(10~12장, 약 360줄) / 3주차(15~18장, 약 430줄). 공용 도우미는 `tools/checks/common.py`. **실행 순서와 110개를 그대로** 유지한다(순서에 기대는 상태가 있을 수 있어 한 번 돌려 비교).
3. 문서: PRD 15-2 파일 구성 절의 `tools/` 줄과 `CLAUDE.md`를 갱신.

위험: 도우미가 파일 중간에 있어 분리하다 빠뜨리면 NameError(실행하면 바로 드러남). 그래픽 작업은 주로 `res/`, `hud.py`, `effect.py`, 각 `draw()`를 건드리므로 `tools/checks/`와 겹치지 않는다. 새 테스트는 해당 장 파일에 넣으면 된다. `shot.py`, `record.py`, `bot_measure.py`는 그대로 `import sim`/`play_mode` 를 쓰므로 영향 없음(`sim.py` 변경은 환경변수 설정 시점뿐이라 `shot.py --window` 같은 창 모드가 깨지지 않는지 확인).

### 안 B: import 정리만
안 A의 1번만. 30분 이내, 위험 최소. check.py는 2483줄 그대로.

### 안 C (비추천): A + play_mode 전역을 객체로
`play_mode.zone` 같은 전역을 `Game` 객체 하나로 묶기. 테스트 222곳과 `duel_mode`, `gameover_mode`, `bot_measure.py`를 모두 고쳐야 하고 그래픽 작업과 충돌하며 게임 동작 이득이 없다. 수업 패턴에서도 벗어난다.

## 3. 안 하는 것
- `play_mode` 전역 정리 (위 이유). 대신 파일 맨 위 전역 선언 옆에 "모드 상태는 수업 패턴대로 모듈 전역" 한 줄 주석만 추가할 수 있다.
- `shot.py`(530줄), `record.py`는 한 도구 한 파일이라 그대로.
- 파일 이름·위치를 바꾸는 큰 이동(게임 모듈을 패키지로 묶기 등): 그래픽 작업과 충돌.

## 4. 검증 계획 (구현 시)
- 정리 전 기준: `check.py` 110/110 통과(이미 측정, 약 40초). `bot_measure.py 2` 정리 전 값을 기록해 두고 정리 뒤 같은 값인지 비교(같은 시드 여부는 실행해서 확인).
- 커밋마다 `check.py` 110개 + `main.py` 시작 화면과 1구역 진입(`tools/shot.py`) 확인.
- 확인 못 하는 것: 직접 플레이 느낌(구조 변경이라 대상 아님).

## 5. 구현 결과 (2026-11-25)
- 안 A로 구현. 정리 전후 `check.py` 110/110, 테스트 이름과 실행 순서 동일, `bot_measure.py 2` 출력 동일(시드 `1000+k` 고정이라 두 번 돌려 같음을 먼저 확인한 뒤 비교).
- 추측 정정: `check.py`의 함수 안 import 187개는 `SDL_VIDEODRIVER` 때문이 아니었다. SDL 초기화는 `open_canvas()`에서 하므로 import 시점과 무관했고, `sim`을 먼저 불러 경로만 잡으면 맨 위에서 불러도 된다. 그래서 `sim.py`는 고치지 않았다.
- `sim.py`(10개), `shot.py`(44개), `record.py`(19개)의 함수 안 import는 승인 범위 밖이라 그대로 둠(필요하면 다음에).
- 확인: `shot.py` 전체 장면 저장(창 모드), `main.py` 6초 실행에서 오류 없음. 직접 플레이는 하지 않았다.
