# slum v6 동작 생성 기록 (2026-11-23, Claude Code)
base: `raw/base.png` = designs_v6/slum_1.png (96, east, 20색 이하, 알파 0/255, 발 아래 2px).
뼈대 estimate_skeleton(0.1) + animate_with_skeleton_v3(write_motion_frames, side/east, seed 5), 설명에 위험 부위 유지 + no effects.
pixminimax 폴더는 frame_0=base(입력 반환), skeleton 폴더는 frame_0부터 생성 프레임. 시트 `shots/pixellab_test/slum_v6_<동작>.png`(첫 칸 base, 3배). 이탈 = base 팔레트 밖 픽셀 비율.

| 동작 | 도구·옵션 | 비용 | 위험 부위 유지 | 평가 |
|---|---|---|---|---|
| walk | skeleton 8 | 3 | 손톱 대부분 안 보임(연보라 사라짐) | 보통 |
| attack | skeleton 6 | 3 | 유지(들어 올려 내려 할큄) | 좋음 |
| hurt | skeleton 4 | 3 | 유지 | 좋음 |
| death | skeleton 8 | 3 | - | 좋음(무릎 꿇고 엎어짐, 누운 몸이 캔버스 끝에 닿음) |
