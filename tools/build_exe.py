"""실행 파일 만들기 (2026-11-21 퀄리티 계획 3-1). 파이썬 없는 Windows PC에서 켜지는 폴더 + zip을 만든다.

실행: python tools/build_exe.py            (PyInstaller 필요: python -m pip install pyinstaller)
결과: dist/Haze/Haze.exe (폴더째 옮겨야 한다), dist/Haze_win64.zip (나눠 줄 파일)

- 한 폴더(onedir) 방식: 한 파일(onefile)보다 켜질 때 빠르고 백신 오탐이 적다.
- 콘솔 창 없이(windowed) 켠다. 오류는 저장 폴더의 기록 파일에 남긴다(계획 3-2).
- 게임이 읽는 폴더만 넣는다(INCLUDE). 원화(forge, 600MB)·컨셉·발표·상점 그림은 넣지 않는다.
- SDL2 DLL은 pysdl2-dll 패키지(sdl2dll)에서 가져온다.
"""
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
NAME = 'Haze'
# 게임 코드가 읽는 폴더 (tests/test_build.py가 src를 훑어 빠진 것이 없는지 본다)
INCLUDE = (
    'assets/sprites/unified', 'assets/backgrounds', 'assets/placeholder', 'assets/props', 'assets/decor', 'assets/portraits', 'assets/tiles',
    'assets/ui', 'assets/effects', 'assets/sfx', 'assets/music', 'assets/fonts', 'data',
)
# 게임 실행에 필요 없는데 딸려 들어오는 큰 패키지 (numpy는 소리·그림 만드는 도구에서만 쓴다)
EXCLUDE = ('IPython', 'jedi', 'parso', 'numpy', 'scipy', 'matplotlib', 'tkinter', 'pytest', 'pygments', 'prompt_toolkit', 'zmq')
ICON_SOURCE = 'assets/sprites/unified/n09_idle_1.png'


def make_icon(out_path):
    """주인공 대기 그림을 정사각형에 놓고 최근접으로 키워 아이콘(.ico)을 만든다 (빌드용, 게임 화면에는 안 쓴다)."""
    from PIL import Image
    im = Image.open(os.path.join(ROOT, ICON_SOURCE)).convert('RGBA')
    im = im.crop(im.getbbox())
    side = max(im.size)
    square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    square.paste(im, ((side - im.width) // 2, side - im.height))
    k = max(1, 256 // side)
    big = square.resize((side * k, side * k), Image.NEAREST)
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    canvas.paste(big, ((256 - big.width) // 2, (256 - big.height) // 2))
    canvas.save(out_path, sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])


def build():
    work = os.path.join(ROOT, 'build', 'pyinstaller')
    dist = os.path.join(ROOT, 'dist')
    os.makedirs(work, exist_ok=True)
    icon = os.path.join(work, 'haze.ico')
    make_icon(icon)
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed', '--name', NAME,
            '--icon', icon, '--paths', os.path.join(ROOT, 'src'),
            '--workpath', work, '--specpath', work, '--distpath', dist,
            '--collect-all', 'sdl2dll', '--hidden-import', 'transitions']
    for mod in EXCLUDE:
        args += ['--exclude-module', mod]
    for folder in INCLUDE:
        args += ['--add-data', f'{os.path.join(ROOT, folder)}{os.pathsep}{folder}']
    args.append(os.path.join(ROOT, 'src', 'main.py'))
    subprocess.run(args, check=True, cwd=ROOT)
    shutil.copyfile(os.path.join(ROOT, 'assets', 'fonts', 'OFL.txt'), os.path.join(dist, NAME, 'FONT_LICENSE_OFL.txt'))
    with open(os.path.join(dist, NAME, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write('헤이즈 (HAZE)\n\nHaze.exe를 실행한다. 이 폴더(_internal 포함)를 통째로 옮겨야 한다.\n'
                '설정·저장은 사용자 폴더의 .haze_options.json, .haze_save.json에 남는다.\n')
    zip_path = os.path.join(dist, f'{NAME}_win64.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        base = os.path.join(dist, NAME)
        for dirpath, _dirs, files in os.walk(base):
            for fn in files:
                full = os.path.join(dirpath, fn)
                z.write(full, os.path.join(NAME, os.path.relpath(full, base)))
    return os.path.join(dist, NAME, NAME + '.exe'), zip_path


if __name__ == '__main__':
    exe, zp = build()
    print('실행 파일', os.path.relpath(exe, ROOT))
    print('나눠 줄 zip', os.path.relpath(zp, ROOT), f'{os.path.getsize(zp) // 1024 // 1024}MB')
