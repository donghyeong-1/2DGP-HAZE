"""화면 UI(HUD) v4 (2026-11-22 전면 수정: 출시작처럼 읽히게 — 던그리드·하데스·데드셀 배치 참고).

배치 (1920x1080, 네 귀퉁이와 위 가운데만 쓴다. 화면 가운데는 비운다):
  * 왼쪽 위  = 생존: 체력 막대(깎인 자국이 따라 줄어든다)·숫자, 대시 칸, 가진 업그레이드 줄. 그 아래 처음 안내 카드(tutorial).
  * 가운데 위 = 헤이즈 게이지(구간 색·경계 숫자) + 아래 한 줄에 구간 이름·%·배율·강화 상태. 보스가 있으면 그 아래 얇은 보스 막대.
  * 오른쪽 위 = 미니맵 + 아래 칩(헤이즈 조각, 남은 적 수, 고농도 방).
  * 오른쪽 아래 = 행동 칸: E 강화 칸(단계 점·남은 시간) / 무기 두 칸(든 무기는 밝은 테두리, 다른 칸은 어둡게 + Q).
    칸 위에 지금 나가는 공격과 재충전 막대, 무기마다 다른 표시(콤보·충전·발사 수).
  * 화면 가운데: 방 클리어·짧은 알림은 잠깐 떴다 사라지는 글자만(판 없이). 큰 띠를 늘 띄우지 않는다.
글자는 그림자가 있고, 중요한 숫자는 보통 크기(28px) 이상. 색만으로 뜻을 전하지 않는다(구간 이름, 키 글자, 아이콘).
2026-11-25 UI 개편(C안 결정형, A안 크기): 부품 그림은 Gemini G06 시트를 tools/apply_ui_parts.py가 구운 assets/ui/uc_*.png.
결정 장식은 게이지 양끝·든 무기 칸·하트 옆·판 모서리에만 둔다. 예전 부품(tools/make_ui.py, make_hud.py)은 아이템·무기 아이콘만 쓴다.
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
ZONE_COLOR = {FADE: (240, 96, 104), NORMAL: (196, 206, 224), AWAKE: (110, 235, 225),
              CRITICAL: (250, 165, 80), OVERLOAD: (250, 220, 90), DEAD: (240, 96, 104)}
ZONE_FILL = {FADE: 'red', NORMAL: 'gray', AWAKE: 'cyan', CRITICAL: 'orange'}    # G06: 노멀은 옅은 회색
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
HP_X, HP_Y, HP_W, HP_H = MARGIN + 44, H - 64, 380, 24      # 속(막대) 자리. 틀 그림 uc_hp_frame은 사방 2px 더 크다
DASH_Y = HP_Y - 32
ITEM_Y = DASH_Y - 76
HINT_TOP = ITEM_Y - 24                   # 처음 안내 카드의 위 가장자리 (tutorial이 쓴다)
# 가운데 위: 게이지
BAR_W, BAR_H = 760, 20                   # 속(막대) 자리. 몸통 틀 uc_gauge_body는 위아래 6px 더 크다
BAR_X, BAR_Y = (W - BAR_W) // 2, H - 58
LABEL_Y = BAR_Y - 32                     # 구간 이름 줄 (글자 가운데). 이름표 띠(높이 40) 안
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
BOSS_EPITHET = {'gatekeeper': '제9구역 관문 간수장', 'crasher': '용광로의 파수꾼', 'ark': '헤이즈 탑의 총감시관', 'heart': '탑의 진짜 주인'}


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
        import boss_intro
        if boss_intro.hud_hidden():     # v8 보스 등장씬 동안은 HUD를 숨긴다 (위아래 검은 띠와 대사만)
            return
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
        import options
        if options.test_mode:                                   # v7 테스트 모드 표시 (화면 아래 가운데)
            kit.text(W // 2, 22, '테스트 모드  무적 · F6 F7 F8 구역 · F9 보스방', (255, 200, 90), small=True, center=True)
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
        # 2026-11-24 사용자: '지지직 화면 전체에 나오는 줄이 너무 별로' -> 주황 틴트·계단 비네트·깜빡이는 가로줄을 없애고,
        # 부드러운 붉은 가장자리가 심장 박자로 조여 왔다 풀리게만 한다 (체력 낮음 경고와 같은 그림, 더 진하게)
        beat = max(0.0, math.sin(t * 7.85)) ** 2                # 약 0.8초에 한 번 뛴다 (오라의 숨과 같은 박자)
        img = assets.image('ui/vignette_red.png')
        img.opacify(min(1.0, 0.5 + 0.4 * beat) * (0.6 if options.reduce_flash else 1.0))
        assets.draw_image(img, W // 2, 0)
        img.opacify(1.0)
        kit.text(W // 2, TOAST_Y + 60, '오버로드!', (255, 120, 128), center=True, big=True)
        bw = 420                                                # 기절 남은 시간
        bx, by = (W - bw) // 2, TOAST_Y - 10
        kit.bar('red', bx, by, bw, 12, p.gauge.stun_timer / config.OVERLOAD_STUN)
        kit.text(W // 2, by - 22, f'기절 {p.gauge.stun_timer:.1f}초', (255, 190, 190), small=True, center=True)

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
                assets.draw_rect_color(BAR_X - 4, BAR_Y - 10, BAR_W + 8, BAR_H + 20, ZONE_COLOR[g.zone])
        body = assets.image('ui/uc_gauge_body.png')              # 몸통 틀: 흰 윗선·밑선 + 남색 그림자, 가로로 이어 붙인다
        for along in range(0, BAR_W, body.w):
            assets.draw_clip(body, 0, 0, min(body.w, BAR_W - along), body.h, BAR_X + along, BAR_Y - 6)
        bounds = self._bounds()
        for lo, hi, zone in bounds:                              # 구간마다 자기 색. 아직 안 찬 부분은 같은 색을 어둡게 덮는다
            x0, x1 = round(self._x_of(lo)) // 2 * 2, round(self._x_of(hi)) // 2 * 2
            kit.fill(ZONE_FILL[zone], x0, BAR_Y, x1 - x0, BAR_H)
            xv = max(x0, min(x1, round(self._x_of(g.value)) // 2 * 2))
            if xv < x1:
                assets.draw_rect_color(xv, BAR_Y, x1 - xv, BAR_H, (13, 18, 31), 0.78)
        for lo, _hi, _zone in bounds[1:]:                        # 구간 경계 눈금: 흰 세로선 (몸통 높이)
            x = round(self._x_of(lo)) // 2 * 2
            assets.draw_rect_color(x - 2, BAR_Y - 6, 4, BAR_H + 12, (242, 246, 250))
        kit.icon('uc_gauge_l', BAR_X - 26, BAR_Y - 15)           # 양끝 결정 첨탑 (왼쪽 빨강 조각 = 페이드, 오른쪽 주황 = 위험)
        kit.icon('uc_gauge_r', BAR_X + BAR_W - 6, BAR_Y - 15)
        kit.icon('uc_needle', round(self._x_of(g.value)) // 2 * 2 - 4, BAR_Y - 12)   # 현재 값 바늘
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
        kit.tag(x0 - 30, LABEL_Y - 20, lw + ew + 60)             # 이름표 띠
        kit.text(x0, LABEL_Y, label, ZONE_COLOR[g.zone])
        if extra:
            kit.text(x0 + lw + 24, LABEL_Y - 1, extra, ecolor, small=True)

    # ----- 왼쪽 위: 체력·대시·업그레이드 -----
    def _draw_vitals(self):
        p = self.player
        kit.icon('uc_heart', MARGIN, HP_Y - 1)
        kit.icon('uc_gem', MARGIN + 26, HP_Y - 10)                           # 하트 옆 작은 결정
        ratio = max(0.0, p.hp) / max(1, p.max_hp)
        kit.fill('empty', HP_X, HP_Y, HP_W, 24)
        ghost = max(ratio, self.hp_ghost)
        kit.fill('orange', HP_X, HP_Y, int(HP_W * ghost) // 2 * 2, 24)       # 방금 깎인 만큼
        kit.fill('red', HP_X, HP_Y, int(HP_W * ratio) // 2 * 2, 24)
        kit.icon('uc_hp_frame', HP_X - 2, HP_Y - 2)                          # 틀: 흰 1점 선, 오른쪽 끝 사선
        if ratio <= 0.3 and int(p.aura_time * 4) % 2 == 0:                 # 체력이 적으면 테두리가 깜빡인다
            for oy in (-2, HP_H + 2):
                assets.draw_rect_color(HP_X - 2, HP_Y + oy, HP_W + 4, 2, (255, 90, 90))
        hp_text = f'{int(p.hp)} / {p.max_hp}'                              # 숫자는 막대 안 오른쪽 (게이지와 겹치지 않게)
        kit.text(HP_X + HP_W - 12, HP_Y + 12, hp_text, WHITE, small=True, right=True)
        for i in range(p.dash_max):                                          # 대시 칸 (충전 중인 칸은 차오른다)
            x = HP_X + i * 34
            kit.icon('uc_dash_on' if i < p.dash_slots else 'uc_dash_off', x, DASH_Y)
            if i == p.dash_slots and p.dash_slots < p.dash_max:
                import mutations
                k = min(1.0, p.dash_charge / max(0.01, mutations.dash_recharge_time(p)))
                assets.draw_rect_color(x + 2, DASH_Y - 6, int(24 * k) // 2 * 2, 2, TEAL)
        self._draw_potions()
        self._draw_items()

    def _draw_potions(self):
        """v7 물약 (Q): 대시 칸 줄 오른쪽 끝(체력 막대 끝에 맞춤)에 병 POTION_MAX개. 찬 병은 빨간 액체, 빈 병은 어두운 병."""
        p = self.player
        for i in range(config.POTION_MAX):
            x = HP_X + HP_W - (config.POTION_MAX - i) * 24
            kit.icon('uc_potion_on' if i < p.potions else 'uc_potion_off', x, DASH_Y - 6)

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
            if active and g.enhanced:                                        # 강화 중: 든 칸 둘레에 단계 색 (평소에는 틀의 청록 이중 선)
                assets.draw_rect_color(x - 4, y - 4, SLOT + 8, SLOT + 8, config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))])
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
            if not active and p.weapons[p.slot] is not None:               # v8 교체기: 이 칸으로 바꾸면 기술이 나간다. 칸 위쪽 막대 = 쿨다운(다 차면 그 무기 색)
                import combo
                ratio = max(0.0, 1.0 - p.swap_cool / max(0.01, getattr(p, 'swap_cool_max', config.SWAP_COOLDOWN)))   # v8 교체 연무는 짧다
                assets.draw_rect_color(x + 6, y + 2, int((SLOT - 12) * ratio) // 2 * 2, 4,
                                       combo.COLORS[wp.weapon_id] if ratio >= 1.0 else (96, 108, 130))
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
            px = ex + 20 + i * 20
            kit.icon('uc_dot_off', px, ACT_Y + 8)                              # 단계 점 자리
            if on:
                assets.draw_rect_color(px + 2, ACT_Y + 10, 6, 6, config.ENHANCE_LEVEL_COLOR[i + 1])
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
            text, color = '궁극기 ' + weapon_mod.ULT_NAMES[w.weapon_id], (255, 200, 120)
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
                kit.icon(('uc_combo_fin' if i == 2 else 'uc_combo_on') if lit else 'uc_combo_off', x + 40 + i * 28, y)
        elif w.weapon_id == 'gauntlet':
            r = w.charge_ratio
            kit.bar('cyan' if r >= 1.0 else 'white', x + 10, y + 5, 110, 12, r)
        else:
            count, _, hot = w.grip() if w.weapon_id == 'chain' else w.volley()
            for i in range(min(count, 4)):
                kit.icon('uc_combo_fin' if hot else 'uc_combo_on', x + 20 + i * 26, y)

    @staticmethod
    def _attack_text(w, g):
        """지금 나가는 공격."""
        kind = w.current_kind()
        import forms
        if forms.active(w) and kind in ('pipe', 'pistol', 'gauntlet', 'chain', 'charge') and not g.enhanced:    # v8 무기 형태: 그 이름
            return '형태: ' + forms.FORMS[w.weapon_id]['name'], forms.COLOR
        prefix = {'pistol_dash': '대시 ', 'pistol_air': '공중 ', 'chain_dash': '대시 ', 'chain_air': '공중 '}.get(kind, '')
        if w.weapon_id == 'pistol':
            count, _, pierce = w.volley()
            shape = '관통' if pierce else '부채꼴' if count >= 3 else '연사'
            return f'{prefix}{count}발 {shape}', (255, 225, 120) if prefix else DIM
        if w.weapon_id == 'chain':
            count, _, stun = w.grip()
            import mutations
            pulls = g.enhanced or mutations.chain_pulls(w.owner)     # v8: 기본은 타격, 모으기 갈래 증강이나 강화면 끌기
            text = prefix + ('관통 ' if count > 3 else f'{count}마리 ') + ('끌기' if pulls else '타격')
            return (text + ' · 기절', (255, 225, 120)) if stun else (text, (255, 225, 120) if prefix else DIM)
        if kind in ('gauntlet_dash', 'gauntlet_air'):
            label = '대시' if kind == 'gauntlet_dash' else '공중'
            return f'{label} 돌진 (-{config.GAUNTLET_QUICK_COST}%)', (255, 225, 120)
        if kind == 'charge':
            return f'충전 {int(w.charge_ratio * 100)}% (-{int(config.GAUNTLET_DRAIN)}%/초)', (120, 220, 245)
        if kind == 'gauntlet_instant':
            return f'즉시 돌진 (-{config.GAUNTLET_CRIT_COST}%)', (255, 150, 120)
        if kind == 'gauntlet':
            return '누르고 떼면 돌진 강타', DIM
        names = {'pipe': ('기본 3연타', DIM), 'dash': ('대시 공격: 관통 베기 · 표식 3개 처형', (255, 225, 120)),
                 'spin': ('점프 공격: 회전 베기', (170, 225, 255)), 'plunge': ('내려찍기', (170, 225, 255))}
        return names[kind]

    # ----- 조준점 -----
    def _draw_reticle(self):
        p = self.player
        x, y = p.mouse_screen if p.mouse_screen is not None else camera.to_screen(p.mouse_x, p.mouse_y)
        x, y = int(x), int(y)
        kit.icon('uc_reticle_ready' if p.weapon.ready else 'uc_reticle_wait', x - 28, y - 28)

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
        kit.panel('plate', px, py, pw, ph)
        base_x, base_y = px + 18 + gap // 2, py + 18 + gap // 2
        colors = {'current': (242, 246, 250), 'cleared': (30, 160, 156), 'visited': (72, 86, 116), 'unknown': (34, 44, 69)}
        borders = {'gold': (242, 210, 116), 'boss': (226, 90, 100), 'shop': (110, 160, 240), 'gate': (240, 150, 60),
                   'rift': (200, 130, 255), 'event': (140, 235, 170)}
        for (cx, cy), state, kind, high in cells:
            x = base_x + (cx - min(xs)) * (cell_w + gap)
            y = base_y + (cy - min(ys)) * (cell_h + gap)
            border = borders.get(kind, (240, 150, 60) if high else (13, 18, 31))
            assets.draw_rect_color(x - 4, y - 4, cell_w + 8, cell_h + 8, (13, 18, 31))
            assets.draw_rect_color(x - 2, y - 2, cell_w + 4, cell_h + 4, border)
            assets.draw_rect_color(x, y, cell_w, cell_h, colors[state])
            mark = ({'gate': 'boss', 'rift': 'haze'}.get(kind, kind)) if kind in borders else 'haze' if high else None   # event: hud_map_event
            if mark:                                             # 방 종류는 색 테두리와 함께 아이콘으로도 알려 준다 (이벤트 방만 예전 그림)
                kit.icon(('hud_map_' if mark == 'event' else 'uc_map_') + mark, x + cell_w // 2 - 10, y + cell_h // 2 - 8)
        self._draw_chips(py - 12)

    def _chip(self, right, top, text, color, icon=None):
        """오른쪽 정렬 칩: 어두운 판 + (아이콘) + 글자. 돌려주는 값은 다음 칩의 위 가장자리."""
        tw = assets.text_width(text, True)
        w = tw + 28 + (30 if icon else 0)
        x, y = right - w, top - 40
        w += w % 2
        x = right - w
        kit.panel('plate', x, y, w, 40)
        if icon:
            kit.icon(icon, x + 14, y + 8)
        kit.text(x + w - 14 - tw, y + 20, text, color, small=True)
        return y - 8

    def _draw_chips(self, top):
        right = W - MARGIN
        top = self._chip(right, top, f'{self.player.shards}', TEAL, icon='uc_shard')      # 아이콘 + 숫자만
        room = self.stage.room
        if room.locked:
            st = self.stage
            wave = f'물결 {st.wave_index}/{st.wave_total} · ' if getattr(st, 'wave_total', 1) > 1 else ''     # v8 물결 전투
            top = self._chip(right, top, f'{wave}남은 적 {st.enemy_count()}', RED)
            ch = getattr(st, 'challenge', None)
            if ch is not None:                                   # v8 도전방: 남은 시간 (다 쓰면 회색)
                left = ch['left']
                text = f'도전 {int(left) // 60}:{int(left) % 60:02d}' if left > 0 else '도전 실패'
                top = self._chip(right, top, text, (255, 214, 120) if left > 10 else RED if left > 0 else (130, 140, 160))
        if room.is_high_haze:
            top = self._chip(right, top, '고농도', (150, 240, 230), icon='uc_diamond')
        n = len(getattr(self.player, 'mutations', []))
        if n:
            self._chip(right, top, f'증강 {n}', (190, 160, 255))

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
        assets.draw_rect_color(x, y - 2, BOSS_W, BOSS_H + 4, (242, 246, 250))   # 위아래 흰 1점 선
        kit.icon('uc_boss_l', x - 6, y - 2)                                   # 양끝 작은 결정
        kit.icon('uc_boss_r', x + BOSS_W, y - 2)
        ratio = max(0.0, boss.hp) / boss.max_hp
        kit.fill('empty', x, y, BOSS_W, 16)
        ghost = self.boss_ghost if self.boss_ref is boss else ratio
        kit.fill('orange', x, y, int(BOSS_W * max(ratio, ghost)), 16)           # 방금 깎인 만큼 (따라 줄어든다)
        kit.fill('boss', x, y, int(BOSS_W * ratio), 16)
        for m in boss_phase_marks(kind):                                   # 페이즈 경계 눈금
            assets.draw_rect_color(x + int(BOSS_W * m) // 2 * 2 - 2, y - 6, 4, BOSS_H + 12, (242, 246, 250))

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
