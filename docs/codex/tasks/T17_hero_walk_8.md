# T17 주인공 걷기 8프레임 (T04 개선)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. T04와 같은 방식(격자 시트 1장 → `process` → `finish_character.py --like` → `check_sprites.py`)을 쓴다. 영상 경로는 쓰지 않는다.

## 배경 (사용자 피드백 2026-11-17: "움직이는 애니메이션이 너무 부자연스럽다")
지금 게임의 걷기(`assets/sprites/unified/n09_walk_1~4.png`, T04 결과 `forge/n09_walk_v3b`)는 문제가 세 가지다.
1. **4장뿐**이라 달리기 속도(초당 480px)에서 다리가 툭툭 끊겨 보인다.
2. **몸통이 프레임마다 앞뒤로 흔들린다**: 머리·골반 가운데의 가로 위치가 프레임마다 +4, +9, −2, +2px로 최대 11px 차이 난다. 지금은 게임 코드가 그리는 위치를 옮겨 메우고 있다(`src/sprites.py` `SHIFT`).
3. **두 다리 색이 같아** 어느 다리가 앞인지 안 읽힌다.

## 입력
- 정체성·화풍: `assets/sprites/forge/hero_v3b/master/master_rgba.png`, 크기·색: `assets/sprites/forge/n09_v3b/finish.json`·`palette.json`
- 지금 걷기(비교용): `assets/sprites/forge/n09_walk_v3b/`, 게임 적용본 `assets/sprites/unified/n09_walk_*.png`

## 요구사항
- 이름 `n09_walk_v4`. **8프레임 한 주기**(2×4 또는 4×2 시트 1장): ① 오른발 앞 접촉 ② 몸 내려감 ③ 왼발이 지나감 ④ 몸 올라감 ⑤ 왼발 앞 접촉 ⑥ 내려감 ⑦ 오른발이 지나감 ⑧ 올라감. 팔은 다리와 반대로 흔든다.
- **몸통 고정**: 모든 프레임에서 몸통(벨트 버클) 가로 위치가 **±2px 안**. 몸의 위아래 출렁임은 접촉 프레임이 가장 낮고 지나가는 프레임이 가장 높게, 차이 2~3px.
- **먼 쪽 다리·팔은 두 단계 어둡게** (가까운 쪽과 바로 구별되게). 이것이 없으면 8프레임으로 늘려도 4프레임 반복처럼 보인다.
- 얼굴·머리카락·옷·몸 크기(키 123px)·발 바닥선이 T04와 같다. 캔버스는 8장 모두 같은 크기.
- 확인용 1배 strip과 GIF(프레임당 0.06초)를 보고서에 연결한다. 보고서에 프레임별 몸통 x와 바닥선 y를 표로 적는다.
- 8장이 한 시트에서 얼굴·옷이 계속 달라지면(3번 시도 후) **6프레임**(접촉·지나감·올라감 × 좌우)으로 줄여 다시 하고, 그 사실을 보고서에 적는다.

## 절차
① `$generate2dsprite` asset 시트(8칸) → ② `process` → ③ `python tools/finish_character.py <frames_raw> n09_walk_v4 --like n09_v3b` → ④ `python tools/check_sprites.py assets/sprites/forge/n09_walk_v4/frames/*.png`.
보고서 `docs/codex/reports/T17.md`, 상태 `review`.

## 합격 기준
- [ ] 1배 GIF에서 걷는(달리는) 동작으로 부드럽게 읽힌다, 앞·뒤 다리가 구별된다
- [ ] 몸통 x 흔들림 ±2px 안, 바닥선 차이 2px 이하 (`check_sprites.py` 통과)
- [ ] 얼굴·옷·크기가 T04·게임 대기 그림과 같다
- [ ] 보고서에 솔직하게
