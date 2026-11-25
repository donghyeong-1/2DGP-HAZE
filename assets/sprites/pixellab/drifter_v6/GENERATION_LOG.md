# 떠돌이 죄수 drifter v6 생성 기록 (2026-11-25, Claude Code)

배경: 이벤트 방 NPC. 임시 그림은 보관인의 색만 바꾼 것이었고, Codex T51 결과(`assets/sprites/forge/drifter_v1/`, 저장소에 올리지 않음)는
1px 단위 그림(2px 격자 일치율 0.69)이라 v6 캐릭터와 그림체가 달랐다. 사용자 결정(2026-11-25): 이런 그림은 PixelLab으로 만든다.

## 디자인 시안 (10회)
도구: `create_image_pro_flash`, 96x96, no_background, style_image = `guard_v6/raw/base.png`(upload),
usage "Art style, detail level, outline and pixel scale only. Same world as this guard, same body height, but do not copy the character."

설명(영문 그대로): Side view, facing right, full body, standing still on the ground. A wandering escaped prisoner who trades in secret:
worn faded prison clothes under a patched, layered ragged cloak in faded reddish-brown and grey-brown, cloth wrapped around the neck,
a hood and scarf hiding half the face. Pouches, small bottles and scrap metal pieces hang from the belt and chest (no backpack).
One arm is held out forward, palm up, with one small glowing teal crystal shard floating just above the hand. Slim, slightly hunched.
Only the crystal is bright teal; everything else is muted and dark. Character about 60 pixels tall, feet near the bottom of the canvas.

| 파일 | seed | 키(도트) | 화면 키 | 색 | 메모 |
|---|---|---|---|---|---|
| raw_gen/drifter_1.png | 3 | 66 | 132px | 24 | 적갈색 망토, 곧게 섬, 깔끔함 -> **선택** |
| raw_gen/drifter_2.png | 11 | 66 | 132px | 28 | 회갈색, 더 구부정, 주머니가 많지만 흩어진 점이 많음 |

참고 키: 주인공 61도트, 간수 64. 비교판 `shots/review/event_v6_designs.png`(주인공·간수·옛 보관인·시안), 확대 `event_v6_designs_zoom.png`.
시안은 Claude Code가 골랐다(작은 NPC). 2안으로 바꾸려면 raw/base.png를 바꾸고 idle을 다시 뽑는다(1회).

## 기준 그림 `raw/base.png`
drifter_1 그대로(알파 0/255, 24색, bbox (11,27)-(61,93)).

## 동작 (1회)
| 동작 | 도구 | 장 | seed | 평가 | 게임에 쓴 번호 |
|---|---|---|---|---|---|
| idle | animate_image_pixminimax (first = last = base, side/east) | 4+1 | 5 | 좋음: 어깨가 오르고 결정이 살짝 뜬다. 발 고정, 색 이탈 없음 | 0, 2 |

설명: Idle breathing loop: the shoulders rise and fall slightly, the cloak sways a little, and the small teal crystal floating above
the open palm bobs gently up and down. The feet stay planted and the character does not move from the spot.

거래 동작(끄덕임)은 게임이 쓰지 않아 만들지 않았다.

적용: `python tools/apply_pixellab_event.py drifter` -> `assets/sprites/unified/npc_drifter_idle_1~2.png`(136x136, 최근접 2배, 2px 격자 100%).
실제 창 확인: `shots/review/event_v6_ingame.png`(슬럼·공장 이벤트 방).
