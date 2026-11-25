# 헤이즈 심장 기계 손 heart_hand v6 생성 기록 (2026-11-25, Claude Code)

배경은 본체(`../heart_core_v6/GENERATION_LOG.md`)와 같다. 오른손 그림 하나를 만들고 왼손은 게임이 좌우로 뒤집는다(옛 방식 그대로).

## 디자인 (18회: 6회 x 3장)
도구: `create_image_pro_flash`, 80x108(캔버스로 크기 맞춤), style_image = 간수 base 64 조각.

| 파일 | seed | 크기(도트) | 메모 |
|---|---|---|---|
| raw_gen/hand_1.png | 3 | 70x99 | 손가락이 가늘고 여섯 개처럼 보임, 어두움: 탈락 |
| raw_gen/hand_2.png | 11 | 75x103 | 통통한 손가락 넷 + 엄지, 손바닥의 큰 결정, 밝은 회색 판 -> **선택**(화면 150x206px, 옛 손 148x204) |
| raw_gen/hand_3.png | 7 | 74x107 | 비슷하지만 음영이 복잡함 |

2·3번 설명(영문 그대로): Front view, palm facing the viewer, no arm, no body. A giant floating mechanical right hand (armoured gauntlet)
of a machine boss, big and heavy like a wrecking tool. Exactly five digits: four very thick, chunky, blocky metal fingers hanging straight
down side by side, each made of three fat armoured segments with a thin teal light line, and one fat thumb sticking out diagonally on the
left side. A wide square palm plate with one large glowing teal diamond crystal in its centre. Above it a heavy wrist cuff with a small
teal diamond emblem and one thick cable stub on top. Lighter gunmetal grey plates with darker gaps so the shapes read clearly, teal lights
only. The hand fills the canvas, wrist at the top, fingertips at the bottom.
(1번은 "four short cable stubs", 손가락 굵기 지시 없음.)

`raw/base.png` = hand_2를 40색으로 줄여 128x128 가운데에.

## 동작 (4회, `animate_image_pixminimax`, seed 5)
| 폴더 | 장 | 평가 | 게임에 쓴 번호 |
|---|---|---|---|
| idle | 4 (first = last) | 좋음: 손가락이 조금 벌어졌다 모임 | 0, 2 |
| fist | 8 | 좋음: 4번부터 꽉 쥔 주먹 | 5 = 치켜든 주먹, 7 = 내려친 주먹 |
| palm | 8 | 1~3번 손가락을 벌림(2번은 흰 섬광), 4번 결정이 밝아짐, 7번 결정이 흰색. 6·8번은 손 전체가 청록으로 물듦(뺌) | 4 = 광선 예고, 7 = 발사 |
| stun | 8 | 4번부터 새까만 실루엣이라 못 씀. 3번(조금 기운 손)만 가져와 도구에서 불빛을 반쯤/전부 끔 | 3 (가공 2장) |

적용: `python tools/apply_pixellab_heart.py` -> `assets/sprites/unified/v6_heart_hand_(idle|fist|palm|stun)_N.png`(260x260, 옛 기준점 규칙 그대로).
모아 보기 `shots/pixellab_test/heart_hand_v6_all.png`.
