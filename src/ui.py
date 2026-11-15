"""화면 UI: 헤이즈 게이지, 체력, 대시 슬롯, 무기·공격 패널, 조준점, 미니맵, 안내 문구.

1920x1080에서 잘 보이도록 글자는 갈무리 14/11px의 2배(28/22px)로 그린다 (assets.draw_text).
바는 단색 칸(placeholder/px_*.png)을 정수 좌표로 채워서 그린다. 실제 UI 에셋은 이후 교체.
"""
import assets
import camera
import config
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


def _frame(x, y, w, h, fill, border='px_black', thickness=4):
    _rect(border, x - thickness, y - thickness, w + thickness * 2, h + thickness * 2)
    _rect(fill, x, y, w, h)


class GameUI:
    def __init__(self, player, stage=None):
        self.player = player
        self.stage = stage

    def update(self, dt):
        pass

    def draw(self):
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

    # ----- 게이지 -----
    def _x_of(self, value):
        return BAR_X + BAR_W * min(value, self.player.gauge.cap) / self.player.gauge.cap

    def _draw_gauge(self):
        g = self.player.gauge
        _rect('px_black', BAR_X - 5, BAR_Y - 5, BAR_W + 10, BAR_H + 10)
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
        # 현재 값 표시선
        _rect('px_white', self._x_of(g.value) - 4, BAR_Y - 11, 8, BAR_H + 22)
        label = f'{ZONE_LABEL[g.zone]} {int(g.value)}%'
        if g.enhanced:
            label += f'   강화 {g.enhance_timer:.1f}s'
        assets.draw_text(BAR_X, BAR_Y - 34, label, ZONE_COLOR[g.zone])
        mult = g.zone_multipliers()
        text = f'공격력 x{mult["attack"]:g}  이동 x{mult["speed"]:g}'
        assets.draw_text(BAR_X + BAR_W - assets.text_width(text, True), BAR_Y - 32, text, DIM, small=True)

    # ----- 체력·대시·조각 -----
    def _draw_status(self):
        p = self.player
        top = config.SCREEN_H - 90
        for i in range(p.dash_max):
            _frame(70 + i * 62, top, 48, 30, 'px_cyan' if i < p.dash_slots else 'px_gray')
        hp_w, hp_h = int(380 * p.max_hp / config.PLAYER_HP), 30
        y = top - 70
        _frame(70, y, hp_w, hp_h, 'px_gray')
        _rect('px_red', 70, y, hp_w * p.hp / p.max_hp, hp_h)
        assets.draw_text(70 + 12, y + hp_h // 2, f'HP {p.hp}/{p.max_hp}', WHITE, small=True)
        assets.draw_text(70, y - 40, f'헤이즈 조각 {p.shards}', TEAL)
        # 가진 아이템: 색 칸에 한 글자 (같은 아이템을 여러 번 얻으면 개수)
        counts = {}
        for item_id in p.items:
            counts[item_id] = counts.get(item_id, 0) + 1
        for i, (item_id, n) in enumerate(counts.items()):
            ix = 70 + i * 54
            info = items.ITEMS[item_id]
            _frame(ix, y - 112, 44, 44, 'px_black', border='px_gray', thickness=3)
            assets.draw_text(ix + 22, y - 90, info['glyph'], info['color'], center=True)
            if n > 1:
                assets.draw_text(ix + 40, y - 106, f'x{n}', WHITE, small=True, center=True)
        if p.stunned:
            assets.draw_text(config.SCREEN_W // 2, config.SCREEN_H - 200, '오버로드! 기절', ZONE_COLOR[OVERLOAD], big=True,
                             center=True)

    # ----- 무기·공격 패널 (아래 가운데) -----
    def _draw_weapon_panel(self):
        p = self.player
        w = p.weapon
        g = p.gauge
        px, py, pw, ph = (config.SCREEN_W - 760) // 2, 14, 760, 92
        _frame(px, py, pw, ph, 'px_black', border='px_gray', thickness=3)
        assets.draw_text(px + 24, py + ph - 26, '철파이프', WHITE)
        assets.draw_text(px + 24, py + 24, '좌클릭 공격', DIM, small=True)
        # 콤보 3칸: 이어 칠수록 켜지고 3타(마무리)는 주황
        for i in range(3):
            lit = i < w.combo
            name = ('px_orange' if i == 2 else 'px_white') if lit else 'px_gray'
            _frame(px + 230 + i * 56, py + 30, 44, 40, name, border='px_black', thickness=3)
        # 다음 공격까지 재충전 바
        cool = config.PIPE_COOLDOWN[max(0, w.combo - 1)]
        ratio = 1.0 if w.ready else 1.0 - w.cooldown / cool
        _frame(px + 230, py + 10, 164, 10, 'px_gray', border='px_black', thickness=2)
        _rect('px_white' if w.ready else 'px_yellow', px + 230, py + 10, 164 * ratio, 10)
        # E 강화 상태
        ex = px + 450
        if g.enhanced:
            _frame(ex, py + 30, 270, 40, 'px_gray', border='px_black', thickness=3)
            _rect('px_cyan', ex, py + 30, 270 * g.enhance_timer / config.ENHANCE_TIME, 40)
            assets.draw_text(ex + 12, py + 50, f'E 강화 중 {g.enhance_timer:.1f}s', (10, 20, 40), small=True)
        elif g.can_enhance():
            _frame(ex, py + 30, 270, 40, 'px_cyan', border='px_white', thickness=3)
            assets.draw_text(ex + 12, py + 50, f'E 강화 가능 (-{config.ENHANCE_COST}%)', (10, 20, 40), small=True)
        else:
            _frame(ex, py + 30, 270, 40, 'px_gray', border='px_black', thickness=3)
            assets.draw_text(ex + 12, py + 50, f'E 강화: 게이지 {g.enhance_min}%+', DIM, small=True)

    # ----- 조준점 -----
    def _draw_reticle(self):
        p = self.player
        x, y = p.mouse_screen if p.mouse_screen is not None else camera.to_screen(p.mouse_x, p.mouse_y)
        x, y = int(x), int(y)
        arms = ((-22, -2, 14, 4), (8, -2, 14, 4), (-2, 8, 4, 14), (-2, -22, 4, 14))  # 십자 네 팔
        color = 'px_white' if p.weapon.ready else 'px_gray'
        for dx, dy, w, h in arms:
            _rect('px_black', x + dx - 2, y + dy - 2, w + 4, h + 4)
        for dx, dy, w, h in arms:
            _rect(color, x + dx, y + dy, w, h)

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
            _rect(border, x - 4, y - 4, cell_w + 8, cell_h + 8)
            _rect(colors[state], x, y, cell_w, cell_h)
        legend = '지도: 황금 노랑 / 정비 파랑 / 보스 빨강'
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
        y = 150
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
