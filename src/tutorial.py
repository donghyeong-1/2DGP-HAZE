"""처음 하는 사람 안내 (2026-11-21 퀄리티 계획 2-5). 처음 그 상황이 되면 짧은 안내판을 한 번만 띄운다.

본 안내는 영구 저장(meta.state['hints'])에 남아 다음 판에는 나오지 않는다. 설정의 '처음 안내'로 끌 수 있다.
순서(먼저 걸리는 것부터): 조작(은신처) -> 게이지(첫 전투 구역) -> 페이드·각성·위험(처음 그 구간) -> E 강화 -> 무기 바꾸기.
안내판은 HINT_TIME초 보이고, 여럿이 걸리면 차례로 보인다. 화면 가운데(캐릭터 머리 위)에 HUD 위로 그린다.
"""
import assets
import config
import hud_kit as kit
import meta
import options

# id -> (제목, 줄들). 줄은 짧게 (테스트: 46자 이하, 3줄 이하)
HINTS = {
    'move': ('조작', ['A D 이동 · Space/W 점프 · Shift/우클릭 대시',
                    '마우스로 조준, 좌클릭 공격 · F 말 걸기·줍기']),
    'gauge': ('헤이즈 게이지', ['때리면 차고, 시간이 지나면 줄어든다',
                           '0%가 되면 쓰러지고, 100%가 되면 폭발한다',
                           '그 사이를 지키며 싸워라']),
    'fade': ('페이드 (20% 아래)', ['약해졌다: 공격과 이동이 느려진다', '적을 때려 게이지를 채워라']),
    'awake': ('각성 (50% 이상)', ['강해졌다: 공격 x1.5, 이동 x1.25']),
    'critical': ('위험 (폭발 직전)', ['가장 세지만 100%가 되면 폭발한다', 'E로 게이지를 써서 내려라']),
    'enhance': ('E 강화', ['E: 게이지 25%로 다음 공격을 강화한다', '세 번 쌓으면 궁극기']),
    'weapon': ('무기 두 개', ['Q 또는 1·2로 무기를 바꾼다']),
}


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
        if self.current is None:
            return
        title, lines = HINTS[self.current]
        W = config.SCREEN_W
        w = max(assets.text_width(line, False) for line in lines + [title]) + 90
        h = 62 + 34 * len(lines)
        x, y = (W - w) // 2, 540                       # 캐릭터 머리 위, 알림 띠(NOTICE_Y - 230)보다 아래
        k = min(1.0, (config.HINT_TIME - self.left) / 0.2, self.left / 0.3)   # 짧게 나타나고 사라진다
        if k <= 0:
            return
        kit.panel('panel', x, y, w, h)
        kit.text(W // 2, y + h - 30, title, (130, 235, 225), center=True)
        for i, line in enumerate(lines):
            kit.text(W // 2, y + h - 66 - 34 * i, line, (225, 232, 245), center=True)
