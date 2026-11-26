# UI 3차 '교도소 철판' PixelLab 생성 기록 (2026-11-26, docs/opus/TASKS.md 3차 O8)

판·막대·작은 부품은 코드 그림(`tools/make_ui_plate.py`). PixelLab은 그림 솜씨가 필요한 것(갈래 아이콘)만.

## 갈래 아이콘 기호 (raw/, 32x32, 1배)
- 도구: `create_image_pro_flash` 32x32, `palette` = ["#0c0e13", "#5a6272", "#a7afbd", "#eef1f6"] (윤곽 + 회색 3단), 배경 없음.
- 첫 장(chain_link_s11)을 화풍 기준(`style_image.source_image_id` 7573ccee-...)으로 나머지에 넣어 굵기·크기를 맞췄다.
- 기호만 회색으로 그리게 하고, `make_ui_plate.icon()`이 회색 4단을 갈래 색 3단(+윤곽)으로 바꿔 코드로 그린 철 원판(지름 30점, 리벳 넷) 가운데에 얹는다 -> `assets/ui/up_mut_<갈래>.png` (64x64).
- 프롬프트 공통 뒷부분: "bold chunky shapes, readable at small size, dark outline, flat shading, no background, centered".

| 갈래 | 프롬프트 앞부분 | 고른 것 |
|---|---|---|
| bloom 각성 | a wide open eye with short rays around it (awakening) | s11 |
| ember 위험 | a warning triangle with a bold exclamation mark inside (danger) | s11 |
| hollow 페이드 | s11 crescent moon dissolving into dots / s12 hooded head dissolving into pixels / s13 a candle with its flame flickering out into smoke wisps | **s13** (s11은 덩어리로 보이고 s12는 흩어지는 느낌이 없다) |
| tide 강화 | two stacked upward chevron arrows (power up) | s11 |
| pipe_combo 연타 | a short iron pipe club with three small impact burst marks | s11 |
| pipe_air 공중 | an iron pipe pointing straight down with a big downward arrow and a ground crack | s11 |
| pipe_dash 이동 베기 | a long horizontal slash streak arc with three speed lines | s11 |
| dash 대시 | a heavy boot with three horizontal speed lines | s11 |
| chain_gather 모으기 | a spiral vortex with four small arrows pointing inward | s11 |
| chain_pierce 관통 | a chain with a spear tip piercing through a thick metal plate | s11 |
| chain_link 연결 | two interlocking chain links (화풍 기준 장) | s11 |
| pistol_rapid 연사 | three bullets flying in a row with motion lines | s11 |
| pistol_ricochet 도탄 | a bullet trail that hits a wall and bends off with a spark | s11 |
| pistol_dash 대시 사격 | a pistol with three speed lines behind | s11 |
| gauntlet_charge 충전 | an armored fist with two small lightning bolts | s11 |
| gauntlet_crash 충돌 | an armored fist punching into a brick wall with cracks | s11 |
| gauntlet_counter 반격 | a small round shield with a curved arrow bouncing back | s11 |
| duo 합성 | two interlocking cog gears | s11 |
| (저주 카드) | a cracked skull with a small chain wrapped across it | s11 |

색: 갈래 색(`mutations.FAMILIES[...]['color']`) 그대로. 단 청록 계열인데 헤이즈가 아닌 이동 베기·연사는 철판 스킨에서 파랑·흰색으로(`ICON_COLOR`). 저주는 빨강.
사용 횟수: 5회 x 21장 = 105회 (2026-11-26 남은 횟수 1146.7 -> 약 1041).

## 판·틀·막대·카드 틀 (2026-11-26 재시험, 기획 세션 지시: 코드 그림 대신 PixelLab)
- 도구: `create_ui_asset`. 부품 판 512x512(25회)에 `pieces` 12개(창 판, 작은 판, 키, 이름표, 버튼, 고른 버튼, 무기 칸, 고른 칸, 체력 막대, 게이지 관, 보스 막대, 간판),
  카드 판 448x600(25회)에 카드 넷(보통·희귀·전설·저주).
- 팔레트(18색): #06070a #0c0e13 #15181f #1d222b #2a303b #3b4352 #5a6272 #8a93a3 #d8dde6 #e2b23a #8a661a #a4552a #68341c #e23a48 #821c28 #f0b432 #96621a #ffde8c (청록 없음).
- 화풍 기준(`style_image_base64`): 문지기 bash_1을 1배로 줄여 방패·어깨 부분만 66x64로 자른 것(리벳 박힌 쇠 방패, 녹, 어두운 강철).
- 공통 설명: dark riveted steel prison plates, chamfered (cut) corners not rounded, visible 2px bevel (light top-left, dark bottom-right), bolt heads,
  a few scratches and chipped paint, hazard yellow-and-black stripes only on the selected button, stencil markings, NO glow, NO crystals, NO neon, NO gradients, NO text.

| 시안 | 원본 | 설명 차이 | 결과 |
|---|---|---|---|
| A 보통 | kit/kit_a.png (seed 21), kit/cards_a.png (seed 21) | 위 공통 | 1배 도트. 판 가운데 256 영역에 그려 옴. 'key' 칸에 키캡 대신 열쇠 그림 -> 키캡은 버튼 조각으로 |
| B 무거움 | kit/kit_b.png (seed 37), kit/cards_b.png (seed 37) | heavy industrial, thick bolted brackets, more rust streaks | 1배 도트. 카드가 60x83으로 작게 와서 변을 이어 붙인 길이가 길다 |
| C 깔끔 | kit/kit_c_raw.png (seed 54) -> kit/kit_c.png | clean painted steel, almost no rust | 첫 요청(seed 53, 설명에 prison)은 **정책 위반으로 거절**(오탐으로 보임). 'prison'·기준 그림을 빼고 다시 요청. 캔버스를 꽉 채운 **2배 도트**로 와서(2x2 칸의 80%만 같은 색) 2x2마다 가장 흔한 색으로 반을 줄였다. 카드는 따로 뽑지 않고 A 카드를 함께 쓴다(cards_c = cards_a) |

- 굽기: `tools/apply_ui_plate.py --look a|b|c` -> `assets/ui/upx_*.png` 19장(9칸 판 7, 이름표, 메뉴 띠, 체력 틀, 게이지 몸통·양끝, 보스 막대 틀(새), 로고 판(새), 카드 틀 넷).
  네 모서리는 원본 그대로, 변은 원본 가운데에서 잘라 이어 붙이고, 가운데는 원본 가운데 색 한 가지로 메운다. 보스 막대 틀은 변 가운데 고리가 반복돼 모서리 옆 한 줄로 고르게(uniform).
  메뉴 띠는 원본 '고른 버튼'이 전부 줄무늬라 글자가 묻혀서, 가운데는 버튼 조각 + 노란 밑줄, 오른쪽 끝 8점만 줄무늬 조각.
- 로고: `tools/make_title_plate.py`가 `upx_logo_plate` 위에 같은 스텐실 글자를 찍어 `upx_logo_title`.
- 사용 횟수: 125회 (성공 5장 x 25, 거절된 C 첫 요청은 차감 없음). 남은 횟수 1041.7 -> 916.7.
