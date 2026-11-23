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
