"""S2-2 효과음 v3 (2026-11-27, 사용자 "효과음은 다 별로인데 아까 준 사이트에서도 효과음 좀 가지고 와서 다시 해줘").
창·오디오 없이: python tests/test_sfx_s2.py (11/24의 tests/test_sfx_v3.py는 예전 묶음 안의 '효과음 v3' 손질, 이름만 겹친다)

- 새 묶음은 assets/sfx_v3/ (tools/make_sfx_v3.py가 녹음 원본으로 굽는다). config.SFX_SET = 'v3'이 기본, 'v2'면 예전 assets/sfx/.
  v3에 없는 이름은 예전 파일을 쓴다(통째로 둔 묶음). 값 하나로 돌아갈 수 있다.
- 게임이 부르는 모든 소리 이름이 지금 묶음에서 파일로 풀린다.
- 새 파일: 44.1kHz 16비트 모노, 최대값 -1dBFS 아래(잘림 없음), 앞 무음 5ms 안, 반복 소리는 0.1~0.45초.
- 자주 나는 소리(config.SFX_VARIANTS)를 새로 만들었으면 변주 셋이 모두 v3에 있고 서로 다르다.
- 새 파일마다 쓴 원본이 출처 표(make_sfx_v3.SOURCES)에 있고, 원본 파일과 라이선스 문서가 저장소에 있다.
"""
import json
import os
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import config  # noqa: E402
import assets  # noqa: E402

V3 = os.path.join(ROOT, 'assets', 'sfx_v3')
V2 = os.path.join(ROOT, 'assets', 'sfx')


def _names(folder):
    return sorted(f[:-4] for f in os.listdir(folder) if f.endswith('.wav'))


def _base(names):
    import re
    return [n for n in names if not re.search(r'_v\d$', n)]


def _manifest():
    with open(os.path.join(V3, 'MANIFEST.json'), encoding='utf-8') as f:
        return json.load(f)


def test_default_set_is_v3_and_v2_reads_the_old_files():
    assert config.SFX_SET == 'v3'
    new = _names(V3)[0]
    assert os.path.normpath(assets.sfx_path(new)) == os.path.normpath(os.path.join(V3, new + '.wav'))
    old = config.SFX_SET
    try:
        config.SFX_SET = 'v2'
        assert os.path.normpath(assets.sfx_path(new)) == os.path.normpath(os.path.join(V2, new + '.wav'))
    finally:
        config.SFX_SET = old
    assert os.path.normpath(assets.sfx_path(new, 'v2')) == os.path.normpath(os.path.join(V2, new + '.wav'))


def test_every_name_the_game_plays_resolves_in_both_sets():
    names = set(_base(_names(V2))) | set(_base(_names(V3)))
    for s in ('v3', 'v2'):
        for n in names:
            if s == 'v2' and n in config.SFX_NEW_ONLY:      # S3: 예전 묶음에 없던 소리(발소리)는 v2에서 조용하다
                continue
            p = assets.sfx_path(n, s)
            assert p and os.path.exists(p), (s, n)
    literal = _literal_names()
    for n in literal:
        assert assets.sfx_path(n, 'v3') and (assets.sfx_path(n, 'v2') or n in config.SFX_NEW_ONLY), n


def _literal_names():
    import re
    found = set()
    for f in os.listdir(os.path.join(ROOT, 'src')):
        if f.endswith('.py'):
            text = open(os.path.join(ROOT, 'src', f), encoding='utf-8').read()
            found |= set(re.findall(r"play_sound\('([a-z0-9_]+)'\)", text))
    return found


def test_new_files_format_peak_and_lead_silence():
    import sfx_metrics as M
    man = _manifest()['sounds']
    for n in _names(V3):
        path = os.path.join(V3, n + '.wav')
        with wave.open(path, 'rb') as f:
            assert (f.getnchannels(), f.getsampwidth(), f.getframerate()) == (1, 2, 44100), n
        m = M.measure_file(path)
        assert m['peak_db'] <= -1.0 and not m['clip'], (n, m['peak_db'])
        assert m['peak_db'] > -20, (n, m['peak_db'])                        # 무음이 아니다 (겹쳐 나는 색 소리는 작다)
        assert m['lead_ms'] <= 5.0, (n, m['lead_ms'])
        base = _base([n])[0] if _base([n]) else n[:n.rindex('_v')]
        if base in config.SFX_VARIANTS:
            assert 0.1 <= m['length'] <= 0.45, (n, m['length'])
        assert m['length'] <= 2.0, (n, m['length'])
        assert base in man, n


def test_remade_frequent_sounds_have_three_different_variants():
    import sfx_metrics as M
    v3 = set(_names(V3))
    for name in config.SFX_VARIANTS:
        if name not in v3:
            continue
        files = [name, name + '_v2', name + '_v3']
        assert all(f in v3 for f in files), name
        xs = [M.read_wav(os.path.join(V3, f + '.wav'))[0] for f in files]
        for i in range(3):
            for j in range(i + 1, 3):
                a, b = xs[i], xs[j]
                same_len = len(a) == len(b)
                assert not (same_len and (abs(a - b).max() < 1e-3)), (name, i, j)        # 같은 파일이 아니다
                assert M.spectrum_distance(a, b) > 0.15 or not same_len, (name, i, j)


def test_every_source_is_registered_with_a_license_file():
    import make_sfx_v3 as S
    man = _manifest()
    for name, info in man['sounds'].items():
        assert info['sources'] or info.get('synth'), name
        for src in info['sources']:
            origin = src.split('/')[0]
            assert origin in S.SOURCES, (name, src)
            assert os.path.exists(os.path.join(ROOT, 'assets', 'sfx_src', src)), (name, src)
    for origin, meta in S.SOURCES.items():
        assert meta['license'] in ('CC0 1.0',) or meta['license'].startswith('CC BY'), origin
        lic = os.path.join(ROOT, 'assets', 'sfx_src', origin)
        assert any(os.path.exists(os.path.join(lic, d, 'License.txt')) for d in os.listdir(lic)
                   if os.path.isdir(os.path.join(lic, d))) or os.path.exists(os.path.join(lic, 'SOURCE.md')), origin


def test_v3_recipes_cover_whole_groups():
    """한 묶음은 통째로 바꾸거나 통째로 둔다: 표의 묶음마다 이름이 모두 v3에 있거나 하나도 없다."""
    import make_sfx_v3 as S
    v3 = set(_names(V3))
    for group, names in S.GROUPS.items():
        have = [n for n in names if n in v3]
        assert len(have) in (0, len(names)), (group, sorted(set(names) - v3))


def test_mix_targets_keep_hits_above_swings_and_movement():
    """v3는 소리별 크기를 파일에 굽는다(종류별 목표 크기). 타격 > 휘두르기·움직임 > 메뉴."""
    import sfx_metrics as M

    def loud(n):
        return M.measure_file(assets.sfx_path(n, 'v3'))['loud_db'] + 20 * __import__('math').log10(assets.sfx_gain(n, 'v3'))
    for hit in ('impact_pipe', 'impact_gauntlet', 'impact_pipe_heavy'):
        for soft in ('swing_1', 'swing', 'dash', 'jump', 'land', 'ui_move'):
            assert loud(hit) > loud(soft) + 3, (hit, soft, loud(hit), loud(soft))


def test_potion_has_its_own_sound_and_falls_back_on_v2():
    assert os.path.exists(assets.sfx_path('potion', 'v3'))
    old = assets.sfx_path('potion', 'v2')
    assert old and old.endswith('enhance.wav')                    # 예전 묶음에는 물약 소리가 없어 강화 소리 그대로

    sys.path.insert(0, HERE)
    import test_combat as tc
    _room, p = tc.make_world()
    p.hp = 20
    heard = []
    real, assets.play_sound = assets.play_sound, heard.append
    try:
        assert p.drink_potion()
    finally:
        assets.play_sound = real
    assert 'potion' in heard and 'enhance' not in heard, heard


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('통과', t.__name__)
    print(f'{len(tests)}개 통과')
