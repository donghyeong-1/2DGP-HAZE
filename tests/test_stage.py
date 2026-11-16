"""스테이지 테스트: 방 잠금·클리어, 4방향 이동, 황금방·정비방·보스방, 아이템, E 강화, 카메라 (창 없이 실행).
실행: python tests/test_stage.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import camera  # noqa: E402
import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import items  # noqa: E402
from enemy import Enemy  # noqa: E402
from player import Player  # noqa: E402
from stage import Stage  # noqa: E402

DT = 1 / 60
T = config.TILE
FLOOR_Y = float(config.SCREEN_H - 16 * T)   # 18줄 방의 바닥 윗면


def make_stage(seed=1):
    game_world.clear()
    effects.reset()
    player = Player(0, 0, None)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    stage = Stage(player, seed=seed)
    stage.start()
    for _ in range(40):
        game_world.update(DT)
    return stage, player


def kill_all():
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        e.take_damage(10 ** 6)


def clear_here(stage):
    kill_all()
    stage.update()


def at_door(stage, p, side):
    """플레이어를 그 문을 막 지나는 위치에 놓고 stage.update로 이동을 일으킨다."""
    room = stage.room
    x, y = room.door_center(side)
    if side == 'R':
        p.x, p.y = room.width - config.PLAYER_HB_W / 2 - 1, y
    elif side == 'L':
        p.x, p.y = config.PLAYER_HB_W / 2 + 1, y
    elif side == 'U':
        p.x, p.y = x, room.height - config.PLAYER_HB_H - 2
    else:
        p.x, p.y = x, 5
    stage.update()


def go(stage, p, side):
    """현재 방을 클리어한 뒤 그쪽 문으로 나간다."""
    if stage.room.locked:
        clear_here(stage)
    at_door(stage, p, side)


def goto(stage, p, path):
    for side in path:
        go(stage, p, side)


# ----- 방 잠금·클리어·이동 -----
def test_start_room_is_safe_and_offers_two_ways():
    stage, p = make_stage()
    assert stage.coord == (0, 0) and stage.enemy_count() == 0 and not stage.room.locked
    assert stage.room.links == {'R', 'U'}


def test_combat_room_locks_until_cleared_then_opens():
    stage, p = make_stage()
    go(stage, p, 'R')
    assert stage.coord == (1, 0) and stage.room.locked and stage.enemy_count() == 6
    assert stage.room.tile_at(stage.room.cols - 1, stage.room.nrows - 3) == '#'   # 잠긴 문은 벽이다
    notices = []
    stage.on_clear = lambda s: notices.append(s.coord)
    kill_all()
    stage.update()
    assert not stage.room.locked and notices == [(1, 0)] and (1, 0) in stage.cleared
    assert stage.room.tile_at(stage.room.cols - 1, stage.room.nrows - 3) == 'R'  # 열린 문은 지나갈 수 있다


def test_cannot_leave_locked_room():
    stage, p = make_stage()
    go(stage, p, 'R')                       # 허브: 잠김
    at_door(stage, p, 'R')
    assert stage.coord == (1, 0)


def test_four_way_movement_changes_rooms_in_the_right_direction():
    stage, p = make_stage()
    go(stage, p, 'R')                       # (1,0) 허브
    clear_here(stage)
    assert stage.room.links == {'L', 'R', 'U', 'D'}   # 사방으로 이어진 허브
    at_door(stage, p, 'U')
    assert stage.coord == (1, 1)            # 위 문 -> 위 방
    assert abs(p.x - stage.room.door_center("D")[0]) <= 4 * T          # 아래 구멍 근처 바닥에 선다
    clear_here(stage)
    at_door(stage, p, 'D')
    assert stage.coord == (1, 0)            # 아래 문 -> 다시 허브
    at_door(stage, p, 'D')
    assert stage.coord == (1, -1)           # 허브 아래 -> 정비방
    at_door(stage, p, 'U')
    assert stage.coord == (1, 0)


def test_entering_through_up_door_lands_beside_the_hole_without_falling_back():
    stage, p = make_stage()
    go(stage, p, 'U')                       # 시작 홀 위 문 -> 우물 방(0,1)의 바닥 구멍으로
    assert stage.coord == (0, 1)
    for _ in range(120):
        game_world.update(DT)
        stage.update()
    assert stage.coord == (0, 1)            # 바로 다시 구멍으로 빠져 돌아가지 않는다


def test_doors_show_what_lies_beyond():
    stage, p = make_stage()
    go(stage, p, 'R')
    clear_here(stage)
    assert stage.room.door_hints.get('D') == 'shop'
    go(stage, p, 'U')
    clear_here(stage)
    assert stage.room.door_hints.get('U') == 'gold'


def test_cleared_room_stays_empty_and_unlocked_when_revisited():
    stage, p = make_stage()
    go(stage, p, 'R')
    clear_here(stage)
    at_door(stage, p, 'L')
    assert stage.coord == (0, 0)
    at_door(stage, p, 'R')
    assert stage.coord == (1, 0) and stage.enemy_count() == 0 and not stage.room.locked


def test_minimap_shows_special_rooms_in_advance_and_visited_rooms():
    stage, p = make_stage()
    cells = {c: (s, k) for c, s, k, _ in stage.minimap_cells()}
    assert cells[(0, 0)] == ('current', 'start')
    go(stage, p, 'R')
    clear_here(stage)
    cells = {c: (s, k) for c, s, k, _ in stage.minimap_cells()}
    assert cells[(1, -1)][1] == 'shop'      # 문 너머 정비방은 미리 보인다
    assert cells[(1, 0)][0] == 'current'


# ----- 황금방 -----
def to_gold(stage, p):
    goto(stage, p, ['R', 'U', 'U'])         # 허브 -> 교차로 -> 황금방
    assert stage.coord == (1, 2)


def test_gold_room_gives_one_item_free_and_removes_the_others():
    stage, p = make_stage()
    to_gold(stage, p)
    assert len(stage.pedestals) == 3 and not stage.room.locked and stage.enemy_count() == 0
    ped = stage.pedestals[0]
    p.x, p.y = ped.x, ped.y
    msgs = []
    stage.on_message = msgs.append
    assert stage.interact() and len(p.items) == 1 and msgs
    assert all(d.gone for d in stage.pedestals)         # 하나만 얻는다
    p.x, p.y = stage.pedestals[1].x, stage.pedestals[1].y
    assert not stage.interact() and len(p.items) == 1


def test_gold_room_remembers_choice_after_leaving():
    stage, p = make_stage()
    to_gold(stage, p)
    stock = list(stage.state[stage.coord]['stock'])
    ped = stage.pedestals[1]
    p.x, p.y = ped.x, ped.y
    stage.interact()
    at_door(stage, p, 'D')
    assert stage.coord == (1, 1)
    at_door(stage, p, 'U')
    assert stage.coord == (1, 2)
    assert [d.item_id for d in stage.pedestals] == stock and all(d.gone for d in stage.pedestals)


# ----- 정비방 -----
def to_shop(stage, p):
    goto(stage, p, ['R'])
    clear_here(stage)
    at_door(stage, p, 'D')
    assert stage.coord == (1, -1)


def test_shop_sells_for_shards_and_marks_sold_out():
    stage, p = make_stage()
    to_shop(stage, p)
    assert len(stage.pedestals) == 4
    ped = stage.pedestals[0]
    p.x, p.y = ped.x, ped.y
    msgs = []
    stage.on_message = msgs.append
    p.shards = 0
    p.hp = 10                                                   # 회복약이 팔려도 사려는 것이 한계가 아니게
    assert not stage.interact() and '모자라' in msgs[-1]        # 조각이 없으면 못 산다
    p.shards = ped.price + 2
    assert stage.interact()
    assert p.shards == 2 and ped.gone                           # 값을 치렀고 품절
    assert not stage.interact()


# ----- 보스 -----
def to_boss(stage, p):
    goto(stage, p, ['R', 'R', 'R', 'R', 'R'])
    assert stage.coord == (5, 0)


def test_boss_room_spawns_boss_and_finishing_it_ends_the_stage():
    stage, p = make_stage()
    to_boss(stage, p)
    assert stage.boss is not None and stage.enemy_count() == 1 and stage.room.locked
    stage.boss.take_damage(10 ** 6)
    stage.update()
    assert (5, 0) in stage.cleared and not stage.finished
    for _ in range(200):
        stage.update()
    assert stage.finished and p.shards >= config.SHARDS_PER_KILL['crasher']


def test_boss_slam_makes_shockwaves_that_cost_gauge():
    stage, p = make_stage()
    to_boss(stage, p)
    boss = stage.boss
    p.invuln_left = 0
    p.x, p.y = boss.x - 600, boss.y
    boss.pattern = 'slam'
    boss.engage()
    g0 = p.gauge.value
    for _ in range(60 * 4):
        game_world.update(DT)
        if p.hp < config.PLAYER_HP:
            break
    assert any(type(o).__name__ == 'Shockwave' for o in game_world.world[game_world.LAYER_EFFECT]) or p.hp < p.max_hp
    assert p.hp < p.max_hp                                       # 충격파에 맞았다
    assert p.gauge.value <= g0 + config.LOSS_DAMAGED - 10        # 게이지가 크게 내려갔다 (-5 와 충격파 -15)


# ----- 아이템 -----
def test_each_item_applies_its_effect():
    stage, p = make_stage()
    g = p.gauge
    cap0, steady0, enh0, dash0 = g.cap, g.decay_interval, g.enhance_cost, p.dash_max
    items.apply(p, 'cap')
    assert g.cap == cap0 + 20
    items.apply(p, 'steady')
    assert g.decay_interval == steady0 + 1.5
    items.apply(p, 'enhance')
    assert g.enhance_cost == enh0 - 5
    items.apply(p, 'dash')
    assert p.dash_max == dash0 + 1
    items.apply(p, 'power')
    assert p.attack_bonus == 1.25
    items.apply(p, 'absorb')
    assert p.kill_bonus == 3
    items.apply(p, 'resist')
    assert abs(p.overload_mult - 0.6) < 1e-9
    hp0 = p.max_hp
    items.apply(p, 'vigor')
    assert p.max_hp == hp0 + 25 and p.hp == p.max_hp
    p.hp = 10
    items.apply(p, 'heal')
    assert p.hp == 50


def test_items_respect_limits():
    stage, p = make_stage()
    p.gauge.cap = config.GAUGE_CAP_MAX
    assert not items.can_take(p, 'cap')
    p.dash_max = config.DASH_SLOTS_MAX
    assert not items.can_take(p, 'dash')
    p.gauge.enhance_cost = 10
    assert not items.can_take(p, 'enhance')
    assert not items.can_take(p, 'heal')                       # 체력이 가득이면 회복약은 의미가 없다


def test_item_bonuses_change_combat_numbers():
    stage, p = make_stage()
    items.apply(p, 'power')
    items.apply(p, 'absorb')
    e = Enemy('slum', p.x + 100, FLOOR_Y, stage.room, p)
    e.stats = dict(e.stats, speed=0.0, sight=0)
    e.hp = e.max_hp = 1000
    game_world.add_object(e, game_world.LAYER_ENEMY)
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    assert e.max_hp - e.hp == config.PIPE_DAMAGE * 1.25 * p.gauge.zone_multipliers()['attack']
    e.hp = 1
    p.weapon.cooldown = 0
    g0 = p.gauge.value
    p.request_attack()
    assert p.gauge.value - g0 >= config.GAIN_HIT + config.GAIN_KILL + 3 - 1     # 처치 보너스 +3 (시간 감소 오차 1)


# ----- 카메라 -----
def test_camera_follows_player_inside_big_room_and_stays_in_bounds():
    stage, p = make_stage()
    go(stage, p, 'R')                               # 허브: 48x27 (화면보다 큼)
    room = stage.room
    assert room.width > config.SCREEN_W and room.height > config.SCREEN_H
    p.x, p.y = room.width - 200, 300
    p.mouse_x, p.mouse_y = p.x, p.y
    camera.snap(p, room)
    assert camera.x == room.width - config.SCREEN_W            # 오른쪽 끝에서 멈춘다
    p.x = 400
    for _ in range(120):
        camera.update(p, room, DT)
    assert 0 <= camera.x <= room.width - config.SCREEN_W and camera.x < 400
    ox, oy = camera.offset()
    assert isinstance(ox, int) and isinstance(oy, int)         # 정수 픽셀
    wx, wy = camera.to_world(100, 200)
    assert camera.to_screen(wx, wy) == (100, 200)


def test_camera_centers_room_smaller_than_screen():
    game_world.clear()
    from room import Room
    rows = ['#' * 20] + ['#' + '.' * 18 + '#'] * 10 + ['#' * 20]   # 20x12: 화면보다 작은 방
    room = Room(rows)
    p = Player(300, 200, room)
    camera.snap(p, room)
    assert camera.x == (room.width - config.SCREEN_W) / 2 < 0


# ----- E 강화 (이전 테스트 유지) -----
def test_enhance_costs_gauge_and_arms_one_strike_only():
    """E는 게이지를 쓰고 다음 공격 한 번을 강화 일격으로 만든다. 한 번 휘두르면 준비가 끝난다 (1회성)."""
    stage, p = make_stage()
    p.gauge.value = 60.0
    p.gauge.zone = p.gauge._zone_of(60.0)
    assert p.request_enhance() and p.gauge.enhanced
    assert p.gauge.value == 60.0 - config.ENHANCE_COST
    assert not p.request_enhance()                              # 준비 중에는 다시 못 쓴다
    e = Enemy('slum', p.x + 100, FLOOR_Y, stage.room, p)
    e.stats = dict(e.stats, speed=0.0, sight=0)
    e.hp = e.max_hp = 1000
    game_world.add_object(e, game_world.LAYER_ENEMY)
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    mult = p.gauge.zone_multipliers()['attack']
    p.request_attack()
    assert e.max_hp - e.hp == config.PIPE_DAMAGE * config.ENHANCE_DAMAGE_MULT * mult      # 강화 일격
    assert not p.gauge.enhanced                                 # 한 번 쓰면 사라진다
    assert p.weapon.last_kind == 'pipe' and p.weapon.last_enhanced     # 기본 공격에 얹힌 강화 일격
    for _ in range(60):
        game_world.update(DT)                                   # 강화 일격의 추가 타격이 끝난 뒤
    hp1 = e.hp
    p.weapon.cooldown = 0
    p.request_attack()
    assert hp1 - e.hp == config.PIPE_DAMAGE * mult              # 다음 공격은 보통 공격이다
    assert p.weapon.last_kind == 'pipe' and not p.weapon.last_enhanced


def test_enhance_expires_if_unused():
    stage, p = make_stage()
    p.gauge.value = 60.0
    p.gauge.zone = p.gauge._zone_of(60.0)
    p.request_enhance()
    p.gauge.tick(config.ENHANCE_TIME + 0.1)
    assert not p.gauge.enhanced                                 # 오래 안 쓰면 준비가 풀린다
    p.gauge.value = 60.0
    p.gauge.zone = p.gauge._zone_of(60.0)
    assert p.request_enhance()                                  # 다시 준비할 수 있다


def test_enhance_refused_when_gauge_too_low():
    stage, p = make_stage()
    p.gauge.value = 29.0
    p.gauge.zone = p.gauge._zone_of(29.0)
    assert not p.request_enhance() and p.gauge.value == 29.0


def test_enhanced_strike_blasts_around_every_enemy_it_hits():
    stage, p = make_stage()
    p.gauge.value = 60.0
    p.gauge.zone = p.gauge._zone_of(60.0)
    p.request_enhance()
    a = Enemy('slum', p.x + 100, FLOOR_Y, stage.room, p)
    b = Enemy('slum', p.x + 280, FLOOR_Y, stage.room, p)  # 강화 사거리(225) 밖, 폭발 반경(190) 안
    for e in (a, b):
        e.stats = dict(e.stats, speed=0.0, sight=0)
        e.hp = e.max_hp = 1000
        game_world.add_object(e, game_world.LAYER_ENEMY)
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    assert a.hp < a.max_hp                                      # 죽이지 않아도 맞은 적 주위에 폭발이 퍼진다
    assert b.hp == b.max_hp - config.ENHANCE_BLAST_DAMAGE


def test_kill_drops_shards():
    stage, p = make_stage()
    go(stage, p, 'R')
    n = stage.enemy_count()
    p.shards = 0
    kill_all()
    assert p.shards >= n                                          # 적마다 1~2조각


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
