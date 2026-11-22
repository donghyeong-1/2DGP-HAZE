"""화면 UI(HUD) v3: 헤이즈 게이지, 체력·대시·조각, 무기·공격, 미니맵, 안내 띠, 보스 체력, 조준점.

배치 원칙 (2026-11-18 전면 수정):
  * 화면 아래쪽(바닥·가시가 있는 곳)은 비워 둔다. HUD는 모두 위쪽 세 구역에 둔다:
    왼쪽 위 = 무기 칸·체력·대시·조각·공격 상태 / 가운데 위 = 헤이즈 게이지와 구간 표시 / 오른쪽 위 = 미니맵.
    가진 업그레이드는 왼쪽 판 바로 아래 줄, 안내 띠·보스 체력은 게이지 아래 가운데.
  * 구역끼리 겹치지 않는다. 반투명 받침을 쓰지 않고 불투명한 테두리 판(hud_kit.panel) 위에 그린다.
  * 글자는 그림자가 있어 밝은 배경에서도 읽힌다. 색만으로 뜻을 전하지 않는다(구간 이름, 방 종류 아이콘, 콤보 마무리 모양).
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
GOLD = (255, 225, 120)

W, H = config.SCREEN_W, config.SCREEN_H
MARGIN = 20
# 왼쪽 위 상태 판
LEFT_X, LEFT_W, LEFT_H = MARGIN, 520, 164
LEFT_Y = H - MARGIN - LEFT_H
# 가운데 위 게이지
BAR_W, BAR_H = 660, 24
BAR_X, BAR_Y = (W - BAR_W) // 2, H - 52
LABEL_Y = BAR_Y - 54                     # 구간 표시 판 (게이지 바로 아래)
NOTICE_Y = LABEL_Y - 70                  # 안내 띠 (구간 표시 판 아래, 화면 가운데)


# ----- 보스 체력 막대 (퀄리티 계획 4-4) -----
BOSS_GHOST_HOLD = 0.35      # 맞은 뒤 이만큼은 깎인 부분이 밝게 남는다(초)
BOSS_GHOST_SPEED = 0.5      # 그다음 초당 이만큼(체력 비율) 따라 준다
BOSS_EPITHET = {'crasher': '용광로의 파수꾼', 'ark': '헤이즈 탑의 총감시관', 'heart': '탑의 진짜 주인'}


PICKUP_TIME = 2.8          # 아이템 띠를 보여 주는 시간(초)
PICKUP_W, PICKUP_H, PICKUP_Y = 760, 96, 120


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


class GameUI:
    def __init__(self, player, stage=None):
        self.player = player
        self.stage = stage
        self.pickup = None          # (이름, 효과 글, 아이콘, 남은 시간): 아이템을 얻었을 때 화면 아래 띠
        self.boss_ref = None
        self.boss_ghost = 1.0
        self.boss_last = 1.0
        self.boss_held = 0.0

    def show_pickup(self, item_id, text):
        import items
        self.pickup = (items.ITEMS[item_id]['name'], text, items.icon_path(item_id), PICKUP_TIME)

    def update(self, dt):
        if self.pickup is not None:
            name, text, icon, left = self.pickup
            self.pickup = (name, text, icon, left - dt) if left - dt > 0 else None
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
        self._draw_status()
        if self.stage is not None:
            self._draw_minimap()
            self._draw_room_notice()
            self._draw_boss_bar()
            self._draw_message()
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
        kit.text(W // 2 + shake, NOTICE_Y - 100, '오버로드!', (255, 235, 120), center=True, big=True)

    # ----- 게이지 (가운데 위) -----
    def _x_of(self, value):
        return BAR_X + BAR_W * min(value, self.player.gauge.cap) / self.player.gauge.cap

    def _draw_gauge(self):
        g = self.player.gauge
        if g.zone in (FADE, CRITICAL):                           # 양끝 위험 구간: 게이지 둘레가 맥박처럼 깜빡인다
            pulse = 0.5 + 0.5 * math.sin(self.player.aura_time * (9 if g.zone == CRITICAL else 6))
            if pulse > 0.5:
                assets.draw_rect_color(BAR_X - 9, BAR_Y - 9, BAR_W + 18, BAR_H + 18, ZONE_COLOR[g.zone])
        kit.panel('frame', BAR_X - 5, BAR_Y - 5, BAR_W + 10, BAR_H + 10)
        bounds = [(0, config.ZONE_FADE_MAX, FADE), (config.ZONE_FADE_MAX, config.ZONE_NORMAL_MAX, NORMAL),
                  (config.ZONE_NORMAL_MAX, g.cap - config.CRITICAL_MARGIN, AWAKE),
                  (g.cap - config.CRITICAL_MARGIN, g.cap, CRITICAL)]
        for lo, hi, zone in bounds:                              # 구간마다 빈 칸 위에 자기 색으로 채운다
            x0, x1 = round(self._x_of(lo)), round(self._x_of(hi))
            kit.fill('empty', x0, BAR_Y, x1 - x0, BAR_H)
            filled = min(g.value, hi) - lo
            if filled > 0:
                kit.fill(ZONE_FILL[zone], x0, BAR_Y, round(self._x_of(lo + filled)) - x0, BAR_H)
        for lo, _hi, _zone in bounds[1:]:                        # 구간 경계 눈금
            x = round(self._x_of(lo))
            assets.draw_rect_color(x - 1, BAR_Y, 2, BAR_H, (11, 16, 32))
        kit.icon('ui_gauge_end_l', BAR_X - 40, BAR_Y - 20)
        kit.icon('ui_gauge_end_r', BAR_X + BAR_W - 4, BAR_Y - 20)
        kit.icon('ui_marker', round(self._x_of(g.value)) - 8, BAR_Y - 8)   # 현재 값 바늘
        # 구간 표시 판: 왼쪽 구간 이름과 %, 가운데 강화 준비, 오른쪽 배율
        kit.panel('plate', BAR_X, LABEL_Y, BAR_W, 40)
        kit.text(BAR_X + 18, LABEL_Y + 20, f'{ZONE_LABEL[g.zone]} {int(g.value)}%', ZONE_COLOR[g.zone])
        mult = g.zone_multipliers()
        kit.text(BAR_X + BAR_W - 18, LABEL_Y + 20, f'공격 x{mult["attack"]:g}  이동 x{mult["speed"]:g}', DIM, small=True,
                 right=True)
        if g.enhanced:                                            # 쌓인 강화 단계 (3단계는 궁극기)
            label = '궁극기 준비!' if g.enhance_level >= config.ENHANCE_MAX_LEVEL else f'강화 {g.enhance_level}단계 준비'
            kit.text(W // 2 + 20, LABEL_Y + 20, label, config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))], small=True,
                     center=True)

    # ----- 왼쪽 위: 무기 칸, 체력, 대시, 조각, 공격 상태 -----
    def _draw_status(self):
        p = self.player
        w, g = p.weapon, p.gauge
        kit.panel('panel', LEFT_X, LEFT_Y, LEFT_W, LEFT_H)
        # 무기 칸 (든 무기 아이콘과 이름, 다른 칸에 무기가 있으면 Q 키)
        sx, sy = LEFT_X + 16, LEFT_Y + 52
        kit.panel('slot_hot' if g.enhanced else 'slot', sx, sy, 96, 96)
        kit.icon(f'icon_w_{w.weapon_id}', sx + 24, sy + 24)
        kit.text(sx + 48, LEFT_Y + 32, w.name, WHITE, small=True, center=True)
        if p.weapons[1 - p.slot] is not None:
            kit.icon('ui_key_q', sx + 70, sy + 70)
        # 체력
        rx = LEFT_X + 132
        hy = LEFT_Y + LEFT_H - 46
        kit.icon('hud_heart', rx, hy - 2)
        hp_w = LEFT_X + LEFT_W - 22 - (rx + 40)
        kit.bar('red', rx + 40, hy - 2, hp_w, 24, p.hp / p.max_hp)
        kit.text(rx + 52, hy + 6, f'{p.hp} / {p.max_hp}', WHITE, small=True)
        # 대시 칸과 조각
        dy = hy - 38
        for i in range(p.dash_max):
            kit.icon('ui_dash_on' if i < p.dash_slots else 'ui_dash_off', rx + 4 + i * 30, dy)
        kit.icon('ui_shard_s', LEFT_X + LEFT_W - 104, dy - 3)
        kit.text(LEFT_X + LEFT_W - 74, dy + 9, f'{p.shards}', TEAL)
        # 공격 상태: 무기 표시 · 다음 공격까지 재충전 · E 강화
        ay = dy - 36
        self._draw_weapon_meter(rx + 4, ay)
        ex = rx + 130
        if g.enhanced:                                           # 쌓인 단계 칸 + 풀리기까지 남은 시간
            self._enhance_key(ex, ay)
            for i in range(config.ENHANCE_MAX_LEVEL):
                on = i < g.enhance_level
                color = config.ENHANCE_LEVEL_COLOR[i + 1] if on else (50, 56, 80)      # 칸마다 단계 색 (보라·금·진홍)
                assets.draw_rect_color(ex + 44 + i * 22, ay + 2, 16, 18, (11, 16, 32))
                assets.draw_rect_color(ex + 46 + i * 22, ay + 4, 12, 14, color)
            kit.bar('violet', ex + 116, ay + 5, 108, 12, g.enhance_timer / config.ENHANCE_TIME)
        elif g.can_enhance():
            self._enhance_key(ex, ay)
            kit.text(ex + 44, ay + 11, f'강화 일격 (-{config.ENHANCE_COST}%)', TEAL, small=True)
        else:
            import keybinds
            kit.text(ex, ay + 11, f'{keybinds.label("enhance", first=True)} 강화: 게이지 {g.enhance_min}%+', (110, 122, 148), small=True)
        ratio = 1.0 if w.ready else 1.0 - w.cooldown / max(w.cooldown_max, 0.01)
        text, color = self._attack_text(w, g)                    # 지금 나가는 공격과 재충전 막대
        if g.enhanced and g.enhance_level >= config.ENHANCE_MAX_LEVEL:      # 다음 공격이 궁극기: 그 이름
            import weapon as weapon_mod
            text, color = '궁극기 ' + weapon_mod.ULT_NAMES[(w.weapon_id, w.ult_kind())], (255, 200, 120)
        elif g.enhanced:
            text, color = f'강화 {g.enhance_level}단계 ' + text.split(':')[0], config.ENHANCE_LEVEL_COLOR[max(1, min(3, g.enhance_level))]
        kit.bar('white' if w.ready else 'yellow', rx + 4, LEFT_Y + 18, 92, 8, ratio)
        kit.text(rx + 112, LEFT_Y + 22, text, color, small=True)
        self._draw_items()
        if p.stunned:                                            # 기절 남은 시간 (화면 가운데)
            bw = 420
            bx, by = (W - bw) // 2, NOTICE_Y - 160
            kit.bar('yellow', bx, by, bw, 12, p.gauge.stun_timer / config.OVERLOAD_STUN)
            kit.text(W // 2, by + 34, f'기절 {p.gauge.stun_timer:.1f}s', (255, 240, 150), small=True, center=True)

    def _enhance_key(self, ex, ay):
        """강화 키 표시: 기본(E)이면 키 그림, 바꿨으면 키 이름 글자 (설정 > 키 바꾸기)."""
        import keybinds
        import sdl2
        key = keybinds.keys('enhance')[0]
        if key == sdl2.SDLK_e:
            kit.icon('ui_key_e', ex, ay - 6)
        else:
            kit.panel('button', ex, ay - 6, 36, 34)
            kit.text(ex + 18, ay + 11, keybinds.key_name(key)[:3], (235, 245, 255), small=True, center=True)

    def _draw_weapon_meter(self, x, y):
        """무기마다 다른 작은 표시: 철파이프 콤보 3칸, 건틀릿 충전, 사슬 끌 마릿수, 식칼 던질 개수."""
        w = self.player.weapon
        if w.weapon_id == 'pipe':
            for i in range(3):
                lit = i < w.combo
                kit.icon(('ui_combo_fin' if i == 2 else 'ui_combo_on') if lit else 'ui_combo_off', x + i * 28, y)
        elif w.weapon_id == 'gauntlet':
            r = w.charge_ratio
            kit.bar('cyan' if r >= 1.0 else 'white', x, y + 5, 100, 12, r)
        else:
            count, _, hot = w.grip() if w.weapon_id == 'chain' else w.volley()
            for i in range(min(count, 4)):
                kit.icon('ui_combo_fin' if hot else 'ui_combo_on', x + i * 26, y)

    def _draw_items(self):
        """왼쪽 판 바로 아래: 가진 업그레이드 아이콘 칸 (같은 것을 여러 번 얻으면 개수)."""
        counts = {}
        for item_id in self.player.items:
            counts[item_id] = counts.get(item_id, 0) + 1
        for i, (item_id, n) in enumerate(counts.items()):
            ix, iy = LEFT_X + i * 62, LEFT_Y - 66
            kit.panel('plate', ix, iy, 58, 58)
            kit.icon(f'icon_{item_id}', ix + 5, iy + 5)
            if n > 1:
                kit.text(ix + 46, iy + 12, f'{n}', WHITE, small=True, center=True)

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

    # ----- 미니맵 (오른쪽 위) -----
    def _draw_minimap(self):
        """방문한 방과 이웃 방. 현재 방은 흰색, 클리어한 방은 청록, 방 종류는 테두리 색과 아이콘."""
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

    # ----- 안내 띠·보스 체력·짧은 메시지 (가운데) -----
    def _banner(self, text, y, color, small=False):
        bw = assets.text_width(text, small) + 110
        kit.panel('banner', (W - bw) // 2, y, bw, 48)
        kit.text(W // 2, y + 24, text, color, small=small, center=True)

    def _draw_room_notice(self):
        import play_mode  # 방 클리어 안내 시간은 play_mode가 갖고 있다
        if play_mode.clear_notice > 0:
            self._banner('방 클리어! 열린 문으로 이동하라', NOTICE_Y, (170, 230, 250))
        elif self.stage.room.locked:
            self._banner(f'적을 모두 처치하라 ({self.stage.enemy_count()})', NOTICE_Y, (245, 150, 160))
        if self.stage.room.is_high_haze:
            kit.text(W // 2, NOTICE_Y - 20, '고농도 방: 헤이즈가 계속 차오른다', TEAL, small=True, center=True)

    def _draw_boss_bar(self):
        boss = self.stage.boss
        if boss is None or not boss.alive:
            return
        bw, bh = 820, 20
        x, y = (W - bw) // 2, NOTICE_Y - 96
        kind = getattr(boss, 'kind', 'crasher')
        kit.panel('panel', x - 26, y - 18, bw + 52, 92)                 # HUD와 같은 판
        kit.text(x, y + 48, getattr(boss, 'title', '보스'), (255, 170, 160))
        kit.text(x + 210, y + 46, BOSS_EPITHET.get(kind, ''), (150, 130, 140), small=True)
        phase = getattr(boss, 'phase', 1)
        if phase > 1:
            kit.text(x + bw, y + 46, f'{phase}페이즈', (255, 120, 110), small=True, right=True)
        ratio = max(0.0, boss.hp) / boss.max_hp
        kit.bar('boss', x, y, bw, bh, ratio)
        ghost = self.boss_ghost if self.boss_ref is boss else ratio
        kit.fill('orange', x + int(bw * ratio), y, int(bw * (ghost - ratio)), bh)  # 방금 깎인 만큼 (따라 줄어든다)
        for m in boss_phase_marks(kind):                                   # 페이즈 경계 눈금
            assets.draw_rect_color(x + int(bw * m) - 1, y - 4, 2, bh + 8, (235, 240, 250))

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

    def _draw_message(self):
        import play_mode
        if play_mode.message_time > 0:
            self._banner(play_mode.message, NOTICE_Y - 230, GOLD)

    def _draw_debug(self):
        p = self.player
        lines = [
            f'상태 {p.state}  점프 {p.jump_count}/{config.MAX_JUMPS}  바닥 {p.on_ground}',
            f'위치 ({p.x:.0f}, {p.y:.0f})  속도 ({p.vx:.0f}, {p.vy:.0f})',
            f'대시 {p.dash_slots}/{p.dash_max}  충전 {p.dash_charge:.2f}s',
            'F1 디버그  F3 게이지+10  F4 게이지-10  F5 방 재시작  H 피격  Esc 일시정지',
        ]
        for i, text in enumerate(lines):
            kit.text(LEFT_X, LEFT_Y - 120 - i * 30, text, (255, 240, 120), small=True)
