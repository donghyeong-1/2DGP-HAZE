# T32 대화 초상화 (주인공 + 은신처 NPC 3명, 표정 2개씩)

먼저 `docs/codex/COMMON.md`를 읽고 그 규칙을 따른다. 원화는 COMMON 4절 화풍(선 없는 평면 색면, 마젠타 배경)을 따르되, **전신이 아니라 가슴 위 상반신**이다.

## 배경
은신처 NPC와 대화하면 글자 판만 뜬다. 스팀 수준의 2D 게임은 대화 판 옆에 말하는 사람의 초상화가 있다. 초상화가 있으면 짧은 대사도 인물이 살아 보인다(배치는 Claude Code).

## 입력 (같은 인물·의상·색을 지킨다)
- 주인공 N-09: `assets/sprites/forge/remake_t01_t03/n09/master/master_rgba.png`, 게임 그림 `assets/sprites/unified/n09_idle_1.png`
- 정비사·보관인·기록관: `assets/sprites/forge/npc_v1/<mechanic|keeper|archivist>/master/master_rgba.png`, 게임 그림 `assets/sprites/unified/npc_<이름>_idle_1.png`

## 그림 (8장)
| 인물 | 표정 ① 보통 | 표정 ② |
|---|---|---|
| 주인공 `n09` | 무표정, 정면에서 살짝 오른쪽 | 이를 악문 결의 |
| 정비사 `mechanic` | 무뚝뚝 | 씩 웃음 |
| 보관인 `keeper` | 차분 | 걱정 |
| 기록관 `archivist` | 생각에 잠김 | 놀람 |

- 마감 크기 **200x200**(1배), 32색 이하, 알파 0·255, 얼굴이 그림 높이의 절반 정도. 눈은 크게 과장(COMMON 4절). 얼굴·머리카락에 청록 림라이트 금지.
- 주인공은 오른쪽을, NPC 3명은 왼쪽을 본다(대화 판 양쪽에 마주 놓는다).
- `finish_character.py`는 전신용이므로 쓰지 않는다. 마감은 같은 원리(최근접 축소 한 번 → 팔레트 32색 → 알파 이진화)로 하고 방법을 보고서에 적는다.
- 새 폴더 `assets/sprites/forge/portraits_v1/<인물>_<1|2>.png` + 8장 비교 시트 `portraits_v1/sheet_1x.png`.

## 절차
주인공 → 정비사 → 보관인 → 기록관. 같은 이미지는 최대 3번. 보고서 `docs/codex/reports/T32.md`, 상태 `review`.

## 합격 기준
- [ ] 게임 속 전신 그림과 같은 인물로 알아볼 수 있다(머리 모양·색·옷)
- [ ] 두 표정이 한눈에 다르다
- [ ] 보고서에 솔직하게
