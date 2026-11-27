"""'mist' 스킨의 고르는 화면 부품 (2026-11-27 S1, docs/opus/TASKS.md '4차'). 은신처 NPC 창 넷(정비사·보관인·기록관·무기 걸이)이 쓴다.

증강 카드(A 안개 미니멀, mutation_mode._card_back)와 같은 말투:
- 판 = 가는 테두리 한 줄(화면 2px) + 거의 불투명한 어두운 바탕 (H1 hud_kit.hud_panel과 같은 부품 um_hud_frame_*).
  테두리 색: 기본 회백(line), 헤이즈 관련만 청록, 합성·특별 보상은 금, 저주·위험은 빨강. 경고 노랑은 쓰지 않는다.
- NPC 창은 세로 목록이라 가로 카드로 바꾸지 않고, 목록 전체를 판 하나에 담는다(줄마다 판을 두면 고른 줄 테두리가 긴 띠처럼 보인다).
  줄 고르기는 M1과 같은 방식: 고른 줄 이름만 글자 폭으로 색을 뒤집고 앞에 커서. 색은 감시 단말의 인광색이 아니라 카드의 밝은 회백.
  살 수 없는 줄(결정 모자람·다 올림·같은 무기)은 흐린 글자, 고르면 흐린 회색으로 뒤집혀 고를 수 있는 줄과 한눈에 갈린다.
- 줄 사이는 아주 옅은 가는 선(화면 2px)으로만 나눈다. 리벳·두꺼운 틀·경고 줄무늬·노란 꺾쇠·긴 띠 없음.
- 키 안내는 증강 선택 화면처럼 키 판 없이 글자만.
"""
import assets
import config
import hud_kit as kit

W, H = config.SCREEN_W, config.SCREEN_H
BACKDROP, BACKDROP_ALPHA = (6, 9, 18), 0.92     # 멈춘 은신처 위 어둠 (증강 화면 0.78보다 진하게: 뒤 NPC 이름표·HUD가 글자와 겹치지 않게)
TITLE = (244, 236, 214)                         # 화면 제목 (증강 선택 제목과 같은 색)
TEXT = (236, 240, 248)                          # 밝은 글자 (카드 이름)
BODY = (205, 215, 235)                          # 본문 (카드 설명)
SOFT = (176, 188, 210)                          # 작은 설명 (증강 카드 아래 안내 글 MIST_NOTE)
FAINT = (150, 165, 190)                         # 부제·키 안내 (증강 선택 화면의 부제와 같은 색)
OFF = (100, 110, 128)                           # 살 수 없는 줄의 글자 (읽힐 만큼만 흐리게)
HAZE = (130, 235, 225)                          # 헤이즈 결정 수·결정 값 (청록은 헤이즈에만)
FAIL = (240, 140, 140)                          # 실패 알림 (결정 모자람·같은 무기)
HOT_BG = (222, 228, 236)                        # 고른 줄 뒤집힘 (고른 카드 테두리 um_hud_frame_hot과 같은 색)
HOT_OFF = (112, 120, 138)                       # 고른 줄이 살 수 없는 것일 때
HOT_FG = (9, 12, 21)                            # 뒤집힌 글자 (카드 바탕 색)
SEP = (30, 36, 50)                              # 줄 사이 가는 선 (바탕보다 조금 밝게만)
PAD, PAD_Y = 20, 14                             # 판 테두리와 줄 사이 (옆, 위아래)


def backdrop():
    assets.draw_rect_color(0, 0, W, H, BACKDROP, BACKDROP_ALPHA)


def panel(x, y, w, h, tone='line'):
    """가는 테두리 한 줄 + 어두운 바탕 (왼쪽 아래 x, y). tone: line / dim / hot / cyan / gold / red."""
    kit.hud_panel('panel', int(x) // 2 * 2, int(y) // 2 * 2, int(w) // 2 * 2, int(h) // 2 * 2, tone)


def sep(x, y, w):
    """줄 사이 아주 옅은 가는 선 (화면 2px)."""
    assets.draw_rect_color(int(x) // 2 * 2, int(y) // 2 * 2, int(w) // 2 * 2, 2, SEP)


def vsep(x, y, h):
    """세로 가는 선 (두 열 사이)."""
    assets.draw_rect_color(int(x) // 2 * 2, int(y) // 2 * 2, 2, int(h) // 2 * 2, SEP)


def pick(x, cy, label, hot, color=SOFT, small=False, center=False, ok=True, mark=True):
    """줄 이름. 고른 줄은 글자 폭 + 양옆 8px만 색을 뒤집고(ok가 아니면 흐린 회색) 앞에 삼각 커서.
    center면 x가 글자 가운데, 아니면 글자 왼쪽 끝. 고르지 않은 줄은 그림자 있는 글자(color)."""
    tw = assets.text_width(label, small)
    left = x - tw // 2 if center else x
    hh = 14 if small else 18
    if not hot:
        kit.text(x, cy, label, color, small=small, center=center)
        return
    assets.draw_rect_color(int(left) - 8, int(cy) - hh, tw + 16, 2 * hh, HOT_BG if ok else HOT_OFF)
    assets.draw_text(x, cy, label, HOT_FG, small=small, center=center)
    if mark:
        cur = assets.image('ui/um_pick_cursor.png' if ok else 'ui/um_pick_cursor_off.png')
        assets.draw_image(cur, int(left) - 30 + cur.w // 2, int(cy) - cur.h // 2)


def keys(pairs, y=49):
    """화면 아래 가운데 키 안내: 키 판 없이 글자만 (증강 선택 화면과 같은 모양). pairs = [(키, 설명)]."""
    kit.text(W // 2, y, '        '.join(f'{k}  {d}' for k, d in pairs), FAINT, center=True, small=True)


def underline(cx, y, label, color=TEXT, small=False):
    """지금 고른 값 아래 가는 밑줄 (글자 폭 + 양옆 4px, 2px)."""
    tw = assets.text_width(label, small)
    assets.draw_rect_color(int(cx) - tw // 2 - 4, int(y), tw + 8, 2, color)
