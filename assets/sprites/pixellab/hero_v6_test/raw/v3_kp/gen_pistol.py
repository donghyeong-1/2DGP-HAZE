"""쌍권총 자세 뼈대 (2026-11-24): base_pistols·run96·jump96의 추정 뼈대(pistol_src.json)에서 두 팔만 조준 각도로 다시 놓는다.

결과: pistol_aim.json(위·앞 위·앞 아래·아래 4장), pistol_run.json(달리며 앞 겨눔 8장), pistol_air.json(공중 앞·위·아래 3장).
x는 오른쪽 +, y는 아래 + (이미지 비율 0~1). 조준 각도는 앞(동쪽) 0도, 위 +.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
UPPER, FORE = 0.10, 0.095          # 위팔·아래팔 길이 (base_pistols에서 잰 값)


def by_label(points):
    return {p['label']: dict(p) for p in points}


def aim(points, deg, bend=8):
    """두 팔을 deg 방향으로 뻗는다 (팔꿈치는 살짝 아래로 굽힘). 두 손목은 거의 같은 곳 (두 총을 나란히)."""
    k = by_label(points)
    for s_lab, e_lab, w_lab, extra in (('RIGHT SHOULDER', 'RIGHT ELBOW', 'RIGHT ARM', 0.0),
                                       ('LEFT SHOULDER', 'LEFT ELBOW', 'LEFT ARM', 0.012)):
        sx, sy = k[s_lab]['x'], k[s_lab]['y']
        a, ea = math.radians(deg), math.radians(deg - bend)
        k[e_lab].update(x=round(sx + UPPER * math.cos(ea), 4), y=round(sy - UPPER * math.sin(ea), 4))
        reach = (UPPER + FORE + extra) * 0.97
        k[w_lab].update(x=round(sx + reach * math.cos(a), 4), y=round(sy - reach * math.sin(a), 4))
    return [k[p['label']] for p in points]


def main():
    src = json.load(open(os.path.join(HERE, 'pistol_src.json')))
    sets = {'pistol_aim': [aim(src['base'], d) for d in (80, 42, -42, -75)],
            'pistol_run': [aim(f, 0) for f in src['run']],
            'pistol_air': [aim(src['jump'], d) for d in (0, 42, -42)]}
    for name, frames in sets.items():
        with open(os.path.join(HERE, name + '.json'), 'w') as fp:
            json.dump(frames, fp, separators=(',', ':'))
        print(name, len(frames))


if __name__ == '__main__':
    main()
