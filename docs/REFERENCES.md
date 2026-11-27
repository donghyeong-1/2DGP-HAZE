# 참고 자료 (REFERENCES)

2D 게임 제작에 도움이 되는 외부 자료를 찾아 평가한 기록이다. 코드나 에셋을 가져온 것이 아니라 **방법을 참고**한 것이며, 가져온 것이 생기면 `docs/ASSETS.md`에 출처와 라이선스를 적는다. (조사일 2026-11-15, Claude Code)

> X(트위터)·스레드의 개별 게시물은 검색으로 잡히지 않았다. 아래는 웹 검색으로 찾은 글, 자료실, 스킬 저장소다.

## 적용한 것
| 자료 | 내용 | 우리 코드에 한 일 |
|---|---|---|
| 코요테 타임 글([kidscancode](https://kidscancode.org/godot_recipes/4.x/2d/coyote_time/index.html), [bugnet](https://bugnet.io/blog/coyote-time-and-input-buffering-explained)) | 낭떠러지를 걸어 떨어진 뒤 0.05~0.1초 동안은 땅 위 점프로 쳐 준다 | `config.COYOTE_TIME = 0.10`, `Player.request_jump`. 코요테로 뛰면 공중 점프는 한 번 그대로 남는다 |
| 점프 입력 버퍼([같은 글](https://bugnet.io/blog/coyote-time-and-input-buffering-explained), [gamedev.net](https://gamedev.net/news/4298-your-players-hate-missed-jump-inputs-heres-why/)) | 착지 직전에 누른 점프를 잠깐 기억했다가 착지하면 뛴다 | `config.JUMP_BUFFER = 0.12`, 점프를 다 쓴 상태에서 누르면 기억했다가 착지 즉시 점프 |
| 타격 멈춤(hit stop) 가이드([Godot 게임필 체크리스트](https://forum.godotengine.org/t/game-feel-checklist-for-godot-4-hit-stop-trauma-shake-coyote-time-and-more/145340), [GameDō](https://gamedo-live.pages.dev/news/game-feel-juice-guide-indie-devs)) | 가벼운 공격 30~50ms, 무거운 공격 60~100ms. 모든 타격에 쓰면 오히려 답답하다 | 1타·2타 45ms, 3타 90ms (`HIT_STOP`), 내가 맞을 때 70ms |
| trauma 방식 화면 흔들림(같은 체크리스트, GDC 2016 "Juicing Your Cameras With Math") | 충격마다 trauma가 쌓이고, 흔들림은 trauma²에 비례, 실제 시간으로 줄어든다 | `effects.add_trauma / tick_shake / shake_offset`. 정수 픽셀로만 흔들고 UI는 제자리에 둔다 |
| 대시 잔상 글([itch.io](https://itch.io/post/4984636)) | 일정 간격으로 현재 스프라이트를 복사해 두고 서서히 옅어지게 한다 | 대시 잔상 (이전 작업) |

## 확인한 점프 수치 (platformer 스킬 문서 기준)
우리 값은 권장 범위 안에 있다. 정점까지 0.35초(권장 0.25~0.45), 높이 3.75타일(권장 2~5), 낙하 속도 상한이 한 프레임에 약 27px(타일 절반 30px 미만이라 얇은 판을 뚫지 않음). 아직 없는 것: 점프 키를 일찍 놓으면 낮게 뛰는 **가변 점프 높이**, 낙하 중력 강화, 머리 모서리 보정. 플레이 점검 뒤 필요하면 추가한다.

## 읽어 볼 만한 자료 (적용 보류)
- [Dead Cells 캐릭터 아트 파이프라인(80.lv)](https://80.lv/articles/case-study-dead-cells-character-art-pipeline), [3D→2D 애니메이션 파이프라인](https://www.jikguard.com/news/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-dead-cells): 키프레임을 먼저 잡고 최소한의 프레임만 쓴 뒤 보간 프레임을 넣는다. 걷기 프레임(T04) 지침을 다듬을 때 참고.
- [Dead Cells가 공정하게 느껴지는 숨은 장치(80.lv)](https://80.lv/articles/dead-cells-hidden-tricks-that-make-the-game-feel-fair): 입력 관용, 판정 보정. 피격·대시 무적 조정에 참고.
- [픽셀 애니메이션 원칙(sprite-ai.art)](https://www.sprite-ai.art/guides/animation-principles): 픽셀은 간격을 조절할 수 없으니 프레임 시간으로 가감속을 표현한다.
- [GMTK Platformer Toolkit(itch.io)](https://gmtk.itch.io/platformer-toolkit/comments?after=72): 점프·이동 수치를 바꿔 가며 느낌을 비교하는 도구.

## 검토 후 설치하지 않은 스킬
Claude Code용 커뮤니티 스킬을 찾아 원문을 읽고 평가했다.

| 스킬 | 판단 | 이유 |
|---|---|---|
| popey/claude-code-skills `2d-games` | 제외 | 경로가 없고(404), 저장소 표시가 다른 프로젝트(Antigravity Awesome Skills)와 섞여 출처가 일관되지 않음. 설치에 `npx`로 네트워크 코드를 받음 |
| davila7/claude-code-templates `game-development` | 제외 | 연결된 하위 스킬이 저장소에 없음, 내용이 일반론, `Bash` 허용 |
| omer-metin/skills-for-antigravity `pixel-art-sprites` | 제외 | 페르소나 문구 위주, 구체 수치 없음, AI로 변환한 문서 |
| **gamedev-skills/awesome-gamedev-agent-skills** (Apache-2.0, 약 375 stars) `game-feel`, `platformer`, `input-systems`, `physics-tuning`, `level-design`, `game-ui-ux`, `roguelike`, `pygame-core` | **설치함 (2026-11-15, 사용자 요청)** | 원문을 읽었고 수상한 지시나 네트워크 호출이 없다(스크립트는 `platformer/scripts/jump_tuner.py` 하나, 표준 라이브러리만 사용). 수치가 구체적이다(타격 멈춤 단계, 코요테 0.06~0.15초, 버퍼 0.05~0.2초 등). 예제 코드는 Godot·Unity용이라 이 프로젝트에는 방법만 참고한다. 처음 시도는 자동 권한 심사에서 거부되었고, 사용자가 설치를 직접 지시한 뒤 `~/.claude/skills/`에 복사했다(원문을 읽어 확인한 파일 그대로, `npx` 사용 안 함). 라이선스 원문은 `~/.claude/skills/_licenses/awesome-gamedev-agent-skills/` |

(다른 PC에서 설치하려면):
```bash
npx skills add gamedev-skills/awesome-gamedev-agent-skills --skill game-feel --agent claude-code
```
다른 스킬(`platformer`, `input-systems` 등)도 `--skill` 이름만 바꾸면 된다. 실행 전에 저장소의 `skills/<분류>/<이름>/SKILL.md`를 먼저 읽어 보길 권한다. Apache-2.0이므로 설치하면 `docs/ASSETS.md`에 출처와 라이선스를 적는다.

## 다음에 해 볼 만한 것 (제안)
1. **가변 점프 높이 + 낙하 중력** (platformer 문서의 "release cut 0.5"): 점프 키를 짧게 누르면 낮게 뜀. 플레이 점검에서 점프가 둥둥 뜨는 느낌이면 적용.
2. **착지 먼지, 대시 시작 먼지** 이펙트 (game-feel의 small 단계). `poof` 시트를 재사용하면 된다.
3. **접근성 옵션**: 화면 흔들림 세기 0~100%와 번쩍임 줄이기(일시정지 화면에 설정). 3주차 UI 작업과 같이.
4. **무기 식칼(투사체)**: 지금의 `projectile.py`를 일반화. 8방향 사전 회전 프레임이 필요하다.
5. **스테이지 격자와 방 전환·미니맵**(기획서 5.6): 3주차 핵심. 적을 모두 처치하면 문이 열리는 흐름.
6. **헤이즈 조각 드롭과 정비방 업그레이드**: 재화가 없어 성장 시스템이 비어 있다.
7. **저장소 점검**: `tests/`를 `pytest` 없이도 도는 현재 방식 그대로 두되, 한 번에 돌리는 `tests/run_all.py`를 두면 편하다.

## 이펙트 제작 방식 (2026-11-24)
- [patch-gg/pixelfx](https://github.com/patch-gg/pixelfx) (MIT)의 `docs/AUTHORING.md`와 `skills/pixelfx/SKILL.md`, 그 바탕인 Hugo Duprez의
  [How to make (good) pixel art effects with Claude](https://www.spritefusion.com/blog/how-to-make-good-pixel-art-effects-with-claude):
  이펙트 하나 = 작은 코드, 색 층과 빛 층, 선과 빛으로 만들기, 속도만큼 늘어나는 불티, 단계가 있는 연출, 굽고 보고 고치기.
  **방식만 배웠다.** 코드와 결과물은 가져오지 않고 `tools/fxkit.py`를 파이썬(numpy)으로 새로 썼다. 절차는 `.claude/skills/haze-fx/SKILL.md`.
- 화풍 참고: INARI(스팀 상점 영상을 프레임별로 봄). 그림·이름·캐릭터는 쓰지 않는다. 처음에는 '흰색이 주, 색은 가장자리'로 읽었으나
  프레임마다 재 보니 반대였다: **진한 색 면이 주, 흰색은 한 장짜리 섬광과 작은 별뿐**(처형 원반 프레임에서 붉은색 약 11%, 흰색 약 2%),
  색 면의 수명은 2~3프레임, 화면 정지는 한 번도 없음, 처형 전 0.3초 암전. 측정값과 장면별 관찰은
  `.claude/skills/haze-inari/references/inari-analysis.md`, 기법과 우리 도구의 대응은 `.claude/skills/haze-inari/SKILL.md`. 영상의 프레임은 저장하지 않았다.

## 2026-11-27 HUD 행동 칸 배치 조사 (무기·E 패널 W4)
사용자 "배치를 새로 짜는 것으로 현재 비슷한 장르 게임들의 ui 배치나, 색, 반투명도, 크기 등을 조사해서 세팅을 해줘"에 따라 지휘 쪽이 조사했다.
**아래 글들은 웹 검색 결과의 요약으로 확인한 것이다.** 일부 사이트는 자동 접근을 막아 본문을 직접 읽지 못했고, 게임 화면을 직접 보지도 못했다. 다시 받아 오려고 하지 않는다.

확인된 것 (출처 있음):
1. 능력 칸·무기 선택·빠른 사용 칸은 보통 화면 아래 가운데나 아래 귀퉁이에 둔다. 화면 한가운데에 늘 떠 있는 HUD는 시선을 전투에서 떼어 놓는다.
   ([abratabia.com HUD 설계 글](https://www.abratabia.com/game-ui-design/hud-design.php), [medium.com/my-games-company HUD 글](https://medium.com/my-games-company/heads-up-an-in-depth-dissection-of-one-of-the-most-important-gaming-ui-elements-the-hud-6aa139510804))
2. 성공한 액션 게임의 HUD는 늘 떠 있는 요소가 3~5개이고 나머지는 필요할 때만 나온다. 자리가 좁으면 숫자·글보다 아이콘으로 알린다. (같은 두 글)
3. 색만으로 정보를 알리지 않는다. 아이콘·모양·글자를 함께 쓴다. 준비됨/재충전 중 같은 상태에 특히. ([uxdesign.cc "how to not overwhelm players"](https://uxdesign.cc/how-to-not-overwhelm-players-c0e1d14c6b4c), 일반 UI 지침)
4. 쿨다운 표시가 화면 가운데에서 멀면 플레이어가 전투에서 눈을 떼야 하고, 결국 보지 않고 연타하게 된다는 플레이어 의견이 있다. 제안된 대책은 준비됐을 때의 소리와 캐릭터 가까이의 신호.
   ([Steam 토론 글](https://steamcommunity.com/app/572220/discussions/0/3476238687974367021))
5. 1080p의 제목 안전 영역은 좌우 96px, 위아래 40px 안쪽이다. TV 기준이라 PC 창 게임에는 느슨하게 적용한다. ([Xbox GDK 'screen areas'](https://devdocs.xbox.com/build/core-features/graphics/overviews/screen-areas))
6. 하데스 계열은 체력과 그에 딸린 자원(게이지, 탄약)을 한 귀퉁이에 붙여 둔다: "God Gauge가 체력 막대 아래에", "탄약이 체력 막대 오른쪽에", Hades II는 체력·마력이 화면 왼쪽 아래 가장자리.
   ([Hades 위키 Gameplay mechanics](https://hades.fandom.com/wiki/Gameplay_mechanics), [pixeltwelve.com Hades II HUD 안내](https://pixeltwelve.com/guides/hades-ii-life-magick-armor-hud))

확인하지 못한 것 (지휘 쪽이 아는 장르 관습. **근거가 약하다**):
- 횡스크롤 액션 로그라이크의 행동 칸은 한 줄로 가지런히, 아랫변을 맞춰 놓는 경우가 많고, 칸의 순서가 키 순서와 같으며, 무기를 바꿔도 칸의 자리는 움직이지 않는다(자리가 곧 기억이다).
- 칸 크기는 1080p에서 한 변 56~72px쯤(화면 높이의 5~7%), 지금 쓰는 것이 다른 것보다 1.2~1.4배 크다.
- 칸 바탕은 어두운 반투명(불투명도 0.6~0.85). 지금 쓰는 칸은 더 불투명하고 밝게, 쓰지 않는 칸은 아이콘을 0.5~0.7로 흐리게.
- 이름·설명 글은 늘 띄워 두지 않고 작게 두거나 바뀔 때만 잠깐 보여 준다.

우리에게 적용한 것: 무기·E 패널 'row'(`docs/opus/TASKS.md` '4차' W4). 다른 게임의 화면을 흉내 내지 않고 구성 원리만 가져왔다.
