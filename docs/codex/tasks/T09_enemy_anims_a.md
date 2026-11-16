# T09 슬럼·고철 투척병 애니메이션

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. T04·T05와 같은 방식(2×2 또는 1×N 격자 시트 1장 → `process` → `finish_character.py --like` → `check_sprites.py`)을 쓴다. 영상 경로는 쓰지 않는다.

## 입력
- 슬럼: `assets/sprites/forge/remake_t01_t03/enemy_slum/master/master_rgba.png`, 크기·색 `remake_t01_t03/finished/enemy_slum_remake/finish.json`·`palette.json`
- 투척병: `remake_t01_t03/enemy_thrower/master/master_rgba.png`, `finished/enemy_thrower_remake/...`
- 게임에 적용된 마감본: `assets/sprites/unified/enemy_slum_idle.png`, `enemy_thrower_idle.png` (키 117·123px)

## 동작
| 이름 | 프레임 | 설명 |
|---|---|---|
| `enemy_slum_walk_v3` | 4 | 구부정한 걸음(T04의 걷기와 같은 방식, 접촉·내려감·통과·올라감) |
| `enemy_slum_attack_v3` | 3 | ① 팔을 뒤로 크게 젖힘(예고, 게임에서 노랗게 번쩍이는 프레임) ② 팔을 앞으로 휘두름 ③ 회복 |
| `enemy_slum_hurt_v3` | 1 | 맞고 움찔 |
| `enemy_thrower_throw_v3` | 3 | ① 고철을 든 팔을 뒤로 젖힘 ② 던지는 순간(팔이 앞으로) ③ 팔이 내려옴 (던지는 고철은 따로 있으니 손에 든 것만) |
| `enemy_thrower_hurt_v3` | 1 | 맞고 움찔 |
(총 12프레임. 동작마다 새 폴더, `--like`는 각 적의 재제작 마감 폴더.)

## 공통 요구사항
- 오른쪽 옆모습, 마젠타 배경, 선 없는 평면 색면 3단계 음영(`COMMON.md` 4절). 모든 칸에서 얼굴·의상·몸 크기·바닥선 기준이 같아야 한다.
- 캐릭터가 칸 경계를 넘거나 잘리지 않게 여백을 둔다. 동작마다 새 폴더에 저장한다(기존 폴더 덮어쓰기 금지).
- 확인용으로 프레임을 1배로 이어 붙인 strip과 GIF를 만들어 보고서에 연결한다. 어색한 점(발 미끄러짐, 얼굴 변형)은 숨기지 않는다.
- 같은 이미지는 최대 3번까지 다시 시도하고 멈춘다. 실패한 시도도 보고서에 적는다.
- 공중 동작·큰 몸짓은 `check_sprites.py`가 "키·바닥선 차이"로 실패할 수 있다(T05 점프의 경우). 그때는 캔버스 안 위치가 의도된 것인지 보고서에 설명한다.

## 합격 기준
- [ ] 슬럼 걷기가 걷는 동작으로 읽힌다, 공격 예고 프레임이 식별된다
- [ ] 얼굴·옷·크기가 재제작 마감본과 같다
- [ ] 보고서에 솔직하게

보고서 `docs/codex/reports/T09.md`, 상태 `review`.
