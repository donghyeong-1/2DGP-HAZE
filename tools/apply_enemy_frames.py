"""Codex가 만든 적·보스 동작 프레임(forge)을 게임용 이름으로 assets/sprites/unified/에 복사한다.

forge 결과 폴더의 frames/<접두어>-N.png -> unified/<세트 이름>_N.png (접두어 기본 'sheet')
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
# T20 (2026-11-18): 최종 보스 아크. 프레임 파일 이름이 동작 이름(barrage-1.png ...)이다
for _act, _count in (('barrage', 2), ('slash', 3), ('absorb', 2), ('overcharge', 2), ('field', 2), ('idle', 2),
                     ('walk', 4), ('vanish', 1), ('appear', 1), ('hurt', 1), ('phase', 1), ('death', 2)):
    SETS[f'boss_ark_{_act}'] = (f'boss_ark_{_act}_v1', _count, _act)


def main():
    for name, spec in SETS.items():
        folder, count = spec[0], spec[1]
        prefix = spec[2] if len(spec) > 2 else 'sheet'
        for n in range(1, count + 1):
            src = os.path.join(FORGE, folder, 'frames', f'{prefix}-{n}.png')
            shutil.copyfile(src, os.path.join(UNIFIED, f'{name}_{n}.png'))
        print(name, count)


if __name__ == '__main__':
    main()
