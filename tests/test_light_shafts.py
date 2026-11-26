"""빛줄기 테스트 (창 없이). 실행: python tests/test_light_shafts.py

O3 (2026-11-26, docs/opus/TASKS.md):
- 등 장식(DECOR_LAMP) 아래로 바닥까지 내려오는 옅은 빛 원뿔 하나씩.
- 방마다 천장에서 기운 빛줄기 0~2개(보스방 0~1개). 문·스폰 근처(room.near_marker)는 피한다.
- 자리는 방 이름으로 정한 난수: 같은 방이면 늘 같은 자리.
- 색은 구역 테마의 빛 색(슬럼 차가운 청백, 용광로 주황, 탑 청록, 은신처 따뜻한 색).
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import config  # noqa: E402
import light_shafts as ls  # noqa: E402
import room as room_mod  # noqa: E402
from room import Room  # noqa: E402

NAMES = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, 'data', 'rooms', '*.txt')))


def rooms(theme='cell'):
    return [Room.load(n, ('L', 'R'), theme=theme) for n in NAMES]


def test_same_room_name_always_gives_the_same_shafts():
    for name in NAMES:
        a = ls.plan(Room.load(name, ('L', 'R')))
        b = ls.plan(Room.load(name, ('L', 'R')))
        assert a == b, name
    assert len({tuple(ls.plan(r)) for r in rooms()}) > 3                # 방마다 다르다


def test_one_cone_under_every_lamp():
    found = 0
    for r in rooms():
        lamps = [(c, row) for kind, c, row in r.decor if kind == room_mod.DECOR_LAMP]
        cones = [s for s in ls.plan(r) if s[0] == 'cone']
        assert len(cones) == len(lamps), r.name
        for (kind, x, y, flip, phase), (c, row) in zip(cones, lamps):
            assert x == c * config.TILE + config.TILE // 2 and y <= r.tile_top(row), r.name
        found += len(lamps)
    assert found > 0


def test_ceiling_shafts_count_and_avoid_doors_and_spawns():
    seen = set()
    for r in rooms():
        slants = [s for s in ls.plan(r) if s[0] in ('slant', 'straight')]
        limit = 1 if ls.is_boss_room(r) else 2
        assert len(slants) <= limit, (r.name, len(slants))
        seen.add(len(slants))
        for kind, x, y, flip, phase in slants:
            col, row = r.col_of(x), r.row_of(y - 1)
            assert (col, row) not in r.near_marker, (r.name, col, row)
            assert r.rows[row][col] == room_mod.EMPTY and r.rows[row - 1][col] == room_mod.SOLID, (r.name, col, row)   # 천장 바로 아래
            for k in range(ls.CLEAR_ROWS):                               # 빛줄기가 내려가는 칸도 문·스폰 근처가 아니다
                assert (col, row + k) not in r.near_marker, (r.name, col, row + k)
    assert seen >= {0, 1, 2} - {0} or len(seen) >= 2                     # 개수가 방마다 달라진다


def test_boss_room_has_at_most_one():
    r = Room.load('boss_arena', ('L',), theme='boss')
    assert ls.is_boss_room(r)
    assert len([s for s in ls.plan(r) if s[0] != 'cone']) <= 1


def test_colors_follow_the_zone_theme():
    cold, hot, teal, warm = (ls.color_for(Room.load(NAMES[0], ('L',), theme=t)) for t in ('cell', 'foundry', 'haze', 'hideout'))
    assert cold[2] > cold[0]                                              # 슬럼: 차가운 청백 (파랑이 가장 세다)
    assert hot[0] > hot[1] > hot[2]                                       # 용광로: 주황
    assert teal[1] > teal[0] and teal[2] > teal[0]                        # 탑: 청록
    assert warm[0] > warm[2]                                              # 은신처: 따뜻한 색
    assert len({cold, hot, teal, warm}) == 4


def test_shaft_images_exist_in_the_light_layer():
    for kind in ls.KINDS:
        path = os.path.join(ROOT, 'assets', ls.KINDS[kind]['image'])
        assert os.path.exists(path), path
        assert ls.KINDS[kind]['image'].startswith('light/')                # 빛 층(반투명 예외)에만 둔다


def test_strengths_are_faint_and_breathe_slowly():
    assert 0.1 <= ls.BACK_ALPHA <= 0.25 and ls.FRONT_ALPHA <= 0.08
    assert 4.0 <= ls.BREATH_PERIOD <= 6.0
    ks = [ls.breath(t / 10, 0.0) for t in range(60)]
    assert 0.6 <= min(ks) < max(ks) <= 1.0


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
