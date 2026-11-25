"""증기 분출 이펙트 (v8, 2026-11-25 다시 만듦): 가는 흰 줄이던 것을 김 덩이로 만든 굵은 기둥으로.
창 없이: python tests/test_steam_jet.py

- 시트는 시드가 다른 세 줄(variants)이고, 분출구는 0.2초마다 띄우는 시트의 줄을 차례로 바꾼다 (같은 모양이 되풀이되지 않게).
- 기둥은 피해 판정(VENT_HALF_WIDTH, VENT_HEIGHT)을 덮을 만큼 굵고 높다.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

import config  # noqa: E402
import game_world  # noqa: E402
from test_devices import DT, room_with  # noqa: E402


def sheet():
    info = json.load(open(os.path.join(ROOT, 'assets', 'effects', 'steam-jet.json'), encoding='utf-8'))
    img = Image.open(os.path.join(ROOT, 'assets', 'effects', 'steam-jet.png'))
    return info, img


def test_steam_sheet_has_three_variants_of_equal_length():
    info, img = sheet()
    assert info.get('variants') == 3 and info['frames'] % 3 == 0
    w, h = info['frameSize']
    assert img.size == (w * info['columns'], h * 3)


def test_steam_column_covers_the_hurt_box():
    """가장 크게 솟은 프레임의 칠한 칸이 판정 높이·폭을 덮는다 (시트 1px = 화면 scale px)."""
    info, img = sheet()
    w, h = info['frameSize']
    px, py = info['pivot']
    s = info['scale']
    a = img.getchannel('A')
    for row in range(3):
        top, left, right = h, w, 0
        for c in range(info['columns']):
            box = a.crop((c * w, row * h, (c + 1) * w, (row + 1) * h)).getbbox()
            if box:
                top, left, right = min(top, box[1]), min(left, box[0]), max(right, box[2])
        assert (py - top) * s >= config.VENT_HEIGHT * 0.9, (row, (py - top) * s)
        assert (px - left) * s >= config.VENT_HALF_WIDTH and (right - px) * s >= config.VENT_HALF_WIDTH


def test_vent_cycles_steam_variants_while_jetting():
    st, p, vent = room_with('stage2', 'vent')
    p.x = vent.x + 3000                                       # 주인공은 멀리
    vent.phase, vent.left, vent.tick = 'jet', 0.9, 0.0
    seen = []
    for _ in range(int(0.85 / DT)):
        before = set(map(id, game_world.world[game_world.LAYER_EFFECT]))
        vent.update(DT)
        for o in game_world.world[game_world.LAYER_EFFECT]:
            if id(o) not in before and getattr(o, 'name', '') == 'steam-jet':
                seen.append(o.variant)
    assert len(seen) >= 4 and seen[:3] == [0, 1, 2], seen


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
