# 최종 보스 아크 ark v6 생성 기록 (2026-11-25, Claude Code)

배경: 옛 그림(Codex T20)은 v6 캐릭터와 화풍·도트 크기가 달랐다. 사용자 결정(2026-11-25): 캐릭터 그림은 PixelLab으로 만든다.
디자인은 이미 검토를 통과한 Gemini G02 원화(`assets/sprites/gemini/boss_designs_v1/ark_side.png`: 챙모자, 긴 검은 코트와 청록 안감,
어깨·팔뚝 장갑의 청록 결정, 가슴·허리의 청록 약병, 지휘봉)를 글로 옮겼다. 원화 그림을 입력으로 넣지는 않았다.

## 디자인 시안 (10회)
도구: `create_image_pro_flash`, 96x88(키를 캔버스로 맞춤), no_background, style_image = 간수 base를 64x64로 자른 것,
usage "Art style, detail level, outline and pixel scale only. Same world as this guard, same head size, but a different, taller and slimmer character."

설명(영문 그대로): Side view, facing right, full body, standing upright on the ground. Chief Warden Ark, the cold commander of a prison tower:
a tall, slim, long-legged man in a long black military greatcoat that reaches his ankles, high upturned collar, teal coat lining visible at the hem,
a black peaked officer cap with a small teal diamond badge, pale grey face with glowing teal eyes. Dark armoured shoulder pad and forearm guard
each set with a teal crystal, three small teal vials on the chest and two on the belt, black gloves, dark trousers and boots. His front hand holds
a slim black officer's baton pointing down and forward. Elegant, narrow silhouette, taller and slimmer than the guard in the style image.
Black and dark grey with teal accents only. The whole figure fits inside the canvas, head near the top, feet at the bottom.

| 파일 | seed | 키(도트) | 화면 키 | 색 | 메모 |
|---|---|---|---|---|---|
| raw_gen/ark_1.png | 3 | 83 | 166px | 35 | 외곽선이 굵고 대비가 셈, 얼굴이 밝음 |
| raw_gen/ark_2.png | 11 | 84 | 168px | 44 | 실루엣이 깔끔하고 코트 밑단의 청록 안감이 원화와 같음 -> **선택** |

참고 키: 간수 64도트, 문지기 104, 옛 아크는 화면 158px. 비교판 `shots/review/ark_v6_designs.png`(간수·기사·문지기·1안·2안·옛 아크).
디자인이 이미 정해진 것(G02)이라 두 장 중 원화에 가까운 쪽을 Claude Code가 골랐다. 1안으로 바꾸려면 base를 바꾸고 동작을 다시 뽑는다(약 13회).

## 기준 그림 `raw/base.png`
ark_2를 40색으로 줄이고(가까운 색 합치기) 128x112 캔버스에 옮김(발 아래 2줄, 동작 여유). bbox (34,26)-(81,110).

## 동작 (13.1회)
걷기만 뼈대(estimate_skeleton 0.1 + animate_with_skeleton_v3 write_motion_frames 8, side/east, seed 5, 3회), 나머지는 `animate_image_pixminimax`
(side/east, seed 5, 각 1회, 복귀 동작은 last = base, frame_0 = base). pixminimax는 탄환·베는 호·충격 별을 그려 넣는다:
`tools/apply_pixellab_char.py`의 clean_body(base 색이 아닌 칸을 지우고 가장 큰 덩어리만 남김)로 몸만 남겼다.
모아 보기 `shots/pixellab_test/ark_v6_all.png`(3배, 첫 칸 base), 구운 그림 `shots/review/ark_v6_baked.png`.

| 동작 | 장 | 평가 | 게임에 쓴 번호 |
|---|---|---|---|
| idle | 4 | 좋음 | 0, 2 |
| walk (skeleton) | 8 | 보통: 느리고 곧은 걸음, 보폭이 작다 | 0, 2, 4, 6 |
| hurt | 4 | 1번은 큰 충격 별. 2번(상체를 젖힘)의 별을 지움 | 2 |
| barrage | 8 | 2번 손을 당김(탄 줄기가 그려짐 -> 지움), 4번 큰 탄환, 6번 손바닥을 내지른 깨끗한 자세 | 2, 6 |
| slash | 8 | 1번 낮게 웅크림, 2~3번 지휘봉을 뒤로, 4번 큰 청록 호(뺌), 5~6번 낮게 내디뎌 뻗음 | 2, 5, 6 (1번은 '나타남') |
| absorb | 8 | 좋음: 2~4번 팔을 활짝, 5~6번 가슴으로 모음 | 3, 5 |
| overcharge | 8 | 1~3번 웅크려 팔 교차, 4번 팔을 젖힘, 5~6번 큰 별·호(뺌) | 2, 4 |
| field | 8 | 1~2번 무릎 꿇고 손을 듦, 3번 흰 줄기(뺌), 4~6번 손바닥을 바닥에 | 2, 5 |
| vanish | 8 | 좋음: 2번부터 조각으로 흩어짐 | 2 |
| phase | 4 | 1번 붉은 초승달(뺌). 3번(주먹을 치켜듦)의 붉은 점을 지움 | 3 |
| death | 8 | 좋음: 무릎 꿇고 고개 숙임 -> 엎어져 누움 | 3, 7 |

적용: `python tools/apply_pixellab_char.py ark` -> `assets/sprites/unified/v6_ark_*.png`(256x224, 최근접 2배), `skin_ark.json`.
옛 세트 이름(`boss_ark_*`)을 새 그림으로 바꿔 그린다(게임 코드·장수·히트박스 그대로).
실제 창 확인: `shots/review/ark_v6_ingame.png`(대기·탄막·사라짐·나타남·베기·걷기·흡수·과충전·장판·페이즈·피격·사망).
