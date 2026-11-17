"""Codex가 만든 적 동작 프레임(forge)을 게임용 이름으로 assets/sprites/unified/에 복사한다.

forge 결과 폴더의 frames/sheet-N.png -> unified/<세트 이름>_N.png
기준점(발 위치)은 각 결과의 보고서(docs/codex/reports/)에 적힌 피벗이며, src/sprites.py FRAMES에 같은 값을 적는다.
실행: python tools/apply_enemy_frames.py
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORGE = os.path.join(ROOT, 'assets', 'sprites', 'forge')
UNIFIED = os.path.join(ROOT, 'assets', 'sprites', 'unified')

# 세트 이름 -> (forge 폴더, 프레임 수).  T12 (2026-11-17): 사냥개·간수
SETS = {
    'enemy_hound_run': ('enemy_hound_run_v3b', 4),
    'enemy_hound_bite': ('enemy_hound_bite_v3', 3),
    'enemy_hound_pounce': ('enemy_hound_pounce_v3', 2),
    'enemy_hound_hurt': ('enemy_hound_hurt_v3', 1),
    'enemy_guard_walk': ('enemy_guard_walk_v3', 4),
    'enemy_guard_swing': ('enemy_guard_swing_v3', 3),
    'enemy_guard_heavy': ('enemy_guard_heavy_v3', 3),
    'enemy_guard_bash': ('enemy_guard_bash_v3', 2),
    'enemy_guard_hurt': ('enemy_guard_hurt_v3', 1),
}


def main():
    for name, (folder, count) in SETS.items():
        for n in range(1, count + 1):
            src = os.path.join(FORGE, folder, 'frames', f'sheet-{n}.png')
            shutil.copyfile(src, os.path.join(UNIFIED, f'{name}_{n}.png'))
        print(name, count)


if __name__ == '__main__':
    main()
