# 간수 guard v6 생성 기록 (2026-11-23, Claude Code)
base: `raw/base.png` = hero_v6_test/raw/designs/guard_1b_3_20c.png (96, east, 20색, 알파 0/255, 발 y93).
뼈대: estimate_skeleton(0.1). 모든 동작 animate_with_skeleton_v3, write_motion_frames, side/east, seed 5, 각 3회.
description: "heavily armored prison guard in dull blue-grey plate armor and helmet with a thin glowing orange visor slit and a small orange chest light, holding a large riot shield with a warning mark in front, and a short heavy baton with an orange glowing tip gripped in the other hand; no effects".
프레임은 모두 생성 프레임(frame_0부터, 입력 반환 없음). 시트: shots/pixellab_test/guard_v6_<동작>.png(첫 칸 base, 3배).

| 동작 | 프레임 | 곤봉 손 유지 | 평가 |
|---|---|---|---|
| walk | 8 | 유지(방패 앞) | 좋음. 처음·끝이 이어지게는 따로 확인 필요 |
| swing | 6 | 유지, 5번에 곤봉이 가는 막대로 늘어남 | 보통 |
| heavy | 6 | 4번에 흰 궤적 효과, 곤봉이 잠깐 사라짐 | 보통(4번 손질 필요) |
| bash | 6 | 곤봉이 방패 쪽으로 옮겨 감, 5~6번 작은 흰 점 | 보통 |
| hurt | 4 | 유지(2번 곤봉 늘어남) | 좋음 |
| death | 8 | 방패·곤봉 놓침(의도) | 좋음 |
