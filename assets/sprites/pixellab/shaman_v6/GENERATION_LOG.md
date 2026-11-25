# 누더기 무당 shaman v6 생성 기록 (2026-11-25, Claude Code)

배경: 옛 그림(Codex T36~T42)은 2px 격자는 맞았지만 PixelLab으로 만든 v6 캐릭터와 화풍·크기가 달랐다.
사용자 결정(2026-11-25): 캐릭터 옆에 서는 도트 그림은 PixelLab으로 만든다. 남은 일반 적 5종을 같은 날 한꺼번에 바꿨다.

방식(5종 공통):
- 디자인: `create_image_pro_flash` 1장(seed 3, 5회). PixelLab은 글로 적은 크기를 지키지 않으므로 **캔버스 크기로 크기를 맞췄다**.
  화풍 기준(style_image)은 캔버스 안에 들어가야 해서 간수 base를 64x64로 자른 것, 작은 캔버스는 사냥개 base의 조각(48x32, 64x48)을 썼다.
  usage "Art style, detail level, outline (metal shading) and pixel scale only ... do not copy".
- 기준 그림 `raw/base.png`: 시안을 40색 이하로 줄이고(가까운 색 합치기), 동작이 캔버스 밖으로 나가지 않게 넓은 캔버스에 옮겼다(땅 위는 발 아래 2줄, 떠 있는 것은 가운데).
- 동작: 전부 `animate_image_pixminimax`(side/east, seed 5, 각 1회). 반복·복귀 동작은 last = base. frame_0 = base(입력 반환).
  설명 끝에 "Keep the exact same design, colours and proportions; do not redraw or restyle. No effects ..."를 붙였지만 피격·사망에는
  충격 별·불티·핏방울이 자주 그려진다 -> `tools/apply_pixellab_char.py`의 'clean'(base 색이 아닌 칸과 10칸 미만 조각 제거)으로 지웠다.
- 모아 보기: `shots/pixellab_test/shaman_v6_all.png`(3배, 첫 칸 base), 게임 그림 전체 `shots/review/enemies5_v6_baked.png`,
  실제 창 `shots/review/enemies5_v6_ingame.png`.

## 디자인 (5회)
캔버스 64x72 (간수 64 조각), 결과 47x67도트(지팡이 포함, 화면 94x134px). `raw_gen/shaman_1.png`. 한 장으로 통과(비교판 `shots/review/enemies5_v6_designs.png`: 간수·사냥개·드론 옆).
설명(영문 그대로, 앞에 "Side view, facing right" 뒤에 색·크기 문장): A ragged slum shaman: a thin, hunched figure wrapped in layered tattered olive and brown rags with a hood, small bone and cloth charms hanging from the belt. One hand holds a tall crooked wooden staff upright in front; a glowing teal haze crystal is bound to the top of the staff. The face is hidden in the hood's shadow with two faint teal eyes. Bare bandaged feet.

## 기준 그림
`raw/base.png` = 96x96 캔버스.

## 동작 (6회)
| 동작 | 장 | 평가 | 게임에 쓴 번호 |
|---|---|---|---|
| idle | 4 | 좋음 | 0, 2 |
| walk | 8 | 보통: 느린 발끌기라 움직임이 작다 | 1~8 |
| cast_try1 | 8 | 다시: 2~4번에서 몸 전체가 청록으로 물들고 별·고리가 그려짐 | - |
| cast | 8 (seed 9, "Do not recolour ... no glow/rings/stars") | 좋음: 지팡이를 들어 올렸다 내림 | 2, 4, 6 |
| hurt | 4 | 1번은 큰 충격 별이 몸을 덮음. 2~3번의 별·핏방울은 지움 | 2, 3 (clean) |
| death | 8 | 좋음: 무릎 -> 지팡이를 놓치며 엎어짐 -> 누움 | 3, 5, 7 |

적용: `python tools/apply_pixellab_char.py shaman` -> `assets/sprites/unified/v6_shaman_*.png`(최근접 2배), `skin_shaman.json`.
옛 세트 이름(`enemy_shaman_*`)을 새 그림으로 바꿔 그린다(게임 코드 그대로, 장수도 그대로).
