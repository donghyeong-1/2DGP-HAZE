# Gemini 작업 목록

사용자가 Gemini에게 이렇게 말하면 된다:

```
docs/gemini/TASKS.md를 읽고, 상태가 ready인 첫 작업을 docs/gemini/COMMON.md 규칙대로 끝까지 진행해줘.
```

끝나면 Claude Code에게 "G01 결과를 검토해줘"라고 한다. 합격이면 Claude Code가 `done`으로 바꾸고 커밋한다.

## 상태 값
`ready`(시작 가능) → `in_progress` → `review`(검토 대기) → `done` / `blocked`(앞 작업 필요) / `rework`(불합격, 작업 파일 수정 후 다시 ready)

## 작업 목록
| ID | 작업 | 파일 | 앞 작업 | 상태 |
|---|---|---|---|---|
| G01 | 새 주인공 디자인 시안 3안 | [G01_hero_concepts.md](tasks/G01_hero_concepts.md) | - | done (A안 선택, 흰 머리로) |
| G02 | 보스 3종 새 디자인 (크래셔·아크·헤이즈 심장) | [G02_boss_designs.md](tasks/G02_boss_designs.md) | - | ready |
| G03 | 일반 적 6종 새 디자인 (투척병·폐인·사냥개·간수·드론·기사) | [G03_enemy_designs.md](tasks/G03_enemy_designs.md) | - | done (11/23 PixelLab으로 대신 만들어 적용) |
| G05 | **UI 전면 개편 시안 3안** (전투 HUD·일시정지·증강 카드) | [G05_ui_concepts.md](tasks/G05_ui_concepts.md) | - | ready (다음에 먼저) |
| G04 | 대화 초상화 (주인공 + NPC 3) | [G04_portraits.md](tasks/G04_portraits.md) | - | ready (주인공 완료, NPC 3장 남음) |

- 표는 할 순서대로다. 지금 하는 작업 다음에는 G05(UI 시안)를 먼저, G04 남은 초상화는 그다음. 서로 독립이라 한 번에 맡겨도 된다. 각자 `assets/sprites/gemini/` 안 자기 폴더에만 쓴다.
- 다음(예정): G06 UI 부품(G05에서 고른 안의 판 테두리·막대 틀·아이콘, 사용자가 안을 고른 뒤 작성), 보스 초상화(G02 결과 후). 구역 배경 원화는 Codex(T49)가 맡는다.
