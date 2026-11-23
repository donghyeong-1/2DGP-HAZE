"""테스트 모드 (v7, 2026-11-23, docs/plan_v7.md 5-H). 창 없이: python tests/test_test_mode.py

- 설정 '테스트 모드'를 켜면 맞아도 체력이 줄지 않고, 게이지는 사망(0)·오버로드(한계)에 닿지 않게 묶인다.
- stage.jump_to(stage, name)은 같은 플레이어로 그 구역의 시작 방을 연다 (F6~F8),
  stage.boss_room(stage)은 그 구역의 보스·관문 방 좌표다 (F9).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import options  # noqa: E402
import stage as stage_mod  # noqa: E402
import test_combat as tc  # noqa: E402
import test_stage as ts  # noqa: E402


def test_test_mode_makes_player_invincible_and_holds_gauge():
    _room, p = tc.make_world()
    options.test_mode = True
    try:
        p.take_hit(50)
        assert p.hp == p.max_hp
        p.gauge.value = 0.5
        tc.step(2)
        assert p.gauge.value >= 5 and p.state != 'DEAD'
        p.gauge.value = p.gauge.cap + 10
        tc.step(2)
        assert p.gauge.value < p.gauge.cap
    finally:
        options.test_mode = False
    p.take_hit(10)
    assert p.hp < p.max_hp                                   # 끄면 다시 맞는다


def test_jump_to_stage_and_boss_room():
    st, p = ts.make_stage()
    two = stage_mod.jump_to(st, 'stage2')
    assert two.name == 'stage2' and two.player is p and two.room is not None
    coord = stage_mod.boss_room(two)
    assert two.type_of(coord) in ('boss', 'gate')


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
