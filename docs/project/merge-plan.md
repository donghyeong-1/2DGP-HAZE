# 병합 계획: PR #1~#4를 main에 합치는 순서와 충돌 해결법

작성: 스레드 3(PR #2), 2026-11-25 새벽. 조정자 요청으로 **로컬에서만** 네 브랜치를 main 위에 차례로 합쳐 봤다(푸시하지 않음).
기준: main `4ed8871`, #1 `d4bded7`, #2 `401a082`(이 문서 커밋 전), #3 `7ca8b20`, #4 `20ac9a9` (2026-11-25 05:45 KST에 받은 것). 그 전 머리 커밋으로도 두 번 해 봤고 결과가 같았다.

## 한 줄 요약
**#2 → #4 → #1 → #3** 순서로 병합한다. 충돌은 두 번(#1, #3) 나고, 모두 **파일 맨 끝에 각자 덧붙인 줄**이라 **양쪽을 모두 남기면** 된다.
네 개를 다 합친 상태에서 전체 테스트 76개 파일 789개 통과, 픽셀 검사 8개 통과, 화면 없는 실제 창으로 한 판 흐름(타이틀 → 은신처 → 구역 1 문지기 → 구역 2 크래셔 → 구역 3 아크·헤이즈 심장 → 탈출 화면 → 크레딧 → 타이틀)을 끝까지 돌렸다.

## PR과 브랜치
| PR | 스레드 | 브랜치 | 내용 |
|---|---|---|---|
| #1 | 밸런스 | `claude/project-thread-dbbb2t` | 밸런스 기준 다시 저장, 구역 시뮬레이터, 초보자 모드 |
| #2 | 증강·버그 훑기 | `claude/project-thread-7i2rva` | 합성 증강 6종, 기본 증강 손질, 버그 훑기(튕김 4곳), 일시정지 형태 목록 |
| #3 | NPC·글·작은 기능 | `claude/project-thread-ny8m1k` | NPC 대사, README·발표 초안·글자 검토, 화면 밖 적 화살표, 황금방 형태 진열대, 제출 준비 |
| #4 | 보스 | `claude/project-thread-x0ifu3` | 보스 등장씬·대사, 구역 1 중간 보스 문지기, 임팩트 프레임 |

## 둘씩 겹쳐 본 결과 (`git merge-tree`)
| | #1 | #2 | #3 | #4 |
|---|---|---|---|---|
| #1 | | 충돌 없음 | `docs/ASSETS.md` | `docs/ASSETS.md`, `src/config.py` |
| #2 | | | 충돌 없음 | 충돌 없음 |
| #3 | | | | `docs/ASSETS.md`, `docs/changes_from_plan.md` |

두 PR이 같이 고쳤지만 git이 알아서 합친 파일(충돌 없음, 합친 뒤 테스트 통과):
`src/ark.py`(#2·#4), `src/weapon.py`(#2·#4), `src/ui.py`(#2·#3·#4), `src/pause_mode.py`(#2·#3), `src/player.py`(#1·#2), `src/play_mode.py`(#3·#4), `src/stage.py`(#3·#4), `src/killers.py`(#3·#4), `tests/test_stage.py`(#3·#4).
#3이 고친 `src/room.py`·`src/pedestal.py`는 다른 PR이 건드리지 않았다.

## 추천 순서와 이유
1. **#2** (증강·버그 훑기): 누구와도 충돌하지 않는다. 먼저 넣으면 뒤의 PR에 아무 영향이 없다. 아크 2페이즈 튕김 수정(아래)도 들어 있어 먼저 넣는 편이 안전하다.
2. **#4** (보스): #2와 충돌 없음. 게임 흐름(관문 문지기, 보스 등장씬)이 바뀌는 PR이라 일찍 넣는다.
3. **#1** (밸런스): `config.py` 끝과 `ASSETS.md` 끝에서 #4와 충돌 → 양쪽 남기기. 밸런스 스레드도 #4+#1을 합쳐 보고 '#4 먼저, #1 다음'을 추천했다(같은 두 곳만 충돌).
4. **#3** (NPC·글): 가장 많은 파일을 고쳤고 발표 초안·제출 체크리스트가 다른 PR 내용을 보고 쓴 것이라 마지막. `ASSETS.md` 끝과 `changes_from_plan.md` 끝에서 충돌 → 양쪽 남기기.

어느 순서로 해도 충돌은 두 번 이상 난다(#1·#3·#4가 서로 `ASSETS.md` 끝을 고쳤다). 코드 파일 충돌은 `config.py` 끝 한 곳뿐이다.

## 충돌 해결법
### GitHub 화면에서
1. #2를 병합한다(Merge pull request).
2. #4를 병합한다.
3. #1에 "This branch has conflicts" → **Resolve conflicts**.
   - `src/config.py` 맨 끝: `<<<<<<< ` 와 `=======`, `>>>>>>> ` 세 줄만 지우고 **두 블록을 모두 남긴다**. 보스 블록(`BOSS_INTRO`, `GATEKEEPER`, `ENEMY_STATS['gatekeeper']` …) 다음에 빈 줄 하나, 그다음 초보자 모드 블록(`EASY_*`). 순서는 바뀌어도 동작은 같다.
   - `docs/ASSETS.md` 맨 끝: 표시 세 줄만 지우고 양쪽 줄(문지기 그림, 증기 분출 다시 굽기)을 모두 남긴다.
   - Mark as resolved → Commit merge → 병합.
4. #3도 같은 방법: `docs/ASSETS.md`(화면 밖 화살표 줄들과 이미지 도구 표), `docs/changes_from_plan.md`(NPC 대사 줄) 모두 양쪽 남기기.

### 로컬 Claude Code로 (명령)
```
git checkout main && git pull
git merge --no-ff origin/claude/project-thread-7i2rva      # #2
git merge --no-ff origin/claude/project-thread-x0ifu3      # #4
git merge --no-ff origin/claude/project-thread-dbbb2t      # #1: config.py, ASSETS.md 충돌 -> 양쪽 남기고 git add, git commit
git merge --no-ff origin/claude/project-thread-ny8m1k      # #3: ASSETS.md, changes_from_plan.md 충돌 -> 양쪽 남기고 git add, git commit
grep -rn "^<<<<<<<\|^>>>>>>>" src docs tests tools data   # 남은 표시가 없어야 한다
PYTHONUTF8=1 python tests/run_all.py && python tests/test_pixel_assets.py
```
양쪽 남기기에서 지울 것은 표시 세 줄뿐이다. 내용 줄은 하나도 지우지 않는다.

## 합친 상태에서 확인한 것
- 전체 테스트: 76개 파일 789개 통과 (`PYTHONUTF8=1 python tests/run_all.py`), 픽셀 검사 8개 통과.
- 한 판 흐름(화면 없는 실제 창, 모드 스택 그대로, 봇이 싸움, 체력은 가득·게이지 40 아래로 안 내려가게):
  - 타이틀에서 Enter → 은신처 → 출발 문 → 구역 1 → 관문: **문지기** 등장씬, 처치 → 구역 2
  - 구역 2 보스방: **크래셔** 등장씬, 처치 → 구역 3
  - 구역 3 보스방: **아크** 등장씬, 2·3페이즈, 처치 → **헤이즈 심장**(봇이 150초 안에 못 깨 체력을 1로 낮춤) → 탈출 화면 → 크레딧 → 타이틀 → 은신처
  - 튕김 0 (고치기 전에는 아크 2페이즈에서 튕겼다, 아래). 그림: `/mnt/project-files/merge-plan/한판흐름.png`
  - 방 사이 길은 건너뛰고 테스트 모드 바로가기(F9와 같은 함수)로 끝 방에 갔다
- 밸런스 비교(`tools/balance_sim.py --compare tools/balance_base.json`, #1이 저장한 기준과 비교): 승률이 바뀐 줄은 셋(사냥개·쌍권총 0.5→1.0, 무당·건틀릿 0.9→1.0, 아크·쌍권총 1.0→0.9), 수치만 조금 바뀐 줄이 39개.
  브랜치마다 따로 재 보니 **차이는 모두 #4(보스)에서 온다**(#2·#3은 차이 0, #1은 자기 기준과 4줄: 쥐 처치 시간 0.1초). #4의 임팩트 프레임(멈춤)이 시간 계산을 바꾼 것으로 보인다.
  → **네 PR을 다 병합한 뒤 밸런스 기준을 다시 저장**한다: `python tools/balance_sim.py --save tools/balance_base.json` (밸런스 스레드에 알림)

## 이 연습에서 찾아 고친 것 (PR #2에 커밋)
- **최종 보스 아크가 2페이즈의 '농도 띠'·'결정 벽' 패턴을 쓰는 순간 게임이 꺼졌다.** 두 패턴의 몸 그림(`boss_ark_bands_*`, `boss_ark_crystals_*`)이 없고 예고 빛 색도 없었다. **main에도 있던 문제**다(네 PR 어느 것도 원인이 아니다).
  비슷한 자세(띠 → 장판, 결정 벽 → 과충전)를 빌리고 색 둘을 넣었다. `tests/test_ark_frames.py`(먼저 써서 실패 확인).
  전용 그림이 필요하면 Codex 작업서를 새로 써야 한다(추천안으로 정함: 지금은 빌린 자세로 둔다).

## 병합한 뒤 할 일
- 각 스레드 보고서에 적어 둔 `PROGRESS.md` 작업 로그 줄과 `DECISIONS.md` 줄을 옮긴다(스레드 규칙상 PROGRESS.md는 아무도 고치지 않았다):
  `docs/project/balance.md`(#1), `day7-augments.md`·`bug-sweep.md`(#2), `v8-day6-npc.md`(#3), `day6-boss.md`(#4), 이 문서.
- `docs/ASSETS.md` 맨 끝 표의 `(빈칸: 확인 필요)`는 사용자가 계정 화면에서 채운다(#3).

## 확인하지 못한 것
- 사람 손으로 한 판(손맛, 소리). 흐름 확인은 봇과 체력 고정으로 했다.
- 다른 스레드가 이 문서를 쓴 뒤에 더 커밋하면 위 결과가 달라질 수 있다. 맨 위 기준 커밋과 PR 머리 커밋이 같은지 본다.
