"""구역 새 적 5종 테스트 (창 없이). 실행: python tests/test_new_enemies.py

2026-11-22 v5 계획 1 (docs/plan_v5.md), 그림 Codex T38~T42. 규칙을 먼저 정한 테스트다.
- 탑: 감시 눈(벽 포탑, 레이저 예고 -> 발사, 부술 수 있음), 결정 기사(순간이동해 옆에서 벤다), 헤이즈 망령(벽 통과, 닿으면 게이지를 뺏음)
- 슬럼: 헤이즈 쥐 떼(작고 빠른 무리, 한 대에 죽음), 누더기 무당(다른 적에게 보호막)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import enemy_kinds as ek  # noqa: E402
import game_world  # noqa: E402
import sprites  # noqa: E402
import test_combat as tc  # noqa: E402

FLOOR_Y = tc.FLOOR_Y
NEW = ('eye', 'knight', 'wraith', 'rat', 'shaman')


def run(frames):
    import effects
    for _ in range(frames):
        effects.hit_stop_left = 0.0
        game_world.update(1 / 60)


def add(kind, x, y, room, p):
    e = ek.make(kind, x, y, room, p)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return e


# ----- 공통: 수치·그림 -----
def test_stats_and_sprites_registered():
    for k in NEW:
        s = config.ENEMY_STATS[k]
        assert 'hp' in s and 'hb' in s
        assert k in config.SHARDS_PER_KILL
        for name in s.get('frames', {}).values():
            assert name in sprites.FRAMES
    import killers
    for k in NEW:
        assert k in killers.ENEMY_NAMES


def test_sprite_files_exist():
    root = os.path.join(HERE, '..', 'assets')
    for name, (n, _x, _y) in sprites.FRAMES.items():
        if not any(name.startswith(f'enemy_{k}_') for k in NEW):
            continue
        for i in range(1, n + 1):
            assert os.path.exists(os.path.join(root, sprites.path(name, i))), (name, i)
    for k in NEW:
        assert os.path.exists(os.path.join(root, sprites.path(f'enemy_{k}_idle', 0)))


def test_make_returns_own_classes():
    room, p = tc.make_world()
    assert isinstance(ek.make('eye', 500.0, FLOOR_Y, room, p), ek.Eye)
    assert isinstance(ek.make('knight', 500.0, FLOOR_Y, room, p), ek.Knight)
    assert isinstance(ek.make('wraith', 500.0, FLOOR_Y, room, p), ek.Wraith)
    assert isinstance(ek.make('shaman', 500.0, FLOOR_Y, room, p), ek.Shaman)


# ----- 감시 눈 -----
def test_eye_sticks_to_wall_and_has_no_gravity():
    room, p = tc.make_world(player_x=900.0)
    e = add('eye', 400.0, FLOOR_Y, room, p)
    y0 = e.y
    assert y0 > FLOOR_Y + 60                                      # 바닥에서 떠서 벽에 붙는다
    assert e.x < 200 and e.face_dir == 1                          # 왼쪽 벽에 붙어 오른쪽(방 안)을 본다
    run(60)
    assert e.y == y0 and e.alive


def test_eye_laser_telegraphs_then_hits():
    room, p = tc.make_world(player_x=500.0)
    e = add('eye', 400.0, FLOOR_Y, room, p)
    hp = p.hp
    windup = e.stats['windup']
    run(int((windup - 0.15) * 60) + 3)                            # 발견 + 예고 거의 끝
    assert e.state == 'ATTACK' and p.hp == hp                     # 예고 중에는 맞지 않는다
    run(int((0.15 + e.stats['attack_time'] + 0.2) * 60))
    assert p.hp < hp                                              # 발사에 맞았다


def test_eye_laser_is_stopped_by_wall():
    room, p = tc.make_world(player_x=500.0)
    e = add('eye', 400.0, FLOOR_Y, room, p)
    x0, y0 = e.muzzle()
    ex, ey = e.beam_end(-1.5708)                                  # 곧장 아래
    assert abs(ey - FLOOR_Y) < config.TILE / 2 + 1                # 바닥에서 멈춘다
    assert abs(ex - x0) < 2
    ex, ey = e.beam_end(3.1416)                                   # 곧장 뒤(벽)
    assert abs(ex - x0) < 200


def test_eye_laser_interrupted_when_hit():
    room, p = tc.make_world(player_x=500.0)
    e = add('eye', 400.0, FLOOR_Y, room, p)
    run(int((e.stats['windup'] - 0.3) * 60) + 3)
    assert e.state == 'ATTACK'
    e.take_damage(1, from_x=p.x)
    assert e.state == 'HIT'
    hp = p.hp
    run(120)
    assert p.hp == hp or e.state != 'ATTACK'


def test_eye_dies_in_a_few_hits():
    room, p = tc.make_world()
    e = add('eye', 400.0, FLOOR_Y, room, p)
    assert e.stats['hp'] <= config.PIPE_DAMAGE * 3
    assert e.take_damage(e.hp)
    assert not e.alive


# ----- 결정 기사 -----
def test_knight_blinks_beside_player_and_slashes():
    room, p = tc.make_world(player_x=400.0)
    k = add('knight', 1100.0, FLOOR_Y, room, p)
    hp = p.hp
    closest = 9999.0
    for _ in range(60 * 6):
        run(1)
        closest = min(closest, abs(k.x - p.x))
    assert closest < 200                                          # 순간이동해 바로 옆에 나타났다
    assert p.hp < hp                                              # 그리고 벴다


def test_knight_untargetable_while_hidden():
    room, p = tc.make_world(player_x=400.0)
    k = add('knight', 1100.0, FLOOR_Y, room, p)
    seen = False
    for _ in range(60 * 5):
        run(1)
        if k.hidden:
            seen = True
            hp = k.hp
            assert k.take_damage(50, from_x=p.x) is False
            assert k.hp == hp
            break
    assert seen


def test_knight_walks_and_dies_normally():
    room, p = tc.make_world(player_x=300.0)
    k = add('knight', 1200.0, FLOOR_Y, room, p)
    assert k.take_damage(k.hp)
    assert not k.alive


# ----- 헤이즈 망령 -----
def test_wraith_flies_through_walls():
    room, p = tc.make_world(player_x=600.0)
    w = add('wraith', 30.0, FLOOR_Y + 300, room, p)               # 왼쪽 벽 속에서 시작
    assert room.tile_at_world(w.x, w.y + 30) == '#'
    w.cooldown = 99.0
    run(60 * 8)
    assert abs(w.x - p.x) < 200                                   # 벽 밖으로 나와 다가왔다
    assert abs(w.center[1] - p.center[1]) < 70                    # 플레이어 높이로 떠 있다


def test_wraith_has_no_gravity():
    room, p = tc.make_world(player_x=300.0)
    w = tc.freeze(add('wraith', 1200.0, FLOOR_Y + 300, room, p))
    y0 = w.y
    run(60)
    assert abs(w.y - y0) < 30


def test_wraith_grab_drains_gauge():
    room, p = tc.make_world(player_x=600.0)
    w = add('wraith', p.x + 120, p.y + 30, room, p)
    w.state = 'CHASE'
    w.cooldown = 0.0
    p.gauge.value = 60.0
    hp = p.hp
    run(int((w.stats['windup'] + 0.8) * 60))
    assert p.hp < hp
    assert p.gauge.value <= 60.0 + config.LOSS_DAMAGED + w.stats['gain_on_hit'] + 1.0   # 맞은 값 + 뺏긴 값


def test_wraith_staggers_when_hit():
    room, p = tc.make_world(player_x=600.0)
    w = add('wraith', p.x + 300, p.y + 30, room, p)
    w.state = 'CHASE'
    w.take_damage(1, from_x=p.x)
    assert w.state == 'HIT'


# ----- 헤이즈 쥐 떼 -----
def test_rat_pack_and_one_hit_kill():
    room, p = tc.make_world()
    rats = ek.make_pack('rat', 900.0, FLOOR_Y, room, p)
    assert len(rats) >= 3
    assert len({round(r.x) for r in rats}) == len(rats)           # 한 자리에 겹치지 않는다
    s = config.ENEMY_STATS['rat']
    assert s['hp'] <= config.PIPE_DAMAGE                          # 한 대에 죽는다
    assert s['speed'] > config.ENEMY_STATS['slum']['speed'] * 1.4 # 작고 빠르다
    assert s['hb'][1] < 60


def test_rat_bites_player():
    room, p = tc.make_world(player_x=400.0)
    r = tc.add_enemy('rat', p.x + 500, room, p)
    hp = p.hp
    run(60 * 4)
    assert p.hp < hp


# ----- 누더기 무당 -----
def test_shaman_shields_nearby_ally():
    room, p = tc.make_world(player_x=300.0)
    sh = add('shaman', p.x + 800, FLOOR_Y, room, p)
    ally = tc.freeze(tc.add_enemy('slum', p.x + 650, room, p))
    run(60 * 5)
    assert ally.shield > 0
    hp = ally.hp
    ally.take_damage(10, from_x=p.x)
    assert ally.hp == hp                                          # 보호막이 막았다
    ally.take_damage(ally.shield + 7, from_x=p.x)
    assert ally.shield <= 0 and ally.hp == hp - 7                 # 넘친 만큼만 들어간다
    assert sh.alive


def test_shaman_does_not_shield_itself_or_twice():
    room, p = tc.make_world(player_x=300.0)
    sh = add('shaman', p.x + 800, FLOOR_Y, room, p)
    ally = tc.freeze(tc.add_enemy('slum', p.x + 650, room, p))
    run(60 * 3)
    assert getattr(sh, 'shield', 0) == 0
    s0 = ally.shield
    run(60 * 4)
    assert ally.shield == s0                                      # 이미 있으면 다시 걸지 않는다


def test_shaman_backs_away_from_player():
    room, p = tc.make_world(player_x=600.0)
    sh = add('shaman', p.x + 200, FLOOR_Y, room, p)
    d0 = abs(sh.x - p.x)
    run(60 * 2)
    assert abs(sh.x - p.x) > d0 + 60


# ----- 배치 -----
def _kinds(name):
    import stage as stage_mod
    room, p = tc.make_world()
    st = stage_mod.Stage(p, seed=1, name=name)
    out = set()
    for c, info in st.layout.items():
        if info.get('type') == 'combat':
            out |= set(info.get('enemies', [])) | set(info.get('swap', {}).values())
    return out


def test_new_enemies_only_in_their_zone():
    assert {'rat', 'shaman'} <= _kinds('stage1')
    assert {'eye', 'knight', 'wraith'} <= _kinds('stage3')
    assert not {'eye', 'knight', 'wraith', 'rat', 'shaman'} & _kinds('stage2')
    assert not {'eye', 'knight', 'wraith'} & _kinds('stage1')
    assert not {'rat', 'shaman'} & _kinds('stage3')


def test_stages_spawn_new_kinds():
    import stage as stage_mod
    for name, want in (('stage1', {'rat', 'shaman'}), ('stage3', {'eye', 'knight', 'wraith'})):
        room, p = tc.make_world()
        st = stage_mod.Stage(p, seed=1, name=name)
        st.start()
        found = set()
        for c, info in st.layout.items():
            if info.get('type') == 'combat':
                st.enter_room(c, 'L')
                found |= {o.kind for o in game_world.world[game_world.LAYER_ENEMY]}
        assert want <= found, (name, found)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
