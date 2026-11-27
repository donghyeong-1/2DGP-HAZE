# 소품 props v6 생성 기록 (2026-11-27 Q1, Claude Code)

배경: 사용자(11/27) "무기 걸이와 같은 조금 퀄리티 떨어지는 것들 pixellab으로 다시 에셋을 뽑아서 적용 해줘", "실제 스팀 게임 수준으로 올리는 것이 목표이다. ai티가 안나도록 잘 해줘".
조사표와 고른 까닭은 `docs/opus/TASKS.md` '4차' Q1.

## 공통
- 도구: `create_image_pro_flash`(no_background), 상태 그림 하나는 `edit_image_pro_flash`, 화로 불꽃은 `animate_image_pixminimax`.
- 화풍 기준(style_image): 간수 `guard_v6/raw/base.png`를 잘라 올린 것. 64x64 캔버스는 몸 둘레 64x64(3,29)-(67,93), 32 캔버스는 가슴·방패 32x32(30,38)-(62,70),
  32x24 캔버스는 어깨 24x24(36,30)-(60,54). usage: "Art style, detail level, outline and pixel scale only. Same world as this armored guard. Do not draw the character."
  (작은 것은 "Art style, outline, shading and pixel scale only. ... Do not draw armor.")
- 프롬프트 끝은 늘 "Muted ... colours, dark navy outline, soft shading lit from the upper left." (간수와 같은 빛 방향)
- 적용: `python tools/apply_pixellab_props.py` (알파 0/255, 3칸 이하 떠 있는 점 지우기, 물건마다 32색으로 줄이고 간수 색과 가까운 색은 간수 색으로, 최근접 2배).
  상태 그림은 같은 그림에서 코드로: 분출구 달아오름(격자 틈만 주황), 품절 진열대 둘(어둡고 차갑게). 부서진 상자만 PixelLab 편집.
- 고른 원본은 `<물건>/raw/`, 시안 전부는 `<물건>/raw_gen/`.

## 물건별 (쓴 횟수 = 구독 생성 횟수)
| 물건 | 쓴 횟수 | 시안 | 고른 것 | 버린 것과 까닭 |
|---|---|---|---|---|
| 무기 걸이 | 20 (생성 3, 편집 1, 막힌 편집 1은 0) | 96x64 seed 3·11·27 | seed 27을 `edit_image_pro_flash` seed 17로 고침 -> `armory/raw/base.png` | s3: 철파이프가 기둥과 구별 안 됨. s11: 권총이 칼날처럼 보임. s27 원본: 권총 둘이 칼날 모양. 편집 seed 5는 "content policy"로 막힘(무기 낱말, 과금 없음) |
| 연습장 표지판 | 10 | 64x64 seed 3·11 | seed 3 -> `practice/raw/base.png` | s11: 비슷하나 과녁 테두리가 덜 깔끔. 원본 외곽선이 흐려 적용 때 남색 바깥 외곽선 1도트를 두름 |
| 상자 | 15 (생성 2, 편집 1) | 32x32 seed 3·11, 부서짐 편집 seed 3 | seed 3 + 편집 -> `crate/raw/base.png`, `broken.png` | s11: 외곽선이 옅음 |
| 증기 분출구 | 10 | 48x32 seed 3·11 | seed 3 -> `vent/raw/base.png` | s11: 너무 밋밋한 막대(틈만 6개) |
| 감시 레이저 머리 | 25 | 32x32 seed 3·11·29, 32x24 seed 29·7 | 32x24 seed 29 -> `laser/raw/base.png` | 32x32 s3: 너무 작음. s11·s29(32x32): 좋았으나 키 31도트(62px)라 천장 바로 아래 통과 발판 그림에 가운데가 가려짐(실제 창에서 확인) -> 한 칸(40px) 안에 드는 납작한 머리로 다시. 32x24 s7: 렌즈가 너무 작음 |
| 진열대 (제단·선반) | 20 | 제단 64x64 seed 3·11, 선반 64x64 seed 3·11 | 제단 s3 -> `pedestal/raw/altar.png`, 선반 s11 -> `shop.png` | 제단 s11: 비슷하나 장식이 약함. 선반 s3: 윗판이 쇠라 아이템과 구별이 약함 |
| 은신처 모루 | 10 | 64x64 seed 3·11 | seed 11 -> `anvil/raw/base.png` | s3: 받침이 납작하고 녹 무늬가 얼룩짐. 불똥은 옛 Codex T28 네 장(`anvil/raw/codex_sparks_N.png`, 원본 보관)의 자리 그대로 옮겨 달군 쇠 색으로 |
| 은신처 화로 | 11 (생성 2, 움직임 1) | 64x64 seed 3·11, 불꽃 4장(seed 5, first = last = base) | seed 3 + `brazier/raw/flicker/frame_0~3.png` | s11: 다리가 길고 그릇이 넓어 화면에서 무거움. 움직임의 4번 장은 0번과 거의 같아 뺌. 그릇·다리 줄은 0번 장으로 고정 |
| 합계 | **121** (11/27 잔액 705.70 -> 584.70) | | | |

## 프롬프트 (영문 그대로)
- 무기 걸이: "Side view game prop, no character. A sturdy standing weapon rack in an underground hideout, front view, flat on the floor. Frame of dark weathered wooden planks and riveted dark iron brackets, two legs on the floor, a top beam with iron pegs. Four weapons hang on it from left to right, each clearly separated: a long straight rusty iron pipe standing upright leaning in the rack; a pair of compact grey pistols hanging side by side by their trigger guards; one heavy grey mechanical gauntlet glove hanging on a peg; a coiled steel chain with a small square metal weight at the end hanging from a hook. Muted steel grey and dark brown colours, dark navy outline, soft shading lit from the upper left. Wide and low, filling the canvas width, standing at the bottom of the canvas."
  - 편집(seed 17, 씀): "Replace the two narrow hanging blade shapes on the left with two clearly readable compact pistols seen from the side, each hanging from its peg by the trigger guard: horizontal barrel on top, short grip angled down, grey steel with a dark navy outline. Make the iron pipe leaning on the left post a little thicker and rusty so it reads as a weapon. Keep the wooden frame, the gauntlet, the chain, the colours and the size exactly the same."
- 연습장 표지판: "Side view game prop, no character. A training-ground signpost in an underground hideout: one thick weathered wooden post standing on a small base of stacked sandbags, with a round practice target board nailed to the top of the post. The target is made of old wood planks with painted rings, faded red and off-white, with a few dents and an iron bolt in the middle. Narrow and tall, about 36 pixels wide and 58 pixels tall, standing at the bottom centre of the canvas. Muted colours, dark navy outline, soft shading lit from the upper left."
- 상자: "Side view game prop, no character. A small breakable wooden supply crate from a rainy prison slum: square box of weathered dark brown planks with dark iron corner brackets and rivets, one cross brace, a faint small teal crystal glint showing through a gap between two planks. Sits flat on the ground, fills the canvas. ..."
  - 부서짐 편집: "The crate has been smashed open: only the bottom third of the box is left standing, broken jagged plank ends sticking up, two loose planks and an iron corner bracket lying flat on the ground in front, splinters. No teal glint any more, the crate is empty. Same wood and iron colours, same width, sitting at the bottom of the canvas."
- 증기 분출구(s3): "Side view game prop, no character. A low steam vent set into a factory floor: a flat heavy iron grate with five dark slots, thick riveted rusty iron rim, two small bolts on each end, a short pipe stub on one side. Very low and wide, about 36 pixels wide and only 12 pixels tall, lying at the very bottom of the canvas, the rest of the canvas empty. Muted dark iron grey and rust colours, ..."
- 감시 레이저 머리(씀, 32x24): "Side view game prop, no character. A flat wide surveillance laser emitter mounted on a ceiling rail: a low boxy dark steel housing that fills the whole canvas width, flat top touching the top edge of the canvas, angled armor plates on both sides, small vent slits, and a round red glass lens in the middle of the underside pointing straight down. Symmetric, about 30 pixels wide and 15 pixels tall. Muted steel blue-grey colours, only the lens is red, ..."
- 제단: "Side view game prop, no character. A low treasure altar pedestal for a reward item: a wide stepped base of dark stone blocks with worn brass trim, and a flat brass offering plate on top with two small curved brass horns at its ends. The top surface is flat and empty. Wide and low, about 54 pixels wide and 30 pixels tall, standing at the bottom centre of the canvas, the upper half of the canvas empty. Dark stone grey with warm old gold brass accents, ..."
- 선반: "Side view game prop, no character. A scavenger merchant's display stand for one item: a short sturdy workbench counter made of riveted dark iron sheets and an old wooden top board, a small price tag of cardboard hanging on the front, a little teal glass lamp clamped to one corner. The top surface is flat and empty. ... Muted steel grey and dark teal colours, ..."
- 모루: "Side view game prop, no character. A heavy old blacksmith anvil in an underground workshop, seen from the side: dark forged iron with a flat polished working face, a pointed horn on the right, a square heel on the left, standing on a squat wide iron foot. A few scratches and a faint warm glint on the working face. Wide and low, about 54 pixels wide and 30 pixels tall, ..."
- 화로: "Side view game prop, no character. A round iron fire brazier standing on three short bent legs in an underground hideout: a deep dark iron bowl with riveted bands and a few holes glowing from inside, filled with burning coal, and a warm orange and yellow fire rising from it. About 44 pixels wide and 52 pixels tall including the flames, ..."
  - 불꽃(animate_image_pixminimax, 4장, view side): "The fire in the bowl flickers and sways gently, flame tips rising and falling, a few embers float up. The iron bowl and legs stay perfectly still and do not move."

## 게임에 들어간 결과
| 결과 | 크기(px) | 그리는 곳 |
|---|---|---|
| `assets/ui/hideout_armory.png` | 186x116 | `src/npc.py` `_draw_rack` (+ 두 칸에 든 무기 아래 표시 줄, `RACK_SLOTS`) |
| `assets/ui/hideout_practice.png` | 74x128 | `src/npc.py` 연습장 |
| `assets/ui/device_crate.png`, `device_crate_broken.png` | 62x62 | `src/devices.py` Crate |
| `assets/ui/device_vent.png`, `device_vent_hot.png` | 92x24 | `src/devices.py` Vent |
| `assets/ui/device_laser.png` | 64x30 | `src/devices.py` Laser |
| `assets/ui/pedestal_gold.png`, `pedestal_shop.png`, `pedestal_gone.png`, `pedestal_gone_shop.png`(새) | 120x150 | `src/pedestal.py` (아이콘 높이 `ICON_Y`: 제단 44, 선반 56) |
| `assets/props/hideout_anvil_1~4.png` | 132x117 | `src/props_anim.py` (발 가운데 x 56, 발 밑 112 그대로) |
| `assets/props/hideout_brazier_1~4.png` | 99x130 (전 99x120) | `src/props_anim.py` (캔버스 10px 키우고 기준점 y 112 -> 126, 바닥에 닿는 자리 그대로) |
