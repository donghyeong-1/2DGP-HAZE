# Gemini 공통 규칙 (모든 작업이 먼저 따른다)

Gemini(Antigravity 또는 Gemini 앱)는 `docs/gemini/TASKS.md`의 작업 하나를 맡아 끝까지 진행한다.
맡는 일: **새 화풍(2026-11-23 v6, `docs/plan_v6.md`)의 원화** — 캐릭터 디자인 시안·마스터, 고해상도 대화 초상화, 구역 배경 원화.
게임 코드·테스트·픽셀 마무리·적용·커밋은 Claude Code가 한다. Codex는 `docs/codex/`의 자기 작업 목록을 따로 진행한다.

## 1. 시작할 때
1. `AGENTS.md`, `docs/plan_v6.md`, `docs/DECISIONS.md` 맨 위 "현재 기준 요약"을 읽는다.
2. `docs/PROGRESS.md`의 "진행 중"을 확인한다. 다른 도구가 적어 둔 파일은 건드리지 않는다.
3. "진행 중"에 `- [Gemini] <작업 ID> <제목> / 수정 중인 파일: assets/sprites/gemini/<작업 폴더>/, docs/gemini/reports/<ID>.md` 를 적는다.
4. `docs/gemini/TASKS.md`에서 그 작업의 상태를 `in_progress`로 바꾼다.

## 2. 쓸 수 있는 곳과 쓰면 안 되는 곳
| 허용 | 금지 |
|---|---|
| `assets/sprites/gemini/<작업 폴더>/` 새로 만들기 | `src/`, `tests/`, `tools/`, `data/` (Claude Code 담당) |
| `docs/gemini/reports/<ID>.md`, `docs/gemini/TASKS.md`(상태 칸만) | `assets/sprites/forge/`, `docs/codex/` (Codex 담당) |
| `docs/image_prompts.md`, `docs/ASSETS.md`(끝에 추가만), `docs/PROGRESS.md`(진행 중·작업 로그 줄만) | `assets/sprites/unified/`, `assets/backgrounds/`, `assets/ui/`, `assets/effects/`, `assets/tiles/` |

- **커밋·푸시는 하지 않는다.** 결과 확인과 커밋은 Claude Code(또는 사용자)가 한다.
- 기존 결과 폴더를 덮어쓰거나 지우지 않는다. 다시 만들면 `_v2` 같은 새 폴더에 둔다.

## 3. 화풍 기준 (v6)
- 참고하는 것은 INARI(1HP STUDIO)의 **연출 기법**뿐이다: 구역마다 지배색 하나 + 강조색 한두 개, 어두운 몸에 밝은 포인트, 실루엣이 분명한 디자인, 흩날리는 2차 움직임 요소.
- **INARI의 캐릭터·소재를 닮게 하지 않는다**(과목이 순수 창작을 요구한다): 흰 머리 + 붉은 포인트 조합, 여우 귀·꼬리, 쿠나이, 동양 사원 소재 금지.
- 세계관은 헤이즈 그대로다: 슬럼(파랑)·철골 공장(주황)·감시탑(청록), 헤이즈는 청록으로 빛나는 중독성 물질. 용어는 `docs/기획서.md`.
- 캐릭터 원화: **선 없는 평면 색면**, 단색 배경(#FF00FF 마젠타), 오른쪽 옆모습 전신, 1024×1024 이상, 여백을 둔다. 음영은 재질마다 밝음·기본·그림자 3단계, 빛은 왼쪽 위.
- 게임 안 크기는 작다(주인공 키 약 41px = 내부 해상도 640×360). 그래서 **실루엣과 색 덩어리로 읽혀야 한다**: 작은 장식보다 큰 모양, 얼굴보다 머리 모양·옷 윤곽.
- 원화 단계에서 픽셀 아트를 흉내 내지 않는다. 픽셀화·동작은 Claude Code가 PixelLab과 마무리 도구로 한다.
- 초상화(대화창용)는 픽셀이 아니라 고해상도 그림이다(상반신, 투명 배경 또는 마젠타).

## 4. 끝날 때
1. `docs/gemini/reports/<ID>.md`에 적는다: 만든 파일 경로, 사용한 모델 이름(알 수 없으면 "모델명 미제공"), 프롬프트 요약, 시도 횟수, 기준과 달라진 점, 해결 못한 문제.
2. `docs/image_prompts.md`와 `docs/ASSETS.md` 끝에 프롬프트·날짜·도구·모델을 한 줄씩 추가한다.
3. `docs/gemini/TASKS.md` 상태를 `review`로 바꾼다.
4. `docs/PROGRESS.md`의 "진행 중" 줄을 지우고 "작업 로그"에 `YYYY-MM-DD [Gemini] <한 일> / <바꾼 파일>`을 추가한다.
5. 채팅에는 한 단락으로 요약한다: 결과 경로, 가장 자신 있는 안, 가장 큰 문제 한 가지.
