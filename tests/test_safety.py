"""저장 손상 대비·오류 기록 테스트 (창 없이). 실행: python tests/test_safety.py

2026-11-21 퀄리티 계획 3-2: 깨진 저장으로도 게임이 켜지고, 진행이 몰래 사라지지 않으며, 오류는 기록에 남는다.
- 저장은 임시 파일에 쓴 뒤 바꿔 끼운다(쓰다 꺼져도 원래 파일이 남는다). 바꾸기 전 파일은 .bak으로 둔다.
- 저장이 깨졌으면 .bak에서 읽고, 그것도 없으면 기본값으로 시작한다. 깨진 파일은 .broken으로 남겨 둔다(덮어써 지우지 않는다).
- 값의 종류가 이상하면(숫자 자리에 글자 등) 그 값만 기본값.
- 오류는 사용자 폴더의 기록 파일(log.PATH)에 시간과 함께 남고, 커지면 .old로 넘긴다.
- 게임 도중 예외가 나면 기록하고 안내 창을 띄운 뒤 끝낸다(main.run_safely).
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import log  # noqa: E402
import meta  # noqa: E402
import options  # noqa: E402
import safe_io  # noqa: E402

TMP = tempfile.mkdtemp()
log.PATH = os.path.join(TMP, 'haze_log.txt')
meta.PATH = os.path.join(TMP, 'save.json')
options.PATH = os.path.join(TMP, 'opt.json')


def fresh(name):
    d = tempfile.mkdtemp(dir=TMP)
    return os.path.join(d, name)


def log_text():
    try:
        return open(log.PATH, encoding='utf-8').read()
    except OSError:
        return ''


def test_write_is_atomic_and_keeps_previous_as_bak():
    path = fresh('a.json')
    assert safe_io.write_json(path, {'v': 1})
    assert safe_io.write_json(path, {'v': 2})
    assert json.load(open(path, encoding='utf-8')) == {'v': 2}
    assert json.load(open(path + '.bak', encoding='utf-8')) == {'v': 1}       # 바로 전 저장
    assert not os.path.exists(path + '.tmp')                                   # 임시 파일이 남지 않는다


def test_broken_save_falls_back_to_bak_and_keeps_broken_copy():
    meta.PATH = fresh('save.json')
    meta.reset()
    meta.state['crystals'] = 40
    meta.save()
    meta.state['crystals'] = 55
    meta.save()                                                                # .bak = 40, 본 파일 = 55
    with open(meta.PATH, 'w', encoding='utf-8') as f:
        f.write('{"crystals": 55, "lev')                                       # 쓰다 끊긴 것처럼 깨뜨린다
    meta.load()
    assert meta.state['crystals'] == 40                                        # 바로 전 저장에서 되살렸다
    assert os.path.exists(meta.PATH + '.broken')                               # 깨진 파일은 지우지 않고 남긴다
    assert 'save.json' in log_text()


def test_broken_save_without_bak_starts_fresh_and_does_not_crash():
    meta.PATH = fresh('save.json')
    with open(meta.PATH, 'wb') as f:
        f.write(b'\x00\xff garbage')
    meta.load()
    assert meta.state['crystals'] == 0 and meta.state['levels']['hp'] == 0
    assert os.path.exists(meta.PATH + '.broken')


def test_wrong_value_types_use_defaults_per_field():
    meta.PATH = fresh('save.json')
    with open(meta.PATH, 'w', encoding='utf-8') as f:
        json.dump({'crystals': 'abc', 'levels': [1, 2], 'runs': None, 'escapes': 3, 'hints': 'move', 'keeper': 1}, f)
    meta.load()
    assert meta.state['crystals'] == 0 and meta.state['levels'] == {k: 0 for k in meta.UPGRADES}
    assert meta.state['runs'] == 0 and meta.state['escapes'] == 3 and meta.state['hints'] == []
    assert meta.state['keeper'] is True


def test_save_failure_is_logged_not_raised():
    d = fresh('dir_as_file')
    os.makedirs(d)
    assert safe_io.write_json(d, {'v': 1}) is False                            # 폴더 자리에는 못 쓴다: 예외 없이 False
    assert 'dir_as_file' in log_text()


def test_broken_options_start_with_defaults():
    options.reset()
    path = fresh('opt.json')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('not json at all')
    options.load(path)
    assert options.shake_level == 2 and options.music_level == options.VOLUME_DEFAULT
    assert os.path.exists(path + '.broken')
    options.reset()


def test_log_rotates_when_big():
    old = log.PATH
    log.PATH = fresh('big_log.txt')
    try:
        for i in range(400):
            log.write('x' * 1000)
        assert os.path.getsize(log.PATH) <= log.MAX_BYTES
        assert os.path.exists(log.PATH + '.old')
    finally:
        log.PATH = old


def test_crash_is_logged_and_reported():
    import main
    shown = []

    def boom():
        raise RuntimeError('일부러 낸 오류')

    code = main.run_safely(boom, report=shown.append)
    assert code == 1
    assert 'RuntimeError' in log_text() and '일부러 낸 오류' in log_text()     # 추적 내용(traceback)이 남는다
    assert shown and log.PATH in shown[0]                                      # 안내 창에 기록 파일 위치
    assert main.run_safely(lambda: None, report=shown.append) == 0


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
