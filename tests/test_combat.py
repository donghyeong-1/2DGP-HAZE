"""전투 테스트: 파이프 공격, 적 AI, 투사체, 게이지 연결, 오버로드 (창 없이 실행). 실행: python tests/test_combat.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
from enemy import Enemy  # noqa: E402
from player import Player  # noqa: E402
from room import Room  # noqa: E402

DT = 1 / 60
FLOOR_Y = float(config.SCREEN_H - 16 * config.TILE)


def make_world(player_x=300.0):
    """방과 플레이어를 world에 넣고 착지시킨다. 적은 add_enemy로 따로 세운다."""
    game_world.clear()
    effects.reset()
    room = Room.load('test_01')
    player = Player(player_x, FLOOR_Y, room)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    step(30)
    player.mouse_x, player.mouse_y = player.x + 400, player.center[1]  # 오른쪽을 겨눈다
    return room, player


def step(frames):
    for _ in range(frames):
        game_world.update(DT)


def add_enemy(kind, x, room, player):
    e = Enemy(kind, x, FLOOR_Y, room, player)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return e


def freeze(e):
    """공격 판정만 시험하려고 적이 움직이지 못하게 한다."""
    e.stats = dict(e.stats, speed=0.0, sight=0)
    return e


def test_pipe_hits_enemy_in_front_and_gains_gauge():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 110, room, p))
    g0 = p.gauge.value
    assert p.request_attack()
    assert e.hp == e.max_hp - config.PIPE_DAMAGE
    assert p.gauge.value == g0 + config.GAIN_HIT


def test_pipe_misses_enemy_behind_and_out_of_reach():
    room, p = make_world()
    behind = freeze(add_enemy('slum', p.x - 110, room, p))
    far = freeze(add_enemy('slum', p.x + config.PIPE_REACH + 200, room, p))
    g0 = p.gauge.value
    p.request_attack()
    assert behind.hp == behind.max_hp and far.hp == far.max_hp
    assert p.gauge.value == g0


def test_aim_up_hits_enemy_on_higher_ground_not_one_below_aim():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 40, room, p))
    p.mouse_x, p.mouse_y = p.x - 300, p.center[1]   # 반대쪽을 겨누면 맞지 않는다
    p.request_attack()
    assert e.hp == e.max_hp


def test_combo_finisher_deals_more_and_gains_more():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 100, room, p))
    e.hp = e.max_hp = 1000
    p.request_attack()
    step(int(config.PIPE_COOLDOWN[0] * 60) + 2)
    p.request_attack()
    step(int(config.PIPE_COOLDOWN[1] * 60) + 2)
    hp_before = e.hp
    g0 = p.gauge.value
    p.request_attack()                      # 3타
    assert hp_before - e.hp == config.PIPE_DAMAGE * config.PIPE_FINISHER_MULT
    assert p.gauge.value - g0 >= config.PIPE_FINISHER_GAIN - 1  # 사이에 시간 감소가 끼어도 6 근처
    assert p.weapon.combo == 3


def test_attack_has_cooldown_and_combo_resets():
    room, p = make_world()
    assert p.request_attack()
    assert not p.request_attack()           # 쿨타임 중
    step(int((config.PIPE_COOLDOWN[0] + config.PIPE_COMBO_WINDOW) * 60) + 5)
    assert p.weapon.combo == 0              # 연타가 끊겼다


def test_kill_gives_kill_gauge_and_removes_enemy():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 100, room, p))
    e.hp = 1
    g0 = p.gauge.value
    p.request_attack()
    assert not e.alive and e not in game_world.world[game_world.LAYER_ENEMY]
    assert p.gauge.value == g0 + config.GAIN_HIT + config.GAIN_KILL


def test_awake_zone_multiplies_damage():
    room, p = make_world()
    p.gauge.value = 60.0
    p.gauge.zone = p.gauge._zone_of(60.0)
    e = freeze(add_enemy('slum', p.x + 100, room, p))
    e.hp = e.max_hp = 1000
    p.request_attack()
    assert e.max_hp - e.hp == config.PIPE_DAMAGE * config.MULT_AWAKE[0]


def test_hit_stop_requested_on_hit():
    room, p = make_world()
    freeze(add_enemy('slum', p.x + 100, room, p))
    p.request_attack()
    assert effects.hit_stop_left > 0
    assert effects.tick_hit_stop(DT) is True


def test_slum_chases_and_hits_player_then_player_is_invulnerable():
    room, p = make_world(player_x=300.0)
    e = add_enemy('slum', 300.0 + 450, room, p)
    g0 = p.gauge.value
    x0 = e.x
    step(60)
    assert e.x < x0 - 100 and e.state in ('CHASE', 'ATTACK')   # 쫓아온다
    for _ in range(240):                                         # 첫 타격까지
        if p.hp < config.PLAYER_HP:
            break
        step(1)
    assert p.hp == config.PLAYER_HP - e.stats['damage']
    assert p.gauge.value <= g0 + config.LOSS_DAMAGED + 1         # 게이지가 줄었다 (시간 감소 포함)
    step(20)
    assert p.hp == config.PLAYER_HP - e.stats['damage']          # 피격 직후 무적이라 연속으로 맞지 않는다


def test_dash_dodges_slum_attack():
    room, p = make_world(player_x=300.0)
    e = freeze(add_enemy('slum', 300.0 + 80, room, p))
    e.stats = dict(e.stats, speed=0.0, sight=900)
    step(int((e.stats['windup'] - 0.12) * 60) + 4)   # 휘두르기 직전
    assert e.state == 'ATTACK'
    p.mouse_x, p.mouse_y = p.x - 400, p.center[1]
    p.request_dash()                                  # 뒤로 대시하며 무적
    step(40)
    assert p.hp == config.PLAYER_HP


def test_thrower_throws_scrap_that_hits_player():
    room, p = make_world(player_x=300.0)
    t = add_enemy('thrower', 300.0 + 700, room, p)
    step(int((t.stats['windup'] + 0.5) * 60))
    assert any(type(o).__name__ == 'Scrap' for o in game_world.world[game_world.LAYER_EFFECT])
    step(120)
    assert p.hp == config.PLAYER_HP - t.stats['damage']
    assert not any(type(o).__name__ == 'Scrap' for o in game_world.world[game_world.LAYER_EFFECT])


def test_dash_passes_through_scrap():
    room, p = make_world(player_x=300.0)
    t = add_enemy('thrower', 300.0 + 700, room, p)
    step(int(t.stats['windup'] * 60) + 6)             # 던진 직후
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    for _ in range(40):                                # 날아오는 고철과 만나는 동안 대시
        if p.dash_slots and p.state != 'DASH' and p.invuln_left <= 0:
            p.request_dash()
        step(1)
    assert p.hp == config.PLAYER_HP


def test_take_hit_applies_gauge_loss_and_extra_delta():
    room, p = make_world()
    g0 = p.gauge.value
    p.take_hit(10, gauge_delta=15)                      # 간수처럼 게이지를 올리는 적
    assert p.hp == config.PLAYER_HP - 10
    assert p.gauge.value == g0 + config.LOSS_DAMAGED + 15
    p.take_hit(10)                                      # 무적 중에는 무시
    assert p.hp == config.PLAYER_HP - 10


def test_gauge_change_listener_reports_reason():
    room, p = make_world()
    seen = []
    p.gauge.change_listeners.append(lambda delta, reason: seen.append((delta, reason)))
    p.take_hit(5)
    assert (config.LOSS_DAMAGED, 'damaged') in seen


def test_overload_hurts_and_stuns_player():
    room, p = make_world()
    p.gauge.add(80)                                     # 30 -> 100 : 오버로드
    assert p.hp == config.PLAYER_HP - int(config.PLAYER_HP * config.OVERLOAD_DAMAGE_RATIO)
    assert p.stunned and p.gauge.value == config.OVERLOAD_RESET
    p.right = True
    assert p.direction == 0                              # 기절 중에는 움직일 수 없다
    assert not p.request_attack()
    state = p.state
    p.request_dash()
    assert p.state == state                               # 대시도 못 한다
    for _ in range(int(config.OVERLOAD_STUN * 60) + 5):   # 기절 시간은 게이지 tick(play_mode가 매 프레임 부른다)으로 줄어든다
        step(1)
        p.gauge.tick(DT)
    assert not p.stunned and p.direction == 1


def test_hits_add_screen_shake_that_decays_in_integer_pixels():
    room, p = make_world()
    freeze(add_enemy('slum', p.x + 100, room, p))
    assert effects.trauma == 0 and effects.shake_offset() == (0, 0)
    p.request_attack()
    assert effects.trauma >= config.SHAKE_HIT
    ox, oy = effects.shake_offset()
    assert isinstance(ox, int) and isinstance(oy, int)
    assert abs(ox) <= config.SHAKE_MAX_OFFSET and abs(oy) <= config.SHAKE_MAX_OFFSET
    effects.tick_shake(2.0)                              # 시간이 지나면 가라앉아 제자리로 돌아온다
    assert effects.trauma == 0 and effects.shake_offset() == (0, 0)


def test_taking_damage_shakes_and_freezes_briefly():
    room, p = make_world()
    p.take_hit(10)
    assert effects.trauma >= config.SHAKE_DAMAGED and effects.hit_stop_left >= config.HIT_STOP_DAMAGED


def make_world_in(room_name, player_x, links=('L', 'R')):
    game_world.clear()
    effects.reset()
    room = Room.load(room_name, links)
    player = Player(player_x, FLOOR_Y, room)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    step(30)
    return room, player


def test_spike_hurts_bounces_and_costs_gauge():
    room, p = make_world_in('pit_02', 300.0)
    p.x, p.y, p.vy = 14 * config.TILE + 30, FLOOR_Y + 40, 0.0       # 가시 구덩이(13~18칸) 안쪽 바로 위에서 떨어뜨린다
    hp0, g0 = p.hp, p.gauge.value
    step(10)
    assert p.hp == hp0 - config.SPIKE_DAMAGE
    assert p.gauge.value <= g0 + config.LOSS_DAMAGED + 1
    assert p.vy > 0 or p.y > FLOOR_Y + 5                          # 위로 튕겨 올랐다
    hp1 = p.hp
    step(20)
    assert p.hp == hp1                                            # 피격 직후 무적이라 연속 피해가 없다


def test_dash_through_spikes_is_safe():
    room, p = make_world_in('pit_02', 12 * config.TILE)
    p.mouse_x, p.mouse_y = p.x + 600, p.center[1]
    p.request_dash()
    step(12)
    assert p.hp == config.PLAYER_HP                               # 대시 무적 중에는 가시도 지나간다


def test_slum_leaps_up_to_chase_player_on_higher_ground():
    room, p = make_world_in('hall_01', 14 * config.TILE + 30)    # 입구 홀의 낮은 단(14~15줄) 위로 올라간다
    p.y = 1080 - 14 * config.TILE                                  # 단 윗면
    step(30)
    e = Enemy('slum', 10 * config.TILE + 30, FLOOR_Y, room, p)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    top = 1080 - 14 * config.TILE
    for _ in range(60 * 6):
        step(1)
        if e.y >= top - 1:
            break
    assert e.y >= top - 1, '슬럼이 단 위로 뛰어오르지 못했다'


def test_slum_walks_down_ledge_to_chase_lower_player():
    room, p = make_world_in('hall_01', 4 * config.TILE)           # 플레이어는 바닥
    top = 1080 - 14 * config.TILE
    e = Enemy('slum', 15 * config.TILE, top, room, p)             # 슬럼은 단 위
    game_world.add_object(e, game_world.LAYER_ENEMY)
    for _ in range(60 * 5):
        step(1)
        if e.y <= FLOOR_Y + 1 and e.x < 12 * config.TILE:
            break
    assert e.y <= FLOOR_Y + 1, '슬럼이 단 아래로 내려오지 못했다'


def test_thrower_ignores_player_on_another_tier():
    room, p = make_world_in('hall_01', 11 * config.TILE)          # 플레이어는 바닥
    ledge_top = 1080 - 11 * config.TILE                           # 오른쪽 얇은 발판 윗면 (바닥보다 5줄 위)
    t = Enemy('thrower', 20 * config.TILE + 30, ledge_top, room, p)
    game_world.add_object(t, game_world.LAYER_ENEMY)
    step(60 * 3)
    assert t.state in ('IDLE', 'CHASE') and not any(
        type(o).__name__ == 'Scrap' for o in game_world.world[game_world.LAYER_EFFECT])   # 층이 달라서 던지지 않는다


def test_slash_variant_follows_aim_direction():
    import math
    for deg, flip_expected, name in ((0, False, 0), (45, False, 1), (90, False, 2), (-45, False, 3), (-90, False, 4),
                                     (180, True, 0), (135, True, 1), (-135, True, 3)):
        v, flip = effects.slash_variant(math.cos(math.radians(deg)), math.sin(math.radians(deg)))
        assert (v, flip) == (name, flip_expected), (deg, v, flip)


def set_gauge(p, value):
    p.gauge.value = float(value)
    p.gauge.zone = p.gauge._zone_of(float(value))


def spawned_names():
    return [o.name for o in game_world.world[game_world.LAYER_EFFECT] if hasattr(o, 'name')]


def test_slash_sheet_depends_on_zone_finisher_and_enhance():
    assert effects.slash_sheet('FADE') == 'pipe-slash-fade'
    assert effects.slash_sheet('NORMAL') == 'pipe-slash'
    assert effects.slash_sheet('AWAKE') == 'pipe-slash-awake'
    assert effects.slash_sheet('CRITICAL') == 'pipe-slash-critical'
    assert effects.slash_sheet('AWAKE', finisher=True) == 'pipe-slash-finisher'                # 3타는 금색 큰 궤적
    assert effects.slash_sheet('FADE', finisher=True, enhanced=True) == 'pipe-slash-enhanced'    # 강화가 가장 우선
    assert len({effects.slash_sheet(z) for z in ('FADE', 'NORMAL', 'AWAKE', 'CRITICAL')}) == 4  # 구간마다 다르다


def test_every_zone_has_attack_fx_and_hit_effects_get_stronger():
    for zone in ('FADE', 'NORMAL', 'AWAKE', 'CRITICAL', 'OVERLOAD', 'DEAD'):
        fx = config.ZONE_FX[zone]
        assert {'slash', 'spark', 'shake', 'stop', 'sound', 'damage_color'} <= set(fx)
    order = [config.ZONE_FX[z] for z in ('FADE', 'NORMAL', 'AWAKE', 'CRITICAL')]
    assert [f['shake'] for f in order] == sorted(f['shake'] for f in order)      # 구간이 높을수록 흔들림·멈춤이 크다
    assert [f['stop'] for f in order] == sorted(f['stop'] for f in order)
    assert config.ENHANCED_FX['shake'] >= order[-1]['shake']
    assert len({f['damage_color'] for f in order}) == 4                          # 데미지 숫자 색도 다르다


def test_weapon_spawns_zone_specific_slash_and_spark():
    seen = {}
    for value, zone in ((10, 'FADE'), (30, 'NORMAL'), (60, 'AWAKE'), (95, 'CRITICAL')):
        room, p = make_world()
        freeze(add_enemy('slum', p.x + 100, room, p))
        set_gauge(p, value)
        p.request_attack()
        names = spawned_names()
        seen[zone] = names
        assert config.ZONE_FX[zone]['slash'] in names and config.ZONE_FX[zone]['spark'] in names, (zone, names)
    assert seen['FADE'] != seen['AWAKE'] != seen['CRITICAL']


def test_enhanced_attack_uses_its_own_slash_and_spark():
    room, p = make_world()
    freeze(add_enemy('slum', p.x + 100, room, p))
    set_gauge(p, 60)
    assert p.request_enhance()
    p.weapon.cooldown = 0
    game_world.world[game_world.LAYER_EFFECT].clear()
    p.request_attack()
    names = spawned_names()
    assert 'pipe-slash-enhanced' in names and 'pipe-slash-awake' not in names


def test_aura_follows_gauge_zone_and_enhance():
    assert effects.aura_names('NORMAL') == []                              # 노멀(20~49%)은 오라가 없다
    assert effects.aura_names('FADE') == ['aura-fade']
    assert effects.aura_names('AWAKE') == ['aura-awake']
    assert effects.aura_names('CRITICAL') == ['aura-critical']
    assert effects.aura_names('AWAKE', enhanced=True) == ['aura-awake', 'aura-enhanced']   # 구간 오라 위에 겹친다
    assert effects.aura_names('NORMAL', enhanced=True) == ['aura-enhanced']


def test_all_effect_sheets_used_by_zone_fx_exist_and_are_valid():
    import json
    names = {fx['slash'] for fx in config.ZONE_FX.values()} | {config.ENHANCED_FX['slash'], config.FINISHER_SLASH}
    names |= set(config.AURA_BY_ZONE.values()) | {config.AURA_ENHANCED, 'overload-burst', 'poof', 'hit-spark', 'crit-hit'}
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'effects')
    for name in names:
        assert os.path.exists(os.path.join(root, name + '.png')), name
        meta = json.load(open(os.path.join(root, name + '.json'), encoding='utf-8'))
        assert meta['frames'] >= 1 and meta['frameSize'][0] > 0
        if name in config.AURA_BY_ZONE.values() or name == config.AURA_ENHANCED:
            assert meta['loop'] is True                                    # 오라는 반복 재생이다


def test_draw_loop_frame_wraps_around():
    info = effects.sheet_info('pipe-slash')                                # 시트 정보만 시험 (그리기는 창이 필요하다)
    assert info['frames'] == info['variants'] * (info['frames'] // info['variants'])


def test_overload_spawns_burst_and_high_zone_entry_spawns_rage():
    room, p = make_world()
    game_world.world[game_world.LAYER_EFFECT].clear()
    p.gauge.add(80)                                                       # 오버로드
    assert 'overload-burst' in spawned_names()
    room, p = make_world()
    set_gauge(p, 45)
    game_world.world[game_world.LAYER_EFFECT].clear()
    p.gauge.add(10)                                                       # 노멀 -> 각성 진입
    assert 'rage' in spawned_names()


def walled_room():
    """바닥 위에 한 칸 두께의 높은 벽(15칸)이 서 있는 방. 벽 너머 공격이 막히는지 시험한다."""
    rows = [['.'] * 32 for _ in range(18)]
    for c in range(32):
        rows[0][c] = rows[16][c] = rows[17][c] = '#'
    for r in range(18):
        rows[r][0] = rows[r][31] = '#'
    for r in range(8, 16):
        rows[r][15] = '#'                                 # 열 15에 8줄 높이 벽
    return Room([''.join(r) for r in rows])


def make_world_with(room, player_x):
    game_world.clear()
    effects.reset()
    player = Player(player_x, FLOOR_Y, room)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    step(30)
    player.mouse_x, player.mouse_y = player.x + 400, player.center[1]
    return room, player


def test_melee_does_not_reach_through_walls():
    room, p = make_world_with(walled_room(), 14 * config.TILE + 30)        # 벽(열 15) 바로 왼쪽
    behind = freeze(add_enemy('slum', 16 * config.TILE + 30, room, p))      # 벽 바로 오른쪽 (사거리 안)
    p.request_attack()
    assert behind.hp == behind.max_hp                                       # 벽 너머라 맞지 않는다
    p.x = 16 * config.TILE + 30 + 100                                       # 같은 쪽으로 옮기면 맞는다
    p.weapon.cooldown = 0
    p.mouse_x, p.mouse_y = behind.x, p.center[1]
    p.request_attack()
    assert behind.hp < behind.max_hp


def test_enhanced_blast_and_dash_and_spin_also_respect_walls():
    room, p = make_world_with(walled_room(), 14 * config.TILE + 30)
    behind = freeze(add_enemy('slum', 16 * config.TILE + 30, room, p))
    behind.hp = behind.max_hp = 1000
    set_gauge(p, 60)
    p.request_enhance()
    p.request_attack()                                                      # 강화 일격도 벽 너머에는 안 닿는다
    assert behind.hp == behind.max_hp
    p.request_dash()                                                        # 대시 평타
    p.weapon.cooldown = 0
    p.request_attack()
    assert p.weapon.last_kind == 'dash' and behind.hp == behind.max_hp


def test_dash_strike_pierces_a_line_of_enemies():
    room, p = make_world()
    a = freeze(add_enemy('slum', p.x + 110, room, p))
    b = freeze(add_enemy('slum', p.x + 300, room, p))                       # 기본 사거리(150) 밖이지만 대시 평타 줄 안
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_dash()
    assert p.state == 'DASH'
    assert p.request_attack() and p.weapon.last_kind == 'dash'
    assert a.hp < a.max_hp and b.hp < b.max_hp                              # 줄에 선 적을 모두 벤다
    assert 'dash-strike' in spawned_names()
    assert p.state == 'DASH' and p.dash_left >= config.DASH_STRIKE_EXTEND   # 돌진하며 벤다


def test_dash_strike_window_closes_after_dash():
    room, p = make_world()
    freeze(add_enemy('slum', p.x + 110, room, p))
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_dash()
    for _ in range(int((config.DASH_TIME + config.DASH_ATTACK_WINDOW - 0.05) * 60)):
        game_world.update(DT)
    assert p.state != 'DASH' and p.dash_window > 0
    assert p.weapon.current_kind() == 'dash'                                # 막 끝난 직후에도 대시 평타
    for _ in range(30):
        game_world.update(DT)
    assert p.dash_window == 0 and p.weapon.current_kind() in ('pipe', 'spin', 'plunge')


def test_jump_attack_spins_around_the_player_and_hops():
    room, p = make_world()
    behind = freeze(add_enemy('slum', p.x - 120, room, p))                  # 조준 반대쪽(뒤)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_jump()
    for _ in range(8):
        game_world.update(DT)
    assert not p.on_ground
    assert p.weapon.current_kind() == 'spin'
    vy0 = p.vy
    assert p.request_attack() and p.weapon.last_kind == 'spin'
    assert behind.hp < behind.max_hp                                        # 360도라 뒤도 벤다
    assert p.vy >= config.AIR_HOP and 'air-spin' in spawned_names()


def test_plunge_hits_below_and_bounces():
    room, p = make_world()
    below = freeze(add_enemy('slum', p.x, room, p))
    p.request_jump()
    for _ in range(14):
        game_world.update(DT)
    p.mouse_x, p.mouse_y = p.x, p.y - 300                                   # 아래를 겨눈다
    assert p.weapon.current_kind() == 'plunge'
    p.invuln_left = 0
    assert p.request_attack() and p.weapon.last_kind == 'plunge'
    assert below.hp < below.max_hp
    assert p.vy == config.PLUNGE_BOUNCE and p.jump_count <= 1               # 맞으면 튕겨 오르고 다시 뛸 수 있다


def test_special_attacks_use_zone_damage_and_attack_bonus():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 110, room, p))
    e.hp = e.max_hp = 1000
    p.attack_bonus = 1.5
    set_gauge(p, 60)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_dash()
    p.request_attack()
    expected = config.PIPE_DAMAGE * config.MULT_AWAKE[0] * 1.5 * config.DASH_STRIKE_MULT
    assert abs((e.max_hp - e.hp) - expected) < 1e-6


def test_attack_blocked_only_while_hit_or_stunned_not_while_dashing():
    room, p = make_world()
    p.request_dash()
    assert p.request_attack()                                               # 대시 중에도 공격할 수 있다
    p2room, p2 = make_world()
    p2.take_hit(5)
    p2.invuln_left = 0
    assert p2.state == 'HIT' and not p2.request_attack()


def test_boss_leaps_over_cover_when_player_hides():
    from boss import Boss
    room, p = make_world_with(Room.load('boss_arena', {'L'}), 10 * config.TILE)
    boss = Boss(38 * config.TILE, 2 * config.TILE, room, p)
    game_world.add_object(boss, game_world.LAYER_ENEMY)
    step(20)
    room.line_blocked = lambda *a, **k: True                                # 플레이어가 벽 뒤에 숨은 상황
    assert boss._choose_pattern() == 'leap'
    boss.pattern = 'leap'
    boss.engage()
    x0 = boss.x
    step(60 * 4)
    assert boss.x < x0 - 400                                               # 숨은 플레이어 쪽으로 넘어왔다
    assert boss.state in ('CHASE', 'ATTACK')


def test_boss_arena_has_no_tall_cover_to_hide_behind():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'rooms', 'boss_arena.txt')
    with open(path, encoding='utf-8') as f:
        rows = [line.strip() for line in f.read().splitlines() if line.strip()]
    stand = len(rows) - 3
    for r in range(1, stand):                                              # 바닥 위 공중 줄에는 벽(#)이 없다 (1칸 단은 stand 줄)
        assert '#' not in rows[r][1:-1], f'{r}줄에 높은 엄폐물이 있다'


def test_player_dies_when_hp_reaches_zero():
    room, p = make_world()
    p.take_hit(config.PLAYER_HP)
    assert p.state == 'DEAD'


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
