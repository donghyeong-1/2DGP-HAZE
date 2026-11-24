"""보스 등장씬과 보스 대사 (v8 6일 차, docs/plan_v8.md 6절). 규칙은 pico2d 없이 돌아가고 그리기만 화면을 쓴다.

보스방에 들어서면(stage.boss가 새로 생기면):
  wait(위아래 검은 띠가 들어온다) -> pan(카메라가 보스 쪽으로) -> lines(대사 2~3줄, 글자가 차례로 찍힌다)
  -> card(이름 띠: zone_card.open_boss, 그동안 카메라가 플레이어에게 돌아온다) -> out(띠가 빠지고 싸움 시작).
- card가 끝날 때까지 게임이 멈춘다(freezing, play_mode가 본다): world를 갱신하지 않으므로 보스도 플레이어도 움직이지
  않고 피해도 없다. 누르고 있던 키는 시작할 때 떼고(release_inputs) 끝날 때 실제로 눌린 키만 다시 누른다(sync_inputs).
- Enter·Space로 넘긴다(filter_event): 카메라 이동 중이면 바로 대사, 글자가 찍히는 중이면 그 줄을 다 보여 주고,
  다 보였으면 다음 줄, 이름 띠면 바로 닫는다. 다른 누름(이동·공격·클릭)은 먹고, 뗀 신호·Esc(일시정지)는 그대로 보낸다.
- 같은 보스를 두 번째 만나면(게임을 켠 뒤, 판이 바뀌어도 기억한다: seen) 짧게: 다시 만난 대사 한 줄, 이동·이름 띠도 짧게.
- 헤이즈 심장은 다 내려온 뒤(intro_left <= 0) 시작한다. 그림이 없는 보스 카드는 건너뛰고 카메라만 돌아온다.
- config.BOSS_INTRO가 False면 아무것도 하지 않는다(zone_card가 예전처럼 이름 띠를 바로 띄운다).

한 줄 대사(bark): 페이즈가 바뀔 때·쓰러질 때 보스가(boss.py·ark.py·heart.py가 bark를 부른다), 플레이어가 쓰러지면
살아 있는 보스가 한 줄 말한다. 게임은 멈추지 않고 화면 아래에 자막으로 잠깐 뜬다.
대사는 캐릭터의 말이라 화면 설명 문장의 '~합니다' 규칙 밖이다(추천안으로 정함). 용어는 docs/기획서.md 용어 정리.
"""
import camera
import config

# ----- 대사 -----
# speaker: 자막 위에 뜨는 이름, color: 이름 색. intro 2~3줄 / again 다시 만났을 때 / phase2·phase3 페이즈 전환 /
# death 쓰러질 때 / win 플레이어가 쓰러졌을 때
LINES = {
    'gatekeeper': {
        'speaker': '관문 간수장 문지기', 'color': (232, 200, 120),
        'intro': ['제9구역 관문이다. 여기부터는 간수의 땅.',
                  '쥐새끼 하나 지나간 적 없다. 돌아가라, N-09.',
                  '돌아가지 않겠다면 방패로 짓이겨 주지.'],
        'again': ['또 슬럼 냄새로군. 이번에도 문은 닫혀 있다.'],
        'phase2': '비상! 전원 관문으로 집결하라!',
        'death': '관문이... 열린다... 공장이 널 기다린다.',
        'win': '관문 이상 없음. 순찰을 계속한다.',
    },
    'crasher': {
        'speaker': '제4구역장 크래셔', 'color': (255, 150, 110),
        'intro': ['슬럼 쥐새끼가 공장까지 기어 올라왔군.',
                  '4구역 용광로는 아무도 못 지나간다.',
                  '녹여서 철골에 박아 주마, N-09.'],
        'again': ['또 너냐. 이번엔 뼈까지 녹여 주지.'],
        'phase2': '뜨겁나? 용광로는 이제 막 달아올랐다!',
        'death': '용광로가... 식는다...',
        'win': '다음 놈. 용광로에 넣어라.',
    },
    'ark': {
        'speaker': '총감시관 아크', 'color': (150, 240, 230),
        'intro': ['실험체 N-09. 탈출 시도, 처음이 아니지.',
                  '헤이즈는 내가 정한 만큼만 흐른다.',
                  '기록을 끝내자. 이 탑이 네 마지막 감방이다.'],
        'again': ['또 탑을 올랐나. 기록이 하나 늘겠군.'],
        'phase2': '농도 조정. 네 게이지는 내 손에 있다.',
        'phase3': '제어 해제. 탑의 헤이즈를 전부 연다.',
        'death': '이 껍데기로는... 부족하군.',
        'win': '기록. 실험체 N-09, 탈출 실패.',
    },
    'heart': {
        'speaker': '헤이즈 심장', 'color': (120, 235, 225),
        'intro': ['이것이 진짜 모습이다. 탑의 심장, 헤이즈의 근원.',
                  '네가 들이마신 헤이즈는 전부 내 숨이었다.',
                  '돌아와라, N-09. 너도 처음부터 나의 일부였다.'],
        'again': ['다시 왔구나. 네 안의 헤이즈가 나를 부른다.'],
        'phase2': '맥동이 빨라진다... 느껴지느냐.',
        'phase3': '탑이 잠긴다. 모든 헤이즈는 나에게 돌아온다.',
        'death': '숨이... 멎는다... 안개가... 걷힌다...',
        'win': '돌아왔구나. 이제 영원히.',
    },
}
MAX_CHARS = 30          # 한 줄 글자 수 한계 (자막이 화면 가운데 한 줄에 들어간다)

# ----- 시간 -----
FULL = dict(wait=0.35, pan=0.9, hold=1.5, card=2.0, back=0.5, out=0.3)       # 처음 만났을 때
SHORT = dict(wait=0.12, pan=0.45, hold=0.9, card=1.0, back=0.4, out=0.25)    # 다시 만났을 때
TYPE_CPS = 30.0         # 대사 글자가 찍히는 빠르기(초당 글자)
ADVANCE_GUARD = 0.3     # 등장씬이 시작되고 이 시간 안의 누름은 무시한다 (들어오며 누르던 점프로 넘어가지 않게)
FROZEN = ('wait', 'pan', 'lines', 'card', 'back')
BAR_H = 112             # 위아래 검은 띠 높이(px, 짝수). 보스방 바닥(2칸 = 128px)과 보스 발이 가려지지 않게
BAR_COLOR = (3, 5, 10)

freezing = False        # 등장씬이 게임을 멈추고 있는가 (play_mode, gamepad)
seen = set()            # 등장씬을 본 보스 종류 (게임을 켜 있는 동안)
_hud_hidden = [False]
_bark = [None]          # [speaker, text, color, 남은 시간]


def reset_all():
    """테스트용: 본 보스·한 줄 대사·멈춤을 모두 지운다."""
    global freezing
    seen.clear()
    _bark[0] = None
    freezing = False
    _hud_hidden[0] = False


def hud_hidden():
    """등장씬 중에는 HUD를 그리지 않는다 (ui.GameUI)."""
    return _hud_hidden[0]


# ----- 한 줄 대사 -----
def bark_time(text):
    return max(2.2, 0.6 + 0.09 * len(text))


def bark(boss, key):
    """보스가 한 줄 말한다(페이즈 전환·처치·플레이어 쓰러짐). 대사가 없으면 False."""
    lines = LINES.get(getattr(boss, 'kind', boss))
    text = lines.get(key) if lines else None
    if not text:
        return False
    _bark[0] = [lines['speaker'], text, lines['color'], bark_time(text)]
    return True


def current_bark():
    """(speaker, text, color) 또는 None."""
    b = _bark[0]
    return None if b is None else (b[0], b[1], b[2])


def tick_bark(dt):
    b = _bark[0]
    if b is not None:
        b[3] -= dt
        if b[3] <= 0:
            _bark[0] = None


# ----- 입력 -----
def filter_event(event):
    """등장씬 중 이벤트 처리: 'advance'(넘기기), 'block'(먹는다), 'pass'(그대로 플레이어·일시정지로)."""
    from pico2d import SDL_KEYDOWN, SDL_MOUSEBUTTONDOWN, SDLK_ESCAPE, SDLK_KP_ENTER, SDLK_RETURN, SDLK_SPACE
    if event.type == SDL_KEYDOWN:
        if event.key in (SDLK_RETURN, SDLK_KP_ENTER, SDLK_SPACE):
            return 'advance'
        return 'pass' if event.key == SDLK_ESCAPE else 'block'
    if event.type == SDL_MOUSEBUTTONDOWN:
        return 'block'          # 공격하며 들어오던 클릭으로 대사를 건너뛰지 않게
    return 'pass'


def _ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


class BossIntro:
    """UI 레이어 객체. play_mode가 ZoneCard 다음에 넣고, 구역이 바뀌면 stage를 바꿔 넣는다."""

    def __init__(self, stage, player=None, card=None):
        global freezing
        freezing = False
        _hud_hidden[0] = False
        self.stage, self.player, self.card = stage, player, card
        self.boss_seen = getattr(stage, 'boss', None)
        self.boss = None
        self.step = None
        self.t = 0.0                 # 지금 단계에서 지난 시간
        self.age = 0.0               # 등장씬이 시작되고 지난 시간
        self.short = False
        self.times = FULL
        self.lines = []
        self.line_index = 0
        self.line_t = 0.0
        self.cam_from = self.cam_boss = (0.0, 0.0)
        self.taunted = None          # 플레이어가 쓰러졌을 때 한 줄을 말한 보스

    # ----- 조회 -----
    def line(self):
        return self.lines[self.line_index] if self.step == 'lines' and self.line_index < len(self.lines) else ''

    def typed(self):
        return min(len(self.line()), int(self.line_t * TYPE_CPS))

    def bars(self):
        """위아래 검은 띠의 지금 높이(px, 짝수)."""
        if self.step is None:
            return 0
        if self.step == 'wait':
            k = self.t / max(self.times['wait'], 1e-6)
        elif self.step == 'out':
            k = 1.0 - self.t / max(self.times['out'], 1e-6)
        else:
            k = 1.0
        return int(BAR_H * max(0.0, min(1.0, k))) // 2 * 2

    # ----- 갱신 -----
    def update(self, dt):
        tick_bark(dt)
        if self.step is None:
            self._watch()
        else:
            self._run(dt)
        self._sync()

    def _sync(self):
        global freezing
        freezing = self.step in FROZEN
        _hud_hidden[0] = self.step in FROZEN

    def _watch(self):
        st = self.stage
        boss = getattr(st, 'boss', None)
        p = self.player
        if boss is not None and getattr(boss, 'alive', True) and p is not None and p.state == 'DEAD' \
                and self.taunted is not boss:
            self.taunted = boss                          # 쓰러진 플레이어에게 한 줄
            bark(boss, 'win')
            return
        if not getattr(config, 'BOSS_INTRO', False):
            self.boss_seen = boss
            return
        if boss is None or boss is self.boss_seen or not getattr(boss, 'alive', True):
            return
        if getattr(boss, 'intro_left', 0) > 0:          # 헤이즈 심장: 다 내려온 뒤에
            return
        if getattr(boss, 'kind', None) not in LINES or (p is not None and p.state == 'DEAD'):
            self.boss_seen = boss
            return
        self._start(boss)

    def _start(self, boss):
        kind = boss.kind
        self.boss_seen = self.boss = boss
        self.short = kind in seen
        seen.add(kind)
        self.times = SHORT if self.short else FULL
        self.lines = list(LINES[kind]['again' if self.short else 'intro'])
        self.line_index, self.line_t = 0, 0.0
        self.step, self.t, self.age = 'wait', 0.0, 0.0
        self.cam_from = (camera.x, camera.y)
        room = self.stage.room
        self.cam_boss = camera.look_at(room, boss.x, boss.y + getattr(boss, 'hb_h', 100) / 2)
        if self.player is not None and hasattr(self.player, 'release_inputs'):
            self.player.release_inputs()                 # 누르고 있던 이동이 멈춘 동안 남지 않게

    def _set_camera(self, pos):
        camera.x, camera.y = float(pos[0]), float(pos[1])

    def _player_camera(self):
        if self.player is None:
            return self.cam_from
        return camera.target_for(self.player, self.stage.room)

    def _run(self, dt):
        boss = self.boss
        if self.step in FROZEN and (boss is not getattr(self.stage, 'boss', None)):
            self._finish()                               # 구역이 바뀌었거나 보스가 사라졌다
            return
        self.t += dt
        self.age += dt
        if boss is not None and self.step in FROZEN and hasattr(boss, 'anim_time'):
            boss.anim_time += dt                         # 멈춘 동안에도 보스는 숨 쉰다 (대기 그림이 번갈아)
        tm = self.times
        if self.step == 'wait':
            if self.t >= tm['wait']:
                self._go('pan')
        elif self.step == 'pan':
            k = _ease(self.t / tm['pan'])
            self._set_camera([a + (b - a) * k for a, b in zip(self.cam_from, self.cam_boss)])
            if self.t >= tm['pan']:
                self._go('lines')
        elif self.step == 'lines':
            self._set_camera(self.cam_boss)
            self.line_t += dt
            if self.typed() >= len(self.line()) and self.line_t >= len(self.line()) / TYPE_CPS + tm['hold']:
                self._next_line()
        elif self.step == 'card':
            import zone_card
            span = zone_card.OPEN + self.card.hold
            k = _ease(self.t / span)
            target = self._player_camera()
            self._set_camera([a + (b - a) * k for a, b in zip(self.cam_boss, target)])
            if not self.card.holding():
                self._finish()
        elif self.step == 'back':
            k = _ease(self.t / tm['back'])
            target = self._player_camera()
            self._set_camera([a + (b - a) * k for a, b in zip(self.cam_boss, target)])
            if self.t >= tm['back']:
                self._finish()
        elif self.step == 'out':
            if self.t >= tm['out']:
                self.step = None

    def _go(self, step):
        self.step, self.t = step, 0.0
        if step == 'lines':
            self.line_index, self.line_t = 0, 0.0
            self._set_camera(self.cam_boss)

    def _next_line(self):
        self.line_index += 1
        self.line_t = 0.0
        if self.line_index < len(self.lines):
            return
        if self.card is not None and self.card.open_boss(self.boss, self.times['card']):
            self._go('card')
        else:
            self._go('back')

    def _finish(self):
        """멈춤을 풀고 띠를 뺀다."""
        if self.step in FROZEN and self.player is not None and hasattr(self.player, 'sync_inputs'):
            try:
                self.player.sync_inputs()                # 지금 실제로 눌린 키만 다시 누른 것으로
            except Exception:                            # noqa: BLE001 (창 없는 실행: 모두 뗀 것으로 둔다)
                pass
        self.step, self.t = 'out', 0.0
        self._sync()

    def advance(self):
        """Enter·Space: 한 단계 넘긴다."""
        if self.step not in FROZEN or self.age < ADVANCE_GUARD:
            return
        if self.step in ('wait', 'pan'):
            self._go('lines')
        elif self.step == 'lines':
            if self.typed() < len(self.line()):
                self.line_t = len(self.line()) / TYPE_CPS     # 이 줄을 다 보여 준다
            else:
                self._next_line()
        elif self.step == 'card':
            self.card.close_now()
            self._finish()
        elif self.step == 'back':
            self._finish()
        self._sync()

    # ----- 그리기 -----
    def draw(self):
        import assets
        import hud_kit as kit
        w, h = config.SCREEN_W, config.SCREEN_H
        bar = self.bars()
        if bar > 0:
            assets.draw_rect_color(0, 0, w, bar, BAR_COLOR)
            assets.draw_rect_color(0, h - bar, w, bar, BAR_COLOR)
        if self.step == 'lines' and bar >= BAR_H:
            info = LINES[self.boss.kind]
            kit.text(w // 2, BAR_H - 26, info['speaker'], info['color'], small=True, center=True)
            kit.text(w // 2, 44, self.line()[:self.typed()], (236, 240, 248), center=True)
            done = self.typed() >= len(self.line())
            kw = kit.keycap(w - 300, 30, 'Enter', hot=done)
            kit.text(w - 300 + kw + 10, 45, '넘기기', kit.FAINT, small=True)
        elif self.step is None:
            self._draw_bark()

    def _draw_bark(self):
        b = current_bark()
        if b is None:
            return
        import assets
        import hud_kit as kit
        speaker, text, color = b
        w = config.SCREEN_W
        box_w = max(assets.text_width(text), assets.text_width(speaker, True)) + 96
        box_w = box_w // 2 * 2
        x, y = (w - box_w) // 2, 206
        assets.draw_rect_color(x, y, box_w, 88, BAR_COLOR, 0.72)
        assets.draw_rect_color(x, y, box_w, 2, color)
        kit.text(w // 2, y + 64, speaker, color, small=True, center=True)
        kit.text(w // 2, y + 30, text, (236, 240, 248), center=True)
