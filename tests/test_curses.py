"""저주 증강 (2026-11-26 사용자 제안: 하데스의 혼돈처럼). 창 없이: python tests/test_curses.py

- 증강 카드 셋 중 한 장이 가끔 저주 카드로 나온다 (첫 보상·저주 중에는 안 나온다).
- 고르면 저주가 바로 걸리고, 전투방을 정해진 수만큼 깨면 풀리면서 보상(등급에 따라 기본 증강 둘 / 진화 / 합성)을 받는다.
- 저주 여섯 가지: 공격력 -20%, 적중·처치 게이지 -40%, 게이지 한계 -30, 무기 교체 잠김, 받는 피해 2배, 오버로드하면 사망.
- 카드에는 저주의 내용·기간과 보상의 등급(결정 1~3개)만 보이고 보상은 '???'.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import curse as curses  # noqa: E402
import mutations as mu  # noqa: E402
import test_combat as tc  # noqa: E402


def _player(first='pipe', second='gauntlet'):
    p = tc.make_world()[1]
    p.set_loadout(first, second)
    return p


def _clear_rooms(p, n, seed=1):
    out = []
    for _ in range(n):
        out.append(curses.on_room_clear(p, random.Random(seed)))
    return out


def test_six_curses_in_three_grades_with_reward_hidden():
    assert len(curses.CURSES) == 6
    for grade in (1, 2, 3):
        assert sum(1 for c in curses.CURSES.values() if c['grade'] == grade) == 2
    import mutation_mode
    p = _player()
    for cid, c in curses.CURSES.items():
        info = curses.card_info(p, curses.CARD + cid)
        assert '???' in info['reward'] and info['grade'] == c['grade']     # 보상은 숨기고 등급만 (카드가 결정 아이콘 수로 그린다)
        assert str(c['rooms']) in info['sub']                              # 기간(전투방 수)이 보인다
        assert len(mutation_mode._wrap(info['desc'], 13)) <= 2, cid        # 두 줄까지 (그 아래는 등급 아이콘과 '보상 ???')


def test_curse_card_is_mixed_into_augment_cards_sometimes():
    p = _player()
    cards = mu.offer(p, random.Random(1))
    assert curses.mix_in(p, list(cards), random.Random(1), chance=1.0) == cards      # 첫 보상(증강이 하나도 없을 때)에는 안 나온다
    mu.give(p, 'combo_speed')
    seen = 0
    for seed in range(400):
        rng = random.Random(seed)
        cards = mu.offer(p, rng)
        mixed = curses.mix_in(p, list(cards), rng)
        n = sum(c.startswith(curses.CARD) for c in mixed)
        assert n <= 1 and len(mixed) == len(cards)
        seen += n
    assert 0.2 < seen / 400 < 0.4, seen                                    # 약 30%
    curses.take(p, curses.CARD + 'weak')
    assert all(not c.startswith(curses.CARD) for s in range(50)           # 저주 중에는 또 나오지 않는다
               for c in curses.mix_in(p, mu.offer(p, random.Random(s)), random.Random(s), chance=1.0))


def test_curse_card_never_replaces_an_evolution_or_duo_card():
    p = _player('pipe', 'pistol')
    for m in ('combo_evo', 'dash_evo'):
        mu.give(p, m)
    for seed in range(60):
        rng = random.Random(seed)
        mixed = curses.mix_in(p, mu.offer(p, rng), rng, chance=1.0)
        assert 'duo_echo_combo' in mixed and any(c.startswith(curses.CARD) for c in mixed)


def test_lock_curse_needs_two_weapons():
    p = tc.make_world()[1]                                                 # 철파이프 하나만
    mu.give(p, 'combo_speed')
    for seed in range(200):
        mixed = curses.mix_in(p, mu.offer(p, random.Random(seed)), random.Random(seed), chance=1.0)
        assert curses.CARD + 'lock' not in mixed


def test_weak_curse_cuts_damage_and_thirst_cuts_gauge_gain():
    p = _player()
    base = mu.damage_mult(p)
    curses.take(p, curses.CARD + 'weak')
    assert abs(mu.damage_mult(p) - base * 0.8) < 1e-9
    _clear_rooms(p, curses.CURSES['weak']['rooms'])
    assert curses.active(p) is None and abs(mu.damage_mult(p) - base) < 1e-9
    p = _player()
    p.gauge.value = 30.0
    curses.take(p, curses.CARD + 'thirst')
    p.gauge.add(10, 'hit')
    assert abs(p.gauge.value - 36.0) < 1e-6                                # 적중으로 얻는 게이지 -40%
    p.gauge.add(10, 'steam')
    assert abs(p.gauge.value - 46.0) < 1e-6                                # 적의 헤이즈 공격으로 오르는 것은 그대로
    p.gauge.add(-10, 'hit')
    assert abs(p.gauge.value - 36.0) < 1e-6                                # 줄어드는 것도 그대로
    _clear_rooms(p, curses.CURSES['thirst']['rooms'])
    p.gauge.add(10, 'hit')
    assert abs(p.gauge.value - 46.0) < 1e-6


def test_lowcap_curse_lowers_the_overload_line_and_restores_it():
    p = _player()
    cap = p.gauge.cap
    p.gauge.value = cap - 5.0
    curses.take(p, curses.CARD + 'lowcap')
    assert p.gauge.cap == cap - 30
    assert p.gauge.value < p.gauge.cap - config.CRITICAL_MARGIN            # 걸리는 순간 바로 터지지 않게 위험 구간 아래로 내린다
    import items
    items.apply(p, 'cap') if hasattr(items, 'apply') else None
    _clear_rooms(p, curses.CURSES['lowcap']['rooms'])
    assert curses.active(p) is None
    assert p.gauge.cap >= cap                                              # 풀리면 원래 한계 (그 사이 얻은 한계 강화도 남는다)


def test_lock_curse_blocks_weapon_swap():
    p = _player('pipe', 'gauntlet')
    slot = p.slot
    curses.take(p, curses.CARD + 'lock')
    assert p.swap_weapon(strike=True) is False and p.slot == slot
    _clear_rooms(p, curses.CURSES['lock']['rooms'])
    assert p.swap_weapon() is not False and p.slot != slot


def test_frail_curse_doubles_damage_taken():
    p = _player()
    base = mu.taken_mult(p)
    curses.take(p, curses.CARD + 'frail')
    assert abs(mu.taken_mult(p) - base * 2.0) < 1e-9
    hp = p.hp
    p.invuln_left = 0.0
    p.take_hit(10)
    assert hp - p.hp == 20


def test_doom_curse_kills_on_overload():
    p = _player()
    curses.take(p, curses.CARD + 'doom')
    p.gauge.add(p.gauge.cap, 'hit')                                        # 오버로드
    assert p.hp <= 0 and p.state == 'DEAD'
    q = _player()                                                          # 저주가 없으면 오버로드는 피해만 준다
    q.gauge.add(q.gauge.cap, 'hit')
    assert q.hp > 0


def test_curse_counts_combat_rooms_and_then_pays_by_grade():
    p = _player('pipe', 'gauntlet')
    mu.give(p, 'combo_speed')
    curses.take(p, curses.CARD + 'weak')                                   # ★: 기본 증강 둘
    n = len(mu.owned(p))
    first = _clear_rooms(p, curses.CURSES['weak']['rooms'] - 1)
    assert all(r is None for r in first) and curses.active(p) == 'weak'    # 아직 걸려 있다
    assert curses.rooms_left(p) == 1
    got = curses.on_room_clear(p, random.Random(3))
    assert curses.active(p) is None and len(got) == 2
    assert len(mu.owned(p)) == n + 2 and all(mu.tier(m) == 'base' for m in got)
    assert all(mu.offerable(p, m) for m in got)                            # 든 무기로 쓸 수 있는 것만

    curses.take(p, curses.CARD + 'lock')                                   # ★★: 든 무기의 진화 하나를 바로
    got = _clear_rooms(p, curses.CURSES['lock']['rooms'], seed=4)[-1]
    assert len(got) == 1 and mu.tier(got[0]) == 'evo' and mu.has(p, got[0]) and mu.offerable(p, got[0])

    curses.take(p, curses.CARD + 'frail')                                  # ★★★: 합성 하나를 재료 진화까지
    got = _clear_rooms(p, curses.CURSES['frail']['rooms'], seed=5)[-1]
    duo = [m for m in got if mu.tier(m) == 'duo']
    assert len(duo) == 1 and mu.has(p, duo[0])
    assert all(mu.has(p, r) for r in mu.MUTATIONS[duo[0]]['requires'])
    assert mu.offerable(p, duo[0])


def test_top_grade_reward_falls_back_when_no_duo_can_be_made():
    p = tc.make_world()[1]
    p.set_loadout('gauntlet')                                              # 건틀릿 하나: 짝이 정해진 합성을 만들 수 없다
    mu.give(p, 'charge_fast')
    curses.take(p, curses.CARD + 'doom')
    got = _clear_rooms(p, curses.CURSES['doom']['rooms'], seed=6)[-1]
    assert got and all(mu.tier(m) == 'evo' for m in got) and len(got) == 2   # 대신 진화 둘


def test_stage_mixes_the_card_in_and_counts_cleared_rooms():
    """방 보상(증강)에 저주 카드가 섞이고, 전투방을 깨면 stage가 저주를 센다."""
    import inspect
    import stage
    src = inspect.getsource(stage.Stage)
    assert 'curse.mix_in' in src and 'curse.on_room_clear' in src


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
