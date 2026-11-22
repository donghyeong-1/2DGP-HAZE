"""은신처·영구 성장 테스트 (창 없이). 실행: python tests/test_meta.py

2026-11-19 사용자 결정(docs/plan_v4.md 4절): 하데스처럼 영구 성장. 판이 끝날 때(죽든 이기든) 헤이즈 결정을 받고,
은신처의 정비사에게서 기본 스탯을 영구로 강화한다. 보관인에게 들고 있던 것 하나를 맡기면 다음 판 시작 때 받는다
(업그레이드는 1단계로만, 무기는 그대로). 타이틀 -> 은신처 -> 출발 문 -> 스테이지 1, 죽으면 은신처로.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')   # 깨진 저장 시험이 사용자 폴더에 기록을 남기지 않게

import config  # noqa: E402
import game_world  # noqa: E402
import items  # noqa: E402
import meta  # noqa: E402
from player import Player  # noqa: E402

DT = 1 / 60


def fresh(tmp=None):
    """테스트마다 빈 저장으로 시작한다 (실제 사용자 저장 파일은 건드리지 않는다)."""
    meta.PATH = os.path.join(tmp or tempfile.mkdtemp(), 'save.json')
    meta.reset()
    return meta.PATH


def new_player():
    game_world.clear()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    return p


# ----- 재화 -----
def test_run_reward_counts_rooms_bosses_and_escape():
    fresh()
    assert meta.run_reward(rooms=7, ends=1, escaped=False) == 7 * config.META_PER_ROOM + config.META_PER_END
    assert meta.run_reward(rooms=20, ends=3, escaped=True) == (20 * config.META_PER_ROOM + 3 * config.META_PER_END
                                                               + config.META_ESCAPE)


def test_finish_run_adds_crystals_once_and_saves():
    path = fresh()
    p = new_player()
    p.run_rooms, p.run_ends = 5, 1
    got = meta.finish_run(p, escaped=False)
    assert got == 5 * config.META_PER_ROOM + config.META_PER_END and meta.state['crystals'] == got
    assert meta.finish_run(p, escaped=False) == 0 and meta.state['crystals'] == got   # 같은 판은 한 번만
    meta.load()
    assert meta.state['crystals'] == got and os.path.exists(path)                       # 파일에 남는다


# ----- 정비사: 기본 스탯 영구 강화 -----
def test_mechanic_upgrades_cost_crystals_and_rise_in_price():
    fresh()
    meta.state['crystals'] = 1000
    prices = []
    for lv in range(meta.UPGRADES['hp']['max']):
        prices.append(meta.price('hp'))
        assert meta.buy('hp') and meta.state['levels']['hp'] == lv + 1
    assert prices == sorted(prices) and prices[-1] > prices[0]
    assert not meta.can_buy('hp') and not meta.buy('hp')                                # 최대 단계
    meta.state['crystals'] = 0
    assert not meta.buy('attack')                                                       # 결정이 모자라다


def test_upgrades_apply_to_a_new_run():
    fresh()
    meta.state['levels'] = {'hp': 2, 'attack': 3, 'gauge': 1, 'dash': 2}
    p = new_player()
    meta.apply_to_player(p)
    assert p.max_hp == config.PLAYER_HP + 2 * config.META_HP and p.hp == p.max_hp
    assert abs(p.attack_bonus - (1 + 3 * config.META_ATTACK)) < 1e-9
    assert abs(p.gauge.value - (config.GAUGE_START + config.META_GAUGE)) < 1e-9
    assert abs(p.dash_recharge - (config.DASH_RECHARGE - 2 * config.META_DASH)) < 1e-9


# ----- 보관인: 하나를 다음 판으로 -----
def test_keeper_slot_must_be_unlocked_first():
    fresh()
    p = new_player()
    items.apply(p, 'cap')
    assert not meta.keeper_open() and not meta.set_keepsake('cap')
    meta.state['crystals'] = config.META_KEEPER_PRICE
    assert meta.unlock_keeper() and meta.keeper_open() and meta.state['crystals'] == 0


def test_keepsake_choices_are_what_the_player_held():
    fresh()
    p = new_player()
    items.apply(p, 'cap')
    items.apply(p, 'cap')
    items.apply(p, 'dash')
    p.give_weapon('knife')
    opts = meta.keepsake_options(p)
    assert set(opts) == {'cap', 'dash', 'w_knife'}                                      # 겹치지 않게, 무기 포함


def test_kept_upgrade_returns_at_level_one_and_weapon_as_is_once():
    fresh()
    meta.state['keeper'] = True
    meta.set_keepsake('cap')
    p = new_player()
    meta.apply_to_player(p)
    assert items.level(p, 'cap') == 1 and meta.state['keepsake'] is None               # 1단계로, 한 번만
    meta.set_keepsake('w_chain')
    q = new_player()
    meta.apply_to_player(q)
    assert q.has_weapon('chain')
    r = new_player()
    meta.apply_to_player(r)
    assert not r.has_weapon('chain')                                                    # 다음 판에는 없다


def test_save_survives_a_broken_file():
    path = fresh()
    with open(path, 'w', encoding='utf-8') as f:
        f.write('{not json')
    meta.load()
    assert meta.state['crystals'] == 0 and meta.state['levels']['hp'] == 0              # 기본값으로 (게임이 멈추지 않는다)


# ----- 은신처 구역 -----
def test_run_starts_in_the_hideout_and_its_door_leads_to_stage_one():
    import stage as stage_mod
    fresh()
    p = new_player()
    s = stage_mod.Stage(p, name='hideout')
    s.start()
    assert s.type_of(s.coord) == 'hideout' and len(s.npcs) == 3
    for _ in range(60):
        game_world.update(DT)
    assert p.on_ground and p.y == 2 * config.TILE == s.npcs[0].y                      # 바닥 위에 선다 (바닥 속에 끼지 않는다)
    assert {n.kind for n in s.npcs} == {'mechanic', 'keeper', 'archivist'}
    assert 'R' in s.room.links and not s.room.locked
    assert [c for c, *_ in s.minimap_cells()] == [(0, 0)]                               # 출발 문 너머는 지도에 없다
    p.x, p.y = s.room.width - config.PLAYER_HB_W / 2 - 1, s.room.door_center('R')[1]
    s.update()
    assert s.finished and s.next_name == 'stage1'


def test_rooms_cleared_are_counted_for_the_reward():
    import stage as stage_mod
    fresh()
    p = new_player()
    s = stage_mod.Stage(p, name='stage1')
    s.start()
    s.enter_room((1, 0), 'L')
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        e.take_damage(10 ** 6)
    s.update()
    assert p.run_rooms == 1 and p.run_ends == 0


# ----- 대화 초상화 (Codex T32, 2026-11-21): 왼쪽에 주인공, 오른쪽에 NPC, 결과에 따라 표정이 바뀐다 -----
def test_dialog_portraits_exist_and_change_with_result():
    from PIL import Image
    import npc_mode
    for who in ('n09', 'mechanic', 'keeper', 'archivist'):
        for n in (1, 2):
            im = Image.open(os.path.join(HERE, '..', 'assets', 'portraits', f'{who}_{n}.png'))
            assert im.size == (200, 200)
    fresh()
    meta.reset()
    npc_mode.kind, npc_mode.selected, npc_mode.note, npc_mode.result = 'mechanic', 0, '', None
    assert npc_mode.faces() == ('n09_1', 'mechanic_1')
    meta.state['crystals'] = 999
    npc_mode.act('hp')                                                     # 샀다: 정비사가 씩 웃고 주인공은 결의
    assert npc_mode.faces() == ('n09_2', 'mechanic_2')
    meta.state['crystals'] = 0
    npc_mode.act('attack')                                                 # 결정이 모자라다: 평소 얼굴
    assert npc_mode.faces() == ('n09_1', 'mechanic_1')
    npc_mode.kind, npc_mode.result = 'keeper', None
    npc_mode.act('unlock')                                                 # 보관인: 모자라면 걱정
    assert npc_mode.faces()[1] == 'keeper_2'
    npc_mode.kind, npc_mode.result = 'archivist', None
    npc_mode.selected = len(npc_mode.rows()) - 1                           # 기록관: 지금까지의 기록을 보면 놀란다
    assert npc_mode.faces()[1] == 'archivist_2'
    npc_mode.selected = 0
    assert npc_mode.faces()[1] == 'archivist_1'
    l, r = npc_mode.portrait_spots()
    assert l[0] + 200 <= npc_mode.PANEL_X and r[0] >= npc_mode.PANEL_X + npc_mode.PANEL_W   # 판 밖 양쪽


# ----- 판 기록 (퀄리티 계획 4-2): 사망·탈출 화면에 걸린 시간·클리어한 방·처치 수·도달 구역·받은 결정 -----
def test_kills_and_run_clock_are_counted():
    from enemy import Enemy
    from room import Room
    fresh()
    p = new_player()
    assert p.run_kills == 0 and p.run_clock == 0.0
    room = Room.load('test_01')
    e = Enemy('slum', 300, 120, room, p)
    game_world.add_object(e, game_world.LAYER_ENEMY)
    e.take_damage(10 ** 6)
    assert p.run_kills == 1                                             # 쓰러뜨린 적을 센다
    import play_mode
    p.tick_run_clock(2.5, 'stage1')
    p.tick_run_clock(9.0, 'hideout')                                    # 은신처에 있던 시간은 세지 않는다
    assert p.run_clock == 2.5


def test_run_summary_lines():
    import ending_mode
    p = new_player()
    p.run_clock, p.run_rooms, p.run_kills, p.run_ends = 754.4, 9, 31, 1
    lines = ending_mode.run_summary(p, '제4구역: 철골 공장', reward=17)
    assert lines == [('도달한 구역', '제4구역: 철골 공장'), ('걸린 시간', '12:34'), ('클리어한 방', '9'),
                     ('쓰러뜨린 적', '31'), ('깬 보스·관문', '1'), ('받은 헤이즈 결정', '+17')]


# ----- 사망 원인 (2026-11-22 v5 빠른 개선 3): 무엇에 죽었는지 사망 화면에 -----
def test_death_cause_names_the_killer():
    import ending_mode
    import killers
    from enemy import Enemy
    from room import Room
    room = Room.load('test_01')
    p = new_player()
    e = Enemy('guard', 300, 120, room, p)
    p.hp = 5
    p.take_hit(99, source=e)
    assert p.state == 'DEAD' and p.death_cause == '간수'
    assert killers.describe('spike') == '가시'
    game_world.clear()
    p = Player(300, 120, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    p.gauge.value = 0.4
    p.gauge.add(-5, 'decay')
    p.update(1 / 60)
    assert p.death_cause == killers.GAUGE_EMPTY                       # 게이지가 바닥나 쓰러짐
    lines = ending_mode.run_summary(p, '제9구역', reward=0)
    assert ('쓰러진 원인', killers.GAUGE_EMPTY) in lines


def test_projectiles_and_elites_are_named():
    import killers
    import projectile
    assert killers.describe(projectile.Scrap.__new__(projectile.Scrap)) == '투척병의 고철'
    from enemy import Enemy
    from room import Room
    e = Enemy('hound', 0, 120, Room.load('test_01'), None)
    e.make_elite('swift')
    assert killers.describe(e) == e.elite_label() + ' 사냥개'


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
