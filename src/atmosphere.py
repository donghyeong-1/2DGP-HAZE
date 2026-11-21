"""화면 분위기: 게이지 구간 색, 가장자리 어둡게(비네트), 흐르는 안개. 세계 위·HUD 아래에 화면 좌표로 그린다.
(2026-11-21 퀄리티 계획 2-2, 그림은 tools/make_atmosphere.py)

- 게이지 구간이 화면 색으로도 읽힌다: 페이드 차갑고 어둡게, 각성 옅은 청록, 위험 붉게 맥동, 강화 준비 보라.
  목표 색으로 부드럽게 바뀐다(한 프레임에 확 바뀌지 않는다).
- 비네트: 페이드일수록, 헤이즈가 짙은 방일수록 진하다.
- 안개: 두 겹이 카메라와 시간에 따라 다른 빠르기로 흐른다(시차). 짙은 방은 진하게, 은신처는 없다.
번쩍임 줄이기(접근성)를 켜면 위험 구간의 맥동을 멈춘다.
- (11/21) 구간이 바뀌는 순간 그 구간 색으로 화면이 잠깐 번쩍이고, 체력이 낮으면 가장자리가 붉게 심장 박자로 맥동한다(drama).
"""
import math

import assets
import camera
import config
import options

EASE = 4.0                     # 목표 색으로 다가가는 빠르기(1/초)
TINTS = {'FADE': ((70, 90, 140), 0.16), 'AWAKE': ((60, 200, 190), 0.05), 'CRITICAL': ((255, 80, 50), 0.07)}
ENHANCED_TINT = ((170, 110, 255), 0.07)
CRITICAL_PULSE = 0.05          # 위험 구간 맥동 폭 (2Hz)


def target_tint(zone, enhanced, t):
    """구간·강화 준비·시간 -> (색, 투명도). 노멀은 색이 없다."""
    if enhanced:
        return ENHANCED_TINT
    color, alpha = TINTS.get(zone, ((0, 0, 0), 0.0))
    if zone == 'CRITICAL' and not options.reduce_flash:
        alpha += CRITICAL_PULSE * (0.5 + 0.5 * math.sin(t * math.tau * 2))
    return color, alpha


def fog_strength(stage_name, high_haze):
    if stage_name == 'hideout':
        return 0.0
    return 0.5 if high_haze else 0.22


def vignette_strength(zone, high_haze):
    base = 0.9 if zone in ('FADE', 'DEAD') else 0.55
    return min(1.0, base + (0.2 if high_haze else 0.0))


class Atmosphere:
    def __init__(self, player, stage):
        self.player, self.stage = player, stage
        self.color, self.alpha, self.time = (0, 0, 0), 0.0, 0.0

    def ease(self, zone, enhanced, dt):
        self.time += dt
        color, alpha = target_tint(zone, enhanced, self.time)
        k = min(1.0, EASE * dt)
        if self.alpha <= 0.001:                          # 색이 없던 상태면 색은 바로 바꾸고 진하기만 천천히
            self.color = color
        elif alpha > 0:
            self.color = tuple(c + (t - c) * k for c, t in zip(self.color, color))
        self.alpha += (alpha - self.alpha) * k

    def update(self, dt):
        g = self.player.gauge
        self.ease(g.zone, g.enhanced, dt)

    def draw(self):
        W, H = config.SCREEN_W, config.SCREEN_H
        room = self.stage.room
        high = bool(getattr(room, 'is_high_haze', False))
        fog = fog_strength(getattr(self.stage, 'name', ''), high)
        if fog > 0:
            img = assets.image('backgrounds/fog_strip.png')
            cx, _ = camera.offset()
            for speed, drift, y, k in ((0.25, 14, 0, 1.0), (0.45, -22, 150, 0.7)):   # 뒤 겹은 느리게, 앞 겹은 반대로
                x0 = int(cx * speed + self.time * drift) % img.w - img.w
                img.opacify(fog * k)
                for x in range(x0, W, img.w):
                    assets.draw_image(img, x + img.w // 2, y + img.h // 2)
            img.opacify(1.0)
        vig = assets.image('ui/vignette.png')
        vig.opacify(vignette_strength(self.player.gauge.zone, high) * 0.7)
        assets.draw_image(vig, W // 2, 0)                  # draw_image의 y는 아래 가장자리 (11/21 고침: 예전엔 위 절반만 덮였다)
        vig.opacify(1.0)
        import drama
        p = self.player
        red = drama.low_hp_pulse(p.hp / max(1, p.max_hp), self.time) if p.state != 'DEAD' else 0.0
        if red > 0:                                       # 체력이 낮다: 붉은 가장자리가 심장 박자로
            img = assets.image('ui/vignette_red.png')
            img.opacify(red)
            assets.draw_image(img, W // 2, 0)
            img.opacify(1.0)
        color, k = drama.zone_flash()
        if k > 0:                                         # 구간이 바뀌는 순간 그 구간 색으로 번쩍
            assets.draw_rect_color(0, 0, W, H, color, k)
        if self.alpha > 0.004:
            assets.draw_rect_color(0, 0, W, H, tuple(int(c) for c in self.color), self.alpha)
