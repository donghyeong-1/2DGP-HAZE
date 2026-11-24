"""갈림길 (v8 계획 5-1, 2026-11-25): 구역 가운데에서 길이 둘로 갈라졌다가 다시 합쳐진다.
창 없이: python tests/test_fork.py

- 구역 1·2: 본 경로의 갈림 방에서 짧은 길(전투방 1)과 긴 길(전투방 3)로 갈라지고, 합류 방에서 다시 만난다.
- 한쪽 길에 들어서면 다른 길은 닫힌다: 문이 사라지고, 황금방을 여는 조건(전투방 모두 클리어)에서도 빠진다.
- 어느 길을 골라도 끝 방·황금방·정비방에 갈 수 있다. 균열방은 긴 길 끝에 붙어 있다(긴 길의 보상).
- 갈림 방의 두 문에는 서로 다른 보상이 보인다 (보상을 보고 고른다).
- 구역 3은 방이 적어 갈라지지 않는다.
"""
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import mapgen  # noqa: E402
from stage import STEP, Stage  # noqa: E402

SEEDS = range(30)


def stage(name, seed):
    start, layout = mapgen.generate(name, seed)
    return Stage(None, layout=layout, start=start, seed=seed, name=name)


def reach(st, skip=()):
    seen, q = {st.start_coord}, deque([st.start_coord])
    while q:
        c = q.popleft()
        for d in st.links_of(c):
            n = (c[0] + STEP[d][0], c[1] + STEP[d][1])
            if n in st.layout and n not in seen and n not in skip:
                seen.add(n)
                q.append(n)
    return seen


def lanes(st):
    short = {c for c, i in st.layout.items() if i.get('lane') == 'short'}
    long_ = {c for c, i in st.layout.items() if i.get('lane') == 'long'}
    return short, long_


def test_zones_one_and_two_fork_into_a_short_and_a_long_lane():
    for name in ('stage1', 'stage2'):
        for seed in SEEDS:
            st = stage(name, seed)
            short, long_ = lanes(st)
            assert sum(1 for c in short if st.type_of(c) == 'combat') == 1, (name, seed)
            assert sum(1 for c in long_ if st.type_of(c) == 'combat') == 3, (name, seed)
            end = next(c for c in st.layout if st.type_of(c) in ('boss', 'gate'))
            assert end in reach(st, skip=long_) and end in reach(st, skip=short), (name, seed)   # 어느 길로도 끝까지


def test_gold_and_shop_do_not_depend_on_the_lane_and_the_rift_ends_the_long_lane():
    for name in ('stage1', 'stage2'):
        for seed in SEEDS:
            st = stage(name, seed)
            short, long_ = lanes(st)
            for kind in ('gold', 'shop'):
                c = next(c for c in st.layout if st.type_of(c) == kind)
                assert c in reach(st, skip=long_) and c in reach(st, skip=short), (name, seed, kind)
            rift = next(c for c in st.layout if st.type_of(c) == 'rift')
            assert rift in long_ and rift in reach(st, skip=short), (name, seed)


def test_entering_one_lane_seals_the_other():
    for lane in ('short', 'long'):
        st = stage('stage1', 3)
        short, long_ = lanes(st)
        mine, other = (short, long_) if lane == 'short' else (long_, short)
        fork = next(c for c, i in st.layout.items() if i.get('fork'))
        merge = next(c for c, i in st.layout.items() if i.get('merge'))
        before = st.gold_rooms_left()
        first = next(c for c in mine if c in {(fork[0] + STEP[d][0], fork[1] + STEP[d][1]) for d in st.links_of(fork)})
        st.choose_lane(first)
        assert st.sealed == other
        for hub in (fork, merge):                                        # 갈림 방·합류 방에서 닫힌 길로 가는 문이 사라진다
            for d in st.links_of(hub):
                assert (hub[0] + STEP[d][0], hub[1] + STEP[d][1]) not in other
        closed = sum(1 for c in other if st.type_of(c) == 'combat')
        assert st.gold_rooms_left() == before - closed                   # 닫힌 길의 방은 황금방 조건에서 빠진다
        assert not any(c in other for c, *_ in st.minimap_cells())


def test_the_two_doors_of_the_fork_show_different_rewards():
    for seed in SEEDS:
        st = stage('stage1', seed)
        fork = next(c for c, i in st.layout.items() if i.get('fork'))
        firsts = [(fork[0] + STEP[d][0], fork[1] + STEP[d][1]) for d in st.links_of(fork)]
        firsts = [c for c in firsts if st.layout[c].get('lane')]
        assert len(firsts) == 2, seed
        assert st.reward_of(firsts[0]) != st.reward_of(firsts[1]), (seed, st.reward_of(firsts[0]))


def test_zone_three_has_no_fork():
    for seed in SEEDS:
        st = stage('stage3', seed)
        assert not any(i.get('lane') or i.get('fork') for i in st.layout.values())


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
