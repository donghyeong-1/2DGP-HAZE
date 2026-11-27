"""타이틀 배경 번개 (2026-11-27 사용자: "배경에 번개 가끔 치는 애니메이션, 실제 번개처럼 번쩍하고 흰검으로 대비 한번씩 빡").

시간만 다룬다(그리기는 title_mode._draw_terminal). 한 번의 번개는 실제 번개처럼 두 번 깜빡인다:
  줄기('bolt', 어두운 하늘에 흰 번갯줄기만) 1~2프레임 -> 대비 판('flash') 2~3프레임 -> 원래 화면('dark', 번갯줄기는 남는다) 2~3프레임
  -> 대비 판 3~4프레임 -> 잔광('glow') 0.3초에 걸쳐 원래대로.
  (11/27 L1: 줄기가 하얀 하늘 위에만 있어 안 보였다. 번쩍이기 직전에 어두운 하늘에서 먼저 보여 준다. 줄기 자리 = 그 번개의 대비 판에 구운 자리)
대비 판·잔광 판·줄기 판은 tools/make_ui_mist.py가 미리 굽는다(실행 중 색 계산 없음). 간격은 6~14초, 들어오고 처음 3초는 치지 않는다.
셋에 하나쯤은 약한 번개(잔광만). 번쩍임 줄이기(options.reduce_flash)면 대비 판·번갯줄기 없이 약한 잔광만.
"""
import random

import options

FIRST_QUIET = 3.0              # 타이틀에 들어오고 이 시간 안에는 치지 않는다
FIRST_MAX = 7.0                # 첫 번개는 FIRST_QUIET~FIRST_MAX 사이
GAP_MIN, GAP_MAX = 6.0, 14.0   # 번개가 끝나고 다음 번개까지
WEAK_CHANCE = 1 / 3            # 약한 번개(잔광만)
GLOW_TIME = 0.3                # 잔광이 원래대로 돌아오는 시간
WEAK_GLOW = 0.55               # 약한 번개의 잔광 세기 (센 번개 1.0)
REDUCED_GLOW = 0.35            # 번쩍임 줄이기의 잔광 세기
FRAME = 1 / 60
FLASH_PLATES = 3               # 대비 판 수 (backgrounds/title_flash_<n>.png): 판마다 먼 하늘에 번갯줄기 하나가 다른 자리에 구워져 있다
                               # 같은 번호의 줄기 판 backgrounds/title_bolt_<n>.png (같은 자리의 줄기만, 어두운 하늘용 색)


class Storm:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.seq = []              # 지금 번개의 남은 단계 [(종류, 남은 시간)]
        self.wait = self.rng.uniform(FIRST_QUIET, FIRST_MAX)
        self.strength = 1.0        # 잔광 세기 (약한 번개는 작다)
        self.plate = None          # 이번 번개의 대비 판 번호 (0부터)
        self._glow_total = GLOW_TIME

    def roll_weak(self):
        return self.rng.random() < WEAK_CHANCE

    def make_strike(self, weak):
        """한 번의 번개 단계 목록 [(종류, 시간)]."""
        if weak:
            return [('glow', GLOW_TIME)]
        f = lambda lo, hi: self.rng.randint(lo, hi) * FRAME  # noqa: E731
        return [('bolt', f(1, 2)), ('flash', f(2, 3)), ('dark', f(2, 3)), ('flash', f(3, 4)), ('glow', GLOW_TIME)]

    def _start(self):
        weak = self.roll_weak() or options.reduce_flash
        self.seq = [list(s) for s in self.make_strike(weak)]
        self.strength = (REDUCED_GLOW if options.reduce_flash else WEAK_GLOW) if weak else 1.0
        self.plate = None if weak else self.rng.randrange(FLASH_PLATES)
        self._glow_total = GLOW_TIME

    def update(self, dt):
        if self.seq:
            self.seq[0][1] -= dt
            while self.seq and self.seq[0][1] <= 1e-9:
                over = -self.seq[0][1]
                self.seq.pop(0)
                if self.seq:
                    self.seq[0][1] -= over
            if not self.seq:
                self.wait = self.rng.uniform(GAP_MIN, GAP_MAX)
            return
        self.wait -= dt
        if self.wait <= 0:
            self._start()

    def phase(self):
        """None(평소) / 'bolt'(번쩍이기 직전, 원래 화면 + 줄기) / 'flash'(대비 판) / 'dark'(두 깜빡임 사이, 원래 화면 + 줄기) / 'glow'(잔광)."""
        return self.seq[0][0] if self.seq else None

    def glow_alpha(self):
        """잔광 판의 불투명도 (잔광 단계에서 세기 -> 0으로 줄어든다)."""
        if self.phase() != 'glow':
            return 0.0
        return max(0.0, min(1.0, self.strength * self.seq[0][1] / self._glow_total))

    def flash_plate(self):
        """대비 판 번호 (번갯줄기가 구워진 판): 'flash' 단계에만, 그 밖에는 None."""
        return self.plate if self.phase() == 'flash' else None

    def bolt_plate(self):
        """줄기 판 번호 (원래 화면 위에 흰 번갯줄기만): 'bolt'와 'dark' 단계에만, 그 밖에는 None. 대비 판 번호와 같다."""
        return self.plate if self.phase() in ('bolt', 'dark') else None

    def force(self, phase):
        """시험용: 지금 상태를 phase로 (테스트·확인 촬영)."""
        self.plate = 0
        self.strength = 1.0
        self.seq = [[phase, 1.0]] if phase else []
        self._glow_total = 2.0
