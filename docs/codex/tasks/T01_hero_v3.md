# T01 주인공 마스터 v3 (음영·디테일 강화)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. (시작 절차, 쓸 수 있는 곳, 보고 방법이 거기 있다.)

## 목표
주인공 N-09(흰 머리 죄수)의 마스터 스틸컷 한 장을 `hero_v2`보다 훨씬 디테일하고 입체적으로 다시 만들고, 픽셀 스프라이트로 마무리한다.

## 입력
- 정체성(같은 인물·의상): `assets/sprites/unified_legacy/n09_idle.png`
- 직전 결과: `assets/sprites/forge/hero_v2/master/master_rgba.png`, `assets/sprites/forge/hero_v2/n09_v2_idle.png`
- 이 두 가지의 인물은 유지하고 아래 개선점만 반영한다. 새 캐릭터를 만들지 않는다.

## v2의 문제 (고칠 것)
1. 얼굴이 눈 하나뿐이라 단순하다.
2. 음영이 거의 없어 평면적이다.
3. 몸이 가늘다 (내용 너비가 키의 30%).
4. 천 질감과 낡은 느낌이 덩어리 몇 개에 그친다.

## 원화 요구사항
`COMMON.md` 4절의 화풍을 따르고, 추가로:
- **얼굴**: 눈은 크고 어둡게(진한 청록~검정) 안에 밝은 홍채 하이라이트 한 점, 눈썹 선, 코 끝과 입 선이 보이게, 귀 윤곽. 앞머리가 눈을 가리지 않게.
- **머리카락**: 큰 덩어리 6~8개로, 덩어리마다 2톤(흰색 + 푸른 회색 그림자), 뾰족한 끝.
- **상의**: 검은 반소매. 주름은 그림자 색면으로, 어깨 솔기, 소매 끝 해진 가장자리, 청록 팔 밴드에 줄 무늬 한 개.
- **하의**: 검은 바지. 무릎 주름, 해진 바짓단, 군데군데 찢어져 살이 보이는 곳 2곳(작게).
- **허리끈·손목 밴드**: 청록 허리끈에 매듭과 늘어진 끝, 손목 밴드에 줄 무늬.
- **손**: 손가락이 5개로 구분되게 큰 덩어리로.
- **신발**: 어두운 장화, 밑창이 다른 색으로 보이게, 끈 표시.
- **비율**: 머리는 키의 약 1/6, 어깨와 몸통은 옆에서 봐도 폭이 키의 33% 이상, 두 팔은 몸에서 조금 떨어져 둘 다 보이게, 두 발은 지면에 닿게.
- 무기 없음, 마스크 없음.

## 절차
1. `$generate2dsprite`로 마스터 스틸컷 1장 생성 (hero_v2와 같은 방식: `master_still`, `--finish hibit`). 저장 폴더: `assets/sprites/forge/hero_v3/`.
2. 마무리: `python tools/finish_character.py assets/sprites/forge/hero_v3/master/master_rgba.png n09_v3`
   (결과: `assets/sprites/forge/n09_v3/`, `assets/sprites/forge/n09_v3_idle.png`)
3. 검사: `python tools/check_sprites.py assets/sprites/forge/n09_v3_idle.png` 가 통과해야 한다.
4. 비교 이미지 `assets/sprites/forge/hero_v3/compare_1x.png`: 같은 바닥선에 왼쪽부터 `unified_legacy/n09_idle.png`, `n09_v2_idle.png`, `n09_v3_idle.png`를 1배로 놓고 진한 남색(#0e1628) 배경에 저장 (PIL 사용, 확대하지 않는다).
5. 보고서 `docs/codex/reports/T01.md` 작성, 상태를 `review`로 (COMMON.md 5절).

## 합격 기준 (모두 만족해야 한다)
- [ ] `check_sprites.py` 통과 (키 123±2, 알파 0/255, 색 48 이하)
- [ ] 눈이 어두운 2×2px 이상으로 보이고 홍채 하이라이트가 구분된다
- [ ] 내용 너비가 39px 이상 (키 123px의 32%)
- [ ] 머리카락 덩어리, 상의 주름, 손가락, 신발 밑창이 1배에서 구분된다
- [ ] 기준 이미지와 같은 인물이다 (흰 머리, 검은 옷, 청록 포인트)
- [ ] 5개 모두 보고서에 솔직하게 체크했다

## 하지 말 것
- 선(외곽선)을 원화에 그리지 않는다 (마무리가 1px 외곽선을 넣는다).
- 그라데이션, 번짐, 반투명을 쓰지 않는다.
- `tools/finish_character.py`의 설정을 바꾸지 않는다. 안 맞으면 원화를 고친다.
