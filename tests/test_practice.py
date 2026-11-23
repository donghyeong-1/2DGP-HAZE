"""연습장 (v7, 2026-11-24, docs/plan_v7.md 5-F). 창 없이: python tests/test_practice.py

- 은신처에 '연습장' 표지판(NPC 'practice')이 있다.
- 연습장 구역('practice')에 들어가면 쓰러지지 않는 허수아비 둘이 선다 (맞아도 체력이 다시 찬다, 공격하지 않는다).
- 허수아비가 받은 피해로 초당 피해(최근 5초)를 잰다.
- 연습 메뉴 함수: 적 불러내기, 증강 넣기·빼기(대시 칸 같은 걸린 효과도 되돌린다), 게이지 정하기, 무기 바꾸기, 정리.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import game_world  # noqa: E402
import mutations as mu  # noqa: E402
import practice  # noqa: E402
import stage as stage_mod  # noqa: E402
import test_stage as ts  # noqa: E402


def _practice():
    st, p = ts.make_stage(name='hideout')
    assert any(n.kind == 'practice' for n in st.npcs)
    st = stage_mod.jump_to(st, 'practice')
    p.no_death = True                                     # play_mode._go_stage가 켠다
    return st, p


def test_practice_room_has_immortal_dummies():
    st, p = _practice()
    dummies = practice.dummies()
    assert len(dummies) == 2
    assert not st.room.locked                             # 연습장은 잠그지 않는다 ('남은 적' 칩이 안 뜬다)
    assert p.x < dummies[0].x                             # 주인공은 허수아비 왼쪽(P 칸)에서 시작
    d = dummies[0]
    for _ in range(20):
        d.take_damage(999, from_x=p.x)
    assert d.alive and d.hp > 0
    assert practice.dps() > 0
    p.invuln_left = 0                                     # 방 들어설 때의 짧은 무적을 지운다
    p.take_hit(9999)
    assert p.hp == 1 and p.state != 'DEAD'                # 연습장에서는 쓰러지지 않는다


def test_menu_spawns_enemies_and_toggles_augments():
    st, p = _practice()
    before = len(game_world.world[game_world.LAYER_ENEMY])
    practice.spawn_enemy(st, 'hound')
    assert len(game_world.world[game_world.LAYER_ENEMY]) == before + 1
    slots = p.dash_max
    practice.toggle_augment(p, 'dash_extra')
    assert mu.has(p, 'dash_extra') and p.dash_max == slots + 1
    practice.toggle_augment(p, 'dash_extra')
    assert not mu.has(p, 'dash_extra') and p.dash_max == slots
    practice.toggle_augment(p, 'combo_speed')
    practice.clear_augments(p)
    assert not mu.owned(p)
    practice.set_gauge(p, 70)
    assert p.gauge.value == 70
    practice.reset(st)
    assert len(practice.dummies()) == 2 and all(not getattr(e, 'dummy', False) is False for e in practice.dummies())


def test_practice_mode_rows_drive_the_practice_functions():
    import practice_mode as pm
    st, p = _practice()
    pm.stage, pm.player = st, p
    before = len(game_world.world[game_world.LAYER_ENEMY])
    pm.change('enemy', 1)
    pm.run('enemy')
    assert len(game_world.world[game_world.LAYER_ENEMY]) == before + 1
    g = p.gauge.value
    pm.change('gauge', 1)
    assert p.gauge.value == min(g + pm.GAUGE_STEP, p.gauge.cap - 1)
    mid = pm.augment_ids()[pm.index['augment']]
    pm.run('augment')
    assert mu.has(p, mid) and mu.MUTATIONS[mid]['name'] in pm.value_label('augment')
    pm.run('clear')
    assert not mu.owned(p)
    assert all(mu.MUTATIONS[m].get('ready', True) for m in pm.augment_ids())
    for item in pm.ROWS:
        pm.value_label(item)                                   # 모든 줄의 값 글자가 오류 없이 나온다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
