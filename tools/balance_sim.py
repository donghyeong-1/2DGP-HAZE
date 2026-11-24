"""밸런스 시뮬레이터: 실제 게임 코드(Player, Enemy, Boss, 무기, 게이지)를 창 없이 돌려 전투 수치를 잰다.

봇 플레이어가 가장 가까운 적에게 다가가 무기마다 정해진 방식으로 공격한다.
- stand : 피하지 않고 맞붙는다 (가장 서툰 플레이의 하한)
- dodge : 적의 공격 예고(깜빡임)를 보면 반대쪽으로 대시한다 (예고를 읽는 플레이)

시나리오마다 여러 시드를 돌려 평균을 낸다. 시드는 적 위치와 난수를 바꾼다.
수치를 바꾸기 전에 --save로 기준을 저장하고, 바꾼 뒤 --compare로 차이를 본다.

실행 예:
  python tools/balance_sim.py                          # 전체 (시나리오 x 무기 x 봇, 시드 10개)
  python tools/balance_sim.py --scenario hound guard --weapon pipe --seeds 10
  python tools/balance_sim.py --scenario boss --gauge 60              # 게이지 60%로 시작
  python tools/balance_sim.py --save tools/balance_base.json
  python tools/balance_sim.py --compare tools/balance_base.json
  python tools/balance_sim.py --zones --seeds 20 --md out.md         # 무기 4종 x 구역 3개 표 (전투방·큰 방·구역 끝 싸움)
  python tools/balance_sim.py --zones --easy                          # 초보자 모드로
"""
import argparse
import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import config  # noqa: E402
import effects  # noqa: E402
import game_world  # noqa: E402
from enemy import Enemy  # noqa: E402
from player import Player  # noqa: E402
from room import Room  # noqa: E402

DT = 1 / 60
COLS, ROWS = 44, 18
FLOOR_Y = float((ROWS - 2) * config.TILE)        # 바닥 두 줄 위
PLAYER_X = 4 * config.TILE

# 시나리오: 이름 -> (적 목록 [(종류, 플레이어로부터 거리)], 제한 시간 초)
SCENARIOS = {
    'slum': ([('slum', 700)], 30),
    'thrower': ([('thrower', 800)], 30),
    'hound': ([('hound', 800)], 30),
    'guard': ([('guard', 700)], 40),
    'group': ([('slum', 650), ('hound', 900), ('thrower', 1300), ('slum', 1100)], 60),
    # 구역 새 적 (11/22 v5): 쥐는 무리 3마리, 눈은 벽에 붙는다, 무당은 슬럼에 보호막을 건다
    'rat': ([('rat', 800)], 30),
    'shaman': ([('shaman', 1000), ('slum', 700), ('thrower', 1100)], 60),
    'eye': ([('eye', 900)], 40),
    'knight': ([('knight', 800)], 40),
    'wraith': ([('wraith', 800)], 40),
    'drone': ([('drone', 900)], 40),
    'cart': ([('cart', 900)], 40),
    'boss': ([('boss', 900)], 90),
    'ark': ([('ark', 900)], 120),
}
# 구역 시나리오 (v8 7일 차, 2026-11-25): 실제 판처럼 구역 적 목록(mapgen.SPECS의 pool)에서 시드로 뽑고, 정예 확률(config.ELITE_CHANCE)을
# 따르고, 무리 수에 따라 물결로 나온다(stage._release_waves와 같은 규칙). 이름 -> (구역, 종류, 제한 시간 초)
#   room: 보통 전투방 (스폰 칸 5개), big: 큰 방 (config.BIG_ROOM_PACKS), gate: 구역 1 관문 (arena_05: 간수 3 + 사냥개 1, 한 번에)
ZONE_SCENARIOS = {
    'z1_room': ('stage1', 'room', 90), 'z1_big': ('stage1', 'big', 150), 'z1_gate': ('stage1', 'gate', 90),
    'z2_room': ('stage2', 'room', 90), 'z2_big': ('stage2', 'big', 150),
    'z3_room': ('stage3', 'room', 90), 'z3_big': ('stage3', 'big', 150),
}
ROOM_PACKS = 5                 # 보통 전투방의 스폰 칸 수 (템플릿이 4~6칸을 쓴다)
# 구역별 표에 쓰는 시나리오: 구역 -> [(이름, 표의 열 이름)]. 구역 끝 싸움은 1: 관문, 2: 크래셔, 3: 아크
ZONE_TABLE = {
    'stage1': [('z1_room', '전투방'), ('z1_big', '큰 방'), ('z1_gate', '관문')],
    'stage2': [('z2_room', '전투방'), ('z2_big', '큰 방'), ('boss', '크래셔')],
    'stage3': [('z3_room', '전투방'), ('z3_big', '큰 방'), ('ark', '아크')],
}
ALL_SCENARIOS = list(SCENARIOS) + list(ZONE_SCENARIOS)
WEAPONS = ('pipe', 'pistol', 'gauntlet', 'chain')
BOTS = ('stand', 'dodge')
# 무기마다 봇이 서는 거리(px): 철파이프는 붙고, 식칼은 떨어져 던지고, 건틀릿은 중간에서 충전
KEEP = {'pipe': 95, 'pistol': 420, 'gauntlet': 230, 'chain': 330}
# 건틀릿 봇이 철파이프로 바꾸는/돌아오는 게이지(%): 충전 하한보다 조금 위에서 바꾼다
GAUNTLET_LOW = config.GAUNTLET_FLOOR + 8.0
GAUNTLET_HIGH = GAUNTLET_LOW + 20.0


def arena():
    """평평한 시험장: 테두리 벽과 두 줄 바닥만 있다."""
    rows = [['.'] * COLS for _ in range(ROWS)]
    for c in range(COLS):
        rows[0][c] = rows[ROWS - 2][c] = rows[ROWS - 1][c] = '#'
    for r in range(ROWS):
        rows[r][0] = rows[r][COLS - 1] = '#'
    return Room([''.join(r) for r in rows], name='sim_arena')


def enemies():
    return [e for e in game_world.world[game_world.LAYER_ENEMY] if getattr(e, 'state', 'DEAD') != 'DEAD']


def spawn(kind, x, room, player):
    if kind == 'boss':
        from boss import Boss
        e = Boss(x, FLOOR_Y, room, player)
    elif kind == 'ark':
        from ark import Ark
        e = Ark(x, FLOOR_Y, room, player)
    else:
        import enemy_kinds
        y = 2 * config.TILE if kind in ('eye', 'wraith', 'drone') else FLOOR_Y   # 벽·공중 적(중력 없음)은 실제 바닥(아래 두 줄 위)에서 올린다
        foes = enemy_kinds.make_pack(kind, x, y, room, player)             # 새 적은 자기 클래스, 쥐는 무리
        for e in foes:
            game_world.add_object(e, game_world.LAYER_ENEMY)
        return foes[0]
    game_world.add_object(e, game_world.LAYER_ENEMY)
    return e


def in_windup(e):
    return e.state == 'ATTACK' and e.attack_time < e._windup_time()


def bot_step(p, bot, weapon_id, state):
    """한 프레임의 봇 입력. state는 봇이 기억하는 값(마지막 대시 시각 등)."""
    foes = enemies()
    p.left = p.right = False
    if not foes:
        p.attack_held = False
        return
    e = min(foes, key=lambda f: abs(f.x - p.x))
    side = 1 if e.x >= p.x else -1
    dist = abs(e.x - p.x)
    ex, ey = e.center if hasattr(e, 'center') else (e.x, e.y + 60)
    p.mouse_x, p.mouse_y = ex, ey

    # 바닥 파동(크래셔 충격파, 아크 흡수·과충전 파동)이 다가오면 점프로 넘는다 (예고를 읽는 플레이)
    if bot == 'dodge' and p.on_ground:
        for o in game_world.world[game_world.LAYER_EFFECT]:
            if type(o).__name__ in ('Shockwave', 'GaugeWave') and abs(o.y - p.y) < 40:
                ahead = (p.x - o.x) * o.dir                  # 파동이 나아가는 쪽으로 플레이어까지 남은 거리
                if 0 < ahead < 130:
                    p.request_jump()
                    break

    # 피하기: 가까운 적이 예고 중이면 반대쪽으로 대시 (한 예고에 한 번)
    # (예고가 끝나기 0.22초 전에 반응: 사람의 반응 시간 정도)
    attack_id = (id(e), e.attacks)
    if (bot == 'dodge' and in_windup(e) and dist < 520 and state.get('dodged') != attack_id
            and e._windup_time() - e.attack_time < 0.22):
        state['dodged'] = attack_id
        p.mouse_x, p.mouse_y = p.x - side * 400, p.center[1]
        p.request_dash()
        p.mouse_x, p.mouse_y = ex, ey
        return

    # 건틀릿은 게이지를 태우는 무기: 게이지가 낮으면 철파이프로 바꿔 채우고, 충분히 차면 다시 든다 (무기 2칸의 의도된 쓰임)
    if weapon_id == 'gauntlet' and not getattr(p.weapon, 'charging', False):
        if p.weapon.weapon_id == 'gauntlet' and p.gauge.value < GAUNTLET_LOW:
            p.swap_weapon(0)
        elif p.weapon.weapon_id == 'pipe' and p.gauge.value > GAUNTLET_HIGH:
            p.swap_weapon(1)
    held = p.weapon.weapon_id
    keep = KEEP[held]
    # 머리 위에 뜬 적(용접 드론 등)은 근접 무기로 닿지 않는다: 밑에 오면 뛰어올라 친다 (11/25, 그 전에는 드론을 못 잡았다)
    if held in ('pipe', 'gauntlet') and ey - p.center[1] > 110 and dist < 140 and p.on_ground:
        p.request_jump()
    if dist > keep + 20:
        p.right, p.left = side > 0, side < 0
    elif held != 'pipe' and dist < keep * 0.5:
        p.right, p.left = side < 0, side > 0            # 원거리 무기는 너무 가까우면 물러난다
    in_reach = dist <= keep + 40
    if held == 'gauntlet':
        w = p.weapon
        if w.charging:
            if w.charge_ratio >= 1.0 and (in_reach or p.gauge.value < GAUNTLET_LOW):
                p.attack_held = False                    # 다 찼으면 사거리 안에서, 게이지가 낮으면 바로 뗀다
        elif in_reach:
            p.attack_held = True
            p.request_attack()
    elif in_reach:
        p.request_attack()


def zone_waves(scenario, seed):
    """구역 시나리오의 물결 목록: [[(종류, 정예 수식어 또는 None), ...], ...]. 같은 시드면 같은 구성."""
    import mapgen
    import stage as stage_mod
    zone, shape, _limit = ZONE_SCENARIOS[scenario]
    rng = random.Random(f'sim:{scenario}:{seed}')
    if shape == 'gate':
        kinds = ['guard', 'guard', 'guard', 'hound']
    else:
        n = config.BIG_ROOM_PACKS if shape == 'big' else ROOM_PACKS
        kinds = [mapgen._weighted(rng, mapgen.SPECS[zone]['pool']) for _ in range(n)]
    packs = [(k, stage_mod.roll_elite(rng, zone)) for k in kinds]
    n_waves = 1
    if shape != 'gate' and len(packs) >= config.WAVE_MIN_PACKS:
        n_waves = 3 if len(packs) >= config.WAVE_THREE_PACKS else 2
    elites = [pk for pk in packs if pk[1]]
    normals = [pk for pk in packs if not pk[1]]
    size = -(-len(packs) // n_waves)
    waves = []
    for _ in range(n_waves - 1):
        if normals[:size]:
            waves.append(normals[:size])
        normals = normals[size:]
    if normals or elites:
        waves.append(normals + elites)
    return waves


def spawn_wave(wave, room, p, rng):
    """물결 하나를 시험장에 흩어 세운다 (플레이어에서 600~1700px). 세운 적 수를 돌려준다."""
    count = 0
    for i, (kind, mod) in enumerate(wave):
        d = 600 + (i * 1100 // max(1, len(wave) - 1) if len(wave) > 1 else 300) + rng.randint(-60, 60)
        x = min(room.width - 2 * config.TILE, PLAYER_X + d)
        before = len(game_world.world[game_world.LAYER_ENEMY])
        e = spawn(kind, x, room, p)
        added = game_world.world[game_world.LAYER_ENEMY][before:]
        if mod and hasattr(e, 'make_elite'):
            e.make_elite(mod)
        count += len(added)
    return count


def run_one(scenario, weapon_id, bot, seed, gauge=None, meta_levels=None):
    random.seed(seed)
    game_world.clear()
    effects.reset()
    room = arena()
    p = Player(PLAYER_X, FLOOR_Y, room)
    if meta_levels:                                      # 은신처 정비사 영구 강화 ('max' = 모두 최대 단계)
        import meta
        levels = ({k: u['max'] for k, u in meta.UPGRADES.items()} if meta_levels == 'max' else meta_levels)
        meta.apply_levels(p, levels)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    for _ in range(20):
        game_world.update(DT)
    if weapon_id != 'pipe':
        p.give_weapon(weapon_id)
    p.attack_held = False
    if gauge is not None:                                # 시작 게이지를 정한다 (기본은 게임 시작값)
        p.gauge.value = float(gauge)
        p.gauge.zone = p.gauge._zone_of(float(gauge))
    rng = random.Random(seed * 7919 + 1)
    waves = []
    foe_count = 0
    if scenario in ZONE_SCENARIOS:
        limit = ZONE_SCENARIOS[scenario][2]
        waves = zone_waves(scenario, seed)
        foe_count = spawn_wave(waves.pop(0), room, p, rng)
    else:
        foes, limit = SCENARIOS[scenario]
        for kind, d in foes:
            x = min(room.width - 2 * config.TILE, PLAYER_X + d + rng.randint(-60, 60))
            before = len(game_world.world[game_world.LAYER_ENEMY])
            e = spawn(kind, x, room, p)
            foe_count += len(game_world.world[game_world.LAYER_ENEMY]) - before
            if kind in ('boss', 'ark'):
                e.rng = random.Random(seed)          # 보스 패턴 순서도 시드마다 다르게 (게임에서는 고정 Random(7))
    wave_wait = None

    hp0 = p.hp
    zone_time = {}
    gmin = gmax = p.gauge.value
    events = []
    p.gauge.listeners.append(lambda name, g: events.append(name))   # 오버로드는 한 번의 add 안에서 바로 리셋되므로 이벤트로 센다
    state = {}
    t = 0.0
    result = 'timeout'
    while t < limit:
        bot_step(p, bot, weapon_id, state)
        game_world.update(DT)
        p.gauge.tick(DT, False)
        t += DT
        z = p.gauge.zone
        zone_time[z] = zone_time.get(z, 0.0) + DT
        gmin, gmax = min(gmin, p.gauge.value), max(gmax, p.gauge.value)
        if p.state == 'DEAD':
            result = 'dead'
            break
        if not enemies():
            if not waves:
                result = 'win'
                break
            wave_wait = config.WAVE_WARN if wave_wait is None else wave_wait - DT   # 다음 물결은 예고 뒤에 (게임과 같다)
            if wave_wait <= 0:
                foe_count += spawn_wave(waves.pop(0), room, p, rng)
                wave_wait = None
    return dict(result=result, time=round(t, 2), foes=foe_count, max_hp=p.max_hp, hp_lost=round(hp0 - max(0, p.hp), 1),
                gauge_end=round(p.gauge.value, 1), gauge_min=round(gmin, 1), gauge_max=round(gmax, 1),
                overloads=events.count('overload'), zones={k: round(v / t, 3) for k, v in zone_time.items()})


def summarize(runs):
    n = len(runs)
    wins = [r for r in runs if r['result'] == 'win']
    zones = {}
    for r in runs:
        for k, v in r['zones'].items():
            zones[k] = zones.get(k, 0.0) + v / n
    return dict(n=n, win=round(len(wins) / n, 2), dead=round(sum(r['result'] == 'dead' for r in runs) / n, 2),
                ttk=round(sum(r['time'] for r in wins) / len(wins), 1) if wins else None,
                hp_lost=round(sum(r['hp_lost'] for r in runs) / n, 1),
                gauge_end=round(sum(r['gauge_end'] for r in runs) / n, 1),
                gauge_min=min(r['gauge_min'] for r in runs), gauge_max=max(r['gauge_max'] for r in runs),
                overloads=round(sum(r['overloads'] for r in runs) / n, 2),
                zones={k: round(v, 2) for k, v in sorted(zones.items(), key=lambda kv: -kv[1])})


def fmt_zones(z):
    return ' '.join(f'{k[:4]}{int(v * 100)}' for k, v in list(z.items())[:3])


# ----- 영구 성장 경제 (은신처, 11/19) -----
def economy():
    """판이 어디서 끝나느냐에 따라 받는 헤이즈 결정: [(설명, 결정)]. 전투방을 모두 돌았다고 친다."""
    import meta
    import stage as stage_mod
    combat = []
    for name in stage_mod.STAGE_ORDER:
        _, layout = stage_mod.load_layout(name)
        combat.append(sum(1 for info in layout.values() if info.get('type', 'combat') == 'combat'))
    rows = [('스테이지 1 중간에 사망 (전투방 절반)', meta.run_reward(combat[0] // 2, 0, False))]
    rooms = ends = 0
    for i, n in enumerate(combat):
        rooms += n + 1                                   # 전투방 + 끝 방(관문·보스)도 클리어한 방
        ends += 1
        label = ('스테이지 1 관문까지', '스테이지 2 크래셔까지', '스테이지 3 아크까지')[i]
        rows.append((label + ' 깨고 사망', meta.run_reward(rooms, ends, False)))
    rows.append(('탈출 (모두 돌고 아크 처치)', meta.run_reward(rooms, ends, True)))
    return rows


def total_meta_cost():
    """정비사 강화를 모두 최대로 + 보관 칸 열기에 드는 결정."""
    import meta
    return sum(sum(u['prices']) for u in meta.UPGRADES.values()) + config.META_KEEPER_PRICE


def print_economy():
    total = total_meta_cost()
    print('판이 끝나는 곳별 헤이즈 결정 (전투방을 모두 돈다고 칠 때)')
    for label, got in economy():
        print(f'  {label:<28} {got:>4}   -> 모두 최대까지 약 {-(-total // max(got, 1))}판')
    print(f'정비사 강화 전부 + 보관 칸 = {total} 결정')


def zone_table(weapons, bots, seeds, gauge=None, meta_levels=None):
    """무기 × 구역 표: {(구역, 시나리오, 무기, 봇): 요약}. 구역 끝 싸움(관문·크래셔·아크)까지 한 번에."""
    out = {}
    for zone, cols in ZONE_TABLE.items():
        for sc, _label in cols:
            for w in weapons:
                for b in bots:
                    runs = [run_one(sc, w, b, seed, gauge, meta_levels) for seed in range(seeds)]
                    s = summarize(runs)
                    s['foes'] = round(sum(r['foes'] for r in runs) / len(runs), 1)
                    out[(zone, sc, w, b)] = s
    return out


def zone_markdown(table, weapons, bots):
    """zone_table 결과를 마크다운 표로: 구역마다 한 표, 줄은 무기·봇, 칸은 '승률 / 처치 초 / 잃은 체력'."""
    names = {'stage1': '구역 1 (슬럼)', 'stage2': '구역 2 (공장)', 'stage3': '구역 3 (탑)'}
    lines = []
    for zone, cols in ZONE_TABLE.items():
        lines.append(f'### {names.get(zone, zone)}')
        lines.append('')
        lines.append('| 무기 | 봇 | ' + ' | '.join(label for _sc, label in cols) + ' |')
        lines.append('|---|---|' + '---|' * len(cols))
        for w in weapons:
            for b in bots:
                cells = []
                for sc, _label in cols:
                    s = table[(zone, sc, w, b)]
                    cells.append(f"{s['win']:.0%} / {s['ttk']}초 / -{s['hp_lost']}")
                lines.append(f'| {w} | {b} | ' + ' | '.join(cells) + ' |')
        foes = ', '.join(f"{label} {table[(zone, sc, weapons[0], bots[0])]['foes']}마리" for sc, label in cols)
        lines.append('')
        lines.append(f'적 수 평균: {foes}')
        lines.append('')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scenario', nargs='*', default=list(SCENARIOS), choices=ALL_SCENARIOS,
                    help='기본은 1:1·보스 시나리오. 구역 시나리오(z1_room 등)는 이름으로 부르거나 --zones')
    ap.add_argument('--weapon', nargs='*', default=list(WEAPONS), choices=list(WEAPONS))
    ap.add_argument('--bot', nargs='*', default=list(BOTS), choices=list(BOTS))
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument('--gauge', type=float, help='시작 게이지(%%). 없으면 게임 시작값')
    ap.add_argument('--save', help='결과를 JSON으로 저장 (변경 전 기준)')
    ap.add_argument('--compare', help='저장한 기준 JSON과 비교해 차이를 보여 준다')
    ap.add_argument('--meta', choices=('max',), help='은신처 영구 강화를 모두 최대로 한 플레이어로 싸운다')
    ap.add_argument('--economy', action='store_true', help='판이 끝나는 곳별 헤이즈 결정과 강화 총비용만 보여 준다')
    ap.add_argument('--zones', action='store_true', help='무기 × 구역 표 (전투방·큰 방·구역 끝 싸움)')
    ap.add_argument('--md', help='--zones 표를 마크다운 파일로도 쓴다')
    ap.add_argument('--easy', action='store_true', help='설정의 초보자 모드를 켜고 싸운다 (config.EASY_*)')
    a = ap.parse_args()
    import options
    options.easy_mode = bool(a.easy)                     # 저장 파일은 건드리지 않는다
    if a.zones:
        started = time.time()
        table = zone_table(a.weapon, a.bot, a.seeds, a.gauge, a.meta)
        text = zone_markdown(table, a.weapon, a.bot)
        print(text)
        print(f'시드 {a.seeds}개, {time.time() - started:.0f}초')
        if a.md:
            with open(a.md, 'w', encoding='utf-8') as f:
                f.write(text + '\n')
        return
    if a.economy:
        print_economy()
        return

    base = json.load(open(a.compare, encoding='utf-8')) if a.compare else {}
    out = {}
    started = time.time()
    print(f"{'시나리오':<8}{'무기':<10}{'봇':<7}{'승률':>6}{'사망':>6}{'처치(초)':>9}{'잃은HP':>8}{'게이지끝':>9}{'최저':>6}{'최고':>6}{'오버':>6}  구간 비율(%)")
    for sc in a.scenario:
        for w in a.weapon:
            for b in a.bot:
                s = summarize([run_one(sc, w, b, seed, a.gauge, a.meta) for seed in range(a.seeds)])
                key = f'{sc}/{w}/{b}'
                out[key] = s
                line = (f"{sc:<10}{w:<11}{b:<8}{s['win']:>6.0%}{s['dead']:>6.0%}{str(s['ttk']):>9}{s['hp_lost']:>8}"
                        f"{s['gauge_end']:>9}{s['gauge_min']:>7}{s['gauge_max']:>7}{s['overloads']:>6}  {fmt_zones(s['zones'])}")
                if key in base:
                    o = base[key]
                    diff = []
                    for k in ('win', 'dead', 'ttk', 'hp_lost', 'gauge_end'):
                        if o.get(k) != s.get(k) and o.get(k) is not None and s.get(k) is not None:
                            diff.append(f'{k} {o[k]}->{s[k]}')
                    line += '   | ' + (', '.join(diff) if diff else '변화 없음')
                print(line, flush=True)
    print(f'시드 {a.seeds}개, {time.time() - started:.0f}초')
    if a.save:
        with open(a.save, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print('저장:', a.save)


if __name__ == '__main__':
    main()
