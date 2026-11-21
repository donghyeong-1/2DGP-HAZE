"""정예 적 테스트 (창 없이). 실행: python tests/test_elite.py

2026-11-21 퀄리티 상승 계획 2-4 (docs/quality_plan.md): 일반 적에 수식어가 붙은 정예가 섞인다.
- 질주(swift): 이동 x1.35, 예고 x0.8
- 강철(tough): 체력 x2.2, 무게 x1.6 (덜 밀린다)
- 폭발(volatile): 쓰러지면 0.6초 예고 뒤 폭발 (가까우면 피해 + 게이지 상승)
정예는 조각을 2배 준다. 구역이 뒤로 갈수록 자주 나온다 (스테이지 1 10%, 2 18%, 3 25%), 은신처에는 없다.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def _foe(kind='slum', mod=None, gap=300):
    room, p = tc.make_world()
    e = tc.freeze(tc.add_enemy(kind, p.x + gap, room, p))
    base_speed, base_windup, base_hp = e.stats['speed'], e.stats['windup'], e.max_hp
    if mod:
        e.make_elite(mod)
    return room, p, e, (base_speed, base_windup, base_hp)


def test_swift_is_faster_and_warns_shorter():
    room, p, e, (speed, windup, hp) = _foe('slum', 'swift')
    e.stats = dict(e.stats)
    assert e.elite == 'swift'
    assert abs(e.stats['speed'] - speed * config.ELITE_MODS['swift']['speed']) < 1e-6 or speed == 0
    assert e.stats['windup'] < windup and e.max_hp == hp


def test_tough_has_more_hp_and_is_pushed_less():
    room, p, plain, (_s, _w, hp) = _foe('slum')
    plain.take_damage(1, from_x=p.x)
    room, p, e, _ = _foe('slum', 'tough')
    assert e.max_hp == e.hp and abs(e.max_hp - hp * config.ELITE_MODS['tough']['hp']) < 1e-6
    e.take_damage(1, from_x=p.x)
    assert 0 < e.vx < plain.vx


def test_volatile_explodes_after_a_warning_and_hurts_only_nearby():
    for gap, hurt in ((120, True), (600, False)):
        room, p, e, _ = _foe('slum', 'volatile', gap=gap)
        p.invuln_left = 0.0
        hp0, g0 = p.hp, p.gauge.value
        e.hp = 1
        e.take_damage(5, from_x=p.x)
        assert p.hp == hp0                                                   # 바로 터지지 않는다 (예고)
        tc.step(int(config.ELITE_BURST_DELAY * 60) + 3)
        assert (p.hp < hp0) == hurt, (gap, p.hp, hp0)
        if hurt:
            assert p.gauge.value > g0 - 1                                    # 게이지가 오른다 (피격 감소보다 크게)


def test_elite_gives_double_shards():
    room, p, e, _ = _foe('slum', 'tough')
    s0 = p.shards
    e.hp = 1
    e.take_damage(5, from_x=p.x)
    assert p.shards - s0 == 2 * config.SHARDS_PER_KILL.get('slum', 1)


def test_elite_rate_grows_by_stage_and_hideout_has_none():
    import stage
    rates = {}
    for name in ('stage1', 'stage2', 'stage3'):
        rng = random.Random(1)
        rolls = [stage.roll_elite(rng, name) for _ in range(4000)]
        rates[name] = sum(1 for r in rolls if r) / len(rolls)
        assert set(r for r in rolls if r) == set(config.ELITE_MODS), name
    assert 0.07 < rates['stage1'] < rates['stage2'] < rates['stage3'] < 0.3, rates
    assert stage.roll_elite(random.Random(1), 'hideout') is None


def test_elites_are_marked_on_screen():
    room, p, e, _ = _foe('slum', 'volatile')
    assert e.elite_label() == config.ELITE_MODS['volatile']['name']
    assert e.elite_color() == config.ELITE_MODS['volatile']['color']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
