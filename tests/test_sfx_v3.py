"""효과음 v3 (2026-11-24 사용자: 휘두르기가 가볍고 타격음이 작다, 몹·보스·공격 종류마다 다른 소리). 창 없이: python tests/test_sfx_v3.py

- 타격음 = 무기 쪽(공격 종류: 1·2타, 3타 마무리, 이동 베기, 공중 베기, 찍기, 강화 1~3단계) + 적 쪽(재질: 살·짐승·갑옷·기계·결정·영체·작은 것·보스).
- 휘두르기 소리도 공격 종류마다 다르다(1·2·3타, 공중, 이동, 찍기, 강화 단계). 각성·위험 구간은 위에 색 소리를 겹친다.
- E 강화는 단계(1·2·3)마다 다른 소리.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import assets  # noqa: E402
import config  # noqa: E402
import test_combat as tc  # noqa: E402

played = []
assets.play_sound = lambda name: played.append(name)


def _wav(name):
    return os.path.exists(os.path.join(ROOT, 'assets', 'sfx', name + '.wav'))


def _set_gauge(p, v):
    p.gauge.value = v
    p.gauge.zone = p.gauge._zone_of(v)


def test_every_enemy_has_a_hit_material_sound():
    for kind in config.ENEMY_STATS:
        mat = config.HIT_MATERIAL[kind]
        assert _wav(f'hit_{mat}'), kind
    assert len(set(config.HIT_MATERIAL.values())) >= 7


def test_enemy_hit_plays_its_material():
    room, p = tc.make_world()
    e = tc.add_enemy('guard', p.x + 300, room, p)
    played.clear()
    e.take_damage(1, from_x=p.x)
    assert 'hit_' + config.HIT_MATERIAL['guard'] in played


def test_pipe_combo_swings_and_impacts_differ_by_step():
    room, p = tc.make_world()
    _set_gauge(p, 35)
    swings, impacts = [], []
    for _ in range(3):
        e = tc.freeze(tc.add_enemy('slum', p.x + 90, room, p))
        e.hp = e.max_hp = 9999
        played.clear()
        assert p.request_attack()
        swings.append(next(n for n in played if n.startswith('swing')))
        impacts.append(next(n for n in played if n.startswith('impact')))
        tc.run_frames(int(p.weapon.cooldown * 60) + 2)
    assert swings == ['swing_1', 'swing_2', 'swing_3'], swings
    assert impacts == ['impact_pipe', 'impact_pipe', 'impact_pipe_heavy'], impacts


def test_air_dash_plunge_and_zone_accents():
    room, p = tc.make_world()
    _set_gauge(p, 35)
    p.request_jump()
    tc.run_frames(8)
    played.clear()
    p.request_attack()
    assert 'swing_air' in played
    tc.run_frames(120)
    p.request_jump()
    tc.run_frames(14)
    p.mouse_x, p.mouse_y = p.x, p.y - 400
    p.weapon.cooldown = 0
    played.clear()
    p.request_attack()
    assert p.weapon.last_kind == 'plunge' and 'swing_plunge' in played
    tc.run_frames(120)
    p.mouse_x, p.mouse_y = p.x + 400, p.center[1]
    _set_gauge(p, 60)                                         # 각성: 위에 색 소리
    p.weapon.cooldown = 0
    played.clear()
    p.request_attack()
    assert 'accent_awake' in played
    _set_gauge(p, 10)                                         # 페이드: 힘 빠진 소리
    tc.run_frames(60)
    played.clear()
    p.request_attack()
    assert 'swing_fade' in played


def test_enhance_levels_sound_different():
    room, p = tc.make_world()
    _set_gauge(p, 90)
    got = []
    for _ in range(3):
        played.clear()
        if p.request_enhance():
            got.append(next(n for n in played if n.startswith('enhance')))
    assert got[:2] == ['enhance_1', 'enhance_2'], got
    for k in (1, 2, 3):
        assert _wav(f'enhance_{k}') and _wav(f'impact_enh{k}') and _wav(f'swing_enh{k}')


def test_all_new_sound_files_exist():
    for name in ('swing_1', 'swing_2', 'swing_3', 'swing_air', 'swing_dash', 'swing_plunge', 'accent_awake', 'accent_critical',
                 'impact_pipe_heavy', 'impact_pipe_dash', 'impact_pipe_air', 'impact_pipe_plunge'):
        assert _wav(name), name


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
