"""벽 튕김 (v8 계획 4-1의 남은 부분, 2026-11-25): 떠 있는 적이 큰 공격을 맞으면 옆으로 날아가고, 벽에 부딪히면 튕기며 피해를 받는다.
창 없이: python tests/test_wall_bounce.py

- 띄워진 적(combo.launch)이 떠 있는 동안 큰 공격(3타·강화 등 big)을 맞으면 옆으로 멀리 날아간다 (보통 공격은 제자리에서 다시 뜬다).
- 날아가다 벽에 막히면 WALL_BOUNCE_DAMAGE를 받고 반대로 튕긴다. 어느 무기든 같다(예전에는 건틀릿 충돌 갈래 '벽꽝'에만 있었다).
- 한 번 뜬 동안 한 번만. 떠 있지 않은 적, 보통 공격을 맞은 적은 튕기지 않는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import combo  # noqa: E402
import config  # noqa: E402
import test_combat as tc  # noqa: E402

T = config.TILE
HIT = 5.0


def setup(launch=True):
    """왼쪽 벽에서 두 칸쯤 떨어진 적과, 그 오른쪽의 주인공: (주인공, 적, 처음 체력). 낮게 뜬 적은 곧 떨어지므로 벽 가까이에 둔다."""
    room, p = tc.make_world(player_x=T + 420.0)
    e = tc.freeze(tc.add_enemy('slum', T + 130, room, p))
    e.hp = e.max_hp = 10 ** 5
    tc.step(3)
    if launch:
        combo.launch(e, config.JUGGLE_RISE)
        tc.step(4)
    return p, e, e.hp


def hit(p, e, big):
    p.weapon._hit(e, HIT, 0.0, config.ZONE_FX['NORMAL'], big=big, extra=False)


def test_a_big_hit_blows_an_airborne_enemy_away_and_a_plain_hit_does_not():
    p, e, _hp = setup()
    x0 = e.x
    hit(p, e, big=False)
    tc.step(20)
    plain = x0 - e.x
    p, e, _hp = setup()
    x0 = e.x
    hit(p, e, big=True)
    tc.step(8)
    assert x0 - e.x > max(60, plain * 2), (x0 - e.x, plain)        # 왼쪽으로 멀리 날아간다


def test_it_bounces_off_the_wall_once_and_takes_damage():
    p, e, hp = setup()
    hit(p, e, big=True)
    tc.step(30)
    assert e.hp == hp - HIT - config.WALL_BOUNCE_DAMAGE, hp - e.hp
    assert e.x > T + e.hb_w / 2 + 15                                # 벽에서 튕겨 나왔다
    if not e.on_ground:                                             # 같은 뜬 동안 다시 날려도 두 번은 튕기지 않는다
        hit(p, e, big=True)
        tc.step(30)
        assert e.hp == hp - 2 * HIT - config.WALL_BOUNCE_DAMAGE


def test_it_can_bounce_again_after_landing_and_a_new_launch():
    p, e, hp = setup()
    hit(p, e, big=True)
    for _ in range(300):
        tc.step(1)
        if e.on_ground and not e.launched:
            break
    assert not e.launched
    e.x = T + 130
    combo.launch(e, config.JUGGLE_RISE)
    tc.step(4)
    hit(p, e, big=True)
    tc.step(30)
    assert e.hp == hp - 2 * HIT - 2 * config.WALL_BOUNCE_DAMAGE, hp - e.hp


def test_grounded_or_plainly_hit_enemies_do_not_bounce():
    p, e, hp = setup(launch=False)                                  # 땅에 선 적을 크게 쳤다
    e.x = T + 60
    hit(p, e, big=True)
    tc.step(30)
    assert e.hp == hp - HIT
    p, e, hp = setup()                                              # 떠 있지만 보통 공격
    e.x = T + 60
    hit(p, e, big=False)
    tc.step(30)
    assert e.hp == hp - HIT


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
