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
    'boss': ([('boss', 900)], 90),
}
WEAPONS = ('pipe', 'knife', 'gauntlet')
BOTS = ('stand', 'dodge')
# 무기마다 봇이 서는 거리(px): 철파이프는 붙고, 식칼은 떨어져 던지고, 건틀릿은 중간에서 충전
KEEP = {'pipe': 95, 'knife': 420, 'gauntlet': 230}
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
    else:
        e = Enemy(kind, x, FLOOR_Y, room, player)
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


def run_one(scenario, weapon_id, bot, seed, gauge=None):
    random.seed(seed)
    game_world.clear()
    effects.reset()
    room = arena()
    p = Player(PLAYER_X, FLOOR_Y, room)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    for _ in range(20):
        game_world.update(DT)
    if weapon_id != 'pipe':
        p.give_weapon(weapon_id)
    p.attack_held = False
    if gauge is not None:                                # 시작 게이지를 정한다 (기본은 게임 시작값)
        p.gauge.value = float(gauge)
        p.gauge.zone = p.gauge._zone_of(float(gauge))
    foes, limit = SCENARIOS[scenario]
    rng = random.Random(seed * 7919 + 1)
    for kind, d in foes:
        x = min(room.width - 2 * config.TILE, PLAYER_X + d + rng.randint(-60, 60))
        spawn(kind, x, room, p)

    hp0 = p.hp
    zone_time = {}
    gmin = gmax = p.gauge.value
    overloads = 0
    last_zone = p.gauge.zone
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
        if z == 'OVERLOAD' and last_zone != 'OVERLOAD':
            overloads += 1
        last_zone = z
        gmin, gmax = min(gmin, p.gauge.value), max(gmax, p.gauge.value)
        if p.state == 'DEAD':
            result = 'dead'
            break
        if not enemies():
            result = 'win'
            break
    return dict(result=result, time=round(t, 2), hp_lost=round(hp0 - max(0, p.hp), 1),
                gauge_end=round(p.gauge.value, 1), gauge_min=round(gmin, 1), gauge_max=round(gmax, 1),
                overloads=overloads, zones={k: round(v / t, 3) for k, v in zone_time.items()})


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scenario', nargs='*', default=list(SCENARIOS), choices=list(SCENARIOS))
    ap.add_argument('--weapon', nargs='*', default=list(WEAPONS), choices=list(WEAPONS))
    ap.add_argument('--bot', nargs='*', default=list(BOTS), choices=list(BOTS))
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument('--gauge', type=float, help='시작 게이지(%%). 없으면 게임 시작값')
    ap.add_argument('--save', help='결과를 JSON으로 저장 (변경 전 기준)')
    ap.add_argument('--compare', help='저장한 기준 JSON과 비교해 차이를 보여 준다')
    a = ap.parse_args()

    base = json.load(open(a.compare, encoding='utf-8')) if a.compare else {}
    out = {}
    started = time.time()
    print(f"{'시나리오':<8}{'무기':<10}{'봇':<7}{'승률':>6}{'사망':>6}{'처치(초)':>9}{'잃은HP':>8}{'게이지끝':>9}{'최저':>6}{'최고':>6}{'오버':>6}  구간 비율(%)")
    for sc in a.scenario:
        for w in a.weapon:
            for b in a.bot:
                s = summarize([run_one(sc, w, b, seed, a.gauge) for seed in range(a.seeds)])
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
