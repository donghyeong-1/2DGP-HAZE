# 새 컴퓨터에서 이어서 작업하기 (SETUP)

이 저장소만 받으면 **게임 실행, 테스트, 문서, 에셋(가공본)**은 그대로 쓸 수 있다. 저장소에 없는 것(AI 도구 설정, 스킬, 외부 도구)은 아래 순서로 준비한다. 2026-11-11에 새로 clone한 사본에서 테스트 31개가 통과하는 것을 확인했다.

## 1. 저장소와 패키지
```bash
git clone https://github.com/donghyeong-1/2DGP-HAZE.git
cd 2DGP-HAZE
python -m pip install -r requirements.txt     # Python 3.12 권장
python tests/test_gauge.py && python tests/test_player.py && python tests/test_pixel_assets.py
python src/main.py                              # 실행 확인
```
- `git config user.name`과 `user.email`이 없으면 커밋 전에 설정한다.
- 이 PC에서 쓴 버전: pico2d 1.5.1, transitions 0.9.3, Pillow 13, numpy 2.5, scipy 1.18.

## 2. AI에게 이어서 시키기
AI 도구는 **프로젝트 폴더를 연 채로** 시작한다 (폴더가 다르면 `AGENTS.md`를 못 찾는다). 대화 기록은 컴퓨터 사이에 이어지지 않으므로, 상태는 아래 문서에서 읽는다.

| 도구 | 읽는 파일 | 시작 프롬프트 예 |
|---|---|---|
| Claude Code | `CLAUDE.md` → `AGENTS.md` | `AGENTS.md 규칙대로 docs/PROGRESS.md와 docs/DECISIONS.md를 읽고 "다음 할 일"을 이어서 진행해줘` |
| Codex | `AGENTS.md` | 위와 같음 |
| Gemini | `GEMINI.md` → `AGENTS.md` | 위와 같음 |

- 현재 상태와 다음 할 일: `docs/PROGRESS.md`. 확정된 결정: `docs/DECISIONS.md` 맨 위 "현재 기준 요약". 설계: `docs/기획서.md` (5장이 구현 설계, 5.9가 주차별 완료 기준).
- **작업을 마칠 때 PROGRESS.md와 DECISIONS.md를 갱신하고 커밋·푸시한다.** 대화에서만 정한 일은 다른 컴퓨터에서 사라진다.
- **작업 시작 전 `git pull`, 끝나면 `git push`.** 두 컴퓨터에서 동시에 작업하지 않는다 (`PROGRESS.md`의 "진행 중" 표시가 잠금 역할).

## 3. 저장소에 없는 것 (필요할 때만 준비)
| 항목 | 언제 필요한가 | 준비 방법 |
|---|---|---|
| AI 도구 로그인·구독 (Claude Code, Codex, Gemini) | AI로 작업할 때 | 각 도구에 로그인 |
| agent-sprite-forge 스킬 | Codex·Claude로 캐릭터 이미지를 새로 만들 때 | `git clone https://github.com/0x0funky/agent-sprite-forge.git` 후 그 폴더에서 `python -m pip install -r requirements.txt`, `python tools/install_skills.py --apply --host codex` (Claude Code는 `--host claude`). 쓴 버전은 commit 6b3da5c |
| codixel 스킬 | 선택 (지금까지 사용 안 함) | `https://github.com/mankidev/codixel`의 `SKILL.md`, `core/`를 `~/.claude/skills/codixel/`에 복사 |
| pixelfx | 이펙트를 새로 만들 때 | `git clone https://github.com/patch-gg/pixelfx.git` (프로젝트 밖 폴더에), Node 18 이상, `node tools/render.mjs <id> --sheet` 후 `python tools/finish_effects.py <pixelfx 폴더> <id>` (`docs/pixel_rules.md`) |
| ffmpeg, 영상 생성 API 키 | 현재 쓰지 않음 | (영상으로 동작 프레임을 만들 때만) |
| `gh` (GitHub CLI) | 선택 | `winget install GitHub.cli` 후 `gh auth login` |
| AI 원본 이미지 `source.png`, `assets/concept/source/` | 마스터 이미지를 처음부터 다시 만들 때 | 저장소에 올리지 않았다. 마무리는 올라가 있는 `master_rgba.png`로 다시 할 수 있다 (`python tools/finish_character.py <master_rgba.png> <이름>`) |

## 4. 이어받을 때 점검 순서
1. `git pull` → 테스트 3개 실행 → `python src/main.py`
2. `docs/PROGRESS.md`의 "진행 중", "다음 할 일", "열린 질문"을 읽는다.
3. 작업을 `PROGRESS.md`의 "진행 중"에 적고 시작한다.
