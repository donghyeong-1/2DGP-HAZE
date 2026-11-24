"""헤이즈 사슬 테스트 (창 없이). 실행: python tests/test_chain.py

기획서 무기 4번: 중거리 제어형. 맞은 적을 끌어당기고, 끌려온 적 1마리당 게이지 +2%.
노멀 1마리 / 각성 사거리 +30%, 최대 2마리 / 위험 끌려온 적 1초 기절, 끌려온 적끼리 충돌 피해.
E 강화: 끌어당긴 적 1초 기절, 사슬이 여러 적을 관통. 보스는 끌려오지 않는다(피해만).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402  (방·플레이어·적을 세우는 도우미를 함께 쓴다)


def setup(gauge, gaps):
    """플레이어 오른쪽 gaps 거리마다 움직이지 않는 슬럼을 세우고 사슬을 든다. 적은 체력을 크게 해 죽지 않는다."""
    room, p = tc.make_world()
    p.give_weapon('chain')
    import mutations
    mutations.give(p, 'gather_wall')        # v8: 끌어오기는 모으기 갈래 증강부터 (이 파일은 끌어오는 사슬의 규칙을 본다)
    tc.set_gauge(p, gauge)
    foes = []
    for gap in gaps:
        e = tc.freeze(tc.add_enemy('slum', p.x + gap, room, p))
        e.hp = e.max_hp = 1000
        foes.append(e)
    tc.step(5)
    p.mouse_x, p.mouse_y = p.x + 600, (foes[0].center[1] if foes else p.center[1])
    return room, p, foes


def fire_and_wait(p, limit=120):
    """사슬을 던지고 끝날 때까지(갈고리가 돌아올 때까지) 돌린다. 던진 갈고리를 돌려준다."""
    assert p.request_attack()
    hook = p.weapon.hook
    assert hook is not None
    for _ in range(limit):
        tc.step(1)
        if p.weapon.hook is None:
            break
    assert p.weapon.hook is None, '사슬이 끝나지 않았다'
    return hook


def test_chain_pulls_hooked_enemy_close_and_gains_two_percent():
    room, p, (e,) = setup(35, [300])
    g0 = p.gauge.value
    hook = fire_and_wait(p)
    assert abs(e.x - p.x) < 140, abs(e.x - p.x)                          # 플레이어 앞까지 끌려왔다
    assert e.hp < 1000 and hook.pulled == [e]
    assert g0 + config.CHAIN_GAIN - 1.01 <= p.gauge.value <= g0 + config.CHAIN_GAIN + 0.01   # 1마리 +2% (자연 감소 1틱 허용)


def test_normal_hooks_one_and_awake_hooks_two():
    room, p, (a, b) = setup(35, [250, 380])
    bx = b.x
    fire_and_wait(p)
    assert a.hp < 1000 and b.hp == 1000 and abs(b.x - bx) < 1             # 노멀: 앞의 1마리만
    room, p, (a, b) = setup(65, [250, 380])
    g0 = p.gauge.value
    hook = fire_and_wait(p)
    assert a.hp < 1000 and b.hp < 1000 and len(hook.pulled) == 2          # 각성: 2마리
    assert abs(b.x - p.x) < 220
    assert p.gauge.value >= g0 + 2 * config.CHAIN_GAIN - 1.01             # 2마리 +4%


def test_awake_reach_is_thirty_percent_longer():
    gap = config.CHAIN_RANGE * 1.15
    room, p, (e,) = setup(35, [gap])
    fire_and_wait(p)
    assert e.hp == 1000                                                   # 노멀 사거리 밖
    room, p, (e,) = setup(65, [gap])
    fire_and_wait(p)
    assert e.hp < 1000                                                    # 각성: 사거리 +30%


def _wait_hit_ends(e, limit=180):
    n = 0
    while e.state == 'HIT' and n < limit:
        tc.step(1)
        n += 1
    return n / 60


def test_critical_stuns_for_one_second_and_pulled_enemies_clash():
    room, p, (a, b) = setup(95, [250, 380])
    hook = fire_and_wait(p)
    assert len(hook.pulled) == 2
    for e in (a, b):                                                      # 끌려온 둘이 부딪쳐 충돌 피해를 더 받는다
        assert abs((1000 - e.hp) - (hook.damage + config.CHAIN_CLASH_DAMAGE)) < 0.01, (1000 - e.hp, hook.damage)
    assert a.state == 'HIT' and abs(_wait_hit_ends(a) - config.CHAIN_STUN) < 0.1   # 1초 기절
    room, p, (a, b) = setup(65, [250, 380])
    hook = fire_and_wait(p)
    for e in (a, b):                                                      # 각성: 충돌 피해 없음
        assert abs((1000 - e.hp) - hook.damage) < 0.01
    assert _wait_hit_ends(a) < 0.4                                        # 짧은 경직뿐


def test_enhanced_chain_pierces_every_enemy_and_stuns():
    room, p, foes = setup(85, [220, 320, 420])
    p.gauge.use_enhance()                                                 # 85 - 25 = 60: 각성(원래는 2마리)
    assert p.gauge.enhanced
    hook = fire_and_wait(p)
    assert len(hook.pulled) == 3 and all(e.hp < 1000 for e in foes)       # 관통: 셋 다
    assert not p.gauge.enhanced                                           # 강화는 한 번 쓰면 끝
    assert foes[0].state == 'HIT' and _wait_hit_ends(foes[0]) > config.CHAIN_STUN - 0.15


def test_boss_is_hit_but_not_pulled():
    from boss import Boss
    room, p, _ = setup(35, [])
    boss = Boss(p.x + 300, tc.FLOOR_Y, room, p)
    boss.stats = dict(boss.stats, speed=0.0, sight=0)
    boss.cooldown = 99.0
    game_world.add_object(boss, game_world.LAYER_ENEMY)
    tc.step(5)
    x0, hp0 = boss.x, boss.hp
    p.mouse_x, p.mouse_y = boss.center
    hook = fire_and_wait(p)
    assert boss.hp < hp0 and abs(boss.x - x0) < 2 and hook.pulled == []


def test_chain_does_not_pass_through_walls():
    room, p = tc.make_world_with(tc.walled_room(), 14 * config.TILE + 30)    # 벽(열 15) 바로 왼쪽
    p.give_weapon('chain')
    behind = tc.freeze(tc.add_enemy('slum', 16 * config.TILE + 60, room, p))
    behind.hp = behind.max_hp = 1000
    p.mouse_x, p.mouse_y = behind.center
    fire_and_wait(p)
    assert behind.hp == 1000


def test_cannot_throw_again_while_chain_is_out():
    room, p, (e,) = setup(35, [380])
    assert p.request_attack()
    tc.step(2)
    assert not p.request_attack()                                         # 갈고리가 돌아오기 전에는 못 던진다


def test_chain_cannot_lock_an_enemy_by_throwing_again_and_again():
    """경직 저항: 끌려온 경직에서 풀린 직후 다시 걸어도 하던 일이 끊기지 않는다 (연타 무적 방지와 같은 규칙)."""
    room, p, (e,) = setup(35, [300])
    fire_and_wait(p)
    _wait_hit_ends(e)
    assert e.stagger_guard > 0
    tc.step(int(config.CHAIN_COOLDOWN * 60) + 1)
    e.x = p.x + 300
    p.mouse_x, p.mouse_y = e.center
    fire_and_wait(p)
    assert e.hp < 1000 - 1.5 * config.CHAIN_DAMAGE                        # 맞았고 끌려왔지만
    assert abs(e.x - p.x) < 140
    assert e.state != 'HIT'                                               # 경직으로 묶이지는 않았다


def test_chain_is_a_gold_room_weapon_with_an_icon():
    import items
    import weapon
    assert weapon.WEAPONS['chain'].weapon_id == 'chain'
    assert 'w_chain' in items.WEAPON_ITEMS and items.ITEMS['w_chain']['weapon'] == 'chain'
    assert os.path.exists(os.path.join(HERE, '..', 'assets', 'ui', 'icon_w_chain.png'))


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
