"""방 템플릿·스테이지 배치 검사: 모든 방이 설계 기준을 지키고, 스테이지가 이어져 있으며(보스까지 길, 황금방·정비방 가지),
이동 가능 범위 계산이 불가능한 방을 걸러내는지 확인 (창 없이 실행). 실행: python tests/test_rooms.py"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import config  # noqa: E402
import room_check  # noqa: E402
from room import Room  # noqa: E402
from room_check import RoomGraph, analyze  # noqa: E402
from stage import OPPOSITE, STEP, Stage, load_layout, template_exits  # noqa: E402


def read_room(name):
    path = os.path.join(HERE, '..', 'data', 'rooms', name + '.txt')
    with open(path, encoding='utf-8') as f:
        return [line.rstrip('\r') for line in f.read().split('\n') if line.strip('\r')]


def blank_room(cols=32, rows=18):
    grid = [['.'] * cols for _ in range(rows)]
    for c in range(cols):
        grid[0][c] = grid[rows - 2][c] = grid[rows - 1][c] = '#'
    for r in range(rows):
        grid[r][0] = grid[r][-1] = '#'
    s = rows - 3
    for r in (s - 2, s - 1, s):
        grid[r][0], grid[r][-1] = 'L', 'R'
    return grid


def as_rows(grid):
    return [''.join(r) for r in grid]


def used_templates():
    start, layout = load_layout()
    return {info['template'] for info in layout.values()}


# ----- 점프 한계와 설계 기준 -----
def test_jump_limits_come_from_config():
    lim = room_check.jump_limits()
    assert lim['rise_single'] == 3 and lim['rise_double'] == 6      # 3.75칸, 약 7.5칸에서 여유를 둔 값
    assert lim['reach_single'] >= 3 and lim['reach_double'] >= 7


def test_every_template_passes_all_checks():
    for name in sorted(used_templates()):
        problems = analyze(read_room(name))
        assert not problems, (name, problems)


def test_no_unused_room_files():
    on_disk = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(HERE, '..', 'data', 'rooms', '*.txt'))}
    assert on_disk - used_templates() <= {'test_01'}, f'스테이지에 안 쓰는 방 파일: {on_disk - used_templates()}'  # test_01은 시험용


def test_rooms_are_not_all_one_screen_and_have_vertical_structure():
    """화면보다 큰 방이 여럿 있고(카메라 필요), 방마다 서 있는 높이가 3층 이상이다."""
    big = 0
    for name in sorted(used_templates()):
        rows = read_room(name)
        room = Room(rows)
        if room.width > config.SCREEN_W or room.height > config.SCREEN_H:
            big += 1
        g = RoomGraph(rows)
        tiers = {r for c, r in g.stand_cells()}
        assert len(tiers) >= 3, f'{name}: 서 있는 높이가 {len(tiers)}층뿐이다'
    assert big >= 5, f'화면보다 큰 방이 {big}개뿐이다'


def test_door_types_in_templates():
    """위·아래 출입구를 가진 방이 있고, 한 방에 문이 여러 개인 방(선택지)이 있다."""
    sides = {name: set(template_exits(name)) for name in used_templates()}
    assert any('U' in s for s in sides.values()) and any('D' in s for s in sides.values())
    assert sum(1 for s in sides.values() if len(s) >= 3) >= 2


# ----- 스테이지 배치 -----
def graph_of(layout, stage):
    links = {c: {stage.neighbour(c, d) for d in stage.links_of(c)} for c in layout}
    return links


def bfs(links, start):
    seen, todo = {start: 0}, [start]
    while todo:
        c = todo.pop(0)
        for n in links[c]:
            if n not in seen:
                seen[n] = seen[c] + 1
                todo.append(n)
    return seen


def test_stage_links_are_symmetric_and_connected():
    start, layout = load_layout()
    stage = Stage(None, layout, start)
    links = graph_of(layout, stage)
    for c, ns in links.items():
        for n in ns:
            assert c in links[n], f'{c} -> {n} 문이 한쪽에만 열려 있다'
    assert len(bfs(links, start)) == len(layout), '이어지지 않은 방이 있다'


def test_stage_has_branches_with_gold_and_shop_before_boss():
    """보스는 시작에서 멀고, 황금방·정비방이 보스로 가는 최단 길 밖의 가지에 있다. 방이 충분히 많다."""
    start, layout = load_layout()
    stage = Stage(None, layout, start)
    links = graph_of(layout, stage)
    types = {c: info.get('type', 'combat') for c, info in layout.items()}
    boss = [c for c, t in types.items() if t == 'boss']
    assert len(boss) == 1 and len(layout) >= 10
    dist = bfs(links, start)
    assert dist[boss[0]] >= 4                                        # 보스까지 방 여러 개를 지난다
    # 최단 경로 복원
    path, cur = [boss[0]], boss[0]
    while cur != start:
        cur = min(links[cur], key=lambda n: dist[n])
        path.append(cur)
    for special in ('gold', 'shop'):
        found = [c for c, t in types.items() if t == special]
        assert found, f'{special} 방이 없다'
        assert all(c not in path for c in found), f'{special} 방이 보스로 가는 길 위에 있다 (선택하는 가지여야 한다)'
    combat_branch = [c for c, t in types.items() if t == 'combat' and c not in path]
    assert len(combat_branch) >= 3                                   # 돌며 조각을 모을 전투 방이 가지에 있다


def test_stage_start_has_two_ways_and_hub_has_four():
    start, layout = load_layout()
    stage = Stage(None, layout, start)
    assert len(stage.links_of(start)) >= 2                           # 첫 방부터 갈림길
    assert max(len(stage.links_of(c)) for c in layout) == 4          # 사방으로 이어진 허브


# ----- 검사기가 불가능한 방을 걸러내는지 -----
def test_checker_rejects_wall_that_cannot_be_crossed():
    grid = blank_room()
    for r in range(1, 16):
        grid[r][15] = '#'                                           # 천장까지 막힌 벽
    problems = analyze(as_rows(grid))
    assert any('나갈 수 없다' in p for p in problems)


def test_checker_rejects_jump_that_is_too_high():
    grid = blank_room()
    for r in range(7, 16):
        for c in range(10, 14):
            grid[r][c] = '#'                                        # 9칸 높이 기둥은 못 넘고 윗길도 없다
    for c in range(1, 31):
        grid[1][c] = '#'
    assert analyze(as_rows(grid))


def test_checker_accepts_stairs_within_jump_limits():
    grid = blank_room()
    for c in range(10, 14):
        grid[14][c] = grid[15][c] = '#'                             # 2칸 높이 단: 넘을 수 있다
    assert analyze(as_rows(grid)) == []


def test_checker_flags_unreachable_spawn_and_spike_near_door():
    grid = blank_room()
    grid[3][16] = 's'                                               # 공중에 떠 있는 스폰
    grid[15][2] = '^'
    problems = analyze(as_rows(grid))
    assert any('서 있을 수 없는 칸' in p for p in problems) and any('가시' in p for p in problems)


def test_spawns_keep_distance_from_entrances():
    grid = blank_room()
    grid[15][4] = 's'                                               # 입구에서 3칸
    assert any('안전 시작' in p for p in analyze(as_rows(grid)))


def test_checker_rejects_up_door_without_platform_to_reach_it():
    grid = blank_room(32, 24)
    for c in (14, 15, 16):
        grid[0][c] = 'U'                                            # 천장 구멍은 있는데 올라갈 발판이 없다
    problems = analyze(as_rows(grid))
    assert any('U 문으로 나갈 수 없다' in p for p in problems)


def test_checker_accepts_up_door_with_stairs():
    grid = blank_room(32, 24)
    for c in (14, 15, 16):
        grid[0][c] = 'U'
    for r, c0, c1 in ((18, 4, 9), (15, 8, 13), (12, 12, 17), (9, 13, 19), (6, 12, 19)):   # 3칸씩 오르는 계단
        for c in range(c0, c1 + 1):
            grid[r][c] = '='
    assert analyze(as_rows(grid)) == []


def test_checker_handles_floor_hole_door():
    grid = blank_room(32, 20)
    for c in (14, 15, 16):
        grid[18][c] = grid[19][c] = 'D'                             # 바닥 구멍
    assert analyze(as_rows(grid)) == []



def test_autotile_masks_mark_exposed_edges():
    rows = ['#' * 20] + ['#' + '.' * 18 + '#'] * 10 + ['#' + '.' * 6 + '###' + '.' * 9 + '#'] + ['#' * 20] * 2
    room = Room(rows)
    assert room.masks[(8, 11)] == 1                                                # 가운데 블록: 윗면만 드러난다
    assert room.masks[(7, 11)] == 1 | 8 and room.masks[(9, 11)] == 1 | 2           # 양 끝은 옆면도 드러난다
    assert room.masks[(5, 12)] == 1 and room.masks[(8, 12)] == 0                   # 바닥 첫 줄은 위만, 둘째 줄은 안쪽
    assert room.masks[(0, 0)] == 0                                                 # 방 모서리 벽은 안쪽 칸이다


def test_room_look_is_deterministic_and_keeps_markers_clear():
    from room import Room
    a, b = Room.load('hub_cavern'), Room.load('hub_cavern')
    assert a.decor == b.decor and a.back == b.back                                 # 같은 방은 늘 같은 모양
    assert a.decor, '소품이 하나도 없다'
    markers = {(c, r) for r, line in enumerate(a.rows) for c, ch in enumerate(line) if ch in 'PEstIB'}
    for kind, col, row in a.decor:
        assert all(abs(col - mc) > 3 or abs(row - mr) > 3 for mc, mr in markers), '스폰·진열대 근처에 소품이 있다'
    assert Room.load('boss_arena', theme='nope').theme == 'cell'                   # 모르는 테마는 기본으로


def test_every_theme_has_a_tile_set_and_background():
    import room as room_module
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    for name in room_module.THEMES:
        assert os.path.exists(os.path.join(root, 'assets', 'tiles', f'tile_set_{name}.png')), name
        assert os.path.exists(os.path.join(root, 'assets', 'backgrounds', f'bg_{name}.png')), name

if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
