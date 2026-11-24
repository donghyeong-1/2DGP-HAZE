"""타격감 v8 (계획 4절, 2026-11-25): 띄우기와 공중 연타, 방향 있는 카메라 킥, 조각나는 처치.
창 없이: python tests/test_feel_v8.py

- 띄우기: 띄워진 적은 떠 있는 동안 움직이지 못한다. 떠 있는 적을 맞히면 조금 다시 뜬다(한 번 뜬 동안 JUGGLE_MAX번까지).
  땅에 닿으면 먼지가 일고 다시 띄울 수 있다. 보스는 뜨지 않는다. 철파이프 3타(올려베기)는 적을 띄운다.
- 카메라 킥: 큰 타격은 공격 방향으로 화면이 한 번 밀렸다가 돌아온다 (흔들림 설정을 따른다).
- 조각나는 처치: 큰 공격으로 죽은 적은 쓰러지는 그림 대신 여러 조각으로 흩어진다. 보통 처치는 그대로.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import combo  # noqa: E402
import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def world(gauge=45):
    room, p = tc.make_world(player_x=400.0)
    tc.set_gauge(p, gauge)
    p.mouse_x, p.mouse_y = p.x + 600, p.center[1]
    return room, p


def enemy(room, p, dx, hp=10 ** 5):
    e = tc.freeze(tc.add_enemy('slum', p.x + dx, room, p))
    e.hp = e.max_hp = hp
    return e


def hit(p, e, damage=5.0, big=False):
    return p.weapon._hit(e, damage, 0.0, config.ZONE_FX['NORMAL'], big=big, extra=False)


def names(layer=None):
    return [type(o).__name__ for o in game_world.world[game_world.LAYER_EFFECT]]


def test_a_launched_enemy_leaves_the_ground_and_a_boss_does_not():
    room, p = world()
    e = enemy(room, p, 120)
    y0 = e.y
    assert combo.launch(e, config.SWAP_LAUNCH) and e.launched
    tc.run_frames(8)
    assert e.y > y0 + 20 and not e.on_ground
    boss = enemy(room, p, 300)
    boss.pullable = False
    assert not combo.launch(boss, config.SWAP_LAUNCH) and not getattr(boss, 'launched', False)


def test_hitting_an_airborne_enemy_pops_it_up_a_few_times_only():
    room, p = world()
    e = enemy(room, p, 120)
    combo.launch(e, config.SWAP_LAUNCH)
    tc.run_frames(14)
    for i in range(config.JUGGLE_MAX):
        e.vy = -200.0                                                    # 떨어지는 중
        hit(p, e)
        assert e.vy >= config.JUGGLE_POP - 1e-6, i                       # 맞으면 다시 뜬다
    e.vy = -200.0
    hit(p, e)
    assert e.vy < 0                                                      # 정해진 횟수를 넘으면 더 뜨지 않는다


def test_landing_raises_dust_and_lets_the_enemy_be_launched_again():
    room, p = world()
    e = enemy(room, p, 120)
    combo.launch(e, 300.0)
    landed = False
    for _ in range(120):
        tc.run_frames(1)
        if e.on_ground and not e.launched:
            landed = True
            break
    assert landed and e.air_hits == 0
    assert any(getattr(o, 'name', '') == 'dust-land' for o in game_world.world[game_world.LAYER_EFFECT])
    assert combo.launch(e, 300.0)


def test_the_pipe_third_hit_launches():
    room, p = world()
    e = enemy(room, p, 110)
    launched = False
    for _ in range(3):
        p.weapon.cooldown = 0.0
        assert p.request_attack()
        for _ in range(16):
            tc.run_frames(1)
            launched = launched or getattr(e, 'launched', False)
    assert launched


def test_a_big_hit_kicks_the_camera_toward_the_blow_and_it_settles():
    room, p = world()
    e = enemy(room, p, 120)
    effects.trauma = 0.0
    hit(p, e, big=False)
    effects.trauma = 0.0
    assert effects.kick_offset() == (0, 0)                               # 보통 타격은 밀지 않는다
    hit(p, e, big=True)
    effects.trauma = 0.0
    kx, ky = effects.kick_offset()
    assert kx > 0                                                        # 오른쪽의 적을 쳤다: 화면이 오른쪽으로 밀린다
    for _ in range(40):
        effects.tick_shake(1 / 60)
    assert effects.kick_offset() == (0, 0)                               # 곧 돌아온다


def test_a_big_kill_shatters_the_body_and_a_plain_kill_does_not():
    room, p = world()
    e = enemy(room, p, 120, hp=5)
    hit(p, e, damage=50.0, big=True)
    assert not e.alive
    assert 'Shatter' in names() and 'Corpse' not in names()
    room, p = world()
    e = enemy(room, p, 120, hp=5)
    hit(p, e, damage=50.0, big=False)
    assert not e.alive and 'Shatter' not in names()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
