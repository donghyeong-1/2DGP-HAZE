"""화면 효과: 시트 애니메이션(타격 불꽃·휘두르기·연기), 떠오르는 글자, 타격 멈춤(hit stop).

시트는 assets/effects/<이름>.png + .json (tools/finish_effects.py가 만든다). 확대·축소·회전 없이 1배,
정수 좌표로 그린다. 시트는 왼쪽 위 칸부터 가로로 채워지고, 프레임을 시간에 맞춰 골라서 원하는 길이로 재생한다.
"""
import json
import math
import random
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
_kick = [0.0, 0.0]   # 카메라 킥 (v8): 큰 타격이 공격 방향으로 화면을 민 거리(px). 곧 0으로 돌아온다
_shake_time = 0.0


slow_left = 0.0      # 슬로 모션이 남은 실제 시간(초)
slow_scale = 1.0     # 슬로 모션 동안의 시간 배율


def request_slow_motion(seconds, scale):
    """잠깐 느려진다 (방의 마지막 적·보스를 쓰러뜨렸을 때). 이미 더 길거나 느린 것이 있으면 그것을 따른다."""
    global slow_left, slow_scale
    slow_left = max(slow_left, seconds)
    slow_scale = min(slow_scale, scale) if slow_left > 0 else scale


def time_scale():
    return slow_scale if slow_left > 0 else 1.0


def tick_slow_motion(real_dt):
    """실제 시간으로 줄어든다 (느려진 게임 시간이 아니라)."""
    global slow_left, slow_scale
    if slow_left > 0:
        slow_left = max(0.0, slow_left - real_dt)
        if slow_left == 0:
            slow_scale = 1.0


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
    global hit_stop_left, trauma, flash_left, slow_left, slow_scale
    _kick[0] = _kick[1] = 0.0
    hit_stop_left = 0.0
    slow_left, slow_scale = 0.0, 1.0
    trauma = 0.0
    flash_left = 0.0
    import cut_in
    cut_in.reset()                               # O1: 도는 컷인도 지운다 (새 판·테스트)


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
    if _kick[0] or _kick[1]:                                 # 킥은 빠르게 돌아온다
        k = math.exp(-config.KICK_DECAY * real_dt)
        _kick[0], _kick[1] = _kick[0] * k, _kick[1] * k
        if abs(_kick[0]) < 0.5 and abs(_kick[1]) < 0.5:
            _kick[0] = _kick[1] = 0.0


def shake_offset():
    """이번 프레임의 화면 흔들림 (x, y) 정수 픽셀. 서로 다른 속도의 사인파를 더해 지직거리지 않고 부드럽게 흔든다."""
    kx, ky = kick_offset()
    if trauma <= 0:
        return (kx, ky)
    amp = config.SHAKE_MAX_OFFSET * trauma * trauma * options.shake_mult()     # 접근성: 흔들림 끔·약하게·보통
    t = _shake_time * 38.0
    return (int(round(amp * math.sin(t * 1.7))) + kx, int(round(amp * math.sin(t * 2.3 + 1.3))) + ky)


def add_kick(dx, dy, px):
    """카메라 킥 (v8): (dx, dy) 방향으로 화면을 px만큼 민다. 흔들림과 달리 방향이 있고 한 번 밀렸다 돌아온다."""
    n = math.hypot(dx, dy)
    if n < 1e-6:
        return
    k = px * options.shake_mult()
    _kick[0] = max(-24.0, min(24.0, _kick[0] + dx / n * k))
    _kick[1] = max(-24.0, min(24.0, _kick[1] + dy / n * k))


def kick_offset():
    """지금의 킥 (x, y) 정수 픽셀. 화면에 보이는 것은 반대로 움직인다(카메라가 그쪽으로 간 것처럼)."""
    return (int(round(_kick[0])), int(round(_kick[1])))


def sheet_info(name):
    if name not in _meta:
        with open(os.path.join(assets.ASSET_DIR, 'effects', name + '.json'), encoding='utf-8') as f:
            _meta[name] = json.load(f)
    return _meta[name]


# 번쩍임 줄이기를 켜면 처음의 하얀 섬광 부분을 건너뛰는 큰 이펙트들 (전체 길이에서 건너뛸 비율)
FLASHY = ('haze-blast', 'ult-nova-pipe', 'ult-nova-knife', 'ult-nova-pistol', 'ult-nova-gauntlet', 'ult-nova-chain', 'quake-blast', 'overload-burst', 'death-burst', 'hit-critical', 'hit-enhanced')
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
        if 'duration' in self.info:      # v8 시트(tools/fxkit.py)는 연출 시간이 그림에 들어 있다: 부르는 쪽 시간 대신 그대로 재생
            self.duration = self.info['duration']
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
        glow = glow_of(self.name)
        if glow is not None:                       # v7: 같은 칸의 번진 빛을 아래에 더하기로 (INARI처럼 빛나게)
            g = assets.image(glow)
            k = img.w // g.w                       # 빛 시트는 절반 크기로 저장될 수 있다
            p = self.time / self.duration
            a = GLOW_ALPHA * (1.0 - p * p) * (0.5 if options.reduce_flash else 1.0)
            assets.draw_clip_added(g, left // k, bottom // k, fw // k, fh // k, dx, dy, 'h' if self.flip else '', s * k, a)
        assets.draw_clip(img, left, bottom, fw, fh, dx, dy, 'h' if self.flip else '', s)


def draw_tint_sheet(name, x, y, t, color, variant=0, scale=None):
    """두 겹 시트(tools/fxkit.export_tint)의 t(0~1) 시점을 (x, y)에 그린다: 빛 -> 색 층(공격 색을 곱함) -> 흰 심."""
    info = sheet_info(name)
    fw, fh = info['frameSize']
    n, v = info['columns'], info['tint']
    px, py = info['pivot']
    s = scale or info.get('scale', config.EFFECT_SCALE)
    i = min(n - 1, max(0, int(t * n)))
    img = assets.image(f'effects/{name}.png')
    dx, dy = x - px * s, y - (fh - py) * s
    g = assets.image(f'light/glow_{name}.png')
    a = GLOW_ALPHA * (1.0 - t * t) * (0.5 if options.reduce_flash else 1.0)
    assets.draw_clip_added(g, i * fw, g.h - (variant + 1) * fh, fw, fh, dx, dy, '', s, a, color)
    assets.draw_clip_tinted(img, i * fw, img.h - (variant + 1) * fh, fw, fh, dx, dy, color, s)
    assets.draw_clip(img, i * fw, img.h - (variant + v + 1) * fh, fw, fh, dx, dy, '', s)


GLOW_ALPHA = 0.85        # 휘두르기·타격 시트 아래 번진 빛의 세기 (처음 값, 끝으로 갈수록 준다)
_glow_cache = {}


def glow_of(name):
    """그 시트의 빛 시트 경로 (assets 기준, tools/make_glow.py가 만든다). 없으면 None (먼지·오라 등)."""
    if name not in _glow_cache:
        import os
        rel = f'light/glow_{name}.png'
        _glow_cache[name] = rel if os.path.exists(os.path.join(assets.ASSET_DIR, rel)) else None
    return _glow_cache[name]


# 직선 베기 색 (밝음 -> 어두움): 대시 평타는 금색, 강화는 단계 색(1 보라·2 금·3 진홍)+흰 코어
PATH_COLORS = {False: [(255, 255, 255), (255, 241, 184), (255, 211, 90), (201, 138, 30)],
               True: [(255, 255, 255), (230, 204, 255), (164, 107, 255), (90, 47, 184)],
               2: [(255, 255, 255), (255, 236, 170), (240, 170, 50), (150, 90, 20)],
               3: [(255, 255, 255), (255, 190, 190), (236, 58, 72), (120, 16, 36)]}
enh_level = 1           # 지금 나가는 강화 공격의 단계 (무기가 공격할 때 정한다): 이펙트 이름·색을 고른다


def enh_suffix():
    """강화 이펙트 시트 이름 뒤에 붙일 단계 표시: 1단계 '', 2단계 '2', 3단계 '3'."""
    return '' if enh_level <= 1 else str(min(3, enh_level))


class PathSlash:
    """대시로 지나온 자리를 한 줄로 가르는 직선 베기. 코드로 그리는 픽셀 선이다 (확대·회전 없음, 사각 블록을 이어 붙임).

    중간이 두껍고 양 끝이 가늘며, 바깥에서 안쪽으로 4톤(어두움 -> 흰 코어)이 겹치고 시간이 지나며 가늘어지고 어두워진다.
    """

    def __init__(self, x0, y0, x1, y1, enhanced=False, life=0.32):
        self.p0, self.p1 = (x0, y0), (x1, y1)
        self.enhanced = enhanced
        self.life, self.time = life, 0.0
        self.name = 'path-slash'
        self.streak = None

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        # v8: 대시 궤적과 같은 그림(흰 속도 줄기 + 일렁이는 색 띠 + 번지는 빛)을 강화 단계 색으로
        import weapon
        if self.streak is None:
            colors = PATH_COLORS[(enh_level if enh_level >= 2 else True) if self.enhanced else False]
            self.streak = weapon.DashStreak((*self.p0, *self.p1), life=self.life, width=34 if self.enhanced else 26, color=colors[2])
        self.streak.t = self.time
        self.streak.draw()


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

    def __init__(self, x, y, angle_deg, count, color, big=False, life=0.22):
        self.x, self.y = x, y
        self.color = color
        self.angle_deg, self.big = angle_deg, big
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
        # v8: 미리 구운 두 겹 시트 (8방향, 색은 여기서 입힌다). 줄 수는 보통/많음 두 가지 그림으로 나타낸다
        name = 'impact-rays-big' if self.big or len(self.rays) >= 10 else 'impact-rays'
        draw_tint_sheet(name, self.x, self.y, self.time / self.life, self.color, int(round(self.angle_deg / 45.0)) % 8)


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
        sprites.draw_silhouette(*self.frame, self.x, self.y, self.face_dir, self.color, max(0.0, self.alpha * fade))


class SlashMark:
    """맞은 적을 가로지르는 베기 자국 (2026-11-21, 던그리드 다단 히트처럼 맞을 때마다 확실히 보이게). 코드로 그리는 픽셀 선:
    순간 길게 그어졌다가 가늘어지며 사라진다. 바깥은 공격 색, 가운데는 흰색. big은 더 길고 두껍다(강한 공격·궁극기)."""

    def __init__(self, x, y, angle_deg, color, big=False):
        self.x, self.y = x, y
        self.ang = math.radians(angle_deg)
        self.color = color
        self.big = big
        self.life = 0.28 if big else 0.2
        self.length = (230 if big else 130) * random.uniform(0.85, 1.15)
        self.width = 22 if big else 12
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        # v8: 미리 구운 두 겹 시트 (22.5도 간격 8각도, 180도 대칭). 색은 여기서 입힌다
        variant = int(round((math.degrees(self.ang) % 180.0) / 22.5)) % 8
        draw_tint_sheet('cut-mark-big' if self.big else 'cut-mark', self.x, self.y, self.time / self.life, self.color, variant)


class ImpactRing:
    """강한 타격이 퍼지는 고리 (사각 점을 둥글게 늘어놓는다). 반지름이 radius_max까지 커지며 점이 작아진다."""

    def __init__(self, x, y, color, radius_max=150, life=0.28):
        self.x, self.y, self.color = x, y, color
        self.radius_max, self.life, self.time = radius_max, life, 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        # v8: 미리 구운 고리 세 크기(반지름 76·156·300px) 중 가까운 것, 아주 크면 큰 것을 3배로 (정수 배율만)
        r = self.radius_max
        name, scale = (('shock-ring-s', 2) if r <= 110 else ('shock-ring-m', 2) if r <= 230 else
                       ('shock-ring-l', 2) if r <= 370 else ('shock-ring-l', 3))
        draw_tint_sheet(name, self.x, self.y, self.time / self.life, self.color, 0, scale)


class LightPillar:
    """궁극기 마지막 일격의 빛기둥: 땅에서 하늘로 솟는 굵은 기둥(흰 가운데 + 단계 색 바깥)과 위로 튀는 불티."""

    def __init__(self, x, floor_y, color, life=0.7):
        self.x, self.floor_y, self.color = x, floor_y, color
        self.life, self.time = life, 0.0
        self.sparks = [(random.uniform(-90, 90), random.uniform(0, 300), random.uniform(500, 1100)) for _ in range(26)]

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        t = self.time / self.life
        width = 170 * (math.sin(math.pi * min(1.0, t * 1.6)) if t < 0.62 else (1 - t) / 0.38 * 0.5)
        for color, k in ((self.color, 1.0), ((255, 255, 255), 0.4)):
            w = int(width * k)
            if w >= 2:
                assets.draw_rect_color(int(self.x - w / 2), int(self.floor_y), w, 1400, color)
        for sx, sy, speed in self.sparks:                 # 위로 튀는 불티
            y = self.floor_y + sy + speed * self.time
            size = 6 if t < 0.5 else 4
            assets.draw_rect_color(int(self.x + sx), int(y), size, size,
                                   (255, 255, 255) if int(sy) % 3 == 0 else self.color)


def spawn_slash_marks(x, y, dir_x, dir_y, color, big=False, count=1):
    """맞은 자리에 베기 자국 count개. 공격 방향에 비스듬히(±55~80도) 긋고, 여럿이면 X자로 엇갈린다."""
    base = math.degrees(math.atan2(dir_y, dir_x)) if (dir_x or dir_y) else 0.0
    for k in range(count):
        side = 1 if k % 2 == 0 else -1
        ang = base + side * random.uniform(55, 80)
        game_world.add_object(SlashMark(x + random.uniform(-10, 10), y + random.uniform(-12, 12), ang, color, big),
                              game_world.LAYER_EFFECT)


def spawn_ring(x, y, color, radius_max=150, life=0.28):
    game_world.add_object(ImpactRing(x, y, color, radius_max, life), game_world.LAYER_EFFECT)


def spawn_impact(x, y, dir_x, dir_y, count, color, big=False):
    """(x, y)에서 방향 (dir_x, dir_y) 쪽으로 더 길게 뻗는 충격 방사선을 낸다."""
    if count <= 0:
        return
    angle = math.degrees(math.atan2(dir_y, dir_x)) if (dir_x or dir_y) else 0.0
    game_world.add_object(ImpactBurst(x, y, angle, count, color, big), game_world.LAYER_EFFECT)


def spawn_smear(frame, x, y, face_dir, aim, enhanced=False):
    """공격 자세(frame = (그림 세트, 번호))의 잔상 두 장을 조준 반대쪽 뒤에 남긴다."""
    color = config.ENHANCE_LEVEL_COLOR[max(1, min(3, enh_level))] if enhanced else (170, 225, 255)
    ax, ay = aim
    for k, alpha in ((1, 0.5), (2, 0.28)):
        game_world.add_object(BodyGhost(frame, x - ax * 16 * k, y - ay * 10 * k, face_dir, color, alpha, delay=0.02 * k),
                              game_world.LAYER_EFFECT)


def spawn(name, x, y, flip=False, duration=0.35, variant=0):
    game_world.add_object(SheetEffect(name, x, y, flip, duration, variant), game_world.LAYER_EFFECT)


def fx_for(zone, enhanced=False):
    """공격 효과 묶음: E 강화 중이면 강화용, 아니면 게이지 구간용."""
    return config.ENHANCED_FX_BY_LEVEL[max(1, min(3, enh_level))] if enhanced else config.ZONE_FX[zone]


def slash_sheet(zone, finisher=False, enhanced=False, shape=None):
    """휘두르기 시트 이름. 강화 > 3타 > 구간 순으로 정한다.
    shape (공격 v3): 'flat' = 가로 베기의 납작한 호(구간 색), 'rise' = 올려베기 마무리의 올라가는 금색 호."""
    if enhanced:
        return config.ENHANCED_FX['slash'] + enh_suffix()
    if finisher:
        return config.FINISHER_SLASH + ('-rise' if shape == 'rise' else '')
    return config.ZONE_FX[zone]['slash'] + ('-flat' if shape == 'flat' else '')


def special_sheet(kind, enhanced=False):
    """점프 평타·내려찍기의 효과 시트: (시트 이름, 방향 변형이 있는가). 강화되면 보라색 큰 시트로 바뀐다.
    (대시 평타는 시트가 아니라 지나온 경로를 훑는 PathSlash 직선이다.)"""
    if kind == 'spin':
        return ('air-spin-enhanced' + enh_suffix() if enhanced else 'air-spin', False)
    if kind == 'plunge':
        return ('pipe-slash-enhanced' + enh_suffix() if enhanced else 'dash-strike', True)
    raise KeyError(kind)


def spawn_path_slash(x0, y0, x1, y1, enhanced=False):
    game_world.add_object(PathSlash(x0, y0, x1, y1, enhanced), game_world.LAYER_EFFECT)


def aura_names(zone, enhanced=False, stunned=False, level=1):
    """지금 게이지 구간과 강화 상태에서 주인공 주위에 그릴 오라 시트들. 강화 준비 중에는 보라색 강화 오라가 구간 오라를
    대체한다 (두 오라는 모두 실루엣을 감싸는 큰 불꽃이라 겹치면 지저분하다)."""
    if stunned:                                            # 오버로드 기절: 과열의 붉은 불길이 모든 오라를 대체한다
        return [config.AURA_STUN]
    if enhanced:                                           # 강화 단계마다 다른 색 (1 보라·2 금·3 진홍)
        return [config.AURA_ENHANCED + ('' if level <= 1 else str(min(3, level)))]
    return [config.AURA_BY_ZONE[zone]] if zone in config.AURA_BY_ZONE else []


def draw_loop(name, x, y, t, flip=False, variant=0):
    """반복 재생 시트(오라)를 t초 지점의 프레임으로 (x, y)에 그린다. y는 발 높이, 기준점(pivot)을 거기에 맞춘다.
    variant: 방향 변형이 있는 시트(탄환 32방향)의 줄 번호."""
    info = sheet_info(name)
    fw, fh = info['frameSize']
    px, py = info['pivot']
    per = info['frames'] // info.get('variants', 1)
    i = variant * per + int(t * info['fps']) % per
    cols = info['columns']
    img = assets.image(f'effects/{name}.png')
    s = info.get('scale', 1)
    left, bottom = (i % cols) * fw, img.h - (i // cols + 1) * fh
    dx, dy = x - ((fw - px) if flip else px) * s, y - (fh - py) * s
    glow = glow_of(name)
    if glow is not None:                                                   # 빛 시트가 있는 오라(기절의 과열)는 빛부터 깐다
        assets.draw_clip_added(assets.image(glow), left, bottom, fw, fh, dx, dy, 'h' if flip else '', s,
                               GLOW_ALPHA * (0.5 if options.reduce_flash else 1.0))
    assets.draw_clip(img, left, bottom, fw, fh, dx, dy, 'h' if flip else '', s)


# ----- 2026-11-26: 사각형으로 그리던 것들을 구운 시트로 (tools/make_fx2.py의 반복 시트·둥근 점) -----
def dir_variant(dx, dy, n=32):
    """방향 벡터에 가장 가까운 방향 변형 번호 (0 = 오른쪽, 반시계로 360/n도씩). 탄환·총구 섬광 시트가 쓴다."""
    return int(round(math.degrees(math.atan2(dy, dx)) / (360.0 / n))) % n


def draw_dot(x, y, color, size=1, alpha=1.0, glow=True):
    """둥근 점 하나 (구운 'dots' 시트, 색은 여기서 입힌다): 예고 고리·조준선·소용돌이처럼 점을 늘어놓는 것들이 쓴다.
    size 0~3 = 지름 약 6·10·14·20px. 번지는 빛(빛 층)을 먼저 깔고, 큰 점은 흰 심을 얹는다."""
    info = sheet_info('dots')
    fw, fh = info['frameSize']
    s = info.get('scale', config.EFFECT_SCALE)
    i = max(0, min(info['columns'] - 1, int(size)))
    img = assets.image('effects/dots.png')
    dx, dy = int(x) // 2 * 2 - fw * s // 2, int(y) // 2 * 2 - fh * s // 2
    if glow:
        assets.draw_clip_added(assets.image('light/glow_dots.png'), i * fw, 0, fw, fh, dx, dy, '', s,
                               alpha * (0.5 if options.reduce_flash else 1.0), color)
    img.opacify(alpha)
    try:
        assets.draw_clip_tinted(img, i * fw, fh, fw, fh, dx, dy, color, s)
        assets.draw_clip(img, i * fw, 0, fw, fh, dx, dy, '', s)
    finally:
        img.opacify(1.0)


def _loop_frame(name, t):
    info = sheet_info(name)
    fw, fh = info['frameSize']
    i = int(t * info['fps']) % info['frames']
    img = assets.image(f'effects/{name}.png')
    cols = info['columns']
    return info, img, fw, fh, (i % cols) * fw, img.h - (i // cols + 1) * fh


def draw_beam(name, cx, y_bottom, y_top, t, base=None):
    """세로 광선: 타일 시트(name)를 y_top에서 y_bottom까지 이어 붙인다 (마지막 칸은 필요한 만큼만 잘라 그린다).
    base를 주면 바닥에 닿은 자리의 불꽃(반복 시트)을 그 위에 그린다."""
    info, img, fw, fh, left, bottom = _loop_frame(name, t)
    s = info.get('scale', config.EFFECT_SCALE)
    px = info['pivot'][0]
    glow = glow_of(name)
    g = assets.image(glow) if glow else None
    x = int(cx) // 2 * 2 - px * s
    y = int(y_top) // 2 * 2
    y_bottom = int(y_bottom) // 2 * 2
    ga = GLOW_ALPHA * (0.5 if options.reduce_flash else 1.0)
    while y > y_bottom:
        rows = min(fh, (y - y_bottom) // s)                 # 이번 칸에서 그릴 줄 수 (타일의 위쪽부터)
        if rows <= 0:
            break
        if g is not None:
            assets.draw_clip_added(g, left, bottom + fh - rows, fw, rows, x, y - rows * s, '', s, ga)
        assets.draw_clip(img, left, bottom + fh - rows, fw, rows, x, y - rows * s, '', s)
        y -= rows * s
    if base:
        draw_loop(base, cx, y_bottom, t)


def draw_strip(name, x0, y, w, t, alpha=1.0):
    """바닥에 깔리는 띠: 타일 시트(name)를 x0에서 w만큼 가로로 이어 붙인다 (y = 바닥 윗면). alpha는 깔릴 때·걷힐 때의 옅어짐."""
    info, img, fw, fh, left, bottom = _loop_frame(name, t)
    s = info.get('scale', config.EFFECT_SCALE)
    py = info['pivot'][1]
    glow = glow_of(name)
    g = assets.image(glow) if glow else None
    x, end = int(x0) // 2 * 2, int(x0 + w) // 2 * 2
    dy = int(y) - (fh - py) * s
    ga = GLOW_ALPHA * alpha * (0.5 if options.reduce_flash else 1.0)
    img.opacify(alpha)
    try:
        while x < end:
            cols = min(fw, (end - x) // s)
            if cols <= 0:
                break
            if g is not None:
                assets.draw_clip_added(g, left, bottom, cols, fh, x, dy, '', s, ga)
            assets.draw_clip(img, left, bottom, cols, fh, x, dy, '', s)
            x += cols * s
    finally:
        img.opacify(1.0)


def draw_warn(x0, y, w, color, alpha=1.0):
    """바닥 예고 표시: 양 끝이 가늘어지는 얇은 띠(2px 칸) + 흰 심 + 띠를 따라 번지는 빛. 길이가 실행 중에 정해져 코드로 그린다."""
    x0, y, w = int(x0) // 2 * 2, int(y) // 2 * 2, max(8, int(w) // 2 * 2)
    img = assets.image('light/dot_48.png')
    img.opacify(0.55 * alpha * (0.5 if options.reduce_flash else 1.0))
    for gx in range(x0 + 12, x0 + w, 24):
        assets.draw_image_added(img, gx, y + 2 - img.h // 2, color=color, times=1)
    img.opacify(1.0)
    assets.draw_rect_color(x0, y, w, 2, color, alpha)                                  # 긴 줄 (끝이 가늘다)
    assets.draw_rect_color(x0 + 6, y, w - 12, 4, color, alpha)
    assets.draw_rect_color(x0 + 14, y + 4, w - 28, 2, color, alpha)
    if w > 44:
        assets.draw_rect_color(x0 + 20, y + 2, w - 40, 2, (255, 255, 255), alpha)      # 흰 심


def slash_variant(ax, ay, angles=(0, 45, 90, -45, -90)):
    """조준 벡터에 가장 가까운 휘두르기 방향 변형과 좌우 반전 여부를 돌려준다. 왼쪽 조준은 오른쪽 변형을 반전해 쓴다."""
    flip = ax < -1e-3
    ang = math.degrees(math.atan2(ay, abs(ax)))   # 왼쪽 조준은 세로축으로 접어 -90~90도로
    best = min(range(len(angles)), key=lambda i: abs(angles[i] - ang))
    return best, flip


def float_text(x, y, text, color, big=False, life=0.8):
    game_world.add_object(FloatText(x, y, text, color, life=life, big=big), game_world.LAYER_EFFECT)


# ----- v7 (2026-11-23) 빛 번짐·처치 연출 (docs/plan_v7.md 3) -----
class Bloom:
    """타격 순간 하얗게 번지는 빛. 부드러운 둥근 빛(assets/light, 빛 층만 반투명 예외)을 색을 곱해 더하기로 그리고 빠르게 식힌다."""

    def __init__(self, x, y, color, big=False, life=0.16, strength=1.0):
        self.x, self.y, self.color, self.big = x, y, color, big
        self.life, self.time, self.strength = life, 0.0, strength

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        img = assets.image('light/bloom_256.png' if self.big else 'light/bloom_128.png')
        k = (1.0 - self.time / self.life) ** 1.6
        img.opacify(min(1.0, self.strength * k * (0.5 if options.reduce_flash else 1.0)))
        assets.draw_image_added(img, int(self.x), int(self.y - img.h // 2), color=self.color, times=1)
        img.opacify(1.0)


class KillSlash:
    """처치 순간 적을 가로지르는 한 줄 베는 선 (INARI의 베는 선). 흰 심 + 색 가장자리, 앞으로 뻗었다가 가늘어지며 사라진다."""

    def __init__(self, x, y, dir_x, dir_y, color, life=0.2, length=260):
        n = math.hypot(dir_x, dir_y) or 1.0
        self.x, self.y, self.dx, self.dy = x, y, dir_x / n, dir_y / n
        self.color, self.life, self.time, self.length = color, life, 0.0, length

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        # v8: 구운 큰 베기 자국(8각도 두 겹 시트)에 색을 입힌다
        variant = int(round((math.degrees(math.atan2(self.dy, self.dx)) % 180.0) / 22.5)) % 8
        draw_tint_sheet('cut-mark-big', self.x, self.y, self.time / self.life, self.color, variant)


class TintFx:
    """두 겹 시트 하나를 색을 입혀 한 번 재생한다 (별 섬광 등). scale은 정수 배율(기본 시트 값)."""

    def __init__(self, name, x, y, color, life=None, scale=None):
        self.name, self.x, self.y, self.color, self.scale = name, x, y, color, scale
        self.life = life or sheet_info(name).get('duration', 0.3)
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        draw_tint_sheet(self.name, self.x, self.y, self.time / self.life, self.color, 0, self.scale)


class ScreenLine:
    """화면을 가로지르는 빛줄기 (INARI의 큰 일격): 흰 심 + 색 가장자리가 순식간에 뻗었다가 가늘어진다. 가로 또는 세로."""

    def __init__(self, x, y, color, life=0.3, vertical=False, width=14):
        self.x, self.y, self.color, self.life, self.vertical, self.width = x, y, color, life, vertical, width
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        t = self.time / self.life
        reach = 2400 * min(1.0, t / 0.12)                              # 가운데에서 양쪽으로 뻗는다
        w = max(2, int(self.width * (1.0 - t) ** 1.4) // 2 * 2)
        img = assets.image('light/bloom_256.png')                     # 줄기를 따라 번지는 빛
        img.opacify(0.3 * (1.0 - t) * (0.5 if options.reduce_flash else 1.0))
        for off in range(-int(reach), int(reach) + 1, 80):
            gx, gy = (self.x, self.y + off) if self.vertical else (self.x + off, self.y)
            assets.draw_image_added(img, int(gx), int(gy - img.h // 2), color=self.color, times=1)
        img.opacify(1.0)
        for color, k in ((self.color, 1.0), ((255, 255, 255), 0.4)):
            ww = max(2, int(w * k) // 2 * 2)
            if self.vertical:
                assets.draw_rect_color(int(self.x - ww // 2), int(self.y - reach), ww, int(reach * 2), color)
            else:
                assets.draw_rect_color(int(self.x - reach), int(self.y - ww // 2), int(reach * 2), ww, color)


class BlurSmear:
    """블러 느낌 (사용자 요청: 처형·궁극기): 가로로 길게 번지는 빛 띠 여러 겹 + 흰 속도선 + 주인공 잔상이 양옆으로 번졌다 모인다.
    화면을 읽어 흐리는 것이 아니라 빛 층을 가로로 늘어놓아 만든다 (pico2d에는 흐림 효과가 없다)."""

    def __init__(self, x, y, color, player=None, life=0.32, reach=620, victims=None, centers=None):
        self.x, self.y, self.color, self.player, self.life, self.reach = x, y, color, player, life, reach
        self.victims = list(victims or [])        # 맞은 적들 [(그림 (세트, 번호), 발 x, 발 y, 보는 쪽)]: 주인공처럼 양옆으로 번진다
        self.centers = list(centers or [])        # 맞은 적들의 가운데: 그 자리마다 빛 띠와 속도선이 번진다
        self.vlines = [(cx + random.uniform(-340, 340), cy + random.uniform(-70, 70), random.uniform(50, 200), cx)
                       for cx, cy in self.centers for _ in range(12)]
        if victims:
            self.life = max(self.life, 0.4)       # 적까지 번질 때는 조금 더 길게 보여 준다
        self.time = 0.0
        self.lines = [(random.uniform(-reach, reach), random.uniform(-150, 150), random.uniform(60, 260)) for _ in range(26)]

    def update(self, dt):
        self.time += dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        t = self.time / self.life
        k = (1.0 - t) ** 1.3 * (0.5 if options.reduce_flash else 1.0)
        img = assets.image('light/bloom_256.png')
        img.opacify(0.22 * k)
        for row in (-70, 0, 70):                                       # 가로로 번지는 빛 띠
            for off in range(-self.reach, self.reach + 1, 70):
                assets.draw_image_added(img, int(self.x + off), int(self.y + row - img.h // 2), color=self.color, times=1)
        img.opacify(1.0)
        for lx, ly, ln in self.lines:                                   # 흰 속도선: 바깥으로 밀려나며 가늘어진다
            x = self.x + lx * (1.0 + 0.5 * t)
            w = int(ln * (1.0 - t))
            if w >= 4:
                assets.draw_rect_color(int(x - w / 2), int(self.y + ly) // 2 * 2, w, 2, (255, 255, 255), 0.75 * k)
        p = self.player
        if p is not None:                                               # 주인공 잔상이 양옆으로 번진다
            for i, d in enumerate((22, 46, 74)):
                for side in (-1, 1):
                    sprites.draw_silhouette(*p._body_frame(), p.x + side * d * (1.0 - t), p.y, p.draw_face(), self.color,
                                            max(0.0, 0.34 - 0.09 * i) * k)
        # 맞은 적도 같이 번진다 (2026-11-24 사용자: '대시 마무리처럼 이펙트가 나가면서 블러가 화려하게 싹 들어가야 한다')
        # 적마다: 가로 빛 띠가 깔리고, 흰 속도선이 바깥에서 적 쪽으로 빨려들고, 색 잔상 네 겹이 멀리 벌어졌다가 빠르게 모인다
        pull = (1.0 - t) ** 2                                           # 처음에 넓게, 금방 모인다 (싹 들어가는 느낌)
        img.opacify(0.2 * k)
        for cx, cy in self.centers:
            for off in range(-280, 281, 70):
                assets.draw_image_added(img, int(cx + off * (0.4 + 0.6 * pull)), int(cy - img.h // 2), color=self.color, times=1)
        img.opacify(1.0)
        for lx, ly, ln, cx in self.vlines:
            x = cx + (lx - cx) * (0.25 + 0.75 * pull)
            w = int(ln * (0.3 + 0.7 * pull))
            if w >= 4:
                assets.draw_rect_color(int(x - w / 2), int(ly) // 2 * 2, w, 2, (255, 255, 255), 0.8 * k)
        for frame, vx, vy, face in self.victims:
            for i, d in enumerate((40, 84, 132, 184)):
                for side in (-1, 1):
                    sprites.draw_silhouette(*frame, vx + side * d * pull, vy, face, self.color if i else (255, 255, 255),
                                            max(0.0, 0.6 - 0.13 * i) * min(1.0, k * 1.6))


def spawn_blur(x, y, color, player=None, victims=None, centers=None):
    game_world.add_object(BlurSmear(x, y, color, player, victims=victims, centers=centers), game_world.LAYER_EFFECT)


def zone_glow(player):
    """지금 주인공의 이펙트 색: 강화 중이면 강화 단계 색, 아니면 게이지 구간 색 (위험 90%+는 레드)."""
    g = player.gauge
    if g.enhanced:
        return config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))]
    return config.ZONE_GLOW.get(g.zone, config.ZONE_GLOW['NORMAL'])


def draw_sheet_at(name, x, y, t):
    """시트(effects/<name>)의 t(0~1) 시점 한 장을 (x, y)에 그린다 (빛 시트 포함). 느려진 게임 시간과 상관없이 연출 객체가 직접 재생할 때."""
    info = sheet_info(name)
    fw, fh = info['frameSize']
    cols, px, py = info['columns'], *info['pivot']
    s = info.get('scale', config.EFFECT_SCALE)
    n = info['frames'] // info.get('variants', 1)
    i = min(n - 1, max(0, int(t * n)))
    img = assets.image(f'effects/{name}.png')
    left, bottom = (i % cols) * fw, img.h - (i // cols + 1) * fh
    dx, dy = x - px * s, y - (fh - py) * s
    glow = glow_of(name)
    if glow is not None:
        g = assets.image(glow)
        assets.draw_clip_added(g, left, bottom, fw, fh, dx, dy, '', s, GLOW_ALPHA * (0.5 if options.reduce_flash else 1.0))
    assets.draw_clip(img, left, bottom, fw, fh, dx, dy, '', s)


class OverloadPop:
    """오버로드 연출 (2026-11-24 사용자 요청): 기운이 주인공에게 빨려들며 화면이 어두워지고(OVERLOAD_GATHER) -> 팡 터지며 빛과 블러,
    공간이 일렁인다(postfx). 실제 시간으로 흐른다(느려진 dt를 시간 배율로 나눈다). 화면은 멈추지 않고 느려진다."""
    BURST = 0.8

    def __init__(self, player):
        self.p = player
        self.name = 'overload-burst'
        self.rt = 0.0
        self.fresh = True
        self.popped = False
        self.x, self.y = player.center
        request_slow_motion(config.OVERLOAD_GATHER + 0.12, 0.1)
        assets.play_sound('ult_cast')
        import camera
        import postfx
        sx, sy = camera.to_screen(self.x, self.y)
        g = config.OVERLOAD_GATHER
        # (시각, 볼록 렌즈, 색 번짐 px, 굴절 고리 px): 모이는 동안 중심이 부풀며 색이 갈라지고, 터지는 순간 크게 휘며 고리가 퍼진다
        postfx.play([(0.0, 0.0, 0.0, 0.0), (g * 0.95, 0.22, 9.0, 0.0), (g + 0.03, 0.3, 22.0, 46.0), (g + 0.3, 0.06, 10.0, 26.0),
                     (g + 0.75, 0.0, 0.0, 0.0)], sx, sy, ring=(g, 2400.0, 260.0))

    def update(self, dt):
        if self.fresh:
            self.fresh = False
        else:
            self.rt += dt / max(0.05, time_scale())
        if not self.popped and self.rt >= config.OVERLOAD_GATHER:
            self.popped = True
            self.x, self.y = self.p.center
            add_trauma(config.SHAKE_OVERLOAD)
            request_flash(config.OVERLOAD_FLASH_POP)
            assets.play_sound('overload_zap')
            spawn_blur(self.x, self.y, config.ZONE_GLOW['OVERLOAD'], self.p)
        if self.rt >= config.OVERLOAD_GATHER + self.BURST:
            game_world.remove_object(self)

    def draw(self):
        g = config.OVERLOAD_GATHER
        if self.rt < g:                                               # 모이는 동안: 어두워지고 기운이 빨려든다
            import camera
            k = self.rt / g
            left, bottom = camera.to_world(0, 0)
            assets.draw_rect_color(left - 16, bottom - 16, config.SCREEN_W + 32, config.SCREEN_H + 32, (6, 0, 4),
                                   0.72 * min(1.0, k * 2.5) * (0.6 if options.reduce_flash else 1.0))
            self.p.draw()                                             # 주인공은 어둠 위로
            draw_sheet_at('overload-gather', *self.p.center, k)
        else:
            draw_sheet_at('overload-burst', self.x, self.y, (self.rt - g) / self.BURST)


def spawn_flare(x, y, color, big=False, line=False, small=False):
    """별 섬광: 큰 색 빛 원반 + 흰 여덟 갈래 별 + 불티. big은 1.5배가 아니라 정수 3배, line이면 화면을 가르는 빛줄기도."""
    if small:                                                         # 보통 타격: 작은 별 하나와 옅은 빛
        game_world.add_object(TintFx('flare-s', x, y, color), game_world.LAYER_EFFECT)
        game_world.add_object(Bloom(x, y, color, False, 0.2, 0.9), game_world.LAYER_EFFECT)
        return
    game_world.add_object(TintFx('flare', x, y, color, scale=3 if big else 2), game_world.LAYER_EFFECT)
    for _ in range(3 if big else 2):                                  # 진한 색 빛 원반 (겹쳐서 진하게)
        game_world.add_object(Bloom(x, y, color, True, 0.34, 1.0), game_world.LAYER_EFFECT)
    if line:
        game_world.add_object(ScreenLine(x, y, color), game_world.LAYER_EFFECT)


def spawn_bloom(x, y, color, big=False, life=0.16, strength=1.0):
    game_world.add_object(Bloom(x, y, color, big, life, strength), game_world.LAYER_EFFECT)


def spawn_kill(x, y, dir_x, dir_y, color):
    """처치 연출: 큰 빛 번짐 + 가로지르는 베는 선 + 짧은 화면 번쩍임 + 짧은 멈춤."""
    spawn_bloom(x, y, (255, 255, 255), big=True, life=0.22, strength=1.0)
    spawn_bloom(x, y, color, big=True, life=0.32, strength=0.7)
    game_world.add_object(KillSlash(x, y, dir_x, dir_y, color), game_world.LAYER_EFFECT)
    if not options.reduce_flash:
        request_flash(config.KILL_FLASH)
    request_hit_stop(config.KILL_STOP)


class SlamChip:
    """땅 강타 파편: 2배 픽셀 사각 조각이 튀어 올랐다가 중력으로 떨어지며 사라진다."""
    GRAVITY = -1800.0

    def __init__(self, x, y, vx, vy, color, size, life):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.color, self.size, self.life, self.time = color, size, life, 0.0

    def update(self, dt):
        self.time += dt
        self.vy += self.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.time >= self.life:
            game_world.remove_object(self)

    def draw(self):
        s = self.size
        assets.draw_rect_color(int(self.x) // 2 * 2, int(self.y) // 2 * 2, s, s, self.color)


SLAM_DEBRIS = ((92, 84, 78), (140, 128, 116), (60, 56, 54))     # 돌·쇳가루 색


def ground_slam(x, floor_y, power=1.0, color=(255, 200, 140)):
    """v7 무게감: 무거운 공격이 땅을 칠 때. 강한 흔들림 + 양옆 먼지 + 튀는 파편 + 바닥 빛 번짐 (power 1 = 보통 강타)."""
    add_trauma(config.SHAKE_SLAM * power)
    for side in (-1, 1):
        spawn('dust-land', x + side * 60 * power, floor_y, flip=side < 0, duration=0.35)
    spawn('quake-blast', x, floor_y, duration=0.46)                    # v8: 사각 파편 대신 구운 바닥 충격 (가시·누운 고리·도는 돌 조각)
    spawn_bloom(x, floor_y + 20, color, big=power >= 1.2, life=0.22, strength=0.7)


ABSORB_COLORS = {'shard': (110, 245, 230), 'gauge': (255, 255, 255)}
ABSORB_GLOW = 0.16          # 입자가 닿을 때 주인공 몸이 빛나는 시간(초)


class AbsorbOrb:
    """v7 흡수 연출 (2026-11-24 사용자 피드백으로 강화): 처치 자리에서 입자 여러 개가 사방으로 튀었다가,
    휘어지며 주인공을 쫓아와 몸에 닿는다. 꼬리를 남기고 둘레에 작은 빛이 있다. 닿으면 몸이 빛나고(player.absorb_glow)
    음이 오르는 소리가 나며, 마지막 입자가 닿으면 마무리 소리(absorb_done)와 큰 빛.
    조각(청록 마름모)·게이지(흰 빛) 수치는 처치 순간 이미 올랐다. 이건 보이는 것과 소리뿐이다."""
    BURST = 0.18
    TRAIL = 6

    def __init__(self, x, y, player, kind, group, rng):
        self.x, self.y, self.player, self.kind, self.group = x, y, player, kind, group
        ang = rng.uniform(0, math.tau)
        speed = rng.uniform(320, 720)
        self.vx, self.vy = math.cos(ang) * speed, math.sin(ang) * speed + 220
        self.swirl = rng.choice((-1, 1)) * rng.uniform(0.6, 1.2)      # 곧장 오지 않고 휘어 들어온다
        self.time = -rng.uniform(0.0, 0.06)                            # 조금씩 엇갈려 출발
        self.trail = []

    def update(self, dt):
        self.time += dt
        self.trail.append((self.x, self.y))
        del self.trail[:-self.TRAIL]
        if self.time < self.BURST:                      # 퍼지며 느려진다
            self.vx *= 0.88
            self.vy *= 0.88
        else:                                           # 점점 빨라지며 몸 가운데로 (옆으로 휘는 힘은 점점 준다)
            tx, ty = self.player.center
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy) or 1.0
            if dist < 30 or self.time > 1.4:
                self._arrive()
                return
            k = min(1.0, (self.time - self.BURST) / 0.4)
            speed = 500 + 2600 * k
            side = self.swirl * (1.0 - k) * speed * 0.6
            want_x = dx / dist * speed - dy / dist * side
            want_y = dy / dist * speed + dx / dist * side
            self.vx += (want_x - self.vx) * min(1.0, 10 * dt)
            self.vy += (want_y - self.vy) * min(1.0, 10 * dt)
        self.x += self.vx * dt
        self.y += self.vy * dt

    def _arrive(self):
        game_world.remove_object(self)
        g = self.group
        g['arrived'] += 1
        p = self.player
        p.absorb_glow = ABSORB_GLOW
        cx, cy = p.center
        color = ABSORB_COLORS[self.kind]
        if g['arrived'] >= g['total']:                  # 마지막 입자: 마무리 소리 + 큰 빛
            assets.play_sound('absorb_done')
            spawn_bloom(cx, cy, (150, 255, 240), big=True, life=0.22, strength=0.55)
        else:
            if g['arrived'] % 2 == 1:                   # 소리는 두 개에 하나 (많이 겹치면 지저분하다), 차례대로 음이 오른다
                assets.play_sound(f'absorb_{min(5, (g["arrived"] + 1) // 2)}')
            spawn_bloom(cx, cy, color, life=0.12, strength=0.3)

    def draw(self):
        color = ABSORB_COLORS[self.kind]
        img = assets.image('light/dot_48.png')
        img.opacify(0.9)
        assets.draw_image_added(img, int(self.x), int(self.y) - img.h // 2, color=color, times=1)
        img.opacify(1.0)
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):       # 꼬리: 뒤로 갈수록 작고 옅다 (2배 픽셀 격자)
            draw_dot(tx, ty, color, 0, alpha=0.25 + 0.5 * i / n, glow=False)
        x, y = int(self.x) // 2 * 2, int(self.y) // 2 * 2
        if self.kind == 'shard':                        # 조각: 청록 마름모(사각 2단)
            assets.draw_rect_color(x - 2, y - 8, 4, 16, color)
            assets.draw_rect_color(x - 8, y - 2, 16, 4, color)
            assets.draw_rect_color(x - 4, y - 4, 8, 8, (235, 255, 252))
        else:                                           # 게이지: 흰 빛 알갱이
            draw_dot(x, y, color, 1, glow=False)


def spawn_absorb(x, y, player, shards, gauge_orbs=3):
    """처치 순간 조각 하나에 입자 둘(최대 12)과 게이지 입자(gauge_orbs x 2)를 흩뿌린다. 소리는 닿는 차례대로 음이 오른다."""
    if player is None:
        return
    rng = random.Random(int(x) * 7 + int(y))
    kinds = ['shard'] * min(12, shards * 2) + ['gauge'] * (gauge_orbs * 2)
    group = {'total': len(kinds), 'arrived': 0}
    for kind in kinds:
        game_world.add_object(AbsorbOrb(x, y, player, kind, group, rng), game_world.LAYER_EFFECT)
