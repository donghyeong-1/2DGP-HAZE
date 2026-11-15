"""스테이지 테스트: 방 잠금·클리어·전환, 미니맵, E 강화, 재화 (창 없이 실행). 실행: python tests/test_stage.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
from player import Player  # noqa: E402
from stage import Stage  # noqa: E402

DT = 1 / 60
FLOOR_Y = float(config.SCREEN_H - 16 * config.TILE)


def make_stage():
    game_world.clear()
    effects.reset()
    player = Player(0, 0, None)
    game_world.add_object(player, game_world.LAYER_PLAYER)
    stage = Stage(player)
    stage.start()
    for _ in range(40):
        game_world.update(DT)
    return stage, player


def kill_all():
    for e in list(game_world.world[game_world.LAYER_ENEMY]):
        e.take_damage(10000)


def test_first_room_has_enemies_and_is_locked():
    stage, p = make_stage()
    assert stage.enemy_count() == 2 and stage.room.locked
    assert stage.room.tile_at(31, 14) == '#'                    # 잠긴 문은 벽이다
    assert stage.links_of((0, 0)) == {'R'}                       # 첫 방은 왼쪽 문이 없다


def test_clearing_room_opens_door_and_moves_to_next_room():
    stage, p = make_stage()
    notices = []
    stage.on_clear = lambda s: notices.append(s.coord)
    kill_all()
    stage.update()
    assert not stage.room.locked and notices == [(0, 0)] and (0, 0) in stage.cleared
    assert stage.room.tile_at(31, 14) == 'R'                    # 열린 문은 지나갈 수 있다
    p.x, p.y = config.SCREEN_W - config.PLAYER_HB_W / 2 - 1, FLOOR_Y
    stage.update()
    assert stage.coord == (1, 0) and stage.room.locked and stage.enemy_count() == 3
    assert p.x < 200 and p.room is stage.room                    # 다음 방의 왼쪽 입구에서 시작


def test_cannot_leave_locked_room():
    stage, p = make_stage()
    p.x, p.y = config.SCREEN_W - config.PLAYER_HB_W / 2 - 1, FLOOR_Y
    stage.update()
    assert stage.coord == (0, 0)


def test_can_go_back_and_cleared_room_stays_empty():
    stage, p = make_stage()
    kill_all(); stage.update()
    p.x, p.y = config.SCREEN_W - config.PLAYER_HB_W / 2 - 1, FLOOR_Y
    stage.update()
    kill_all(); stage.update()
    p.x, p.y = config.PLAYER_HB_W / 2 + 1, FLOOR_Y
    stage.update()
    assert stage.coord == (0, 0) and stage.enemy_count() == 0 and not stage.room.locked


def test_last_room_is_high_haze_and_exit_finishes_stage():
    stage, p = make_stage()
    for _ in range(2):
        kill_all(); stage.update()
        p.x, p.y = config.SCREEN_W - config.PLAYER_HB_W / 2 - 1, FLOOR_Y
        stage.update()
    assert stage.coord == (2, 0) and stage.room.is_high_haze and not stage.finished
    kill_all(); stage.update()
    p.x, p.y = config.SCREEN_W - config.PLAYER_HB_W / 2 - 1, FLOOR_Y
    stage.update()
    assert stage.finished


def test_minimap_shows_visited_and_neighbours():
    stage, p = make_stage()
    cells = {c: s for c, s, _ in stage.minimap_cells()}
    assert cells == {(0, 0): 'current', (1, 0): 'unknown'}


def test_kill_drops_shards():
    stage, p = make_stage()
    kill_all()
    assert p.shards == 2 * config.SHARDS_PER_KILL['slum']


def test_enhance_costs_gauge_and_boosts_pipe():
    stage, p = make_stage()
    kill_all(); stage.update()
    p.gauge.value = 60.0
    p.gauge.zone = p.gauge._zone_of(60.0)
    assert p.request_enhance() and p.gauge.enhanced
    assert p.gauge.value == 60.0 - config.ENHANCE_COST
    assert not p.request_enhance()                              # 강화 중에는 다시 못 쓴다
    from enemy import Enemy
    e = Enemy('slum', p.x + 100, FLOOR_Y, stage.room, p)
    e.stats = dict(e.stats, speed=0.0, sight=0)
    e.hp = e.max_hp = 1000
    game_world.add_object(e, game_world.LAYER_ENEMY)
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    assert e.max_hp - e.hp == config.PIPE_DAMAGE * config.ENHANCE_DAMAGE_MULT * p.gauge.zone_multipliers()['attack']


def test_enhance_refused_when_gauge_too_low():
    stage, p = make_stage()
    p.gauge.value = 29.0
    p.gauge.zone = p.gauge._zone_of(29.0)
    assert not p.request_enhance() and p.gauge.value == 29.0


def test_enhanced_kill_blasts_neighbours():
    stage, p = make_stage()
    kill_all(); stage.update()
    p.gauge.value = 60.0
    p.gauge.zone = p.gauge._zone_of(60.0)
    p.request_enhance()
    from enemy import Enemy
    a = Enemy('slum', p.x + 100, FLOOR_Y, stage.room, p)
    b = Enemy('slum', p.x + 230, FLOOR_Y, stage.room, p)  # 파이프 사거리(약 202) 밖, 폭발 반경 안
    for e in (a, b):
        e.stats = dict(e.stats, speed=0.0, sight=0)
        game_world.add_object(e, game_world.LAYER_ENEMY)
    a.hp = 1
    p.mouse_x, p.mouse_y = p.x + 300, p.center[1]
    p.request_attack()
    assert not a.alive and b.hp == b.max_hp - config.ENHANCE_BLAST_DAMAGE


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
