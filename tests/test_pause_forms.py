"""일시정지 화면 '이번 판' 카드의 무기 형태 목록 (v8 2일 차에 남겨 둔 것, 2026-11-25).
창 없이: python tests/test_pause_forms.py

- 얻은 형태는 무기 이름과 함께 맨 위에 보인다. 들고 있지 않은 무기의 형태는 흐리게(미장착).
- 형태만 얻었어도 '아직 아이템이 없습니다'를 띄우지 않는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import forms  # noqa: E402
import pause_mode  # noqa: E402
import test_combat as tc  # noqa: E402


def test_no_forms_no_rows():
    _room, p = tc.make_world()
    assert pause_mode.form_rows(p) == []
    assert pause_mode.form_rows(None) == []


def test_owned_forms_are_listed_with_weapon_names():
    _room, p = tc.make_world()
    held = p.weapon.weapon_id
    forms.give(p, held)
    forms.give(p, 'chain' if held != 'chain' else 'pipe')
    rows = pause_mode.form_rows(p)
    assert [r[0] for r in rows][0] == forms.FORMS[held]['name']
    by_name = {name: (weapon, on) for name, weapon, on in rows}
    assert by_name[forms.FORMS[held]['name']][1] is True
    other = 'chain' if held != 'chain' else 'pipe'
    assert by_name[forms.FORMS[other]['name']][1] is False      # 들고 있지 않은 무기
    assert all(weapon for _n, weapon, _on in rows)


def test_forms_alone_count_as_something_to_show():
    _room, p = tc.make_world()
    p.items = []
    assert not pause_mode.has_build(p)
    forms.give(p, p.weapon.weapon_id)
    assert pause_mode.has_build(p)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
