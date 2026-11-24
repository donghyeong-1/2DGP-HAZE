"""공장 새 적 테스트: 용접 드론·자폭 수레 (창 없이). 실행: python tests/test_factory_enemies.py

2026-11-22 v5 계획 1 (docs/plan_v5.md, "구역마다 같은 적만 나온다"는 사용자 의견):
- 용접 드론: 중력 없이 날아 플레이어 머리 위로 온다. 예고(토치가 아래로, 렌즈가 밝아짐) 뒤 아래로 곧은 불꽃을 뿜는다.
  불꽃은 바닥(벽 칸)에서 멈춘다. 옆으로 비키면 맞지 않는다. 쓰러지면 잔해가 바닥으로 떨어진다.
  -> 마우스 조준을 위로 쓰게 만든다.
- 자폭 수레: 굴러와 가까이서 예고(경고등·통이 부풂) 뒤 터진다(반경 안의 플레이어 피해). 맞으면 맞은 쪽 반대로 되밀려
  굴러가고, 다른 적이나 벽에 닿으면 그 자리에서 터져 적에게 큰 피해(받아치기).
- 공장(스테이지 2)에만 나온다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import enemy_kinds as ek  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402

FLOOR_Y = tc.FLOOR_Y


def run(frames):
    import effects
    for _ in range(frames):
        effects.hit_stop_left = 0.0
        game_world.update(1 / 60)


def add(kind, x, y, room, p):
    e = ek.make(kind, x, y, room, p)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return e


def enemies(cls):
    return [o for o in game_world.world[game_world.LAYER_ENEMY] if isinstance(o, cls)]


# ----- 드론 -----
def test_make_returns_plain_enemy_for_old_kinds():
    room, p = tc.make_world()
    from enemy import Enemy
    e = ek.make('slum', p.x + 300, FLOOR_Y, room, p)
    assert type(e) is Enemy
    assert isinstance(ek.make('drone', p.x + 300, FLOOR_Y + 300, room, p), ek.Drone)
    assert isinstance(ek.make('cart', p.x + 300, FLOOR_Y, room, p), ek.Cart)


def test_drone_flies_without_gravity():
    room, p = tc.make_world(player_x=200.0)
    d = add('drone', 1400.0, FLOOR_Y + 320, room, p)
    d.cooldown = 99.0
    run(60)
    assert d.y > FLOOR_Y + 200                                    # 떨어지지 않는다


def test_drone_goes_above_player():
    room, p = tc.make_world(player_x=600.0)
    d = add('drone', 1000.0, FLOOR_Y + 300, room, p)
    d.cooldown = 99.0
    run(240)
    assert abs(d.x - p.x) < 90                                    # 머리 위로 와서
    assert d.y - p.y > 150                                        # 떠 있다


def test_drone_torch_hits_player_below_and_stops_at_floor():
    room, p = tc.make_world(player_x=600.0)
    d = add('drone', p.x, p.y + 260, room, p)
    d.state = 'CHASE'
    d.cooldown = 0.0
    hp = p.hp
    run(int((d.stats['windup'] + 0.3) * 60))
    assert d.move == 'torch'
    assert p.hp < hp                                              # 아래로 뿜은 불꽃에 맞는다
    x0, y0, x1, y1 = d.flame_box()
    assert y0 >= FLOOR_Y - 1                                      # 바닥을 뚫지 않는다


def test_drone_torch_misses_if_player_steps_aside():
    room, p = tc.make_world(player_x=600.0)
    d = add('drone', p.x, p.y + 260, room, p)
    d.state = 'CHASE'
    d.cooldown = 0.0
    run(5)                                                        # 예고가 시작됐다
    assert d.state == 'ATTACK'
    p.x += 220                                                    # 옆으로 비킨다
    hp = p.hp
    run(int((d.stats['windup'] + 0.5) * 60))
    assert p.hp == hp


def test_drone_wreck_falls_to_floor():
    room, p = tc.make_world(player_x=300.0)
    d = add('drone', 900.0, FLOOR_Y + 300, room, p)
    d.take_damage(9999, from_x=p.x)
    wrecks = [o for o in game_world.world[game_world.LAYER_EFFECT] if isinstance(o, ek.FallingWreck)]
    assert wrecks
    run(90)
    assert abs(wrecks[0].y - FLOOR_Y) < 2                         # 바닥에 떨어져 누웠다


# ----- 수레 -----
def test_cart_rolls_in_and_explodes_near_player():
    room, p = tc.make_world(player_x=400.0)
    c = add('cart', p.x + 700, FLOOR_Y, room, p)
    hp = p.hp
    run(int(5.0 * 60))
    assert not c.alive and not enemies(ek.Cart)                   # 터져서 사라졌다
    assert p.hp < hp


def test_hit_cart_rolls_back_and_blows_up_enemies():
    room, p = tc.make_world(player_x=400.0)
    c = add('cart', p.x + 150, FLOOR_Y, room, p)
    c.cooldown = 99.0
    other = tc.add_enemy('guard', p.x + 700, room, p)
    tc.freeze(other)
    hp0, ghp = p.hp, other.hp
    c.take_damage(10, from_x=p.x)                                 # 받아친다
    assert c.returned
    run(90)
    assert not c.alive                                            # 굴러가 적에 부딪쳐 터졌다
    assert other.hp <= ghp - config.ENEMY_STATS['cart']['blast_enemy'] + 1
    assert p.hp == hp0                                            # 멀리 있던 플레이어는 멀쩡하다


def test_killed_cart_still_blows_after_delay():
    room, p = tc.make_world(player_x=400.0)
    c = add('cart', p.x + 90, FLOOR_Y, room, p)
    c.cooldown = 99.0
    hp = p.hp
    c.take_damage(9999, from_x=p.x)
    run(int(ek.CART_DEATH_DELAY * 60) + 3)
    assert p.hp < hp                                              # 가까이서 부수면 휘말린다


# ----- 배치 -----
def test_factory_enemies_only_in_foundry():
    import stage as stage_mod

    def kinds_of(name):
        room, p = tc.make_world()
        st = stage_mod.Stage(p, seed=1, name=name)
        out = set()
        for c, info in st.layout.items():
            if info.get('type') == 'combat':
                out |= set(info.get('enemies', [])) | set(info.get('swap', {}).values())
        return out
    assert {'drone', 'cart'} <= kinds_of('stage2')
    assert not {'drone', 'cart'} & kinds_of('stage1')


def test_stage2_spawns_drone_through_factory():
    import stage as stage_mod
    found = set()
    for seed in range(1, 7):                     # 판마다 배치가 다르다: 몇 판에 걸쳐 본다
        room, p = tc.make_world()
        st = stage_mod.Stage(p, seed=seed, name='stage2')
        st.start()
        for c, info in st.layout.items():
            if info.get('type') == 'combat':
                st.enter_room(c, 'L')
                found |= {type(o).__name__ for o in game_world.world[game_world.LAYER_ENEMY]}
                found |= {type(o).__name__ for w in st.waves for o in w}     # v8 물결 전투: 아직 나오지 않은 물결의 적
    assert {'Drone', 'Cart'} <= found


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
