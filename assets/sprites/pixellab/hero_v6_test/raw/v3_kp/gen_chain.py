"""사슬 자세 뼈대 (2026-11-24): base_chain의 추정 뼈대에서 관절을 옮긴다 (gen_gauntlet.pose 재사용).

땅 5장(chain_ground.json): 돌리기(사슬 쥔 팔을 머리 위로) / 앞 던지기 / 두 손으로 당기기(몸을 뒤로) / 앞 위 던지기 / 앞 아래 던지기.
공중 3장(chain_air.json, 점프 뼈대 기준): 앞 던지기 / 앞 위 던지기 / 아래 던지기.
"""
import json
import os

from gen_gauntlet import pose

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = [{"x": 0.5685, "y": 0.4162, "label": "NOSE", "z_index": -2}, {"x": 0.5042, "y": 0.4637, "label": "NECK", "z_index": -2},
        {"x": 0.5405, "y": 0.4591, "label": "RIGHT SHOULDER", "z_index": 0}, {"x": 0.5722, "y": 0.5467, "label": "RIGHT ELBOW", "z_index": 0},
        {"x": 0.6729, "y": 0.5765, "label": "RIGHT ARM", "z_index": 0}, {"x": 0.4678, "y": 0.4684, "label": "LEFT SHOULDER", "z_index": -4},
        {"x": 0.3989, "y": 0.4964, "label": "LEFT ELBOW", "z_index": -4}, {"x": 0.3709, "y": 0.5485, "label": "LEFT ARM", "z_index": -4},
        {"x": 0.5405, "y": 0.6361, "label": "RIGHT HIP", "z_index": -1}, {"x": 0.5703, "y": 0.7815, "label": "RIGHT KNEE", "z_index": -1},
        {"x": 0.5815, "y": 0.9306, "label": "RIGHT LEG", "z_index": -1}, {"x": 0.4995, "y": 0.6343, "label": "LEFT HIP", "z_index": -3},
        {"x": 0.4809, "y": 0.7796, "label": "LEFT KNEE", "z_index": -3}, {"x": 0.4362, "y": 0.9176, "label": "LEFT LEG", "z_index": -3},
        {"x": 0.5666, "y": 0.4013, "label": "RIGHT EYE", "z_index": -1}, {"x": 0.5592, "y": 0.3994, "label": "LEFT EYE", "z_index": -3},
        {"x": 0.5424, "y": 0.3976, "label": "RIGHT EAR", "z_index": 0}, {"x": 0.5275, "y": 0.3976, "label": "LEFT EAR", "z_index": -4}]


def main():
    jump = json.load(open(os.path.join(HERE, 'pistol_src.json')))['jump']
    lunge = {'NECK': (0.55, 0.47), 'RIGHT SHOULDER': (0.59, 0.46), 'LEFT SHOULDER': (0.52, 0.47),
             'LEFT ELBOW': (0.46, 0.53), 'LEFT ARM': (0.47, 0.58),
             'RIGHT HIP': (0.55, 0.64), 'LEFT HIP': (0.51, 0.645), 'RIGHT KNEE': (0.64, 0.765), 'RIGHT LEG': (0.70, 0.93),
             'LEFT KNEE': (0.44, 0.80), 'LEFT LEG': (0.36, 0.93)}
    ground = [
        pose(BASE, {'NECK': (0.49, 0.465), 'RIGHT ELBOW': (0.58, 0.37), 'RIGHT ARM': (0.62, 0.27),          # 돌리기
                    'LEFT ELBOW': (0.52, 0.53), 'LEFT ARM': (0.57, 0.52)}),
        pose(BASE, dict(lunge, **{'RIGHT ELBOW': (0.68, 0.47), 'RIGHT ARM': (0.79, 0.47)})),              # 앞 던지기
        pose(BASE, {'NECK': (0.47, 0.48), 'RIGHT SHOULDER': (0.50, 0.47), 'LEFT SHOULDER': (0.44, 0.48),   # 당기기
                    'RIGHT ELBOW': (0.44, 0.54), 'RIGHT ARM': (0.54, 0.52), 'LEFT ELBOW': (0.42, 0.53), 'LEFT ARM': (0.52, 0.51),
                    'RIGHT HIP': (0.50, 0.64), 'LEFT HIP': (0.47, 0.64), 'RIGHT KNEE': (0.60, 0.79), 'RIGHT LEG': (0.68, 0.93),
                    'LEFT KNEE': (0.42, 0.78), 'LEFT LEG': (0.38, 0.93)}),
        pose(BASE, dict(lunge, **{'RIGHT ELBOW': (0.63, 0.39), 'RIGHT ARM': (0.71, 0.31)})),              # 앞 위
        pose(BASE, dict(lunge, **{'RIGHT ELBOW': (0.66, 0.55), 'RIGHT ARM': (0.74, 0.63)})),              # 앞 아래
    ]
    tuck = {'RIGHT KNEE': (0.60, 0.58), 'RIGHT LEG': (0.56, 0.70), 'LEFT KNEE': (0.47, 0.57), 'LEFT LEG': (0.43, 0.68),
            'LEFT ELBOW': (0.42, 0.38), 'LEFT ARM': (0.44, 0.44)}
    air = [pose(jump, dict(tuck, **{'RIGHT ELBOW': (0.63, 0.33), 'RIGHT ARM': (0.74, 0.32)})),
           pose(jump, dict(tuck, **{'RIGHT ELBOW': (0.60, 0.25), 'RIGHT ARM': (0.67, 0.17)})),
           pose(jump, dict(tuck, **{'RIGHT ELBOW': (0.60, 0.42), 'RIGHT ARM': (0.66, 0.52)}))]
    for name, frames in (('chain_ground', ground), ('chain_air', air)):
        with open(os.path.join(HERE, name + '.json'), 'w') as fp:
            json.dump(frames, fp, separators=(',', ':'))
        print(name, len(frames))


if __name__ == '__main__':
    main()
