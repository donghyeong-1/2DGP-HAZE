# drone v6 동작 생성 기록 (2026-11-23, Claude Code)
base: `raw/base.png` = designs_v6/drone_2.png (96, east, 20색 이하, 알파 0/255, 발 아래 2px).
네 발/기계라 사람 뼈대가 안 맞아 모든 동작 animate_image_pixminimax(side/east, 'keep exact same design, do not redraw or restyle' + no effects), 반복·복귀 동작은 last=base.
pixminimax 폴더는 frame_0=base(입력 반환), skeleton 폴더는 frame_0부터 생성 프레임. 시트 `shots/pixellab_test/drone_v6_<동작>.png`(첫 칸 base, 3배). 이탈 = base 팔레트 밖 픽셀 비율.

| 동작 | 도구·옵션 | 비용 | 위험 부위 유지 | 평가 |
|---|---|---|---|---|
| fly | pixminimax 4, first=last | 1 | 노즐 유지 | 좋음 |
| aim | pixminimax 4 | 1 | 유지 | 좋음(작은 기울기) |
| fire_try1 | pixminimax 8, first=last, seed 5 | 1 | - | 다시(노즐 아래 불꽃 줄기를 그림) |
| fire | pixminimax 8, first=last, "absolutely no flame jet" seed 9 | 1 | 노즐 끝만 주황으로 밝아짐 | 좋음 |
| hurt_try1 | pixminimax 4, seed 5 | 1 | - | 다시(불꽃 튐) |
| hurt | pixminimax 4, "no sparks" seed 9 | 1 | 유지 | 보통(2~3번 작은 불티가 아직 남음) |
| wreck | pixminimax 8 | 1 | - | 좋음(기울며 떨어져 바닥에서 부서짐) |
