# T27 보스 크래셔 걷기 4장 + 사망 2장

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. T10과 같은 방식(격자 시트 → `process` → `finish_character.py --like` → `check_sprites.py`)을 쓴다.

## 배경 (퀄리티 상승 계획 1-4)
스테이지 2 보스 크래셔는 걷는 그림이 없어 **대기 그림으로 바닥을 미끄러진다.** 죽을 때도 쓰러지는 그림이 없다. 아크(T20)는 둘 다 있어 차이가 크다.

## 입력
- 원화 `assets/sprites/forge/remake_t01_t03/boss_crasher/master/master_rgba.png`, 마감 기준 `remake_t01_t03/finished/boss_crasher_remake/`(키 195)
- 비교: `assets/sprites/unified/boss_crasher_idle_1~3.png`, `boss_crasher_smash_*`, 아크 걷기 `boss_ark_walk_*`

## 동작 (6장)
| 이름 | 장 | 자세 |
|---|---|---|
| `boss_crasher_walk` | 4 | 무거운 걸음. ①② 왼발 내딛음(몸이 그쪽으로 기울고 어깨 흔들림) ③④ 오른발. 걸음마다 몸이 살짝 내려앉는다 |
| `boss_crasher_death` | 2 | ① 무릎을 꿇고 팔이 늘어짐(한 손으로 바닥 짚음) ② 앞으로 엎어짐(높이 키의 1/3 이하) |

- 바닥선 같게, 걷기 4장은 몸통 위치가 거의 같게(게임이 앞으로 옮긴다). 기준점을 보고서에.
- 새 폴더 `assets/sprites/forge/crasher_walk_death_v1/frames/`, GIF(걷기 각 0.14초).

## 절차
걷기 → 사망. 같은 이미지는 최대 3번. 보고서 `docs/codex/reports/T27.md`, 상태 `review`.

## 합격 기준
- [ ] 걷기 GIF에서 왼발·오른발이 번갈아 보인다(같은 걸음 두 번 금지, T21 교훈)
- [ ] 정지 그림과 같은 인물·크기
- [ ] 보고서에 솔직하게
