# 보스 크래셔 crasher v6 생성 기록 (2026-11-23, Claude Code)
이번 작업 약 44회 사용 → 남은 1874.5회(Tier 1, 2026-12-23 갱신).

## 기준 그림 `raw/base.png`
- 출발: hero_v6_test/raw/designs/crasher_1b_2_20c.png(정면) → `rotate_image`(2회) 8방향 중 east(`hero_v6_test/raw/designs/crasher_rot/dir_2.png`).
- 정면 상태에서 손 수정 3회(edit_image_pro_flash 1, edit_image_pixen 2) 실패 → 비교 `shots/pixellab_test/crasher_hand_fix.png`.
- east 그림에서 손 영역만 인페인트 3회(마스크 x56 y60 w46 h42): `raw/hand_fix/inpaint_pf_1.png`(Pro Flash seed 5, 6회), `inpaint_pf_2.png`(Pro Flash seed 17, 6회), `inpaint_3.png`(inpaint_image seed 9, 10회). 비교 `shots/pixellab_test/crasher_hand_fix2.png`.
- **채택: inpaint_pf_2** — 주먹이 자루를 감싸고 자루가 주먹을 관통해 아래 망치 머리로 이어짐(망치 머리는 발 앞 바닥에 놓임). 원래 20색 팔레트로 되돌려 18색, 알파 0/255, 128 캔버스, bbox (41,0)-(100,126) 키 126(배기관 끝 포함, 몸통 약 120), 발 아래 여백 2px.
- 손 수정 전 그림: `raw/hand_fix/base_before_handfix.png`. 손·망치 영역 좌표(메인 세션 손질용): x 56~101, y 60~101.

## 동작
뼈대: estimate_skeleton(새 base). description: "huge hulking scrap-metal brute boss in rusty orange and dark brown patched armor plates with weld seams, two exhaust pipes rising from its back with sooty tips, a glowing orange furnace in its chest, its fist always gripping the handle of a big rusty sledgehammer; no effects". side/east, seed 5.
idle만 frame_0 = base(pixminimax 입력 반환), 나머지는 frame_0부터 생성 프레임. 시트 `shots/pixellab_test/crasher_v6_<동작>.png`(첫 칸 base, 3배).

| 동작 | 도구 | 비용 | 프레임 | 망치 손 | 팔레트 이탈 | 평가 |
|---|---|---|---|---|---|---|
| idle | pixminimax first=last, 4 | 1 | 4+1 | 유지 | 0% | 좋음(움직임 아주 작음) |
| walk | skeleton, write 8 | 3 | 8 | 쥐고 있으나 망치 머리가 거의 안 보임 | 0% | 보통 |
| smash | skeleton, write 8 | 3 | 8 | 유지(2~3번 머리 위, 7~8번 바닥) | 0% | 보통: 4~5번 몸이 비틀리며 3/4 시점으로 돎, 망치가 작아짐 |
| charge | skeleton, write 6 | 3 | 6 | 뒤쪽에 쥠 | 2% | 보통: 몸이 3/4 정면으로 돌아 둥글게 보임 |
| leap | skeleton, write 8 | 3 | 8 | 유지(6~8번 내려찍기) | 1% | 보통: 2~5번 캔버스 위로 잘림(128 안에 점프 높이가 안 들어감) |
| hurt_try1 | skeleton, write 4 | 3 | 4 | - | 6% | 다시: 1번이 갈색 덩어리로 뭉개짐, 회색 파편 |
| hurt | skeleton, write 4, "strict side view; no effects, no debris", seed 9 | 3 | 4 | 유지 | 0% | 좋음(작게 뒤로 흔들림) |
| death | skeleton, write 8 | 3 | 8 | 놓침(의도) | 0% | 좋음: 무릎 꿇고 앞으로 엎어짐. 6~8번 오른쪽 끝(x128)에 닿아 잘릴 수 있음 |

---
# 3/4 시점 v2 (2026-11-23) — 위 옆모습판은 `raw_side_old/`로 옮김
사유: rotate_image east 옆모습이 확정 디자인과 다른 캐릭터가 됨. 확정 그림(crasher_1b_2_20c, 3/4 시점) 그대로 동작을 만듦. 약 43회 사용.

## 방향 판단
머리가 몸통 중심(x 56)보다 오른쪽(x ~72)에 있고 얼굴·가슴이 화면 오른쪽 앞을 향함 → **오른쪽을 보는 3/4 시점으로 판단, 좌우 반전 안 함**.

## 손 수정 (Pro Flash 인페인트, 마스크 x16 y58 w30 h28, 각 6회)
`raw/hand_fix/q_original.png`(원본), `q_inpaint_1`(seed 17), `q_inpaint_2`(seed 5), `q_inpaint_3`(seed 29). 비교 `shots/pixellab_test/crasher_hand_fix3.png`(아래 줄 손 확대).
**채택 q_inpaint_1**: 손가락 마디가 보이는 주먹이 자루를 대각선으로 감싸 쥐고, 자루가 주먹을 관통해 망치 머리로 이어짐. 2는 손이 흐릿, 3은 자루가 세로 막대처럼 따로 놂.
원래 20색 팔레트로 되돌림 → `raw/base.png` (128, 20색, 알파 0/255, 3px 아래로 내려 bbox (1,4)-(112,126), 발 아래 2px).

## 동작 (view low top-down, direction south-east로 3/4 시점 유지)
설명 앞에 "keep the same three-quarter view and exact same design as the reference"; skeleton description: "huge scrap-metal brute boss, big rusty orange shoulder plates, small head, glowing orange furnace core in the chest, two exhaust pipes on the back, its right fist always gripping the handle of a big rusty sledgehammer; no effects". 뼈대 estimate_skeleton(새 base). idle만 frame_0=base.
모든 결과 base 팔레트 이탈 0%. 시트 `shots/pixellab_test/crasher_v6b_<동작>.png`(첫 칸 base, 3배).

| 동작 | 도구 | 비용 | 망치 손 | 디자인 유지(어깨·머리·핵·망치) | 평가 |
|---|---|---|---|---|---|
| idle | pixminimax first=last 4 | 1 | 유지 | 전부 유지 | 좋음 |
| walk | skeleton 8, seed 5 | 3 | 유지 | 전부 유지 | 좋음 |
| smash_try1 | skeleton 8, seed 5 | 3 | 유지 | 5~7번 몸이 뒤로 돌아 핵 사라짐, 2~4번 망치가 위쪽 끝 잘림 | 보통 |
| smash | skeleton 8, "core always visible, stays inside the frame", seed 9 | 3 | 유지 | 2~5번 유지, 6~8번 등을 보이며 핵 사라짐, 7~8번 바닥 회색 먼지 점 | 보통 |
| charge | skeleton 6, seed 5 | 3 | 앞쪽으로 옮겨 쥠 | 2·5·6번 몸이 돌아 핵 가려짐 | 보통 |
| leap_try1 | skeleton 8, seed 5 | 3 | 유지 | 3~4번 망치 위로 잘림, 6번 뭉개짐 | 다시 |
| leap | skeleton 8, "small hop ... stays inside the frame", seed 9 | 3 | 유지 | 2~5번 유지(망치 끝이 위쪽에 닿음), 6~8번 등 보임·먼지 점 | 보통 |
| hurt | skeleton 4, seed 9 | 3 | 유지 | 전부 유지 | 좋음 |
| death | skeleton 8, seed 5 | 3 | 놓침(의도) | 무릎 꿇고 앞으로 엎어짐, 누운 몸이 캔버스 양끝에 닿아 잘릴 수 있음 | 보통 |
