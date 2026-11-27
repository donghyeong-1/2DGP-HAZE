"""타이틀 배경 번개 (2026-11-27 사용자: "실제 번개처럼 번쩍하고 흰검으로 대비 한번씩 빡"). 창 없이: python tests/test_title_storm.py

- 간격 6~14초, 타이틀에 들어오고 처음 3초는 치지 않는다.
- 한 번의 번개: 줄기 1~2프레임(어두운 하늘에 흰 번갯줄기) -> 대비 판 2~3프레임 -> 원래 화면 2~3프레임(줄기는 남는다)
  -> 대비 판 3~4프레임 -> 잔광 0.3초. 전체 0.6초 안쪽. 줄기 단계의 판 번호 = 뒤따르는 대비 판 번호 (L1 번갯줄기, 11/27).
- 셋에 하나쯤은 약한 번개(잔광만). 1초에 세 번 넘게 번쩍이지 않는다. 번쩍임 줄이기면 대비 판 없이 약한 잔광만.
- 번쩍임은 배경 층에만: 글자 뒤 어둠·로고·메뉴·감시 글자는 번쩍임 위에 그려진다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import options  # noqa: E402
import title_storm as ts  # noqa: E402

FRAME = 1 / 60


def run(storm, seconds, dt=FRAME):
    """프레임마다 (시각, 상태)를 모은다."""
    out, t = [], 0.0
    for _ in range(int(seconds / dt)):
        storm.update(dt)
        t += dt
        out.append((t, storm.phase()))
    return out


def strikes(frames):
    """번개가 시작한 시각들 (평소 -> 번개 상태로 바뀐 프레임)."""
    starts, prev = [], None
    for t, ph in frames:
        if ph is not None and prev is None:
            starts.append(t)
        prev = ph
    return starts


def test_quiet_start_and_interval_range():
    for seed in range(20):
        starts = strikes(run(ts.Storm(seed=seed), 200))
        assert starts and starts[0] >= ts.FIRST_QUIET, (seed, starts[:1])
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        assert gaps and all(ts.GAP_MIN - 0.05 <= g <= ts.GAP_MAX + 0.7 for g in gaps), (seed, gaps)   # 시작 사이 = 간격 + 번개 길이
    assert ts.FIRST_QUIET >= 2.5 and (ts.GAP_MIN, ts.GAP_MAX) == (6.0, 14.0)


def test_one_full_strike_is_bolt_flash_dark_flash_glow_within_06s():
    """센 번개의 첫 단계는 줄기 단계(1~2프레임), 그 뒤 대비 판 -> 원래 화면 -> 대비 판 -> 잔광. 전체 0.6초 안쪽."""
    lens = set()
    for seed in range(40):
        s = ts.Storm(seed=seed)
        seq = s.make_strike(weak=False)
        kinds = [k for k, _d in seq]
        assert kinds == ['bolt', 'flash', 'dark', 'flash', 'glow'], kinds
        frames = [round(d * 60) for _k, d in seq]
        assert 1 <= frames[0] <= 2 and 2 <= frames[1] <= 3 and 2 <= frames[2] <= 3 and 3 <= frames[3] <= 4, frames
        lens.add(frames[0])
        assert abs(seq[4][1] - 0.3) < 0.051
        assert sum(d for _k, d in seq) <= 0.6
    assert lens == {1, 2}


def test_bolt_phase_only_in_strong_strikes():
    """약한 번개(잔광만)와 번쩍임 줄이기에는 줄기 단계가 없다."""
    assert [k for k, _d in ts.Storm(seed=2).make_strike(weak=True)] == ['glow']
    old = options.reduce_flash
    try:
        options.reduce_flash = True
        s = ts.Storm(seed=4)
        for _ in range(120 * 60):
            s.update(FRAME)
            assert s.phase() != 'bolt' and s.bolt_plate() is None
    finally:
        options.reduce_flash = old
    s = ts.Storm(seed=6)
    for _ in range(200 * 60):
        s.update(FRAME)
        if s.phase() == 'glow' and s.strength < 1.0:          # 약한 번개 도중
            assert s.bolt_plate() is None


def test_bolt_plate_matches_following_flash_plate_and_stays_in_dark():
    """줄기 단계의 판 번호 = 뒤따르는 대비 판 번호 (줄기 자리가 같다). 두 깜빡임 사이(dark)에도 같은 줄기가 남는다."""
    checked = 0
    for seed in range(12):
        s = ts.Storm(seed=seed)
        bolt = None
        for _ in range(90 * 60):
            s.update(FRAME)
            ph = s.phase()
            if ph == 'bolt':
                bolt = s.bolt_plate()
                assert bolt is not None and 0 <= bolt < ts.FLASH_PLATES
                assert s.flash_plate() is None
            elif ph == 'flash':
                assert bolt is not None and s.flash_plate() == bolt, (seed, bolt, s.flash_plate())
                checked += 1
            elif ph == 'dark':
                assert s.bolt_plate() == bolt
            elif ph is None:
                bolt = None
    assert checked


def test_weak_strikes_are_glow_only_about_one_in_three():
    s = ts.Storm(seed=1)
    weak = [s.make_strike(weak=True)]
    assert [k for k, _d in weak[0]] == ['glow']
    picks = [ts.Storm(seed=n).roll_weak() for n in range(600)]
    assert 0.2 < sum(picks) / len(picks) < 0.45


def test_no_more_than_three_flashes_per_second():
    for seed in range(10):
        frames = run(ts.Storm(seed=seed), 120)
        ons, prev = [], None
        for t, ph in frames:
            if ph == 'flash' and prev != 'flash':
                ons.append(t)
            prev = ph
        assert ons
        for i, t in enumerate(ons):
            assert sum(1 for u in ons[i:] if u - t < 1.0) <= 3


def test_reduce_flash_has_no_contrast_plate():
    old = options.reduce_flash
    try:
        options.reduce_flash = True
        s = ts.Storm(seed=3)
        frames, alphas = [], []
        for _ in range(120 * 60):
            s.update(FRAME)
            frames.append((0, s.phase()))
            alphas.append(s.glow_alpha())
            assert s.flash_plate() is None
        assert strikes(frames)
        assert all(ph in (None, 'glow') for _t, ph in frames)          # 줄기 단계도 대비 판도 없다
        assert 0 < max(alphas) <= ts.REDUCED_GLOW
    finally:
        options.reduce_flash = old


def test_glow_fades_out_and_bolt_plate_only_while_flashing():
    s = ts.Storm(seed=5)
    seen_glow, seen_bolt = [], []
    for _ in range(60 * 60):
        s.update(FRAME)
        ph = s.phase()
        if ph == 'glow':
            seen_glow.append(s.glow_alpha())
        if s.flash_plate() is not None:
            seen_bolt.append(ph)
            assert 0 <= s.flash_plate() < ts.FLASH_PLATES
    assert seen_glow and max(seen_glow) <= 1.0 and min(seen_glow) >= 0.0
    assert set(seen_bolt) == {'flash'}


def test_flash_is_drawn_under_the_text_layers():
    """번쩍이는 동안에도 어둠·로고·메뉴·감시 글자가 번쩍임 판 위에 그려진다 (그리는 순서를 기록해 본다)."""
    import assets
    import hud_kit as kit
    import title_mode as tm
    calls = []

    class Img:
        def __init__(self, rel):
            self.rel, self.w, self.h = rel, 64, 32

    saved = {n: getattr(assets, n) for n in ('image', 'draw_image', 'draw_clip', 'draw_rect_color', 'draw_text', 'text_width',
                                             'draw_image_tinted')}
    saved_text, saved_weather = kit.text, tm._weather
    try:
        assets.image = Img
        assets.draw_image = lambda img, *a, **k: calls.append(img.rel)
        assets.draw_image_tinted = lambda img, *a, **k: calls.append(img.rel)
        assets.draw_clip = lambda img, *a, **k: calls.append(img.rel)
        assets.draw_rect_color = lambda *a, **k: calls.append('rect')
        assets.draw_text = lambda x, y, s, *a, **k: calls.append('text:' + s)
        assets.text_width = lambda s, *a, **k: 10 * len(s)
        kit.text = lambda x, y, s, *a, **k: calls.append('text:' + s)

        class Rain:
            def draw(self):
                calls.append('rain')
        tm._weather = lambda: Rain()
        plates = {'flash': 'backgrounds/title_flash_1.png', 'glow': 'backgrounds/title_glow.png',
                  'bolt': 'backgrounds/title_bolt_1.png', 'dark': 'backgrounds/title_bolt_1.png'}
        for phase, plate in plates.items():
            calls.clear()
            tm._storm[0] = ts.Storm(seed=1)
            tm._storm[0].force(phase)
            tm._draw_terminal()
            assert plate in calls, (phase, calls[:6])
            i = calls.index(plate)
            assert calls.index('backgrounds/title_mist.png') < i < calls.index('rain')
            # 대비 판일 때는 머리글 뒤 어둠을 뺀 시트 (흰 하늘 위 회색 얼룩, L1)
            shade = 'light/title_shade_flash.png' if phase == 'flash' else 'light/title_shade.png'
            assert shade in calls and ('light/title_shade.png' if phase == 'flash' else 'light/title_shade_flash.png') not in calls
            head = 'CAM 04 · 제9구역 폐기물 슬럼 · REC' if phase == 'flash' else 'TOWER SURVEILLANCE // INMATE N-09'   # R1: 번쩍일 때 첫 줄은 뺀다
            for later in (shade, 'ui/um_logo_title.png', head, tm.MENU[1].label):
                hit = [n for n, c in enumerate(calls) if c == later or (isinstance(c, str) and c.startswith('text:') and c.endswith(later))]
                assert hit and hit[0] > i, (phase, later)
            if phase in ('flash', 'glow'):
                assert not any('title_bolt' in str(c) for c in calls), phase
            assert 'ui/um_lamps.png' not in calls                  # 오른쪽 위 등 판은 지웠다 (11/27)
            assert not any('n09' in str(c) for c in calls)          # 주인공도
    finally:
        for n, f in saved.items():
            setattr(assets, n, f)
        kit.text, tm._weather = saved_text, saved_weather
        tm._storm[0] = None


# ----- R1 나머지 손질 (11/27): 긴 줄기, 번쩍일 때 로고 그늘·머리글 -----
ROOT = os.path.join(HERE, '..')
BOLT_MIN_LEN = 280          # 줄기의 세로 길이 (화면 px, 보이는 픽셀의 위 끝 ~ 아래 끝. L1은 약 170~230)
BOLT_TOP_MAX = 16           # 줄기 위 끝이 이보다 위 (화면 맨 위에서 내려온다)


def _png(rel):
    import numpy as np
    from PIL import Image
    return np.array(Image.open(os.path.join(ROOT, 'assets', rel)).convert('RGBA'))


def test_r1_bolt_is_long_and_starts_at_the_top_of_the_sky():
    """줄기 판 셋: 보이는 줄기가 화면 맨 위(하늘 위쪽)에서 시작해 BOLT_MIN_LEN 이상 내려온다. 판마다 자리가 다르다."""
    import numpy as np
    spots = []
    for n in range(1, ts.FLASH_PLATES + 1):
        a = _png(f'backgrounds/title_bolt_{n}.png')
        ys, xs = np.nonzero(a[:, :, 3])
        assert ys.min() <= BOLT_TOP_MAX, (n, ys.min())
        assert ys.max() - ys.min() >= BOLT_MIN_LEN, (n, ys.max() - ys.min())
        spots.append(int(np.median(xs)))
    assert min(abs(a - b) for i, a in enumerate(spots) for b in spots[i + 1:]) > 150, spots


def test_r1_bolt_plate_and_flash_plate_share_the_bolt_pixel_for_pixel():
    """줄기 판의 줄기 = 같은 번호 대비 판의 줄기 (같은 자리·같은 색). 대비 판의 그 밖의 줄기 색 픽셀은 없다."""
    import numpy as np
    for n in range(1, ts.FLASH_PLATES + 1):
        b, f = _png(f'backgrounds/title_bolt_{n}.png'), _png(f'backgrounds/title_flash_{n}.png')
        on = b[:, :, 3] > 0
        assert (f[on][:, :3] == b[on][:, :3]).all(), n
        bright = (f[:, :, :3] >= 200).all(axis=2)            # 줄기 색(흰 심·옅은 가장자리)은 하늘(176,190,232)보다 밝다
        assert not (bright & ~on).any(), n
        # 2px 격자: 줄기 알파가 2x2 칸 단위
        m = on.astype(int)
        assert (m[0::2, 0::2] == m[1::2, 0::2]).all() and (m[0::2, 0::2] == m[0::2, 1::2]).all() and (m[0::2, 0::2] == m[1::2, 1::2]).all(), n


def _logo_box():
    import config
    import title_mode as tm
    logo = _png('ui/um_logo_title.png')
    h, w = logo.shape[:2]
    top = config.SCREEN_H - tm.LOGO_Y - h                   # 그림 줄 (위가 0)
    left = config.SCREEN_W // 2 - w // 2
    return logo, top, left


def test_r1_flash_has_no_grey_halo_around_the_logo_and_logo_sits_on_dark():
    """번쩍이는 프레임: 로고·메뉴 뒤 어둠(부드러운 알파)을 깔지 않는다(흰 하늘 위 회색 둥근 그늘). 대신 대비 판에
    로고 둘레 어두운 실루엣이 구워져 있어 로고 글자 바로 둘레는 실루엣 색이다 (로고가 흰 하늘 위에서도 읽힌다)."""
    import numpy as np
    import config
    shade = _png('light/title_shade_flash.png')[:, :, 3]
    logo, top, left = _logo_box()
    s = 2                                                    # 어둠 시트는 절반 크기
    y0, y1 = max(0, (top - 200) // s), (top + logo.shape[0] + 120) // s
    x0, x1 = (left - 200) // s, (left + logo.shape[1] + 200) // s
    assert shade[y0:y1, x0:x1].max() == 0, shade[y0:y1, x0:x1].max()
    from scipy import ndimage
    ring = ndimage.binary_dilation(logo[:, :, 3] > 0, iterations=4) & ~(logo[:, :, 3] > 0)
    for n in range(1, ts.FLASH_PLATES + 1):
        f = _png(f'backgrounds/title_flash_{n}.png')[top:top + logo.shape[0], left:left + logo.shape[1], :3]
        dark = f.astype(int).sum(axis=2) < 60
        assert dark[ring].mean() > 0.99, (n, dark[ring].mean())
    assert config.SCREEN_W == shade.shape[1] * s


def test_r1_flash_header_first_line_is_not_drawn():
    """번쩍이는 프레임에만 머리글 첫 줄을 그리지 않는다 (흰 하늘 위에서 글자와 그림자가 겹쳐 지저분했다. 어두운 한 색으로 그려 보니
    들보 위 기둥 머리에 글자 일부가 묻혀 빼기로 했다). 둘째 줄(검은 들보 위)은 그대로. 평소·줄기·잔광 프레임은 그림자 있는 인광 글자 그대로."""
    import assets
    import title_mode as tm
    first = 'TOWER SURVEILLANCE // INMATE N-09'
    saved = {n: getattr(assets, n) for n in ('image', 'draw_image', 'draw_clip', 'draw_rect_color', 'draw_text', 'text_width',
                                             'draw_image_tinted')}
    saved_weather = tm._weather
    calls = []

    class Img:
        def __init__(self, rel):
            self.rel, self.w, self.h = rel, 64, 32

    class Rain:
        def draw(self):
            pass
    try:
        assets.image = Img
        for n in ('draw_image', 'draw_clip', 'draw_rect_color', 'draw_image_tinted'):
            setattr(assets, n, lambda *a, **k: None)
        assets.draw_text = lambda x, y, s, color, *a, **k: calls.append((s, tuple(color)))
        assets.text_width = lambda s, *a, **k: 10 * len(s)
        tm._weather = lambda: Rain()
        for phase in (None, 'bolt', 'flash', 'dark', 'glow'):
            calls.clear()
            tm._storm[0] = ts.Storm(seed=1)
            tm._storm[0].force(phase)
            tm._draw_terminal()
            mine = [c for s, c in calls if s == first]
            second = [c for s, c in calls if s.startswith('CAM 04')]
            assert len(second) == 2, (phase, second)                     # 둘째 줄은 늘 그림자 + 글자
            if phase == 'flash':
                assert mine == [], mine
            else:
                assert len(mine) == 2 and tuple(tm.PH) in mine, (phase, mine)   # 그림자 + 인광 글자
    finally:
        for n, f in saved.items():
            setattr(assets, n, f)
        tm._weather = saved_weather
        tm._storm[0] = None


# ----- R2 (11/27): 줄기가 글자 자리를 지나지 않고, 어두운 화면에서 한 줄로 읽힌다 -----
TEXT_CLEAR = 16              # 줄기와 글자 상자 사이 (px)
BOLT_MAX_GAP = 60            # 어두운 화면(줄기 판)에서 보이는 줄기 조각 사이 가장 큰 세로 끊김 (px). R1 판 3은 76(가운데 조각은 머리글 뒤 어둠에 묻혀 두 조각으로 보였다), 판 1·2는 36·35
BOLT_APART = 250             # 판끼리 줄기 가로 자리(가운데) 차이 (px)


def _title_text_boxes():
    """타이틀 글자 상자 (왼, 위, 오른, 아래) 화면 px, 위가 0. 머리글 두 줄은 실제 창에서 잰 폭(x 110~556, 첫 줄 위 끝 48 ~ 둘째 줄 아래 끝 98)."""
    import config
    import title_mode as tm
    W, H = config.SCREEN_W, config.SCREEN_H
    logo = _png('ui/um_logo_title.png')
    lh, lw = logo.shape[:2]
    boxes = [('head', (110, 46, 560, 100)),
             ('logo', (W // 2 - lw // 2, H - tm.LOGO_Y - lh, W // 2 + lw // 2, H - tm.LOGO_Y)),
             ('logo_sub', (W // 2 - 50, H - (tm.LOGO_Y - 28) - 16, W // 2 + 50, H - (tm.LOGO_Y - 28) + 16)),
             ('version', (W - tm.TERM_MARGIN - 150, H - 60 - 16, W - tm.TERM_MARGIN, H - 60 + 16))]
    for b in tm.MENU:                                       # 메뉴 한 줄: 고르면 글자 폭 + 커서(왼쪽 34px)까지
        cy = H - (b.y + b.h // 2)
        boxes.append(('menu_' + b.key, (W // 2 - 120, cy - 22, W // 2 + 90, cy + 22)))
    return boxes


def _bolt_visible(n):
    import numpy as np
    return _png(f'backgrounds/title_bolt_{n}.png')[:, :, 3] > 0


def test_r2_bolts_keep_clear_of_the_title_text():
    """판 셋 모두 줄기의 보이는 픽셀이 머리글·로고·'헤이즈'·메뉴·판번호 글자 상자(+TEXT_CLEAR)와 겹치지 않는다
    (R1 판 3은 위쪽 조각이 왼쪽 위 머리글 글자를 지나갔다)."""
    import numpy as np
    for n in range(1, ts.FLASH_PLATES + 1):
        v = _bolt_visible(n)
        for name, (x0, y0, x1, y1) in _title_text_boxes():
            m = TEXT_CLEAR
            assert not v[max(0, y0 - m):y1 + m, max(0, x0 - m):x1 + m].any(), (n, name)


def test_r2_bolt_reads_as_one_line_on_the_dark_screen():
    """어두운 화면(줄기 판)에서 보이는 줄기 조각 사이 가장 큰 세로 끊김이 BOLT_MAX_GAP 이하 (앞 구조물에 가려 끊겨도 멀지 않게)."""
    import numpy as np
    for n in range(1, ts.FLASH_PLATES + 1):
        rows = np.nonzero(_bolt_visible(n).any(axis=1))[0]
        gap = int(np.diff(rows).max()) - 1
        assert gap <= BOLT_MAX_GAP, (n, gap)


def test_r2_bolts_stand_apart():
    """판끼리 줄기 가로 자리(보이는 픽셀의 가운데값)가 BOLT_APART px 이상 다르다."""
    import numpy as np
    xs = [int(np.median(np.nonzero(_bolt_visible(n))[1])) for n in range(1, ts.FLASH_PLATES + 1)]
    assert min(abs(a - b) for i, a in enumerate(xs) for b in xs[i + 1:]) >= BOLT_APART, xs


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
