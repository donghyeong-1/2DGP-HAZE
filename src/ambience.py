"""환경음: 구역마다 다른 짧은 소리를 몇 초마다 낸다 (2026-11-21 퀄리티 계획 2-3).
배경음악은 한 곡만 틀 수 있어서, 반복 녹음 대신 짧은 소리를 가끔(AMB_GAP초 사이 무작위) 흩뿌린다.
슬럼 물방울, 공장 증기, 탑 바람, 은신처 화로. 소리는 tools/make_sfx.py가 만든다.
"""
import random

import assets
import config

SOUNDS = {'stage1': 'amb_drip', 'stage2': 'amb_steam', 'stage3': 'amb_wind', 'hideout': 'amb_forge'}


class Ambience:
    def __init__(self, stage, seed=None):
        self.stage = stage
        self.rng = random.Random(seed)
        self.left = self.rng.uniform(*config.AMB_GAP) * 0.5      # 첫 소리는 조금 일찍

    def update(self, dt):
        sound = SOUNDS.get(getattr(self.stage, 'name', ''))
        if sound is None:
            return
        self.left -= dt
        if self.left <= 0:
            assets.play_sound(sound)
            self.left = self.rng.uniform(*config.AMB_GAP)

    def draw(self):
        pass
