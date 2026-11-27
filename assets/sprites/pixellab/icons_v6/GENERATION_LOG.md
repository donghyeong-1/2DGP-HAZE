# 무기·아이템 아이콘 icons v6 생성 기록 (2026-11-27 I1, Claude Code)

배경: Q1 보고("무기 아이콘 icon_w_*: 이제 걸이 무기와 화풍이 다름", "아이템 아이콘: Codex, 진열대 위에서 평면적"). 사용자(11/27) "추천대로 다 고쳐줘".
그 전 무기 아이콘은 코드 그림(`tools/make_weapons.py`), 아이템 아이콘은 Codex T13. 둘 다 1px 도트(2px 격자 일치 0.79~0.87)라 2px인 캐릭터·소품과 도트 굵기가 달랐다.

## 방법
- 도구: `create_image_pro_flash`(no_background). 48x48 아이콘 = 도트 2px로 24x24 도트라, **한 장에 24x24 칸을 여럿 두고 칸마다 아이콘 하나**를 뽑았다
  (한 장 5회로 4~10개. 같은 장 안의 아이콘은 선 굵기·명암·빛 방향이 저절로 같다).
- 화풍 기준(style_image):
  - 무기: Q1 무기 걸이 원본(`props_v6/armory/raw/base.png`)의 무기 부분 96x24 (0,12)-(96,36). usage "These are the same four weapons hanging on a rack: match their look, colours, outline and pixel scale, but draw each weapon as a separate chunky icon."
  - 사슬 다시 뽑기: 고른 건틀릿 칸 24x24 (`weapons_b.png` (48,0)-(72,24)). usage "Same icon set as this gauntlet icon: match outline thickness, steel colours, shading and pixel scale. Do not draw a gauntlet."
  - 아이템: 증강 갈래 아이콘 기호 `ui_plate_v1/raw/pipe_combo_s11.png`를 24x24 (3,4)-(27,28)로 자른 것. usage "Icon style only: chunky shapes, outline thickness, flat shading and pixel scale. Do not copy the subject."
- 적용: `python tools/apply_pixellab_icons.py` (칸 자르기, 알파 0/255, 떠 있는 조각 지우기(무기는 몸통 하나만, 아이템은 1칸 점과 칸 가장자리에 닿는 이웃 칸 조각),
  벌마다 색 고정(무기 32색, 아이템 48색), 칸 가운데, 최근접 2배 48x48). 무기는 외곽선을 두고 몸통 색에 감마 0.62(어두운 HUD 칸에서 묻혀서),
  물약은 십자가 청록을 물약 색 초록으로. 그 뒤 `python tools/make_form_icons.py`(형태 = 새 무기 + 금별), `python tools/make_fury_icon.py`(분노 = 새 공격력을 보라로).

## 시안과 고른 것 (쓴 횟수 = 구독 생성 횟수)
| 파일 (raw_gen/) | 크기·seed | 기준 그림 | 평가 |
|---|---|---|---|
| weapons_rack_s3.png | 96x24 s3 | 걸이 무기 | 쌍권총 두 자루가 또렷 -> **쌍권총**. 파이프가 누런 회색, 사슬은 갈고리 + 네모 추 |
| weapons_icon_s3.png | 96x24 s3 | 갈래 아이콘 | 걸이와 덜 닮음(건틀릿이 뭉개짐, 파이프가 흰색) -> 버림 |
| weapons_rack_s11.png | 96x24 s11 | 걸이 무기 | 파이프가 걸이처럼 녹슨 갈색 -> **철파이프**, 주먹 마디가 또렷 -> **건틀릿**. 사슬은 고리 + 공(사슬로 덜 읽힘) |
| chain_s3.png | 24x24 s3 | 건틀릿 칸 | 사슬 고리 다섯이 보이고 위 끝에 네모 추 -> **사슬** (시트의 사슬은 HUD에서 갈고리처럼 읽혔다) |
| items_s3.png | 96x72 s3 | 갈래 아이콘 | 좋으나 외곽선이 가늘고 아이콘이 칸의 70%쯤 -> 버림 |
| items_s11.png | 96x72 s11 | 갈래 아이콘 | 외곽선이 굵고 또렷. 1배 화면에서 장화·모래시계·공격력의 실루엣이 옛 그림보다 작아 다시 뽑음 |
| items_big_s11.png | 96x72 s11 ("칸을 거의 채우는") | 갈래 아이콘 | 크지만 공격력(파이프 아래 붉은 고리)이 뜻이 약함 -> 버림 |
| items_big_s29.png | 96x72 s29 ("칸을 거의 채우는") | 갈래 아이콘 | 실루엣이 가장 크고 굵다 -> **아이템 10종 전부** |
| 합계 | **40회** (11/27 잔액 584.70 -> 544.70) | | 무기 20(시트 3장 + 사슬 1장), 아이템 20(시트 4장) |

## 프롬프트 (영문 그대로)
- 무기 시트: "Game UI icon sheet: a row of four separate weapon icons, each one centred inside its own 24x24 pixel square cell, cells side by side, nothing crossing between cells. Left to right: 1) a long rusty iron pipe lying diagonally from lower left to upper right; 2) a pair of compact grey pistols seen from the side, one slightly behind the other, barrels pointing right; 3) one heavy grey mechanical gauntlet fist seen from the side, knuckles pointing right; 4) a short coiled steel chain with a small square metal weight at the end, diagonal. Bold chunky shapes and big clear silhouettes readable at small size, few details, dark navy outline, muted steel grey with small rust and teal accents, soft shading lit from the upper left, transparent background."
- 사슬: "Game UI weapon icon: a short length of heavy steel chain made of five big chunky oval links clearly separated, running diagonally from lower left to upper right, with a small square metal weight hanging on the upper end. Bold chunky shapes, big clear silhouette readable at small size, few details, dark navy outline, muted steel grey, soft shading lit from the upper left, transparent background, centred in the canvas."
- 아이템 시트(씀, seed 29): "Game UI icon sheet: a grid of twelve separate item icons, 4 columns by 3 rows, each icon filling almost its whole 24x24 pixel square cell (about 21 pixels wide or tall), big and bold, nothing crossing between cells. Row 1, left to right: a fat glass capsule tube with metal caps filled with glowing teal liquid and tick marks on the side; a big open grey metal hand catching a teal crystal; a wide hourglass with blue sand and dark metal frame; a thick orange upward arrow rising over a short iron bar. Row 2: a big grey metal shield with a yellow face split by a crack; a big grey boot with a white wing on its heel; a short heavy iron pipe striking down with a burst of red sparks at its end; a big flexed grey metal arm with a pink heart on the upper arm. Row 3: a medicine bottle with a dark cap and a green cross label; a tall teal crystal shard; last two cells empty. Bold chunky shapes and big clear silhouettes readable at small size, few details, dark navy outline, muted colours with one clear accent colour per icon, flat shading lit from the upper left, transparent background."
  (s3·s11은 "each icon centred inside its own 24x24 pixel square cell"와 "fat/big/wide" 없는 같은 문장)

## 칸 -> 결과
- 무기: `icon_w_pipe`(weapons_b 0칸), `icon_w_pistol`(weapons_a 1칸), `icon_w_gauntlet`(weapons_b 2칸), `icon_w_chain`(chain.png)
- 아이템(items.png 4x3): 1줄 `icon_cap`·`icon_absorb`·`icon_steady`·`icon_enhance`, 2줄 `icon_resist`·`icon_dash`·`icon_power`·`icon_vigor`, 3줄 `icon_heal`·`icon_shard`
- 코드로 다시 만든 것: `icon_f_pipe·pistol·gauntlet·chain`(make_form_icons), `icon_fury`(make_fury_icon). `icon_w_knife`(옛 무기, 부르는 코드 없음)는 그대로.

## I1-fix (2026-11-27): 무기 밝기, 아이템 넷의 뜻
지휘 쪽이 I1 비교판을 원래 크기로 보고 짚은 것: (1) 무기 아이콘이 HUD에서 예전보다 덜 읽힌다, (2) 공격력(세운 파이프 + 불꽃)과 균열의 분노(같은 그림의 보라)가
풀이 난 기둥처럼 보이고 색만 다르다. 흡수의 손이 굽은 관처럼, 모래시계 모래에 체크 무늬.

- 무기 넷(생성 없음): `apply_pixellab_icons.py`의 밝히기를 감마 0.62에서 `stand()`로 바꿈. 바깥 외곽선(투명과 맞닿은 칸)은 어둡게 두고, 안쪽 칸은 밝기 순서대로
  구간 [118, 250]으로 편다(쌍권총 [168, 252], 건틀릿 [150, 252], 사슬 [128, 250]: 가는 모양이라 외곽선 비율이 커서). 밝기만 더해 녹·강철의 색 차이는 지킨다
  (흰색 쪽 섞기는 녹이 바래고, 곱은 남색 칸의 푸른 기가 과장되어 버렸다).
  HUD 칸 바탕 (12, 16, 27) 위 평균 명암 차이(든 칸 / 들지 않은 칸, I1 전 -> I1 -> I1-fix):
  철파이프 103.9/43.1 -> 71.5/29.1 -> 125.5/51.4, 쌍권총 121.5/50.0 -> 71.8/29.7 -> 123.5/51.2, 건틀릿 141.4/57.8 -> 79.2/32.5 -> 147.0/60.1, 사슬 82.2/34.8 -> 53.5/23.0 -> 86.5/36.0.
- 흡수·결핍 방지(생성 없음): I1의 `items_big_s11.png`(같은 프롬프트) 칸으로 바꿈 -> `raw/items_alt.png`. 손바닥·엄지가 보이고, 모래가 체크 무늬 없이 한 덩어리.
- 공격력·균열의 분노(생성 10회, 잔액 544.70 -> 534.70): 96x24 한 줄 4칸, 화풍 기준 = 고른 아이템 시트의 방패 칸 24x24(`raw/items.png` (0,24)-(24,48)),
  usage "Same icon set as this shield icon: match outline thickness, chunky shapes, shading and pixel scale. Do not draw a shield."
  프롬프트: "Game UI icon sheet: a row of four separate item icons, each one filling almost its whole 24x24 pixel square cell, big and bold, nothing crossing between cells. Left to right: 1) a heavy iron pipe smashing down diagonally into a big bright orange-red impact starburst; 2) a clenched grey metal fist punching forward with a big bright orange-red impact starburst at the knuckles; 3) a clenched grey metal fist wrapped in tall violet flames; 4) a glowing violet jagged crack torn open in the air with violet flames bursting out of it. Bold chunky shapes and big clear silhouettes readable at small size, few details, dark navy outline, flat shading lit from the upper left, transparent background."
  | 파일 (raw_gen/) | seed | 평가 |
  |---|---|---|
  | power_fury_s29.png | 29 | 1칸 파이프가 내리쳐 터지는 주황 충격 -> **공격력**, 3칸 보라 불꽃에 휩싸인 주먹 -> **균열의 분노** (`raw/power_fury.png`). 2칸 주먹 + 충격도 좋음, 4칸 균열은 지저분함 |
  | power_fury_s7.png | 7 | 같은 구성이 더 작고 흐림 -> 버림 |
  `tools/make_fury_icon.py`(공격력 색 바꾸기)는 이제 쓰지 않는다(--force 없이는 멈춤).

