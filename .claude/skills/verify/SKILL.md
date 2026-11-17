---
name: verify
description: 헤이즈 저장소에서 커밋·푸시하기 직전에 쓰는 점검 절차. 전체 테스트(픽셀 규칙 포함), PROGRESS·DECISIONS·ASSETS 갱신, Codex 영역과 "진행 중" 파일 보호, 명시 경로 git add, 한국어 커밋 메시지를 한 번에 확인한다. 코드·에셋·문서를 바꾼 작업을 마무리할 때마다 쓴다.
---

# verify

## 1. 자동 점검
`python tools/verify.py` — 실패하면 종료 코드 1과 이유를 출력한다.
- 전체 테스트(`tests/run_all.py`, 픽셀 규칙 `test_pixel_assets.py` 포함)
- 코드·에셋을 바꿨는데 `docs/PROGRESS.md`를 안 바꿨는지, 작업 로그에 오늘 `[Claude Code]` 줄이 있는지
- "진행 중"에 다른 도구의 줄이 있으면 그 파일은 건드리지 않는다
- Codex 영역(`assets/sprites/forge/`, `docs/codex/reports/`) 변경은 검토·적용이 끝난 것만 커밋한다
- 스테이지된 AI 원본(`source.png`)과 5MB 넘는 파일

## 2. 사람이 판단할 것 (도구가 못 본다)
- **화면**: 그림·연출·UI를 바꿨으면 `playtest-capture`로 실제 창에서 보고 나서 커밋한다. 테스트 통과는 "보인다"는 뜻이 아니다.
- **문서**: 새로 확정된 결정 → `docs/DECISIONS.md`. 새 에셋·도구 → `docs/ASSETS.md`(출처·라이선스, 코드 그림이면 code-drawn). 조작이 바뀌면 `README.md`.
- **PROGRESS 작업 로그 형식**: `YYYY-MM-DD [Claude Code] 한 일 / 바꾼 파일`. "다음 할 일"도 고친다.
- **문서 고치는 스크립트**: 새 내용을 전부 계산·검사한 뒤에만 파일을 쓴다. 쓰는 도중 실패하면 파일이 비워진다(2026-11-17 PROGRESS가 두 번 비워진 사고).

## 3. 커밋
- `git pull` 먼저 (두 컴퓨터를 쓴다).
- `git add -A` 금지. 경로를 하나하나 적는다. Codex가 작업 중인 파일(진행 중, `docs/codex/TASKS.md`의 상태 줄 등)이 같이 올라가지 않게 한다.
- 다른 도구가 같은 파일(예: PROGRESS)에 커밋 안 된 줄을 넣어 두었으면, 내 수정만 담은 내용을 `git hash-object -w --stdin` + `git update-index --cacheinfo`로 인덱스에 올린다.
- 커밋 메시지는 한국어. 마지막 줄에 시스템이 알려 준 Co-Authored-By 줄.
- 푸시 뒤 `git status --short`로 남은 파일이 의도한 것(Codex 진행분 등)뿐인지 본다.

## 4. 보고
통과한 테스트 수, 화면으로 확인한 것과 **확인하지 못한 것**(손맛, 소리, 난이도 체감)을 구분해서 말한다.
