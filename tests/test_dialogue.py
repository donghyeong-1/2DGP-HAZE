"""은신처 NPC 대사 (v8 6일 차, 2026-11-25). 창 없이: python tests/test_dialogue.py

- 판이 끝나면 meta가 직전 판 기록(state['last'])을 남긴다: 어디서 쓰러졌나, 무엇에, 무슨 무기를 들었나, 처음 쓰러뜨린 보스.
- 정비사·보관인·기록관은 그 기록으로 다른 말을 한다(data/dialogue.py, 고르는 규칙은 src/talk.py).
- 대사마다 그 조건이 실제 판 기록에서 걸리는지, 위의 조건이 먼저인지, 같은 조건의 대사가 판마다 돌아가는지 확인한다.
- 떠돌이 죄수 인사말, 엔딩 한 줄.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')

import game_world  # noqa: E402
import killers  # noqa: E402
import meta  # noqa: E402
import talk  # noqa: E402
from player import Player  # noqa: E402

NPCS = ('mechanic', 'keeper', 'archivist')
SPEECH_MAX = 30          # NPC 창 오른쪽 위, 보통 글자(28px) 한 줄
DRIFTER_MAX = 24
ENDING_MAX = 40


def fresh():
    meta.PATH = os.path.join(tempfile.mkdtemp(), 'save.json')
    meta.reset()


def new_player(weapons=('pipe', None)):
    game_world.clear()
    p = Player(0, 0, None)
    game_world.add_object(p, game_world.LAYER_PLAYER)
    p.set_loadout(*weapons)
    return p


def end_run(zone, cause='', escaped=False, weapons=('pipe', None), rooms=3, kills=10, ark_down=False):
    """한 판을 끝낸다 (사망 또는 탈출). 직전 판 기록을 돌려준다."""
    p = new_player(weapons)
    p.run_rooms, p.run_kills = rooms, kills
    p.death_cause = cause
    meta.finish_run(p, escaped=escaped, zone=zone, ark_down=ark_down)
    return meta.state['last']


# ----- 직전 판 기록 -----
def test_finish_run_records_the_last_run():
    fresh()
    last = end_run('stage2', cause='고철 투척병', weapons=('pistol', 'chain'), rooms=7, kills=25)
    assert last['zone'] == 'stage2' and not last['escaped'] and last['cause'] == '고철 투척병'
    assert last['weapon'] in ('pistol', 'chain') and set(last['weapons']) == {'pistol', 'chain'}
    assert last['rooms'] == 7 and last['kills'] == 25
    assert last['first'] == ['gate'] and meta.state['beaten'] == ['gate']     # 공장에서 쓰러졌다 = 관문을 넘었다
    meta.load()
    assert meta.state['last'] == last and meta.state['beaten'] == ['gate']   # 저장된다


def test_first_kill_is_only_the_first_time():
    fresh()
    assert end_run('stage2')['first'] == ['gate']
    assert end_run('stage2')['first'] == []
    assert end_run('stage3')['first'] == ['crasher']
    assert end_run('stage3', cause='헤이즈 심장의 결정 비', ark_down=True)['first'] == ['ark']
    last = end_run('stage3', escaped=True)
    assert last['first'] == ['heart'] and last['escaped'] and last['escapes'] == 1
    assert meta.state['beaten'] == ['gate', 'crasher', 'ark', 'heart']


def test_escape_on_a_fresh_save_counts_every_boss_as_first():
    fresh()
    last = end_run('stage3', escaped=True)
    assert last['first'] == ['gate', 'crasher', 'ark', 'heart']


def test_streak_counts_deaths_in_the_same_zone():
    fresh()
    assert end_run('stage1')['streak'] == 1
    assert end_run('stage1')['streak'] == 2
    assert end_run('stage1')['streak'] == 3
    assert end_run('stage2')['streak'] == 1
    assert end_run('stage3', escaped=True)['streak'] == 0


def test_broken_last_record_is_dropped_on_load():
    fresh()
    meta.state['last'] = 'garbage'
    meta.state['beaten'] = ['gate', 'nonsense', 3]
    meta.save()
    meta.load()
    assert meta.state['last'] is None and meta.state['beaten'] == ['gate']
    meta.state['last'] = {'zone': 5, 'weapon': 'spoon', 'first': 'x', 'rooms': 'many'}
    meta.save()
    meta.load()
    last = meta.state['last']
    assert last['zone'] == '' and last['weapon'] is None and last['first'] == [] and last['rooms'] == 0
    assert 'any' in talk.tags(last, runs=3)                                    # 망가진 기록이어도 대사는 나온다


def test_old_save_without_record_does_not_greet_like_a_stranger():
    fresh()
    meta.state['runs'] = 4                     # 기록 항목이 생기기 전의 저장
    assert talk.tags(None, runs=4) == {'any'}
    assert talk.tags(None, runs=0) == {'any', 'none'}


# ----- 사망 원인 -> 조건 -----
def test_cause_kinds():
    assert talk.cause_kind(killers.OVERLOAD) == 'overload'
    assert talk.cause_kind(killers.GAUGE_EMPTY) == 'empty'
    assert talk.cause_kind('크래셔의 충격파') == 'boss:crasher'
    assert talk.cause_kind('총감시관 아크') == 'boss:ark'
    assert talk.cause_kind('아크의 헤이즈 탄') == 'boss:ark'
    assert talk.cause_kind('헤이즈 심장의 손') == 'boss:heart'
    assert talk.cause_kind('헤이즈 쥐') == 'enemy'
    assert talk.cause_kind('가시') == 'hazard'
    assert talk.cause_kind('') == ''


def test_devices_have_death_cause_names():
    import devices
    assert killers.describe(devices.Vent.__new__(devices.Vent)) == '증기 분출구'
    assert killers.describe(devices.Laser.__new__(devices.Laser)) == '감시 레이저'
    assert talk.cause_kind('증기 분출구') == 'hazard' and talk.cause_kind('감시 레이저') == 'hazard'


# 조건마다 그 조건이 걸리는 실제 판 (fresh 저장에서 차례로 끝낸다)
SAMPLES = {
    'none': [],
    'first_escape': [dict(zone='stage3', escaped=True)],
    'escaped': [dict(zone='stage3', escaped=True), dict(zone='stage3', escaped=True)],
    'first_kill:gate': [dict(zone='stage2')],
    'first_kill:crasher': [dict(zone='stage2'), dict(zone='stage3')],
    'first_kill:ark': [dict(zone='stage2'), dict(zone='stage3'), dict(zone='stage3', ark_down=True, cause='헤이즈 심장')],
    'died:stage1': [dict(zone='stage1')],
    'died:stage2': [dict(zone='stage2')],
    'died:stage3': [dict(zone='stage3')],
    'died_at:crasher': [dict(zone='stage2', cause='크래셔')],
    'died_at:ark': [dict(zone='stage3', cause='아크의 게이지 파동')],
    'died_at:heart': [dict(zone='stage3', cause='헤이즈 심장의 결정 비', ark_down=True)],
    'cause:overload': [dict(zone='stage1', cause=killers.OVERLOAD)],
    'cause:empty': [dict(zone='stage1', cause=killers.GAUGE_EMPTY)],
    'cause:hazard': [dict(zone='stage1', cause='가시')],
    'weapon:pipe': [dict(zone='stage1', weapons=('pipe', None))],
    'weapon:pistol': [dict(zone='stage1', weapons=('pistol', None))],
    'weapon:gauntlet': [dict(zone='stage1', weapons=('gauntlet', None))],
    'weapon:chain': [dict(zone='stage1', weapons=('chain', None))],
    'streak': [dict(zone='stage2')] * 3,
    'early': [dict(zone='stage1', rooms=0)],
    'many_kills': [dict(zone='stage1', kills=55)],
    'any': [],
}


def found_after(runs):
    fresh()
    for r in runs:
        end_run(**r)
    return talk.tags(meta.state['last'], meta.state['runs'])


def test_every_condition_in_the_data_is_reached_by_a_real_run():
    used = {e[0] for who in NPCS for e in talk.data().LINES[who]}
    assert used <= set(SAMPLES), used - set(SAMPLES)
    for when in used:
        assert when in found_after(SAMPLES[when]), when


def test_every_line_can_be_said():
    """대사마다: 그 조건만 걸린 판(+ any)이면 그 대사가 나온다 (같은 조건이 여럿이면 판 수로 돌아가며)."""
    for who in NPCS:
        entries = talk.data().LINES[who]
        for i, e in enumerate(entries):
            group = [x for x in entries if x[0] == e[0]]
            k = group.index(e)
            got = talk.pick(who, {e[0], 'any'}, runs=k)
            assert got is not None and got[0] == e[1], (who, i, e, got)


def test_higher_conditions_win():
    fresh()
    for _ in range(3):
        end_run('stage1', cause=killers.OVERLOAD, weapons=('chain', None), rooms=0)
    found = talk.tags(meta.state['last'], meta.state['runs'])
    assert {'died:stage1', 'early', 'streak', 'cause:overload', 'weapon:chain'} <= found
    lines = talk.data().LINES
    assert talk.pick('keeper', found)[0] == next(e[1] for e in lines['keeper'] if e[0] == 'streak')
    assert talk.pick('mechanic', found)[0] == next(e[1] for e in lines['mechanic'] if e[0] == 'cause:overload')
    assert talk.pick('archivist', found)[0] == next(e[1] for e in lines['archivist'] if e[0] == 'cause:overload')


def test_same_condition_lines_rotate_with_runs():
    fresh()
    seen = set()
    for _ in range(4):
        end_run('stage1', weapons=('pistol', None))
        seen.add(talk.speech('mechanic', meta.state)[0])
    pistol = [e[1] for e in talk.data().LINES['mechanic'] if e[0] == 'weapon:pistol']
    assert seen == set(pistol) and len(pistol) == 2


def test_each_npc_always_has_something_to_say():
    for who in NPCS:
        assert talk.pick(who, {'any'}) is not None
        assert talk.data().LINES[who][-1][0] == 'any'


def test_line_count_lengths_and_moods():
    lines = talk.data().LINES
    total = sum(len(lines[w]) for w in NPCS)
    assert 36 <= total <= 48, total                                   # 계획: 40줄 안팎
    for who in NPCS:
        for e in lines[who]:
            assert len(e[1]) <= SPEECH_MAX, (who, e[1], len(e[1]))
            assert len(e) == 2 or e[2] in (1, 2), e
    assert 2 <= len(talk.data().DRIFTER) <= 3
    assert all(len(s) <= DRIFTER_MAX for s in talk.data().DRIFTER)
    assert all(len(s) <= ENDING_MAX for s in talk.data().ENDING.values())


def test_speech_uses_only_known_words():
    """용어: 화면에 '변이'를 쓰지 않고, 무기 이름은 철파이프·쌍권총·건틀릿·사슬 (식칼은 쌍권총이 되었다)."""
    words = [e[1] for w in NPCS for e in talk.data().LINES[w]] + list(talk.data().DRIFTER) + list(talk.data().ENDING.values())
    for s in words:
        assert '변이' not in s and '식칼' not in s and '화이트' not in s, s


# ----- 창에 연결 -----
def test_npc_window_shows_the_line_and_face():
    import npc_mode
    fresh()
    npc_mode.result, npc_mode.selected = None, 0
    npc_mode.kind = 'mechanic'
    assert npc_mode.speech() == talk.data().LINES['mechanic'][0][1]       # 처음: none
    assert npc_mode.faces() == ('n09_1', 'mechanic_1')
    end_run('stage2')                                                      # 관문을 처음 넘었다: 정비사가 씩 웃는다
    assert npc_mode.speech() == next(e[1] for e in talk.data().LINES['mechanic'] if e[0] == 'first_kill:gate')
    assert npc_mode.faces() == ('n09_1', 'mechanic_2')
    npc_mode.kind = 'armory'
    assert npc_mode.speech() is None                                       # 무기 걸이는 말하지 않는다
    npc_mode.kind = 'keeper'
    for _ in range(2):
        end_run('stage2')
    assert npc_mode.faces() == ('n09_1', 'keeper_2')                       # 같은 곳에서 세 번: 걱정


def test_ending_line_first_and_again():
    assert talk.ending_line(1) == talk.data().ENDING['first']
    assert talk.ending_line(3) == talk.data().ENDING['again']


def test_drifter_greets_differently_by_run():
    import events
    fresh()
    seen = set()
    for runs in range(3):
        meta.state['runs'] = runs
        seen.add(events.greeting())
    assert seen == set(talk.data().DRIFTER)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
