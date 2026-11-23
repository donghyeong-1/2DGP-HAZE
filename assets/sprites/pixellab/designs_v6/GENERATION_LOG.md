# 적 5종 디자인 v6 (2026-11-23, Claude Code)
50회 사용(Pro Flash 96 × 10, 각 5회). 사용자 확인용, 동작은 확정 뒤.
도구: `create_image_pro_flash`, 96x96, no_background, seed 3(=1안) / 11(=2안), style_image = guard_v6/raw/base.png(upload),
usage "Art style, detail level and pixel scale only (flat dark colour blocks, 1px dark edge, muted body, one bright danger part, few small glints). Do not copy the character."
설명 공통 끝: "Same art style and pixel density as the reference: flat color blocks, few colors, 1px dark edge." + 몸 색 / 위험 부위 하나만 밝게 / 작은 반짝임.
원본 `raw_gen/<이름>_<n>.png`, 정리본 `<이름>_<n>.png`: 자기 색 중 FASTOCTREE 20색(디더 없음, 원래 있던 색으로 되돌림), 알파 0/255, 발 아래 2px(드론은 공중이라 위치 유지).
비교: `shots/pixellab_test/designs_enemies.png` (주인공 base96, 간수 base, 각 적 1·2안, 같은 바닥, 3배).

| 파일 | 키×폭 | 색(원본→정리) | 평가 |
|---|---|---|---|
| slum_1 | 62×62 | 24→20 | **추천**. 구부정한 옆모습, 회갈색 누더기, 연보라 손톱만 밝음 |
| slum_2 | 66×55 | 38→19 | 좋음. 두건, 노란 손톱. 몸이 밝은 회색이라 1안보다 탁함이 덜함 |
| thrower_1 | 69×60 | 18→18 | **추천**. 방독면·등 고철 자루·손의 달군 주황 고철이 다 읽힘 |
| thrower_2 | 71×58 | 43→19 | 보통. 긴 외투에 자루가 묻혀 실루엣이 덩어리짐 |
| hound_1 | 45×80 | 31→20 | **추천**. 드러난 금속 갈비뼈, 붉은 눈·이빨 |
| hound_2 | 47×85 | 16→16 | 좋음. 더 육중, 주황 눈. 몸길이가 목표(70)보다 김 |
| drone_1 | 57×49 | 8→8 | 보통. 상자형, 디테일·색이 적어 간수 수준보다 밋밋 |
| drone_2 | 72×58 | 25→20 | **추천**. 둥근 녹슨 몸통·외눈 렌즈·쌍 프로펠러·아래 주황 노즐 |
| knight_1 | 71×85 | 21→20 | **추천**. 검푸른 갑옷, 어깨·가슴 결정, 보랏빛 청록 결정 검. 어깨 결정이 주인공 청록과 조금 가까움 |
| knight_2 | 71×91 | 45→20 | 보통. 결정이 몸 전체에 밝은 얼음색으로 퍼져 화풍(탁한 몸)이 깨지고 캔버스 끝에 닿음 |
모두 오른쪽 옆모습(드론 포함), 청록은 기사 결정 외엔 없음. 키는 목표보다 4~11px 큼(thrower·slum) — 필요하면 캔버스 정리 때 맞춤.
