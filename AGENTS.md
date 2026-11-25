# AGENTS.md

모든 AI 도구(Claude Code, Codex, Gemini)가 공통으로 따르는 프로젝트 규칙이다.
이 파일이 유일한 기준 문서(single source of truth)이며, `CLAUDE.md`와 `GEMINI.md`는 이 파일을 참조만 한다.

## 작업 시작 시 (필수)
0. 처음 쓰는 컴퓨터면 `docs/SETUP.md`로 환경을 준비하고(설치된 스킬·도구 목록은 `docs/SKILLS.md`), 작업 전에 `git pull`, 끝나면 커밋·푸시한다.
1. `docs/PROGRESS.md`를 읽어 현재 상태와 다음 할 일을 확인한다.
2. `docs/DECISIONS.md`를 읽어 이미 확정된 결정을 뒤집지 않는다.
3. 작업을 시작하기 전에 `PROGRESS.md`의 "진행 중"에 자신의 도구 이름과 작업 내용을 적는다.

## 작업 종료 시 (필수)
1. `docs/PROGRESS.md`를 갱신한다. (완료 항목 체크, "작업 로그"에 한 줄 추가, "다음 할 일" 수정)
2. 새로 확정된 결정이 있으면 `docs/DECISIONS.md`에 추가한다.
3. 작업 로그 형식: `YYYY-MM-DD [도구명] 한 일 / 바꾼 파일`

## 충돌 방지
- 같은 파일을 두 도구가 동시에 수정하지 않는다. "진행 중"에 적힌 파일은 건드리지 않는다.
- 확정되지 않은 사항은 임의로 정하지 말고 `PROGRESS.md`의 "열린 질문"에 적는다.

## 역할 분담 (Claude Code / Codex / Gemini)
- **Claude Code**: `src/`, `tests/`, `tools/`, `data/`, 문서, 코드로 그리는 에셋(`assets/tiles`, `assets/ui`, `assets/effects`), 결과 검토와 커밋·푸시.
- **Codex**: 이미지 생성이 필요한 에셋 중 캐릭터와 도트 크기를 맞출 필요가 없는 것(배경·일러스트). 2026-11-25 사용자 결정으로 게임 화면에 놓이는 도트 그림은 새로 맡기지 않는다(아래 PixelLab 줄). 작업 목록과 프롬프트는 전부 `docs/codex/`에 있다. 사용자가 "docs/codex/TASKS.md를 읽고 상태가 ready인 첫 작업을 진행해줘"라고 하면 `docs/codex/COMMON.md`와 해당 작업 파일(`docs/codex/tasks/`)을 따른다. Codex는 `assets/sprites/forge/`와 `docs/codex/reports/` 안에서만 쓰고, 커밋은 하지 않는다.
- **Gemini** (2026-11-23 추가, v6 `docs/plan_v6.md`): 새 화풍의 원화(캐릭터 디자인 시안·마스터, 고해상도 대화 초상화, 구역 배경 원화). 사용자가 "docs/gemini/TASKS.md를 읽고 상태가 ready인 첫 작업을 진행해줘"라고 하면 `docs/gemini/COMMON.md`와 해당 작업 파일(`docs/gemini/tasks/`)을 따른다. Gemini는 `assets/sprites/gemini/`와 `docs/gemini/reports/` 안에서만 쓰고, 커밋은 하지 않는다.
- **PixelLab** (유료 구독, MCP 연결됨. 2026-11-25 사용자 결정): 게임 화면에 놓이는 도트 그림(주인공·적·보스·NPC, 캐릭터 옆에 서는 소품)은 Claude Code가 PixelLab으로 만든다. 간수 `assets/sprites/pixellab/guard_v6/raw/base.png`를 화풍 기준으로 넣고, 도트 2px(1배 원본을 최근접 2배)로 적용한다(`tools/apply_pixellab_char.py`, `tools/apply_pixellab_event.py`). 다른 도구가 그린 그림은 디자인 참고로만 쓴다. 결과 원본은 `assets/sprites/pixellab/`.
- 서로의 영역 파일은 건드리지 않는다. 작업 전 `PROGRESS.md`의 "진행 중"을 확인한다.

## 프로젝트 요약
- 과목: 2D 게임 프로그래밍 (Python, pico2d), 순수 창작 2D 게임
- 장르: 횡스크롤 액션 로그라이트 (마우스 조준, 방 단위 던전, 죽으면 판은 처음부터, 은신처의 영구 성장은 남음. 2026-11-19 로그라이크에서 변경)
- 처음 기획(1차 발표) 대비 바뀐 것은 모두 `docs/changes_from_plan.md`에 기록한다 (3차 발표에서 말한다). 기획을 바꾸면 그 문서에도 한 줄 추가한다.
- 제목: 《헤이즈 (Haze)》. 순수 창작물이며 용어는 `docs/기획서.md`의 용어 정리를 따른다.
- 핵심 재미: 헤이즈 중독 게이지 (0%에서 사망, 1~19% 페이드, 100%에서 오버로드 폭발 → 그 사이를 유지). 현재 규칙의 요약은 `docs/DECISIONS.md` 맨 위 "현재 기준 요약"을 따른다.
- 기준 문서: `docs/기획서.md` (용어는 "헤이즈"로 통일한다)
- 개발 기간: ~2026-12 둘째 주, 1인 + AI 활용
- 1차 발표: 영상 1분 30초 / PPT 10p 이내 / 제출은 YouTube 링크 + Git 주소

## 코드 규칙
- 주석과 문서는 한국어, 변수·함수·클래스·파일명은 영어
- 수업 구조를 따른다: `world` 리스트 + 각 객체의 `update()` / `draw()`, 상태 머신은 `transitions` 라이브러리의 `Machine` 사용
- 과목 공지: 캐릭터 이미지는 AI 이미지 생성 툴로 직접 준비하는 것을 권장하고, 기존 에셋 사용은 허용하되 그래픽 오리지널리티가 낮아지므로 기획(규칙·시스템)의 차별화가 드러나야 한다. 프롬프트는 `docs/image_prompts.md`에 기록한다.
- 픽셀 아트 규칙(`docs/pixel_rules.md`): 최근접 필터, 1배 확대·축소·회전 금지, 정수 좌표로 그리기. 에셋을 추가하면 `python tests/test_pixel_assets.py`를 통과해야 한다.
- 과목 공지(2026-11-11 사용자 전달): 맵 에디터 같은 외부 툴을 사용해도 되고 적극 사용을 권장한다. 쓰는 도구와 버전, 라이선스는 `docs/ASSETS.md`에 기록한다.
- 에셋은 저작권 문제가 없는 것만 사용하고 출처·라이선스를 `docs/ASSETS.md`에 기록한다. 타인의 이미지·소리는 출처와 라이선스를 확인하지 않고 사용하지 않는다.
- 커밋 메시지는 한국어로 작성한다.
- 규칙(전투·게이지·적 행동)을 바꿀 때는 그 규칙을 확인하는 테스트를 먼저 쓰고(실패 확인) 코드를 고친다.

## 프로젝트 스킬 (`.claude/skills/`, 저장소에 포함)
Claude Code는 스킬로 불러 쓰고, 다른 도구는 같은 파일을 절차서로 읽는다. 자세한 내용은 `docs/SKILLS.md` 8절.
- **verify**: 커밋 전 점검. `python tools/verify.py` (테스트, PROGRESS 갱신, Codex 영역·진행 중 파일 보호, 원본·큰 파일).
- **balance-sim**: 전투 수치를 바꾸기 전후 비교. `python tools/balance_sim.py --save/--compare tools/balance_base.json`.
- **playtest-capture**: 실제 창 화면 캡처, 봇이 싸우는 장면 촬영. `python tools/capture.py --help`.
- **haze-fx**: 이펙트를 만드는 절차. `python tools/make_fx2.py --look <이름>`으로 모아 보기를 세 번 이상 고친 뒤 굽는다. 실행 중 사각형으로 이펙트를 그리지 않는다.
- **haze-inari**: 보류 (2026-11-24 사용자 결정). 저장소에 두지만 사용자가 이름으로 부를 때만 쓴다. 이펙트·연출은 haze-fx로 만든다.

## 폴더 구조
- `docs/` 기획서, 진행상황, 결정, 에셋 출처
- `src/` 게임 코드 (예정)
- `assets/` 이미지·사운드 (예정)
