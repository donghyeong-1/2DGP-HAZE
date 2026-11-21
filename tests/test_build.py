"""실행 파일(PyInstaller) 준비 테스트 (빌드 없이). 실행: python tests/test_build.py

2026-11-21 퀄리티 계획 3-1: 파이썬 없는 PC에서 켜지는 실행 파일.
- 실행 파일 안에서는 에셋·데이터를 PyInstaller가 풀어 둔 폴더(sys._MEIPASS)에서 찾는다.
- 빌드에 넣는 폴더(tools/build_exe.INCLUDE)가 게임 코드가 읽는 폴더를 모두 덮는다. 원화(forge)·컨셉·발표 자료는 넣지 않는다.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import assets  # noqa: E402
import build_exe  # noqa: E402


def test_resource_root_uses_bundle_folder_when_frozen():
    assert os.path.abspath(assets.resource_root()) == ROOT                       # 개발: 저장소 폴더
    assert assets.resource_root(frozen=True, bundle=r'C:\game\_internal') == r'C:\game\_internal'


def test_build_includes_every_folder_the_game_reads():
    src = ''.join(open(p, encoding='utf-8').read() for p in glob.glob(os.path.join(ROOT, 'src', '*.py')))
    used = set(re.findall(r"'((?:sprites/unified|backgrounds|placeholder|props|decor|portraits|tiles|ui|effects|sfx|music|fonts))[/']", src))
    used |= {'sfx', 'music', 'fonts', 'effects'}                                 # os.path.join(ASSET_DIR, 'sfx', ...) 형태
    for folder in used:
        assert 'assets/' + folder in build_exe.INCLUDE, folder
    assert 'data' in build_exe.INCLUDE
    for big in ('assets/sprites/forge', 'assets/concept', 'assets/presentation_examples', 'assets/store'):
        assert big not in build_exe.INCLUDE and not any(i.startswith(big) for i in build_exe.INCLUDE), big


def test_included_size_is_small():
    total = 0
    for folder in build_exe.INCLUDE:
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, folder)):
            total += sum(os.path.getsize(os.path.join(dirpath, f)) for f in files)
    assert total < 60 * 1024 * 1024, f'{total // 1024 // 1024}MB'               # 원화가 섞여 들어가지 않았다


def test_title_logo_is_store_logo_at_1x():
    """퀄리티 계획 4-1: 타이틀 로고는 상점 로고(T29, 2x2 블록)를 정확히 절반으로 줄인 1배 그림 (tools/make_store_art.py)."""
    from PIL import Image
    big = Image.open(os.path.join(ROOT, 'assets', 'store', 'library_logo.png')).convert('RGBA')
    small = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo_title.png')).convert('RGBA')
    half = big.resize((big.width // 2, big.height // 2), Image.NEAREST)
    assert small.tobytes() == half.crop(half.getbbox()).tobytes()              # 잃는 픽셀 없이 절반
    src = open(os.path.join(ROOT, 'src', 'title_mode.py'), encoding='utf-8').read()
    assert "ui/logo_title.png" in src


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
