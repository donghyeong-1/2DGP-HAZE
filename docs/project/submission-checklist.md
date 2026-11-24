# 최종 제출 전 남은 일 (체크리스트)

2026-11-25 Claude(프로젝트 스레드) 작성. 제출 직전에 위에서부터 한 번 훑는다. `[x]`는 이 문서를 쓸 때 확인한 것, `[ ]`는 남은 일이다. **(사용자)**라고 적힌 것은 사용자만 할 수 있다.

기획서 4.1의 일정으로는 12/10~12/14가 "버그 수정 및 최종 제출" 기간이다. 3차(최종) 발표 날짜와 형식은 아직 정해지지 않았다(`docs/PROGRESS.md` 열린 질문).

## 1. 사용자가 정할 것
- [ ] **(사용자)** 3차 발표 날짜와 형식. 1·2차는 "영상 1분 30초 + PPT 10쪽 이내, YouTube 링크와 GitHub 주소를 e-class에 제출, 마감은 발표 당일 0시 1분"이었다. 3차 발표 초안(`docs/project/presentation_3rd_draft.md`)은 같은 형식이라고 가정했다.
- [ ] **(사용자)** 주인공 이름. 게임과 대사는 'N-09'로만 부른다. '화이트'는 임시 이름이라 화면에 쓰지 않았다.
- [ ] **(사용자)** 열린 PR 병합 순서. 이 문서를 쓸 때 열린 브랜치는 넷이다(NPC 대사·글 정리·작은 기능, 보스·문지기, 증강·버그 훑기, 밸런스·초보자 모드). 모두 `docs/ASSETS.md`·`docs/DECISIONS.md` 맨 끝에 줄을 덧붙여서, 뒤에 병합하는 PR은 그 두 파일에서 충돌이 난다. 충돌은 양쪽 줄을 모두 남기면 된다.

## 2. 에셋 출처·라이선스 (제출 전 필수)
- [ ] **(사용자)** `docs/ASSETS.md` 맨 끝 표 "이미지 생성 도구·모델과 이용 조건"의 빈칸 채우기. 확인할 것:
  - Codex(OpenAI) 내장 이미지 생성의 모델명과 생성물 이용 조건. Codex 앱·계정 화면 또는 OpenAI 공식 약관에서 본다.
  - PixelLab 생성물 이용 조건. **주인공 동작 전부를 체험판(trial) 계정으로 만들었다**. 체험판 생성물을 공개 영상·저장소에 써도 되는지가 가장 중요하다. PixelLab 웹사이트의 약관·요금제 화면에서 본다.
  - Gemini(Antigravity) 생성물 이용 조건. 모델명은 G04·G05에서 `gemini-3.1-flash-image`로 확인했다.
- [ ] 빈칸이 채워지면 엔딩 크레딧(`src/credits_mode.py`)의 '이미지 모델명은 도구가 제공하지 않았다' 줄을 고친다.
- [x] 크레딧에 PixelLab·Gemini 줄을 더했다(2026-11-25). 음악 CC-BY 3곡(Rise of Spirit, Gi-i Dark Ambient Techno, Ancient Apparitions)의 작가 표기, Kenney CC0, Galmuri OFL은 이미 크레딧에 있다.
- [ ] 발표 영상에도 CC-BY 곡을 쓰면 영상 설명란에 곡명·작가·라이선스를 적는다(CC-BY 조건).
- [ ] `docs/image_prompts.md`(Codex 영역) 끝 항목이 마지막 Codex 작업(T49)까지 있는지 Codex에게 확인시킨다.

## 3. 저장소
- [ ] 모든 PR을 병합한 뒤 `main`에서 `python tools/verify.py`와 `PYTHONUTF8=1 python tests/run_all.py`가 통과하는지 본다. 스레드 브랜치는 PROGRESS.md를 고치지 않아서 verify가 'PROGRESS 작업 로그' 항목에서 걸린다. **각 스레드 보고서(`docs/project/*.md`)의 "PROGRESS.md 작업 로그에 넣을 줄"을 옮겨 넣으면 풀린다.**
- [ ] PROGRESS.md의 "지금 상태"(2026-11-19 기준)와 "다음 할 일"을 v8 기준으로 다시 쓴다. 지금은 식칼·Q 교체 등 옛 내용이 남아 있다.
- [x] 저장소에 5MB를 넘는 파일은 없다(가장 큰 것이 글꼴 5.4MB). `.git`은 527MB라 처음 받는 데 시간이 걸린다. 교수·조교가 받는다면 README에 "용량이 크다"를 적어 둘지 정한다.
- [x] `build/`, `dist/`는 `.gitignore`에 있다.
- [ ] 제출할 GitHub 주소가 공개 저장소인지, 시크릿 창에서 열리는지 본다: https://github.com/donghyeong-1/2DGP-HAZE

## 4. 게임 마감
- [x] 디버그 표시는 기본 꺼짐(`config.DEBUG = False`), 테스트 모드도 기본 꺼짐(`options.test_mode = False`).
- [ ] **(사용자)** 새 저장으로 타이틀 → 은신처 → 슬럼(문지기) → 공장(크래셔) → 탑(아크·헤이즈 심장) → 탈출 → 크레딧까지 한 판. 테스트 모드 없이 한 번, 초보자 모드로 한 번.
- [ ] **(사용자)** 실행 파일: `python tools/build_exe.py`로 만들고, Python이 없는 컴퓨터(또는 새 사용자 계정)에서 켜서 소리·글꼴·저장이 되는지 본다.
- [ ] **(사용자)** 게임패드가 있으면 한 판 중 몇 방을 패드로.
- [ ] 각 스레드 보고서의 "화면으로 확인하지 못한 것"을 모아 직접 본다:
  - `docs/project/v8-day6-npc.md`: 무기 설명 칸 길이, 일시정지 조작 목록, 화면 밖 화살표 깜빡임
  - `docs/project/day6-boss.md`, `docs/project/day7-augments.md`, `docs/project/bug-sweep.md`, `docs/project/balance.md`: 각 문서의 같은 절
- [ ] 대화 초상화 `assets/portraits/n09_1~2.png`는 v6 전의 주인공 그림(Codex T32)이다. 지금 주인공(흰 머리, PixelLab)과 다르면 Gemini G04 초상화로 바꿀지 정한다.
- [x] 저장 파일 위치(`~/.haze_save.json`, `~/.haze_options.json`, 오류 기록 `~/.haze_log.txt`)는 README에 있다.

## 5. 발표 자료
- [ ] 3차 발표 초안(`docs/project/presentation_3rd_draft.md`)에 마지막 기능까지 반영됐는지 본다(2026-11-25 문지기·초보자 모드·증기 이펙트·버그 수정 반영).
- [ ] PPT 10쪽 만들기. 2차 때 도구는 `tools/make_presentation_2nd.py`였다.
- [ ] 데모 영상 촬영. 순서는 초안의 대본, 촬영 방법은 `docs/demo_2nd.md`와 같다. 테스트 모드(F6~F9 바로가기)로 보스까지 빨리 간다.
- [ ] YouTube 업로드(공개 또는 일부 공개, 비공개는 안 된다), 시크릿 창에서 열리는지 확인.
- [ ] e-class에 영상 링크와 GitHub 주소 제출. 마감은 발표 당일 0시 1분이었다(전날 밤 안에).
- [ ] `docs/changes_from_plan.md`의 마지막 줄까지 발표에서 말할 순서에 들어갔는지 본다.
