# 보스 이름 카드 상반신 boss_cards_v6 생성 기록 (2026-11-26, Claude Code)

배경: 보스 등장씬의 이름 카드(Codex T34·T47)가 예전 디자인이었다(크래셔는 웃통 벗은 대머리 남자, 아크는 밝은 만화풍 장교, 문지기는 카드 없음).
지금 보스 그림(PixelLab v6)과 같은 인물로 다시 만든다(docs/opus/TASKS.md O4). 36회 사용(장당 6회), 남은 약 1248회.

## 공통
- 도구: `create_image_pro_flash`, 208x200(장당 6회), no_background, seed 3·11.
- style_image: 주인공 대화 초상화 `portraits_v6/raw_gen/n09_1.png`(100x100, upload),
  usage "Art style, outline, shading, detail level and pixel scale only: a dialogue portrait from the same game. Do not copy this character, his colours, his hair or his clothes."
- style_options: color_palette **false**(주인공의 살색·옷 색이 따라오지 않게), outline·detail·shading true.
- 디자인은 각 보스의 GENERATION_LOG.md 설명을 그대로 옮겼다. 방향은 카드 글자 쪽(왼쪽)을 보는 3/4 시점, 허리에서 자른 상반신.

## 설명 (영문 그대로)
- crasher: Upper-body portrait (head, shoulders and chest only, cropped at the waist) of Crasher, a huge hulking scrap-metal brute boss, three-quarter view facing left. He is a walking furnace made of armor, not a human: enormous rounded rusty orange shoulder plates, riveted rusty orange and dark brown armor plates with weld seams, a small helmeted head sunk low between the huge shoulders with two narrow glowing orange eye slits, a glowing orange-red furnace core set in the middle of the chest, two black exhaust pipes rising behind the shoulders with sooty tips. No bare skin, no human face, no hair. Heavy, menacing. Colours: rusty orange, dark brown, charcoal grey, glowing orange-red core only.
- ark: Upper-body portrait (...) of Chief Warden Ark, the cold commander of a prison tower, three-quarter view facing left. A gaunt, pale grey thin face with sharp cheekbones and glowing teal eyes, a black peaked officer cap with a small teal diamond badge, a long black military greatcoat with a high upturned collar and teal lining, a dark armoured shoulder pad set with a teal crystal, three small teal vials on the chest, a black gloved hand holding a slim black officer's baton across the chest. Elegant, severe, narrow silhouette. Colours: black, dark grey, pale grey skin, teal accents only.
- gatekeeper: Upper-body portrait (...) of the Gatekeeper, a prison gate warden in heavy black steel full plate armour, three-quarter view facing left. A closed great helm with a single glowing teal eye slit, big rusted copper shoulder plates with rivets, a tall rusty iron-barred tower shield held at the front edge of the picture, a short spiked iron mace raised in the other hand, a ring of brass keys hanging at the belt. Heavy, stern, unmovable. Colours: dark steel grey, black, rusted copper, brass, a single teal eye glow only.

## 시안 평가 (비교판 `shots/review/boss_cards_v6_options.png`: 게임 그림 3배 | 1안 | 2안)
| 파일 | seed | 색 | 평가 |
|---|---|---|---|
| raw_gen/crasher_1.png | 3 | 13 | 디자인은 맞으나 색이 적어 갈색으로 탁하다 |
| raw_gen/crasher_2.png | 11 | 62 | 밝은 녹슨 주황 어깨판·가슴 용광로·배기관이 게임 그림의 색과 가장 가깝다 -> **선택** |
| raw_gen/ark_1.png | 3 | 27 | 어깨 장갑의 청록 결정, 약병 셋, 지휘봉이 게임 그림과 같다 -> **선택** |
| raw_gen/ark_2.png | 11 | 36 | 비슷하나 어깨 결정이 작고 얼굴이 어둡다 |
| raw_gen/gatekeeper_1.png | 3 | 45 | 구리 어깨판·쇠창살 방패·철퇴·황동 열쇠·청록 눈구멍이 모두 또렷하다 -> **선택** |
| raw_gen/gatekeeper_2.png | 11 | 33 | 비슷하나 어둡고 열쇠가 작다 |

사용자가 다른 시안을 고르면 `tools/apply_pixellab_boss_cards.py`의 CARDS에서 이름만 바꾸고 다시 돌린다.
헤이즈 심장은 사람이 아니라 새로 뽑지 않았다(지금 본체 v6_heart_core_3 + 손 heart_hand_idle_1을 그대로 배치).

## 굽기
`python tools/apply_pixellab_boss_cards.py`: 구역 카드 배경(zone_foundry·zone_haze·zone_cell)을 0.5배로 어둡게 + 인물 뒤에 구역 빛 색을 옅게,
상반신은 알파 영역으로 잘라 최근접 2배(도트 2px), 오른쪽 끝에서 140px, 허리가 카드 아래 끝. 예전 카드는 `assets/concept/boss_cards_old/`.
