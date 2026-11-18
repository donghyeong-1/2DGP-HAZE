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
import options
import sprites

_meta = {}
flash_left = 0.0     # 화면 전체 섬광이 남은 시간 (오버로드 순간)
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
    global hit_stop_left, trauma, flash_left
    hit_stop_left = 0.0
    trauma = 0.0
    flash_left = 0.0


def request_flash(seconds):
    """화면 전체를 하얗게 번쩍이게 한다 (UI가 flash_left를 보고 그린다)."""
    global flash_left
    flash_left = max(flash_left, seconds)


def add_trauma(amount):
    """충격을 더한다. 겹치면 쌓이고 1에서 멈춘다. 가벼운 타격은 거의 안 흔들리고 센 타격은 크게 흔들린다."""
    global trauma
    trauma = min(1.0, trauma + amount)


def tick_shake(real_dt):
    """흔들림을 실제 시간으로 줄인다 (타격 멈춤 중에도 계속 줄어서 화면이 어긋난 채 굳지 않는다)."""
    global trauma, _shake_time, flash_left
    flash_left = max(0.0, flash_left - real_dt)            # 섬광도 타격 멈춤 중에 실제 시간으로 줄어든다
    if trauma > 0:
        _shake_time += real_dt
        trauma = max(0.0, trauma - config.SHAKE_DECAY * real_dt)


def shake_offset():
    """이번 프레임의 화면 흔들림 (x, y) 정수 픽셀. 서로 다른 속도의 사인파를 더해 지직거리지 않고 부드럽게 흔든다."""
    if trauma <= 0:
        return (0, 0)
    amp = config.SHAKE_MAX_OFFSET * trauma * trauma * options.shake_mult()     # 접근성: 흔들림 끔·약하게·보통
    t = _shake_time * 38.0
    return (int(round(amp * math.sin(t * 1.7))), int(round(amp * math.sin(t * 2.3 + 1.3))))


def sheet_info(name):
    if name not in _meta:
        with open(os.path.join(assets.ASSET_DIR, 'effects', name + '.json'), encoding='utf-8') as f:
            _meta[name] = json.load(f)
    return _meta[name]


# 번쩍임 줄이기를 켜면 처음의 하얀 섬광 부분을 건너뛰는 큰 이펙트들 (전체 길이에서 건너뛸 비율)
FLASHY = ('haze-blast', 'quake-blast', 'overload-burst', 'death-burst', 'hit-critical', 'hit-enhanced')
FLASHY_SKIP = 0.25


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
        if options.reduce_flash and name in FLASHY:  # 접근성: 번쩍임 줄이기면 하얀 중심이 큰 첫 장면을 건너뛴다
            self.time = duration * FLASHY_SKIP

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


# 직선 베기 색 (밝음 -> 어두움): 대시 평타는 금색, 강화는 보라+흰 코어
PATH_COLORS = {False: [(255, 255, 255), (255, 241, 184), (255, 211, 90), (201, 138, 30)],
               True: [(255, 255, 255), (230, 204, 255), (164, 107, 255), (90, 47, 184)]}


class PathSlash:
    """대시로 지나온 자리를 한 줄로 가르는 직선 베기. 코드로 그리는 픽셀 선이다 (확대·회전 없음, 사각 블록을 이어 붙임).

    중간이 두껍고 양 끝이 가늘며, 바깥에서 안쪽으로 4톤(어두움 -> 흰 코어)이 겹치고 시간이 지나며 가늘어지고 어두워진다.
    """

    def __init__(self, x0, y0, x1, y1, enhanced=False, life=0.32):
        self.p0, self.p1 = (x0, y0), (x1, y1)
        self.enhanced = enhanced
        self.life, self.time = life, 0.0
        self.name = 'path-slash'

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        (x0, y0), (x1, y1) = self.p0, self.p1
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 1:
            return
        t = self.time / self.life
        base = (44 if self.enhanced else 30) * (1.0 - t) ** 0.8 + 2
        colors = PATH_COLORS[self.enhanced]
        # 바깥(어두움) -> 코어(흰색) 순서로 점점 가늘게 덧그린다
        for layer, (color, scale) in enumerate(zip(reversed(colors), (1.0, 0.72, 0.46, 0.22))):
            step = 5
            n = max(2, int(length // step))
            for i in range(n + 1):
                s = i / n
                taper = math.sin(math.pi * min(1.0, max(0.0, s))) ** 0.6          # 양 끝은 가늘다
                size = int(base * scale * max(0.18, taper))
                if size < 2:
                    continue
                cx, cy = x0 + (x1 - x0) * s, y0 + (y1 - y0) * s
                assets.draw_rect_color(int(round(cx - size / 2)), int(round(cy - size / 2)), size, size, color)


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


class ImpactBurst:
    """맞은 자리에서 사방으로 뻗는 충격 방사선 (격투 게임의 집중선). 코드로 그리는 픽셀 선이다 (사각 블록, 정수 좌표).

    맞은 방향 쪽 선이 더 길고, 선은 바깥으로 튀어 나가며 짧아진다. 끝 두 칸은 흰색이다.
    """

    def __init__(self, x, y, angle_deg, count, color, big=False, life=0.17):
        self.x, self.y = x, y
        self.color = color
        self.life, self.time = life, 0.0
        self.rays = []
        for k in range(count):
            ang = angle_deg + k * 360.0 / count + (((k * 37) % 11) - 5) * 2.0       # 고정된 어긋남 (매번 같은 모양)
            near = abs(((ang - angle_deg + 180) % 360) - 180) < 45                    # 맞은 방향 쪽은 길게
            length = (58 if near else 34) * (1.35 if big else 1.0) * (0.85 + 0.3 * ((k * 7) % 3) / 2)
            self.rays.append((math.radians(ang), length))

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        p = self.time / self.life
        r0 = 12 + 30 * p
        for ang, length in self.rays:
            r1 = r0 + length * (1.0 - p) ** 0.7
            dx, dy = math.cos(ang), math.sin(ang)
            r = r0
            while r < r1:
                tip = r1 - r < 11
                size = 4 if tip else 5
                assets.draw_rect_color(int(round(self.x + dx * r - size / 2)), int(round(self.y + dy * r - size / 2)),
                                       size, size, (255, 255, 255) if tip else self.color)
                r += 5


class BodyGhost:
    """공격 순간 몸의 잔상 (스미어). 타격 자세를 뒤쪽에 옅게 겹쳐 그려 휘두르는 속도감을 준다."""

    def __init__(self, frame, x, y, face_dir, color, alpha, life=0.13, delay=0.0):
        self.frame = frame                      # (그림 세트, 번호)
        self.x, self.y, self.face_dir = x, y, face_dir
        self.color, self.alpha = color, alpha
        self.life, self.time, self.delay = life, 0.0, delay

    def update(self, dt):
        self.time += dt
        if self.time >= self.life + self.delay:
            game_world.remove_object(self)

    def draw(self):
        if self.time < self.delay:
            return
        fade = 1.0 - (self.time - self.delay) / self.life
        sprites.draw(*self.frame, self.x, self.y, self.face_dir, self.color, max(0.0, self.alpha * fade))


def spawn_impact(x, y, dir_x, dir_y, count, color, big=False):
    """(x, y)에서 방향 (dir_x, dir_y) 쪽으로 더 길게 뻗는 충격 방사선을 낸다."""
    if count <= 0:
        return
    angle = math.degrees(math.atan2(dir_y, dir_x)) if (dir_x or dir_y) else 0.0
    game_world.add_object(ImpactBurst(x, y, angle, count, color, big), game_world.LAYER_EFFECT)


def spawn_smear(frame, x, y, face_dir, aim, enhanced=False):
    """공격 자세(frame = (그림 세트, 번호))의 잔상 두 장을 조준 반대쪽 뒤에 남긴다."""
    color = (190, 150, 255) if enhanced else (170, 225, 255)
    ax, ay = aim
    for k, alpha in ((1, 0.5), (2, 0.28)):
        game_world.add_object(BodyGhost(frame, x - ax * 16 * k, y - ay * 10 * k, face_dir, color, alpha, delay=0.02 * k),
                              game_world.LAYER_EFFECT)


def spawn(name, x, y, flip=False, duration=0.35, variant=0):
    game_world.add_object(SheetEffect(name, x, y, flip, duration, variant), game_world.LAYER_EFFECT)


def fx_for(zone, enhanced=False):
    """공격 효과 묶음: E 강화 중이면 강화용, 아니면 게이지 구간용."""
    return config.ENHANCED_FX if enhanced else config.ZONE_FX[zone]


def slash_sheet(zone, finisher=False, enhanced=False):
    """휘두르기 시트 이름. 강화 > 3타 > 구간 순으로 정한다."""
    if enhanced:
        return config.ENHANCED_FX['slash']
    if finisher:
        return config.FINISHER_SLASH
    return config.ZONE_FX[zone]['slash']


def special_sheet(kind, enhanced=False):
    """점프 평타·내려찍기의 효과 시트: (시트 이름, 방향 변형이 있는가). 강화되면 보라색 큰 시트로 바뀐다.
    (대시 평타는 시트가 아니라 지나온 경로를 훑는 PathSlash 직선이다.)"""
    if kind == 'spin':
        return ('air-spin-enhanced' if enhanced else 'air-spin', False)
    if kind == 'plunge':
        return ('pipe-slash-enhanced' if enhanced else 'dash-strike', True)
    raise KeyError(kind)


def spawn_path_slash(x0, y0, x1, y1, enhanced=False):
    game_world.add_object(PathSlash(x0, y0, x1, y1, enhanced), game_world.LAYER_EFFECT)


def aura_names(zone, enhanced=False, stunned=False):
    """지금 게이지 구간과 강화 상태에서 주인공 주위에 그릴 오라 시트들. 강화 준비 중에는 보라색 강화 오라가 구간 오라를
    대체한다 (두 오라는 모두 실루엣을 감싸는 큰 불꽃이라 겹치면 지저분하다)."""
    if stunned:                                            # 오버로드 기절: 전기 아크가 모든 오라를 대체한다
        return [config.AURA_STUN]
    if enhanced:
        return [config.AURA_ENHANCED]
    return [config.AURA_BY_ZONE[zone]] if zone in config.AURA_BY_ZONE else []


def draw_loop(name, x, y, t, flip=False):
    """반복 재생 시트(오라)를 t초 지점의 프레임으로 (x, y)에 그린다. y는 발 높이, 기준점(pivot)을 거기에 맞춘다."""
    info = sheet_info(name)
    fw, fh = info['frameSize']
    px, py = info['pivot']
    i = int(t * info['fps']) % info['frames']
    cols = info['columns']
    img = assets.image(f'effects/{name}.png')
    s = info.get('scale', 1)
    left, bottom = (i % cols) * fw, img.h - (i // cols + 1) * fh
    assets.draw_clip(img, left, bottom, fw, fh, x - ((fw - px) if flip else px) * s, y - (fh - py) * s, 'h' if flip else '', s)


def slash_variant(ax, ay, angles=(0, 45, 90, -45, -90)):
    """조준 벡터에 가장 가까운 휘두르기 방향 변형과 좌우 반전 여부를 돌려준다. 왼쪽 조준은 오른쪽 변형을 반전해 쓴다."""
    flip = ax < -1e-3
    ang = math.degrees(math.atan2(ay, abs(ax)))   # 왼쪽 조준은 세로축으로 접어 -90~90도로
    best = min(range(len(angles)), key=lambda i: abs(angles[i] - ang))
    return best, flip


def float_text(x, y, text, color, big=False, life=0.8):
    game_world.add_object(FloatText(x, y, text, color, life=life, big=big), game_world.LAYER_EFFECT)
