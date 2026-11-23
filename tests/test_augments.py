"""증강 v2 (헤이즈 변이 + 무기 갈래, docs/plan_v7.md 2절). 창 없이: python tests/test_augments.py

- 갈래(family): 게이지 4계열(각성·위험·페이드·강화, 지금 12종) + 철파이프 연타·공중·이동 베기 + 공통 대시.
- 카드 3장: 가진 갈래 x3, 들고 있는 무기 갈래 x2, 공통 x1, 안 든 무기 갈래 x0.2. 셋 중 하나는 아직 없는 갈래.
- 진화(tier 'evo')는 같은 갈래 기본 2개를 가졌고 구현이 끝났을 때만 나온다.
- 철파이프 갈래 기본 증강은 실제로 효과가 있다 (공속, 3타 피해, 공중 피해, 대시 공격 피해, 대시).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import mutations as mu  # noqa: E402
import test_combat as tc  # noqa: E402


def _player():
    _room, p = tc.make_world()
    return p


def test_every_augment_has_a_known_family_and_tier():
    for mid, m in mu.MUTATIONS.items():
        assert m['family'] in mu.FAMILIES, mid
        assert m.get('tier', 'base') in ('base', 'evo', 'duo'), mid
    for fam in ('pipe_combo', 'pipe_air', 'pipe_dash', 'dash'):
        base = [m for m in mu.MUTATIONS.values() if m['family'] == fam and m.get('tier', 'base') == 'base']
        assert len(base) == 3, fam


def test_owned_family_is_offered_more_often():
    p = _player()
    mu.give(p, 'combo_speed')
    rng = random.Random(1)
    hits = sum(any(mu.MUTATIONS[m]['family'] == 'pipe_combo' for m in mu.offer(p, rng)) for _ in range(300))
    p2 = _player()
    rng = random.Random(1)
    base = sum(any(mu.MUTATIONS[m]['family'] == 'pipe_combo' for m in mu.offer(p2, rng)) for _ in range(300))
    assert hits > base


def test_offer_always_has_a_new_family():
    p = _player()
    for mid in ('combo_speed', 'air_power', 'dashcut_power'):
        mu.give(p, mid)
    rng = random.Random(3)
    for _ in range(100):
        fams = {mu.MUTATIONS[m]['family'] for m in mu.offer(p, rng)}
        assert fams - {mu.MUTATIONS[m]['family'] for m in mu.owned(p)}


def test_evolution_needs_two_of_its_family_and_implementation():
    p = _player()
    evo = [m for m, v in mu.MUTATIONS.items() if v.get('tier') == 'evo']
    assert evo
    rng = random.Random(5)
    assert not any(m in evo for _ in range(200) for m in mu.offer(p, rng))
    for m in evo:
        fam = mu.MUTATIONS[m]['family']
        if mu.MUTATIONS[m].get('ready'):
            for b in [k for k, v in mu.MUTATIONS.items() if v['family'] == fam and v.get('tier', 'base') == 'base'][:2]:
                mu.give(p, b)
            assert mu.available(p, m)


def test_pipe_augments_change_numbers():
    p = _player()
    assert mu.attack_speed_mult(p) == 1.0
    mu.give(p, 'combo_speed')
    assert mu.attack_speed_mult(p) < 1.0
    assert mu.pipe_damage_mult(p, finisher=True, air=False, dash=False) == 1.0
    mu.give(p, 'combo_third')
    assert mu.pipe_damage_mult(p, finisher=True, air=False, dash=False) > 1.0
    mu.give(p, 'air_power')
    assert mu.pipe_damage_mult(p, finisher=False, air=True, dash=False) > 1.0
    mu.give(p, 'dashcut_power')
    assert mu.pipe_damage_mult(p, finisher=False, air=False, dash=True) > 1.0
    slots = p.dash_max
    mu.give(p, 'dash_extra')
    assert p.dash_max == slots + 1


def test_combo_speed_shortens_real_pipe_cooldown_and_dash_iframe_lasts_longer():
    _room, p = tc.make_world()
    p.weapon.try_attack()
    plain = p.weapon.cooldown_max
    _room, p = tc.make_world()
    mu.give(p, 'combo_speed')
    p.weapon.try_attack()
    assert p.weapon.cooldown_max < plain
    mu.give(p, 'dash_iframe')
    tc.step(30)
    p.request_dash()
    tc.step(1)
    assert p.invuln_left > config.DASH_INVULN - 1 / 60


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
