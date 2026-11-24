"""황금방 형태 (v8 남겨 둔 것, 2026-11-25). 창 없이: python tests/test_gold_forms.py

무기 형태(src/forms.py)는 구역의 첫 전투방 보상으로만 얻었다. 이제 황금방 진열대 하나가 형태가 될 수 있다.
- 들고 있는 무기 가운데 아직 형태가 없는 것이 있으면, 황금방 진열 셋 = 무기 하나 + 형태 하나 + 업그레이드 하나.
- 형태가 없는(모두 얻은) 판에는 지금처럼 무기 하나 + 업그레이드 둘.
- 형태 진열대를 고르면 그 무기의 형태를 얻는다(아이템 목록에는 들어가지 않는다). 이미 가진 형태는 고를 수 없다.
- 아이콘은 무기 아이콘에 형태 표시를 더한 그림(assets/ui/icon_f_<무기>.png, 48x48).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import forms  # noqa: E402
import game_world  # noqa: E402
import items  # noqa: E402
from player import Player  # noqa: E402


def new_player(first='pipe', second=None):
    game_world.clear()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    p.set_loadout(first, second)
    return p


def test_form_items_exist_for_every_weapon():
    for wid in forms.FORMS:
        info = items.ITEMS['f_' + wid]
        assert info['form'] == wid and forms.FORMS[wid]['name'] in info['name']
        assert items.icon_path('f_' + wid) == f'ui/icon_f_{wid}.png'


def test_gold_stock_has_a_form_for_a_held_weapon():
    p = new_player('pipe', 'chain')
    for seed in range(20):
        stock = items.roll_gold(random.Random(seed), 3, p)
        kinds = [('weapon' if 'weapon' in items.ITEMS[i] else 'form' if 'form' in items.ITEMS[i] else 'up') for i in stock]
        assert sorted(kinds) == ['form', 'up', 'weapon'], stock
        form = next(i for i in stock if 'form' in items.ITEMS[i])
        assert items.ITEMS[form]['form'] in ('pipe', 'chain')


def test_no_form_when_every_held_weapon_has_one():
    p = new_player('pipe', 'chain')
    forms.give(p, 'pipe')
    forms.give(p, 'chain')
    for seed in range(10):
        stock = items.roll_gold(random.Random(seed), 3, p)
        assert not any('form' in items.ITEMS[i] for i in stock)
        assert sum(1 for i in stock if i in items.UPGRADES) == 2


def test_taking_a_form_gives_it_and_not_an_item():
    p = new_player('pistol')
    assert items.can_take(p, 'f_pistol') and not items.can_take(p, 'f_chain')   # 들고 있지 않은 무기의 형태는 못 고른다
    items.apply(p, 'f_pistol')
    assert 'pistol' in p.forms and p.items == []
    assert not items.can_take(p, 'f_pistol')


def test_form_icons_follow_pixel_rules():
    from PIL import Image
    for wid in forms.FORMS:
        im = Image.open(os.path.join(HERE, '..', 'assets', 'ui', f'icon_f_{wid}.png')).convert('RGBA')
        assert im.size == (48, 48)
        alpha = im.getchannel('A').histogram()
        assert sum(alpha[1:255]) == 0


def test_gold_room_shows_and_gives_a_form():
    import test_stage as ts
    stage, p = ts.make_stage()
    ts.to_gold(stage, p)
    ped = next((d for d in stage.pedestals if 'form' in items.ITEMS[d.item_id]), None)
    assert ped is not None and items.ITEMS[ped.item_id]['form'] == 'pipe'          # 처음 판: 철파이프만 들었다
    p.x, p.y = ped.x, ped.y
    assert stage.interact() and 'pipe' in p.forms and all(d.gone for d in stage.pedestals)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
