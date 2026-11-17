"""화면 UI: 헤이즈 게이지, 체력, 대시 슬롯, 무기·공격 패널, 조준점, 미니맵, 안내 문구.

1920x1080에서 잘 보이도록 글자는 갈무리 14/11px의 2배(28/22px)로 그린다 (assets.draw_text).
틀은 크기가 변하므로 사각형으로 입체 테두리를 그리고(_frame), 모양이 있는 조각(게이지 장식·바늘, 대시·콤보 칸,
조준점, 미니맵 아이콘)은 tools/make_hud.py가 만든 assets/ui/hud_*.png를 1배로 그린다.
색만으로 뜻을 전하지 않는다(game-ui-ux 지침): 구간은 이름, 방 종류는 아이콘, 콤보 마무리는 모양으로도 구분한다.
"""
import assets
import camera
import config
import effects
import items
from haze_gauge import AWAKE, CRITICAL, DEAD, FADE, NORMAL, OVERLOAD

ZONE_LABEL = {FADE: '페이드', NORMAL: '노멀', AWAKE: '각성', CRITICAL: '위험', OVERLOAD: '오버로드', DEAD: '사망'}
ZONE_COLOR = {FADE: (225, 70, 80), NORMAL: (110, 150, 220), AWAKE: (90, 210, 240),
              CRITICAL: (240, 150, 60), OVERLOAD: (250, 220, 90), DEAD: (225, 70, 80)}

BAR_W, BAR_H = 960, 36
BAR_X, BAR_Y = (config.SCREEN_W - BAR_W) // 2, config.SCREEN_H - 78
WHITE = (235, 240, 250)
TEAL = (130, 235, 225)
DIM = (150, 165, 190)


def _rect(name, x, y, w, h):
    """왼쪽 아래 (x, y) 기준으로 단색 사각형을 그린다."""
    if w > 0:
        assets.draw_rect_image(assets.image('placeholder/' + name + '.png'), x, y, w, h)


BAND = {'px_black': (58, 74, 108), 'px_gray': (86, 108, 150), 'px_white': (234, 255, 255)}   # 테두리 띠 색


def _frame(x, y, w, h, fill, border='px_black', thickness=4):
    """입체 테두리 틀: 바깥 외곽선, 강철 띠(위는 밝고 아래는 어둡다), 안쪽 외곽선, 속."""
    t = thickness
    _rect('px_black', x - t, y - t, w + t * 2, h + t * 2)
    if t >= 3:
        r, g, b = BAND.get(border, BAND['px_black'])
        ow, oh = w + t * 2 - 2, h + t * 2 - 2
        assets.draw_rect_color(x - t + 1, y - t + 1, ow, oh, (r, g, b))
        assets.draw_rect_color(x - t + 1, y + h + t - 2, ow, 1, (min(255, r + 70), min(255, g + 70), min(255, b + 64)))   # 윗변 빛
        assets.draw_rect_color(x - t + 1, y - t + 1, ow, 1, (r // 2, g // 2, b // 2))                                    # 아랫변 그늘
        _rect('px_black', x - 1, y - 1, w + 2, h + 2)
    else:
        _rect(border, x - t + 1, y - t + 1, w + t * 2 - 2, h + t * 2 - 2)
    _rect(fill, x, y, w, h)


def _icon(name, x, y):
    """assets/ui/hud_<name>.png를 왼쪽 아래 (x, y)에 1배로 그린다."""
    img = assets.image(f'ui/hud_{name}.png')
    assets.draw_image(img, x + img.w // 2, y)


class GameUI:
    def __init__(self, player, stage=None):
        self.player = player
        self.stage = stage

    def update(self, dt):
        pass

    def draw(self):
        self._draw_screen_fx()          # 화면 전체 효과(오버로드 섬광, 기절 비네트)는 HUD 아래에 깐다
        self._draw_gauge()
        self._draw_status()
        self._draw_weapon_panel()
        if self.stage is not None:
            self._draw_minimap()
            self._draw_room_notice()
            self._draw_boss_bar()
            self._draw_message()
        self._draw_reticle()
        if config.DEBUG:
            self._draw_debug()

    # ----- 화면 전체 효과 (오버로드 / 기절) -----
    def _draw_screen_fx(self):
        import math
        p = self.player
        W, H = config.SCREEN_W, config.SCREEN_H
        if effects.flash_left > 0:                              # 오버로드 순간: 화면 전체가 하얗게 번쩍였다가 가라앉는다
            a = min(1.0, effects.flash_left / config.OVERLOAD_FLASH) ** 1.6
            assets.draw_rect_color(0, 0, W, H, (255, 255, 255), 0.9 * a)
        if not p.stunned:
            return
        t = p.aura_time
        pulse = 0.5 + 0.5 * math.sin(t * 14)                    # 맥동
        assets.draw_rect_color(0, 0, W, H, (255, 150, 60), 0.06 + 0.05 * pulse)      # 화면 전체 주황 틴트
        for i in range(6):                                      # 가장자리 붉은 비네트: 안쪽으로 갈수록 옅다 (계단식)
            inset, thick = i * 26, 26
            a = 0.34 * (1 - i / 6) * (0.65 + 0.35 * pulse)
            c = (255, 70, 50)
            assets.draw_rect_color(0, H - inset - thick, W, thick, c, a)                  # 위
            assets.draw_rect_color(0, inset, W, thick, c, a)                              # 아래
            assets.draw_rect_color(inset, 0, thick, H, c, a)                              # 왼쪽
            assets.draw_rect_color(W - inset - thick, 0, thick, H, c, a)                  # 오른쪽
        seed = int(t * 20)                                      # 전기 노이즈 줄: 20Hz로 자리가 바뀌는 얇은 가로줄
        for k in range(7):
            y = (seed * 97 + k * 163) % H
            assets.draw_rect_color(0, y, W, 3 + ((seed + k) % 3) * 2, (255, 242, 170), 0.15)
        shake = int(round(4 * math.sin(t * 70)))
        assets.draw_text(W // 2 + shake, H - 215, '오버로드!', (255, 235, 120), center=True, big=True)

    # ----- 게이지 -----
    def _x_of(self, value):
        return BAR_X + BAR_W * min(value, self.player.gauge.cap) / self.player.gauge.cap

    def _draw_gauge(self):
        g = self.player.gauge
        if g.zone in (FADE, CRITICAL):                           # 양끝 위험 구간: 게이지 둘레가 맥박처럼 깜빡인다
            import math
            pulse = 0.35 + 0.35 * math.sin(self.player.aura_time * (9 if g.zone == CRITICAL else 6))
            assets.draw_rect_color(BAR_X - 12, BAR_Y - 12, BAR_W + 24, BAR_H + 24, ZONE_COLOR[g.zone], max(0.0, pulse))
        _frame(BAR_X, BAR_Y, BAR_W, BAR_H, 'px_gray', thickness=5)
        # 구간 띠 (페이드 / 노멀 / 각성 / 위험)
        bounds = [(0, config.ZONE_FADE_MAX, 'px_red'), (config.ZONE_FADE_MAX, config.ZONE_NORMAL_MAX, 'px_blue'),
                  (config.ZONE_NORMAL_MAX, g.cap - config.CRITICAL_MARGIN, 'px_cyan'),
                  (g.cap - config.CRITICAL_MARGIN, g.cap, 'px_orange')]
        for lo, hi, name in bounds:
            x0, x1 = self._x_of(lo), self._x_of(hi)
            _rect('px_gray', x0, BAR_Y, x1 - x0, BAR_H)
            fill = min(g.value, hi) - lo
            if fill > 0:
                _rect(name, x0, BAR_Y, self._x_of(lo + fill) - x0, BAR_H)
        for lo, _hi, _name in bounds[1:]:                        # 구간 경계 눈금
            _rect('px_black', self._x_of(lo) - 1, BAR_Y, 3, BAR_H)
        assets.draw_rect_color(BAR_X, BAR_Y + BAR_H - 5, BAR_W, 5, (255, 255, 255), 0.22)   # 유리 같은 윗면 빛
        assets.draw_rect_color(BAR_X, BAR_Y, BAR_W, 6, (11, 16, 32), 0.30)                  # 아랫면 그늘
        _icon('gauge_cap_l', BAR_X - 40, BAR_Y - 14)
        _icon('gauge_cap_r', BAR_X + BAR_W, BAR_Y - 14)
        _icon('marker', self._x_of(g.value) - 12, BAR_Y - 18)        # 현재 값 바늘
        assets.draw_rect_color(BAR_X - 6, BAR_Y - 50, BAR_W + 12, 40, (11, 16, 32), 0.55)     # 글자 받침 (밝은 벽 위에서도 읽히게)
        label = f'{ZONE_LABEL[g.zone]} {int(g.value)}%'
        if g.enhanced:
            label += '   강화 일격 준비'
        assets.draw_text(BAR_X, BAR_Y - 34, label, ZONE_COLOR[g.zone])
        mult = g.zone_multipliers()
        text = f'공격력 x{mult["attack"]:g}  이동 x{mult["speed"]:g}'
        assets.draw_text(BAR_X + BAR_W - assets.text_width(text, True), BAR_Y - 32, text, DIM, small=True)

    # ----- 체력·대시·조각 -----
    def _draw_status(self):
        p = self.player
        top = config.SCREEN_H - 90
        rows = 3 if p.items else 2
        assets.draw_rect_color(24, top - 76 - rows * 66 + 60, 470, 60 + rows * 66, (11, 16, 32), 0.50)   # 왼쪽 위 상태 묶음의 받침
        for i in range(p.dash_max):
            _icon('dash_on' if i < p.dash_slots else 'dash_off', 66 + i * 50, top - 2)
        hp_w, hp_h = int(380 * p.max_hp / config.PLAYER_HP), 30
        y = top - 70
        _frame(70, y, hp_w, hp_h, 'px_gray')
        _rect('px_red', 70, y, hp_w * p.hp / p.max_hp, hp_h)
        assets.draw_rect_color(70, y + hp_h - 5, hp_w, 5, (255, 255, 255), 0.20)
        assets.draw_rect_color(70, y, hp_w, 5, (11, 16, 32), 0.30)
        _icon('heart', 34, y + 1)
        assets.draw_text(70 + 12, y + hp_h // 2, f'HP {p.hp}/{p.max_hp}', WHITE, small=True)
        assets.draw_image(assets.image('ui/icon_shard.png'), 70 + 24, y - 62)                        # 조각 아이콘
        assets.draw_text(126, y - 40, f'헤이즈 조각 {p.shards}', TEAL)
        # 가진 아이템: 색 칸에 한 글자 (같은 아이템을 여러 번 얻으면 개수)
        counts = {}
        for item_id in p.items:
            counts[item_id] = counts.get(item_id, 0) + 1
        for i, (item_id, n) in enumerate(counts.items()):
            ix = 70 + i * 60
            _frame(ix, y - 136, 54, 54, 'px_black', border='px_gray', thickness=3)
            assets.draw_image(assets.image(f'ui/icon_{item_id}.png'), ix + 27, y - 133)              # 아이템 아이콘
            if n > 1:
                assets.draw_text(ix + 50, y - 128, f'x{n}', WHITE, small=True, center=True)
        if p.stunned:                                           # 기절 남은 시간 바
            w = 420
            bx, by = (config.SCREEN_W - w) // 2, config.SCREEN_H - 300
            _frame(bx, by, w, 18, 'px_gray', border='px_black', thickness=4)
            _rect('px_yellow', bx, by, w * p.gauge.stun_timer / config.OVERLOAD_STUN, 18)
            assets.draw_text(config.SCREEN_W // 2, by + 44, f'기절 {p.gauge.stun_timer:.1f}s', (255, 240, 150), small=True,
                             center=True)

    # ----- 무기·공격 패널 (아래 가운데) -----
    def _draw_weapon_panel(self):
        p = self.player
        w = p.weapon
        g = p.gauge
        px, py, pw, ph = (config.SCREEN_W - 980) // 2, 14, 980, 92   # 이름·공격 종류 | 콤보 | E 강화 (글자가 겹치지 않는 너비)
        _frame(px, py, pw, ph, 'px_black', border='px_gray', thickness=3)
        assets.draw_text(px + 24, py + ph - 26, '철파이프', WHITE)
        kind = w.current_kind()
        names = {'pipe': ('기본 3연타', DIM), 'dash': ('대시 평타: 지나온 길 베기', (255, 225, 120)),
                 'spin': ('점프 평타: 회전 베기', (170, 225, 255)), 'plunge': ('내려찍기', (170, 225, 255))}
        text, color = names[kind]
        if g.enhanced:                                   # 강화는 지금 나가는 공격에 얹힌다
            text, color = '강화 ' + text.split(':')[0], (225, 190, 255)
        assets.draw_text(px + 24, py + 24, text, color, small=True)
        # 콤보 3칸: 이어 칠수록 켜지고 3타(마무리)는 주황
        for i in range(3):
            lit = i < w.combo
            _icon(('combo_fin' if i == 2 else 'combo_on') if lit else 'combo_off', px + 388 + i * 56, py + 28)
        # 다음 공격까지 재충전 바
        cool = config.PIPE_COOLDOWN[max(0, w.combo - 1)]
        ratio = 1.0 if w.ready else 1.0 - w.cooldown / cool
        _frame(px + 390, py + 10, 164, 10, 'px_gray', border='px_black', thickness=2)
        _rect('px_white' if w.ready else 'px_yellow', px + 390, py + 10, 164 * ratio, 10)
        # E 강화 상태
        ex = px + 610
        if g.enhanced:                                           # 강화 일격 준비 (1회성): 바는 준비가 풀리기까지 남은 시간
            _frame(ex, py + 30, 340, 40, 'px_gray', border='px_white', thickness=3)
            _rect('px_cyan', ex, py + 30, 340 * g.enhance_timer / config.ENHANCE_TIME, 40)
            assets.draw_text(ex + 12, py + 50, '강화 일격 준비!', (10, 20, 40), small=True)
        elif g.can_enhance():
            _frame(ex, py + 30, 340, 40, 'px_cyan', border='px_white', thickness=3)
            _icon('key_e', ex + 6, py + 30)
            assets.draw_text(ex + 54, py + 50, f'강화 일격 준비 (-{config.ENHANCE_COST}%)', (10, 20, 40), small=True)
        else:
            _frame(ex, py + 30, 340, 40, 'px_gray', border='px_black', thickness=3)
            assets.draw_text(ex + 12, py + 50, f'E 강화: 게이지 {g.enhance_min}%+', DIM, small=True)

    # ----- 조준점 -----
    def _draw_reticle(self):
        p = self.player
        x, y = p.mouse_screen if p.mouse_screen is not None else camera.to_screen(p.mouse_x, p.mouse_y)
        x, y = int(x), int(y)
        _icon('reticle_ready' if p.weapon.ready else 'reticle_wait', x - 28, y - 28)

    # ----- 미니맵 -----
    def _draw_minimap(self):
        """오른쪽 위 미니맵: 방문한 방과 이웃 방. 현재 방은 흰색, 클리어한 방은 청록, 고농도 방은 주황 테두리."""
        cell_w, cell_h, gap = 40, 26, 8
        cells = self.stage.minimap_cells()
        xs = [c[0][0] for c in cells]
        ys = [c[0][1] for c in cells]
        right = config.SCREEN_W - 80
        base_x = right - (max(xs) - min(xs) + 1) * (cell_w + gap)
        base_y = config.SCREEN_H - 110 - (max(ys) - min(ys)) * (cell_h + gap)
        colors = {'current': 'px_white', 'cleared': 'px_cyan', 'visited': 'px_blue', 'unknown': 'px_gray'}
        kind_border = {'gold': 'px_yellow', 'boss': 'px_red', 'shop': 'px_blue'}
        for (cx, cy), state, kind, high in cells:
            x = base_x + (cx - min(xs)) * (cell_w + gap)
            y = base_y + (cy - min(ys)) * (cell_h + gap)
            border = kind_border.get(kind, 'px_orange' if high else 'px_black')
            _rect('px_black', x - 5, y - 5, cell_w + 10, cell_h + 10)
            _rect(border, x - 4, y - 4, cell_w + 8, cell_h + 8)
            _rect(colors[state], x, y, cell_w, cell_h)
            mark = kind if kind in kind_border else 'haze' if high else None
            if mark:                                             # 방 종류는 색 테두리와 함께 아이콘으로도 알려 준다
                _icon('map_' + mark, x + cell_w // 2 - 10, y + cell_h // 2 - 8)
        legend = '지도: 별 황금방 / 렌치 정비방 / 뿔 보스'
        lw = assets.text_width(legend, True)
        assets.draw_rect_color(right - lw - 10, base_y - 50, lw + 20, 32, (11, 16, 32), 0.55)
        assets.draw_text(right - assets.text_width(legend, True), base_y - 34, legend, DIM, small=True)

    def _draw_room_notice(self):
        import play_mode  # 방 클리어 안내 시간은 play_mode가 갖고 있다
        cx = config.SCREEN_W // 2
        if play_mode.clear_notice > 0:
            text = '방 클리어! 열린 문으로 이동하라'
            assets.draw_text(cx, config.SCREEN_H - 175, text, (170, 230, 250), center=True)
        elif self.stage.room.locked:
            assets.draw_text(cx, config.SCREEN_H - 175, f'적을 모두 처치하라 ({self.stage.enemy_count()})', (240, 140, 150),
                             center=True)
        if self.stage.room.is_high_haze:
            assets.draw_text(cx, config.SCREEN_H - 212, '고농도 방: 헤이즈가 계속 차오른다', TEAL, small=True, center=True)

    def _draw_boss_bar(self):
        boss = self.stage.boss
        if boss is None or not boss.alive:
            return
        w = 900
        x = (config.SCREEN_W - w) // 2
        y = config.SCREEN_H - 290   # 위쪽 게이지와 안내 문구 아래 (아래쪽은 싸움이 벌어지는 바닥이라 가린다)
        _frame(x, y, w, 26, 'px_gray', border='px_black', thickness=5)
        _rect('px_red', x, y, w * max(0.0, boss.hp) / boss.max_hp, 26)
        assets.draw_text(config.SCREEN_W // 2, y + 56, '크래셔', (255, 150, 150), center=True)

    def _draw_message(self):
        import play_mode
        if play_mode.message_time > 0:
            assets.draw_text(config.SCREEN_W // 2, 300, play_mode.message, (255, 240, 150), center=True)

    def _draw_debug(self):
        p = self.player
        lines = [
            f'상태 {p.state}  점프 {p.jump_count}/{config.MAX_JUMPS}  바닥 {p.on_ground}',
            f'위치 ({p.x:.0f}, {p.y:.0f})  속도 ({p.vx:.0f}, {p.vy:.0f})',
            f'대시 {p.dash_slots}/{p.dash_max}  충전 {p.dash_charge:.2f}s',
            'F1 디버그  F3 게이지+10  F4 게이지-10  F5 방 재시작  H 피격  Esc 일시정지',
        ]
        for i, text in enumerate(lines):
            assets.draw_text(70, config.SCREEN_H - 300 - i * 30, text, (255, 240, 120), small=True)
