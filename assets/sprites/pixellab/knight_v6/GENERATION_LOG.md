# knight v6 동작 생성 기록 (2026-11-23, Claude Code)
base: `raw/base.png` = designs_v6/knight_2.png (96, east, 20색 이하, 알파 0/255, 발 아래 2px).
뼈대 estimate_skeleton(0.1) + animate_with_skeleton_v3(write_motion_frames, side/east, seed 5), 설명에 위험 부위 유지 + no effects. idle·vanish·appear_gen은 pixminimax.
pixminimax 폴더는 frame_0=base(입력 반환), skeleton 폴더는 frame_0부터 생성 프레임. 시트 `shots/pixellab_test/knight_v6_<동작>.png`(첫 칸 base, 3배). 이탈 = base 팔레트 밖 픽셀 비율.

| 동작 | 도구·옵션 | 비용 | 위험 부위 유지 | 평가 |
|---|---|---|---|---|
| idle | pixminimax 4, first=last | 1 | 검 유지 | 좋음 |
| walk | skeleton 8 | 3 | 검 유지 | 좋음(검 끝이 오른쪽 끝에 닿음) |
| slash | skeleton 6 | 3 | 1~2번 검이 뒤로 들려 거의 안 보임 | 보통 |
| vanish | pixminimax 4 | 1 | 몸이 결정 조각으로 부서져 사라짐 | 좋음 |
| appear_gen | pixminimax 4, first=last | 1 | - | 다시(끝 프레임에 검이 없음) |
| appear | vanish를 거꾸로 이어 붙임(조각→기준 그림), 로컬, 무료 | 0 | 유지 | 좋음 |
| hurt | skeleton 4 | 3 | 유지, 1번 어두운 덩어리 | 보통 |
| death | skeleton 8 | 3 | 검 쥔 채 무릎→엎어짐 | 좋음(캔버스 끝에 닿음) |
