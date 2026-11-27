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
    kit.hud_keycap(key_x, key_y, keybinds.label(f'weapon{i + 1}', first=True)[:3], hot=active, dim_color=IDLE)
    if not active and p.weapons[p.slot] is not None:                # v8 교체기 (flat과 같은 뜻)
        import combo
        ratio = max(0.0, 1.0 - p.swap_cool / max(0.01, getattr(p, 'swap_cool_max', config.SWAP_COOLDOWN)))
        bx, by, bw = bar
        assets.draw_rect_color(bx, by, _even(bw * ratio), 4, combo.COLORS[wp.weapon_id] if ratio >= 1.0 else COOL)


def _texts(u, bar_x, bar_y, bar_w, atk_y, name_y, right):
    """무기 이름·지금 나가는 공격·재충전 막대·무기 표시 (문구와 색은 flat과 같다)."""
    p = u.player
    w, g = p.weapon, p.gauge
    text, color = u._attack_text(w, g)
    if g.enhanced and g.enhance_level >= config.ENHANCE_MAX_LEVEL:
        import weapon as weapon_mod
        text, color = '궁극기 ' + weapon_mod.ULT_NAMES[w.weapon_id], (255, 200, 120)
    elif g.enhanced:
        text, color = f'강화 {g.enhance_level}단계 ' + text.split(':')[0], config.ENHANCE_LEVEL_COLOR[_tier(g)]
    kit.text(right, atk_y, text, color, small=True, right=True)
    kit.text(right, name_y, w.name, WHITE, right=True)
    ratio = 1.0 if w.ready else 1.0 - w.cooldown / max(w.cooldown_max, 0.01)
    kit.hud_bar('white' if w.ready else 'gray', bar_x, bar_y, bar_w, 8, ratio)
    meter_x = right - assets.text_width(w.name, False) - 24
    u._draw_weapon_meter(meter_x - 130, name_y - 12)


def _cost(g, x, y, center=True):
    ready, hot = g.can_enhance(), g.enhanced
    cost = f'-{g.cost}%' if hasattr(g, 'cost') else f'-{config.ENHANCE_COST}%'
    s = f'강화 {cost}' if (ready or hot) else f'강화 {g.enhance_min}%+'
    kit.text(x, y, s, TEAL if ready else LOW_TEXT, small=True, center=center)


def _e_key(g, x, y):
    import keybinds
    kit.hud_keycap(x, y, keybinds.label('enhance', first=True)[:3], hot=g.can_enhance() or g.enhanced, dim_color=IDLE)


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


DRAW = {'a': draw_a, 'b': draw_b, 'c': draw_c}


def draw(u, style):
    DRAW[style](u)
