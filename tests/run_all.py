"""모든 테스트 파일을 차례로 실행한다 (pytest 없이). 실행: python tests/run_all.py"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
failed = []
for path in sorted(glob.glob(os.path.join(HERE, 'test_*.py'))):
    name = os.path.basename(path)
    result = subprocess.run([sys.executable, path], capture_output=True, text=True, encoding='utf-8', errors='replace')
    last = (result.stdout.strip().splitlines() or [''])[-1]
    print(f'{"통과" if result.returncode == 0 else "실패"}  {name}  {last}')
    if result.returncode != 0:
        failed.append(name)
        print(result.stdout[-1500:], result.stderr[-1500:])
sys.exit(1 if failed else 0)
