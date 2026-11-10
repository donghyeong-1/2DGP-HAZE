"""효과음 파일 검사 (창·오디오 장치 없이 실행). 실행: python tests/test_sfx.py 또는 pytest"""
import os
import sys
import wave

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import config  # noqa: E402

NAMES = ['jump', 'double_jump', 'dash', 'land', 'hit', 'pickup', 'enhance', 'overload', 'death']


def test_sfx_files_are_valid_short_wavs():
    for name in NAMES:
        path = os.path.join(ROOT, 'assets', 'sfx', name + '.wav')
        assert os.path.exists(path), name
        with wave.open(path, 'rb') as f:
            assert f.getnchannels() == 1 and f.getsampwidth() == 2
            seconds = f.getnframes() / f.getframerate()
            assert 0.05 < seconds < 1.0, f'{name}: {seconds:.2f}초'
            data = f.readframes(f.getnframes())
        peak = max(abs(int.from_bytes(data[i:i + 2], 'little', signed=True)) for i in range(0, len(data), 2))
        assert 3000 < peak < 32000, f'{name}: 피크 {peak} (무음이거나 클리핑)'


def test_sound_is_silent_when_disabled():
    import assets
    assert config.SOUND_ENABLED is False  # 테스트에서는 꺼져 있다
    assets.play_sound('jump')             # 예외 없이 아무 일도 하지 않아야 한다


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
