# G03 일반 적 6종 새 디자인

먼저 `docs/gemini/COMMON.md`를 읽고 그 규칙을 따른다. G01·G02와 **같은 화풍**(기준: `assets/sprites/gemini/hero_concepts_v1/hero_A_side.png`).

## 배경
v6 안 A: 가장 자주 나오는 적 4종(투척병 24회, 슬럼 폐인 21회, 사냥개 19회, 간수 15회)과 구역 특색 2종(공장 드론, 탑 결정 기사)을
새로 만든다. 원화를 줄인 그림이 그대로 PixelLab 첫 프레임이 된다. 기존 역할·공격 방식은 유지하고 모습만 새로.
기존 그림: `assets/sprites/unified/enemy_<이름>_*_1.png` (아래 표).

## 공통
- 왼쪽을 보는 옆모습(주인공을 마주 봄), 마젠타 단색 배경, 1024px 이상, 몸 잘림 없음.
- 적은 주인공보다 **채도 낮고 탁한 색** + 각자 위험 부위 하나만 밝게(공격이 나오는 곳). 주인공의 청록은 쓰지 않거나 아주 작게.
- 게임 크기가 작다(키 40~70px). 줄여도 읽히는 큰 실루엣.

| 파일 | 적 | 역할 | 기존 그림 | 게임 키 |
|---|---|---|---|---|
| `slum_side.png` | 슬럼 폐인 | 헤이즈에 중독된 주민, 비틀거리며 할퀴기 | `enemy_slum_walk_1.png` | 약 58px |
| `thrower_side.png` | 고철 투척병 | 등에 고철 자루, 멀리서 던짐 | `enemy_thrower_walk_1.png` | 약 62px |
| `hound_side.png` | 사냥개 | 네 발 짐승, 달려들어 물기 | `enemy_hound_run_1.png` | 약 40px(몸길이 70) |
| `guard_side.png` | 중장갑 간수 | 방패와 곤봉, 느리고 단단함 | `enemy_guard_walk_1.png` | 약 68px |
| `drone_side.png` | 용접 드론 | 날아다니며 아래로 불꽃 | `enemy_drone_fly_1.png` | 폭 약 60px |
| `knight_side.png` | 결정 기사 | 탑의 기사, 순간이동 후 베기 | `enemy_knight_walk_1.png` | 약 70px |

추가로 `enemies_sheet.png`: 여섯 적과 주인공 실루엣을 같은 바닥에 세운 크기 비교. 새 폴더 `assets/sprites/gemini/enemy_designs_v1/`. 그림마다 최대 3번.

## 합격 기준
- [ ] 같은 화풍, 여섯 실루엣이 서로 확실히 다르다
- [ ] 위험 부위 하나만 밝게, 주인공과 색으로 구별
- [ ] 마젠타 배경, 잘림 없음, 보고서
