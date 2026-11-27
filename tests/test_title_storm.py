"""타이틀 배경 번개 (2026-11-27 사용자: "실제 번개처럼 번쩍하고 흰검으로 대비 한번씩 빡"). 창 없이: python tests/test_title_storm.py

- 간격 6~14초, 타이틀에 들어오고 처음 3초는 치지 않는다.
- 한 번의 번개: 대비 판 2~3프레임 -> 원래 화면 2~3프레임 -> 대비 판 3~4프레임 -> 잔광 0.3초. 전체 0.6초 안쪽.
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


def test_one_full_strike_is_flash_dark_flash_glow_within_06s():
    for seed in range(40):
        s = ts.Storm(seed=seed)
        seq = s.make_strike(weak=False)
        kinds = [k for k, _d in seq]
        assert kinds == ['flash', 'dark', 'flash', 'glow'], kinds
        frames = [round(d * 60) for _k, d in seq]
        assert 2 <= frames[0] <= 3 and 2 <= frames[1] <= 3 and 3 <= frames[2] <= 4, frames
        assert abs(seq[3][1] - 0.3) < 0.051
        assert sum(d for _k, d in seq) <= 0.6


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
        assert all(ph in (None, 'glow') for _t, ph in frames)
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
        for phase in ('flash', 'glow'):
            calls.clear()
            tm._storm[0] = ts.Storm(seed=1)
            tm._storm[0].force(phase)
            tm._draw_terminal()
            plate = 'backgrounds/title_flash_1.png' if phase == 'flash' else 'backgrounds/title_glow.png'
            assert plate in calls, (phase, calls[:6])
            i = calls.index(plate)
            assert calls.index('backgrounds/title_mist.png') < i
            for later in ('light/title_shade.png', 'ui/um_logo_title.png', 'text:TOWER SURVEILLANCE // INMATE N-09', 'text:' + tm.MENU[1].label):
                assert calls.index(later) > i, (phase, later)
            assert 'ui/um_lamps.png' not in calls                  # 오른쪽 위 등 판은 지웠다 (11/27)
            assert not any('n09' in str(c) for c in calls)          # 주인공도
    finally:
        for n, f in saved.items():
            setattr(assets, n, f)
        kit.text, tm._weather = saved_text, saved_weather
        tm._storm[0] = None


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
