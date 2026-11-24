"""큰 방 (v8 계획 5-3, 2026-11-25): 두 화면짜리 전투방 여섯.
창 없이: python tests/test_big_rooms.py

- 여섯 방 모두 화면(32x18칸)의 두 배쯤이고, 방 검사(문·발판·스폰 규칙)를 통과하며 좌우 문만 있다.
- 구역마다 BIG_ROOMS_PER_ZONE개가 들어간다. 같은 모양이 한 구역에 두 번 나오지 않고,
  출발 방 바로 옆은 아니며, 하나는 갈림길 밖에 있거나 두 길에 하나씩 있다(어느 길을 골라도 만난다).
- 큰 방의 적 무리는 BIG_ROOM_PACKS(세 물결). 은신처·연습장에는 큰 방이 없다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import mapgen  # noqa: E402
import room_check  # noqa: E402
import stage as stage_mod  # noqa: E402
import test_stage as ts  # noqa: E402
from room import Room  # noqa: E402
from stage import BIG_ROOMS, Stage  # noqa: E402

SCREEN = 32 * 18
SEEDS = range(30)


def rows_of(name):
    path = os.path.join(HERE, '..', 'data', 'rooms', name + '.txt')
    return open(path, encoding='utf-8').read().split('\n')[:-1]


def make(name, seed):
    start, layout = mapgen.generate(name, seed)
    return Stage(None, layout=layout, start=start, seed=seed, name=name)


def test_six_big_rooms_are_two_screens_and_pass_the_room_check():
    assert len(BIG_ROOMS) == 6
    wide = tall = 0
    for name in BIG_ROOMS:
        rows = rows_of(name)
        cols, n = len(rows[0]), len(rows)
        assert cols * n >= SCREEN * 2, (name, cols, n)
        assert not room_check.analyze(rows), name
        assert stage_mod.template_exits(name) == {'L', 'R'}, name
        assert sum(r.count('E') for r in rows) >= config.BIG_ROOM_PACKS, name
        wide += cols >= 60
        tall += n >= 30
    assert wide >= 3 and tall >= 3                                       # 가로로 긴 방 셋, 위아래로 긴 방 셋


def test_each_zone_gets_its_big_rooms():
    for name, want in config.BIG_ROOMS_PER_ZONE.items():
        for seed in SEEDS:
            st = make(name, seed)
            big = [c for c in st.layout if st.is_big(c)]
            assert len(big) == want, (name, seed, big)
            assert len({st.template_of(c) for c in big}) == len(big)     # 같은 모양이 두 번 나오지 않는다
            sx, sy = st.start_coord
            for c in big:
                assert st.type_of(c) == 'combat' and st.links_of(c) <= {'L', 'R'}
                assert abs(c[0] - sx) + abs(c[1] - sy) > 1, (name, seed, c)
            lanes = {st.layout[c].get('lane') for c in big}
            assert None in lanes or lanes == {'short', 'long'}, (name, seed, lanes)   # 어느 길을 골라도 하나는 만난다


def test_every_shape_shows_up_somewhere():
    seen = set()
    for name in config.BIG_ROOMS_PER_ZONE:
        for seed in SEEDS:
            st = make(name, seed)
            seen |= {st.template_of(c) for c in st.layout if st.is_big(c)}
    assert seen == set(BIG_ROOMS), set(BIG_ROOMS) - seen


def test_a_big_room_has_more_packs_and_three_waves():
    found = 0
    for seed in (1, 2, 3):
        stage, _p = ts.make_stage(seed=seed)
        stage.on_mutation = lambda ids: None
        for c in sorted(stage.layout):
            if not stage.is_big(c):
                continue
            stage.enter_room(c)
            assert stage.room.width > config.SCREEN_W or stage.room.height > config.SCREEN_H
            assert stage.wave_packs == config.BIG_ROOM_PACKS, (seed, c, stage.wave_packs)
            assert stage.wave_total >= 2 and stage.room.locked
            for e in game_world.world[game_world.LAYER_ENEMY]:
                assert 0 < e.x < stage.room.width and 0 < e.y < stage.room.height
            found += 1
    assert found >= 3


def test_hideout_and_practice_have_no_big_rooms():
    for name in ('hideout', 'practice'):
        st = Stage(None, name=name)
        assert not any(st.is_big(c) for c in st.layout)


def test_big_room_templates_load():
    for name in BIG_ROOMS:
        room = Room.load(name, {'L', 'R'})
        assert len(room.enemy_spawns) >= config.BIG_ROOM_PACKS
        assert room.door_center('L') and room.door_center('R')


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
