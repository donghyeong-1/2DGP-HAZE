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
