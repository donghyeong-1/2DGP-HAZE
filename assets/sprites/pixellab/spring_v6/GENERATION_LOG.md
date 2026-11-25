# 헤이즈 샘 spring v6 생성 기록 (2026-11-25, Claude Code)

배경: 이벤트 방 소품. 임시 그림은 코드로 그린 돌 그릇이었고, Codex T52 결과(`assets/sprites/forge/spring_v1/`, 저장소에 올리지 않음)는
1px 단위 그림(2px 격자 일치율 0.59)이었다. 사용자 결정(2026-11-25): 캐릭터 옆에 서는 도트 그림은 PixelLab으로 만든다.

## 디자인 시안 (10회)
도구: `create_image_pro_flash`, 64x64, no_background, style_image = 간수 base를 몸 둘레로 잘라 64x64에 놓은 것(upload),
usage "Art style, detail level, outline and pixel scale only. Same world as this guard. Do not draw the character."

설명(영문 그대로): Side view game prop, no character. A haze spring: a low round basin built from scrap metal plates and old bricks
around a broken drain pipe that rises from the floor and bends over the basin. The basin is full of glowing teal liquid with a few sharp
teal crystals growing out of the surface. The rim, bricks and pipe are dark grey-blue and rusty; only the liquid surface and the crystals
are bright teal. Flat bottom sitting on the ground, wide and low, about 58 pixels wide and 36 pixels tall, centered at the bottom of the canvas.

| 파일 | seed | 크기(도트) | 화면 크기 | 색 | 메모 |
|---|---|---|---|---|---|
| raw_gen/spring_1.png | 3 | 61x50 | 122x100px | 67 | 관이 그릇 위로 굽어 방울이 맺힘, 벽돌 그릇이 깔끔 -> **선택** |
| raw_gen/spring_2.png | 11 | 60x51 | 120x102px | 34 | 관 입구가 정면, 결정이 더 많고 돌무더기가 큼 |

요청한 36도트보다 높게(50) 나왔지만 주인공(화면 122px) 옆에서 무릎~허리 높이의 그릇으로 읽혀 그대로 쓴다.

## 그림 (6회)
| 그림 | 도구 | seed | 평가 | 게임에 쓴 것 |
|---|---|---|---|---|
| ripple (4+1장) | animate_image_pixminimax (first = last = base) | 5 | 좋음: 수면이 일렁이고 2~3번에 관에서 방울이 떨어지며 결정이 희게 반짝인다. 관·벽돌은 움직이지 않음 | 0, 1, 2, 3 |
| dry.png | edit_image_pro_flash (text) | 3 | 좋음: 물이 빠지고 결정이 회색 그루터기로. 관·벽돌 위치 그대로, 청록 0칸 | 그대로 |

ripple 설명: The glowing teal liquid surface in the basin ripples gently and the teal crystals glint and shimmer; one drop falls from the
pipe into the pool. The pipe, bricks and basin stay perfectly still and do not move.
dry 설명: The spring has dried up. Remove all the glowing teal liquid: the basin is empty and dark inside, with a dull grey dry bottom.
The crystals are dead: grey, cracked, broken into short stumps with a few grey shards lying in the basin. No glow, no teal or cyan colour
anywhere, no drip from the pipe. Keep the pipe, the bricks, the metal plate and the overall shape, size and position exactly the same.

적용: `python tools/apply_pixellab_event.py spring` -> `assets/ui/event_spring_1~4.png`, `event_spring_dry.png`(128x102, 최근접 2배,
2px 격자 100%, base + dry의 색을 48색으로 줄여 다시 칠함: UI 그림 64색 제한). 게임은 물결 4장을 장당 0.3초로 돌린다(`src/events.py`).
실제 창 확인: `shots/review/event_v6_ingame.png`(슬럼·공장, 마른 샘).
