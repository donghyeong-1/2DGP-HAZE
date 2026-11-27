"""타이틀(로비) 화면: 제목 일러스트, 로고, 메뉴(게임 시작 · 설정 · 크레딧 · 종료), 조작 안내.

키보드(W/S·위/아래, Enter·Space)나 마우스(올리면 고르고 누르면 실행)로 메뉴를 고른다.
단축키: O 설정, C 크레딧, Esc 종료. 부품 그림은 hud_kit(판·버튼).
"""
from pico2d import (SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDL_QUIT, SDLK_ESCAPE, SDLK_c, SDLK_o, clear_canvas, get_events,
                    update_canvas)

import assets
import config
import game_framework
import hud_kit as kit
import mist_menu as mm

W, H = config.SCREEN_W, config.SCREEN_H
BUTTON_W, BUTTON_H, GAP = 420, 62, 16
VERSION = 'v0.9 · 2026'
MENU_TOP = 470                             # 첫 버튼의 위쪽 y
MENU = [kit.Button(key, label, (W - BUTTON_W) // 2, MENU_TOP - BUTTON_H - i * (BUTTON_H + GAP), BUTTON_W, BUTTON_H)
        for i, (key, label) in enumerate((('start', '게임 시작'), ('options', '설정'), ('credits', '크레딧'),
                                           ('quit', '종료')))]


def controls_text():
    """타이틀 아래 조작 줄. 키 이름은 키 설정을 따른다."""
    import keybinds
    k = lambda a: keybinds.label(a, first=True)  # noqa: E731
    return (f'{k("left")} {k("right")} 이동   {k("jump")} 점프   마우스 조준·좌클릭 공격   {k("dash")}·우클릭 대시   '
            f'{k("enhance")} 강화   {k("potion")} 물약   {k("swap")} 무기 교체   {k("interact")} 상호작용')


selected = 0
age = 0.0                                  # 타이틀에 머문 시간 (주인공 대기 동작)
_rain = [None]                             # 철판 스킨: 게임의 비 (atmosphere.Weather)
_storm = [None]                            # mist 스킨: 배경 번개 (title_storm.Storm)
HERO_X, HERO_Y = 330, 180                  # 철판 스킨: 주인공 발 위치 (벽 덩어리 위, tools/make_title_plate.py LEDGE_ROWS x 60)
LOGO_Y = 600                               # 로고 아래 가장자리
MENU_PANEL = (W // 2 - 260, 150, 520, 340)  # 철판 스킨: 메뉴 뒤 철판 (x, y, w, h)
# 'mist' 스킨: 감시 단말 (2026-11-27 확정). 인광 글자색, 왼쪽 위 머리글, 오른쪽 아래 판번호 자리 (어둠 시트도 이 자리에 맞춰 굽는다)
# 주사선·꺾쇠·머리글·색 뒤집힌 항목은 메뉴 화면과 같이 쓰려고 mist_menu로 꺼냈다 (11/27 M1. 이 화면은 픽셀 단위로 그대로)
PH, PH_DIM, PH_MENU, PH_BG = mm.PH, mm.PH_DIM, mm.PH_MENU, mm.PH_BG
TERM_HEAD = mm.TERM_HEAD                   # 머리글 첫 줄 (왼쪽, 글자 가운데 y)
TERM_MARGIN = 110                          # 오른쪽 아래 판번호의 오른쪽 여백
BRACKET_MARGIN = mm.BRACKET_MARGIN         # 화면 네 귀퉁이 꺾쇠
SCAN_STEP, SCAN_ALPHA = mm.SCAN_STEP, mm.SCAN_ALPHA


def enter():
    global selected, age
    selected = 0
    age = 0.0
    _storm[0] = None                       # 들어올 때마다 처음 몇 초는 조용히
    import transition
    transition.reveal()
    assets.play_music('title')


def exit():
    pass


def pause():
    pass


def resume():
    pass


def run(key):
    """메뉴 항목 실행."""
    assets.play_sound('pickup')
    if key == 'start':
        import play_mode
        game_framework.change_mode(play_mode)
    elif key == 'options':
        import options_mode
        game_framework.push_mode(options_mode)
    elif key == 'credits':
        import credits_mode
        game_framework.change_mode(credits_mode)
    else:
        game_framework.quit()


def handle_events():
    global selected
    for event in get_events():
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        if event.type == SDL_KEYDOWN and event.key in (SDLK_ESCAPE, SDLK_o, SDLK_c):
            run({SDLK_ESCAPE: 'quit', SDLK_o: 'options', SDLK_c: 'credits'}[event.key])
            return
        before = selected
        selected, action = kit.menu_pick(MENU, selected, event, H)
        if selected != before and event.type != SDL_MOUSEBUTTONDOWN:
            assets.play_sound('swing_fade')                # 고르는 소리 (작게)
        if action == 'click':
            run(MENU[selected].key)
            return


def update():
    global age
    dt = getattr(game_framework, 'frame_time', 0) or 1 / 60
    age += dt
    if kit.is_plate():
        _weather().update(dt)
    if kit.is_mist():
        _get_storm().update(dt)


def _get_storm():
    if _storm[0] is None:
        import title_storm
        _storm[0] = title_storm.Storm()
    return _storm[0]


def _weather():
    if _rain[0] is None:
        import atmosphere
        _rain[0] = atmosphere.Weather(seed=3)
        _rain[0].set_kind('rain')
    return _rain[0]


def _draw_terminal():
    """'mist' 스킨 제목 화면 (2026-11-27 확정 B 감시 단말): 슬럼 배경(발판·주인공 없이)과 비, 가끔 치는 번개(배경 층에만:
    흰 하늘 + 검은 실루엣 대비 판 -> 잔광, title_storm), 글자 뒤에 어둠(글자에서 멀어질수록 옅어지는 빛 층 시트 light/title_shade),
    주사선, 네 귀퉁이 꺾쇠, 감시 머리글, 색이 어긋난 인광 로고(PixelLab). 고른 메뉴는 글자 폭만큼 색을 뒤집고 앞에 커서.
    띠·판·줄무늬로 감싸지 않는다. 11/27 사용자: 왼쪽 아래 발판과 주인공, 오른쪽 위 등 판은 지운다."""
    storm = _get_storm()
    phase = storm.phase()
    _draw_mist_background()
    if phase == 'flash':                                  # 번쩍: 미리 구운 대비 판 (흰 하늘, 검은 실루엣, 먼 하늘의 번갯줄기)
        assets.draw_image(assets.image(f'backgrounds/title_flash_{storm.flash_plate() + 1}.png'), W // 2, 0)
    elif phase == 'glow':                                 # 잔광: 조금 밝은 푸른 판을 옅게 덮어 원래대로
        assets.draw_image_tinted(assets.image('backgrounds/title_glow.png'), W // 2, 0, '', (255, 255, 255), storm.glow_alpha())
    elif storm.bolt_plate() is not None:                  # 번쩍이기 직전·두 깜빡임 사이: 어두운 하늘에 흰 번갯줄기 (대비 판과 같은 자리)
        assets.draw_image(assets.image(f'backgrounds/title_bolt_{storm.bolt_plate() + 1}.png'), W // 2, 0)
    _weather().draw()
    # 글자 뒤 어둠: 절반 크기 그림을 2배로 (빛 층 예외: 부드러운 알파). 대비 판일 때는 머리글·로고·메뉴 뒤 어둠을 뺀 시트
    # (11/27 L1: 흰 하늘 위에서 머리글 뒤 어둠이 회색 얼룩으로 보였다. R1: 로고 뒤 어둠도 둥근 회색 그늘로 보였다 ->
    #  대비 판에 로고 둘레 어두운 실루엣을 구웠고, 메뉴는 원래 검은 땅 실루엣 위다)
    shade = assets.image('light/title_shade_flash.png' if phase == 'flash' else 'light/title_shade.png')
    assets.draw_clip(shade, 0, 0, shade.w, shade.h, 0, 0, scale=2)
    mm.scanlines()
    mm.brackets()
    if phase == 'flash':                                  # R1: 흰 하늘 위 첫 줄은 번쩍이는 2~4프레임 동안 그리지 않는다 (글자와 그림자가 겹쳐
        hx, hy = mm.TERM_HEAD                             # 지저분했다. 어두운 한 색으로 그려 보니 들보 위 기둥 머리에 글자가 묻혔다). 둘째 줄은 검은 들보 위라 그대로
        kit.text(hx, hy - 26, 'CAM 04 · 제9구역 폐기물 슬럼 · REC', PH_DIM, small=True)
    else:
        mm.header([('TOWER SURVEILLANCE // INMATE N-09', PH), ('CAM 04 · 제9구역 폐기물 슬럼 · REC', PH_DIM)])
    assets.draw_image(assets.image('ui/um_logo_title.png'), W // 2, LOGO_Y)
    kit.text(W // 2, LOGO_Y - 28, '헤이즈', PH, center=True)
    for i, btn in enumerate(MENU):                        # 색 뒤집기: 글자 폭 + 양옆 8px만 (길게 뻗는 띠 아님)
        mm.pick(W // 2, btn.y + btn.h // 2, btn.label, i == selected, PH_MENU)
    kit.text(W - TERM_MARGIN, 60, VERSION, PH_DIM, small=True, right=True)


def _draw_mist_background():
    """감시 단말 배경 그림 (tools/make_ui_mist.py): 발판·주인공 없는 슬럼."""
    assets.draw_image(assets.image('backgrounds/title_mist.png'), W // 2, 0)


def draw_scene():
    """위에 쌓인 메뉴 화면(설정·키 설정, mist)이 깔 배경: 타이틀의 배경과 비만 (로고·메뉴·글자 뒤 어둠·번개 없이).
    번개는 설정 창이 떠 있는 동안 멈춰 있어서 (흰 대비 판에서 멈출 수 있다) 그리지 않는다."""
    if kit.is_mist():
        _draw_mist_background()
        _weather().draw()
        return
    draw_frozen()


def _draw_plate():
    """UI 3차 '교도소 철판' 제목 화면: 게임 속 슬럼 원경·중경·벽(구운 배경) + 게임의 비 + 주인공 대기 동작 + 스텐실 철판 로고 +
    철판 메뉴(고른 항목은 노란 꺾쇠와 띠). 새 일러스트를 쓰지 않는다 (docs/opus/TASKS.md 3차 O8-3)."""
    import sprites
    assets.draw_image(assets.image('backgrounds/title_plate.png'), W // 2, 0)     # tools/make_title_plate.py
    _weather().draw()
    n = int(age / config.IDLE_FRAME_TIME) % sprites.count('n09_idle') + 1
    sprites.draw('n09_idle', n, HERO_X, HERO_Y, 1)
    logo = assets.image(kit.art('logo_title.png'))
    assets.draw_image(logo, W // 2, LOGO_Y)
    x, y, w, h = MENU_PANEL
    kit.panel('panel', x, y, w, h)
    for i, b in enumerate(MENU):
        hot = i == selected
        b.draw(hot)
        if hot:
            tw = assets.text_width(b.label, False)
            kit.marker(W // 2 - tw // 2 - 46, b.y + b.h // 2)
    kit.text(W - 28, 30, VERSION, (138, 147, 163), small=True, right=True)


def draw_frozen():
    """제목 화면 (설정 창이 아래에 깔 때도 쓴다)."""
    if kit.is_mist():
        _draw_terminal()
        return
    if kit.is_plate():
        _draw_plate()
        return
    assets.draw_image(assets.image('backgrounds/screen_title.png'), W // 2, 0)   # Codex T16 제목 화면 일러스트
    assets.draw_image(assets.image('ui/logo_title.png'), W // 2, 588)          # 상점 로고(T29)를 1배로 (tools/make_store_art.py)
    for i, b in enumerate(MENU):
        b.draw(i == selected)
    kit.text(W - 28, 30, VERSION, (140, 155, 185), small=True, right=True)   # 조작은 일시정지·설정에서 (제목 화면은 비워 둔다)


def draw():
    clear_canvas()
    draw_frozen()
    import transition
    transition.draw()                              # 화면 전환 점묘 (계획 4-3, 가장 위)
    update_canvas()
