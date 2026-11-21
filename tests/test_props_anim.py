"""움직이는 배경 소품 테스트 (창 없이). 실행: python tests/test_props_anim.py

2026-11-21 퀄리티 계획 2-1 (Codex T28 적용): 테마마다 움직이는 소품 3종(4장 반복, 0.12초)을 방에 자동으로 놓는다.
- 천장에 매다는 것은 바로 위가 벽, 바닥에 놓는 것은 바로 아래가 벽, 벽에서 뿜는 것은 왼쪽이 벽인 칸에 놓는다.
- 그림이 벽·발판·가시를 덮지 않고, 문·스폰·진열대 근처와 서로 겹치는 자리는 피한다.
- 전투 방마다 3개 이상 (끝난 기준: "방마다 3개 이상 움직이는 것").
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

from PIL import Image  # noqa: E402

import config  # noqa: E402
import props_anim  # noqa: E402
from room import Room  # noqa: E402

ROOT = os.path.join(HERE, '..')
COMBAT_ROOMS = ('arena_05', 'cover_04', 'crossing', 'hall_01', 'hub_cavern', 'pit_02', 'start_hall', 'tower_03', 'well_room')


def test_every_theme_has_three_props_with_four_same_size_frames():
    for theme in ('cell', 'foundry', 'haze', 'hideout'):
        names = props_anim.PROPS[theme]
        assert 2 <= len(names) <= 3, theme
        for name in names:
            sizes = {Image.open(os.path.join(ROOT, 'assets', 'props', f'{theme}_{name}_{i}.png')).size for i in (1, 2, 3, 4)}
            assert len(sizes) == 1, (theme, name, sizes)                 # 4장이 같은 캔버스 (기준점이 흔들리지 않게)


def test_frames_loop_every_0_12_seconds():
    assert [props_anim.frame_at(t) for t in (0.0, 0.11, 0.13, 0.25, 0.37, 0.49)] == [1, 1, 2, 3, 4, 1]


def _cells(room, p):
    """그림 사각형(가장자리 8px 빼고)이 덮는 칸."""
    t, m = config.TILE, 8
    c0, c1 = int((p.left + m) // t), int((p.left + p.w - m) // t)
    top_row = room.row_of(p.bottom + p.h - m)
    bottom_row = room.row_of(p.bottom + m)
    return {(c, r) for c in range(c0, c1 + 1) for r in range(top_row, bottom_row + 1)}


def test_combat_rooms_get_three_props_on_clear_ground():
    for theme in ('cell', 'foundry', 'haze'):
        for name in COMBAT_ROOMS:
            room = Room.load(name, {'L', 'R'}, theme=theme)
            placed = room.anim_props
            assert len(placed) >= 3, (theme, name, len(placed))
            taken = set()
            for p in placed:
                cells = _cells(room, p)
                assert all(room.tile_at(c, r) == '.' for c, r in cells), (theme, name, p.name)   # 벽·발판·가시를 덮지 않는다
                assert not cells & room.near_marker, (theme, name, p.name)                   # 문·스폰 근처를 피한다
                assert not cells & taken, (theme, name, p.name)                              # 서로 겹치지 않는다
                taken |= cells
                assert p.name.startswith(theme + '_')


def test_mount_rules():
    room = Room.load('hall_01', {'L', 'R'}, theme='haze')
    t = config.TILE
    for p in room.anim_props:
        kind = props_anim.KIND[p.name.split('_', 1)[1]]
        ax, ay = props_anim.ANCHOR[p.name.split('_', 1)[1]]
        x, y = p.left + ax, p.bottom + p.h - ay                       # 기준점의 월드 좌표
        col, row = int(x // t), room.row_of(y - 1)
        if kind == 'ceiling':
            assert y % t == 0 and room.tile_at(col, room.row_of(y + 1)) == '#', p.name   # 바로 위가 벽
        elif kind == 'floor':
            assert y % t == 0 and room.tile_at(col, room.row_of(y - 1)) == '#', p.name   # 바로 아래가 벽


def test_special_rooms_and_placement_is_fixed():
    gold = Room.load('gold_room', {'L'}, theme='gold')
    assert gold.anim_props == []                                      # 황금방·정비방·보스방은 자기 소품만
    a = Room.load('hall_01', {'L', 'R'}, theme='cell').anim_props
    b = Room.load('hall_01', {'L', 'R'}, theme='cell').anim_props
    assert [(p.name, p.left, p.bottom) for p in a] == [(p.name, p.left, p.bottom) for p in b]   # 같은 방은 같은 자리
    hide = Room.load('hideout_room', set(), theme='hideout')                # 은신처는 손으로 정한 자리: 정비사 옆 모루, 화로 둘
    assert sorted(p.name for p in hide.anim_props) == ['hideout_anvil', 'hideout_brazier', 'hideout_brazier']
    floor_y = 2 * config.TILE
    assert all(p.bottom + p.h - props_anim.ANCHOR[p.name.split('_', 1)[1]][1] == floor_y for p in hide.anim_props)


# ----- 멈춘 장식 (Codex T31, 2026-11-21 계획 2-4): 테마마다 바닥 3종·벽 3종, 움직이는 소품 다음에 방마다 3개 -----
def test_static_decor_files_match_table():
    for theme in ('cell', 'foundry', 'haze'):
        names = props_anim.DECOR[theme]
        assert len(names) == 6, theme
        for name in names:
            im = Image.open(os.path.join(ROOT, 'assets', 'decor', f'{theme}_{name}.png'))
            assert im.size == props_anim.SIZE[name], (theme, name, im.size)


def test_static_decor_is_placed_clear_of_everything():
    for theme in ('cell', 'foundry', 'haze'):
        for name in COMBAT_ROOMS:
            room = Room.load(name, {'L', 'R'}, theme=theme)
            assert len(room.decor_props) >= 2, (theme, name, len(room.decor_props))
            taken = set()
            for p in room.anim_props + room.decor_props:
                cells = _cells(room, p)
                assert all(room.tile_at(c, r) == '.' for c, r in cells), (theme, name, p.name)
                assert not cells & room.near_marker, (theme, name, p.name)
                assert not cells & taken, (theme, name, p.name)              # 움직이는 소품과도 겹치지 않는다
                taken |= cells
            for p in room.decor_props:
                if props_anim.KIND[p.name.split('_', 1)[1]] == 'floor':
                    assert p.bottom % config.TILE == 0, p.name               # 바닥 소품의 밑줄이 바닥에 닿는다
    assert Room.load('gold_room', {'L'}, theme='gold').decor_props == []
    assert Room.load('hideout_room', set(), theme='hideout').decor_props == []


# ----- 받침 규칙 (2026-11-21 지형 지물 배치 재검토): 소품은 무언가에 붙어 있어야 한다 -----
def _cols(p):
    t = config.TILE
    return range(int((p.left + props_anim.MARGIN) // t), int((p.left + p.w - props_anim.MARGIN) // t) + 1)


def _rows(room, p):
    return range(room.row_of(p.bottom + p.h - props_anim.MARGIN), room.row_of(p.bottom + props_anim.MARGIN) + 1)


def mounted(room, p):
    """소품 그림이 받침에 닿아 있는가: 바닥 것은 밑 전체가 벽 위, 천장 것은 위 전체가 벽 아래,
    벽 것(back·wall)은 위가 천장에 붙거나 옆이 벽에 붙는다."""
    prop = p.name.split('_', 1)[1]
    kind = props_anim.KIND[prop]
    solid = lambda c, r: room.tile_at(c, r) == '#'          # noqa: E731
    below = room.row_of(p.bottom - 1)
    above = room.row_of(p.bottom + p.h + 1)
    if kind == 'floor':
        return all(solid(c, below) for c in _cols(p))
    under_ceiling = all(solid(c, above) for c in _cols(p))
    if kind == 'ceiling':
        return under_ceiling
    t = config.TILE
    left_col, right_col = int((p.left - 1) // t), int((p.left + p.w + 1) // t)
    on_left = all(solid(left_col, r) for r in _rows(room, p))
    on_right = all(solid(right_col, r) for r in _rows(room, p))
    return under_ceiling or on_left or on_right


def test_every_prop_is_mounted_on_something():
    for theme in ('cell', 'foundry', 'haze'):
        for name in COMBAT_ROOMS + ('bridge_06', 'stairs_07', 'pillars_08', 'shaft_09', 'terrace_10', 'twin_11'):
            room = Room.load(name, {'L', 'R', 'U', 'D'}, theme=theme)
            for p in room.anim_props + room.decor_props:
                assert mounted(room, p), (theme, name, p.name, p.left, p.bottom)


def test_drip_is_not_auto_placed():
    """물방울은 관(천장)과 웅덩이(바닥)가 한 그림이라 방 높이에 맞출 수 없다: 자동 배치에서 뺀다."""
    assert 'drip' not in props_anim.PROPS['cell']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
