# T16 제목 화면 일러스트

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. 이전 작업(T07~T11)과 같은 방식(시트 1장 → `process` → `finish_character.py` 또는 `hibit_plate.py` → 검사)을 쓴다.

배경판(T06)·사망/엔딩 화면(T11)과 같은 방식(`$generate2dmap` 배경, `conform_background.py` → `hibit_plate.py --size 1920x1080 --colors 32 --smooth 0`, 확대 금지)으로 **제목 화면 한 장**을 만든다.

## 입력
- 정체성·화풍: 주인공 `assets/sprites/forge/hero_v3b/master/master_rgba.png`, 분위기는 `assets/sprites/forge/screens_v1/screen_ending_v3.png`·`screen_death_v3.png`와 `backgrounds_v1/`
- 세계관: `docs/기획서.md` 1.2절 (푸른 헤이즈 결정이 뒤덮은 격리 도시 '네뷸라 교도소')
- 게임이 얹는 것: 로고 이미지 `assets/ui/logo.png`(320×96, HAZE)와 메뉴 글자. **그림에는 글자와 로고를 넣지 않는다.**

## 장면
- 하늘이 푸르게 번진 밤, 푸른 헤이즈 결정이 군데군데 솟은 거대한 교도소 외벽과 탑의 원경.
- 왼쪽 아래에 주인공이 파이프를 든 채 외벽 위에서 도시를 내려다보는 옆모습(작게, 화면 높이의 약 25%). 흰 머리·청록 밴드·허리끈 유지.
- **화면 가운데 위쪽(대략 x 560~1360, y 120~360)은 비워 둔다** (로고 자리). 아래쪽 가운데도 메뉴 글자 자리로 비워 둔다.

## 규격
- 1920×1080, 32색 이하, 투명 픽셀 0개. 저장 `assets/sprites/forge/screens_v1/screen_title_v3.png`, 중간 산출물은 `screens_v1/title/`.

## 공통 요구사항
- 선 없는 평면 색면, 재질마다 밝음·기본·그림자 3단계, 빛은 왼쪽 위 (`COMMON.md` 4절). 같은 이미지는 최대 3번까지 시도하고 멈춘다.
- 동작마다 새 폴더에 저장한다(기존 폴더 덮어쓰기 금지). 실패한 시도와 어색한 점은 보고서에 숨기지 않는다.
- 아이콘·소품은 **1배로 봤을 때 읽히는 것**이 기준이다. 얇은 선과 작은 무늬는 키워서 그린다.

## 합격 기준
- [ ] 규격 통과 (Pillow로 크기·색 수·불투명 확인, `reduction` 경고는 보고서에 설명)
- [ ] 로고·메뉴 글자 자리가 비어 있고, 글자를 합성한 미리보기(`preview_title_ui_1x.png`)에서 읽힌다
- [ ] 보고서 `docs/codex/reports/T16.md`, 상태 `review`
