"""2차 발표용 PPT(2장)와 영상 대본(docs/script_2nd.md)을 만든다.

가이드(2026_2DGP_2차발표가이드): 1분 30초 영상 = 진행 상황 발표 + 게임 데모. PPT는 게임 설명 1장,
개발 계획 대비 진행 상황 1장(기획 변경 내용 포함). 데모 화면은 assets/presentation_examples/demo_*.png (실제 게임 캡처).

사용: python tools/make_presentation_2nd.py
결과: docs/presentation_2nd.pptx, docs/script_2nd.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (ACCENT, GREEN, MUTED, ROOT, WARN, blocks, caption_box, new_deck, new_slide,  # noqa: E402
                     picture_slot, table)

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "presentation_2nd.pptx"
SCRIPT_OUT = ROOT / "docs" / "script_2nd.md"
EX = ROOT / "assets" / "presentation_examples"
FOOTER = "Haze | 2D 게임 프로그래밍 2차 발표 | 김동형"
TOTAL = 2

NARRATION_SLIDES = [
    "헤이즈는 게이지가 0퍼센트면 죽고 100퍼센트면 폭발하는 횡스크롤 액션 로그라이크입니다. "
    "마우스로 조준해 방의 적을 모두 처치하면 문이 열립니다.",
    "계획했던 이동과 게이지, 마우스 조준 공격, 적 두 종을 모두 구현했고, 방 잠금과 이동, 미니맵, E 강화는 일정을 앞당겼습니다. "
    "변경은 화면을 1920 곱하기 1080으로 키운 것뿐입니다. 남은 것은 무기, 적, 보스, 업그레이드입니다. 그럼 데모를 보겠습니다.",
]
NARRATION_DEMO = [
    "첫 방입니다. 적이 있어서 문이 잠겨 있습니다. 마우스로 겨누고 좌클릭으로 파이프를 휘두르면, 맞힐 때마다 게이지가 오릅니다.",
    "대시를 하면 잔상이 남고 무적입니다. 적을 모두 처치하면 문이 열리고 다음 방으로 갑니다.",
    "마지막 방은 헤이즈가 짙어 게이지가 계속 차오릅니다. 게이지가 높을 때 E를 누르면 게이지를 쓰고 무기가 강해지며, 처치한 적은 폭발합니다.",
    "이번 주 목표는 여기까지입니다. 감사합니다.",
]

prs = new_deck()

# ----- 1장: 게임 설명 -----
s = new_slide(prs, "헤이즈 (Haze): 게이지를 지키며 싸우는 액션 로그라이크", FOOTER, 1, TOTAL, NARRATION_SLIDES[0], title_size=27)
blocks(s, [
    ("장르", "마우스 조준 횡스크롤 액션 로그라이크. 사망하면 처음부터 다시 시작합니다."),
    ("핵심 재미: 헤이즈 게이지", "0%면 사망, 100%면 오버로드 폭발. 싸우면 오르고 시간이 지나면 줄어서, 그 사이를 유지해야 합니다."),
    ("구간별 전투력", "각성(50~89%)은 공격력 ×1.5, 위험(90~99%)은 ×1.8. E 키로 게이지를 써서 낮추고 무기를 강화합니다."),
    ("진행", "방의 적을 모두 처치하면 문이 열리고, 격자형 방을 지나 탈출구까지 돌파합니다."),
], 0.6, 1.5, 5.4, 20, 16, 0.1)
picture_slot(s, EX / "demo_enhance.png", 6.2, 1.5, 6.75, 3.8)
caption_box(s, 6.2, 5.42, 6.75, 1.5, "실제 게임 화면 (E 강화 전투)",
            ["위: 헤이즈 게이지(구간 색 띠) / 왼쪽 위: 체력·대시 슬롯·조각", "오른쪽 위: 미니맵. 붉은 문 = 잠김, 청록 빛 = 열림"], size=15)

# ----- 2장: 계획 대비 진행 상황 -----
s = new_slide(prs, "개발 계획 대비 현재 진행 상황 (11/15)", FOOTER, 2, TOTAL, NARRATION_SLIDES[1], title_size=28,
              tag="2주차 목표 완료")
W = [1.45, 3.75, 5.35, 1.55]
rows = [
    ["주차", "1차 발표 계획", "현재 상태", "진행"],
    ["1주차\n11/5~11/11", "프레임워크, 이동·2단 점프·대시, 타일 충돌, 게이지 로직",
     "완료. 상태 머신(transitions), 게이지 구간·오버로드, 대시 슬롯", ("완료", GREEN)],
    ["2주차\n11/12~11/18", "마우스 조준 공격, 일반 적 2종, 게이지 UI 연결",
     "완료. 철파이프 3연타, 슬럼·투척병 AI, 타격·처치·피격 게이지, 체력·게이지 UI", ("완료", GREEN)],
    ["3주차\n11/19~", "방 문 잠금·전환, 스테이지 격자, 재화, 무기·적 추가",
     "앞당김: 방 잠금·클리어·전환, 3개 방, 미니맵, 고농도 방, E 강화(폭발), 조각 드롭", ("일부 완료", ACCENT)],
    ["남은 일", "무기 3종, 적 2종, 보스 2종, 정비방, 스테이지 2·3",
     "걷기 애니메이션(Codex 이미지 작업 대기), 식칼·건틀릿, 사냥개·간수, 보스, 업그레이드", ("진행 예정", WARN)],
]
end = table(s, 0.6, 1.5, W, rows, size=13, row_h=0.82)
text_y = end + 0.12
caption_box(s, 0.6, text_y, 12.1, 7.0 - text_y, "기획 변경 내용 (1차 발표 이후)",
            ["① 화면을 1280×720에서 1920×1080으로 1.5배 확대 (타일 60px, 캐릭터 키 123px). 방은 같은 32×18칸",
             "② 피격 직후 0.8초 무적, 코요테 타임·점프 버퍼·화면 흔들림 추가 (조작감 보강)  ③ 고농도 방을 스테이지 1 마지막 방에 먼저 배치"],
            size=13)

prs.save(str(OUT))
print("saved", OUT.relative_to(ROOT))

# ----- 대본 -----
total = sum(len(x) for x in NARRATION_SLIDES + NARRATION_DEMO)
lines = ["# 2차 발표 영상 대본 (1분 30초)", "",
         "가이드: 프로젝트 진행 상황 발표 + 게임 데모 실행. 글자가 또렷하고 음성이 잘 들려야 한다. **녹화 뒤 반드시 직접 재생해서 들어본다.**", "",
         "## 구성과 시간 (합계 90초)", "",
         "| 시간 | 화면 | 내용 |", "|---|---|---|",
         "| 0:00~0:15 | PPT 1장 | 게임 설명 |",
         "| 0:15~0:40 | PPT 2장 | 계획 대비 진행 상황, 기획 변경 |",
         "| 0:40~1:30 | 게임 데모 | 아래 데모 순서 |", "",
         "## 슬라이드 낭독", ""]
for i, t in enumerate(NARRATION_SLIDES, 1):
    lines += [f"**{i}장.** {t}  ({len(t)}자)", ""]
lines += ["## 데모 순서와 낭독 (게임 화면 녹화, 1920×1080)", "",
          "실행: `python src/main.py` → 타이틀에서 아무 키.", ""]
steps = [
    "방 1: 가까운 슬럼에게 다가가 좌클릭으로 3연타(3타째 큰 화면 흔들림). 투척병은 없고 슬럼 2마리.",
    "Shift(또는 우클릭)로 대시해 공격을 피하며 잔상을 보여 준다. 적을 모두 처치 → '방 클리어' 문구, 문이 청록색으로 열림.",
    "오른쪽 문으로 이동 → 방 2(투척병이 던지는 고철은 점프나 대시로 피한다). 미니맵이 채워지는 것을 보여 준다.",
    "방 3(고농도 방): 게이지가 올라가 있을 때(50% 이상 권장) E를 눌러 강화 → 적을 처치해 폭발 장면. 필요하면 `F1` 후 `F3`으로 게이지를 올려 둔다.",
    "마지막 방을 클리어하고 오른쪽 탈출구로 나가 '탈출 성공' 화면까지.",
]
for i, (step, narr) in enumerate(zip(steps, NARRATION_DEMO), 1):
    lines += [f"{i}. {step}", f"   - 낭독: {narr}  ({len(narr)}자)"]
lines += ["", f"총 낭독 {total}자 (공백 포함). 분당 320자 가정 시 약 {total / 320 * 60:.0f}초 + 데모 조작 시간. "
          "길면 데모 낭독 문장을 줄이고, 짧으면 방 2 설명을 늘린다.", "",
          "## 제출 체크리스트 (발표 당일 0시 1분까지, 시간 엄수)", "",
          "- [ ] 영상 YouTube 업로드(공개 또는 일부 공개), 링크를 e-class에 제출",
          "- [ ] GitHub 저장소 링크 e-class 제출: https://github.com/donghyeong-1/2DGP-HAZE",
          "- [ ] 발표자료는 저장소에 있음: `docs/presentation_2nd.pptx`, 대본 `docs/script_2nd.md`",
          "- [ ] 영상을 직접 재생해 글자 가독성과 음성을 확인"]
SCRIPT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("saved", SCRIPT_OUT.relative_to(ROOT), f"({total}자)")
