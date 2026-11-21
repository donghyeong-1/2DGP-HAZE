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
            ax, ay = sprites.FRAME_ANCHOR.get((name, n), (px, py))       # 그림마다 기준점이 따로 있으면 그것 (T25 피격 2장째)
            if (name, n) not in sprites.FRAME_ANCHOR:
                sizes.add((w, h))
            assert 0 < ax < w and 0 < ay <= h, (name, n, (w, h))
        assert len(sizes) == 1, f'{name}: 프레임마다 캔버스가 다르다 {sizes}'      # 한 동작의 프레임은 캔버스가 같다 (기준점을 따로 둔 그림 빼고)


def test_still_sprites_exist_for_every_enemy():
    for kind, stats in config.ENEMY_STATS.items():
        w, h = size_of(sprites.path(stats['sprite'], 0))
        assert h >= stats['hb'][1], (kind, h)                                     # 그림이 충돌 박스보다 작지 않다
    for name in ('n09_idle', 'enemy_guard_idle', 'enemy_hound_idle', 'boss_ark_idle'):
        assert size_of(sprites.path(name, 0))


def test_place_puts_the_pivot_on_the_feet():
    # 걷기(가로 74, 기준점 (36, 126)): 가운데(37)에서 1px 오른쪽으로 옮겨 그려야 기준점이 발 위치에 온다. 발 아래 1px
    assert sprites.place('n09_walk', 1, 74, 127, 1) == (1, 1)
    # 좌우 반전하면 기준점이 반대편(74 - 1 - 36 = 37)으로 가므로 가운데 그대로
    assert sprites.place('n09_walk', 1, 74, 127, -1) == (0, 1)
    # 위치 보정 SHIFT가 있는 프레임은 그만큼 더 옮긴다 (앞쪽 +, 반전하면 반대로)
    w, h = size_of(sprites.path('n09_punch', 1))
    _, px, py = sprites.FRAMES['n09_punch']
    sdx, sdy = sprites.SHIFT[('n09_punch', 1)]
    assert sprites.place('n09_punch', 1, w, h, 1) == (w // 2 - px + sdx, h - py - sdy)
    assert sprites.place('n09_punch', 1, w, h, -1) == (w // 2 - (w - 1 - px) - sdx, h - py - sdy)
    assert sprites.place('n09_idle', 0, 42, 125, 1) == (0, sprites.STILL_FOOT_MARGIN)   # 정지 그림은 가운데
    # 도약 공중 프레임은 그림 안에서 41px 떠 있다: 그만큼 더 내려 그려 이미 공중인 몸에 또 띄우지 않는다
    _, foot_ground = sprites.place('boss_crasher_leap', 1, 226, 211, 1)
    _, foot_air = sprites.place('boss_crasher_leap', 2, 226, 211, 1)
    assert foot_air - foot_ground == 41


def test_walk_shift_keeps_the_body_steady():
    """걷기 보정은 몇 px 안쪽이고, 다리가 몸 밑을 지날 때만 몸을 들어 올린다 (발이 바닥 아래로 내려가지 않는다)."""
    for (name, n), (dx, dy) in sprites.SHIFT.items():
        assert n <= sprites.count(name) and 0 <= dy <= 3, (name, n)
        if name.endswith('_walk'):
            assert abs(dx) <= 6, (name, n)


def test_ui_images_exist():
    import items
    for item_id in list(items.ITEMS) + ['shard']:
        assert size_of(f'ui/icon_{item_id}.png') == (48, 48), item_id
    for kind in ('gold', 'shop', 'gone'):
        assert size_of(f'ui/pedestal_{kind}.png') == (120, 150), kind
    for name in ('screen_death.png', 'screen_ending.png'):
        assert size_of('backgrounds/' + name) == (config.SCREEN_W, config.SCREEN_H)


def test_walk_and_run_cycles_alternate_left_and_right_steps():
    """걷기·달리기 반복은 왼발·오른발 걸음이 번갈아야 한다 (T19 달리기는 같은 걸음이 두 번이라 발이 교차하지 않았다)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
    import check_gait
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sprites', 'unified')
    for name in ('n09_walk', 'n09_run'):
        paths = [os.path.join(root, f'{name}_{i}.png') for i in range(1, 9)]
        assert check_gait.gait_ratio(paths)[2] >= check_gait.PASS_RATIO, name


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
