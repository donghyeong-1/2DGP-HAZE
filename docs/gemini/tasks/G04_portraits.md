# G04 대화 초상화 (주인공 + 은신처 NPC 3)

먼저 `docs/gemini/COMMON.md`를 읽고 그 규칙을 따른다.

## 배경
INARI처럼 대화 때 작은 픽셀 말풍선 옆에 **고해상도 상반신 초상화**를 띄운다(`docs/plan_v6.md`). 초상화는 픽셀 아트가 아니다.
보스 초상화는 G02 디자인이 확정된 뒤 따로 만든다.

## 만들 것 (각 상반신, 1024×1024 이상, 마젠타 단색 배경)
| 파일 | 인물 | 기준 |
|---|---|---|
| `hero_portrait.png` | 주인공 | `assets/sprites/gemini/hero_concepts_v1/hero_A_side.png` + **흰 머리**(G01 결정), 청록 눈, 머플러 |
| `mechanic_portrait.png` | 정비사 (영구 강화) | `assets/sprites/unified/npc_mechanic_idle_1.png` 모습·색 유지 |
| `keeper_portrait.png` | 보관인 (물건 맡기기) | `assets/sprites/unified/npc_keeper_idle_1.png` |
| `archivist_portrait.png` | 기록관 (이야기·기록) | `assets/sprites/unified/npc_archivist_idle_1.png` |

- 넷 모두 같은 화풍(선 있는 애니풍 일러스트 허용, 색은 게임 그림과 맞춘다), 같은 크기·구도(가슴 위, 화면 안쪽을 보는 3/4 각도).
- 표정 기본 1장씩. 여유가 있으면 주인공만 표정 2장 더(`hero_portrait_angry.png`, `hero_portrait_hurt.png`).
- 새 폴더 `assets/sprites/gemini/portraits_v1/`. 그림마다 최대 3번.

## 합격 기준
- [ ] 게임 속 모습(픽셀)과 같은 인물로 알아볼 수 있다
- [ ] 네 장의 화풍·구도·크기가 같다
- [ ] 마젠타 배경, 보고서에 모델명·프롬프트
