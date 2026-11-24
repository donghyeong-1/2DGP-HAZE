"""상황에 따른 극적인 연출과 타격감 (2026-11-21 사용자 요청). pico2d 없이 돌아가는 규칙 + 그리기.

- 효과음 고르기: 쌍권총·사슬은 게이지 구간과 강화에 따라(pistol_sound, chain_sound, latch_sound), 궁극기 마무리는 무기마다.
- 구간이 바뀌면 그 구간 색으로 화면이 잠깐 번쩍인다(on_zone -> zone_flash). 각성에 들어서면 zone_awake.
  번쩍임 줄이기(접근성)를 켜면 options.FLASH_SCALE만큼 약하게.
- 심장 소리: 체력 30% 이하(15% 이하면 더 빠르게)·위험 구간에서 뛴다(tick). 체력이 낮으면 화면 가장자리가 붉게 맥동(low_hp_pulse).
- 페이드 구간에서는 음악을 작게(music_duck) — 기운이 빠진 느낌.
- 피해 숫자(DamageNumber): 적이 맞은 자리에 떠오른다. 구간·강화 색, 큰 피해는 큰 글자. 설정 '피해 숫자'로 끈다.
- 방의 마지막 적: 잠깐 멈춤(LAST_KILL_STOP) + kill_last (play_mode._on_room_cleared).
"""
import math
import random

import options

NEW_SOUNDS = ('throw_fade', 'throw_awake', 'throw_critical', 'throw_enhanced',
              'chain_throw_fade', 'chain_throw_awake', 'chain_throw_critical', 'chain_throw_enhanced', 'chain_latch_heavy',
              'ult_final_pipe', 'ult_final_pistol', 'ult_final_gauntlet', 'ult_final_chain',
              'zone_awake', 'heartbeat', 'kill_last')

# ----- 효과음 고르기 -----
_ZONE_SUFFIX = {'FADE': '_fade', 'NORMAL': '', 'AWAKE': '_awake', 'CRITICAL': '_critical', 'OVERLOAD': '_critical', 'DEAD': '_fade'}


def pistol_sound(zone, enhanced):
    """쌍권총 사격 소리 (v7): 강화 = 큰 한 발, 그 밖은 구간마다."""
    return 'shot_big' if enhanced else 'shot' + _ZONE_SUFFIX.get(zone, '').replace('_critical', '_critical')


def chain_sound(zone, enhanced):
    return 'chain_throw_enhanced' if enhanced else 'chain_throw' + _ZONE_SUFFIX.get(zone, '')


def latch_sound(zone, enhanced):
    return 'chain_latch_heavy' if enhanced or zone in ('CRITICAL', 'OVERLOAD') else 'chain_latch'


# ----- 구간 번쩍임 -----
ZONE_FLASH = {'FADE': ((70, 90, 160), 0.22), 'NORMAL': ((200, 214, 235), 0.10), 'AWAKE': ((80, 230, 215), 0.24),
              'CRITICAL': ((255, 80, 50), 0.30)}
FLASH_TIME = 0.35
_flash = [(0, 0, 0), 0.0, 0.0]          # 색, 최대 세기, 남은 시간


def on_zone(zone):
    import assets
    color, k = ZONE_FLASH.get(zone, ((0, 0, 0), 0.0))
    _flash[:] = [color, k * options.flash_mult(), FLASH_TIME]
    if zone == 'AWAKE':
        assets.play_sound('zone_awake')


def zone_flash():
    """(색, 지금 세기 0~1)."""
    color, k, left = _flash
    return color, (k * left / FLASH_TIME if left > 0 else 0.0)


# ----- 심장 소리·붉은 가장자리 -----
HEART_SLOW, HEART_FAST, HEART_CRITICAL = 0.85, 0.55, 0.7
LOW_HP = 0.3
_beat = [0.0]


def heartbeat_interval(hp_ratio, zone):
    """심장이 뛰는 간격(초). 안 뛰면 None."""
    out = []
    if hp_ratio <= LOW_HP / 2:
        out.append(HEART_FAST)
    elif hp_ratio <= LOW_HP:
        out.append(HEART_SLOW)
    if zone == 'CRITICAL':
        out.append(HEART_CRITICAL)
    return min(out) if out else None


def low_hp_pulse(hp_ratio, t):
    """체력이 낮을 때 붉은 가장자리 세기(0~1). 낮을수록 진하고 심장 박자에 맞춰 맥동(번쩍임 줄이기면 맥동 없이)."""
    if hp_ratio > LOW_HP:
        return 0.0
    base = 0.35 + 0.45 * (LOW_HP - max(0.0, hp_ratio)) / LOW_HP
    if options.reduce_flash:
        return base
    period = HEART_FAST if hp_ratio <= LOW_HP / 2 else HEART_SLOW
    return base * (0.55 + 0.45 * math.exp(-((t % period) * 9)))


def music_duck(zone):
    """구간별 음악 크기 배율: 페이드는 먹먹하게."""
    return 0.55 if zone in ('FADE', 'DEAD') else 1.0


def reset():
    _flash[:] = [(0, 0, 0), 0.0, 0.0]
    _beat[0] = 0.0
    _recent.clear()
    style.clear()
    _streak[:] = [0, -99.0]


# ----- 연속 처치 (v7, 2026-11-24 사용자: 이어 잡을수록 소리가 좋아지면 잡는 맛) -----
STREAK_WINDOW = 2.2     # 이 시간 안에 다음 적을 잡으면 단계가 오른다
STREAK_MAX = 6          # 소리 단계 수 (assets/sfx/kill_streak_1~6.wav, tools/make_sfx.py)
_streak = [0, -99.0]    # [지금 단계, 마지막 처치 시각]


def hit_sound(kind):
    """적이 맞을 때의 재질 소리 이름 (config.HIT_MATERIAL, 없으면 예전 공통 소리)."""
    import config
    mat = config.HIT_MATERIAL.get(kind)
    return f'hit_{mat}' if mat else 'enemy_hit'


def kill_streak():
    """적을 처치했다: 연속 처치 단계를 올리고 그 단계의 처치 소리를 낸다. 단계를 돌려준다."""
    import assets
    now = _clock[0]
    _streak[0] = min(STREAK_MAX, _streak[0] + 1) if now - _streak[1] <= STREAK_WINDOW else 1
    _streak[1] = now
    assets.play_sound(f'kill_streak_{_streak[0]}')
    return _streak[0]


def tick(dt, player):
    """매 프레임(play_mode): 번쩍임이 줄고, 심장이 뛴다."""
    import assets
    _clock[0] += dt
    _flash[2] = max(0.0, _flash[2] - dt)
    if player is None or player.state == 'DEAD':
        _beat[0] = 0.0
        return
    interval = heartbeat_interval(player.hp / max(1, player.max_hp), player.gauge.zone)
    if interval is None:
        _beat[0] = 0.0
        return
    _beat[0] -= dt
    if _beat[0] <= 0:
        assets.play_sound('heartbeat')
        _beat[0] += interval
        if _beat[0] <= 0:
            _beat[0] = interval


# ----- 피해 숫자 -----
DAMAGE_COLORS = {'FADE': (150, 165, 200), 'NORMAL': (240, 244, 252), 'AWAKE': (110, 240, 225),
                 'CRITICAL': (255, 140, 90), 'ENHANCED': (215, 170, 255)}
BIG_DAMAGE = 40
NUMBER_LIFE, NUMBER_RISE = 0.65, 56
LAST_KILL_STOP = 0.12


def damage_color(player):
    g = getattr(player, 'gauge', None)
    if g is None:
        return DAMAGE_COLORS['NORMAL']
    if getattr(g, 'enhanced', False):
        import config
        return config.ENHANCE_LEVEL_COLOR.get(min(3, max(1, g.enhance_level)), DAMAGE_COLORS['ENHANCED'])
    return DAMAGE_COLORS.get(g.zone, DAMAGE_COLORS['NORMAL'])


STACK_WINDOW = 0.45     # 같은 적에게 이 시간 안에 이어 맞으면 숫자가 위로 쌓인다(다단 히트)
STACK_STEP = {False: 40, True: 50}     # 숫자 칸 높이(35·45)보다 조금 넓게 (겹치지 않게)
DIGITS = '0123456789+-%'                # 숫자 글꼴 시트의 글자 순서 (tools/make_digits.py ORDER)
_clock = [0.0]
_recent = {}            # id(적) -> (마지막으로 맞은 시각, 쌓인 수)
style = {}              # 지금 때리는 공격의 숫자 모양: big(큰 숫자), color(색). 무기가 take_damage 앞뒤로 정한다


class DamageNumber:
    """맞은 자리에 튀어 오르는 피해 숫자 (세계 좌표, 효과 레이어). 전용 픽셀 글꼴(assets/ui/dmg_tiny·small·big)에
    색을 곱해 그린다. 처음 0.07초는 조금 위에서 '톡' 튀고, 솟았다가 멈춘 뒤 끝에서 깜빡이며 사라진다.
    큰 숫자는 처음 0.12초 좌우로 떨린다. 반투명 없이 그린다.
    v7: 게이지 증감(+3%)도 같은 글꼴의 작은 판(size='tiny')으로 띄운다 (gauge_number)."""

    def __init__(self, x, y, damage, color, big=None, stack=0, text=None, size=None):
        self.big = damage >= BIG_DAMAGE if big is None else bool(big)
        self.size = size or ('big' if self.big else 'small')
        self.x, self.y0 = x + random.uniform(-10, 10), y + STACK_STEP[self.size == 'big'] * stack
        self.text, self.color = text if text is not None else str(int(round(damage))), color
        self.stack = stack
        self.time = 0.0

    def update(self, dt):
        import game_world
        self.time += dt
        if self.time >= NUMBER_LIFE:
            game_world.remove_object(self)

    def offset(self):
        """(dx, dy): 튀어 오르는 움직임."""
        t = self.time
        pop = 10 if t < 0.07 else 0
        rise = NUMBER_RISE * (1 - (1 - min(1.0, t / NUMBER_LIFE)) ** 3)
        shake = int(4 * math.sin(t * 90)) if self.big and t < 0.12 else 0
        return shake, int(rise + pop)

    def draw(self):
        import assets
        if self.time / NUMBER_LIFE > 0.78 and int(self.time * 30) % 2:   # 끝에서 깜빡이며 사라진다
            return
        from sdl2 import SDL_SetTextureColorMod
        img = assets.image(f'ui/dmg_{self.size}.png')
        cw, ch = img.w // len(DIGITS), img.h
        dx, dy = self.offset()
        x = int(self.x) + dx - cw * len(self.text) // 2 + len(self.text)   # 글자끼리 1px 겹쳐 붙인다
        y = int(self.y0) + dy
        SDL_SetTextureColorMod(img.texture, *self.color)
        try:
            for k, ch_ in enumerate(self.text):
                assets.draw_clip(img, DIGITS.index(ch_) * cw, 0, cw, ch, x + k * (cw - 2), y)
        finally:
            SDL_SetTextureColorMod(img.texture, 255, 255, 255)


def damage_number(target, damage, player):
    """적이 맞았다: 피해 숫자를 띄운다 (설정에서 끄면 띄우지 않는다). 공격의 모양(style)과 같은 적에게 이어 맞은 수를 쓴다."""
    if not options.show_damage or damage <= 0:
        return
    import game_world
    key = id(target)
    last, count = _recent.get(key, (-9.0, -1))
    stack = count + 1 if _clock[0] - last <= STACK_WINDOW else 0
    _recent[key] = (_clock[0], stack)
    top = target.y + getattr(target, 'hb_h', 100) + 12
    color = style.get('color') or damage_color(player)
    game_world.add_object(DamageNumber(target.x, top, damage, color, style.get('big'), stack), game_world.LAYER_EFFECT)


def gauge_number(x, y, delta, color):
    """게이지 증감을 피해 숫자와 같은 픽셀 글꼴(작은 판)로 띄운다. 0이 되는 작은 변화는 띄우지 않는다."""
    n = int(round(delta))
    if n == 0:
        return
    import game_world
    game_world.add_object(DamageNumber(x, y, 0, color, big=False, text=f'{n:+d}%', size='tiny'), game_world.LAYER_EFFECT)


class hit_style:
    """with drama.hit_style(big=True, color=...): 그 안의 take_damage가 띄우는 숫자 모양."""

    def __init__(self, big=None, color=None):
        self.new = {k: v for k, v in (('big', big), ('color', color)) if v is not None}

    def __enter__(self):
        self.old = dict(style)
        style.update(self.new)

    def __exit__(self, *exc):
        style.clear()
        style.update(self.old)

