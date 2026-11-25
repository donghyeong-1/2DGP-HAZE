# 문지기 gatekeeper v6 생성 기록 (2026-11-25, Claude Code)

배경: Codex T50 그림(키 165px)은 1px 단위 그림이라 v6 캐릭터(도트 2px, PixelLab)와 그림체·도트 크기가 달랐다(사용자 지적).
v6 방식(간수를 화풍 기준으로 PixelLab에서 디자인 → 동작 → `tools/apply_pixellab_char.py`)으로 다시 만든다.

## 디자인 시안 (12회 사용, 남은 약 1600회)
도구: `create_image_pro_flash`, 128x128, no_background, style_image = guard_v6/raw/base.png(upload),
usage "Art style, detail level and pixel scale only ... Same world and faction as this guard, but do not copy the character".
설명: 오른쪽을 보는 옆모습, 검은 강철 중갑 + 녹슨 구리색 어깨판, 청록 눈구멍 하나, 쇠창살 탑 방패(어깨~정강이), 짧은 철퇴, 허리의 황동 열쇠.

| 파일 | seed | 키(도트) | 화면 키 | 색 | 메모 |
|---|---|---|---|---|---|
| raw_gen/gatekeeper_1.png | 3 | 104 | 208px | 20 | 방패가 몸 앞에 비스듬히, 철퇴를 낮게 듦 |
| raw_gen/gatekeeper_2.png | 11 | 113 | 226px | 25 | 더 크고 방패가 곧게 섬, 어깨판이 큼 |

참고 키: 주인공 61도트, 간수 64, 크래셔 122. 요청한 84도트보다 둘 다 크게 나왔다.
비교: `shots/review/gatekeeper_v6_designs.png` (주인공·간수·1안·2안·크래셔·T50, 같은 바닥).

## 기준 그림 `raw/base.png` (사용자가 1안 선택)
gatekeeper_1을 128 캔버스 가운데로 옮기고 발을 y126에 맞춤. 20색, 알파 0/255, bbox (20,22)-(112,126), 키 104도트(화면 208px).

## 동작 (약 22회 사용)
뼈대: estimate_skeleton(0.1). idle만 pixminimax(first=last, 4장, 1회, frame_0 = base), 나머지는 animate_with_skeleton_v3
write_motion_frames, side/east, 각 3회. 팔레트 이탈은 모두 0%. 시트 `shots/pixellab_test/gatekeeper_v6_<동작>.png`(첫 칸 base, 3배).

| 동작 | 장 | seed | 평가 | 게임에 쓴 번호 |
|---|---|---|---|---|
| idle | 4+1 | 5 | 좋음(작은 숨쉬기) | 0, 2 |
| walk | 8 | 5 | 좋음 | 0~7 |
| bash | 6 | 5 | 좋음: 웅크림 -> 낮게 내지름 -> 섬 | 1, 4, 5 |
| heavy_try1 | 6 | 5 | 다시: 2~3번에서 방패와 철퇴가 사라짐 | - |
| heavy | 6 | 9 | 보통: 0~2번 철퇴를 머리 위로, 4번 앞으로 내려찍음. 3~5번은 방패가 옆으로 서서 얇게 보인다 | 1, 4, 5 |
| call | 4 | 5 | 좋음: 철퇴를 치켜든다 | 0, 2 |
| hurt | 4 | 9 | 0번 뭉개짐, 2번 좋음 | 2 (+ death 1번을 벽에 부딪혀 비틀로) |
| death | 8 | 5 | 좋음: 무릎 -> 엎어짐 -> 누움 | 1, 3, 5 |

적용: `python tools/apply_pixellab_char.py gatekeeper` -> `assets/sprites/unified/boss_gatekeeper_*`(256x256, 최근접 2배), `skin_gatekeeper.json`.
