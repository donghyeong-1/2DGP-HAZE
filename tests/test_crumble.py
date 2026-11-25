"""부서지는 발판 (v8 계획 5-5의 남은 부분, 2026-11-25): 슬럼의 얇은 발판 일부는 밟으면 잠시 뒤 무너졌다가 다시 생긴다.
창 없이: python tests/test_crumble.py

- 슬럼 전투방에서 얇은 발판(통과 발판) 한 토막이 부서지는 발판이 된다 (판의 시드로, 문 가까이는 아니다).
- 주인공이 올라서면 CRUMBLE_DELAY 뒤에 무너져 밟을 수 없고 그려지지 않는다. CRUMBLE_BACK 뒤에 다시 생긴다.
- 올라서지 않으면 무너지지 않는다. 공장·탑에는 없다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import config  # noqa: E402
import devices  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import mapgen  # noqa: E402
from player import Player  # noqa: E402
from stage import Stage  # noqa: E402

DT = 1 / 60


def find(name='stage1'):
    """부서지는 발판이 있는 방에 들어간 (stage, player, 발판). 없으면 (None, None, None)."""
    for seed in range(20):
        game_world.clear()
        effects.reset()
        p = Player(0, 0, None)
        game_world.add_object(p, game_world.LAYER_PLAYER)
        start, layout = mapgen.generate(name, seed)
        st = Stage(p, layout=layout, start=start, seed=seed, name=name)
        st.start()
        for c in sorted(st.layout):
            if st.type_of(c) != 'combat':
                continue
            st.enter_room(c)
            cr = next((d for d in st.devices if d.kind == 'crumble'), None)
            if cr is not None:
                for e in list(game_world.world[game_world.LAYER_ENEMY]):
                    game_world.remove_object(e)
                return st, p, cr
    return None, None, None


def stand_on(p, cr):
    col, row = cr.cells[len(cr.cells) // 2]
    p.x, p.y = devices.cell_pos(p.room, col, row)[0], p.room.height - row * config.TILE
    p.vx = p.vy = 0.0
    p.invuln_left = 5.0


def step(n):
    for _ in range(n):
        game_world.update(DT)


def test_a_slum_room_has_a_crumbling_platform_away_from_the_doors():
    st, p, cr = find()
    assert cr is not None and 2 <= len(cr.cells) <= 8
    for col, row in cr.cells:
        assert st.room.tile_at(col, row) == '='
        assert devices.DOOR_MARGIN <= col < st.room.cols - devices.DOOR_MARGIN
    assert len({row for _c, row in cr.cells}) == 1                      # 한 줄로 이어진 한 토막


def test_it_falls_after_being_stood_on_and_comes_back():
    st, p, cr = find()
    room = st.room
    stand_on(p, cr)
    step(3)
    assert p.on_ground and cr.state == 'shaking'
    step(int(config.CRUMBLE_DELAY * 60) + 3)
    assert cr.state == 'gone'
    assert all(room.tile_at(col, row) == '.' for col, row in cr.cells)  # 밟을 수 없다
    assert not p.on_ground or p.y < room.height - cr.cells[0][1] * config.TILE - 4   # 주인공이 떨어진다
    step(int(config.CRUMBLE_BACK * 60) + 3)
    assert cr.state == 'idle'
    assert all(room.tile_at(col, row) == '=' for col, row in cr.cells)  # 다시 생겼다


def test_it_stays_when_nobody_stands_on_it():
    st, p, cr = find()
    p.x, p.y = cr.cells[0][0] * config.TILE - 600, 2 * config.TILE
    step(int((config.CRUMBLE_DELAY + 0.5) * 60))
    assert cr.state == 'idle' and all(st.room.tile_at(col, row) == '=' for col, row in cr.cells)


def test_other_zones_have_none():
    for name in ('stage2', 'stage3'):
        assert find(name)[2] is None


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
