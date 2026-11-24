"""효과음 듣는 방 (v8 계획 4-6). 창 없이: python tests/test_sfx_room.py

- 연습 메뉴에 '효과음 듣기' 줄이 있다.
- assets/sfx의 모든 소리가 종류별 목록에 한 번씩 들어 있다.
- '좋음'·'바꿔' 표시는 파일로 저장되고 다시 열면 그대로다. '바꿔'인 것은 종류별 목록(redo)으로도 적힌다.
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'src'))

import practice_mode  # noqa: E402
import sfx_mode  # noqa: E402


def test_practice_menu_opens_the_sfx_room():
    assert 'sfx' in practice_mode.ROWS and practice_mode.NAMES['sfx'] == '효과음 듣기'


def test_every_sound_file_is_listed_once():
    files = sorted(f[:-4] for f in os.listdir(os.path.join(HERE, '..', 'assets', 'sfx')) if f.endswith('.wav'))
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
    assert data['marks'] == {names[0]: 'bad', names[1]: 'good'} and data['redo'] == {label: [names[0]]}
    sfx_mode.marks = {}
    assert sfx_mode.load() == {names[0]: 'bad', names[1]: 'good'}
    sfx_mode.mark(names[0], None)                                        # 표시 지우기
    assert names[0] not in sfx_mode.load()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
