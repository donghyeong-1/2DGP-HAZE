"""강화 단계별 공격·색, 피해 숫자, 타격 이펙트, 궁극기 이펙트 테스트 (창 없이). 실행: python tests/test_enhance_levels.py

2026-11-21 사용자 요청:
- 강화 단계마다 다른 공격: 2단계는 식칼이 사방으로 한 바퀴 더(칼 8자루), 건틀릿이 부채꼴 세 갈래(11/24 돌진 강타로 바뀌어
  부딪힌 자리에서 양옆 충격파), 사슬은 돌아올 때
  주인공 둘레에 충격(가까운 적 모두). 철파이프 2단계(올려베기 -> 내려찍기)는 그대로.
- 강화 단계마다 다른 색: 1단계 보라, 2단계 금, 3단계(궁극기 준비) 진홍. 이펙트 시트(<이름>2·3), 오라, 화면 색, 숫자 색.
- 피해 숫자: 맞을 때 하나만(예전에는 무기 숫자와 겹쳐 두 개), 전용 픽셀 숫자 그림(assets/ui/dmg_small·dmg_big),
  같은 적에게 이어 맞으면 위로 쌓인다(다단 히트), 강한 공격은 큰 숫자.
- 타격 이펙트: 맞을 때마다 적을 가로지르는 베기 자국(SlashMark), 강한 공격은 X자 자국 두 개 + 퍼지는 고리(ImpactRing).
- 궁극기: 연타마다 범위 안에 큰 베기 자국 여러 개, 마지막 일격에 빛기둥(LightPillar)·큰 고리·화면 섬광.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402

ROOT = os.path.join(HERE, '..')


def objs(name):
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == name]


def armed(wid, level, gauge=60, gaps=(300,)):
    room, p = tc.make_world()
    if wid != 'pipe':
        p.give_weapon(wid)
    tc.set_gauge(p, 95 if level >= 2 else gauge)
    foes = []
    for gap in gaps:
        e = tc.freeze(tc.add_enemy('slum', p.x + gap, room, p))
        e.hp = e.max_hp = 10 ** 5
        foes.append(e)
    p.mouse_x, p.mouse_y = p.x + 600, foes[0].center[1]
    for _ in range(level):
        assert p.request_enhance()
    return room, p, foes


# ----- 단계별 다른 공격 -----
def test_gauntlet_level2_impact_sends_shockwaves_both_ways():
    """11/24 돌진 강타: 2단계는 부딪힌 자리에서 양옆으로 땅을 타는 충격파 둘 (예전 부채꼴 세 갈래 대신)."""
    for level, want in ((1, 0), (2, 2)):
        room, p, foes = armed('gauntlet', level)
        p.attack_held = True
        assert p.request_attack()
        tc.step(int(config.GAUNTLET_CHARGE_TIME['CRITICAL'] * 60) + 3)
        p.attack_held = False
        most = 0
        for _ in range(20):
            tc.step(1)
            most = max(most, len(objs('Blast')))
        assert foes[0].hp < foes[0].max_hp and most == want, (level, most)


def test_chain_level2_shocks_around_the_player_when_it_returns():
    import test_chain as tch
    room, p, foes = armed('chain', 2, gaps=(300, -120))           # 뒤에 선 적은 갈고리에 안 걸린다
    behind = foes[1]
    hp0 = behind.hp
    tch.fire_and_wait(p)
    assert behind.hp < hp0                                         # 돌아올 때의 충격에 맞았다
    room, p, foes = armed('chain', 1, gaps=(300, -120))
    hp0 = foes[1].hp
    tch.fire_and_wait(p)
    assert foes[1].hp == hp0                                       # 1단계에는 충격이 없다


# ----- 단계별 색 -----
def test_effect_sheets_and_colors_change_by_level():
    for base in ('hit-enhanced', 'pipe-slash-enhanced', 'air-spin-enhanced', 'aura-enhanced'):
        for lv in (2, 3):
            assert os.path.exists(os.path.join(ROOT, 'assets', 'effects', f'{base}{lv}.png')), (base, lv)
    room, p, foes = armed('pipe', 1)
    w = p.weapon
    w.level = 1
    fx1 = w._fx(True)
    w.level = 2
    fx2 = w._fx(True)
    assert fx1['spark'] == 'hit-enhanced' and fx2['spark'] == 'hit-enhanced2'
    assert fx1['damage_color'] != fx2['damage_color']
    assert effects.aura_names('NORMAL', True, level=1) == ['aura-enhanced']
    assert effects.aura_names('NORMAL', True, level=2) == ['aura-enhanced2']
    assert effects.aura_names('NORMAL', True, level=3) == ['aura-enhanced3']
    import atmosphere
    tints = {lv: atmosphere.target_tint('NORMAL', True, 0.0, level=lv)[0] for lv in (1, 2, 3)}
    assert len(set(tints.values())) == 3
    assert len({config.ENHANCE_LEVEL_COLOR[lv] for lv in (1, 2, 3)}) == 3


# ----- 피해 숫자 -----
def test_one_pixel_number_per_hit_and_stacking():
    room, p, foes = armed('pipe', 0, gauge=35)
    e = foes[0]
    for _ in range(3):
        p.weapon._hit(e, 12, 0, config.ZONE_FX['NORMAL'], extra=False)
    nums = objs('DamageNumber')
    texts = [o for o in objs('FloatText') if o.text.isdigit()]
    assert len(nums) == 3 and not texts                            # 숫자는 맞을 때마다 하나 (겹치지 않는다)
    assert len({n.stack for n in nums}) == 3                       # 이어 맞으면 위로 쌓인다
    for name in ('dmg_small', 'dmg_big'):
        assert os.path.exists(os.path.join(ROOT, 'assets', 'ui', name + '.png'))


def test_strong_hits_get_big_numbers():
    import drama
    room, p, foes = armed('pipe', 0, gauge=35)
    p.weapon._hit(foes[0], 12, 0, config.ZONE_FX['NORMAL'], big=True, extra=False)
    assert objs('DamageNumber')[-1].big
    assert drama.DamageNumber(0, 0, 5, (255, 255, 255)).big is False


# ----- 타격 이펙트 -----
def test_every_hit_leaves_a_slash_mark_and_strong_hits_more():
    room, p, foes = armed('pipe', 0, gauge=35)
    p.weapon._hit(foes[0], 12, 0, config.ZONE_FX['NORMAL'], extra=False)
    assert len(objs('SlashMark')) == 1 and not objs('ImpactRing')
    p.weapon._hit(foes[0], 12, 0, config.ZONE_FX['NORMAL'], big=True, extra=False)
    assert len(objs('SlashMark')) == 3 and len(objs('ImpactRing')) == 1   # X자 자국 + 고리


# ----- 궁극기 -----
def test_ultimate_draws_slash_storm_and_final_pillar():
    import test_ultimate as tu
    room, p, foes = tu.stacked(90, 3, [150])
    assert p.request_attack()
    seen_marks, seen_pillar, seen_ring = 0, False, False
    for _ in range(240):
        effects.hit_stop_left = 0.0
        tc.step(1)
        seen_marks = max(seen_marks, len([o for o in objs('SlashMark') if o.big]))
        seen_pillar = seen_pillar or bool(objs('LightPillar'))
        seen_ring = seen_ring or any(r.radius_max >= 300 for r in objs('ImpactRing'))
        if not tu.ultimates():
            break
    assert seen_marks >= 3 and seen_pillar and seen_ring


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
