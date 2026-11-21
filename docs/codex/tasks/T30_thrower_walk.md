# T30 투척병 걷기 4장 (+ 뒤로 물러서기 2장)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. T27과 같은 방식(격자 시트 → `process` → `finish_character.py --like` → `check_sprites.py`)을 쓴다.

## 배경 (퀄리티 계획 0 "모든 행동에 고유한 동작 그림")
일반 적 4종 중 **투척병만 걷는 그림이 없어** 대기 그림 한 장으로 바닥을 미끄러진다. 투척병은 거리를 벌리려고 자주 움직이므로(쫓기·뒤로 물러서기) 눈에 잘 띈다. 슬럼·간수·사냥개는 걷기·달리기가 있다.

## 입력
- 원화 `assets/sprites/forge/remake_t01_t03/enemy_thrower/master/master_rgba.png`, 마감 기준 `remake_t01_t03/finished/`의 투척병(키 123)
- 비교: `assets/sprites/unified/enemy_thrower_idle.png`, `enemy_thrower_throw_1~3.png`, 슬럼 걷기 `enemy_slum_walk_*`

## 동작 (6장)
| 이름 | 장 | 자세 |
|---|---|---|
| `enemy_thrower_walk` | 4 | 앞으로 걷기. ①② 왼발 내딛음 ③④ 오른발. 던질 고철을 든 손은 몸 쪽에 붙인다 |
| `enemy_thrower_back` | 2 | 앞(오른쪽)을 본 채 뒤로 한 걸음 물러섬. ① 뒷발을 뒤로 뻗음 ② 앞발을 끌어옴. 몸을 살짝 숙여 경계 |

- 바닥선 같게, 몸통 위치는 거의 같게(게임이 옮긴다). 기준점(발 가운데 x, 바닥 y)을 보고서에.
- 새 폴더 `assets/sprites/forge/thrower_walk_v1/frames/`, GIF(각 0.12초).

## 절차
걷기 → 물러서기. 같은 이미지는 최대 3번. 보고서 `docs/codex/reports/T30.md`, 상태 `review`.

## 합격 기준
- [ ] 걷기 GIF에서 왼발·오른발이 번갈아 보인다(같은 걸음 두 번 금지, T21 교훈)
- [ ] 정지 그림(`enemy_thrower_idle`)과 같은 인물·크기·색
- [ ] 보고서에 솔직하게
