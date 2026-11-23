"""배경음악 v2 (2026-11-24 사용자: 같은 곡만 계속 들려 별로다). 창 없이: python tests/test_music_v2.py

- 곡은 OpenGameArt의 CC0·CC-BY 3.0 곡 8개 (ogg·mp3). 타이틀·은신처·슬럼·공장·탑·전투·크래셔·아크.
- 적이 남아 방이 잠겨 있으면 전투곡, 다 잡으면 그 구역 탐험곡. 보스가 살아 있으면 보스곡이 먼저. 은신처·연습장은 은신처 곡.
- CC-BY 곡의 작곡가는 크레딧에 적는다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import assets  # noqa: E402
import play_mode  # noqa: E402

TRACKS = ('title', 'hideout', 'explore', 'factory', 'tower', 'combat', 'boss', 'ark')


class FakeRoom:
    def __init__(self, locked):
        self.locked = locked


class FakeStage:
    def __init__(self, name, locked=False, boss=None):
        self.name, self.room, self.boss = name, FakeRoom(locked), boss


class FakeBoss:
    alive = True


def test_every_track_has_a_compressed_file():
    for name in TRACKS:
        path = assets.music_path(name)
        assert path and path.endswith(('.ogg', '.mp3')), name
        assert os.path.getsize(path) > 300_000, name                # 짧은 반복이 아니라 1분이 넘는 곡
        assert os.path.getsize(path) < 5_000_000, name              # 저장소 규칙: 5MB 미만


def test_combat_music_while_the_room_is_locked():
    assert play_mode.music_for(FakeStage('stage1', locked=True)) == 'combat'
    assert play_mode.music_for(FakeStage('stage1', locked=False)) == 'explore'
    assert play_mode.music_for(FakeStage('stage2', locked=False)) == 'factory'
    assert play_mode.music_for(FakeStage('stage3', locked=True, boss=FakeBoss())) == 'boss'
    assert play_mode.music_for(FakeStage('hideout', locked=True)) == 'hideout'
    assert play_mode.music_for(FakeStage('practice', locked=False)) == 'hideout'


def test_credits_name_the_cc_by_composers():
    import credits_mode
    text = ' '.join(t for _, t in credits_mode.CREDITS)
    for who in ('Alexandr Zhelanov', 'SouljahdeShiva', 'marcelofg55', 'OpenGameArt'):
        assert who in text, who


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
