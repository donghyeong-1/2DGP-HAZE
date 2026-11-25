"""은신처 NPC 대사 고르기 (v8 6일 차, 2026-11-25). pico2d와 무관한 순수 로직이다.

직전 판 기록(meta.state['last'], meta.finish_run이 남긴다)에서 조건 이름(tags)을 만들고,
data/dialogue.py의 목록에서 걸린 조건 중 가장 위의 대사를 고른다. 같은 조건의 대사가 여럿이면 끝낸 판 수로 돌아간다.
"""
import importlib.util
import os

import assets
import killers

ZONES = ('stage1', 'stage2', 'stage3')
EARLY_ROOMS = 1          # 슬럼에서 이만큼 이하의 방만 깨고 쓰러지면 'early'
STREAK = 3               # 같은 구역에서 이만큼 이어 쓰러지면 'streak'
MANY_KILLS = 40          # 한 판에 이만큼 쓰러뜨리면 'many_kills'
BOSS_WORDS = (('헤이즈 심장', 'heart'), ('아크', 'ark'), ('크래셔', 'crasher'))   # 사망 원인 글 -> 보스 (심장이 먼저: '심장의 손')
HAZARDS = ('가시', '증기 분출구', '감시 레이저')

_data = None


def data():
    """data/dialogue.py 모듈 (한 번 읽어 둔다)."""
    global _data
    if _data is None:
        path = os.path.join(assets.DATA_DIR, 'dialogue.py')
        spec = importlib.util.spec_from_file_location('haze_dialogue', path)
        _data = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_data)
    return _data


def cause_kind(cause):
    """사망 원인 글(killers.describe) -> 'overload' / 'empty' / 'boss:<보스>' / 'hazard' / 'enemy' / ''."""
    if not cause:
        return ''
    if cause == killers.OVERLOAD:
        return 'overload'
    if cause == killers.GAUGE_EMPTY:
        return 'empty'
    for word, boss in BOSS_WORDS:
        if word in cause:
            return 'boss:' + boss
    if cause in HAZARDS:
        return 'hazard'
    return 'enemy'


def tags(last, runs=0):
    """직전 판 기록 -> 조건 이름 집합 (data/dialogue.py 머리말의 표). 기록이 없으면 처음(none, 끝낸 판이 없을 때만) + any."""
    out = {'any'}
    if not isinstance(last, dict):
        if runs <= 0:
            out.add('none')
        return out
    if last.get('escaped'):
        out.add('first_escape' if last.get('escapes', 0) <= 1 else 'escaped')
    for boss in last.get('first', []):
        out.add('first_kill:' + boss)
    zone = last.get('zone')
    if not last.get('escaped') and zone in ZONES:
        out.add('died:' + zone)
        if zone == 'stage1' and last.get('rooms', 0) <= EARLY_ROOMS:
            out.add('early')
        if last.get('streak', 0) >= STREAK:
            out.add('streak')
    kind = cause_kind(last.get('cause', ''))
    if kind.startswith('boss:'):
        out.add('died_at:' + kind[5:])
    elif kind in ('overload', 'empty', 'hazard'):
        out.add('cause:' + kind)
    if last.get('weapon'):
        out.add('weapon:' + last['weapon'])
    if last.get('kills', 0) >= MANY_KILLS:
        out.add('many_kills')
    return out


def pick(who, found, runs=0):
    """조건 집합 found에서 NPC who의 대사 하나: (글, 표정 1·2). 없으면 None.
    목록에서 처음 걸린 조건을 쓰고, 그 조건의 대사들 중 runs번째(돌아가며)를 고른다."""
    entries = data().LINES.get(who)
    if not entries:
        return None
    when = next((e[0] for e in entries if e[0] in found), None)
    if when is None:
        return None
    group = [e for e in entries if e[0] == when]
    e = group[runs % len(group)]
    return e[1], (e[2] if len(e) > 2 else 1)


def speech(who, state):
    """meta.state로 who의 대사: (글, 표정) 또는 None."""
    runs = state.get('runs', 0) if state else 0
    return pick(who, tags(state.get('last') if state else None, runs), runs)


def drifter_line(runs):
    """떠돌이 죄수 인사말 (판마다 돌아간다)."""
    lines = data().DRIFTER
    return lines[runs % len(lines)]


def ending_line(escapes):
    """탈출 화면 한 줄: 처음 탈출이면 'first', 아니면 'again'."""
    return data().ENDING['first' if escapes <= 1 else 'again']
