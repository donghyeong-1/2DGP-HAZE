"""주인공 공격 동작 v3 (2026-11-24, docs/plan_v7.md 8절). 창 없이: python tests/test_attack_v3.py

연타·공중·대시·강화마다 동작 그림과 이펙트 모양이 맞아야 한다:
- 땅 옆 1타 = 가로 베기(n09_swing_side, 납작한 가로 호), 2타 = 사선 반원(side2), 3타 = 올려베기(side3, 올라가는 금색 호).
- 공중 공격: 1타 가로(n09_air1) -> 2타 반원(n09_air2), 위로 겨누면 올려베기(n09_airup). 땅에 닿으면 다시 1타부터.
- E 1단계 = X베기(n09_e1), 대시 평타 = 낮은 돌진 가로 베기(n09_dashcut, 멈추지 않는다).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import sprites  # noqa: E402
import test_combat as tc  # noqa: E402


def _effects():
    return [getattr(o, 'name', '') for o in game_world.world[game_world.LAYER_EFFECT]]


def _clear_effects():
    for o in list(game_world.world[game_world.LAYER_EFFECT]):
        game_world.remove_object(o)


def test_new_sets_exist():
    for name in ('n09_swing_side2', 'n09_swing_side3', 'n09_air1', 'n09_air2', 'n09_airup', 'n09_dashcut', 'n09_e1'):
        assert name in sprites.SKIN, name


def test_ground_combo_poses_and_effect_shapes():
    _room, p = tc.make_world()
    seen = []
    for i in range(3):
        _clear_effects()
        assert p.request_attack()
        seen.append(p._body_frame()[0])
        names = _effects()
        if i == 0:
            assert any(n.endswith('-flat') for n in names), names              # 가로 베기 = 납작한 가로 호
        if i == 2:
            assert config.FINISHER_SLASH + '-rise' in names, names             # 올려베기 = 올라가는 금색 호
        tc.run_frames(int(p.weapon.cooldown * 60) + 2)
    assert seen == ['n09_swing_side', 'n09_swing_side2', 'n09_swing_side3'], seen


def test_air_attacks_alternate_and_reset_on_landing():
    _room, p = tc.make_world()
    p.request_jump()
    tc.run_frames(6)
    assert p.request_attack() and p.weapon.last_kind == 'spin'
    assert p._body_frame()[0] == 'n09_air1'
    assert any(n.endswith('-flat') for n in _effects())
    tc.run_frames(2)
    p.weapon.cooldown = 0                                                       # 대기 시간을 건너뛰고 공중에서 바로 2타
    assert not p.on_ground and p.request_attack()
    assert p._body_frame()[0] == 'n09_air2'
    tc.run_frames(120)                                                         # 착지
    assert p.on_ground and p.air_combo == 0
    p.request_jump()
    tc.run_frames(6)
    p.mouse_x, p.mouse_y = p.x + 40, p.center[1] + 400                          # 위로 겨눔
    assert p.request_attack()
    assert p._body_frame()[0] == 'n09_airup'


def test_enhanced_strike_shows_x_slash_pose():
    _room, p = tc.make_world()
    p.gauge.value = 60
    p.gauge.zone = p.gauge._zone_of(60)
    p.request_enhance()
    assert p.gauge.enhanced and p.gauge.enhance_level == 1
    assert p.request_attack()
    assert p._body_frame()[0] == 'n09_e1'


def test_dash_strike_shows_dash_cut_pose_without_slowing():
    _room, p = tc.make_world()
    p.request_dash()
    assert p.request_attack()                                                   # 대시 중: 끝나면 벤다
    for _ in range(60):
        tc.run_frames(1)
        if p.state != 'DASH':
            break
    assert p._body_frame()[0] == 'n09_dashcut'
    assert p.swing_anim == 'n09_dashcut'


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
