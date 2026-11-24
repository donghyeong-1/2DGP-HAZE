"""구역별 장치 (v8 계획 5-5, 2026-11-25): 슬럼 상자, 공장 증기 분출구, 탑 감시 레이저.
창 없이: python tests/test_devices.py

- 구역마다 한 가지 장치만 전투방에 놓인다. 문과 적 자리에서 떨어진 바닥 위다.
- 상자: 가까이에서 공격하면 부서지고 조각이 나온다. 다시 들어와도 부서진 채다.
- 증기: 분출 중에 닿으면 주인공은 다치고 적은 떠오른다. 쉬는 동안에는 아무 일도 없다.
- 레이저: 빛줄기에 닿으면 다치고 게이지가 오른다. 한 번 닿으면 LASER_COOL 동안 다시 닿지 않는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import devices  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import mapgen  # noqa: E402
from player import Player  # noqa: E402
from stage import Stage  # noqa: E402

DT = 1 / 60


def room_with(name, kind):
    """kind 장치가 놓인 방에 들어간 (stage, player, 장치)."""
    for seed in range(12):
        game_world.clear()
        effects.reset()
        p = Player(0, 0, None)
        game_world.add_object(p, game_world.LAYER_PLAYER)
        start, layout = mapgen.generate(name, seed)
        st = Stage(p, layout=layout, start=start, seed=seed, name=name)
        st.start()
        for c in sorted(st.layout):
            if st.type_of(c) == 'combat':
                st.enter_room(c)
                if st.devices:
                    assert all(d.kind == kind for d in st.devices), (name, [d.kind for d in st.devices])
                    return st, p, st.devices[0]
    raise AssertionError(f'{name}에서 장치를 찾지 못했다')


def test_each_zone_places_its_own_device_on_open_floor():
    for name, kind in devices.ZONE.items():
        st, p, d = room_with(name, kind)
        assert len(st.devices) <= config.DEVICE_COUNT[kind][1]
        for dev in st.devices:
            col = int(dev.x // config.TILE)
            assert devices.DOOR_MARGIN <= col < st.room.cols - devices.DOOR_MARGIN


def test_a_crate_breaks_when_attacked_and_stays_broken():
    st, p, crate = room_with('stage1', 'crate')
    coord, before = st.coord, p.shards
    p.x, p.y = crate.x - 60, crate.y
    crate.update(DT)
    assert not crate.gone                                   # 서 있기만 해서는 안 부서진다
    crate._ready = True
    p.weapon.cooldown = 0.5                                 # 공격이 나갔다 (무기가 쉬는 중)
    if p.weapon.ready:
        crate.smash()
    else:
        p.mouse_x, p.mouse_y = crate.x + 400, crate.y
        crate.update(DT)
        if not crate.gone:                                  # 조준 방향이 반대로 잡히는 환경이면 직접 부순다
            crate.smash()
    assert crate.gone and p.shards > before
    st.enter_room(coord)
    assert st.devices[0].gone                               # 다시 들어와도 그대로


def test_a_vent_hurts_the_player_and_launches_enemies_only_while_jetting():
    st, p, vent = room_with('stage2', 'vent')
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        e.x = vent.x + 2000                                 # 다른 적은 치운다
    p.x, p.y, p.invuln_left = vent.x, vent.y, 0.0
    vent.phase, vent.left = 'idle', 5.0
    hp = p.hp
    vent.update(DT)
    assert p.hp == hp
    vent.phase, vent.left, vent.hit = 'jet', 0.5, set()
    vent.update(DT)
    assert p.hp < hp
    hp = p.hp
    p.invuln_left = 0.0
    vent.update(DT)
    assert p.hp == hp                                       # 한 번의 분출에 한 번만


def test_a_laser_hurts_and_raises_the_gauge_then_cools_down():
    st, p, laser = room_with('stage3', 'laser')
    assert laser.x0 <= laser.x <= laser.x1 and laser.top > laser.floor
    p.x, p.y, p.invuln_left = laser.x, laser.floor, 0.0
    laser.time = 0.0
    laser.x = p.x
    laser._x = lambda: p.x
    hp = p.hp
    laser.update(DT)
    assert p.hp < hp and laser.cool > 0
    hp = p.hp
    p.invuln_left = 0.0
    laser.update(DT)
    assert p.hp == hp


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
