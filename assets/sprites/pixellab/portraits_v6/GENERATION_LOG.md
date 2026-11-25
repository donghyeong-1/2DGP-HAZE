# 대화 초상화 portraits v6 생성 기록 (2026-11-25, Claude Code)

배경: 은신처 대화창의 NPC 초상화 6장(Codex T32)은 밝은 평면 만화풍에 1px 단위(2px 격자 일치율 0.8)라, 같은 날 PixelLab으로 바꾼
NPC 몸 그림·주인공 초상화와 화풍이 달랐다. 사용자 요청: "대화 초상화를 새 몸 그림에 맞춰줘".

## 화풍 기준
주인공 초상화 `assets/portraits/n09_1.png`(Gemini G04 원화를 줄인 것, 2px 격자)를 1배(100x100)로 줄인 `raw/hero_style_100.png`.
주인공 기본 표정은 이 그림을 그대로 쓴다.

## NPC 기본 표정 (18회: 6회 x 3장)
`create_image_pro_flash`, 100x100, seed 3, style_image = hero_style_100,
usage "Portrait art style, head size, framing, shading, outline and pixel scale only. This is the hero's dialogue portrait from the same game;
draw a different person in exactly this style." 세 장 모두 한 번에 통과. 설명은 새 몸 그림(`../mechanic_v6` 등)과 같은 설정:
- mechanic_1: Dialogue portrait, head and shoulders bust, three-quarter view facing LEFT ... A sturdy, confident woman mechanic ...: tanned skin,
  dark hair tied up in a bun, orange goggles pushed up on her forehead, strong jaw, calm serious expression ... olive-green work overalls with
  metal buckles over a dark shirt; one shoulder shows a grey mechanical prosthetic arm with a small teal light; the head of a big steel wrench
  is visible behind her shoulder.
- keeper_1: ... An old storekeeper ...: a wrinkled old man with a long nose, bushy grey eyebrows and a grey beard, tired but kind eyes ...
  worn brown hooded cloak with the hood up and a faded teal lining ...; a leather strap crosses his chest, and the corner of an iron-banded
  wooden chest with a padlock is visible on his back.
- archivist_1: ... A young record keeper (archivist) ...: slim face, messy brown hair, round glasses, a yellow pencil tucked behind the ear ...
  worn grey-blue shirt with a small ID tag ... hugs the top edge of a thick red-brown ledger book.

## 표정 2 (30회: 6회 x 5장)
`edit_image_pro_flash`(method text, "Change only the facial expression ... Keep everything else exactly the same").
| 파일 | 표정 | 메모 |
|---|---|---|
| mechanic_2 | 씩 웃음(이를 보이는 웃음, 한쪽 눈썹) | 좋음 |
| keeper_2 | 걱정(눈썹을 모으고 아래를 봄) | 좋음 |
| archivist_2 | 놀람(눈을 크게, 입을 벌림) | 좋음 |
| n09_2_try1 | 결의 | 다시: 색 고정 옵션 때문에 9색이 되며 청록 눈빛이 사라짐 |
| n09_2 | 결의(눈썹을 내리고 옅은 웃음), 색 고정 끔, seed 7, "eyes MUST stay bright glowing teal" | 좋음 |

편집본은 그림 전체가 조금씩 다시 그려지고 색 수가 줄어든다. 그대로 번갈아 보이면 옷·머리까지 출렁이므로
`tools/apply_pixellab_portraits.py`가 **기본 표정 그림에 얼굴 사각형만** 편집본에서 가져와 붙인다(색은 기본 표정의 색으로).
바뀐 칸: 주인공 521, 정비사 525, 보관인 1284, 기록관 760 (100x100 중).

적용: `python tools/apply_pixellab_portraits.py` -> `assets/portraits/<인물>_<1|2>.png`(200x200, 최근접 2배, 2px 격자 100%).
확인: `shots/review/portraits_v6_final.png`(여덟 장 + 주인공 편집 원본), `portraits_v6_ingame.png`(대화창 세 장).

## 주인공 초상화를 PixelLab으로 다시 (2026-11-26, 사용자: "주인공 표정들 pixellab으로 npc 제작한 것처럼 주인공 제작 다시 하자")
그 전까지 주인공 기본 표정은 Gemini G04 원화를 줄인 것이었다(`raw_gen/n09_1_gemini.png`, 결의는 그 그림의 PixelLab 편집 `n09_2_gemini_edit.png`).

### 기본 표정 시안 7장 (42회: 6회 x 7, `hero_gen/`)
`create_image_pro_flash`, 100x100, no_background. 설명(공통): Dialogue portrait, head and shoulders bust, three-quarter view facing RIGHT,
looking slightly down to the right. Prisoner N-09 ...: a lean young man with pale grey-blue skin, wild spiky white hair swept back and up,
sharp narrow eyes glowing bright teal, calm tired serious expression, mouth closed. ... thick dark charcoal scarf (muffler) ... black padded work
jacket with chest pockets. A few thin wisps of teal haze rise from the scarf. Muted dark palette ... teal eyes as the only bright colour.

| 파일 | 화풍 기준 | seed | 평가 |
|---|---|---|---|
| hero_a_s3 / a_s11 / a_s7 | 정비사 초상화 `raw_gen/mechanic_1.png` | 3 / 11 / 7 | 피부가 갈색·회갈색으로 나와 다른 사람처럼 보임(정비사의 살색이 옮겨 옴). a_s3은 아래에 줄이 생김 |
| hero_c_s5 / c_s9 | 정비사 초상화, 색 따라 하기 끔(`style_options.color_palette=false`), "very pale bluish-white skin (NOT tanned)" | 5 / 9 | 피부는 희지만 눈빛이 약하고 얼굴이 납작한 선화 느낌 |
| **hero_b_s3** | 예전 주인공 초상화 `raw/hero_style_100.png`("same character's current portrait. Keep his design ... paint him again with richer pixel-art shading") | 3 | **선택**: 같은 사람으로 보이고(머리 모양·창백한 푸른 피부·빛나는 청록 눈), 머리가 더 크게 잡혀 NPC 초상화와 크기가 맞는다 |
| hero_b_s11 | 위와 같음 | 11 | 좋음. 머리 왼쪽에 떨어진 점이 있고 얼굴이 더 옆을 봄 (예비) |

배운 것: 다른 인물의 초상화를 화풍 기준으로 넣으면 살색이 따라온다. 같은 인물을 다시 그릴 때는 그 인물의 예전 그림을 기준으로 넣고 "다시 그려라"고 쓴다.
비교판 `shots/review/hero_portrait_candidates.png`(왼쪽 위가 예전 것), 크게 본 것 `hero_portrait_zoom.png`.

### 결의 표정 (12회: 6회 x 2)
`edit_image_pro_flash`(method text, 색 고정 끔, 원본 = hero_b_s3): "Change only the facial expression to DETERMINED: he lifts his gaze and looks
forward instead of down, eyes opened a little wider, eyebrows lowered and drawn together, a faint confident smile ... eyes MUST stay bright glowing teal.
Keep everything else exactly the same ...". seed 7(**선택**)·seed 3. 두 장 모두 얼굴 밖은 거의 그대로였다(달라진 칸 120·147 중 얼굴 밖 30·34).
`hero_gen/hero_b_s3_mood_s7.png` -> `raw_gen/n09_2.png`. 얼굴 사각형은 (36,30)-(78,72)로 바꿈(`tools/apply_pixellab_portraits.py`의 FACE).
확인: 실제 대화창 `shots/review/hero_portrait_ingame.png`(위 기본, 아래 강화를 샀을 때의 결의 + 정비사의 씩 웃음).

### 사용자 선택으로 바꿈 (2026-11-26, 같은 날)
시안 비교판을 본 사용자가 **아랫줄 세 번째 = `hero_c_s5`**(정비사 초상화를 화풍 기준으로, 색 따라 하기 끔, seed 5)를 골랐다("아래 줄 3번째 걸로 스타일을 뽑자").
Claude Code가 골랐던 b_s3(예전 초상화를 다시 그린 것)보다 선이 또렷하고 피부가 희며 머플러가 푸른 쪽이다: NPC 초상화와 같은 그림체.
- 기본 표정 `raw_gen/n09_1.png` = `hero_gen/hero_c_s5.png` (알파 0/255로만 정리)
- 결의 표정 (12회: 6회 x 2): 같은 편집 지시, 원본 = hero_c_s5, seed 7(**선택**)·seed 3. 얼굴 밖은 거의 그대로(달라진 칸 86·97).
  `hero_gen/hero_c_s5_mood_s7.png` -> `raw_gen/n09_2.png`. 얼굴 사각형 (44,28)-(74,62).
- b_s3와 그 결의 표정(`hero_b_s3*.png`)은 `hero_gen/`에 남겨 둔다.
확인: `shots/review/hero_portrait_final.png`(두 표정), `hero_portrait_ingame_crop.png`(실제 대화창, 위 기본·아래 결의).

