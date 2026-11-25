"""증강 보상 시뮬레이션: 한 판에 진화·합성 카드가 얼마나 자주 열리는지 잰다 (2026-11-25, v8 7일 차 뒤 점검).

전투 없이 보상 뽑기만 돈다: 구역 1 -> 2 -> 3의 배치를 만들고(mapgen), 갈림길에서 한쪽 길을 고르고,
닫히지 않은 전투방과 구역 보스를 모두 깼다고 치고 '증강' 보상마다 mutations.offer로 카드 셋을 뽑아 하나를 고른다.
결과(2026-11-25, 300판): 큰 방·구역 보스 보상을 증강으로 고정하기 전에는 평균 5.5번·합성 9%(focus), 고정한 뒤 평균 9.6번·합성 45%.
떠돌이 죄수의 증강 거래·균열방은 세지 않는다(더 얻을 수 있다는 뜻: 결과는 조금 보수적이다).

고르는 방식
  random  아무 카드나
  casual  두 번에 한 번은 focus처럼, 나머지는 아무 카드나 (갈래를 대충 챙기는 사람. --detail에서만)
  focus   합성 > 진화 > 이미 가진 갈래의 기본 카드(진화에 가까워진다) > 든 무기의 카드 > 아무 카드
  target  focus와 같되, 든 무기로 만들 수 있는 '짝이 정해진 합성' 하나를 정해 그 두 갈래의 카드를 먼저 고른다 (조합법을 아는 사람. --detail에서만)

사용: python tools/augment_sim.py [--runs 300] [--zones 3]
      python tools/augment_sim.py --detail [--runs 600]     # 구역별 누적·무기 조합별·합성 카드별 (2026-11-26)
결과(2026-11-26, 600판 --detail)는 docs/project/balance.md '증강이 열리는 빈도' (카드 뽑기 손질 전후).
"""
import argparse
import collections
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import config  # noqa: E402

config.SOUND_ENABLED = False
import mapgen  # noqa: E402
import mutations as mu  # noqa: E402
from player import Player  # noqa: E402
from stage import STAGE_ORDER, Stage  # noqa: E402

LOADOUTS = [('pipe', 'pistol'), ('pipe', 'gauntlet'), ('pipe', 'chain'), ('pistol', 'gauntlet'), ('pistol', 'chain'), ('gauntlet', 'chain')]


def choose(player, cards, policy, rng):
    if policy == 'random' or (policy == 'casual' and rng.random() < 0.5):
        return rng.choice(cards)
    held = {w.weapon_id for w in player.weapons if w is not None}
    aim = pair_families(held) if policy == 'target' else ()

    def score(mid):
        m, t = mu.MUTATIONS[mid], mu.tier(mid)
        fam = m['family']
        if t == 'duo':
            return 6
        if t == 'evo':
            return 5 if fam in aim else 4
        if fam in aim and not mu.has(player, mu.evolution_of(fam)):
            return 3
        weapon = mu.FAMILIES[fam].get('weapon')
        if fam not in mu.GAUGE_FAMILIES and mu.base_count(player, fam) >= 1 and (weapon is None or weapon in held):
            return 2
        if weapon in held:
            return 1
        return 0
    best = max(score(c) for c in cards)
    return rng.choice([c for c in cards if score(c) == best])


def pair_families(held):
    """든 무기로 만들 수 있는 '짝이 정해진 합성' 가운데 첫 번째의 두 갈래 (없으면 빈 튜플)."""
    for mid, m in mu.MUTATIONS.items():
        if mu.tier(mid) != 'duo' or not m.get('requires'):
            continue
        fams = [mu.MUTATIONS[r]['family'] for r in m['requires']]
        if all(mu.FAMILIES[f].get('weapon') in (None, *held) for f in fams):
            return tuple(fams)
    return ()


def run(seed, loadout, policy, zones):
    rng = random.Random(f'augsim:{seed}:{policy}')
    p = Player(0, 0, None)
    p.set_loadout(*loadout)
    picks, first = 0, {}
    for i, name in enumerate(STAGE_ORDER[:zones]):
        start, layout = mapgen.generate(name, seed + i)
        st = Stage(p, layout=layout, start=start, seed=seed + i, name=name)
        lane = rng.choice(('short', 'long'))
        st.sealed = {c for c, info in st.layout.items() if info.get('lane') and info['lane'] != lane}
        rooms = [(c, st.rewards[c]) for c in sorted(st.rewards) if c not in st.sealed]     # 큰 방·구역 보스 보상도 들어 있다
        for c, reward in rooms:
            if reward != 'mutation':
                continue
            cards = mu.offer(p, random.Random(f'{seed}:{i}:{c}'))
            if not cards:
                continue
            picks += 1
            for t in ('evo', 'duo'):
                if t not in first and any(mu.tier(m) == t for m in cards):
                    first[t] = (picks, i + 1)
            mu.give(p, choose(p, cards, policy, rng))
    got = collections.Counter(mu.tier(m) for m in mu.owned(p))
    got['duo_ids'] = [m for m in mu.owned(p) if mu.tier(m) == 'duo']
    return picks, first, got


def detail(runs, zones):
    """고르는 방식마다: 구역을 몇 개 깼을 때까지 합성 카드를 봤는가(누적), 무기 조합별, 어떤 합성을 얻었는가."""
    names = {'pipe': '파이프', 'pistol': '쌍권총', 'gauntlet': '건틀릿', 'chain': '사슬'}
    for policy in ('random', 'casual', 'focus', 'target'):
        seen_zone, evo_zone = collections.Counter(), collections.Counter()
        by_load = collections.defaultdict(lambda: [0, 0, 0])            # 조합 -> [판 수, 합성 카드를 본 판, 합성을 얻은 판]
        duo_ids = collections.Counter()
        for k in range(runs):
            load = LOADOUTS[k % len(LOADOUTS)]
            n, first, got = run(1000 + k, load, policy, zones)
            if 'duo' in first:
                seen_zone[first['duo'][1]] += 1
            if 'evo' in first:
                evo_zone[first['evo'][1]] += 1
            row = by_load[load]
            row[0] += 1
            row[1] += 'duo' in first
            row[2] += bool(got['duo_ids'])
            duo_ids.update(got['duo_ids'])
        print(f'[{policy}]')
        cum_e = cum_d = 0
        for z in range(1, zones + 1):
            cum_e += evo_zone[z]
            cum_d += seen_zone[z]
            print(f'  구역 {z}을 깰 때까지: 진화 카드를 본 판 {cum_e / runs:.0%}, 합성 카드를 본 판 {cum_d / runs:.0%}')
        for load, (n, seen, owned) in by_load.items():
            print(f'  {names[load[0]]}+{names[load[1]]}: 합성 카드를 본 판 {seen / n:.0%}, 얻은 판 {owned / n:.0%}')
        top = ', '.join(f"{mu.MUTATIONS[m]['name']} {c / runs:.0%}" for m, c in duo_ids.most_common())
        print(f'  얻은 합성(판 대비): {top or "없음"}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=300)
    ap.add_argument('--zones', type=int, default=3)
    ap.add_argument('--weight', type=int, default=None, help='실험: 증강 보상의 무게 (지금 값은 mutations.REWARD_WEIGHTS)')
    ap.add_argument('--detail', action='store_true', help='구역별 누적·무기 조합별·합성 카드별로 본다')
    a = ap.parse_args()
    if a.weight is not None:
        mu.REWARD_WEIGHTS['mutation'] = a.weight
    if a.detail:
        print(f'{a.runs}판, 구역 {a.zones}개까지, 무기 조합 {len(LOADOUTS)}가지를 번갈아 (자세히)')
        detail(a.runs, a.zones)
        return
    print(f'{a.runs}판, 구역 {a.zones}개까지, 무기 조합 {len(LOADOUTS)}가지를 번갈아')
    for policy in ('random', 'focus'):
        picks, evo, duo, evo_at, duo_at, evos, duos = [], 0, 0, [], [], 0, 0
        zone_duo = collections.Counter()
        for k in range(a.runs):
            n, first, got = run(1000 + k, LOADOUTS[k % len(LOADOUTS)], policy, a.zones)
            picks.append(n)
            if 'evo' in first:
                evo += 1
                evo_at.append(first['evo'][0])
            if 'duo' in first:
                duo += 1
                duo_at.append(first['duo'][0])
                zone_duo[first['duo'][1]] += 1
            evos += got['evo']
            duos += got['duo']
        avg = lambda xs: sum(xs) / len(xs) if xs else 0.0      # noqa: E731
        print(f'[{policy}] 증강 보상 평균 {avg(picks):.1f}번 (최소 {min(picks)}, 최대 {max(picks)})')
        print(f'  진화 카드가 한 번이라도 나온 판 {evo / a.runs:.0%} (처음 나온 때: 평균 {avg(evo_at):.1f}번째 보상), 판마다 얻은 진화 {evos / a.runs:.2f}개')
        print(f'  합성 카드가 한 번이라도 나온 판 {duo / a.runs:.0%} (처음 나온 때: 평균 {avg(duo_at):.1f}번째 보상, '
              f'구역별 {dict(sorted(zone_duo.items()))}), 판마다 얻은 합성 {duos / a.runs:.2f}개')


if __name__ == '__main__':
    main()
