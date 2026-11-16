# T10 보스 크래셔 애니메이션

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. T04·T05와 같은 방식(2×2 또는 1×N 격자 시트 1장 → `process` → `finish_character.py --like` → `check_sprites.py`)을 쓴다. 영상 경로는 쓰지 않는다.

## 입력
- 마스터: `assets/sprites/forge/remake_t01_t03/boss_crasher/master/master_rgba.png`, 크기·색 `remake_t01_t03/finished/boss_crasher_remake/finish.json`·`palette.json`
- 게임 적용본: `assets/sprites/unified/boss_crasher_idle.png` (키 195px, 폭 188px). 보스 패턴은 `src/boss.py`: 바닥 찍기(smash), 충격파(slam), 돌진(charge), 도약(leap)

## 동작
| 이름 | 프레임 | 설명 |
|---|---|---|
| `boss_crasher_idle_v3` | 2 | 무겁게 숨쉬는 대기(증기 배출구가 조금 뿜는다) |
| `boss_crasher_smash_v3` | 3 | ① 두 주먹을 머리 위로 들어 올림(예고) ② 바닥을 내려찍음 ③ 주먹이 바닥에 박힌 채 |
| `boss_crasher_charge_v3` | 2 | 돌진: 몸을 앞으로 숙이고 어깨를 내밀고 달림 ①② |
| `boss_crasher_leap_v3` | 3 | 도약: ① 웅크림 ② 공중(팔 벌림) ③ 착지 충격 자세 |
| `boss_crasher_hurt_v3` | 1 | 맞고 움찔 |
(총 11프레임. 캔버스가 넓어져도 된다. 바닥선은 모든 프레임이 같아야 하고, 도약의 공중 프레임만 오프셋을 둔다.)

## 공통 요구사항
- 오른쪽 옆모습, 마젠타 배경, 선 없는 평면 색면 3단계 음영(`COMMON.md` 4절). 모든 칸에서 얼굴·의상·몸 크기·바닥선 기준이 같아야 한다.
- 캐릭터가 칸 경계를 넘거나 잘리지 않게 여백을 둔다. 동작마다 새 폴더에 저장한다(기존 폴더 덮어쓰기 금지).
- 확인용으로 프레임을 1배로 이어 붙인 strip과 GIF를 만들어 보고서에 연결한다. 어색한 점(발 미끄러짐, 얼굴 변형)은 숨기지 않는다.
- 같은 이미지는 최대 3번까지 다시 시도하고 멈춘다. 실패한 시도도 보고서에 적는다.
- 공중 동작·큰 몸짓은 `check_sprites.py`가 "키·바닥선 차이"로 실패할 수 있다(T05 점프의 경우). 그때는 캔버스 안 위치가 의도된 것인지 보고서에 설명한다.

## 합격 기준
- [ ] 찍기 예고(주먹 든 자세)와 내려찍기가 구분된다
- [ ] 얼굴·갑옷·크기가 마감본과 같다(흉터 위치, 푸른 증기 구멍)
- [ ] 보고서에 솔직하게

보고서 `docs/codex/reports/T10.md`, 상태 `review`.
