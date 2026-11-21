"""판마다 바뀌는 방 모양 테스트 (창 없이). 실행: python tests/test_room_variants.py

2026-11-21 퀄리티 계획 2-4 "방 구성 늘리기": 지도(격자)는 그대로 두고, 전투 방은 판마다 원래 모양 또는
새 방 모양(stage.COMBAT_VARIANTS) 중 하나가 된다 (판의 시드로 정한다, 로그라이트).
- 새 모양은 그 칸에 필요한 문(이웃과 이어진 쪽)을 모두 가진 것만 고른다.
- 시작·관문·보스·황금방·정비방·균열방은 바뀌지 않는다.
- 적 구성은 원래 방과 같다 (원래 방의 스폰 종류를 새 모양의 스폰 칸에 차례로 놓는다).
- 스테이지마다 판을 여러 번 하면 방 모양이 4종 이상 늘어난다.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import game_world  # noqa: E402
import stage as stage_mod  # noqa: E402
from player import Player  # noqa: E402
from room import Room  # noqa: E402
from stage import STAGE_ORDER, Stage, template_exits  # noqa: E402


def test_choice_is_fixed_per_seed_and_varies_between_seeds():
    a, b = Stage(None, seed=7), Stage(None, seed=7)
    assert all(a.template_of(c) == b.template_of(c) for c in a.layout)
    picks = {tuple(Stage(None, seed=s).template_of(c) for c in sorted(a.layout)) for s in range(20)}
    assert len(picks) > 5                                              # 시드가 바뀌면 방 모양이 바뀐다


def test_only_combat_rooms_vary_and_doors_always_fit():
    for name in STAGE_ORDER:
        for seed in range(25):
            st = Stage(None, seed=seed, name=name)
            for coord, info in st.layout.items():
                chosen = st.template_of(coord)
                if st.type_of(coord) != 'combat':
                    assert chosen == info['template'], (name, coord)
                assert st.links_of(coord) <= template_exits(chosen), (name, seed, coord, chosen)


def test_each_stage_gains_four_or_more_shapes():
    for name in STAGE_ORDER:
        base = {info['template'] for info in Stage(None, seed=0, name=name).layout.values()}
        seen = set()
        for seed in range(40):
            st = Stage(None, seed=seed, name=name)
            seen |= {st.template_of(c) for c in st.layout}
        assert len(seen - base) >= 4, (name, sorted(seen - base))


def kinds_in_world():
    return collections.Counter(e.kind for e in game_world.world[game_world.LAYER_ENEMY])


def test_variant_room_keeps_the_same_enemies():
    game_world.clear()
    found = 0
    for seed in range(40):
        game_world.clear()
        p = Player(0, 0, None)
        game_world.add_object(p, game_world.LAYER_PLAYER)
        st = Stage(p, seed=seed)
        for coord, info in st.layout.items():
            if st.type_of(coord) != 'combat' or st.template_of(coord) == info['template']:
                continue
            st.enter_room(coord, 'L')
            got = kinds_in_world()
            want = collections.Counter(st.original_kinds(info))
            assert got == want, (seed, coord, st.template_of(coord), got, want)
            found += 1
        if found >= 6:
            break
    assert found >= 6
    game_world.clear()


def test_new_shapes_are_real_rooms():
    for name in stage_mod.COMBAT_VARIANTS:
        room = Room.load(name)
        assert {'L', 'R'} <= set(room.exits), name
        assert len(room.enemy_spawns) >= 6, name                       # 원래 방의 적(최대 6)을 다 놓을 수 있다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
