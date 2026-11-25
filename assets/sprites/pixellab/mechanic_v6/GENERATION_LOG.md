# 정비사 mechanic v6 생성 기록 (2026-11-25, Claude Code)

배경: 은신처 NPC. 옛 그림(Codex T22)은 2px 격자는 맞았지만 PixelLab으로 만든 v6 캐릭터와 화풍이 달랐다.
사용자 결정(2026-11-25): 캐릭터 옆에 서는 도트 그림은 PixelLab으로 만든다. 은신처 NPC 셋을 같은 날 한꺼번에 바꿨다.

## 디자인 시안 (15회: 5회 x 3장)
도구: `create_image_pro_flash`, no_background, style_image = 간수 `guard_v6/raw/base.png`(96 캔버스) 또는 그 몸 둘레를 64x64로 자른 것(작은 캔버스),
usage "Art style, detail level, outline and pixel scale only. Same world as this guard, same body height ..., but do not copy the character."
1차(96x96, "about N pixels tall")는 키가 70~77도트로 간수(64)·주인공(61)보다 크게 나와 쓰지 않았다(PixelLab은 글로 적은 키를 지키지 않는다).
2차는 **캔버스를 줄여**(키가 캔버스를 넘지 못하게) 같은 설명으로 다시 뽑았다. 디자인 방향은 옛 그림(Codex T22)·대화 초상화(`assets/portraits/`)의 설정을 글로 옮긴 것.

설명(영문 그대로, 앞에 "Side view, facing right, full body, standing still on the ground." 뒤에 색·키 문장): A sturdy, broad-shouldered woman mechanic of a hidden prisoner hideout: dark hair tied in a bun, orange goggles pushed up on her forehead, stained olive-green work overalls with orange patches over a dark shirt, heavy boots. Her right arm is a grey mechanical prosthetic with one small teal glowing light. She rests a very large steel wrench over her shoulder with one hand, the other hand on her hip.

| 파일 | 캔버스 | seed | 키(도트) | 메모 |
|---|---|---|---|---|
| raw_gen/mechanic_1.png | 96x96 | 3 | 77 | 너무 큼(154px). 디자인은 좋음 |
| raw_gen/mechanic_2.png | 96x96 | 11 | 77 | 너무 큼 |
| raw_gen/mechanic_3.png | 80x72 | 3 | 66 | **선택**(화면 132px, 렌치 포함). 28색 |

비교판: `shots/review/npc_v6_designs.png`(1차), `npc_v6_designs2.png`(2차, 주인공·간수·떠돌이 옆). 시안은 Claude Code가 골랐다(작은 NPC).

## 기준 그림 `raw/base.png`
mechanic_3 그대로(알파 0/255).

## 동작 (1회)
`animate_image_pixminimax`, first = last = base, 4장, side/east, seed 5. 게임에 쓴 번호: 0(= base), 2. 색 이탈·발 미끄러짐 없음.
설명: Idle breathing loop: her chest and shoulders rise and fall slightly and the big wrench resting on her shoulder shifts a little with the breath. The feet stay planted and she does not move from the spot.
모아 보기: `shots/review/npc_v6_frames.png`.

적용: `python tools/apply_pixellab_event.py mechanic` -> `assets/sprites/unified/npc_mechanic_idle_1~2.png`(116x134, 최근접 2배, 2px 격자 100%).
실제 창 확인: `shots/review/g06/hideout.png`.
