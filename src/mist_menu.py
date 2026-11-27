"""'mist' 스킨의 감시 단말 부품 (2026-11-27). 타이틀(B 감시 단말, 확정)과 메뉴 화면(일시정지·설정·키 설정·결과·크레딧, M1)이 같이 쓴다.

타이틀이 _draw_terminal 안에서 직접 그리던 것을 꺼냈다: 주사선, 네 귀퉁이 꺾쇠, 왼쪽 위 감시 머리글, 고른 항목의 색 뒤집힘 + 커서.
타이틀은 이 정리 뒤에도 픽셀 단위로 같다(tests/test_ui_skin.py가 그리기 호출 기록으로 확인).
메뉴 화면 몫으로 더한 것:
- shade(): 글자 뒤 어둠. 타이틀처럼 글자 상자에서 멀어질수록 옅어지는 부드러운 알파(빛 층 예외)를 조각 시트
  assets/light/menu_shade_<soft|wide>.png(tools/make_ui_mist.py --menu)로 9칸 이어 붙여 어떤 크기 상자에도 깐다.
  타이틀은 글자 자리가 고정이라 한 장으로 구운 시트(light/title_shade)를 그대로 쓴다.
- dim(): 뒤에 비치는 화면(멈춘 게임·타이틀 배경)을 전체적으로 어둡게.
- keycap()·footer(): 키 글자 판은 H1 HUD의 가는 테두리 한 줄 + 어두운 바탕 (um_hud_frame_ph*). 철판 키캡·노란 꺾쇠 없음.
- bar(): 음량 막대 = H1 가는 테두리 막대(hud_bar)에 인광색 속(um_fill_phos_*).
판·띠·리벳·경고 줄무늬·노란 꺾쇠를 쓰지 않는다 (11/26 사용자: "공사장 느낌 너무 나는데").
"""
import assets
import config
import hud_kit as kit

W, H = config.SCREEN_W, config.SCREEN_H
# 인광 글자색 (타이틀과 같은 값. title_mode.PH 등은 여기서 가져간다)
PH = (168, 240, 200)                       # 인광 글자: 제목·고른 값·중요한 값
PH_DIM = (60, 110, 100)                    # 타이틀 머리글 둘째 줄·판번호
PH_MENU = (112, 170, 150)                  # 고르지 않은 메뉴 (어둠 위에서 읽히게 PH_DIM보다 밝게)
PH_BG = (10, 16, 20)                       # 고른 항목의 뒤집힌 글자
# 메뉴 화면에 더한 두 단계 (글이 많은 화면: 본문과 작은 설명)
PH_TEXT = (196, 232, 216)                  # 본문 (긴 글을 오래 읽어도 눈이 덜 아프게 인광색을 조금 빼서)
PH_SOFT = (132, 186, 166)                  # 고르지 않은 줄 이름·작은 설명 (PH_MENU보다 조금 밝게: 작은 글자도 읽히게)
PH_DIM_TEXT = (96, 146, 132)   # U1-2: (84, 128, 116)은 어두운 바탕 위 4.3:1 -> 5.4:1 (작은 글자 4.5:1 기준)               # 고르지 않은 줄의 고르지 않은 값 (가장 흐린 글자. 어둠 위에서 읽히는 만큼만)
TERM_HEAD = (110, H - 60)                  # 머리글 첫 줄 (왼쪽, 글자 가운데 y)
BRACKET_MARGIN = 24                        # 화면 네 귀퉁이 꺾쇠
SCAN_STEP, SCAN_ALPHA = 4, 0.16            # 주사선: 4px마다 2px 어두운 줄
SHADE_COLOR = (4, 6, 12)                   # 글자 뒤 어둠 색 (tools/make_ui_mist.SHADE_COLOR)
SHADE_MID = 64                             # 조각 시트 가운데 한 변 (절반 크기 px, tools/make_ui_mist.SHADE_MID)


def scanlines():
    for y in range(0, H, SCAN_STEP):
        assets.draw_rect_color(0, y, W, 2, (0, 0, 0), SCAN_ALPHA)


def brackets():
    """화면 네 귀퉁이 꺾쇠 (um_bracket)."""
    b = assets.image('ui/um_bracket.png')
    m = BRACKET_MARGIN
    for x, y, flip in ((m, H - m - b.h, ''), (W - m - b.w, H - m - b.h, 'h'), (m, m, 'v'), (W - m - b.w, m, 'hv')):
        assets.draw_image(b, x + b.w // 2, y, flip)


def header(lines):
    """왼쪽 위 감시 머리글: [(글, 색)] 한두 줄 (작은 글자, 줄 사이 26px)."""
    hx, hy = TERM_HEAD
    for i, (s, color) in enumerate(lines):
        kit.text(hx, hy - 26 * i, s, color, small=True)


def pick(x, cy, label, hot, color=PH_MENU, center=True, small=False, mark=True, span=None):
    """메뉴 항목. 고른 항목은 글자 폭 + 양옆 8px만 색을 뒤집고 앞에 커서(um_cursor). 길게 뻗는 띠 아님.
    center면 x가 글자 가운데, 아니면 글자 왼쪽 끝. 돌려주는 값은 (뒤집힌 블록의 왼쪽 x, 폭) — 고르지 않았으면 글자 자리.
    span: 뒤집힌 블록이 cy에서 (아래로, 위로) 뻗는 길이. 기본은 위아래 같게 큰 글자 18·작은 글자 14.
    설정 화면(11/27 S1-fix)은 (14, 18): 설명을 이름에 붙이려고 아래만 줄인다. 갈무리 28px 글자는 실제 픽셀이 cy-12 ~ cy+15라
    위아래를 같게 14로 줄이면 윗줄이 잘린다(S1에서 그랬다). 아래 14·위 18이면 글자 위아래로 2·3px 여유."""
    tw = assets.text_width(label, small)
    left = x - tw // 2 if center else x
    hh = 14 if small else 18
    below, above = span or (hh, hh)
    if hot:
        assets.draw_rect_color(left - 8, cy - below, tw + 16, below + above, PH)
        if small:
            assets.draw_text(x, cy, label, PH_BG, small=True, center=center)
        else:
            assets.draw_text(x, cy, label, PH_BG, center=center)
        if mark:                                          # 커서 (다른 자리에 커서를 둔 화면은 뺀다)
            assets.draw_image(assets.image('ui/um_cursor.png'), left - 34, cy - 21)
    else:
        kit.text(x, cy, label, color, small=small, center=center)
    return left - 8, tw + 16


def cursor(left, cy):
    """고른 줄 앞 커서 (um_cursor): left는 글자 왼쪽 끝, cy는 글자 가운데 (pick과 같은 자리)."""
    assets.draw_image(assets.image('ui/um_cursor.png'), left - 34, cy - 21)


# ----- 메뉴 화면 (M1) -----
DIM_TITLE, DIM_GAME = 0.62, 0.84   # 뒤 화면을 덮는 어둠: 타이틀 배경(원래 어둡다) / 멈춘 게임(HUD·밝은 벽이 글자와 겹치지 않게)


def dim(alpha):
    """뒤에 비치는 화면을 전체적으로 어둡게 (한 색 한 장)."""
    assets.draw_rect_color(0, 0, W, H, SHADE_COLOR, alpha)


def scene_dim(under):
    """설정·키 설정 창이 깔 화면에 맞는 어둠: 맨 아래가 멈춘 게임이면 DIM_GAME, 타이틀이면 DIM_TITLE."""
    seen = 0
    while under is not None and seen < 4:
        name = getattr(under, '__name__', '')
        if name.endswith('pause_mode') or name.endswith('play_mode'):
            return DIM_GAME
        if name.endswith('title_mode'):
            return DIM_TITLE
        under = getattr(under, '_under', None)
        seen += 1
    return DIM_TITLE


def shade(x0, y0, x1, y1, kind='soft'):
    """글자 상자 (x0, y0)~(x1, y1) 뒤의 어둠: 상자 안은 가장 진하고 밖으로 멀어질수록 옅어진다 (빛 층 시트 9칸, 화면 2배).
    가운데는 시트의 한 색과 같은 사각형 한 장, 네 변은 길이 방향으로 같은 값이라 이어 붙여도 이음매가 없다."""
    img = assets.image(f'light/menu_shade_{kind}.png')
    n, m = img.w, SHADE_MID
    r = (n - m) // 2                                         # 번지는 폭 (절반 크기 px)
    R = 2 * r
    x0, y0 = int(x0) // 2 * 2, int(y0) // 2 * 2
    x1, y1 = max(x0, (int(x1) + 1) // 2 * 2), max(y0, (int(y1) + 1) // 2 * 2)
    w, h = x1 - x0, y1 - y0
    k = kit_alpha(kind)
    if w and h:
        assets.draw_rect_color(x0, y0, w, h, SHADE_COLOR, k)
    step = 2 * m
    for along in range(0, w, step):
        seg = min(step, w - along) // 2
        assets.draw_clip(img, r, r + m, seg, r, x0 + along, y1, scale=2)          # 위
        assets.draw_clip(img, r, 0, seg, r, x0 + along, y0 - R, scale=2)         # 아래
    for along in range(0, h, step):
        seg = min(step, h - along) // 2
        assets.draw_clip(img, 0, r, r, seg, x0 - R, y0 + along, scale=2)         # 왼쪽
        assets.draw_clip(img, r + m, r, r, seg, x1, y0 + along, scale=2)         # 오른쪽
    for (l, b, x, y) in ((0, r + m, x0 - R, y1), (r + m, r + m, x1, y1), (0, 0, x0 - R, y0 - R), (r + m, 0, x1, y0 - R)):
        assets.draw_clip(img, l, b, r, r, x, y, scale=2)


SHADE_K = {'soft': 0.80, 'wide': 0.80}     # 조각 시트 가운데의 진하기 (tools/make_ui_mist.MENU_SHADES)


def kit_alpha(kind):
    return SHADE_K[kind]


def text_shade(x, cy, s, small=False, big=False, center=False, right=False, pad=10, kind='soft'):
    """글자 한 줄 뒤의 어둠 (글자 상자 + pad)."""
    tw = assets.text_width(s, small, big)
    left = x - tw // 2 if center else (x - tw if right else x)
    hh = 21 if big else (11 if small else 14)
    shade(left - pad, cy - hh - pad, left + tw + pad, cy + hh + pad, kind)


def frame(x, y, w, h, tone='ph_dim', well=True):
    """가는 테두리 한 줄(화면 2px) + 어두운 바탕 (H1 HUD 판과 같은 모양). tone: ph / ph_dim / hot / line / dim."""
    kit.hud_panel('plate', x, y, w, h, tone, alpha=kit.HUD_WELL_ALPHA if well else 0.0)


def keycap(x, y, label, hot=True, inverted=False):
    """키 글자 판 (왼쪽 아래 x, y, 높이 30): 가는 인광 테두리 + 어두운 바탕. 폭은 글자에 맞춘다(철판 키캡과 같은 폭). 돌려주는 값은 폭.
    inverted: 고른 칸 (테두리 안을 인광색으로 채우고 글자를 어둡게, 메뉴 항목의 색 뒤집힘과 같은 말투)."""
    w = max(34, assets.text_width(label, True) + 16) // 2 * 2
    x, y = int(x), int(y)
    if inverted:
        assets.draw_rect_color(x, y, w, 30, PH)
        assets.draw_text(x + w // 2, y + 16, label, PH_BG, small=True, center=True)
        return w
    frame(x, y, w, 30, 'ph' if hot else 'ph_dim')
    assets.draw_text(x + w // 2, y + 16, label, PH if hot else PH_MENU, small=True, center=True)
    return w


def footer_widths(pairs):
    return [max(34, assets.text_width(k, True) + 16) + 10 + assets.text_width(d, True) for k, d in pairs]


def footer_shade(pairs, y=34, raw=False):
    """키 안내 뒤의 어둠. 어둠은 둘레 글자까지 덮으므로 글자를 쓰기 전에 (다른 어둠과 함께) 먼저 깐다."""
    import input_device
    if not raw:
        pairs = input_device.footer(pairs)                 # N1-3: footer와 같은 목록으로 폭을 잰다
    total = sum(footer_widths(pairs)) + 44 * (len(pairs) - 1)
    x = (W - total) // 2
    shade(x - 6, y - 4, x + total + 6, y + 34)


def footer(pairs, y=34, raw=False):
    """화면 아래 가운데 키 안내 (자리·간격은 hud_kit.footer와 같다): 가는 테두리 키 + 설명. 뒤 어둠은 footer_shade로 먼저.
    N1-3: 마지막 장치가 패드면 패드 버튼으로 (raw면 그대로)."""
    import input_device
    if not raw:
        pairs = input_device.footer(pairs)
    widths = footer_widths(pairs)
    total = sum(widths) + 44 * (len(pairs) - 1)
    x = (W - total) // 2
    for (k, d), w in zip(pairs, widths):
        kw = keycap(x, y, k)
        kit.text(x + kw + 10, y + 15, d, PH_SOFT, small=True)
        x += w + 44


def bar(x, y, w, h, ratio, hot=False):
    """음량 막대: H1 가는 테두리 막대(hud_bar)에 인광색 속 (테두리는 고른 줄이면 밝게)."""
    kit.hud_bar('phos', x, y, w, h, ratio, tone='ph' if hot else 'ph_dim')


def title(x, cy, s, color=PH, center=False):
    """화면 제목: 판 없이 큰 글자 (그림자 있는 글자)."""
    kit.text(x, cy, s, color, big=True, center=center)


def rule(x, y, w, color=PH_DIM):
    """가는 장식선 (화면 2px 한 줄): 절 제목 아래."""
    assets.draw_rect_color(int(x), int(y), int(w), 2, color)


def underline(cx, y, label, color=PH, small=True):
    """고른 값 아래 가는 밑줄 (글자 폭 + 양옆 8px, 2px)."""
    tw = assets.text_width(label, small)
    assets.draw_rect_color(int(cx) - tw // 2 - 8, int(y), tw + 16, 2, color)


def terminal(lines):
    """메뉴 화면 공통 틀: 주사선 + 네 귀퉁이 꺾쇠 + 왼쪽 위 머리글 (글자 뒤 어둠 포함)."""
    scanlines()
    brackets()
    hx, hy = TERM_HEAD
    width = max(assets.text_width(s, True) for s, _c in lines)
    shade(hx - 8, hy - 26 * (len(lines) - 1) - 12, hx + width + 8, hy + 12)
    header(lines)
