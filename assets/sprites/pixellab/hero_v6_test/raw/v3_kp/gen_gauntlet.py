"""건틀릿 자세 뼈대 (2026-11-24): base_gauntlets의 추정 뼈대(gauntlet_src.json)에서 관절을 옮겨 자세를 만든다.

땅 5장(gauntlet_ground.json): 충전(주먹을 허리 뒤로 당기고 낮게) / 앞 강타(앞발 디디며 팔을 쭉) / 회수 / 앞 위 강타 / 앞 아래 강타.
공중 3장(gauntlet_air.json, 점프 뼈대 기준): 아래로 내리찍는 강타 / 앞 강타 / 앞 위 강타 (skeleton v3는 3장부터).
x는 오른쪽 +, y는 아래 + (이미지 비율 0~1). 머리(코·눈·귀)는 목이 움직인 만큼 같이 옮긴다.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = ('NOSE', 'RIGHT EYE', 'LEFT EYE', 'RIGHT EAR', 'LEFT EAR')


def pose(src, moves):
    k = {p['label']: dict(p) for p in src}
    if 'NECK' in moves:
        dx, dy = moves['NECK'][0] - k['NECK']['x'], moves['NECK'][1] - k['NECK']['y']
        for h in HEAD:
            k[h]['x'] = round(k[h]['x'] + dx, 4)
            k[h]['y'] = round(k[h]['y'] + dy, 4)
    for lab, (x, y) in moves.items():
        k[lab]['x'], k[lab]['y'] = x, y
    return [k[p['label']] for p in src]


def main():
    src = json.load(open(os.path.join(HERE, 'gauntlet_src.json')))
    base, jump = src['base'], src['jump']
    legs_lunge = {'RIGHT HIP': (0.55, 0.64), 'LEFT HIP': (0.51, 0.645), 'RIGHT KNEE': (0.64, 0.765), 'RIGHT LEG': (0.70, 0.93),
                  'LEFT KNEE': (0.44, 0.80), 'LEFT LEG': (0.36, 0.93)}
    ground = [
        pose(base, {'NECK': (0.48, 0.48), 'RIGHT SHOULDER': (0.51, 0.47), 'LEFT SHOULDER': (0.45, 0.48),       # 충전
                    'RIGHT ELBOW': (0.43, 0.55), 'RIGHT ARM': (0.43, 0.61), 'LEFT ELBOW': (0.55, 0.53), 'LEFT ARM': (0.60, 0.50),
                    'RIGHT HIP': (0.52, 0.65), 'LEFT HIP': (0.48, 0.65), 'RIGHT KNEE': (0.60, 0.78), 'RIGHT LEG': (0.64, 0.93),
                    'LEFT KNEE': (0.44, 0.80), 'LEFT LEG': (0.38, 0.93)}),
        pose(base, dict(legs_lunge, **{'NECK': (0.55, 0.47), 'RIGHT SHOULDER': (0.59, 0.46), 'LEFT SHOULDER': (0.52, 0.47),  # 앞 강타
                                       'RIGHT ELBOW': (0.69, 0.47), 'RIGHT ARM': (0.80, 0.46), 'LEFT ELBOW': (0.46, 0.53),
                                       'LEFT ARM': (0.48, 0.59)})),
        pose(base, {'NECK': (0.52, 0.47), 'RIGHT SHOULDER': (0.56, 0.46), 'LEFT SHOULDER': (0.49, 0.47),       # 회수
                    'RIGHT ELBOW': (0.62, 0.52), 'RIGHT ARM': (0.70, 0.52), 'LEFT ELBOW': (0.46, 0.53), 'LEFT ARM': (0.50, 0.58),
                    'RIGHT HIP': (0.545, 0.635), 'LEFT HIP': (0.50, 0.64), 'RIGHT KNEE': (0.61, 0.775), 'RIGHT LEG': (0.65, 0.93),
                    'LEFT KNEE': (0.46, 0.79), 'LEFT LEG': (0.40, 0.93)}),
        pose(base, dict(legs_lunge, **{'NECK': (0.53, 0.47), 'RIGHT SHOULDER': (0.57, 0.46), 'LEFT SHOULDER': (0.50, 0.47),  # 앞 위
                                       'RIGHT ELBOW': (0.64, 0.39), 'RIGHT ARM': (0.72, 0.31), 'LEFT ELBOW': (0.45, 0.53),
                                       'LEFT ARM': (0.47, 0.59)})),
        pose(base, dict(legs_lunge, **{'NECK': (0.56, 0.48), 'RIGHT SHOULDER': (0.60, 0.47), 'LEFT SHOULDER': (0.53, 0.48),  # 앞 아래
                                       'RIGHT ELBOW': (0.67, 0.55), 'RIGHT ARM': (0.75, 0.63), 'LEFT ELBOW': (0.47, 0.54),
                                       'LEFT ARM': (0.49, 0.60)})),
    ]
    tuck = {'RIGHT KNEE': (0.60, 0.58), 'RIGHT LEG': (0.56, 0.70), 'LEFT KNEE': (0.47, 0.57), 'LEFT LEG': (0.43, 0.68)}
    air = [
        pose(jump, dict(tuck, **{'RIGHT ELBOW': (0.56, 0.42), 'RIGHT ARM': (0.58, 0.53),                       # 아래로 내리찍기
                                 'LEFT ELBOW': (0.42, 0.38), 'LEFT ARM': (0.44, 0.44)})),
        pose(jump, dict(tuck, **{'RIGHT ELBOW': (0.63, 0.33), 'RIGHT ARM': (0.74, 0.32),                       # 공중 앞 강타
                                 'LEFT ELBOW': (0.42, 0.38), 'LEFT ARM': (0.44, 0.44)})),
        pose(jump, dict(tuck, **{'RIGHT ELBOW': (0.60, 0.25), 'RIGHT ARM': (0.67, 0.17),                       # 공중 앞 위 강타
                                 'LEFT ELBOW': (0.42, 0.38), 'LEFT ARM': (0.44, 0.44)})),
    ]
    for name, frames in (('gauntlet_ground', ground), ('gauntlet_air', air)):
        with open(os.path.join(HERE, name + '.json'), 'w') as fp:
            json.dump(frames, fp, separators=(',', ':'))
        print(name, len(frames))


if __name__ == '__main__':
    main()
