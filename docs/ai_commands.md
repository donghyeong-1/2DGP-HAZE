# 다른 AI에게 내릴 명령어 (ai_commands)

> 참고(과거 기준): 이 문서의 일부 명령은 이전 상태(PPT 자리 표시, 파일 구조)를 기준으로 쓰였다. 현재 규칙은 `docs/DECISIONS.md`의 "현재 기준 요약", PPT는 `docs/slide_image_guide.md`를 따른다.

순서는 **1) Gemini: 이미지 제작 → 2) Codex: PPT 다듬기와 이미지 반영 → 3) Claude 또는 직접: 영상 녹화 전 최종 점검**이다.
각 명령은 그대로 복사해서 붙여넣는다. 작업이 끝나면 해당 AI가 `docs/PROGRESS.md`를 갱신하도록 규칙에 넣어 두었다.

---

## 1. Gemini: 캐릭터 이미지 제작

```text
먼저 C:\code\2-2\2DGP-project\AGENTS.md, docs\PROGRESS.md, docs\DECISIONS.md, docs\image_prompts.md, assets\concept\README.md 를 읽어라. (파일 접근이 안 되면 아래 내용을 기준으로 진행하고, 결과를 내게 알려라.)

[목표]
게임 《헤이즈》의 캐릭터 콘셉트 이미지 7장을 만든다. 과목 공지에 따라 캐릭터는 AI 이미지로 직접 만든다. 발표 PPT에 넣을 이미지다.

[만들 이미지와 파일명]
n09.png (주인공, 흰 머리, 양팔 온전, 복면 없음), boss_ark.png, enemy_slum.png, enemy_thrower.png, enemy_hound.png, enemy_guard.png, boss_crasher.png
저장 위치: C:\code\2-2\2DGP-project\assets\concept\

[규칙]
1. docs\image_prompts.md 의 "스타일 접두사"를 모든 프롬프트 앞에 붙이고, 캐릭터별 프롬프트를 그 뒤에 이어 쓴다.
2. 주인공(n09)을 먼저 만들어 가장 좋은 1장을 고르고, 그 이미지를 참조 이미지로 삼아 나머지 6장을 같은 화풍으로 만든다.
3. 구도는 전신, 어두운 단색 배경, 글자와 로고 없음으로 통일한다. 배경이 투명하면 더 좋다. 화풍은 image_prompts.md의 "화풍 방향"(어둡고 거친 반실사 만화풍, 청록 포인트)을 따른다.
4. 프롬프트에 특정 작품·작가 이름을 쓰지 않는다. **타인의 캐릭터 이미지를 참조 이미지로 올리지 않는다.** 오리지널 외형으로 만들고, 번호표·로고·특정 소품은 넣지 않는다. 닮아 보이면 머리 모양과 옷, 얼굴 특징을 바꿔 다시 만든다.
5. 캐릭터 색감은 어두운 남색, 슬레이트 회색, 푸른 청록 포인트로 통일한다.
6. 한 장씩 결과를 내게 보여 주고, 내가 승인하면 다음 장으로 넘어간다.

[끝낼 때]
- docs\image_prompts.md 의 "생성 기록" 표에 날짜, 대상, 사용한 도구(모델명)를 추가한다.
- docs\ASSETS.md 표에 AI 생성 이미지 7장의 출처(도구명, 생성일, 사용 위치)를 추가한다.
- docs\PROGRESS.md 의 "작업 로그"에 "[Gemini] 캐릭터 이미지 N장 제작 / assets\concept\..." 한 줄을 추가하고, 완료한 항목을 체크한다.
- 다른 파일(기획서.md, PPT, tools 폴더)은 수정하지 않는다.
```

---

## 2. Codex: PPT 다듬기와 이미지 반영

이미지가 모두 없어도 시작할 수 있다. 이미지가 일부만 있으면 있는 것만 넣고 나머지는 자리를 비워 두게 한다.

```text
먼저 C:\code\2-2\2DGP-project\AGENTS.md, docs\PROGRESS.md, docs\DECISIONS.md, docs\기획서.md, docs\script_1st.md 를 읽어라. 확정된 결정(DECISIONS.md)을 뒤집지 마라.

[목표]
1차 발표 PPT 2종을 다듬고 캐릭터 이미지를 반영한다.
- docs\presentation_1st.pptx : 발표용, 반드시 10페이지 이내, 영상 1분 30초용
- docs\plan_deck.pptx : 기획서용, 분량 제한 없음 (현재 19장)
두 파일은 tools\make_presentation_1st.py, tools\make_plan_deck.py (python-pptx)로 생성된다. 수정은 이 스크립트에서 하고 스크립트를 실행해 pptx를 다시 만든다. pptx를 직접 편집하지 마라. (스크립트와 결과가 어긋나기 때문이다.)

[평가 기준 (모두 만족해야 함)]
기획 명확성 30%, 핵심 게임플레이 설계 30%, 재미 요소·차별성 25%, 개발 계획의 현실성 10%, 발표 전달력 5%.
발표 권장 구성: 게임 소개 → 게임 기획 → 핵심 재미 요소 → 개발 계획. 이 순서를 유지한다.
과목 공지: 기존 에셋을 쓰면 그래픽 오리지널리티가 낮아지므로 기획(규칙·시스템)의 차별화가 확실히 드러나야 한다.

[해야 할 일]
1. assets\concept\ 에 있는 이미지를 PPT에 넣는다. 파일명: n09.png, boss_ark.png, enemy_slum.png, enemy_thrower.png, enemy_hound.png, enemy_guard.png, boss_crasher.png
   - 발표 PPT: 표지(주인공), 3번 세계관(주인공), 8번 콘텐츠 규모(적 4종과 보스 2종)에 배치한다. 10페이지를 넘기지 마라.
   - 기획서 PPT: 5번(주인공), 10번(적·보스)에 배치한다. 슬라이드 번호가 바뀌면 2번과 19번의 슬라이드 범위도 같이 고친다.
   - 이미지는 가로세로 비율을 유지하고, 단색 배경이면 배경을 제거해 PPT 배경과 어울리게 한다.
2. 디자인을 다듬는다. 글자가 넘치거나 겹치는 곳, 정렬이 어긋난 곳, 글자 크기가 너무 작은 곳(발표 PPT는 본문 14pt 이상)을 고친다. 전체 색상과 폰트(맑은 고딕) 체계는 유지한다.
3. 발표 PPT는 전달력을 높인다. 슬라이드당 핵심 메시지를 하나로 줄이고, 글을 도형과 숫자 중심으로 바꾼다. 게이지 구간 그림(6번)은 유지한다.
4. 내용은 docs\기획서.md 와 일치해야 한다. 어긋난 수치나 용어가 있으면 PPT가 아니라 기획서.md 기준으로 맞추되, 기획서.md가 틀렸다고 판단되면 고치지 말고 내게 보고한다.
5. 발표 PPT 각 슬라이드의 발표자 노트에 들어 있는 대본(tools\make_presentation_1st.py 의 SCRIPT)이 슬라이드 내용과 맞는지 확인한다. 대본 전체는 한국어로 천천히 읽어 90초에 맞게 450~500자 수준으로 줄인다. 길이를 확인한 방법(글자 수, 추정 시간)을 보고한다.
6. 검증한다. 스크립트 실행 후 tools\export_slides.ps1 로 슬라이드를 PNG로 내보내(예: powershell -File tools\export_slides.ps1 -Pptx docs\presentation_1st.pptx -OutDir build\slides_presentation) 모든 슬라이드를 눈으로 확인한다. 확인하지 못한 슬라이드가 있으면 그렇다고 보고한다.

[금지]
- 기획서.md, DECISIONS.md의 확정 내용을 임의로 바꾸지 마라.
- 순수 창작으로 소개한다.
- 이미지가 없는 상태에서 임의의 이미지를 만들어 넣지 마라.

[끝낼 때]
- docs\PROGRESS.md 의 "작업 로그"에 "[Codex] PPT 다듬기와 이미지 반영 / 바꾼 파일" 한 줄을 추가하고 "다음 할 일"을 갱신한다.
- 최종 보고에 바꾼 점, 확인한 슬라이드 목록, 확인하지 못한 것, 남은 문제를 적는다.
```

---

## 3. 영상 녹화 전 최종 점검 (Claude 또는 Codex)

```text
AGENTS.md, docs\PROGRESS.md 를 읽고, 영상을 녹화하기 전 최종 점검을 해라.
1. docs\presentation_1st.pptx 가 10페이지 이내인지, 슬라이드마다 이미지가 의도대로 들어갔는지 확인한다.
2. docs\script_1st.md 의 대본이 슬라이드 순서와 맞는지 확인하고, 글자 수로 추정한 낭독 시간을 보고한다.
3. docs\기획서.md 와 두 PPT의 수치·용어가 일치하는지 확인한다. (게이지 수치, 무기 4종, E 무기 강화, 업그레이드 6종, 스테이지 3개)
4. 타인의 작품 이름이 남아 있지 않은지 검색한다.
5. docs\ASSETS.md 에 사용한 이미지의 출처가 적혀 있는지 확인한다.
결과를 목록으로 보고하고, 고친 것과 고치지 않은 것을 구분한다.
```

---

## 4. Codex: 생성된 이미지 정리 + PPT 반영 + 다듬기 (통합 명령, 현재 사용)

원본 이미지는 `assets\concept\source\` 에 있다. (protagonist_illust.webp, protagonist_pixel_draft.png, enemy_sheet.webp, 모두 765×1024, 우리 Gemini 생성물)

```text
먼저 C:\code\2-2\2DGP-project\AGENTS.md, docs\PROGRESS.md, docs\DECISIONS.md, docs\기획서.md, docs\image_prompts.md, docs\script_1st.md 를 읽어라. DECISIONS.md의 확정 사항을 뒤집지 마라. 작업 시작 전에 PROGRESS.md의 "진행 중"에 "[Codex] 이미지 정리와 PPT 반영"을 적어라.

[1단계: 이미지 정리]  (Python, Pillow 사용)
원본: assets\concept\source\ 안의 세 파일. 결과 저장: assets\concept\
1. protagonist_illust.webp → n09.png (주인공). 오른쪽 아래 ✦ 모양 워터마크가 보이지 않게, 이미지 가장자리를 잘라내거나 단색 배경으로 덮어라. 배경은 PPT 배경(진한 남색 #0F1623)과 어울리게 처리한다.
2. enemy_sheet.webp 는 한 장에 캐릭터 6개가 들어 있다. 6개로 잘라 저장한다. (위치는 직접 눈으로 보고 정한다)
   - 왼쪽 위(코트 입은 감시관) → boss_ark.png
   - 가운데 위(낡은 옷, 쇠파이프 든 마른 죄수) → enemy_slum.png
   - 오른쪽 위(방패 든 죄수) → enemy_thrower.png
   - 가운데(검은 안개 사냥개) → enemy_hound.png
   - 왼쪽 아래(방패와 헬멧의 중장갑 경비) → enemy_guard.png
   - 오른쪽 아래(기계 팔의 거구) → boss_crasher.png
   각 조각의 여백을 정리하고 ✦ 워터마크가 들어간 조각은 같은 방식으로 지운다. boss_crasher의 가슴에 작은 글자가 있으면 보고한다(지울 수 있으면 지운다).
3. protagonist_pixel_draft.png 는 얼굴에 주근깨와 짙은 눈 밑 그늘이 있어 사용하지 않는다. 폴더에 두기만 하고 PPT에 넣지 마라.
4. 저장한 파일을 직접 열어 확인하고, 잘린 부분이나 남은 워터마크가 있으면 보고한다.

[2단계: PPT 반영]
PPT는 tools\make_presentation_1st.py (발표용, 10페이지 이내 엄수)와 tools\make_plan_deck.py (기획서용, 분량 제한 없음)에서 생성된다. pptx를 직접 편집하지 말고 스크립트를 수정해 실행한다. (python tools\make_presentation_1st.py, python tools\make_plan_deck.py)
- 발표 PPT: 표지에 n09.png(주인공), 3번 세계관에 n09.png, 8번 콘텐츠 규모에 적 4종과 보스 2종(작게 한 줄로)을 배치한다. 슬라이드를 늘리지 마라.
- 기획서 PPT: 5번에 n09.png, 10번에 적 4종과 보스 2종 이미지를 카드에 넣는다. 번호가 바뀌면 2번과 19번의 슬라이드 범위를 맞춘다.
- 이미지는 가로세로 비율을 유지하고, 글자와 겹치지 않게 한다.

[3단계: 다듬기]
- 평가 기준: 기획 명확성 30%, 핵심 게임플레이 30%, 재미·차별성 25%, 개발 계획 현실성 10%, 전달력 5%. 권장 구성 순서(소개 → 기획 → 핵심 재미 → 개발 계획)를 유지한다.
- 글자 넘침, 겹침, 정렬 어긋남을 고친다. 발표 PPT 본문은 14pt 이상으로 한다. 폰트(맑은 고딕)와 색 체계는 유지한다.
- 발표 PPT는 슬라이드당 핵심 메시지를 하나로 줄이고 도형·숫자 중심으로 정리한다. 게이지 구간 그림(6번)은 유지한다.
- 대본(tools\make_presentation_1st.py 의 SCRIPT)을 슬라이드와 맞추고, 90초 낭독 기준 450~500자 수준으로 다듬는다. 글자 수와 추정 시간 계산 방법을 보고한다. 수정 후 docs\script_1st.md 도 갱신한다.
- 내용은 docs\기획서.md 와 일치시킨다. 기획서.md가 틀렸다고 보이면 고치지 말고 보고한다.

[검증]
tools\export_slides.ps1 로 두 PPT를 PNG로 내보내(예: powershell -File tools\export_slides.ps1 -Pptx docs\presentation_1st.pptx -OutDir build\slides_presentation) 모든 슬라이드를 눈으로 확인한다. 확인하지 못한 슬라이드는 그렇다고 보고한다.

[금지]
- 순수 창작으로 소개한다.
- 다른 작품의 캐릭터 이미지를 프로젝트에 넣지 마라. (assets 폴더에는 우리가 만든 이미지만 둔다)
- 이미지를 임의로 새로 만들어 넣지 마라.
- 기획서.md, DECISIONS.md의 확정 내용을 바꾸지 마라.

[끝낼 때]
- docs\ASSETS.md 에 이미지 7종의 출처(도구: Gemini 이미지 생성, 생성일 2026-10-31, 사용 위치)를 표로 추가한다. 정확한 모델명을 모르면 "Gemini (모델명 확인 필요)"로 적는다.
- docs\PROGRESS.md 의 "진행 중"을 비우고 "작업 로그"에 "[Codex] 이미지 정리, PPT 반영과 다듬기 / 바꾼 파일" 한 줄을 추가한다.
- 최종 보고: 바꾼 점, 확인한 슬라이드 목록, 확인하지 못한 것, 남은 문제.
```

---

## 5. Codex: PPT 가독성 개선 (영상 녹화용)

```text
먼저 C:\code\2-2\2DGP-project\AGENTS.md, docs\PROGRESS.md, docs\DECISIONS.md 를 읽어라. 작업 시작 전에 PROGRESS.md의 "진행 중"에 "[Codex] PPT 가독성 개선 / tools\make_presentation_1st.py, tools\make_plan_deck.py"를 적어라. 다른 도구가 같은 파일을 수정 중이면 멈추고 보고해라.

[목표]
발표 PPT(docs\presentation_1st.pptx, 10장 이내)와 기획서 PPT(docs\plan_deck.pptx)를 읽기 쉽게 만든다. 발표 PPT는 1분 30초 영상으로 녹화되어 YouTube 화면(1080p, 일부는 모바일)에서 보이므로 한눈에 읽혀야 한다. 내용의 의미와 수치는 바꾸지 말고, 표현과 배치만 바꾼다. 줄여야 하는 문장은 핵심만 남기고, 줄인 내용을 보고한다.

[수정 방법]
tools\make_presentation_1st.py, tools\make_plan_deck.py 를 수정해 실행한다. pptx를 직접 편집하지 마라. 실행: python tools\make_presentation_1st.py, python tools\make_plan_deck.py

[발표 PPT 기준 (엄격)]
1. 글자 크기: 제목 32pt 이상, 본문과 카드 설명 20pt 이상, 보조 설명과 하단 문구는 16pt 이상. 14pt 이하 글자를 쓰지 마라. 글자가 안 들어가면 글을 줄이거나 카드를 늘려라.
2. 분량: 슬라이드당 핵심 메시지 하나. 글줄은 최대 6줄, 한 줄은 최대 25자 안팎. 문장 대신 키워드와 숫자로 바꾼다. (예: "페이드 0~19%: 이동 -20%, 공격력 ×0.8" → 구간 이름, 범위, 핵심 수치만)
3. 위계: 제목 > 핵심 숫자·키워드(크고 굵게, 강조색) > 설명(작게, 보조색). 한 슬라이드에서 강조색은 최대 2가지.
4. 대비: 배경(#0F1623) 위의 본문은 밝은 색(#E8EEF7 이상). 어두운 회색 글자를 쓰지 마라. 이미지 위에 글자를 얹지 마라.
5. 여백: 가장자리 여백 0.6인치 이상, 카드와 카드 사이 간격 0.2인치 이상, 요소를 격자에 맞춰 정렬한다. 한 슬라이드의 빈 공간이 한쪽에 몰리지 않게 한다.
6. 표와 목록: 표는 5행 이하, 열은 3개 이하. 불릿은 4개 이하. 길면 두 장으로 나누지 말고 핵심만 남겨라. (발표 PPT는 10장을 넘기지 마라)
7. 이미지: 캐릭터 이미지는 크게(슬라이드 높이의 50% 이상), 잘리거나 겹치지 않게 한다.
8. 글자 줄바꿈: 단어 중간에서 끊기지 않게 한다. (한국어 어절 단위로 줄바꿈)
9. 슬라이드 하단의 쪽번호와 푸터는 12pt 이하로 작게 두어도 된다.

[기획서 PPT 기준]
본문 14pt 이상, 표 14pt 이상. 위 3~8번(위계, 대비, 여백, 표 크기, 이미지, 줄바꿈)을 적용한다. 분량은 발표 PPT보다 많아도 되지만 글자가 빽빽하면 슬라이드를 나눠도 된다. 슬라이드 수가 바뀌면 2번(구성)과 19번(평가 기준 대응)의 슬라이드 번호 범위를 맞춘다.

[유지할 것]
- 폰트(맑은 고딕), 전체 색 체계, 권장 구성 순서(소개 → 기획 → 핵심 재미 → 개발 계획)
- 게이지 구간 그림(발표 6번), 이미지 파일명과 배치 방향
- 발표자 노트의 대본은 슬라이드 내용과 맞게 유지한다. 대본을 고쳤다면 docs\script_1st.md 도 갱신하고, 글자 수(공백 포함)와 90초 낭독 가능 여부를 보고한다.

[금지]
- 순수 창작으로 소개한다.
- docs\기획서.md, DECISIONS.md 의 확정 내용을 바꾸지 마라. 틀린 내용을 발견하면 고치지 말고 보고한다.
- 이미지를 새로 만들거나 바꾸지 마라.

[검증 (필수)]
1. python으로 두 PPT를 다시 만들고, powershell -File tools\export_slides.ps1 -Pptx docs\presentation_1st.pptx -OutDir build\slides_presentation, 같은 방식으로 기획서 PPT도 PNG로 내보낸다.
2. 모든 슬라이드를 눈으로 확인한다. 한 장도 건너뛰지 마라.
3. 발표 PPT는 슬라이드마다 위 기준 1~8번을 체크한 표를 만들어 보고한다. (슬라이드 번호 / 가장 작은 글자 크기 / 글줄 수 / 위반 항목 / 조치)
4. 확인하지 못한 슬라이드가 있으면 그렇다고 보고한다.
5. 스크립트 코드에서 글자 크기를 검사해 14pt 이하 글자가 남았는지 목록을 출력한다. (발표 PPT는 푸터 제외)

[끝낼 때]
- build\ 폴더는 삭제한다.
- PROGRESS.md의 "진행 중"을 비우고 "작업 로그"에 "[Codex] PPT 가독성 개선 / 바꾼 파일" 한 줄을 추가한다.
- 최종 보고: 슬라이드별 바뀐 점, 줄인 문장 목록, 확인한 슬라이드, 확인하지 못한 것, 남은 문제.
```


## Codex에서 agent-sprite-forge로 스프라이트 만들기 (2026-11-07, 미검증)
설치됨: `~/.codex/skills`의 codeart2d, generate2dmap, generate2dmedia, generate2dsprite, video2dsprite. 이 PC에는 영상 경로와 ffmpeg가 없어 character 애니메이션을 영상에서 뽑는 `video2dsprite`는 쓰지 않는다.
1. Codex에서 `$generate2dsprite`로 마스터 스틸컷 한 장을 만든다. 기준 이미지는 `assets/sprites/unified/n09_idle.png`, 옆모습·오른쪽을 봄, 흰 머리, 같은 도트 굵기, `--finish hibit`(플랫 원화 → 후처리로 픽셀화, 이진 알파, 1px 외곽선).
2. 동작(걷기, 달리기, 점프, 공격, 피격)은 Codex 이미지 생성으로 동작별 프레임 격자(예: 2×2, 3×3)를 만들어 PNG 프레임으로 `generate2dsprite`에 넘겨 정렬·팔레트·마무리를 한다.
3. 결과는 `assets/sprites/detailed/`에 두고 `docs/sprite_spec.md`(80px, 공통 팔레트 약 60색, 외곽선 1px)와 `python tests/test_pixel_assets.py`로 확인한다.
4. 사용한 프롬프트와 모델은 `docs/image_prompts.md`에 기록한다. 규칙은 `docs/pixel_rules.md`.


## Codex 프롬프트: 마스터 스틸컷 재생성 (hibit, 눈·비율 개선) (2026-11-07)
주인공 (눈 보존). 기존 시험 결과(`assets/sprites/forge/master/`)는 지우지 말고 `assets/sprites/forge/hero_v2/`에 새로 만들 것.
```text
AGENTS.md, docs/sprite_spec.md, docs/pixel_rules.md를 읽고 규칙을 따라줘. PROGRESS.md "진행 중"에 "[Codex] 주인공 마스터 v2"를 적고 시작해.
Use $generate2dsprite to make ONE master still of the player (--finish hibit), and stop for approval. No animation, no video.
기준: assets/sprites/unified/n09_idle.png (같은 인물·의상), 직전 시험 결과 assets/sprites/forge/master/master_rgba.png (이 화풍은 좋음, 아래만 고친다).
고칠 점:
1) 얼굴: 옆모습이지만 눈을 크고 굵고 어둡게(진한 청록~검정, 최소 키의 3%), 눈썹 선, 코와 입이 선명히. 작은 요소는 8배 축소에서 사라지니 과장해서 그려줘.
2) 비율: 머리를 키의 약 1/6로 약간 크게, 어깨와 몸통을 넓게 해서 옆에서 봐도 몸 너비가 키의 35% 이상.
3) 기준의 낡은 느낌(해진 소매·바짓단)을 큰 덩어리로 살린다. 잔 디테일 금지.
4) 납작하고 선 없는 색면, 마젠타 배경, 오른쪽 옆모습, 두 팔 보이게 자연스럽게 벌림, 두 발 지면, 무기 없음.
저장: assets/sprites/forge/hero_v2/. 끝나면 python tools/finish_character.py assets/sprites/forge/hero_v2/<master_rgba 경로> n09_v2 를 실행하고, 기존 unified/n09_idle.png와 1배로 나란히 놓은 비교 이미지를 hero_v2/compare_1x.png로 저장한 뒤 눈이 보이는지 솔직하게 알려줘. docs/image_prompts.md에 프롬프트·날짜 기록, 끝나면 PROGRESS "진행 중"을 비워.
```
나머지 6종은 위 형식에서 1)~3)을 캐릭터에 맞게 바꾸고 기준 이미지를 각 `unified/<이름>_idle.png`로 한다. 키는 `docs/sprite_spec.md` 표의 값.
