# 진행상황 (PROGRESS)

마지막 갱신: 2026-11-05 [Claude Code]

## 진행 중
- (없음. 작업을 시작하면 `[도구명] 작업 내용 / 수정 중인 파일`을 적는다.)

## 1차 발표 마감 (최우선)
- 발표일 2026-11-04, 제출 마감은 발표 당일 00:01 → **실질 마감은 11월 3일 밤**
- 제출물: 발표 영상(정확히 1분 30초, YouTube 공개 설정, 소리·화질 확인) + Git 저장소 주소 + 10p 이내 PPT
- 1차 발표는 기획 중심 평가이므로 게임 구현은 필요 없다.

| 날짜 | 할 일 | 상태 |
|---|---|---|
| 11/1 (일) | 기획서·두 PPT·대본 최종화 | 문서와 PPT 완료, 대본 길이 확인 남음 |
| 11/2 (월) | 영상 녹화·편집, 1분 30초 맞추기 | 예정 |
| 11/3 (화) | YouTube 업로드(공개), GitHub 커밋, e-class 제출 (자정 전) | 예정 |

## 완료
- 기획서(`docs/기획서.md`), 발표 PPT 10장(`docs/presentation_1st.pptx`), 기획서 PPT 32장(`docs/plan_deck.pptx`), 대본(`docs/script_1st.md`)
- 설계 목업 15종(`assets/presentation_examples/`, `tools/make_mockups.py`)
- 캐릭터 7종 콘셉트(`assets/concept/`)와 통일 규격 스프라이트(`assets/sprites/unified/`, `docs/sprite_spec.md`)
- 공유 규칙(AGENTS.md)과 결정 기록(DECISIONS.md 맨 위 "현재 기준 요약")

## 다음 할 일 (우선순위 순)
1. [ ] 대본을 소리 내어 읽어 90초에 맞추기 (현재 약 500자, 95초 추정), 표지에 이름 추가
2. [ ] GitHub 저장소 생성, 원격 연결, 첫 커밋 (제출용 주소). 커밋 전 용량이 큰 원본 이미지 포함 여부 결정
3. [ ] 영상 녹화, YouTube 업로드(공개), e-class 제출
4. [ ] 이미지 생성 모델명과 이용 조건 확인 후 `docs/ASSETS.md` 보완
5. [~] 1주차(11/5~11/11): 뼈대·이동·2단 점프·충돌·상태 머신·대시 슬롯 구현 완료(5.9 항목 대부분). 남은 것: 마우스 조준 방향 확인, 직접 플레이 점검, 동작 프레임 교체
6. [ ] (발표 후) 스프라이트 동작 프레임 제작, 무료 에셋(타일·UI·사운드) 선정

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
