"""화면 UI(HUD) v4 (2026-11-22 전면 수정: 출시작처럼 읽히게 — 던그리드·하데스·데드셀 배치 참고).

배치 (1920x1080, 네 귀퉁이와 위 가운데만 쓴다. 화면 가운데는 비운다):
  * 왼쪽 위  = 생존: 체력 막대(깎인 자국이 따라 줄어든다)·숫자, 대시 칸, 가진 업그레이드 줄. 그 아래 처음 안내 카드(tutorial).
  * 가운데 위 = 헤이즈 게이지(구간 색·경계 숫자) + 아래 한 줄에 구간 이름·%·배율·강화 상태. 보스가 있으면 그 아래 얇은 보스 막대.
  * 오른쪽 위 = 미니맵 + 아래 칩(헤이즈 조각, 남은 적 수, 고농도 방).
  * 오른쪽 아래 = 행동 칸: E 강화 칸(단계 점·남은 시간) / 무기 두 칸(든 무기는 밝은 테두리, 다른 칸은 어둡게 + Q).
    칸 위에 지금 나가는 공격과 재충전 막대, 무기마다 다른 표시(콤보·충전·발사 수).
  * 화면 가운데: 방 클리어·짧은 알림은 잠깐 떴다 사라지는 글자만(판 없이). 큰 띠를 늘 띄우지 않는다.
글자는 그림자가 있고, 중요한 숫자는 보통 크기(28px) 이상. 색만으로 뜻을 전하지 않는다(구간 이름, 키 글자, 아이콘).
부품 그림은 tools/make_ui.py(판·막대·칸·키)와 tools/make_hud.py(조준점·미니맵 아이콘·하트)가 만든다.
"""
import math

import assets
import camera
import config
import effects
import hud_kit as kit
import options
from haze_gauge import AWAKE, CRITICAL, DEAD, FADE, NORMAL, OVERLOAD

ZONE_LABEL = {FADE: '페이드', NORMAL: '노멀', AWAKE: '각성', CRITICAL: '위험', OVERLOAD: '오버로드', DEAD: '사망'}
ZONE_COLOR = {FADE: (240, 96, 104), NORMAL: (130, 170, 235), AWAKE: (110, 225, 245),
              CRITICAL: (250, 165, 80), OVERLOAD: (250, 220, 90), DEAD: (240, 96, 104)}
ZONE_FILL = {FADE: 'red', NORMAL: 'blue', AWAKE: 'cyan', CRITICAL: 'orange'}
WHITE = (235, 240, 250)
TEAL = (130, 235, 225)
DIM = (150, 165, 190)
FAINT = (105, 118, 145)
GOLD = (255, 225, 120)
RED = (245, 120, 130)
INK = (8, 11, 20)            # 막대 받침·테두리 (불투명)

W, H = config.SCREEN_W, config.SCREEN_H
MARGIN = 28
# 왼쪽 위: 체력
HP_X, HP_Y, HP_W, HP_H = MARGIN + 40, H - 64, 380, 26
DASH_Y = HP_Y - 44
ITEM_Y = DASH_Y - 70
HINT_TOP = ITEM_Y - 24                   # 처음 안내 카드의 위 가장자리 (tutorial이 쓴다)
# 가운데 위: 게이지
BAR_W, BAR_H = 760, 22
BAR_X, BAR_Y = (W - BAR_W) // 2, H - 58
LABEL_Y = BAR_Y - 30                     # 구간 이름 줄 (글자 가운데)
BOSS_W, BOSS_H = 960, 16
BOSS_Y = LABEL_Y - 86                    # 보스 막대 (이름은 그 위 줄)
TOAST_Y = H - 330                        # 방 클리어·짧은 알림 (화면 위쪽 1/3)
# 오른쪽 아래: 행동 칸
SLOT = 92
ACT_Y = 24
ACT_RIGHT = W - MARGIN
# 옛 이름 (다른 모듈이 기대던 값)
NOTICE_Y = TOAST_Y


# ----- 보스 체력 막대 (퀄리티 계획 4-4) -----
BOSS_GHOST_HOLD = 0.35      # 맞은 뒤 이만큼은 깎인 부분이 밝게 남는다(초)
BOSS_GHOST_SPEED = 0.5      # 그다음 초당 이만큼(체력 비율) 따라 준다
BOSS_EPITHET = {'crasher': '용광로의 파수꾼', 'ark': '헤이즈 탑의 총감시관', 'heart': '탑의 진짜 주인'}


PICKUP_TIME = 2.8          # 아이템 띠를 보여 주는 시간(초)
PICKUP_W, PICKUP_H, PICKUP_Y = 760, 96, 150


def ghost_step(ghost, ratio, dt, held=0.0):
    """깎인 체력 자국(ghost)이 지금 체력(ratio)을 따라간다. held = 마지막으로 맞은 뒤 지난 시간."""
    if ratio >= ghost:
        return ratio
    if held < BOSS_GHOST_HOLD:
        return ghost
    return max(ratio, ghost - BOSS_GHOST_SPEED * dt)


def boss_phase_marks(kind):
    """페이즈가 바뀌는 체력 비율 (막대 위 눈금)."""
    if kind == 'heart':
        return sorted(config.HEART['phases'])
    return sorted(config.ARK_PHASES) if kind == 'ark' else [0.5]


def _strip(x, y, w, h, color=INK):
    """막대 받침: 1px 밝은 테두리 + 어두운 속 (불투명)."""
    assets.draw_rect_color(int(x) - 3, int(y) - 3, int(w) + 6, int(h) + 6, (46, 56, 82))
    assets.draw_rect_color(int(x) - 2, int(y) - 2, int(w) + 4, int(h) + 4, color)


keycap = kit.keycap


class GameUI:
    def __init__(self, player, stage=None):
        self.player = player
        self.stage = stage
        self.pickup = None          # (이름, 효과 글, 아이콘, 남은 시간): 아이템을 얻었을 때 화면 아래 띠
        self.boss_ref = None
        self.boss_ghost = 1.0
        self.boss_last = 1.0
        self.boss_held = 0.0
        self.hp_ghost = 1.0         # 플레이어 체력의 깎인 자국
        self.hp_last = 1.0
        self.hp_held = 1.0

    def show_pickup(self, item_id, text):
        import items
        self.pickup = (items.ITEMS[item_id]['name'], text, items.icon_path(item_id), PICKUP_TIME)

    def update(self, dt):
        if self.pickup is not None:
            name, text, icon, left = self.pickup
            self.pickup = (name, text, icon, left - dt) if left - dt > 0 else None
        p = self.player
        ratio = max(0.0, p.hp) / max(1, p.max_hp)
        self.hp_held = 0.0 if ratio < self.hp_last else self.hp_held + dt
        self.hp_last = ratio
        self.hp_ghost = ghost_step(self.hp_ghost, ratio, dt, self.hp_held)
        boss = self.stage.boss if self.stage is not None else None
        if boss is None:
            self.boss_ref = None
            return
        ratio = max(0.0, boss.hp) / boss.max_hp
        if boss is not self.boss_ref:                       # 새 보스: 자국 없이 시작
            self.boss_ref, self.boss_ghost, self.boss_last, self.boss_held = boss, ratio, ratio, 1.0
        if ratio < self.boss_last:
            self.boss_held = 0.0
        else:
            self.boss_held += dt
        self.boss_last = ratio
        self.boss_ghost = ghost_step(self.boss_ghost, ratio, dt, self.boss_held)

    def draw(self):
        self._draw_screen_fx()          # 화면 전체 효과(오버로드 섬광, 기절 비네트)는 HUD 아래에 깐다
        self._draw_gauge()
        self._draw_vitals()
        self._draw_actions()
        if self.stage is not None:
            self._draw_minimap()
            self._draw_boss_bar()
            self._draw_toasts()
        self._draw_pickup()
        self._draw_reticle()
        if config.DEBUG:
            self._draw_debug()

    # ----- 화면 전체 효과 (오버로드 / 기절) -----
    def _draw_screen_fx(self):
        p = self.player
        if effects.flash_left > 0:                              # 오버로드 순간: 화면 전체가 하얗게 번쩍였다가 가라앉는다
            a = min(1.0, effects.flash_left / config.OVERLOAD_FLASH) ** 1.6
            assets.draw_rect_color(0, 0, W, H, (255, 255, 255), 0.9 * a * options.flash_mult())   # 접근성: 번쩍임 줄이기
        if not p.stunned:
            return
        t = p.aura_time
        pulse = 0.5 + 0.5 * math.sin(t * 14)                    # 맥동
        assets.draw_rect_color(0, 0, W, H, (255, 150, 60), 0.06 + 0.05 * pulse)      # 화면 전체 주황 틴트
        for i in range(6):                                      # 가장자리 붉은 비네트: 안쪽으로 갈수록 옅다 (계단식)
            inset, thick = i * 26, 26
            a = 0.34 * (1 - i / 6) * (0.65 + 0.35 * pulse)
            c = (255, 70, 50)
            assets.draw_rect_color(0, H - inset - thick, W, thick, c, a)                  # 위
            assets.draw_rect_color(0, inset, W, thick, c, a)                              # 아래
            assets.draw_rect_color(inset, 0, thick, H, c, a)                              # 왼쪽
            assets.draw_rect_color(W - inset - thick, 0, thick, H, c, a)                  # 오른쪽
        seed = int(t * 20)                                      # 전기 노이즈 줄: 20Hz로 자리가 바뀌는 얇은 가로줄
        for k in range(0 if options.reduce_flash else 7):       # 번쩍임 줄이기면 깜빡이는 줄을 그리지 않는다
            y = (seed * 97 + k * 163) % H
            assets.draw_rect_color(0, y, W, 3 + ((seed + k) % 3) * 2, (255, 242, 170), 0.15)
        shake = int(round(4 * math.sin(t * 70)))
        kit.text(W // 2 + shake, TOAST_Y + 60, '오버로드!', (255, 235, 120), center=True, big=True)
        bw = 420                                                # 기절 남은 시간
        bx, by = (W - bw) // 2, TOAST_Y - 10
        kit.bar('yellow', bx, by, bw, 12, p.gauge.stun_timer / config.OVERLOAD_STUN)
        kit.text(W // 2, by - 22, f'기절 {p.gauge.stun_timer:.1f}s', (255, 240, 150), small=True, center=True)

    # ----- 가운데 위: 헤이즈 게이지 -----
    def _x_of(self, value):
        return BAR_X + BAR_W * min(value, self.player.gauge.cap) / self.player.gauge.cap

    def _bounds(self):
        g = self.player.gauge
        return [(0, config.ZONE_FADE_MAX, FADE), (config.ZONE_FADE_MAX, config.ZONE_NORMAL_MAX, NORMAL),
                (config.ZONE_NORMAL_MAX, g.cap - config.CRITICAL_MARGIN, AWAKE),
                (g.cap - config.CRITICAL_MARGIN, g.cap, CRITICAL)]

    def _draw_gauge(self):
        g = self.player.gauge
        if g.zone in (FADE, CRITICAL):                           # 양끝 위험 구간: 게이지 둘레가 맥박처럼 깜빡인다
            pulse = 0.5 + 0.5 * math.sin(self.player.aura_time * (9 if g.zone == CRITICAL else 6))
            if pulse > 0.5:
                assets.draw_rect_color(BAR_X - 8, BAR_Y - 8, BAR_W + 16, BAR_H + 16, ZONE_COLOR[g.zone])
        _strip(BAR_X, BAR_Y, BAR_W, BAR_H)
        bounds = self._bounds()
        for lo, hi, zone in bounds:                              # 구간마다 빈 칸 위에 자기 색으로 채운다
            x0, x1 = round(self._x_of(lo)), round(self._x_of(hi))
            kit.fill('empty', x0, BAR_Y + 1, x1 - x0, BAR_H - 2 if BAR_H - 2 in kit.FILL_HEIGHTS else 20)
            filled = min(g.value, hi) - lo
            if filled > 0:
                kit.fill(ZONE_FILL[zone], x0, BAR_Y + 1, round(self._x_of(lo + filled)) - x0, 20)
        for lo, _hi, _zone in bounds[1:]:                        # 구간 경계 눈금 (막대 위아래로 조금 튀어나온다)
            x = round(self._x_of(lo))
            assets.draw_rect_color(x - 1, BAR_Y - 5, 3, BAR_H + 10, (46, 56, 82))
            assets.draw_rect_color(x, BAR_Y - 4, 1, BAR_H + 8, INK)
        kit.icon('ui_gauge_end_l', BAR_X - 44, BAR_Y - 21)
        kit.icon('ui_gauge_end_r', BAR_X + BAR_W, BAR_Y - 21)
        kit.icon('ui_marker', round(self._x_of(g.value)) - 8, BAR_Y - 9)   # 현재 값 바늘
        # 아래 한 줄: [구간 이름 %] [배율] [강화 상태]
        label = f'{ZONE_LABEL[g.zone]} {int(g.value)}%'
        mult = g.zone_multipliers()
        extra = '' if g.zone == NORMAL else f'공격 x{mult["attack"]:g} · 이동 x{mult["speed"]:g}'
        if g.enhanced:
            lv = max(1, min(3, g.enhance_level))
            extra = '궁극기 준비!' if g.enhance_level >= config.ENHANCE_MAX_LEVEL else f'강화 {g.enhance_level}단계 준비'
            ecolor = config.ENHANCE_LEVEL_COLOR[lv]
        else:
            ecolor = DIM
        lw = assets.text_width(label, False)
        ew = assets.text_width(extra, True) + 24 if extra else 0
        x0 = W // 2 - (lw + ew) // 2
        kit.text(x0, LABEL_Y, label, ZONE_COLOR[g.zone])
        if extra:
            kit.text(x0 + lw + 24, LABEL_Y - 1, extra, ecolor, small=True)

    # ----- 왼쪽 위: 체력·대시·업그레이드 -----
    def _draw_vitals(self):
        p = self.player
        kit.icon('hud_heart', MARGIN, HP_Y - 1)
        _strip(HP_X, HP_Y, HP_W, HP_H)
        ratio = max(0.0, p.hp) / max(1, p.max_hp)
        kit.fill('empty', HP_X, HP_Y + 1, HP_W, 24)
        ghost = max(ratio, self.hp_ghost)
        kit.fill('orange', HP_X, HP_Y + 1, int(HP_W * ghost), 24)           # 방금 깎인 만큼
        kit.fill('red', HP_X, HP_Y + 1, int(HP_W * ratio), 24)
        if ratio <= 0.3 and int(p.aura_time * 4) % 2 == 0:                 # 체력이 적으면 테두리가 깜빡인다
            for ox, oy, ww, hh in ((-3, -3, HP_W + 6, 2), (-3, HP_H + 1, HP_W + 6, 2)):
                assets.draw_rect_color(HP_X + ox, HP_Y + oy, ww, hh, (255, 90, 90))
        hp_text = f'{int(p.hp)} / {p.max_hp}'                              # 숫자는 막대 안 오른쪽 (게이지와 겹치지 않게)
        kit.text(HP_X + HP_W - 12, HP_Y + 13, hp_text, WHITE, small=True, right=True)
        for i in range(p.dash_max):                                          # 대시 칸 (충전 중인 칸은 차오른다)
            x = HP_X + i * 60
            kit.icon('hud_dash_on' if i < p.dash_slots else 'hud_dash_off', x, DASH_Y)
            if i == p.dash_slots and p.dash_slots < p.dash_max:
                k = p.dash_charge / max(0.01, p.dash_recharge)
                assets.draw_rect_color(x + 4, DASH_Y - 6, int(46 * k), 4, TEAL)
        self._draw_potions()
        self._draw_items()

    def _draw_potions(self):
        """v7 물약 (Q): 대시 칸 줄 오른쪽 끝에 병 POTION_MAX개. 찬 병은 초록 액체, 빈 병은 테두리만. 2배 픽셀 사각형."""
        p = self.player
        for i in range(config.POTION_MAX):
            x, y = HP_X + 300 + i * 26, DASH_Y + 2
            full = i < p.potions
            ink = (12, 16, 28)
            assets.draw_rect_color(x + 6, y + 30, 8, 6, (150, 110, 70) if full else (70, 60, 56))   # 코르크
            assets.draw_rect_color(x + 4, y + 22, 12, 8, ink)                                       # 목 테두리
            assets.draw_rect_color(x + 6, y + 22, 8, 8, (200, 230, 225) if full else (40, 48, 60))
            assets.draw_rect_color(x, y, 20, 24, ink)                                               # 몸통 테두리
            assets.draw_rect_color(x + 2, y + 2, 16, 20, (70, 220, 140) if full else (34, 40, 54))
            if full:
                assets.draw_rect_color(x + 4, y + 14, 4, 6, (200, 255, 220))                        # 빛 반사

    def _draw_items(self):
        """체력 아래 줄: 가진 업그레이드 아이콘 칸 (같은 것을 여러 번 얻으면 개수)."""
        counts = {}
        for item_id in self.player.items:
            counts[item_id] = counts.get(item_id, 0) + 1
        for i, (item_id, n) in enumerate(counts.items()):
            ix, iy = MARGIN + i * 60, ITEM_Y
            kit.panel('plate', ix, iy, 56, 56)
            kit.icon(f'icon_{item_id}', ix + 4, iy + 4)
            if n > 1:
                kit.text(ix + 46, iy + 10, f'{n}', WHITE, small=True, center=True)

    # ----- 오른쪽 아래: 행동 칸 (E 강화 / 무기 두 칸) -----
    def _draw_actions(self):
        p = self.player
        w, g = p.weapon, p.gauge
        right = ACT_RIGHT
        slots = [p.weapons[0], p.weapons[1]]
        xs = [right - 2 * SLOT - 14, right - SLOT]
        for i, wp in enumerate(slots):                                       # 무기 두 칸
            x, y = xs[i], ACT_Y
            active = i == p.slot
            if active:
                assets.draw_rect_color(x - 4, y - 4, SLOT + 8, SLOT + 8, config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))]
                                       if g.enhanced else TEAL)
            kit.panel('slot_hot' if active else 'slot', x, y, SLOT, SLOT)
            if wp is None:
                kit.text(x + SLOT // 2, y + SLOT // 2, '빈 칸', FAINT, small=True, center=True)
                continue
            img = assets.image(f'ui/icon_w_{wp.weapon_id}.png')
            if active:
                assets.draw_image(img, x + SLOT // 2, y + (SLOT - img.h) // 2)
            else:
                assets.draw_image_tinted(img, x + SLOT // 2, y + (SLOT - img.h) // 2, '', (120, 130, 150), 0.7)
            import keybinds
            keycap(x + 4, y + SLOT - 34, keybinds.label(f'weapon{i + 1}', first=True)[:3], hot=active)
        # E 강화 칸
        ex = xs[0] - SLOT - 26
        ready = g.can_enhance()
        hot = g.enhanced
        if hot:
            assets.draw_rect_color(ex - 4, ACT_Y - 4, SLOT + 8, SLOT + 8, config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))])
        kit.panel('slot_hot' if hot or ready else 'slot', ex, ACT_Y, SLOT, SLOT)
        img = assets.image('ui/icon_enhance.png')
        if hot or ready:
            assets.draw_image(img, ex + SLOT // 2 + 8, ACT_Y + 24)
        else:
            assets.draw_image_tinted(img, ex + SLOT // 2 + 8, ACT_Y + 24, '', (110, 120, 140), 0.6)
        import keybinds
        keycap(ex + 4, ACT_Y + SLOT - 34, keybinds.label('enhance', first=True)[:3], hot=ready or hot)
        for i in range(config.ENHANCE_MAX_LEVEL):                            # 쌓인 단계 점 (칸 아래쪽)
            on = i < g.enhance_level and hot
            color = config.ENHANCE_LEVEL_COLOR[i + 1] if on else (50, 56, 80)
            px = ex + 18 + i * 22
            assets.draw_rect_color(px, ACT_Y + 8, 16, 14, INK)
            assets.draw_rect_color(px + 2, ACT_Y + 10, 12, 10, color)
        if hot:
            assets.draw_rect_color(ex + 6, ACT_Y + 2, int((SLOT - 12) * g.enhance_timer / config.ENHANCE_TIME), 4,
                                   config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))])
        cost = f'-{g.cost}%' if hasattr(g, 'cost') else f'-{config.ENHANCE_COST}%'
        kit.text(ex + SLOT // 2, ACT_Y + SLOT + 18, f'강화 {cost}' if (ready or hot) else f'강화 {g.enhance_min}%+',
                 TEAL if ready else FAINT, small=True, center=True)
        # 칸 위 한 줄: 무기 이름 · 지금 나가는 공격 · 재충전 막대, 그 왼쪽에 무기 표시(콤보·충전·발사 수)
        text, color = self._attack_text(w, g)
        if g.enhanced and g.enhance_level >= config.ENHANCE_MAX_LEVEL:      # 다음 공격이 궁극기: 그 이름
            import weapon as weapon_mod
            text, color = '궁극기 ' + weapon_mod.ULT_NAMES[(w.weapon_id, w.ult_kind())], (255, 200, 120)
        elif g.enhanced:
            text, color = f'강화 {g.enhance_level}단계 ' + text.split(':')[0], config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))]
        top = ACT_Y + SLOT + 44
        kit.text(right, top + 12, text, color, small=True, right=True)
        kit.text(right, top + 46, w.name, WHITE, right=True)
        ratio = 1.0 if w.ready else 1.0 - w.cooldown / max(w.cooldown_max, 0.01)
        bx = xs[0]
        kit.bar('white' if w.ready else 'yellow', bx, ACT_Y + SLOT + 12, right - bx, 8, ratio)
        meter_x = right - assets.text_width(w.name, False) - 24
        self._draw_weapon_meter(meter_x - 130, top + 34)

    def _draw_weapon_meter(self, x, y):
        """무기마다 다른 작은 표시: 철파이프 콤보 3칸, 건틀릿 충전, 사슬 끌 마릿수, 식칼 던질 개수."""
        w = self.player.weapon
        if w.weapon_id == 'pipe':
            for i in range(3):
                lit = i < w.combo
                kit.icon(('ui_combo_fin' if i == 2 else 'ui_combo_on') if lit else 'ui_combo_off', x + 40 + i * 28, y)
        elif w.weapon_id == 'gauntlet':
            r = w.charge_ratio
            kit.bar('cyan' if r >= 1.0 else 'white', x + 10, y + 5, 110, 12, r)
        else:
            count, _, hot = w.grip() if w.weapon_id == 'chain' else w.volley()
            for i in range(min(count, 4)):
                kit.icon('ui_combo_fin' if hot else 'ui_combo_on', x + 20 + i * 26, y)

    @staticmethod
    def _attack_text(w, g):
        """지금 나가는 공격."""
        kind = w.current_kind()
        prefix = {'knife_dash': '대시 ', 'knife_air': '공중 ', 'chain_dash': '대시 ', 'chain_air': '공중 '}.get(kind, '')
        if w.weapon_id == 'knife':
            count, _, pierce = w.volley()
            shape = '관통' if pierce else '부채꼴' if count >= 3 else '투척'
            return f'{prefix}{count}발 {shape}', (255, 225, 120) if prefix else DIM
        if w.weapon_id == 'chain':
            count, _, stun = w.grip()
            text = prefix + ('관통 끌기' if count > 3 else f'{count}마리 끌기')
            return (text + ' · 기절', (255, 225, 120)) if stun else (text, (255, 225, 120) if prefix else DIM)
        if kind in ('gauntlet_dash', 'gauntlet_air'):
            label = '대시' if kind == 'gauntlet_dash' else '공중'
            return f'{label} 충격파 (-{config.GAUNTLET_QUICK_COST}%)', (255, 225, 120)
        if kind == 'charge':
            return f'충전 {int(w.charge_ratio * 100)}% (-{int(config.GAUNTLET_DRAIN)}%/초)', (120, 220, 245)
        if kind == 'gauntlet_instant':
            return f'즉시 발사 (-{config.GAUNTLET_CRIT_COST}%)', (255, 150, 120)
        if kind == 'gauntlet':
            return '누르고 떼면 충격파', DIM
        names = {'pipe': ('기본 3연타', DIM), 'dash': ('대시 평타: 지나온 길 베기', (255, 225, 120)),
                 'spin': ('점프 평타: 회전 베기', (170, 225, 255)), 'plunge': ('내려찍기', (170, 225, 255))}
        return names[kind]

    # ----- 조준점 -----
    def _draw_reticle(self):
        p = self.player
        x, y = p.mouse_screen if p.mouse_screen is not None else camera.to_screen(p.mouse_x, p.mouse_y)
        x, y = int(x), int(y)
        kit.icon('hud_reticle_ready' if p.weapon.ready else 'hud_reticle_wait', x - 28, y - 28)

    # ----- 오른쪽 위: 미니맵 + 칩 -----
    def _draw_minimap(self):
        """방문한 방과 이웃 방. 현재 방은 흰색, 클리어한 방은 청록, 방 종류는 테두리 색과 아이콘. 아래에 칩."""
        cell_w, cell_h, gap = 40, 26, 8
        cells = self.stage.minimap_cells()
        xs = [c[0][0] for c in cells]
        ys = [c[0][1] for c in cells]
        cols, rows = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        pw, ph = cols * (cell_w + gap) + 36, rows * (cell_h + gap) + 36
        px, py = W - MARGIN - pw, H - MARGIN - ph
        kit.panel('panel', px, py, pw, ph)
        base_x, base_y = px + 18 + gap // 2, py + 18 + gap // 2
        colors = {'current': (235, 245, 255), 'cleared': (63, 177, 207), 'visited': (60, 90, 150), 'unknown': (44, 54, 80)}
        borders = {'gold': (242, 210, 116), 'boss': (226, 90, 100), 'shop': (110, 160, 240), 'gate': (240, 150, 60),
                   'rift': (200, 130, 255)}
        for (cx, cy), state, kind, high in cells:
            x = base_x + (cx - min(xs)) * (cell_w + gap)
            y = base_y + (cy - min(ys)) * (cell_h + gap)
            border = borders.get(kind, (240, 150, 60) if high else (11, 16, 32))
            assets.draw_rect_color(x - 3, y - 3, cell_w + 6, cell_h + 6, (11, 16, 32))
            assets.draw_rect_color(x - 2, y - 2, cell_w + 4, cell_h + 4, border)
            assets.draw_rect_color(x, y, cell_w, cell_h, colors[state])
            mark = ({'gate': 'boss', 'rift': 'haze'}.get(kind, kind)) if kind in borders else 'haze' if high else None
            if mark:                                             # 방 종류는 색 테두리와 함께 아이콘으로도 알려 준다
                kit.icon('hud_map_' + mark, x + cell_w // 2 - 10, y + cell_h // 2 - 8)
        self._draw_chips(py - 12)

    def _chip(self, right, top, text, color, icon=None):
        """오른쪽 정렬 칩: 어두운 판 + (아이콘) + 글자. 돌려주는 값은 다음 칩의 위 가장자리."""
        tw = assets.text_width(text, True)
        w = tw + 28 + (30 if icon else 0)
        x, y = right - w, top - 40
        assets.draw_rect_color(x, y, w, 40, (46, 56, 82))
        assets.draw_rect_color(x + 2, y + 2, w - 4, 36, (14, 19, 33))
        if icon:
            kit.icon(icon, x + 10, y + 8)
        kit.text(x + w - 14 - tw, y + 20, text, color, small=True)
        return y - 8

    def _draw_chips(self, top):
        right = W - MARGIN
        top = self._chip(right, top, f'{self.player.shards}', TEAL, icon='ui_shard_s')      # 아이콘 + 숫자만
        room = self.stage.room
        if room.locked:
            top = self._chip(right, top, f'남은 적 {self.stage.enemy_count()}', RED)
        if room.is_high_haze:
            top = self._chip(right, top, '고농도', (150, 240, 230))
        n = len(getattr(self.player, 'mutations', []))
        if n:
            self._chip(right, top, f'변이 {n}', (190, 160, 255))

    # ----- 가운데 위: 보스 체력 (게이지 아래, 판 없이 얇게) -----
    def _draw_boss_bar(self):
        boss = self.stage.boss
        if boss is None or not boss.alive:
            return
        x, y = (W - BOSS_W) // 2, BOSS_Y
        kind = getattr(boss, 'kind', 'crasher')
        title = getattr(boss, 'title', '보스')
        kit.text(x, y + 34, title, (255, 170, 160))
        kit.text(x + assets.text_width(title, False) + 18, y + 32, BOSS_EPITHET.get(kind, ''), FAINT, small=True)
        phase = getattr(boss, 'phase', 1)
        if phase > 1:
            kit.text(x + BOSS_W, y + 32, f'{phase}페이즈', (255, 120, 110), small=True, right=True)
        _strip(x, y, BOSS_W, BOSS_H)
        ratio = max(0.0, boss.hp) / boss.max_hp
        kit.fill('empty', x, y, BOSS_W, 16)
        ghost = self.boss_ghost if self.boss_ref is boss else ratio
        kit.fill('orange', x, y, int(BOSS_W * max(ratio, ghost)), 16)           # 방금 깎인 만큼 (따라 줄어든다)
        kit.fill('boss', x, y, int(BOSS_W * ratio), 16)
        for m in boss_phase_marks(kind):                                   # 페이즈 경계 눈금
            assets.draw_rect_color(x + int(BOSS_W * m) - 1, y - 5, 3, BOSS_H + 10, (235, 240, 250))

    # ----- 가운데: 잠깐 떴다 사라지는 알림 (판 없이 글자만) -----
    def _draw_toasts(self):
        import play_mode
        if play_mode.clear_notice > 0:
            age = 3.0 - play_mode.clear_notice
            rise = int(max(0.0, 0.25 - age) * 120)                         # 아래에서 살짝 올라온다
            y = TOAST_Y + 40 - rise
            text = '방 클리어'
            tw = assets.text_width(text, False, True)
            for side in (-1, 1):                                           # 양옆 장식 선
                x0 = W // 2 + side * (tw // 2 + 30) - (160 if side < 0 else 0)
                assets.draw_rect_color(x0, y - 2, 160, 4, GOLD)
            kit.text(W // 2, y, text, GOLD, center=True, big=True)
            kit.text(W // 2, y - 46, '열린 문으로 이동하세요', (205, 215, 235), small=True, center=True)
        if play_mode.message_time > 0:
            kit.text(W // 2, TOAST_Y - 40, play_mode.message, GOLD, center=True)

    def _draw_pickup(self):
        """아이템을 얻으면 화면 아래 가운데에 아이콘·이름·효과 띠 (아래에서 올라왔다가 내려간다)."""
        if self.pickup is None:
            return
        name, text, icon, left = self.pickup
        age = PICKUP_TIME - left
        k = min(1.0, age / 0.15, left / 0.2)                   # 올라오고 내려가는 정도
        y = int(PICKUP_Y - (1 - k) * (PICKUP_H + PICKUP_Y))
        x = (W - PICKUP_W) // 2
        kit.panel('panel', x, y, PICKUP_W, PICKUP_H)
        img = assets.image(icon)
        assets.draw_image(img, x + 60, y + (PICKUP_H - img.h) // 2)
        kit.text(x + 120, y + PICKUP_H - 34, name, GOLD)
        kit.text(x + 120, y + 26, text, (205, 215, 235), small=True)

    def _draw_debug(self):
        p = self.player
        lines = [
            f'상태 {p.state}  점프 {p.jump_count}/{config.MAX_JUMPS}  바닥 {p.on_ground}',
            f'위치 ({p.x:.0f}, {p.y:.0f})  속도 ({p.vx:.0f}, {p.vy:.0f})',
            f'대시 {p.dash_slots}/{p.dash_max}  충전 {p.dash_charge:.2f}s',
            'F1 디버그  F3 게이지+10  F4 게이지-10  F5 방 재시작  H 피격  Esc 일시정지',
        ]
        for i, text in enumerate(lines):
            kit.text(MARGIN, HINT_TOP - 200 - i * 30, text, (255, 240, 120), small=True)
