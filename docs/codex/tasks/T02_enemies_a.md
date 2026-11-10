# T02 적 3종 마스터 v3 (슬럼 폐인, 고철 투척병, 중장갑 간수)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. **앞 작업 T01이 `done`일 때만 시작한다.** (`docs/codex/TASKS.md` 확인)

## 목표
적 3종의 마스터 스틸컷을 주인공 v3와 **같은 화풍·같은 디테일 수준**으로 만들고 픽셀 스프라이트로 마무리한다. 한 번에 한 캐릭터씩 차례로 만든다.

## 화풍 기준
- 화풍·음영·림라이트 기준: `assets/sprites/forge/hero_v3/master/master_rgba.png` (T01 결과). 채도, 명암 단계, 눈 크기 비율을 맞춘다.
- 정체성 기준: 각 캐릭터의 `assets/sprites/unified_legacy/<이름>_idle.png`.
- 청록(cyan)은 모든 캐릭터 공통 포인트색으로 쓴다.

## 캐릭터 (이름 / 키 / 설명)
| 이름 | 목표 키 | 설명 |
|---|---|---|
| `enemy_slum_v3` | 117 | 앙상한 대머리 적대적 죄수, 해진 회색 옷, 구부정한 자세, 주먹을 쥠, 피부에 희미한 청록 혈관, 크고 어두운 광기 어린 눈, 밧줄 허리띠, 붕대 감은 맨발 |
| `enemy_thrower_v3` | 123 | 어두운 머리에 고글(렌즈 청록)을 쓴 고철 수집 죄수, 왼팔에 리벳과 녹이 있는 고철 방패, 오른손에 고철 조각을 쥠, 기운 자국이 있는 옷, 장화 |
| `enemy_guard_v3` | 135 | 육중한 갑옷 간수, 청록 바이저가 큰 헬멧, 앞쪽에 줄무늬 표식이 있는 큰 강철 방패, 묵직한 경찰봉, 어깨 보호대, 조끼 주머니, 장화, 넓은 실루엣 |

## 원화 요구사항 (모든 캐릭터)
`COMMON.md` 4절을 따르고, 추가로:
- 눈 또는 바이저·렌즈 같은 얼굴 요소를 크게 과장한다 (키의 3% 이상).
- 천·금속 재질마다 3단계 음영 색면. 녹, 해진 가장자리, 리벳, 이음매는 큰 덩어리로.
- 오른쪽 옆모습, 방패나 무기는 정면 쪽(오른쪽)에 둔다.

## 절차 (캐릭터마다 반복)
1. `$generate2dsprite`로 마스터 스틸컷 1장 (`--finish hibit`). 저장: `assets/sprites/forge/<이름>/`.
2. `python tools/finish_character.py assets/sprites/forge/<이름>/master/master_rgba.png <이름>`
   (결과: `assets/sprites/forge/<이름>/`의 마무리 결과와 `assets/sprites/forge/<이름>_idle.png`)
3. `python tools/check_sprites.py assets/sprites/forge/<이름>_idle.png` 통과 확인.
4. 세 캐릭터가 모두 끝나면 `n09_v3_idle.png`와 세 적을 1배로 나란히 놓은 `assets/sprites/forge/lineup_v3_a_1x.png`를 만든다 (진한 남색 배경, 바닥선 맞춤, 확대하지 않음).
5. 보고서 `docs/codex/reports/T02.md` 작성, 상태 `review` (COMMON.md 5절).

## 합격 기준
- [ ] 세 캐릭터 모두 `check_sprites.py` 통과
- [ ] 얼굴 요소(눈·바이저·렌즈)가 1배에서 구분된다
- [ ] 주인공 v3와 나란히 놓았을 때 채도·명암·디테일 수준이 같다
- [ ] 기존(`unified_legacy`)과 같은 캐릭터로 알아볼 수 있다
- [ ] 보고서에 솔직하게 적었다

## 하지 말 것
T01과 같다 (원화에 선 금지, 반투명 금지, 마무리 설정 변경 금지).
