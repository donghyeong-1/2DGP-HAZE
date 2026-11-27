"""N1-4 (2026-11-27) 작은 해상도 (창 없이). 실행: python tests/test_n1_res.py

U1-2 표 18번: 1280x720·1600x900은 1920 논리 화면을 정수가 아닌 비율로 줄여 도트가 고르지 않다. 빼지 않고(작은 모니터·노트북),
- 도트가 정확히 절반이 되는 960x540을 선택지 맨 앞에 더한다 (2px 도트 -> 1px, 갈무리 글자는 원래 크기 11·14px).
- 기본 해상도는 그대로 1920x1080.
- 설정 파일은 해상도를 이름으로도 저장한다. 옛 파일(번호만, 960x540이 없던 순서)은 옛 순서로 읽어 같은 해상도가 된다.
- 해상도 줄 설명은 가장 선명한 해상도를 알려 준다.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import log  # noqa: E402

log.PATH = os.path.join(tempfile.mkdtemp(), 'haze_log.txt')
import options  # noqa: E402

options.PATH = os.path.join(tempfile.mkdtemp(), 'opt.json')


def test_half_size_is_offered_first_and_default_stays():
    names = [n for n, _w, _h in options.RESOLUTIONS]
    assert names[0] == '960x540' and names[1:] == ['1280x720', '1600x900', '1920x1080', '전체 화면']
    options.reset()
    assert options.resolution_name() == '1920x1080'


def test_window_size_for_half():
    import display
    assert display.window_size('960x540', 1920, 1080) == (960, 540, False)


def test_saved_by_name_and_old_index_files_keep_their_size():
    path = os.path.join(tempfile.mkdtemp(), 'o.json')
    options.reset()
    options.set_resolution([n for n, _w, _h in options.RESOLUTIONS].index('960x540'))
    options.save(path)
    options.reset()
    options.load(path)
    assert options.resolution_name() == '960x540'
    for old_index, name in enumerate(('1280x720', '1600x900', '1920x1080', '전체 화면')):   # N1 전 파일: 번호만
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'resolution': old_index}, f)
        options.reset()
        options.load(path)
        assert options.resolution_name() == name, (old_index, options.resolution_name())
    options.reset()


def test_resolution_description_names_the_sharpest_size():
    import options_mode
    assert '1920x1080' in options_mode.DESCS['resolution'] and '선명' in options_mode.DESCS['resolution']


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
