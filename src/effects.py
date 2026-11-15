"""화면 효과: 시트 애니메이션(타격 불꽃·휘두르기·연기), 떠오르는 글자, 타격 멈춤(hit stop).

시트는 assets/effects/<이름>.png + .json (tools/finish_effects.py가 만든다). 확대·축소·회전 없이 1배,
정수 좌표로 그린다. 시트는 왼쪽 위 칸부터 가로로 채워지고, 프레임을 시간에 맞춰 골라서 원하는 길이로 재생한다.
"""
import json
import math
import os

import assets
import config
import game_world

_meta = {}
hit_stop_left = 0.0  # 남은 타격 멈춤 시간. play_mode가 이 동안 world 갱신을 건너뛴다
trauma = 0.0         # 화면 흔들림 세기 0~1
_shake_time = 0.0


def request_hit_stop(seconds):
    global hit_stop_left
    hit_stop_left = max(hit_stop_left, seconds)


def tick_hit_stop(dt):
    """멈춤 중이면 시간을 깎고 True(이번 프레임은 갱신하지 않는다)를 돌려준다."""
    global hit_stop_left
    if hit_stop_left > 0:
        hit_stop_left = max(0.0, hit_stop_left - dt)
        return True
    return False


def reset():
    global hit_stop_left, trauma
    hit_stop_left = 0.0
    trauma = 0.0


def add_trauma(amount):
    """충격을 더한다. 겹치면 쌓이고 1에서 멈춘다. 가벼운 타격은 거의 안 흔들리고 센 타격은 크게 흔들린다."""
    global trauma
    trauma = min(1.0, trauma + amount)


def tick_shake(real_dt):
    """흔들림을 실제 시간으로 줄인다 (타격 멈춤 중에도 계속 줄어서 화면이 어긋난 채 굳지 않는다)."""
    global trauma, _shake_time
    if trauma > 0:
        _shake_time += real_dt
        trauma = max(0.0, trauma - config.SHAKE_DECAY * real_dt)


def shake_offset():
    """이번 프레임의 화면 흔들림 (x, y) 정수 픽셀. 서로 다른 속도의 사인파를 더해 지직거리지 않고 부드럽게 흔든다."""
    if trauma <= 0:
        return (0, 0)
    amp = config.SHAKE_MAX_OFFSET * trauma * trauma
    t = _shake_time * 38.0
    return (int(round(amp * math.sin(t * 1.7))), int(round(amp * math.sin(t * 2.3 + 1.3))))


def sheet_info(name):
    if name not in _meta:
        with open(os.path.join(assets.ASSET_DIR, 'effects', name + '.json'), encoding='utf-8') as f:
            _meta[name] = json.load(f)
    return _meta[name]


class SheetEffect:
    """시트 한 장을 duration초에 걸쳐 한 번 재생하고 사라진다. (x, y)에 시트의 pivot을 맞춘다."""

    def __init__(self, name, x, y, flip=False, duration=0.35, variant=0):
        self.name = name
        self.x, self.y = x, y
        self.flip = flip
        self.duration = duration
        self.variant = variant           # 방향 변형 줄 번호 (휘두르기처럼 variants가 있는 시트만)
        self.time = 0.0
        self.info = sheet_info(name)

    @property
    def frame(self):
        """variants가 있는 시트는 줄마다 같은 길이의 애니메이션이다. 시간에 맞춰 그 줄 안의 프레임을 고른다."""
        variants = self.info.get('variants', 1)
        n = self.info['frames'] // variants
        return self.variant * n + min(n - 1, int(self.time / self.duration * n))

    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            game_world.remove_object(self)

    def draw(self):
        fw, fh = self.info['frameSize']
        cols = self.info['columns']
        px, py = self.info['pivot']  # pivot은 프레임 왼쪽 위 기준 (x, y)
        i = self.frame
        col, row = i % cols, i // cols
        img = assets.image(f'effects/{self.name}.png')
        sheet_h = img.h
        left, bottom = col * fw, sheet_h - (row + 1) * fh
        s = self.info.get('scale', config.EFFECT_SCALE)  # 정수 배율(최근접)로만 키운다. pivot도 같은 배율로 옮긴다
        dx = self.x - ((fw - px) if self.flip else px) * s
        dy = self.y - (fh - py) * s
        assets.draw_clip(img, left, bottom, fw, fh, dx, dy, 'h' if self.flip else '', s)


class FloatText:
    """게이지 증감 같은 짧은 글자. 위로 떠오르며 사라진다."""

    def __init__(self, x, y, text, color, life=0.8, rise=70, big=False):
        self.x, self.y0 = x, y
        self.text, self.color = text, color
        self.life, self.time, self.rise = life, 0.0, rise
        self.big = big

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        t = self.time / self.life
        assets.draw_text(self.x, self.y0 + self.rise * t, self.text, self.color, center=True, big=self.big)


def spawn(name, x, y, flip=False, duration=0.35, variant=0):
    game_world.add_object(SheetEffect(name, x, y, flip, duration, variant), game_world.LAYER_EFFECT)


def slash_variant(ax, ay, angles=(0, 45, 90, -45, -90)):
    """조준 벡터에 가장 가까운 휘두르기 방향 변형과 좌우 반전 여부를 돌려준다. 왼쪽 조준은 오른쪽 변형을 반전해 쓴다."""
    flip = ax < -1e-3
    ang = math.degrees(math.atan2(ay, abs(ax)))   # 왼쪽 조준은 세로축으로 접어 -90~90도로
    best = min(range(len(angles)), key=lambda i: abs(angles[i] - ang))
    return best, flip


def float_text(x, y, text, color, big=False, life=0.8):
    game_world.add_object(FloatText(x, y, text, color, life=life, big=big), game_world.LAYER_EFFECT)
