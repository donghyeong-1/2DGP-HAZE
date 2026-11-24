"""이벤트 방 (v8 계획 5-4, 2026-11-25): 헤이즈 샘, 떠돌이 죄수, 도전방.
창 없이: python tests/test_events.py

- 구역 1·2의 본 경로에 이벤트 방이 하나 있다. 갈림길 밖이라 어느 길을 골라도 지난다. 구역 3에는 없다.
- 같은 판의 구역 1과 2에는 서로 다른 이벤트가 나온다.
- 헤이즈 샘: 게이지를 고른 구간으로 맞춘다. 한 번 쓰면 마른다. 사망·오버로드는 일어나지 않는다.
- 떠돌이 죄수: 체력·조각·증강을 맞바꾼다. 모자라면 고를 수 없고, 거래는 하나만. 지나가기는 다시 올 수 있다.
- 도전방: 구역마다 전투방 하나. 시간 안에 모두 쓰러뜨리면 보상이 CHALLENGE_MULT배, 늦으면 그대로.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import effects  # noqa: E402
import events  # noqa: E402
import game_world  # noqa: E402
import mapgen  # noqa: E402
import mutations  # noqa: E402
import test_fork as tf  # noqa: E402
import test_stage as ts  # noqa: E402
from haze_gauge import AWAKE, CRITICAL, NORMAL  # noqa: E402
from player import Player  # noqa: E402
from stage import Stage  # noqa: E402

SEEDS = range(30)


def event_room(stage):
    return next((c for c in stage.layout if stage.type_of(c) == 'event'), None)


def open_event(seed, kind):
    """kind 이벤트가 나오는 판을 찾아 이벤트 방에 들어간다: (stage, player, 열린 카드 목록을 담는 리스트)."""
    while events.KINDS[seed % len(events.KINDS)] != kind:
        seed += 1
    game_world.clear()
    effects.reset()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    start, layout = mapgen.generate('stage1', seed)                          # 생성 배치 (test_stage는 손으로 짠 배치를 쓴다)
    stage = Stage(p, layout=layout, start=start, seed=seed, name='stage1')
    stage.start()
    opened = []
    stage.on_mutation = opened.append
    stage.enter_room(event_room(stage), 'L')
    p.x, p.y = stage.event.x, stage.event.y
    return stage, p, opened


def test_zones_one_and_two_have_one_event_room_on_the_main_path():
    for name in ('stage1', 'stage2'):
        for seed in SEEDS:
            st = tf.stage(name, seed)
            rooms = [c for c in st.layout if st.type_of(c) == 'event']
            assert len(rooms) == 1 and rooms[0][1] == 0, (name, seed, rooms)
            c = rooms[0]
            assert c[0] >= 2 and not st.layout[c].get('lane')                 # 첫 전투방 뒤, 갈림길 밖
            assert st.links_of(c) == {'L', 'R'}
            short, long_ = tf.lanes(st)
            assert c in tf.reach(st, skip=long_) and c in tf.reach(st, skip=short)
            assert sum(1 for k in st.layout if st.type_of(k) == 'combat') == mapgen.SPECS[name]['combat']
    for seed in SEEDS:
        assert event_room(tf.stage('stage3', seed)) is None


def test_the_two_zones_of_one_run_get_different_events():
    for seed in SEEDS:
        a, b = tf.stage('stage1', seed), tf.stage('stage2', seed + 1)         # 다음 구역의 시드는 +1 (stage.next_stage)
        assert events.kind_of(a) != events.kind_of(b)


def test_the_event_room_has_no_enemies_and_opens_its_cards_on_interact():
    for kind in events.KINDS:
        stage, p, opened = open_event(1, kind)
        assert stage.event.kind == kind and not stage.room.locked and stage.enemy_count() == 0
        assert stage.interact() and opened[-1] == events.cards(kind)
        p.x += 600                                                           # 멀리서는 열리지 않는다
        opened.clear()
        stage.interact()
        assert not opened


def test_the_spring_sets_the_gauge_to_the_chosen_zone_once():
    for key, zone in (('normal', NORMAL), ('awake', AWAKE), ('critical', CRITICAL)):
        stage, p, opened = open_event(1, 'spring')
        p.gauge.value = 22.0
        stage.interact()
        text, _color, follow = events.take(p, f'{events.CARD}spring:{key}')
        assert follow is None and p.gauge.zone == zone, (key, p.gauge.value, p.gauge.zone)
        assert p.gauge.value == events.spring_target(p, key) and p.gauge.stun_timer == 0
        assert stage.event.used
        opened.clear()
        assert not stage.interact() and not opened                           # 한 번 쓰면 마른다
        stage.enter_room(event_room(stage), 'L')                             # 다시 들어와도 그대로
        assert stage.event.used


def test_set_value_never_kills_or_overloads():
    stage, p, _ = open_event(1, 'spring')
    p.gauge.set_value(500)
    assert p.gauge.value == p.gauge.cap - 1 and p.gauge.stun_timer == 0
    p.gauge.set_value(-50)
    assert p.gauge.value == 1.0 and p.gauge.zone != 'DEAD'


def test_the_drifter_trades_health_shards_and_augments():
    stage, p, opened = open_event(1, 'drifter')
    card = events.CARD + 'deal:'
    p.hp, p.shards = 60, 0
    stage.interact()
    assert not events.card_info(p, card + 'heal')['ok'] and events.take(p, card + 'heal') is None    # 조각이 모자라다
    assert events.take(p, card + 'skip')[2] is None and not stage.event.used                        # 지나가기: 다시 올 수 있다
    p.shards = config.DEAL_HEAL_SHARDS
    events.take(p, card + 'heal')
    assert p.shards == 0 and p.hp == 60 + config.DEAL_HEAL_HP and stage.event.used                   # 거래는 하나만
    assert not stage.interact()

    stage, p, opened = open_event(1, 'drifter')
    p.hp, p.shards = 60, 0
    stage.interact()
    events.take(p, card + 'shards')
    assert p.hp == 60 - config.DEAL_SHARDS_HP and p.shards == config.DEAL_SHARDS_GAIN

    stage, p, opened = open_event(1, 'drifter')
    p.hp = config.DEAL_BLOOD_HP
    stage.interact()
    assert events.take(p, card + 'blood') is None                             # 체력이 딱 그만큼이면 못 낸다 (죽지 않게)
    p.hp = config.DEAL_BLOOD_HP + 10
    _text, _color, follow = events.take(p, card + 'blood')
    assert p.hp == 10 and follow and all(m in mutations.MUTATIONS for m in follow)   # 이어서 증강 셋 중 하나를 고른다


def test_the_card_window_keeps_going_when_a_deal_leads_to_augments():
    import mutation_mode
    stage, p, opened = open_event(1, 'drifter')
    p.hp = 90
    stage.interact()
    mutation_mode.setup(p, opened[-1])
    mutation_mode.selected = opened[-1].index(events.CARD + 'deal:blood')
    follow = mutation_mode.choose()
    assert follow and p.hp == 90 - config.DEAL_BLOOD_HP
    mutation_mode.setup(p, follow)
    before = len(mutations.owned(p))
    assert mutation_mode.choose() is None and len(mutations.owned(p)) == before + 1
    mutation_mode.setup(p, opened[-1])                                        # 모자란 카드는 고를 수 없다
    p.shards = 0
    assert not mutation_mode.can_pick(opened[-1].index(events.CARD + 'deal:heal'))


def challenge_room(seed):
    stage, p = ts.make_stage(seed=seed)
    stage.on_mutation = lambda ids: None
    (c,) = stage.challenges
    stage.rewards[c] = 'shards'
    return stage, p, c


def test_each_zone_has_one_challenge_room():
    for name in config.CHALLENGE_ZONES:
        for seed in SEEDS:
            st = tf.stage(name, seed)
            assert len(st.challenges) == 1, (name, seed)
            (c,) = st.challenges
            sx, sy = st.start_coord
            assert st.type_of(c) == 'combat' and not st.is_big(c) and abs(c[0] - sx) + abs(c[1] - sy) > 1


def test_clearing_a_challenge_in_time_boosts_the_reward():
    gains = {}
    for late in (False, True):
        stage, p, c = challenge_room(2)
        stage.enter_room(c, 'L')
        ch = stage.challenge
        assert ch and ch['left'] == stage.challenge_limit() > config.CHALLENGE_BASE and stage.room.locked
        calls, grant = [], stage.grant_reward
        stage.grant_reward = lambda kind, boost=False: (calls.append(boost), p.__setattr__('shards', 0), grant(kind, boost))
        for _ in range(60):
            stage.update()
        assert stage.challenge['left'] < ch['limit']                          # 시간이 간다
        if late:
            stage.challenge['left'] = 0.02
        for _ in range(40):                                                   # 물결을 차례로 쓰러뜨린다
            if not stage.room.locked:
                break
            ts.kill_all()
            for _ in range(int(config.WAVE_WARN * 60) + 4):
                game_world.update(ts.DT)
                stage.update()
        assert not stage.room.locked and stage.challenge is None
        assert calls == [not late]                                            # 제때 깼을 때만 커진 보상
        gains[late] = p.shards                                                # 보상으로 받은 조각 (처치로 얻은 것은 뺀다)
    assert gains[False] == gains[True] * config.CHALLENGE_MULT > 0, gains


def test_ordinary_rooms_have_no_challenge():
    stage, p, c = challenge_room(2)
    other = next(k for k in sorted(stage.layout) if stage.type_of(k) == 'combat' and k not in stage.challenges)
    stage.enter_room(other, 'L')
    assert stage.challenge is None


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
