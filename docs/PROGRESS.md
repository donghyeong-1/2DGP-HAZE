# 진행상황 (PROGRESS)

마지막 갱신: 2026-11-15 [Claude Code]

## 진행 중
- (없음. 작업을 시작하면 `[도구명] 작업 내용 / 수정 중인 파일`을 적는다.)

## 1차 발표 (2026-11-04, 지남)
- 영상 촬영 완료(사용자 보고 11/3). GitHub 저장소 https://github.com/donghyeong-1/2DGP-HAZE 공개. e-class 제출 여부는 사용자가 확인.
- (기록) 발표일 2026-11-04, 제출 마감은 발표 당일 00:01 → 실질 마감은 11월 3일 밤
- 제출물: 발표 영상(정확히 1분 30초, YouTube 공개 설정, 소리·화질 확인) + Git 저장소 주소 + 10p 이내 PPT
- 1차 발표는 기획 중심 평가이므로 게임 구현은 필요 없다.

| 날짜 | 할 일 | 상태 |
|---|---|---|
| 11/1 (일) | 기획서·두 PPT·대본 최종화 | 문서와 PPT 완료, 대본 길이 확인 남음 |
| 11/2 (월) | 영상 녹화·편집, 1분 30초 맞추기 | 예정 |
| 11/3 (화) | YouTube 업로드(공개), GitHub 커밋, e-class 제출 (자정 전) | 예정 |

## 완료
- 캐릭터 7종 hibit 화풍 제작·검토 완료, `assets/sprites/unified/` 교체 (구 파일은 `unified_legacy/`)
- 1주차 구현(`src/`): 프레임워크, 이동·2단 점프·대시·타일 충돌, 상태 머신, 게이지 로직, 모드 4종, 테스트 31개
- 이펙트 8종(pixelfx 마무리), 픽셀 폰트(갈무리), 픽셀 규칙 문서와 자동 검사
- 기획서(`docs/기획서.md`), 발표 PPT 10장(`docs/presentation_1st.pptx`), 기획서 PPT 32장(`docs/plan_deck.pptx`), 대본(`docs/script_1st.md`)
- 설계 목업 15종(`assets/presentation_examples/`, `tools/make_mockups.py`)
- 캐릭터 7종 콘셉트(`assets/concept/`)와 통일 규격 스프라이트(`assets/sprites/unified/`, `docs/sprite_spec.md`)
- 공유 규칙(AGENTS.md)과 결정 기록(DECISIONS.md 맨 위 "현재 기준 요약")

## 다음 할 일 (우선순위 순)
1. [ ] **(사용자) 2차 발표 제출 (발표 당일 0시 1분까지)**: `python src/main.py`로 데모 녹화(순서는 `docs/script_2nd.md`) → 소리·글자 확인 → YouTube 업로드 → e-class에 영상 링크와 GitHub 링크 제출. PPT는 `docs/presentation_2nd.pptx`
2. [ ] **(사용자) 직접 플레이 점검**: 공격 사거리, 적 속도·체력, 피격 무적, 대시 잔상, 점프 느낌. 불편한 수치는 `src/config.py`만 고친다 (기획서 5.10의 `[ ]`)
3. [ ] **(사용자)** Codex 작업: T06·T09·T10·T11 제작본 검토(`review`). T12는 구현할 적에 대한 사용자 결정 대기 (`docs/codex/TASKS.md`의 한 줄 명령)
4. [ ] **(사용자)** 이미지 생성 모델명·이용 조건 확인 후 `docs/ASSETS.md`의 "이미지 생성 모델" 줄 채우기. BGM 후보 선택(다운로드는 허락 필요)
5. [x] 2주차 Claude 작업(조준 공격, 적 2종, 게이지 연결, 충돌 박스) + 3주차 앞당김(방 잠금·전환, 미니맵, 고농도 방, E 강화, 조각) (11/15)
6. [ ] (3주차 11/19~) 정비방과 업그레이드(조각 사용), 무기 식칼·건틀릿·사슬, 적 사냥개·간수, 스테이지 2·3, 보스 크래셔·아크, 걷기 프레임이 오면 애니메이션 연결, 가변 점프 높이·접근성 옵션

## 열린 질문
- 타이틀 로고와 큰 제목 글자("탈출 성공" 등)는 픽셀 폰트를 키울 수 없어 이미지로 만들어야 한다 (지금은 14px 글자로 임시 표시)
- 코드네임 "화이트"와 주인공 이름은 임시 값이다.
- 게이지 수치(-1%/3초, 스킬 증감 등)는 플레이 테스트 전 초안이다.
- 2·3차 발표 일정
- (해결 2026-11-03) 저장소 문서의 과거 기록은 중립 문장으로 정리함

## 작업 로그
- 2026-11-01 [Claude] 로그라이크로 용어 통일, 한 줄 소개 갱신, 기획서·PPT·결정 문서 불일치 수정, 최종 재생성 / AGENTS.md, docs/*, tools/*
- 2026-11-01 [Claude] 페이드 사망 기준을 0%로 확정(1~19%는 약화 구간), E 강화 30% 이상, 건틀릿 5% 하한
- 2026-11-01 [Claude] 게이지 규칙 v2 반영(시간 경과 감소, 고농도 방, 보스 스킬 상승·하강, 무기 4종 구간 변화)
- 2026-11-01 [Claude] S·F·Esc 조작 보강, 기획서 PPT 3장 추가(32장)
- 2026-11-01 [Claude] 두 PPT 재작성(설명·예시 보강), 설계 목업 15종 생성, 공통 도구 deckkit 추가
- 2026-11-01 [Claude] 스프라이트 80px 통일 가공과 규격 문서
- 2026-11-01 [Codex] 발표 PPT 예시 자리 안내, 가독성 개선, 스프라이트 시안 제작 (이후 Claude가 재작성)
- 2026-10-31 [Claude/Gemini] 기획서 초안과 수정, 공유 규칙 작성, 초기 PPT와 대본 생성
2026-11-02 [Claude Code] 기획서 PPT 검토 반영: 게이지 한계 기준 문장, 대미지 예시 36→45 근거, 비교표 대상 구체화, 표지 이름, transitions 설치 / make_plan_deck.py, make_presentation_1st.py, make_mockups.py, 기획서.md, DECISIONS.md
2026-11-05 [Claude Code] 기획서 5장 구현 설계 추가(폴더 구조, 루프, 좌표·충돌, 플레이어 FSM, config 수치, 방 데이터, 게이지·무기·적 설계, 테스트, 1주차 완료 기준) / docs/기획서.md, DECISIONS.md, sprite_spec.md, PROGRESS.md
2026-11-05 [Claude Code] 1주차 구현: src/(game_framework, game_world, config, haze_gauge, player 상태 머신·2단 점프·대시 슬롯·타일 충돌, room, ui, title/play/pause/ending 모드), data/rooms/test_01.txt, tests/(게이지 11개, 플레이어 13개 통과), README.md, 임시 이미지 생성 도구
2026-11-07 [Claude Code] 픽셀 아트 규칙 적용: draw_image 정수 좌표 1배 그리기, 최근접 필터 설정, pixel_rules.md, tests/test_pixel_assets.py(5개), 기획서 5.3·AGENTS.md 반영 / src/*, docs/*
2026-11-07 [Claude Code] 한글 픽셀 폰트 갈무리(OFL 1.1) 적용: assets/fonts, draw_text 원래 크기 14/11px만, 폰트 테스트, ASSETS·pixel_rules·DECISIONS 갱신 / src/assets.py 외 UI·모드 파일
2026-11-07 [Claude Code] pixelfx 이펙트 8종 마무리(tools/finish_effects.py, assets/effects), 픽셀 테스트 이펙트까지 확대(7개), agent-sprite-forge를 Codex·Claude Code에, codixel을 Claude Code에 설치, 문서 갱신 / tools/finish_effects.py, tests/test_pixel_assets.py, assets/effects/*, docs/*

2026-11-07 [Codex] 주인공 마스터 스틸컷 시험 및 1배 비교 / assets/sprites/forge/, docs/image_prompts.md, docs/ASSETS.md, docs/PROGRESS.md
2026-11-07 [Claude Code] hibit 마무리 변형 4종 시험(눈 약함 확인), tools/finish_character.py, sprite_spec hibit 절, Codex 재생성 프롬프트, 결정 기록 / tools/finish_character.py, docs/*, .gitignore

2026-11-07 [Codex] 주인공 마스터 v2 및 1배 비교 / assets/sprites/forge/hero_v2/, docs/image_prompts.md, docs/ASSETS.md, docs/PROGRESS.md
2026-11-07 [Claude Code] 주인공 v2 검토(합격), 나머지 6종 일괄 생성 프롬프트 작성 / docs/ai_commands.md, DECISIONS.md, PROGRESS.md

2026-11-07 [Codex] 적·보스 마스터 6종과 1배 비교 / assets/sprites/forge/, docs/image_prompts.md, docs/ASSETS.md, docs/PROGRESS.md
2026-11-07 [Claude Code] 6종 결과 검토(7종 화풍 일치), unified 교체·legacy 보존, 구 스크립트 보호, 발 여백 보정 / assets/sprites/unified*, tools/pixelize_sprites.py, src/config.py, src/player.py, docs/*
2026-11-09 [Claude Code] 1주차 진행 점검(체크리스트 11개 중 9개 확인, 2개 직접 확인 대기), 5.9 표기와 PROGRESS 정리 / docs/기획서.md, docs/PROGRESS.md
2026-11-11 [Claude Code] 새 clone 검증(테스트 31개 통과), requirements.txt와 docs/SETUP.md 추가(다른 컴퓨터에서 이어서 작업하는 절차) / requirements.txt, docs/SETUP.md, AGENTS.md, README.md
2026-11-11 [Claude Code] 효과음 9종 코드 합성·연결(tools/make_sfx.py, assets/sfx, 소리 테스트 2개), 에셋 현황·모델명·BGM 후보 정리, Codex 프롬프트(걷기·타일·로고) 작성 / tools/make_sfx.py, src/assets.py, player.py, play_mode.py, main.py, config.py, tests/test_sfx.py, docs/*
2026-11-11 [Claude Code] codeart2d 스킬로 로고·타일 5종 제작(tools/codeart, tools/make_codeart.py), 방·타이틀에 적용, 코드 아트 검사 테스트 추가 / tools/*, assets/ui, assets/tiles, src/room.py, src/title_mode.py, tests/test_pixel_assets.py, docs/*
2026-11-11 [Claude Code] 외부 툴 허용 공지를 AGENTS.md·DECISIONS에 기록, Codex 분담·맵 에디터 도입 검토 / AGENTS.md, docs/DECISIONS.md, docs/PROGRESS.md (해상도 1920x1080 이전은 보류, 코드 변경 없음)
2026-11-11 [Claude Code] Codex 작업 큐 세팅(docs/codex: TASKS, COMMON, T01~T06, 보고서 양식), tools/check_sprites.py, finish_character.py를 1.5배·--like·프레임 폴더 지원으로 확장, AGENTS.md 역할 분담 추가 / docs/codex/*, tools/*, AGENTS.md, docs/sprite_spec.md, docs/ai_commands.md, docs/DECISIONS.md

2026-11-11 [Codex] T01 주인공 마스터 v3 제작·검사(시각 기준 일부 미달, 검토 대기) / assets/sprites/forge/hero_v3/, assets/sprites/forge/n09_v3/, assets/sprites/forge/n09_v3_idle.png, docs/codex/reports/T01.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md, docs/PROGRESS.md
2026-11-11 [Claude Code] 해상도 1.5배 이전(1920x1080, 타일 60): config·UI·모드 위치·플레이어 테스트, 타일 5종·로고 60px 고디테일 재제작, 캐릭터 7종 임시 재마무리, 임시 타일 삭제, 기획서 5.3·5.5 수치 갱신 / src/*, tests/test_player.py, tools/*, assets/tiles, assets/ui, assets/sprites/unified, docs/*
2026-11-11 [Claude Code] T01 검토: 부분 합격(몸·옷 좋아짐, 얼굴·림라이트 문제) -> 재작업 v3b 지침 작성 / docs/codex/reports/T01_review.md, tasks/T01_hero_v3.md, COMMON.md, TASKS.md
2026-11-11 [Codex] T01 주인공 v3b 재작업 및 1배·얼굴 비교, 스프라이트와 픽셀 검사 통과, 검토 대기 / assets/sprites/forge/hero_v3b/, assets/sprites/forge/n09_v3b/, assets/sprites/forge/n09_v3b_idle.png, docs/codex/reports/T01.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md, docs/PROGRESS.md
2026-11-11 [Claude Code] T01 v3b 검토 합격, T02·T03·T04 ready로 전환, 후속 작업 기준을 v3b로 변경, 게임의 주인공 스프라이트를 v3b로 교체 / docs/codex/*, DECISIONS.md, PROGRESS.md, assets/sprites/unified/n09_idle.png
2026-11-11 [Codex] T02 적 3종 v3 제작, 1배 비교 및 픽셀 검사 통과, 검토 대기 / assets/sprites/forge/enemy_*_v3*, assets/sprites/forge/lineup_v3_a_1x.png, docs/codex/reports/T02.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md, docs/PROGRESS.md
2026-11-11 [Claude Code] T02 검토 합격(적 3종 v3), unified 교체 / docs/codex/reports/T02_review.md, TASKS.md, DECISIONS.md, assets/sprites/unified/

2026-11-11 [Codex] T01~T03 마스터 7종 재제작 및 1배 비교, 개별 스프라이트 검사와 픽셀 테스트 통과, 검토 대기 / assets/sprites/forge/remake_t01_t03/, docs/codex/reports/T0*_remake.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md
2026-11-11 [Claude Code] 대시 잔상 효과(던그리드 스타일): 대시 중 0.016초마다 청록색 반투명 잔상을 남기고 0.3초에 3단계로 옅어짐, 테스트 2개 추가(15개 통과) / src/player.py, src/assets.py, src/config.py, tests/test_player.py
2026-11-15 [Claude Code] 2주차 전투 구현: 철파이프 마우스 조준 공격(3연타·부채꼴 판정·화면 멈춤), 적 2종(슬럼·투척병, transitions FSM), 고철 투사체(codeart2d 스프라이트), 게이지 전투 연결(+3/+8/-5, 오버로드 피해·기절), 피격 무적, 체력 바·남은 적 UI, 충돌 body.py 분리, 효과음 4종, 테스트 16개 추가 / src/(body, effects, weapon, enemy, projectile, player, play_mode, ui, haze_gauge, assets, config), tests/test_combat.py, tools/*, data/rooms/test_01.txt, docs/*
2026-11-15 [Claude Code] 외부 자료 조사(docs/REFERENCES.md)와 반영: 코요테 타임·점프 입력 버퍼, trauma 화면 흔들림, 타격 멈춤 단계화, tests/run_all.py, 테스트 7개 추가 / src/(player, effects, assets, game_world, play_mode, weapon, config), tests/*, docs/REFERENCES.md, DECISIONS.md, 기획서.md, README.md. 커뮤니티 스킬은 평가만 하고 설치 보류(사용자 결정)
2026-11-15 [Claude Code] 2차 발표 준비: 스킬 8종 설치(gamedev-skills), 스테이지 격자·방 잠금/클리어/전환·미니맵·고농도 방(src/stage.py, data/stages, data/rooms/combat_*), E 강화(폭발)·조각 드롭, 테스트 10개 추가(스테이지), 발표 PPT 2장과 영상 대본(tools/make_presentation_2nd.py, docs/presentation_2nd.pptx, docs/script_2nd.md), 데모 캡처(assets/presentation_examples/demo_*.png) / src/*, data/*, tests/test_stage.py, tools/*, docs/*
2026-11-15 [Claude Code] 공격 UI·글자 보강: 이펙트 정수 2배, 글자 28/22/42px, 무기·공격 패널(콤보·재충전·E 상태), 조준점, 데미지 숫자, 큰 체력 바, 일시정지·타이틀 문구 갱신, 픽셀 규칙 정수 배율 예외 기록. 자동 플레이 봇으로 스테이지 1 클리어 가능 확인(E 안 씀 24초·체력 28, E 사용 18초·체력 70) / src/(ui, assets, effects, weapon, enemy, config, play_mode, pause_mode, ending_mode, title_mode), tests/test_pixel_assets.py, docs/*
2026-11-15 [Claude Code] 휘두르기 방향형(tools/make_slash.py, 5방향 사전 렌더+반전, 3종) + 방 재설계(방 5종, 가시, 층 이동 적 AI, 도달 가능성 검사기 src/room_check.py, tests/test_rooms.py, docs/level_design.md), 방 텍스트 s·t 스폰, 스테이지 1을 방 5개로 확장, 자동 플레이 봇으로 클리어 확인(E 안 씀 44.8초·체력 25 / E 사용 42.7초·체력 50), 전투 테스트 6개 추가 / src/(effects, weapon, room, room_check, stage, enemy, player, config), data/rooms/*, data/stages/stage1.py, tools/make_slash.py, assets/effects/pipe-slash*, tests/*, docs/*
2026-11-15 [Claude Code] 맵 개편(사용자 요청): 가변 크기 방+카메라(src/camera.py, room.py), 4방향 출입구와 선택 이동(stage.py), 스테이지 1을 12개 방 가지 구조로(보스 길+가지), 황금방·정비방(items.py, pedestal.py, 진열대 F 상호작용), 보스 크래셔(boss.py, Shockwave), 방 템플릿 7종 신규와 검사기 확장(room_check.py), 휘두르기 이펙트를 codeart2d 스킬(fx_build)로 재제작(tools/make_slash.py), 기획서 2.2·2.3·5.1·5.3·5.6·5.11과 level_design.md 개정, 테스트 재작성(방 검사 16, 스테이지 22). 자동 플레이 봇으로 보스 길 전체와 보스 클리어 확인(60.6초, 체력 30) / src/*, data/*, tests/*, tools/make_slash.py, assets/effects/pipe-slash*, docs/*
2026-11-15 [Claude Code] 게이지 구간·강화별 공격 효과와 주인공 오라(사용자 요청): 휘두르기 시트 구간 3종 추가+강화 보라색 교체, 오라 4종과 오버로드 폭발(tools/make_aura.py, codeart2d fx_build), 구간별 명중 효과·흔들림·멈춤·소리·데미지 색(config.ZONE_FX), 구간 진입 표시, 테스트 9개 추가 / src/(config, effects, weapon, player), tools/(make_slash, make_aura, make_sfx), assets/effects/(pipe-slash-*, aura-*, overload-burst), assets/sfx/swing_*, tests/*, docs/*
2026-11-15 [Claude Code] 특수 공격·1회성 강화·시야선·오라 재설계(사용자 요청): 대시 평타(관통 돌진 베기)·점프 평타(회전 베기)·내려찍기(튕김), 강화를 1회성 일격으로(대미지 ×2.5, 맞은 적마다 폭발), 벽 너머 근접 공격 차단(Room.line_blocked), 보스 도약 내려찍기와 경기장 기둥 낮춤, 공격 효과를 구간마다 모양이 다르게(시트 재제작), 오라를 몸 중심 기운 모양으로 재설계, UI(공격 종류 표시·강화 준비), 테스트 추가 / src/(weapon, boss, room, player, haze_gauge, effects, ui, config), tools/(make_slash, make_aura), assets/effects/*, data/rooms/boss_arena.txt, tests/*, docs/*
2026-11-15 [Claude Code] 대시 평타를 지나온 경로 직선 베기로(effects.PathSlash, 대시 중 누르면 끝날 때 터짐), 강화가 현재 공격(기본·대시·점프·내려찍기)에 얹히도록(강화 점프 시트 air-spin-enhanced), 오라를 실루엣 기반 불꽃(240×320 16프레임, PixelSpec + render_pixelspec 검사)으로 고품질 재제작, 강화 오라가 구간 오라 대체, 테스트 수정·추가 / src/(weapon, effects, player, assets, config, ui), tools/(make_aura, make_slash), assets/effects/(aura-*, air-spin-enhanced), tests/*, docs/*
2026-11-15 [Claude Code] 오버로드 기절 연출(사용자 요청): 화면 전체 섬광·붉은 비네트·전기 노이즈·기절 바, 주인공 전기 아크 오라(aura-stun)·몸 떨림, 회복 먼지, 효과음 2종, 테스트 3개 추가 / src/(ui, effects, player, config), tools/(make_aura, make_sfx), assets/effects/aura-stun, assets/sfx/*, tests/*, docs/*
2026-11-15 [Claude Code] 공격 이펙트 고품질 재제작(사용자 요청): 뾰족한 초승달 검기·스윙 모션·열 색조 디더링·외곽선·링/섬광/불꽃, 9개 시트 전부 교체 / tools/make_slash_hq.py, assets/effects/(pipe-slash*, dash-strike, air-spin*), docs/*
2026-11-16 [Claude Code] 타수 증가(구간·강화별 추가 타격 ExtraHits), 아래로 겨눈 대시(얇은 발판 통과/단단한 바닥은 수평), 방 12개 구조 재설계(tools/build_rooms.py)와 자동 타일링 타일 세트·뒷벽·소품·배경 6테마 재제작(tools/make_tiles_hq.py), Room 겉모습 계산·테마, 테스트 추가 / src/(weapon, player, room, stage, config, title_mode, ending_mode), data/rooms/*, data/stages/stage1.py, tools/*, assets/tiles/tile_set_*, assets/backgrounds/*, tests/*, docs/*

2026-11-16 [Codex] Claude Code의 호환 스킬 9개 설치, T04 걷기 4프레임과 T06 배경판 3종 제작·검사 / assets/sprites/forge/, docs/codex/reports/T04.md, docs/codex/reports/T06.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md

2026-11-16 [Codex] T05 주인공 대기·공격·피격·점프 14프레임 제작 및 검사, 검토 대기 / assets/sprites/forge/hero_actions_v3/, assets/sprites/forge/n09_*_v3*/, docs/codex/reports/T05.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md
2026-11-16 [Claude Code] Codex T02·T03 재제작 적·보스 6종과 T04 걷기 4프레임을 게임에 적용(player._body_image, WALK_*), 테스트 2개 추가 / src/(player, config), assets/sprites/unified/*, tests/test_combat.py, docs/*
2026-11-16 [Claude Code] Codex T05 검토·적용(대기 숨쉬기·피격·점프 프레임, player._body_frame, config.PLAYER_FRAMES), Codex 작업 큐 T07~T12 작성(철파이프 공격, 대시·내려찍기·사망, 적 애니메이션, 크래셔, 사망·엔딩 화면, 간수·사냥개·아크 blocked) / src/(player, config), assets/sprites/unified/*, tests/test_combat.py, docs/codex/TASKS.md, docs/codex/tasks/T07~T12, docs/*

2026-11-16 [Codex] T07 철파이프 공격 5방향 15프레임 제작, 1배 비교·스프라이트 검사·픽셀 테스트, 검토 대기 / assets/sprites/forge/hero_pipe_v3/, assets/sprites/forge/n09_swing_*_v3*/, docs/codex/reports/T07.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md
2026-11-16 [Claude Code] Codex T07 검토·적용(철파이프 공격 자세 5방향, player.start_swing·_body_frame, config.SWING_TIME), 테스트 2개 추가 / src/(player, weapon, config), assets/sprites/unified/n09_swing_*, tests/test_combat.py, docs/*

2026-11-16 [Codex] T08 대시·내려찍기·사망 7프레임 제작 및 검사, 검토 대기 / assets/sprites/forge/hero_special_v3/, assets/sprites/forge/n09_dash_v3*, n09_plunge_v3*, n09_death_v3*, docs/codex/reports/T08.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md
2026-11-16 [Claude Code] Codex T08 검토·적용(대시·내려찍기·사망 자세, player._body_frame 확장, start_plunge_pose, dead_time), 테스트 추가 / src/(player, weapon, config), assets/sprites/unified/n09_dash·plunge·death_*, tests/test_combat.py, docs/*

2026-11-16 [Codex] T09 슬럼 폐인·고철 투척병 애니메이션 12프레임 제작·검사, 검토 대기 / assets/sprites/forge/enemy_actions_v3/, assets/sprites/forge/enemy_slum_*, assets/sprites/forge/enemy_thrower_*, docs/codex/reports/T09.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md

2026-11-16 [Codex] T10 크래셔 대기·찍기·돌진·도약·피격 11프레임 제작·검사, 검토 대기 / assets/sprites/forge/crasher_actions_v3/, assets/sprites/forge/boss_crasher_*_v3*/, docs/codex/reports/T10.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md
2026-11-16 [Claude Code] Codex T09 검토·적용(슬럼 걷기·공격·피격, 투척병 던지기·피격, Enemy._body_frame/_body_image, config.ENEMY_FRAMES), 테스트 2개 추가 / src/(enemy, config), assets/sprites/unified/enemy_slum_*·enemy_thrower_*, tests/test_combat.py, docs/*

2026-11-16 [Codex] T11 사망·엔딩 일러스트 2장과 문구 합성 비교 제작, 1920×1080·32색·불투명 검사 및 픽셀 테스트 통과 / assets/sprites/forge/screens_v1/, docs/codex/reports/T11.md, docs/codex/TASKS.md, docs/image_prompts.md, docs/ASSETS.md
2026-11-16 [Claude Code] Codex T10 검토·적용(크래셔 패턴별 동작 그림, Boss._body_frame, ENEMY_FRAME_LIFT), 테스트 2개 추가 / src/(boss, enemy, config), assets/sprites/unified/boss_crasher_*, tests/test_combat.py, docs/*
