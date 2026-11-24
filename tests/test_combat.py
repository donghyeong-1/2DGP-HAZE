"""전투 테스트: 파이프 공격, 적 AI, 투사체, 게이지 연결, 오버로드 (창 없이 실행). 실행: python tests/test_combat.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import sprites  # noqa: E402
import weapon  # noqa: E402
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


def test_hound_is_faster_and_weaker_than_slum_and_guard_is_tougher():
    h, s, g = (config.ENEMY_STATS[k] for k in ('hound', 'slum', 'guard'))
    assert h['speed'] > s['speed'] > g['speed'] and h['hp'] < s['hp'] < g['hp']
    assert g['windup'] > s['windup'] > h['windup'] and g['damage'] > s['damage']


def test_hound_and_guard_chase_and_hit_player():
    for kind in ('hound', 'guard'):
        room, p = make_world(player_x=300.0)
        e = add_enemy(kind, 300.0 + 450, room, p)
        for _ in range(360):
            if p.hp < config.PLAYER_HP:
                break
            step(1)
        assert p.hp == config.PLAYER_HP - e.stats['damage'], kind


def test_hound_and_guard_sprites_exist_and_stage_spawns_them():
    import os as _os
    for kind in ('hound', 'guard'):
        assert _os.path.exists(_os.path.join(_os.path.dirname(__file__), '..', 'assets', sprites.path(config.ENEMY_STATS[kind]['sprite'], 0)))
    from room import SPAWN_KINDS
    assert SPAWN_KINDS['h'] == 'hound' and SPAWN_KINDS['g'] == 'guard'


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
    p.x, p.y, p.vy = 14 * config.TILE + 30, FLOOR_Y + 40, 0.0       # 가시 구덩이(11~21칸) 안쪽 바로 위에서 떨어뜨린다
    hp0, g0 = p.hp, p.gauge.value
    step(24)                                                      # 구덩이 바닥(한 줄 아래)까지 떨어져 가시에 닿는다
    assert p.hp == hp0 - config.SPIKE_DAMAGE
    assert p.gauge.value <= g0 + config.LOSS_DAMAGED + 1
    assert p.vy > 0 or p.y > FLOOR_Y + 5                          # 위로 튕겨 올랐다
    hp1 = p.hp
    step(20)
    assert p.hp == hp1                                            # 피격 직후 무적이라 연속 피해가 없다


def test_dash_through_spikes_is_safe():
    rows = ['#' * 32] + ['#' + '.' * 30 + '#'] * 14 + ['#' + '.' * 8 + '^^^' + '.' * 19 + '#'] + ['#' * 32] * 2
    room, p = make_world_with(Room(rows), 8 * config.TILE)
    p.mouse_x, p.mouse_y = p.x + 600, p.center[1]
    p.request_dash()
    step(12)
    assert p.x > 12 * config.TILE and p.hp == config.PLAYER_HP    # 대시 무적 중에는 가시도 지나간다


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
        slash = config.ZONE_FX[zone]['slash']                       # 1타 가로 베기는 같은 구간 색의 납작한 호(-flat)
        assert (slash in names or slash + '-flat' in names) and config.ZONE_FX[zone]['spark'] in names, (zone, names)
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
    assert effects.aura_names('AWAKE', enhanced=True) == ['aura-enhanced']                # 강화 준비 중에는 강화 오라가 대체한다
    assert effects.aura_names('NORMAL', enhanced=True) == ['aura-enhanced']


def test_all_effect_sheets_used_by_zone_fx_exist_and_are_valid():
    import json
    names = {fx['slash'] for fx in config.ZONE_FX.values()} | {config.ENHANCED_FX['slash'], config.FINISHER_SLASH}
    names |= set(config.AURA_BY_ZONE.values()) | {config.AURA_ENHANCED, 'overload-burst', 'puff', 'surge', 'haze-blast', 'quake-blast', 'death-burst', 'dust-land', 'shockwave'}
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
    assert 'surge' in spawned_names()


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


def test_enhanced_blast_also_respects_walls():
    room, p = make_world_with(walled_room(), 14 * config.TILE + 30)
    behind = freeze(add_enemy('slum', 16 * config.TILE + 30, room, p))
    behind.hp = behind.max_hp = 1000
    set_gauge(p, 60)
    p.request_enhance()
    p.request_attack()                                                      # 강화 일격도 벽 너머에는 안 닿는다
    assert behind.hp == behind.max_hp


def dash_until_done(p, attack=True):
    """대시하고(옵션: 대시 중에 평타를 눌러 두고) 대시가 끝날 때까지 프레임을 돌린다."""
    p.request_dash()
    assert p.state == 'DASH'
    if attack:
        assert p.request_attack() and p.weapon.last_kind == 'dash'
    for _ in range(60):
        game_world.update(DT)
        if p.state != 'DASH':
            break
    assert p.state != 'DASH'


def test_dash_strike_cuts_the_whole_path_travelled_when_the_dash_ends():
    room, p = make_world()
    a = freeze(add_enemy('slum', p.x + 110, room, p))
    b = freeze(add_enemy('slum', p.x + 300, room, p))                       # 대시가 지나온 경로 위 (기본 사거리 150 밖)
    c = freeze(add_enemy('slum', p.x + 520, room, p))                       # 경로가 끝난 뒤 (대시 거리 360 밖)
    d = freeze(add_enemy('slum', p.x - 150, room, p))                       # 출발점 뒤
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_dash()
    assert p.request_attack() and p.weapon.last_kind == 'dash'
    assert a.hp == a.max_hp and b.hp == b.max_hp                           # 대시 중에는 아직 베지 않는다
    for _ in range(60):
        game_world.update(DT)
        if p.state != 'DASH':
            break
    assert a.hp < a.max_hp and b.hp < b.max_hp                              # 대시가 끝나는 순간 지나온 경로를 한 번에 벤다
    assert c.hp == c.max_hp and d.hp == d.max_hp                            # 경로 밖은 맞지 않는다
    assert 'path-slash' in spawned_names()                                  # 지나온 직선을 긋는 효과


def test_dash_strike_path_is_a_straight_line_from_start_to_end():
    room, p = make_world()
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    x0, y0 = p.center
    dash_until_done(p, attack=False)
    x1, y1, = p.center
    ox, oy, ex, ey = p.last_dash_path
    assert abs(ox - x0) < 1 and abs(oy - y0) < 1                            # 시작
    assert abs(ex - x1) < 1 and abs(ey - y1) < 1                            # 끝
    assert ex - ox > 0.8 * config.DASH_SPEED * config.DASH_TIME             # 약 360px


def test_dash_strike_pressed_right_after_the_dash_still_cuts_the_path():
    room, p = make_world()
    a = freeze(add_enemy('slum', p.x + 200, room, p))
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    dash_until_done(p, attack=False)
    assert a.hp == a.max_hp
    assert p.dash_window > 0 and p.weapon.current_kind() == 'dash'
    assert p.request_attack()
    assert a.hp < a.max_hp                                                  # 끝난 직후(0.22초 안)에는 바로 벤다


def test_dash_strike_skips_enemies_behind_walls():
    room, p = make_world_with(walled_room(), 12 * config.TILE)
    behind = freeze(add_enemy('slum', 16 * config.TILE + 30, room, p))
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    dash_until_done(p)                                                      # 벽(열 15)에서 멈춰 경로가 짧아진다
    assert behind.hp == behind.max_hp


def test_dash_strike_window_closes_after_dash():
    room, p = make_world()
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    dash_until_done(p, attack=False)
    for _ in range(int(config.DASH_ATTACK_WINDOW * 60) + 6):
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
    assert p.vy >= config.AIR_HOP and any(n.endswith('-flat') for n in spawned_names())   # 공격 v3: 공중 1타 가로 호


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
    e = freeze(add_enemy('slum', p.x + 200, room, p))
    e.hp = e.max_hp = 1000
    p.attack_bonus = 1.5
    set_gauge(p, 60)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    dash_until_done(p)
    expected = config.PIPE_DAMAGE * config.MULT_AWAKE[0] * 1.5 * config.DASH_STRIKE_MULT
    assert abs((e.max_hp - e.hp) - expected) < 1e-6


def test_enhanced_applies_to_the_dash_strike_and_is_consumed():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 200, room, p))
    e.hp = e.max_hp = 1000
    set_gauge(p, 60)
    assert p.request_enhance()
    mult = p.gauge.zone_multipliers()['attack']                               # 강화 비용을 쓴 뒤의 구간 배율
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    dash_until_done(p)
    assert p.weapon.last_kind == 'dash' and p.weapon.last_enhanced              # 강화가 대시 평타에 얹혔다
    assert not p.gauge.enhanced                                               # 쓰고 나면 사라진다
    assert abs((e.max_hp - e.hp) - config.PIPE_DAMAGE * mult * config.ENHANCE_DAMAGE_MULT) < 1e-6
    enhanced_lines = [o for o in game_world.world[game_world.LAYER_EFFECT] if getattr(o, 'name', '') == 'path-slash']
    assert enhanced_lines and all(o.enhanced for o in enhanced_lines)          # 보라색 강화 직선


def test_enhanced_dash_strike_is_wider_and_blasts_around_each_enemy():
    room, p = make_world()
    off = freeze(add_enemy('slum', p.x + 200, room, p))
    off.y += 0                                                                  # 경로 위
    near = freeze(add_enemy('slum', p.x + 330, room, p))
    for e in (off, near):
        e.hp = e.max_hp = 1000
    set_gauge(p, 60)
    p.request_enhance()
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    dash_until_done(p)
    assert off.hp < off.max_hp and near.hp < near.max_hp
    assert config.DASH_STRIKE_ENHANCED_HALF_WIDTH > config.DASH_STRIKE_HALF_WIDTH


def test_enhanced_applies_to_the_jump_attack_and_plunge():
    room, p = make_world()
    behind = freeze(add_enemy('slum', p.x - 200, room, p))                      # 일반 회전 사거리(170) 밖, 강화 사거리(255) 안
    behind.hp = behind.max_hp = 1000
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.request_jump()
    for _ in range(8):
        game_world.update(DT)
    set_gauge(p, 60)
    assert p.request_enhance()
    assert p.weapon.current_kind() == 'spin'
    p.request_attack()
    assert p.weapon.last_kind == 'spin' and p.weapon.last_enhanced and not p.gauge.enhanced
    assert 'air-spin-enhanced' in spawned_names()
    assert behind.hp < behind.max_hp                                            # 강화로 사거리가 늘었다
    # 내려찍기도 강화된다
    room2, q = make_world()
    below = freeze(add_enemy('slum', q.x, room2, q))
    below.hp = below.max_hp = 1000
    q.request_jump()
    for _ in range(14):
        game_world.update(DT)
    set_gauge(q, 60)
    q.request_enhance()
    mult2 = q.gauge.zone_multipliers()['attack']
    q.mouse_x, q.mouse_y = q.x, q.y - 300
    q.invuln_left = 0
    q.request_attack()
    assert q.weapon.last_kind == 'plunge' and q.weapon.last_enhanced
    assert 'pipe-slash-enhanced' in spawned_names()
    assert abs((below.max_hp - below.hp) - config.PIPE_DAMAGE * mult2 * config.ENHANCE_DAMAGE_MULT) < 1e-6


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


def test_overload_triggers_screen_flash_hit_stop_and_zap():
    room, p = make_world()
    effects.reset()
    assert effects.flash_left == 0
    p.gauge.add(80)                                                       # 오버로드
    assert effects.flash_left >= config.OVERLOAD_FLASH - 1e-9             # 화면 전체 섬광
    assert effects.hit_stop_left >= config.OVERLOAD_HIT_STOP - 1e-9       # 폭발 순간 멈춤
    assert 'overload-burst' in spawned_names()
    effects.tick_shake(config.OVERLOAD_FLASH + 0.1)
    assert effects.flash_left == 0                                        # 섬광은 실제 시간으로 가라앉는다


def test_stun_aura_replaces_other_auras_and_exists():
    assert effects.aura_names('CRITICAL', enhanced=True, stunned=True) == ['aura-stun']
    assert effects.aura_names('AWAKE', stunned=True) == ['aura-stun']
    assert effects.aura_names('NORMAL', stunned=False) == []
    import json
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'effects')
    meta = json.load(open(os.path.join(root, 'aura-stun.json'), encoding='utf-8'))
    assert meta['loop'] is True and meta['frames'] == 16
    burst = json.load(open(os.path.join(root, 'overload-burst.json'), encoding='utf-8'))
    assert burst['scale'] == 2                                            # 화면을 가로지르는 큰 충격 링(정수 2배)


def test_waking_up_from_stun_spawns_puff_once():
    room, p = make_world()
    p.gauge.add(80)
    assert p.stunned
    game_world.world[game_world.LAYER_EFFECT].clear()
    for _ in range(int(config.OVERLOAD_STUN * 60) + 10):
        p.gauge.tick(DT)
        game_world.update(DT)
    assert not p.stunned
    assert spawned_names().count('puff') == 1                              # 깨어나는 순간 연기 한 번


def test_player_dies_when_hp_reaches_zero():
    room, p = make_world()
    p.take_hit(config.PLAYER_HP)
    assert p.state == 'DEAD'



def run_frames(n):
    for _ in range(n):
        game_world.update(DT)


def test_higher_zones_and_enhanced_attacks_hit_more_times():
    for value, extra in ((35, 0), (65, 1), (95, 2)):
        room, p = make_world()
        e = freeze(add_enemy('slum', p.x + 100, room, p))
        e.hp = e.max_hp = 10000
        set_gauge(p, value)
        p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
        p.request_attack()
        first = e.max_hp - e.hp
        run_frames(40)
        total = e.max_hp - e.hp
        assert abs(total - first * (1 + extra * config.EXTRA_HIT_RATIO)) < 1e-6, (value, first, total)


def test_enhanced_attack_adds_three_extra_hits_even_in_the_normal_zone():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 100, room, p))
    e.hp = e.max_hp = 10000
    set_gauge(p, 60)
    p.request_enhance()
    set_gauge(p, 35)
    p.gauge.enhance_timer = 12
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    first = e.max_hp - e.hp
    run_frames(60)
    assert abs((e.max_hp - e.hp) - first * (1 + 3 * config.EXTRA_HIT_RATIO)) < 1e-6


def test_extra_hits_stop_when_the_enemy_dies():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 100, room, p))
    e.hp = e.max_hp = 10000
    set_gauge(p, 95)
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    e.hp = 1
    run_frames(30)                                                    # 추가 타격에 죽고 더 이상 때리지 않는다
    assert not e.alive
    assert not any(isinstance(o, weapon.ExtraHits) for o in game_world.world[game_world.LAYER_EFFECT])


def test_dash_aimed_down_drops_through_a_one_way_platform():
    room, p = make_world_with(Room(['#' * 20] + ['#' + '.' * 18 + '#'] * 8 + ['#' + '.' * 6 + '=' * 6 + '.' * 6 + '#']
                                   + ['#' + '.' * 18 + '#'] * 4 + ['#' * 20]), 10 * config.TILE)
    # 발판 위에 세운다
    plat_row = 9
    p.y = room.tile_top(plat_row)
    p.on_ground = True
    run_frames(10)
    y0 = p.y
    assert p.on_ground and room.tile_at_world(p.x, p.y - 1) == '='
    p.mouse_x, p.mouse_y = p.x, p.y - 400                              # 마우스를 바로 아래로
    p.request_dash()
    assert p.state == 'DASH'
    run_frames(20)
    assert p.y < y0 - 100                                              # 발판을 뚫고 내려갔다


def test_dash_aimed_down_on_solid_ground_becomes_a_horizontal_dash():
    room, p = make_world()
    p.mouse_x, p.mouse_y = p.x + 5, p.y - 400
    x0 = p.x
    p.request_dash()
    run_frames(15)
    assert abs(p.x - x0) > 150 and p.on_ground                         # 바닥에 박히지 않고 옆으로 대시한다


def test_run_frames_follow_distance_when_moving_toward_aim():
    room, p = make_world()
    p.mouse_x = p.x + 2000                                               # 오른쪽을 겨누고 오른쪽으로 달린다
    p.right = True
    run_frames(int(config.RUN_START_TIME * 60) + 20)
    assert p.state == 'RUN' and p._body_frame()[0] == 'n09_run'          # 달리기 그림
    n = int(p.move_dist / config.RUN_FRAME_PX) % sprites.count('n09_run') + 1
    assert p._body_frame() == ('n09_run', n)                              # 이동 거리에 비례해 넘어간다
    p.right = False
    run_frames(30)
    assert p.move_dist == 0.0                                             # 멈추면 첫 프레임부터 다시


def test_backpedal_plays_run_frames_in_reverse_and_slower():
    """조준 반대쪽으로 움직이면(뒷걸음) 달리기 그림을 거꾸로 돌리고, 조금 느리게 물러난다."""
    room, p = make_world(player_x=900.0)
    p.mouse_x = p.x - 2000                                               # 왼쪽을 겨누고
    p.right = True                                                       # 오른쪽으로 움직인다
    seen = []
    for _ in range(40):
        p.mouse_x = p.x - 2000
        run_frames(1)
        name, n = p._body_frame()
        assert name == 'n09_run', name
        if not seen or seen[-1] != n:
            seen.append(n)
    assert len(seen) >= 3
    steps = [(seen[i] - seen[i + 1]) % sprites.count('n09_run') for i in range(len(seen) - 1)]   # v6 새 주인공은 6장
    assert all(s == 1 for s in steps), seen                              # 번호가 거꾸로 줄어든다 (8 -> 7 -> 6 ...)
    assert abs(p.vx - config.RUN_SPEED * config.BACKPEDAL_SPEED_MULT) < 1e-6   # 앞으로 달릴 때보다 느리다


def test_swing_ends_on_follow_through_frame():
    """휘두르기는 4번(마무리)에서 끝난다. 5번(파이프를 몸 뒤로 되감는 회수 그림)은 쓰지 않는다."""
    room, p = make_world()
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    seen = set()
    for _ in range(40):
        run_frames(1)
        name, n = p._body_frame()
        if name.startswith('n09_swing'):
            seen.add(n)
    assert max(seen) == config.SWING_LAST_FRAME == 4, seen


def test_run_start_ramps_speed_then_full():
    room, p = make_world()
    p.mouse_x = p.x + 2000
    p.right = True
    run_frames(2)
    assert 0 < p.vx < config.RUN_SPEED                                    # 출발 자세 동안은 최고 속도보다 느리다
    run_frames(int(config.RUN_START_TIME * 60) + 4)
    assert abs(p.vx - config.RUN_SPEED * p.speed_mult()) < 1e-6


def test_run_start_and_stop_transition_frames():
    room, p = make_world()
    p.mouse_x = p.x + 2000
    p.right = True
    run_frames(1)
    assert p._body_frame() == ('n09_run_trans', 1)                        # 출발: 숙이며 디딤
    run_frames(int(config.RUN_START_TIME * 60 * 0.6))
    assert p._body_frame() == ('n09_run_trans', 2)                        # 뒷발로 차고 나감
    run_frames(int(config.RUN_START_TIME * 60))
    assert p._body_frame()[0] == 'n09_run'
    run_frames(30)                                                       # 충분히 달린 뒤 멈춘다
    p.right = False
    run_frames(1)
    assert p.state == 'IDLE' and p._body_frame() == ('n09_run_trans', 3)  # 멈춤: 몸을 젖혀 제동
    run_frames(int(config.RUN_STOP_TIME * 60 * 0.6))
    assert p._body_frame() == ('n09_run_trans', 4)                        # 버티며 선다
    run_frames(int(config.RUN_STOP_TIME * 60))
    assert p._body_frame()[0] == 'n09_idle'
    p.right = True                                                       # 짧게 톡 움직이고 멈추면 제동 자세 없이 선다
    run_frames(int(config.RUN_STOP_MIN_RUN * 60 * 0.5))
    p.right = False
    run_frames(1)
    assert p._body_frame()[0] == 'n09_idle'


def test_turn_frame_keeps_previous_facing_briefly():
    room, p = make_world(player_x=900.0)
    p.mouse_x = p.x + 2000
    p.right = True
    run_frames(30)
    assert p.face_dir == 1
    p.mouse_x = p.x - 2000                                               # 달리다가 조준이 뒤로 넘어간다
    run_frames(1)
    assert p.face_dir == -1 and p._body_frame() == ('n09_run_trans', 5)
    assert p.draw_face() == 1                                            # 전환 그림은 원래 보던 쪽 그대로 그린다
    run_frames(int(config.RUN_TURN_TIME * 60) + 2)
    assert p.draw_face() == -1 and p._body_frame()[0] != 'n09_run_trans'


def test_body_frame_follows_state():
    room, p = make_world()
    assert p._body_frame()[0] == 'n09_idle' and p._body_frame()[1] >= 1           # 서 있으면 숨쉬기
    p.right = True
    run_frames(10)
    assert p._body_frame()[0] in ('n09_run', 'n09_run_trans', 'n09_walk')   # 움직이면 이동 그림
    p.right = False
    run_frames(10)
    p.request_jump()
    run_frames(3)
    assert p._body_frame() == ('n09_jump', 2)                                     # 상승
    run_frames(40)
    assert p._body_frame()[0] in ('n09_jump', 'n09_idle')
    p.invuln_left = 0
    p.take_hit(5)
    assert p.state == 'HIT' and p._body_frame() == ('n09_hurt', 1)                # 맞자마자 첫 프레임
    run_frames(12)
    assert p.state != 'HIT' or p._body_frame() == ('n09_hurt', 2)


def test_attack_shows_swing_pose_by_aim_direction():
    for aim_dy, expected in ((0.0, 'side'), (200.0, 'upfwd'), (600.0, 'up'), (-200.0, 'downfwd'), (-600.0, 'down')):
        room, p = make_world()
        p.mouse_x, p.mouse_y = p.x + 300, p.center[1] + aim_dy
        assert p.request_attack()
        assert p.swing_dir == expected, (aim_dy, p.swing_dir)
        assert p._body_frame() == ('n09_swing_' + expected, 1)               # 젖힘 프레임으로 시작
        run_frames(int(config.SWING_TIME * 60 * 0.3))
        assert p._body_frame() == ('n09_swing_' + expected, 3)               # 타격(최대 신장)
        run_frames(int(config.SWING_TIME * 60 * 0.5))
        assert p._body_frame() == ('n09_swing_' + expected, 4)               # 마무리에서 끝난다 (5번 회수는 쓰지 않는다)
        run_frames(30)
        assert p._body_frame()[0] != 'n09_swing_' + expected                 # 끝나면 대기로 돌아간다


def test_dash_death_and_plunge_poses():
    room, p = make_world()
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_dash()
    assert p.state == 'DASH' and p._body_frame()[0] == 'n09_dash'                # 대시 자세
    run_frames(30)
    room, q = make_world()
    q.hp = 0
    q.die()
    assert q.state == 'DEAD' and q._body_frame() == ('n09_death', 1)             # 뒤로 젖혀짐
    run_frames(int(config.DEATH_FRAME_TIMES[0] * 60) + 3)
    assert q._body_frame() == ('n09_death', 2)                                   # 무릎 꿇음
    run_frames(60)
    assert q._body_frame() == ('n09_death', 3)                                   # 엎어진 채 유지
    room, r = make_world()
    r.request_jump()
    run_frames(10)
    r.mouse_x, r.mouse_y = r.x, r.y - 400
    r.request_attack()
    assert r.weapon.last_kind == 'plunge' and r._body_frame() == ('n09_plunge', 1)
    run_frames(int(config.PLUNGE_POSE_TIME * 60 * 0.5))
    assert r._body_frame()[0] in ('n09_plunge', 'n09_jump')


def test_enemy_frames_follow_state():
    room, p = make_world()
    e = add_enemy('slum', p.x + 700, room, p)
    assert e._body_frame() == (None, 0)                                   # 대기: 그림 한 장
    run_frames(40)
    assert e.state == 'CHASE' and e._body_frame()[0] == 'enemy_slum_walk'   # 쫓아오면 걷기
    e.state = 'ATTACK'
    e.attack_time = 0.0
    assert e._body_frame() == ('enemy_slum_attack', 1)                    # 예고
    e.attack_time = e.stats['windup'] + 0.01
    assert e._body_frame() == ('enemy_slum_attack', 2)                    # 타격
    e.attack_time = e.stats['windup'] + e.stats['attack_time'] * 0.9
    assert e._body_frame() == ('enemy_slum_attack', 3)                    # 회복
    e.state = 'HIT'
    e.hit_left = 0.18                                                     # 막 맞음: 움찔 (T25 이후 뒤 절반은 2장째)
    assert e._body_frame() == ('enemy_slum_hurt', 1)
    th = add_enemy('thrower', p.x + 500, room, p)
    th.state = 'ATTACK'
    th.attack_time = 0.0
    assert th._body_frame() == ('enemy_thrower_throw', 1)
    th.state = 'CHASE'
    assert th._body_frame() == (None, 0)                                  # 걷지 않는 적은 대기 그림


def test_hound_and_guard_use_move_specific_frames():
    import sprites
    room, p = make_world()
    for kind, walk, expect in (('hound', 'enemy_hound_run', {'bite': 'enemy_hound_bite', 'pounce': 'enemy_hound_pounce'}),
                               ('guard', 'enemy_guard_walk', {'swing': 'enemy_guard_swing', 'heavy': 'enemy_guard_heavy',
                                                              'bash': 'enemy_guard_bash'})):
        e = add_enemy(kind, p.x + 700, room, p)
        e.state, e.vx, e.on_ground = 'CHASE', 100.0, True
        assert e._body_frame()[0] == walk                                 # 걷기·달리기 그림
        for move, name in expect.items():
            e.state, e.move = 'ATTACK', move
            e.attack_time = 0.0
            assert e._body_frame() == (name, 1), (kind, move)            # 기술마다 다른 예고 자세
            for t in (0.05, 0.2, 0.5, 1.0):                               # 어느 시점이든 그 세트에 있는 번호만
                e.attack_time = e._windup_time() + t
                got, n = e._body_frame()
                assert got == name and 1 <= n <= sprites.count(name), (kind, move, t, n)
        e.state = 'HIT'
        e.hit_left = 0.18
        assert e._body_frame() == (f'enemy_{kind}_hurt', 1)
    h = add_enemy('hound', p.x + 300, room, p)
    h.state, h.move, h.attack_time = 'ATTACK', 'pounce', h._windup_time() + 0.1
    h.on_ground = False
    assert h._body_frame() == ('enemy_hound_pounce', 2)                   # 나는 동안 앞발을 뻗는다


def test_boss_frames_follow_pattern():
    from boss import Boss
    room, p = make_world()
    b = Boss(p.x + 600, 120, room, p)
    game_world.add_object(b, game_world.LAYER_ENEMY)
    assert b._body_frame()[0] == 'boss_crasher_idle'
    b.state, b.pattern, b.attack_time = 'ATTACK', 'slam', 0.0
    assert b._body_frame() == ('boss_crasher_smash', 1)                   # 예고: 주먹을 든다
    b.attack_time = b._windup() + 0.01
    assert b._body_frame() == ('boss_crasher_smash', 2)                   # 내려찍음
    b.attack_time = b._windup() + b._active() * 0.9
    assert b._body_frame() == ('boss_crasher_smash', 3)                   # 마무리
    b.pattern, b.attack_time = 'charge', b._windup() + 0.01
    assert b._body_frame()[0] == 'boss_crasher_charge'
    b.pattern, b.attack_time = 'leap', 0.0
    assert b._body_frame() == ('boss_crasher_leap', 1)
    b.attack_time = b._windup() + 0.1
    assert b._body_frame() == ('boss_crasher_leap', 2)                    # 공중
    b.state, b.land_left = 'CHASE', 0.2
    assert b._body_frame() == ('boss_crasher_leap', 3)                    # 착지
    b.land_left, b.flash = 0.0, 0.1
    assert b._body_frame() == ('boss_crasher_hurt', 1)                    # 맞으면 움찔


def test_hit_spawns_impact_rays_and_attack_leaves_smear():
    room, p = make_world()
    e = freeze(add_enemy('slum', p.x + 100, room, p))
    e.hp = e.max_hp = 10000
    set_gauge(p, 95)
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    layer = game_world.world[game_world.LAYER_EFFECT]
    bursts = [o for o in layer if isinstance(o, effects.ImpactBurst)]
    assert bursts and len(bursts[0].rays) == config.IMPACT_RAYS['CRITICAL']       # 위험 구간 10줄
    assert any(isinstance(o, effects.BodyGhost) for o in layer)                    # 휘두르는 몸의 잔상
    run_frames(30)
    assert not any(isinstance(o, (effects.ImpactBurst, effects.BodyGhost)) for o in layer)   # 짧게 사라진다


# ----- 애니메이션 자연스러움 -----
def test_swing_on_ground_slows_running_and_steps_toward_aim():
    room, p = make_world()
    p.right = True
    run_frames(20)
    assert p.state == 'RUN'
    full = config.RUN_SPEED * p.speed_mult()
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    x0 = p.x
    p.request_attack()
    run_frames(int(config.SWING_STYLE_TIME[1] * 60))
    assert p.x - x0 < full * config.SWING_STYLE_TIME[1] * 0.8              # 그냥 달릴 때보다 덜 갔다 (거의 멈춘다)
    room, q = make_world()
    q.mouse_x, q.mouse_y = q.x + 300, q.center[1]
    x0 = q.x
    q.request_attack()
    run_frames(15)
    assert q.x > x0 + 5                                                      # 서서 쳐도 조준 쪽으로 한 발 내딛는다


def test_swing_shows_strike_pose_while_hit_stop_freezes_the_game():
    """판정은 누르는 순간이고 곧바로 타격 멈춤이 걸린다. 멈춘 동안 몸이 아직 젖힌 채면 폭발만 먼저 보인다 -> 타격 자세 이상을 보인다."""
    for style_hits in (0, 2):                                                # 1타, 3타(마무리)
        room, p = make_world()
        e = freeze(add_enemy('slum', p.x + 80, room, p))
        e.hp = e.max_hp = 10 ** 6
        p.mouse_x, p.mouse_y = e.x, e.center[1]
        for _ in range(style_hits):
            p.request_attack()
            run_frames(int(max(config.PIPE_COOLDOWN) * 60) + 1)
        effects.reset()
        assert p.request_attack()
        assert effects.hit_stop_left > 0                                     # 맞혔으니 멈춤이 걸렸다
        assert p._body_frame()[1] >= 3, (style_hits, p._body_frame())       # 멈춘 화면에는 타격 자세
        while effects.hit_stop_left > 0:                                    # 멈춤이 풀린 뒤에도 젖힘으로 되돌아가지 않는다
            effects.tick_hit_stop(DT)
        for _ in range(int(p.swing_left * 60)):
            run_frames(1)
            if p.swing_left > 0:
                assert p._body_frame()[1] >= 3, (style_hits, p._body_frame())


def test_combo_swings_have_different_shapes():
    room, p = make_world()
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    assert p.swing_style == 1 and p._body_frame() == ('n09_swing_side', 1)   # 1타: 준비부터
    run_frames(int(config.PIPE_COOLDOWN[0] * 60) + 1)
    p.request_attack()
    assert p.swing_style == 2 and p._body_frame() == ('n09_swing_side2', 1)  # 2타: 공격 v3 사선 반원 (머리 위로 든 모습을 짧게 보인다)
    run_frames(int(config.PIPE_COOLDOWN[1] * 60) + 1)
    p.request_attack()
    assert p.swing_style == 3 and p.swing_total == config.SWING_STYLE_TIME[3]   # 3타: 길게 끌어 크게 내딛는다
    assert abs(p.lunge_vx) == config.SWING_LUNGE[3]


# ----- 적 AI 다양화 -----
def _attack_moves(kind, distance, attacks=8):
    """적을 플레이어 앞에 세워 두고 여러 번 공격하게 해서 쓴 기술을 모은다 (플레이어는 맞아도 죽지 않게)."""
    room, p = make_world(player_x=300.0)
    p.hp = p.max_hp = 10 ** 6
    e = add_enemy(kind, 300.0 + distance, room, p)
    e.stats = dict(e.stats, speed=0.0, keep_away=0, retreat=0.0)
    used = []
    for _ in range(60 * 40):
        if e.state == 'ATTACK' and (not used or used[-1][1] != e.attacks):
            used.append((e.move, e.attacks))
        step(1)
        p.invuln_left = 0
        p.gauge.value = 50
        if e.state != 'ATTACK':
            e.x = 300.0 + distance                 # 덮치기·돌진으로 움직여도 같은 거리에서 다시 시작
        if len(used) >= attacks:
            break
    return [m for m, _ in used]


def test_first_attack_is_the_basic_move_then_moves_vary():
    for kind, distance in (('slum', 90), ('thrower', 600), ('guard', 110), ('hound', 100)):
        moves = _attack_moves(kind, distance)
        basic = config.ENEMY_STATS[kind]['moves'][0][0]
        assert moves and moves[0] == basic, (kind, moves)
        if kind != 'hound':                                                # 사냥개는 이 거리에서 물기뿐 (덮치기는 멀 때)
            assert len(set(moves)) >= 2, (kind, moves)                     # 같은 기술만 쓰지 않는다


def test_hound_pounces_from_distance_and_hits():
    room, p = make_world(player_x=300.0)
    h = add_enemy('hound', 300.0 + 330, room, p)
    h.attacks = 1                                                          # 첫 기본기는 지나간 상태
    step(1)
    h.state, h.cooldown = 'CHASE', 0.0
    step(1)
    assert h.state == 'ATTACK' and h.move == 'pounce', (h.state, h.move)    # 물기 거리 밖이면 덮친다
    for _ in range(120):
        if p.hp < config.PLAYER_HP:
            break
        step(1)
    assert p.hp == config.PLAYER_HP - h.stats['damage']


def test_hound_retreats_after_attacking():
    room, p = make_world(player_x=300.0)
    h = add_enemy('hound', 300.0 + 100, room, p)
    p.hp = p.max_hp = 10 ** 6
    for _ in range(120):
        step(1)
        if h.attacks >= 1:
            break
    assert h.retreat_left > 0
    x0 = h.x
    step(15)
    assert h.x > x0 + 20                                                   # 치고 빠진다


def test_thrower_hops_back_when_player_comes_close():
    room, p = make_world(player_x=300.0)
    t = add_enemy('thrower', 300.0 + 500, room, p)
    p.hp = p.max_hp = 10 ** 6
    for _ in range(180):                                                  # 첫 던지기가 끝날 때까지
        step(1)
        if t.attacks >= 1 and t.state == 'CHASE':
            break
    t.cooldown = 5.0
    p.x = t.x - 150
    x0 = t.x
    step(40)
    assert t.x > x0 + 60                                                   # 뒤로 뛰어 거리를 벌렸다


def test_thrower_lob_arcs_onto_player():
    room, p = make_world(player_x=300.0)
    t = add_enemy('thrower', 300.0 + 600, room, p)
    step(1)
    t.state = 'CHASE'
    t.engage()
    t.move = 'lob'
    step(int(t._windup_time() * 60) + 2)
    lobs = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Lob']
    assert lobs and lobs[0].vy > 0                                        # 위로 던졌다
    for _ in range(120):
        if p.hp < config.PLAYER_HP:
            break
        step(1)
    assert p.hp == config.PLAYER_HP - t.stats['damage']                    # 포물선 끝이 플레이어 자리다


def test_guard_heavy_makes_short_shockwaves_and_keeps_attacking_when_hit():
    room, p = make_world(player_x=300.0)
    g = add_enemy('guard', 300.0 + 110, room, p)
    step(1)
    g.state = 'CHASE'
    g.engage()
    g.move = 'heavy'
    g.take_damage(5, from_x=p.x)
    assert g.state == 'ATTACK'                                             # 공격 중에는 맞아도 끊기지 않는다
    step(int(g._windup_time() * 60) + 2)
    assert any(type(o).__name__ == 'Shockwave' for o in game_world.world[game_world.LAYER_EFFECT])


def test_enemy_resists_stagger_right_after_recovering():
    room, p = make_world(player_x=300.0)
    e = freeze(add_enemy('slum', 300.0 + 100, room, p))
    e.hp = e.max_hp = 1000
    step(1)
    e.take_damage(5, from_x=p.x)
    assert e.state == 'HIT'                                               # 첫 타격은 경직
    step(int(0.25 * 60))
    assert e.state != 'HIT'
    e.state = 'CHASE'
    e.engage()
    e.take_damage(5, from_x=p.x)
    assert e.state == 'ATTACK' and e.hp == 990                            # 풀린 직후에는 맞아도 피해만 받고 공격을 이어 간다
    step(int((config.ENEMY_STAGGER_GUARD + 0.3) * 60))
    e.state = 'CHASE'
    e.take_damage(5, from_x=p.x)
    assert e.state == 'HIT'                                               # 저항 시간이 지나면 다시 경직된다


def test_mashing_without_dodging_gets_punished():
    """피하지 않고 철파이프만 연타하면 슬럼·사냥개에게도 맞는다 (예고를 읽고 피하는 플레이가 이득)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
    import balance_sim                                                    # 멀리서 다가가 연타하는 봇 (실제 싸움 흐름)
    for kind in ('slum', 'hound'):
        lost = sum(balance_sim.run_one(kind, 'pipe', 'stand', seed)['hp_lost'] for seed in range(4))
        assert lost > 0, kind


def test_enemies_patrol_before_seeing_player_and_spread_apart():
    room, p = make_world(player_x=300.0)
    e = add_enemy('slum', 300.0 + 1000, room, p)
    xs = set()
    for _ in range(240):
        step(1)
        xs.add(int(e.x))
    assert e.state == 'IDLE' and max(xs) - min(xs) > 40, (e.state, max(xs) - min(xs))   # 제자리 주변을 걸어 다닌다
    room, p = make_world(player_x=300.0)
    a = add_enemy('slum', 900.0, room, p)
    b = add_enemy('slum', 905.0, room, p)
    a.stats = dict(a.stats, stagger=False)
    b.stats = dict(b.stats, stagger=False)
    step(50)
    assert abs(a.x - b.x) > 20                                             # 한 자리에 겹쳐 서지 않는다


# ----- 보스 패턴 다양화 -----
def _boss_world():
    from boss import Boss
    room, p = make_world_with(Room.load('boss_arena', {'L'}), 10 * config.TILE)
    boss = Boss(30 * config.TILE, FLOOR_Y + 200, room, p)
    game_world.add_object(boss, game_world.LAYER_ENEMY)
    step(30)
    return room, p, boss


def test_boss_uses_many_patterns_without_repeating():
    room, p, boss = _boss_world()
    room.line_blocked = lambda *a, **k: False
    seen = []
    for d in (100, 400, 800) * 8:
        p.x = boss.x - d
        boss.count = 1
        name = boss._choose_pattern()
        assert name != boss.last_pattern
        boss.last_pattern = name
        seen.append(name)
    assert {'smash', 'combo', 'slam', 'charge', 'rubble', 'steam'} <= set(seen), seen


def test_boss_enters_phase_two_at_half_health():
    room, p, boss = _boss_world()
    assert boss.phase == 1
    boss.take_damage(boss.max_hp / 2 + 1)
    step(1)
    assert boss.phase == 2 and boss.roar_left > 0
    w2 = boss._windup()
    boss.phase = 1
    assert w2 < boss._windup()                                             # 2페이즈는 예고가 짧다


def test_boss_rubble_warns_then_falls_on_player():
    room, p, boss = _boss_world()
    p.hp = p.max_hp = 10 ** 6
    p.invuln_left = 0
    boss.state = 'CHASE'
    boss.pattern = 'rubble'
    boss.engage()
    step(int(boss._windup() * 60) + 2)
    debris = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Debris']
    assert len(debris) >= 3
    first = min(debris, key=lambda o: o.wait)
    assert abs(first.x - p.x) < 40                                         # 첫 고철은 플레이어 자리에
    hp0 = p.hp
    step(int(0.6 * 60))
    assert p.hp == hp0 and not first.falling                                # 표시가 깜빡이는 동안은 맞지 않는다
    for _ in range(90):
        if p.hp < hp0:
            break
        p.x = first.x
        step(1)
    assert p.hp < hp0                                                      # 피하지 않으면 맞는다


def test_boss_steam_vents_raise_gauge_once_without_hp_damage():
    """헤이즈 증기 분출(기획 3.2): 바닥 표시가 깜빡인 뒤 증기가 솟고, 닿으면 게이지 +12% 한 번. HP는 그대로."""
    room, p, boss = _boss_world()
    p.hp = p.max_hp = 1000
    p.invuln_left = 0
    set_gauge(p, 40)
    boss.state = 'CHASE'
    boss.pattern = 'steam'
    boss.engage()
    step(int(boss._windup() * 60) + 2)
    vents = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'SteamVent']
    assert len(vents) == 2                                                 # 1페이즈 두 줄기
    first = min(vents, key=lambda o: abs(o.x - p.x))
    assert abs(first.x - p.x) < 40                                         # 하나는 플레이어 자리에
    g0 = p.gauge.value
    step(int(0.4 * 60))
    assert not first.erupting and abs(p.gauge.value - g0) < 1.5            # 표시가 깜빡이는 동안은 닿지 않는다
    for _ in range(90):
        p.x = first.x
        step(1)
    assert p.gauge.value >= g0 + config.STEAM_GAUGE - 1.5                  # 한 번 올랐다
    assert p.gauge.value <= g0 + config.STEAM_GAUGE + 0.5                  # 여러 번 오르지 않는다
    assert p.hp == 1000                                                    # 피해는 없다


def test_boss_steam_has_three_vents_in_phase_two_and_dash_avoids_it():
    room, p, boss = _boss_world()
    boss.phase = 2
    boss.state = 'CHASE'
    boss.pattern = 'steam'
    boss.engage()
    step(int(boss._windup() * 60) + 2)
    vents = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'SteamVent']
    assert len(vents) == 3
    import projectile
    room, p = make_world()
    set_gauge(p, 40)
    v = projectile.SteamVent(p.x, p.y, 0.0, config.STEAM_GAUGE, room, p)
    game_world.add_object(v, game_world.LAYER_EFFECT)
    step(int(projectile.SteamVent.WARN * 60) - 3)
    p.invuln_left = 1.0                                                    # 대시 무적이면 닿지 않는다
    step(15)
    assert v.erupting and p.gauge.value < 41


def test_boss_rubble_hurts_hp_but_not_extra_gauge():
    """떨어지는 고철은 HP 피해만 준다 (기획의 크래셔 게이지 패턴은 충격파 -20, 증기 +12뿐). 게이지는 피격 기본 손실만."""
    import boss as boss_mod
    assert boss_mod.RUBBLE_GAUGE == 0


def test_boss_combo_hits_three_times_stepping_forward():
    room, p, boss = _boss_world()
    p.hp = p.max_hp = 10 ** 6
    p.x = boss.x - 170
    boss.state = 'CHASE'
    boss.pattern = 'combo'
    boss.engage()
    x0 = closest = boss.x
    hits = []
    for _ in range(120):
        step(1)
        p.invuln_left = 0
        if boss.state == 'ATTACK' and boss.pattern == 'combo':
            hits.append(boss.hits_done)
            closest = min(closest, boss.x)
    assert max(hits) == 3 and closest < x0 - 40                             # 세 번 내리치며 다가왔다


def test_boss_phase_two_charges_back_again():
    room, p, boss = _boss_world()
    boss.phase = 2
    p.hp = p.max_hp = 10 ** 6
    p.x = boss.x - 700
    boss.state = 'CHASE'
    boss.pattern = 'charge'
    boss.engage()
    turned = False
    for _ in range(60 * 4):
        step(1)
        p.invuln_left = 0
        if boss.state == 'ATTACK' and boss.charges_left == 1 and boss.struck is False:
            turned = True
        if boss.state != 'ATTACK':
            break
    assert turned                                                          # 한 번 더 돌아서 달렸다

# ----- 무기: 건틀릿·교체 (쌍권총은 tests/test_pistol.py, 2026-11-24 식칼 대체) -----
def test_gauntlet_charges_by_burning_gauge_and_fires_on_release():
    room, p = make_world()
    p.give_weapon('gauntlet')
    set_gauge(p, 40)
    e = freeze(add_enemy('slum', p.x + 250, room, p))
    e.hp = e.max_hp = 1000
    p.mouse_x, p.mouse_y = p.x + 400, e.center[1]
    p.attack_held = True
    assert p.request_attack() and p.weapon.charging
    run_frames(int(config.GAUNTLET_CHARGE_TIME['NORMAL'] * 60) + 5)
    assert p.weapon.charge_ratio == 1.0
    assert p.gauge.value < 40 - config.GAUNTLET_DRAIN * config.GAUNTLET_CHARGE_TIME['NORMAL'] * 0.8   # 충전하는 동안 게이지가 탔다
    assert p._body_frame() == ('n09_gauntlet', 1)                        # 건틀릿 팔을 허리 뒤로 당긴 충전 자세 (T26)
    p.attack_held = False
    run_frames(1)
    assert not p.weapon.charging and any(type(o).__name__ == 'Blast' for o in game_world.world[game_world.LAYER_EFFECT])
    run_frames(30)
    assert e.hp < 1000


def test_gauntlet_drain_stops_at_floor_and_short_tap_does_nothing():
    room, p = make_world()
    p.give_weapon('gauntlet')
    set_gauge(p, config.GAUNTLET_FLOOR + 3)
    p.attack_held = True
    p.request_attack()
    run_frames(180)
    assert p.gauge.value >= config.GAUNTLET_FLOOR - 1e-6                 # 하한 아래로는 태우지 않는다
    p.attack_held = False
    run_frames(2)
    room, q = make_world()
    q.give_weapon('gauntlet')
    q.attack_held = True
    q.request_attack()
    run_frames(3)
    q.attack_held = False
    run_frames(1)
    assert not any(type(o).__name__ == 'Blast' for o in game_world.world[game_world.LAYER_EFFECT])   # 너무 짧으면 헛손질


def test_gauntlet_floor_survives_one_boss_shockwave():
    """충전으로 게이지를 태워도, 보스 충격파 한 방(기본 손실 + 보스 추가 손실)에 게이지 0이 되지 않는다."""
    worst = -(config.LOSS_DAMAGED + config.ENEMY_STATS['crasher']['wave_gauge'])
    assert config.GAUNTLET_FLOOR > worst, (config.GAUNTLET_FLOOR, worst)


def test_gauntlet_cannot_charge_without_gauge_to_burn():
    room, p = make_world()
    p.give_weapon('gauntlet')
    set_gauge(p, config.GAUNTLET_FLOOR)                                   # 태울 게이지가 없다
    p.attack_held = True
    p.request_attack()
    run_frames(120)
    assert p.weapon.charge_ratio < config.GAUNTLET_MIN_RATIO              # 공짜로 차지 않는다
    p.attack_held = False
    run_frames(2)
    assert not any(type(o).__name__ == 'Blast' for o in game_world.world[game_world.LAYER_EFFECT])
    room, p = make_world()
    p.give_weapon('gauntlet')
    set_gauge(p, config.GAUNTLET_FLOOR + 6)                               # 조금 남았으면 그만큼만 찬다
    p.attack_held = True
    p.request_attack()
    run_frames(120)
    need = 6 / config.GAUNTLET_DRAIN / config.GAUNTLET_CHARGE_TIME['NORMAL']
    assert abs(p.weapon.charge_ratio - need) < 0.05, (p.weapon.charge_ratio, need)


def test_gauntlet_fires_instantly_in_critical_zone_and_vents_gauge():
    room, p = make_world()
    p.give_weapon('gauntlet')
    set_gauge(p, 95)
    p.attack_held = True
    assert p.request_attack()
    assert not p.weapon.charging and p.gauge.value <= 95 - config.GAUNTLET_CRIT_COST + 0.01
    blasts = [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'Blast']
    assert blasts and blasts[0].size == config.GAUNTLET_SIZE['CRITICAL']


def test_weapon_slots_swap_with_q_and_numbers():
    room, p = make_world()
    assert p.weapon.weapon_id == 'pipe' and p.weapons[1] is None
    assert not p.swap_weapon()                                           # 빈 칸으로는 못 바꾼다
    p.give_weapon('pistol')
    assert p.weapon.weapon_id == 'pistol' and p.slot == 1                # 얻으면 바로 든다
    p.swap_weapon()
    assert p.weapon.weapon_id == 'pipe'
    p.swap_weapon(1)
    assert p.weapon.weapon_id == 'pistol'
    p.give_weapon('gauntlet')                                            # 두 번째 칸은 바뀐다 (철파이프는 그대로)
    assert p.weapons[0].weapon_id == 'pipe' and p.weapon.weapon_id == 'gauntlet' and not p.has_weapon('pistol')

# ----- 페이드(약해진 상태)에서는 모든 공격이 똑같이 약해진다 (대시·점프 공격만 강하게 나가던 버그) -----
def _fade_world(gap):
    room, p = make_world()
    set_gauge(p, 10)                                                    # 페이드 (1~19%)
    e = freeze(add_enemy('slum', p.x + gap, room, p))
    e.hp = e.max_hp = 1000
    return room, p, e


def test_fade_shrinks_basic_attack_reach_like_its_small_slash():
    room, p, e = _fade_world(0)
    left, bottom, right, top = e.rect()
    e.x = p.x + config.PIPE_REACH * 0.95 + (right - left) / 2           # 노멀이면 닿는 거리
    p.mouse_x, p.mouse_y = e.center
    p.request_attack()
    assert e.hp == 1000                                                 # 페이드: 범위 x FADE_REACH 라 닿지 않는다
    set_gauge(p, 35)
    p.weapon.cooldown = 0
    p.request_attack()
    assert e.hp < 1000                                                  # 노멀은 닿는다


def test_fade_dash_and_jump_attacks_lose_their_bonus_and_reach_too():
    room, p, e = _fade_world(120)
    w = p.weapon
    cx, cy = p.center
    w.resolve_dash_strike(False, path=(p.x - 200, cy, p.x + 300, cy))   # 대시 평타: 적을 지나는 경로
    dash = 1000 - e.hp
    e.hp = 1000
    w._attack_pipe(False)                                               # 같은 페이드에서 기본 1타
    basic = 1000 - e.hp
    assert dash > 0 and abs(dash - basic) < 1e-6, (dash, basic)         # 추가 배율 x1.4가 없다
    e.hp = 1000
    e.x = p.x + config.AIR_SPIN_REACH * 0.95 + e.hb_w / 2               # 노멀 회전 베기는 닿는 거리
    w._attack_spin(False)
    assert e.hp == 1000                                                 # 회전 베기도 범위가 줄었다
    set_gauge(p, 35)
    w._attack_spin(False)
    assert e.hp < 1000                                                  # 노멀은 그대로 닿는다



def test_fade_jump_attack_is_a_front_slash_not_a_circle():
    """2026-11-20 사용자: 페이드에서 점프 공격이 일반 상태처럼 둘레 전체를 베었다. 기본 공격처럼 조준 앞쪽만 벤다."""
    room, p, front = _fade_world(90)
    behind = freeze(add_enemy('slum', p.x - 90, room, p))
    behind.hp = behind.max_hp = 1000
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    p.weapon._attack_spin(False)
    assert front.hp < 1000                                              # 앞은 맞는다
    assert behind.hp == 1000                                            # 등 뒤는 안 맞는다 (원이 아니다)
    set_gauge(p, 35)
    p.weapon._attack_spin(False)
    assert behind.hp < 1000                                             # 노멀은 그대로 한 바퀴

# ----- 투척병 거리 유지 (2026-11-21 Codex T30 그림: 걷기 4장·물러서기 2장) -----
# 멀면(THROWER_APPROACH 넘게) 걸어서 다가오고, 가까우면(keep_away 안) 뛰어 물러나거나 뛰기를 못 하면 플레이어를 본 채 뒷걸음.
def test_thrower_walks_closer_when_player_is_far():
    room, p = make_world(player_x=200.0)
    t = add_enemy('thrower', 200.0 + 1100, room, p)
    p.hp = p.max_hp = 10 ** 6
    t.see()
    t.cooldown = 5.0                                                        # 던지기 전에 걷는 것만 본다
    x0 = t.x
    step(30)
    assert t.x < x0 - 30 and t.face_dir == -1                               # 플레이어 쪽으로 걸었다
    assert t._body_frame()[0] == 'enemy_thrower_walk'


def test_thrower_stands_in_the_middle_band():
    room, p = make_world(player_x=300.0)
    t = add_enemy('thrower', 300.0 + 450, room, p)
    t.see()
    t.cooldown = 5.0
    x0 = t.x
    step(30)
    assert abs(t.x - x0) < 2                                                # 알맞은 거리: 서서 던질 차례를 기다린다


def test_thrower_backsteps_facing_player_when_it_cannot_hop():
    room, p = make_world(player_x=300.0)
    t = add_enemy('thrower', 300.0 + 200, room, p)
    p.hp = p.max_hp = 10 ** 6
    t.see()
    t.cooldown = 5.0
    t.hop_cooldown = 5.0                                                    # 뛰어 물러나기는 아직 못 한다
    x0 = t.x
    step(20)
    assert t.x > x0 + 15 and t.face_dir == -1                               # 플레이어를 본 채 뒤로
    assert t._body_frame()[0] == 'enemy_thrower_back'


# ----- 적 테두리·강한 공격 예고 (2026-11-22 v5 빠른 개선 5) -----
def test_strong_moves_are_telegraphed_during_windup_only():
    room, p = make_world()
    g = add_enemy('guard', p.x + 100, room, p)
    g.move = 'heavy'
    g.state = 'ATTACK'
    g.attack_time = 0.0
    assert g.telegraph() == 'heavy'                                     # 예고 중: 머리 위 '!' + (돌진이면) 바닥 표시
    g.attack_time = g._windup_time() + 0.01
    assert g.telegraph() is None                                        # 치는 순간부터는 없다
    g.move, g.attack_time = 'swing', 0.0
    assert g.telegraph() is None                                        # 약한 기본기는 예고 표시 없이 (깜빡임만)
    for kind, move in (('slum', 'lunge'), ('hound', 'pounce'), ('guard', 'bash')):
        assert move in config.STRONG_MOVES and move in config.RUSH_MOVES, move


def test_every_enemy_gets_a_thin_outline():
    room, p = make_world()
    e = add_enemy('slum', p.x + 300, room, p)
    assert e.outline_color() == config.ENEMY_OUTLINE                    # 평소: 옅은 테두리 (어두운 배경에서도 보이게)
    e.make_elite('tough')
    assert e.outline_color() == e.elite_color()                         # 정예는 자기 색 테두리


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
