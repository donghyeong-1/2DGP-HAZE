"""처음 하는 사람 안내 (2026-11-21 퀄리티 계획 2-5). 처음 그 상황이 되면 짧은 안내판을 한 번만 띄운다.

본 안내는 영구 저장(meta.state['hints'])에 남아 다음 판에는 나오지 않는다. 설정의 '처음 안내'로 끌 수 있다.
순서(먼저 걸리는 것부터): 조작(은신처) -> 게이지(첫 전투 구역) -> 페이드·각성·위험(처음 그 구간) -> E 강화 -> 무기 바꾸기.
안내판은 HINT_TIME초 보이고, 여럿이 걸리면 차례로 보인다. 왼쪽 위 체력 아래에 카드로 그린다(11/22 UI v4).
"""
import assets
import config
import hud_kit as kit
import keybinds
import meta
import options

# id -> (제목, 줄들). 줄은 짧게 (테스트: 46자 이하, 3줄 이하). {동작}은 키 설정의 키 이름으로 바뀐다 (hint_text)
HINTS = {
    'move': ('조작', ['{left} {right} 이동 · {jump} 점프 · {dash}/우클릭 대시',
                    '마우스로 조준, 좌클릭 공격 · {interact} 말 걸기·줍기']),
    'gauge': ('헤이즈 게이지', ['적을 때리면 차오르고, 시간이 지나면 줄어듭니다',
                           '0%가 되면 쓰러지고, 100%가 되면 폭발합니다',
                           '그 사이를 유지하며 싸우세요']),
    'fade': ('페이드 (20% 아래)', ['공격이 약해지고 이동이 느려집니다', '적을 때려 게이지를 채우세요']),
    'awake': ('각성 (50% 이상)', ['공격 x1.5, 이동 x1.25로 강해집니다']),
    'critical': ('위험 (폭발 직전)', ['가장 강하지만 게이지 한계에 닿으면 폭발합니다', '{enhance} 강화로 게이지를 써서 낮추세요']),
    'enhance': ('{enhance} 강화', ['게이지 25%를 써서 다음 공격을 강화합니다', '세 번 쌓으면 궁극기가 나갑니다']),
    'weapon': ('무기 두 개', ['{swap} · {weapon1} · {weapon2} 키로 무기를 교체합니다', '교체하는 순간 교체기가 나갑니다']),
}


# 게임패드로 할 때 줄이 달라지는 안내 (N1-3: 마우스·숫자 키가 없다). 나머지는 {동작}이 패드 버튼 이름으로 바뀐다
PAD_HINTS = {
    'move': ('조작', ['L스틱 이동 · A 점프 · B 대시', 'R스틱 조준 · X 공격 · Y 말 걸기·줍기']),
    'weapon': ('무기 두 개', ['LB 버튼으로 무기를 교체합니다', '교체하는 순간 교체기가 나갑니다']),
}


def hint_text(hid):
    """(제목, 줄들)에 지금 키 설정의 키 이름을 넣는다. 마지막 장치가 패드면 패드 버튼 이름 (N1-3)."""
    import input_device
    names = {a: keybinds.label(a, first=a not in ('jump',)) for a in keybinds.IDS}
    title, lines = PAD_HINTS[hid] if input_device.is_pad() and hid in PAD_HINTS else HINTS[hid]
    return title.format(**names), [line.format(**names) for line in lines]


def _seen(hid):
    meta.ensure_loaded()
    return hid in meta.state.setdefault('hints', [])


def _mark(hid):
    meta.ensure_loaded()
    hints = meta.state.setdefault('hints', [])
    if hid not in hints:
        hints.append(hid)
        meta.save()


def wanted(player, stage):
    """지금 상황에서 아직 안 본 안내 id들 (보여 줄 순서)."""
    name = getattr(stage, 'name', '')
    g = player.gauge
    out = []
    if name == 'hideout':
        out.append('move')
    else:
        out.append('gauge')
        zone_hint = {'FADE': 'fade', 'AWAKE': 'awake', 'CRITICAL': 'critical'}.get(g.zone)
        if zone_hint:
            out.append(zone_hint)
        if g.can_enhance():
            out.append('enhance')
        if player.weapons[1] is not None:
            out.append('weapon')
    return [h for h in out if not _seen(h)]


class Tutorial:
    def __init__(self, player=None, stage=None):
        self.player, self.stage = player, stage
        self.current = None          # 지금 보여 주는 안내 id
        self.left = 0.0

    def current_id(self):
        return self.current

    def update_with(self, player, stage, dt):
        import zone_card
        if zone_card.showing:                      # 구역 제목 카드가 가운데를 덮는 동안은 기다린다
            return
        if self.current is not None:
            self.left -= dt
            if self.left > 0:
                return
            self.current = None
        if not options.show_hints:
            return
        todo = wanted(player, stage)
        if todo:
            self.current, self.left = todo[0], config.HINT_TIME
            _mark(todo[0])

    def update(self, dt):
        self.update_with(self.player, self.stage, dt)

    def draw(self):
        """왼쪽 위 체력 아래의 안내 카드 (화면 가운데·캐릭터를 가리지 않게, 11/22 UI v4).
        왼쪽에 청록 띠, 제목, 왼쪽 정렬 줄, 아래에 남은 시간 막대. 옆에서 미끄러져 들어왔다 나간다."""
        if self.current is None:
            return
        import game_world
        if game_world.quiet:                       # R1: mist 메뉴 창 뒤에 깔린 멈춘 게임에서는 안내 카드를 빼고
            return
        import boss_intro
        if boss_intro.hud_hidden():                # v8 보스 등장씬 동안은 숨긴다 (HUD와 같이)
            return
        import ui
        title, lines = hint_text(self.current)
        k = min(1.0, (config.HINT_TIME - self.left) / 0.2, self.left / 0.3)   # 짧게 나타나고 사라진다
        if k <= 0:
            return
        w = max([assets.text_width(line, True) for line in lines] + [assets.text_width(title, False)]) + 64
        h = 58 + 32 * len(lines) + 14
        x = ui.MARGIN - int((1 - k) * (w + ui.MARGIN))
        y = ui.HINT_TOP - h
        left = max(0.0, self.left / config.HINT_TIME)
        if kit.is_mist():                          # H1 mist: HUD와 같은 가는 테두리 판. 청록 띠 없이(청록은 헤이즈에만), 제목은 밝은 회백
            kit.hud_panel('panel', x // 2 * 2, y // 2 * 2, w // 2 * 2, h // 2 * 2)
            kit.text(x + 30, y + h - 30, title, (236, 240, 246))
            for i, line in enumerate(lines):
                kit.text(x + 30, y + h - 68 - 32 * i, line, (205, 213, 228), small=True)
            assets.draw_rect_color(x // 2 * 2 + 4, y // 2 * 2 + 4, int((w - 8) * left) // 2 * 2, 2, (128, 137, 152))   # 남은 시간
            return
        assets.draw_rect_color(x, y, w, h, (46, 56, 82))
        assets.draw_rect_color(x + 2, y + 2, w - 4, h - 4, (12, 17, 30))
        assets.draw_rect_color(x + 2, y + 2, 8, h - 4, (130, 235, 225))           # 왼쪽 띠
        kit.text(x + 30, y + h - 30, title, (130, 235, 225))
        for i, line in enumerate(lines):
            kit.text(x + 30, y + h - 68 - 32 * i, line, (225, 232, 245), small=True)
        assets.draw_rect_color(x + 10, y + 2, int((w - 12) * left), 4, (90, 150, 170))   # 남은 시간
