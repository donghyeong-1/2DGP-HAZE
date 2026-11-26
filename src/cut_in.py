"""실루엣 컷인 (O1, 2026-11-26, docs/opus/TASKS.md). 규칙은 pico2d 없이 돌아가고 그리기만 화면을 쓴다.

화면을 한 가지 색으로 덮고 그 위에 검은 실루엣만 움직이는 0.7초 연출. 새 그림 없이 지금 있는 자세 그림의 실루엣과
구운 원반 한 장(assets/effects/cutin-disc, tools/make_fx2.py, 색은 게임이 입힌다)으로 만든다.
- play(color, actors, word): actors = [(그림 세트, 번호, 보는 쪽, (화면 x, 화면 y = 발), 정수 배율 또는 None)].
  None이면 그림 높이에 맞춰 1~3배를 고른다(보통 3배, 헤이즈 심장처럼 큰 것은 1배). 한 번에 하나만(도는 중이면 무시).
- 시간표: 0~0.08 들어옴(첫 프레임 흰 섬광, 번쩍임 줄이기면 없이) / 0.08~0.5 단색 바탕 + 원반 + 실루엣이 SLIDE만큼
  미끄러짐(빠르게 시작해 느려진다) + 화면을 가로지르는 가는 선 셋 / 0.5~0.7 위아래에서 닫히며 빠진다.
- 도는 동안 게임이 멈춘다: play_mode.update가 cut_in.update(실제 시간)만 하고 돌아간다(세계·적·피해 모두 멈춤).
  끝나면 on_end를 부르고 그대로 이어진다(포효·흔들림·대사 한 줄은 멈춰 있다가 그 뒤에 나온다).
- 쓰는 곳: 보스 페이즈 전환(boss_phase: 같은 싸움에서 같은 페이즈는 한 번), 증강 '궁극기 각성'의 궁극기 시전(weapon).
- config.CUT_IN이 False면 아무것도 하지 않는다(play가 False: 부르는 쪽이 바로 이어서 한다).
"""
import config
import game_world

DURATION = 0.7
T_IN = 0.08              # 들어옴 (흰 섬광 한 프레임 뒤 단색)
T_HOLD = 0.5             # 여기까지 실루엣이 미끄러지고, 그 뒤 닫힌다
SLIDE = 40               # 실루엣이 미끄러지는 거리(px)
MAX_ACTOR_H = 600        # 배율을 주지 않은 실루엣을 키울 때 몸(빈 곳을 뺀 높이)이 화면에서 넘지 않는 높이(px)
BOSS_FILL = (0.45, 0.60) # 보스 실루엣의 몸이 화면 높이에서 차지하는 비율 (그 안의 정수 배율, 없으면 가장 가까운 정수 배)
BOSS_FOOT_Y = 200        # 보스 실루엣의 발 높이(px): 몸이 원반 가운데에 걸치게
WORD_FONT = ('Galmuri14.ttf', 14 * 8)   # 큰 글자: 도트 글꼴을 원래 크기의 정수 배로 (흐려지지 않게)
BAR = (3, 5, 10)         # 닫히는 띠 색 (보스 등장씬의 검은 띠와 같다)
INK = (6, 8, 14)         # 실루엣 색 (캐릭터 테두리 색과 같은 푸른 검정)
BOSS_COLORS = {          # 보스마다 컷인 색
    'crasher': (226, 92, 44),      # 주홍
    'gatekeeper': (92, 116, 140),  # 청회색
    'ark': (34, 176, 168),         # 청록
    'heart': (34, 176, 168),
    'heart3': (190, 28, 58),       # 심장 3페이즈는 진홍
}

_cur = [None]
_body_h = {}             # 그림 경로 -> 몸 높이(알파가 있는 줄 수)
_word_font = [None]
history = []             # 요청이 받아들여진 컷인의 글자 (테스트·확인용)
colors = []


def reset():
    """새 판·테스트: 도는 컷인과 기록을 지운다."""
    c = _cur[0]
    _cur[0] = None
    if c is not None:
        game_world.remove_object(c)
    history.clear()
    colors.clear()


def running():
    return _cur[0] is not None


def current():
    return _cur[0]


def slide(t):
    """실루엣이 미끄러진 정도 0~1 (빠르게 시작해 느려진다)."""
    k = max(0.0, min(1.0, t / T_HOLD))
    return 1.0 - (1.0 - k) ** 3


def play(color, actors, word=None, duration=DURATION, on_end=None):
    """컷인을 시작한다. 시작했으면 True (꺼져 있거나 이미 돌고 있으면 False: 부르는 쪽이 바로 이어서 한다)."""
    if not getattr(config, 'CUT_IN', False) or running():
        return False
    c = CutIn(color, list(actors), word, min(float(duration), 0.8), on_end)
    _cur[0] = c
    history.append(word)
    colors.append(tuple(color))
    game_world.add_object(c, game_world.LAYER_UI)          # UI 층 맨 위 (HUD까지 덮는다)
    return True


def update(dt):
    """play_mode가 컷인이 도는 동안 세계 대신 부른다 (실제 시간)."""
    c = _cur[0]
    if c is not None:
        c.update(dt)


def boss_scale(body_h, screen_h=None):
    """보스 실루엣 배율: 몸 높이 x 배율이 화면 높이의 BOSS_FILL 안에 드는 정수 (여럿이면 0.52에 가까운 것,
    없으면 범위에 가장 가까운 것). 크래셔·문지기 2배, 아크 3배, 헤이즈 심장 1배(44%, 2배면 88%)."""
    screen_h = screen_h or config.SCREEN_H
    lo, hi = BOSS_FILL
    mid = (lo + hi) / 2

    def key(s):
        r = body_h * s / screen_h
        return (max(lo - r, r - hi, 0.0), abs(r - mid))
    return min(range(1, 7), key=key)


def boss_phase(boss, phase, word, color_key=None):
    """보스 페이즈 전환 컷인: 그 보스의 지금 자세(포효·페이즈 자세)를 실루엣으로. 같은 보스·같은 페이즈는 한 번만."""
    done = boss.__dict__.setdefault('_cut_phases', set())
    if phase in done:
        return False
    done.add(phase)
    if hasattr(boss, '_core_frame'):                       # 헤이즈 심장: 본체 그림
        name, n = boss._core_frame()
    else:
        import weapon
        frame = weapon.enemy_frame(boss)
        if frame is None:
            return False
        name, n = frame
    color = BOSS_COLORS.get(color_key or boss.kind, BOSS_COLORS['crasher'])
    import sprites
    rn, rk = sprites.resolve(name, n)
    try:
        scale = boss_scale(body_height(sprites.path(rn, rk)))
    except OSError:                                       # 그림 파일이 없는 테스트용 보스
        scale = None
    return play(color, [(name, n, -1, (config.SCREEN_W * 62 // 100, BOSS_FOOT_Y), scale)], word)


class CutIn:
    def __init__(self, color, actors, word, duration, on_end):
        self.color = tuple(int(c) for c in color)
        self.actors = actors
        self.word = word
        self.duration = duration
        self.on_end = on_end
        self.t = 0.0
        self.drawn = 0

    def phase(self):
        if self.t < T_IN:
            return 'in'
        return 'hold' if self.t < T_HOLD else 'close'

    def update(self, dt):
        self.t += dt
        if self.t >= self.duration and _cur[0] is self:
            _cur[0] = None
            game_world.remove_object(self)
            if self.on_end is not None:
                self.on_end()

    # ----- 그리기 -----
    def draw(self):
        import assets
        import options
        offset = assets.draw_offset
        assets.draw_offset = (0, 0)
        try:
            self._draw(assets, options.reduce_flash)
        finally:
            assets.draw_offset = offset
        self.drawn += 1

    def _draw(self, assets, calm):
        w, h = config.SCREEN_W, config.SCREEN_H
        if self.drawn == 0 and not calm:                   # 들어오는 첫 프레임: 흰 섬광
            assets.draw_rect_color(-16, -16, w + 32, h + 32, (255, 255, 255))
            return
        r, g, b = self.color
        deep = (r * 32 // 100, g * 32 // 100, b * 32 // 100)          # 바탕은 어둡게, 원반이 그 색 그대로
        assets.draw_rect_color(-16, -16, w + 32, h + 32, deep)
        s = slide(self.t)
        self._disc(assets, w * 58 // 100, h // 2)
        self._lines(assets, w, h, s)
        for name, n, face, (sx, sy), scale in self.actors:
            self._actor(assets, name, n, face, int(sx - face * SLIDE * (1.0 - s)), int(sy), scale)
        if self.word:
            self._word(assets, w, h, s)
        if self.t >= T_HOLD:                                # 위아래에서 닫히며 빠진다
            k = min(1.0, (self.t - T_HOLD) / max(self.duration - T_HOLD, 1e-6))
            k = k * k * (3 - 2 * k)
            bar = int(h / 2 * k) // 2 * 2 + 2
            assets.draw_rect_color(-16, -16, w + 32, bar + 16, BAR)
            assets.draw_rect_color(-16, h - bar, w + 32, bar + 16, BAR)

    def _disc(self, assets, cx, cy):
        """구운 원반 (회색조 시트에 색을 곱한다). 처음 몇 장은 커지고 마지막 장에 머문다."""
        import effects
        try:
            info = effects.sheet_info('cutin-disc')
        except OSError:
            return
        fw, fh = info['frameSize']
        sc = info.get('scale', 2)
        n = info['columns']
        i = min(n - 1, int(self.t * info.get('fps', 30)))
        img = assets.image('effects/cutin-disc.png')
        x, y = cx - fw * sc // 2 // 2 * 2, cy - fh * sc // 2 // 2 * 2
        assets.draw_clip_tinted(img, i * fw, fh, fw, fh, x, y, self.color, sc)    # 윗줄 = 색 층
        assets.draw_clip(img, i * fw, 0, fw, fh, x, y, '', sc)                   # 아랫줄 = 흰 심

    def _lines(self, assets, w, h, s):
        """화면을 가로지르는 가는 선 셋: 왼쪽에서 빠르게 뻗는다 (밝은 색 둘, 검정 하나)."""
        r, g, b = self.color
        light = ((r + 255 * 2) // 3, (g + 255 * 2) // 3, (b + 255 * 2) // 3)
        for y, thick, color, delay in ((h * 30 // 100, 4, light, 0.0), (h * 70 // 100, 2, light, 0.06), (h * 22 // 100, 2, INK, 0.1)):
            k = slide(max(0.0, self.t - delay) * 1.6)
            length = int(w * k) // 2 * 2
            if length > 0:
                assets.draw_rect_color(0, y // 2 * 2, length, thick, color)

    def _actor(self, assets, name, n, face, x, y, scale):
        """검은 실루엣을 정수 배로 (발이 (x, y))."""
        import sprites
        from sdl2 import SDL_SetTextureColorMod
        name, n = sprites.resolve(name, n)
        img = assets.silhouette(sprites.path(name, n))
        if scale is None:
            scale = max(1, min(3, MAX_ACTOR_H // max(1, body_height(sprites.path(name, n)))))
        dx, foot = sprites.place(name, n, img.w, img.h, face)
        left = (x + dx * scale - img.w * scale // 2) // 2 * 2
        bottom = (y - foot * scale) // 2 * 2
        SDL_SetTextureColorMod(img.texture, *INK)
        try:
            assets.draw_clip(img, 0, 0, img.w, img.h, left, bottom, 'h' if face < 0 else '', scale)
        finally:
            SDL_SetTextureColorMod(img.texture, 255, 255, 255)

    def _word(self, assets, w, h, s):
        f = word_font()
        if f is None:
            return
        x = int(w * 10 // 100 + 32 * (1.0 - s)) // 2 * 2                        # 실루엣과 반대쪽으로 조금 미끄러진다
        y = h // 2 - 40
        f.draw(x + 8, y - 8, self.word, INK)                                    # 그림자
        f.draw(x, y, self.word, (250, 250, 252))


def word_font():
    if _word_font[0] is None:
        import os
        import assets
        path = os.path.join(assets.ASSET_DIR, 'fonts', WORD_FONT[0])
        if not os.path.exists(path):
            return None
        from pico2d import load_font
        _word_font[0] = load_font(path, WORD_FONT[1])
    return _word_font[0]


def body_height(relative_path):
    """그림에서 알파가 있는 줄 수 (캔버스의 빈 곳을 뺀 몸 높이): 실루엣 배율을 고를 때 쓴다."""
    if relative_path not in _body_h:
        import os
        import assets
        from PIL import Image
        box = Image.open(os.path.join(assets.ASSET_DIR, relative_path)).getchannel('A').getbbox()
        _body_h[relative_path] = (box[3] - box[1]) if box else 1
    return _body_h[relative_path]
