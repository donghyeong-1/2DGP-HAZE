# PixelLab 새 주인공 시험 생성 기록 (2026-11-23, Claude Code)

v6 0단계 규격 시험. 기준 원화: `assets/sprites/gemini/hero_concepts_v1/hero_A_side.png` (G01 A안, 머플러).
계정: 체험판(trial). 시작 잔여 38회 → 끝 28회 (이번 시험 10회 사용). 동시 작업 1개 제한.

## 입력 준비 (로컬, 무료)
- 마젠타 배경(약 255,19,252) 허용치로 제거: r>200, b>190, g<120, |r-b|<70 → 알파 0.
- 잘라낸 원본: `raw/ref_clean_full.png` (899x864)
- 몸 키 41px로 LANCZOS 축소 후 알파 0/255로 정리, 64x64 캔버스 바닥 2px 위에 배치: `raw/ref_input_64.png`
- 업로드는 `get_upload_url` + curl (base64 직접 전달 안 함)

## 생성 내역
| 파일 | 도구 | 옵션 | 비용 | 결과 |
|---|---|---|---|---|
| `raw/still_try1_pixflux.png` | `create_image_pixflux` | init_image=ref_input_64, strength 200, 64x64, no_background, view side, direction east, black outline, medium shading, seed 7 | 1 | **채택**. 원화에 가장 가까움. 상체는 여전히 살짝 뒤돌아 있음 |
| `raw/still_try2_proflash.png` | `create_image_pro_flash` | 64x64, style_image=ref_input_64, seed 11 | 5 | 탈락. 닌자풍으로 바뀌고 파이프가 붉은 손잡이 칼이 됨, 키 47px |
| `raw/idle_try1/` (7장) | `animate_image` | first_frame=still_try1, frame_count 6, seed 3 | 1 | 반복 안 됨(마지막 프레임이 처음으로 안 돌아옴) |
| `raw/idle_try2_pixminimax/` (9장) | `animate_image_pixminimax` | first=last=still_try1, frame_count 8, view side, direction east, seed 5 | 1 | **채택**. 0번≈8번으로 반복됨, 색 19개 유지 |
| `raw/run_try1/` (11장) | `animate_image` | first_frame=still_try1, frame_count 10, seed 3 | 1 | 탈락. 보폭이 작아 걷기처럼 보임 |
| `raw/run_try2_pixminimax/` (9장) | `animate_image_pixminimax` | first_frame=still_try1, frame_count 8, view side, direction east, seed 5 | 1 | **채택 후보**. 진짜 달리기. 1~2번은 서기→달리기 전환, 반복 구간은 3~8번(6장) |

frame_0은 모두 입력 그림 그대로다(도구가 0번에 입력을 돌려준다).

## 확인용 그림 (`shots/pixellab_test/`)
- `*_sheet_x3.png` 투명 시트 3배, `*_dark_x3.png` 슬럼 배경(18,24,40) 3배, `*.gif`
- `run_try2_loop_f3-8_centered.gif` 반복 구간만 몸통 중심을 맞춘 것
- `compare_old_vs_new_{dark,light}_x3.png` 왼쪽부터: 지금 주인공 n09_idle_1 1/3 축소, 새 1안, 새 2안, 입력(원화 축소)

## 2차: 흰 머리 + 크기 2안 (A안 확정 후 추가 지시)
입력: 원화 머리카락을 로컬에서 흰색 3단계(248,250,252 / 220,226,232 / 그림자 150,165,185 차가운 회청)로 바꾼 뒤 축소
(`raw/ref_clean_full_whitehair.png`, `raw/ref_input_64_whitehair.png` 키 41, `raw/ref_input_96_whitehair.png` 키 62).
설명에 "bright white hair", "large clean color blocks, high contrast, few colors, cyan accents only"를 넣었다. 4회 사용 → 남은 24회.

| 파일 | 도구 | 옵션 | 비용 | 결과 |
|---|---|---|---|---|
| `raw/still41_whitehair_try1.png` | `create_image_pixflux` | init 64 흰머리, strength 200, 64x64, side/east, black outline, basic shading, seed 7 | 1 | 흰 머리 잘 나옴(손 칠 필요 없음). 20색, 키 41 |
| `raw/run41_whitehair_pixminimax/` (9장) | `animate_image_pixminimax` | first=still41, 8프레임, side/east, seed 5 | 1 | 달리기 좋음. 반복 3~8번, 몸이 오른쪽으로 약 2px 흐름, 19색 |
| `raw/still62_whitehair_try1.png` | `create_image_pixflux` | init 96 흰머리, 96x96, 나머지 같음 | 1 | 더 매끈, 16색, 키 62 |
| `raw/run62_whitehair_pixminimax/` (9장) | `animate_image_pixminimax` | first=still62, 96x96, 8프레임 | 1 | 동작 부드러움, 15색. 5~8번에서 파이프가 뒷손으로 옮겨 감, 몸이 오른쪽으로 약 7px 흐름 |

비교 그림: `shots/pixellab_test/size_compare.png` (41px는 3배, 62px는 2배, 서기 키 123/124px로 맞춤), 시트·GIF는 `run41_whitehair*`, `run62_whitehair*`.
붉은 포인트: 41px안의 손에 피부 그림자색(185,104,110) 1색이 있다. 포인트가 아닌 피부색이지만 청록만 남기려면 손볼 곳.

## 3차: 62px안 확정, 전체 동작 (2026-11-23)
공통: `animate_image_pixminimax`, first_frame=`raw/still62_whitehair_try1.png`(96x96), view side, direction east,
subject "a young man with white hair in black clothes with a long dark scarf with cyan flame ends, holding an iron pipe in his front hand",
initial_pose "standing upright facing right, pipe lowered in the front hand", 설명에 "holding iron pipe in front hand, same hand every frame".
각 1회(8프레임 이하는 1회 요금). 11회 사용 → 남은 13회. frame_0은 입력 그대로, 프레임 수는 입력 포함.
흐름 px = frame_0 대비 몸 중심(알파 픽셀 평균) 최대 이동.

| 폴더 | 프레임 | 추가 옵션 | 파이프 손 | 흐름 px (x / y) | 평가 |
|---|---|---|---|---|---|
| `idle62/` | 8+1 | last=still(루프), seed 5 | 유지 | 1 / 1 | **좋음**. 0번=8번 루프, 15색 |
| `jump62/` | 8+1 | 1~4 도약·상승, 5~8 낙하, seed 5 | 유지 | 7 / 32 위로 | **보통**. 머플러 위로 날림 좋음. 7~8번 몸이 길게 늘어지고 머플러가 위쪽 끝(y 3) 닿음. 게임에선 위치를 몸 기준으로 다시 맞춰야 함 |
| `land62/` | 4+1 | last=still, seed 5 | 유지 | 2 / 6 | **좋음**. 무릎 굽혔다 원래 자세로 |
| `dash62/` | 8+1 | seed 5 (6프레임 요청 → pixminimax는 4의 배수라 8) | 유지(낮게 앞으로) | 18 / 9 | **좋음**. 낮은 돌진, 머플러 길게 수평. 4~5번 오른쪽 끝(x 95) 닿아 잘릴 수 있음, 원래 자세로 안 돌아옴 |
| `attack162/` | 8+1 | seed 5 | 유지 | 7 / 3 | **보통**. 4번에 청록 휘두름 궤적이 함께 그려짐. 5~8번은 휘두름보다 앞으로 찌른 자세로 끝나고 얼굴이 약간 정면으로 돎 |
| `attack262_try1/` | 8+1 | 반대 방향 백핸드, seed 5 | 섞임 | 7 / 3 | 다시: 몸이 정면으로 돌고 2번에 파이프가 두 개로 보임 |
| `attack262/` (재시도) | 8+1 | 아래→위 대각 올려치기로 바꿈, "never turning toward the camera", seed 9 | 유지 | 8 / 6 | **보통**. 5번에 청록 궤적, 8번=처음 자세라 이어 붙이기 쉬움. 2~4번 얼굴이 정면 쪽으로 돎 |
| `attack362/` | 8+1 | 내려찍기, seed 5 | 유지(양손 들어올림) | 15 / 14 | **보통**. 힘 있는 내려찍기, 4~5번 흰 궤적. 2~3번 위쪽 끝(y 2) 닿고 4번 위쪽에 흰 점 1~2개, 끝에 낮은 자세로 머묾 |
| `hurt62_try1/` | 4+1 | last=still, seed 5 | 유지 | 9 / 3 | 다시: 붉은 베기 효과가 그려짐(붉은 포인트 금지) |
| `hurt62/` (재시도) | 4+1 | "no effects and no slash marks", last=still, seed 9 | 유지 | 5 / 10 | **보통**. 자세는 좋으나 1~2번에 흰 충격 호가 여전히 그려짐(2번은 몸과 떨어져 지우기 쉬움, 1번은 몸과 겹침) |
| `death62/` | 8+1 | seed 5 | 놓침(의도) | 4 / 28 아래로 | **좋음**. 파이프 떨어뜨리고 뒤로 쓰러져 누움, 불꽃 어두워짐. 누운 몸이 캔버스 폭 거의 전부(x 3~93) |

확인용: `shots/pixellab_test/<동작>62_sheet_x3.png`, `<동작>62_dark_x3.png`, `<동작>62.gif` (재시도 전 것은 `_try1`).
공통 손볼 것: 동작마다 몸 위치가 흘러 게임 적용 시 발 기준 정렬 필요. 모델이 휘두름·피격 효과(청록/흰 궤적)를 그림에 같이 그리는 경향이 있음 — 청록 궤적은 그대로 써도 되지만 효과를 코드로 따로 그릴 거면 지워야 함.

## 4차: 입력 그림(ref_input_96_whitehair) 충실도 시험 (2026-11-23)
목표: PixelLab이 다시 그리지 않고 입력 그림 모습(끝이 꺾인 파이프, 뾰족한 흰 머리, 목에 감긴 머플러)을 유지한 채 움직이게.

### 기준 base96 (무료)
- `raw/ref_input_96_whitehair.png`는 973색. 마젠타 배경이 섞인 테두리 62px(r-g>18, b-g>12)는 팔레트 후보에서 뺐다.
- 요청한 MAXCOVERAGE는 테두리를 빼도 몸이 보라·청록으로 떠서(평균 색 오차 15.0) `raw/base96_maxcoverage.png`로만 남겼다.
- **`raw/base96.png` = FASTOCTREE 24색**(오차 8.5, MEDIANCUT 9.0), dither 없음, 팔레트 각 색을 원본에 실제 있던 가장 가까운 색으로 되돌림, 알파 0/255.
- 비교: `shots/pixellab_test/base96_compare.png` (원본 / MAXCOVERAGE / base96, 4배)

### MCP 도구 확인 (모양 유지형)
- `animate_with_skeleton_v3`: 한 장 기준 그림을 18관절 뼈대 포즈대로 매 프레임 다시 그림. `estimate_skeleton`(0.1회)로 관절 추출, `write_motion_frames`로 동작 자동 작성. 4~14프레임 3회.
- `animate_character`(mode skeleton-v3/template): PixelLab에 저장된 캐릭터가 있어야 함 → `create_character_pro_flash`(첫 그림 재사용 시 회전 비용) 추가 비용이라 이번엔 안 씀.
- `estimate_custom_skeleton`: 머플러·파이프 같은 추가 관절 리그(8프레임당 1회). 안 씀.
- `pixelart_workbench` draw/motion: 원본 픽셀을 부위로 잘라 위치·각도 트랙으로 움직이는 방식(무료, 픽셀 그대로 유지). 부위 영역·피벗·키를 직접 써야 하고, 가려졌던 부분(뒷다리 등)은 손으로 채워야 함. 이번엔 시간상 안 씀.

### 결과 (5.1회 사용 → 남은 7.9회)
| 방식·폴더 | 도구·옵션 | 비용 | 꺾인 파이프 | 머리 | 머플러 | base96 팔레트 이탈 | 평가 |
|---|---|---|---|---|---|---|---|
| `raw/pixminimax_idle96/` (8+1) | `animate_image_pixminimax`, first=last=base96, side/east, seed 5, "keep exact same design ... do not redraw or restyle" | 1 | 유지 | 유지 | 유지, 끝 불꽃만 흔들림 | 0% (24색 그대로) | **매우 충실**. 사실상 입력 그대로에 머플러만 움직임 |
| `raw/pixminimax_run96/` (8+1) | 같은 설명 + 달리기, seed 5 | 1 | 유지(갈고리 보임) | **바뀜**: 2번 이후 얼굴이 정면으로 돌아 하얀 가면·해골처럼 보이고 귀 같은 뿔이 생김, 7~8번 흰 셔츠 앞섶 | 유지 | 0% | 보통. 동작은 좋지만 얼굴 정체성이 흔들림 |
| `raw/skeleton_run96/` (8, 입력 반환 없음) | `estimate_skeleton`(0.1) + `animate_with_skeleton_v3`, write_motion_frames 8, side/east, seed 5 | 3.1 | 유지 | **유지**(뒤로 살짝 돈 머리 그대로) | 유지, 불꽃 끝이 조금 납작 | 0% | **가장 충실한 달리기**. 단 4~5번 팔 흔들림에 파이프가 세로로 들림, 다리 보폭 큼 |
| (참고) `raw/run62_whitehair_pixminimax/` | 3차 게임 적용분 | - | 곧은 막대로 바뀜 | 바뀜 | - | 100% 이탈(15색, 평균 거리 10.8) | 입력과 다른 그림 |

비교 그림: `shots/pixellab_test/fidelity_pixminimax.png`, `fidelity_skeleton.png`, `fidelity_old_still62.png` (첫 칸이 base96, 4배).
발견: 입력이 24색처럼 적은 색이면 두 방식 모두 입력 팔레트를 그대로 지킨다(이탈 0%). 3차에서 모습이 달라진 주원인은 pixflux로 still62를 다시 그린 단계였다.
추천: 서서 하는 동작(대기·피격 등 몸이 크게 안 도는 것)은 pixminimax(first=last=base96, 1회), 크게 움직이는 동작(달리기·점프·공격)은 skeleton v3(3회)로. 파이프가 들리는 문제는 뼈대 keypoints를 직접 주어 오른팔(RIGHT ARM)을 낮게 고정하면 줄일 수 있음.

## 5차 (v2): base96 기준 주인공 전체 동작 (2026-11-23, 결제 후)
계정: Tier 1(Pixel Apprentice), 이번 주기 2000회(2026-12-23 갱신), 크레딧 $0. 이번 작업 35회 사용 → 남은 1965회. 동시 작업 여러 개 가능해짐.
공통: 첫 프레임·기준 = `raw/base96.png`(upload, 96x96, side/east). 뼈대는 `estimate_skeleton`(4차 결과) 재사용.
- pixminimax 설명: "keep exact same design: hooked crowbar iron pipe held in the front hand, spiky white hair, scarf wrapped around neck with cyan flame ends, side-view face with one cyan glowing eye, never turn the face toward the camera, do not redraw or restyle" + 동작.
- skeleton v3 description: "young man with spiky white hair and a side-view face with one cyan glowing eye, dark charcoal jacket and pants, grey scarf wrapped around his neck with long tails ending in cyan flames, holding a hooked crowbar iron pipe (low) in his front (right) hand", action은 짧은 동작 문장, `write_motion_frames`.
- 프레임: pixminimax 폴더는 frame_0=base96(입력 반환), skeleton 폴더는 모두 생성 프레임(입력 없음).
- 흐름 = base96 대비 몸 중심 x 이동 / 발끝 y 이동(px). 팔레트 이탈 = base96 24색 밖 픽셀 비율.

| 폴더 | 도구·옵션 | 비용 | 파이프 손 | 얼굴 유지 | 흐름 x / 발 y | 이탈 | 평가 |
|---|---|---|---|---|---|---|---|
| `idle96/` (8+1) | 4차 `pixminimax_idle96` 복사, first=last | 0 | 유지 | 유지 | 0~2 / 0 | 0% | **좋음** |
| `hurt96_try1/` (4+1) | pixminimax first=last, "no effects, no slash marks", seed 5 | 1 | 유지 | 유지 | -4~2 / -2 | 6.4% | 다시: 흰 베기 효과가 그려짐 |
| `hurt96/` (4) | **skeleton v3로 바꿈**, write 4, seed 9 | 3 | 유지 | 유지 | -6~0 / -2 | 0% | **좋음**. 효과 없음, 마지막이 서기에 가까움 |
| `land96_try1/` (4+1) | pixminimax first=last, seed 5 | 1 | 유지 | **정면으로 돎**(흰 가면) | 0~3 / 0 | 0% | 다시 |
| `land96/` (4) | **skeleton v3로 바꿈**, write 4, seed 9 | 3 | 유지(수평으로 낮게) | 유지 | 2~5 / 0 | 0% | **좋음** |
| `run96/` (8) | skeleton v3, 4차 달리기 뼈대에서 앞팔(RIGHT ELBOW/ARM)을 어깨 기준 base96과 같은 오프셋(+0.030,+0.078 / +0.130,+0.134)으로 고정, x ±0.02 흔들림, seed 5 | 3 | **매 프레임 앞아래로 유지** | 유지 | 3~4 / -4 | 0% | **좋음**. 4차의 파이프 들림 해결 |
| `run_start96/` (4) | skeleton v3, write 4, seed 5 | 3 | 유지 | 유지 | 1~4 / -6 | 0% | **좋음** |
| `jump96/` (8) | skeleton v3, write 8, seed 5 | 3 | 유지 | 유지 | -1~4 / -16 | 0% | **보통**. 3~5번 파이프 끝이 머리 위로 삐죽 보임. 캔버스 안 상승은 16px뿐이라 높이는 게임 물리로 |
| `dash96_try1/` (6) | skeleton v3, write 6, seed 5 | 3 | 바닥에 놓임 | 머리가 바닥까지 꺾임 | 1~17 / 2 | 0% | 다시: 기어가는 모양 |
| `dash96/` (6) | skeleton v3, "lunge forward in a low wide stance ... head up", seed 9 | 3 | 유지하나 2~5번 세로로 듦 | 유지 | -2~8 / 0 | 0% | **보통**. 자세는 낮은 돌진, 파이프가 세워짐(앞팔 고정 뼈대로 재생성하면 나아질 것) |
| `attack196/` (8) | skeleton v3, 가로 휘두르기, seed 5 | 3 | 유지 | 유지 | -5~9 / 0 | 0% | **좋음**. 휘두르기보다 앞으로 뻗는 쪽, 끝이 기본 자세로 돌아옴 |
| `attack296/` (8) | skeleton v3, 아래→위 올려치기, seed 5 | 3 | 유지 | 대체로 유지 | 0~8 / 0 | 0% | **보통**. 2~4번 파이프 세로, 6~7번 몸이 비틀리며 머플러가 뭉침 |
| `attack396/` (8) | skeleton v3, 내려찍기, seed 5 | 3 | 유지 | 유지 | -6~14 / 0 | 0% | **좋음**. 머리 위로 들었다가 5번에 수직 내려찍고 웅크림 |
| `death96/` (8) | skeleton v3, 쓰러짐, seed 5 | 3 | 놓침(의도) | 유지 | -9~-1 / 1 | 0% | **좋음**. 파이프 떨어뜨리고 뒤로 누움 |

확인 시트: `shots/pixellab_test/v2_<동작>.png`(첫 칸 base96, 3배, 어두운 배경)와 `v2_<동작>.gif`. 첫 시도는 `v2_<동작>_try1`.
교훈: pixminimax는 서 있는 동작에서도 피격·착지처럼 몸이 크게 움직이면 얼굴을 정면으로 돌리거나 효과를 그린다. skeleton v3는 얼굴·팔레트를 지키고 효과를 안 그린다. 파이프 방향은 앞팔 관절을 직접 주면 잡힌다.

## 6차: 적·보스 디자인 시험 (2026-11-23, 10회 한도)
8.2회 사용(생성 8 + 뼈대 추정 0.2) → 남은 1956.8회. 결과 `raw/designs/`, 확인 `shots/pixellab_test/design_guard.png`, `design_crasher.png`(주인공 base96과 같은 바닥, 3배), `design_skeleton_check.png`(추정 뼈대 겹침).
색표 그림: `raw/designs/palette_guard.png`(base96 24색에서 청록 7색 빼고 주황 3단 추가, 20색), `palette_crasher.png`(base96 어두운 6색 + 녹슨 주황·갈색·회색 11색).
Pro Flash는 128 캔버스가 6회라 한도 때문에 간수 1안에만 썼다.

| 파일 | 도구·옵션 | 비용 | 키 / 색 | 평가 |
|---|---|---|---|---|
| `guard_1.png` (96) | `create_image_pro_flash`, style_image=base96("art style and pixel scale only"), seed 3 | 5 | 64px / 16색 | **좋음**. 오른쪽 옆모습, 앞쪽 큰 방패, 뒷손 곤봉 끝만 주황. 평면 색면·1px 어두운 가장자리로 주인공과 화풍·픽셀 굵기가 맞음. 회청 장갑이 감옥 구역 색과 맞음 |
| `guard_2.png` (96) | `create_image_pixflux`, color_image=palette_guard(강제 팔레트), side/east, selective outline, basic shading, seed 11 | 1 | 82px / 18색 | 다시: 정면을 봄, 가슴 바이저까지 주황, 키 과함. 색은 맞음 |
| `crasher_1.png` (128) | `create_image_pixflux`, color_image=palette_crasher, side/east, seed 11 | 1 | 118px / 16색 | 다시: 정면 골렘, 망치 팔·배기관이 안 보임, 키 과함 |
| `crasher_2.png` (128) | `create_image_pixen`, side/east, selective outline, seed 23 | 1 | 121px / 40색 | **보통**. 디자인은 요구에 가장 맞음(치켜든 큰 망치, 등 배기관, 덧댄 고철, 녹슨 주황·갈색). 단 3/4 시점이고 검은 굵은 외곽선·40색으로 주인공보다 진하고 촘촘함, 키 121(목표 100) |

뼈대 추정(`estimate_skeleton`, 각 0.1): guard_1·crasher_2 모두 18관절이 팔다리에 맞게 잡힘(간수 곤봉 팔·방패 팔, 크래셔 망치 든 팔 포함) → skeleton v3 동작 가능. 크래셔는 배기관·망치가 커서 `estimate_custom_skeleton` 리그가 더 나을 수 있음.
다음 추천: 간수는 guard_1 그대로 동작 진행. 크래셔는 crasher_2를 style 참조 없이 쓰기보다 `create_image_pro_flash`(128, 6회)에 style_image=base96(128로 패딩) + crasher_2 디자인 설명으로 화풍을 맞춘 1안을 더 뽑아 보기.

## 7차: 간수·크래셔 1안에 디테일 추가 (2026-11-23, 15회 한도)
10회 사용 → 남은 1946.8회. 시작 그림은 각 1안(처음부터 새로 그리지 않음). 결과 `raw/designs/<이름>_1b_<n>.png`, 색 줄인 것 `_20c.png`.
확인: `shots/pixellab_test/design2_guard.png`, `design2_crasher.png`(base96, 1안, 새 3안, 같은 바닥, 3배), `design2_<이름>_20c.png`(20색으로 줄인 것 비교).
색 줄이기(무료, 로컬): 그림 자신의 색 중 FASTOCTREE 20색, 각 색을 원래 있던 색으로 되돌림, 디더 없음.

| 파일 | 도구·옵션 | 비용 | 색 | 평가 |
|---|---|---|---|---|
| `guard_1b_1` | `edit_image_pixen`(guard_1), seed 3 | 1 | 54 | 보통: 디테일은 읽히나 장갑 판 가장자리 전체에 주황 선이 둘러져 1안의 차분한 회청 화풍이 깨짐 |
| `guard_1b_2` | `edit_image_pixen`, seed 17 | 1 | 30 | 다시: 주황 테두리가 더 많아 네온처럼 됨 |
| `guard_1b_3` | `edit_image_pro_flash`(source=guard_1 Pro Flash id), text, seed 5 | 5 | 63 → **20c 판 20** | **좋음**: 1안 화풍·실루엣 그대로, 바이저 주황 가는 선, 가슴 주황 표시등, 방패 경고 표식·긁힌 자국, 판 가장자리 하이라이트 몇 점. 41~62px(3배 화면)에서도 바이저·표시등이 읽힘 |
| `crasher_1b_1` | `edit_image_pixen`(crasher_1), seed 3 | 1 | 72 → 20c 판 20 | 보통: 망치 머리·용접·가슴 열기 3곳은 좋으나 배기관이 회색 연기 줄처럼 가늘게 나옴 |
| `crasher_1b_2` | `edit_image_pixen`, seed 17 | 1 | 66 → **20c 판 20** | **좋음**: 1안 화풍 유지 + 큰 망치 머리 팔, 등 위 배기관 2개(끝 그을음), 녹·금·덧댄 판, 가슴 주황 용광로. 20c 판에서 그을음이 조금 옅어짐 |
| `crasher_1b_3` | `create_image_pixflux` init=crasher_1 strength 300, 강제 팔레트, seed 29 | 1 | 17 | 다시: 거의 안 바뀜(망치·배기관 없음). strength가 높음 |

교훈: 편집 도구는 색을 16 → 50~70색으로 늘린다. 화풍(16색 안팎)을 지키려면 편집 뒤 로컬 20색 줄이기가 필요하고, 줄여도 모습은 거의 그대로(평균 색 오차 7~9).
추천: 간수 = `guard_1b_3_20c.png`, 크래셔 = `crasher_1b_2_20c.png`. 크래셔 1안은 정면 시점이라 횡스크롤 east 동작으로 쓰려면 옆모습 회전(rotate_image 1회)이 따로 필요하다.

## v3: 주인공 공격 동작 1차 (2026-11-23~24, plan_v7 8절)
약 92회 사용 → 남은 1637회.
방법: `raw/v3_kp/gen_v3.py`가 동작마다 8프레임의 앞손(파이프) 위치·파이프 각도·몸 자세(서기/돌진/웅크림/공중/무릎)를 정하고 2관절 IK로 RIGHT ELBOW/ARM을 계산해 `<동작>.json`(keypoints)과 `tips.json`(계획한 파이프 끝)을 만든다.
→ `animate_with_skeleton_v3`(first_frame=base96, first_frame_keypoints=기존 추정, keypoints=위 파일, side/east, seed 5, 3회).
description 공통: "... gripping a hooked crowbar iron pipe in his front hand every frame; keep exact same design; strict side view, face never turns to the camera; no effects, no trails".
결과 `raw/v3_<동작>/frame_0~7.png`(모두 생성 프레임). 시트 `shots/pixellab_test/v3_<동작>.png`: 윗줄 = 결과(첫 칸 base96), 아랫줄 = 같은 프레임 위에 계획 궤적(빨강)과 그 프레임의 계획 파이프 끝(노랑 점). 계획 전체 미리보기 `v3_plan_overview.png`.
주의: 점은 "계획한" 끝이다. 모델은 손 위치는 대체로 따르지만 파이프 방향은 스스로 정해서, 실제 끝과 다를 수 있다.

| 동작 | 평가 | 파이프 궤적이 의도와 맞는지 |
|---|---|---|
| g1 수평 횡베기 | 보통 | 뒤로 당김(4번)→앞(5번)은 맞으나 2번에 앞으로 뻗었다가 돌아감, 가로지르는 느낌 약함 |
| g2 사선 반원 내려베기 | **좋음** | 머리 뒤로 들어 앞 아래로, 계획과 거의 같음 |
| g3 회전 횡베기 | 보통 | 수평으로 앞을 향하지만 찌르기처럼 보이고 회전감이 약함 |
| up 올려베기 | **좋음** | 앞 아래 → 세로 → 머리 위, 계획대로 |
| low 발밑 훑기 | 보통 | 웅크림은 맞지만 파이프가 바닥을 수평으로 훑기보다 사선 |
| dash 낮은 돌진 횡베기 | 보통 | 허리 높이 수평은 맞으나 찌르기 느낌, 캔버스 안 전진은 작음 |
| air1 공중 횡베기 | 보통 | 다리 접음 OK, 수평 앞. 4번에 작은 궤적 선 |
| air2 공중 반원 | 보통 | 뒤 아래→머리 위→앞 아래 원은 읽히지만 5~7번에 흰 초승달 효과를 그림 |
| air_up 공중 올려베기 | **좋음** | 계획대로 |
| air_down 내려찍기 | 보통(2회 시도) | 1차 = 들었다가 앞으로 수평(다시), 2차 = 들었다가 앞 아래 사선. 수직으로 내리꽂지는 않음. 2차를 `v3_air_down/`, 1차는 `v3_air_down_try1/` |
| e1 X베기 | 보통 | 내려베기·올려베기 두 번은 맞으나 흰 초승달 효과 3장(팔레트 밖 1%) |
| e2_rise 크게 올려베기 | **좋음** | 웅크림→올려베기→뛰어올라 머리 위 |
| e2_slam 크게 내려찍기 | **좋음** | 공중 머리 위 → 앞 아래로 내려찍고 웅크림 |
| ult 난무 | 보통 | 세 번 휘두름 순서는 맞으나 흰 궤적·잔상 효과가 섞임 |
| combo4 빠른 역횡베기 | 보통 | 가슴 앞으로 감았다 어깨 높이로 뻗는 동작이 찌르기처럼 보임 |
| combo5 회전베기 | 보통 | 크게 당겼다 수평 앞, 회전감 약함 |
| quake 낙뢰 내려찍기 착지 | **좋음** | 머리 위 → 무릎 꿇고 파이프를 세로로 땅에 박음 |
| flash 섬광 베기 | 보통 | 낮은 자세→앞으로 뻗기→멈춤, 5번에 파이프가 세로로 섬, 전진 거리 작음 |
공통: 얼굴은 모든 동작에서 옆모습 유지, 팔레트 이탈 0~1%. 횡베기 계열은 2D 옆모습에서 "파이프가 카메라 쪽을 지나는" 순간을 모델이 찌르기로 그리는 경향이 있다 — 이펙트(납작한 타원 호)를 코드로 덧그려 보완하는 쪽이 현실적.

### D. 무기별 기준 그림 (각 5회, 권총 인페인트 1회는 정책 필터로 실패·무과금)
| 파일 | 도구 | 결과 |
|---|---|---|
| `weapon_bases/pistols_edit.png` | edit_image_pro_flash, palette correction, seed 5 | 두 정을 앞으로 겨눔. 머리 모양이 더 뾰족하게 바뀜, 11색 |
| `weapon_bases/pistols_edit2.png` | 같은 도구, "sci-fi blasters", seed 11 | **추천** → `base_pistols.png`(14색). 머리·옷 유지, 앞손 겨눔 + 뒷손 가슴 앞 |
| `weapon_bases/pistols_inpaint.png` | inpaint_image_pro_flash (x50 y40 w34 h32), seed 11 | 몸은 원본 그대로, 권총 한 정만 보임 |
| `weapon_bases/gauntlets_edit.png` | edit_image_pro_flash, seed 5 | 양손 건틀릿이지만 작고 어두워 잘 안 읽힘 |
| `weapon_bases/gauntlets_inpaint.png` | inpaint, seed 5 | **추천** → `base_gauntlets.png`(24색). 몸 원본 그대로, 앞으로 쥔 큰 주먹 건틀릿 |
| `weapon_bases/chain_edit.png` | edit_image_pro_flash, seed 5 | 사슬은 좋으나 파이프 조각이 남음(다시) |
| `weapon_bases/chain_inpaint.png` | inpaint (h40), seed 5 | **추천** → `base_chain.png`(24색). 앞손에 감긴 청록 사슬이 아래로 늘어짐 |
비교 `shots/pixellab_test/v3_weapon_bases.png`. base_*.png는 자기 색 24색 이하·알파 0/255로 정리. 인페인트안은 뒷손이 원래 그림처럼 가려져 있어 "양손"은 동작 단계에서 보이게 해야 함.

### air_down2 (2026-11-24, 수직 내리꽂기 재생성, 6회)
`raw/v3_kp/gen_air_down2.py`(gen_v3의 IK 재사용 + 다리를 높이 접는 tuck 자세, 3~7번은 몸을 7~9% 올려 파이프 끝이 캔버스 안에 들게 함).
- 1차(seed 5, 손 = 허리 앞 0.05,0.19): 마지막 7번만 수직 아래, 4~6번은 파이프가 위로 서고 허리에 가로 막대가 한 개 더 그려짐 → `raw/v3_air_down2_try1/`, `shots/.../v3_air_down2_try1.png`.
- **2차(seed 9, 손 = 어깨 바로 아래 0.02,0.19, "exactly one pipe ... hooked end at the bottom")**: 3~7번 모두 파이프가 수직 아래(갈고리 끝이 아래), 계획 궤적과 일치 → `raw/v3_air_down2/`, `shots/.../v3_air_down2.png`. 타격 프레임 = frame_4(3번부터 수직, 4번이 완전히 뻗음). 파이프 끝은 발바닥보다 약 17px 아래(96 캔버스·파이프 길이상 25~30px은 불가). frame_0은 웅크린 자세에 파이프가 잘 안 보임.

## 쌍권총 사격 자세 (2026-11-24, 메인 세션)
약 8.0회 사용 (뼈대 추정 0.1 x 10 + skeleton v3 3 + 3 + 2) → 남은 약 1623회.
방법: `estimate_skeleton`으로 base_pistols·run96 8장·jump96 4번의 뼈대를 얻고(`raw/v3_kp/pistol_src.json`), `raw/v3_kp/gen_pistol.py`가
두 팔만 조준 각도로 다시 놓아(위팔 0.10, 아래팔 0.095, 팔꿈치 8도 아래로 굽힘) `pistol_aim/run/air.json`을 만든다.
→ `animate_with_skeleton_v3`(first_frame=base_pistols upload, side/east, seed 5). description: "white-haired young man in a dark long coat
with a dark teal scarf, holding two compact sci-fi pistols with glowing teal lines ... no effects, no muzzle flash, no trails".

| 결과 | 장 | 평가 |
|---|---|---|
| `raw/v3_pistol_aim/` (위 80도·앞 위 42도·앞 아래 -42도·아래 -75도) | 4 | 좋음. 위 겨눔은 총이 작게 보임 |
| `raw/v3_pistol_run/` (달리며 앞 겨눔) | 8 | 좋음. 2·4·6번에 총구 섬광을 그려 넣어 적용 도구가 총열 끝 앞을 자름(FLASH_CUT) |
| `raw/v3_pistol_air/` (공중 앞·앞 위·앞 아래) | 3 | 보통. 다리를 접지 않고 선 다리 그대로 |
확인 시트 `shots/pixellab_test/v3_pistol_poses.png`. 게임 적용 `hero6_pistol_up/upfwd/downfwd/down/run/air`, 총구 위치 `hero6_muzzle.json`.

## 건틀릿 자세 (2026-11-24, 메인 세션)
약 5.1회 사용 (뼈대 추정 0.1 + skeleton v3 3 + 2, 2장 요청은 3장부터라 거절·무과금).
`estimate_skeleton`(base_gauntlets) + 점프 뼈대(pistol_src.json) → `raw/v3_kp/gen_gauntlet.py`가 관절을 옮겨 땅 5장·공중 3장.
`animate_with_skeleton_v3`(first_frame=base_gauntlets upload, side/east, seed 5), description "... wearing a large armored haze gauntlet
with glowing teal lines on his front fist ... no effects, no shockwave, no trails".

| 결과 | 장 | 평가 |
|---|---|---|
| `raw/v3_gauntlet_ground/` (충전·앞 강타·회수·앞 위·앞 아래) | 5 | 좋음. 충전은 주먹이 몸 뒤라 잘 안 보임, 앞 아래는 몸 뒤 회색 궤적(적용 도구 GREY_CUT로 지움) |
| `raw/v3_gauntlet_air/` (아래·앞·앞 위) | 3 | 좋음. 이번엔 무릎을 접음. 아래 강타는 주먹이 허리 옆이라 약함 |
확인 시트 `shots/pixellab_test/v3_gauntlet_poses.png`. 게임 적용 `hero6_gauntlet`(예전 n09_gauntlet 4장 순서)·`_upfwd`·`_downfwd`·`_air`·`_airdown`.

## 사슬 자세 (2026-11-24, 메인 세션)
약 5.1회 사용 (뼈대 추정 0.1 + skeleton v3 3 + 2) → 남은 약 1613회.
`estimate_skeleton`(base_chain) + 점프 뼈대 → `raw/v3_kp/gen_chain.py`(gen_gauntlet.pose 재사용)가 땅 5장·공중 3장.
`animate_with_skeleton_v3`(first_frame=base_chain upload, side/east, seed 5), description "... holding a glowing teal haze chain wrapped
around his front hand ... no effects, no trails".

| 결과 | 장 | 평가 |
|---|---|---|
| `raw/v3_chain_ground/` (돌리기·앞 던지기·당기기·앞 위·앞 아래) | 5 | 좋음. 당기기·앞 위는 목도리 끝 회색 궤적(GREY_CUT로 지움) |
| `raw/v3_chain_air/` (앞·앞 위·아래) | 3 | 보통. 앞은 목도리 회색 궤적(지움), 아래는 사슬이 머리 위로 크게 돎 |
확인 시트 `shots/pixellab_test/v3_chain_poses.png`. 게임 적용 `hero6_chain`(예전 n09_chain 3장 순서)·`_upfwd`·`_downfwd`·`_air`.

