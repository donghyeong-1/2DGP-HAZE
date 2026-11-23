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
