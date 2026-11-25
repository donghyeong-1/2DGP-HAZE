"""임팩트 프레임을 강화 일격·보스 막타까지 (창 없이). 실행: python tests/test_impact_frame.py

v8 4-2 (docs/plan_v8.md, 대기열 4 '남겨 둔 것'): 처형·궁극기 마무리에는 이미 있다(FinisherCut). 강화 일격(E)과 보스 막타에도
1~2프레임: 배경 검정 + 주인공·맞은 적의 흰 실루엣 + 흰 베기 선.
- 강화 일격이 여러 적을 맞혀도 한 장면(맞은 적이 늘어날 뿐). 평범한 타격·평범한 처치에는 없다.
- 보스(문지기·크래셔·아크·헤이즈 심장)를 쓰러뜨린 타격이면 강화가 아니어도 나온다.
- 큰 마무리(FinisherCut)가 돌고 있으면 겹치지 않는다. 설정 '번쩍임 줄이기'면 나오지 않는다.
- 그려진 프레임 수로 끝난다(멈춤 중에도 늘어지지 않게). 타격 멈춤 중에도 그 순간에 보이게 UI 층 맨 앞(세계 위, HUD 아래)에 둔다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import impact_frame  # noqa: E402
import options  # noqa: E402
import test_combat as tc  # noqa: E402


def frames():
    return [o for o in game_world.world[game_world.LAYER_UI] if isinstance(o, impact_frame.ImpactFrame)]


def world(n=2):
    room, p = tc.make_world()
    foes = []
    for i in range(n):
        e = tc.freeze(tc.add_enemy('slum', p.x + 200 + 60 * i, room, p))
        e.hp = e.max_hp = 10 ** 5
        foes.append(e)
    return room, p, foes


def test_enhanced_strike_makes_one_frame_for_all_victims():
    room, p, foes = world(2)
    for e in foes:
        p.weapon._hit(e, 12, 0, config.ENHANCED_FX, big=True, extra=False)
    fs = frames()
    assert len(fs) == 1 and len(fs[0].victims) == 2                # 한 장면에 맞은 적 둘
    assert fs[0].player is p


def test_normal_hits_and_kills_have_no_frame():
    room, p, foes = world(1)
    p.weapon._hit(foes[0], 12, 0, config.ZONE_FX['NORMAL'], big=True, extra=False)
    foes[0].hp = 1
    p.weapon._hit(foes[0], 12, 0, config.ZONE_FX['NORMAL'], extra=False)
    assert not foes[0].alive and not frames()


def test_boss_final_blow_makes_a_frame():
    from gatekeeper import Gatekeeper
    room, p, foes = world(0)
    g = Gatekeeper(p.x + 200, p.y, room, p)
    game_world.add_object(g, game_world.LAYER_ENEMY)
    p.weapon._hit(g, 12, 0, config.ZONE_FX['NORMAL'], extra=False)
    assert not frames()                                            # 살아 있으면 없다
    g.hp = 1
    p.weapon._hit(g, 12, 0, config.ZONE_FX['NORMAL'], extra=False)
    assert not g.alive and len(frames()) == 1
    assert impact_frame.is_boss(g) and not impact_frame.is_boss(tc.add_enemy('slum', p.x, room, p))


def test_skipped_with_reduce_flash_or_during_finisher():
    room, p, foes = world(1)
    old = options.reduce_flash
    try:
        options.reduce_flash = True
        p.weapon._hit(foes[0], 12, 0, config.ENHANCED_FX, big=True, extra=False)
        assert not frames()
    finally:
        options.reduce_flash = old
    import weapon
    game_world.add_object(weapon.FinisherCut(foes[0].x, foes[0].y, (255, 255, 255), p, foes[0]), game_world.LAYER_EFFECT)
    p.weapon._hit(foes[0], 12, 0, config.ENHANCED_FX, big=True, extra=False)
    assert not frames()


def test_ends_after_its_frames_are_drawn():
    room, p, foes = world(1)
    f = impact_frame.trigger(p, foes[0], foes[0].x)
    assert f is not None and f.visible()
    f.update(1.0)
    assert f in frames()                                           # 시간이 아니라 그려진 수로 끝난다
    f.drawn = impact_frame.FRAMES
    assert not f.visible()
    f.update(0.0)
    assert f not in frames()
    assert impact_frame.FRAMES in (1, 2)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
