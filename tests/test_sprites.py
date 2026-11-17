"""동작 그림 테스트: 파일이 다 있는가, 발 기준점이 그림 안에 있는가, 기준점 맞춤 계산 (창 없이 실행).
실행: python tests/test_sprites.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from PIL import Image  # noqa: E402

import config  # noqa: E402
import sprites  # noqa: E402

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


def size_of(rel):
    return Image.open(os.path.join(BASE, rel)).size


def test_every_frame_file_exists_and_pivot_is_inside():
    for name, (count, px, py) in sprites.FRAMES.items():
        sizes = set()
        for n in range(1, count + 1):
            w, h = size_of(sprites.path(name, n))
            sizes.add((w, h))
            assert 0 < px < w and 0 < py <= h, (name, n, (w, h))
        assert len(sizes) == 1, f'{name}: 프레임마다 캔버스가 다르다 {sizes}'      # 한 동작의 프레임은 캔버스가 같다


def test_still_sprites_exist_for_every_enemy():
    for kind, stats in config.ENEMY_STATS.items():
        w, h = size_of(sprites.path(stats['sprite'], 0))
        assert h >= stats['hb'][1], (kind, h)                                     # 그림이 충돌 박스보다 작지 않다
    for name in ('n09_idle', 'enemy_guard_idle', 'enemy_hound_idle', 'boss_ark_idle'):
        assert size_of(sprites.path(name, 0))


def test_place_puts_the_pivot_on_the_feet():
    # 가로 86, 기준점 x=37인 그림: 가운데(43)에서 6px 오른쪽으로 옮겨 그려야 기준점이 발 위치에 온다
    assert sprites.place('n09_walk', 1, 86, 125, 1) == (6, 1)
    # 좌우 반전하면 기준점이 반대편(86 - 1 - 37 = 48)으로 가므로 5px 왼쪽으로
    assert sprites.place('n09_walk', 1, 86, 125, -1) == (-5, 1)
    assert sprites.place('n09_idle', 0, 42, 125, 1) == (0, sprites.STILL_FOOT_MARGIN)   # 정지 그림은 가운데
    # 도약 공중 프레임은 그림 안에서 41px 떠 있다: 그만큼 더 내려 그려 이미 공중인 몸에 또 띄우지 않는다
    _, foot_ground = sprites.place('boss_crasher_leap', 1, 226, 211, 1)
    _, foot_air = sprites.place('boss_crasher_leap', 2, 226, 211, 1)
    assert foot_air - foot_ground == 41


def test_ui_images_exist():
    import items
    for item_id in list(items.ITEMS) + ['shard']:
        assert size_of(f'ui/icon_{item_id}.png') == (48, 48), item_id
    for kind in ('gold', 'shop', 'gone'):
        assert size_of(f'ui/pedestal_{kind}.png') == (120, 150), kind
    for name in ('screen_death.png', 'screen_ending.png'):
        assert size_of('backgrounds/' + name) == (config.SCREEN_W, config.SCREEN_H)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
