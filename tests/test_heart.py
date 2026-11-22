"""최종 거대 보스 헤이즈 심장 테스트 (창 없이). 실행: python tests/test_heart.py

2026-11-22 v5 계획 2-2 (docs/plan_v5.md, 던그리드 벨리알처럼 화면을 채우는 다부위 보스):
- 탑 꼭대기 보스방에서 아크를 쓰러뜨리면 방 위에서 내려온다(아크의 진짜 모습). 등장 동안은 맞지 않는다.
- 본체(심장) + 따로 움직이는 기계 손 둘(손마다 체력). 손 체력이 0이 되면 손이 바닥에 떨어져 기절한다.
  두 손이 모두 기절하면 심장이 열려 약점이 드러난다(큰 피해). 닫혀 있을 때는 피해가 크게 줄어든다.
- 패턴: 손 내려치기(위에서 그림자 예고 -> 내려찍기, 바닥에 잠시 박혀 있음) / 손바닥 광선 훑기(세로 광선이 방을 가로지름)
  / 결정 비(떨어질 자리 예고) / 농도 파동(방 전체 게이지가 오르내리는 파도).
- 페이즈가 오르면 방이 바뀐다: 2페이즈 발판이 솟음(임시 벽), 3페이즈 바닥이 헤이즈로 잠김(고농도) + 심장이 내려옴.
- 심장을 쓰러뜨리면 손도 함께 쓰러지고 방이 클리어된다(구역 끝).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import heart as hm  # noqa: E402
from player import Player  # noqa: E402
from room import Room  # noqa: E402

T = config.TILE
H = config.HEART


def run(frames):
    for _ in range(frames):
        effects.hit_stop_left = 0.0
        effects.slow_left = 0.0
        game_world.update(1 / 60)


def make_fight(intro=False):
    game_world.clear()
    effects.reset()
    room = Room.load('boss_arena', ('L',))
    p = Player(12 * T, 2 * T + 5, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    run(20)
    p.hp = p.max_hp = 10 ** 6
    core = hm.spawn(room, p)
    core.cooldown = 99.0
    if not intro:
        core.intro_left = 0.0
        run(2)
    return room, p, core


def test_spawn_core_and_two_hands_and_intro_invulnerable():
    room, p, core = make_fight(intro=True)
    hands = [o for o in game_world.world[game_world.LAYER_ENEMY] if isinstance(o, hm.HeartHand)]
    assert len(hands) == 2 and core.hands == hands
    hp = core.hp
    core.take_damage(100, from_x=p.x)
    assert core.hp == hp                                          # 등장 중에는 맞지 않는다
    run(int(H['intro'] * 60) + 5)
    assert core.intro_left <= 0


def test_core_armored_until_both_hands_stunned():
    room, p, core = make_fight()
    hp = core.hp
    core.take_damage(100, from_x=p.x)
    closed_loss = hp - core.hp
    assert abs(closed_loss - 100 * H['closed_mult']) < 1e-6        # 닫혀 있으면 피해가 줄어든다
    for h in core.hands:
        h.take_damage(10 ** 4, from_x=p.x)
        assert h.stunned and h.alive                              # 손은 쓰러지지 않고 기절한다
    run(2)
    assert core.open_left > 0                                     # 두 손 모두 기절: 심장이 열린다
    hp = core.hp
    core.take_damage(100, from_x=p.x)
    assert abs((hp - core.hp) - 100 * H['open_mult']) < 1e-6
    run(int(max(H['open_time'], H['hand_stun']) * 60) + 120)
    assert core.open_left <= 0
    assert all(not h.stunned and h.hp == h.max_hp for h in core.hands)   # 손은 다시 일어난다


def test_hand_slam_hits_player_below_and_rests_on_floor():
    room, p, core = make_fight()
    p.invuln_left = 0.0
    hand = core.hands[0]
    hand.start('slam')
    hp = p.hp
    run(int((H['slam_aim'] + 0.6) * 60))
    assert p.hp < hp                                              # 내려찍기에 맞았다
    assert hand.mode == 'rest' and abs(hand.y - p.y) < 2          # 바닥에 박혀 있다 (때릴 기회)
    run(int((H['slam_rest'] + 2.5) * 60))
    assert hand.mode == 'idle'


def test_laser_sweeps_across_and_hits_once():
    room, p, core = make_fight()
    p.invuln_left = 0.0
    hand = core.hands[1]
    hand.start('laser')
    hp = p.hp
    run(int(7 * 60))
    lost = hp - p.hp
    assert lost == H['laser_damage']                                  # 한 번만
    assert hand.mode in ('idle', 'return')


def test_dash_through_laser_is_just_dash():
    room, p, core = make_fight()
    hand = core.hands[1]
    hand.start('laser')
    hp = p.hp
    for _ in range(int(7 * 60)):
        if hand.mode == 'sweep' and abs(hand.x - p.x) < 90 and p.state != 'DASH' and p.dash_slots > 0:
            p.mouse_x, p.mouse_y = hand.x, p.center[1]                 # 광선 쪽으로 뚫고 지나간다
            p.request_dash()
        run(1)
    assert p.hp == hp and p.just_dashes >= 1


def test_crystal_rain_falls_with_warnings():
    room, p, core = make_fight()
    core.start_pattern('rain')
    shards = [o for o in game_world.world[game_world.LAYER_EFFECT] if isinstance(o, hm.CrystalShard)]
    assert len(shards) == H['rain_count']
    assert any(abs(s.x - p.x) < 60 for s in shards)               # 하나는 플레이어 자리


def test_pulse_moves_gauge_up_then_down():
    room, p, core = make_fight()
    p.gauge.value = 50.0
    core.start_pattern('pulse')
    vals = []
    for _ in range(int(H['pulse_time'] * 60)):
        run(1)
        vals.append(p.gauge.value)
    run(2)
    assert max(vals) > 50 + 4 and min(vals) < max(vals) - 8        # 오르내린다
    assert not [o for o in game_world.world[game_world.LAYER_EFFECT] if isinstance(o, hm.HazePulse)]


def test_phases_change_the_room():
    room, p, core = make_fight()
    y1 = core.y
    core.hp = core.max_hp * H['phases'][0] - 1
    run(3)
    assert core.phase == 2 and any(v == 'heart' for v in room.extra_solids.values())   # 발판이 솟았다
    core.hp = core.max_hp * H['phases'][1] - 1
    run(3)
    assert core.phase == 3 and room.is_high_haze                  # 바닥이 헤이즈로 잠긴다
    run(120)
    assert core.y < y1                                            # 심장이 내려왔다


def test_killing_core_ends_fight():
    room, p, core = make_fight()
    core.open_left = 5.0
    core.take_damage(10 ** 6, from_x=p.x)
    run(2)
    assert not core.alive and not any(getattr(o, 'alive', False) for o in game_world.world[game_world.LAYER_ENEMY])


def test_ark_death_brings_heart_in_final_room():
    import stage as stage_mod
    game_world.clear()
    effects.reset()
    room = Room.load('boss_arena', ('L',))
    p = Player(12 * T, 2 * T + 5, room)
    st = stage_mod.Stage(p, seed=1, name='stage3')
    st.start()
    boss_coord = next(c for c, i in st.layout.items() if i.get('type') == 'boss')
    st.enter_room(boss_coord, 'L')
    game_world.add_object(p, game_world.LAYER_PLAYER)
    ark = st.boss
    ark.take_damage(10 ** 6, from_x=p.x)
    st.update()
    assert isinstance(st.boss, hm.HeartCore) and st.room.locked and boss_coord not in st.cleared


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
