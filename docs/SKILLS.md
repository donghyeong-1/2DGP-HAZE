# 설치된 스킬·도구 현황 (SKILLS)

이 노트북(Windows 11, 사용자 `ohama`)에 설치된 AI 스킬과 개발 도구를 한곳에 정리한 문서다. 작성: 2026-11-17 [Claude Code], 설치 폴더를 직접 확인한 결과다.
새 컴퓨터에서는 `docs/SETUP.md`로 환경을 만들고, 이 문서로 어떤 스킬이 왜 필요한지 확인한다. 스킬 자체는 저장소에 올리지 않는다(각자 PC의 홈 폴더).

## 1. 한눈에 보기

| 스킬 | 종류 | Claude Code (`~/.claude/skills`) | Codex (`~/.codex/skills`) | 이 프로젝트에서 실제로 쓴 곳 |
|---|---|:-:|:-:|---|
| codeart2d | 에셋 제작 (코드로 그림) | 설치 | 설치 | 휘두르기·오라·폭발 이펙트, 로고·타일 초기판, PixelSpec 품질 검사 |
| generate2dsprite | 에셋 제작 (이미지 생성) | 설치 | 설치 | **Codex가** 주인공·적·보스 마스터와 동작 프레임 전부(T01~T10) |
| generate2dmap | 에셋 제작 (이미지 생성) | 설치 | 설치 | **Codex가** 배경 3종(T06)과 사망·엔딩 화면(T11) |
| generate2dmedia | 에셋 제작 (이미지 경로) | 설치 | 설치 | generate2dsprite·generate2dmap이 이미지를 만들 때 거치는 계층 (Codex 내장 `image_gen` 경로) |
| video2dsprite | 에셋 제작 (영상 → 프레임) | 설치 | 설치 | **쓰지 않음** (영상 API 키·ffmpeg가 없다). 마무리 도구(`finish_frames` hibit)만 간접 사용 |
| codixel | 에셋 제작 (참조 이미지 → 픽셀) | 설치 | 설치 | 지금까지 직접 쓰지 않음 (선택) |
| game-feel | 게임 개발 지침 | 설치 | 설치 | 타격 멈춤, 화면 흔들림, 오버로드 섬광, 타수 증가의 근거 |
| platformer | 게임 개발 지침 | 설치 | 설치 | 점프 수치, 코요테 타임, 방 도달 가능성 한계 계산의 근거 |
| level-design | 게임 개발 지침 | 설치 | 설치 | 방 재설계, `room_check.py`(도달 가능성 검사기) |
| roguelike | 게임 개발 지침 | 설치 | 설치 | 방 단위 진행, 황금방·정비방, 사망 시 처음부터 |
| game-ui-ux | 게임 개발 지침 | 설치 | 설치 | HUD 크기·글자 보강 (2주차) |
| input-systems | 게임 개발 지침 | 설치 | 설치 | 점프 버퍼, 입력 처리 점검 |
| physics-tuning | 게임 개발 지침 | 설치 | 설치 | 대시·충돌 처리 점검 |
| pygame-core | 게임 개발 지침 | 설치 | 설치 | 참고만 (이 프로젝트는 pico2d를 쓴다) |

- 합계 14개. 두 도구에 **같은 14개**가 설치돼 있다.
- 상태 값: "쓰지 않음"은 설치만 되어 있다는 뜻이다. 설치 자체는 문제없다.

## 2. 스킬별 설명

### 2.1 에셋 제작 스킬 (agent-sprite-forge)
출처: https://github.com/0x0funky/agent-sprite-forge (MIT, commit `6b3da5c`), 버전 `forge 0.5.0`. 설치 폴더에는 `SKILL.md`, `scripts/`, `references/`, `agents/`가 있다.

| 스킬 | 하는 일 | 쓰는 도구 | 비고 |
|---|---|---|---|
| **generate2dsprite** | 캐릭터·소품·아이콘·이펙트의 마스터 정지 이미지, 시트, 동작 프레임을 만든다. 크기·색·팔레트 맞춤과 QA, 엔진용 내보내기까지 한다 | Codex 내장 `image_gen` + `scripts/` (키잉·분리·정렬 `process`, `finish_frames` hibit 마무리) | 이 프로젝트의 캐릭터는 전부 이 경로. 동작 프레임은 **영상이 아니라 2×2 시트**로 만든다 |
| **generate2dmap** | 맵·배경·타일·소품·시차 배경을 만든다. 충돌, 도달 가능성 검사, 미리보기, Tiled·Godot·LDtk 내보내기 | `conform_background.py`, `hibit_plate.py` | 배경 3종(T06), 화면 일러스트 2장(T11). 방 구조는 이 스킬이 아니라 우리 `tools/build_rooms.py`가 만든다 |
| **generate2dmedia** | 이미지·영상 생성 경로를 고르는 계층. API 키가 있으면 API, 없으면 Codex·Grok CLI. 사용 기록(ledger), 환경 점검(`forge_doctor`) | `route_media.py` | 이 PC는 API 키가 없고 **Codex CLI 경로**로 동작. 환경 점검 결과: `assets/sprites/forge/doctor.json` |
| **video2dsprite** | 승인된 마스터 한 장에서 동작마다 영상 한 개를 만들어 프레임으로 뽑는다 | xAI API 또는 Grok CLI, ffmpeg | **쓰지 않는다**. 영상 경로와 ffmpeg가 없다 (`docs/DECISIONS.md`) |
| **codeart2d** | 이미지 모델 없이 코드로 픽셀 스프라이트(PixelSpec), 벡터 소품·아이콘(SVG), FX(`fx_build`), 자동 타일 등을 그린다. 팔레트·QA 검사 | `scripts/`의 `fx_build.py`, `render_pixelspec.py`, `svg_render.py`, `autotile_build.py`, `pixel_qa.py` 등 | **마지막 수단**이라고 스스로 규정. 결과는 문서에 "code-drawn"으로 밝힌다 |

관련 규칙(`AGENTS.md`, `docs/codex/COMMON.md`): 이미지 생성이 필요한 에셋은 Codex, 코드로 그리는 에셋은 Claude Code가 맡는다. 마무리는 `tools/finish_character.py`, 검사는 `tools/check_sprites.py`.

### 2.2 codixel
출처: https://github.com/mankidev/codixel (MIT, commit `604a9dc`). 참조 이미지를 받아 픽셀화하고 단계마다 사용자와 확인하며 리깅·애니메이션하는 방식의 스킬이다. `SKILL.md`와 `core/pixel.js`가 설치돼 있다. 우리는 Codex가 마스터를 만드는 방식을 썼기 때문에 **직접 쓴 적은 없다**.

### 2.3 게임 개발 지침 8종 (gamedev-skills)
출처: https://github.com/gamedev-skills/awesome-gamedev-agent-skills (Apache-2.0, 2026-11-15 설치, 라이선스는 `~/.claude/skills/_licenses/`). 코드를 생성하는 도구가 아니라 **작업할 때 참고하는 지침 문서**다. 게임 파일에는 포함되지 않는다. 평가와 적용 아이디어는 `docs/REFERENCES.md`.

| 스킬 | 한 줄 설명 |
|---|---|
| game-feel | 화면 흔들림(trauma), 히트 스톱, 트윈, 스쿼시·스트레치, 넉백으로 타격감을 올린다 |
| platformer | 점프 느낌(코요테 타임, 점프 버퍼, 가변 점프, 낙하 중력), 벽 점프, 함정, 얇은 바닥 |
| level-design | 플레이어 이동 한계를 실제 수치에서 재서 레벨을 짠다. 열쇠·능력 잠금과 막힘(soft-lock) 검사 |
| roguelike | 한 판 구조, 영구 사망, 메타 진행, 시드 |
| game-ui-ux | HUD·메뉴의 배치, 크기, 접근성 |
| input-systems | 입력 액션, 데드존, 입력 버퍼, 키 재설정 |
| physics-tuning | 고정 시간 간격, 터널링 방지, 충돌 층 |
| pygame-core | pygame 게임 기본 루프. 이 프로젝트는 pico2d라서 참고만 |

## 3. 스킬 밖의 개발 도구

| 도구 | 버전 | 용도 |
|---|---|---|
| Python | 3.12.10 | 게임·도구 실행 |
| pico2d | 1.5.1 (PySDL2 0.9.17, pysdl2-dll 2.32.10) | 게임 엔진 (수업 규칙) |
| transitions | 0.9.3 | 상태 머신 (플레이어·적) |
| numpy / Pillow / scipy | 2.5.4 / 13.0.0 / 1.18.1 | 에셋 생성 도구(`tools/make_*.py`)와 검사 |
| python-pptx | 1.0.2 | 발표 자료 생성(`tools/make_presentation_2nd.py`) |
| Node.js | v24.20.0 | pixelfx 이펙트 렌더링(필요할 때만) |
| pixelfx (patch-gg, MIT) | - | 이전 이펙트 시트의 출처 (`docs/ASSETS.md`) |
| resvg-py | **미설치** | codeart2d의 SVG 렌더(`svg_render.py`)에 필요. 이전 로고·타일 SVG 도구용이라 지금은 필요 없다. 설치: `python -m pip install "resvg-py>=0.5,<0.6"` |

## 4. 스킬 외 AI 환경 (참고)

| 항목 | 내용 |
|---|---|
| Claude Code 동기화 스킬 | `~/.claude/skills/synced/`: Anthropic 제공 built-in-browser, chrome-browser, computer-use, deep-research, docs, docx, google-workspace, import-memory, morning, pdf, pptx, skill-creator, xlsx. 계정에서 자동 동기화되며 우리가 설치한 것이 아니다 |
| Claude Code 플러그인 | `claude-plugins-official` 마켓(anthropics/claude-plugins-official), 내장 `cc-plugin-agents-md` |
| Claude 앱 도구 | 내장 브라우저, 터미널 패널, 시각화 위젯, Claude in Chrome(필요 시) |
| Codex 기본 스킬 | `~/.codex/skills/.system`: imagegen, openai-docs, review-agent, skill-creator, skill-installer. imagegen이 이미지 생성의 실제 엔진 |
| Codex 설정 | `~/.codex/config.toml` |

## 5. 새 컴퓨터에서 설치하는 법 (요약)
1. `docs/SETUP.md`의 환경 준비(Python, `pip install pico2d transitions numpy pillow scipy python-pptx`).
2. agent-sprite-forge: 저장소를 받아 `requirements.txt` 설치 후 `generate2dsprite`, `generate2dmap`, `generate2dmedia`, `video2dsprite`, `codeart2d`를 `~/.claude/skills`와 `~/.codex/skills`에 복사. 상세는 `docs/SETUP.md`.
3. gamedev-skills 8종: `npx skills add gamedev-skills/awesome-gamedev-agent-skills --skill <이름> --agent claude-code` (`docs/REFERENCES.md`). Codex에는 같은 폴더를 `~/.codex/skills`로 복사.
4. codixel: 저장소의 `SKILL.md`, `core/`를 `~/.claude/skills/codixel/`에 복사.
5. 확인: `python ~/.claude/skills/generate2dmedia/scripts/forge_doctor.py` 같은 환경 점검(경로는 스킬 폴더 안내를 따른다).

## 6. 사용 규칙 (프로젝트)
- 에셋 작업 전에 이 표를 보고 알맞은 스킬을 먼저 쓴다 (사용자 요청 2026-11-07, 메모리 "설치 스킬 적극 활용").
- 스킬로 만든 에셋은 모델·도구·날짜·프롬프트를 `docs/ASSETS.md`와 `docs/image_prompts.md`에 기록한다.
- 코드로 그린 에셋은 문서에 반드시 "code-drawn"으로 표기한다 (과목 공지의 오리지널리티 평가 대응).

## 7. 이 PC에도 설치함 (2026-11-17, [Claude Code])
- 위 14개를 **두 번째 컴퓨터(ohama 노트북 B)**에도 맞췄다. gamedev-skills 8종은 `npx` 대신 저장소(commit `c6ca6c4`)를 받아 원문을 읽고 복사했다. 검사 결과: 마크다운 문서와 `platformer/scripts/jump_tuner.py`(표준 라이브러리만) 외에 실행 파일이 없고, 네트워크 호출·권한 확장(`allowed-tools`)·민감 경로 접근이 없다.
- 설치 위치: `~/.claude/skills/<이름>/`과 `~/.codex/skills/<이름>/` 양쪽. 라이선스 문구는 `~/.claude/skills/_licenses/gamedev-skills-LICENSE`, `-NOTICE`.
- codixel은 이 PC의 Codex에도 복사했다(`SKILL.md`, `core/`). `resvg-py`는 이 PC에 이미 설치돼 있다.
- Codex에만 있는 `hatch-pet`은 이 프로젝트와 무관하다(건드리지 않음).
- 확인: `python ~/.claude/skills/platformer/scripts/jump_tuner.py --help` 가 동작한다. 새 스킬은 **Claude Code와 Codex를 다시 시작해야** 목록에 나타난다.

## 8. 프로젝트 스킬 (2026-11-17, [Claude Code])
위 스킬들은 각자 PC의 홈 폴더에 설치하는 범용 스킬이다. 아래 3개는 **이 게임 전용**이라 저장소의 `.claude/skills/`에 넣었다. `git pull`만 하면 두 컴퓨터 모두 쓸 수 있다.
다른 프로젝트의 스킬 목록(인수인계, 커밋 전 검증, 규칙 TDD, 밸런스 시뮬레이션, 타격감, 화면 크기별 실행, 에셋 파이프라인)을 참고해, 이 프로젝트에 아직 없던 것만 만들었다. 인수인계와 에셋 기록은 `AGENTS.md`·`docs/ASSETS.md`가 이미 하고, 타격감은 `game-feel` 스킬이 있다. 규칙 TDD는 `AGENTS.md` 코드 규칙에 한 줄로 넣었다.

| 스킬 | 도구 | 하는 일 |
|---|---|---|
| verify | `tools/verify.py` | 커밋 전: 전체 테스트, PROGRESS 작업 로그, "진행 중"·Codex 영역 보호, AI 원본·5MB 넘는 파일 차단 |
| balance-sim | `tools/balance_sim.py`, 기준 `tools/balance_base.json` | 봇이 실제 게임 코드로 싸워 7 시나리오(아크 포함) x 4 무기 x 2 봇 x 시드의 승률·처치 시간·잃은 HP·게이지 흐름을 잰다(수 초). 수치 변경 전후 비교. `--meta max`(은신처 영구 강화 최대), `--economy`(판이 끝나는 곳별 헤이즈 결정) |
| playtest-capture | `tools/capture.py` | 실제 창으로 게임 화면 캡처. 방·적·무기·게이지 지정, 봇 조작 전투를 여러 장 찍고 모아 보기 저장. `--display 2`(또는 `HAZE_DISPLAY=2`)로 창을 두 번째 모니터에 띄운다 (게임 실행 `python src/main.py`도 `HAZE_DISPLAY`를 따른다) |

시뮬레이터가 게임 코드 변경으로 깨지지 않게 `tests/test_tools.py`가 지킨다.
