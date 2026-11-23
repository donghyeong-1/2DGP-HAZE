# thrower v6 동작 생성 기록 (2026-11-23, Claude Code)
base: `raw/base.png` = designs_v6/thrower_1.png (96, east, 20색 이하, 알파 0/255, 발 아래 2px).
뼈대 estimate_skeleton(0.1) + animate_with_skeleton_v3(write_motion_frames, side/east, seed 5), 설명에 위험 부위 유지 + no effects.
pixminimax 폴더는 frame_0=base(입력 반환), skeleton 폴더는 frame_0부터 생성 프레임. 시트 `shots/pixellab_test/thrower_v6_<동작>.png`(첫 칸 base, 3배). 이탈 = base 팔레트 밖 픽셀 비율.

| 동작 | 도구·옵션 | 비용 | 위험 부위 유지 | 평가 |
|---|---|---|---|---|
| walk | skeleton 8 | 3 | 매 프레임 달군 고철 유지 | 좋음 |
| throw | skeleton 6 | 3 | 3~5번 고철이 자루 쪽으로 가려짐, 6번 다시 손에 | 보통 |
| hurt | skeleton 4 | 3 | 1번 자루 위에 주황 빛 덩어리 | 보통 |
| death | skeleton 8 | 3 | 놓침(의도) | 좋음(자루 위로 뒤로 쓰러짐) |
