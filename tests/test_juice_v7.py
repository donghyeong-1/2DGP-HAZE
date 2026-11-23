"""v7 손맛 다듬기 (2026-11-24 사용자 플레이 피드백). 창 없이: python tests/test_juice_v7.py

- 피해 숫자가 더 크다(점 6px, 강타 8px). 게이지 증감(+3%)도 같은 픽셀 숫자 글꼴(점 4px)로 뜬다.
- 흡수: 처치하면 입자 여러 개가 흩어졌다 주인공을 쫓아와 닿고, 닿을 때 몸이 빛나며 소리가 난다(마지막엔 마무리 소리).
- 연속 처치: 짧은 시간 안에 이어 잡을수록 처치 소리가 단계별로 좋아진다(최대 6단계), 끊기면 1단계부터.
- 빛 번짐: 휘두르기·타격 시트에는 같은 모양의 부드러운 빛 시트(assets/light/glow_*)가 있어 더하기로 겹쳐 그린다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

import assets  # noqa: E402
import drama  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
import test_combat as tc  # noqa: E402

played = []


def _record_sounds():
    played.clear()
    assets.play_sound = lambda name: played.append(name)


def _objs(name):
    return [o for o in game_world.world[game_world.LAYER_EFFECT] if type(o).__name__ == name]


def test_digit_sheets_are_bigger_and_have_signs():
    for name, min_h in (('dmg_tiny', 25), ('dmg_small', 35), ('dmg_big', 45)):
        im = Image.open(os.path.join(ROOT, 'assets', 'ui', name + '.png'))
        assert im.height >= min_h, (name, im.size)
        assert im.width % len(drama.DIGITS) == 0
    assert set('+-%') <= set(drama.DIGITS)


def test_gauge_change_floats_the_same_pixel_number():
    _room, p = tc.make_world()
    import play_mode
    play_mode.player = p
    play_mode._on_gauge_change(3, 'hit')
    nums = _objs('DamageNumber')
    assert nums and nums[-1].text == '+3%' and nums[-1].size == 'tiny'
    assert not [o for o in _objs('FloatText') if '%' in o.text]


def test_absorb_particles_chase_and_light_up_the_player():
    _record_sounds()
    _room, p = tc.make_world()
    effects.spawn_absorb(p.x + 300, p.y + 80, p, shards=2, gauge_orbs=3)
    orbs = _objs('AbsorbOrb')
    assert len(orbs) >= 10                                     # 입자가 여러 개
    tc.run_frames(5)
    assert all(o.trail for o in _objs('AbsorbOrb'))            # 꼬리를 남기며 날아온다
    glowed = False
    for _ in range(120):
        tc.run_frames(1)
        glowed = glowed or p.absorb_glow > 0
    assert not _objs('AbsorbOrb')                              # 모두 닿았다
    assert glowed                                              # 닿을 때 몸이 빛났다
    assert any(n.startswith('absorb_') for n in played)
    assert 'absorb_done' in played                             # 마지막 입자: 마무리 소리


def test_kill_streak_sounds_build_up_and_reset():
    _record_sounds()
    drama.reset()
    levels = [drama.kill_streak() for _ in range(8)]
    assert levels == [1, 2, 3, 4, 5, 6, 6, 6]
    assert played[:3] == ['kill_streak_1', 'kill_streak_2', 'kill_streak_3']
    drama.tick(drama.STREAK_WINDOW + 0.1, None)
    assert drama.kill_streak() == 1                            # 끊기면 처음부터
    for k in range(1, drama.STREAK_MAX + 1):
        assert os.path.exists(os.path.join(ROOT, 'assets', 'sfx', f'kill_streak_{k}.wav'))
    assert os.path.exists(os.path.join(ROOT, 'assets', 'sfx', 'absorb_done.wav'))


def test_slash_and_hit_sheets_have_glow_sheets_drawn_additively():
    for name in ('pipe-slash', 'pipe-slash-flat', 'pipe-slash-finisher', 'hit-normal', 'air-spin', 'dash-strike'):
        assert effects.glow_of(name) == f'light/glow_{name}.png', name
        sheet = Image.open(os.path.join(ROOT, 'assets', 'effects', name + '.png'))
        glow = Image.open(os.path.join(ROOT, 'assets', 'light', f'glow_{name}.png'))
        assert glow.size in (sheet.size, (sheet.width // 2, sheet.height // 2))   # 같은 칸 배치 (절반 크기로 저장할 수 있다)
    assert effects.glow_of('dust-land') is None                 # 먼지는 빛나지 않는다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
