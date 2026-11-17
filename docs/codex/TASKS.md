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
| T01 | 주인공 마스터 v3 (음영·디테일 강화, 키 123px) | [T01_hero_v3.md](tasks/T01_hero_v3.md) | - | done (v3b 합격) / 재제작 보류 (걷기와 비율이 달라 v3b 유지, `reports/T01_remake.md`) |
| T02 | 적 3종 마스터 v3 (슬럼 폐인, 고철 투척병, 중장갑 간수) | [T02_enemies_a.md](tasks/T02_enemies_a.md) | T01 | done (v3 합격) / 재제작 done·게임 적용 2026-11-16 (`reports/T02_remake.md`) |
| T03 | 적·보스 3종 마스터 v3 (안개 사냥개, 크래셔, 아크) | [T03_enemies_b.md](tasks/T03_enemies_b.md) | T01 | done·게임 적용 2026-11-16 (`reports/T03_remake.md`) |
| T04 | 주인공 걷기 프레임 (2×2 시트 4프레임) | [T04_hero_walk.md](tasks/T04_hero_walk.md) | T01 | done·게임 적용 2026-11-16 |
| T05 | 주인공 대기·공격·피격·점프 프레임 | [T05_hero_actions.md](tasks/T05_hero_actions.md) | T04 | done (대기·피격·점프 적용, 공격은 빈손이라 T07로 재작업) |
| T06 | 배경판 3종 (감옥 복도, 철골 공장, 감시자의 탑) | [T06_backgrounds.md](tasks/T06_backgrounds.md) | - | done·게임 적용 2026-11-17 (원경 `far_<테마>.png`의 바탕으로 사용) |
| T07 | 주인공 철파이프 공격 (5방향 × 3프레임) | [T07_hero_pipe_attack.md](tasks/T07_hero_pipe_attack.md) | T05 | done·게임 적용 2026-11-16 (파이프가 가늘어 필요하면 재작업) |
| T08 | 주인공 대시·내려찍기·사망 포즈 | [T08_hero_dash_plunge_death.md](tasks/T08_hero_dash_plunge_death.md) | T05 | done·게임 적용 2026-11-16 |
| T09 | 슬럼·투척병 애니메이션 (걷기·공격·피격·던지기) | [T09_enemy_anims_a.md](tasks/T09_enemy_anims_a.md) | T02 | done·게임 적용 2026-11-16 |
| T10 | 보스 크래셔 애니메이션 (대기·찍기·돌진·도약·피격) | [T10_boss_crasher_anims.md](tasks/T10_boss_crasher_anims.md) | T03 | done·게임 적용 2026-11-16 |
| T11 | 사망·엔딩 화면 일러스트 2장 | [T11_end_screens.md](tasks/T11_end_screens.md) | - | done·게임 적용 2026-11-16 |
| T12 | 간수·사냥개 애니메이션 (기술별 동작, 아크는 보류) | [T12_guard_hound_ark_anims.md](tasks/T12_guard_hound_ark_anims.md) | - | done·게임 적용 2026-11-17 (아크는 보류) |
| T13 | 아이템 아이콘 10종 (48×48) | [T13_item_icons.md](tasks/T13_item_icons.md) | - | done·게임 적용 2026-11-17 (`assets/ui/icon_*.png` 교체) |
| T14 | 진열대·문·상호작용 소품 6종 | [T14_props_pedestal_door.md](tasks/T14_props_pedestal_door.md) | - | done·진열대 3종 적용 2026-11-17 (문 3종은 미적용: 방 타일 세트의 테마별 문틀을 쓴다) |
| T15 | 철파이프 굵게 재작업 (T07 개선, 5방향) | [T15_pipe_thicker.md](tasks/T15_pipe_thicker.md) | T07 | done·게임 적용 2026-11-17 (기준점 갱신) |
| T16 | 제목 화면 일러스트 | [T16_title_screen.md](tasks/T16_title_screen.md) | - | done·게임 적용 2026-11-17 (`assets/backgrounds/screen_title.png`) |
| T17 | 주인공 걷기 8프레임 (몸통 고정, 먼 다리 어둡게) | [T17_hero_walk_8.md](tasks/T17_hero_walk_8.md) | T04 | done·게임 적용 2026-11-17 (v4b 8장, 달리기는 T19) |
| T18 | 주인공 휘두르기 사이 프레임 (방향마다 3장 → 5장, 수평부터) | [T18_hero_swing_inbetween.md](tasks/T18_hero_swing_inbetween.md) | T15 | done·게임 적용 2026-11-18 (5장, 맞히면 타격 자세부터) |
| T19 | 주인공 달리기 8프레임 + 출발·멈춤·방향 전환 5장 | [T19_hero_run_8.md](tasks/T19_hero_run_8.md) | - | done·게임 적용 2026-11-18 (조준 쪽 달리기, 뒷걸음은 T17 걷기 역재생) |
| T20 | 최종 보스 아크 애니메이션 (패턴 5종 예고·실행, 이동·순간이동·피격, 페이즈·사망) 23장 | [T20_boss_ark_anims.md](tasks/T20_boss_ark_anims.md) | T03 | done·그림 적용 2026-11-18 (23장 등록, 보스 코드는 Claude Code 작업) |

- 앞 작업이 `done`이 되면 Claude Code가 뒤 작업을 `ready`로 바꾼다. (Codex는 `blocked` 작업을 시작하지 않는다.)
- **목표 키(px)**: 화면 1920×1080, 타일 60px 기준 1.5배. 주인공 123, 슬럼 117, 투척병 123, 간수 135, 사냥개 81, 아크 159, 크래셔 195. 값은 `tools/finish_character.py`가 알고 있다.
- **추천 순서(2026-11-18): 대기 중인 작업 없음.** (T17~T20 완료) 이동 속도(초당 480px = 키의 3.9배)가 걷기가 아니라 달리기 속도라, 늘 화면에 나오는 이동 모션을 달리기로 바꾸는 T19가 휘두르기 사이 프레임(T18)보다 먼저다.
- (그 전 추천: T12 → T17 → T18.) 사용자가 걷기·공격 모션이 부자연스럽다고 했다. 정지 그림 한 장으로 미끄러지는 사냥개·간수가 가장 눈에 띄고, 그다음 주인공 걷기, 휘두르기 순이다. 지금은 게임 코드 보정(`src/sprites.py` `SHIFT`, 공격 중 감속·내딛기)으로 메우고 있다.
- (그 전 순서: T13 → T14 → T15 → T16, 모두 완료·적용)
- (이전 순서: T07 → T09 → T10 → T08 → T11) (공격 포즈와 적 애니메이션이 게임 체감에 가장 크다). T06 배경은 사용자 검토 대기.
- 한 번에 한 작업만 실행한다 (이미지 생성 사용량, 파일 충돌 방지).
