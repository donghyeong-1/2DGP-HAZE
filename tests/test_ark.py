"""최종 보스 아크 테스트 (창 없이). 실행: python tests/test_ark.py

기획서 3.2: 헤이즈 탄막(탄환당 +5%), 순간이동 베기(-10%), 흡수 파동(-25%), 과충전 파동(+25%), 오염 장판(위에서 초당 +5%), 3페이즈.
게이지 수치는 '맞았을 때 최종 변화'다 (피격 기본 손실 -5까지 합친 값).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import projectile  # noqa: E402
from player import Player  # noqa: E402

DT = 1 / 60


def arena():
    import balance_sim                                   # 평평한 시험장 (44x18칸)
    return balance_sim.arena()


def make_fight(gap=500.0, gauge=50.0):
    """평평한 방에 플레이어와 아크를 세운다. 아크는 공격하지 않게 쿨다운을 길게 둔다(테스트가 직접 패턴을 시킨다)."""
    from ark import Ark
    game_world.clear()
    effects.reset()
    room = arena()
    floor = float(2 * config.TILE)                       # y는 위로 증가: 바닥 두 줄 위가 바닥 윗면
    p = Player(6 * config.TILE, floor, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    a = Ark(p.x + gap, floor, room, p)
    a.cooldown = 99.0
    game_world.add_object(a, game_world.LAYER_ENEMY)
    step(20)
    assert p.on_ground and a.on_ground
    set_gauge(p, gauge)
    p.hp = p.max_hp = 10 ** 6
    p.invuln_left = 0.0
    return room, p, a


def step(n):
    for _ in range(n):
        game_world.update(DT)


def set_gauge(p, value):
    p.gauge.value = float(value)
    p.gauge.zone = p.gauge._zone_of(float(value))


def objects(name):
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == name]


def start(a, pattern):
    a.state = 'CHASE'
    a.pattern = pattern
    a.count = 1
    a.engage()


def test_stage3_boss_room_spawns_ark():
    import stage as stage_mod
    game_world.clear()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    s = stage_mod.Stage(p, name='stage3')
    s.start()
    boss_room = next(c for c, info in s.layout.items() if info.get('type') == 'boss')
    s.enter_room(boss_room, 'L')
    assert type(s.boss).__name__ == 'Ark' and s.boss.title == '총감시관 아크'
    s2 = stage_mod.Stage(p, name='stage2')
    s2.start()
    s2.enter_room(next(c for c, info in s2.layout.items() if info.get('type') == 'boss'), 'L')
    assert type(s2.boss).__name__ == 'Boss' and s2.boss.title == '크래셔'


def test_barrage_bullet_raises_gauge_by_five():
    room, p, a = make_fight(gauge=50)
    hp0 = p.hp
    b = projectile.HazeBullet(p.x + 60, p.center[1], -1.0, 0.0, room, p)
    game_world.add_object(b, game_world.LAYER_EFFECT)
    step(10)
    assert abs(p.gauge.value - (50 + config.ARK_BULLET_NET)) < 0.6        # 최종 +5
    assert hp0 - p.hp == config.ARK_BULLET_DAMAGE


def test_barrage_fires_a_fan_toward_player_by_phase():
    for phase, count in ((1, config.ARK_BULLET_COUNT[0]), (3, config.ARK_BULLET_COUNT[2])):
        room, p, a = make_fight()
        a.phase = phase
        start(a, 'barrage')
        step(int(a._windup() * 60) + 2)
        bullets = objects('HazeBullet')
        assert len(bullets) == count, (phase, len(bullets))
        assert all(b.vx < 0 for b in bullets)                             # 플레이어(왼쪽) 쪽으로


def test_absorb_wave_lowers_gauge_by_25_and_can_be_jumped():
    room, p, a = make_fight(gauge=60)
    w = projectile.GaugeWave(p.x + 100, p.y, -1, 600.0, 'absorb', room, p)
    game_world.add_object(w, game_world.LAYER_EFFECT)
    step(20)
    assert abs(p.gauge.value - (60 + config.ARK_ABSORB_NET)) < 0.6        # 최종 -25
    room, p, a = make_fight(gauge=60)
    p.y += 160                                                            # 점프로 넘는다 (파동 높이 위)
    p.vy = 0.0
    w = projectile.GaugeWave(p.x + 100, p.y - 160, -1, 600.0, 'absorb', room, p)
    game_world.add_object(w, game_world.LAYER_EFFECT)
    for _ in range(12):
        p.vy = 0.0
        p.y = w.y + 160
        step(1)
    assert abs(p.gauge.value - 60) < 0.6


def test_overcharge_wave_raises_gauge_by_25():
    room, p, a = make_fight(gauge=40)
    w = projectile.GaugeWave(p.x + 100, p.y, -1, 600.0, 'overcharge', room, p)
    game_world.add_object(w, game_world.LAYER_EFFECT)
    step(20)
    assert abs(p.gauge.value - (40 + config.ARK_OVERCHARGE_NET)) < 0.6    # 최종 +25


def test_absorb_waves_close_in_from_edges_and_overcharge_spreads_out():
    room, p, a = make_fight(gap=700)
    start(a, 'absorb')
    step(int(a._windup() * 60) + 2)
    waves = objects('GaugeWave')
    assert len(waves) == 2 and {w.dir for w in waves} == {-1, 1}
    assert all((w.dir > 0) == (w.x < a.x) for w in waves)                 # 양끝에서 아크 쪽으로 조여 든다
    room, p, a = make_fight(gap=700)
    start(a, 'overcharge')
    step(int(a._windup() * 60) + 2)
    waves = objects('GaugeWave')
    assert len(waves) >= 2 and all((w.dir > 0) == (w.x > a.x) for w in waves)   # 아크에서 바깥으로


def test_field_raises_gauge_five_per_second_only_while_standing_in_it():
    room, p, a = make_fight(gauge=40)
    f = projectile.PollutionField(p.x, p.y, 300, 5.0, room, p)
    game_world.add_object(f, game_world.LAYER_EFFECT)
    step(60)
    assert abs(p.gauge.value - (40 + config.ARK_FIELD_RATE)) < 0.8        # 1초에 +5
    p.x += 400                                                            # 밖으로 나가면 오르지 않는다
    g = p.gauge.value
    step(60)
    assert p.gauge.value <= g + 0.01
    step(int(5 * 60))
    assert f not in game_world.world[game_world.LAYER_EFFECT]             # 시간이 지나면 사라진다


def test_slash_vanishes_appears_beside_player_and_cuts_gauge_by_10():
    room, p, a = make_fight(gap=700, gauge=50)
    start(a, 'slash')
    assert a._body_frame() == ('boss_ark_vanish', 1)                       # 안개로 흩어진다
    step(int(config.ARK_VANISH_TIME * 60) + 2)
    assert abs(a.x - p.x) < 220                                           # 플레이어 옆에 나타났다
    assert a._body_frame() == ('boss_ark_appear', 1)                       # 낮게 웅크림 (탄막 예고와 구별)
    step(int(config.ARK_APPEAR_TIME * 60 * 0.75))
    assert a._body_frame() == ('boss_ark_slash', 1)                        # 손날을 당김
    hp0 = p.hp
    step(int(a._active() * 60) + 4)
    assert p.hp < hp0 and abs(p.gauge.value - (50 + config.ARK_SLASH_NET)) < 0.6   # 최종 -10


def test_phases_change_at_two_thirds_and_one_third():
    room, p, a = make_fight()
    assert a.phase == 1
    a.hp = a.max_hp * 0.6
    step(2)
    assert a.phase == 2 and a.roar_left > 0 and a._body_frame() == ('boss_ark_phase', 1)
    a.hp = a.max_hp * 0.3
    step(2)
    assert a.phase == 3
    w3 = a._windup()
    a.phase = 1
    assert w3 < a._windup()                                               # 3페이즈는 예고가 짧다


def test_pattern_tables_by_phase_and_gauge_waves_alternate():
    room, p, a = make_fight(gap=500)
    room.line_blocked = lambda *args, **kw: False
    picks = []
    a.count = 1
    for _ in range(150):
        name = a._choose_pattern()
        a.last_pattern = name
        if name in ('absorb', 'overcharge'):
            a.last_wave = name
        picks.append(name)
    assert not {'absorb', 'overcharge'} & set(picks)                      # 1페이즈에는 게이지 파동이 없다
    assert {'barrage', 'slash', 'field'} <= set(picks)
    a.phase = 2
    picks = []
    for _ in range(300):
        name = a._choose_pattern()
        assert name != a.last_pattern                                     # 같은 패턴을 연달아 쓰지 않는다
        a.last_pattern = name
        if name in ('absorb', 'overcharge'):
            a.last_wave = name
        picks.append(name)
    waves = [n for n in picks if n in ('absorb', 'overcharge')]
    assert {'absorb', 'overcharge'} <= set(waves)
    assert all(waves[i] != waves[i + 1] for i in range(len(waves) - 1))   # 흡수와 과충전을 번갈아 (게이지를 위아래로 흔든다)


def test_first_pattern_is_barrage():
    room, p, a = make_fight()
    a.count = 0
    assert a._choose_pattern() == 'barrage'


def test_telegraph_poses_are_distinct():
    room, p, a = make_fight()
    seen = {}
    for pattern in ('barrage', 'absorb', 'overcharge', 'field'):
        start(a, pattern)
        a.attack_time = a._windup() * 0.8
        seen[pattern] = a._body_frame()
        a.attack_time = a._windup() + 0.05
        assert a._body_frame()[1] == 2                                     # 실행 자세
    assert seen == {'barrage': ('boss_ark_barrage', 1), 'absorb': ('boss_ark_absorb', 1),
                    'overcharge': ('boss_ark_overcharge', 1), 'field': ('boss_ark_field', 1)}


def test_every_pattern_has_pictures_to_draw():
    """2·3페이즈 방 쓰기(bands·crystals)는 전용 그림이 없어 그리다 튕겼다 (11/25 무작위 입력 난전에서 찾음).
    모든 패턴의 예고·실행 자세가 실제 그림 파일을 가리켜야 한다."""
    import ark
    import sprites
    room, p, a = make_fight()
    names = {n for table in ark.TABLES.values() for n in table} - {'wave'} | {'absorb', 'overcharge'}
    for pattern in sorted(names - {'slash'}):
        start(a, pattern)
        for t in (a._windup() * 0.5, a._windup() + 0.05):
            a.attack_time = t
            name, n = sprites.resolve(*a._body_frame())
            assert os.path.exists(os.path.join(HERE, '..', 'assets', sprites.path(name, n))), (pattern, name, n)


def test_death_shows_death_pose_and_clears_the_room():
    room, p, a = make_fight()
    assert a.take_damage(10 ** 6)
    assert not a.alive and a in game_world.world[game_world.LAYER_ENEMY]   # 바로 사라지지 않고 쓰러진다
    assert a._body_frame() == ('boss_ark_death', 1)
    step(int(config.ARK_DEATH_FALL * 60) + 2)
    assert a._body_frame() == ('boss_ark_death', 2)
    assert sum(1 for e in game_world.world[game_world.LAYER_ENEMY] if e.alive) == 0   # 방은 클리어된다
    assert p.shards >= config.SHARDS_PER_KILL['ark']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
