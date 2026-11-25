"""증강 보상 시뮬레이션: 한 판에 진화·합성 카드가 얼마나 자주 열리는지 잰다 (2026-11-25, v8 7일 차 뒤 점검).

전투 없이 보상 뽑기만 돈다: 구역 1 -> 2 -> 3의 배치를 만들고(mapgen), 갈림길에서 한쪽 길을 고르고,
닫히지 않은 전투방과 구역 보스를 모두 깼다고 치고 '증강' 보상마다 mutations.offer로 카드 셋을 뽑아 하나를 고른다.
결과(2026-11-25, 300판): 큰 방·구역 보스 보상을 증강으로 고정하기 전에는 평균 5.5번·합성 9%(focus), 고정한 뒤 평균 9.6번·합성 45%.
떠돌이 죄수의 증강 거래·균열방은 세지 않는다(더 얻을 수 있다는 뜻: 결과는 조금 보수적이다).

고르는 방식
  random  아무 카드나
  focus   합성 > 진화 > 이미 가진 갈래의 기본 카드(진화에 가까워진다) > 든 무기의 카드 > 아무 카드

사용: python tools/augment_sim.py [--runs 300] [--zones 3]
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
    if policy == 'random':
        return rng.choice(cards)
    held = {w.weapon_id for w in player.weapons if w is not None}

    def score(mid):
        m, t = mu.MUTATIONS[mid], mu.tier(mid)
        fam = m['family']
        if t == 'duo':
            return 4
        if t == 'evo':
            return 3
        weapon = mu.FAMILIES[fam].get('weapon')
        if fam not in mu.GAUGE_FAMILIES and mu.base_count(player, fam) >= 1 and (weapon is None or weapon in held):
            return 2
        if weapon in held:
            return 1
        return 0
    best = max(score(c) for c in cards)
    return rng.choice([c for c in cards if score(c) == best])


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
    return picks, first, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=300)
    ap.add_argument('--zones', type=int, default=3)
    ap.add_argument('--weight', type=int, default=None, help='실험: 증강 보상의 무게 (지금 값은 mutations.REWARD_WEIGHTS)')
    a = ap.parse_args()
    if a.weight is not None:
        mu.REWARD_WEIGHTS['mutation'] = a.weight
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
