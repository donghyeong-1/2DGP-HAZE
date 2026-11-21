"""화면 분위기(빛·안개 덧칠) 테스트 (창 없이). 실행: python tests/test_atmosphere.py

2026-11-21 퀄리티 상승 계획 2-2 (docs/quality_plan.md): 헤이즈 게이지 구간이 화면 색으로도 읽힌다.
- 페이드(약해짐)는 차갑고 어둡게, 각성은 옅은 청록, 위험은 붉게 맥동, 강화 준비는 보라.
- 가장자리를 어둡게(비네트), 헤이즈가 짙은 방은 안개가 진하게 흐르고 은신처에는 안개가 없다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import atmosphere  # noqa: E402
import config  # noqa: E402


def test_zone_tint_is_cold_when_weak_warm_when_critical_and_none_when_normal():
    color, alpha = atmosphere.target_tint('NORMAL', False, 0.0)
    assert alpha == 0
    cold, a_fade = atmosphere.target_tint('FADE', False, 0.0)
    assert a_fade > 0 and cold[2] > cold[0]                      # 파랗게
    warm, a_crit = atmosphere.target_tint('CRITICAL', False, 0.0)
    assert a_crit > 0 and warm[0] > warm[2]                      # 붉게
    pulse = {round(atmosphere.target_tint('CRITICAL', False, t)[1], 3) for t in (0.0, 0.125, 0.375)}
    assert len(pulse) > 1                                        # 위험은 맥동한다
    violet, a_enh = atmosphere.target_tint('NORMAL', True, 0.0)
    assert a_enh > 0 and violet[2] > violet[1]                   # 강화 준비: 보라


def test_tint_eases_toward_target_instead_of_snapping():
    a = atmosphere.Atmosphere.__new__(atmosphere.Atmosphere)
    a.color, a.alpha, a.time = (0, 0, 0), 0.0, 0.0
    a.ease('FADE', False, 1 / 60)
    _, target = atmosphere.target_tint('FADE', False, 0.0)
    assert 0 < a.alpha < target                                  # 한 프레임에 바로 바뀌지 않는다
    for _ in range(120):
        a.ease('FADE', False, 1 / 60)
    assert abs(a.alpha - target) < 0.01


def test_fog_and_vignette_depend_on_room():
    assert atmosphere.fog_strength('hideout', False) == 0          # 은신처는 맑다
    assert atmosphere.fog_strength('stage1', True) > atmosphere.fog_strength('stage1', False) > 0
    assert atmosphere.vignette_strength('FADE', False) > atmosphere.vignette_strength('NORMAL', False)
    assert atmosphere.vignette_strength('NORMAL', True) > atmosphere.vignette_strength('NORMAL', False)


def test_overlay_images_exist_and_fit_the_screen():
    from PIL import Image
    root = os.path.join(HERE, '..', 'assets')
    v = Image.open(os.path.join(root, 'ui', 'vignette.png'))
    assert v.size == (config.SCREEN_W, config.SCREEN_H) and v.mode == 'RGBA'
    alpha = v.getchannel('A')
    assert set(alpha.getdata()) <= {0, 255}                                     # 픽셀 규칙: 알파는 켜짐·꺼짐 (점묘로 농도를 낸다)
    W, H = config.SCREEN_W, config.SCREEN_H

    def density(x0, y0):
        box = alpha.crop((x0, y0, x0 + 64, y0 + 64)).getdata()
        return sum(1 for a in box if a) / len(box)
    assert density(W // 2 - 32, H // 2 - 32) == 0                               # 가운데는 투명
    assert density(0, 0) > 0.5                                                  # 모서리는 촘촘히 어둡다
    f = Image.open(os.path.join(root, 'backgrounds', 'fog_strip.png'))
    assert f.mode == 'RGBA' and W % f.size[0] == 0                              # 화면 너비를 정수 번 이어 붙인다
    fa = list(f.getchannel('A').getdata())
    assert set(fa) <= {0, 255} and sum(1 for a in fa if a) / len(fa) < 0.5     # 점묘로 성기게 (게임이 옅게 그린다)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
