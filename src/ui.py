"""화면 UI: 헤이즈 게이지 바, 대시 슬롯, 디버그 정보. (임시 도형 기반, 실제 UI 에셋은 이후 교체)"""
import assets
import config
from haze_gauge import AWAKE, CRITICAL, DEAD, FADE, NORMAL, OVERLOAD

ZONE_LABEL = {FADE: '페이드', NORMAL: '노멀', AWAKE: '각성', CRITICAL: '위험', OVERLOAD: '오버로드', DEAD: '사망'}
ZONE_COLOR = {FADE: (225, 70, 80), NORMAL: (110, 150, 220), AWAKE: (90, 210, 240),
              CRITICAL: (240, 150, 60), OVERLOAD: (250, 220, 90), DEAD: (225, 70, 80)}

BAR_X, BAR_Y, BAR_W, BAR_H = 340, config.SCREEN_H - 40, 600, 20


def _rect(name, x, y, w, h):
    """왼쪽 아래 (x, y) 기준으로 단색 사각형을 그린다."""
    if w > 0:
        assets.draw_rect_image(assets.image('placeholder/' + name + '.png'), x, y, w, h)


class GameUI:
    def __init__(self, player):
        self.player = player

    def update(self, dt):
        pass

    def draw(self):
        self._draw_gauge()
        self._draw_dash_slots()
        if config.DEBUG:
            self._draw_debug()

    def _x_of(self, value):
        return BAR_X + BAR_W * min(value, self.player.gauge.cap) / self.player.gauge.cap

    def _draw_gauge(self):
        g = self.player.gauge
        _rect('px_black', BAR_X - 3, BAR_Y - 3, BAR_W + 6, BAR_H + 6)
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
        _rect('px_white', self._x_of(g.value) - 2, BAR_Y - 6, 4, BAR_H + 12)
        label = f'{ZONE_LABEL[g.zone]} {int(g.value)}%'
        if g.enhanced:
            label += f'  강화 {g.enhance_timer:.1f}s'
        assets.draw_text(BAR_X, BAR_Y - 24, label, ZONE_COLOR[g.zone])

    def _draw_dash_slots(self):
        p = self.player
        for i in range(p.dash_max):
            name = 'px_cyan' if i < p.dash_slots else 'px_gray'
            _rect(name, 40 + i * 26, config.SCREEN_H - 58, 20, 14)
        assets.draw_text(40, config.SCREEN_H - 82, f'HP {p.hp}', (235, 240, 250))

    def _draw_debug(self):
        p = self.player
        lines = [
            f'상태 {p.state}  점프 {p.jump_count}/{config.MAX_JUMPS}  바닥 {p.on_ground}',
            f'위치 ({p.x:.0f}, {p.y:.0f})  속도 ({p.vx:.0f}, {p.vy:.0f})',
            f'대시 {p.dash_slots}/{p.dash_max}  충전 {p.dash_charge:.2f}s',
            'F1 디버그  F3 게이지+10  F4 게이지-10  H 피격  Esc 일시정지',
        ]
        for i, text in enumerate(lines):
            assets.draw_text(40, config.SCREEN_H - 110 - i * 16, text, (255, 240, 120), small=True)
