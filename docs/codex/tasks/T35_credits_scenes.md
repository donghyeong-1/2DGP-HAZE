# T35 엔딩 크레딧 장면 3장

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. 화면 일러스트(T11·T16)와 같은 방식(`$generate2dmap` plate 원화 → `conform_background.py` → `hibit_plate.py`, 1배)을 쓴다.

## 배경 (퀄리티 계획 4단계)
크레딧은 지금 탈출 화면 그림(`assets/backgrounds/screen_ending.png`)을 어둡게 깔고 글자만 올라간다. 크레딧이 흐르는 동안 **탈출 뒤 이야기 3장면**이 차례로 바뀌면 끝맺음이 산다(바꿔 보여 주는 코드는 Claude Code).

## 입력
- 탈출 화면 `assets/backgrounds/screen_ending.png`(화풍·주인공 뒷모습 기준), 제목 화면 `screen_title.png`, 은신처 원경 `far_hideout.png`, 주인공 마스터 `assets/sprites/forge/remake_t01_t03/n09/master/master_rgba.png`
- NPC: `assets/sprites/forge/npc_v1/<mechanic|keeper|archivist>/master/master_rgba.png`

## 그림 (3장, 각 1920x1080)
| 이름 | 장면 |
|---|---|
| `credits_1` | 새벽, 감옥 밖 언덕에서 주인공이 멀어진 탑을 돌아본다(뒷모습·옆모습) |
| `credits_2` | 은신처: 정비사·보관인·기록관이 화로 곁에서 쉬고, 빈자리 하나 |
| `credits_3` | 맑은 하늘 아래 헤이즈가 걷힌 도시 원경, 주인공이 작게 길 위에 |

- 1920x1080, 1배 마감(T16과 같은 색 수·블록), 글자 없음. **가운데 아래 1/3은 어둡고 단순하게**(크레딧 글자가 흐른다).
- 새 폴더 `assets/sprites/forge/credits_scenes_v1/<이름>.png` + 세 장 비교 시트.

## 절차
1 → 2 → 3. 같은 이미지는 최대 3번. 보고서 `docs/codex/reports/T35.md`, 상태 `review`.

## 합격 기준
- [ ] 탈출 화면과 같은 화풍·인물
- [ ] 아래쪽 글자 자리가 차분하다
- [ ] 보고서에 솔직하게
