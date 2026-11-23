"""맵 절차 생성 (v7, 2026-11-24, docs/plan_v7.md 5-E). 창 없이: python tests/test_mapgen.py

매판 시드로 구역 배치를 새로 만든다. 여러 시드에서:
- 모든 방이 시작 방에서 문으로 이어진다 (도달 가능).
- 끝 방(관문·보스)은 하나, 본 경로 오른쪽 끝.
- 구역마다 특수방(황금·정비·균열)이 정해진 수만큼 있고 각각 문으로 이어진다.
- 전투방 수가 구역 규모와 같다. 같은 시드면 같은 배치.
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import mapgen  # noqa: E402
from stage import STEP, Stage  # noqa: E402

SEEDS = range(40)


def _reach(st):
    seen, q = {st.start_coord}, deque([st.start_coord])
    while q:
        c = q.popleft()
        for d in st.links_of(c):
            n = (c[0] + STEP[d][0], c[1] + STEP[d][1])
            if n in st.layout and n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def _stage(name, seed):
    start, layout = mapgen.generate(name, seed)
    return Stage(None, layout=layout, start=start, seed=seed, name=name)


def test_every_room_is_reachable_and_one_end():
    for name in ('stage1', 'stage2', 'stage3'):
        for seed in SEEDS:
            st = _stage(name, seed)
            assert _reach(st) == set(st.layout), (name, seed)
            ends = [c for c in st.layout if st.type_of(c) in ('boss', 'gate')]
            assert len(ends) == 1, (name, seed)


def test_special_rooms_and_combat_count():
    for name, spec in mapgen.SPECS.items():
        for seed in SEEDS:
            st = _stage(name, seed)
            types = [st.type_of(c) for c in st.layout]
            assert types.count('combat') == spec['combat'], (name, seed)
            for kind in spec['specials']:
                assert types.count(kind) == 1, (name, seed, kind)
            assert types.count('start') == 1


def test_combat_rooms_have_enemies_from_the_zone_pool():
    for name, spec in mapgen.SPECS.items():
        st = _stage(name, 3)
        for c, info in st.layout.items():
            if info['type'] == 'combat':
                kinds = Stage.original_kinds(None, info)
                assert kinds and all(k in spec['pool'] or k in ('slum', 'thrower') for k in kinds), (name, c, kinds)


def test_same_seed_same_layout_and_seeds_differ():
    a = mapgen.generate('stage1', 7)
    b = mapgen.generate('stage1', 7)
    assert a == b
    shapes = {tuple(sorted(mapgen.generate('stage1', s)[1])) for s in range(10)}
    assert len(shapes) >= 4                                  # 판마다 배치가 다르다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
