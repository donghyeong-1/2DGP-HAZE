"""최종 보스 아크: 모든 패턴의 몸 그림이 실제로 있고, 예고 빛 색이 있다 (버그 훑기, 2026-11-25).
창 없이: python tests/test_ark_frames.py

병합 연습 중 화면 없는 창으로 한 판을 돌리다 찾았다: 2페이즈부터 나오는 '농도 띠(bands)'·'결정 벽(crystals)'은
boss_ark_bands_1.png 같은 그림이 없어 그리는 순간 게임이 꺼졌다(FileNotFoundError), 예고 빛 색(GLOW)도 없었다(KeyError).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import ark  # noqa: E402
import sprites  # noqa: E402
import test_ark as ta  # noqa: E402

ASSETS = os.path.join(HERE, '..', 'assets')


def _patterns():
    out = set(ark.WINDUP) | set(ark.ACTIVE)
    for table in ark.TABLES.values():
        out |= set(table)
    return sorted(out - {'wave'}) + ['absorb', 'overcharge']      # 'wave'는 흡수·과충전 중 하나로 바뀐다


def test_every_pattern_has_body_frames_on_disk():
    _room, _p, a = ta.make_fight()
    for pattern in _patterns():
        for t, teleported in ((0.0, False), (0.0, True), (5.0, True)):
            a.state, a.pattern, a.attack_time, a.teleported = 'ATTACK', pattern, t, teleported
            name, n = sprites.resolve(*a._body_frame())
            path = os.path.join(ASSETS, sprites.path(name, n))
            assert os.path.exists(path), f'{pattern}: {path} 없음'


def test_every_pattern_has_a_windup_glow():
    for pattern in _patterns():
        assert pattern in ark.GLOW, pattern


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
