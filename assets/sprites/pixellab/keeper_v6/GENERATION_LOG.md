# 보관인 keeper v6 생성 기록 (2026-11-25, Claude Code)

배경: 은신처 NPC. 옛 그림(Codex T22)은 2px 격자는 맞았지만 PixelLab으로 만든 v6 캐릭터와 화풍이 달랐다.
사용자 결정(2026-11-25): 캐릭터 옆에 서는 도트 그림은 PixelLab으로 만든다. 은신처 NPC 셋을 같은 날 한꺼번에 바꿨다.

## 디자인 시안 (15회: 5회 x 3장)
도구: `create_image_pro_flash`, no_background, style_image = 간수 `guard_v6/raw/base.png`(96 캔버스) 또는 그 몸 둘레를 64x64로 자른 것(작은 캔버스),
usage "Art style, detail level, outline and pixel scale only. Same world as this guard, same body height ..., but do not copy the character."
1차(96x96, "about N pixels tall")는 키가 70~77도트로 간수(64)·주인공(61)보다 크게 나와 쓰지 않았다(PixelLab은 글로 적은 키를 지키지 않는다).
2차는 **캔버스를 줄여**(키가 캔버스를 넘지 못하게) 같은 설명으로 다시 뽑았다. 디자인 방향은 옛 그림(Codex T22)·대화 초상화(`assets/portraits/`)의 설정을 글로 옮긴 것.

설명(영문 그대로, 앞에 "Side view, facing right, full body, standing still on the ground." 뒤에 색·키 문장): An old storekeeper of a hidden prisoner hideout: a hunched old man with a grey beard and long nose, wearing a worn brown hooded cloak with a faded teal lining, the hood up. He carries a big iron-banded wooden chest with a padlock strapped on his back like a backpack, and holds a small glowing warm-orange lantern low in one hand in front of him. Patched trousers, old boots.

| 파일 | 캔버스 | seed | 키(도트) | 메모 |
|---|---|---|---|---|
| raw_gen/keeper_1.png | 96x96 | 3 | 77 | 너무 큼 |
| raw_gen/keeper_2.png | 96x96 | 11 | 70 | 큼 |
| raw_gen/keeper_3.png | 80x64 | 3 | 59 | **선택**(화면 118px). 34색 |

비교판: `shots/review/npc_v6_designs.png`(1차), `npc_v6_designs2.png`(2차, 주인공·간수·떠돌이 옆). 시안은 Claude Code가 골랐다(작은 NPC).

## 기준 그림 `raw/base.png`
keeper_3 그대로(알파 0/255).

## 동작 (1회)
`animate_image_pixminimax`, first = last = base, 4장, side/east, seed 5. 게임에 쓴 번호: 0(= base), 2. 색 이탈·발 미끄러짐 없음.
설명: Idle breathing loop: the old man's shoulders and hood rise and fall slightly, and the lantern in his hand sways gently while its flame flickers. The feet stay planted and he does not move from the spot.
모아 보기: `shots/review/npc_v6_frames.png`.

적용: `python tools/apply_pixellab_event.py keeper` -> `assets/sprites/unified/npc_keeper_idle_1~2.png`(100x122, 최근접 2배, 2px 격자 100%).
실제 창 확인: `shots/review/g06/hideout.png`.
