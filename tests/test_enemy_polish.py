"""적 다듬기 (창 없이). 실행: python tests/test_enemy_polish.py

v8 6일 차 대기열 2 (docs/NEXT_SESSION.md 4절): 행동·연출만 (수치는 밸런스 스레드).
1. 예고 -> 공격 -> 빈틈 리듬 통일: 일반 적은 공격이 끝나면 모두 '빈틈'(OPEN) 상태로 잠깐 서 있다.
   - 빈틈 동안은 움직이지 않고(땅의 적) 공격하지 않으며, 맞으면 간수(공격 중 슈퍼 아머)도 움찔한다.
   - 빈틈은 공격 쿨다운 안에서 흐른다: 공격과 공격 사이의 시간은 그대로다.
   - 보스는 자기 패턴의 빈틈이 따로 있어 그대로 둔다.
2. 서로 겹치지 않기: 같은 바닥의 땅 적은 한 자리에 겹쳐 서지 않는다 (앞에 동료가 있으면 줄을 선다).
3. 띄우기가 안 먹히던 적: 떠다니는 적(드론·망령)과 벽의 감시 눈은 띄우면 '뜬 상태'가 영영 풀리지 않고
   드론·망령은 위로 밀려 올라간 채였다. 경직이 끝나면 뜬 상태가 풀리고 제 높이로 돌아온다.
4. 보스 표시: weapon.py가 getattr(e, 'BOSS')로 보스를 거르는데(조각 처치·날려 보내기·처형 배율) 어느 보스도 BOSS가 없었다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import combo  # noqa: E402
import config  # noqa: E402
import effects  # noqa: E402
import enemy_kinds  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402

DT = 1 / 60


def world(px=300.0):
    room, p = tc.make_world(px)
    p.hp = p.max_hp = 10 ** 6
    return room, p


def add(kind, x, room, p):
    e = enemy_kinds.make(kind, x, tc.FLOOR_Y, room, p)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return e


def step(p, n=1):
    for _ in range(n):
        effects.hit_stop_left = 0.0
        effects.slow_left = 0.0
        p.invuln_left = 1.0
        game_world.update(DT)


def attack_until_open(e, p, limit=600):
    """적이 공격을 시작해 끝낼 때까지 돌린다. OPEN에 들어선 첫 프레임에서 멈춘다."""
    e.cooldown = 0.0
    started = False
    for _ in range(limit):
        step(p)
        started = started or e.state == 'ATTACK'
        if started and e.state == 'OPEN':
            return True
    return False


# ----- 1. 리듬 -----
def test_every_regular_enemy_opens_after_attacking():
    for kind, gap in (('slum', 110), ('hound', 110), ('guard', 140), ('thrower', 420), ('rat', 90),
                      ('drone', 0), ('wraith', 60), ('knight', 120)):
        room, p = world()
        e = add(kind, p.x + gap, room, p)
        assert attack_until_open(e, p), kind
        assert e.opening() > 0, kind


def test_opening_stands_still_and_does_not_attack():
    room, p = world()
    e = add('slum', p.x + 110, room, p)
    assert attack_until_open(e, p)
    x0 = e.x
    e.cooldown = 0.0                                               # 쿨다운이 끝나도 빈틈 동안은 공격하지 않는다
    for _ in range(int(e.open_left * 60) - 2):
        step(p)
        assert e.state == 'OPEN' and abs(e.x - x0) < 1.0
    step(p, 4)
    assert e.state != 'OPEN'


def test_opening_lives_inside_the_cooldown():
    room, p = world()
    e = add('guard', p.x + 140, room, p)
    assert attack_until_open(e, p)
    base = config.ENEMY_STATS['guard']['cooldown']
    assert 0.85 * base - 2 * DT <= e.cooldown <= 1.2 * base       # 쿨다운은 예전 그대로
    assert e.open_left <= e.cooldown + DT                         # 빈틈은 쿨다운 안에서 끝난다 = 공격 사이 시간은 그대로


def test_guard_super_armor_does_not_cover_the_opening():
    room, p = world()
    e = add('guard', p.x + 140, room, p)
    assert attack_until_open(e, p)
    e.stagger_guard = 0.0
    e.take_damage(1, from_x=p.x)
    assert e.state == 'HIT'


def test_opening_holds_the_recovery_pose():
    room, p = world()
    e = add('slum', p.x + 110, room, p)
    assert attack_until_open(e, p)
    name, n = e._body_frame()
    frames = config.ENEMY_STATS['slum']['frames']
    if 'attack' in frames:
        assert name == frames.get(e.move, frames['attack']) and n >= 1
    assert e._tint() is not None                                   # 빈틈은 색으로도 보인다


def test_bosses_keep_their_own_rhythm():
    from gatekeeper import Gatekeeper
    room, p = world()
    g = Gatekeeper(p.x + 600, tc.FLOOR_Y, room, p)
    game_world.add_object(g, game_world.LAYER_ENEMY)
    for _ in range(400):
        step(p)
        assert g.state != 'OPEN'


# ----- 2. 겹치지 않기 -----
def worst_overlap(kinds, frames=360, settle=150):
    room, p = world()
    es = [add(k, 900 + 10 * i, room, p) for i, k in enumerate(kinds)]
    worst = 1e9
    for f in range(frames):
        step(p)
        if f < settle:
            continue
        g = [e for e in es if e.alive and e.on_ground and e.state != 'HIT']
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a, b = g[i], g[j]
                if abs(a.y - b.y) < 40:
                    worst = min(worst, abs(a.x - b.x) / ((a.hb_w + b.hb_w) / 2))
    return worst


def test_ground_enemies_do_not_stack():
    for kinds in (['slum'] * 3, ['slum', 'guard', 'slum'], ['thrower', 'thrower'], ['slum', 'hound', 'rat']):
        assert worst_overlap(kinds) >= 0.8, kinds                  # 몸 너비의 80% 이상 떨어져 선다


# ----- 3. 떠다니는 적 띄우기 -----
def test_floating_enemies_recover_from_launch():
    for kind in ('drone', 'wraith', 'eye'):
        room, p = world()
        e = add(kind, p.x + 500, room, p)
        step(p, 180)                                               # 쫓아와 제 높이(드론은 머리 위)에 자리 잡는다
        y0 = e.y
        assert combo.launch(e, config.JUGGLE_RISE)
        for f in range(240):
            if f in (10, 20):
                combo.juggle(e)
            step(p)
        assert not e.launched, kind                                # 경직이 끝나면 뜬 상태가 풀린다
        assert abs(e.y - y0) < 60, (kind, e.y - y0)                 # 제 높이로 돌아온다 (둥실거림 ±12)


# ----- 4. 보스 표시 -----
def test_boss_classes_are_marked():
    import ark
    import boss
    import gatekeeper
    import heart
    import impact_frame
    for cls in (boss.Boss, ark.Ark, gatekeeper.Gatekeeper, heart.HeartCore, heart.HeartHand):
        assert getattr(cls, 'BOSS', False), cls.__name__
    assert not getattr(enemy_kinds.Enemy, 'BOSS', False) and not getattr(enemy_kinds.Drone, 'BOSS', False)
    assert set(impact_frame.BOSS_KINDS) >= {'gatekeeper', 'crasher', 'ark', 'heart'}


def test_big_kill_on_boss_is_not_shattered():
    from gatekeeper import Gatekeeper
    import weapon
    room, p = world()
    g = Gatekeeper(p.x + 200, tc.FLOOR_Y, room, p)
    game_world.add_object(g, game_world.LAYER_ENEMY)
    g.hp = 1
    p.weapon._hit(g, 50, 0, config.ZONE_FX['NORMAL'], big=True, extra=False)
    assert not g.alive
    assert not [o for o in game_world.world[game_world.LAYER_EFFECT] if isinstance(o, weapon.Shatter)]


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
