# Codex 작업 큐 (TASKS)

Codex가 맡는 이미지 에셋 작업 목록이다. 프롬프트는 작업마다 `docs/codex/tasks/`의 파일에 모두 적혀 있어서, **사용자가 프롬프트를 직접 쓸 필요가 없다.**

## Codex에 입력할 말 (이것만 붙여 넣으면 된다)
```text
docs/codex/TASKS.md를 읽고, 상태가 ready인 첫 작업을 docs/codex/COMMON.md 규칙대로 끝까지 진행해줘.
```
특정 작업을 시키려면: `docs/codex/TASKS.md를 읽고 T01을 docs/codex/COMMON.md 규칙대로 진행해줘.`

## 작업 끝난 뒤 Claude Code에게 할 말
```text
T01 결과를 검토해줘
```
Claude Code가 `docs/codex/reports/T01.md`와 결과 파일을 측정·비교해서 합격이면 `done`으로 바꾸고 커밋·푸시한다. 불합격이면 어디를 고칠지 해당 작업 파일을 수정한다.

## 상태 값
`ready`(시작 가능) → `in_progress`(Codex 작업 중) → `review`(Codex 끝, 검토 대기) → `done`(합격) / `blocked`(앞 작업이 끝나야 함) / `rework`(불합격, 작업 파일 수정 후 다시 ready)

## 작업 목록
| ID | 작업 | 파일 | 앞 작업 | 상태 |
|---|---|---|---|---|
| T01 | 주인공 마스터 v3 (음영·디테일 강화, 키 123px) | [T01_hero_v3.md](tasks/T01_hero_v3.md) | - | done (v3b 합격, 결과 `n09_v3b_idle.png`) |
| T02 | 적 3종 마스터 v3 (슬럼 폐인, 고철 투척병, 중장갑 간수) | [T02_enemies_a.md](tasks/T02_enemies_a.md) | T01 | done (합격) |
| T03 | 적·보스 3종 마스터 v3 (안개 사냥개, 크래셔, 아크) | [T03_enemies_b.md](tasks/T03_enemies_b.md) | T01 | ready |
| T04 | 주인공 걷기 프레임 (2×2 시트 4프레임) | [T04_hero_walk.md](tasks/T04_hero_walk.md) | T01 | ready |
| T05 | 주인공 대기·공격·피격·점프 프레임 | [T05_hero_actions.md](tasks/T05_hero_actions.md) | T04 | blocked |
| T06 | 배경판 3종 (감옥 복도, 철골 공장, 감시자의 탑) | [T06_backgrounds.md](tasks/T06_backgrounds.md) | - | ready |

- 앞 작업이 `done`이 되면 Claude Code가 뒤 작업을 `ready`로 바꾼다. (Codex는 `blocked` 작업을 시작하지 않는다.)
- **목표 키(px)**: 화면 1920×1080, 타일 60px 기준 1.5배. 주인공 123, 슬럼 117, 투척병 123, 간수 135, 사냥개 81, 아크 159, 크래셔 195. 값은 `tools/finish_character.py`가 알고 있다.
- 한 번에 한 작업만 실행한다 (이미지 생성 사용량, 파일 충돌 방지).
