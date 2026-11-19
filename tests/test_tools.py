"""개발 도구 검사: 밸런스 시뮬레이터가 지금 게임 코드로 돌아가는지 (창 없이). 실행: python tests/test_tools.py"""
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import balance_sim  # noqa: E402
import config  # noqa: E402


def test_balance_sim_runs_every_weapon_and_reports_fields():
    for weapon_id in balance_sim.WEAPONS:
        r = balance_sim.run_one('slum', weapon_id, 'stand', 0)
        assert r['result'] in ('win', 'dead', 'timeout')
        assert set(r) >= {'time', 'hp_lost', 'gauge_end', 'gauge_min', 'gauge_max', 'zones'}
        assert abs(sum(r['zones'].values()) - 1.0) < 0.01                  # 구간 비율의 합은 1


def test_balance_sim_is_deterministic_per_seed():
    a = balance_sim.run_one('hound', 'pipe', 'dodge', 3)
    b = balance_sim.run_one('hound', 'pipe', 'dodge', 3)
    assert a == b                                                         # 같은 시드면 같은 결과 (전후 비교의 전제)


def test_balance_sim_start_gauge_option():
    r = balance_sim.run_one('slum', 'pipe', 'stand', 0, gauge=70)
    assert r['gauge_max'] >= 70


def test_balance_sim_counts_overloads():
    r = balance_sim.run_one('group', 'knife', 'stand', 0, gauge=95)       # 위험 구간에서 식칼 연사: 오버로드가 난다
    assert r['overloads'] >= 1, r


def test_check_gait_tells_alternating_steps_from_a_repeated_stride():
    import check_gait
    walk = [os.path.join(ROOT, 'assets', 'sprites', 'unified', f'n09_walk_{i}.png') for i in range(1, 9)]
    assert check_gait.gait_ratio(walk)[2] >= check_gait.PASS_RATIO          # 걷기: 왼발·오른발 걸음이 다르다
    repeated = walk[:4] + walk[:4]                                          # 같은 걸음 두 번 = 발이 교차하지 않는다
    assert check_gait.gait_ratio(repeated)[2] < 0.1


def test_window_display_choice_from_argument_or_environment():
    import window_place
    old = os.environ.pop('HAZE_DISPLAY', None)
    try:
        assert window_place.wanted_display() is None                       # 정하지 않으면 옮기지 않는다
        os.environ['HAZE_DISPLAY'] = '2'
        assert window_place.wanted_display() == 2
        assert window_place.wanted_display(1) == 1                          # 직접 넘긴 값이 우선
        os.environ['HAZE_DISPLAY'] = 'abc'
        assert window_place.wanted_display() is None
    finally:
        os.environ.pop('HAZE_DISPLAY', None)
        if old is not None:
            os.environ['HAZE_DISPLAY'] = old


def test_balance_sim_meta_option_applies_permanent_upgrades():
    """--meta max: 정비사 강화를 모두 최대로 한 플레이어로 싸운다 (영구 성장이 난이도를 얼마나 낮추는지 본다)."""
    import meta
    base = balance_sim.run_one('slum', 'pipe', 'stand', 0)
    full = balance_sim.run_one('slum', 'pipe', 'stand', 0, meta_levels='max')
    top = meta.UPGRADES['hp']['max']
    assert base['max_hp'] == config.PLAYER_HP and full['max_hp'] == config.PLAYER_HP + top * config.META_HP


def test_economy_counts_crystals_for_each_way_a_run_can_end():
    rows = balance_sim.economy()
    names = [r[0] for r in rows]
    assert names[0].startswith('스테이지 1') and names[-1].startswith('탈출')
    assert rows[-1][1] > rows[0][1] > 0                                     # 멀리 갈수록 많이 받는다
    import meta
    assert balance_sim.total_meta_cost() == sum(sum(u['prices']) for u in meta.UPGRADES.values()) + config.META_KEEPER_PRICE


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
