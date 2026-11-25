"""Codex T50 문지기 그림을 게임에 적용한다 (2026-11-25 Claude Code 검토·적용).

원본: assets/sprites/forge/gatekeeper_v1/frames/<동작>-<번호>.png (360x284 공통 캔버스, 기준점 (168, 250) = 발 가운데·바닥)
결과: assets/sprites/unified/boss_gatekeeper_<세트>_<번호>.png, boss_gatekeeper_idle.png, skin_gatekeeper.json
크기·색은 바꾸지 않고 그대로 복사한다(1배). 간수 그림을 키워 구운 임시 그림(tools/make_gatekeeper.py)을 대신한다.

세트 이름은 게임이 쓰는 이름에 맞춘다:
  idle 2 (대기 숨쉬기) / walk 4 / heavy 3 = slam(내려찍기: 예고·타격·바닥) / bash 3 = charge(방패 돌진: 웅크림·돌진·제동)
  call 2 (증원 호출: 호루라기) / hurt 2 = hurt-1(움찔) + death-1(한 무릎: 벽에 부딪혀 비틀) / death 2
사용: python tools/apply_gatekeeper_t50.py
"""
import glob
import json
import os
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'sprites', 'forge', 'gatekeeper_v1', 'frames')
UNI = os.path.join(ROOT, 'assets', 'sprites', 'unified')
ANCHOR = (168, 250)
SETS = {
    'idle': ['idle-1', 'idle-2'],
    'walk': ['walk-1', 'walk-2', 'walk-3', 'walk-4'],
    'heavy': ['slam-1', 'slam-2', 'slam-3'],
    'bash': ['charge-1', 'charge-2', 'charge-3'],
    'call': ['call-1', 'call-2'],
    'hurt': ['hurt-1', 'death-1'],
    'death': ['death-1', 'death-2'],
}


def main():
    for old in glob.glob(os.path.join(UNI, 'boss_gatekeeper_*.png')):        # 임시 그림을 치운다 (장수가 달라 남는 파일이 없게)
        os.remove(old)
    frames = {}
    for name, files in SETS.items():
        for n, f in enumerate(files, 1):
            src = os.path.join(SRC, f + '.png')
            im = Image.open(src)
            assert im.size == (360, 284), (f, im.size)
            assert set(im.convert('RGBA').getchannel('A').getdata()) <= {0, 255}, f
            shutil.copyfile(src, os.path.join(UNI, f'boss_gatekeeper_{name}_{n}.png'))
        frames[f'boss_gatekeeper_{name}'] = [len(files), *ANCHOR]
    shutil.copyfile(os.path.join(SRC, 'idle-1.png'), os.path.join(UNI, 'boss_gatekeeper_idle.png'))
    with open(os.path.join(UNI, 'skin_gatekeeper.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'frames': frames, 'skin': {}}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('saved', {k: v[0] for k, v in frames.items()})


if __name__ == '__main__':
    main()
