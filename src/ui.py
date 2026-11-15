"""화면 UI: 헤이즈 게이지 바, 대시 슬롯, 디버그 정보. (임시 도형 기반, 실제 UI 에셋은 이후 교체)"""
import assets
import config
import game_world
from haze_gauge import AWAKE, CRITICAL, DEAD, FADE, NORMAL, OVERLOAD

ZONE_LABEL = {FADE: '페이드', NORMAL: '노멀', AWAKE: '각성', CRITICAL: '위험', OVERLOAD: '오버로드', DEAD: '사망'}
ZONE_COLOR = {FADE: (225, 70, 80), NORMAL: (110, 150, 220), AWAKE: (90, 210, 240),
              CRITICAL: (240, 150, 60), OVERLOAD: (250, 220, 90), DEAD: (225, 70, 80)}

BAR_X, BAR_Y, BAR_W, BAR_H = 510, config.SCREEN_H - 60, 900, 30


def _rect(name, x, y, w, h):
    """왼쪽 아래 (x, y) 기준으로 단색 사각형을 그린다."""
    if w > 0:
        assets.draw_rect_image(assets.image('placeholder/' + name + '.png'), x, y, w, h)


class GameUI:
    def __init__(self, player, stage=None):
        self.player = player
        self.stage = stage

    def update(self, dt):
        pass

    def draw(self):
        self._draw_gauge()
        self._draw_dash_slots()
        if self.stage is not None:
            self._draw_minimap()
            self._draw_room_notice()
        if config.DEBUG:
            self._draw_debug()

    def _x_of(self, value):
        return BAR_X + BAR_W * min(value, self.player.gauge.cap) / self.player.gauge.cap

    def _draw_gauge(self):
        g = self.player.gauge
        _rect('px_black', BAR_X - 4, BAR_Y - 4, BAR_W + 8, BAR_H + 8)
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
        _rect('px_white', self._x_of(g.value) - 3, BAR_Y - 9, 6, BAR_H + 18)
        label = f'{ZONE_LABEL[g.zone]} {int(g.value)}%'
        if g.enhanced:
            label += f'  강화 {g.enhance_timer:.1f}s'
        assets.draw_text(BAR_X, BAR_Y - 30, label, ZONE_COLOR[g.zone])

    def _draw_dash_slots(self):
        p = self.player
        for i in range(p.dash_max):
            name = 'px_cyan' if i < p.dash_slots else 'px_gray'
            _rect(name, 60 + i * 39, config.SCREEN_H - 87, 30, 21)
        # 체력 바
        hp_w = 234
        _rect('px_black', 56, config.SCREEN_H - 128, hp_w + 8, 24)
        _rect('px_gray', 60, config.SCREEN_H - 124, hp_w, 16)
        _rect('px_red', 60, config.SCREEN_H - 124, hp_w * p.hp / config.PLAYER_HP, 16)
        assets.draw_text(60, config.SCREEN_H - 148, f'HP {p.hp}/{config.PLAYER_HP}', (235, 240, 250))
        assets.draw_text(60, config.SCREEN_H - 172, f'헤이즈 조각 {p.shards}', (130, 235, 225), small=True)
        if p.stunned:
            assets.draw_text(config.SCREEN_W // 2, config.SCREEN_H - 150, '오버로드! 기절', ZONE_COLOR[OVERLOAD], center=True)

    def _draw_minimap(self):
        """오른쪽 위 미니맵: 방문한 방과 이웃 방. 현재 방은 흰색, 클리어한 방은 청록, 고농도 방은 주황 테두리."""
        cell_w, cell_h, gap = 36, 24, 6
        base_x, base_y = config.SCREEN_W - 70 - 3 * (cell_w + gap), config.SCREEN_H - 150
        colors = {'current': 'px_white', 'cleared': 'px_cyan', 'visited': 'px_blue', 'unknown': 'px_gray'}
        for (cx, cy), state, high in self.stage.minimap_cells():
            x = base_x + cx * (cell_w + gap)
            y = base_y + cy * (cell_h + gap)
            _rect('px_orange' if high else 'px_black', x - 3, y - 3, cell_w + 6, cell_h + 6)
            _rect(colors[state], x, y, cell_w, cell_h)
        assets.draw_text(base_x, base_y + 40, '지도', (170, 185, 210), small=True)

    def _draw_room_notice(self):
        import play_mode  # 방 클리어 안내 시간은 play_mode가 갖고 있다
        if play_mode.clear_notice > 0:
            goal = self.stage.layout[self.stage.coord].get('goal')
            text = '탈출구가 열렸다 ->' if goal else '방 클리어! 오른쪽 문이 열렸다 ->'
            assets.draw_text(config.SCREEN_W // 2, config.SCREEN_H - 150, text, (170, 230, 250), center=True)
        elif self.stage.room.locked:
            assets.draw_text(config.SCREEN_W // 2, config.SCREEN_H - 150, f'적을 모두 처치하라 ({self.stage.enemy_count()})',
                             (240, 140, 150), center=True)
        if self.stage.room.is_high_haze:
            assets.draw_text(config.SCREEN_W // 2, config.SCREEN_H - 176, '고농도 방: 헤이즈가 계속 차오른다', (130, 235, 225),
                             small=True, center=True)

    def _draw_debug(self):
        p = self.player
        lines = [
            f'상태 {p.state}  점프 {p.jump_count}/{config.MAX_JUMPS}  바닥 {p.on_ground}',
            f'위치 ({p.x:.0f}, {p.y:.0f})  속도 ({p.vx:.0f}, {p.vy:.0f})',
            f'대시 {p.dash_slots}/{p.dash_max}  충전 {p.dash_charge:.2f}s',
            'F1 디버그  F3 게이지+10  F4 게이지-10  F5 적 재생성  H 피격  Esc 일시정지',
        ]
        for i, text in enumerate(lines):
            assets.draw_text(60, config.SCREEN_H - 205 - i * 18, text, (255, 240, 120), small=True)
