"""화면 분위기: 게이지 구간 색, 가장자리 어둡게(비네트), 흐르는 안개. 세계 위·HUD 아래에 화면 좌표로 그린다.
(2026-11-21 퀄리티 계획 2-2, 그림은 tools/make_atmosphere.py)

- 게이지 구간이 화면 색으로도 읽힌다: 페이드 차갑고 어둡게, 각성 옅은 청록, 위험 붉게 맥동, 강화 준비 보라.
  목표 색으로 부드럽게 바뀐다(한 프레임에 확 바뀌지 않는다).
- 비네트: 페이드일수록, 헤이즈가 짙은 방일수록 진하다.
- 안개·빛 번짐·날씨·비네트: 배경 바로 위(캐릭터 아래)에 그린다 (draw_back). 안개는 두 겹이 카메라와 시간에 따라 다른 빠르기로 흐른다(시차). 짙은 방은 진하게, 은신처는 없다.
번쩍임 줄이기(접근성)를 켜면 위험 구간의 맥동을 멈춘다.
- (11/21) 구간이 바뀌는 순간 그 구간 색으로 화면이 잠깐 번쩍이고, 체력이 낮으면 가장자리가 붉게 심장 박자로 맥동한다(drama).
"""
import math
import random

import assets
import camera
import config
import options

active = None                  # 지금 판의 Atmosphere (배경 분위기용)
EASE = 4.0                     # 목표 색으로 다가가는 빠르기(1/초)
TINTS = {'FADE': ((70, 90, 140), 0.16), 'AWAKE': ((60, 200, 190), 0.05), 'CRITICAL': ((255, 80, 50), 0.07)}
ENHANCED_TINT = ((170, 110, 255), 0.07)
ENHANCED_TINTS = {1: ENHANCED_TINT, 2: ((255, 190, 70), 0.07), 3: ((255, 70, 90), 0.09)}   # 강화 단계별 (보라·금·진홍)
CRITICAL_PULSE = 0.05          # 위험 구간 맥동 폭 (2Hz)


def target_tint(zone, enhanced, t, level=1):
    """구간·강화 준비(단계)·시간 -> (색, 투명도). 노멀은 색이 없다."""
    if enhanced:
        return ENHANCED_TINTS[max(1, min(3, level))]
    color, alpha = TINTS.get(zone, ((0, 0, 0), 0.0))
    if zone == 'CRITICAL' and not options.reduce_flash:
        alpha += CRITICAL_PULSE * (0.5 + 0.5 * math.sin(t * math.tau * 2))
    return color, alpha


# 구역 날씨 (11/22 v5): 방 테마마다 화면 앞을 지나가는 입자. 슬럼 비, 공장 불티, 탑 헤이즈 입자, 은신처 먼지
WEATHER = {'cell': 'rain', 'foundry': 'ember', 'haze': 'mote', 'hideout': 'dust'}
WEATHER_COUNT = {'rain': 90, 'ember': 75, 'mote': 65, 'dust': 45}
# 빛 번짐: 이 소품 둘레에 색을 더해 그린다 (assets/ui/glow.png 점묘를 더하기 섞기로)
LIGHT_COLORS = {'bulb': (255, 190, 110), 'brazier': (255, 150, 60), 'anvil': (255, 140, 60), 'crystal': (90, 240, 220),
                'searchlight': (170, 240, 255), 'broken_crystals': (90, 240, 220)}
LIGHT_RADIUS = {'brazier': 150, 'crystal': 130, 'searchlight': 120}


def weather_kind(theme):
    return WEATHER.get(theme)


class Weather:
    """화면 좌표의 날씨 입자. 비는 비스듬히 내리고, 불티·헤이즈 입자·먼지는 흔들리며 오른다. 화면 밖으로 나가면 반대편에서 다시."""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.kind = None
        self.points = []
        self.time = 0.0

    def set_kind(self, kind):
        if kind == self.kind:
            return
        self.kind = kind
        W, H = config.SCREEN_W, config.SCREEN_H
        n = WEATHER_COUNT.get(kind, 0)
        r = self.rng
        self.points = [[r.uniform(0, W), r.uniform(0, H), r.uniform(0.6, 1.4), r.choice((3, 3, 4, 5) if kind in ('ember', 'mote') else (2, 2, 3)), r.uniform(0, 6.28)]
                       for _ in range(n)]

    def update(self, dt):
        self.time += dt
        W, H = config.SCREEN_W, config.SCREEN_H
        for pt in self.points:
            x, y, speed, size, phase = pt
            if self.kind == 'rain':
                x, y = x - 260 * speed * dt, y - 1300 * speed * dt
            elif self.kind == 'ember':
                x, y = x + math.sin(self.time * 2 + phase) * 40 * dt, y + 90 * speed * dt
            else:                                         # 헤이즈 입자·먼지: 느리게 떠오르며 흔들림
                x, y = x + math.sin(self.time * 0.8 + phase) * 18 * dt, y + 26 * speed * dt
            if y < -20:
                y += H + 40
            elif y > H + 20:
                y -= H + 40
            x %= W
            pt[0], pt[1] = x, y

    def draw(self):
        if not self.kind:
            return
        for x, y, speed, size, phase in self.points:
            if self.kind == 'rain':
                for k in range(3):                          # 짧은 사선 빗줄기
                    assets.draw_rect_color(int(x + k * 2), int(y + k * 10), 2, 10, (150, 175, 220))
            elif self.kind == 'ember':
                on = math.sin(self.time * 6 + phase) > -0.3   # 깜빡이는 불티
                if on:
                    assets.draw_rect_color(int(x), int(y), size, size, (255, 170, 70) if size < 4 else (255, 220, 140))
            elif self.kind == 'mote':
                assets.draw_rect_color(int(x), int(y), size, size, (110, 235, 220))
            else:
                assets.draw_rect_color(int(x), int(y), 2, 2, (220, 190, 150))


def fog_strength(stage_name, high_haze):
    if stage_name == 'hideout':
        return 0.0
    return 0.5 if high_haze else 0.22


def vignette_strength(zone, high_haze):
    base = 0.9 if zone in ('FADE', 'DEAD') else 0.55
    return min(1.0, base + (0.2 if high_haze else 0.0))


def _flicker(t, x):
    return 0.85 + 0.15 * math.sin(t * 7 + x * 0.01) * math.sin(t * 2.3 + x)


class Atmosphere:
    def __init__(self, player, stage):
        self.player, self.stage = player, stage
        self.color, self.alpha, self.time = (0, 0, 0), 0.0, 0.0
        self.weather = Weather()
        global active
        active = self                                    # room.draw가 배경 분위기를 그리려고 찾는다

    def ease(self, zone, enhanced, dt, level=1):
        self.time += dt
        color, alpha = target_tint(zone, enhanced, self.time, level)
        k = min(1.0, EASE * dt)
        if self.alpha <= 0.001:                          # 색이 없던 상태면 색은 바로 바꾸고 진하기만 천천히
            self.color = color
        elif alpha > 0:
            self.color = tuple(c + (t - c) * k for c, t in zip(self.color, color))
        self.alpha += (alpha - self.alpha) * k

    def update(self, dt):
        g = self.player.gauge
        self.ease(g.zone, g.enhanced, dt, g.enhance_level)
        room = getattr(self.stage, 'room', None)
        self.weather.set_kind(weather_kind(getattr(room, 'theme', None)) if room is not None else None)
        self.weather.update(dt)

    def _draw_lights(self, room):
        """등불·화로·결정 둘레 빛 번짐 (점묘를 색 곱해 더하기로, 살짝 일렁임)."""
        if room is None or not hasattr(room, 'lights'):
            return
        img = assets.image('ui/glow.png')
        ox, oy = camera.offset()
        for x, y, r, color in room.lights():
            sx, sy = x + ox, y + oy
            if -r < sx < config.SCREEN_W + r and -r < sy < config.SCREEN_H + r:
                img.opacify(0.32 * _flicker(self.time, x))
                assets.draw_image_added(img, int(sx), int(sy - img.h // 2), color=color, times=1)
        img.opacify(1.0)

    def draw_back(self):
        """배경에만 얹는 분위기: 안개, 빛 번짐, 날씨, 비네트. 배경 바로 위, 타일·캐릭터 아래에 그린다
        (room.draw가 배경 직후 부른다. 캐릭터·적·보스를 가리지 않는다). 화면 좌표로 그린다."""
        W = config.SCREEN_W
        room = self.stage.room
        high = bool(getattr(room, 'is_high_haze', False))
        screen_offset = assets.draw_offset
        assets.draw_offset = (0, 0)
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
        self._draw_lights(room)
        self.weather.draw()
        vig = assets.image('ui/vignette.png')
        vig.opacify(vignette_strength(self.player.gauge.zone, high) * 0.7)
        assets.draw_image(vig, W // 2, 0)                  # draw_image의 y는 아래 가장자리
        vig.opacify(1.0)
        assets.draw_offset = screen_offset

    def draw(self):
        """위에 얹는 것: 상태 표시(체력 낮음 붉은 가장자리, 구간 번쩍임, 구간 색)만. 나머지는 draw_back."""
        W, H = config.SCREEN_W, config.SCREEN_H
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
