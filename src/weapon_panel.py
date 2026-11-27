"""무기·E 패널 시안 셋 (2026-11-27 W1, docs/opus/TASKS.md '4차' W1). HUD 오른쪽 아래 묶음(E 칸·무기 두 칸·콤보 칸·재충전 막대·
'강화' 글자·무기 이름과 지금 나가는 공격)을 config.HUD_WEAPON_STYLE에 따라 그린다. mist 스킨에서만 쓰인다(hud_kit.weapon_style).
'flat'(지금 모습)은 ui.GameUI._draw_actions가 예전대로 그리고, 여기는 'a'·'b'·'c'만 맡는다.

사용자(11/27): "무기, E 나오는 UI창이 너무 밋밋하게 변경이 되었는데 조금의 특색이 들어가면 좋겠다."
  a '결정 소켓': E = 마름모 소켓에 박힌 헤이즈 결정. 쓸 수 있음 = 결정이 차 있다, 못 씀 = 빈 소켓(윤곽만), 켬 = 결정이 단계 색으로
                 빛나고 남은 시간만큼 차 있다(위에서부터 빠진다). 단계 = 소켓 왼쪽 위 변을 따라 돋은 결정 조각 셋.
                 무기 칸 = 두 모서리를 깎은 결정 면, 든 칸이 크다(96 / 76).
  b '감시 단말': 칸을 닫지 않고 네 귀퉁이 꺾쇠 + 주사선 바탕. 든 칸 = 긴 밝은 꺾쇠 + 인광색 'ACT', 다른 칸 = 짧은 회백 꺾쇠.
                 E = 둥근 조준 계기. 못 씀 = 끊긴 원, 쓸 수 있음 = 이어진 원 + 눈금, 켬 = 단계 색 원 + 원 위 호(단계) + 안쪽 시간 막대.
  c '문장':      세 칸을 한 덩어리로: 가운데 마름모 E 문장이 앞에, 양옆 방패 모양 무기 칸이 그 뒤에 물린다(든 칸이 크다 100 / 76).
                 증강 카드 장식선 말투의 가로선이 덩어리 위를 지나고, 그 위에 단계 마름모 셋. 켜면 가로선이 단계 색으로 차고
                 남은 시간만큼 양끝에서 줄어든다.
그림 부품은 tools/make_ui_mist.py --wp (assets/ui/um_wp_*). 판·장식은 미리 구운 한 장씩(실행 중 사각형을 겹쳐 장식을 만들지 않는다).
좌표는 모두 짝수(도트 2px 격자), 확대·회전 없음.
"""
import assets
import config
import hud_kit as kit
import ui

WHITE = (235, 240, 250)
TEAL = (130, 235, 225)
IDLE = ui.IDLE                  # 들지 않은 칸의 아이콘 색 곱·숫자·'빈 칸'
LOW_TEXT = (140, 150, 168)      # 못 씀일 때 '강화 30%+' (flat의 FAINT보다 조금 밝게: 어두운 방에서 읽히게)
PH = (168, 240, 200)            # 감시 단말 인광색 (타이틀·메뉴와 같은 색)
COOL = (96, 108, 130)           # 교체기 막대가 덜 찼을 때


def _put(name, left, bottom):
    img = assets.image(f'ui/um_wp_{name}.png')
    assets.draw_image(img, left + img.w // 2, bottom)
    return img


def _even(v):
    return int(v) // 2 * 2


def _tier(g):
    return max(1, min(3, g.enhance_level))


def _weapon_in_slot(p, i, x, y, w, h, icon_cx, icon_bottom, key_x, key_y, bar):
    """무기 칸 속: 아이콘(든 칸 = 원래 색, 다른 칸 = 회백 곱), 키 글자, 빈 칸 글자, 교체기 막대(다른 칸: 다 차면 그 무기 색)."""
    wp = p.weapons[i]
    active = i == p.slot
    if wp is None:
        kit.text(icon_cx, y + h // 2, '빈 칸', IDLE, small=True, center=True)
        return
    img = assets.image(f'ui/icon_w_{wp.weapon_id}.png')
    if active:
        assets.draw_image(img, icon_cx, icon_bottom)
    else:
        assets.draw_image_tinted(img, icon_cx, icon_bottom, '', IDLE, 0.85)
    import keybinds
    kit.hud_keycap(key_x, key_y, keybinds.badge(f'weapon{i + 1}'), hot=active, dim_color=IDLE)
    if not active and p.weapons[p.slot] is not None:                # v8 교체기 (flat과 같은 뜻)
        import combo
        ratio = max(0.0, 1.0 - p.swap_cool / max(0.01, getattr(p, 'swap_cool_max', config.SWAP_COOLDOWN)))
        bx, by, bw = bar
        assets.draw_rect_color(bx, by, _even(bw * ratio), 4, combo.COLORS[wp.weapon_id] if ratio >= 1.0 else COOL)


def _attack_line(u):
    """지금 나가는 공격 글자와 색 (강화 중이면 '강화 n단계 …', 3단계면 궁극기 이름). 문구는 flat과 같다."""
    p = u.player
    w, g = p.weapon, p.gauge
    text, color = u._attack_text(w, g)
    if g.enhanced and g.enhance_level >= config.ENHANCE_MAX_LEVEL:
        import weapon as weapon_mod
        text, color = '궁극기 · ' + weapon_mod.ULT_NAMES[w.weapon_id], (255, 200, 120)
    elif g.enhanced:
        text, color = f'강화 {g.enhance_level}단계 ' + text.split(':')[0], config.ENHANCE_LEVEL_COLOR[_tier(g)]
    return text, color


def _texts(u, bar_x, bar_y, bar_w, atk_y, name_y, right):
    """무기 이름·지금 나가는 공격·재충전 막대·무기 표시 (문구와 색은 flat과 같다)."""
    p = u.player
    w = p.weapon
    text, color = _attack_line(u)
    kit.text(right, atk_y, text, color, small=True, right=True)
    kit.text(right, name_y, w.name, WHITE, right=True)
    if bar_x is not None:                                          # d는 재충전을 든 칸 안 줄로 보여 준다
        ratio = 1.0 if w.ready else 1.0 - w.cooldown / max(w.cooldown_max, 0.01)
        kit.hud_bar('white' if w.ready else 'gray', bar_x, bar_y, bar_w, 8, ratio)
    meter_x = right - assets.text_width(w.name, False) - 24
    u._draw_weapon_meter(meter_x - 130, name_y - 12)


def _cost(g, x, y, center=True, right=False):
    ready, hot = g.can_enhance(), g.enhanced
    cost = f'-{g.cost}%' if hasattr(g, 'cost') else f'-{config.ENHANCE_COST}%'
    s = f'강화 {cost}' if (ready or hot) else f'강화 {g.enhance_min}%+'
    kit.text(x, y, s, TEAL if ready else LOW_TEXT, small=True, center=center, right=right)


def _e_key(g, x, y):
    import keybinds
    kit.hud_keycap(x, y, keybinds.badge('enhance'), hot=g.can_enhance() or g.enhanced, dim_color=IDLE)


# ----- a 결정 소켓 -----
A_BIG, A_SMALL, A_GAP = 96, 76, 10
A_SHARDS = ((-56, 12), (-42, 26), (-28, 40))     # 소켓 가운데에서 결정 조각(12x22)의 왼쪽 아래 (왼쪽 위 변을 따라 바깥으로)


def draw_a(u):
    p = u.player
    g = p.gauge
    R, B = ui.ACT_RIGHT, ui.ACT_Y
    sizes = [A_BIG if i == p.slot else A_SMALL for i in (0, 1)]
    x0 = R - (sizes[0] + A_GAP + sizes[1])
    xs = [x0, x0 + sizes[0] + A_GAP]
    for i in (0, 1):
        s, x, active = sizes[i], xs[i], i == p.slot
        _put(f'a_slot_{"big" if active else "small"}_{"hot" if active else "line"}', x, B)
        small = s == A_SMALL                                         # 작은 칸: 아이콘을 오른쪽 아래로 (왼쪽 위 키 글자와 겹치지 않게)
        _weapon_in_slot(p, i, x, B, s, s, x + s // 2 + (6 if small else 4), B + (8 if small else (s - 48) // 2 - 2),
                        x + 4, B + s - 34, (x + 14, B + 4, s - 24))
    # E 소켓 (마름모 104, 캔버스 112)
    cx, cy = x0 - 12 - 52, B + 52
    ready, hot = g.can_enhance(), g.enhanced
    _put(f'a_socket_e{_tier(g)}' if hot else 'a_socket_line', cx - 56, cy - 56)
    cl, cb = cx - 12 + 6, cy - 26                                   # 결정 24x52 (가운데에서 조금 오른쪽: 왼쪽에 키 글자)
    if hot:
        _put('a_crystal_empty', cl, cb)
        img = assets.image(f'ui/um_wp_a_crystal_e{_tier(g)}.png')
        hh = _even(img.h * max(0.0, min(1.0, g.enhance_timer / config.ENHANCE_TIME)))
        if hh > 0:
            assets.draw_clip(img, 0, 0, img.w, hh, cl, cb)
    else:
        _put('a_crystal_haze' if ready else 'a_crystal_empty', cl, cb)
    _e_key(g, cx - 48, cy - 16)
    for i, (dx, dy) in enumerate(A_SHARDS):
        on = hot and i < g.enhance_level
        _put(f'a_shard_e{i + 1}' if on else 'a_shard_off', cx + dx, cy + dy)
    _cost(g, cx, cy + 80)
    _texts(u, x0, B + A_BIG + 14, R - x0, B + 166, B + 200, R)


# ----- b 감시 단말 -----
B_SLOT, B_GAP = 92, 14


def draw_b(u):
    p = u.player
    g = p.gauge
    R, B = ui.ACT_RIGHT, ui.ACT_Y
    xs = [R - 2 * B_SLOT - B_GAP, R - B_SLOT]
    for i in (0, 1):
        x, active = xs[i], i == p.slot
        _put('b_well', x, B)
        _put('b_bracket_hot' if active else 'b_bracket_line', x, B)
        if active:
            kit.text(x + B_SLOT - 8, B + B_SLOT - 16, 'ACT', PH, small=True, right=True)
        _weapon_in_slot(p, i, x, B, B_SLOT, B_SLOT, x + B_SLOT // 2 + 4, B + 18, x + 4, B + B_SLOT - 34, (x + 8, B + 6, B_SLOT - 16))
    # E 계기 (원 지름 96, 캔버스 112)
    cx, cy = xs[0] - 18 - 48, B + 52
    ready, hot = g.can_enhance(), g.enhanced
    _put(f'b_dial_e{_tier(g)}' if hot else ('b_dial_line' if ready else 'b_dial_low'), cx - 56, cy - 56)
    img = assets.image('ui/icon_enhance.png')
    if hot or ready:
        assets.draw_image(img, cx + 6, cy - 22)
    else:
        assets.draw_image_tinted(img, cx + 6, cy - 22, '', IDLE, 0.55)
    _e_key(g, cx - 40, cy + 6)
    for i in range(3):
        _put(f'b_arc{i}_on' if hot and i < g.enhance_level else f'b_arc{i}_off', cx - 56, cy - 56)
    if hot:
        r = max(0.0, min(1.0, g.enhance_timer / config.ENHANCE_TIME))
        assets.draw_rect_color(cx - 28, cy - 36, _even(56 * r), 4, config.ENHANCE_LEVEL_COLOR[_tier(g)])
    _cost(g, cx, cy + 80)
    _texts(u, xs[0], B + B_SLOT + 14, R - xs[0], B + 166, B + 200, R)


# ----- c 문장 -----
C_BIG, C_SMALL = (100, 108), (76, 84)
C_CREST, C_OVER = (96, 116), 12
C_RULE_W = 244


def draw_c(u):
    p = u.player
    g = p.gauge
    R, B = ui.ACT_RIGHT, ui.ACT_Y
    dims = [C_BIG if i == p.slot else C_SMALL for i in (0, 1)]
    left = R - (dims[0][0] + C_CREST[0] + dims[1][0] - 2 * C_OVER)
    crest_x = left + dims[0][0] - C_OVER
    xs = [left, crest_x + C_CREST[0] - C_OVER]
    for i in (0, 1):
        (w, h), x, active = dims[i], xs[i], i == p.slot
        _put(f'c_shield_{"big" if active else "small"}_{"hot" if active else "line"}', x, B)
        vis = (x, x + w - C_OVER) if i == 0 else (x + C_OVER, x + w)      # 문장에 덮이지 않는 쪽
        icx = (vis[0] + vis[1]) // 2
        key_x = x + 6 if i == 0 else x + w - 40
        # 교체기 막대는 방패 윗변 위에 겹쳐 그린다 (다 차면 윗변이 그 무기 색으로 켜진다)
        _weapon_in_slot(p, i, x, B, w, h, icx, B + h // 2 - 26, key_x, B + h - 36, (vis[0] + 6, B + h - 4, vis[1] - vis[0] - 12))
    # E 문장 (마름모 92x108, 무기 칸 앞)
    ready, hot = g.can_enhance(), g.enhanced
    ccx = crest_x + C_CREST[0] // 2
    _put(f'c_crest_e{_tier(g)}' if hot else ('c_crest_line' if ready else 'c_crest_low'), crest_x, B)
    img = assets.image('ui/icon_enhance.png')
    if hot or ready:
        assets.draw_image(img, ccx + 10, B + 34)
    else:
        assets.draw_image_tinted(img, ccx + 10, B + 34, '', IDLE, 0.55)
    _e_key(g, ccx - 40, B + 44)                                     # 키 글자는 문장 안 왼쪽 (위 꼭짓점 쪽은 좁다)
    # 가로선: 덩어리 위를 지나 이름 줄과 잇는다. 켜면 단계 색으로 차고 남은 시간만큼 양끝에서 줄어든다
    ry = B + C_CREST[1] + 4
    rl = R - C_RULE_W
    _put('c_rule_line', rl, ry)
    if hot:
        rimg = assets.image(f'ui/um_wp_c_rule_e{_tier(g)}.png')
        r = max(0.0, min(1.0, g.enhance_timer / config.ENHANCE_TIME))
        half = _even(rimg.w // 2 * r)
        if half > 0:
            assets.draw_clip(rimg, rimg.w // 2 - half, 0, 2 * half, rimg.h, rl + rimg.w // 2 - half, ry)
    for i, dx in enumerate((-24, 0, 24)):
        on = hot and i < g.enhance_level
        _put(f'c_pip_e{i + 1}' if on else 'c_pip_off', ccx - 8 + dx, ry)
    _cost(g, rl + 2, ry + 26, center=False)
    _texts(u, rl + 130, ry + 20, C_RULE_W - 130, ry + 58, ry + 92, R)


# ----- d 떠 있는 칸 (2026-11-27 W2) -----
# 사용자가 A·B·C를 본 뒤 참고 그림과 함께 "이런 느낌 안되나?". 그림에서 가져온 것은 구성 원리뿐이다(모양·색은 헤이즈의 것):
#  (1) 칸이 하나씩 따로 떠 있다(반투명 바탕, 칸 사이가 비어 있다)  (2) 크기·자리가 어긋난다(무기 두 칸은 세로로 쌓고 위 칸이 왼쪽으로 비켜,
#  E 칸은 따로 오른쪽 아래)  (3) 든 칸만 그 무기의 색으로 밝다  (4) 칸 바깥에 반쯤 걸친 동그란 키 배지  (5) E 칸 모서리의 단계 숫자 배지
#  (6) 아이콘은 지금 것(크고 단순한 실루엣) 그대로.
D_SLOT_W, D_SLOT_H = 100, 64
D_E = 84
D_KEY = 32
D_LV = 26
D_ALPHA = 0.84                  # 칸 바탕 불투명도: 뒤가 조금 비치되 밝은 벽 위에서도 글자·아이콘이 읽히게 (촬영으로 정함)
D_INK = (8, 11, 20)             # 단계 배지 숫자 (밝은 단계 색 위)
D_RECHARGE = ((216, 221, 230), (128, 137, 152))   # 든 칸 아래 재충전 줄: 다 참 / 차는 중 (flat 막대의 흰색·회색)


def _well(name, left, bottom, alpha=D_ALPHA):
    img = assets.image(f'ui/um_wp_{name}.png')
    assets.draw_image_tinted(img, left + img.w // 2, bottom, '', (255, 255, 255), alpha)


def _key_badge(label, cx, cy, hot, text_color, art=False):
    """칸 바깥에 반쯤 걸친 동그란 키 배지 (불투명). 글자는 가운데. art: row에서 그림 값(HUD_WEAPON_ART)을 따른다."""
    if not label:                                   # N1-3: 패드의 무기 칸 (칸마다 키가 없다)
        return
    (_put_art if art else _put)('d_key_hot' if hot else 'd_key_line', cx - D_KEY // 2, cy - D_KEY // 2)
    kit.text(cx, cy, label, text_color, small=True, center=True)


def d_layout():
    """칸 자리 (왼쪽 아래 기준): 무기 1번 칸(위, 왼쪽으로 비킴), 2번 칸(아래), E 칸(따로 오른쪽 아래)."""
    R, B = ui.ACT_RIGHT, ui.ACT_Y
    ex, ey = R - D_E, B + 16
    x2, y2 = ex - 28 - D_SLOT_W, B + 12
    x1, y1 = x2 - 24, y2 + D_SLOT_H + 10
    return (x1, y1), (x2, y2), (ex, ey)


def draw_d(u):
    import keybinds
    p = u.player
    w, g = p.weapon, p.gauge
    R = ui.ACT_RIGHT
    (x1, y1), (x2, y2), (ex, ey) = d_layout()
    spots = [(x1, y1), (x2, y2)]
    for x, y in spots:                                             # 바탕 먼저 (반투명, 칸마다 따로)
        _well('d_well', x, y)
    _well('d_e_well', ex, ey)
    for i, (x, y) in enumerate(spots):
        _d_weapon_slot(p, i, x, y)
    # E 칸: 쓸 수 있음 = 회백, 못 씀 = 회백 테두리 + 흐린 아이콘·키·글자, 켬 = 단계 색 테두리 + 단계 배지 + 위쪽 안 시간 줄
    ready, hot = g.can_enhance(), g.enhanced
    lv = _tier(g)
    _put(f'd_e_e{lv}' if hot else 'd_e_line', ex, ey)
    img = assets.image('ui/icon_enhance.png')
    if hot or ready:
        assets.draw_image(img, ex + D_E // 2, ey + 20)
    else:
        assets.draw_image_tinted(img, ex + D_E // 2, ey + 20, '', IDLE, 0.55)
    if hot:
        r = max(0.0, min(1.0, g.enhance_timer / config.ENHANCE_TIME))
        assets.draw_rect_color(ex + 16, ey + D_E - 10, _even((D_E - 30) * r), 4, config.ENHANCE_LEVEL_COLOR[lv])
    _key_badge(keybinds.badge('enhance'), ex + D_E // 2, ey, ready or hot, (242, 246, 250) if (ready or hot) else IDLE)
    if hot or ready:                                               # 모서리 단계 배지 (켬 = 단계 색 + 숫자, 쓸 수 있음 = 빈 배지, 못 씀 = 없음)
        bx, by = ex + D_E - D_LV + 8, ey + D_E - D_LV + 8
        _put(f'd_lv_e{lv}' if hot else 'd_lv_off', bx, by)
        if hot:
            _lv_number(g, bx, by)
    _cost(g, R, ey + D_E + 30, center=False, right=True)
    # 무기 이름·지금 나가는 공격 (오른쪽 맞춤, 묶음 위), 무기 표시(콤보 칸 등)는 이름 왼쪽
    _texts(u, None, None, None, y1 + D_SLOT_H + 26, y1 + D_SLOT_H + 60, R)


def _lv_number(g, bx, by):
    assets.draw_text(bx + D_LV // 2, by + D_LV // 2 + 2, str(g.enhance_level), D_INK, small=True, center=True)   # 글자가 아래로 처져 보여 2px 올림


def _d_weapon_slot(p, i, x, y):
    """D 무기 칸 하나: 테두리(든 칸 = 무기 색), 아이콘, 빈 칸 글자, 든 칸 재충전 줄 / 다른 칸 교체기 줄, 왼쪽에 반쯤 걸친 키 배지."""
    import keybinds
    w = p.weapon
    wp = p.weapons[i]
    active = i == p.slot and wp is not None
    _put(f'd_slot_{wp.weapon_id}' if active else 'd_slot_line', x, y)
    cy = y + D_SLOT_H // 2
    if wp is None:
        kit.text(x + D_SLOT_W // 2 + 8, cy, '빈 칸', IDLE, small=True, center=True)
    else:
        img = assets.image(f'ui/icon_w_{wp.weapon_id}.png')
        icx = x + D_SLOT_W // 2 + 8
        if active:
            assets.draw_image(img, icx, y + (D_SLOT_H - img.h) // 2)
            ratio = 1.0 if w.ready else 1.0 - w.cooldown / max(w.cooldown_max, 0.01)   # 재충전: 든 칸 아래 안쪽 줄
            assets.draw_rect_color(x + 22, y + 6, _even((D_SLOT_W - 32) * ratio), 4, D_RECHARGE[0 if w.ready else 1])
        else:
            assets.draw_image_tinted(img, icx, y + (D_SLOT_H - img.h) // 2, '', IDLE, 0.85)
            if p.weapons[p.slot] is not None:                   # 교체기 (flat과 같은 뜻: 다 차면 그 무기 색)
                import combo
                r = max(0.0, 1.0 - p.swap_cool / max(0.01, getattr(p, 'swap_cool_max', config.SWAP_COOLDOWN)))
                assets.draw_rect_color(x + 22, y + 6, _even((D_SLOT_W - 32) * r), 4, combo.COLORS[wp.weapon_id] if r >= 1.0 else COOL)
    _key_badge(keybinds.badge(f'weapon{i + 1}'), x, cy, active, (242, 246, 250) if active else IDLE)


# ----- da = D 배치 + A 결정 소켓 (2026-11-27 W3, 기본값) -----
# 사용자(11/27): "D 배치에 A 결정 소켓으로 합쳐줘". 지휘 쪽 판단으로 W2 약점 셋도 같이 손봤다:
#  1) '강화 -25%' 글자는 소켓 위에 작은 반투명 꼬리표(um_wp_da_tag_well)를 받치고 그 위에 쓴다(긴 띠 아님)
#  2) 켜지 않았을 때는 단계 배지를 그리지 않는다('쓸 수 있음'은 찬 청록 결정이 알린다). 켜면 소켓 오른쪽 위 변에 단계 숫자 배지
#  3) 무기 이름·공격 줄·콤보 칸은 무기 칸 묶음 바로 위, 칸 묶음 왼쪽 끝(키 배지 바깥)에 맞춰 왼쪽 정렬
# A의 변을 따라 난 결정 조각(단계)은 숫자 배지와 뜻이 겹쳐 뺐다. A의 소켓 안 'E' 글자도 빼고 소켓 아래 꼭짓점에 걸친 키 배지 하나로.
DA_ALPHA = 0.9                  # 칸·소켓·꼬리표 바탕 불투명도 (D 0.84에서 올림: 뒤 상자 무늬가 아이콘을 덜 흐리게. 촬영으로 정함)
DA_SOCKET = 104                 # 소켓 마름모 한 변 대각 (캔버스 112)
DA_TAG_W, DA_TAG_H = 128, 28


def da_layout():
    """자리: 무기 1번 칸(위, 왼쪽으로 비킴)·2번 칸(아래)의 왼쪽 아래, 소켓 가운데 (cx, cy)."""
    R, B = ui.ACT_RIGHT, ui.ACT_Y
    cx, cy = R - DA_SOCKET // 2, B + 16 + DA_SOCKET // 2
    x2, y2 = cx - DA_SOCKET // 2 - 12 - D_SLOT_W, B + 12
    x1, y1 = x2 - 24, y2 + D_SLOT_H + 10
    return (x1, y1), (x2, y2), (cx, cy)


def draw_da(u):
    import keybinds
    p = u.player
    w, g = p.weapon, p.gauge
    R = ui.ACT_RIGHT
    (x1, y1), (x2, y2), (cx, cy) = da_layout()
    spots = [(x1, y1), (x2, y2)]
    tag_x, tag_y = cx - 14 - DA_TAG_W // 2, cy + DA_SOCKET // 2 + 6
    for x, y in spots:                                             # 바탕 먼저 (반투명, 칸마다 따로)
        _well('d_well', x, y, DA_ALPHA)
    _well('da_socket_well', cx - 56, cy - 56, DA_ALPHA)
    _well('da_tag_well', tag_x, tag_y, DA_ALPHA)
    for i, (x, y) in enumerate(spots):
        _d_weapon_slot(p, i, x, y)
    # E 결정 소켓 (A와 같은 뜻): 못 씀 = 빈 결정 윤곽, 쓸 수 있음 = 청록 결정, 켬 = 단계 색 소켓·결정(남은 시간만큼 차 있고 위에서부터 빠진다)
    ready, hot = g.can_enhance(), g.enhanced
    lv = _tier(g)
    _put(f'da_socket_e{lv}' if hot else 'da_socket_line', cx - 56, cy - 56)
    cl, cb = cx - 12, cy - 26
    if hot:
        _put('a_crystal_empty', cl, cb)
        img = assets.image(f'ui/um_wp_a_crystal_e{lv}.png')
        hh = _even(img.h * max(0.0, min(1.0, g.enhance_timer / config.ENHANCE_TIME)))
        if hh > 0:
            assets.draw_clip(img, 0, 0, img.w, hh, cl, cb)
    else:
        _put('da_crystal_haze' if ready else 'a_crystal_empty', cl, cb)       # 쓸 수 있음: A보다 한 단 어두운 청록 (든 무기 칸이 먼저 읽히게)
    _key_badge(keybinds.badge('enhance'), cx, cy - DA_SOCKET // 2, ready or hot, (242, 246, 250) if (ready or hot) else IDLE)
    if hot:                                                        # 단계 배지: 소켓 오른쪽 위 변에 걸쳐서, 켰을 때만
        bx, by = cx + 24, cy + 24
        _put(f'd_lv_e{lv}', bx, by)
        _lv_number(g, bx, by)
    _cost(g, tag_x + DA_TAG_W // 2, tag_y + DA_TAG_H // 2)
    # 무기 이름(위)·지금 나가는 공격(아래)·무기 표시: 무기 칸 묶음 바로 위, 칸 묶음 왼쪽 끝에 맞춰 왼쪽 정렬
    left = x1 - D_KEY // 2
    text, color = _attack_line(u)
    atk_y, name_y = y1 + D_SLOT_H + 22, y1 + D_SLOT_H + 54
    kit.text(min(left, R - assets.text_width(text, True)), atk_y, text, color, small=True)
    kit.text(left, name_y, w.name, WHITE)
    tw = assets.text_width(w.name, False)
    u._draw_weapon_meter(left + tw + 14 - {'pipe': 40, 'gauntlet': 10}.get(w.weapon_id, 20), name_y - 12)


# ----- row = 한 줄 배치 (2026-11-27 W4, 기본값) -----
# 사용자: "배치를 새로 짜는 것으로 현재 비슷한 장르 게임들의 ui 배치나, 색, 반투명도, 크기 등을 조사해서 세팅을 해줘". 조사 요지는 docs/REFERENCES.md.
# 규칙: ① 자리 고정 ② 키 순서대로 한 줄(왼쪽부터 1·2·E, 아랫변 맞춤) ③ 든 칸은 크기·바탕 불투명도·아이콘 밝기·밝은 겉 테두리로 동시에 구분(색만 쓰지 않는다)
#       ④ 글은 줄이고 아이콘·모양으로 ⑤ 상태 변화는 큰 모양 변화로(결정이 비고 차고 색이 바뀐다) ⑥ 가장자리 여백(오른쪽 28 = 미니맵과 같은 ui.MARGIN, 아래 40 이상).
# 든 칸이 그 자리에서 커지고 줄의 왼쪽 끝·E 소켓은 움직이지 않는다(1번 칸 왼쪽 끝과 2번 칸 오른쪽 끝이 고정, 두 칸의 경계만 24px 움직인다).
# 무기 색은 든 칸 안쪽 줄과 재충전 줄에만. W3의 결정 소켓(못 씀 = 빈 윤곽, 쓸 수 있음 = 청록, 켬 = 단계 색이 남은 시간만큼)과 단계 숫자 배지·키 배지는 그대로.
ROW_BIG, ROW_SMALL = (96, 72), (72, 56)       # 든 칸 / 들지 않은 칸 (약 1.3 : 1)
ROW_GAP = 18                                  # 칸 사이 (키 배지가 칸 사이 틈에 들어가게. 소켓과의 틈은 ROW_SOCKET_GAP)
ROW_SOCKET_GAP = 10
ROW_TAG_W = 104                               # '강화' 꼬리표 (소켓 위, 2번 칸 위 이름 줄과 겹치지 않는 폭)
ROW_BASE = 56                                 # 칸 아랫변. 키 배지(지름 32)가 반쯤 걸쳐 아래 끝이 40
ROW_SOCKET = 96                               # 소켓 그림 (마름모 88, 둘레 4px)
# R2(11/27): 기본 그림 'mix'의 마름모 테두리(um_wp_row_socket_mix_*, 96x104 캔버스). 세로로 긴 마름모(겉 70x92)의 가운데가 도트 한가운데(x = cx - 1)라
# 홀수 폭(13도트) PixelLab 결정과 축이 같다. 아래 꼭짓점은 예전처럼 줄 아랫변보다 8px 아래, 위 꼭짓점은 4px 높아진다
ROW_MIX_H, ROW_MIX_HALF = 104, 46             # 캔버스 높이, 겉 마름모 반높이 (px)
ROW_MIX_LV_DX = -4                             # 단계 숫자 배지를 4px 안쪽으로 (마름모가 좁아져 오른쪽 위 변에 걸치게)
ROW_ALPHA_HELD, ROW_ALPHA_IDLE, ROW_ALPHA_SOCKET = 0.9, 0.72, 0.86    # 바탕 불투명도
ROW_ICON_IDLE = ((172, 180, 196), 0.6)        # 들지 않은 칸 아이콘: 회백 곱, 불투명도 0.6


ROW_NAME_DY = 22                              # 무기 이름 줄 (든 칸 윗변에서 위로). W6: 평소에는 칸 바로 위 (W5의 40은 설명 줄이 없을 때 이름이 떠 보였다)
ROW_NAME_UP = 40                              # 설명 줄이 뜨는 동안의 이름 줄 (설명 줄이 이름과 칸 사이에 들어온다)
ROW_NAME_MID = 30                             # 오르내리는 중간 한 단계
ROW_RISE_STEP = 0.05                          # 한 단계 시간(초)
ROW_HINT_DY = 16                              # 공격 설명 줄 (이름 바로 아래, 든 칸 윗변과의 틈)
ROW_MARK = 10                                 # 든 칸 안 무기 표시 한 칸 (화면 px, um_wp_row_combo_*)
ROW_HINT_STEPS = ((0.3, 0.6), (0.15, 0.3))    # 사라지기 전 남은 시간 -> 밝기 (단계 페이드: 1 -> 0.6 -> 0.3 -> 없음)


def _row_meter(w, x, y, sw, sh):
    """든 칸 안쪽 오른쪽 세로 줄: 철파이프 콤보 칸 셋(셋째 = 3타, 빨강), 쌍권총·사슬 개수 칸(넷까지, 강화·관통이면 빨강), 건틀릿 충전 막대(다 차면 청록).
    아래에서 위로 찬다. 재충전 줄(아래 6~10px)과 칸 테두리 안쪽."""
    mx, my = x + sw - 8 - ROW_MARK, y + 14
    if w.weapon_id == 'gauntlet':
        r = max(0.0, min(1.0, w.charge_ratio))
        hgt = sh - 24
        assets.draw_rect_color(mx + 2, my, ROW_MARK - 4, hgt, (48, 56, 72))      # 빈 막대 (바탕보다 밝게: 비어 있어도 자리가 보이게)
        fh = _even(hgt * r)
        if fh > 0:
            assets.draw_rect_color(mx + 2, my, ROW_MARK - 4, fh, (46, 230, 214) if r >= 1.0 else (216, 221, 230))
        return
    if w.weapon_id == 'pipe':
        marks = [('fin' if i == 2 else 'on') if i < w.combo else 'off' for i in range(3)]
    else:
        count, _, hot = w.grip() if w.weapon_id == 'chain' else w.volley()
        marks = ['fin' if hot else 'on'] * min(count, 4)
    for i, m in enumerate(marks):
        _put(f'row_combo_{m}', mx, my + i * (ROW_MARK + 2))


def _row_hint_state(u):
    """설명 줄과 이름 자리 (W6): 무기를 바꾸거나 강화를 켜거나(단계가 바뀌거나) 형태가 바뀌거나 방에 들어선 직후부터 잰다.
    돌려주는 것: (이름 줄 높이 = 든 칸 윗변에서 위로, 설명 줄 밝기 0이면 그리지 않음).
    이름은 평소 든 칸 바로 위(ROW_NAME_DY). 바뀐 직후 ROW_RISE_STEP초에 한 단계(ROW_NAME_MID), 그 뒤 ROW_NAME_UP까지 올라가 설명 줄이 그 아래 틈에 뜬다.
    config.WEAPON_HINT_TIME이 지나면 설명 줄이 두 단계로 어두워져 사라지고, 이름이 같은 두 단계로 칸 위에 내려온다. 움직임은 짝수 픽셀."""
    import forms
    p = u.player
    w, g = p.weapon, p.gauge
    room = getattr(u.stage, 'room', None) if u.stage is not None else None
    key = (p.slot, w.weapon_id, g.enhanced, g.enhance_level if g.enhanced else 0, forms.active(w), id(room))
    clock = getattr(u, 'clock', 0.0)
    if getattr(u, 'hint_key', None) != key:
        u.hint_key, u.hint_start = key, clock
    age = clock - u.hint_start
    T = config.WEAPON_HINT_TIME
    if age < ROW_RISE_STEP or T <= age < T + ROW_RISE_STEP:
        return ROW_NAME_MID, 0.0
    if age >= T:
        return ROW_NAME_DY, 0.0
    level = 1.0
    for t, lv in ROW_HINT_STEPS:
        if T - age <= t:
            level = lv
    return ROW_NAME_UP, level


def _row_hint(u, x, y, right, level):
    """공격 설명 줄 (level: 밝기, 사라지기 전 두 단계로 어두워진다). 반투명 바탕(꼬리표와 같은 색) 위에 쓰고,
    오른쪽 끝은 right('강화' 꼬리표 앞)를 넘지 않게 왼쪽으로 민다."""
    if level <= 0:
        return
    text, color = _attack_line(u)
    tw = assets.text_width(text, True)
    x0 = min(x, right - tw)
    assets.draw_rect_color(x0 - 6, y - 12, tw + 12, 24, kit.HUD_WELL, round(0.78 * level, 2))
    kit.text(x0, y, text, tuple(int(c * level + v * (1 - level)) for c, v in zip(color, kit.HUD_WELL)), small=True)


# P1(11/27) 시험: HUD_WEAPON_ART = 'px'이면 row가 PixelLab 부품을 쓴다 (코드 부품 이름 -> PixelLab 부품 이름). 없는 것은 코드 그림
PX_ART = {'row_slot_': 'slot_', 'row_socket_': 'socket_', 'a_crystal_': 'crystal_', 'da_crystal_': 'crystal_', 'd_key_': 'key_'}
# W6(11/27) 확정 'mix' (사용자 "결정을 둘러싼 테두리(소켓)은 기본(코드), 나머지 다른 소켓은 pixelLab"): 결정·무기 칸 틀만 PixelLab
MIX_ART = ('row_slot_', 'a_crystal_', 'da_crystal_')


def _art(name):
    """row 부품 이름 -> 지금 그림 값('code'·'px'·'mix')에 맞는 assets/ui 경로 꼬리 ('wp_<이름>' 또는 'wpx_<이름>')."""
    art = getattr(config, 'HUD_WEAPON_ART', 'code')
    if art in ('px', 'mix'):
        for head, px in PX_ART.items():
            if name.startswith(head) and (art == 'px' or head in MIX_ART):
                cand = 'wpx_' + px + name[len(head):]
                if cand not in _PX_HAVE:
                    import os
                    _PX_HAVE[cand] = os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'ui', f'um_{cand}.png'))
                if _PX_HAVE[cand]:
                    return cand
    return 'wp_' + name


_PX_HAVE = {}                   # PixelLab 부품이 있는지 (한 번만 찾아본다)


def _put_art(name, left, bottom):
    img = assets.image(f'ui/um_{_art(name)}.png')
    assets.draw_image(img, left + img.w // 2, bottom)
    return img


def row_layout(held):
    """칸 자리 [(왼쪽, 아래, 폭, 높이) 1번, 2번], 소켓 가운데 (cx, cy). held = 든 칸 번호(0·1)."""
    R = ui.ACT_RIGHT
    cx = R - 48                                               # 소켓 그림(96)의 오른쪽 끝 = 화면 오른쪽 여백 끝 (꼭짓점은 4px 안)
    cy = ROW_BASE - 8 + 44                                    # 아래 꼭짓점이 줄 아랫변보다 8px 아래로 (어긋남)
    right = cx - 44 - ROW_SOCKET_GAP                          # 2번 칸 오른쪽 끝 (고정)
    w1, h1 = ROW_BIG if held == 0 else ROW_SMALL
    w2, h2 = ROW_BIG if held == 1 else ROW_SMALL
    left = right - (ROW_BIG[0] + ROW_GAP + ROW_SMALL[0])      # 1번 칸 왼쪽 끝 (고정)
    return [(left, ROW_BASE, w1, h1), (left + w1 + ROW_GAP, ROW_BASE, w2, h2)], (cx, cy)


def _meter_span(w):
    """무기 표시(_draw_weapon_meter)가 원점에서 차지하는 오른쪽 끝 (철파이프 콤보 칸 셋, 건틀릿 충전 막대, 사슬·쌍권총 개수 칸)."""
    if w.weapon_id == 'pipe':
        return 118
    if w.weapon_id == 'gauntlet':
        return 120
    count = (w.grip() if w.weapon_id == 'chain' else w.volley())[0]
    return 20 + 26 * (max(1, min(count, 4)) - 1) + 22


def draw_row(u):
    import keybinds
    p = u.player
    w, g = p.weapon, p.gauge
    R = ui.ACT_RIGHT
    spots, (cx, cy) = row_layout(p.slot)
    mix = getattr(config, 'HUD_WEAPON_ART', 'code') == 'mix'
    if mix:                                                    # R2: 세로로 긴 마름모 (아래 꼭짓점 그대로, 가운데가 2px 위)
        cy = ROW_BASE - 8 + ROW_MIX_HALF
        sock, s_bottom, s_half = 'row_socket_mix_', cy - ROW_MIX_H // 2, ROW_MIX_HALF
    else:
        sock, s_bottom, s_half = 'row_socket_', cy - ROW_SOCKET // 2, 44
    tag_x, tag_y = R - ROW_TAG_W, cy + s_half + 6
    for i, (x, y, sw, sh) in enumerate(spots):                 # 바탕 먼저 (칸마다 따로 반투명. 든 칸이 더 불투명)
        big = i == p.slot
        _well(f'row_well_{"big" if big else "small"}', x, y, ROW_ALPHA_HELD if big else ROW_ALPHA_IDLE)
    _well(sock + 'well', cx - ROW_SOCKET // 2, s_bottom, ROW_ALPHA_SOCKET)
    _well('row_tag_well', tag_x, tag_y, ROW_ALPHA_SOCKET)
    for i, (x, y, sw, sh) in enumerate(spots):
        wp = p.weapons[i]
        active = i == p.slot and wp is not None
        _put_art(f'row_slot_{wp.weapon_id}' if active else 'row_slot_line', x, y)
        if wp is None:
            kit.text(x + sw // 2, y + sh // 2, '빈 칸', IDLE, small=True, center=True)
        else:
            img = assets.image(f'ui/icon_w_{wp.weapon_id}.png')
            icx, iby = x + sw // 2 + (-4 if active else 4), y + (sh - img.h) // 2    # 든 칸: 아이콘을 왼쪽으로 비켜 오른쪽에 무기 표시 세로 줄 (W5)
            if active:
                assets.draw_image(img, icx, iby)
                ratio = 1.0 if w.ready else 1.0 - w.cooldown / max(w.cooldown_max, 0.01)   # 재충전: 든 칸 안쪽 아래 줄 (다 차면 무기 색)
                import combo
                assets.draw_rect_color(x + 20, y + 6, _even((sw - 28) * ratio), 4, combo.COLORS[wp.weapon_id] if w.ready else COOL)
            else:
                assets.draw_image_tinted(img, icx, iby, '', *ROW_ICON_IDLE)
                if p.weapons[p.slot] is not None:                   # 교체기 (flat과 같은 뜻: 다 차면 그 무기 색)
                    import combo
                    r = max(0.0, 1.0 - p.swap_cool / max(0.01, getattr(p, 'swap_cool_max', config.SWAP_COOLDOWN)))
                    assets.draw_rect_color(x + 16, y + 6, _even((sw - 24) * r), 4, combo.COLORS[wp.weapon_id] if r >= 1.0 else COOL)
        _key_badge(keybinds.badge(f'weapon{i + 1}'), x + 2, y + 2, active, (242, 246, 250) if active else IDLE, art=True)
    # E 결정 소켓 (W3과 같은 뜻)
    ready, hot = g.can_enhance(), g.enhanced
    lv = _tier(g)
    _put_art(f'{sock}e{lv}' if hot else sock + 'line', cx - ROW_SOCKET // 2, s_bottom)
    probe = assets.image(f'ui/um_{_art("a_crystal_empty")}.png')       # 결정 그림 크기 (코드 24x52, PixelLab 28x56): 소켓 가운데에
    cl, cb = cx - probe.w // 2, cy - probe.h // 2
    if hot:
        _put_art('a_crystal_empty', cl, cb)
        img = assets.image(f'ui/um_{_art(f"a_crystal_e{lv}")}.png')
        hh = _even(img.h * max(0.0, min(1.0, g.enhance_timer / config.ENHANCE_TIME)))
        if hh > 0:
            assets.draw_clip(img, 0, 0, img.w, hh, cl, cb)
    else:
        _put_art('da_crystal_haze' if ready else 'a_crystal_empty', cl, cb)
    _key_badge(keybinds.badge('enhance'), cx - 8, ROW_BASE + 2, ready or hot, (242, 246, 250) if (ready or hot) else IDLE, art=True)
    if hot:                                                        # 단계 숫자 배지: 소켓 오른쪽 위 변에 걸쳐서, 켰을 때만
        bx, by = cx + 18 + (ROW_MIX_LV_DX if mix else 0), cy + 18
        _put(f'd_lv_e{lv}', bx, by)
        _lv_number(g, bx, by)
    _cost(g, tag_x + ROW_TAG_W // 2, tag_y + DA_TAG_H // 2)
    # W5: 무기 표시(콤보 칸·개수 칸·충전 막대)는 든 칸 안쪽 오른쪽 세로 줄 (아이콘은 왼쪽으로 비켜 있다)
    hx, hy, hw, hh_ = spots[p.slot] if p.weapons[p.slot] is not None else spots[0]
    top = hy + hh_
    _row_meter(w, hx, hy, hw, hh_)
    # 늘 떠 있는 글은 무기 이름(든 칸 위, 든 칸을 따라간다)과 '강화' 꼬리표뿐. 공격 설명 줄은 이름 바로 아래(든 칸 윗변과의 틈)에 잠깐만
    name_dy, level = _row_hint_state(u)
    kit.text(hx, top + name_dy, w.name, WHITE, small=True)
    _row_hint(u, hx, top + ROW_HINT_DY, tag_x - 18, level)      # 꼬리표 글자와 붙어 보이지 않게 18px 띄운다


DRAW = {'a': draw_a, 'b': draw_b, 'c': draw_c, 'd': draw_d, 'da': draw_da, 'row': draw_row}


def draw(u, style):
    DRAW[style](u)
