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

- 다음 작업(예정, G01 결과를 보고 Claude Code가 작성): 고른 안의 마스터(옆모습·정면·색표), 보스 3종 새 디자인, 대화 초상화(NPC 3 + 보스 3), 구역 배경 원화.
