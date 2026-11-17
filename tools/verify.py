"""커밋 전 점검: 테스트, 문서 갱신, 커밋하면 안 되는 파일을 한 번에 확인한다.

실행: python tools/verify.py        (문제가 있으면 종료 코드 1)
검사
 1. tests/run_all.py 전체 (픽셀 규칙 test_pixel_assets 포함)
 2. src/·tools/·data/·assets/를 바꿨는데 docs/PROGRESS.md를 안 바꿨으면 경고 (작업 로그 한 줄)
 3. PROGRESS.md 작업 로그에 오늘 날짜 줄이 있는지
 4. PROGRESS.md "진행 중"에 다른 도구(Codex 등)의 줄이 있으면 알림: 그 파일들은 건드리지 않는다
 5. 바뀐 파일 중 Codex 영역(assets/sprites/forge/, docs/codex/reports/)을 알려 준다: 검토가 끝난 것만 커밋한다
 6. 큰 파일(5MB 넘는)과 AI 원본(source.png)이 스테이지에 올라가 있지 않은지
"""
import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8').stdout


def main():
    problems, notes = [], []

    r = subprocess.run([sys.executable, 'tests/run_all.py'], capture_output=True, text=True, encoding='utf-8', env=ENV)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    total = sum(int(m.group(1)) for ln in lines for m in [re.search(r'(\d+)개 통과', ln)] if m)
    if r.returncode != 0 or any(ln.startswith('실패') for ln in lines):
        problems.append('테스트 실패:\n' + '\n'.join(lines[-15:]) + ('\n' + r.stderr[-1500:] if r.stderr else ''))
    else:
        notes.append(f'테스트 {total}개 통과')

    changed = [ln[3:].strip().strip('"') for ln in git('status', '--porcelain').splitlines()]
    code = [f for f in changed if f.startswith(('src/', 'tools/', 'data/', 'assets/', 'tests/'))
            and not f.startswith('assets/sprites/forge/')]
    if code and 'docs/PROGRESS.md' not in changed:
        problems.append('코드·에셋을 바꿨는데 docs/PROGRESS.md 작업 로그를 갱신하지 않았다: ' + ', '.join(code[:6]))

    progress = open('docs/PROGRESS.md', encoding='utf-8').read()
    today = datetime.date.today().isoformat()
    if code and f'{today} [Claude Code]' not in progress:
        problems.append(f'PROGRESS.md 작업 로그에 오늘({today}) [Claude Code] 줄이 없다')
    m = re.search(r'## 진행 중\n(.*?)\n## ', progress, re.S)
    if m:
        others = [ln for ln in m.group(1).splitlines() if ln.startswith('- ') and '(없음' not in ln]
        for ln in others:
            notes.append('진행 중(건드리지 말 것): ' + ln[2:])

    codex = [f for f in changed if f.startswith(('assets/sprites/forge/', 'docs/codex/reports/'))]
    if codex:
        notes.append(f'Codex 영역 변경 {len(codex)}건(검토·적용이 끝난 것만 커밋): ' + ', '.join(codex[:4])
                     + (' ...' if len(codex) > 4 else ''))

    for f in git('diff', '--cached', '--name-only').splitlines():
        if f.endswith('source.png') or '/source/' in f:
            problems.append(f'AI 원본은 커밋하지 않는다(.gitignore): {f}')
        elif os.path.isfile(f) and os.path.getsize(f) > 5 * 1024 * 1024:
            problems.append(f'5MB 넘는 파일이 스테이지에 있다: {f} ({os.path.getsize(f) // 1024 // 1024}MB)')

    for n in notes:
        print('  -', n)
    if problems:
        print('\n문제:')
        for p in problems:
            print('  x', p)
        sys.exit(1)
    print('통과: 커밋해도 된다 (git add는 경로를 명시해서)')


if __name__ == '__main__':
    main()
