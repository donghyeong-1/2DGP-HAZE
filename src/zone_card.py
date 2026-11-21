"""구역 제목 카드 (2026-11-21, Codex T33 그림). 스테이지 1~3에 들어가는 순간 가로 띠 일러스트가 화면 가운데에서
위아래로 열리고, 그 위에 구역 이름이 뜬 뒤 닫힌다.

그림: assets/backgrounds/zone_<테마>.png (1920x400, 가운데가 어둡게 비어 있어 글자를 얹는다).
열림·닫힘은 반투명 없이 띠의 높이(잘라 그리는 줄 수)로 한다 (픽셀 규칙: 정수 좌표, 1배).
UI 레이어 객체다. play_mode가 구역이 바뀌면 stage를 바꿔 넣고, 이름이 바뀐 것을 보고 카드를 띄운다.
보스 등장 카드(Codex T34, assets/backgrounds/boss_card_<보스>.png): 보스방에 들어서면(stage.boss가 새로 생기면)
보스 그림 띠가 열리고 왼쪽에 별칭·이름. 띠가 열려 있는 동안(닫히기 전까지) 게임이 멈춘다(freezing, play_mode가 본다).
"""
import assets
import config
import hud_kit as kit

CARDS = {'stage1': 'cell', 'stage2': 'foundry', 'stage3': 'haze'}    # 구역 -> 카드 그림 테마
NUMBERS = {'stage1': 'STAGE 1', 'stage2': 'STAGE 2', 'stage3': 'FINAL STAGE'}
CARD_H = 400
CENTER_Y = 560            # 띠 가운데의 화면 y
OPEN, HOLD, CLOSE = 0.35, 2.0, 0.35
freezing = False          # 보스 카드가 열려 있어 게임을 멈추는가 (play_mode)
showing = False           # 지금 카드가 떠 있는가 (처음 안내판이 이 동안 기다린다, tutorial)
TEXT_MIN_H = 160          # 띠가 이만큼 열려야 글자를 쓴다 (글자가 띠 밖으로 나오지 않게)


def says_title(stage_name):
    """예전 글자 알림으로 구역 이름을 띄우는가 (카드가 있는 구역은 카드가 대신한다)."""
    return stage_name not in CARDS


class ZoneCard:
    def __init__(self, stage):
        global showing, freezing
        showing = freezing = False                 # 새 판: 지난 판에 떠 있던 카드 표시를 지운다
        self.stage = stage
        self.seen = stage.name
        self.boss_seen = getattr(stage, 'boss', None)
        self.boss = False                          # 지금 띄운 카드가 보스 카드인가
        self.image = ''                            # 띠 그림 경로
        self.t = None
        self.theme = None
        self.title = ''
        self.label = ''

    def update(self, dt):
        global showing, freezing
        self._step(dt)
        showing = self.t is not None
        freezing = self.boss and self.t is not None and self.t < OPEN + HOLD

    def _step(self, dt):
        name = self.stage.name
        if name != self.seen:                      # 새 구역에 들어왔다
            self.seen = name
            self.boss_seen = getattr(self.stage, 'boss', None)
            if name in CARDS:
                self.t, self.theme, self.boss = 0.0, CARDS[name], False
                self.image = f'backgrounds/zone_{self.theme}.png'
                self.title, self.label = getattr(self.stage, 'title', ''), NUMBERS.get(name, '')
            return
        boss = getattr(self.stage, 'boss', None)
        if boss is not None and boss is not self.boss_seen and getattr(boss, 'alive', True):   # 보스방에 들어섰다
            import assets as _assets
            import ui
            self.boss_seen = boss
            kind = getattr(boss, 'kind', 'crasher')
            self.t, self.theme, self.boss = 0.0, f'boss_{kind}', True
            self.image = f'backgrounds/boss_card_{kind}.png'
            self.title, self.label = getattr(boss, 'title', ''), ui.BOSS_EPITHET.get(kind, '')
            _assets.play_sound('ult_cast')         # 모였다가 터지는 큰 소리로 등장
            return
        if self.t is None:
            return
        self.t += dt
        if self.t >= OPEN + HOLD + CLOSE:
            self.t = None

    def visible(self):
        return self.t is not None

    def height(self):
        """지금 열린 띠의 높이(px, 짝수)."""
        if self.t is None:
            return 0
        if self.t < OPEN:
            k = self.t / OPEN
        elif self.t < OPEN + HOLD:
            k = 1.0
        else:
            k = max(0.0, 1.0 - (self.t - OPEN - HOLD) / CLOSE)
        k = 1 - (1 - k) ** 2                        # 빠르게 열리고 끝에서 느려진다
        return int(CARD_H * k) // 2 * 2

    def draw(self):
        h = self.height()
        if h <= 0:
            return
        img = assets.image(self.image)
        top_cut = (CARD_H - h) // 2                 # 그림 가운데 h줄만 잘라 그린다
        bottom = CENTER_Y - h // 2
        assets.draw_rect_color(0, bottom - 4, config.SCREEN_W, h + 8, (6, 9, 18))   # 위아래 검은 테두리 줄
        assets.draw_clip(img, 0, top_cut, config.SCREEN_W, h, 0, bottom)
        if h >= TEXT_MIN_H and self.boss:           # 보스: 왼쪽에 별칭과 이름 (오른쪽은 보스 그림)
            kit.text(170, CENTER_Y + 40, self.label, (130, 235, 225))
            kit.text(170, CENTER_Y - 12, self.title, (240, 244, 252), big=True)
        elif h >= TEXT_MIN_H:
            kit.text(config.SCREEN_W // 2, CENTER_Y + 34, self.label, (130, 235, 225), center=True)
            kit.text(config.SCREEN_W // 2, CENTER_Y - 18, self.title, (240, 244, 252), center=True, big=True)
