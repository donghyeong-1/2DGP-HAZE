# 헤이즈 망령 wraith v6 생성 기록 (2026-11-25, Claude Code)

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
- 모아 보기: `shots/pixellab_test/wraith_v6_all.png`(3배, 첫 칸 base), 게임 그림 전체 `shots/review/enemies5_v6_baked.png`,
  실제 창 `shots/review/enemies5_v6_ingame.png`.

## 디자인 (5회)
캔버스 64x64 (간수 64 조각), 결과 39x63도트(화면 78x126px). `raw_gen/wraith_1.png`. 한 장으로 통과(비교판 `shots/review/enemies5_v6_designs.png`: 간수·사냥개·드론 옆).
설명(영문 그대로, 앞에 "Side view, facing right" 뒤에 색·크기 문장): A haze wraith, a ghost made of dark teal mist: a thin humanoid upper body with long thin arms hanging forward and clawed fingers, a pointed hooded head with two bright glowing eyes, and instead of legs a wispy curling tail of mist trailing down. It floats in the air, leaning slightly forward.

## 기준 그림
`raw/base.png` = 80x80 캔버스.

## 동작 (4회)
| 동작 | 장 | 평가 | 게임에 쓴 번호 |
|---|---|---|---|
| float | 4 | 좋음: 안개 끝이 흔들림 | 1, 2, 3, 4 |
| grab | 8 | 좋음: 1~2번 팔을 뒤로, 3~6번 앞으로 뻗음 | 1, 2, 4 |
| hurt | 4 | 1번 큰 별. 3번(몸을 젖힘)의 불티를 지움 | 3 (clean) |
| death | 8 | 좋음: 가늘어지다 조각으로 흩어짐 | 3, 5 (옛 세트와 같은 2장) |

적용: `python tools/apply_pixellab_char.py wraith` -> `assets/sprites/unified/v6_wraith_*.png`(최근접 2배), `skin_wraith.json`.
옛 세트 이름(`enemy_wraith_*`)을 새 그림으로 바꿔 그린다(게임 코드 그대로, 장수도 그대로).
