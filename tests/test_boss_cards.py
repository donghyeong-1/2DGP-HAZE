"""보스 이름 카드 테스트 (창 없이). 실행: python tests/test_boss_cards.py

O4 (2026-11-26, docs/opus/TASKS.md): 보스 넷의 이름 카드를 지금 보스 그림(PixelLab v6)에 맞춰 다시 구웠다.
카드는 1920x400, 문지기 카드가 새로 생겨 이름 띠가 뜬다, 새 상반신 부분은 도트 2px 격자다.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

KINDS = ('gatekeeper', 'crasher', 'ark', 'heart')


def test_every_boss_has_a_1920x400_card():
    for kind in KINDS:
        path = os.path.join(ROOT, 'assets', 'backgrounds', f'boss_card_{kind}.png')
        assert os.path.exists(path), kind
        assert Image.open(path).size == (1920, 400), kind


def test_gatekeeper_card_opens():
    import zone_card

    class Boss:
        kind, title = 'gatekeeper', '문지기'

    class Stage:
        name, boss = 'stage1', None
    card = zone_card.ZoneCard(Stage())
    assert card.open_boss(Boss())


def test_new_portraits_are_on_the_two_pixel_grid_and_match_the_saved_card():
    import apply_pixellab_boss_cards as tool
    for kind in ('crasher', 'ark', 'gatekeeper'):
        card, fig, (x, y) = tool.place(kind)
        saved = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'backgrounds', f'boss_card_{kind}.png')).convert('RGB'))
        mask = np.asarray(fig.getchannel('A')) == 255
        region = saved[y:y + fig.height, x:x + fig.width]
        want = np.asarray(fig.convert('RGB'))
        assert (region[mask] == want[mask]).all(), kind                  # 저장된 카드의 인물 = 도구가 놓는 그림
        assert x % 2 == 0 and y % 2 == 0 and fig.width % 2 == 0 and fig.height % 2 == 0, kind
        blocks = want.reshape(fig.height // 2, 2, fig.width // 2, 2, 3)
        assert (blocks == blocks[:, :1, :, :1]).all(), kind              # 2x2 칸마다 한 색 (도트 2px)
        m = mask.reshape(fig.height // 2, 2, fig.width // 2, 2)
        assert (m == m[:, :1, :, :1]).all(), kind


def test_old_cards_are_kept_as_concept():
    for kind in ('crasher', 'ark', 'heart'):
        assert os.path.exists(os.path.join(ROOT, 'assets', 'concept', 'boss_cards_old', f'boss_card_{kind}.png')), kind


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
