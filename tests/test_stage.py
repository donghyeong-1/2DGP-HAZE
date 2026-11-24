"""스테이지 테스트: 방 잠금·클리어, 4방향 이동, 황금방·정비방·보스방, 아이템, E 강화, 카메라 (창 없이 실행).
실행: python tests/test_stage.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import camera  # noqa: E402
import config  # noqa: E402
config.PROCEDURAL_MAPS = False   # 손으로 짠 배치(data/stages)의 좌표로 방 로직을 검사한다. 생성 배치는 test_mapgen.py
import effects  # noqa: E402
import game_world  # noqa: E402
import items  # noqa: E402
from enemy import Enemy  # noqa: E402
from player import Player  # noqa: E402
from stage import Stage  # noqa: E402

DT = 1 / 60
T = config.TILE
FLOOR_Y = float(config.SCREEN_H - 16 * T)   # 18줄 방의 바닥 윗면


def make_stage(seed=1, name='stage1'):
    game_world.clear()
    effects.reset()
    player = Player(0, 0, None)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    stage = Stage(player, seed=seed, name=name)
    stage.start()
    for _ in range(40):
        game_world.update(DT)
    return stage, player


def kill_all():
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        e.take_damage(10 ** 6)


def clear_here(stage):
    for _ in range(400):                   # v8 물결 전투: 마지막 물결까지 쓰러뜨려야 방이 열린다
        kill_all()
        stage.update()
        if not stage.room.locked:
            return


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
    assert stage.coord == (1, 0) and stage.room.locked and stage.wave_enemies == sum(      # v8: 물결로 나뉘어도 적의 수는 그대로
        config.PACK_SIZE.get(k, 1) for k in stage.layout[(1, 0)]['enemies'])      # 쥐 떼는 한 칸에 여러 마리
    assert stage.room.tile_at(stage.room.cols - 1, stage.room.nrows - 3) == '#'   # 잠긴 문은 벽이다
    notices = []
    stage.on_clear = lambda s: notices.append(s.coord)
    clear_here(stage)                      # v8 물결 전투: 마지막 물결까지
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
def clear_all_combat(stage):
    """황금방은 그 구역의 전투방을 모두 클리어해야 열린다: 테스트에서는 전부 클리어한 것으로 둔다."""
    stage.cleared |= {c for c in stage.layout if stage.type_of(c) == 'combat'}


def to_gold(stage, p):
    clear_all_combat(stage)
    goto(stage, p, ['R', 'U', 'U'])         # 허브 -> 교차로 -> 황금방
    assert stage.coord == (1, 2)


def test_gold_room_stays_shut_until_every_combat_room_is_cleared():
    stage, p = make_stage()
    msgs = []
    stage.on_message = msgs.append
    goto(stage, p, ['R', 'U'])                                      # 허브를 클리어하고 교차로에 막 들어옴
    assert stage.coord == (1, 1)
    combat = [c for c in stage.layout if stage.type_of(c) == 'combat']
    assert stage.gold_rooms_left() == len(combat) - 1
    assert stage.room.door_texts.get('U', '').endswith(f'{stage.gold_rooms_left()}')   # 문에 남은 방 수
    clear_here(stage)
    at_door(stage, p, 'U')
    assert stage.coord == (1, 1) and any('황금방' in m for m in msgs)  # 들어가지 못하고 이유가 뜬다
    stage.cleared |= set(combat) - {stage.coord}                    # 나머지를 깨고
    stage.cleared.discard(stage.coord)
    stage.room.locked = True
    clear_here(stage)                                               # 마지막 방을 클리어하는 순간
    assert stage.gold_rooms_left() == 0 and any('열렸' in m for m in msgs)
    assert 'U' not in stage.room.door_texts                          # 문 글자가 원래대로
    at_door(stage, p, 'U')
    assert stage.coord == (1, 2)


def test_gate_and_boss_rooms_do_not_count_for_the_gold_room():
    stage, p = make_stage()
    clear_all_combat(stage)
    assert stage.gold_rooms_left() == 0 and (5, 0) not in stage.cleared   # 관문은 깨지 않아도 된다


# ----- 균열방 (체력을 내고 들어간다) -----
def to_rift_door(stage, p):
    """스테이지 1: 허브 -> 교차로 -> 아레나 -> 홀, 홀의 오른쪽 문 너머가 균열방."""
    goto(stage, p, ['R', 'U', 'R', 'R'])
    assert stage.coord == (3, 1)
    clear_here(stage)


def test_every_stage_has_one_rift_room():
    for name in ('stage1', 'stage2', 'stage3'):
        stage, p = make_stage(name=name)
        assert sum(1 for c in stage.layout if stage.type_of(c) == 'rift') == 1, name


def test_rift_room_takes_health_once_on_entry():
    stage, p = make_stage()
    to_rift_door(stage, p)
    assert stage.room.door_hints.get('R') == 'rift'
    cost = stage.rift_cost()
    assert cost == -(-p.max_hp * config.RIFT_HP_COST // 100)          # 최대 체력의 15% (올림)
    hp0 = p.hp
    at_door(stage, p, 'R')
    assert stage.type_of(stage.coord) == 'rift' and p.hp == hp0 - cost
    at_door(stage, p, 'L')
    hp1 = p.hp
    at_door(stage, p, 'R')
    assert stage.type_of(stage.coord) == 'rift' and p.hp == hp1      # 두 번째부터는 내지 않는다


def test_rift_room_refuses_entry_when_health_is_too_low():
    stage, p = make_stage()
    to_rift_door(stage, p)
    msgs = []
    stage.on_message = msgs.append
    p.hp = stage.rift_cost()                                         # 내면 죽는다
    at_door(stage, p, 'R')
    assert stage.coord == (3, 1) and p.hp == stage.rift_cost() and any('체력' in m for m in msgs)


def test_rift_room_offers_double_upgrade_or_fury_and_one_choice():
    stage, p = make_stage()
    to_rift_door(stage, p)
    at_door(stage, p, 'R')
    ids = [d.item_id for d in stage.pedestals]
    assert len(ids) == 2 and 'fury' in ids
    up = next(d for d in stage.pedestals if d.item_id != 'fury')
    assert up.item_id in items.UPGRADES
    p.x, p.y = up.x, up.y
    assert stage.interact() and items.level(p, up.item_id) == 2      # 두 단계 한꺼번에
    assert all(d.gone for d in stage.pedestals)                      # 하나만 고른다
    stage2, q = make_stage()
    to_rift_door(stage2, q)
    at_door(stage2, q, 'R')
    fury = next(d for d in stage2.pedestals if d.item_id == 'fury')
    q.x, q.y = fury.x, fury.y
    a0 = q.attack_bonus
    assert stage2.interact() and abs(q.attack_bonus - a0 - config.RIFT_FURY_ATTACK) < 1e-9


def test_gold_room_gives_one_item_free_and_removes_the_others():
    stage, p = make_stage()
    to_gold(stage, p)
    assert len(stage.pedestals) == 3 and not stage.room.locked and stage.enemy_count() == 0
    assert sum(1 for d in stage.pedestals if d.item_id in items.WEAPON_ITEMS) == 1     # 하나는 늘 무기
    ped = next(d for d in stage.pedestals if d.item_id not in items.WEAPON_ITEMS)
    p.x, p.y = ped.x, ped.y
    msgs = []
    stage.on_message = msgs.append
    assert stage.interact() and len(p.items) == 1 and msgs
    assert all(d.gone for d in stage.pedestals)         # 하나만 얻는다
    other = next(d for d in stage.pedestals if d is not ped)
    p.x, p.y = other.x, other.y
    assert not stage.interact() and len(p.items) == 1


def test_gold_room_weapon_goes_into_second_slot():
    stage, p = make_stage()
    to_gold(stage, p)
    ped = next(d for d in stage.pedestals if d.item_id in items.WEAPON_ITEMS)
    p.x, p.y = ped.x, ped.y
    assert stage.interact()
    assert p.weapons[1] is not None and p.weapon is p.weapons[1] and p.items == []     # 무기 칸에 들어가 바로 든다
    assert p.weapons[1].weapon_id == items.ITEMS[ped.item_id]['weapon']


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


def test_shop_has_three_upgrades_and_first_aid():
    stage, p = make_stage()
    to_shop(stage, p)
    ids = [d.item_id for d in stage.pedestals]
    assert len(ids) == 4 and ids.count('heal') == 1                 # 응급 치료는 늘 있다 (구역 사이 회복이 없으므로)
    assert all(i in items.UPGRADES for i in ids if i != 'heal') and len(set(ids)) == 4


def test_shop_upgrade_price_rises_by_level_and_sells_out_at_level_three():
    stage, p = make_stage()
    to_shop(stage, p)
    ped = next(d for d in stage.pedestals if d.item_id != 'heal')
    p.x, p.y = ped.x, ped.y
    msgs = []
    stage.on_message = msgs.append
    p.shards = 0
    assert not stage.interact() and '부족' in msgs[-1]        # 조각이 없으면 못 산다
    prices = []
    for level in range(1, items.MAX_LEVEL + 1):
        assert not ped.gone and ped.price == items.price(p, ped.item_id)
        prices.append(ped.price)
        p.shards = ped.price + 2
        assert stage.interact()
        assert p.shards == 2 and items.level(p, ped.item_id) == level   # 값을 치르고 한 단계 올랐다
    assert prices[0] < prices[1] < prices[2]                        # 단계가 오를수록 비싸다 (3단계는 크게)
    assert prices[2] >= 2 * prices[0]
    assert ped.gone and not stage.interact()                        # 3단계면 품절


def test_shop_potion_sells_once():
    """v7: 정비방 '물약'은 물약 한 병을 채운다 (예전 응급 치료 체력 +40). 한 번 팔리면 사라진다."""
    import config
    stage, p = make_stage()
    to_shop(stage, p)
    ped = next(d for d in stage.pedestals if d.item_id == 'heal')
    p.x, p.y = ped.x, ped.y
    p.potions, p.shards = 0, 99
    assert stage.interact() and p.potions == 1 and ped.gone
    assert not stage.interact()
    assert config.POTION_MAX >= 1


# ----- 보스 -----
def to_boss(stage, p):
    """스테이지 2: 시작 -> 교차로(오른쪽) -> 허브(위) -> 오른쪽 넷 -> 보스(크래셔)."""
    goto(stage, p, ['R', 'U', 'R', 'R', 'R', 'R'])
    assert stage.coord == (5, 1)


def test_boss_room_spawns_boss_and_finishing_it_ends_the_stage():
    stage, p = make_stage(name='stage2')
    to_boss(stage, p)
    assert stage.boss is not None and stage.enemy_count() == 1 and stage.room.locked
    stage.boss.take_damage(10 ** 6)
    stage.update()
    assert (5, 1) in stage.cleared and not stage.finished
    for _ in range(200):
        stage.update()
    assert stage.finished and p.shards >= config.SHARDS_PER_KILL['crasher']


def test_boss_slam_makes_shockwaves_that_cost_gauge():
    stage, p = make_stage(name='stage2')
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
def test_upgrades_follow_the_design_table_for_three_levels():
    """기획서 3.4 업그레이드 표 (1 -> 2 -> 3단계)."""
    stage, p = make_stage()
    g = p.gauge
    table = {
        'cap':     (lambda: g.cap, [120, 140, 160]),                     # 오버로드 한계 100 -> 160%
        'absorb':  (lambda: config.GAIN_KILL + p.kill_bonus, [10, 12, 14]),   # 처치 +8 -> +14%
        'steady':  (lambda: g.decay_interval, [4.0, 5.0, 6.0]),          # 감소 간격 3 -> 6초
        'enhance': (lambda: g.enhance_cost, [20, 17, 15]),               # E 비용 25 -> 15%
        'resist':  (lambda: round(config.OVERLOAD_DAMAGE_RATIO * p.overload_mult, 3), [0.15, 0.10, 0.05]),   # 폭발 피해 20 -> 5%
        'dash':    (lambda: p.dash_max, [3, 4, 5]),                      # 대시 슬롯 2 -> 5
    }
    for item_id, (read, values) in table.items():
        for lv, want in enumerate(values, 1):
            assert items.can_take(p, item_id)
            items.apply(p, item_id)
            assert items.level(p, item_id) == lv and abs(read() - want) < 1e-9, (item_id, lv, read())
        assert not items.can_take(p, item_id)                       # 3단계가 끝
    import config as cfg
    p.potions = cfg.POTION_MAX
    assert not items.can_take(p, 'heal')                            # v7: 물약이 가득이면 정비방 물약은 못 산다
    p.potions = 0
    items.apply(p, 'heal')
    assert p.potions == 1                                           # v7: 체력 대신 물약 한 병


def test_basic_growth_is_attack_or_health_sharing_three_levels():
    """기본 성장은 공격력 / 최대 체력 중 택1: 둘이 단계 3칸을 함께 쓴다."""
    stage, p = make_stage()
    hp0 = p.max_hp
    items.apply(p, 'power')
    items.apply(p, 'vigor')
    assert abs(p.attack_bonus - (1 + config.GROWTH_ATTACK)) < 1e-9
    assert p.max_hp == hp0 + config.GROWTH_HP and p.hp == p.max_hp
    assert items.level(p, 'power') == items.level(p, 'vigor') == 2
    items.apply(p, 'power')
    assert not items.can_take(p, 'power') and not items.can_take(p, 'vigor')


def test_gold_room_item_counts_toward_the_same_level():
    stage, p = make_stage()
    to_gold(stage, p)
    ped = next(d for d in stage.pedestals if d.item_id not in items.WEAPON_ITEMS)
    p.x, p.y = ped.x, ped.y
    assert stage.interact() and items.level(p, ped.item_id) == 1
    assert items.price(p, ped.item_id) == items.price_at(ped.item_id, 2)   # 정비방에서는 2단계 값


def test_pedestal_text_shows_next_level():
    stage, p = make_stage()
    assert items.describe(p, 'cap').startswith('1단계')
    items.apply(p, 'cap')
    assert items.describe(p, 'cap').startswith('2단계') and '140' in items.describe(p, 'cap')


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
    assert abs(e.max_hp - e.hp - config.PIPE_DAMAGE * (1 + config.GROWTH_ATTACK) * p.gauge.zone_multipliers()['attack']) < 1e-9
    e.hp = 1
    p.weapon.cooldown = 0
    g0 = p.gauge.value
    p.request_attack()
    assert p.gauge.value - g0 >= config.GAIN_HIT + config.GAIN_KILL + 2 - 1     # 흡수 효율 1단계 +2 (시간 감소 오차 1)


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
    p.gauge.value = 50.0
    p.gauge.zone = p.gauge._zone_of(50.0)
    assert p.request_enhance() and p.gauge.enhanced
    assert p.gauge.value == 50.0 - config.ENHANCE_COST
    assert not p.request_enhance() and p.gauge.enhance_level == 1   # 25%: 한 단계 더 쌓으려면 30% 이상이 있어야 (11/19 중첩)
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



# ----- 스테이지 3개와 이어 가기 -----
def test_three_stages_in_order_with_titles():
    import stage as stage_mod
    assert stage_mod.STAGE_ORDER == ('stage1', 'stage2', 'stage3')
    for name, nxt in (('stage1', 'stage2'), ('stage2', 'stage3'), ('stage3', None)):
        s, p = make_stage(name=name)
        assert s.name == name and s.next_name == nxt and s.title           # 구역 이름이 있다
        assert s.coord == s.start_coord and not s.room.locked and s.enemy_count() == 0


def test_stage1_ends_at_gate_fight_without_boss():
    """기획서: 크래셔는 스테이지 2 보스, 아크는 스테이지 3 보스. 스테이지 1은 관문 방의 정예 전투를 이기면 다음 구역으로."""
    stage, p = make_stage()
    kinds = [info.get('type') for info in stage.layout.values()]
    assert 'boss' not in kinds and kinds.count('gate') == 1
    goto(stage, p, ['R', 'R', 'R', 'R', 'R'])
    assert stage.type_of(stage.coord) == 'gate' and stage.boss is None
    assert stage.room.locked and stage.enemy_count() >= 4                   # 정예 무리
    assert {e.kind for e in game_world.world[game_world.LAYER_ENEMY]} & {'guard', 'hound'}
    clear_here(stage)
    for _ in range(200):
        stage.update()
    assert stage.finished


def test_gate_door_is_announced():
    stage, p = make_stage()
    goto(stage, p, ['R', 'R', 'R', 'R'])
    clear_here(stage)
    assert stage.room.door_hints.get('R') == 'gate'


def test_stage_bosses_follow_design():
    for name, boss in (('stage2', 'crasher'), ('stage3', 'ark')):
        s, p = make_stage(name=name)
        found = [info.get('boss') for info in s.layout.values() if info.get('type') == 'boss']
        assert found == [boss], (name, found)


def test_typed_spawns_can_be_swapped_per_room():
    """템플릿에 s·t로 적힌 적도 스테이지 데이터의 swap으로 바꿀 수 있다 (같은 방 모양을 다른 구역에서 다른 적으로)."""
    stage, p = make_stage(name='stage2')
    swapped = [(c, info) for c, info in stage.layout.items() if info.get('swap')]
    assert swapped
    coord, info = swapped[0]
    stage.enter_room(coord, 'L')
    kinds = {e.kind for e in game_world.world[game_world.LAYER_ENEMY]}
    for old, new in info['swap'].items():
        assert old not in kinds or old in info['swap'].values()
        assert new in kinds


def test_next_stage_keeps_player_progress():
    import stage as stage_mod
    stage, p = make_stage()
    p.hp, p.shards = 61, 17
    p.give_weapon('pistol')
    p.items.append('w_dummy')
    p.gauge.value = 47.0
    stage.finished = True
    nxt = stage_mod.next_stage(stage)
    assert nxt is not None and nxt.name == 'stage2' and nxt.player is p
    assert nxt.on_clear is stage.on_clear and nxt.on_message is stage.on_message
    assert (p.hp, p.shards, p.weapon.weapon_id, p.gauge.value) == (61, 17, 'pistol', 47.0) and 'w_dummy' in p.items
    assert p.room is nxt.room and nxt.coord == nxt.start_coord
    last, _ = make_stage(name='stage3')
    last.finished = True
    assert stage_mod.next_stage(last) is None                               # 마지막 구역 다음은 탈출(엔딩)


# ----- 아이템 얻을 때 이름·효과 띠 (2026-11-22 v5 빠른 개선 6) -----
def test_pickup_shows_banner_with_icon_name_and_effect():
    import ui
    stage, p = make_stage()
    to_gold(stage, p)
    ped = next(d for d in stage.pedestals if d.item_id not in items.WEAPON_ITEMS)
    p.x, p.y = ped.x, ped.y
    got = []
    stage.on_pickup = lambda item_id, text: got.append((item_id, text))
    assert stage.interact()
    assert got and got[0][0] == ped.item_id and got[0][1]
    hud = ui.GameUI(p, stage)
    hud.show_pickup(ped.item_id, got[0][1])
    name, text, icon = hud.pickup[:3]
    assert name == items.ITEMS[ped.item_id]['name'] and icon == items.icon_path(ped.item_id)
    hud.update(ui.PICKUP_TIME + 0.1)
    assert hud.pickup is None                                            # 잠깐만 보인다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
