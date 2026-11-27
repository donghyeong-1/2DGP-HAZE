"""효과음 듣는 방 (v8 계획 4-6). 창 없이: python tests/test_sfx_room.py

- 연습 메뉴에 '효과음 듣기' 줄이 있다.
- assets/sfx의 모든 소리가 종류별 목록에 한 번씩 들어 있다.
- '좋음'·'바꿔' 표시는 파일로 저장되고 다시 열면 그대로다. '바꿔'인 것은 종류별 목록(redo)으로도 적힌다.
- S2-2 (11/27): 목록은 예전 묶음(assets/sfx)과 새 묶음(assets/sfx_v3)의 이름을 합친 것(새 소리 'potion'이 더해졌다).
  표시는 게임이 쓰는 묶음 칸에 적는다(v3면 'marks_v3'·'redo_v3', v2면 예전 그대로 'marks'·'redo'). V로 예전 소리와 번갈아 듣는다.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import config  # noqa: E402
import practice_mode  # noqa: E402
import sfx_mode  # noqa: E402


def test_practice_menu_opens_the_sfx_room():
    assert 'sfx' in practice_mode.ROWS and practice_mode.NAMES['sfx'] == '효과음 듣기'


def test_every_sound_file_is_listed_once():
    files = sorted({f[:-4] for d in ('sfx', 'sfx_v3') for f in os.listdir(os.path.join(HERE, '..', 'assets', d)) if f.endswith('.wav')})
    listed = sorted(n for _, names in sfx_mode.catalog() for n in names)
    assert listed == files and len(files) > 100
    assert all(names for _, names in sfx_mode.catalog())                 # 빈 종류는 없다


def test_marks_are_saved_and_come_back():
    sfx_mode.PATH = os.path.join(tempfile.mkdtemp(), 'sfx_review.json')
    sfx_mode.marks = {}
    label, names = sfx_mode.catalog()[0]
    sfx_mode.mark(names[0], 'bad')
    sfx_mode.mark(names[1], 'good')
    data = json.load(open(sfx_mode.PATH, encoding='utf-8'))
    assert data['marks_v3'] == {names[0]: 'bad', names[1]: 'good'} and data['redo_v3'] == {label: [names[0]]}
    sfx_mode.marks = {}
    assert sfx_mode.load() == {names[0]: 'bad', names[1]: 'good'}
    sfx_mode.mark(names[0], None)                                        # 표시 지우기
    assert names[0] not in sfx_mode.load()
    old = config.SFX_SET
    try:                                                                 # 예전 묶음의 표시는 예전 칸 그대로, 서로 섞이지 않는다
        config.SFX_SET = 'v2'
        assert sfx_mode.load() == {}
        sfx_mode.mark(names[2], 'good')
        data = json.load(open(sfx_mode.PATH, encoding='utf-8'))
        assert data['marks'] == {names[2]: 'good'} and data['marks_v3'] == {names[1]: 'good'}
    finally:
        config.SFX_SET = old


def test_v_switches_between_new_and_old_sounds():
    sfx_mode.listen = None
    assert sfx_mode.listening() == config.SFX_SET == 'v3' and '새 소리' in sfx_mode.listen_label()
    assert sfx_mode.toggle_listen() == 'v2' and '예전 소리' in sfx_mode.listen_label()
    assert sfx_mode.toggle_listen() == 'v3'
    assert ('V', '예전과 비교') in sfx_mode.FOOTER


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
