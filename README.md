# 헤이즈 (Haze)

2D 게임 프로그래밍 프로젝트. 게이지가 0%면 죽고 100%면 터진다. 그 사이를 지키며 싸우는 횡스크롤 액션 로그라이크 (Python, pico2d).

## 실행
```
pip install pico2d transitions
python src/main.py
```
| 키 | 동작 |
|---|---|
| A / D | 이동 |
| Space, W | 점프 (공중에서 한 번 더) |
| S + Space | 얇은 바닥 아래로 내려가기 |
| Shift, 마우스 우클릭 | 마우스 방향 대시 (슬롯 2개) |
| Esc | 일시정지 |
| F1 | 디버그 표시 (F3/F4 게이지 ±10, H 피격) |

## 테스트
```
python tests/test_gauge.py
python tests/test_player.py
```

## 문서
- 새 컴퓨터에서 이어서 작업하기: `docs/SETUP.md`
- 기획서: `docs/기획서.md` (5장이 구현 설계)
- 진행 상황: `docs/PROGRESS.md`, 결정 기록: `docs/DECISIONS.md`
- 에셋 출처: `docs/ASSETS.md`
