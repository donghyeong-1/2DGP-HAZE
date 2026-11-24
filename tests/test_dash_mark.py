"""대시 공격 v2: 관통 베기 + 표식 + 처형 (2026-11-24 사용자 요청 "이나리 같은 대시 공격", 영상 참고).
창 없이: python tests/test_dash_mark.py

- 철파이프: 대시 중에 누르면 대시가 끝날 때가 아니라 적을 지나가는 그 순간 벤다 (관통).
- 무기 4종 모두: 대시 공격(대시 중·직후 공격)이 맞힌 적에게 표식이 하나 쌓인다 (같은 대시로는 한 적에 하나).
- 대시 공격이 맞으면 대시 한 칸이 바로 돌아온다 (대시 -> 베기 -> 대시로 이어 간다).
- 표식이 DASH_MARKS(3)개가 되면 처형: 잠깐 뒤 큰 일격, 표식은 비워진다. 표식은 DASH_MARK_TIME 동안 안 쌓이면 사라진다.
- 대시 공격이 아닌 공격은 표식을 쌓지 않는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402


def _world(wid='pipe', gauge=50):
    room, p = tc.make_world(player_x=200.0)
    if wid != 'pipe':
        p.give_weapon(wid)
    tc.set_gauge(p, gauge)
    p.mouse_x, p.mouse_y = p.x + 600, p.center[1]
    return room, p


def _enemy(room, p, dx, hp=10 ** 5):
    e = tc.freeze(tc.add_enemy('slum', p.x + dx, room, p))
    e.hp = e.max_hp = hp
    return e


def _dash_attack(p, toward=1, frames=40):
    """대시하자마자 공격. 끝나면 적 쪽을 다시 겨눈다."""
    p.mouse_x = p.x + 600 * toward
    p.dash_slots = max(p.dash_slots, 1)
    p.weapon.cooldown = 0.0
    p.request_dash()
    tc.run_frames(1)
    p.attack_held = True
    assert p.request_attack()
    p.attack_held = False
    tc.run_frames(frames)


def test_pipe_dash_cuts_the_enemy_while_passing_through():
    room, p = _world()
    e = _enemy(room, p, 120)
    cuts = []
    real = p.weapon._hit
    p.weapon._hit = lambda enemy, *a, **k: (cuts.append(enemy), real(enemy, *a, **k))[1]
    p.request_dash()
    tc.run_frames(1)
    assert p.request_attack()
    hit_in_dash = False
    for _ in range(12):
        tc.run_frames(1)
        if e.hp < e.max_hp:
            hit_in_dash = p.state == 'DASH'
            break
    assert hit_in_dash                                                   # 끝나기 전에, 지나가는 순간 맞았다
    tc.run_frames(20)
    assert p.x > e.x                                                     # 꿰뚫고 지나갔다
    assert cuts.count(e) == 1                                            # 끝에서 한 번 더 베지 않는다


def test_dash_attack_hit_gives_back_a_dash():
    room, p = _world()
    _enemy(room, p, 120)
    p.dash_slots = 1
    _dash_attack(p, frames=3)
    assert p.dash_slots == 1                                             # 쓴 칸이 바로 돌아왔다
    room, p = _world()
    p.dash_slots = 1
    _dash_attack(p, frames=3)
    assert p.dash_slots == 0                                             # 헛치면 그대로


def test_three_marks_execute_and_reset():
    room, p = _world()
    e = _enemy(room, p, 120)
    _dash_attack(p, 1)
    assert e.dash_marks == 1
    _dash_attack(p, -1)
    assert e.dash_marks == 2
    before = e.hp
    _dash_attack(p, 1, frames=3)
    assert any(type(o).__name__ == 'DashExecution' for o in game_world.world[game_world.LAYER_EFFECT])
    tc.run_frames(40)
    assert e.dash_marks == 0
    assert before - e.hp >= config.DASH_EXEC_DAMAGE * 0.9                # 처형 일격 (+ 세 번째 베기)


def test_marks_fade_and_plain_attacks_do_not_mark():
    room, p = _world()
    e = _enemy(room, p, 120)
    _dash_attack(p, 1)
    assert e.dash_marks == 1
    tc.run_frames(int(config.DASH_MARK_TIME * 60) + 10)
    assert e.dash_marks == 0                                             # 시간이 지나면 사라진다
    room, p = _world()
    e = _enemy(room, p, 70)
    tc.run_frames(30)
    assert p.request_attack()
    tc.run_frames(20)
    assert e.hp < e.max_hp and getattr(e, 'dash_marks', 0) == 0          # 평타는 표식이 없다


def test_every_weapon_dash_attack_marks_once_per_dash():
    for wid, dx in (('pistol', 250), ('gauntlet', 160), ('chain', 280)):
        room, p = _world(wid)
        e = _enemy(room, p, dx)
        p.mouse_x = p.x + 600
        p.request_dash()
        tc.run_frames(1)
        p.attack_held = True                                             # 쌍권총은 누르고 있으면 여러 발
        assert p.request_attack(), wid
        for _ in range(20):
            tc.run_frames(1)
        p.attack_held = False
        tc.run_frames(40)
        assert e.hp < e.max_hp, wid
        assert e.dash_marks == 1, (wid, e.dash_marks)                    # 한 대시에는 하나


def test_execution_uses_a_real_picture_even_when_the_enemy_has_no_motion_frame():
    """2026-11-24 버그: 적이 동작 그림 없이 서 있으면 _body_frame이 (None, 0)을 준다(정지 그림 한 장을 쓰라는 뜻).
    처형 연출이 그 이름으로 실루엣을 그리다 None.png를 찾지 못해 게임이 종료됐다."""
    import sprites
    room, p = _world()
    e = _enemy(room, p, 120)
    e._body_frame = lambda: (None, 0)                                    # 동작 그림이 없는 순간
    _dash_attack(p, 1)
    _dash_attack(p, -1)
    _dash_attack(p, 1, frames=3)
    ex = next(o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == 'DashExecution')
    for _ in range(3):
        tc.run_frames(1)
        name, n = ex.frame
        assert name is not None, ex.frame
        root = os.path.join(HERE, '..', 'assets')
        assert os.path.exists(os.path.join(root, sprites.path(*sprites.resolve(name, n)))), ex.frame


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
