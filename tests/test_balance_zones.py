"""밸런스 시뮬레이터의 구역 시나리오 테스트 (v8 7일 차, 2026-11-25, 창 없이 실행). 실행: python tests/test_balance_zones.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))

import config  # noqa: E402
import mapgen  # noqa: E402
import balance_sim  # noqa: E402


def test_zone_waves_follow_the_room_rules():
    for sc, (zone, shape, _limit) in balance_sim.ZONE_SCENARIOS.items():
        for seed in range(5):
            waves = balance_sim.zone_waves(sc, seed)
            assert waves == balance_sim.zone_waves(sc, seed)                # 같은 시드면 같은 구성
            packs = [pk for w in waves for pk in w]
            if shape == 'gate':
                assert len(waves) == 1 and sorted(k for k, _m in packs) == ['guard', 'guard', 'guard', 'hound']
                continue
            want = config.BIG_ROOM_PACKS if shape == 'big' else balance_sim.ROOM_PACKS
            assert len(packs) == want
            assert all(k in mapgen.SPECS[zone]['pool'] for k, _m in packs)  # 구역 적 목록에서만
            assert len(waves) == (3 if want >= config.WAVE_THREE_PACKS else 2)
            assert all(m is None for w in waves[:-1] for _k, m in w)        # 정예는 마지막 물결에만


def test_zone_room_runs_and_counts_enemies():
    r = balance_sim.run_one('z1_room', 'pipe', 'dodge', 0)
    assert r['result'] in ('win', 'dead', 'timeout') and r['foes'] >= balance_sim.ROOM_PACKS


def test_melee_bot_jumps_to_reach_a_hovering_drone():
    """드론은 머리 위에 뜬다. 예전 봇은 뛰지 않아 근접 무기로 한 대도 못 쳤다."""
    for weapon_id in ('pipe', 'gauntlet'):
        r = balance_sim.run_one('drone', weapon_id, 'stand', 0)
        assert r['result'] == 'win', (weapon_id, r)


def test_zone_run_carries_hp_between_fights_and_is_deterministic():
    a = balance_sim.zone_run('stage3', 'chain', 'dodge', 1)
    assert a == balance_sim.zone_run('stage3', 'chain', 'dodge', 1)
    result, reached, hp = a
    n_room, n_big, _end = balance_sim.RUN_ORDER['stage3']
    assert result in ('clear', 'dead', 'timeout') and 0 <= reached <= n_room + n_big + 1
    assert (result == 'clear') == (reached == n_room + n_big + 1) and (hp > 0) == (result == 'clear')
    r = balance_sim.run_one('slum', 'pipe', 'stand', 0, hp=40)
    assert r['hp_end'] <= 40                                          # 남은 체력으로 시작한다


def test_zone_table_markdown_has_every_zone():
    table = balance_sim.zone_table(['pipe'], ['dodge'], 1)
    text = balance_sim.zone_markdown(table, ['pipe'], ['dodge'])
    for title in ('구역 1', '구역 2', '구역 3', '크래셔', '아크'):
        assert title in text
    assert ('문지기' if balance_sim.HAS_GATEKEEPER else '관문') in text          # 문지기(v8 6일 차)가 들어오면 관문 싸움이 문지기


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
