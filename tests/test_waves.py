"""물결 전투 (v8 계획 5-2, 2026-11-25): 전투방의 적이 한꺼번에 서 있지 않고 물결로 나온다.
창 없이: python tests/test_waves.py

- 적 무리가 WAVE_MIN_PACKS 이상인 전투방은 2물결, WAVE_THREE_PACKS 이상이면 3물결. 그보다 적으면 예전처럼 한 번에.
- 지금 물결을 다 쓰러뜨리면 다음 물결의 자리에 WAVE_WARN초 예고가 뜬 뒤 적이 나온다.
- 마지막 물결까지 쓰러뜨려야 방이 열리고 보상을 받는다. 예고 중에도 방은 잠겨 있다.
- 정예는 마지막 물결에 나온다. 적의 수와 구성은 물결로 나눠도 그대로다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
sys.path.insert(0, HERE)

import config  # noqa: E402
import game_world  # noqa: E402
import test_stage as ts  # noqa: E402


def alive():
    return [e for e in game_world.world[game_world.LAYER_ENEMY] if e.alive]


def kill_all():
    for e in alive():
        e.take_damage(10 ** 9)


def step(stage, frames):
    for _ in range(frames):
        game_world.update(ts.DT)
        stage.update()


def rooms(seeds=(1, 2, 3, 4)):
    """여러 판의 전투방을 차례로 들어가 본다: (stage, 좌표)."""
    for seed in seeds:
        stage, p = ts.make_stage(seed=seed)
        stage.on_mutation = lambda ids: None                             # 보상 카드 창은 열지 않는다
        for c in sorted(stage.layout):
            if stage.type_of(c) == 'combat':
                stage.enter_room(c)
                yield stage, c


def test_big_rooms_split_into_waves_and_small_rooms_do_not():
    seen = set()
    for stage, c in rooms():
        packs = stage.wave_packs
        want = 1 if packs < config.WAVE_MIN_PACKS else 2 if packs < config.WAVE_THREE_PACKS else 3
        assert 1 <= stage.wave_total <= want, (c, packs, stage.wave_total)   # 정예가 많으면 앞 물결이 줄 수 있다 (정예는 모두 마지막 물결)
        want = stage.wave_total
        seen.add(want)
        if want > 1:
            assert stage.waves and len(alive()) < stage.wave_enemies         # 처음에는 일부만 서 있다
        else:
            assert not stage.waves and len(alive()) == stage.wave_enemies
    assert seen & {2, 3}, seen                                           # 물결로 나뉘는 방이 실제로 있다


def test_the_next_wave_arrives_after_a_warning_and_the_room_opens_only_at_the_end():
    for stage, c in rooms(seeds=(1, 2)):
        if stage.wave_total < 2:
            continue
        total, killed = stage.wave_enemies, 0
        for wave in range(1, stage.wave_total + 1):
            assert stage.wave_index == wave and stage.room.locked
            killed += len(alive())
            kill_all()
            step(stage, 2)
            if wave < stage.wave_total:
                assert stage.room.locked and c not in stage.cleared      # 예고 중: 아직 잠겨 있다
                assert not alive() and stage.wave_timer is not None
                step(stage, int(config.WAVE_WARN * 60) + 3)
                assert alive(), (c, wave)                                # 다음 물결이 나왔다
        assert killed == total, (killed, total)                          # 적의 수는 그대로
        assert not stage.room.locked and c in stage.cleared
        return
    raise AssertionError('물결이 있는 방을 찾지 못했다')


def test_elites_come_in_the_last_wave():
    found = False
    for stage, c in rooms(seeds=range(1, 13)):
        if stage.wave_total < 2:
            continue
        early = alive() + [e for w in stage.waves[:-1] for e in w]
        assert not any(getattr(e, 'elite', None) for e in early), c
        found = found or any(getattr(e, 'elite', None) for e in stage.waves[-1])
    assert found                                                         # 정예가 마지막 물결에 실제로 나온다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
