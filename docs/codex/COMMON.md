# Codex 공통 규칙 (모든 작업이 먼저 따른다)

Codex는 `docs/codex/TASKS.md`의 작업 파일 하나를 맡아 끝까지 진행하고, 이 문서의 규칙을 따른다. Claude Code는 게임 로직·테스트·문서·마무리 스크립트를 맡고, **Codex는 이미지 생성이 필요한 에셋을 맡는다.**

## 1. 시작할 때
1. `AGENTS.md`, `docs/DECISIONS.md`(맨 위 "현재 기준 요약"), `docs/pixel_rules.md`, `docs/sprite_spec.md`를 읽는다.
2. `docs/PROGRESS.md`의 "진행 중"을 확인한다. 다른 도구의 항목이 있으면 그 파일을 건드리지 않는다.
3. "진행 중"에 `- [Codex] <작업 ID> <제목> / 수정 중인 파일: assets/sprites/forge/<폴더>/, docs/codex/reports/<ID>.md` 를 적는다.
4. `docs/codex/TASKS.md`에서 그 작업의 상태를 `in_progress`로 바꾼다.

## 2. 쓸 수 있는 곳과 쓰면 안 되는 곳
| 허용 | 금지 |
|---|---|
| `assets/sprites/forge/<작업 폴더>/` 새로 만들기 | `src/`, `tests/`, `tools/`, `data/` (Claude Code 담당) |
| `docs/codex/reports/<ID>.md`(보고서), `docs/codex/TASKS.md`(상태 칸만) | `assets/sprites/unified/`, `unified_legacy/`, `assets/effects/`, `assets/tiles/`, `assets/ui/`, `assets/fonts/` |
| `docs/image_prompts.md`, `docs/ASSETS.md`(끝에 추가만), `docs/PROGRESS.md`(진행 중·작업 로그 줄만) | 기존 결과 폴더(`hero_v2/` 등) 덮어쓰기·삭제. 새 버전은 항상 새 폴더 |

- **커밋·푸시는 하지 않는다.** 결과 확인과 커밋은 Claude Code(또는 사용자)가 한다.
- 외부 툴(맵 에디터 등)은 사용해도 되고 권장된다. 쓰면 도구, 버전, 라이선스를 `docs/ASSETS.md`에 적는다.

## 3. 만드는 방법
- 이미지 생성은 설치된 스킬을 쓴다: `$generate2dsprite`(마스터·시트), `$generate2dmap`(배경·맵). 영상 경로와 ffmpeg는 이 PC에 없으니 `video2dsprite`는 쓰지 않는다. 이미지 생성은 Codex 내장 `image_gen`이다.
- 마무리(픽셀화)는 항상 `python tools/finish_character.py <master_rgba.png> <이름>`으로 한다. 목표 키·색 수·외곽선이 그 스크립트에 고정되어 있다. 설정을 임의로 바꾸지 않는다.
- 결과 확인은 `python tools/check_sprites.py <결과 png들>` 으로 한다. 실패하면 원인을 고쳐 다시 만든다. **같은 이미지에 최대 3번**까지 다시 시도하고, 그래도 안 되면 멈추고 보고서에 이유를 적는다.
- 이미지 생성 사용량은 사용자의 구독에서 나간다. 한 번에 한 장씩 만들고, 쓸데없이 여러 후보를 만들지 않는다.

## 4. 화풍 기준 (모든 캐릭터 공통)
- 원화는 **선 없는 평면 색면**, 마젠타(#FF00FF) 배경, 오른쪽 옆모습, 1024×1024, 전신이 여백을 두고 들어오게.
- 음영은 색면으로 한다: 재질마다 밝음·기본·그림자 3단계, 빛은 왼쪽 위. 반대쪽에 **청록(cyan) 림라이트는 옷·팔·다리·신발·갑옷 같은 천·금속에만 얇게** 쓰고, **얼굴·머리카락·피부에는 쓰지 않는다**(T01 검토에서 외곽선처럼 보이거나 흩어진 점이 되었다). 피부는 살색 두 톤만, 분홍·보라 그림자 금지. 그라데이션·번짐·반투명 금지.
- 작은 요소는 축소에서 사라지니 **크게 과장**한다: 눈은 키의 3% 이상, 눈썹·코·입 선, 손가락 구분, 신발 밑창.
- 같은 인물·의상·비율을 지킨다. 기준 이미지가 있으면 그것을 따른다.
- 확대·축소·회전 금지 규칙(`docs/pixel_rules.md`)은 마무리에서 지켜진다. 원화 단계에서는 픽셀 아트를 흉내 내지 않는다(후처리가 픽셀을 만든다).

## 5. 끝날 때
1. `docs/codex/reports/<ID>.md`에 아래를 적는다 (`docs/codex/reports/_template.md` 복사).
   - 만든 파일 경로, 사용한 프롬프트 요약, 시도 횟수, `check_sprites.py` 결과 전체, 기준 이미지와 달라 보이는 점(머리·옷·비율·눈), 해결하지 못한 문제. **잘 안 된 점을 숨기지 않는다.**
2. `docs/image_prompts.md`와 `docs/ASSETS.md` 끝에 프롬프트·날짜·사용 도구를 한 줄씩 추가한다. 이미지 모델명을 알 수 없으면 "모델명 미제공"이라고 적는다.
3. `docs/codex/TASKS.md`의 상태를 `review`로 바꾼다.
4. `docs/PROGRESS.md`의 "진행 중" 항목을 지우고 "작업 로그"에 `YYYY-MM-DD [Codex] <한 일> / <바꾼 파일>`을 추가한다.
5. 채팅에는 한 단락으로만 요약한다: 결과 경로, 통과 여부, 가장 큰 문제 한 가지.
