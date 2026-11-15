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
| 마우스 좌클릭 | 마우스 방향으로 철파이프 공격 (꾹 누르면 이어서, 3타째가 강하다) |
| 대시 중·직후 좌클릭 | 대시 평타: 앞으로 돌진하며 줄에 선 적을 모두 벤다 |
| 공중에서 좌클릭 | 점프 평타: 회전 베기. 아래를 겨누면 내려찍기(맞으면 튕겨 오름) |
| E | 게이지 25%를 쓰고 **다음 공격 한 번**을 강화 일격으로 (1회성, 맞은 적마다 폭발) |
| F | 진열대 앞에서 아이템 획득(황금방)·구매(정비방) |
| Shift, 마우스 우클릭 | 마우스 방향 대시 (슬롯 2개, 지나간 자리에 잔상) |
| Esc | 일시정지 |
| F1 | 디버그 표시 (F3/F4 게이지 ±10, F5 적 재생성, H 피격) |

## 테스트
```
python tests/run_all.py     # 전부 (아래를 개별로도 실행 가능)
python tests/test_gauge.py
python tests/test_player.py
python tests/test_stage.py
python tests/test_rooms.py
python tests/test_combat.py
```

## 문서
- 새 컴퓨터에서 이어서 작업하기: `docs/SETUP.md`
- 기획서: `docs/기획서.md` (5장이 구현 설계)
- 진행 상황: `docs/PROGRESS.md`, 결정 기록: `docs/DECISIONS.md`
- 에셋 출처: `docs/ASSETS.md`
