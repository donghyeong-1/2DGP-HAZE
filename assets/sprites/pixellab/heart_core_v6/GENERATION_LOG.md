# 헤이즈 심장 본체 heart_core v6 생성 기록 (2026-11-25, Claude Code)

배경: 옛 그림(Codex T45)은 2px 격자는 맞았지만 평평한 색면이라 PixelLab으로 만든 다른 캐릭터와 화풍이 달랐다.
사용자 결정(2026-11-25): 캐릭터 그림은 PixelLab으로 만든다. 디자인은 Gemini G02 원화(`heart_core.png`)와 옛 그림이 같은 설정이라 그것을 글로 옮겼다.

## 크기 문제와 해법
본체는 화면 약 870x470px = 435x235점이라 PixelLab 캔버스 한도(256)를 넘는다. 좌우 대칭이므로 **왼쪽 절반만(224x240) 만들고
`tools/apply_pixellab_heart.py`가 좌우로 뒤집어 붙인다**(오른쪽 끝 = 가운데 절단선). 결과 448x240점 = 896x480px.

## 디자인 (9회)
도구: `create_image_pro_flash`, 224x240, seed 3, style_image = 간수 base를 64x64로 자른 것,
usage "Art style, detail level, outline, metal shading and pixel scale only ... Do not draw the character." 한 장으로 통과.
설명(영문 그대로): Front view, flat orthographic, no perspective, no character. This image shows ONLY THE LEFT HALF of a huge, perfectly
symmetric, fortress-like machine called the Haze Heart. The machine is cut vertically through its exact centre and the cut lies exactly on
the RIGHT EDGE of the canvas, running the full height of the machine. From the right edge (the centre) going left: half of a tall armoured
central gate, a closed heavy door panel with angular grooves, whose centre seam is a thin glowing teal line exactly at the right edge;
above the gate, half of a winged emblem plate with a teal diamond at the right edge; left of the gate a thick pillar with bolts; then a
broad angular wing block that tapers into a horizontal blade pointing left, with a glowing teal light strip along it; thick curved cables
arching over the top left; a heavy stepped base along the bottom. Dark gunmetal and charcoal armour plates with teal light accents only.
The half machine fills the whole canvas and touches the right edge; nothing else is drawn.

`raw_gen/core_half_1.png`(34색, 오른쪽 끝 열 240칸 중 238칸이 불투명 = 절단선에 붙음) -> `raw/base.png`.
비교판 `shots/review/heart_v6_designs.png`(뒤집어 붙인 새 본체와 옛 본체).

## 동작 (2회, `animate_image_pixminimax`, seed 5, 각 8장)
| 폴더 | 첫 장 | 내용 | 게임에 쓴 번호 |
|---|---|---|---|
| open | base | 문이 왼쪽으로 밀려 들어가며 방 안의 결정 절반이 드러난다. 다른 부분은 그대로 | 0 = 닫힘, 1 = 살짝 열림(닫힌 채 맥동), 7 = 열림 |
| dying | open 7번의 방 안쪽을 어두운 색으로 막은 것(`raw/open_filled.png`) | 결정이 깨져 흩어지고 불이 꺼지며 금이 간다. 5번부터는 거의 검은 실루엣이라 쓰지 않음 | 2 = 쓰러짐 1, 4 = 쓰러짐 2 |

열린 방 안쪽은 투명으로 나온다: 적용 도구가 열린 그림의 구멍 자리를 가장 어두운 색으로 막는다.
맞는 순간(hurt)은 열린 그림의 결정을 희게 밝힌 것(도구에서 가공).

적용: `python tools/apply_pixellab_heart.py` -> `assets/sprites/unified/v6_heart_core*_N.png`(900x580, 결정 가운데가 (450,312), 기준점 (450,462)),
`skin_heart.json`. 구운 그림 `shots/review/heart_v6_baked.png`, 실제 창 `shots/review/heart_v6_ingame.png`.
