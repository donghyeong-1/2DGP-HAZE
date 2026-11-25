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
