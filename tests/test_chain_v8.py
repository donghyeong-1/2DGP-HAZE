"""사슬 v8 (2026-11-25 사용자 요청): 기본은 공격, 당기기는 증강으로.
창 없이: python tests/test_chain_v8.py

- 사슬의 기본 공격은 맞은 적을 **끌어오지 않는다**. 사슬을 날려 멀리 있는 적을 친다(끌던 때보다 세다).
- '모으기' 갈래의 증강을 하나라도 가지면 사슬이 맞은 적을 끌어온다 (예전의 기본 동작).
- E 강화 일격은 증강이 없어도 끌어온다 (관통해 모두 끌어와 기절: 예전 그대로).
- 새 증강 '벽 걸기'(모으기 갈래): 아무도 걸리지 않은 사슬이 벽에 닿으면 그 벽으로 내가 날아간다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import mutations  # noqa: E402
import test_combat as tc  # noqa: E402


def setup(gaps, gauge=35, cards=()):
    room, p = tc.make_world()
    p.give_weapon('chain')
    for c in cards:
        mutations.give(p, c)
    tc.set_gauge(p, gauge)
    foes = []
    for gap in gaps:
        e = tc.freeze(tc.add_enemy('slum', p.x + gap, room, p))
        e.hp = e.max_hp = 1000
        foes.append(e)
    tc.step(5)
    p.mouse_x, p.mouse_y = p.x + 600, (foes[0].center[1] if foes else p.center[1])
    return room, p, foes


def fire(p, frames=120):
    p.weapon.cooldown = 0.0
    assert p.request_attack()
    tc.step(frames)


def test_the_base_chain_strikes_without_pulling():
    room, p, (e,) = setup([300])
    x0 = e.x
    fire(p)
    assert e.hp < e.max_hp
    assert abs(e.x - p.x) > 220, (e.x, p.x)                              # 끌려오지 않았다 (밀리는 것은 괜찮다)
    assert e.x >= x0 - 5


def test_a_gather_augment_turns_the_pull_back_on():
    room, p, (e,) = setup([300], cards=('gather_stun',))
    fire(p)
    assert abs(e.x - p.x) < 180, (e.x, p.x)                              # 주인공 앞까지 끌려온다


def test_the_base_strike_hits_harder_than_the_old_pulling_hit():
    room, p, (e,) = setup([300])
    fire(p)
    plain = e.max_hp - e.hp
    room, p, (e,) = setup([300], cards=('gather_stun',))
    fire(p)
    pulled = e.max_hp - e.hp
    assert plain >= pulled * config.CHAIN_LASH_MULT - 1e-6 and config.CHAIN_LASH_MULT > 1.0


def test_the_enhanced_chain_still_pulls_without_any_augment():
    room, p, (e,) = setup([300], gauge=60)
    assert p.request_enhance()
    fire(p)
    assert abs(e.x - p.x) < 180


def test_wall_hook_flies_me_to_the_wall_only_with_the_augment():
    room, p, _ = setup([])
    x0 = p.x
    fire(p, frames=90)
    assert abs(p.x - x0) < 40                                            # 증강이 없으면 제자리
    room, p, _ = setup([], cards=('gather_wall',))
    x0 = p.x
    p.mouse_x, p.mouse_y = p.x + 600, p.center[1] + 4
    reach = p.weapon.grip()[1]
    wall = None                                                          # 사거리 안에 벽이 있는 쪽을 찾는다
    for side in (1, -1):
        for d in range(60, int(reach), 20):
            if room.tile_at_world(p.x + side * d, p.center[1] + 4) == '#':
                wall = (side, d)
                break
        if wall:
            break
    if wall is None:                                                     # 이 방에서는 좌우 벽이 사거리 밖이다: 위로 쏜다
        p.mouse_x, p.mouse_y = p.x, p.center[1] + 600
        y0 = p.y
        fire(p, frames=40)
        assert p.y > y0 + 60 or mutations.has(p, 'gather_wall')
        return
    p.mouse_x = p.x + wall[0] * 600
    fire(p, frames=90)
    assert abs(p.x - x0) > wall[1] - 110, (p.x, x0, wall)                # 벽 앞까지 날아갔다


def test_the_gather_family_has_the_wall_hook_card():
    m = mutations.MUTATIONS['gather_wall']
    assert m['family'] == 'chain_gather' and '벽' in m['desc'] and m['desc'].endswith('니다')


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
