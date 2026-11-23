"""구역 배치 절차 생성 (v7, 2026-11-24, docs/plan_v7.md 5-E). 매판 시드로 방 격자를 새로 만든다.

규칙 (방 템플릿의 문 방향을 지킨다, stage.template_exits):
1. 시작 방 (0,0)에서 오른쪽으로 본 경로(전투방 main개), 오른쪽 끝에 끝 방(구역 1 관문, 2·3 보스방).
2. 본 경로 중간 한 방에서 위로 갈래(전투방 branch개)를 오른쪽으로 뻗는다. 그 끝 오른쪽에 균열방(왼쪽 문만).
3. 황금방(아래 문만)은 위가 빈 방 위에, 정비방(위 문만)은 본 경로 방 아래에 붙인다.
4. 전투방 템플릿은 필요한 문 방향을 모두 가진 것 중에서 고른다 (남는 문은 이웃이 없으면 열리지 않는다).
5. 적: 템플릿의 E 칸은 구역 적 목록에서 무게대로, s·t 칸(폐인·투척병)은 구역에 맞게 바꾼다(swap).
pico2d와 무관한 순수 로직. 결과는 data/stages/stageN.py와 같은 모양의 (START, layout) 딕셔너리다.
"""
import random

# 문 방향별로 고를 수 있는 전투 템플릿 (stage.template_exits 기준, 2026-11-24 data/rooms)
COMBAT = {
    'hall_01': {'L', 'R'}, 'pit_02': {'L', 'R'}, 'tower_03': {'L', 'R'}, 'cover_04': {'L', 'R'}, 'arena_05': {'L', 'R'},
    'bridge_06': {'L', 'R'}, 'stairs_07': {'L', 'R'}, 'pillars_08': {'L', 'R'},
    'crossing': {'L', 'R', 'U', 'D'}, 'hub_cavern': {'L', 'R', 'U', 'D'}, 'shaft_09': {'L', 'R', 'U', 'D'},
    'terrace_10': {'L', 'R', 'U', 'D'}, 'twin_11': {'L', 'R', 'U', 'D'}, 'well_room': {'D', 'R'},
}
# 구역 규모·특수방·적. pool: E 칸에 넣는 적과 무게(손으로 짠 배치의 등장 비율), swap: s·t 칸을 바꿀 후보
SPECS = {
    'stage1': dict(combat=8, specials=('gold', 'shop', 'rift'), end='gate', main=(5, 6),
                   pool={'slum': 5, 'thrower': 4, 'guard': 2, 'rat': 2, 'shaman': 1, 'hound': 1},
                   swap={}, high_haze=(1, 2)),
    'stage2': dict(combat=8, specials=('gold', 'shop', 'rift'), end='boss', boss='crasher', main=(5, 6),
                   pool={'thrower': 3, 'hound': 3, 'guard': 3, 'drone': 2, 'cart': 2, 'slum': 1},
                   swap={'slum': ('hound', 'guard', 'cart'), 'thrower': ('thrower', 'drone')}, high_haze=(1, 3)),
    'stage3': dict(combat=5, specials=('shop', 'rift'), end='boss', boss='ark', final='heart', main=(3, 4),
                   pool={'hound': 3, 'knight': 3, 'eye': 2, 'wraith': 2, 'guard': 1, 'thrower': 1},
                   swap={'slum': ('hound', 'knight'), 'thrower': ('eye', 'knight')}, high_haze=(1, 2)),
}
GENERIC_SLOTS = 6            # E 칸에 채울 적 수 (템플릿이 쓰는 만큼만 쓰인다)
STEP = {'L': (-1, 0), 'R': (1, 0), 'U': (0, 1), 'D': (0, -1)}
OPP = {'L': 'R', 'R': 'L', 'U': 'D', 'D': 'U'}


def _weighted(rng, weights):
    keys = sorted(weights)
    r = rng.random() * sum(weights[k] for k in keys)
    for k in keys:
        r -= weights[k]
        if r <= 0:
            return k
    return keys[-1]


def _shape(rng, spec):
    """방 좌표와 종류, 이어야 할 이웃(edges)을 정한다."""
    n_main = rng.randint(*spec['main'])
    n_main = min(n_main, spec['combat'] - 1)
    n_branch = spec['combat'] - n_main
    rooms = {(0, 0): 'start'}
    edges = set()

    def link(a, b):
        edges.add((a, b))
        edges.add((b, a))

    prev = (0, 0)
    for x in range(1, n_main + 1):                      # 본 경로
        rooms[(x, 0)] = 'combat'
        link(prev, (x, 0))
        prev = (x, 0)
    end = (n_main + 1, 0)
    rooms[end] = spec['end']
    link(prev, end)
    root = (rng.randint(1, max(1, n_main - n_branch)), 0)   # 위 갈래가 시작되는 본 경로 방
    prev = root
    for k in range(n_branch):                           # 위 갈래 (오른쪽으로)
        c = (root[0] + k, 1)
        rooms[c] = 'combat'
        link(prev, c)
        prev = c
    branch_end = prev
    if 'rift' in spec['specials']:
        rift = (branch_end[0] + 1, 1)
        rooms[rift] = 'rift'
        link(branch_end, rift)
    if 'gold' in spec['specials']:                      # 위가 빈 위 갈래 방 위에
        c = rng.choice([c for c in rooms if c[1] == 1 and rooms[c] == 'combat'])
        rooms[(c[0], 2)] = 'gold'
        link(c, (c[0], 2))
    if 'shop' in spec['specials']:                      # 본 경로 전투방 아래 (끝 방 바로 앞은 피한다)
        c = rng.choice([c for c in rooms if c[1] == 0 and rooms[c] == 'combat' and c[0] < n_main] or
                       [c for c in rooms if c[1] == 0 and rooms[c] == 'combat'])
        rooms[(c[0], -1)] = 'shop'
        link(c, (c[0], -1))
    return rooms, edges


def _needs(c, edges):
    return {d for d, (dx, dy) in STEP.items() if (c, (c[0] + dx, c[1] + dy)) in edges}


def _accidental(c, exits, rooms, edges, chosen):
    """이 템플릿을 쓰면 의도하지 않은 이웃과 문이 이어지는가 (닫힌 방 종류나 이미 고른 템플릿과)."""
    from stage import template_exits
    for d in exits:
        n = (c[0] + STEP[d][0], c[1] + STEP[d][1])
        if n in rooms and (c, n) not in edges:
            other = chosen.get(n)
            if other is not None and OPP[d] in template_exits(other):
                return True
    return False


def _template(rng, c, kind, spec, edges, rooms, chosen):
    if kind == 'start':
        return 'start_hall'
    if kind == 'gold':
        return 'gold_room'
    if kind == 'shop':
        return 'shop_room'
    if kind == 'rift':
        return 'rift_room'
    if kind == 'boss':
        return 'boss_arena'
    if kind == 'gate':
        return 'arena_05'
    need = _needs(c, edges)
    options = [t for t, ex in sorted(COMBAT.items()) if need <= ex and not _accidental(c, ex, rooms, edges, chosen)]
    options = options or [t for t, ex in sorted(COMBAT.items()) if need <= ex]
    return rng.choice(options)


def _enemies(rng, spec):
    return [_weighted(rng, spec['pool']) for _ in range(GENERIC_SLOTS)]


def generate(name, seed):
    """(START, layout). 같은 (name, seed)면 같은 배치."""
    spec = SPECS[name]
    rng = random.Random(f'mapgen:{name}:{seed}')
    rooms, edges = _shape(rng, spec)
    layout, chosen = {}, {}
    for c in sorted(rooms, key=lambda c: (c[1] != 0, c)):      # 본 경로부터 (문 충돌 검사에 앞 방을 쓴다)
        kind = rooms[c]
        t = _template(rng, c, kind, spec, edges, rooms, chosen)
        chosen[c] = t
        info = {'template': t, 'type': kind}
        if kind == 'combat':
            info['enemies'] = _enemies(rng, spec)
            if spec['swap']:
                info['swap'] = {k: rng.choice(v) for k, v in spec['swap'].items()}
        elif kind == 'boss':
            info['boss'] = spec['boss']
            if spec.get('final'):
                info['final'] = spec['final']
        elif kind == 'gate':
            info['swap'] = {'slum': 'guard', 'thrower': 'hound'}   # 관문: 정예 간수·사냥개 (손으로 짠 배치와 같다)
        layout[c] = info
    combats = sorted(c for c in layout if layout[c]['type'] == 'combat')
    for c in rng.sample(combats, min(len(combats), rng.randint(*spec['high_haze']))):
        layout[c]['high_haze'] = True
    return (0, 0), layout
