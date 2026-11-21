"""상황에 따른 극적인 연출과 타격감 (2026-11-21 사용자 요청). pico2d 없이 돌아가는 규칙 + 그리기.

- 효과음 고르기: 식칼·사슬은 게이지 구간과 강화에 따라(knife_sound, chain_sound, latch_sound), 궁극기 마무리는 무기마다.
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
              'ult_final_pipe', 'ult_final_knife', 'ult_final_gauntlet', 'ult_final_chain',
              'zone_awake', 'heartbeat', 'kill_last')

# ----- 효과음 고르기 -----
_ZONE_SUFFIX = {'FADE': '_fade', 'NORMAL': '', 'AWAKE': '_awake', 'CRITICAL': '_critical', 'OVERLOAD': '_critical', 'DEAD': '_fade'}


def knife_sound(zone, enhanced):
    return 'throw_enhanced' if enhanced else 'throw' + _ZONE_SUFFIX.get(zone, '')


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


def tick(dt, player):
    """매 프레임(play_mode): 번쩍임이 줄고, 심장이 뛴다."""
    import assets
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
        return DAMAGE_COLORS['ENHANCED']
    return DAMAGE_COLORS.get(g.zone, DAMAGE_COLORS['NORMAL'])


class DamageNumber:
    """맞은 자리에 떠오르는 피해 숫자 (세계 좌표, 효과 레이어). 반투명 없이 끝에 깜빡이다 사라진다."""

    def __init__(self, x, y, damage, color):
        self.x, self.y0 = x + random.uniform(-14, 14), y
        self.text, self.color = str(int(round(damage))), color
        self.big = damage >= BIG_DAMAGE
        self.time = 0.0

    def update(self, dt):
        import game_world
        self.time += dt
        if self.time >= NUMBER_LIFE:
            game_world.remove_object(self)

    def draw(self):
        import assets
        t = self.time / NUMBER_LIFE
        if t > 0.75 and int(self.time * 30) % 2:            # 끝에서 깜빡이며 사라진다
            return
        rise = NUMBER_RISE * (1 - (1 - t) ** 2)              # 빨리 솟았다가 멈춘다
        assets.draw_text(int(self.x), int(self.y0 + rise), self.text, self.color, center=True, big=self.big)


def damage_number(target, damage, player):
    """적이 맞았다: 피해 숫자를 띄운다 (설정에서 끄면 띄우지 않는다)."""
    if not options.show_damage or damage <= 0:
        return
    import game_world
    top = target.y + getattr(target, 'hb_h', 100) + 12
    game_world.add_object(DamageNumber(target.x, top, damage, damage_color(player)), game_world.LAYER_EFFECT)
