"""게임 실행 코드(src/)는 pico2d·Pillow·transitions만으로 돌아야 한다 (창 없이 실행).

2026-11-23: 캐릭터 테두리 코드가 실행 중 numpy를 써서, numpy가 없는 실행 환경(사용자 PC의 게임 실행 파이썬)에서
게임을 시작하자마자 꺼졌다. numpy·scipy는 tools/(그림 만들기)에서만 쓴다.
실행: python tests/test_runtime_deps.py
"""
import ast
import glob
import os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
FORBIDDEN = {'numpy', 'scipy', 'cv2', 'torch'}


def imported_modules(path):
    tree = ast.parse(open(path, encoding='utf-8').read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name.split('.')[0], node.lineno
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module.split('.')[0], node.lineno


def test_game_code_does_not_import_numpy_or_scipy():
    bad = []
    for path in sorted(glob.glob(os.path.join(SRC, '*.py'))):
        for mod, line in imported_modules(path):
            if mod in FORBIDDEN:
                bad.append(f'{os.path.basename(path)}:{line} {mod}')
    assert not bad, '게임 실행 코드가 numpy/scipy를 쓴다: ' + ', '.join(bad)


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
