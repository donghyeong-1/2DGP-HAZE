"""손맛(피격 반응) 테스트 (창 없이). 실행: python tests/test_feel.py

2026-11-21 퀄리티 상승 계획 1-5 (docs/quality_plan.md):
- 맞은 적은 처음 잠깐 하얗게 번쩍이고(흰 번쩍임), 그 뒤 붉게 물든다.
- 밀려나는 거리는 적의 무게(사냥개 가볍게, 간수 무겁게)와 공격의 크기(큰 공격은 더 멀리)에 따라 다르다.
- 방의 마지막 적이 쓰러지면 잠깐 느려진다(슬로 모션). 보스는 더 길게.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import test_combat as tc  # noqa: E402


def _foe(kind, gap=120):
    room, p = tc.make_world()
    e = tc.freeze(tc.add_enemy(kind, p.x + gap, room, p))
    e.hp = e.max_hp = 1000
    return room, p, e


def test_hit_flashes_white_first_then_red():
    room, p, e = _foe('slum')
    e.take_damage(1, from_x=p.x)
    assert e.white_flash()                                  # 맞은 순간: 하얗게
    tc.step(int(config.ENEMY_WHITE_FLASH * 60) + 1)
    assert not e.white_flash() and e._tint() == (255, 90, 90)   # 그 뒤: 붉게


def test_light_enemies_fly_farther_than_heavy_ones():
    pushed = {}
    for kind in ('hound', 'slum', 'guard'):
        room, p, e = _foe(kind)
        e.take_damage(1, from_x=p.x)
        pushed[kind] = e.vx
    assert pushed['hound'] > pushed['slum'] > pushed['guard'] > 0, pushed


def test_big_hits_push_farther():
    room, p, e = _foe('slum')
    w = p.weapon
    w._hit(e, 1, 0, config.ZONE_FX['NORMAL'], extra=False)
    small = e.vx
    room, p, e = _foe('slum')
    p.weapon._hit(e, 1, 0, config.ENHANCED_FX, big=True, extra=False)
    assert e.vx > small * 1.4, (e.vx, small)


def test_slow_motion_scales_time_then_wears_off():
    effects.reset()
    assert effects.time_scale() == 1.0
    effects.request_slow_motion(0.4, 0.3)
    assert effects.time_scale() == 0.3
    effects.tick_slow_motion(0.2)
    assert effects.time_scale() < 1.0
    effects.tick_slow_motion(0.3)
    assert effects.time_scale() == 1.0


def test_clearing_a_room_slows_time_longer_for_a_boss():
    import play_mode

    class Dead:
        alive = False

    class FakeStage:
        boss = None

    effects.reset()
    play_mode._on_room_cleared(FakeStage())
    normal = effects.slow_left
    assert normal > 0 and effects.time_scale() < 1.0
    effects.reset()
    s = FakeStage()
    s.boss = Dead()
    play_mode._on_room_cleared(s)
    assert effects.slow_left > normal                       # 보스를 쓰러뜨리면 더 길게


# ----- Codex T25: 피격 2장, 쓰러지는 3장 (11/21) -----
def test_hurt_pose_alternates_two_frames():
    room, p, e = _foe('slum')
    e.take_damage(1, from_x=p.x)
    assert e._body_frame() == ('enemy_slum_hurt', 1)
    tc.step(7)
    assert e._body_frame() == ('enemy_slum_hurt', 2)                   # 뒤로 더 젖혀 비틀


def test_killed_enemy_collapses_then_scatters():
    import game_world
    import sprites
    for kind in ('slum', 'thrower', 'hound', 'guard'):
        assert sprites.count(f'enemy_{kind}_death') == 3 and sprites.count(f'enemy_{kind}_hurt') == 2, kind
    room, p, e = _foe('slum')
    e.hp = 1
    assert e.take_damage(5, from_x=p.x)
    corpses = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Corpse']
    assert len(corpses) == 1 and corpses[0].frame() == ('enemy_slum_death', 1)
    c = corpses[0]
    tc.step(30)
    assert c.frame() == ('enemy_slum_death', 3)                         # 쓰러져 누워 있다
    tc.step(int(config.CORPSE_TIME * 60) + 10)
    assert c not in game_world.world[game_world.LAYER_EFFECT]           # 헤이즈로 흩어져 사라진다



# ----- Codex T26: 무기별 전용 자세 (11/21) -----
def _poses(p, frames):
    seen = []
    for _ in range(frames):
        name = p._body_frame()
        if not seen or seen[-1] != name:
            seen.append(name)
        tc.step(1)
    return seen


def test_pistol_shot_uses_its_aiming_pose():
    room, p = tc.make_world()
    p.give_weapon('pistol')
    assert p.request_attack()
    seen = _poses(p, 30)
    assert ('n09_pistol', 1) in seen, seen                                # 두 총을 앞으로 겨눈 자세


def test_gauntlet_fire_and_air_down_poses():
    room, p = tc.make_world()
    p.give_weapon('gauntlet')
    tc.set_gauge(p, 60)
    p.attack_held = True
    assert p.request_attack() and p.weapon.charging
    tc.step(5)
    assert p._body_frame() == ('n09_gauntlet', 1)                         # 충전
    tc.step(int(config.GAUNTLET_CHARGE_TIME['AWAKE'] * 60) + 5)
    p.attack_held = False
    tc.step(1)
    assert p._body_frame() == ('n09_gauntlet', 2)                         # 발사
    seen = _poses(p, 30)
    assert ('n09_gauntlet', 3) in seen                                    # 회수
    p.start_punch('blast_down')
    assert p._body_frame() in (('n09_gauntlet', 4), ('n09_gauntlet_airdown', 1))   # 공중에서 아래로 쏘는 자세 (v7 새 그림은 따로)


def test_gauntlet_punch_follows_aim_and_air():
    import sprites
    if 'n09_gauntlet_upfwd' not in sprites.SKIN:
        return
    room, p = tc.make_world()
    p.give_weapon('gauntlet')
    for dy, name in ((300, 'n09_gauntlet_upfwd'), (-300, 'n09_gauntlet_downfwd'), (0, 'n09_gauntlet')):
        p.mouse_x, p.mouse_y = p.x + 400, p.center[1] + dy
        p.start_punch('blast')
        assert p._body_frame()[0] == name, (dy, p._body_frame())
    p.request_jump()
    tc.step(8)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.start_punch('blast')
    assert p._body_frame() == ('n09_gauntlet_air', 1)                     # 공중 앞 강타


def test_chain_throw_follows_aim_and_air():
    import sprites
    if 'n09_chain_upfwd' not in sprites.SKIN:
        return
    room, p = tc.make_world()
    p.give_weapon('chain')
    p.punch_kind, p.punch_total = 'throw', 1.0
    for dy, name in ((300, 'n09_chain_upfwd'), (-300, 'n09_chain_downfwd'), (0, 'n09_chain')):
        p.mouse_x, p.mouse_y = p.x + 400, p.center[1] + dy
        p.punch_left = 0.5                                                # 던지는 중간
        assert p._body_frame()[0] == name, (dy, p._body_frame())
    p.request_jump()
    tc.step(8)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.punch_left = 0.5
    assert p._body_frame() == ('n09_chain_air', 1)                        # 공중 앞 던지기


def test_chain_throw_then_pull_poses():
    room, p = tc.make_world()
    p.give_weapon('chain')
    e = tc.freeze(tc.add_enemy('slum', p.x + 300, room, p))
    e.hp = e.max_hp = 1000
    p.mouse_x, p.mouse_y = e.center
    assert p.request_attack()
    seen = _poses(p, 60)
    chain = [s for s in seen if s[0] == 'n09_chain']
    assert chain[:2] == [('n09_chain', 1), ('n09_chain', 2)] and ('n09_chain', 3) in chain, seen   # 돌림 -> 던짐 -> 당김


# ----- Codex T27: 크래셔 걷기 4장·쓰러짐 2장 (11/21) -----
def _crasher():
    from boss import Boss
    import game_world
    room, p = tc.make_world()
    b = Boss(p.x + 500, tc.FLOOR_Y, room, p)
    game_world.add_object(b, game_world.LAYER_ENEMY)
    return room, p, b


def test_crasher_walks_with_four_alternating_frames():
    import sprites
    room, p, b = _crasher()
    assert sprites.count('boss_crasher_walk') == 4
    b.state, b.vx, b.flash = 'CHASE', 80.0, 0.0
    seen = set()
    for i in range(8):
        b.walk_phase = i * 0.5
        name, n = b._body_frame()
        assert name == 'boss_crasher_walk', name
        seen.add(n)
    assert seen == {1, 2, 3, 4}


def test_crasher_collapses_instead_of_vanishing():
    import game_world
    room, p, b = _crasher()
    b.hp = 1
    assert b.take_damage(5, from_x=p.x)
    corpses = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Corpse']
    assert len(corpses) == 1 and corpses[0].frame() == ('boss_crasher_death', 1)
    tc.step(30)
    assert corpses[0].frame() == ('boss_crasher_death', 2)              # 엎어짐

# ----- 보스 체력 막대 (퀄리티 계획 4-4): 맞은 만큼이 잠깐 밝게 남았다가 따라 줄고, 페이즈 경계에 눈금 -----
def test_boss_bar_damage_trail_and_phase_marks():
    import ui
    assert ui.ghost_step(1.0, 0.7, 0.1) == 1.0                        # 맞은 직후 잠깐은 그대로 (BOSS_GHOST_HOLD)
    g = 1.0
    for _ in range(120):
        g = ui.ghost_step(g, 0.7, 1 / 60, held=1.0)
    assert abs(g - 0.7) < 1e-6                                         # 2초 안에 현재 체력까지 따라온다
    assert ui.ghost_step(0.5, 0.8, 0.1) == 0.8                         # 체력이 오르면 바로 맞춘다
    assert ui.boss_phase_marks('crasher') == [0.5]
    assert ui.boss_phase_marks('ark') == sorted(config.ARK_PHASES)


def test_player_is_knocked_back_away_from_the_attacker():
    """v7 (2026-11-23) 무게감: 주인공도 맞으면 때린 쪽 반대로 밀려난다 (경직 동안 점점 멈춘다)."""
    room, p, e = _foe('slum', gap=120)              # 적이 오른쪽에 있다
    x0 = p.x
    p.take_hit(5, source=e)
    tc.step(int(config.HIT_STUN * 60))
    assert p.x < x0 - 20, (x0, p.x)                  # 왼쪽으로 밀렸다
    e.x = p.x - 120                                  # 이번엔 왼쪽에서 맞는다
    p.invuln_left = 0.0
    tc.step(30)
    x1 = p.x
    p.take_hit(5, source=e)
    tc.step(int(config.HIT_STUN * 60))
    assert p.x > x1 + 20, (x1, p.x)


def test_kill_spawns_absorb_orbs_that_fly_into_the_player():
    """v7 흡수 연출: 처치하면 조각·게이지 알갱이가 생기고, 잠시 뒤 모두 주인공에게 닿아 사라진다."""
    import game_world
    room, p, e = _foe('slum', gap=100)
    e.hp = 1
    e.take_damage(5, from_x=p.x)
    tc.step(2)
    orbs = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'AbsorbOrb']
    assert len(orbs) >= 3
    tc.step(100)
    assert not [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'AbsorbOrb']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
