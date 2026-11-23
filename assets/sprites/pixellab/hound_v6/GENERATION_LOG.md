# hound v6 동작 생성 기록 (2026-11-23, Claude Code)
base: `raw/base.png` = designs_v6/hound_1.png (96, east, 20색 이하, 알파 0/255, 발 아래 2px).
네 발/기계라 사람 뼈대가 안 맞아 모든 동작 animate_image_pixminimax(side/east, 'keep exact same design, do not redraw or restyle' + no effects), 반복·복귀 동작은 last=base.
pixminimax 폴더는 frame_0=base(입력 반환), skeleton 폴더는 frame_0부터 생성 프레임. 시트 `shots/pixellab_test/hound_v6_<동작>.png`(첫 칸 base, 3배). 이탈 = base 팔레트 밖 픽셀 비율.

| 동작 | 도구·옵션 | 비용 | 위험 부위 유지 | 평가 |
|---|---|---|---|---|
| run | pixminimax 8 | 1 | 눈·이빨 유지 | 좋음 |
| bite | pixminimax 8, last=base | 1 | 유지, 6번 작은 불티 | 보통(머리 내미는 폭이 작음) |
| pounce | pixminimax 8 | 1 | 유지 | 보통(7~9번 발밑 돌·먼지 그림, 앞으로 캔버스 끝 닿음) |
| hurt_try1 | pixminimax 4, last=base, seed 5 | 1 | - | 다시(붉은·흰 충격 효과) |
| hurt_try2 | pixminimax 4, "no impact flash..." seed 9 | 1 | - | 다시(더 큰 충격 별) |
| hurt | hurt_try1에서 base 팔레트 밖 픽셀과 떨어진 점을 로컬로 지움(무료) | 0 | 유지 | 보통(움직임 작음) |
| death | pixminimax 8 | 1 | 눈 어두워짐 | 좋음 |
