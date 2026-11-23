"""물약 (v7, 2026-11-23, docs/plan_v7.md 5-C). 창 없이 실행: python tests/test_potion.py

- 판은 물약 POTION_START병으로 시작하고 최대 POTION_MAX병.
- Q(키 설정 'potion')로 마시면 체력 POTION_HEAL 회복, POTION_COOLDOWN 동안은 다시 못 마신다.
- 체력이 가득하거나 물약이 없거나 쓰러졌으면 마시지 않는다.
- 정비방 '물약'(item 'heal')은 한 병을 채운다(가득하면 못 산다).
- 무기 바꾸기 기본 키는 Tab으로 옮겼다(Q는 물약).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import sdl2  # noqa: E402

import config  # noqa: E402
import items  # noqa: E402
import keybinds  # noqa: E402
import test_combat as tc  # noqa: E402


def test_run_starts_with_potions():
    _room, p = tc.make_world()
    assert p.potions == config.POTION_START <= config.POTION_MAX


def test_drinking_heals_and_uses_one():
    _room, p = tc.make_world()
    p.hp = 20
    assert p.drink_potion()
    assert p.hp == min(p.max_hp, 20 + config.POTION_HEAL)
    assert p.potions == config.POTION_START - 1
    assert not p.drink_potion()                       # 쿨다운 중
    tc.step(int(config.POTION_COOLDOWN * 60) + 2)
    assert p.drink_potion()


def test_no_drinking_at_full_hp_or_empty():
    _room, p = tc.make_world()
    assert not p.drink_potion()                       # 체력 가득
    p.hp, p.potions = 10, 0
    assert not p.drink_potion()


def test_shop_potion_refills_one_up_to_max():
    _room, p = tc.make_world()
    p.potions = config.POTION_MAX - 1
    assert items.can_take(p, 'heal')
    items.apply(p, 'heal')
    assert p.potions == config.POTION_MAX
    assert not items.can_take(p, 'heal')


def test_q_is_potion_and_tab_swaps_weapon():
    keybinds.reset()
    assert keybinds.action_for(sdl2.SDLK_q) == 'potion'
    assert keybinds.action_for(sdl2.SDLK_TAB) == 'swap'


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
