"""이펙트 색 점검 (창 없이). 실행: python tests/test_effect_colors.py

O7 (2026-11-26, docs/opus/TASKS.md, plan_v8 4-5): docs/DECISIONS.md 2026-11-25 '색 언어' 표대로 쓰이는지.
고친 것만 확인한다: 적의 낙하 예고는 노랑 하나(config.FALL_WARN_COLOR). 크래셔의 고철 기둥 표시가 주황이었다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import boss_terrain  # noqa: E402
import combo  # noqa: E402
import config  # noqa: E402
import projectile  # noqa: E402


def test_every_falling_warning_is_the_same_yellow():
    r, g, b = config.FALL_WARN_COLOR
    assert r > 200 and g > 180 and b < 120                       # 노랑
    assert projectile.Debris.WARN_COLOR == config.FALL_WARN_COLOR  # 천장 고철 더미
    assert boss_terrain.PILLAR_WARN_COLOR == config.FALL_WARN_COLOR  # 고철 기둥 (전에는 주황)


def test_weapon_imprint_colors_follow_the_color_language():
    """무기 각인 빛: 철파이프 파랑, 쌍권총 민트, 건틀릿 주황, 사슬 보라 (표 그대로인지 지켜 둔다)."""
    pipe, pistol, gauntlet, chain = (combo.COLORS[k] for k in ('pipe', 'pistol', 'gauntlet', 'chain'))
    assert pipe[2] > pipe[1] > pipe[0]                            # 파랑
    assert pistol[1] > pistol[2] > pistol[0]                      # 민트 (초록이 가장 세다)
    assert gauntlet[0] > gauntlet[1] > gauntlet[2]                # 주황
    assert chain[2] > chain[0] > chain[1]                         # 보라


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
