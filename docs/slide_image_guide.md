# 발표 PPT 예시 그림 안내

발표 PPT와 기획서 PPT의 예시 그림은 `tools/make_mockups.py`가 만들어 `assets/presentation_examples/`에 저장한다. 스크립트가 같은 폴더의 `slide_01.png`~`slide_10.png`와 `mock_*.png`를 읽어 슬라이드에 넣는다.

| 파일 | 내용 | 쓰이는 곳 |
|---|---|---|
| slide_01 | 제목 화면 | 표지 |
| slide_02 | 전투 화면(HUD) | 게임 소개, 화면 UI, 재화 순환 |
| slide_03 | 세계관 약도 | 세계관 |
| slide_04 | 격자 맵과 방 단면 | 진행 루프 |
| slide_05 | 조작 설명도 | 조작 |
| slide_06 | 게이지 구간별 상태 | 핵심 재미, 게임 특징 |
| slide_07 | 전투 전후 비교 | 전투 예시, 초보자 가이드 |
| slide_08 | 스테이지 구성 | 콘텐츠 |
| slide_09 | 개발 일정 | 개발 계획 |
| slide_10 | 크레딧 | 에셋·출처 |
| mock_weapons, mock_boss_crasher, mock_boss_ark, mock_gauge_graph, mock_upgrades | 무기, 보스 패턴, 게이지 흐름, 업그레이드 | 기획서 PPT |

## 다시 만드는 방법
```
python tools/make_mockups.py
python tools/make_presentation_1st.py
python tools/make_plan_deck.py
```
규칙이 바뀌면 `make_mockups.py`의 해당 장면과 두 PPT 스크립트를 함께 고친다. 모든 그림은 실제 구현 화면이 아니라 설계 목업이다.
