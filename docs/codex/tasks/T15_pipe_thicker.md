# T15 철파이프 굵게 재작업 (T07 개선)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. 이전 작업(T07~T11)과 같은 방식(시트 1장 → `process` → `finish_character.py` 또는 `hibit_plate.py` → 검사)을 쓴다.

## 배경
T07의 공격 포즈 5방향 × 3프레임은 합격했지만 철파이프가 약 3px로 가늘어서 막대나 창처럼 보인다(내려찍기 T08 plunge의 파이프는 4~5px로 더 낫다). **몸 자세는 그대로 두고 파이프만 굵게** 다시 만든다.

## 입력
- 기존 결과: `assets/sprites/forge/n09_swing_side_v3_take3`, `n09_swing_up_v3`, `n09_swing_down_v3`, `n09_swing_upfwd_v3`, `n09_swing_downfwd_v3` (각 `frames/`)와 원화 `hero_pipe_v3/<방향>/source.png`, `assets/sprites/forge/n09_plunge_v3`(굵기 기준)
- 정체성·화풍: `assets/sprites/forge/hero_v3b/master/master_rgba.png`

## 요구사항
- 파이프 굵기를 **1배에서 5~6px**로, 길이는 약 70px, 철 질감(밝은 면 + 그림자 면 + 어두운 끝마개 + 손잡이 쪽 청록 천 감김)으로.
- 몸·얼굴·옷·발 위치는 T07과 같게 유지한다 (게임의 발 기준점 `config.PLAYER_FRAMES`를 바꾸지 않아도 되도록). 캔버스 크기가 바뀌면 보고서에 적는다.
- 방향마다 한 번에 한 장씩: 수평 → 위 → 아래 → 앞 위 → 앞 아래. 이름은 `n09_swing_<방향>_v4`, 저장은 새 폴더.

## 공통 요구사항
- 선 없는 평면 색면, 재질마다 밝음·기본·그림자 3단계, 빛은 왼쪽 위 (`COMMON.md` 4절). 같은 이미지는 최대 3번까지 시도하고 멈춘다.
- 동작마다 새 폴더에 저장한다(기존 폴더 덮어쓰기 금지). 실패한 시도와 어색한 점은 보고서에 숨기지 않는다.
- 아이콘·소품은 **1배로 봤을 때 읽히는 것**이 기준이다. 얇은 선과 작은 무늬는 키워서 그린다.

## 합격 기준
- [ ] 5방향 모두 파이프가 5~6px로 굵고 방향이 맞다
- [ ] 얼굴·옷·몸 크기·발 바닥선이 T07과 같다, 반투명 0개, 기존 팔레트 안
- [ ] 보고서 `docs/codex/reports/T15.md`, 상태 `review`
