# 개발 일지

AI가 만든 코드를 그대로 쓰지 않고, 기능마다 아래 순서로 확인한 뒤 커밋한다.

1. **명세:** 이번 단계에서 무엇이 되어야 하는지 정한다.
2. **검토:** 작성한 코드를 읽고 명세와 수업 구조에 맞는지 확인한다.
3. **실행:** 실제 창으로 띄워 스크린샷(`tools/shot.py`)을 남긴다.
4. **테스트:** 명세를 자동 점검(`tools/check.py`)으로 옮겨 고정 프레임(1/60초)으로 돌린다.
5. **설명:** 어떻게 동작하는지, 왜 그렇게 만들었는지 적는다.

```
C:\Python313\python.exe tools\check.py      # 자동 점검 (창 없이)
C:\Python313\python.exe tools\shot.py       # 스크린샷 (docs/shots/)
C:\Python313\python.exe main.py             # 게임 실행
```

---

## 1주차: 뼈대와 공유 총알

### 1. 프로젝트 뼈대

**명세**
- `main.py`를 실행하면 1280×720 창에 벽과 나무 바닥이 있는 빈 구역이 뜬다.
- ESC 또는 창 닫기로 종료한다.
- 수업 LEC15의 `game_framework`(모드 스택), `game_world`(레이어) 구조를 그대로 쓴다.

**검토**
- `game_framework.py`: LEC15 코드에 `frame_time`(직전 프레임 시간)만 추가했다. 이동을 프레임 수가 아니라 시간에 비례시키기 위해서다. 창을 끌다 멈춘 경우 한 번에 크게 움직이지 않도록 최대 0.05초로 자른다.
- `game_world.py`: LEC15의 레이어 관리에 충돌 쌍(`add_collision_pair`, `handle_collisions`)을 더했다. 충돌 판정은 `get_bb()` 사각형끼리 겹치는지로 본다. LEC15의 `add_oject` 오타는 `add_object`로 바로잡았다.
- `play_mode.py`: 이벤트 처리를 `dispatch(event)`로 분리했다. 자동 점검이 실제 게임과 같은 경로로 입력을 넣기 위해서다.
- pico2d 1.5.1의 `draw_rectangle(..., filled=True)`로 색을 채운 도형을 그릴 수 있어서, 1~3주차는 이미지 파일 없이 도형으로 개발한다.

**실행**
- `main.py`를 3초 동안 실행해 실시간 루프가 오류 없이 도는 것을 확인했다.
- 스크린샷: `docs/shots/w1_1_skeleton.png`

**테스트** (`tools/check.py`)
- `skeleton_runs_and_esc_quits`: 120프레임 동안 오류 없이 돌고, ESC 입력 시 `game_framework.running`이 꺼진다.

**설명**
- 자동 점검은 SDL 더미 화면으로 창 없이 돈다. 더미 화면에서는 픽셀을 읽을 수 없어서 스크린샷만 실제 창으로 찍는다.
- 상태 머신은 수업(LEC12~15)처럼 `transitions` 라이브러리의 `Machine`을 쓴다. PRD 15-2의 `state_machine.py`는 따로 만들지 않는다.
