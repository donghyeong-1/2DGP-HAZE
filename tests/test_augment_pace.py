"""증강을 얻는 속도 (2026-11-25): 한 판에 증강 보상이 평균 5.5번뿐이라 합성 카드(진화 둘)가 거의 열리지 않았다
(tools/augment_sim.py: 집중해서 골라도 9%의 판). 큰 방과 구역 보스의 보상을 증강으로 고정한다.
창 없이: python tests/test_augment_pace.py

- 큰 방을 깨면 늘 증강을 고른다 (오래 싸운 방의 보상).
- 구역 1·2의 끝(문지기·크래셔)을 쓰러뜨리면 증강을 고른다. 마지막 구역은 탈출이라 없다.
- 한 판에 증강 보상이 평균 8번 이상이다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import mapgen  # noqa: E402
from player import Player  # noqa: E402
from stage import END_TYPES, Stage  # noqa: E402

DT = 1 / 60


def make(name, seed, start=False):
    game_world.clear()
    effects.reset()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    first, layout = mapgen.generate(name, seed)
    st = Stage(p, layout=layout, start=first, seed=seed, name=name)
    if start:
        st.start()
    return st, p


def test_big_rooms_always_reward_an_augment():
    for name in config.BIG_ROOMS_PER_ZONE:
        for seed in range(30):
            st, _p = make(name, seed)
            for c in st.layout:
                if st.is_big(c):
                    assert st.reward_of(c) == 'mutation', (name, seed, c, st.reward_of(c))


def end_room(st):
    return next(c for c in st.layout if st.type_of(c) in END_TYPES)


def clear_end(name, seed=3):
    """끝 방에 들어가 보스(또는 관문의 적)를 모두 쓰러뜨리고 2초를 흘린다: 그동안 열린 카드 창 목록."""
    st, p = make(name, seed, start=True)
    opened = []
    st.on_mutation = opened.append
    st.enter_room(end_room(st), 'L')
    for _ in range(600):                                   # 등장씬·증원·2연전이 있어도 끝까지: 살아 있는 것을 계속 쓰러뜨린다
        for e in list(game_world.world[game_world.LAYER_ENEMY]):
            if e.alive:
                e.take_damage(10 ** 9)
        game_world.update(DT)
        st.update()
        if st.finished:
            break
    return st, opened


def test_zone_bosses_one_and_two_reward_an_augment_and_the_last_does_not():
    for name in ('stage1', 'stage2'):
        st, opened = clear_end(name)
        assert st.finished and len(opened) == 1, (name, st.finished, len(opened))
        assert len(opened[0]) == 3                          # 증강 셋 중 하나
    st, opened = clear_end('stage3')
    assert not opened                                       # 마지막 구역: 탈출


def test_the_boss_door_shows_the_augment_reward():
    st, _p = make('stage1', 3)
    assert st.reward_of(end_room(st)) == 'mutation'
    st3, _p = make('stage3', 3)
    assert st3.reward_of(end_room(st3)) is None


def test_a_run_gets_at_least_eight_augment_rewards_on_average():
    import augment_sim
    picks = [augment_sim.run(2000 + k, augment_sim.LOADOUTS[k % 6], 'focus', 3)[0] for k in range(40)]
    assert sum(picks) / len(picks) >= 8.0, sum(picks) / len(picks)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
