# T51 떠돌이 죄수 NPC (이벤트 방, 2026-11-25 Claude 프로젝트 초안, Claude Code 등록)

> 2026-11-25 Claude Code 검토·등록(`docs/codex/TASKS.md`에 `ready`, T50 다음). 지금 게임은 보관인 그림의 색을 바꾼 임시 그림(`assets/sprites/unified/npc_drifter_idle_1~2.png`)을 쓴다.

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. T22(은신처 NPC)와 같은 방식: **마스터 1장 → 대기 2장 → `finish_character.py <원화> npc_drifter --height 117` → `check_sprites.py`**.

## 배경 (v8 계획 5-4, `src/events.py`)
구역 1·2의 이벤트 방에 **떠돌이 죄수**가 서 있다. 체력·조각·증강을 맞바꾸는 거래를 하나 해 준다.
가까이 가면 머리 위에 인사말이 뜬다("쉿, 간수는 없어. 거래 하나만 하자." 등, `data/dialogue.py`).
지금 그림은 보관인(`npc_keeper_idle_1~2.png`, T22)의 색만 바꾼 것이라 **실루엣이 보관인과 똑같다**. 이것을 바꾼다.

## 입력
- 은신처 NPC 셋: `assets/sprites/unified/npc_mechanic_idle_1.png`, `npc_keeper_idle_1.png`, `npc_archivist_idle_1.png` (같은 화풍, 다른 실루엣)
- 지금 임시 그림: `assets/sprites/unified/npc_drifter_idle_1.png` (128x132 캔버스)
- 키 **117px**(보관인과 같은 높이)

## 생김새
- 오래 떠돈 죄수. 해진 죄수복 위에 **여러 겹 누빈 망토**, 목까지 감은 천, 얼굴 반을 가린 두건.
- 등이 아니라 **허리와 가슴에** 주머니·병·고철 조각을 주렁주렁 단다(보관인의 등짐 상자와 구별).
- 한 손을 앞으로 내밀어 손바닥 위에 작은 헤이즈 결정 하나(거래하는 사람). 결정만 청록으로 빛난다.
- 색은 바랜 적갈색·회갈색(이벤트 방 강조색 `events.COLORS['drifter'] = (240, 190, 120)`과 어울리게).

## 동작 (4장)
| 이름 | 장 | 자세 |
|---|---|---|
| `idle` | 2 | 숨쉬기(어깨 1~2px), 손바닥 결정이 살짝 오르내림 |
| `deal` | 2 | 결정을 쥐고 끄덕임 (거래를 마쳤을 때, 선택) |

- 오른쪽 옆모습(게임이 플레이어 쪽으로 뒤집는다). 발 바닥선 같은 줄, 캔버스 통일.
- 새 폴더 `assets/sprites/forge/drifter_v1/` (마스터, `frames/`, 1배 GIF).

## 절차
마스터 → 대기 2장 → (가능하면) 거래 2장. 같은 이미지는 최대 3번. 보고서 `docs/codex/reports/T51.md`, 상태 `review`.

## 합격 기준
- [ ] 1배에서 보관인과 실루엣으로 구별된다(등짐 없음, 망토·앞으로 내민 손)
- [ ] 은신처 NPC 셋과 같은 화풍·외곽선·밝기
- [ ] 거래하는 사람으로 읽힌다(손 위 결정)
- [ ] 보고서에 솔직하게
